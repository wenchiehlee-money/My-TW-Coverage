import os
import re
import json

def generate_docsify_assets():
    base_dir = r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage"
    enrichment_dir = os.path.join(base_dir, "output", "enrichment_all_rendered")
    themes_dir = os.path.join(base_dir, "themes")

    # 1. 處理 enrichment_all_rendered 索引
    print("Scanning enrichment files...")
    enrichment_files = []
    if os.path.exists(enrichment_dir):
        for f in os.listdir(enrichment_dir):
            if f.endswith(".md") and f != "README.md":
                # 預期格式: 1101_台泥.md
                match = re.match(r"^(\d+)[-_](.+)\.md$", f)
                if match:
                    code = match.group(1)
                    name = match.group(2)
                    enrichment_files.append((code, name, f))
                else:
                    # 備份格式，萬一沒有代號
                    enrichment_files.append(("9999", f.replace(".md", ""), f))
    
    # 依股票代號排序
    enrichment_files.sort(key=lambda x: x[0])
    
    # 分組 (簡化分組名稱，以防 markdown 錨點解析異常)
    groups = {
        "1xxx 水泥 食品 塑膠 紡織": [],
        "2xxx 電機 鋼鐵 電子 半導體": [],
        "3xxx 電子 光電 通信 網通": [],
        "4xxx-5xxx 化學 生技 其他電子": [],
        "6xxx-9xxx 航運 觀光 金融 其他": []
    }
    
    for code, name, fname in enrichment_files:
        try:
            val = int(code)
        except ValueError:
            val = 9999
            
        if 1000 <= val < 2000:
            groups["1xxx 水泥 食品 塑膠 紡織"].append((code, name, fname))
        elif 2000 <= val < 3000:
            groups["2xxx 電機 鋼鐵 電子 半導體"].append((code, name, fname))
        elif 3000 <= val < 4000:
            groups["3xxx 電子 光電 通信 網通"].append((code, name, fname))
        elif 4000 <= val < 6000:
            groups["4xxx-5xxx 化學 生技 其他電子"].append((code, name, fname))
        else:
            groups["6xxx-9xxx 航運 觀光 金融 其他"].append((code, name, fname))

    # 生成 output/enrichment_all_rendered/README.md
    readme_path = os.path.join(enrichment_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 台灣上市櫃公司個股研究報告索引\n\n")
        f.write("> 本索引收錄共 {} 家台灣上市櫃公司之個股研究報告。點擊下方分類快速跳轉。\n\n".format(len(enrichment_files)))
        
        # 目錄連結
        for g_name in groups.keys():
            # 轉換為標準 markdown 錨點格式
            anchor = g_name.lower().replace(" ", "-").replace("/", "")
            f.write("- [{}](#{})\n".format(g_name, anchor))
        f.write("\n---\n\n")
        
        # 寫入各組內容
        for g_name, items in groups.items():
            f.write("## {}\n\n".format(g_name))
            if not items:
                f.write("*目前無資料*\n\n")
                continue
            
            # 使用 Markdown 表格展示
            cols = 5
            f.write("| " + " | ".join(["公司"] * cols) + " |\n")
            f.write("| " + " | ".join(["---"] * cols) + " |\n")
            
            row_items = []
            for item in items:
                code, name, fname = item
                # 相對路徑
                link = "[{} {}]({})".format(code, name, fname)
                row_items.append(link)
                if len(row_items) == cols:
                    f.write("| " + " | ".join(row_items) + " |\n")
                    row_items = []
            if row_items:
                row_items += [""] * (cols - len(row_items))
                f.write("| " + " | ".join(row_items) + " |\n")
            f.write("\n")
            
    print(f"Generated {readme_path} with {len(enrichment_files)} companies.")

    # 2. 讀取 output/themes/README.md 來解析投資主題
    print("Generating sidebar...")
    themes_links = []
    themes_readme_path = os.path.join(themes_dir, "README.md")
    if os.path.exists(themes_readme_path):
        with open(themes_readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 解析 markdown 連結
        matches = re.findall(r'-\s+\[\!\[([^\]]+)\]\([^\)]+\)\]\(([^/]+?\.md)\)', content)
        if not matches:
            matches = re.findall(r'-\s+\[([^\]]+)\]\(([^/]+?\.md)\)', content)
            
        for title, link in matches:
            themes_links.append((title, f"output/themes/{link}"))
            
    # 如果沒有找到，就直接掃描目錄
    if not themes_links and os.path.exists(themes_dir):
        for f in os.listdir(themes_dir):
            if f.endswith(".md") and f != "README.md":
                title = f.replace(".md", "").replace("_", " ")
                themes_links.append((title, f"output/themes/{f}"))
                
    # 3. 生成根目錄的 _sidebar.md (保持極簡與乾淨分組)
    sidebar_path = os.path.join(base_dir, "_sidebar.md")
    sidebar_content = """- [🏠 首頁](README.md)
- [📈 投資主題總覽](output/themes/README.md)
- [AI 伺服器](output/themes/AI_伺服器.md)
- [工業電腦 (IPC)](output/themes/工業電腦.md)
- [DRAM / 記憶體](output/themes/DRAM.md)
- [CoWoS 先進封裝](output/themes/CoWoS.md)
- [HBM 高頻寬記憶體](output/themes/HBM.md)
- [CPO / 矽光子](output/themes/矽光子.md)
- [資料中心](output/themes/資料中心.md)
- [NVIDIA 供應鏈](output/themes/NVIDIA.md)
- [Apple 供應鏈](output/themes/Apple.md)
- [Tesla / 電動車](output/themes/電動車.md)
"""
    with open(sidebar_path, "w", encoding="utf-8") as f:
        f.write(sidebar_content)
        
    print(f"Generated {sidebar_path}")

    # 4. 生成 wikilink_map.js
    print("Generating wikilink map...")
    wikilink_map = {}
    
    # 處理個股
    for code, name, fname in enrichment_files:
        rel_path = f"output/enrichment_all_rendered/{fname}"
        wikilink_map[code.lower()] = rel_path
        wikilink_map[name.lower()] = rel_path
        wikilink_map[f"{code}_{name}".lower()] = rel_path
        wikilink_map[f"{code}-{name}".lower()] = rel_path
        
    # 處理主題
    if os.path.exists(themes_dir):
        for f in os.listdir(themes_dir):
            if f.endswith(".md") and f != "README.md":
                theme_name = f.replace(".md", "")
                rel_path = f"output/themes/{f}"
                wikilink_map[theme_name.lower()] = rel_path
                wikilink_map[theme_name.replace("_", " ").lower()] = rel_path
                wikilink_map[theme_name.replace("_", "-").lower()] = rel_path
                
    map_js_path = os.path.join(base_dir, "wikilink_map.js")
    with open(map_js_path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated mapping file for docsify wikilink resolution.\n")
        f.write("window.WIKILINK_MAP = ")
        json.dump(wikilink_map, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"Generated {map_js_path} with {len(wikilink_map)} mapping entries.")

if __name__ == "__main__":
    generate_docsify_assets()
