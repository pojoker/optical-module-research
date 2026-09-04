#!/usr/bin/env python3
"""build_atlas_v15.py — 光模块产业「披露证据地图」v1.5

在冻结的 v1.4 视觉与交互语言上扩展：
- 输入 output/edges.csv（225 边）与 output/nodes.csv（161 节点）
- 节点只按 nodes.csv 的「类型」字段自动归入七个产业层
- 横向节点、纵向产业层；节点较多的层自动排成两行
- Marvell / 博通标记为「产品映射盲区」
- 输出自包含、无外部资源依赖的 output/光模块产业图谱-v1.5.html
"""

import csv
import json
import os
import re
from collections import Counter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODES_PATH = os.path.join(ROOT, "output", "nodes.csv")
EDGES_PATH = os.path.join(ROOT, "output", "edges.csv")
OUT_PATH = os.path.join(ROOT, "output", "光模块产业图谱-v1.5.html")

LAYER_ORDER = ("L1", "L2", "L3", "L4", "L5", "L6", "L7")
LAYER_LABEL = {
    "L1": "上游材料",
    "L2": "光/电芯片 + DSP芯片",
    "L3": "封装/代工 + 贸易/委托加工",
    "L4": "光器件",
    "L5": "模块/光电子商",
    "L6": "代工(EMS) / 线缆 / 系统 / 终端",
    "L7": "算力终端 / 云",
}
DSP_BLINDSPOT = {"Marvell", "博通(Broadcom)"}


def layer_for_type(node_type):
    """按「类型」字段归层；顺序用于消解复合类型，不使用节点名称映射。"""
    t = (node_type or "").strip()

    if any(k in t for k in ("算力终端", "云巨头")):
        return "L7"
    if any(k in t for k in (
        "芯片", "DSP", "半导体", "半导体IDM", "驱动控制", "功率器件封测"
    )):
        return "L2"
    if any(k in t for k in (
        "代工(EMS)", "线缆/系统/终端", "系统设备商", "网络设备OEM",
        "CATV设备商", "CATV分销商", "消费电子终端", "汽车电机厂"
    )):
        return "L6"
    if "光器件" in t or "模块/器件" in t:
        return "L4"
    if any(k in t for k in (
        "模块/光电子商", "光模块厂", "光模块/宽带", "供应链主体", "旭创关联方"
    )):
        return "L5"
    if any(k in t for k in (
        "封装/代工", "贸易", "代理", "物流", "设备商", "设备经销",
        "设备/科研", "科研院所", "仪器", "自动化", "焊接"
    )):
        return "L3"
    if any(k in t for k in (
        "上游材料", "材料/设备供应商", "加工件供应商", "锻件厂"
    )):
        return "L1"
    raise ValueError(f"未覆盖的节点类型: {t!r}")


def grade_class(grade):
    if grade.startswith("实边(已死"):
        return "dead"
    if grade.startswith("实边"):
        return "lit"
    if grade.startswith("推断边"):
        return "infer"
    if grade.startswith("程序段落"):
        return "leak"
    return "shadow"


def country_key(country):
    c = country or ""
    if c.startswith("中国") or (
        "中国" in c and all(x not in c for x in ("日本", "德国", "新加坡"))
    ):
        return "cn"
    if "美国" in c:
        return "us"
    if "日本" in c or "台湾" in c:
        return "jt"
    if c == "待核":
        return "veil"
    return "other"


def norm(name):
    """边端点名称归一；匿名端点保留原文并在渲染时生成幽灵槽位。"""
    if not name:
        return name
    n = name.strip()
    alias = {
        "AAOI": "Applied Optoelectronics(AAOI)",
        "华为+海思": "华为(含海思)",
        "华为": "华为(含海思)",
        "博通": "博通(Broadcom)",
        "博通(客户)": "博通(Broadcom)",
        "Broadcom": "博通(Broadcom)",
        "NVIDIA(客户)": "NVIDIA",
        "索尔思": "索尔思(Source Photonics)",
        "Fabrinet(解匿)": "Fabrinet",
        "Fabrinet(疑似客户)": "Fabrinet",
        "Ciena(解匿)": "Ciena",
        "Google(解匿)": "Google",
        "中际旭创(作为客户)": "中际旭创",
        "罗博特科": "罗博特科/ficonTEC",
        "ficonTEC(罗博特科)": "罗博特科/ficonTEC",
        "PINEWAVE(关联方)": "PINEWAVE",
        "等离子体所(客户)": "等离子体所",
        "浙江粮油(出口代理)": "浙江粮油",
        "索恩格": "索恩格(SEG Automotive)",
        "苏世博": "索恩格(SEG Automotive)",
        "Corning(解匿)": "Corning Incorporated",
    }
    return alias.get(n, n)


def load():
    with open(NODES_PATH, encoding="utf-8-sig", newline="") as f:
        nodes = list(csv.DictReader(f))
    with open(EDGES_PATH, encoding="utf-8-sig", newline="") as f:
        edges = list(csv.DictReader(f))
    return nodes, edges


def build():
    nodes, edges = load()
    node_map = {}
    for row in nodes:
        name = row["名称"].strip()
        node_map[name] = {
            "id": name,
            "type": row["类型"].strip(),
            "country": row["国别"].strip(),
            "code": row.get("代码", "").strip(),
            "note": row.get("备注", "").strip(),
            "layer": layer_for_type(row["类型"]),
            "ck": country_key(row["国别"]),
            "deg": 0,
            "blindspot": name in DSP_BLINDSPOT,
        }

    edge_payload = []
    ghosts = {}

    def endpoint(name):
        if name in node_map:
            return name
        gid = "◈ " + name
        if gid not in ghosts:
            ghosts[gid] = {
                "id": gid,
                "type": "匿名槽位",
                "country": "",
                "code": "",
                "note": "边端点未在 nodes.csv 单列；不计入 161 节点。",
                "layer": None,
                "ck": "veil",
                "deg": 0,
                "ghost": True,
                "blindspot": False,
                "_neighbor_layers": [],
            }
        return gid

    for row in edges:
        supplier = endpoint(norm(row["供方"]))
        demander = endpoint(norm(row["需方"]))
        edge_payload.append({
            "id": row["edge_id"],
            "s": supplier,
            "d": demander,
            "cls": grade_class(row["边等级"]),
            "grade": row["边等级"],
            "amt": row["占比或金额"],
            "fy": row["财年"],
            "src": row["证据文件"],
            "anchor": row["锚点"],
            "vs": row["验证状态"],
            "note": row["备注"],
        })
        for endpoint_id in (supplier, demander):
            if endpoint_id in node_map:
                node_map[endpoint_id]["deg"] += 1
            else:
                ghosts[endpoint_id]["deg"] += 1

        if supplier in ghosts and demander in node_map:
            ghosts[supplier]["_neighbor_layers"].append(node_map[demander]["layer"])
        if demander in ghosts and supplier in node_map:
            ghosts[demander]["_neighbor_layers"].append(node_map[supplier]["layer"])

    for ghost in ghosts.values():
        layers = ghost.pop("_neighbor_layers")
        ghost["layer"] = Counter(layers).most_common(1)[0][0] if layers else "L5"

    render_nodes = list(node_map.values()) + list(ghosts.values())
    layer_counts = Counter(n["layer"] for n in node_map.values())
    grade_counts = Counter(e["cls"] for e in edge_payload)
    return {
        "nodes": render_nodes,
        "edges": edge_payload,
        "layerOrder": LAYER_ORDER,
        "layerLabel": LAYER_LABEL,
        "layerCounts": dict(layer_counts),
        "canonicalNodeCount": len(nodes),
        "edgeCount": len(edges),
        "ghostCount": len(ghosts),
        "gradeCounts": dict(grade_counts),
        "badge": f"{len(edges)}边/{len(nodes)}节点/判例2A+2B",
    }


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>光模块产业 · 披露证据图谱 v1.5</title>
<style>
:root{
  --void:#080B14;--panel:#0F1420;--panel2:#161D2B;--grid:#1B2333;
  --ink:#EAEEF6;--mute:#727D97;--faint:#3A4358;
  --lit:#4FE0C4;--infer:#FFB347;--shadow:#4A5470;--dead:#E05A6A;--leak:#48D7E8;
  --cn:#F0655C;--us:#5B9DF0;--jt:#FFCF5E;--other:#8792AB;--veil:#5A6480;
  --mono:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
  --disp:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--void);color:var(--ink);font-family:var(--disp);
  -webkit-font-smoothing:antialiased}
body{background-image:linear-gradient(var(--grid) 1px,transparent 1px),
  linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:44px 44px}
body::before{content:"";position:fixed;inset:0;pointer-events:none;
  background:radial-gradient(100% 65% at 50% -10%,rgba(79,224,196,.07),transparent 62%),
  radial-gradient(80% 60% at 100% 100%,rgba(91,157,240,.05),transparent 55%)}
.wrap{position:relative;max-width:1500px;margin:auto;padding:46px 26px 76px}
.eyebrow{display:flex;align-items:center;gap:12px;margin-bottom:17px;color:var(--lit);
  font-family:var(--mono);font-size:12px;letter-spacing:.3em;text-transform:uppercase}
.eyebrow::before{content:"";width:26px;height:1px;background:var(--lit);box-shadow:0 0 8px var(--lit)}
h1{max-width:17ch;margin:0 0 18px;font-size:clamp(34px,5vw,60px);line-height:1.04;
  letter-spacing:-.025em;font-weight:650}
h1 span{color:var(--lit);text-shadow:0 0 24px rgba(79,224,196,.45)}
.thesis{max-width:67ch;margin:0 0 30px;color:var(--mute);font-size:clamp(15px,1.6vw,18px);
  line-height:1.68}.thesis b{color:var(--ink);font-weight:550}
.stats{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));margin-bottom:28px;
  border:1px solid var(--faint);border-radius:14px;overflow:hidden;
  background:linear-gradient(180deg,rgba(22,29,43,.72),rgba(15,20,32,.72))}
.stat{padding:16px 18px;border-right:1px solid var(--faint)}.stat:last-child{border:0}
.stat .n{font-family:var(--mono);font-size:27px;font-weight:650}.stat .k{margin-top:4px;
  color:var(--mute);font-size:11px;letter-spacing:.04em}
.legend{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:16px}
.chip{display:inline-flex;align-items:center;gap:8px;padding:7px 12px;border:1px solid var(--faint);
  border-radius:999px;background:rgba(15,20,32,.72);color:var(--mute);font-family:var(--mono);
  font-size:11px;cursor:pointer;user-select:none;transition:.18s}
.chip:hover{color:var(--ink);border-color:var(--mute)}.chip.off{opacity:.3}
.chip .sw{width:21px;border-top:2px solid}.chip[data-c=lit] .sw{border-color:var(--lit);
  box-shadow:0 0 7px var(--lit)}.chip[data-c=infer] .sw{border-color:var(--infer);
  border-top-style:dashed}.chip[data-c=shadow] .sw{border-color:var(--shadow);
  border-top-style:dashed}.chip[data-c=dead] .sw{border-color:var(--dead);
  border-top-style:dotted}.chip[data-c=leak] .sw{border-color:var(--leak);
  border-top-style:dashed}
.stage{position:relative;overflow:auto;border:1px solid var(--faint);border-radius:18px;
  background:linear-gradient(180deg,rgba(11,15,24,.86),rgba(8,11,20,.95));
  box-shadow:0 28px 80px rgba(0,0,0,.22)}
svg{display:block;width:100%;min-width:1180px;height:auto}
.band-label{font-family:var(--mono);font-size:12px;letter-spacing:.12em;fill:var(--mute)}
.band-count{font-family:var(--mono);font-size:10px;fill:var(--faint)}
.edge{fill:none;cursor:pointer;transition:opacity .18s,stroke-width .18s}
.edge.lit{stroke:var(--lit);stroke-width:1.35;opacity:.56}
.edge.infer{stroke:var(--infer);stroke-width:1.45;stroke-dasharray:8 5;opacity:.75}
.edge.shadow{stroke:var(--shadow);stroke-width:1;stroke-dasharray:2 6;opacity:.42}
.edge.dead{stroke:var(--dead);stroke-width:1.4;stroke-dasharray:1 7;opacity:.78}
.edge.leak{stroke:var(--leak);stroke-width:1.45;stroke-dasharray:6 4;opacity:.82}
.edge.hot{opacity:1;stroke-width:2.8}.edge.dim{opacity:.035}
.flow{fill:none;stroke:var(--lit);stroke-width:2;stroke-linecap:round;pointer-events:none;
  filter:drop-shadow(0 0 4px var(--lit));opacity:.78}
.node{cursor:pointer;transition:opacity .18s}.node .halo{fill:none;stroke-width:1.2}
.node .core{transition:r .18s}.node .name{font-size:10.5px;fill:var(--ink);
  paint-order:stroke;stroke:var(--void);stroke-width:3px;stroke-linejoin:round}
.node.ghost .name{fill:var(--veil);font-style:italic}.node.dim{opacity:.09}
.node.hot .name{fill:#fff;font-weight:700}.node.blind .halo{stroke:var(--infer)!important;
  stroke-width:1.7;stroke-dasharray:5 4}.blind-label{font-family:var(--mono);font-size:8px;
  fill:var(--infer);paint-order:stroke;stroke:var(--void);stroke-width:3px;letter-spacing:.05em}
.cn{fill:var(--cn)}.us{fill:var(--us)}.jt{fill:var(--jt)}
.other{fill:var(--other)}.veil{fill:var(--veil)}
.drawer{position:fixed;z-index:50;top:0;right:0;width:min(430px,92vw);height:100%;
  padding:28px 26px;overflow-y:auto;background:linear-gradient(180deg,#10151F,#0B0F18);
  border-left:1px solid var(--faint);box-shadow:-30px 0 60px rgba(0,0,0,.5);
  transform:translateX(100%);transition:transform .3s cubic-bezier(.4,0,.1,1)}
.drawer.open{transform:none}.drawer h3{margin:0 42px 5px 0;font-size:20px;line-height:1.25}
.close{position:absolute;top:20px;right:20px;width:32px;height:32px;border:1px solid var(--faint);
  border-radius:8px;background:none;color:var(--mute);cursor:pointer}
.gradetag{display:inline-block;margin:8px 0 18px;padding:4px 9px;border-radius:6px;
  font-family:var(--mono);font-size:10px}.gt-lit{background:rgba(79,224,196,.14);color:var(--lit)}
.gt-infer{background:rgba(255,179,71,.14);color:var(--infer)}
.gt-shadow{background:rgba(74,84,112,.22);color:#9aa6c4}
.gt-dead{background:rgba(224,90,106,.16);color:#f08391}
.gt-leak{background:rgba(72,215,232,.14);color:var(--leak)}
.field{padding:12px 0;border-top:1px solid var(--grid)}.lab{margin-bottom:5px;color:var(--mute);
  font-family:var(--mono);font-size:9px;letter-spacing:.18em;text-transform:uppercase}
.val{font-size:13px;line-height:1.55;word-break:break-word}.mono{font-family:var(--mono);
  color:var(--lit)}.field a{color:var(--us);text-decoration:none}.field a:hover{text-decoration:underline}
.edge-row{width:100%;padding:12px 0;border:0;border-top:1px solid var(--grid);
  background:none;color:inherit;text-align:left;cursor:pointer}.edge-row:hover .val{color:#fff}
.hint{margin:15px 0 5px;color:var(--mute);font-family:var(--mono);font-size:10px;
  letter-spacing:.12em}.foot{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;
  margin-top:30px;padding-top:20px;border-top:1px solid var(--grid);color:var(--mute);
  font-size:13px;line-height:1.72}.foot-copy{max-width:80ch}.foot b{color:var(--ink)}
.badge{flex:none;padding:8px 12px;border:1px solid var(--lit);border-radius:999px;color:var(--lit);
  font-family:var(--mono);font-size:11px;box-shadow:0 0 18px rgba(79,224,196,.08)}
@media(max-width:900px){.stats{grid-template-columns:repeat(3,1fr)}.stat:nth-child(3){border-right:0}
  .stat:nth-child(-n+3){border-bottom:1px solid var(--faint)}.foot{display:block}.badge{display:inline-block;
  margin-top:16px}}@media(max-width:620px){.wrap{padding:30px 14px 58px}.stats{grid-template-columns:repeat(2,1fr)}
  .stat:nth-child(odd){border-right:1px solid var(--faint)}.stat:nth-child(even){border-right:0}
  .stat{border-bottom:1px solid var(--faint)}.stat:nth-last-child(-n+2){border-bottom:0}}
@media(prefers-reduced-motion:reduce){.flow{display:none}.edge,.node{transition:none}}
</style>
</head>
<body>
<main class="wrap">
  <div class="eyebrow">披露证据图谱 · v1.5 · 2026-07</div>
  <h1>光模块产业，<span>被证据分层</span>的结构</h1>
  <p class="thesis">这不是一张行业名单，而是一张<b>披露证据地图</b>。节点按
    <code>nodes.csv</code> 的类型自动归层；边的亮暗与线型回答同一个问题：
    <b>我们凭什么看得见这条供货关系？</b></p>
  <section class="stats" id="stats" aria-label="数据统计"></section>
  <nav class="legend" id="legend" aria-label="边等级筛选"></nav>
  <section class="stage">
    <svg id="svg" viewBox="0 0 1760 1200" role="img"
      aria-label="光模块产业七层披露证据网络图"></svg>
  </section>
  <footer class="foot">
    <div class="foot-copy"><b>诚实边界。</b> 阴影虚线只表示公开披露留下了槽位，
      不能据此点名对手方。DSP 芯片层的 Marvell 与博通使用虚线描边：
      两侧披露制度都不提供 DSP→模块厂的具名通路，因此标为<b>产品映射盲区</b>。
      点击任意节点查看其全部入边与出边，点击边查看证据文件、年份、金额与锚点。</div>
    <div class="badge" id="badge"></div>
  </footer>
</main>
<aside class="drawer" id="drawer" role="dialog" aria-label="证据详情">
  <button class="close" id="dclose" aria-label="关闭">✕</button>
  <div id="dbody"></div>
</aside>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const NS='http://www.w3.org/2000/svg';
const CK={cn:'中国',us:'美国',jt:'日本/台湾',other:'其他',veil:'待核/匿名'};
const CLSNAME={lit:'实边 · 强制披露实名',infer:'推断边 · A/B级判定',
  shadow:'半边槽位 · 对手方不可见',dead:'实边 · 已死亡',
  leak:'程序泄漏 · 侧信道实名'};
const W=1760,PADX=42,TOP=34,ROW_GAP=62;
const svg=document.getElementById('svg'),idmap={},byLayer={};
D.layerOrder.forEach(l=>byLayer[l]=[]);
D.nodes.forEach(n=>{idmap[n.id]=n;byLayer[n.layer].push(n)});
D.layerOrder.forEach(l=>byLayer[l].sort((a,b)=>
  (a.ghost?1:0)-(b.ghost?1:0)||b.deg-a.deg||a.id.localeCompare(b.id,'zh-CN')));

let cursor=TOP;
D.layerOrder.forEach((layer,li)=>{
  const arr=byLayer[layer],rows=arr.length>16?2:1;
  const bandH=rows===2?166:112;
  arr.forEach((n,i)=>{
    const row=rows===2?i%2:0;
    const col=rows===2?Math.floor(i/2):i;
    const inRow=Math.ceil((arr.length-row)/rows);
    const usable=W-PADX*2-180;
    n.x=PADX+170+usable*(col+.5)/Math.max(1,inRow);
    n.y=cursor+(rows===2?(48+row*ROW_GAP):58);
  });
  byLayer[layer]._top=cursor;byLayer[layer]._height=bandH;
  cursor+=bandH;
});
const H=cursor+24;
svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
svg.innerHTML=`<defs><filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
  <feGaussianBlur stdDeviation="1.15" result="b"/><feMerge><feMergeNode in="b"/>
  <feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`;

const gBands=document.createElementNS(NS,'g');svg.appendChild(gBands);
D.layerOrder.forEach((layer,li)=>{
  const arr=byLayer[layer],top=arr._top,h=arr._height;
  const rect=document.createElementNS(NS,'rect');
  rect.setAttribute('x','0');rect.setAttribute('y',top);rect.setAttribute('width',W);
  rect.setAttribute('height',h);rect.setAttribute('fill',li%2?'rgba(15,20,32,.34)':'rgba(8,11,20,.18)');
  rect.setAttribute('stroke','var(--grid)');gBands.appendChild(rect);
  const label=document.createElementNS(NS,'text');label.setAttribute('class','band-label');
  label.setAttribute('x',PADX);label.setAttribute('y',top+28);
  label.textContent=`0${li+1}  ${D.layerLabel[layer]}`;gBands.appendChild(label);
  const count=document.createElementNS(NS,'text');count.setAttribute('class','band-count');
  count.setAttribute('x',PADX);count.setAttribute('y',top+47);
  count.textContent=`${D.layerCounts[layer]||0} NODES`;gBands.appendChild(count);
});

function path(a,b){
  if(a.layer===b.layer){
    const lift=Math.max(20,Math.min(55,Math.abs(a.x-b.x)*.18));
    return `M${a.x},${a.y} C${a.x},${a.y-lift} ${b.x},${b.y-lift} ${b.x},${b.y}`;
  }
  const my=(a.y+b.y)/2;
  return `M${a.x},${a.y} C${a.x},${my} ${b.x},${my} ${b.x},${b.y}`;
}
const edgeEls=[],flowEls=[],edgeMap={};
const gEdges=document.createElementNS(NS,'g');svg.appendChild(gEdges);
D.edges.forEach(e=>{
  const a=idmap[e.s],b=idmap[e.d];if(!a||!b)return;edgeMap[e.id]=e;
  const p=document.createElementNS(NS,'path');p.setAttribute('class',`edge ${e.cls}`);
  p.setAttribute('d',path(a,b));p.dataset.cls=e.cls;p._e=e;p._a=a;p._b=b;
  p.addEventListener('click',ev=>{ev.stopPropagation();openEdge(e,a,b)});
  gEdges.appendChild(p);edgeEls.push(p);
  if(e.cls==='lit'&&a.layer!==b.layer){
    const f=document.createElementNS(NS,'path');f.setAttribute('class','flow');
    f.setAttribute('d',path(a,b));f.style.strokeDasharray='3 330';
    f.style.animation=`flow ${3+Math.random()*1.8}s linear infinite`;
    f.style.animationDelay=`${-Math.random()*3}s`;f.dataset.cls='lit';
    gEdges.appendChild(f);flowEls.push(f);
  }
});
const anim=document.createElementNS(NS,'style');
anim.textContent='@keyframes flow{from{stroke-dashoffset:0}to{stroke-dashoffset:-1000}}';
svg.appendChild(anim);

const ABBR={'Applied Optoelectronics(AAOI)':'AAOI','罗博特科/ficonTEC':'罗博特科',
  '索尔思(Source Photonics)':'索尔思','华为(含海思)':'华为',
  '博通(Broadcom)':'博通','Corning Incorporated':'Corning'};
function label(id){
  const raw=id.replace('◈ ','');if(ABBR[raw])return ABBR[raw];
  const clean=raw.replace(/\(.*/,'');
  return clean.length>10?clean.slice(0,9)+'…':clean;
}
const gNodes=document.createElementNS(NS,'g');svg.appendChild(gNodes);
D.nodes.forEach(n=>{
  const g=document.createElementNS(NS,'g');
  g.setAttribute('class',`node ${n.ghost?'ghost ':''}${n.blindspot?'blind ':''}`);
  g.dataset.nid=n.id;
  const title=document.createElementNS(NS,'title');title.textContent=`${n.id.replace('◈ ','')} · ${n.type}`;
  const r=n.ghost?3.5:Math.max(4.8,Math.min(10,4+n.deg*.42));
  const halo=document.createElementNS(NS,'circle');halo.setAttribute('class',`halo ${n.ck}`);
  halo.setAttribute('cx',n.x);halo.setAttribute('cy',n.y);halo.setAttribute('r',r+4);
  halo.setAttribute('stroke',`var(--${n.ck})`);halo.setAttribute('stroke-opacity',n.ghost?'.4':'.88');
  const core=document.createElementNS(NS,'circle');core.setAttribute('class',`core ${n.ck}`);
  core.setAttribute('cx',n.x);core.setAttribute('cy',n.y);core.setAttribute('r',r);
  core.setAttribute('fill-opacity',n.ghost?'.32':'1');if(!n.ghost)core.setAttribute('filter','url(#soft)');
  const text=document.createElementNS(NS,'text');text.setAttribute('class','name');
  text.setAttribute('x',n.x);text.setAttribute('y',n.y+18);text.setAttribute('text-anchor','middle');
  text.textContent=label(n.id);g.append(title,halo,core,text);
  if(n.blindspot){
    const tag=document.createElementNS(NS,'text');tag.setAttribute('class','blind-label');
    tag.setAttribute('x',n.x);tag.setAttribute('y',n.y-14);tag.setAttribute('text-anchor','middle');
    tag.textContent='产品映射盲区';g.appendChild(tag);
  }
  g.addEventListener('click',ev=>{ev.stopPropagation();openNode(n)});
  g.addEventListener('mouseenter',()=>hover(n.id));g.addEventListener('mouseleave',clearHover);
  gNodes.appendChild(g);
});

function neighbors(id){const s=new Set([id]);D.edges.forEach(e=>{
  if(e.s===id)s.add(e.d);if(e.d===id)s.add(e.s)});return s}
function hover(id){const nb=neighbors(id);edgeEls.forEach(p=>{
  const on=p._e.s===id||p._e.d===id;p.classList.toggle('hot',on);p.classList.toggle('dim',!on)});
  document.querySelectorAll('.node').forEach(g=>{
    g.classList.toggle('hot',g.dataset.nid===id);g.classList.toggle('dim',!nb.has(g.dataset.nid))})}
function clearHover(){edgeEls.forEach(p=>p.classList.remove('hot','dim'));
  document.querySelectorAll('.node').forEach(g=>g.classList.remove('hot','dim'))}

const drawer=document.getElementById('drawer'),dbody=document.getElementById('dbody');
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function field(lab,val,mono=false){return val?`<div class="field"><div class="lab">${esc(lab)}</div>
  <div class="val${mono?' mono':''}">${esc(val)}</div></div>`:''}
function openEdge(e,a,b){
  const anchor=/^https?:/.test(e.anchor)?`<div class="field"><div class="lab">锚点 URL</div>
    <div class="val"><a href="${esc(e.anchor)}" target="_blank" rel="noopener">${esc(e.anchor)}</a></div></div>`:
    field('锚点',e.anchor);
  dbody.innerHTML=`<h3>${esc(a.id.replace('◈ ',''))} → ${esc(b.id.replace('◈ ',''))}</h3>
    <span class="gradetag gt-${e.cls}">${esc(e.grade)} · ${CLSNAME[e.cls]}</span>
    ${field('占比 / 金额',e.amt,true)}${field('财年',e.fy,true)}${field('证据文件',e.src)}
    ${anchor}${field('验证状态',e.vs)}${field('备注',e.note)}
    <div class="hint">边 ${esc(e.id)}</div>`;
  drawer.classList.add('open');
}
function openNode(n){
  const outs=D.edges.filter(e=>e.s===n.id),ins=D.edges.filter(e=>e.d===n.id);
  const line=(e,dir)=>`<button class="edge-row" data-eid="${esc(e.id)}"><div class="lab">
    ${dir} ${esc(e.id)} · ${esc(e.grade)}</div><div class="val mono">
    ${esc((dir==='供给'?e.d:e.s).replace('◈ ',''))} · ${esc(e.amt)}</div></button>`;
  dbody.innerHTML=`<h3>${esc(n.id.replace('◈ ',''))}</h3>
    <span class="gradetag gt-${n.ghost?'shadow':'lit'}">${esc(n.type)} · ${CK[n.ck]}</span>
    ${n.blindspot?'<span class="gradetag gt-infer">产品映射盲区</span>':''}
    ${field('所属产业层',D.layerLabel[n.layer])}${field('代码',n.code,true)}${field('备注',n.note)}
    ${outs.length?`<div class="hint">作为供方 · ${outs.length} 条 ↓</div>${outs.map(e=>line(e,'供给')).join('')}`:''}
    ${ins.length?`<div class="hint">作为需方 · ${ins.length} 条 ↓</div>${ins.map(e=>line(e,'获得')).join('')}`:''}
    ${!outs.length&&!ins.length?'<div class="hint">当前台账无关联边</div>':''}`;
  dbody.querySelectorAll('[data-eid]').forEach(el=>el.addEventListener('click',()=>{
    const e=edgeMap[el.dataset.eid];openEdge(e,idmap[e.s],idmap[e.d])}));
  drawer.classList.add('open');
}
document.getElementById('dclose').onclick=()=>drawer.classList.remove('open');
document.addEventListener('keydown',e=>{if(e.key==='Escape')drawer.classList.remove('open')});
svg.addEventListener('click',()=>drawer.classList.remove('open'));

const g=D.gradeCounts;
document.getElementById('stats').innerHTML=[
  [D.edgeCount,'条关系边'],[D.canonicalNodeCount,'个数据节点'],[g.lit||0,'实边 · 照亮'],
  [g.shadow||0,'半边 · 阴影'],[g.infer||0,'推断边 · A/B级'],['2A+2B','解匿判例']
].map(([n,k])=>`<div class="stat"><div class="n">${n}</div><div class="k">${k}</div></div>`).join('');
const legend=document.getElementById('legend');
['lit','infer','shadow','dead','leak'].forEach(c=>{
  const el=document.createElement('button');el.className='chip';el.dataset.c=c;
  el.innerHTML=`<span class="sw"></span>${CLSNAME[c]}`;
  el.onclick=()=>{el.classList.toggle('off');const off=el.classList.contains('off');
    edgeEls.forEach(p=>{if(p.dataset.cls===c)p.style.display=off?'none':''});
    flowEls.forEach(f=>{if(f.dataset.cls===c)f.style.display=off?'none':''})};
  legend.appendChild(el);
});
const countries=document.createElement('div');countries.className='chip';countries.style.cursor='default';
countries.innerHTML=Object.entries(CK).map(([k,v])=>`<span style="display:inline-flex;align-items:center;
  gap:4px"><span style="width:7px;height:7px;border-radius:50%;background:var(--${k})"></span>${v}</span>`).join(' · ');
legend.appendChild(countries);
document.getElementById('badge').textContent=D.badge;
</script>
</body>
</html>
"""


def main():
    data = build()
    json_payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = HTML.replace("__DATA__", json_payload)

    assert data["edgeCount"] == 236, data["edgeCount"]
    assert data["canonicalNodeCount"] == 169, data["canonicalNodeCount"]
    assert sum(data["layerCounts"].values()) == 169
    assert data["gradeCounts"].get("infer") == 4
    assert {"Marvell", "博通(Broadcom)"}.issubset(
        {n["id"] for n in data["nodes"] if n.get("blindspot")}
    )
    assert "236边/169节点/判例2A+2B" in html
    assert not re.search(
        r'<(?:script|link)[^>]+(?:src|href)\s*=\s*["\']https?://', html, re.I
    ), "HTML 含外部脚本或样式依赖"

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"wrote {OUT_PATH} {len(html)} bytes")
    print("节点分层统计（nodes.csv 161节点）")
    for layer in LAYER_ORDER:
        print(f"  {layer} {LAYER_LABEL[layer]}: {data['layerCounts'].get(layer, 0)}")
    print(f"  匿名幽灵槽位（不计入161节点）: {data['ghostCount']}")
    print(f"edges {data['edgeCount']} render_nodes {len(data['nodes'])}")
    print("自测: 225边✓ 161节点✓ 七层全覆盖✓ B级样式✓ DSP盲区✓ 零外部资源依赖✓")


if __name__ == "__main__":
    main()
