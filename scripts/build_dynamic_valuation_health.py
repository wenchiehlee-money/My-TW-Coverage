"""Build a health manifest for company Markdown pages and dynamic valuation chart artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ARTIFACTS = {
    "csv": "_dynamic_valuation_box_3y.csv",
    "svg": "_dynamic_valuation_box_3y.svg",
    "png": "_dynamic_valuation_box_3y.png",
}
REQUIRED_CSV_COLUMNS = {
    "date",
    "close",
    "ttm_eps",
    "pe",
    "pe_mean",
    "price_mean",
}
UPDATED_RE = re.compile(r"Updated: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) CST")
CHART_TZ = timezone(timedelta(hours=8))


def chart_updated_at(path: Path) -> datetime | None:
    try:
        if path.suffix.lower() == ".png":
            from PIL import Image
            with Image.open(path) as image:
                value = str(image.info.get("Updated", ""))
        else:
            value = path.read_text(encoding="utf-8")
        match = UPDATED_RE.search(value)
        if not match:
            return None
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=CHART_TZ)
    except (ImportError, OSError, UnicodeError, ValueError):
        return None


def symbols_from_json(json_dir: Path) -> list[str]:
    symbols: set[str] = set()
    for path in sorted(json_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ticker = str(payload.get("ticker", "")).strip()
        if ticker.isdigit():
            symbols.add(ticker.zfill(4))
    return sorted(symbols)


def csv_info(path: Path) -> tuple[int, str, bool]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows_without_metadata = (line for line in handle if not line.lstrip().startswith("#"))
            reader = csv.DictReader(rows_without_metadata)
            columns = set(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error):
        return 0, "", False
    dates = sorted((row.get("date") or "").strip() for row in rows if (row.get("date") or "").strip())
    return len(rows), (dates[-1] if dates else ""), REQUIRED_CSV_COLUMNS.issubset(columns)


def company_pages(json_dir: Path, page_dir: Path) -> dict[str, Path]:
    pages = {}
    for path in sorted(json_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ticker = str(data.get("ticker", "")).strip()
        company = str(data.get("company_name", "")).strip()
        if ticker.isdigit() and company:
            pages[ticker.zfill(4)] = page_dir / f"{ticker}_{company}.md"
    return pages


def build_rows(json_dir: Path, chart_dir: Path, max_age_days: float,
               page_dir: Path = Path("output/themes/company")) -> list[dict[str, str]]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    rows: list[dict[str, str]] = []
    pages = company_pages(json_dir, page_dir)
    for symbol in symbols_from_json(json_dir):
        paths = {kind: chart_dir / f"{symbol}{suffix}" for kind, suffix in ARTIFACTS.items()}
        page = pages.get(symbol)
        page_exists = page is not None and page.is_file()
        page_bytes = page.stat().st_size if page_exists else 0
        page_fresh = page_exists and page.stat().st_mtime >= cutoff
        exists = {kind: bool(path and path.is_file()) for kind, path in paths.items()}
        sizes = {f"{kind}_bytes": str(path.stat().st_size) if exists[kind] else "0" for kind, path in paths.items()}
        updated = {kind: chart_updated_at(path) if exists[kind] else None for kind, path in paths.items()}
        fresh = {kind: exists[kind] and updated[kind] is not None and updated[kind].timestamp() >= cutoff for kind, path in paths.items()}
        row_count, csv_last_date, columns_ok = csv_info(paths["csv"]) if exists["csv"] else (0, "", False)
        page_healthy = page_exists and page_bytes > 0 and page_fresh
        artifacts_healthy = all(exists.values()) and all(fresh.values()) and all(int(value) > 0 for value in sizes.values()) and columns_ok and row_count > 0 and bool(csv_last_date)
        rows.append({
            "symbol": symbol,
            "generated_at": generated_at,
            "company_md_path": page.as_posix() if page is not None else "",
            "company_md_exists": str(page_exists).lower(),
            "company_md_fresh": str(page_fresh).lower(),
            "company_md_bytes": str(page_bytes),
            "company_md_status": "healthy" if page_healthy else "broken_or_stale",
            "csv_path": paths["csv"].as_posix(),
            "svg_path": paths["svg"].as_posix(),
            "png_path": paths["png"].as_posix(),
            "csv_exists": str(exists["csv"]).lower(),
            "svg_exists": str(exists["svg"]).lower(),
            "png_exists": str(exists["png"]).lower(),
            "csv_fresh": str(fresh["csv"]).lower(),
            "svg_fresh": str(fresh["svg"]).lower(),
            "png_fresh": str(fresh["png"]).lower(),
            "csv_rows": str(row_count),
            "csv_last_date": csv_last_date,
            "required_columns_ok": str(columns_ok).lower(),
            **sizes,
            "artifact_status": "healthy" if artifacts_healthy else "broken_or_stale",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-dir", default="data/enrichment_all")
    parser.add_argument("--chart-dir", default="output/dynamic_valuation_box")
    parser.add_argument("--page-dir", default="output/themes/company")
    parser.add_argument("--company-md-output", default="output/company_md_health.csv")
    parser.add_argument("--artifacts-output", default="output/valuation_artifacts_health.csv")
    parser.add_argument("--max-age-days", type=float, default=3.0)
    args = parser.parse_args()

    rows = build_rows(Path(args.json_dir), Path(args.chart_dir), args.max_age_days, Path(args.page_dir))
    output_groups = {
        Path(args.company_md_output): [
            "symbol", "generated_at", "company_md_path", "company_md_exists",
            "company_md_fresh", "company_md_bytes", "company_md_status",
        ],
        Path(args.artifacts_output): [
            "symbol", "generated_at", "csv_path", "svg_path", "png_path",
            "csv_exists", "svg_exists", "png_exists", "csv_fresh", "svg_fresh",
            "png_fresh", "csv_rows", "csv_last_date", "required_columns_ok",
            "csv_bytes", "svg_bytes", "png_bytes", "artifact_status",
        ],
    }
    failures = 0
    for output, fieldnames in output_groups.items():
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerows({name: row.get(name, "") for name in fieldnames} for row in rows)
            os.replace(temporary, output)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        status_field = "company_md_status" if "company_md_status" in fieldnames else "artifact_status"
        broken = sum(row[status_field] != "healthy" for row in rows)
        failures += broken
        print(f"health rows={len(rows)} broken_or_stale={broken} output={output}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
