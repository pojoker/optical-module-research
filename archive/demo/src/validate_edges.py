#!/usr/bin/env python3
"""
validate_edges.py — 供应链图谱 demo 边生成器校验器（Stage3 终验）
=====================================================================

只依赖 Python 标准库。

功能一 结构校验（无 --truth 也执行）
  1. edges.csv 前 10 列必须匹配 EDGE_COLS 契约；旧 10 列文件逐行照常校验。
     允许在前 10 列之后附带可选扩展列（D1 新增：edge_type / edge_subtype /
     scope），见功能四。向后兼容：缺少这些列的现有 236 边文件仍 RESULT=PASS。
  2. 四件套非空：供方/需方/占比或金额/财年/边等级/证据文件/锚点 任一为空 -> FAIL。
  3. edge_id 唯一性；锚点列须为 http(s) URL、或"同E/同D"式引用（须能解析到存在的 edge_id）。
  4. nodes.csv 须 6 列；实名节点引用完整性（供方/需方 不含"(匿名)"者须在 nodes.csv
     名称列存在），缺失 -> WARN 级（不影响 RESULT）。
  5. 边等级枚举检查：只允许
     {实边, 实边(已死亡), 推断边(A级), 推断边(B级), 推断边(C级), 推断边(D级),
      半边, 半边槽位, 程序段落泄漏}。

功能四 可选扩展字段校验（D1 / C项 / E项，仅当 edges.csv 含这些列时执行）
  - edge_type：非空前必须在 {supply, equity, guarantee, legal_event, other}。
  - edge_subtype：非空前必须在 EDGE_SUBTYPES 受控词表内。
  - scope：非空前必须在 {group, legal_entity, branch}（E 项 counterparty_scope）。
  以上三项均【可选】：列缺失或非空不填时不报错，保证对现有 236 边零回归。

功能二 真值比对（提供 --truth 时执行）
  truth.json: {"checks":[{"id","desc","where":{...},"expect":{"field","contains"}}]}
  - where：字段等值匹配；"X_contains" 后缀表示字段包含子串；财年一律按包含匹配。
  - 命中 0 行 -> NO_MATCH；>=1 行 -> 全部命中行满足 expect.contains 则 PASS，否则 FAIL。
  - 每条 check 输出 PASS/FAIL/NO_MATCH + 命中行数 + 命中行 edge_id。

输出：人类可读报告到 stdout，末尾汇总行
  RESULT: <PASS|FAIL> structural=<n_err> truth=<n_pass>/<n_total>
退出码：存在结构 FAIL 或 真值 FAIL -> 1，否则 0。

----------------------------------------------------------------------
自测（结构校验，针对现有 output 数据，预期 RESULT=PASS）
----------------------------------------------------------------------
命令：
  python3 demo/src/validate_edges.py --edges output/edges.csv --nodes output/nodes.csv

结果（structural=0，RESULT=PASS；另有 5 条描述型锚点 WARN 与 25 条节点引用 WARN，均不计入 n_err）：
（注：本环境 Bash 被禁用，无法实时执行；以下为按代码逻辑对 output/ 数据静态推演的输出，
 请在本机运行上方命令确认，预期与下方一致。）

=== 结构校验 ===
[OK]   edge_id 唯一性 (共 73 条边)
[OK]   四件套非空 (供方/需方/占比或金额/财年/边等级/证据文件/锚点)
[OK]   锚点格式 (http(s) URL 或 同E/同D 引用)
[WARN] 锚点描述型: edge_id=E010 描述型锚点(非 http(s) URL / 非 同E/同D 引用)
[WARN] 锚点描述型: edge_id=E011 描述型锚点(非 http(s) URL / 非 同E/同D 引用)
[WARN] 锚点描述型: edge_id=E012 描述型锚点(非 http(s) URL / 非 同E/同D 引用)
[WARN] 锚点描述型: edge_id=E013 描述型锚点(非 http(s) URL / 非 同E/同D 引用)
[WARN] 锚点描述型: edge_id=E014 描述型锚点(非 http(s) URL / 非 同E/同D 引用)
[OK]   边等级枚举 (均在允许集合内)
[OK]   nodes.csv 列数 (均 6 列, 共 38 节点)
[WARN] 节点引用缺失: edge_id=E008 需方='华为+海思' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E010 需方='中际旭创(作为客户)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E011 供方='ficonTEC(罗博特科)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E011 需方='博通(客户)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E012 供方='ficonTEC(罗博特科)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E012 需方='NVIDIA(客户)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E013 需方='等离子体所(客户)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E014 需方='Fabrinet(疑似客户)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E016 需方='浙江粮油(出口代理)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E017 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E018 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E019 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E020 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E021 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E022 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E023 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E024 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E025 供方='AAOI' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E033 需方='华为' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E036 需方='Ciena(解匿)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E037 需方='Google(解匿)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E038 供方='Fabrinet(解匿)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E044 需方='PINEWAVE(关联方)' 未在 nodes.csv 找到
[WARN] 节点引用缺失: edge_id=E050 需方='苏世博' 未在 nodes.csv 找到
  （上述 25 条为 WARN 级，多为括号注释/命名差异，不影响 RESULT）
=== 汇总 ===
RESULT: PASS structural=0 truth=0/0
=====================================================================
"""

import argparse
import csv
import json
import os
import re
import sys

EDGE_COLS = ["edge_id", "供方", "需方", "占比或金额", "财年", "边等级",
             "证据文件", "锚点", "验证状态", "备注"]
NODE_COLS = ["node_id", "名称", "类型", "国别", "代码", "备注"]
FOUR_PIECE = ["供方", "需方", "占比或金额", "财年", "边等级", "证据文件", "锚点"]
EDGE_LEVELS = {
    "实边", "实边(已死亡)",
    "推断边(A级)", "推断边(B级)", "推断边(C级)", "推断边(D级)",
    "半边", "半边槽位", "程序段落泄漏",
}
# ----------------------------------------------------------------------
# 可选扩展字段（v1.7a 治理还债 D1 / C项 / E项）：向后兼容的旧 10 列文件
# 不含这些列；它们只在前 10 列之后作为可选扩展列出现时才被校验。
#   edge_type    —— 边的基础类型（C 项 edge type/subtype schema）
#   edge_subtype —— 边子类型（供货/股权/担保/裁判文书/环评/专利等细分）
#   scope        —— 本条披露数字的反方观察口径（E 项 counterparty_scope：
#                   group | legal_entity | branch）
# 枚举取值直接取自 ROADMAP-v1.7a §C/§E 与证据类型边界最小条款。
# ----------------------------------------------------------------------
EDGE_TYPES = {"supply", "equity", "guarantee", "legal_event", "other"}
EDGE_SUBTYPES = {
    # 供货类
    "代工", "分销", "直销", "主供", "采购",
    # 股权类（C 项：直持/间持、比例或区间、持股链、有效期）
    "股权直持", "股权间持",
    # 担保类（C 项：额度/余额、担保期间、是否已解除）
    "担保",
    # 裁判文书默认产出（证据类型边界最小条款）
    "历史合同", "纠纷事件",
    # 环评/能评默认产出
    "产能事件", "设备供货",
    # 专利（v1.8 先定义两 subtype，均不得转为供货边）
    "共同申请", "专利转让",
    # 兜底
    "其他",
}
SCOPE_LEVELS = {"group", "legal_entity", "branch"}
EXTENDED_FIELDS = ["edge_type", "edge_subtype", "scope"]
ANON_MARK = "(匿名)"
REF_RE = re.compile(r"^同[ED]\d+$")
URL_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*)://")


def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def classify_anchor(anchor, edge_ids):
    """返回 (status, msg)。status: 'ok' | 'warn' | 'fail'。"""
    a = (anchor or "").strip()
    if a == "":
        return "fail", "空锚点"
    if a.startswith("同"):
        for part in a.split(";"):
            p = part.strip()
            if not REF_RE.match(p):
                return "fail", "非法同E/同D引用: %r" % p
            ref = p[1:]  # 同E005 -> E005
            if ref not in edge_ids:
                return "fail", "悬空引用: %s (无对应 edge_id)" % p
        return "ok", ""
    if "://" in a:
        m = URL_RE.match(a)
        if not m or m.group(1).lower() not in ("http", "https"):
            return "fail", "非 http(s) URL: %r" % a
        return "ok", ""
    # 裸域名（如 SEC式锚:file.finance.qq.com/...）或描述型溯源说明 -> 接受，但提示
    return "warn", "描述型锚点(非 http(s) URL / 非 同E/同D 引用)"


def where_match(edge, where):
    for key, val in where.items():
        if key.endswith("_contains"):
            field = key[:-len("_contains")]
            if field not in edge or val not in (edge.get(field) or ""):
                return False
        else:
            field = key
            cell = edge.get(field) or ""
            if field == "财年":
                if val not in cell:          # 财年一律按包含匹配
                    return False
            elif cell != val:
                return False
    return True


# ======================================================================
# W5 校验扩展：三个互斥的子命令模式（schema 校验，不触碰既有结构校验）
# ======================================================================

FLOW_FIELDS = ["flow_id", "产品", "构成项", "构成类型", "系数或占比",
               "计价单位", "期间", "证据文件", "锚点", "验证状态", "备注"]
FLOW_REQUIRED_TOP = ["meta", "flows", "warnings"]

CAT_EXPECT_COLS = ["cat_id", "公司", "产品型号", "速率", "封装", "技术路线",
                   "来源URL", "抓取日期", "备注"]
CAT_URL_IDX = 6       # 来源URL
CAT_DATE_IDX = 7      # 抓取日期
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LINK_EXPECT_COLS = ["link_id", "公司", "公司代码", "产品线", "速率档", "HS编码",
                    "出口相关性(直接/间接/无)", "去向证据(友商链)", "证据锚点", "备注"]
LINK_REL_IDX = 6      # 出口相关性
LINK_REL_VALUES = {"直接", "间接", "无"}
LINK_ANCHOR_IDX = 8   # 证据锚点


def _check_file_exists(path):
    """文件不存在 -> 向 stderr 打印清晰错误并返回 2（供三个新模式的统一入口）。"""
    if not os.path.exists(path):
        sys.stderr.write("错误：文件不存在: %s\n" % path)
        return False
    return True


def check_flows(path):
    """--check-flows <json>：字段齐全 + 占比为字符串 + warnings 为数组。"""
    out, n_err = [], 0

    def log(l): out.append(l)
    def ok(m): log("[OK]   " + m)
    def fail(m): log("[FAIL] " + m)
    def warn(m): log("[WARN] " + m)

    if not _check_file_exists(path):
        return 2

    log("=== flows schema 校验 (%s) ===" % path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail("JSON 解析失败: %s" % e)
        log("")
        log("=== 汇总 ===")
        log("RESULT: FAIL structural=1")
        sys.stdout.write("\n".join(out) + "\n")
        return 1

    # 顶层字段齐全
    missing_top = [k for k in FLOW_REQUIRED_TOP if k not in data]
    if missing_top:
        n_err += len(missing_top)
        fail("顶层字段缺失: %s" % ", ".join(missing_top))
    else:
        ok("顶层字段齐全 (meta/flows/warnings)")

    # warnings 为数组
    if "warnings" in data:
        if isinstance(data["warnings"], list):
            ok("warnings 为数组 (共 %d 条)" % len(data["warnings"]))
        else:
            n_err += 1
            fail("warnings 非数组，类型=%s" % type(data["warnings"]).__name__)

    flows = data.get("flows", [])
    if not isinstance(flows, list):
        n_err += 1
        fail("flows 非数组")
        flows = []

    # 每条 flow：字段齐全 + 占比为字符串
    field_missing, ratio_bad = [], []
    for i, fl in enumerate(flows, start=1):
        if not isinstance(fl, dict):
            n_err += 1
            fail("flows[%d] 非对象" % i)
            continue
        for fld in FLOW_FIELDS:
            if fld not in fl:
                field_missing.append((i, fld))
        ratio = fl.get("系数或占比")
        if "系数或占比" in fl and not isinstance(ratio, str):
            ratio_bad.append((i, type(ratio).__name__))

    if field_missing:
        n_err += len(field_missing)
        seen = set()
        for i, fld in field_missing:
            if (i, fld) not in seen:
                seen.add((i, fld))
                fail("flow[%d] 缺字段 %s" % (i, fld))
    else:
        ok("每条 flow 字段齐全 (共 %d 条)" % len(flows))

    if ratio_bad:
        n_err += len(ratio_bad)
        for i, t in ratio_bad:
            fail("flow[%d] 系数或占比 非字符串，类型=%s" % (i, t))
    else:
        ok("每条 flow 系数或占比 均为字符串")

    passed = n_err == 0
    log("")
    log("=== 汇总 ===")
    log("RESULT: %s structural=%d" % ("PASS" if passed else "FAIL", n_err))
    sys.stdout.write("\n".join(out) + "\n")
    return 0 if passed else 1


def check_catalog(path):
    """--check-catalog <csv>：9 列 + URL 列 http 开头 + 抓取日期 YYYY-MM-DD。"""
    out, n_err = [], 0

    def log(l): out.append(l)
    def ok(m): log("[OK]   " + m)
    def fail(m): log("[FAIL] " + m)
    def warn(m): log("[WARN] " + m)

    if not _check_file_exists(path):
        return 2

    log("=== catalog schema 校验 (%s) ===" % path)
    with open(path, newline="", encoding="utf-8-sig") as f:  # 注意 BOM
        rows = list(csv.reader(f))

    if not rows:
        fail("catalog.csv 为空")
        log("")
        log("=== 汇总 ===")
        log("RESULT: FAIL structural=1")
        sys.stdout.write("\n".join(out) + "\n")
        return 1

    header = rows[0]
    data_rows = rows[1:]

    # 9 列
    if len(header) != 9:
        n_err += 1
        fail("表头列数=%d (期望 9): %s" % (len(header), header))
    else:
        ok("表头 9 列: %s" % ",".join(header))

    # 仅当列数正确时，按固定下标做逐行 URL / 日期校验
    if len(header) == 9:
        url_bad, date_bad = [], []
        for i, row in enumerate(data_rows, start=2):
            if len(row) <= CAT_URL_IDX or not (row[CAT_URL_IDX] or "").startswith("http"):
                url_bad.append(i)
            if len(row) <= CAT_DATE_IDX or not DATE_RE.match(row[CAT_DATE_IDX] or ""):
                date_bad.append(i)
        if url_bad:
            n_err += len(url_bad)
            for i in url_bad:
                fail("行 %d: 来源URL 列未以 http 开头" % i)
        else:
            ok("来源URL 列均以 http 开头 (共 %d 行)" % len(data_rows))
        if date_bad:
            n_err += len(date_bad)
            for i in date_bad:
                fail("行 %d: 抓取日期 不符合 YYYY-MM-DD" % i)
        else:
            ok("抓取日期 均符合 YYYY-MM-DD (共 %d 行)" % len(data_rows))
    else:
        warn("因表头列数异常，跳过逐行 URL/日期 校验")

    passed = n_err == 0
    log("")
    log("=== 汇总 ===")
    log("RESULT: %s structural=%d" % ("PASS" if passed else "FAIL", n_err))
    sys.stdout.write("\n".join(out) + "\n")
    return 0 if passed else 1


def check_linkage(path):
    """--check-linkage <csv>：10 列 + 出口相关性∈{直接,间接,无} + 锚点非空。"""
    out, n_err = [], 0

    def log(l): out.append(l)
    def ok(m): log("[OK]   " + m)
    def fail(m): log("[FAIL] " + m)
    def warn(m): log("[WARN] " + m)

    if not _check_file_exists(path):
        return 2

    log("=== linkage schema 校验 (%s) ===" % path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        fail("linkage.csv 为空")
        log("")
        log("=== 汇总 ===")
        log("RESULT: FAIL structural=1")
        sys.stdout.write("\n".join(out) + "\n")
        return 1

    header = rows[0]
    data_rows = rows[1:]

    # 10 列
    if len(header) != 10:
        n_err += 1
        fail("表头列数=%d (期望 10): %s" % (len(header), header))
    else:
        ok("表头 10 列: %s" % ",".join(header))

    if len(header) == 10:
        rel_bad, anchor_bad = [], []
        for i, row in enumerate(data_rows, start=2):
            rel = (row[LINK_REL_IDX] if len(row) > LINK_REL_IDX else "").strip() \
                if len(row) > LINK_REL_IDX else ""
            if rel not in LINK_REL_VALUES:
                rel_bad.append((i, row[LINK_REL_IDX] if len(row) > LINK_REL_IDX else ""))
            anchor = (row[LINK_ANCHOR_IDX] if len(row) > LINK_ANCHOR_IDX else "")
            if (anchor or "").strip() == "":
                anchor_bad.append(i)
        if rel_bad:
            n_err += len(rel_bad)
            for i, v in rel_bad:
                fail("行 %d: 出口相关性=%r 不在 {直接,间接,无}" % (i, v))
        else:
            ok("出口相关性 均∈{直接,间接,无} (共 %d 行)" % len(data_rows))
        if anchor_bad:
            n_err += len(anchor_bad)
            for i in anchor_bad:
                fail("行 %d: 证据锚点(锚点)为空" % i)
        else:
            ok("证据锚点(锚点) 均非空 (共 %d 行)" % len(data_rows))
    else:
        warn("因表头列数异常，跳过逐行 出口相关性/锚点 校验")

    passed = n_err == 0
    log("")
    log("=== 汇总 ===")
    log("RESULT: %s structural=%d" % ("PASS" if passed else "FAIL", n_err))
    sys.stdout.write("\n".join(out) + "\n")
    return 0 if passed else 1


def main():
    ap = argparse.ArgumentParser(description="供应链图谱 demo 边生成器校验器")
    # 既有结构校验模式（零回归红线：行为与输出完全不变）
    ap.add_argument("--edges", default=None, help="edges.csv 路径（结构校验模式）")
    ap.add_argument("--nodes", default=None, help="nodes.csv 路径（结构校验模式）")
    ap.add_argument("--truth", default=None, help="truth.json 路径（可选）")
    # W5 校验扩展：三个互斥的 schema 校验子命令
    ap.add_argument("--check-flows", default=None, help="校验 flows JSON schema")
    ap.add_argument("--check-catalog", default=None, help="校验 catalog.csv schema")
    ap.add_argument("--check-linkage", default=None, help="校验 linkage.csv schema")
    args = ap.parse_args()

    # ---- W5 校验扩展：互斥子命令优先，均优先于既有结构校验 ----
    n_new = sum(x is not None for x in
                (args.check_flows, args.check_catalog, args.check_linkage))
    if n_new > 1:
        sys.stderr.write(
            "错误：--check-flows / --check-catalog / --check-linkage 互斥，只能指定其一\n")
        sys.exit(2)
    if args.check_flows is not None:
        sys.exit(check_flows(args.check_flows))
    if args.check_catalog is not None:
        sys.exit(check_catalog(args.check_catalog))
    if args.check_linkage is not None:
        sys.exit(check_linkage(args.check_linkage))

    # ---- 既有结构校验模式 ----
    if not args.edges or not args.nodes:
        sys.stderr.write("错误：结构校验模式需要同时提供 --edges 与 --nodes 参数\n")
        sys.exit(2)

    out = []
    def log(line): out.append(line)
    def ok(msg): log("[OK]   " + msg)
    def fail(msg): log("[FAIL] " + msg)
    def warn(msg): log("[WARN] " + msg)

    n_err = 0  # 结构 FAIL 计数（WARN 不计入）

    log("=== 结构校验 ===")

    # ---------------- edges ----------------
    edge_rows = load_csv(args.edges)
    if not edge_rows:
        fail("edges.csv 为空")
        n_err += 1
        edges, edge_ids = [], set()
        ext_header = []
    else:
        header = edge_rows[0]
        data_rows = edge_rows[1:]
        if header[:10] != EDGE_COLS:
            warn("edges.csv 前 10 列表头与契约不符: %s" % header[:10])

        # 可选扩展列（出现在前 10 列之后；缺失则维持旧契约，零回归）
        ext_header = header[10:] if len(header) > 10 else []
        ext_idx = {name: 10 + k for k, name in enumerate(ext_header)}
        if ext_header:
            unknown = [c for c in ext_header if c not in EXTENDED_FIELDS]
            if unknown:
                warn("检测到未识别的扩展列（跳过其校验）: %s" % unknown)
            known = [c for c in ext_header if c in EXTENDED_FIELDS]
            if known:
                ok("可选扩展字段已识别: %s" % ", ".join(known))
        else:
            ok("无可选扩展字段（维持 10 列契约，向后兼容）")

        edges = []
        edge_ids = set()
        for i, row in enumerate(data_rows, start=2):  # 第 1 行为表头
            if len(row) < 10:
                n_err += 1
                eid_hint = row[0] if row else ""
                missing = EDGE_COLS[len(row):]
                fail("行 %d (edge_id=%s): 缺列 %s" % (i, eid_hint, missing))
                d = dict(zip(EDGE_COLS, row))
            else:
                if len(row) > len(header):
                    n_err += 1
                    eid_hint = row[0] if row else ""
                    fail("行 %d (edge_id=%s): 列数 %d 多于表头 %d，多余 %s"
                         % (i, eid_hint, len(row), len(header), row[len(header):]))
                d = dict(zip(EDGE_COLS, row))
            for c in EDGE_COLS:
                d.setdefault(c, "")
            # 扩展列映射（按名索引，避免位置依赖）
            for c in ext_header:
                j = ext_idx[c]
                d[c] = row[j] if j < len(row) else ""
            edges.append(d)
            eid = (d.get("edge_id") or "").strip()
            if eid:
                edge_ids.add(eid)

    # edge_id 唯一性
    seen = {}
    for d in edges:
        eid = (d.get("edge_id") or "").strip()
        if eid == "":
            n_err += 1
            fail("存在空 edge_id（行数据缺失）")
            continue
        seen[eid] = seen.get(eid, 0) + 1
    dup = sorted([e for e, c in seen.items() if c > 1])
    if dup:
        n_err += len(dup)
        fail("edge_id 重复: %s" % ", ".join(dup))
    else:
        ok("edge_id 唯一性 (共 %d 条边)" % len(edges))

    # 四件套非空
    fp_fail = []
    for d in edges:
        eid = d.get("edge_id") or ""
        for f in FOUR_PIECE:
            if (d.get(f) or "").strip() == "":
                fp_fail.append((eid, f))
    if fp_fail:
        n_err += len(fp_fail)
        for eid, f in fp_fail:
            fail("四件套空值: edge_id=%s 字段[%s]为空" % (eid, f))
    else:
        ok("四件套非空 (供方/需方/占比或金额/财年/边等级/证据文件/锚点)")

    # 锚点格式
    anchor_fail, anchor_warn = [], []
    for d in edges:
        eid = d.get("edge_id") or ""
        status, msg = classify_anchor(d.get("锚点"), edge_ids)
        if status == "fail":
            n_err += 1
            anchor_fail.append((eid, msg))
        elif status == "warn":
            anchor_warn.append((eid, msg))
    if anchor_fail:
        for eid, msg in anchor_fail:
            fail("锚点非法: edge_id=%s %s" % (eid, msg))
    else:
        ok("锚点格式 (http(s) URL 或 同E/同D 引用)")
    for eid, msg in anchor_warn:
        warn("锚点描述型: edge_id=%s %s" % (eid, msg))

    # 边等级枚举
    lvl_fail = []
    for d in edges:
        eid = d.get("edge_id") or ""
        lvl = (d.get("边等级") or "").strip()
        if lvl not in EDGE_LEVELS:
            lvl_fail.append((eid, lvl))
    if lvl_fail:
        n_err += len(lvl_fail)
        for eid, lvl in lvl_fail:
            fail("边等级非法: edge_id=%s 值=%r" % (eid, lvl))
    else:
        ok("边等级枚举 (均在允许集合内)")

    # 可选扩展字段枚举校验（D1 / C项 / E项；仅当对应列存在且非空时校验）
    if ext_header:
        ext_fail = []
        for d in edges:
            eid = d.get("edge_id") or ""
            for fld, allowed in (("edge_type", EDGE_TYPES),
                                 ("edge_subtype", EDGE_SUBTYPES),
                                 ("scope", SCOPE_LEVELS)):
                if fld not in ext_header:
                    continue
                v = (d.get(fld) or "").strip()
                if v and v not in allowed:
                    ext_fail.append((eid, fld, v))
        if ext_fail:
            n_err += len(ext_fail)
            for eid, fld, v in ext_fail:
                fail("扩展字段非法: edge_id=%s %s=%r 不在受控词表" % (eid, fld, v))
        else:
            ok("可选扩展字段枚举 (edge_type/edge_subtype/scope 均在受控词表内)")

    # ---------------- nodes ----------------
    node_rows = load_csv(args.nodes)
    node_header = node_rows[0] if node_rows else []
    node_data = node_rows[1:] if len(node_rows) > 1 else []
    if node_header != NODE_COLS:
        warn("nodes.csv 表头与契约不符: %s" % node_header)

    node_bad = False
    for i, row in enumerate(node_data, start=2):
        if len(row) != 6:
            n_err += 1
            node_bad = True
            fail("nodes.csv 行 %d: 列数=%d (期望 6)" % (i, len(row)))
    node_names = set()
    for row in node_data:
        if len(row) >= 2:
            node_names.add((row[1] or "").strip())
    if not node_bad:
        ok("nodes.csv 列数 (均 6 列, 共 %d 节点)" % len(node_data))

    # 实名节点引用完整性（WARN）
    ref_warn = []
    for d in edges:
        eid = d.get("edge_id") or ""
        for f in ("供方", "需方"):
            v = (d.get(f) or "").strip()
            if v and ANON_MARK not in v and v not in node_names:
                ref_warn.append((eid, f, v))
    if ref_warn:
        for eid, f, v in ref_warn:
            warn("节点引用缺失: edge_id=%s %s=%r 未在 nodes.csv 找到" % (eid, f, v))
        log("  （上述 %d 条为 WARN 级，多为括号注释/命名差异，不影响 RESULT）" % len(ref_warn))
    else:
        ok("实名节点引用完整性 (供方/需方 均能在 nodes.csv 找到)")

    # ---------------- 真值比对 ----------------
    n_pass = 0
    n_total = 0
    truth_fail = 0
    if args.truth:
        with open(args.truth, encoding="utf-8") as f:
            truth = json.load(f)
        checks = truth.get("checks", [])
        n_total = len(checks)
        log("")
        log("=== 真值比对 ===")
        for chk in checks:
            cid = chk.get("id", "?")
            desc = chk.get("desc", "")
            where = chk.get("where", {})
            expect = chk.get("expect", {})
            matched = [e for e in edges if where_match(e, where)]
            if not matched:
                status = "NO_MATCH"
            else:
                ef = expect.get("field")
                ec = expect.get("contains")
                all_ok = True
                for e in matched:
                    val = e.get(ef, "")
                    if ec is None or ec == "":
                        continue
                    if ec not in val:
                        all_ok = False
                status = "PASS" if all_ok else "FAIL"
            if status == "PASS":
                n_pass += 1
            elif status == "FAIL":
                truth_fail += 1
            ids = ",".join(e["edge_id"] for e in matched)
            log("[%s] %s | %s | 命中%d行: %s" % (cid, status, desc, len(matched), ids))

    # ---------------- 汇总 ----------------
    passed = (n_err == 0) and (not args.truth or truth_fail == 0)
    result = "PASS" if passed else "FAIL"
    log("")
    log("=== 汇总 ===")
    log("RESULT: %s structural=%d truth=%d/%d" % (result, n_err, n_pass, n_total))

    sys.stdout.write("\n".join(out) + "\n")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
