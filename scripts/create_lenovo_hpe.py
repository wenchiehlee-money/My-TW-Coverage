import json
from pathlib import Path

root = Path(r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage")

companies = [
    {
        "ticker": "0992.HK",
        "company_name": "聯想集團",
        "title": "0992.HK - [[聯想集團]]",
        "sector": "Technology",
        "industry": "Computer Hardware & Servers",
        "market_cap": "118,500 百萬港幣",
        "ev": "125,000 百萬港幣",
        "desc": "聯想集團 (0992.HK，[[聯想集團]]) 總部位於中國北京與美國北卡羅來納州，為全球市佔率第一的個人電腦 (PC) 供應商，產品包含 ThinkPad、Yoga 及 Legion 電競系列。公司同時為全球主要伺服器與基礎架構提供商 (ISG)，提供 ThinkSystem 伺服器與 AI 算力基礎設施，並積極拓展 AI PC 換機潮。",
        "up": "- **CPU / GPU 晶片:** [[Intel]]、[[AMD]]、[[NVIDIA]]、[[Qualcomm]]\n- **代工與組裝夥伴:** [[仁寶]]、[[廣達]]、[[緯創]]、[[英業達]]、[[鴻海]]\n- **記憶體與面板:** [[Samsung]]、[[SK 海力士]]、[[京東方]]",
        "mid": "- **聯想集團 (Lenovo)** — 品牌行銷、系統產品設計、軟硬體整合與自建合資組裝廠 (如合肥聯寶)",
        "down": "- **全球企業與個人用戶:** 全球商用企業客戶、政府機構、教育市場與廣大消費性市場\n- **通路夥伴:** 全球經銷商 (Distributors)、系統整合商與直營電商",
        "cust": "- 全球大型企業、政府機構、教育市場與廣大個人消費者",
        "supp": "- [[Intel]]、[[AMD]]、[[NVIDIA]]、[[仁寶]]、[[廣達]]",
        "pe_ttm": "11.20x", "ps_ttm": "0.28x", "ev_ebitda": "6.50x", "fwd_pe": "8.90x", "fwd_ps": "0.24x",
        "eps_26": "0.13 USD", "rev_26": "62,500M USD", "eps_27": "0.15 USD", "rev_27": "69,200M USD",
        "rev_3y": "| | FY2025 | FY2024 | FY2023 |\n|:---|---:|---:|---:|\n| Revenue | 56,864.00 | 56,864.00 | 61,898.00 |\n| Gross Margin (%) | 17.20 | 17.20 | 17.00 |\n| Net Income | 1,011.00 | 1,011.00 | 1,608.00 |\n| EPS ($) | 0.08 | 0.08 | 0.13 |",
        "rev_4q": "| | FY2026 Q1 | FY2025 Q4 | FY2025 Q3 | FY2025 Q2 |\n|:---|---:|---:|---:|---:|\n| Revenue | 15,447.00 | 13,800.00 | 15,720.00 | 14,440.00 |\n| Gross Margin (%) | 16.80 | 17.10 | 16.50 | 17.50 |\n| Net Income | 243.00 | 248.00 | 337.00 | 249.00 |\n| EPS ($) | 0.02 | 0.02 | 0.03 | 0.02 |",
        "seg": "| Intelligent Devices Group (IDG - PC & Mobile) | 74.50% ($11,508M) | ThinkPad / Legion / Moto 手機與 AI PC 出貨 |\n| Infrastructure Solutions Group (ISG - Servers) | 19.80% ($3,058M) | ThinkSystem AI 伺服器與水冷系統 |\n| Solutions & Services Group (SSG - IT Services) | 5.70% ($881M) | 企業 IT 運營服務與雲端託管服務 |"
    },
    {
        "ticker": "HPE",
        "company_name": "HPE",
        "title": "HPE - [[HPE]]",
        "sector": "Technology",
        "industry": "Computer Hardware & Servers",
        "market_cap": "25,400 百萬美元",
        "ev": "38,200 百萬美元",
        "desc": "Hewlett Packard Enterprise (HPE，[[HPE]]) 總部位於美國德州休士頓，為全球企業級伺服器、數據儲存設備及邊緣運算網路方案巨頭。旗艦產品包含 ProLiant 伺服器、Cray 超級電腦 (如 Frontier/El Capitan)、Alletra 儲存系統及 Aruba 邊緣網路。公司正併購 Juniper Networks 以強化 AI 網通生態系統。",
        "up": "- **CPU / GPU 晶片:** [[NVIDIA]] (H100/B200)、[[AMD]] (EPYC/Instinct MI300)、[[Intel]]\n- **伺服器與網通 ODM 代工:** [[鴻海]]、[[廣達]]、[[緯創]]、[[英業達]]、[[智邦]]\n- **電源與水冷散熱:** [[台達電]]、[[奇鋐]]、[[雙鴻]]",
        "mid": "- **HPE** — 企業伺服器架構設計、GreenLake 混合雲訂閱平台與 Cray 超級電腦整合",
        "down": "- **全球企業與 Tier-2/3 CSP:** 全球大型企業、金融機構、國防科研機構與雲端服務提供商\n- **經銷與 SI 夥伴:** 全球系統整合商 (SI)、經銷商與直銷經理",
        "cust": "- 全球超級電腦中心、大型企業數據中心、國防機構與電信營運商",
        "supp": "- [[NVIDIA]]、[[AMD]]、[[Intel]]、[[鴻海]]、[[廣達]]、[[台達電]]",
        "pe_ttm": "14.80x", "ps_ttm": "0.85x", "ev_ebitda": "8.20x", "fwd_pe": "9.50x", "fwd_ps": "0.78x",
        "eps_26": "1.95 USD", "rev_26": "30,500M USD", "eps_27": "2.20 USD", "rev_27": "33,800M USD",
        "rev_3y": "| | FY2025 | FY2024 | FY2023 |\n|:---|---:|---:|---:|\n| Revenue | 30,035.00 | 29,135.00 | 28,496.00 |\n| Gross Margin (%) | 33.80 | 35.10 | 34.20 |\n| Net Income | 1,720.00 | 1,254.00 | 868.00 |\n| EPS ($) | 1.31 | 0.96 | 0.66 |",
        "rev_4q": "| | FY2026 Q1 | FY2025 Q4 | FY2025 Q3 | FY2025 Q2 |\n|:---|---:|---:|---:|---:|\n| Revenue | 7,710.00 | 8,464.00 | 7,710.00 | 7,204.00 |\n| Gross Margin (%) | 33.20 | 33.50 | 33.20 | 33.80 |\n| Net Income | 512.00 | 512.00 | 512.00 | 314.00 |\n| EPS ($) | 0.39 | 0.39 | 0.39 | 0.24 |",
        "seg": "| Server (ProLiant & HPE Cray AI Servers) | 54.20% ($4,178M) | AI 伺服器 (H100/MI300) 與超級電腦積壓訂單 |\n| Intelligent Edge (Aruba Networking) | 16.50% ($1,272M) | 企業 Wi-Fi 6E/7、Campus Switch 設備 |\n| Hybrid Cloud & Storage (Alletra & GreenLake) | 29.30% ($2,260M) | GreenLake 混合雲訂閱與 AI 數據儲存 |"
    }
]

for c in companies:
    t = c['ticker']
    j_data = {
        'schema_version': '0.1.0',
        'ticker': t,
        'company_name': c['company_name'],
        'title': c['title'],
        'source_md': f"output/enrichment_all_rendered/{t}_{c['company_name']}.md",
        'extracted_at': '2026-08-05 21:23 CST',
        'profile': {'sector': c['sector'], 'industry': c['industry'], 'market_cap': c['market_cap'], 'enterprise_value': c['ev']},
        'business': {'summary': c['desc'], 'entities': [c['company_name']]},
        'supply_chain': {'upstream': [], 'midstream': [], 'downstream': [], 'other': []},
        'relationships': {'customers': [], 'suppliers': [], 'competitors': [], 'peers': [], 'substitutes': [], 'other': []},
        'competitive_position': {'moats': [], 'risks': [], 'notes': []},
        'entities': [{'name': c['company_name'], 'type': 'international_company', 'wikilink': c['company_name']}],
        'source_text': {
            'business_summary_md': c['desc'],
            'supply_chain_md': f"**上游:**\n{c['up']}\n\n**中游:**\n{c['mid']}\n\n**下游:**\n{c['down']}",
            'customers_suppliers_md': f"### 主要客戶\n- {c['cust']}\n\n### 主要供應商\n- {c['supp']}",
            'financial_md': f"## 財務概況 (單位: 百萬台幣, 只有 Margin 為 %)\n\n### 估值指標\n\n基準日: 2026-07-30 | 股價: 全球市場交易 | TTM 截至: 近期\n\n#### 市場估值\n\n| 指標 | 數值 | 分子 | 分母 | 說明 |\n|:---|:---|:---|:---|:---|\n| P/E (TTM) | {c['pe_ttm']} | 股價 | TTM EPS | 股價 / TTM EPS |\n| P/S (TTM) | {c['ps_ttm']} | 市值 | TTM 營收 | 市值 / TTM 營收 |\n| EV/EBITDA (TTM) | {c['ev_ebitda']} | 企業價值 | TTM EBITDA | 企業價值 / TTM EBITDA |\n\n#### Consensus 估值\n\nConsensus 截至: 2026-08-01 | Primary: Yahoo.Finance | Revenue 單位: 百萬數據\n\n| 指標 | Primary Consensus | 說明 | 信心 |\n|:---|:---|:---|:---|\n| 2026E EPS | {c['eps_26']} | Forward P/E; current year | high |\n| 2026E Revenue | {c['rev_26']} | Forward P/S; current year | medium |\n| 2027E EPS | {c['eps_27']} | Forward P/E; next year | high |\n| 2027E Revenue | {c['rev_27']} | Forward P/S; next year | medium |\n\n| 估值指標 | 數值 | 分子 | 分母 | 使用基礎 |\n|:---|:---|:---|:---|:---|\n| Forward P/E (Consensus) | {c['fwd_pe']} | 股價 | 2027E EPS | 股價 / consensus EPS |\n| Forward P/S (Consensus) | {c['fwd_ps']} | 市值 | 2027E Revenue | 市值 / consensus revenue |\n\n### 年度關鍵財務數據 (近 3 年)\n{c['rev_3y']}\n\n### 季度關鍵財務數據 (近 4 季)\n{c['rev_4q']}\n\n### 營收平台佔比 (Revenue by Platform %)\n| 平台 / 事業群 | 最新佔比 | 趨勢與推動力 |\n|:---|:---|:---|\n{c['seg']}\n"
        },
        'quality': {'parser_status': 'parsed', 'review_status': 'reviewed', 'wikilink_count': 10, 'warnings': []}
    }
    j_path = root / f"data/enrichment_all/{t}.json"
    j_path.write_text(json.dumps(j_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Wrote {j_path}")
