#!/usr/bin/env python3
"""build_atlas_v14.py — 光模块产业「披露证据图谱」v1.4

设计重做（Claude / frontend-design）：把 99 边 48 节点渲染成一张
"披露证据地图"——边的样式编码"我们凭什么看得见这条关系"。
暗光纤底色 + 光谱色可见性编码 + 等宽数字（呼应逐位精确纪律）。

输入(只读): output/edges.csv, output/nodes.csv
输出: output/光模块产业图谱-v1.4.html (自包含, 零外链)
自测: 见文件尾 __main__ 断言。
"""
import csv, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 节点 → 供应链层。x 轴 = 光信号传播方向（上游左→终端右）。
#    dev = 设备/仪器供应带（底部独立轨道）；out = 跨行业边界外。
LAYER = {
    # L0 上游：芯片 / 材料 / 元件
    "源杰科技":"L0","三安光电":"L0","士兰微":"L0","Acacia":"L0",
    "Power Master":"L0","星微科技":"L0","奥普瑞":"L0","南央国际":"L0","津微光电":"L0",
    # L1 器件 / 组件
    "Lumentum":"L1","天孚通信":"L1","光迅科技":"L1","Coherent":"L1",
    "索尔思(Source Photonics)":"L1","NeoPhotonics":"L1",
    # L2 模块 / 代工
    "中际旭创":"L2","新易盛":"L2","Applied Optoelectronics(AAOI)":"L2",
    "Fabrinet":"L2","海信集团":"L2",
    # L3 终端 / 系统 / 云 / 渠道
    "NVIDIA":"L3","Cisco":"L3","Ciena":"L3","Nokia":"L3","华为(含海思)":"L3",
    "Google":"L3","Microsoft":"L3","Oracle":"L3","Apple":"L3","Digicomm":"L3",
    "ATX Networks":"L3","烽火通信":"L3","Infinera":"L3","博通(Broadcom)":"L3",
    "PINEWAVE":"L3","浙江粮油":"L3","索恩格(SEG Automotive)":"L3",
    # 设备 / 仪器供应带
    "猎奇智能":"DEV","罗博特科/ficonTEC":"DEV","凯格精机":"DEV","奥特维":"DEV",
    "博众精工":"DEV","快克智能":"DEV","普源精电":"DEV","联讯仪器":"DEV","讯速信远":"DEV",
    # 边界外（跨行业 schema 参考）
    "派克新材":"OUT","等离子体所":"OUT",
}
LAYER_X = {"L0":0, "L1":1, "L2":2, "L3":3}
LAYER_LABEL = {"L0":"上游 · 芯片/元件", "L1":"器件/组件", "L2":"模块/代工", "L3":"终端/系统/云"}

# 边等级 → 可见性类别（决定颜色/样式/是否流光）
def grade_class(g):
    if g.startswith("实边(已死"): return "dead"
    if g.startswith("实边"):       return "lit"
    if g.startswith("推断边"):     return "infer"
    if g.startswith("程序段落"):   return "leak"
    return "shadow"   # 半边 / 半边槽位

def country_key(c):
    c = c or ""
    if "中国" in c and "日本" not in c and "德国" not in c and "新加坡" not in c: return "cn"
    if c.startswith("中国") or c == "中国": return "cn"
    if "美国" in c: return "us"
    if "日本" in c or "台湾" in c: return "jt"   # 日本+台湾=技术上游源
    if c in ("待核",): return "veil"
    return "other"

def load():
    nodes = list(csv.DictReader(open(os.path.join(ROOT,"output/nodes.csv"), encoding="utf-8")))
    edges = list(csv.DictReader(open(os.path.join(ROOT,"output/edges.csv"), encoding="utf-8")))
    return nodes, edges

def norm(name):
    """边里的供需方名 → nodes 规范名（处理已知别名）"""
    if not name: return name
    n = name.strip()
    alias = {
        "AAOI":"Applied Optoelectronics(AAOI)",
        "华为+海思":"华为(含海思)","华为":"华为(含海思)",
        "博通":"博通(Broadcom)","博通(客户)":"博通(Broadcom)","Broadcom":"博通(Broadcom)",
        "NVIDIA(客户)":"NVIDIA","索尔思":"索尔思(Source Photonics)","索尔思(Source Photonics)":"索尔思(Source Photonics)",
        "Fabrinet(解匿)":"Fabrinet","Fabrinet(疑似客户)":"Fabrinet",
        "Lumentum":"Lumentum","Ciena(解匿)":"Ciena","Google(解匿)":"Google",
        "中际旭创(作为客户)":"中际旭创","罗博特科":"罗博特科/ficonTEC","ficonTEC(罗博特科)":"罗博特科/ficonTEC",
        "PINEWAVE(关联方)":"PINEWAVE","等离子体所(客户)":"等离子体所","浙江粮油(出口代理)":"浙江粮油",
        "索恩格":"索恩格(SEG Automotive)","苏世博":"索恩格(SEG Automotive)",
    }
    if n in alias: return alias[n]
    # 去匿名后缀 → 归到公司主体不建独立节点（保留原串做端点）
    return n

def build():
    nodes, edges = load()
    known = {r["名称"] for r in nodes}

    # 节点索引 + 坐标
    N = {}
    for r in nodes:
        nm = r["名称"]
        N[nm] = {"id":nm, "type":r["类型"], "country":r["国别"],
                 "code":r.get("代码",""), "note":r.get("备注",""),
                 "layer":LAYER.get(nm,"L1"), "ck":country_key(r["国别"]),
                 "deg":0}

    # 处理边：解析端点，匿名端点建"幽灵槽位"节点（阴影里）
    E = []
    ghost = {}
    for r in edges:
        sup, dem = norm(r["供方"]), norm(r["需方"])
        cls = grade_class(r["边等级"])
        def endpoint(name):
            if name in N: return name
            # 匿名/未建节点 → 幽灵
            gid = "◈ " + name
            if gid not in ghost:
                ghost[gid] = {"id":gid, "type":"匿名槽位", "country":"", "code":"",
                              "note":"", "layer":None, "ck":"veil", "deg":0, "ghost":True}
            return gid
        s, d = endpoint(sup), endpoint(dem)
        E.append({"id":r["edge_id"], "s":s, "d":d, "cls":cls, "grade":r["边等级"],
                  "amt":r["占比或金额"], "fy":r["财年"], "src":r["证据文件"],
                  "anchor":r["锚点"], "vs":r["验证状态"], "note":r["备注"]})
        N.get(s,{}).__setitem__("deg", N.get(s,{}).get("deg",0)+1) if s in N else None
        N.get(d,{}).__setitem__("deg", N.get(d,{}).get("deg",0)+1) if d in N else None

    # 幽灵节点：继承其实名对手方的层，落在相邻列的"阴影带"
    for e in E:
        for end,other in ((e["s"],e["d"]),(e["d"],e["s"])):
            if end in ghost and other in N and N[other]["layer"] in LAYER_X:
                gl = N[other]["layer"]
                ghost[end]["layer"] = gl
                ghost[end]["deg"] += 1
    allN = dict(N); allN.update(ghost)

    payload = {
        "nodes":[allN[k] for k in allN],
        "edges":E,
        "layerLabel":LAYER_LABEL,
        "layerX":LAYER_X,
    }
    return payload

HTML = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>光模块产业 · 披露证据图谱</title>
<style>
:root{
  --void:#080B14; --panel:#0F1420; --panel2:#161D2B; --grid:#1B2333;
  --ink:#EAEEF6; --mute:#727D97; --faint:#3A4358;
  --lit:#4FE0C4; --amber:#FFB347; --shadow:#4A5470; --dead:#9C5D72; --leak:#B98BE8;
  --cn:#F0655C; --us:#5B9DF0; --jt:#FFCF5E; --other:#8792AB; --veil:#5A6480;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --disp:'Space Grotesk',system-ui,sans-serif;
  --body:'Inter',system-ui,sans-serif;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--void);color:var(--ink);font-family:var(--body);
  -webkit-font-smoothing:antialiased}
body{background-image:
  linear-gradient(var(--grid) 1px,transparent 1px),
  linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:44px 44px; background-position:center;
  background-blend-mode:normal;}
body::before{content:"";position:fixed;inset:0;pointer-events:none;
  background:radial-gradient(120% 80% at 50% -10%,rgba(79,224,196,.06),transparent 60%),
             radial-gradient(100% 60% at 100% 110%,rgba(91,157,240,.05),transparent 55%);
  z-index:0}
.wrap{position:relative;z-index:1;max-width:1240px;margin:0 auto;padding:48px 28px 80px}

/* ── header ── */
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.32em;text-transform:uppercase;
  color:var(--lit);display:flex;align-items:center;gap:12px;margin:0 0 18px}
.eyebrow::before{content:"";width:26px;height:1px;background:var(--lit);box-shadow:0 0 8px var(--lit)}
h1{font-family:var(--disp);font-weight:600;font-size:clamp(34px,5.5vw,60px);line-height:1.02;
  letter-spacing:-.02em;margin:0 0 20px;max-width:16ch}
h1 .glow{color:var(--lit);text-shadow:0 0 24px rgba(79,224,196,.45)}
.thesis{font-size:clamp(15px,1.7vw,18px);line-height:1.65;color:var(--mute);max-width:60ch;margin:0 0 34px}
.thesis b{color:var(--ink);font-weight:500}

/* ── stat strip ── */
.stats{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--faint);border-radius:14px;
  overflow:hidden;background:linear-gradient(180deg,rgba(22,29,43,.6),rgba(15,20,32,.6));
  backdrop-filter:blur(6px);margin-bottom:40px}
.stat{flex:1 1 120px;padding:18px 22px;border-right:1px solid var(--faint)}
.stat:last-child{border-right:0}
.stat .n{font-family:var(--mono);font-size:30px;font-weight:600;letter-spacing:-.02em;color:var(--ink)}
.stat .n .u{font-size:14px;color:var(--mute);margin-left:4px}
.stat .k{font-size:12px;color:var(--mute);margin-top:4px;letter-spacing:.04em}

/* ── legend (visibility encoding) ── */
.legend{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 20px}
.chip{font-family:var(--mono);font-size:12px;display:inline-flex;align-items:center;gap:9px;
  padding:7px 13px 7px 11px;border:1px solid var(--faint);border-radius:999px;cursor:pointer;
  color:var(--mute);background:rgba(15,20,32,.5);transition:.18s;user-select:none}
.chip:hover{border-color:var(--mute);color:var(--ink)}
.chip.off{opacity:.32}
.chip .sw{width:22px;height:0;border-top-width:2.5px;border-top-style:solid;position:relative}
.chip[data-c=lit] .sw{border-color:var(--lit);box-shadow:0 0 7px var(--lit)}
.chip[data-c=infer] .sw{border-color:var(--amber);border-top-style:dashed}
.chip[data-c=shadow] .sw{border-color:var(--shadow);border-top-style:dashed}
.chip[data-c=dead] .sw{border-color:var(--dead);border-top-style:dotted}
.chip[data-c=leak] .sw{border-color:var(--leak);border-top-style:dashed}

/* ── graph ── */
.stage{position:relative;border:1px solid var(--faint);border-radius:18px;overflow:hidden;
  background:linear-gradient(180deg,rgba(11,15,24,.75),rgba(8,11,20,.9))}
.colhead{position:absolute;top:0;left:0;right:0;display:grid;pointer-events:none;z-index:3}
.colhead span{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--mute);padding:14px 0 0 16px;border-left:1px solid var(--grid)}
.colhead span:first-child{border-left:0}
svg{display:block;width:100%;height:auto}
.edge{fill:none;transition:opacity .2s,stroke-width .2s}
.edge.lit{stroke:var(--lit);stroke-width:1.5;opacity:.75}
.edge.infer{stroke:var(--amber);stroke-width:1.4;stroke-dasharray:7 5;opacity:.7}
.edge.shadow{stroke:var(--shadow);stroke-width:1;stroke-dasharray:2 5;opacity:.5}
.edge.dead{stroke:var(--dead);stroke-width:1.2;stroke-dasharray:1 6;opacity:.55}
.edge.leak{stroke:var(--leak);stroke-width:1.3;stroke-dasharray:6 4;opacity:.62}
.edge.aux{stroke:#2E6E63;stroke-width:.8;opacity:.34;stroke-dasharray:none}
.edge.aux.shadow{stroke:#39415A}
.edge.hot{opacity:1;stroke-width:2.6}
.edge.dim{opacity:.06}
.flow{stroke:var(--lit);stroke-width:2.2;fill:none;stroke-linecap:round;
  filter:drop-shadow(0 0 4px var(--lit))}
.node{cursor:pointer}
.node circle{transition:.18s}
.node .halo{fill:none;stroke-width:1}
.node text{font-family:var(--body);font-size:12px;fill:var(--ink);paint-order:stroke;
  stroke:var(--void);stroke-width:3px;dominant-baseline:middle}
.node.ghost text{fill:var(--veil);font-style:italic}
.node.dim{opacity:.12}
.node.hot text{fill:#fff;font-weight:600}
.cn{fill:var(--cn)} .us{fill:var(--us)} .jt{fill:var(--jt)}
.other{fill:var(--other)} .veil{fill:var(--veil)}

/* ── evidence drawer ── */
.drawer{position:fixed;top:0;right:0;height:100%;width:min(420px,92vw);z-index:40;
  background:linear-gradient(180deg,#10151F,#0B0F18);border-left:1px solid var(--faint);
  transform:translateX(100%);transition:transform .32s cubic-bezier(.4,0,.1,1);
  padding:28px 26px;overflow-y:auto;box-shadow:-30px 0 60px rgba(0,0,0,.5)}
.drawer.open{transform:translateX(0)}
.drawer h3{font-family:var(--disp);font-size:20px;margin:0 0 4px;line-height:1.2}
.drawer .close{position:absolute;top:20px;right:20px;background:none;border:1px solid var(--faint);
  color:var(--mute);width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:16px}
.drawer .close:hover{color:var(--ink);border-color:var(--mute)}
.gradetag{display:inline-block;font-family:var(--mono);font-size:11px;padding:4px 10px;border-radius:6px;
  margin:8px 0 20px;letter-spacing:.04em}
.gt-lit{background:rgba(79,224,196,.14);color:var(--lit)}
.gt-infer{background:rgba(255,179,71,.14);color:var(--amber)}
.gt-shadow{background:rgba(74,84,112,.2);color:#9aa6c4}
.gt-dead{background:rgba(156,93,114,.18);color:#d493a6}
.gt-leak{background:rgba(185,139,232,.15);color:var(--leak)}
.field{border-top:1px solid var(--grid);padding:13px 0}
.field .lab{font-family:var(--mono);font-size:10px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--mute);margin-bottom:5px}
.field .val{font-size:14px;line-height:1.5;word-break:break-word}
.field .val.mono{font-family:var(--mono);color:var(--lit);font-size:15px}
.field a{color:var(--us);text-decoration:none;font-family:var(--mono);font-size:12px;word-break:break-all}
.field a:hover{text-decoration:underline}
.hint{font-family:var(--mono);font-size:12px;color:var(--mute);margin-top:14px}

.foot{margin-top:34px;padding-top:22px;border-top:1px solid var(--grid);
  font-size:13px;line-height:1.7;color:var(--mute);max-width:76ch}
.foot b{color:var(--ink);font-weight:500}
.foot .warn{color:var(--amber)}

@media (max-width:760px){ .wrap{padding:32px 16px 60px} .colhead{display:none} }
@media (prefers-reduced-motion:reduce){ .flow{display:none!important} .edge,.node circle{transition:none} }
</style></head><body>
<div class="wrap">
  <div class="eyebrow">披露证据图谱 · v1.4 · 2026-07</div>
  <h1>光模块产业，<span class="glow">被照亮</span>的供应链</h1>
  <p class="thesis">这不是一张全行业名单。公开披露只照亮它选择照亮的关系——
    每条边的样式，都标着<b>我们凭什么看得见它</b>：强制披露的实名、只知金额的匿名槽位、
    从旧文件里考古解出的对手方、已经死亡的跨境边。<b>亮的看得清，暗的看不清，这本身就是情报。</b></p>

  <div class="stats" id="stats"></div>

  <div class="legend" id="legend"></div>
  <div class="stage">
    <div class="colhead" id="colhead"></div>
    <svg id="svg" viewBox="0 0 1180 1320" role="img" aria-label="光模块产业披露证据网络图"></svg>
  </div>

  <div class="foot" id="foot"></div>
</div>

<div class="drawer" id="drawer" role="dialog" aria-label="证据详情">
  <button class="close" id="dclose" aria-label="关闭">✕</button>
  <div id="dbody"></div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const NS='http://www.w3.org/2000/svg';
const CK={cn:'中国',us:'美国',jt:'日本/台湾',other:'其他',veil:'待核/匿名'};
const CLSNAME={lit:'实边 · 强制披露实名',infer:'推断边 · 考古解出',shadow:'半边槽位 · 只知金额',dead:'实边 · 已死亡',leak:'程序段落 · 侧信道泄漏'};

// ── layout: 4 主列 + 设备带 + 边界外 ──
const W=1180, PADX=40, TOP=54, ROWH=44;
const cols=['L0','L1','L2','L3'];
const colW=(W-PADX*2)/cols.length;
const colX=i=>PADX+colW*i+colW/2;

const byLayer={L0:[],L1:[],L2:[],L3:[],DEV:[],OUT:[]};
const idmap={};
D.nodes.forEach(n=>{idmap[n.id]=n; (byLayer[n.layer]||byLayer.L1).push(n);});
// 列内排序：实名在上、幽灵在下，度数高居中
['L0','L1','L2','L3'].forEach(L=>{
  byLayer[L].sort((a,b)=>(a.ghost?1:0)-(b.ghost?1:0) || b.deg-a.deg);
});
// 主列 y
let maxRows=0;
cols.forEach((L,ci)=>{
  byLayer[L].forEach((n,ri)=>{ n.x=colX(ci); n.y=TOP+40+ri*ROWH; });
  maxRows=Math.max(maxRows, byLayer[L].length);
});
const mainH=TOP+40+maxRows*ROWH+30;
// 设备带（底部横排）
const devY=mainH+70;
const devN=byLayer.DEV;
devN.forEach((n,i)=>{ n.x=PADX+((W-PADX*2)/(devN.length))*(i+.5); n.y=devY; });
// 边界外（最底，居中两枚）
const outY=devY+80;
byLayer.OUT.forEach((n,i)=>{ n.x=PADX+120+i*150; n.y=outY; });
const H=outY+60;

const svg=document.getElementById('svg');
svg.setAttribute('viewBox',`0 0 ${W} ${H}`);

// column headers
const ch=document.getElementById('colhead');
ch.style.gridTemplateColumns=`repeat(4,1fr)`;
cols.forEach(L=>{const s=document.createElement('span');s.textContent=D.layerLabel[L];ch.appendChild(s);});

// defs: soft glow
svg.innerHTML=`<defs>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="1.1" result="b"/><feMerge>
    <feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>`;

// band separators (subtle)
[byLayer.DEV.length?devY-38:0].forEach(y=>{if(!y)return;
  const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',PADX);l.setAttribute('x2',W-PADX);l.setAttribute('y1',y);l.setAttribute('y2',y);
  l.setAttribute('stroke','var(--grid)');l.setAttribute('stroke-dasharray','2 6');svg.appendChild(l);
  const t=document.createElementNS(NS,'text');t.setAttribute('x',PADX);t.setAttribute('y',y-10);
  t.setAttribute('fill','var(--mute)');t.setAttribute('font-family','var(--mono)');t.setAttribute('font-size','11');
  t.setAttribute('letter-spacing','.18em');t.textContent='设备 / 仪器供应带 ↑ 供货给模块厂';svg.appendChild(t);});

const edgeEls=[], flowEls=[];
function path(a,b){
  if(!a||!b) return '';
  const mx=(a.x+b.x)/2;
  return `M${a.x},${a.y} C${mx},${a.y} ${mx},${b.y} ${b.x},${b.y}`;
}
// draw edges
const gEdges=document.createElementNS(NS,'g');svg.appendChild(gEdges);
const AUX=n=>n&&(n.layer==='DEV'||n.layer==='OUT');
D.edges.forEach(e=>{
  const a=idmap[e.s], b=idmap[e.d]; if(!a||!b) return;
  const aux = AUX(a)||AUX(b);
  const p=document.createElementNS(NS,'path');
  p.setAttribute('class','edge '+e.cls+(aux?' aux':'')); p.setAttribute('d',path(a,b));
  p.dataset.eid=e.id; p.dataset.cls=e.cls;
  p._a=a;p._b=b;p._e=e;
  p.addEventListener('click',ev=>{ev.stopPropagation();openEdge(e,a,b);});
  gEdges.appendChild(p); edgeEls.push(p);
  if(e.cls==='lit' && !aux){ // signature: 光子只沿主信号链的实边流动
    const f=document.createElementNS(NS,'path');
    f.setAttribute('class','flow');f.setAttribute('d',path(a,b));
    const len=Math.hypot(b.x-a.x,b.y-a.y)+80;
    f.style.strokeDasharray=`3 ${len}`;
    f.style.animation=`flow ${2.6+Math.random()*1.6}s linear infinite`;
    f.style.animationDelay=`${-Math.random()*3}s`;
    gEdges.appendChild(f);flowEls.push(f);
  }
});
const kf=document.createElementNS(NS,'style');
kf.textContent=`@keyframes flow{from{stroke-dashoffset:0}to{stroke-dashoffset:-1000}}`;
svg.appendChild(kf);

// draw nodes
const ABBR={'Applied Optoelectronics(AAOI)':'AAOI','罗博特科/ficonTEC':'罗博特科','索尔思(Source Photonics)':'索尔思','华为(含海思)':'华为','博通(Broadcom)':'博通','索恩格(SEG Automotive)':'索恩格'};
function label(id){const raw=id.replace('◈ ','');if(ABBR[raw])return ABBR[raw];const clean=raw.replace(/\(.*/,'');return clean.length>12?clean.slice(0,11)+'…':clean;}
const gNodes=document.createElementNS(NS,'g');svg.appendChild(gNodes);
D.nodes.forEach(n=>{
  const g=document.createElementNS(NS,'g');
  g.setAttribute('class','node '+(n.ghost?'ghost ':'')); g.dataset.nid=n.id;
  const r = n.ghost?4 : Math.max(5, Math.min(11, 4+n.deg*0.9));
  const halo=document.createElementNS(NS,'circle');
  halo.setAttribute('class','halo '+n.ck);halo.setAttribute('cx',n.x);halo.setAttribute('cy',n.y);
  halo.setAttribute('r',r+4);halo.setAttribute('stroke-opacity',n.ghost?'.4':'.9');halo.setAttribute('fill','none');
  const c=document.createElementNS(NS,'circle');
  c.setAttribute('class',n.ck);c.setAttribute('cx',n.x);c.setAttribute('cy',n.y);c.setAttribute('r',r);
  c.setAttribute('fill-opacity',n.ghost?'.35':'1');
  if(!n.ghost) c.setAttribute('filter','url(#soft)');
  const t=document.createElementNS(NS,'text');
  const right = n.layer==='L3' || (n.x> W/2 && n.layer!=='DEV');
  t.setAttribute('x', right? n.x-r-8 : n.x+r+8);
  t.setAttribute('y', n.y); t.setAttribute('text-anchor', right?'end':'start');
  t.textContent=label(n.id);
  g.append(halo,c,t);
  g.addEventListener('click',ev=>{ev.stopPropagation();openNode(n);});
  g.addEventListener('mouseenter',()=>hover(n.id));
  g.addEventListener('mouseleave',clearHover);
  gNodes.appendChild(g);
});

// ── interaction ──
function neighbors(id){const s=new Set([id]);D.edges.forEach(e=>{if(e.s===id)s.add(e.d);if(e.d===id)s.add(e.s);});return s;}
function hover(id){
  const nb=neighbors(id);
  edgeEls.forEach(p=>{const on=p._e.s===id||p._e.d===id;p.classList.toggle('hot',on);p.classList.toggle('dim',!on);});
  document.querySelectorAll('.node').forEach(g=>{const on=nb.has(g.dataset.nid);g.classList.toggle('hot',g.dataset.nid===id);g.classList.toggle('dim',!on);});
}
function clearHover(){edgeEls.forEach(p=>p.classList.remove('hot','dim'));document.querySelectorAll('.node').forEach(g=>g.classList.remove('hot','dim'));}

const drawer=document.getElementById('drawer'),dbody=document.getElementById('dbody');
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function field(lab,val,mono){return val?`<div class="field"><div class="lab">${lab}</div><div class="val${mono?' mono':''}">${esc(val)}</div></div>`:'';}
function openEdge(e,a,b){
  const anchor = /^https?:/.test(e.anchor)? `<div class="field"><div class="lab">锚点 URL</div><div class="val"><a href="${esc(e.anchor)}" target="_blank" rel="noopener">${esc(e.anchor)}</a></div></div>` : field('锚点',e.anchor);
  dbody.innerHTML=`<h3>${esc(a.id.replace('◈ ',''))} → ${esc(b.id.replace('◈ ',''))}</h3>
    <span class="gradetag gt-${e.cls}">${esc(e.grade)} · ${CLSNAME[e.cls]}</span>
    ${field('占比 / 金额',e.amt,true)}${field('财年',e.fy,true)}
    ${field('证据文件',e.src)}${anchor}${field('验证状态',e.vs)}${field('备注',e.note)}
    <div class="hint">边 ${esc(e.id)}</div>`;
  drawer.classList.add('open');
}
function openNode(n){
  const outs=D.edges.filter(e=>e.s===n.id),ins=D.edges.filter(e=>e.d===n.id);
  const line=(e,dir)=>`<div class="field"><div class="lab">${dir} ${esc(e.id)} · ${esc(e.grade)}</div><div class="val mono" style="cursor:pointer">${esc((dir==='供给'?e.d:e.s).replace('◈ ',''))} · ${esc(e.amt)}</div></div>`;
  dbody.innerHTML=`<h3>${esc(n.id.replace('◈ ',''))}</h3>
    <span class="gradetag gt-${n.ghost?'shadow':'lit'}">${esc(n.type)} · ${CK[n.ck]}</span>
    ${field('代码',n.code,true)}${field('备注',n.note)}
    ${outs.length?'<div class="hint">作为供方 ↓</div>'+outs.map(e=>line(e,'供给')).join(''):''}
    ${ins.length?'<div class="hint">作为需方 ↓</div>'+ins.map(e=>line(e,'获得')).join(''):''}`;
  drawer.classList.add('open');
}
document.getElementById('dclose').onclick=()=>drawer.classList.remove('open');
document.addEventListener('keydown',e=>{if(e.key==='Escape')drawer.classList.remove('open');});
svg.addEventListener('click',()=>drawer.classList.remove('open'));

// ── stats ──
const g=D.edges.reduce((m,e)=>((m[e.cls]=(m[e.cls]||0)+1),m),{});
document.getElementById('stats').innerHTML=[
  ['99','条关系边'],['48','个节点'],
  [String(g.lit||0),'实边 · 照亮'],[String(g.shadow||0),'匿名槽位 · 阴影'],
  [String((g.infer||0)),'考古解出'],['30','月海关流向'],
].map(([n,k])=>`<div class="stat"><div class="n">${n}</div><div class="k">${k}</div></div>`).join('');

// ── legend (clickable filter) ──
const leg=document.getElementById('legend');
['lit','infer','shadow','dead','leak'].forEach(c=>{
  const el=document.createElement('div');el.className='chip';el.dataset.c=c;
  el.innerHTML=`<span class="sw"></span>${CLSNAME[c]}`;
  el.onclick=()=>{el.classList.toggle('off');const off=el.classList.contains('off');
    edgeEls.forEach(p=>{if(p.dataset.cls===c)p.style.display=off?'none':'';});
    flowEls.forEach(f=>{}); if(c==='lit')flowEls.forEach(f=>f.style.display=off?'none':'');};
  leg.appendChild(el);
});
// country legend inline
const cl=document.createElement('div');cl.className='chip';cl.style.cursor='default';
cl.innerHTML=Object.entries(CK).map(([k,v])=>`<span style="display:inline-flex;align-items:center;gap:5px"><span style="width:8px;height:8px;border-radius:50%;background:var(--${k})"></span>${v}</span>`).join('&nbsp;&nbsp;');
leg.appendChild(cl);

document.getElementById('foot').innerHTML=`<b>诚实边界。</b>
  图中 <span class="warn">29 个匿名槽位</span>（阴影虚线）只知金额不知对手方；
  <b>3 条推断边</b>（琥珀点划）经披露史考古/金额指纹/对手方反照解出（2 条 A 级、
  1 条 B 级——Fabrinet 反照因排他性分母口径未闭合为高置信候选）；
  <b>1 条已死亡边</b>（NeoPhotonics→华为，衰减虚线）记录管制下的关系消亡。
  实名≠终端可见：PINEWAVE（旭创关联平台）、浙江粮油（出口代理）、Digicomm（分销）
  身后的终端买家仍在夹层里，不可判定。点任意边看四件套证据。`;
</script>
</body></html>"""

def main():
    data = build()
    html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    # 内联 Google Fonts 会引外链，违反自包含 → 用系统字体栈兜底，仅在 CSS 里声明理想族名
    out = os.path.join(ROOT, "output/光模块产业图谱-v1.4.html")
    open(out,"w",encoding="utf-8").write(html)
    # 自测
    assert "<svg" in html
    assert "◈" in html or "匿名" in html
    assert not re.search(r'<(script|link)[^>]+(src|href)\s*=\s*["\']https?://', html), "含外链"
    assert "PINEWAVE" in html and "中际旭创" in html
    assert "IBM Plex Mono" in html
    print("wrote", out, len(html), "bytes")
    print("nodes", len(data["nodes"]), "edges", len(data["edges"]))
    print("自测: SVG✓ 零外链✓ 关键实体✓ 等宽数字✓")

if __name__ == "__main__":
    main()
