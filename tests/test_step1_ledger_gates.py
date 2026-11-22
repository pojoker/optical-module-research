"""Step 1 账本确定性机器门回归（2026-11-21）。

全部用内存构造的正反例直接调用 scan.py 的纯校验函数，不读写真实账本；
每个反例都断言出现了带对应不变量编号与关键文案的受控 fail（而非异常）。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import participation  # noqa: E402
import scan  # noqa: E402


SE056 = {
    "row_id": "SE056",
    "公司": "意华股份",
    "证据等级": "B",
    "情景标记": "base",
    "单位": "千只",
    "出货量": "3726893.686",
    "推导式": "FY2024年报产销量表本期列直接披露",
    "收入输入": "2,464,381,267.00元(意华股份2024年报同节分产品表)",
    "ASP输入": "隐含混合ASP≈661.2元/只(2024量价同表口径)",
    "产能天顶检": "产销率98.55%复算(销3726893.686千只/产3781727.897千只),通过",
}


class GateCase(unittest.TestCase):
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

    def assertClean(self, errs: list[str]) -> None:
        self.assertEqual(errs, [])


class ShipmentGateTest(GateCase):
    def row(self, **overrides: str) -> dict[str, str]:
        data = dict(SE056)
        data.update(overrides)
        return data

    def test_se056_thousandfold_asp_is_blocked(self) -> None:
        errs = self.errors(scan._check_shipment_row, self.row())
        self.assertBlocked(errs, "⑪", "隐含ASP算术不符")

    def test_se056_corrected_two_significant_digits_passes(self) -> None:
        self.assertClean(self.errors(scan._check_shipment_row, self.row(ASP输入="隐含混合ASP≈0.66元/只")))
        self.assertClean(self.errors(scan._check_shipment_row, self.row(ASP输入="隐含混合ASP≈0.6612元/只")))

    def test_wan_units_and_wanyuan_revenue_are_scaled(self) -> None:
        ok = self.row(单位="万只", 出货量="2109", 收入输入="3,745,651.87万元", ASP输入="隐含混合ASP≈1,776元/只")
        self.assertClean(self.errors(scan._check_shipment_row, ok))
        bad = self.row(单位="万只", 出货量="2109", 收入输入="3,745,651.87万元", ASP输入="隐含混合ASP≈17.76元/只")
        self.assertBlocked(self.errors(scan._check_shipment_row, bad), "⑪", "隐含ASP算术不符")

    def test_kk_unit_is_million_pieces(self) -> None:
        ok = self.row(单位="KK", 出货量="202.54", 收入输入="3,957.42万元", ASP输入="隐含混合ASP≈0.195元/只")
        self.assertClean(self.errors(scan._check_shipment_row, ok))

    def test_hardcoded_yuan_per_jian_mismatch_is_blocked(self) -> None:
        for unit in ("台", "万片", "千克", "万个", "支/套"):
            with self.subTest(unit=unit):
                bad = self.row(单位=unit, 出货量="100", 收入输入="-", ASP输入="ASP≈10元/件")
                self.assertBlocked(self.errors(scan._check_shipment_row, bad), "⑪", "ASP计价单位")

    def test_yuan_per_jian_with_jian_unit_passes(self) -> None:
        ok = self.row(单位="万件", 出货量="1301.99", 收入输入="2,038,769,308.96元", ASP输入="隐含混合ASP≈156.6元/件")
        self.assertClean(self.errors(scan._check_shipment_row, ok))

    def test_scientific_notation_is_blocked(self) -> None:
        errs = self.errors(scan._check_shipment_row, self.row(ASP输入="隐含ASP≈1.414e+05元/台", 收入输入="-"))
        self.assertBlocked(errs, "⑪", "科学计数法")
        errs = self.errors(scan._check_shipment_row, self.row(收入输入="2.46e+09元", ASP输入="-"))
        self.assertBlocked(errs, "⑪", "科学计数法")

    def test_yoy_back_calculation_cannot_be_grade_b(self) -> None:
        errs = self.errors(scan._check_shipment_row, self.row(推导式="2025销量按同比反算2024", ASP输入="-"))
        self.assertBlocked(errs, "⑪", "同比反算")
        ok = self.row(推导式="2025销量按同比反算2024", 证据等级="C", ASP输入="-")
        self.assertClean(self.errors(scan._check_shipment_row, ok))

    def test_utilization_without_output_is_blocked(self) -> None:
        bad = self.row(ASP输入="-", 产能天顶检="销量2,109万只≤产能2,806万只(隐含利用率75.2%),通过")
        self.assertBlocked(self.errors(scan._check_shipment_row, bad), "⑪", "利用率")
        ok = self.row(ASP输入="-", 产能天顶检="产量2,700万只/产能2,806万只(利用率96.2%),通过")
        self.assertClean(self.errors(scan._check_shipment_row, ok))
        ratio = self.row(ASP输入="-", 产能天顶检="销量/产能比75.2%,通过")
        self.assertClean(self.errors(scan._check_shipment_row, ratio))

    def test_selftest_five_column_fixture_still_passes(self) -> None:
        base = {"row_id": "SE001", "证据等级": "B", "情景标记": "", "单位": "只", "出货量": "1000"}
        self.assertClean(self.errors(scan._check_shipment_row, base))


class SyncAndIntegrityGateTest(GateCase):
    def test_universe_count_must_match_frozen(self) -> None:
        self.assertBlocked(self.errors(scan._check_tree_universe, {"universe": {"count": 461}}, 463), "①", "universe.count")
        self.assertClean(self.errors(scan._check_tree_universe, {"universe": {"count": 463}}, 463))

    def test_triage_duplicate_hit_id_is_blocked(self) -> None:
        rows = [{"hit_id": "仕佳光子+D8+2025年报"}, {"hit_id": "仕佳光子+D8+2025年报"}]
        self.assertBlocked(self.errors(scan._check_triage_ids, rows), "⑦", "hit_id重复")
        self.assertClean(self.errors(scan._check_triage_ids, [{"hit_id": "a"}, {"hit_id": "b"}]))

    def test_watchlist_cell_must_be_tree_leaf(self) -> None:
        self.assertBlocked(
            self.errors(scan._check_watchlist, [{"公司": "光迅科技", "cell_id": "EQ7边"}], {"EQ7"}),
            "⑦",
            "EQ7边",
        )
        ok = [{"cell_id": ""}, {"cell_id": "ANY"}, {"cell_id": "D4/M4"}]
        self.assertClean(self.errors(scan._check_watchlist, ok, {"D4", "M4"}))

    def test_tree_leaf_cells_walks_nested_children(self) -> None:
        tree = {"tree": [{"id": "M", "children": [{"cell_id": "M1"}, {"id": "M2", "children": [{"cell_id": "M2a"}]}]}]}
        self.assertEqual(scan._tree_leaf_cells(tree), {"M1", "M2a"})


class EdgeGateTest(GateCase):
    def edge(self, **overrides: str) -> dict[str, str]:
        data = {"edge_id": "E900", "占比或金额原文": "27.6%", "验证状态": "会话端已验证-SEC原文命中", "备注": ""}
        data.update(overrides)
        return data

    def test_clean_edge_passes(self) -> None:
        self.assertClean(self.errors(scan._check_edge_integrity, self.edge()))

    def test_unbalanced_paren_truncation_is_blocked(self) -> None:
        errs = self.errors(scan._check_edge_integrity, self.edge(验证状态="B级终态(R2审查:U门闭合$1272M上界/L门客户级归类不"))
        self.assertBlocked(errs, "④", "括号不平衡")

    def test_trailing_separator_truncation_is_blocked(self) -> None:
        for tail in ("；", "，", "-"):
            with self.subTest(tail=tail):
                errs = self.errors(scan._check_edge_integrity, self.edge(占比或金额原文=f"11.86%；8.65%{tail}"))
                self.assertBlocked(errs, "④", "截断")

    def test_placeholder_dash_is_not_truncation(self) -> None:
        self.assertClean(self.errors(scan._check_edge_integrity, self.edge(占比或金额原文="-")))

    def test_stale_working_paper_refs_are_blocked(self) -> None:
        for ref in ("deanonymization-cases.md", "seed findings", "jituanyi-leads.md"):
            with self.subTest(ref=ref):
                errs = self.errors(scan._check_edge_integrity, self.edge(备注=f"出处见 {ref}"))
                self.assertBlocked(errs, "②", ref)


class AnchorGateTest(GateCase):
    PDF = "https://static.cninfo.com.cn/finalpage/2026-03-13/1225006760.PDF"

    def point(self, pid: str, company: str, url: str | None = None, quote: str = "", tag: str = "A股") -> dict[str, str]:
        return {
            "point_id": pid,
            "公司": company,
            "上市标签": tag,
            "锚点URL": url if url is not None else self.PDF,
            "命中引语": quote,
            "判定等级": "判定闸-生产中",
        }

    def test_macro_xueqiu_basic_auth_url_is_blocked(self) -> None:
        row = {"claim_id": "MC003", "证据等级": "C", "证据类型": "二手汇总", "链接": "https://ssgsmarketing@xueqiu.com/7831343781/395687338"}
        self.assertBlocked(self.errors(scan._check_macro_row, row), "⑨", "basic-auth")

    def test_macro_baidu_search_placeholder_is_blocked(self) -> None:
        row = {"claim_id": "MC022", "证据等级": "C", "证据类型": "二手汇总", "链接": "https://www.baidu.com/s?wd=%E4%B8%9C"}
        self.assertBlocked(self.errors(scan._check_macro_row, row), "⑨", "搜索占位")

    def test_macro_grade_b_requires_real_link(self) -> None:
        row = {"claim_id": "MC012", "证据等级": "B", "证据类型": "机构报告/厂商规格", "链接": "", "来源描述": "某机构报告"}
        self.assertBlocked(self.errors(scan._check_macro_row, row), "⑨", "无合法http")
        internal = {"claim_id": "MC031", "证据等级": "B", "证据类型": "内部证据账本可重算", "链接": ""}
        self.assertClean(self.errors(scan._check_macro_row, internal))
        ok = {"claim_id": "MC001", "证据等级": "B", "证据类型": "机构报告/厂商规格", "链接": "https://lightcounting.com/newsletter/x"}
        self.assertClean(self.errors(scan._check_macro_row, ok))

    def test_point_malformed_url_is_blocked(self) -> None:
        row = self.point("P900", "测试", url="https://ssgsmarketing@xueqiu.com/1")
        self.assertBlocked(self.errors(scan._check_point_row, row, exists=lambda rel: True), "⑧", "basic-auth")
        row = self.point("P901", "测试", url="https://www.baidu.com/s?wd=x")
        self.assertBlocked(self.errors(scan._check_point_row, row, exists=lambda rel: True), "⑧", "搜索占位")

    def test_missing_corpus_ir_path_is_blocked(self) -> None:
        row = self.point("P196", "沪硅产业", url="corpus/ir/688126/688126_2099-01-01_沪硅产业_不存在.docx")
        errs = self.errors(scan._check_point_row, row, exists=lambda rel: False)
        self.assertBlocked(errs, "⑩", "corpus/ir/688126/688126_2099-01-01_沪硅产业_不存在.docx")

    def test_existing_corpus_path_with_fragment_passes(self) -> None:
        row = self.point("P187", "测试", url="corpus/qa/301165/qa.jsonl#indexId=2301891159369191424")
        seen: list[str] = []
        errs = self.errors(scan._check_point_row, row, exists=lambda rel: seen.append(rel) or True)
        self.assertClean(errs)
        self.assertEqual(seen, ["corpus/qa/301165/qa.jsonl"])

    def test_real_repo_corpus_path_resolution(self) -> None:
        row = self.point("P198", "红板科技", url="corpus/annual/603459/603459/603459_红板科技_2026_招股说明书.pdf")
        self.assertClean(self.errors(scan._check_point_row, row))

    def test_a_share_cross_company_shared_annual_report_is_blocked(self) -> None:
        pts = [self.point("P083", "深南电路"), self.point("P084", "徕木股份", url=self.PDF + "#page=12")]
        self.assertBlocked(self.errors(scan._check_point_table, pts), "⑧", "共用同一巨潮PDF")

    def test_shared_report_with_relationship_note_passes(self) -> None:
        pts = [self.point("P083", "深南电路"), self.point("P084", "徕木股份", quote="公司主要客户包括深南电路")]
        self.assertClean(self.errors(scan._check_point_table, pts))

    def test_shared_report_same_company_alias_passes(self) -> None:
        pts = [self.point("P044", "江苏南大光电材料股份有限公司"), self.point("P152", "南大光电")]
        self.assertClean(self.errors(scan._check_point_table, pts))

    def test_shared_report_non_a_share_is_out_of_scope(self) -> None:
        pts = [self.point("P1", "甲公司", tag="港股"), self.point("P2", "乙公司")]
        self.assertClean(self.errors(scan._check_point_table, pts))


class ResolveCompanyTest(unittest.TestCase):
    UNIVERSE = {
        "江苏南大光电材料股份有限公司",
        "汇聚科技(Huiju Technology)",
        "鸿腾精密(FIT Hon Teng)",
        "Applied Optoelectronics(AAOI)",
        "Intel(含其代工厂)",
        "中际旭创",
        "光迅科技",
        "汇绿生态",
    }

    def test_explicit_aliases(self) -> None:
        cases = {
            "南大光电": "江苏南大光电材料股份有限公司",
            "汇聚科技": "汇聚科技(Huiju Technology)",
            "鸿腾精密": "鸿腾精密(FIT Hon Teng)",
            "FIT": "鸿腾精密(FIT Hon Teng)",
            "AAOI": "Applied Optoelectronics(AAOI)",
            "Intel": "Intel(含其代工厂)",
            "武汉钧恒科技有限公司": "汇绿生态",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(participation.resolve_company(name, self.UNIVERSE), expected)

    def test_bracket_stripped_match(self) -> None:
        self.assertEqual(
            participation.resolve_company("汇聚科技（Huiju）", self.UNIVERSE),
            "汇聚科技(Huiju Technology)",
        )

    def test_unambiguous_bidirectional_substring(self) -> None:
        self.assertEqual(participation.resolve_company("中际旭创股份有限公司", self.UNIVERSE), "中际旭创")
        self.assertEqual(participation.resolve_company("南大光电材料", self.UNIVERSE), "江苏南大光电材料股份有限公司")

    def test_ambiguous_or_short_names_do_not_merge(self) -> None:
        universe = {"光迅科技", "光迅科技国际"}
        self.assertIsNone(participation.resolve_company("光迅科", universe))
        self.assertIsNone(participation.resolve_company("光迅", self.UNIVERSE))
        self.assertIsNone(participation.resolve_company("", self.UNIVERSE))
        self.assertIsNone(participation.resolve_company("不存在的公司", self.UNIVERSE))


if __name__ == "__main__":
    unittest.main()
