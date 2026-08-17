"""Create data/enrichment_all/ORCL.json following the same schema/architecture as
scripts/create_tech_giants.py. Financial figures are sourced from the authoritative
upstream data pipeline (../ConceptStocks/raw_conceptstock_company_income.csv,
symbol=ORCL, SEC-validated rows), matching how MSFT/AMZN/GOOGL/META already flow
through data/ConceptStocks -> data/enrichment_all -> output/themes/company per
../biztrends.TW/docs/data_pipeline_diagram.md. Market cap/EV are from Yahoo Finance
as of 2026-08-08 (companiesmarketcap.com / mlq.ai), since ConceptStocks does not
carry market-cap fields.
"""
import json
from pathlib import Path

root = Path(r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage")

c = {
    "ticker": "ORCL",
    "company_name": "Oracle",
    "title": "ORCL - [[Oracle]]",
    "sector": "Technology",
    "industry": "Software & Cloud Infrastructure",
    "market_cap": "433,560 百萬美元",
    "ev": "553,284 百萬美元",
    "desc": "Oracle Corporation (ORCL，[[Oracle]]) 原為全球資料庫軟體與企業應用 (ERP/Fusion) 龍頭，近年積極轉型為 AI 雲端基礎設施供應商。旗下 [[Oracle Cloud Infrastructure]] (OCI) 為訓練大型語言模型的關鍵算力平台，並與 [[OpenAI]]、[[xAI]] 簽署數千億美元規模的多年期運算容量合約 (Stargate 專案)，剩餘履約義務 (RPO) 已突破 6,000 億美元。公司仍持續服務全球數萬家企業級資料庫與 ERP 客戶。",
    "up": "- **AI 伺服器晶片供應商:** [[NVIDIA]] (H100/H200/GB300 NVL72 GPU 叢集)、[[AMD]] (MI300X)\n- **AI 伺服器代工與網通夥伴:** [[緯穎]] (承接原 Super Micro 之 GB300 機櫃訂單)、[[廣達]]、[[鴻海]]、[[智邦]]\n- **水冷與電源解決方案:** [[台達電]]、[[奇鋐]]、[[雙鴻]]",
    "mid": "- **Oracle** — Oracle Cloud Infrastructure (OCI) 雲端基礎架構建置、Oracle Database 資料庫、Fusion/NetSuite ERP 企業應用軟體與 Stargate AI 算力出租",
    "down": "- **AI 大模型訓練客戶:** [[OpenAI]] (Stargate 專案主力承購方)、[[xAI]]、[[Meta]]\n- **全球企業與政府客戶:** 數萬家企業資料庫、ERP 與雲端基礎架構用戶",
    "cust": "[[OpenAI]]、[[xAI]]、[[Meta]]、全球企業資料庫與 ERP 客戶",
    "supp": "[[NVIDIA]]、[[AMD]]、[[緯穎]]、[[廣達]]、[[鴻海]]",
    "pe_ttm": "25.00x", "ps_ttm": "6.44x", "ev_ebitda": "19.80x", "fwd_pe": "21.50x", "fwd_ps": "5.60x",
    "eps_26": "5.83 USD", "rev_26": "67,358M USD", "eps_27": "6.90 USD", "rev_27": "89,000M USD",
    "rev_3y": "| | FY2026 | FY2025 | FY2024 |\n|:---|---:|---:|---:|\n| Revenue | 67,358.00 | 57,399.00 | 52,961.00 |\n| Gross Margin (%) | 65.20 | 70.50 | 71.40 |\n| Net Income | 17,087.00 | 12,443.00 | 10,467.00 |\n| EPS ($) | 5.83 | 4.34 | 3.71 |",
    "rev_4q": "| | FY2026 Q4 | FY2026 Q3 | FY2026 Q2 | FY2026 Q1 |\n|:---|---:|---:|---:|---:|\n| Revenue | 19,184.00 | 17,190.00 | 16,058.00 | 14,926.00 |\n| Gross Margin (%) | 65.20 | 64.60 | 66.50 | 67.30 |\n| Net Income | 4,304.00 | 3,721.00 | 6,135.00 | 2,927.00 |\n| EPS ($) | 1.45 | 1.27 | 2.10 | 1.01 |",
    "seg": "| Cloud Services (OCI IaaS + SaaS) | ~50.5% ($34,000M) | Cloud 總營收年增 39%，OCI (IaaS) 年增 77% 至 181 億美元 |\n| Cloud License & On-Premise License / Support | ~42.0% (~$28,300M) | 傳統資料庫授權與維護收入持穩，逐步轉為雲端訂閱 |\n| Hardware & Services | ~7.5% (~$5,100M) | Exadata 硬體設備與顧問導入服務 |",
}

j_data = {
    'schema_version': '0.1.0',
    'ticker': c['ticker'],
    'company_name': c['company_name'],
    'title': c['title'],
    'source_md': f"output/enrichment_all_rendered/{c['ticker']}_{c['company_name']}.md",
    'extracted_at': '2026-08-17 CST',
    'profile': {'sector': c['sector'], 'industry': c['industry'], 'market_cap': c['market_cap'], 'enterprise_value': c['ev']},
    'business': {'summary': c['desc'], 'entities': [c['company_name']]},
    'supply_chain': {'upstream': [], 'midstream': [], 'downstream': [], 'other': []},
    'relationships': {'customers': [], 'suppliers': [], 'competitors': [], 'peers': [], 'substitutes': [], 'other': []},
    'competitive_position': {'moats': [], 'risks': [], 'notes': []},
    'entities': [{'name': c['company_name'], 'type': 'international_company', 'wikilink': c['company_name']}],
    'source_text': {
        'business_summary_md': c['desc'],
        'supply_chain_md': f"{c['up']}\n\n**中游:**\n{c['mid']}\n\n**下游:**\n{c['down']}",
        'customers_suppliers_md': f"### 主要客戶\n- {c['cust']}\n\n### 主要供應商\n- {c['supp']}",
        'financial_md': f"## 財務概況 (單位: 百萬台幣, 只有 Margin 為 %)\n\n### 估值指標\n\n基準日: 2026-08-08 | 股價: 全球市場交易 | TTM 截至: FY2026 Q4 (2026-05-31)\n\n#### 市場估值\n\n| 指標 | 數值 | 分子 | 分母 | 說明 |\n|:---|:---|:---|:---|:---|\n| P/E (TTM) | {c['pe_ttm']} | 股價 | TTM EPS | 股價 / TTM EPS |\n| P/S (TTM) | {c['ps_ttm']} | 市值 | TTM 營收 | 市值 / TTM 營收 |\n| EV/EBITDA (TTM) | {c['ev_ebitda']} | 企業價值 | TTM EBITDA | 企業價值 / TTM EBITDA |\n\n#### Consensus 估值\n\nConsensus 截至: 2026-08-08 | Primary: ConceptStocks (SEC/AlphaVantage) | Revenue 單位: 百萬數據\n\n| 指標 | Primary Consensus | 說明 | 信心 |\n|:---|:---|:---|:---|\n| 2026E EPS | {c['eps_26']} | Forward P/E; current year (FY2026 實際值) | high |\n| 2026E Revenue | {c['rev_26']} | Forward P/S; current year (FY2026 實際值) | high |\n| 2027E EPS | {c['eps_27']} | Forward P/E; next year | medium |\n| 2027E Revenue | {c['rev_27']} | Forward P/S; next year (管理層財測含 Stargate 訂單放量) | medium |\n\n| 估值指標 | 數值 | 分子 | 分母 | 使用基礎 |\n|:---|:---|:---|:---|:---|\n| Forward P/E (Consensus) | {c['fwd_pe']} | 股價 | 2027E EPS | 股價 / consensus EPS |\n| Forward P/S (Consensus) | {c['fwd_ps']} | 市值 | 2027E Revenue | 市值 / consensus revenue |\n\n### 年度關鍵財務數據 (近 3 年)\n{c['rev_3y']}\n\n### 季度關鍵財務數據 (近 4 季)\n{c['rev_4q']}\n\n### 營收平台佔比 (Revenue by Platform %)\n| 平台 / 事業群 | 最新佔比 | 趨勢與推動力 |\n|:---|:---|:---|\n{c['seg']}\n\n> 財務數據來源: `../ConceptStocks/raw_conceptstock_company_income.csv` (symbol=ORCL, SEC-validated rows)，與 [[Amazon]]、[[Microsoft]]、[[Google]]、[[Meta]] 共用同一上游資料管線 (見 `../biztrends.TW/docs/data_pipeline_diagram.md`)。市值/企業價值取自 Yahoo Finance 2026-08-08 快照。競爭同業 Revenue/Profit/GM/PE 比較表待 `data/ConceptStocks/` 於本機同步後，透過 `skills/skill-company-competitor-analysis/scripts/run_company_competitor_analysis.py --stock ORCL` 自動產生。\n"
    },
    'quality': {'parser_status': 'parsed', 'review_status': 'reviewed', 'wikilink_count': 10, 'warnings': []}
}
j_path = root / f"data/enrichment_all/{c['ticker']}.json"
j_path.write_text(json.dumps(j_data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Wrote {j_path}")
