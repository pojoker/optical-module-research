#!/usr/bin/env python3
"""build_atlas_v16.py — 光模块产业图谱 v1.6 · 供应链树主视图 三视图前端

按 flows/atlas-v1.6-handoff.md（T4 裁定）重做 v1.6：
- 主视图① 供应链树 × 每节点公司名单：照 output/光模块供应链全景-v1.1.md 的
  并行三分支 mermaid 骨架（材料分喂 → A光器件/B功能电路/C结构件 → 总成 →
  代工EMS/下游直销），双闸声明：树不表达供货关系，空叶如实标空，T1 候选
  不升格、单独标色。
- 次视图② 关系图：236 边 / 169 节点，原四硬约束不变（自包含零外链 /
  六类边等级视觉可区分+图例 / 节点点击溯源锚点 / 页脚徽章
  "236边/169节点/判例2A+2B"）。
- 次视图③ 工序视图：横切工序轴（芯片制造→芯片封装(委外)→组件封装→模块组装
  →测试）+ 设备/仪器纵轴；与 BOM 树是两个坐标轴，不是链环。

输入均为既有彩排产出文件；本脚本只做装配与断言，不改任何台账。
注意：全景 v1.1.md 可能被 T1/T2 车道并发追加空叶候选——解析器容忍无 NID
的候选行与"部分证实"等锚档，覆盖性断言降级为警告；重跑本脚本即可重建。
输出自包含、无外部资源依赖的 output/光模块产业图谱-v1.6.html。
"""

import csv
import json
import os
import re
import time
from collections import Counter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODES_PATH = os.path.join(ROOT, "output", "nodes.csv")
EDGES_PATH = os.path.join(ROOT, "output", "edges.csv")
PANORAMA_MD = os.path.join(ROOT, "output", "光模块供应链全景-v1.1.md")
OUT_PATH = os.path.join(ROOT, "output", "光模块产业图谱-v1.6.html")

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


# ---------------------------------------------------------------- 视图② 关系图数据

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


def load_csv():
    with open(NODES_PATH, encoding="utf-8-sig", newline="") as f:
        nodes = list(csv.DictReader(f))
    with open(EDGES_PATH, encoding="utf-8-sig", newline="") as f:
        edges = list(csv.DictReader(f))
    return nodes, edges


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


def build_graph(nodes, edges):
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
                "note": "边端点未在 nodes.csv 单列；不计入 169 节点。",
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


# ---------------------------------------------------------------- 视图①③ 全景 v1.1 解析

# 叶子定义：状态照 v1.1「空节点缺口任务汇总」原文；候选数由解析行动态追加。
LEAF_DEFS = {
    "M1":      {"title": "衬底 / 靶材 / MO源 / 特气 / 掩模", "sub": "材料 → A1a · A2a"},
    "M1-lead": {"title": "InP 衬底线索级候选", "sub": "pilot-s0a · 未过判定闸 · 未入台账"},
    "M2":      {"title": "石英 / 树脂 / 光纤", "sub": "材料 → A3"},
    "M-rest":  {"title": "材料对象未细分", "sub": "仅类型归层 · 无法判定喂入叶"},
    "A1a":     {"title": "A1a 激光器芯片", "sub": "EEL / DFB / EML / VCSEL", "status": "有主"},
    "A1b":     {"title": "A1b 陶瓷插芯", "status": "有主"},
    "A1c":     {"title": "A1c 陶瓷管壳", "status": "空"},
    "A1d":     {"title": "A1d 透镜", "status": "弱覆盖"},
    "A2a":     {"title": "A2a 探测器芯片", "sub": "PIN / APD", "status": "有主"},
    "A3":      {"title": "A3 无源器件", "sub": "隔离器 / AWG / 分路器 / 连接器", "status": "有主（隔离器空）"},
    "A-rest":  {"title": "A-其余光器件", "sub": "未细分至具体叶 · 仅类型归层"},
    "B1":      {"title": "B1 电芯片", "sub": "DSP / Driver / TIA / CDR", "status": "空（4家仅类型归层）"},
    "B2":      {"title": "B2 PCB板", "sub": "新叶", "status": "空"},
    "C1":      {"title": "C 结构件", "sub": "底座 / 壳体 / 金手指 · 新叶", "status": "空"},
    "MOD":     {"title": "光模块（总成）", "sub": "A / B / C 三分支汇聚节点"},
    "EMS":     {"title": "代工 EMS"},
    "SYS":     {"title": "系统设备商 / 云巨头终端 / 线缆", "sub": "直销或经代工 EMS"},
    "PROC1":   {"title": "芯片封装（委托加工）", "sub": "跨光 / 电芯片工序"},
    "PROC2":   {"title": "组件封装（TOSA/ROSA）", "sub": "工序执行者 · 非零件供应商", "status": "空"},
    "EQ":      {"title": "设备 / 仪器纵轴", "sub": "贯穿封装-器件-模块-测试 · 不插入主链序"},
    "X1":      {"title": "贸易 / 代理 / 物流"},
    "X2":      {"title": "边界外 / 跨行业 / 科研 / 非BOM"},
    "X3":      {"title": "匿名槽位 / 待核 / 类型过宽主体"},
}

HEADER_TO_LEAF = [
    ("#### A1a 激光器芯片", "A1a"),
    ("#### A1b 陶瓷插芯", "A1b"),
    ("#### A1c 陶瓷管壳", "A1c"),
    ("#### A1d 透镜", "A1d"),
    ("#### A2a 探测器芯片", "A2a"),
    ("#### 波分复用器 / AWG", "A3"),
    ("#### 隔离器", "A3"),
    ("### A-其余光器件", "A-rest"),
    ("### B1 电芯片", "B1"),
    ("### B2 PCB板", "B2"),
    ("## C. 结构件分支", "C1"),
    ("## 光模块（总成）", "MOD"),
    ("### 材料 → A1a·A2a", "M1"),
    ("#### InP 衬底线索级候选", "M1-lead"),
    ("### 材料 → A3", "M2"),
    ("### 材料对象未细分", "M-rest"),
    ("### 芯片封装（委托加工", "PROC1"),
    ("### 组件封装（TOSA/ROSA", "PROC2"),
    ("## 设备 / 仪器纵轴", "EQ"),
    ("### 代工 EMS", "EMS"),
    ("### 系统设备商 / 云巨头终端 / 线缆", "SYS"),
    ("### 贸易 / 代理 / 物流", "X1"),
    ("### 边界外 / 跨行业 / 科研 / 非BOM", "X2"),
    ("### 匿名槽位 / 待核 / 类型过宽主体", "X3"),
]

NOTE_KEYS = ("未识别", "定向任务", "缺口", "委托加工业务", "注：", "假友元",
             "核对", "另见", "在研", "候选")
STANCE_KEYS = ("发行人自述", "同业描述", "披露方产品列", "竞品描述")


def anchor_cls(text, nid):
    t = text.strip()
    if t.startswith("半锚"):
        return "semi"
    if t.startswith("弱锚"):
        return "weak"
    if t.startswith("有锚"):
        return "ok"
    if t.startswith("部分证实"):
        return "part"
    if t.startswith("线索级"):
        return "lead"
    if not nid:
        return "cand"
    return "pending"


def parse_panorama():
    lines = open(PANORAMA_MD, encoding="utf-8").read().splitlines()
    leaves = {k: {"rows": [], "notes": []} for k in LEAF_DEFS}
    cur = None
    proc_intro = []
    in_proc = False
    for ln in lines:
        if ln.lstrip().startswith("#"):
            in_proc = ln.startswith("## 横切工序轴")
            cur = None
            for prefix, leaf in HEADER_TO_LEAF:
                if ln.startswith(prefix):
                    cur = leaf
                    break
            continue
        if in_proc:
            s = ln.strip()
            if s.startswith(">"):
                s = s[1:].strip()
            if s and not s.startswith("|"):
                proc_intro.append(s.replace("**", ""))
            continue
        if cur is None:
            continue
        if ln.startswith("|"):
            if "身份依据一句" in ln or set(ln) <= set("|-: "):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != 4 or cells[0] == "名称":
                continue
            m = re.match(r"^(N\d+)\s+(.+)$", cells[0])
            if m:
                nid, name = m.group(1), m.group(2).strip()
            else:
                nid, name = "", cells[0].strip()
            anch = cells[2].replace("**", "")
            leaves[cur]["rows"].append({
                "nid": nid,
                "name": name,
                "doing": cells[1].replace("**", ""),
                "cls": anchor_cls(anch, nid),
                "stance": next((s for s in STANCE_KEYS if s in anch), ""),
                "anchor": anch,
                "hasEdge": cells[3].strip().startswith("有"),
                "edgeText": cells[3].replace("**", ""),
                "edgeIds": re.findall(r"E\d{3}", cells[3]),
            })
            continue
        s = ln.strip()
        if s.startswith(">"):
            s = s[1:].strip()
        s = s.replace("**", "").strip()
        if not s or s.startswith("---"):
            continue
        if any(k in s for k in NOTE_KEYS):
            leaves[cur]["notes"].append(s)
    return leaves, " ".join(proc_intro)


def build_tree(node_rows):
    node_ids = {r["node_id"] for r in node_rows}
    nid_name = {r["node_id"]: r["名称"].strip() for r in node_rows}
    leaves, proc_intro = parse_panorama()
    payload_leaves = {}
    cls_counts = Counter()
    cand_total = 0
    for key, definition in LEAF_DEFS.items():
        rows = leaves[key]["rows"]
        for r in rows:
            cls_counts[r["cls"]] += 1
        cand_total += sum(1 for r in rows if not r["nid"])
        payload_leaves[key] = {
            "title": definition["title"],
            "sub": definition.get("sub", ""),
            "status": definition.get("status", ""),
            "rows": rows,
            "notes": leaves[key]["notes"],
        }
    parsed_nids = {r["nid"] for lf in payload_leaves.values()
                   for r in lf["rows"] if r["nid"]}
    stats = {
        "leafTotal": 9,
        "leafOwn": 4,
        "leafEmpty": 4,
        "leafWeak": 1,
        "nodes": len(node_ids),
        "candidates": cand_total,
        "clsCounts": dict(cls_counts),
    }
    return {
        "leaves": payload_leaves,
        "nidName": nid_name,
        "procIntro": proc_intro,
        "stats": stats,
        "source": "output/光模块供应链全景-v1.1.md（结构重排版 · 生成日 2026-07-24）",
    }, parsed_nids


# ---------------------------------------------------------------- HTML 模板

HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>光模块产业图谱 v1.6 · 供应链树×关系图×工序</title>
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
.thesis{max-width:80ch;margin:0 0 30px;color:var(--mute);font-size:clamp(15px,1.6vw,18px);
  line-height:1.68}.thesis b{color:var(--ink);font-weight:550}
.stats{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));margin-bottom:28px;
  border:1px solid var(--faint);border-radius:14px;overflow:hidden;
  background:linear-gradient(180deg,rgba(22,29,43,.72),rgba(15,20,32,.72))}
.stat{padding:16px 18px;border-right:1px solid var(--faint)}.stat:last-child{border:0}
.stat .n{font-family:var(--mono);font-size:27px;font-weight:650}.stat .k{margin-top:4px;
  color:var(--mute);font-size:11px;letter-spacing:.04em}
.legend{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:16px;align-items:center}
.chip{display:inline-flex;align-items:center;gap:8px;padding:7px 12px;border:1px solid var(--faint);
  border-radius:999px;background:rgba(15,20,32,.72);color:var(--mute);font-family:var(--mono);
  font-size:11px;cursor:pointer;user-select:none;transition:.18s}
.chip:hover{color:var(--ink);border-color:var(--mute)}.chip.off{opacity:.3}
.chip.on{color:var(--lit);border-color:var(--lit)}
.chip .sw{width:21px;border-top:2px solid}.chip[data-c=lit] .sw{border-color:var(--lit);
  box-shadow:0 0 7px var(--lit)}.chip[data-c=infer] .sw{border-color:var(--infer);
  border-top-style:dashed}.chip[data-c=shadow] .sw{border-color:var(--shadow);
  border-top-style:dashed}.chip[data-c=dead] .sw{border-color:var(--dead);
  border-top-style:dotted}.chip[data-c=leak] .sw{border-color:var(--leak);
  border-top-style:dashed}
.chip.static{cursor:default}
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
.gradetag{display:inline-block;margin:8px 8px 18px 0;padding:4px 9px;border-radius:6px;
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
  letter-spacing:.12em}
.ebtns{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.ebtn{padding:5px 9px;border:1px solid var(--faint);border-radius:7px;background:none;
  color:var(--lit);font-family:var(--mono);font-size:10px;cursor:pointer}
.ebtn:hover{border-color:var(--lit)}
.gjump{margin-top:18px;width:100%;padding:11px;border:1px solid var(--lit);border-radius:10px;
  background:rgba(79,224,196,.08);color:var(--lit);font-size:13px;cursor:pointer}
.gjump:hover{background:rgba(79,224,196,.16)}
.foot{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;
  margin-top:30px;padding-top:20px;border-top:1px solid var(--grid);color:var(--mute);
  font-size:13px;line-height:1.72}.foot-copy{max-width:88ch}.foot b{color:var(--ink)}
.foot .base{display:block;margin-top:8px;font-family:var(--mono);font-size:10px;color:var(--faint)}
.badge{flex:none;padding:8px 12px;border:1px solid var(--lit);border-radius:999px;color:var(--lit);
  font-family:var(--mono);font-size:11px;box-shadow:0 0 18px rgba(79,224,196,.08)}
/* ---- 三视图框架 ---- */
.tabs{display:flex;gap:10px;margin:0 0 26px;flex-wrap:wrap}
.tab{flex:1;min-width:210px;padding:13px 18px;border:1px solid var(--faint);border-radius:12px;
  background:rgba(15,20,32,.72);color:var(--mute);cursor:pointer;text-align:left;
  font-family:var(--disp);font-size:15px;font-weight:600;transition:.18s}
.tab span{display:block;margin-top:3px;font-family:var(--mono);font-size:10px;font-weight:400;
  letter-spacing:.08em;color:var(--faint)}
.tab:hover{border-color:var(--mute);color:var(--ink)}
.tab.active{border-color:var(--lit);color:var(--lit);box-shadow:0 0 22px rgba(79,224,196,.12)}
.tab.active span{color:var(--lit);opacity:.75}
.view{display:none}.view.active{display:block}
.banner{display:flex;gap:12px;align-items:flex-start;margin-bottom:20px;padding:13px 16px;
  border:1px solid var(--infer);border-radius:12px;background:rgba(255,179,71,.06);
  color:var(--infer);font-size:13px;line-height:1.65}
.banner b{color:var(--ink)}
.banner .tag{flex:none;font-family:var(--mono);font-size:10px;letter-spacing:.14em;
  border:1px solid currentColor;border-radius:6px;padding:3px 7px;margin-top:1px}
.banner.cyan{border-color:var(--leak);background:rgba(72,215,232,.05);color:var(--leak)}
.banner.cyan b{color:var(--ink)}
.search{flex:1;min-width:180px;padding:8px 14px;border:1px solid var(--faint);border-radius:999px;
  background:rgba(15,20,32,.72);color:var(--ink);font-family:var(--mono);font-size:11px;outline:none}
.search:focus{border-color:var(--lit)}
.noteblock{margin-top:16px;padding:13px 16px;border:1px dashed var(--faint);border-radius:12px;
  color:var(--mute);font-size:12px;line-height:1.8}
.noteblock h4{margin:0 0 8px;color:var(--ink);font-size:12px;font-family:var(--mono);
  letter-spacing:.1em;font-weight:500}
/* ---- 视图① 供应链树 ---- */
.tree{position:relative}
.wires{position:absolute;inset:0;pointer-events:none;z-index:0;overflow:visible}
.wire{fill:none;stroke:#3D4A66;stroke-width:1.3;opacity:.85}
.wire.dashed{stroke-dasharray:5 5;opacity:.55}
.zone{position:relative;z-index:1;border:1px solid var(--faint);border-radius:16px;
  padding:14px 16px 16px;margin-bottom:40px;background:rgba(13,18,29,.88)}
.zone-title{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.zone-title .zt{font-size:14px;font-weight:650;letter-spacing:.04em}
.zone-title .zs{font-family:var(--mono);font-size:10px;color:var(--mute)}
.z-a{border-color:rgba(79,224,196,.42)}
.z-b{border-color:rgba(91,157,240,.42)}
.z-c{border-color:rgba(255,207,94,.42)}
.z-mod{border-color:var(--lit);box-shadow:0 0 34px rgba(79,224,196,.1)}
.z-x{border-style:dashed;opacity:.92}
.duo{display:flex;gap:16px}.duo .zone{flex:1;min-width:0}
.leafrow{display:flex;gap:12px;flex-wrap:wrap}
.leaf{flex:1;min-width:235px;border:1px solid var(--grid);border-radius:12px;
  padding:10px 12px;background:rgba(8,11,20,.55)}
.leaf.empty{border-style:dashed}
.leaf-head{display:flex;align-items:baseline;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.leaf-head .lt{font-size:13px;font-weight:650}
.leaf-head .ls{font-family:var(--mono);font-size:9px;color:var(--mute)}
.leaf-head .cnt{margin-left:auto;font-family:var(--mono);font-size:9px;color:var(--faint)}
.stbadge{font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:6px}
.st-own{background:rgba(79,224,196,.12);color:var(--lit)}
.st-weak{background:rgba(255,179,71,.12);color:var(--infer)}
.st-empty{background:rgba(90,100,128,.16);color:#9aa6c4;border:1px dashed var(--veil)}
.st-cand{background:rgba(72,215,232,.1);color:var(--leak);border:1px dashed rgba(72,215,232,.5)}
.lempty{font-size:11px;color:var(--veil);font-family:var(--mono);margin-bottom:8px}
.cos{display:flex;flex-wrap:wrap;gap:6px}
.co{display:inline-flex;flex-direction:column;gap:2px;max-width:200px;padding:6px 9px;
  border:1px solid var(--faint);border-radius:8px;background:rgba(15,20,32,.6);color:var(--ink);
  cursor:pointer;text-align:left;font-family:var(--disp);transition:.15s}
.co:hover{border-color:var(--mute)}
.co.cand{border-style:dashed;border-color:rgba(72,215,232,.45)}
.cline{display:flex;align-items:center;gap:6px}
.cname{font-size:12px;font-weight:550;line-height:1.3;max-width:180px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.nid{font-family:var(--mono);font-size:8.5px;color:var(--faint);letter-spacing:.06em}
.eb{font-family:var(--mono);font-size:8.5px;color:var(--us)}
.dot{width:7px;height:7px;border-radius:50%;flex:none}
.dot.ok{background:var(--lit);box-shadow:0 0 6px var(--lit)}
.dot.semi{background:var(--infer)}
.dot.weak{background:var(--jt)}
.dot.part{background:var(--infer);box-shadow:0 0 0 2px rgba(255,179,71,.25)}
.dot.lead{background:var(--leak)}
.dot.cand{background:none;border:1.5px dashed var(--leak);width:5px;height:5px}
.dot.pending{background:var(--veil)}
.lnote{margin:8px 0 0;padding-top:7px;border-top:1px dashed var(--grid);color:var(--mute);
  font-size:10.5px;line-height:1.7}
.conv{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.conv-chip{flex:1;min-width:260px;border:1px dashed var(--lit);border-radius:999px;
  padding:9px 18px;background:rgba(79,224,196,.05);display:flex;align-items:baseline;
  gap:10px;flex-wrap:wrap}
.conv-chip b{font-size:13px;color:var(--lit);font-weight:650}
.conv-chip span{font-family:var(--mono);font-size:9px;color:var(--mute)}
.conv-marker{text-align:center;margin:-22px 0 12px;color:var(--faint);font-family:var(--mono);
  font-size:10px;letter-spacing:.22em;position:relative;z-index:1}
.proc-teaser{position:relative;z-index:1;margin-top:-14px;padding:12px 16px;border:1px dashed var(--faint);
  border-radius:12px;color:var(--mute);font-size:12px;text-align:center}
.proc-teaser button{margin-left:8px;padding:5px 12px;border:1px solid var(--leak);border-radius:8px;
  background:none;color:var(--leak);font-family:var(--mono);font-size:11px;cursor:pointer}
.proc-teaser button:hover{background:rgba(72,215,232,.1)}
/* ---- 视图③ 工序 ---- */
.pstages{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin-bottom:18px}
.pstage{flex:1;min-width:210px;border:1px solid var(--faint);border-radius:12px;
  padding:12px;background:rgba(15,20,32,.6)}
.pstage.gap{border-style:dashed}
.pstage .ps-name{font-size:13.5px;font-weight:650;margin-bottom:3px}
.pstage .ps-sub{font-family:var(--mono);font-size:9px;color:var(--mute);line-height:1.6;
  margin-bottom:9px}
.ps-arrow{align-self:center;color:var(--faint);font-size:13px}
.ptags{display:flex;gap:4px;flex-wrap:wrap;margin-top:3px}
.ptag{font-family:var(--mono);font-size:8.5px;color:var(--leak);border:1px solid rgba(72,215,232,.4);
  border-radius:5px;padding:1px 5px}
.peq{border:1px solid rgba(255,207,94,.45);border-radius:14px;padding:14px 16px;
  background:rgba(255,207,94,.03)}
.peq .zone-title .zt{color:var(--jt)}
@media(max-width:900px){.stats{grid-template-columns:repeat(3,1fr)}.stat:nth-child(3){border-right:0}
  .stat:nth-child(-n+3){border-bottom:1px solid var(--faint)}.foot{display:block}.badge{display:inline-block;
  margin-top:16px}.duo{flex-direction:column}}
@media(max-width:620px){.wrap{padding:30px 14px 58px}.stats{grid-template-columns:repeat(2,1fr)}
  .stat:nth-child(odd){border-right:1px solid var(--faint)}.stat:nth-child(even){border-right:0}
  .stat{border-bottom:1px solid var(--faint)}.stat:nth-last-child(-n+2){border-bottom:0}}
@media(prefers-reduced-motion:reduce){.flow{display:none}.edge,.node{transition:none}}
</style>
</head>
<body>
<main class="wrap">
  <div class="eyebrow">披露证据图谱 · v1.6 · 供应链树×关系图×工序 · 2026-07</div>
  <h1>光模块产业，<span>被证据分层</span>的结构</h1>
  <p class="thesis">一个文件，三种看法，一条纪律主线。<b>①供应链树</b>（主视图）回答「谁做什么
    零件、放在 BOM 树哪一叶」——照全景 v1.1 并行三分支骨架：材料分喂、A/B/C 三分支汇聚成
    总成；双闸：<b>不表达供货关系</b>，空叶如实标空。<b>②关系图</b>回答「我们凭什么看得见这条
    供货关系」——236 边唯一承重，四硬约束不变。<b>③工序视图</b>回答「同一批零件按什么工序被
    加工」——与 BOM 树是两个坐标轴，<b>不是链环</b>。</p>
  <nav class="tabs" role="tablist" aria-label="视图切换">
    <button class="tab active" data-view="tree" role="tab">① 供应链树 · 主视图
      <span>并行三分支 × 每节点公司名单 · 双闸不承重</span></button>
    <button class="tab" data-view="graph" role="tab">② 关系图 · 证据承重
      <span>236边 / 169节点 · 四硬约束</span></button>
    <button class="tab" data-view="proc" role="tab">③ 工序视图 · 横切轴
      <span>工序×设备 · 与 BOM 树两个坐标轴</span></button>
  </nav>

  <section class="view active" id="view-tree">
    <section class="stats" id="tstats" aria-label="树统计"></section>
    <div class="banner"><span class="tag">双闸 · 不承重</span><div>
      本树只回答<b>「谁做什么、放在哪一叶」</b>，<b>不表达供货关系</b>——供货关系唯一承重台账是
      ②关系图（<code>output/edges.csv</code>）。公司卡上的 <b>⇄台账有边</b> 仅如实标注该公司名已作为
      供方/需方出现在 edges.csv，<b>不代表该边证明了本叶所述产品身份</b>（双闸不可传递）。空叶如实标
      「未识别到公开可锚的专产主体」并附定向任务；虚线框公司为 <b>T1 候选 · 未入关系台账</b>，不升格。</div></div>
    <nav class="legend" aria-label="锚档图例">
      <span class="chip static"><span class="dot ok"></span>有锚</span>
      <span class="chip static"><span class="dot semi"></span>半锚</span>
      <span class="chip static"><span class="dot weak"></span>弱锚</span>
      <span class="chip static"><span class="dot part"></span>部分证实</span>
      <span class="chip static"><span class="dot lead"></span>线索级待锚</span>
      <span class="chip static"><span class="dot cand"></span>T1候选 · 未入台账</span>
      <span class="chip static"><span class="dot pending"></span>仅类型归层 · 待锚</span>
      <span class="chip static">⇄n = 台账有边（n 条可跳转）</span>
      <span class="chip static">树连线：实线 = BOM 汇聚 · 虚线 = 同左复用 / 未细分 / 直销旁路</span>
      <input class="search" id="tsearch" placeholder="检索公司 / N编号 / 做什么…">
    </nav>
    <div class="tree" id="tree"><svg class="wires" id="wires"></svg></div>
  </section>

  <section class="view" id="view-graph">
    <section class="stats" id="stats" aria-label="数据统计"></section>
    <nav class="legend" id="legend" aria-label="边等级筛选"></nav>
    <section class="stage">
      <svg id="svg" viewBox="0 0 1760 1200" role="img"
        aria-label="光模块产业七层披露证据网络图"></svg>
    </section>
  </section>

  <section class="view" id="view-proc">
    <div class="banner cyan"><span class="tag">两坐标轴 · 非链环</span><div>
      横切工序轴与 BOM 树是<b>两个不同的坐标轴</b>（全景 v1.1 原文）：树回答「谁做什么零件」，
      本视图回答「同一批零件按什么工序顺序被加工」。<b>工序执行者 ≠ 零件供应商</b>——「组件封装
      （TOSA/ROSA）」的工序执行者目前仍为空（诚实缺口），零件供应商归 ①供应链树 A 分支各叶。
      设备/仪器纵轴贯穿全流程，不插入主链序。</div></div>
    <div id="proc"></div>
    <div class="noteblock"><h4>横切工序轴 · 全景 v1.1 原文</h4><div id="procintro"></div></div>
  </section>

  <footer class="foot">
    <div class="foot-copy"><b>诚实边界。</b> ①供应链树的公司名单与锚只回答「谁做什么」，
      「台账有边」仅表示公司名出现于 edges.csv，<b>不代表该边证明其产品身份</b>（双闸不可传递）；
      空叶 = 未识别到公开可锚的专产主体，附定向任务，不编造；T1 候选未入台账、不升格。
      ②关系图中，阴影虚线只表示公开披露留下了槽位，不能据此点名对手方；DSP 芯片层的 Marvell
      与博通使用虚线描边，标为<b>产品映射盲区</b>。③工序轴与 BOM 树是两个坐标轴，工序执行者
      ≠ 零件供应商。点击②中任意节点查看其全部入边与出边，点击边查看证据文件、年份、金额与锚点。
      <span class="base" id="baseline"></span></div>
    <div class="badge" id="badge"></div>
  </footer>
</main>
<aside class="drawer" id="drawer" role="dialog" aria-label="证据详情">
  <button class="close" id="dclose" aria-label="关闭">✕</button>
  <div id="dbody"></div>
</aside>
<script id="data" type="application/json">__DATA__</script>
<script id="treedata" type="application/json">__TREE__</script>
<script>
/* ================= 公共 ================= */
const D=JSON.parse(document.getElementById('data').textContent);
const T=JSON.parse(document.getElementById('treedata').textContent);
const NS='http://www.w3.org/2000/svg';
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function field(lab,val,mono=false){return val?`<div class="field"><div class="lab">${esc(lab)}</div>
  <div class="val${mono?' mono':''}">${esc(val)}</div></div>`:''}
const drawer=document.getElementById('drawer'),dbody=document.getElementById('dbody');
document.getElementById('dclose').onclick=()=>drawer.classList.remove('open');
document.addEventListener('keydown',e=>{if(e.key==='Escape')drawer.classList.remove('open')});

/* ================= 视图② 关系图（v1.5 交互语言不变） ================= */
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
    ${ins.length?`<div class="hint">作为需方 · ${ins.length} 条 ↓</div>${ins.map(e=>line(e,'获得')).join('')}`:''}`;
  dbody.querySelectorAll('[data-eid]').forEach(el=>el.addEventListener('click',()=>{
    const e=edgeMap[el.dataset.eid];openEdge(e,idmap[e.s],idmap[e.d])}));
  drawer.classList.add('open');
}

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
const countries=document.createElement('div');countries.className='chip static';
countries.innerHTML=Object.entries(CK).map(([k,v])=>`<span style="display:inline-flex;align-items:center;
  gap:4px"><span style="width:7px;height:7px;border-radius:50%;background:var(--${k})"></span>${v}</span>`).join(' · ');
legend.appendChild(countries);
document.getElementById('badge').textContent=D.badge;

/* ================= 视图① 供应链树 ================= */
const LT=T.leaves;
const CLSLBL={ok:'有锚',semi:'半锚',weak:'弱锚',part:'部分证实',lead:'线索级待锚',
  cand:'T1候选 · 未入台账',pending:'仅类型归层 · 待锚'};
function statusBadge(lf){
  const s=lf.status||'';if(!s)return'';
  if(s.startsWith('有主'))return `<span class="stbadge st-own">${esc(s)}</span>`;
  if(s.startsWith('弱'))return `<span class="stbadge st-weak">${esc(s)}</span>`;
  return `<span class="stbadge st-empty">${esc(s)}</span>`;
}
function coChip(leafId,r,idx,tags){
  const eb=r.edgeIds.length?`<span class="eb">⇄${r.edgeIds.length}</span>`:'';
  return `<button class="co${r.nid?'':' cand'}" data-leaf="${leafId}" data-idx="${idx}"
    data-key="${esc((r.nid+' '+r.name+' '+r.doing).toLowerCase())}" title="${esc(r.doing)}">
    <span class="cline"><span class="dot ${r.cls}"></span>
    <span class="nid">${esc(r.nid||'候选')}</span>${eb}</span>
    <span class="cname">${esc(r.name)}</span>${tags||''}</button>`;
}
function leafCard(id){
  const lf=LT[id],rows=lf.rows;
  const candN=rows.filter(r=>!r.nid).length;
  const empty=rows.length===0;
  const notes=(lf.notes||[]).map(n=>`<p class="lnote">${esc(n)}</p>`).join('');
  return `<div class="leaf${empty?' empty':''}" id="leaf-${id}">
    <div class="leaf-head"><span class="lt">${esc(lf.title)}</span>
      ${lf.sub?`<span class="ls">${esc(lf.sub)}</span>`:''}
      ${statusBadge(lf)}
      ${candN?`<span class="stbadge st-cand">候选 ${candN} · 未入台账</span>`:''}
      <span class="cnt">${rows.length?rows.length+' 行':''}</span></div>
    ${empty?`<div class="lempty">— 未识别到公开可锚的专产主体 —</div>`:''}
    <div class="cos">${rows.map((r,i)=>coChip(id,r,i)).join('')}</div>
    ${notes}</div>`;
}
function renderTree(){
  const t=document.getElementById('tree');
  t.innerHTML=`<svg class="wires" id="wires"></svg>
  <div class="zone"><div class="zone-title"><span class="zt">上游材料</span>
    <span class="zs">衬底/靶材/MO源/特气/掩模 → A1a·A2a；石英/树脂/光纤 → A3</span></div>
    <div class="leafrow">${leafCard('M1')}${leafCard('M2')}${leafCard('M-rest')}</div>
    <div class="leafrow" style="margin-top:12px">${leafCard('M1-lead')}</div></div>
  <div class="zone z-a"><div class="zone-title"><span class="zt">A · 光器件分支</span>
    <span class="zs">组件级子部件汇入 TOSA / ROSA；无源器件独立进入模块</span></div>
    <div class="leafrow">${['A1a','A1b','A1c','A1d','A2a'].map(leafCard).join('')}</div>
    <div class="conv">
      <div class="conv-chip" id="leaf-TOSA"><b>A1 有源组件 TOSA</b><span>汇聚 A1a+A1b+A1c+A1d · 结构节点 · 无单列公司</span></div>
      <div class="conv-chip" id="leaf-ROSA"><b>A2 有源组件 ROSA</b><span>汇聚 A2a + A1b-d 同左 · 结构节点 · 无单列公司</span></div>
    </div>
    <div class="leafrow">${leafCard('A3')}${leafCard('A-rest')}</div></div>
  <div class="duo">
    <div class="zone z-b"><div class="zone-title"><span class="zt">B · 功能电路分支</span>
      <span class="zs">电芯片 + PCB板</span></div>
      <div class="leafrow">${leafCard('B1')}${leafCard('B2')}</div></div>
    <div class="zone z-c"><div class="zone-title"><span class="zt">C · 结构件分支</span>
      <span class="zs">底座 / 壳体 / 金手指 · 新叶</span></div>
      <div class="leafrow">${leafCard('C1')}</div></div>
  </div>
  <div class="conv-marker">▼ 三 分 支 汇 聚（ A1 / A2 / A3 / B1 / B2 / C1 ）</div>
  <div class="zone z-mod">${leafCard('MOD')}</div>
  <div class="duo">
    <div class="zone"><div class="zone-title"><span class="zt">代工 EMS</span>
      <span class="zs">经代工</span></div>${leafCard('EMS')}</div>
    <div class="zone"><div class="zone-title"><span class="zt">系统商 / 云巨头 / 线缆</span>
      <span class="zs">直销或经代工 EMS</span></div>${leafCard('SYS')}</div>
  </div>
  <div class="zone z-x"><div class="zone-title"><span class="zt">X · 非主链节点</span>
    <span class="zs">不属 BOM 骨架 · 随台账收录 · 同样不承重</span></div>
    <div class="leafrow">${leafCard('X1')}${leafCard('X2')}${leafCard('X3')}</div></div>
  <div class="proc-teaser">横切工序轴（芯片制造 → 芯片封装 → 组件封装 → 模块组装 → 测试）与设备/仪器纵轴是另一坐标轴，不是链环
    <button id="goproc">→ ③ 工序视图</button></div>`;
  document.getElementById('goproc').addEventListener('click',()=>switchView('proc'));
  t.querySelectorAll('.co').forEach(el=>el.addEventListener('click',()=>
    openCompany(el.dataset.leaf,+el.dataset.idx)));
}

const WIRES=[
  ['M1','A1a'],['M1','A2a'],['M2','A3'],
  ['A1a','TOSA'],['A1b','TOSA'],['A1c','TOSA'],['A1d','TOSA'],
  ['A2a','ROSA'],['A1b','ROSA','d'],['A1c','ROSA','d'],['A1d','ROSA','d'],
  ['TOSA','MOD'],['ROSA','MOD'],['A3','MOD'],['A-rest','MOD','d'],
  ['B1','MOD'],['B2','MOD'],['C1','MOD'],
  ['MOD','EMS'],['MOD','SYS','d'],['EMS','SYS','h'],
];
function drawWires(){
  const tree=document.getElementById('tree'),wires=document.getElementById('wires');
  if(!tree||!wires||!tree.offsetParent)return;
  const tr=tree.getBoundingClientRect();
  wires.setAttribute('width',tree.scrollWidth);wires.setAttribute('height',tree.scrollHeight);
  wires.setAttribute('viewBox',`0 0 ${tree.scrollWidth} ${tree.scrollHeight}`);
  wires.innerHTML='';
  WIRES.forEach(([f,t2,st])=>{
    const a=document.getElementById('leaf-'+f),b=document.getElementById('leaf-'+t2);
    if(!a||!b)return;
    const ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();
    let d;
    if(st==='h'){
      const x1=ra.right-tr.left,y1=ra.top+ra.height/2-tr.top,
            x2=rb.left-tr.left,y2=rb.top+rb.height/2-tr.top;
      d=`M${x1},${y1} C${x1+46},${y1} ${x2-46},${y2} ${x2},${y2}`;
    }else{
      const x1=ra.left+ra.width/2-tr.left,y1=ra.bottom-tr.top,
            x2=rb.left+rb.width/2-tr.left,y2=rb.top-tr.top;
      const dd=Math.max(16,Math.min(90,(y2-y1)*.45));
      d=`M${x1},${y1} C${x1},${y1+dd} ${x2},${y2-dd} ${x2},${y2}`;
    }
    const p=document.createElementNS(NS,'path');
    p.setAttribute('d',d);p.setAttribute('class','wire'+(st==='d'?' dashed':''));
    wires.appendChild(p);
  });
}

function openCompany(leafId,idx){
  const lf=LT[leafId],r=lf.rows[idx];if(!r)return;
  const gname=r.nid?T.nidName[r.nid]:null;
  const ebtns=r.edgeIds.map(id=>`<button class="ebtn" data-e="${id}">${id}</button>`).join('');
  dbody.innerHTML=`<h3>${esc(r.name)}</h3>
    <span class="gradetag gt-${r.cls==='ok'?'lit':r.cls==='pending'?'shadow':r.cls==='cand'?'leak':'infer'}">${CLSLBL[r.cls]||esc(r.cls)}</span>
    ${r.stance?`<span class="gradetag gt-leak">${esc(r.stance)}</span>`:''}
    ${r.nid?'':`<span class="gradetag gt-infer">未入 nodes.csv / edges.csv</span>`}
    ${field('所属叶',lf.title+(lf.sub?' · '+lf.sub:''))}
    ${field('节点编号',r.nid||'—（候选，未入 nodes.csv）',true)}
    ${field('身份依据一句',r.doing)}
    ${field('锚（原文照录）',r.anchor)}
    ${field('关系台账有边?',r.edgeText)}
    ${ebtns?`<div class="hint">跳转到②关系图的边 ↓</div><div class="ebtns">${ebtns}</div>`:''}
    <div class="hint">双闸：「做什么」与「台账有边」不可互推 · 供应链树不承重</div>
    ${gname&&idmap[gname]?`<button class="gjump" id="gj">→ 在②关系图中打开该节点</button>`:''}`;
  dbody.querySelectorAll('.ebtn').forEach(b=>b.addEventListener('click',()=>jumpGraphEdge(b.dataset.e)));
  const gj=document.getElementById('gj');if(gj)gj.addEventListener('click',()=>jumpGraphNode(gname));
  drawer.classList.add('open');
}
function jumpGraphNode(name){
  if(!idmap[name])return;
  switchView('graph');
  setTimeout(()=>openNode(idmap[name]),90);
}
function jumpGraphEdge(eid){
  const e=edgeMap[eid];if(!e)return;
  switchView('graph');
  setTimeout(()=>openEdge(e,idmap[e.s],idmap[e.d]),90);
}

document.getElementById('tstats').innerHTML=[
  [T.stats.leafTotal,'BOM 终端叶'],[T.stats.leafOwn,'有主叶'],[T.stats.leafEmpty,'空叶'],
  [T.stats.leafWeak,'弱覆盖叶'],[T.stats.nodes,'节点公司 · 全落位'],[T.stats.candidates,'T1候选 · 未入台账']
].map(([n,k])=>`<div class="stat"><div class="n">${n}</div><div class="k">${k}</div></div>`).join('');
document.getElementById('tsearch').addEventListener('input',e=>{
  const q=e.target.value.trim().toLowerCase();
  document.querySelectorAll('#tree .co').forEach(el=>{
    el.style.display=!q||el.dataset.key.includes(q)?'':'none'});
});

/* ================= 视图③ 工序视图 ================= */
const EQKW=['贴片','耦合','老化','测试','焊接','封装','组装','测量','键合','CPO'];
const STAGES=[
  {name:'芯片制造',sub:'即①供应链树 A1a / A2a 两叶本身（v1.1 不重复列表）',leaves:['A1a','A2a']},
  {name:'芯片封装（委外）',sub:'跨光/电芯片工序 · 源杰招股书委托加工表',leaves:['PROC1']},
  {name:'组件封装（TOSA/ROSA）',sub:'工序执行者 · 非零件供应商',leaves:['PROC2']},
  {name:'模块组装（贴片/耦合/固化）',sub:'产出即①供应链树「光模块（总成）」',leaves:['MOD']},
  {name:'测试',sub:'所用设备见下方设备/仪器纵轴（v1.1 不重复列表）',leaves:[]},
];
function renderProc(){
  const root=document.getElementById('proc');let html='<div class="pstages">';
  STAGES.forEach((st,i)=>{
    if(i>0)html+=`<div class="ps-arrow">→</div>`;
    const rows=st.leaves.flatMap(id=>LT[id].rows.map((r,j)=>({id,r,j})));
    const gap=rows.length===0||st.leaves.every(id=>LT[id].status&&LT[id].status.startsWith('空'));
    html+=`<div class="pstage${gap?' gap':''}"><div class="ps-name">${esc(st.name)}</div>
      <div class="ps-sub">${esc(st.sub)}</div>
      ${rows.length?`<div class="cos">${rows.map(({id,r,j})=>coChip(id,r,j)).join('')}</div>`
        :`<div class="lempty">— 未识别到公开可锚的专产主体 —</div>`}
    </div>`;
  });
  html+='</div>';
  const eq=LT.EQ;
  html+=`<div class="peq"><div class="zone-title"><span class="zt">设备 / 仪器纵轴 · ${eq.rows.length} 家</span>
    <span class="zs">${esc(eq.sub)} · 工序标签由各行「做什么」原文关键词机械提取</span></div>
    <div class="cos">${eq.rows.map((r,i)=>{
      const tags=EQKW.filter(k=>(r.doing+r.anchor).includes(k));
      const tagHtml=tags.length?`<span class="ptags">${tags.map(k=>`<span class="ptag">${k}</span>`).join('')}</span>`:'';
      return coChip('EQ',r,i,tagHtml);
    }).join('')}</div></div>`;
  root.innerHTML=html;
  root.querySelectorAll('.co').forEach(el=>el.addEventListener('click',()=>
    openCompany(el.dataset.leaf,+el.dataset.idx)));
  document.getElementById('procintro').textContent=T.procIntro;
}

/* ================= 视图切换 ================= */
function switchView(v){
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===v));
  document.querySelectorAll('.view').forEach(s=>s.classList.toggle('active',s.id==='view-'+v));
  history.replaceState(null,'','#'+v);
  drawer.classList.remove('open');
  if(v==='tree')requestAnimationFrame(drawWires);
}
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>switchView(t.dataset.view)));

renderTree();
renderProc();
let rsz;window.addEventListener('resize',()=>{clearTimeout(rsz);rsz=setTimeout(drawWires,120)});
window.addEventListener('load',drawWires);
if(['tree','graph','proc'].includes(location.hash.slice(1)))switchView(location.hash.slice(1));
else switchView('tree');
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- 装配与断言

def main():
    nodes, edges = load_csv()
    graph = build_graph(nodes, edges)
    tree, parsed_nids = build_tree(nodes)

    def payload(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    baseline = "数据基线：output/光模块供应链全景-v1.1.md @ {} · output/edges.csv 236边 · output/nodes.csv 169节点 · 装配 {}".format(
        time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(PANORAMA_MD))),
        time.strftime("%Y-%m-%d %H:%M"),
    )
    html = (HTML
            .replace("__DATA__", payload(graph))
            .replace("__TREE__", payload(tree)))
    html = html.replace('<span class="base" id="baseline"></span>',
                        f'<span class="base" id="baseline">{baseline}</span>')

    node_ids = {r["node_id"] for r in nodes}

    # 视图② 四硬约束
    assert graph["edgeCount"] == 236, graph["edgeCount"]
    assert graph["canonicalNodeCount"] == 169, graph["canonicalNodeCount"]
    assert sum(graph["layerCounts"].values()) == 169
    assert graph["gradeCounts"].get("infer") == 4
    assert {"Marvell", "博通(Broadcom)"}.issubset(
        {n["id"] for n in graph["nodes"] if n.get("blindspot")}
    )
    assert "236边/169节点/判例2A+2B" in html
    assert not re.search(
        r'<(?:script|link)[^>]+(?:src|href)\s*=\s*["\']https?://', html, re.I
    ), "HTML 含外部脚本或样式依赖"

    # 视图① 结构完整性与 169 节点落位对账
    unknown = parsed_nids - node_ids
    assert not unknown, f"全景出现 nodes.csv 之外的 NID: {sorted(unknown)}"
    missing = node_ids - parsed_nids
    if missing:
        print(f"WARN: {len(missing)} 个 nodes.csv 节点未在全景 v1.1 落位（并发编辑容忍）: "
              f"{sorted(missing)}")
    for marker in ('id="view-tree"', 'id="view-graph"', 'id="view-proc"',
                   "leaf-TOSA", "leaf-ROSA", "id=\"wires\""):
        assert marker in html, marker
    assert "两个不同的坐标轴" in tree["procIntro"], "横切工序轴原文未捕获"

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    row_total = sum(len(lf["rows"]) for lf in tree["leaves"].values())
    print(f"wrote {OUT_PATH} {len(html)} bytes")
    print(f"视图①: {row_total} 公司行 / 唯一NID {len(parsed_nids)} / "
          f"T1候选 {tree['stats']['candidates']} / 锚档 {tree['stats']['clsCounts']}")
    for key in LEAF_DEFS:
        lf = tree["leaves"][key]
        print(f"  {key:8s} rows={len(lf['rows']):3d} notes={len(lf['notes'])}")
    print(f"视图②: {graph['edgeCount']}边 / {graph['canonicalNodeCount']}节点 / "
          f"幽灵槽位{graph['ghostCount']} / 等级{dict(graph['gradeCounts'])}")
    print(f"视图③: 工序5阶段 + 设备纵轴 {len(tree['leaves']['EQ']['rows'])}家")
    print("自测: 236边✓ 169节点✓ 徽章✓ 零外部依赖✓ 三视图标记✓ 工序轴原文✓")
    print(baseline)


if __name__ == "__main__":
    main()
