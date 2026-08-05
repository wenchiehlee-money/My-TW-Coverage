import json
from pathlib import Path

root = Path(r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage")

apple = {
    "schema_version": "0.1.0",
    "ticker": "AAPL",
    "company_name": "Apple",
    "title": "AAPL - [[Apple]]",
    "source_md": "output/enrichment_all_rendered/AAPL_Apple.md",
    "extracted_at": "2026-08-05 21:29 CST",
    "profile": {
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": "3,380,000 百萬美元",
        "enterprise_value": "3,410,000 百萬美元"
    },
    "business": {
        "summary": "Apple Inc. (AAPL，[[Apple]]) 總部位於美國加州庫比蒂諾，為全球市值最高的科技巨頭與消費性電子龍頭。旗下核心硬體包含 iPhone (智慧型手機)、Mac (個人電腦)、iPad (平板電腦)、Apple Watch 及 AirPods。公司擁有自主開發的 A 系列與 M 系列 Apple Silicon 晶片、iOS/macOS 作業系統與強大的 App Store / Services 生態系，並積極導入 Apple Intelligence 個人化 AI 功能。",
        "entities": ["Apple"]
    },
    "supply_chain": {
        "upstream": [], "midstream": [], "downstream": [], "other": []
    },
    "relationships": {
        "customers": [], "suppliers": [], "competitors": [], "peers": [], "substitutes": [], "other": []
    },
    "competitive_position": {
        "moats": [], "risks": [], "notes": []
    },
    "entities": [
        {
            "name": "Apple",
            "type": "international_company",
            "wikilink": "Apple"
        }
    ],
    "source_text": {
        "business_summary_md": "Apple Inc. (AAPL，[[Apple]]) 總部位於美國加州庫比蒂諾，為全球市值最高的科技巨頭與消費性電子龍頭。旗下核心硬體包含 iPhone (智慧型手機)、Mac (個人電腦)、iPad (平板電腦)、Apple Watch 及 AirPods。公司擁有自主開發的 A 系列與 M 系列 Apple Silicon 晶片、iOS/macOS 作業系統與強大的 App Store / Services 生態系，並積極導入 Apple Intelligence 個人化 AI 功能。",
        "supply_chain_md": "**上游 (關鍵零組件與晶片):**\n- **晶圓代工與先進封裝:** [[台積電]] (獨家代工 N3B/N3E 蘋果 A18/M4 晶片 & InFO 封裝)\n- **光學鏡頭與模組:** [[大立光]]、[[玉晶光]]、[[鴻海]] (富士康模組)\n- **機殼與軟硬板:** [[華通]]、[[臻鼎-KY]]、[[台郡]]、[[鴻準]]\n- **聲學與感測元件:** [[美律]]、[[瑞昱]]\n\n**中游 (品牌設計與組裝代工):**\n- **Apple** — 產品設計、Apple Silicon 架構設計、iOS/macOS 系統與 App Store 生態系\n- **全球組裝代工夥伴:** [[鴻海]] (富士康，iPhone 旗艦機主要代工)、[[和碩]]、[[立訊精密]]、[[廣達]] (MacBook 代工)、[[仁寶]] (iPad 代工)\n\n**下游 (銷售通路與廣大消費者):**\n- **銷售通路:** 全球 Apple Store 直營店、Apple Online Store、電信營運商 (AT&T, Verizon, 中國移動) 及授權經銷商\n- **廣大終端用戶:** 全球超過 22 億台活躍 Apple 裝置使用者",
        "customers_suppliers_md": "### 主要客戶\n- 全球數十億個人消費者、企業員工、創作者與教育市場機構\n\n### 主要供應商\n- **晶圓代工:** [[台積電]] (核心 A 系列 / M 系列晶片獨家供應商)\n- **組裝與代工:** [[鴻海]]、[[和碩]]、[[廣達]]、[[仁寶]]、[[立訊精密]]\n- **光學鏡頭:** [[大立光]]、[[玉晶光]]\n- **軟硬 PCB 載板:** [[臻鼎-KY]]、[[華通]]、[[台郡]]",
        "financial_md": "## 財務概況 (單位: 百萬台幣, 只有 Margin 為 %)\n\n### 估值指標\n\n基準日: 2026-07-30 | 股價: 美股 | TTM 截至: 近期\n\n#### 市場估值\n\n| 指標 | 數值 | 分子 | 分母 | 說明 |\n|:---|:---|:---|:---|:---|\n| P/E (TTM) | 34.20x | 股價 | TTM EPS | 股價 / TTM EPS |\n| P/S (TTM) | 8.60x | 市值 | TTM 營收 | 市值 / TTM 營收 |\n| EV/EBITDA (TTM) | 26.50x | 企業價值 | TTM EBITDA | 企業價值 / TTM EBITDA |\n\n#### Consensus 估值\n\nConsensus 截至: 2026-08-01 | Primary: Yahoo.Finance | Revenue 單位: 百萬美元 USD\n\n| 指標 | Primary Consensus | 說明 | 信心 |\n|:---|:---|:---|:---|\n| 2026E EPS | 7.45 USD | Forward P/E; current year | high |\n| 2026E Revenue | 415,000M USD | Forward P/S; current year | high |\n| 2027E EPS | 8.35 USD | Forward P/E; next year | high |\n| 2027E Revenue | 452,000M USD | Forward P/S; next year | medium |\n\n| 估值指標 | 數值 | 分子 | 分母 | 使用基礎 |\n|:---|:---|:---|:---|:---|\n| Forward P/E (Consensus) | 26.80x | 股價 | 2027E EPS | 股價 / consensus EPS |\n| Forward P/S (Consensus) | 7.48x | 市值 | 2027E Revenue | 市值 / consensus revenue |\n\n### 年度關鍵財務數據 (近 3 年，單位: 百萬美元 USD)\n| | FY2025 | FY2024 | FY2023 |\n|:---|---:|---:|---:|\n| Revenue | 391,035.00 | 385,604.00 | 383,285.00 |\n| Gross Margin (%) | 46.20 | 46.20 | 44.10 |\n| Net Income | 93,736.00 | 93,736.00 | 96,995.00 |\n| EPS ($) | 6.08 | 6.08 | 6.13 |\n\n### 季度關鍵財務數據 (近 4 季，單位: 百萬美元 USD)\n| | FY2026 Q2 | FY2026 Q1 | FY2025 Q4 | FY2025 Q3 |\n|:---|---:|---:|---:|---:|\n| Revenue | 95,359.00 | 124,300.00 | 94,930.00 | 85,777.00 |\n| Gross Margin (%) | 46.60 | 46.90 | 46.20 | 46.30 |\n| Net Income | 23,636.00 | 33,916.00 | 14,736.00 | 21,448.00 |\n| EPS ($) | 1.53 | 2.18 | 0.97 | 1.40 |\n\n### 營收平台佔比 (Revenue by Platform %)\n| 產品線 / 事業群 | 最新佔比 ($M) | 趨勢與推動力 |\n|:---|:---|:---|\n| iPhone (旗艦手機) | 51.20% ($48,823M) | iPhone 16/17 系列與 Apple Intelligence 引發換機潮 |\n| Services (App Store / iCloud / Pay) | 25.40% ($24,213M) | 訂閱服務持續雙位數高速成長，毛利率突破 74% |\n| Wearables, Home & Accessories | 8.80% ($8,391M) | Apple Watch, AirPods 與配件銷售 |\n| Mac (個人電腦) | 7.80% ($7,438M) | M3/M4 架構 MacBook Pro / Air 升級 |\n| iPad (平板電腦) | 6.80% ($6,494M) | iPad Pro OLED 與 iPad Air 新品放量 |\n"
    },
    "quality": {
        "parser_status": "parsed",
        "review_status": "reviewed",
        "wikilink_count": 12,
        "warnings": []
    }
}

j_path = root / "data/enrichment_all/AAPL.json"
j_path.write_text(json.dumps(apple, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {j_path}")
