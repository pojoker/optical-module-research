"""Step 4 后端三刀止血、旧锚清零、海内外原件抓核与封版门禁测试（2026-11-22）。

覆盖六大实时程序化核验维度（全部基于落盘源文件实时重算，不依赖静态口头结论）：
① content_ledger.csv 全表 633 行四档诚实分级、578 条 verified_local 全文连续 + #Lx..y(\\n计行)闭环及 README/report 对齐；
② sync_daily_queue.py 消除未知条目静默归噪音(默认 unclassified)、9 项 10–11 月重点财报/并购挽救入列与 32/33 海外快照 + 6 份巨潮 PDF SHA-256 核验；
③ edge_negative_cuts.csv 43 条真否定按简称归一零碰撞、25 条合并边 replacement_edge_ids 全闭环、6 条非供货边隔离；
④ points.csv 272/272 行 100% 有效 http(s):// 或真实 corpus/ 路径锚(0 裸文字/0 Markdown 包装)、P074 检索日期保留、P277 天准科技闭环；
⑤ triage.csv 凯盛/中润驳回、参与识别 94 家确认 / 13 家待确认、外部只读源 463 项、refs 8 文件与 solution_links 冻结；
⑥ scan.py 新增纯函数硬门正反例单测。
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402
from calls.validator import FROZEN_SOLUTION_LINKS  # noqa: E402
from corpus.daily_review import sync_daily_queue  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_nospace(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


class Step4ContentLedgerTiersAndLineClosureTest(unittest.TestCase):
    def test_content_ledger_633_rows_four_tiers_nl_slices_and_doc_alignment(self) -> None:
        csv_path = ROOT / "corpus/content_ledger/content_ledger.csv"
        raw_bytes = csv_path.read_bytes()
        self.assertTrue(raw_bytes.startswith(b"\xef\xbb\xbf"), "content_ledger.csv 须保留 UTF-8 BOM")
        raw_text = raw_bytes.decode("utf-8-sig")
        self.assertNotIn("\r", raw_text)
        phys_lines = len(raw_text.rstrip("\n").split("\n"))
        rows = load_csv("corpus/content_ledger/content_ledger.csv")
        self.assertEqual(len(rows), 633)
        self.assertEqual(phys_lines, 634)
        self.assertEqual(len(rows[0]), 16)

        status_counts = Counter(r["quote_verification_status"] for r in rows)
        self.assertEqual(
            dict(status_counts),
            {
                "verified_local": 578,
                "table_normalized": 37,
                "segmented_verified": 15,
                "inherited_v1_verified": 3,
            },
        )

        # 全表逐行实时核验源文件与 \n 行区间
        src_cache: dict[str, tuple[list[str], str]] = {}
        by_cid = {r["cid"]: r for r in rows}
        self.assertTrue(by_cid["CLG0632"]["local_source_path"].endswith("#L642..648"))
        self.assertTrue(by_cid["CLG0633"]["local_source_path"].endswith("#L630..631"))

        hash_l_rows = 0
        for r in rows:
            cid = r["cid"]
            st = r["quote_verification_status"]
            vq = r["verbatim_quote"]
            lsp = r["local_source_path"]
            parts = lsp.split("#", 1)
            rel = parts[0]
            frag = parts[1] if len(parts) > 1 else ""
            fp = ROOT / rel
            self.assertTrue(fp.is_file(), f"{cid} 缺失源文件 {rel}")
            if rel not in src_cache:
                txt = fp.read_text(encoding="utf-8", errors="ignore")
                src_cache[rel] = (txt.split("\n"), norm_nospace(txt))
            nl_lines, norm_full = src_cache[rel]

            if st == "verified_local":
                nq = norm_nospace(vq)
                self.assertIn(nq, norm_full, f"{cid} verified_local 未在全文连续命中")
                if frag:
                    hash_l_rows += 1
                    m = re.fullmatch(r"L(\d+)\.\.(\d+)", frag)
                    self.assertIsNotNone(m, f"{cid} 非法行锚格式 #{frag}")
                    s_ln, e_ln = int(m.group(1)), int(m.group(2))
                    self.assertTrue(1 <= s_ln <= e_ln <= len(nl_lines))
                    slice_txt = "\n".join(nl_lines[s_ln - 1 : e_ln])
                    self.assertIn(nq, norm_nospace(slice_txt), f"{cid} 未命中 \\n 行切片 #{frag}")
            elif st == "table_normalized":
                segs = [norm_nospace(s) for s in vq.split(" / ") if norm_nospace(s)]
                self.assertGreaterEqual(len(segs), 2, f"{cid} table_normalized 未含 ' / ' 分隔")
                for seg in segs:
                    self.assertIn(seg, norm_full, f"{cid} 表格片段未命中原文: {seg[:20]}")
            elif st == "segmented_verified":
                segs = [norm_nospace(s) for s in re.split(r"……|…|\.\.\.", vq) if norm_nospace(s)]
                self.assertGreaterEqual(len(segs), 2, f"{cid} segmented_verified 未含省略分隔")
                for seg in segs:
                    self.assertIn(seg, norm_full, f"{cid} 节略片段未命中原文: {seg[:20]}")
            elif st == "inherited_v1_verified":
                nq = norm_nospace(vq)
                self.assertIn(nq[:20], norm_full, f"{cid} 首20字锚未命中")
                self.assertIn(nq[-20:], norm_full, f"{cid} 尾20字锚未命中")

        self.assertEqual(hash_l_rows, 2)

        # 核验 quote_verification_report.json 与 README.md 与 CSV 实时统计完全一致
        report = json.loads(
            (ROOT / "corpus/content_ledger/quote_verification_report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["total_rows"], len(rows))
        self.assertEqual(report["physical_csv_lines"], phys_lines)
        self.assertEqual(report["unique_companies"], len({r["company"] for r in rows}))
        self.assertEqual(report["verification_status_counts"], dict(status_counts))
        self.assertEqual(report["batch_counts"], dict(Counter(r["batch"] for r in rows)))
        self.assertEqual(report["fact_type_counts"], dict(Counter(r["fact_type"] for r in rows)))
        self.assertEqual(report["stance_counts"], dict(Counter(r["stance"] for r in rows)))
        self.assertEqual(report["tense_counts"], dict(Counter(r["tense"] for r in rows)))

        readme = (ROOT / "corpus/content_ledger/README.md").read_text(encoding="utf-8")
        for must_str in ("633 条", "26 家", "578 条", "37 条", "15 条", "3 条", "#L630..631", "研序"):
            self.assertIn(must_str, readme)


class Step4DailyQueueUnclassifiedAndWebArchiveTest(unittest.TestCase):
    def test_sync_daily_queue_no_silent_noise_and_rescued_oct_nov_enrolled(self) -> None:
        # 未知普通新闻严禁静默落入 routine_pr_without_state_transition，必须返回 unclassified
        unknown_sample = {
            "publisher_entity_id": "COHR",
            "title": "Coherent Hosts Regional Photonics Customer Workshop in Munich",
            "canonical_url": "https://www.coherent.com/news/munich-workshop-2026",
        }
        self.assertEqual(sync_daily_queue._classify_overseas_noise(unknown_sample), "unclassified")
        self.assertIs(sync_daily_queue.TRIGGERED_OVERSEAS_DC_IDS, sync_daily_queue.SEEDED_OVERSEAS_DC_IDS)
        self.assertEqual(len(sync_daily_queue.SEEDED_OVERSEAS_DC_IDS), 25)

        stats = json.loads((ROOT / "corpus/daily_review/triage_stats.json").read_text(encoding="utf-8"))
        split_all = stats["overseas_staging"]["seeded_plus_positive_rules_split"]
        self.assertNotIn("routine_pr_without_state_transition", split_all["noise_breakdown"])
        self.assertEqual(
            set(split_all["noise_breakdown"]).issubset(sync_daily_queue.HIGH_CONFIDENCE_NOISE_CLASSES),
            True,
        )
        self.assertGreater(split_all["unclassified_count"], 0)
        self.assertEqual(
            split_all["seeded_triggered_count"]
            + split_all["positive_rule_triggered_count"]
            + split_all["high_confidence_noise_count"]
            + split_all["unclassified_count"],
            split_all["total_unique_disclosures"],
        )

        # 9 项 10-11 月挽救披露全部命中正向规则并写入 review_queue.csv
        focal_9 = (
            "DC_A6ADDA0BAFA7",  # MTSI FY26Q4
            "DC_58448CDF4801",  # TSEM Q3
            "DC_DB6E7B2D27BB",  # GFS Q3
            "DC_25B37F48DF71",  # VECO Q3
            "DC_6B392C92DA0A",  # VECO x ACLS
            "DC_86F8DBF8F95E",  # SOI FY27H1
            "DC_C85C91649A7A",  # ANET Q3
            "DC_89DB234EEA46",  # CRDO x ORCL
            "DC_35C4F1F433DF",  # KEYS FY26Q4
        )
        pos_ids = set(stats["overseas_staging"]["positive_rule_triggered_dc_ids"])
        q_rows = load_csv("corpus/daily_review/review_queue.csv")
        q_blob = "\n".join(r["candidate_or_qa_ref"] for r in q_rows)
        for did in focal_9:
            self.assertIn(did, pos_ids)
            self.assertIn(did, q_blob)

        # KEYS FY26Q4 未入 calls，严禁虚挂 kb_target_ref
        keys_row = next(r for r in q_rows if "DC_35C4F1F433DF" in r["candidate_or_qa_ref"])
        self.assertIn(keys_row["status"], ("watch_deferred", "pending_primary_text"))
        self.assertEqual(keys_row["kb_target_ref"], "")

    def test_overseas_32_of_33_web_archives_and_domestic_6_pdfs_sha256_verified(self) -> None:
        manifest = json.loads((ROOT / "corpus/web/step4_20261122/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["total_targets"], 33)
        self.assertEqual(manifest["archived_http_200_count"], 32)
        self.assertEqual(manifest["blocked_or_js_shell_count"], 1)

        ok_items = [x for x in manifest["items"] if x["archive_status"] == "archived_http_200"]
        blocked_items = [x for x in manifest["items"] if x["archive_status"] != "archived_http_200"]
        self.assertEqual(len(ok_items), 32)
        self.assertEqual(len(blocked_items), 1)
        self.assertEqual(blocked_items[0]["item_id"], "DRQ0037")

        for item in ok_items:
            with self.subTest(item_id=item["item_id"]):
                html_p = ROOT / item["html_path"]
                txt_p = ROOT / item["txt_path"]
                self.assertTrue(html_p.is_file())
                self.assertTrue(txt_p.is_file())
                self.assertEqual(sha256_file(html_p), item["html_sha256"])
                self.assertEqual(sha256_file(txt_p), item["txt_sha256"])

        # Lumentum FY27Q1 原文逐字核实 >$5B NPO/CPO win
        lite_txt = (ROOT / "corpus/web/step4_20261122/lite_20261102_fy27q1_results.txt").read_text(encoding="utf-8")
        self.assertIn(
            "During the quarter, we secured our second major NPO/CPO win, backed by purchase commitments exceeding $5 billion.",
            lite_txt,
        )

        # calls/sources.csv 最新财报日期推进至 2026-11-18
        sources = load_csv("calls/sources.csv")
        self.assertEqual(len(sources), 180)
        self.assertEqual(max(r["published_date"] for r in sources if r["published_date"]), "2026-11-18")

        # 国内新归档 6 份巨潮 PDF 原件 %PDF- 魔数与 SHA-256 核验
        dom_verdicts = json.loads(
            (ROOT / "out/step4-backend-final-closure-20261122/domestic-drq-verdicts.json").read_text(encoding="utf-8")
        )
        archived_pdfs = dom_verdicts["newly_archived_cninfo_ir_files"]
        self.assertEqual(len(archived_pdfs), 6)
        for item in archived_pdfs:
            pdf_p = ROOT / item["local_pdf"]
            txt_p = ROOT / item["local_txt"]
            self.assertTrue(pdf_p.read_bytes().startswith(b"%PDF-"))
            self.assertEqual(sha256_file(pdf_p), item["pdf_sha256"])
            self.assertEqual(sha256_file(txt_p), item["txt_sha256"])


class Step4NegativeCutsAndPointsAnchorClosureTest(unittest.TestCase):
    def test_negative_cuts_43_true_negatives_norm_zero_collision_and_25_consolidated_closed(self) -> None:
        cuts = load_csv("corpus/relationships/edge_negative_cuts.csv")
        edges = load_csv("edges.csv")
        tl_rows = load_csv("corpus/relationships/relationship_timeline.csv")
        self.assertEqual(len(cuts), 74)
        self.assertEqual(len(edges), 236)
        self.assertEqual(len(tl_rows), 458)

        cat_counts = Counter(c["cut_category"] for c in cuts)
        self.assertEqual(
            dict(cat_counts),
            {
                "non_optical_related_or_bad_debt": 40,
                "non_optical_counterparty": 3,
                "consolidated_into_group_edge": 25,
                "non_supply_relation": 6,
            },
        )

        eids = {e["edge_id"] for e in edges}
        active_norm: set[tuple[str, str]] = set()
        for e in edges:
            ns = scan._norm_co_name(e["供方"])
            nd = scan._norm_co_name(e["需方"])
            if ns and nd:
                active_norm.add((ns, nd))
                active_norm.add((nd, ns))

        true_negatives = [
            c for c in cuts if c["cut_category"] in ("non_optical_related_or_bad_debt", "non_optical_counterparty")
        ]
        self.assertEqual(len(true_negatives), 43)
        for c in true_negatives:
            for a, b in (
                (c["company"], c["counterparty"]),
                (c["company"], c["counterparty_normalized"]),
                (c["implied_supplier"], c["implied_customer"]),
            ):
                na, nb = scan._norm_co_name(a), scan._norm_co_name(b)
                if na and nb:
                    self.assertNotIn((na, nb), active_norm, f"真否定归一化碰撞 {c['cut_id']}: {(na, nb)}")

        consolidated = [c for c in cuts if c["cut_category"] == "consolidated_into_group_edge"]
        self.assertEqual(len(consolidated), 25)
        for c in consolidated:
            reps = [x.strip() for x in re.split(r"[;,，/\s|]+", c["replacement_edge_ids"]) if x.strip()]
            self.assertTrue(reps, f"{c['cut_id']} replacement_edge_ids 为空")
            for reid in reps:
                self.assertIn(reid, eids)

        del scan.ERR[:]
        scan._check_relationship_tables(tl_rows, eids, cut_rows=cuts, active_edges=edges)
        errs = list(scan.ERR)
        del scan.ERR[:]
        self.assertEqual(errs, [])

    def test_points_272_rows_zero_bare_anchors_p074_preserved_and_p277_tianzhun(self) -> None:
        pts = load_csv("points.csv")
        self.assertEqual(len(pts), 272)
        by_id = {p["point_id"]: p for p in pts}

        # P074 检索日期严格保留 2026-11-21
        self.assertEqual(by_id["P074"]["检索日期"], "2026-11-21")

        # P277 天准科技 2026 半年报 p.14 CPO 在线 AOI 小批量交付逐字核验
        p277 = by_id["P277"]
        self.assertEqual(
            (p277["公司"], p277["cell_id"], p277["状态"], p277["上市标签"]),
            ("天准科技", "EQ6", "生产中", "A股"),
        )
        tz_txt = (ROOT / "corpus/ir/688003/688003_2026-08-20_2026年半年度报告.pdf.txt").read_text(
            encoding="utf-8", errors="ignore"
        )
        self.assertIn(norm_nospace(p277["命中引语"].strip('"')), norm_nospace(tz_txt))

        # 272/272 行 100% 以合法 http(s):// 或真实 corpus/ 路径开头，0 裸文字、0 Markdown [text](url) 包装
        nl_cache: dict[str, int] = {}
        for p in pts:
            pid = p["point_id"]
            anchor = p["锚点URL"].strip()
            self.assertTrue(anchor, f"{pid} 锚点URL为空")
            self.assertFalse(anchor.startswith("["), f"{pid} 仍含 Markdown 链接包装: {anchor[:40]}")
            self.assertTrue(
                anchor.startswith(("http://", "https://", "corpus/")),
                f"{pid} 仍为无直链/无本地路径裸文字锚: {anchor[:60]}",
            )
            for m in scan._CORPUS_PATH_RE.finditer(anchor):
                raw_ref = m.group(0).rstrip('。."\'”’')
                parts = raw_ref.split("#", 1)
                rel = parts[0]
                fp = ROOT / rel
                self.assertTrue(fp.exists(), f"{pid} 本地路径不存在: {rel}")
                if len(parts) > 1:
                    lm = re.fullmatch(r"L(\d+)\.\.(\d+)", parts[1])
                    if lm:
                        if rel not in nl_cache:
                            nl_cache[rel] = len(fp.read_text(encoding="utf-8", errors="ignore").split("\n"))
                        s_ln, e_ln = int(lm.group(1)), int(lm.group(2))
                        self.assertTrue(1 <= s_ln <= e_ln <= nl_cache[rel], f"{pid} 行区间越界: {raw_ref}")


class Step4TriageParticipationAndGuardrailsTest(unittest.TestCase):
    def test_triage_tail_adjudicated_participation_94_13_and_external_guardrails(self) -> None:
        triage = {r["hit_id"]: r for r in load_csv("triage.csv")}
        self.assertEqual(triage["凯盛科技客户京瓷+M3+互查矩阵"]["处置"], "驳回-非本格")
        self.assertEqual(triage["中润光学+D6+2025年报"]["处置"], "驳回-非本格")
        self.assertEqual(
            triage["天准科技+EQ6+688003__em_天准科技_em__2025_2025年年度报告.pdf"]["处置"],
            "已入点",
        )
        self.assertEqual(triage["FIT+ANY+FIT_2025_Annual_Report.pdf"]["处置"], "待判")
        self.assertIn("2026-11-22", triage["FIT+ANY+FIT_2025_Annual_Report.pdf"]["理由"])

        part_rows = load_csv("out/参与识别.csv")
        self.assertEqual(len(part_rows), 466)
        part_counts = Counter(r["结论"] for r in part_rows)
        self.assertEqual(part_counts["已确认参与"], 94)
        self.assertEqual(part_counts["待确认"], 13)
        self.assertEqual(part_counts["尚未发现已过闸证据"], 359)

        part_by_code = {r["代码"].strip(): r for r in part_rows}
        self.assertEqual(part_by_code["688003"]["结论"], "已确认参与")
        self.assertNotEqual(part_by_code["600552"]["结论"], "待确认")
        self.assertNotEqual(part_by_code["688307"]["结论"], "待确认")

        # 外部只读源、refs 预算、solution_links 与 archive 零污染
        wr_annual = Path("/Users/jowang/Downloads/workflow-rehearsal/corpus/annual")
        self.assertEqual(len(os.listdir(wr_annual)), 463)
        self.assertEqual(len(os.listdir(ROOT / "refs")), 8)
        self.assertEqual(tuple(load_csv("calls/solution_links.csv")), FROZEN_SOLUTION_LINKS)

        arc_git = subprocess.check_output(
            ["git", "status", "--porcelain", "--", "archive/"],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(arc_git.strip(), "")


class ScanStep4PureFunctionsTest(unittest.TestCase):
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

    def test_content_ledger_verified_local_nl_slice_and_fake_table_blocked(self) -> None:
        mock_src = "第一行导语\n第二行前半\f同物理换行含分页符光耦合设备精度达50nm\n第三行获客户验证认可\n第四行尾部"
        base = {
            "cid": "CLG900",
            "fact_type": "设备-工序能力",
            "stance": "neutral",
            "cell_ids": "EQ4",
            "verbatim_quote": "光耦合设备精度达 50nm\n第三行获客户验证认可",
            "local_source_path": "corpus/annual/mock.txt#L2..3",
            "quote_verification_status": "verified_local",
        }
        # 正例：\n 第 2..3 行精确命中（含 \f 不拆行）
        self.assertEqual(
            self.errors(
                scan._check_content_ledger,
                [base],
                {"EQ4"},
                exists=lambda _: True,
                read_text=lambda _: mock_src,
            ),
            [],
        )
        # 反例：若误用 splitlines() 把 \f 当换行标成 #L3..4，必须被拦
        errs_splitlines = self.errors(
            scan._check_content_ledger,
            [dict(base, local_source_path="corpus/annual/mock.txt#L3..4")],
            {"EQ4"},
            exists=lambda _: True,
            read_text=lambda _: mock_src,
        )
        self.assertTrue(any("未命中声明" in e for e in errs_splitlines))

        # 反例：表格斜杠拼接行冒充 verified_local 必须被拦，改标 table_normalized 则通过
        fake_verified = dict(
            base,
            local_source_path="corpus/annual/mock.txt",
            verbatim_quote="第一行导语 / 第四行尾部",
            quote_verification_status="verified_local",
        )
        errs_fake = self.errors(
            scan._check_content_ledger,
            [fake_verified],
            {"EQ4"},
            exists=lambda _: True,
            read_text=lambda _: mock_src,
        )
        self.assertTrue(any("未在原文连续命中" in e for e in errs_fake))
        self.assertEqual(
            self.errors(
                scan._check_content_ledger,
                [dict(fake_verified, quote_verification_status="table_normalized")],
                {"EQ4"},
                exists=lambda _: True,
                read_text=lambda _: mock_src,
            ),
            [],
        )

    def test_negative_cuts_cut_category_dispatch_and_norm_co_name_collision(self) -> None:
        tl = [
            {
                "timeline_id": "TL0001",
                "supplier": "源杰科技",
                "customer": "中际旭创",
                "source_channel": "annual_report",
                "value_raw": "1000万元",
                "source_edge_ids": "E184",
                "notes": "正常供货边",
            }
        ]
        active = [{"供方": "源杰科技", "需方": "中际旭创"}, {"供方": "长飞光纤光缆", "需方": "博创科技"}]

        # 正例：consolidated_into_group_edge + non_supply_relation 合法放行
        ok_cuts = [
            {
                "cut_id": "CUT001",
                "company": "博创科技",
                "counterparty": "长飞光纤光缆有限公司",
                "counterparty_normalized": "长飞光纤光缆有限公司",
                "implied_supplier": "长飞光纤光缆有限公司",
                "implied_customer": "博创科技",
                "cut_category": "consolidated_into_group_edge",
                "replacement_edge_ids": "E163",
                "leaked_in_edges_csv": "false",
            },
            {
                "cut_id": "CUT030",
                "company": "源杰科技",
                "counterparty": "中际旭创股份有限公司",
                "counterparty_normalized": "中际旭创股份有限公司",
                "implied_supplier": "",
                "implied_customer": "",
                "cut_category": "non_supply_relation",
                "replacement_edge_ids": "",
                "leaked_in_edges_csv": "false",
            },
        ]
        self.assertEqual(
            self.errors(scan._check_relationship_tables, tl, {"E184", "E163"}, cut_rows=ok_cuts, active_edges=active),
            [],
        )

        # 反例：consolidated 悬空边 E999 被拦
        bad_cons = [dict(ok_cuts[0], replacement_edge_ids="E999")]
        errs_cons = self.errors(
            scan._check_relationship_tables, tl, {"E184", "E163"}, cut_rows=bad_cons, active_edges=active
        )
        self.assertTrue(any("E999" in e for e in errs_cons))

        # 反例：真否定带“股份有限公司”后缀经 _norm_co_name 归一后撞上活跃边（简称“中际旭创”）必须被拦
        bad_norm_leak = [
            {
                "cut_id": "CUT999",
                "company": "源杰科技（本部）",
                "counterparty": "中际旭创股份有限公司",
                "counterparty_normalized": "中际旭创股份有限公司",
                "implied_supplier": "源杰科技（本部）",
                "implied_customer": "中际旭创股份有限公司",
                "cut_category": "non_optical_counterparty",
                "replacement_edge_ids": "",
                "leaked_in_edges_csv": "false",
            }
        ]
        errs_leak = self.errors(
            scan._check_relationship_tables, tl, {"E184", "E163"}, cut_rows=bad_norm_leak, active_edges=active
        )
        self.assertTrue(any("泄漏至活跃 edges.csv" in e for e in errs_leak))


if __name__ == "__main__":
    unittest.main()
