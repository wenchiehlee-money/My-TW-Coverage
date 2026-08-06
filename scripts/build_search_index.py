"""Build a static full-text search index for the docsify site.

Docsify's built-in search plugin only indexes pages reachable from
_sidebar.md, which this project keeps intentionally empty (navigation is
wikilink-driven). That means the default search box never sees the 1,700+
company reports or the theme pages. This script walks the rendered output
and produces search_data.json, a compact {path, title, ticker, text} array
that index.html loads and indexes client-side with lunr.js.

Run after scripts/build_themes.py / render step, or via
generate_docsify_assets.py which calls this at the end.
"""
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANY_DIR = os.path.join(BASE_DIR, "output", "themes", "company")
THEMES_DIR = os.path.join(BASE_DIR, "output", "themes")
OUTPUT_PATH = os.path.join(BASE_DIR, "search_data.json")

# Financial tables are numeric noise for full-text search and bloat the
# index; only index the narrative sections above them.
FINANCIALS_HEADING = re.compile(r"^##\s*財務概況", re.MULTILINE)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
BADGE_LINK_RE = re.compile(r"\[!\[([^\]]*)\]\([^)]*\)\]\([^)]*\)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MD_SYMBOLS_RE = re.compile(r"[#*`>_~|-]")
WS_RE = re.compile(r"\s+")


def markdown_to_text(md: str) -> str:
    text = BADGE_LINK_RE.sub(lambda m: m.group(1), md)
    text = WIKILINK_RE.sub(lambda m: m.group(1), text)
    text = IMAGE_RE.sub("", text)
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = MD_SYMBOLS_RE.sub(" ", text)
    text = WS_RE.sub(" ", text)
    return text.strip()


def extract_title(md: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    if match:
        return markdown_to_text(match.group(1))
    return fallback


def build_company_docs() -> list:
    docs = []
    if not os.path.isdir(COMPANY_DIR):
        return docs
    for fname in sorted(os.listdir(COMPANY_DIR)):
        if not fname.endswith(".md") or fname == "README.md":
            continue
        match = re.match(r"^(\d+[A-Za-z]*(?:\.[A-Za-z]+)?)[-_](.+)\.md$", fname)
        ticker = match.group(1) if match else ""
        company = match.group(2) if match else fname[:-3]
        path = os.path.join(COMPANY_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        split = FINANCIALS_HEADING.split(content, maxsplit=1)
        narrative = split[0] if split else content
        docs.append({
            "path": f"output/themes/company/{fname}",
            "title": extract_title(content, f"{ticker} {company}".strip()),
            "ticker": ticker,
            "text": markdown_to_text(narrative),
        })
    return docs


def build_theme_docs() -> list:
    docs = []
    if not os.path.isdir(THEMES_DIR):
        return docs
    for fname in sorted(os.listdir(THEMES_DIR)):
        if not fname.endswith(".md") or fname == "README.md":
            continue
        path = os.path.join(THEMES_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({
            "path": f"output/themes/{fname}",
            "title": extract_title(content, fname[:-3]),
            "ticker": "",
            "text": markdown_to_text(content),
        })
    return docs


def build_root_readme_doc() -> list:
    path = os.path.join(THEMES_DIR, "README.md")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [{
        "path": "output/themes/README.md",
        "title": extract_title(content, "投資主題總覽"),
        "ticker": "",
        "text": markdown_to_text(content),
    }]


def main():
    docs = build_root_readme_doc() + build_theme_docs() + build_company_docs()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"Generated {OUTPUT_PATH} with {len(docs)} documents ({size_mb:.2f} MB).")


if __name__ == "__main__":
    main()
