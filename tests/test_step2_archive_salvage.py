"""Step 2 归档遗珠打捞、内容台账扩抽、时间线贯通与机器门回归测试（2026-11-21）。

包含两部分：
1. 对真实落盘资产的独立程序化核验（直接计算 SHA-256、重跑逐字引语匹配、重算海关18个月对账、
   重核 truth.json 16/16 与 74 对负向剔除零泄漏，绝不轻信汇总 JSON）。
2. 对 scan.py 新增纯函数（_check_customs_tables / _check_content_ledger /
   _check_relationship_tables 及扩展后的 _CORPUS_PATH_RE）的内存正反例单测。
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
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scan  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(rel_path: str) -> list[dict[str, str]]:
    with (ROOT / rel_path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


class Annual2023AndArchiveSafetyTest(unittest.TestCase):
    def test_annual_2023_has_at_least_34_pdfs_and_demo_30_pdfs_100pct_in_corpus(self) -> None:
        annual_2023_dir = ROOT / "corpus" / "annual-2023"
        self.assertTrue(annual_2023_dir.exists(), "corpus/annual-2023 不存在")

        annual_2023_pdfs = [
            Path(dp) / fn
            for dp, _, fns in os.walk(annual_2023_dir, followlinks=True)
            for fn in fns
            if fn.lower().endswith(".pdf")
        ]
        self.assertGreaterEqual(len(annual_2023_pdfs), 34)
        for p in annual_2023_pdfs:
            self.assertGreater(p.stat().st_size, 0, f"空 PDF: {p}")

        # Build live SHA-256 set across corpus/{annual,annual-2024,annual-2023}
        corpus_hashes: set[str] = set()
        for sub in ("corpus/annual", "corpus/annual-2024", "corpus/annual-2023"):
            base = ROOT / sub
            for dp, _, fns in os.walk(base, followlinks=True):
                for fn in fns:
                    if fn.lower().endswith(".pdf"):
                        corpus_hashes.add(sha256_file(Path(dp) / fn))

        demo_dir = ROOT / "archive" / "demo" / "data"
        demo_pdfs = sorted(
            Path(dp) / fn
            for dp, _, fns in os.walk(demo_dir, followlinks=True)
            for fn in fns
            if fn.lower().endswith(".pdf")
        )
        self.assertEqual(len(demo_pdfs), 30)
        missing = [str(p.relative_to(ROOT)) for p in demo_pdfs if sha256_file(p) not in corpus_hashes]
        self.assertEqual(missing, [], f"demo PDF 未在本地 corpus/ 命中 SHA-256: {missing}")

    def test_v16_sidecars_match_archive_grok_texts_and_archive_git_clean(self) -> None:
        grok_dir = ROOT / "archive" / "flows" / "out" / "_v16_txt_grok"
        grok_txts = sorted(grok_dir.glob("*.txt"))
        self.assertEqual(len(grok_txts), 11)

        v16_sidecars = {p.name: p for p in (ROOT / "corpus" / "legacy-input" / "v16").rglob("*.pdf.txt")}
        for src in grok_txts:
            expected_name = f"{src.stem}.pdf.txt"
            self.assertIn(expected_name, v16_sidecars, f"缺失 v16 旁车: {expected_name}")
            self.assertEqual(sha256_file(src), sha256_file(v16_sidecars[expected_name]))

        out = subprocess.check_output(
            ["git", "status", "--porcelain", "--", "archive/"],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(out.strip(), "", f"archive/ 下受 git 追踪文件发生变动:\n{out}")


class SalvagedTruthAndEntityRegistryTest(unittest.TestCase):
    def test_truth_regression_assertions_16_of_16_live_against_edges_csv(self) -> None:
        truth_raw = json.loads((ROOT / "archive" / "demo" / "truth.json").read_text(encoding="utf-8"))
        salvaged = json.loads(
            (ROOT / "corpus" / "salvaged" / "truth_regression_assertions.json").read_text(encoding="utf-8")
        )
        assertions = salvaged.get("assertions") or []
        self.assertEqual(len(truth_raw["checks"]), 16)
        self.assertEqual(len(assertions), 16)

        edges_by_id = {r["edge_id"]: r for r in load_csv("edges.csv")}
        for item in assertions:
            with self.subTest(tid=item["id"]):
                eid = item["canonical_edge_id"]
                self.assertIn(eid, edges_by_id)
                live_val = edges_by_id[eid][item["canonical_field"]]
                cmp_val = live_val.replace(",", "") if item.get("normalize_commas") else live_val
                self.assertIn(item["expected_substring"], cmp_val)

    def test_entity_nodes_and_entity_registry_yaml(self) -> None:
        nodes = load_csv("corpus/salvaged/entity_nodes.csv")
        self.assertGreaterEqual(len(nodes), 169)
        node_ids = [r["node_id"] for r in nodes]
        self.assertEqual(len(node_ids), len(set(node_ids)))

        blob = "\n".join(json.dumps(r, ensure_ascii=False) for r in nodes)
        for must_have in ("PINEWAVE", "浙江粮油", "顺丰速运", "金信诺", "等离子体所", "索恩格"):
            with self.subTest(subject=must_have):
                self.assertIn(must_have, blob)

        intermediaries = [r for r in nodes if r["is_intermediary_layer"] == "true"]
        self.assertGreaterEqual(len(intermediaries), 7)

        reg = yaml.safe_load((ROOT / "refs" / "entity-registry.yaml").read_text(encoding="utf-8"))
        self.assertIsInstance(reg, dict)
        for key in ("schema_version", "identity_layer", "observation_scope_layer", "node_directory"):
            self.assertIn(key, reg)


class CustomsAndMacroGateTest(unittest.TestCase):
    def test_customs_four_tables_zero_newlines_and_18_month_exact_reconciliation(self) -> None:
        expected_rows = {
            "customs_monthly.csv": 30,
            "customs_partners.csv": 2881,
            "customs_province.csv": 2246,
            "customs_trademode.csv": 731,
        }
        parsed: dict[str, list[dict[str, str]]] = {}
        for fname, exp_cnt in expected_rows.items():
            path = ROOT / "corpus" / "customs" / fname
            raw = path.read_text(encoding="utf-8-sig", newline="")
            norm_raw = raw.replace("\r\n", "\n")
            self.assertNotIn("\r", norm_raw, f"{fname} 含裸 \\r")
            phys_lines = len(norm_raw.rstrip("\n").split("\n"))
            rows = load_csv(f"corpus/customs/{fname}")
            self.assertEqual(len(rows), exp_cnt)
            self.assertEqual(phys_lines, len(rows) + 1, f"{fname} 存在引号内嵌入换行符")
            for r in rows:
                for col, v in r.items():
                    self.assertNotIn("\n", v, f"{fname} 列 {col} 含 \\n")
                    self.assertNotIn("\r", v, f"{fname} 列 {col} 含 \\r")
            parsed[fname] = rows

        months_18 = [f"2025{m:02d}" for m in range(1, 13)] + [f"2026{m:02d}" for m in range(1, 7)]
        monthly_usd = {r["月份"]: int(r["金额"]) for r in parsed["customs_monthly.csv"] if r["月份"] in months_18}
        monthly_kg = {r["月份"]: int(r["出口量kg"]) for r in parsed["customs_monthly.csv"] if r["月份"] in months_18}
        self.assertEqual(len(monthly_usd), 18)

        for sub_name, amt_col in (
            ("customs_partners.csv", "金额"),
            ("customs_province.csv", "金额USD"),
            ("customs_trademode.csv", "金额USD"),
        ):
            usd_sum: dict[str, int] = defaultdict(int)
            kg_sum: dict[str, int] = defaultdict(int)
            for r in parsed[sub_name]:
                usd_sum[r["月份"]] += int(r[amt_col])
                kg_sum[r["月份"]] += int(r["出口量kg"])
            for ym in months_18:
                self.assertEqual(usd_sum[ym], monthly_usd[ym], f"{sub_name} {ym} USD 对账不一致")
                self.assertEqual(kg_sum[ym], monthly_kg[ym], f"{sub_name} {ym} kg 对账不一致")

        # Verify HS 85177950 catalog/linkage/README boundary and MC033-MC035
        self.assertEqual(len(load_csv("corpus/customs/hs85177950_product_catalog.csv")), 25)
        self.assertEqual(len(load_csv("corpus/customs/hs85177950_company_linkage.csv")), 27)
        readme = (ROOT / "corpus" / "customs" / "README.md").read_text(encoding="utf-8")
        self.assertIn("不构成产品登记表", readme)
        self.assertIn("不分公司", readme)

        macro = {r["claim_id"]: r for r in load_csv("macro_evidence.csv")}
        for cid in ("MC033", "MC034", "MC035"):
            self.assertIn(cid, macro)
        usd_2025 = sum(monthly_usd[f"2025{m:02d}"] for m in range(1, 13))
        usd_2026h1 = sum(monthly_usd[f"2026{m:02d}"] for m in range(1, 7))
        self.assertEqual(usd_2025, 5189328259)
        self.assertEqual(usd_2026h1, 3427389890)
        self.assertIn("5,189,328,259", macro["MC033"]["来源描述"])
        self.assertIn("3,427,389,890", macro["MC034"]["来源描述"])


class ContentLedgerAndKn007Test(unittest.TestCase):
    def test_content_ledger_597_rows_enums_cells_and_100pct_live_quote_verification(self) -> None:
        rows = load_csv("corpus/content_ledger/content_ledger.csv")
        self.assertGreaterEqual(len(rows), 631)

        pre_step3 = [r for r in rows if r["batch"] != "step3_daily_2026q4"]
        self.assertEqual(len(pre_step3), 597)

        companies = {r["company"] for r in pre_step3}
        self.assertEqual(len(companies), 20)

        exp_rows = [r for r in pre_step3 if r["batch"] == "step2_expansion"]
        exp_companies = {r["company"] for r in exp_rows}
        self.assertEqual(len(exp_companies), 15)
        self.assertGreaterEqual(len(exp_rows), 200)

        tree_doc = yaml.safe_load((ROOT / "tree.yaml").read_text(encoding="utf-8"))
        leaf_cells = scan._tree_leaf_cells(tree_doc)
        self.assertEqual(len(leaf_cells), 41)

        del scan.ERR[:]
        scan._check_content_ledger(rows, leaf_cells)
        errs = list(scan.ERR)
        del scan.ERR[:]
        self.assertEqual(errs, [])

        # Re-run strict whitespace-stripped substring check directly on local source files
        def norm(s: str) -> str:
            return re.sub(r"\s+", "", s or "")

        source_cache: dict[str, str] = {}
        misses: list[str] = []
        for r in exp_rows:
            rel_path = r["local_source_path"].split("#")[0]
            full_path = ROOT / rel_path
            self.assertTrue(full_path.exists(), f"{r['cid']} 本地源文件不存在: {rel_path}")
            if rel_path not in source_cache:
                source_cache[rel_path] = norm(full_path.read_text(encoding="utf-8", errors="ignore"))
            if norm(r["verbatim_quote"]) not in source_cache[rel_path]:
                misses.append(r["cid"])
        self.assertEqual(misses, [], f"step2_expansion 存在未逐字命中本地原文的条目: {misses}")

    def test_kn007_burn_in_gross_margin_empirical_anchor(self) -> None:
        kb_doc = yaml.safe_load((ROOT / "knowledge.yaml").read_text(encoding="utf-8"))
        kn007 = next(k for k in kb_doc["knowledge"] if k["id"] == "KN007")
        detail = str(kn007.get("说细点") or "")
        for pct in ("37.45%", "50.65%", "12.55%"):
            self.assertIn(pct, detail)


class RelationshipTimelineCutsAndRefsTest(unittest.TestCase):
    def test_timeline_covers_all_236_edges_isolates_special_states_and_has_daily_columns(self) -> None:
        tl_rows = load_csv("corpus/relationships/relationship_timeline.csv")
        edges = load_csv("edges.csv")
        expected_eids = {r["edge_id"] for r in edges}
        self.assertEqual(len(expected_eids), 236)

        covered_eids: set[str] = set()
        for r in tl_rows:
            for tok in re.split(r"[;,\s]+", r["source_edge_ids"].strip()):
                if tok:
                    covered_eids.add(tok.split("#")[0])
        self.assertEqual(covered_eids, expected_eids)

        # Equipment watch pool supplementary rows (including FT-OB-20241213)
        self.assertTrue(any("FT-OB-20241213" in r["notes"] and r["numeric_value"] == "4800" for r in tl_rows))

        # Special observe_type isolation
        obs_types = {r["observe_type"] for r in tl_rows}
        for special in ("confirmed_ended", "procedural_intermediary", "bad_debt_frozen"):
            self.assertIn(special, obs_types)

        # Daily hookup columns present
        for col in ("event_date", "source_channel", "daily_ref_id"):
            self.assertIn(col, tl_rows[0])

        rel_readme = (ROOT / "corpus" / "relationships" / "README.md").read_text(encoding="utf-8")
        self.assertIn("daily_qa", rel_readme)
        self.assertIn("event_disclosed", rel_readme)

    def test_negative_cuts_74_rows_zero_leak_and_refs_case005_budget_8(self) -> None:
        cuts = load_csv("corpus/relationships/edge_negative_cuts.csv")
        self.assertEqual(len(cuts), 74)

        edges = load_csv("edges.csv")
        active_undir: set[tuple[str, str]] = set()
        for e in edges:
            s, d = e["供方"].strip(), e["需方"].strip()
            active_undir.add((s, d))
            active_undir.add((d, s))

        leaked = []
        for c in cuts:
            comp = c["company"].strip()
            cp = c["counterparty"].strip()
            cpn = c["counterparty_normalized"].strip()
            isup = c["implied_supplier"].strip()
            icus = c["implied_customer"].strip()
            if (
                c["leaked_in_edges_csv"].strip().lower() == "true"
                or (comp, cp) in active_undir
                or (comp, cpn) in active_undir
                or (isup and icus and (isup, icus) in active_undir)
            ):
                leaked.append(c["cut_id"])
        self.assertEqual(leaked, [])

        self.assertEqual(len(load_csv("corpus/relationships/counterparty_audit.csv")), 15)
        self.assertEqual(len(load_csv("corpus/relationships/sellside_watch_alarms.csv")), 7)

        cases_md = (ROOT / "refs" / "解匿判例库.md").read_text(encoding="utf-8")
        self.assertIn("## 判例#005", cases_md)
        self.assertEqual(len(os.listdir(ROOT / "refs")), 8)


class ScanStep2PureFunctionsTest(unittest.TestCase):
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

    def assertBlocked(self, errs: list[str], tag: str, needle: str) -> None:
        self.assertTrue(
            any(e.startswith(f"[{tag}]") and needle in e for e in errs),
            f"期望 [{tag}] 含 {needle!r}，实际: {errs}",
        )

    def test_corpus_path_re_recognizes_all_step2_subtrees(self) -> None:
        paths = [
            "corpus/annual-2023/300308/a.pdf",
            "corpus/annual-2024/300570/b.pdf.txt#L446",
            "corpus/customs/customs_partners.csv",
            "corpus/content_ledger/content_ledger.csv#TCG24-09",
            "corpus/relationships/relationship_timeline.csv",
            "corpus/salvaged/entity_nodes.csv",
        ]
        for p in paths:
            with self.subTest(path=p):
                expected = p.split("#")[0]
                row = {"point_id": "P999", "锚点URL": f"见（{p}）"}
                seen: list[str] = []
                errs = self.errors(scan._check_point_row, row, exists=lambda rel: seen.append(rel) or True)
                self.assertEqual(errs, [])
                self.assertEqual(seen, [expected])
                bad_errs = self.errors(scan._check_point_row, row, exists=lambda rel: False)
                self.assertBlocked(bad_errs, "⑩", expected)

    def _customs_fixture(self) -> dict[str, list[dict[str, str]]]:
        months = list(scan._CUSTOMS_RECON_MONTHS)
        return {
            "monthly": [{"月份": ym, "HS编码": "85177950", "金额": "100000"} for ym in months],
            "partners": [{"月份": ym, "贸易伙伴": "马来西亚", "金额": "100000"} for ym in months],
            "province": [{"月份": ym, "注册地": "江苏省", "贸易伙伴": "马来西亚", "金额USD": "100000"} for ym in months],
            "trademode": [{"月份": ym, "贸易伙伴": "马来西亚", "贸易方式": "进料加工贸易", "金额USD": "100000"} for ym in months],
        }

    def test_customs_tables_positive_and_negative_cases(self) -> None:
        ok = self._customs_fixture()
        self.assertEqual(self.errors(scan._check_customs_tables, ok), [])

        # Embedded newline in field
        bad_nl = self._customs_fixture()
        bad_nl["partners"][0] = dict(bad_nl["partners"][0], 贸易伙伴="哥斯达黎\n加")
        self.assertBlocked(self.errors(scan._check_customs_tables, bad_nl), "⑨", "内嵌换行符")

        # Duplicate PK
        bad_pk = self._customs_fixture()
        bad_pk["trademode"].append({"月份": "202501", "贸易伙伴": "马来西亚", "贸易方式": "进料加工贸易", "金额USD": "0"})
        self.assertBlocked(self.errors(scan._check_customs_tables, bad_pk), "⑨", "重复主键")

        # USD reconciliation drift >= 0.01%
        bad_drift = self._customs_fixture()
        bad_drift["province"][3] = dict(bad_drift["province"][3], 金额USD="100025")
        self.assertBlocked(self.errors(scan._check_customs_tables, bad_drift), "⑨", "偏差")

    def test_content_ledger_positive_and_negative_cases(self) -> None:
        base = {
            "cid": "CL01",
            "fact_type": "技术参数",
            "stance": "neutral",
            "cell_ids": "C1,M2a",
            "verbatim_quote": "100G PAM4 EML芯片实现量产。",
            "local_source_path": "corpus/legacy-input/sample.txt",
        }
        self.assertEqual(
            self.errors(scan._check_content_ledger, [base, dict(base, cid="CL02", cell_ids="通用", stance="issuer_self")], {"C1", "M2a"}, exists=lambda _: True),
            [],
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [base, base], {"C1", "M2a"}, exists=lambda _: True),
            "⑧",
            "cid重复",
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [dict(base, fact_type="订单金额")], {"C1", "M2a"}, exists=lambda _: True),
            "⑧",
            "fact_type非法",
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [dict(base, stance="bullish")], {"C1", "M2a"}, exists=lambda _: True),
            "⑧",
            "stance非法",
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [dict(base, cell_ids="C1,NOPE9")], {"C1", "M2a"}, exists=lambda _: True),
            "⑧",
            "NOPE9",
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [dict(base, verbatim_quote="")], {"C1", "M2a"}, exists=lambda _: True),
            "⑧",
            "verbatim_quote为空",
        )
        self.assertBlocked(
            self.errors(scan._check_content_ledger, [base], {"C1", "M2a"}, exists=lambda _: False),
            "⑧",
            "local_source_path不存在",
        )

    def test_relationship_tables_positive_and_negative_cases(self) -> None:
        tl = {
            "timeline_id": "TL0001",
            "supplier": "天孚通信",
            "customer": "Fabrinet",
            "source_channel": "annual_report",
            "value_raw": "63.31%(326884.36万元)",
            "source_edge_ids": "E043;E072#sub",
            "notes": "正常备注(核验通过)",
        }
        cuts_ok = [
            {
                "cut_id": "CUT001",
                "company": "博创科技",
                "counterparty": "长飞光纤光缆有限公司",
                "counterparty_normalized": "长飞光纤光缆有限公司",
                "implied_supplier": "长飞光纤光缆有限公司",
                "implied_customer": "博创科技",
                "leaked_in_edges_csv": "false",
            }
        ]
        active = [{"供方": "天孚通信", "需方": "Fabrinet"}]

        self.assertEqual(
            self.errors(
                scan._check_relationship_tables,
                [tl, dict(tl, timeline_id="TL0002", source_channel="daily_announcement", source_edge_ids="")],
                {"E043", "E072"},
                cut_rows=cuts_ok,
                active_edges=active,
            ),
            [],
        )
        self.assertBlocked(
            self.errors(scan._check_relationship_tables, [tl, tl], {"E043", "E072"}, active_edges=active),
            "②",
            "timeline_id重复",
        )
        self.assertBlocked(
            self.errors(scan._check_relationship_tables, [dict(tl, source_edge_ids="E043;E999")], {"E043", "E072"}, active_edges=active),
            "②",
            "E999",
        )
        self.assertBlocked(
            self.errors(scan._check_relationship_tables, [dict(tl, source_channel="sellside_ppt")], {"E043", "E072"}, active_edges=active),
            "②",
            "source_channel非法",
        )
        self.assertBlocked(
            self.errors(scan._check_relationship_tables, [dict(tl, value_raw="63.31%(326884.36万元")], {"E043", "E072"}, active_edges=active),
            "②",
            "括号不平衡",
        )
        leaked_cut = [dict(cuts_ok[0], cut_id="CUT999", company="天孚通信", counterparty="Fabrinet", counterparty_normalized="Fabrinet", implied_supplier="天孚通信", implied_customer="Fabrinet")]
        self.assertBlocked(
            self.errors(scan._check_relationship_tables, [tl], {"E043", "E072"}, cut_rows=leaked_cut, active_edges=active),
            "②",
            "泄漏至活跃 edges.csv",
        )


if __name__ == "__main__":
    unittest.main()
