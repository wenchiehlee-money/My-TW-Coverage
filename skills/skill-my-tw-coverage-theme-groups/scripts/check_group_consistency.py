#!/usr/bin/env python3
"""Cross-check a theme's data/themes/*.json `competitive_groups` against each
company's own canonical `relationships.competitors` in data/enrichment_all/*.json.

This is a pure comparison tool. It never edits data — it only reports where the
two sources disagree so a human (or an agent following
skill-my-tw-coverage-theme-groups/SKILL.md) can decide how to reconcile them.

Usage:
  python3 skills/skill-my-tw-coverage-theme-groups/scripts/check_group_consistency.py --theme "AI 伺服器"
  python3 skills/skill-my-tw-coverage-theme-groups/scripts/check_group_consistency.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def find_coverage_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (
            (candidate / "data" / "themes").is_dir()
            and (candidate / "data" / "enrichment_all").is_dir()
            and (candidate / "scripts" / "build_themes.py").is_file()
        ):
            return candidate
    raise SystemExit("Cannot find My-TW-Coverage root. Run from the repository root or a subdirectory.")


ROOT = find_coverage_root()
sys.path.insert(0, str(ROOT))

from scripts.build_themes import (  # noqa: E402
    ENRICHMENT_JSON_DIR,
    load_company_json_files,
    load_theme_definitions,
    scan_theme_links,
)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def normalized_key(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", value).lower()


def build_name_index() -> dict[str, str]:
    """Map company-name-ish strings (name, ticker, normalized variants) -> ticker."""
    index: dict[str, str] = {}
    for path in load_company_json_files():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ticker = str(data.get("ticker") or "").strip()
        company = str(data.get("company_name") or "").strip()
        if not ticker or not company:
            continue
        for alias in (ticker, company):
            index.setdefault(alias, ticker)
            index.setdefault(normalized_key(alias), ticker)
        for suffix in ("-KY", "-KY創", "-創"):
            if company.endswith(suffix):
                base = company[: -len(suffix)]
                index.setdefault(base, ticker)
                index.setdefault(normalized_key(base), ticker)
    return index


def resolve_ticker(name: str, name_index: dict[str, str]) -> str | None:
    name = name.strip()
    if not name:
        return None
    return name_index.get(name) or name_index.get(normalized_key(name))


def load_competitor_tickers(ticker: str, name_index: dict[str, str]) -> tuple[set[str], list[str]]:
    """Return (resolved competitor tickers, unresolved raw entity names)."""
    path = ENRICHMENT_JSON_DIR / f"{ticker}.json"
    if not path.exists():
        return set(), []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set(), []
    relationships = data.get("relationships", {}) if isinstance(data.get("relationships"), dict) else {}
    resolved: set[str] = set()
    unresolved: list[str] = []
    for item in relationships.get("competitors", []) or []:
        if not isinstance(item, dict):
            continue
        entities = list(item.get("entities") or [])
        entities.extend(WIKILINK_RE.findall(str(item.get("text") or "")))
        for entity in entities:
            entity = str(entity).strip()
            if not entity:
                continue
            resolved_ticker = resolve_ticker(entity, name_index)
            if resolved_ticker:
                resolved.add(resolved_ticker)
            else:
                unresolved.append(entity)
    return resolved, unresolved


def check_theme(tag: str, theme_def: dict[str, Any], theme_map: dict[str, list[dict[str, Any]]], name_index: dict[str, str]) -> list[str]:
    report: list[str] = []
    entries = theme_map.get(tag, [])
    if not entries:
        return report
    theme_tickers = {str(e.get("ticker") or "") for e in entries}
    company_by_ticker = {str(e.get("ticker") or ""): str(e.get("company") or "") for e in entries}

    competitive_groups = theme_def.get("competitive_groups", []) or []
    group_by_ticker: dict[str, str] = {}
    group_members: dict[str, set[str]] = {}
    for group in competitive_groups:
        if not isinstance(group, dict):
            continue
        name = str(group.get("name") or "").strip()
        if not name:
            continue
        tickers = {str(t).strip() for t in group.get("tickers", []) or []}
        group_members[name] = tickers
        for t in tickers:
            group_by_ticker[t] = name

    if not group_by_ticker:
        return report

    section: list[str] = []

    # 1. Group members whose canonical competitors point to a ticker present in
    #    this theme's dataset but NOT in the same competitive_group.
    for group_name, tickers in group_members.items():
        for ticker in sorted(tickers):
            competitors, _unresolved = load_competitor_tickers(ticker, name_index)
            outside = competitors & theme_tickers - tickers - {ticker}
            for other in sorted(outside):
                other_group = group_by_ticker.get(other, "(未分組/fallback)")
                company = company_by_ticker.get(ticker, ticker)
                other_company = company_by_ticker.get(other, other)
                section.append(
                    f"  - {ticker} {company} 的 relationships.competitors 列了 {other} {other_company}，"
                    f"但 {other} 目前在「{other_group}」，不在同組「{group_name}」"
                )

    # 2. Group members that DO have canonical competitor data, but none of it
    #    overlaps this group (informational — may mean relationships.competitors
    #    is incomplete, or may mean the grouping needs a second look). Tickers
    #    with a completely empty relationships.competitors are skipped — there
    #    is nothing to compare, so flagging them would be pure noise.
    for group_name, tickers in group_members.items():
        if len(tickers) < 2:
            continue
        for ticker in sorted(tickers):
            competitors, unresolved = load_competitor_tickers(ticker, name_index)
            if not competitors and not unresolved:
                continue
            if not (competitors & (tickers - {ticker})):
                company = company_by_ticker.get(ticker, ticker)
                section.append(
                    f"  - {ticker} {company} 有列 relationships.competitors，但沒有一個是「{group_name}」的同組成員"
                    f"（可能是 relationships.competitors 尚未補齊，不一定代表分組錯）"
                )

    if section:
        report.append(f"## {tag}")
        report.extend(section)
        report.append("")
    return report


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", help="Theme tag, e.g. 'AI 伺服器'")
    parser.add_argument("--all", action="store_true", help="Check every theme with competitive_groups")
    args = parser.parse_args()

    if not args.theme and not args.all:
        parser.error("Pass --theme <tag> or --all")

    theme_definitions = load_theme_definitions()
    theme_map = scan_theme_links(theme_definitions)
    name_index = build_name_index()

    tags = list(theme_definitions.keys()) if args.all else [args.theme]

    output: list[str] = []
    for tag in tags:
        theme_def = theme_definitions.get(tag)
        if not theme_def:
            print(f"Theme '{tag}' not found in data/themes.")
            return 1
        output.extend(check_theme(tag, theme_def, theme_map, name_index))

    if not output:
        print("No inconsistencies found between competitive_groups and relationships.competitors.")
        return 0

    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
