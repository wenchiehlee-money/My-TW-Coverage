"""Build a health manifest for dynamic valuation chart artifact triplets."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from datetime import datetime, timezone
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


def build_rows(json_dir: Path, chart_dir: Path, max_age_days: float) -> list[dict[str, str]]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    rows: list[dict[str, str]] = []
    for symbol in symbols_from_json(json_dir):
        paths = {kind: chart_dir / f"{symbol}{suffix}" for kind, suffix in ARTIFACTS.items()}
        exists = {kind: path.is_file() for kind, path in paths.items()}
        sizes = {f"{kind}_bytes": str(path.stat().st_size) if exists[kind] else "0" for kind, path in paths.items()}
        fresh = {kind: exists[kind] and path.stat().st_mtime >= cutoff for kind, path in paths.items()}
        row_count, csv_last_date, columns_ok = csv_info(paths["csv"]) if exists["csv"] else (0, "", False)
        healthy = all(exists.values()) and all(fresh.values()) and all(int(value) > 0 for value in sizes.values()) and columns_ok and row_count > 0 and bool(csv_last_date)
        rows.append({
            "symbol": symbol,
            "generated_at": generated_at,
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
            "artifact_status": "healthy" if healthy else "broken_or_stale",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-dir", default="data/enrichment_all")
    parser.add_argument("--chart-dir", default="output/dynamic_valuation_box")
    parser.add_argument("--output", default="output/dynamic_valuation_box_health.csv")
    parser.add_argument("--max-age-days", type=float, default=3.0)
    args = parser.parse_args()

    rows = build_rows(Path(args.json_dir), Path(args.chart_dir), args.max_age_days)
    fieldnames = list(rows[0]) if rows else ["symbol", "generated_at", "artifact_status"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    broken = sum(row["artifact_status"] != "healthy" for row in rows)
    print(f"chart_health rows={len(rows)} broken_or_stale={broken} output={output}")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
