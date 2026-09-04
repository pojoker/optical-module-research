#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discovery_queue.py — 统一发现队列 + 判定闸台账（**原型-未准入**，kimi/k3 车道，D2 硬化版）

定位：ROADMAP-v1.7a（已冻结）"常设容器 = 统一发现队列 + 判定闸"的候选实现。
核心主张——S0 该常设的是**队列与闸**（容器），该事件/缺口/治理触发的是**算子**；
无触发不扫描，不为流程完整制造任务。本脚本保持"原型-未准入"标注，直至终验转正。

判定闸台账 schema（v1.7a 落地）：
  六类裁决：生产中 / 拟生产 / 采购使用 / 销售代理 / 仅提及 / 无法判断
  裁决四件套：闸裁决 + 裁决人（闸 owner=终验）+ 裁决时间戳（ISO 8601）+ 理由
  不变式：四者同空（未裁决）或同填（已裁决），不允许半填；裁决逐条入台账。

发现算子（v1.7a：事件/缺口/治理触发）：
  media_lead    媒体事件线索（真实入队 flows/out/leads-pool.csv）
  customs_diff  海关分国别月度量结构突变（实算 flows/out/customs-partners.csv）
  bom_scan      S0a 词表扫描（MOCK 占位；触发=词表变更或年度快照）
  bfs_jump      S0b 递归跳（MOCK 占位；触发=新入账公开主体）
  gap_list      S0c 必要接口/结构缺口清单（保留算子 id，接口预留未注册；
                非边——BOM 必需部件不能直接推出公司间交易边；缺口触发）

真实算子接口：见 DiscoveryOperator。真实实现子类化该接口、注册进
OPERATOR_REGISTRY 即接入，队列/闸台账/自检不变；MOCK 类同构占位。
详见 flows/discovery-queue-README.md。

红线执行：
  - 本车道**不作任何闸裁决**（证据判定归终验）。真实闸台账输出为空骨架；
    自检中的台账正/反例仅存在于内存，不写入产出文件。
  - MOCK 行仅为 schema/接口演示，行内显式标注 MOCK，不得引用。
  - 海关量异常只是触发器（旁证，不承重），队列内"待验证T1路径"已写明。
  - 代码零实体名：脚本不含任何公司/实体名，实体级裁决归 entity-registry 与终验。

纪律断言（脚本自检，任一失败即退出码 1）：
  A1 发现算子 ∈ 已知集合；A2 状态 ∈ 状态机合法值；A3 queue_id 唯一；
  A4 bom_scan 行必须带词表出处（含版本）；
  A5 闸台账逐行：queue_id 必须存在、裁决 ∈ 六类、四件套同空或同填、
     时间戳为 ISO 格式（含 MOCK 正例必过 / 反例必拦的内存自测）；
  A6 候选集覆盖率分母只统计"过闸且裁决=生产中"的对象——原始命中永远不作
     分母（D 项防线；拟生产是否计入 C_layer 属终验口径，本脚本不预断）。

输入（只读）：flows/out/leads-pool.csv、flows/out/customs-partners.csv
产出（前缀 proto-，原型-未准入，不覆盖任何既有产物）：
  flows/out/proto-discovery-queue.csv        统一发现队列
  flows/out/proto-gate-ledger-skeleton.csv   判定闸台账骨架（空，待终验填写）
  flows/out/proto-coverage-mock.csv          候选集覆盖率表演示行（MOCK）
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEADS_CSV = ROOT / "flows" / "out" / "leads-pool.csv"
PARTNERS_CSV = ROOT / "flows" / "out" / "customs-partners.csv"
OUT_QUEUE = ROOT / "flows" / "out" / "proto-discovery-queue.csv"
OUT_GATE = ROOT / "flows" / "out" / "proto-gate-ledger-skeleton.csv"
OUT_COVERAGE = ROOT / "flows" / "out" / "proto-coverage-mock.csv"

# v1.7a 算子集：media_lead/customs_diff 真实；bom_scan(S0a)/bfs_jump(S0b) MOCK；
# gap_list(S0c 必要接口清单，非边)保留算子 id，接口预留未注册。
OPERATORS = {"media_lead", "customs_diff", "bom_scan", "bfs_jump", "gap_list"}
STATES = {"待闸", "过闸-待边工序", "剔除-已登记", "已入图"}
# 闸六类裁决（v1.7a 冻结；闸 owner=终验，裁决逐条入台账）
VERDICTS = {"生产中", "拟生产", "采购使用", "销售代理", "仅提及", "无法判断"}

# customs_diff 触发阈值：2026H1 vs 2025H1 分伙伴金额
DIFF_PCT = 50.0          # 同比变化幅度阈值 %
DIFF_ABS_USD = 5_000_000  # 绝对变化阈值（防小基数噪声）

QUEUE_HEADER = [
    "queue_id", "发现算子", "对象类型", "对象", "发现证据(URL/出处)", "发现日期",
    "待验证T1路径", "状态", "闸裁决", "闸裁决人", "闸裁决时间戳", "裁决理由", "备注",
]
# 闸台账 schema（v1.7a 落地版）：六类裁决 + owner/时间戳/理由四件套
GATE_HEADER = [
    "gate_id", "queue_id", "对象", "命中上下文(段落/词)", "段落类型预判",
    "闸裁决", "裁决人", "裁决时间戳", "理由", "剔除登记号(若剔除)",
]
# 候选集覆盖率表（v1.7a D 项公式；禁称总体查全）
COVERAGE_HEADER = [
    "部件词", "词表出处(含版本)", "语料快照日",
    "C_layer_过闸生产候选数", "G_layer_已入图层主体数", "交集_G∩C",
    "候选集覆盖率", "已裁决数", "待裁决数", "待裁决老化(天)", "候选处理率", "口径备注",
]

_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$")


def new_row(qid, op, otype, obj, evidence, date, t1path, note=""):
    return {
        "queue_id": qid, "发现算子": op, "对象类型": otype, "对象": obj,
        "发现证据(URL/出处)": evidence, "发现日期": date,
        "待验证T1路径": t1path, "状态": "待闸", "闸裁决": "", "闸裁决人": "",
        "闸裁决时间戳": "", "裁决理由": "", "备注": note,
    }


class DiscoveryOperator:
    """发现算子接口（v1.7a：容器常设、算子事件/缺口/治理触发，无触发不扫描）。

    真实算子接入契约：
      1. 子类化本类，填 name（∈ OPERATORS）/ trigger / object_type，实现 scan()；
      2. scan() 只经 new_row() 产出行（状态=待闸；闸字段留空，裁决归终验）；
         证据字段必须可回溯（URL/出处+日期），queue_id 建议 DQ-<算子标记>-<序号>；
      3. 注册进 OPERATOR_REGISTRY；队列 schema、闸台账、A1-A6 自检均不变。
    MOCK 算子（is_mock=True）仅演示接口与 schema，产出不得引用。
    """
    name = ""
    trigger = ""
    object_type = ""
    is_mock = False

    def scan(self):
        raise NotImplementedError


class MediaLeadOperator(DiscoveryOperator):
    name = "media_lead"
    trigger = "媒体事件线索入池（flows/out/leads-pool.csv 更新）"
    object_type = "company"

    def scan(self):
        """media_lead：线索池真实入队。状态映射：待验证→待闸。"""
        rows = []
        with open(LEADS_CSV, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rows.append(new_row(
                    qid=f"DQ-{r['lead_id']}", op=self.name, otype=self.object_type,
                    obj=r["涉及公司"], evidence=r["线索来源(媒体/公众号名+URL)"],
                    date=r["报道日期"], t1path=r["待验证的T1路径"],
                    note=f"线索描述：{r['线索描述'][:80]}…" if len(r["线索描述"]) > 80
                         else f"线索描述：{r['线索描述']}",
                ))
        return rows


class CustomsDiffOperator(DiscoveryOperator):
    name = "customs_diff"
    trigger = "海关月度数据更新（分伙伴金额结构突变超阈值）"
    object_type = "flow_anomaly"

    def scan(self):
        """customs_diff：分伙伴 2026H1 vs 2025H1 金额同比，实算触发器。"""
        sums = {}
        with open(PARTNERS_CSV, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["币种"] != "USD":
                    continue
                ym = r["月份"]
                half = "H1-2025" if "202501" <= ym <= "202506" else \
                       "H1-2026" if "202601" <= ym <= "202606" else None
                if half:
                    key = (r["贸易伙伴"], half)
                    sums[key] = sums.get(key, 0) + float(r["金额"])
        partners = {p for p, _ in sums}
        rows, n = [], 0
        for p in sorted(partners):
            a, b = sums.get((p, "H1-2025"), 0.0), sums.get((p, "H1-2026"), 0.0)
            delta = b - a
            pct = (delta / a * 100.0) if a else (float("inf") if b else 0.0)
            if abs(pct) >= DIFF_PCT and abs(delta) >= DIFF_ABS_USD:
                n += 1
                rows.append(new_row(
                    qid=f"DQ-CD-{n:03d}", op=self.name, otype=self.object_type,
                    obj=p,
                    evidence="flows/out/customs-partners.csv 自算（2025H1 vs 2026H1，USD）",
                    date="2026-07-24",
                    t1path=("按省份分拆+台账节点定位对应该伙伴国的主要出口主体，"
                            "定向检索其产能/募投/环评披露；海关量为旁证不承重"),
                    note=(f"2025H1={a:,.0f} → 2026H1={b:,.0f} USD，"
                          f"Δ={delta:+,.0f}（{pct:+.1f}%）"),
                ))
        return rows


class BomScanMock(DiscoveryOperator):
    """S0a 词表扫描占位。真实实现：词表版本 + 语料快照 → 命中段落 → 入队待闸。"""
    name = "bom_scan"
    trigger = "词表变更或年度快照"
    object_type = "company"
    is_mock = True

    def scan(self):
        return [
            new_row(
                qid="DQ-BOM-MOCK-001", op=self.name, otype=self.object_type,
                obj="MOCK-示例主体甲",
                evidence="MOCK（schema 占位，非真实检索结果）",
                date="MOCK",
                t1path="MOCK：命中段落上下文 → 判定闸（六类裁决）",
                note="词表出处：MOCK-词表-v0（占位）；MOCK 行不得引用",
            ),
        ]


class BfsJumpMock(DiscoveryOperator):
    """S0b 递归跳占位。真实实现：新入账公开主体 + 证券代码 → 核心披露 → 对手方段落。"""
    name = "bfs_jump"
    trigger = "新入账公开主体"
    object_type = "company"
    is_mock = True

    def scan(self):
        return [
            new_row(
                qid="DQ-BFS-MOCK-001", op=self.name, otype=self.object_type,
                obj="MOCK-示例主体乙",
                evidence=("MOCK（接口占位：真实实现以新入账公开主体证券代码"
                          "枚举其当期核心披露的交易对手段落）"),
                date="MOCK",
                t1path="MOCK：证券代码 → 核心披露 → 对手方段落 → 判定闸",
                note="触发=新入账公开主体；MOCK 行不得引用",
            ),
        ]


OPERATOR_REGISTRY = [
    MediaLeadOperator(),
    CustomsDiffOperator(),
    BomScanMock(),
    BfsJumpMock(),
    # gap_list（S0c 必要接口/结构缺口清单，非边）：算子 id 保留，接口预留未注册。
]


def validate_gate_ledger(rows, queue_ids):
    """A5：闸台账逐行校验（六类裁决 + 四件套不变式 + ISO 时间戳）。

    返回错误列表（空=通过）。闸 owner=终验；本函数只验合法性，不作裁决。
    """
    errors = []
    known = set(queue_ids)
    for r in rows:
        gid = r.get("gate_id") or "<无gate_id>"
        if r["queue_id"] not in known:
            errors.append(f"A5 {gid}: queue_id {r['queue_id']!r} 不在队列中")
        if r["闸裁决"] and r["闸裁决"] not in VERDICTS:
            errors.append(f"A5 {gid}: 非法裁决 {r['闸裁决']!r}（六类之外）")
        quartet = [r["闸裁决"], r["裁决人"], r["裁决时间戳"], r["理由"]]
        if any(quartet) and not all(quartet):
            errors.append(f"A5 {gid}: 裁决四件套（裁决/裁决人/时间戳/理由）须同空或同填")
        if r["裁决时间戳"] and not _ISO_RE.match(r["裁决时间戳"]):
            errors.append(f"A5 {gid}: 裁决时间戳非 ISO 8601: {r['裁决时间戳']!r}")
    return errors


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def self_test(queue, gate_rows):
    errors = []
    ids = [r["queue_id"] for r in queue]
    if len(ids) != len(set(ids)):
        errors.append("A3 queue_id 不唯一")
    for r in queue:
        if r["发现算子"] not in OPERATORS:
            errors.append(f"A1 未知算子: {r['queue_id']}")
        if r["状态"] not in STATES:
            errors.append(f"A2 非法状态: {r['queue_id']}")
        if r["闸裁决"] and r["闸裁决"] not in VERDICTS:
            errors.append(f"A2b 队列内非法闸裁决: {r['queue_id']}")
        if r["发现算子"] == "bom_scan" and "词表出处" not in r["备注"]:
            errors.append(f"A4 bom_scan 缺词表出处: {r['queue_id']}")
    errors += validate_gate_ledger(gate_rows, ids)

    # A5 内存自测：MOCK 正例必须过、反例必须被拦（不写入真实台账）
    any_qid = ids[0] if ids else "DQ-NONE"
    mock_ok = [{
        "gate_id": "GL-MOCK-OK", "queue_id": any_qid, "对象": "MOCK",
        "命中上下文(段落/词)": "MOCK", "段落类型预判": "MOCK",
        "闸裁决": "生产中", "裁决人": "终验(MOCK)", "裁决时间戳": "2026-07-24T00:00:00Z",
        "理由": "MOCK 正例", "剔除登记号(若剔除)": "",
    }]
    mock_bad = [
        # 旧裁决词（六类之外）必须被拦
        {**mock_ok[0], "gate_id": "GL-MOCK-BAD1", "闸裁决": "确认"},
        # 四件套半填（缺理由）必须被拦
        {**mock_ok[0], "gate_id": "GL-MOCK-BAD2", "理由": ""},
        # 时间戳非 ISO 必须被拦
        {**mock_ok[0], "gate_id": "GL-MOCK-BAD3", "裁决时间戳": "昨天"},
        # queue_id 不存在必须被拦
        {**mock_ok[0], "gate_id": "GL-MOCK-BAD4", "queue_id": "DQ-NOPE-000"},
    ]
    if validate_gate_ledger(mock_ok, ids):
        errors.append("A5 自检失败: MOCK 正例未通过校验")
    for bad in mock_bad:
        if not validate_gate_ledger([bad], ids):
            errors.append(f"A5 自检失败: MOCK 反例 {bad['gate_id']} 未被拦截")
    return errors


def coverage_mock_row():
    """D 项候选集覆盖率演示行（MOCK；公式口径见 v1.7a 确认审最小条款2）。"""
    return {
        "部件词": "MOCK-示例部件",
        "词表出处(含版本)": "MOCK-词表-v0（占位）",
        "语料快照日": "MOCK",
        "C_layer_过闸生产候选数": "MOCK：冻结语料+词表下 S0a 命中且闸裁决=生产中的对象数",
        "G_layer_已入图层主体数": "MOCK：已取得合格证据并进入对应图层的主体数",
        "交集_G∩C": "MOCK",
        "候选集覆盖率": "MOCK=|G∩C|/|C|（禁称总体查全）",
        "已裁决数": "MOCK",
        "待裁决数": "MOCK：待裁决不得从分母消失",
        "待裁决老化(天)": "MOCK",
        "候选处理率": "MOCK=已裁决/(已裁决+待裁决)",
        "口径备注": ("MOCK 演示行：分母冻结三硬条件=词表版本锁定/闸裁决完成/集合快照落盘；"
                     "拟生产是否计入 C_layer 由终验定口径，本脚本不预断；MOCK 行不得引用"),
    }


def main():
    queue = []
    for op in OPERATOR_REGISTRY:
        queue += op.scan()
    mock_cnt = sum(1 for op in OPERATOR_REGISTRY if op.is_mock)

    gate_rows = []  # 闸裁决归终验，本车道只交空骨架（schema 已落地）
    errors = self_test(queue, gate_rows)

    write_csv(OUT_QUEUE, QUEUE_HEADER, queue)
    write_csv(OUT_GATE, GATE_HEADER, gate_rows)
    write_csv(OUT_COVERAGE, COVERAGE_HEADER, [coverage_mock_row()])

    by_op = {}
    for r in queue:
        by_op[r["发现算子"]] = by_op.get(r["发现算子"], 0) + 1
    print("== discovery_queue 原型自检（D2 硬化版，原型-未准入） ==")
    print(f"队列总量: {len(queue)} 行；按算子: {by_op}（含 {mock_cnt} 个 MOCK 算子）")
    print(f"状态分布: 全部 待闸（闸裁决归终验，本车道不代判）")
    print(f"闸台账: 空骨架（schema=六类裁决+四件套；A5 含正反例内存自测）")
    if errors:
        print("纪律断言失败:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("纪律断言 A1-A6: 通过")
    print(f"产出: {OUT_QUEUE.name} / {OUT_GATE.name} / {OUT_COVERAGE.name}（原型-未准入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
