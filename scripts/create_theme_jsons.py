import json
from pathlib import Path

root = Path(r"C:\Users\WJLEE\SynologyDrive\NAS\github.com\My-TW-Coverage")

# 1. Industrial PC Theme JSON
ipc_json = {
    "tag": "工業電腦",
    "aliases": ["IPC", "工業自動化", "智能製造"],
    "render": {
        "badge_label": "工業電腦",
        "badge_color": "green",
        "output_filename": "工業電腦.md"
    },
    "description": "工業電腦 (IPC) 專用主題，涵蓋工業自動化、邊緣 AI (Edge AI)、智慧零售、車載電腦與醫療電子之硬體製造與系統整合商。"
}

(root / "data/themes/工業電腦.json").write_text(json.dumps(ipc_json, ensure_ascii=False, indent=2), encoding="utf-8")

# 2. DRAM Theme JSON
dram_json = {
    "tag": "DRAM",
    "aliases": ["記憶體", "DRAM/記憶體", "HBM", "NAND", "快閃記憶體"],
    "render": {
        "badge_label": "DRAM/記憶體",
        "badge_color": "green",
        "output_filename": "DRAM.md"
    },
    "description": "DRAM 與記憶體產業主題，涵蓋 HBM3E 先進記憶體、Server DRAM、DDR5、NAND Flash 原廠、台系記憶體製造廠與控制模組大廠。"
}

(root / "data/themes/DRAM.json").write_text(json.dumps(dram_json, ensure_ascii=False, indent=2), encoding="utf-8")

print("Wrote theme JSON files!")
