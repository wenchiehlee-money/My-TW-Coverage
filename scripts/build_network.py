"""
build_network.py — Generate wikilink network graph data and interactive visualization.

Scans all ticker reports for wikilink co-occurrences and generates:
1. network/graph_data.json — node/edge data for visualization
2. network/index.html — interactive D3.js force-directed graph

Usage:
  python scripts/build_network.py                # Default: min 5 co-occurrences
  python scripts/build_network.py --min-weight 10  # Higher threshold = fewer edges
  python scripts/build_network.py --top 100       # Only top N nodes by mention count
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    REPORTS_DIR, setup_stdout,
    classify_wikilink, CATEGORY_COLORS, CATEGORY_LABELS,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETWORK_DIR = os.path.join(PROJECT_ROOT, "network")


def scan_graph(min_weight=5, top_n=None):
    """Scan all reports and build co-occurrence graph."""
    # Step 1: collect wikilinks per file
    node_counts = defaultdict(int)
    wl_per_file = {}

    for root, dirs, files in os.walk(REPORTS_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            m = re.match(r"^(\d{4})", f)
            if not m:
                continue
            with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                content = fh.read().split("## 財務概況")[0]
            wls = set(re.findall(r"\[\[([^\]]+)\]\]", content))
            wl_per_file[m.group(1)] = wls
            for wl in wls:
                node_counts[wl] += 1

    # Step 2: filter to top N nodes if specified
    if top_n:
        top_nodes = set(
            name for name, _ in sorted(node_counts.items(), key=lambda x: -x[1])[:top_n]
        )
    else:
        # At minimum, only include nodes that appear in >= 2 files
        top_nodes = set(name for name, count in node_counts.items() if count >= 2)

    # Step 3: count co-occurrences
    edges = defaultdict(int)
    for ticker, wls in wl_per_file.items():
        filtered = sorted(wls & top_nodes)
        for i in range(len(filtered)):
            for j in range(i + 1, len(filtered)):
                edges[(filtered[i], filtered[j])] += 1

    # Step 4: filter edges by weight
    filtered_edges = {k: v for k, v in edges.items() if v >= min_weight}

    # Step 5: only keep nodes that have at least one edge
    active_nodes = set()
    for (a, b) in filtered_edges:
        active_nodes.add(a)
        active_nodes.add(b)

    nodes = []
    for name in active_nodes:
        cat = classify_wikilink(name)
        nodes.append({
            "id": name,
            "count": node_counts[name],
            "category": cat,
            "color": CATEGORY_COLORS[cat],
        })

    edge_list = []
    for (source, target), weight in filtered_edges.items():
        edge_list.append({
            "source": source,
            "target": target,
            "weight": weight,
        })

    return nodes, edge_list


def build_html(nodes, edges):
    """Generate self-contained D3.js interactive network visualization."""
    graph_json = json.dumps({"nodes": nodes, "links": edges}, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<title>Taiwan Stock Wikilink Network</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #1a1a2e; color: #eee; overflow: hidden; }}
  #controls {{ position: fixed; top: 12px; left: 12px; z-index: 10; background: rgba(26,26,46,0.95); padding: 16px; border-radius: 10px; border: 1px solid #333; }}
  #controls h2 {{ font-size: 16px; margin-bottom: 8px; }}
  #controls label {{ font-size: 13px; display: block; margin: 6px 0 2px; }}
  #controls input[type=range] {{ width: 180px; }}
  #controls input[type=text] {{ width: 180px; padding: 4px 8px; background: #2a2a4e; border: 1px solid #444; color: #eee; border-radius: 4px; }}
  
  #legend {{
    position: fixed;
    bottom: 12px;
    left: 12px;
    z-index: 10;
    background: rgba(26,26,46,0.95);
    padding: 14px;
    border-radius: 10px;
    border: 1px solid #333;
    max-width: 500px;
  }}
  #legend-container {{
    display: flex;
    gap: 16px;
  }}
  .legend-left {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-right: 1px solid #444;
    padding-right: 16px;
    flex-shrink: 0;
  }}
  .legend-right {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-grow: 1;
    min-width: 100px;
    transition: min-width 0.3s ease;
  }}
  .legend-right.expanded {{
    min-width: 260px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    font-size: 13px;
  }}
  #app-title-container {{
    display: flex;
    align-items: center;
    cursor: pointer;
    user-select: none;
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.2s;
  }}
  #app-title-container:hover {{
    background: rgba(255,255,255,0.08);
  }}
  #app-arrow {{
    display: inline-block;
    margin-left: 6px;
    font-size: 10px;
    color: #888;
    transition: transform 0.2s;
  }}
  .legend-right.expanded #app-arrow {{
    transform: rotate(90deg);
  }}
  #app-breakdown-list {{
    display: none;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px 12px;
    max-height: 110px;
    overflow-y: auto;
    padding-right: 4px;
    margin-top: 4px;
  }}
  .legend-right.expanded #app-breakdown-list {{
    display: grid;
  }}
  #app-breakdown-list label {{
    display: flex;
    align-items: center;
    font-size: 12px;
    cursor: pointer;
    color: #ccc;
    user-select: none;
  }}
  #app-breakdown-list input[type=checkbox] {{
    margin-right: 6px;
    cursor: pointer;
    accent-color: #9b59b6;
  }}
  #app-breakdown-list::-webkit-scrollbar {{
    width: 6px;
  }}
  #app-breakdown-list::-webkit-scrollbar-track {{
    background: rgba(0,0,0,0.1);
  }}
  #app-breakdown-list::-webkit-scrollbar-thumb {{
    background: #444;
    border-radius: 3px;
  }}
  #app-breakdown-list::-webkit-scrollbar-thumb:hover {{
    background: #555;
  }}
  #toggle-all-apps {{
    display: none;
    margin-left: auto;
    font-size: 10px;
    padding: 2px 6px;
    background: #2a2a4e;
    border: 1px solid #444;
    color: #eee;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.2s;
  }}
  .legend-right.expanded #toggle-all-apps {{
    display: inline-block;
  }}

  #tooltip {{ position: fixed; background: rgba(0,0,0,0.9); color: #fff; padding: 8px 14px; border-radius: 6px; font-size: 13px; pointer-events: none; display: none; z-index: 20; border: 1px solid #555; }}
  #stats {{ position: fixed; top: 12px; right: 12px; z-index: 10; background: rgba(26,26,46,0.95); padding: 12px 16px; border-radius: 10px; border: 1px solid #333; font-size: 13px; }}
  svg {{ width: 100vw; height: 100vh; }}
</style>
</head>
<body>
<div id="controls">
  <h2>Wikilink Network</h2>
  <label>Min Edge Weight: <span id="weightVal">5</span></label>
  <input type="range" id="weightSlider" min="1" max="50" value="5">
  <label>Search:</label>
  <input type="text" id="search" placeholder="e.g. 台積電, NVIDIA, CoWoS">
</div>

<div id="legend">
  <div id="legend-container">
    <div class="legend-left">
      <div class="legend-item">
        <div style="width:12px;height:12px;border-radius:50%;background:#e74c3c;margin-right:8px"></div>
        <span>台灣公司</span>
      </div>
      <div class="legend-item">
        <div style="width:12px;height:12px;border-radius:50%;background:#3498db;margin-right:8px"></div>
        <span>國際公司</span>
      </div>
      <div class="legend-item">
        <div style="width:12px;height:12px;border-radius:50%;background:#2ecc71;margin-right:8px"></div>
        <span>技術/標準</span>
      </div>
      <div class="legend-item">
        <div style="width:12px;height:12px;border-radius:50%;background:#f39c12;margin-right:8px"></div>
        <span>材料/基板</span>
      </div>
    </div>
    <div class="legend-right">
      <div style="display:flex;align-items:center;margin-bottom:4px;">
        <div id="app-title-container">
          <div style="width:12px;height:12px;border-radius:50%;background:#9b59b6;margin-right:8px"></div>
          <span style="font-size:13px;font-weight:bold;color:#fff;">終端應用</span>
          <span id="app-arrow">▸</span>
        </div>
        <button id="toggle-all-apps">全選/全不選</button>
      </div>
      <div id="app-breakdown-list"></div>
    </div>
  </div>
</div>

<div id="tooltip"></div>
<div id="stats"></div>
<svg></svg>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const fullData = {graph_json};
const width = window.innerWidth, height = window.innerHeight;

const svg = d3.select("svg");
const g = svg.append("g");

// Zoom
svg.call(d3.zoom().scaleExtent([0.1, 8]).on("zoom", (e) => g.attr("transform", e.transform)));

const tooltip = d3.select("#tooltip");
let simulation, linkG, nodeG, labelG;

// 儲存目前勾選的終端應用 id
const activeAppIds = new Set(fullData.nodes.filter(n => n.category === 'application').map(n => n.id));

// 動態渲染終端應用 checkbox 清單
const appListDiv = d3.select("#app-breakdown-list");
const appNodes = fullData.nodes.filter(n => n.category === 'application').sort((a, b) => b.count - a.count);

appNodes.forEach(node => {{
  const label = appListDiv.append("label");
  
  label.append("input")
    .attr("type", "checkbox")
    .property("checked", true)
    .attr("value", node.id)
    .on("change", function() {{
      if (this.checked) {{
        activeAppIds.add(node.id);
      }} else {{
        activeAppIds.delete(node.id);
      }}
      render(+d3.select("#weightSlider").property("value"));
    }});
    
  label.append("span").text(`${{node.id}} (${{node.count}})`);
}});

// 點擊「終端應用」標題切換展開/收合
d3.select("#app-title-container").on("click", function() {{
  const container = d3.select(".legend-right");
  const isExpanded = container.classed("expanded");
  container.classed("expanded", !isExpanded);
}});

// 全選/全不選功能
let allSelected = true;
d3.select("#toggle-all-apps").on("click", function() {{
  allSelected = !allSelected;
  appListDiv.selectAll("input[type=checkbox]").property("checked", allSelected);
  if (allSelected) {{
    appNodes.forEach(node => activeAppIds.add(node.id));
  }} else {{
    activeAppIds.clear();
  }}
  render(+d3.select("#weightSlider").property("value"));
}});

function render(minWeight) {{
  // 過濾連結，如果端點是未被選取的終端應用，就過濾掉
  const links = fullData.links.filter(l => {{
    if (l.weight < minWeight) return false;
    
    const sourceId = l.source.id || l.source;
    const targetId = l.target.id || l.target;
    
    const sourceNode = fullData.nodes.find(n => n.id === sourceId);
    const targetNode = fullData.nodes.find(n => n.id === targetId);
    
    if (sourceNode && sourceNode.category === 'application' && !activeAppIds.has(sourceId)) {{
      return false;
    }}
    if (targetNode && targetNode.category === 'application' && !activeAppIds.has(targetId)) {{
      return false;
    }}
    return true;
  }});

  const activeIds = new Set();
  links.forEach(l => {{ activeIds.add(l.source.id || l.source); activeIds.add(l.target.id || l.target); }});
  const nodes = fullData.nodes.filter(n => activeIds.has(n.id));

  d3.select("#stats").html(`Nodes: ${{nodes.length}} | Edges: ${{links.length}}`);

  g.selectAll("*").remove();

  // Scale
  const maxCount = d3.max(nodes, d => d.count) || 1;
  const rScale = d3.scaleSqrt().domain([1, maxCount]).range([4, 40]);
  const maxWeight = d3.max(links, l => l.weight) || 1;
  const wScale = d3.scaleLinear().domain([minWeight, maxWeight]).range([0.5, 4]);
  const oScale = d3.scaleLinear().domain([minWeight, maxWeight]).range([0.15, 0.6]);

  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(80).strength(0.3))
    .force("charge", d3.forceManyBody().strength(-150))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => rScale(d.count) + 2));

  linkG = g.append("g").selectAll("line").data(links).join("line")
    .attr("stroke", "#555").attr("stroke-opacity", d => oScale(d.weight))
    .attr("stroke-width", d => wScale(d.weight));

  nodeG = g.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("r", d => rScale(d.count)).attr("fill", d => d.color)
    .attr("stroke", "#fff").attr("stroke-width", 0.5).attr("opacity", 0.9)
    .call(d3.drag().on("start", dragStart).on("drag", dragging).on("end", dragEnd))
    .on("mouseover", (e, d) => {{
      tooltip.style("display", "block").html(
        `<b>${{d.id}}</b><br>提及次數: ${{d.count}}<br>類別: ${{d.category}}`
      );
      highlightNeighbors(d);
    }})
    .on("mousemove", (e) => tooltip.style("left", e.pageX+12+"px").style("top", e.pageY-20+"px"))
    .on("mouseout", () => {{ tooltip.style("display", "none"); resetHighlight(); }});

  labelG = g.append("g").selectAll("text").data(nodes.filter(d => d.count >= 20)).join("text")
    .text(d => d.id).attr("font-size", d => Math.max(8, Math.min(14, rScale(d.count) * 0.7)))
    .attr("fill", "#ccc").attr("text-anchor", "middle").attr("dy", d => rScale(d.count) + 12)
    .style("pointer-events", "none");

  simulation.on("tick", () => {{
    linkG.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
    nodeG.attr("cx", d=>d.x).attr("cy", d=>d.y);
    labelG.attr("x", d=>d.x).attr("y", d=>d.y);
  }});
}}

function highlightNeighbors(d) {{
  const neighbors = new Set();
  linkG.each(function(l) {{
    if (l.source.id === d.id) neighbors.add(l.target.id);
    if (l.target.id === d.id) neighbors.add(l.source.id);
  }});
  neighbors.add(d.id);
  nodeG.attr("opacity", n => neighbors.has(n.id) ? 1 : 0.1);
  linkG.attr("stroke-opacity", l => (l.source.id===d.id||l.target.id===d.id) ? 0.8 : 0.03);
  labelG.attr("opacity", n => neighbors.has(n.id) ? 1 : 0.1);
}}

function resetHighlight() {{
  nodeG.attr("opacity", 0.9);
  linkG.attr("stroke-opacity", d => 0.3);
  labelG.attr("opacity", 1);
}}

function dragStart(e, d) {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
function dragging(e, d) {{ d.fx = e.x; d.fy = e.y; }}
function dragEnd(e, d) {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}

// Controls
d3.select("#weightSlider").on("input", function() {{
  const v = +this.value;
  d3.select("#weightVal").text(v);
  render(v);
}});

d3.select("#search").on("input", function() {{
  const q = this.value.toLowerCase();
  if (!q) {{ resetHighlight(); return; }}
  const match = fullData.nodes.find(n => n.id.toLowerCase().includes(q));
  if (match) highlightNeighbors(match);
}});

// Initial render
render(5);
</script>
</body>
</html>"""


def main():
    setup_stdout()

    args = sys.argv[1:]
    min_weight = 5
    top_n = None

    for i, arg in enumerate(args):
        if arg == "--min-weight" and i + 1 < len(args):
            min_weight = int(args[i + 1])
        elif arg == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])

    os.makedirs(NETWORK_DIR, exist_ok=True)

    print(f"Scanning wikilink co-occurrences (min weight: {min_weight})...")
    nodes, edges = scan_graph(min_weight=min_weight, top_n=top_n)
    print(f"Graph: {len(nodes)} nodes, {len(edges)} edges")

    # Save JSON data
    graph_data = {"nodes": nodes, "links": edges}
    json_path = os.path.join(NETWORK_DIR, "graph_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {json_path}")

    # Generate HTML
    html = build_html(nodes, edges)
    html_path = os.path.join(NETWORK_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {html_path}")

    print(f"\nOpen in browser: {html_path}")
    print("Or serve locally: python -m http.server 8000 --directory network/")


if __name__ == "__main__":
    main()
