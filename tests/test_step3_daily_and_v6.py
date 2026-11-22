"""Step 3 高价值 Daily 并库、95/5 持久待审池、v6 宇宙对称扩容与机器门回归测试（2026-11-21）。

包含六大维度实时程序化核验（直接读取主表与本地源文本核算，不依赖静态摘要 JSON）：
a) points.csv 一手已核增量与科瑞技术 P275/P276 能力点及匿名客户边界；
b) content_ledger.csv 全部 step3_daily_2026q4（含 CLG0632–CLG0633）100.0% 本地去空白逐字命中；
c) relationship_timeline.csv TL9001–TL9005 与 74 条负向剔除零碰撞；
d) calls/*.csv（CM002/CM007/EV035/EV036）与 review_queue.csv 未核线索严格隔离（pending_primary_text / pending_filing_anchor）；
e) v6 宇宙 466 分母、参与识别 93 家已确认、observation_list、外部只读源 463 项守恒、refs 8 文件预算与 sync_daily_queue --check；
f) scan._check_daily_review_queue 与扩展 _CORPUS_PATH_RE 纯内存正反例单测。
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402
from calls.validator import FROZEN_SOLUTION_LINKS  # noqa: E402


def load_csv(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_nospace(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


class Step3PointsAndDomesticUpdatesTest(unittest.TestCase):
    def test_points_step3_updates_kerui_p275_p276_and_strict_boundaries(self) -> None:
        pts = load_csv("points.csv")
        by_id = {r["point_id"]: r for r in pts}

        # P061 联讯仪器: 科创板 688808 转正为 A股
        p061 = by_id["P061"]
        self.assertEqual(p061["公司"], "联讯仪器")
        self.assertEqual(p061["上市标签"], "A股")
        self.assertIn("688808", p061["判定等级"])
        self.assertIn("1225511954.PDF#page=17", p061["判定等级"])

        # P202 云南鑫耀 + 母公司云南锗业 002428 2025 年报 10.01 万片逐字核验
        p202 = by_id["P202"]
        self.assertEqual(p202["公司"], "云南鑫耀半导体材料有限公司")
        self.assertIn("云南锗业", p202["判定等级"])
        self.assertIn("10.01万片", p202["判定等级"])
        yng_txt = (
            ROOT / "corpus/annual/002428/002428__em_云南锗业_em__2025_2025年年度报告.pdf.txt"
        ).read_text(encoding="utf-8", errors="ignore")
        self.assertIn(
            norm_nospace("生产化合物半导体材料：砷化镓晶片7.63万片（1-6寸合计），磷化铟晶片10.01万片（2-4寸合计）。"),
            norm_nospace(yng_txt),
        )

        # P275 & P276 科瑞技术 (002957): EQ3 共晶贴片 + EQ4 50nm 光耦合 + 严格匿名边界
        kerui_txt = (
            ROOT / "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt"
        ).read_text(encoding="utf-8", errors="ignore")
        kerui_norm = norm_nospace(kerui_txt)
        for name in ("Lumentum", "lumentum", "Coherent", "coherent"):
            self.assertNotIn(name, kerui_txt)

        p275 = by_id["P275"]
        self.assertEqual(
            (p275["公司"], p275["cell_id"], p275["状态"], p275["上市标签"]),
            ("科瑞技术", "EQ3", "生产中", "A股"),
        )
        self.assertEqual(
            p275["锚点URL"],
            "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        )
        self.assertIn(
            "光模块芯片共晶贴片设备：适配光模块芯片贴装需求，实现高精度、高稳定性贴装，保障光模块性能",
            p275["命中引语"],
        )
        self.assertIn(norm_nospace(p275["命中引语"].strip('"')), kerui_norm)
        self.assertIn("匿名", p275["判定等级"])

        p276 = by_id["P276"]
        self.assertEqual(
            (p276["公司"], p276["cell_id"], p276["状态"], p276["上市标签"]),
            ("科瑞技术", "EQ4", "生产中", "A股"),
        )
        self.assertEqual(
            p276["锚点URL"],
            "https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
        )
        self.assertIn(
            "光耦合设备精度达 50nm，达到行业领先水平，技术产业化成果突出，在光模块领域提供多个核心工序的工艺设备并获得海外头部客户验证和认可",
            p276["命中引语"],
        )
        self.assertIn(norm_nospace(p276["命中引语"].strip('"')), kerui_norm)
        self.assertIn("Lumentum", p276["判定等级"])
        self.assertIn("严禁", p276["判定等级"])

        # P059 / P172 / P173 罗博特科: INS2/INS3 批量交付 vs INS4 NPI & 11/16 英伟达客户确认 + NDA 界限 + 瑞士 OCS
        for pid in ("P059", "P172", "P173"):
            with self.subTest(pid=pid):
                note = by_id[pid]["判定等级"]
                self.assertIn("INS2", note)
                self.assertIn("INS3", note)
                self.assertIn("INS4", note)
                self.assertIn("英伟达系ficonTEC的客户之一", note)
                self.assertIn("商业秘密", note)
                self.assertIn("OCS", note)

        # P271 天孚通信: CPO 稳定量产交付 vs NPO 2027 逐步上量严格分账
        p271_note = by_id["P271"]["判定等级"]
        self.assertIn("CPO", p271_note)
        self.assertIn("稳定量产交付", p271_note)
        self.assertIn("NPO", p271_note)
        self.assertIn("2027", p271_note)

        # P074 中际旭创 / P073 新易盛 / P077 剑桥科技
        self.assertIn("2027H2", by_id["P074"]["判定等级"])
        self.assertIn("30亿美元", by_id["P074"]["判定等级"])
        self.assertIn("10月确认收入", by_id["P073"]["判定等级"])
        self.assertIn("1.6T", by_id["P073"]["判定等级"])
        self.assertIn("越南", by_id["P077"]["判定等级"])
        self.assertIn("100万支/月", by_id["P077"]["判定等级"])
        self.assertIn("三个客户", by_id["P077"]["判定等级"])

        # P117 / P169 炬光科技: >36通道 V型槽转批量 vs MPLA 技术许可协议区隔硬件销量
        for pid in ("P117", "P169"):
            with self.subTest(pid=pid):
                self.assertIn("1225658451.PDF#page=86", by_id[pid]["锚点URL"])
                self.assertIn("大于36通道", by_id[pid]["判定等级"])
                self.assertIn("MPLA", by_id[pid]["判定等级"])
                self.assertIn("技术许可", by_id[pid]["判定等级"])

        # P206 博众精工: 中南鸿思 60% 耦合 vs 苏州博众半导体共晶贴片 & 订单不等同收入警示
        p206_note = by_id["P206"]["判定等级"]
        self.assertIn("中南鸿思60%", p206_note)
        self.assertIn("苏州博众半导体", p206_note)
        self.assertIn("订单并不直接等同于收入", p206_note)

        # P209 华工科技: 原引语与原锚保留 + 11/05 光互联 65.39 亿及分部口径边界
        p209 = by_id["P209"]
        self.assertIn("65.39亿元", p209["判定等级"])
        self.assertIn("5.66亿元", p209["判定等级"])
        self.assertIn("光电器件系列产品", p209["判定等级"])


class Step3ContentLedgerVerbatimTest(unittest.TestCase):
    def test_step3_daily_2026q4_rows_100pct_local_verbatim_match(self) -> None:
        rows = load_csv("corpus/content_ledger/content_ledger.csv")
        step3_rows = [r for r in rows if r["batch"] == "step3_daily_2026q4"]
        self.assertEqual(len(step3_rows), 36)

        cids = [r["cid"] for r in step3_rows]
        self.assertIn("CLG0632", cids)
        self.assertIn("CLG0633", cids)

        by_cid = {r["cid"]: r for r in step3_rows}
        self.assertEqual((by_cid["CLG0632"]["company"], by_cid["CLG0632"]["cell_ids"]), ("科瑞技术", "EQ3"))
        self.assertEqual((by_cid["CLG0633"]["company"], by_cid["CLG0633"]["cell_ids"]), ("科瑞技术", "EQ4"))
        self.assertEqual(
            by_cid["CLG0632"]["local_source_path"],
            "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt#L642..648",
        )
        self.assertEqual(
            by_cid["CLG0633"]["local_source_path"],
            "corpus/annual/002957/002957/002957__em_科瑞技术_em__2025_2025年年度报告.pdf.txt#L630..631",
        )

        tree_doc = yaml.safe_load((ROOT / "tree.yaml").read_text(encoding="utf-8"))
        leaf_cells = scan._tree_leaf_cells(tree_doc)
        del scan.ERR[:]
        scan._check_content_ledger(rows, leaf_cells)
        errs = list(scan.ERR)
        del scan.ERR[:]
        self.assertEqual(errs, [])

        source_cache: dict[str, str] = {}
        misses: list[str] = []
        for r in step3_rows:
            for col, val in r.items():
                self.assertNotIn("\n", val, f"{r['cid']}.{col} 含 \\n")
                self.assertNotIn("\r", val, f"{r['cid']}.{col} 含 \\r")
            for bad in ("已覆盖", "已完成", "已回答"):
                self.assertNotIn(bad, r["atomic_fact"])
                self.assertNotIn(bad, r["verbatim_quote"])
            rel_path = r["local_source_path"].split("#")[0]
            full_path = ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"{r['cid']} 缺失本地源文件: {rel_path}")
            if rel_path not in source_cache:
                source_cache[rel_path] = norm_nospace(full_path.read_text(encoding="utf-8", errors="ignore"))
            if norm_nospace(r["verbatim_quote"]) not in source_cache[rel_path]:
                misses.append(r["cid"])

        self.assertEqual(misses, [], f"step3_daily_2026q4 存在未逐字命中本地源文件的条目: {misses}")


class Step3TimelineCallsAndQueueBoundaryTest(unittest.TestCase):
    def test_relationship_timeline_tl9001_tl9005_and_zero_negative_cut_collision(self) -> None:
        tl_rows = load_csv("corpus/relationships/relationship_timeline.csv")
        by_tid = {r["timeline_id"]: r for r in tl_rows}
        for tid in ("TL9001", "TL9002", "TL9003", "TL9004", "TL9005"):
            self.assertIn(tid, by_tid)

        self.assertEqual(
            (
                by_tid["TL9001"]["relation_id"],
                by_tid["TL9001"]["supplier"],
                by_tid["TL9001"]["customer"],
                by_tid["TL9001"]["event_date"],
            ),
            ("R057", "罗博特科/ficonTEC", "NVIDIA", "2026-11-16"),
        )
        self.assertEqual(
            (
                by_tid["TL9002"]["relation_id"],
                by_tid["TL9002"]["supplier"],
                by_tid["TL9002"]["customer"],
                by_tid["TL9002"]["event_date"],
            ),
            ("R205", "Tower Semiconductor", "中际旭创", "2026-11-03"),
        )

        cuts = load_csv("corpus/relationships/edge_negative_cuts.csv")
        self.assertEqual(len(cuts), 74)
        neg_pairs: set[tuple[str, str]] = set()
        for c in cuts:
            comp = c["company"].strip()
            cp = c["counterparty"].strip()
            cpn = (c["counterparty_normalized"] or cp).strip()
            isup = c["implied_supplier"].strip()
            icus = c["implied_customer"].strip()
            for a, b in ((comp, cp), (comp, cpn), (isup, icus)):
                if a and b:
                    neg_pairs.add((a, b))
                    neg_pairs.add((b, a))

        for tid in ("TL9001", "TL9002", "TL9003", "TL9004", "TL9005"):
            pair = (by_tid[tid]["supplier"].strip(), by_tid[tid]["customer"].strip())
            self.assertNotIn(pair, neg_pairs, f"{tid} 与 74 条负剔除碰撞: {pair}")

    def test_calls_adjudications_events_and_unverified_staging_strictly_in_review_queue(self) -> None:
        commitments = {r["commitment_id"]: r for r in load_csv("calls/commitments.csv")}
        self.assertEqual(commitments["CM002"]["status"], "fulfilled")
        self.assertEqual(commitments["CM002"]["evidence_claim_id"], "CL075")
        self.assertEqual(commitments["CM007"]["status"], "partially_fulfilled")
        self.assertEqual(commitments["CM007"]["evidence_claim_id"], "CL076")

        events = {r["event_id"]: r for r in load_csv("calls/events.csv")}
        self.assertEqual((events["EV035"]["primary_subject_id"], events["EV035"]["lifecycle_stage"]), ("CSCO", "first_shipment"))
        self.assertIn("G300", events["EV035"]["summary"])
        self.assertEqual(
            (events["EV036"]["primary_subject_id"], events["EV036"]["counterparty_ids"], events["EV036"]["lifecycle_stage"]),
            ("TSEM", "WATCH_INNOLIGHT", "announced"),
        )

        # calls/solution_links.csv 字节级冻结
        sl_rows = tuple(load_csv("calls/solution_links.csv"))
        self.assertEqual(sl_rows, FROZEN_SOLUTION_LINKS)

        # 未取得静态一手正文的海外空壳线索(如 LWLG DC_4B0F75924A65)严禁混入 reviewed calls/claims.csv
        reviewed_claims = [r for r in load_csv("calls/claims.csv") if r["review_status"] == "reviewed"]
        claims_blob = json.dumps(reviewed_claims, ensure_ascii=False)
        for forbidden_unverified in (
            "Lightwave Logic",
            "DC_4B0F75924A65",
            "G-cb80feb5485f402e",
        ):
            self.assertNotIn(forbidden_unverified, claims_blob)

        # 核实 Step 4 / Step 5 全文核验后的状态跃迁与真实受限留置边界
        q_rows = load_csv("corpus/daily_review/review_queue.csv")
        q_by_id = {r["queue_id"]: r for r in q_rows}

        for verified_drq in ("DRQ0015", "DRQ0016", "DRQ0017", "DRQ0046", "DRQ0047", "DRQ0051"):
            self.assertEqual(q_by_id[verified_drq]["status"], "ingested_to_kb")
            self.assertTrue(q_by_id[verified_drq]["kb_target_ref"].strip())
        self.assertEqual(
            q_by_id["DRQ0046"]["kb_target_ref"],
            "knowledge:KN011;knowledge:KN012;knowledge:KN013;knowledge:KN014",
        )
        self.assertIn("26,999万元", q_by_id["DRQ0047"]["title_or_claim"])
        self.assertEqual(q_by_id["DRQ0051"]["kb_target_ref"], "points:P277")

        for deferred_drq in ("DRQ0032", "DRQ0054"):
            self.assertEqual(q_by_id[deferred_drq]["status"], "watch_deferred")

        pending_text_refs = "\n".join(
            f"{r['entity_name']} | {r['candidate_or_qa_ref']} | {r['title_or_claim']}"
            for r in q_rows
            if r["status"] == "pending_primary_text"
        )
        for must_pending_text in ("DC_4B0F75924A65",):
            self.assertIn(must_pending_text, pending_text_refs)

        pending_anchor_rows = [r for r in q_rows if r["status"] == "pending_filing_anchor"]
        pending_anchor_blob = "\n".join(
            f"{r['queue_id']} | {r['entity_name']} | {r['title_or_claim']} | {r['missing_verification_gate']}"
            for r in pending_anchor_rows
        )
        for must_anchor in ("微见智能", "镭神技术", "科瑞技术", "长光华芯", "利扬芯片"):
            self.assertIn(must_anchor, pending_anchor_blob)

        # DRQ0050 保留专项盯防 Lumentum / Coherent 具名归属，DRQ0055 指向 P275/P276/CLG0632/CLG0633
        drq50 = q_by_id["DRQ0050"]
        self.assertEqual((drq50["entity_name"], drq50["status"]), ("科瑞技术", "pending_filing_anchor"))
        self.assertIn("Lumentum", drq50["missing_verification_gate"])
        self.assertIn("Coherent", drq50["missing_verification_gate"])

        kerui_ingested = [
            r for r in q_rows if r["entity_name"] == "科瑞技术" and r["status"] == "ingested_to_kb"
        ]
        self.assertEqual(len(kerui_ingested), 1)
        self.assertEqual(
            kerui_ingested[0]["kb_target_ref"],
            "points:P275;points:P276;content:CLG0632;content:CLG0633",
        )


class Step3UniverseV6AndExternalGuardrailsTest(unittest.TestCase):
    def test_v6_denominator_participation_93_observation_list_and_readonly_safety(self) -> None:
        frozen = load_csv("corpus/_frozen.csv")
        frozen_codes = {r["代码"].strip() for r in frozen}
        self.assertEqual(len(frozen_codes), 466)
        for code in ("688808", "002428", "002957"):
            self.assertIn(code, frozen_codes)
        for unlisted in ("微见智能", "镭神技术"):
            self.assertNotIn(unlisted, frozen_codes)

        tree_doc = yaml.safe_load((ROOT / "tree.yaml").read_text(encoding="utf-8"))
        self.assertEqual(tree_doc["universe"]["count"], 466)
        obs_names = scan.observation_names()
        self.assertIn("微见智能", obs_names)
        self.assertIn("镭神技术", obs_names)

        # entity_nodes.csv N171 科瑞技术 对齐 P275;P276
        nodes = {r["node_id"]: r for r in load_csv("corpus/salvaged/entity_nodes.csv")}
        self.assertEqual(nodes["N171"]["canonical_name"], "科瑞技术")
        self.assertEqual(nodes["N171"]["point_ids"], "P275;P276")

        # out/参与识别.csv 466 宇宙、总确认 94 家(含 Step4 新增 P277 天准科技)，688808/002428/002957/688003 均为 已确认参与
        part_rows = load_csv("out/参与识别.csv")
        self.assertEqual(len(part_rows), 466)
        part_by_code = {r["代码"].strip(): r for r in part_rows}
        for code, expected_name in (("688808", "联讯仪器"), ("002428", "云南锗业"), ("002957", "科瑞技术"), ("688003", "天准科技")):
            self.assertEqual(part_by_code[code]["公司"], expected_name)
            self.assertEqual(part_by_code[code]["结论"], "已确认参与")
        confirmed = [r for r in part_rows if r["结论"] == "已确认参与"]
        self.assertEqual(len(confirmed), 94)

        # 外部只读源 /Users/jowang/Downloads/workflow-rehearsal/corpus/annual 精确保持 463 项
        wr_annual = Path("/Users/jowang/Downloads/workflow-rehearsal/corpus/annual")
        self.assertEqual(len(os.listdir(wr_annual)), 463)

        # refs/ 严格保持 8 个文件
        self.assertEqual(len(os.listdir(ROOT / "refs")), 8)

        # sync_daily_queue.py --check 退出码 0
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "corpus/daily_review/sync_daily_queue.py"), "--check"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"sync_daily_queue.py --check 失败:\n{proc.stderr}\n{proc.stdout}")


class ScanDailyReviewQueueGateTest(unittest.TestCase):
    def setUp(self) -> None:
        del scan.ERR[:]

    def tearDown(self) -> None:
        del scan.ERR[:]

    def errors(self, fn, *args, **kwargs) -> list[str]:
        del scan.ERR[:]
        fn(*args, **kwargs)
        out = list(scan.ERR)
        del scan.ERR[:]
        return out

    def assertBlocked(self, errs: list[str], needle: str) -> None:
        self.assertTrue(
            any(e.startswith("[⑦]") and needle in e for e in errs),
            f"期望 [⑦] 含 {needle!r}，实际: {errs}",
        )

    def test_corpus_path_re_recognizes_daily_review(self) -> None:
        row = {"point_id": "P999", "锚点URL": "见（corpus/daily_review/review_queue.csv#DRQ0050）"}
        seen: list[str] = []
        errs = self.errors(scan._check_point_row, row, exists=lambda rel: seen.append(rel) or True)
        self.assertEqual(errs, [])
        self.assertEqual(seen, ["corpus/daily_review/review_queue.csv"])
        bad_errs = self.errors(scan._check_point_row, row, exists=lambda rel: False)
        self.assertTrue(any(e.startswith("[⑩]") and "corpus/daily_review/review_queue.csv" in e for e in bad_errs))

    def test_check_daily_review_queue_positive_and_negative_cases(self) -> None:
        pids = {"P275", "P276"}
        eids = {"E012"}
        clg_ids = {"CLG0632", "CLG0633"}
        tl_ids = {"TL9001"}
        call_ids = {"CM002", "EV035"}

        ingested = {
            "queue_id": "DRQ0001",
            "priority": "P0",
            "trigger_type": "T4_universe_blindspot",
            "status": "ingested_to_kb",
            "entity_name": "科瑞技术",
            "kb_target_ref": "points:P275;points:P276;edges:E012;content:CLG0632;timeline:TL9001;calls:CM002",
            "missing_verification_gate": "",
        }
        pending_text = {
            "queue_id": "DRQ0002",
            "priority": "P0",
            "trigger_type": "T2_supply_relationship_or_ma",
            "status": "pending_primary_text",
            "entity_name": "Marvell × Lumentum",
            "kb_target_ref": "",
            "missing_verification_gate": "需下载Marvell官网全文与SEC 8-K原件",
        }
        pending_anchor = {
            "queue_id": "DRQ0003",
            "priority": "P1",
            "trigger_type": "T1_lifecycle_shift",
            "status": "pending_filing_anchor",
            "entity_name": "云南锗业",
            "kb_target_ref": "points:P275",
            "missing_verification_gate": "缺巨潮正式公告PDF",
        }
        deferred = {
            "queue_id": "DRQ0004",
            "priority": "P2",
            "trigger_type": "T3_commitment_verification",
            "status": "watch_deferred",
            "entity_name": "远期观察项",
            "kb_target_ref": "",
            "missing_verification_gate": "",
        }

        # Positive case (5 positional args + call_ids)
        self.assertEqual(
            self.errors(
                scan._check_daily_review_queue,
                [ingested, pending_text, pending_anchor, deferred],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            [],
        )

        # Positive case against live disk review_queue.csv using exact 5-arg signature
        live_q = load_csv("corpus/daily_review/review_queue.csv")
        live_pids = {r["point_id"] for r in load_csv("points.csv")}
        live_eids = {r["edge_id"] for r in load_csv("edges.csv")}
        live_clg_ids = {r["cid"] for r in load_csv("corpus/content_ledger/content_ledger.csv")}
        live_tl_ids = {r["timeline_id"] for r in load_csv("corpus/relationships/relationship_timeline.csv")}
        self.assertEqual(
            self.errors(scan._check_daily_review_queue, live_q, live_pids, live_eids, live_clg_ids, live_tl_ids),
            [],
        )

        # Negative cases
        self.assertBlocked(
            self.errors(scan._check_daily_review_queue, [], pids, eids, clg_ids, tl_ids, call_ids=call_ids),
            "为空或缺失",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(pending_text, missing_verification_gate="含换行\n符")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "内嵌换行符",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(ingested, queue_id="BAD0001")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "queue_id非法",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [ingested, dict(pending_text, queue_id="DRQ0001")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "queue_id重复",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(ingested, priority="P9")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "priority非法",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(ingested, trigger_type="legacy_type")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "trigger_type非法",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(ingested, status="closed")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "status非法",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(pending_anchor, missing_verification_gate="")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "missing_verification_gate",
        )
        self.assertBlocked(
            self.errors(
                scan._check_daily_review_queue,
                [dict(ingested, kb_target_ref="")],
                pids,
                eids,
                clg_ids,
                tl_ids,
                call_ids=call_ids,
            ),
            "kb_target_ref",
        )
        for bad_ref, needle in (
            ("points:P999", "points引用悬空"),
            ("edges:E999", "edges引用悬空"),
            ("content:CLG9999", "content引用悬空"),
            ("timeline:TL9999", "timeline引用悬空"),
            ("calls:EV999", "calls引用悬空"),
            ("frozen:002957", "前缀非法"),
        ):
            with self.subTest(bad_ref=bad_ref):
                self.assertBlocked(
                    self.errors(
                        scan._check_daily_review_queue,
                        [dict(ingested, kb_target_ref=bad_ref)],
                        pids,
                        eids,
                        clg_ids,
                        tl_ids,
                        call_ids=call_ids,
                    ),
                    needle,
                )


if __name__ == "__main__":
    unittest.main()
