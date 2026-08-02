"""
build_themes.py — Generate thematic investment screens from wikilink graph.

Scans all ticker reports for wikilinks, groups companies by theme (technology,
material, application), and generates markdown pages showing the full value chain
for each theme.

Usage:
  python scripts/build_themes.py              # Rebuild all themes
  python scripts/build_themes.py --list       # List available themes
  python scripts/build_themes.py "CoWoS"      # Rebuild single theme

Output: output/themes/ folder with one .md per theme.
"""

import json
import os
import re
import sys
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "Pilot_Reports")
THEMES_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "themes")
OUTPUT_THEMES_DIR = os.path.join(PROJECT_ROOT, "output", "themes")


def safe_theme_filename(tag):
    return tag.replace(" ", "_").replace("/", "_")


def load_theme_definitions():
    """Load curated theme definitions from data/themes/*.json."""
    if not os.path.isdir(THEMES_DATA_DIR):
        raise FileNotFoundError(f"Theme data directory not found: {THEMES_DATA_DIR}")

    themes = {}
    for filename in sorted(os.listdir(THEMES_DATA_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(THEMES_DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            definition = json.load(f)

        tag = definition.get("tag")
        if not tag:
            raise ValueError(f"Missing 'tag' in {path}")
        for required in ("name", "desc"):
            if not definition.get(required):
                raise ValueError(f"Missing '{required}' in {path}")

        definition.setdefault("related", [])
        definition.setdefault("category", "未分類")
        definition.setdefault("index_categories", [definition["category"]])
        definition.setdefault("order", 9990)
        themes[tag] = definition

    return dict(
        sorted(themes.items(), key=lambda item: (item[1].get("order", 9990), item[0]))
    )


def scan_wikilinks():
    """Scan all reports, return {wikilink: [(ticker, company, sector, context)]}."""
    wl_map = defaultdict(list)

    for sector_dir in os.listdir(REPORTS_DIR):
        sector_path = os.path.join(REPORTS_DIR, sector_dir)
        if not os.path.isdir(sector_path):
            continue
        for f in os.listdir(sector_path):
            if not f.endswith(".md"):
                continue
            m = re.match(r"^(\d{4})_(.+)\.md$", f)
            if not m:
                continue
            ticker, company = m.group(1), m.group(2)
            filepath = os.path.join(sector_path, f)
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()

            # Split content into sections for context
            sections = {
                "desc": "",
                "supply_chain": "",
                "customers": "",
            }
            parts = re.split(r"## ", content)
            for part in parts:
                if part.startswith("業務簡介"):
                    sections["desc"] = part
                elif part.startswith("供應鏈位置"):
                    sections["supply_chain"] = part
                elif part.startswith("主要客戶及供應商"):
                    sections["customers"] = part

            # Find all wikilinks in non-financial sections
            text = sections["desc"] + sections["supply_chain"] + sections["customers"]
            for wl in set(re.findall(r"\[\[([^\]]+)\]\]", text)):
                # Determine role from context
                role = "related"
                if wl in sections["supply_chain"]:
                    if "上游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "upstream"
                    elif "下游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "downstream"
                    elif "中游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "midstream"

                wl_map[wl].append(
                    {
                        "ticker": ticker,
                        "company": company,
                        "sector": sector_dir,
                        "role": role,
                    }
                )

    return wl_map


def build_theme_page(theme_tag, theme_def, wl_map):
    """Build a single theme markdown page."""
    entries = wl_map.get(theme_tag, [])
    if not entries:
        return None

    lines = []
    lines.append(f"# {theme_def['name']}")
    lines.append("")
    lines.append(f"> {theme_def['desc']}")
    lines.append("")
    lines.append(f"**涵蓋公司數:** {len(entries)}")
    lines.append("")

    # Related themes
    related = theme_def.get("related", [])
    related_with_counts = []
    for r in related:
        count = len(wl_map.get(r, []))
        if count > 0:
            related_with_counts.append(f"[[{r}]] ({count})")
    if related_with_counts:
        lines.append(f"**相關主題:** {' | '.join(related_with_counts)}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Group by role
    upstream = [e for e in entries if e["role"] == "upstream"]
    midstream = [e for e in entries if e["role"] == "midstream"]
    downstream = [e for e in entries if e["role"] == "downstream"]
    other = [e for e in entries if e["role"] == "related"]

    def format_entries(entries):
        # Group by sector
        by_sector = defaultdict(list)
        for e in entries:
            by_sector[e["sector"]].append(e)
        result = []
        for sector in sorted(by_sector.keys()):
            items = sorted(by_sector[sector], key=lambda x: x["ticker"])
            for item in items:
                result.append(
                    f"- **{item['ticker']} {item['company']}** ({sector})"
                )
        return result

    if upstream:
        lines.append(f"## 上游 ({len(upstream)})")
        lines.append("")
        lines.extend(format_entries(upstream))
        lines.append("")

    if midstream:
        lines.append(f"## 中游 ({len(midstream)})")
        lines.append("")
        lines.extend(format_entries(midstream))
        lines.append("")

    if downstream:
        lines.append(f"## 下游 ({len(downstream)})")
        lines.append("")
        lines.extend(format_entries(downstream))
        lines.append("")

    if other:
        lines.append(f"## 相關公司 ({len(other)})")
        lines.append("")
        lines.extend(format_entries(other))
        lines.append("")

    return "\n".join(lines)


def build_index(themes_built, theme_definitions):
    """Build output/themes/README.md index."""
    lines = []
    lines.append("# Thematic Investment Screens")
    lines.append("")
    lines.append("> Auto-generated supply chain maps for thematic investing.")
    lines.append("> Regenerate: `python scripts/build_themes.py`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group by category from data/themes/*.json so the index follows the catalog.
    grouped = defaultdict(list)
    for tag, definition in theme_definitions.items():
        if tag not in themes_built:
            continue
        for category in definition.get("index_categories", [definition.get("category", "未分類")]):
            grouped[category].append((tag, definition))

    categories = sorted(
        grouped.items(),
        key=lambda item: min(defn.get("order", 9990) for _, defn in item[1]),
    )

    for cat_name, items in categories:
        lines.append(f"## {cat_name}")
        lines.append("")
        for tag, definition in sorted(
            items, key=lambda item: (item[1].get("order", 9990), item[0])
        ):
            count = themes_built[tag]
            safe_name = safe_theme_filename(tag)
            lines.append(f"- [{tag}]({safe_name}.md) — {count} 家公司")
        lines.append("")

    return "\n".join(lines)


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    os.makedirs(OUTPUT_THEMES_DIR, exist_ok=True)
    theme_definitions = load_theme_definitions()

    args = sys.argv[1:]

    if "--list" in args:
        for tag, defn in theme_definitions.items():
            print(f"  {tag}: {defn['name']}")
        return

    print("Scanning wikilinks across all reports...")
    wl_map = scan_wikilinks()
    print(f"Found {len(wl_map)} unique wikilinks.\n")

    # Filter to requested theme or build all
    if args and args[0] != "--list":
        themes_to_build = {args[0]: theme_definitions.get(args[0])}
        if not themes_to_build[args[0]]:
            print(f"Theme '{args[0]}' not in data/themes. Use --list to see available themes.")
            return
    else:
        themes_to_build = theme_definitions

    themes_built = {}
    for tag, defn in themes_to_build.items():
        page = build_theme_page(tag, defn, wl_map)
        if page:
            safe_name = safe_theme_filename(tag)
            filepath = os.path.join(OUTPUT_THEMES_DIR, f"{safe_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(page)
            count = len(wl_map.get(tag, []))
            themes_built[tag] = count
            print(f"  {tag}: {count} companies -> {safe_name}.md")

    # Build index
    index = build_index(themes_built, theme_definitions)
    with open(os.path.join(OUTPUT_THEMES_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(index)

    print(f"\nDone. Generated {len(themes_built)} theme pages in output/themes/")


if __name__ == "__main__":
    main()
