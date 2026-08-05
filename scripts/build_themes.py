#!/usr/bin/env python3
"""Generate thematic investment screens from canonical enrichment JSON.

Theme definitions live in data/themes/*.json. Company participation comes from
reviewed data/enrichment_all/*.json content, not from archived Pilot_Reports.

Usage:
  python scripts/build_themes.py              # Rebuild all themes
  python scripts/build_themes.py --list       # List available themes
  python scripts/build_themes.py "CoWoS"      # Rebuild single theme

Output: output/themes/ folder with one .md per theme.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENRICHMENT_JSON_DIR = PROJECT_ROOT / "data" / "enrichment_all"
THEMES_DATA_DIR = PROJECT_ROOT / "data" / "themes"
OUTPUT_THEMES_DIR = PROJECT_ROOT / "output" / "themes"
COMPANY_OUTPUT_DIR = PROJECT_ROOT / "output" / "enrichment_all_rendered"
DEFAULT_BIZTRENDS_ROOT = PROJECT_ROOT.parent / "biztrends.TW"
IC_TPEX_DIR = DEFAULT_BIZTRENDS_ROOT / "data" / "ic.tpex.org.tw"
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

ENTITY_ALIAS_BY_COMPANY = {
    "中華電": ["中華電信"],
    "台灣大": ["台灣大哥大"],
    "遠傳": ["遠傳電信"],
    "世界": ["世界先進"],
    "光寶科": ["光寶科技"],
    "台達電": ["台達電子"],
    "華碩": ["ASUSTeK Computer", "ASUS"],
    "仁寶": ["Compal Electronics", "Compal"],
    "技嘉": ["Gigabyte Technology", "GIGABYTE"],
    "臻鼎-KY": ["臻鼎"],
    "鈺齊-KY": ["鈺齊"],
    "鴻華先進-創": ["鴻華先進"],
    "友達": ["友達光電"],
    "群創": ["群創光電"],
    "日月光投控": ["日月光"],
    "LINEPAY": ["LINE Pay"],
}



def safe_theme_filename(tag: str) -> str:
    return tag.replace(" ", "_").replace("/", "_") + ".md"


def theme_output_filename(theme_def: dict[str, Any]) -> str:
    render = theme_def.get("render", {}) if isinstance(theme_def.get("render"), dict) else {}
    filename = str(render.get("output_filename") or "").strip()
    return filename or safe_theme_filename(str(theme_def.get("tag", "")).strip())


def badge_label_text(label: str) -> str:
    return quote(label.replace("-", "--"), safe="")


def render_badge_link(label: str, target: str, color: str = "blue", *, quote_target: bool = True) -> str:
    badge_label = str(label).strip()
    badge_color = str(color or "blue").strip()
    image = f"https://img.shields.io/badge/{badge_label_text(badge_label)}-{quote(badge_color, safe='')}"
    href = quote(target) if quote_target else target
    return f"[![{badge_label}]({image})]({href})"


def render_theme_badge(theme_def: dict[str, Any], href: str | None = None, label: str | None = None) -> str:
    render = theme_def.get("render", {}) if isinstance(theme_def.get("render"), dict) else {}
    badge_label = str(label or render.get("badge_label") or theme_def.get("tag") or "Theme").strip()
    color = str(render.get("badge_color") or "green").strip()
    target = href or theme_output_filename(theme_def)
    return render_badge_link(badge_label, target, color)


def render_company_badge(label: str, target: str) -> str:
    return render_badge_link(label, target, "blue", quote_target=False)


def normalized_entity_key(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", value).lower()


def extract_self_aliases(data: dict[str, Any], ticker: str) -> set[str]:
    aliases: set[str] = set()
    business = data.get("business", {}) if isinstance(data.get("business"), dict) else {}
    summary = str(business.get("summary") or business.get("business_summary_md") or "")
    ticker_pattern = re.escape(ticker)
    for match in re.finditer(rf"[（(][^）)]*{ticker_pattern}[^）)]*?[\s,，、/：:;；-]*\[\[([^\]]+)\]\](?=[\s,，、/;；）)])[^）)]*[）)]", summary):
        aliases.add(match.group(1).strip())
    start_match = re.match(rf"\s*\[\[([^\]]+)\]\]\s*[（(]\s*{ticker_pattern}\s*[）)]", summary)
    if start_match:
        aliases.add(start_match.group(1).strip())
    return {alias for alias in aliases if alias}


def load_company_badge_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for path in sorted(COMPANY_OUTPUT_DIR.glob("*.md")):
        stem = path.stem
        if "_" not in stem:
            continue
        ticker, company = stem.split("_", 1)
        href = f"company/{quote(path.name)}"
        aliases = {ticker, company, f"{ticker} {company}", f"{ticker}_{company}"}
        aliases.update(ENTITY_ALIAS_BY_COMPANY.get(company, []))
        json_path = ENRICHMENT_JSON_DIR / f"{ticker}.json"
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            aliases.update(extract_self_aliases(data, ticker))
        for suffix in ("-KY", "-KY創", "-創"):
            if company.endswith(suffix):
                aliases.add(company[: -len(suffix)])
        for alias in aliases:
            if alias:
                index.setdefault(alias, (alias, href))
                normalized = normalized_entity_key(alias)
                if normalized:
                    index.setdefault(normalized, (alias, href))
    return index


def render_related_entity(entity: str, company_index: dict[str, tuple[str, str]]) -> str:
    label = str(entity).strip()
    target = company_index.get(label) or company_index.get(normalized_entity_key(label))
    if not target:
        return f"[[{label}]]"
    _, href = target
    return render_company_badge(label, href)


def load_theme_definitions() -> dict[str, dict[str, Any]]:
    """Load curated theme definitions from data/themes/*.json."""
    if not THEMES_DATA_DIR.is_dir():
        raise FileNotFoundError(f"Theme data directory not found: {THEMES_DATA_DIR}")

    themes: dict[str, dict[str, Any]] = {}
    for path in sorted(THEMES_DATA_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            definition = json.load(f)

        tag = str(definition.get("tag", "")).strip()
        if not tag:
            raise ValueError(f"Missing 'tag' in {path}")
        for required in ("id", "name", "desc"):
            if not definition.get(required):
                raise ValueError(f"Missing '{required}' in {path}")

        definition.setdefault("aliases", [tag])
        definition.setdefault("anchor_entities", [])
        definition.setdefault("related_theme_tags", [])
        definition.setdefault("related_entities", [])
        definition.setdefault("category", "未分類")
        definition.setdefault("index_categories", [definition["category"]])
        definition.setdefault("order", 9990)
        definition.setdefault("render", {"output_filename": safe_theme_filename(tag)})
        themes[tag] = definition

    return dict(
        sorted(themes.items(), key=lambda item: (item[1].get("order", 9990), item[0]))
    )


def load_company_json_files(ticker: str | None = None) -> list[Path]:
    if ticker:
        path = ENRICHMENT_JSON_DIR / f"{ticker}.json"
        return [path] if path.exists() else []
    return sorted(ENRICHMENT_JSON_DIR.glob("*.json"))


def plain_context_text(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text).strip()


def profile_sector(data: dict[str, Any]) -> str:
    profile = data.get("profile", {}) if isinstance(data.get("profile"), dict) else {}
    return plain_context_text(profile.get("chain_name") or profile.get("industry") or profile.get("sector") or "")


# GICS/yfinance industry labels (English) used as a fallback grouping key when a
# company has no IC-taxonomy chain_name. Translated so all rendered output stays
# Traditional Chinese per project rule.
GICS_INDUSTRY_ZH: dict[str, str] = {
    "Advertising Agencies": "廣告代理",
    "Aerospace & Defense": "航太與國防",
    "Agricultural Inputs": "農業投入品",
    "Airlines": "航空公司",
    "Aluminum": "鋁業",
    "Apparel Manufacturing": "服飾製造",
    "Apparel Retail": "服飾零售",
    "Asset Management": "資產管理",
    "Auto & Truck Dealerships": "汽車與卡車經銷",
    "Auto Manufacturers": "汽車製造",
    "Auto Parts": "汽車零組件",
    "Banks": "銀行",
    "Banks - Regional": "區域銀行",
    "Beverages - Non-Alcoholic": "非酒精飲料",
    "Biotech - Therapeutics": "生技治療藥物",
    "Biotechnology": "生物科技",
    "Broadcasting": "廣播媒體",
    "Building Materials": "建材",
    "Building Products & Equipment": "建築產品與設備",
    "Business Equipment & Supplies": "商用設備與用品",
    "Capital Markets": "資本市場",
    "Chemicals": "化學",
    "Communication Equipment": "通訊設備",
    "Computer Hardware": "電腦硬體",
    "Conglomerates": "綜合企業",
    "Consulting Services": "顧問服務",
    "Consumer Electronics": "消費性電子",
    "Copper": "銅業",
    "Credit Services": "信用服務",
    "Department Stores": "百貨公司",
    "Drug Manufacturers - Specialty & Generic": "特殊/學名藥製造",
    "Education & Training Services": "教育與訓練服務",
    "Electrical Equipment & Parts": "電氣設備與零件",
    "Electronic Components": "電子零組件",
    "Electronic Gaming & Multimedia": "電子遊戲與多媒體",
    "Electronics & Computer Distribution": "電子與電腦通路",
    "Electronics Distribution": "電子零組件通路",
    "Engineering & Construction": "工程與營造",
    "Entertainment": "娛樂",
    "Farm Products": "農產品",
    "Financial Conglomerates": "金融控股集團",
    "Food Distribution": "食品通路",
    "Footwear & Accessories": "鞋類與配件",
    "Furnishings, Fixtures & Appliances": "家具家飾與家電",
    "Gambling": "博弈",
    "Ground Transportation": "陸上運輸",
    "Health Information Services": "健康資訊服務",
    "Home Improvement Retail": "居家修繕零售",
    "Household & Personal Products": "家用與個人用品",
    "Industrial Computing": "工業電腦",
    "Industrial Distribution": "工業品通路",
    "Information Technology Services": "資訊科技服務",
    "Insurance - Diversified": "綜合保險",
    "Insurance - Life": "人壽保險",
    "Insurance - Property & Casualty": "產物保險",
    "Insurance - Reinsurance": "再保險",
    "Insurance Brokers": "保險經紀",
    "Integrated Freight & Logistics": "綜合貨運與物流",
    "Internet Content & Information": "網路內容與資訊",
    "Internet Retail": "網路零售",
    "Leisure": "休閒",
    "Lodging": "住宿業",
    "Lumber & Wood Production": "木材生產",
    "Marine Shipping": "海運",
    "Medical Devices": "醫療器材",
    "Metal Fabrication": "金屬加工",
    "Oil & Gas Equipment & Services": "油氣設備與服務",
    "Oil & Gas Refining & Marketing": "石油煉製與行銷",
    "Optical Components": "光學元件",
    "Other Electronics": "其他電子產品",
    "Other Industrial Metals & Mining": "其他工業金屬與礦業",
    "Packaged Foods": "包裝食品",
    "Packaging & Containers": "包裝與容器",
    "Personal Services": "個人服務",
    "Pollution & Treatment Controls": "污染防治設備",
    "Publishing": "出版業",
    "Railroads": "鐵路",
    "Real Estate - Development": "不動產開發",
    "Real Estate - Diversified": "綜合不動產",
    "Real Estate Services": "不動產服務",
    "Recreational Vehicles": "休閒車輛",
    "Scientific & Technical Instruments": "科學與技術儀器",
    "Security & Protection Services": "保全與防護服務",
    "Semiconductor Equipment": "半導體設備",
    "Semiconductor Equipment & Materials": "半導體設備與材料",
    "Semiconductor Materials": "半導體材料",
    "Semiconductors": "半導體",
    "Software - Application": "應用軟體",
    "Software - Infrastructure": "基礎架構軟體",
    "Solar": "太陽能",
    "Specialty Business Services": "特殊商業服務",
    "Specialty Chemicals": "特用化學",
    "Specialty Industrial Machinery": "特殊工業機械",
    "Specialty Retail": "特殊零售",
    "Staffing & Employment Services": "人力派遣服務",
    "Steel": "鋼鐵",
    "Telecom Services": "電信服務",
    "Textile Manufacturing": "紡織製造",
    "Thermal Coal": "動力煤",
    "Tools & Accessories": "工具與配件",
    "Trucking": "卡車運輸",
    "Utilities - Regulated Electric": "電力事業(受監管)",
    "Utilities - Regulated Gas": "燃氣事業(受監管)",
    "Utilities - Regulated Water": "自來水事業(受監管)",
    "Utilities - Renewable": "再生能源公用事業",
    "Waste Management": "廢棄物管理",
}


def translate_sector_label(text: str) -> str:
    text = str(text or "").strip()
    if not text:
        return text
    if text in GICS_INDUSTRY_ZH:
        return GICS_INDUSTRY_ZH[text]
    if re.search(r"[一-鿿]", text):
        return text
    parts = [p.strip() for p in re.split(r"\s*->\s*", text) if p.strip()]
    if len(parts) > 1:
        return " / ".join(GICS_INDUSTRY_ZH.get(p, p) for p in parts)
    return text


def parse_market_cap(value: Any) -> float:
    text = str(value or "")
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return 0.0


def load_company_market_caps() -> dict[str, tuple[float, str]]:
    caps: dict[str, tuple[float, str]] = {}
    for path in load_company_json_files():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ticker = str(data.get("ticker", "")).strip()
        profile = data.get("profile", {}) if isinstance(data.get("profile"), dict) else {}
        label = str(profile.get("market_cap") or "").strip()
        if ticker:
            caps[ticker] = (parse_market_cap(label), label)
    return caps


def company_output_link(data: dict[str, Any]) -> str:
    ticker = str(data.get("ticker", "")).strip()
    company = str(data.get("company_name", "")).strip()
    filename = f"{ticker}_{company}.md"
    if (COMPANY_OUTPUT_DIR / filename).exists():
        return f"company/{quote(filename)}"
    return ""


def company_output_link_by_identity(ticker: str, company: str) -> str:
    filename = f"{ticker}_{company}.md"
    if ticker and company and (COMPANY_OUTPUT_DIR / filename).exists():
        return f"company/{quote(filename)}"
    return ""


def load_ic_chain_names() -> dict[str, str]:
    chain_names: dict[str, str] = {}
    path = IC_TPEX_DIR / "raw_SupplyChainMap.csv"
    if not path.exists():
        return chain_names
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = str(row.get("產業鏈代碼", "")).strip()
            name = str(row.get("產業鏈名稱", "")).strip()
            if code and name:
                chain_names.setdefault(code, name)
    return chain_names


def split_criteria_values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = [str(x) for x in value]
    else:
        raw = [str(value)]
    values: set[str] = set()
    for item in raw:
        values.update(part.strip() for part in re.split(r"[;,，、]", item) if part.strip())
    return values


def criterion_matches(row: dict[str, str], criterion: dict[str, Any]) -> bool:
    positions = split_criteria_values(criterion.get("position") or criterion.get("positions"))
    subcategories = split_criteria_values(criterion.get("subcategory") or criterion.get("subcategories"))
    if positions and str(row.get("位置", "")).strip() not in positions:
        return False
    if subcategories and str(row.get("子分類", "")).strip() not in subcategories:
        return False
    return True


def int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def iter_ic_taxonomy_entries(
    theme_tag: str,
    theme_def: dict[str, Any],
    chain_names: dict[str, str],
    market_caps: dict[str, tuple[float, str]],
) -> list[dict[str, Any]]:
    theme_supply_chain = theme_def.get("theme_supply_chain")
    if not isinstance(theme_supply_chain, dict):
        return []

    entries: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for role in ("upstream", "midstream", "downstream"):
        criteria = theme_supply_chain.get(role, [])
        if isinstance(criteria, dict):
            criteria = [criteria]
        if not isinstance(criteria, list):
            continue
        for criterion in criteria:
            if not isinstance(criterion, dict):
                continue
            chain_code = str(criterion.get("chain_code", "")).strip()
            if not chain_code:
                continue
            default_rank = {"upstream": 100, "midstream": 200, "downstream": 300}.get(role, 900)
            primary_rank = int_value(criterion.get("primary_rank"), default_rank)
            path = IC_TPEX_DIR / f"raw_SupplyChain_{chain_code}.csv"
            if not path.exists():
                continue
            chain_name = str(criterion.get("chain_name") or chain_names.get(chain_code) or chain_code).strip()
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if not criterion_matches(row, criterion):
                        continue
                    ticker = str(row.get("代號", "")).strip()
                    company = str(row.get("名稱", "")).strip()
                    if not ticker or not company:
                        continue
                    position = str(row.get("位置", "")).strip()
                    subcategory = str(row.get("子分類", "")).strip()
                    key = (theme_tag, role, ticker, subcategory)
                    if key in seen:
                        continue
                    seen.add(key)
                    market_cap, market_cap_label = market_caps.get(ticker, (0.0, ""))
                    entries.append({
                        "ticker": ticker,
                        "company": company,
                        "sector": f"{chain_name} - {subcategory}" if subcategory else chain_name,
                        "company_link": company_output_link_by_identity(ticker, company),
                        "role": role,
                        "source_path": f"ic.tpex.org.tw/{chain_code}/{position}/{subcategory}",
                        "match": "ic.tpex.org.tw",
                        "market_cap": market_cap,
                        "market_cap_label": market_cap_label,
                        "primary_rank": primary_rank,
                    })
    return entries


def iter_extra_entities(theme_def: dict[str, Any], market_caps: dict[str, tuple[float, str]]) -> list[dict[str, Any]]:
    """Manually curated companies to inject into a theme's dataset.

    Use when the upstream TPEx taxonomy simply omits a company from every
    matching chain/subcategory row (a source data gap, not something the
    scan/grouping logic can recover from) — see data/themes/*.json 'extra_entities'.
    """
    extras = theme_def.get("extra_entities", []) or []
    entries: list[dict[str, Any]] = []
    for item in extras:
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "").strip()
        company = str(item.get("company") or "").strip()
        if not ticker or not company:
            continue
        role = str(item.get("role") or "related").strip() or "related"
        market_cap, market_cap_label = market_caps.get(ticker, (0.0, ""))
        entries.append({
            "ticker": ticker,
            "company": company,
            "sector": str(item.get("sector") or "").strip(),
            "company_link": company_output_link_by_identity(ticker, company),
            "role": role,
            "source_path": f"extra_entities/{ticker}",
            "match": "manual",
            "market_cap": market_cap,
            "market_cap_label": market_cap_label,
            "primary_rank": int_value(item.get("primary_rank"), {"upstream": 100, "midstream": 200, "downstream": 300}.get(role, 900)),
        })
    return entries


def item_entities(item: dict[str, Any]) -> set[str]:
    values = {str(x).strip() for x in item.get("entities", []) or [] if str(x).strip()}
    text = str(item.get("text", ""))
    values.update(x.strip().split("|", 1)[0].strip() for x in WIKILINK_RE.findall(text) if x.strip())
    return values


def text_matches(text: str, needle: str) -> bool:
    if not needle:
        return False
    if f"[[{needle}]]" in text:
        return True
    if re.search(r"[A-Za-z0-9]", needle):
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(needle)}(?![A-Za-z0-9])", text, re.IGNORECASE) is not None
    return needle in text


def theme_match_terms(theme_def: dict[str, Any], *, include_anchor: bool) -> list[str]:
    terms = [str(theme_def.get("tag", "")).strip()]
    terms.extend(str(x).strip() for x in theme_def.get("aliases", []) or [])
    if include_anchor:
        terms.extend(str(x).strip() for x in theme_def.get("anchor_entities", []) or [])
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        if term and term not in seen:
            out.append(term)
            seen.add(term)
    return out


def role_from_path(path: str, fallback: str = "related") -> str:
    path = path.lower()
    if "supply_chain.upstream" in path or "relationships.suppliers" in path:
        return "upstream"
    if "supply_chain.midstream" in path:
        return "midstream"
    if "supply_chain.downstream" in path or "relationships.customers" in path:
        return "downstream"
    return fallback


def iter_contexts(data: dict[str, Any]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    business = data.get("business", {}) if isinstance(data.get("business"), dict) else {}
    if business.get("summary"):
        contexts.append({"path": "business.summary", "role": "related", "text": str(business.get("summary", "")), "entities": set(business.get("entities", []) or [])})

    supply_chain = data.get("supply_chain", {}) if isinstance(data.get("supply_chain"), dict) else {}
    for key in ("upstream", "midstream", "downstream", "other"):
        for idx, item in enumerate(supply_chain.get(key, []) or []):
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(k, "")) for k in ("category", "text"))
            contexts.append({"path": f"supply_chain.{key}[{idx}]", "role": role_from_path(f"supply_chain.{key}"), "text": text, "entities": item_entities(item)})

    relationships = data.get("relationships", {}) if isinstance(data.get("relationships"), dict) else {}
    for key in ("customers", "suppliers", "competitors", "peers", "substitutes", "other"):
        for idx, item in enumerate(relationships.get(key, []) or []):
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(k, "")) for k in ("role", "category", "text"))
            contexts.append({"path": f"relationships.{key}[{idx}]", "role": role_from_path(f"relationships.{key}"), "text": text, "entities": item_entities(item)})

    comp = data.get("competitive_position", {}) if isinstance(data.get("competitive_position"), dict) else {}
    for key in ("moats", "risks", "notes"):
        for idx, item in enumerate(comp.get(key, []) or []):
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(k, "")) for k in ("role", "category", "text"))
            contexts.append({"path": f"competitive_position.{key}[{idx}]", "role": "related", "text": text, "entities": item_entities(item)})
    return contexts


def explicit_theme_entries(data: dict[str, Any], theme_defs: dict[str, dict[str, Any]]) -> list[tuple[str, str, str]]:
    by_id = {str(defn.get("id")): tag for tag, defn in theme_defs.items()}
    entries: list[tuple[str, str, str]] = []
    for item in data.get("themes", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("status") in {"rejected", "false_positive"}:
            continue
        key = str(item.get("tag") or item.get("theme_tag") or "").strip()
        theme_id = str(item.get("id") or item.get("theme_id") or "").strip()
        tag = key if key in theme_defs else by_id.get(theme_id, "")
        if not tag:
            continue
        source_path = str(item.get("source_path") or item.get("presentation_path") or "themes[]").strip()
        entries.append((tag, role_from_path(source_path, str(item.get("role") or "related")), source_path))
    return entries


def scan_theme_links(theme_defs: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """Scan canonical company JSON and IC taxonomy, returning {theme_tag: [company entries]}."""
    theme_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    chain_names = load_ic_chain_names()
    market_caps = load_company_market_caps()

    for tag, theme_def in theme_defs.items():
        for entry in iter_ic_taxonomy_entries(tag, theme_def, chain_names, market_caps):
            key = (tag, entry["ticker"], entry["source_path"])
            if key in seen:
                continue
            seen.add(key)
            theme_map[tag].append(entry)
        for entry in iter_extra_entities(theme_def, market_caps):
            key = (tag, entry["ticker"], entry["source_path"])
            if key in seen:
                continue
            seen.add(key)
            theme_map[tag].append(entry)

    for json_path in load_company_json_files():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ticker = str(data.get("ticker", "")).strip()
        company = str(data.get("company_name", "")).strip()
        if not ticker or not company:
            continue
        market_cap, market_cap_label = market_caps.get(ticker, (0.0, ""))
        base = {
            "ticker": ticker,
            "company": company,
            "sector": profile_sector(data),
            "company_link": company_output_link(data),
            "market_cap": market_cap,
            "market_cap_label": market_cap_label,
        }

        for tag, role, source_path in explicit_theme_entries(data, theme_defs):
            key = (tag, ticker, source_path)
            if key in seen:
                continue
            seen.add(key)
            theme_map[tag].append({**base, "role": role, "source_path": source_path, "match": "explicit"})

        for context in iter_contexts(data):
            text = str(context["text"])
            entities = set(context.get("entities") or [])
            for tag, theme_def in theme_defs.items():
                include_anchor = (
                    str(theme_def.get("type", "")) == "brand_supply_chain_theme"
                    and (str(context["path"]).startswith("relationships.customers") or str(context["path"]).startswith("relationships.suppliers") or str(context["path"]).startswith("supply_chain."))
                )
                terms = theme_match_terms(theme_def, include_anchor=include_anchor)
                matched = ""
                for term in terms:
                    if term in entities or text_matches(text, term):
                        matched = term
                        break
                if not matched:
                    continue
                key = (tag, ticker, str(context["path"]))
                if key in seen:
                    continue
                seen.add(key)
                role = "related" if isinstance(theme_def.get("theme_supply_chain"), dict) else str(context["role"])
                theme_map[tag].append({**base, "role": role, "source_path": str(context["path"]), "match": matched})

    return theme_map


def build_theme_page(theme_tag: str, theme_def: dict[str, Any], theme_map: dict[str, list[dict[str, str]]]) -> str | None:
    entries = theme_map.get(theme_tag, [])
    if not entries:
        return None

    lines = [f"# {theme_def['name']}", "", f"> {theme_def['desc']}", ""]
    has_theme_supply_chain = isinstance(theme_def.get("theme_supply_chain"), dict)
    structured_roles = {"upstream", "midstream", "downstream"}

    def primary_rank(item: dict[str, Any]) -> int:
        return int_value(item.get("primary_rank"), {"upstream": 100, "midstream": 200, "downstream": 300}.get(str(item.get("role") or ""), 900))

    if has_theme_supply_chain:
        best_role_by_ticker: dict[str, str] = {}
        for ticker, ticker_entries in defaultdict(list, {
            ticker: [e for e in entries if e.get("ticker") == ticker and e.get("role") in structured_roles]
            for ticker in {str(e.get("ticker") or "") for e in entries if e.get("role") in structured_roles}
        }).items():
            if not ticker_entries:
                continue
            best = sorted(ticker_entries, key=lambda e: (primary_rank(e), str(e.get("role") or ""), str(e.get("source_path") or "")))[0]
            best_role_by_ticker[ticker] = str(best.get("role") or "")
        entries = [
            e for e in entries
            if e.get("role") not in structured_roles or best_role_by_ticker.get(str(e.get("ticker") or "")) == e.get("role")
        ]

    structured_entries = [e for e in entries if e.get("role") in structured_roles]
    if has_theme_supply_chain:
        structured_tickers = {str(e.get("ticker") or "") for e in structured_entries}
        entries = [
            e for e in entries
            if e.get("role") in structured_roles or str(e.get("ticker") or "") not in structured_tickers
        ]
    lines.append(f"**涵蓋公司數:** {len({e['ticker'] for e in entries})}")
    if has_theme_supply_chain:
        source = str(theme_def.get("theme_supply_chain", {}).get("taxonomy_source") or "../biztrends.TW/data/ic.tpex.org.tw/raw_SupplyChain_*.csv")
        lines.append(f"**IC 產業鏈資料來源 (部分公司):** `{source}`")
    lines.append("")

    related_parts: list[str] = []
    theme_defs_by_tag = getattr(build_theme_page, "theme_definitions", {})
    company_badge_index = getattr(build_theme_page, "company_badge_index", {})
    for related_tag in theme_def.get("related_theme_tags", []) or []:
        count = len({e["ticker"] for e in theme_map.get(related_tag, [])})
        if count > 0 and related_tag in theme_map:
            related_def = theme_defs_by_tag.get(related_tag, {"tag": related_tag})
            related_parts.append(f"{render_theme_badge(related_def)} ({count})")
    if theme_def.get("related_entities"):
        related_parts.extend(render_related_entity(str(entity), company_badge_index) for entity in theme_def.get("related_entities", []) or [])
    if related_parts:
        lines.append(f"**相關主題/實體:** {' | '.join(related_parts)}")
        lines.append("")

    lines.extend(["---", ""])

    def market_cap_value(item: dict[str, Any]) -> float:
        try:
            return float(item.get("market_cap") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    competitive_groups = theme_def.get("competitive_groups", []) or []
    competitive_group_by_ticker: dict[str, str] = {}
    curated_order_index: dict[str, int] = {}
    for order, group in enumerate(competitive_groups):
        if not isinstance(group, dict):
            continue
        group_name = str(group.get("name") or "").strip()
        if not group_name:
            continue
        curated_order_index.setdefault(group_name, order)
        for ticker in group.get("tickers", []) or []:
            competitive_group_by_ticker[str(ticker).strip()] = group_name

    merged: dict[str, dict[str, Any]] = {}
    for entry in entries:
        ticker = entry["ticker"]
        item = merged.setdefault(ticker, {**entry, "source_paths": [], "matches": []})
        source_path = entry.get("source_path", "")
        match = entry.get("match", "")
        if source_path and source_path not in item["source_paths"]:
            item["source_paths"].append(source_path)
        if match and match not in item["matches"]:
            item["matches"].append(match)

    group_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in merged.values():
        ticker = str(item.get("ticker") or "")
        group_name = competitive_group_by_ticker.get(ticker) or translate_sector_label(plain_context_text(item.get("sector") or "")) or "其他"
        group_items[group_name].append(item)

    def group_sort_key(name: str) -> tuple:
        if name in curated_order_index:
            return (0, curated_order_index[name], name)
        total_cap = sum(market_cap_value(i) for i in group_items[name])
        return (1, -total_cap, name)

    lines.append(f"## 相關公司 ({len(merged)})")
    lines.append("")
    for group_name in sorted(group_items.keys(), key=group_sort_key):
        items = sorted(group_items[group_name], key=lambda x: (-market_cap_value(x), str(x.get("ticker") or "")))
        lines.append(f"**{group_name}** ({len(items)})")
        for item in items:
            label = f"{item['ticker']} {item['company']}"
            linked = render_company_badge(label, item["company_link"]) if item.get("company_link") else label
            cap_label = str(item.get("market_cap_label") or "")
            context = f"市值: {cap_label}" if cap_label else ""
            lines.append(f"- {linked} ({context})" if context else f"- {linked}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"




def theme_company_count(theme_def: dict[str, Any], entries: list[dict[str, str]]) -> int:
    return len({e["ticker"] for e in entries})


def build_index(themes_built: dict[str, int], theme_definitions: dict[str, dict[str, Any]]) -> str:
    """Build output/themes/README.md index."""
    lines = [
        "# 主題式投資篩選 Thematic Investment Screens",
        "",
        "> Auto-generated supply chain maps from `data/themes/*.json` and `data/enrichment_all/*.json`.",
        "> Regenerate: `python skills/skill-my-tw-coverage-render-markdown/scripts/build_themes.py`",
        "",
        "---",
        "",
    ]

    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for tag, definition in theme_definitions.items():
        if tag not in themes_built:
            continue
        for category in definition.get("index_categories", [definition.get("category", "未分類")]):
            grouped[str(category)].append((tag, definition))

    categories = sorted(
        grouped.items(),
        key=lambda item: min(defn.get("order", 9990) for _, defn in item[1]),
    )

    for cat_name, items in categories:
        lines.append(f"## {cat_name}")
        lines.append("")
        for tag, definition in sorted(items, key=lambda item: (item[1].get("order", 9990), item[0])):
            count = themes_built[tag]
            lines.append(f"- {render_theme_badge(definition)} — {count} 家公司")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    OUTPUT_THEMES_DIR.mkdir(parents=True, exist_ok=True)
    theme_definitions = load_theme_definitions()

    args = sys.argv[1:]
    if "--list" in args:
        for tag, defn in theme_definitions.items():
            print(f"  {tag}: {defn['name']} ({defn['id']})")
        return 0

    print("Scanning canonical enrichment JSON for theme links...")
    theme_map = scan_theme_links(theme_definitions)
    build_theme_page.theme_definitions = theme_definitions
    build_theme_page.company_badge_index = load_company_badge_index()
    print(f"Found {len(theme_map)} themes with company matches.\n")

    if args and args[0] != "--list":
        themes_to_build = {args[0]: theme_definitions.get(args[0])}
        if not themes_to_build[args[0]]:
            print(f"Theme '{args[0]}' not in data/themes. Use --list to see available themes.")
            return 1
    else:
        themes_to_build = theme_definitions

    themes_built: dict[str, int] = {}
    for tag, definition in themes_to_build.items():
        if not definition:
            continue
        page = build_theme_page(tag, definition, theme_map)
        if not page:
            continue
        filename = theme_output_filename(definition)
        (OUTPUT_THEMES_DIR / filename).write_text(page, encoding="utf-8")
        count = theme_company_count(definition, theme_map.get(tag, []))
        themes_built[tag] = count
        print(f"  {tag}: {count} companies -> {filename}")

    index = build_index(themes_built, theme_definitions)
    (OUTPUT_THEMES_DIR / "README.md").write_text(index, encoding="utf-8")
    print(f"\nDone. Generated {len(themes_built)} theme pages in output/themes/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
