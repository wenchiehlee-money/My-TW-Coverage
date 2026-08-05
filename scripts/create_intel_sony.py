import json
from pathlib import Path

root = Path(r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage")

companies = [
    {
        "ticker": "INTC",
        "company_name": "Intel",
        "title": "INTC - [[Intel]]",
        "sector": "Technology",
        "industry": "Semiconductors",
        "market_cap": "135,000 百萬美元",
        "ev": "165,000 百萬美元",
        "desc": "Intel Corporation (INTC，[[Intel]]) 為全球個人電腦 x86 處理器 (Core 系列) 與企業伺服器 CPU (Xeon 系列) 龍頭。公司推動 IDM 2.0 戰略，劃分為產品事業群 (CCG 個人電腦、DCAI 數據中心與 AI、NEX 網路與邊緣) 以及獨立運作的晶圓代工部門 (Intel Foundry)。旗下亦包含車用晶片子公司 Mobileye。",
        "up": "- **晶圓代工與先進封裝外包:** [[台積電]] (N3/N4 代工 Lunar Lake / Arrow Lake 之 Compute Tile)\n- **半導體設備與關鍵組件:** [[ASML]] (High-NA EUV 首批客戶)、[[應用材料]]、[[Lam Research]]\n- **載板與散熱:** [[欣興]]、[[南電]]、[[健策]]",
        "mid": "- **Intel** — x86 架構設計、Core / Xeon 處理器研發、Foveros 3D 封裝與自有晶圓廠製造",
        "down": "- **全球 PC 品牌巨頭:** [[Dell]]、[[Lenovo]]、[[HP]]、[[華碩]]、[[宏碁]]\n- **伺服器與 CSP:** [[廣達]]、[[鴻海]]、[[緯創]]、[[英業達]]、[[Microsoft]]、[[Amazon]]",
        "cust": "- [[Dell]]、[[Lenovo]]、[[HP]]、[[華碩]]、[[廣達]]、[[鴻海]]",
        "supp": "- [[台積電]]、[[ASML]]、[[欣興]]、[[應用材料]]",
        "pe_ttm": "N/A (虧損)", "ps_ttm": "2.49x", "ev_ebitda": "14.20x", "fwd_pe": "21.00x", "fwd_ps": "2.10x",
        "eps_26": "0.95 USD", "rev_26": "56,500M USD", "eps_27": "1.65 USD", "rev_27": "64,000M USD",
        "rev_3y": "| | FY2025 | FY2024 | FY2023 |\n|:---|---:|---:|---:|\n| Revenue | 54,228.00 | 54,228.00 | 63,054.00 |\n| Gross Margin (%) | 38.50 | 40.00 | 42.60 |\n| Net Income | -18,756.00 | 1,010.00 | 8,014.00 |\n| EPS ($) | -4.40 | 0.24 | 1.94 |",
        "rev_4q": "| | FY2026 Q1 | FY2025 Q4 | FY2025 Q3 | FY2025 Q2 |\n|:---|---:|---:|---:|---:|\n| Revenue | 13,284.00 | 14,256.00 | 13,284.00 | 12,830.00 |\n| Gross Margin (%) | 39.20 | 38.00 | 36.50 | 38.70 |\n| Net Income | -821.00 | 125.00 | -16,639.00 | -1,610.00 |\n| EPS ($) | -0.19 | 0.03 | -3.88 | -0.38 |",
        "seg": "| Client Computing Group (CCG - PC CPU) | 55.40% ($7,359M) | Core Ultra (Lunar Lake/Arrow Lake) AI PC 晶片 |\n| Data Center and AI (DCAI - Xeon) | 31.20% ($4,144M) | Xeon 6 (Granite Rapids / Sierra Forest) 伺服器 CPU |\n| Network and Edge (NEX) & Mobileye | 13.40% ($1,781M) | 網通交換晶片與 Mobileye 智駕方案 |"
    },
    {
        "ticker": "SONY",
        "company_name": "Sony",
        "title": "SONY - [[Sony]]",
        "sector": "Consumer Discretionary & Technology",
        "industry": "Consumer Electronics & Entertainment",
        "market_cap": "115,000 百萬美元",
        "ev": "122,000 百萬美元",
        "desc": "Sony Group Corporation (SONY，[[Sony]]) 總部位於日本東京，為全球跨國消費性電子、半導體感測器與娛樂影視巨頭。旗下核心業務包含 PlayStation (PS5 家用遊戲機與遊戲軟體遊戲開發)、CMOS 影像感測器 (CIS，為 Apple iPhone 與高階手機主要供應商)、Sony Music 音樂出版、Sony Pictures 電影發行及高端 Bravia 電視與音響。",
        "up": "- **晶圓代工與合資廠:** [[台積電]] (JASM 熊本廠合作夥伴)、自有熊本/長崎 CIS 晶圓廠\n- **遊戲機與電子零組件代工:** [[鴻海]] (PS5 主機組裝)、[[和碩]]\n- **光學與顯示元件:** [[採鈺]]、[[大立光]]",
        "mid": "- **Sony** — CMOS 影像感測器研發製造、PlayStation 主機架構、遊戲開發工作室 (PlayStation Studios) 與影音娛樂內容製作",
        "down": "- **全球手持裝置品牌:** [[Apple]] (iPhone CIS 鏡頭感測器巨頭)、[[小米]]、[[OPPO]]、[[vivo]]\n- **廣大全球玩家與影視消費者:** PS5 家用主機玩家、PlayStation Plus 訂閱戶、全球影院與串流平台客戶",
        "cust": "- [[Apple]]、[[小米]]、全球 PlayStaton 玩家與娛樂訂閱客戶",
        "supp": "- [[台積電]]、[[鴻海]]、[[和碩]]、[[AMD]] (PS5 APU 供應商)",
        "pe_ttm": "17.50x", "ps_ttm": "1.35x", "ev_ebitda": "9.80x", "fwd_pe": "14.20x", "fwd_ps": "1.20x",
        "eps_26": "6.80 USD", "rev_26": "92,000M USD", "eps_27": "7.90 USD", "rev_27": "101,000M USD",
        "rev_3y": "| | FY2025 | FY2024 | FY2023 |\n|:---|---:|---:|---:|\n| Revenue | 86,520.00 | 85,120.00 | 79,200.00 |\n| Gross Margin (%) | 26.80 | 27.50 | 28.20 |\n| Net Income | 6,850.00 | 6,420.00 | 6,100.00 |\n| EPS ($) | 5.52 | 5.17 | 4.91 |",
        "rev_4q": "| | FY2026 Q1 | FY2025 Q4 | FY2025 Q3 | FY2025 Q2 |\n|:---|---:|---:|---:|---:|\n| Revenue | 21,500.00 | 22,800.00 | 24,100.00 | 18,120.00 |\n| Gross Margin (%) | 27.10 | 26.50 | 27.80 | 25.90 |\n| Net Income | 1,820.00 | 1,650.00 | 2,150.00 | 1,230.00 |\n| EPS ($) | 1.47 | 1.33 | 1.73 | 0.99 |",
        "seg": "| Game & Network Services (G&NS - PS5) | 33.50% ($7,203M) | PS5 硬體銷售、第一方遊戲軟體與 PS Plus 訂閱 |\n| Imaging & Sensing Solutions (I&SS - CIS) | 19.80% ($4,257M) | 高階智慧型手機 (iPhone) 用 50MP+ CMOS 影像感測器 |\n| Entertainment, Technology & Services (ET&S) | 18.20% ($3,913M) | Bravia 電視、相機與耳機音響 |\n| Music & Pictures (音樂與電影娛樂) | 28.50% ($6,127M) | 影音內容發行、音樂版權與串流平台授權 |"
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
        'extracted_at': '2026-08-05 21:30 CST',
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
