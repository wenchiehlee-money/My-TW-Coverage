#!/usr/bin/env python3
"""Backfill atomic valuation and normalized consensus into enrichment JSON files."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_DIR = ROOT / "data/enrichment_all"
DEFAULT_CONSENSUS = ROOT.parent / "biztrends.TW/data/market_expectations/normalized_consensus.csv"

VALUATION_RE = re.compile(
    r"^### 估值指標(?: \(股價 \$(?P<price>[^ ]+) as of (?P<as_of>[^|)]+)"
    r"(?: \| TTM 截至 (?P<ttm>[^|)]+))?"
    r"(?: \| Forward 預估至 (?P<forward>[^|)]+))?\))?",
    re.M,
)
H3_RE = re.compile(r"(?m)^### .*$")
METRIC_KEYS = {
    "P/E (TTM)": "pe_ttm",
    "Forward P/E": "forward_pe",
    "P/S (TTM)": "ps_ttm",
    "P/B": "pb",
    "EV/EBITDA": "ev_ebitda_ttm",
}


def parse_number(value: object) -> float | None:
    text = str(value or "").strip().replace(",", "").replace("$", "")
    if not text or text in {"-", "NA", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S CST"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_million_twd(text: object) -> float | None:
    raw = str(text or "")
    match = re.search(r"([0-9,]+(?:\.\d+)?)", raw)
    return parse_number(match.group(1)) if match else None


def split_h3_sections(markdown: str) -> list[str]:
    matches = list(H3_RE.finditer(markdown))
    if not matches:
        return []
    sections: list[str] = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        sections.append(markdown[match.start():end].strip())
    return sections


def parse_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_valuation(financial_md: str, profile: dict[str, Any]) -> dict[str, Any] | None:
    match = VALUATION_RE.search(financial_md)
    if not match:
        return None
    section = ""
    for candidate in split_h3_sections(financial_md):
        if candidate.startswith("### 估值指標"):
            section = candidate
            break
    table_lines = [line for line in section.splitlines() if line.strip().startswith("|")]
    metrics: dict[str, float] = {}
    if len(table_lines) >= 3:
        headers = parse_row(table_lines[0])
        values = parse_row(table_lines[2])
        for header, value in zip(headers, values):
            key = METRIC_KEYS.get(header)
            number = parse_number(value)
            if key and number is not None:
                metrics[key] = number
    valuation = {
        "as_of": (match.group("as_of") or "").strip(),
        "currency": "TWD",
        "price": parse_number(match.group("price")),
        "ttm_period_end": (match.group("ttm") or "").strip(),
        "forward_period_end": (match.group("forward") or "").strip(),
        "market_cap_m_twd": parse_million_twd(profile.get("market_cap")),
        "enterprise_value_m_twd": parse_million_twd(profile.get("enterprise_value")),
        "metrics": metrics,
    }
    return valuation


def load_consensus(path: Path) -> dict[str, list[dict[str, str]]]:
    by_stock: dict[str, list[dict[str, str]]] = {}
    if not path.is_file():
        return by_stock
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            stock = str(row.get("stock_code", "")).strip()
            if stock:
                by_stock.setdefault(stock, []).append(row)
    return by_stock


def source_rank(row: dict[str, str]) -> tuple[int, date, str]:
    source = row.get("source", "")
    source_bonus = 0 if source == "Yahoo.Finance.latest" else 1 if source == "Yahoo.Finance.history" else 2
    return (source_bonus, parse_date(row.get("forecast_asof_date")) or date.min, source)


def latest(rows: list[dict[str, str]], *, metric: str, source_prefix: str | None = None, fiscal_year: str = "", period_offset: str = "") -> dict[str, str] | None:
    candidates = []
    for row in rows:
        if row.get("metric") != metric or row.get("period_type") != "annual":
            continue
        if source_prefix and not row.get("source", "").startswith(source_prefix):
            continue
        if fiscal_year and row.get("fiscal_year") != fiscal_year:
            continue
        if period_offset and row.get("period_offset") != period_offset:
            continue
        if parse_number(row.get("value")) is None:
            continue
        candidates.append(row)
    if not candidates:
        return None
    return max(candidates, key=lambda r: (parse_date(r.get("forecast_asof_date")) or date.min, -source_rank(r)[0]))


def pct_diff(primary: float | None, cross: float | None) -> float | None:
    if primary is None or cross in (None, 0):
        return None
    return (primary - cross) / cross * 100.0


def consensus_item(rows: list[dict[str, str]], metric: str, period_offset: str) -> dict[str, Any] | None:
    primary = latest(rows, metric=metric, source_prefix="Yahoo.Finance", period_offset=period_offset)
    fiscal_year = primary.get("fiscal_year", "") if primary else ""
    cross = latest(rows, metric=metric, source_prefix="FactSet", fiscal_year=fiscal_year) if fiscal_year else None
    if not primary and not cross:
        return None
    primary_value = parse_number(primary.get("value")) if primary else None
    cross_value = parse_number(cross.get("value")) if cross else None
    unit = (primary or cross or {}).get("unit")
    high = parse_number((cross or {}).get("high"))
    low = parse_number((cross or {}).get("low"))
    median = parse_number((cross or {}).get("median"))
    if metric == "revenue" and unit == "TWD":
        if primary_value is not None:
            primary_value = primary_value / 1_000_000.0
        if cross_value is not None:
            cross_value = cross_value / 1_000_000.0
        if high is not None:
            high = high / 1_000_000.0
        if low is not None:
            low = low / 1_000_000.0
        if median is not None:
            median = median / 1_000_000.0
        unit = "百萬台幣"
    difference = pct_diff(primary_value, cross_value)
    if primary and primary.get("confidence") == "low":
        confidence = "low"
    elif not cross:
        confidence = "medium"
    elif difference is not None and abs(difference) > 25:
        confidence = "low"
    elif difference is not None and abs(difference) > 10:
        confidence = "medium"
    else:
        confidence = "high"
    return {
        "metric": metric,
        "period_type": "annual",
        "period_offset": period_offset,
        "fiscal_year": fiscal_year or (cross.get("fiscal_year", "") if cross else ""),
        "primary_value": primary_value,
        "primary_source": primary.get("source") if primary else None,
        "primary_as_of": primary.get("forecast_asof_date") if primary else None,
        "cross_check_value": cross_value,
        "cross_check_source": cross.get("source") if cross else None,
        "cross_check_as_of": cross.get("forecast_asof_date") if cross else None,
        "difference_pct": difference,
        "unit": unit,
        "analyst_count": parse_number((cross or {}).get("analyst_count")),
        "high": high,
        "low": low,
        "median": median,
        "confidence": confidence,
    }


def build_consensus(rows: list[dict[str, str]]) -> dict[str, Any]:
    items = [item for item in [
        consensus_item(rows, "eps", "0y"),
        consensus_item(rows, "eps", "1y"),
        consensus_item(rows, "revenue", "0y"),
        consensus_item(rows, "revenue", "1y"),
    ] if item]
    target = latest(rows, metric="target_price", source_prefix="FactSet")
    target_price = parse_number(target.get("value")) if target else None
    as_of_dates = [parse_date(item.get("primary_as_of")) for item in items if item.get("primary_as_of")]
    latest_as_of = max([d for d in as_of_dates if d], default=None)
    return {
        "normalized_source": "data/market_expectations/normalized_consensus.csv",
        "primary_source": "Yahoo.Finance",
        "cross_check_source": "FactSet",
        "as_of": latest_as_of.isoformat() if latest_as_of else None,
        "items": items,
        "target_price": {
            "value": target_price,
            "source": target.get("source") if target else None,
            "as_of": target.get("forecast_asof_date") if target else None,
            "analyst_count": parse_number(target.get("analyst_count")) if target else None,
        } if target_price is not None else None,
    }


def add_derived(valuation: dict[str, Any]) -> None:
    price = valuation.get("price")
    market_cap = valuation.get("market_cap_m_twd")
    consensus = valuation.get("consensus", {})
    derived: dict[str, Any] = {}
    for item in consensus.get("items", []) or []:
        metric = item.get("metric")
        offset = item.get("period_offset")
        value = item.get("primary_value")
        if metric == "eps" and offset == "1y" and price and value:
            derived["forward_pe_consensus"] = price / value
            derived["forward_pe_fiscal_year"] = item.get("fiscal_year")
        if metric == "revenue" and offset == "1y" and market_cap and value:
            derived["forward_ps_consensus"] = market_cap / value
            derived["forward_ps_fiscal_year"] = item.get("fiscal_year")
    if derived:
        valuation["derived_consensus_metrics"] = derived


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-dir", default=str(DEFAULT_JSON_DIR))
    parser.add_argument("--consensus", default=str(DEFAULT_CONSENSUS))
    parser.add_argument("--ticker")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    consensus = load_consensus(Path(args.consensus))
    json_dir = Path(args.json_dir)
    paths = [json_dir / f"{args.ticker}.json"] if args.ticker else sorted(json_dir.glob("*.json"))
    updated = skipped = 0
    for path in paths:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        financial_md = str(data.get("source_text", {}).get("financial_md", ""))
        valuation = parse_valuation(financial_md, data.get("profile", {}) or {})
        if not valuation:
            skipped += 1
            continue
        ticker = str(data.get("ticker") or path.stem)
        valuation["consensus"] = build_consensus(consensus.get(ticker, []))
        add_derived(valuation)
        data.setdefault("financials", {})["valuation"] = valuation
        if not args.dry_run:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    print(f"Updated: {updated} | Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
