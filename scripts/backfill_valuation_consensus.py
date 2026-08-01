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
DEFAULT_GOODINFO_ANNUAL = ROOT.parent / "Python-Actions.GoodInfo.Analyzer/data/stage1_raw/raw_performance.csv"
DEFAULT_GOODINFO_QUARTERLY = ROOT.parent / "Python-Actions.GoodInfo.Analyzer/data/stage1_raw/raw_performance1.csv"
DEFAULT_INVESTOR_CONFERENCE_DATA = ROOT.parent / "InvestorConference/data"

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



def quarter_to_date(period: object) -> str:
    text = str(period or "").strip()
    match = re.match(r"^(\d{4})Q([1-4])$", text)
    if not match:
        return ""
    year = match.group(1)
    month_day = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}[match.group(2)]
    return f"{year}-{month_day}"


def eps_source_rank(row: dict[str, Any]) -> int:
    source = str(row.get("source") or "")
    if source.startswith("InvestorConference"):
        return 0
    if source.startswith("MOPS"):
        return 1
    if source.startswith("GoodInfo"):
        return 2
    return 9


def merge_eps_entries(existing: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_period: dict[str, dict[str, Any]] = {}
    for row in [*existing, *new_rows]:
        period = str(row.get("period", "")).strip()
        eps = parse_number(row.get("eps_twd"))
        if not period or eps is None:
            continue
        normalized = dict(row)
        normalized["eps_twd"] = eps
        current = by_period.get(period)
        if current is None or eps_source_rank(normalized) < eps_source_rank(current):
            by_period[period] = normalized
    return sorted(by_period.values(), key=lambda r: r["period"], reverse=True)


def load_actual_eps(annual_path: Path, quarterly_path: Path) -> dict[str, dict[str, Any]]:
    by_stock: dict[str, dict[str, Any]] = {}

    if annual_path.is_file():
        with annual_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ticker = str(row.get("stock_code", "")).strip()
                year = str(row.get("年度", "")).strip()
                eps = parse_number(row.get("eps_元_稅後_eps"))
                if not ticker or not re.match(r"^\d{4}$", year) or eps is None:
                    continue
                entry = by_stock.setdefault(ticker, {"source": "GoodInfo.Analyzer", "annual": [], "quarterly": []})
                entry["annual"].append({
                    "period": f"{year}-12-31",
                    "eps_twd": eps,
                    "eps_type": "after_tax",
                    "source": "GoodInfo.Analyzer",
                    "source_file": str(annual_path.relative_to(ROOT.parent)),
                })

    if quarterly_path.is_file():
        with quarterly_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ticker = str(row.get("stock_code", "")).strip()
                period = quarter_to_date(row.get("季度"))
                eps = parse_number(row.get("eps_元_稅後_eps"))
                if not ticker or not period or eps is None:
                    continue
                entry = by_stock.setdefault(ticker, {"source": "GoodInfo.Analyzer", "annual": [], "quarterly": []})
                entry["quarterly"].append({
                    "period": period,
                    "eps_twd": eps,
                    "eps_type": "after_tax",
                    "source": "GoodInfo.Analyzer",
                    "source_file": str(quarterly_path.relative_to(ROOT.parent)),
                })

    for entry in by_stock.values():
        entry["annual"] = merge_eps_entries([], entry.get("annual", []))
        entry["quarterly"] = merge_eps_entries([], entry.get("quarterly", []))
    return by_stock


def file_period_to_date(year: str, quarter: str) -> str:
    month_day = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}[quarter]
    return f"{year}-{month_day}"


def extract_release_date(text: str) -> str | None:
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}", text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(0), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def parse_investorconference_earnings_release(path: Path) -> dict[str, Any] | None:
    match = re.search(r"(?P<ticker>[^/]+)_(?P<year>20\d{2})_q(?P<quarter>[1-4])_earnings_release\.md$", path.name, re.IGNORECASE)
    if not match:
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    eps_match = re.search(r"diluted earnings per share of NT\$\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if not eps_match:
        eps_match = re.search(r"EPS of NT\$\s*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    eps = parse_number(eps_match.group(1)) if eps_match else None
    if eps is None:
        return None
    revenue_match = re.search(r"consolidated revenue of\s+NT\$\s*([0-9,]+(?:\.[0-9]+)?)\s*billion", text, re.IGNORECASE)
    net_income_match = re.search(r"net income of\s+NT\$\s*([0-9,]+(?:\.[0-9]+)?)\s*billion", text, re.IGNORECASE)
    row = {
        "period": file_period_to_date(match.group("year"), match.group("quarter")),
        "eps_twd": eps,
        "eps_type": "diluted",
        "source": "InvestorConference.earnings_release",
        "source_file": str(path.relative_to(ROOT.parent)),
        "released_at": extract_release_date(text),
    }
    revenue = parse_number(revenue_match.group(1)) if revenue_match else None
    net_income = parse_number(net_income_match.group(1)) if net_income_match else None
    if revenue is not None:
        row["revenue_m_twd"] = revenue * 1000
    if net_income is not None:
        row["net_income_m_twd"] = net_income * 1000
    return {"ticker": match.group("ticker"), "row": row}


def load_investorconference_actual_eps(data_root: Path) -> dict[str, dict[str, Any]]:
    by_stock: dict[str, dict[str, Any]] = {}
    if not data_root.is_dir():
        return by_stock
    for path in sorted(data_root.glob("*/*_earnings_release.md")):
        parsed = parse_investorconference_earnings_release(path)
        if not parsed:
            continue
        ticker = str(parsed["ticker"]).strip()
        if not ticker.isdigit():
            continue
        entry = by_stock.setdefault(ticker, {"source": "InvestorConference", "annual": [], "quarterly": []})
        entry["quarterly"].append(parsed["row"])
    for entry in by_stock.values():
        entry["quarterly"] = merge_eps_entries([], entry.get("quarterly", []))
    return by_stock


def merge_actual_eps_sources(*sources: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source in sources:
        for ticker, payload in source.items():
            entry = merged.setdefault(ticker, {"source": "merged_actual_eps", "annual": [], "quarterly": []})
            entry["annual"] = merge_eps_entries(entry.get("annual", []), payload.get("annual", []))
            entry["quarterly"] = merge_eps_entries(entry.get("quarterly", []), payload.get("quarterly", []))
    return merged

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
    enterprise_value = valuation.get("enterprise_value_m_twd")
    metrics = valuation.get("metrics", {}) or {}

    derived_inputs: dict[str, Any] = {}
    pe_ttm = metrics.get("pe_ttm")
    ps_ttm = metrics.get("ps_ttm")
    pb = metrics.get("pb")
    ev_ebitda_ttm = metrics.get("ev_ebitda_ttm")
    if price and pe_ttm:
        derived_inputs["ttm_eps_twd"] = price / pe_ttm
    if market_cap and ps_ttm:
        derived_inputs["ttm_revenue_m_twd"] = market_cap / ps_ttm
    if market_cap and pb:
        derived_inputs["book_value_m_twd"] = market_cap / pb
    if enterprise_value and ev_ebitda_ttm:
        derived_inputs["ttm_ebitda_m_twd"] = enterprise_value / ev_ebitda_ttm
    if derived_inputs:
        derived_inputs["source"] = "derived_from_market_valuation_multiples"
        valuation["derived_inputs"] = derived_inputs

    consensus = valuation.get("consensus", {})
    derived: dict[str, Any] = {}
    for item in consensus.get("items", []) or []:
        metric = item.get("metric")
        offset = item.get("period_offset")
        value = item.get("primary_value")
        if metric == "eps" and offset == "1y" and price and value:
            derived["forward_pe_consensus"] = price / value
            derived["forward_pe_fiscal_year"] = item.get("fiscal_year")
            derived["forward_eps_twd"] = value
        if metric == "revenue" and offset == "1y" and market_cap and value:
            derived["forward_ps_consensus"] = market_cap / value
            derived["forward_ps_fiscal_year"] = item.get("fiscal_year")
            derived["forward_revenue_m_twd"] = value
    if derived:
        valuation["derived_consensus_metrics"] = derived


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-dir", default=str(DEFAULT_JSON_DIR))
    parser.add_argument("--consensus", default=str(DEFAULT_CONSENSUS))
    parser.add_argument("--goodinfo-annual", default=str(DEFAULT_GOODINFO_ANNUAL))
    parser.add_argument("--goodinfo-quarterly", default=str(DEFAULT_GOODINFO_QUARTERLY))
    parser.add_argument("--investorconference-data", default=str(DEFAULT_INVESTOR_CONFERENCE_DATA))
    parser.add_argument("--ticker")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    consensus = load_consensus(Path(args.consensus))
    actual_eps = merge_actual_eps_sources(
        load_actual_eps(Path(args.goodinfo_annual), Path(args.goodinfo_quarterly)),
        load_investorconference_actual_eps(Path(args.investorconference_data)),
    )
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
        financials = data.setdefault("financials", {})
        financials["valuation"] = valuation
        if ticker in actual_eps:
            financials["actual_eps"] = actual_eps[ticker]
        if not args.dry_run:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    print(f"Updated: {updated} | Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
