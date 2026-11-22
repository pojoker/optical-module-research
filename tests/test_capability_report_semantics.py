"""能力明细生成器的证据语义契约测试（WP-A）。

背景（Kimi 语义审计 H2 / Cursor 契约审计 H1）：

1. `points.csv.判定等级` 是「准入路径 + 括号过程备注」的过程型串，不是 A–D 证据等级。
   生成器把它原样写进 `capability_details.csv` 的「证据等级」列，读者会读成证据分级；
   同时 `EVIDENCE_RANK` 只对无括号前缀精确匹配，195 行带括号的「判定闸-生产中(…)」
   全部 miss，落到默认 rank 1（低于 context_only），导致选点错误。
2. C5 / M1 / MOD1 是粗粒度格，格名括号里枚举了异构子能力（DSP/Driver/TIA/CDR/主控MCU、
   InP/GaAs/SOI、800G/1.6T）。生成器用格名去匹配产品与材料，等于把整格枚举当成
   每家公司的产品能力，进而被读成产品供货或路线能力。

本测试只锁生成器语义与读者可见措辞；机器门通过不代表领域结论成立。
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_detailed_capability_report as report  # noqa: E402
import participation  # noqa: E402


UNIVERSE = [
    {
        "代码": "000063",
        "名称": "测试公司甲",
        "市场": "深交所主板",
        "行业分类": "通信设备",
    },
    {
        "代码": "300394",
        "名称": "测试公司乙",
        "市场": "深交所创业板",
        "行业分类": "光通信设备",
    },
]

TREE = {
    "C5": {"name": "电芯片(DSP/Driver/TIA/CDR/主控MCU)", "route": "共用", "process_note": ""},
    "M1": {"name": "衬底(InP/GaAs/SOI)", "route": "共用", "process_note": ""},
    "MOD1": {"name": "数通直检模块(800G/1.6T)", "route": "数通COB/硅光", "process_note": ""},
    "C4": {"name": "硅光PIC", "route": "数通COB/硅光", "process_note": ""},
}


def point(
    point_id: str,
    company: str,
    cell_id: str,
    grade: str,
    quote: str = "",
    date: str = "2026-07-26",
) -> dict[str, str]:
    return {
        "point_id": point_id,
        "公司": company,
        "cell_id": cell_id,
        "状态": "生产中",
        "上市标签": "A股",
        "判定等级": grade,
        "命中引语": quote,
        "锚点URL": "https://example.com/report.pdf",
        "检索日期": date,
    }


class AdmissionSemanticsTest(unittest.TestCase):
    """判定等级 = 准入路径 + 过程备注；不得冒充 A–D 证据等级。"""

    def test_bracketed_process_note_keeps_base_rank(self) -> None:
        bracketed = "判定闸-生产中(kimi取证:自研+外代工流片,fab-lite;锚待codex复核)"
        self.assertEqual(report.admission_path(bracketed), "判定闸-生产中")
        self.assertEqual(
            report.admission_rank(bracketed),
            report.ADMISSION_RANK["判定闸-生产中"],
        )

    def test_bracketed_note_does_not_fall_to_unknown_rank(self) -> None:
        bracketed = "判定闸-生产中(闸内可降档;锚待复核)"
        self.assertEqual(report.admission_rank(bracketed), report.admission_rank("判定闸-生产中"))
        self.assertGreater(report.admission_rank(bracketed), report.admission_rank("context_only"))
        self.assertNotEqual(report.admission_rank(bracketed), report.UNKNOWN_ADMISSION_RANK)

    def test_fullwidth_bracket_is_stripped_too(self) -> None:
        self.assertEqual(
            report.admission_path("判定闸-生产中（疑Driver/TIA类；宁严可改在建）"),
            "判定闸-生产中",
        )

    def test_nested_bracket_note_does_not_leak_into_path(self) -> None:
        self.assertEqual(
            report.admission_path("判定闸-生产中(自研芯片(800G)已发货;锚待复核)"),
            "判定闸-生产中",
        )

    def test_unknown_path_stays_at_unknown_rank(self) -> None:
        self.assertEqual(report.admission_rank("某个没见过的路径"), report.UNKNOWN_ADMISSION_RANK)
        self.assertEqual(report.admission_path(""), "")

    def test_canonical_output_schema_is_not_changed(self) -> None:
        self.assertIn("证据等级", report.FIELDNAMES)
        self.assertNotIn("准入依据", report.FIELDNAMES)

    def test_pdf_label_does_not_call_it_evidence_grade(self) -> None:
        source = inspect.getsource(report.build_pdf)
        self.assertIn("准入依据：", source)
        self.assertNotIn("证据等级：", source)


class RowBuildingTest(unittest.TestCase):
    """用固定 fixture 重算行，避免依赖仓库当前数据。"""

    def setUp(self) -> None:
        self._read_rows = participation.read_rows
        self._universe = participation.unique_universe
        self._tree = report.tree_metadata
        participation.read_rows = lambda _path: list(self.points)  # type: ignore[assignment]
        participation.unique_universe = lambda: list(UNIVERSE)  # type: ignore[assignment]
        report.tree_metadata = lambda: dict(TREE)  # type: ignore[assignment]
        self.points: list[dict[str, str]] = []

    def tearDown(self) -> None:
        participation.read_rows = self._read_rows  # type: ignore[assignment]
        participation.unique_universe = self._universe  # type: ignore[assignment]
        report.tree_metadata = self._tree  # type: ignore[assignment]

    def rows_for(self, points: list[dict[str, str]]) -> dict[str, dict[str, str]]:
        self.points = points
        return {(row["公司"], row["cell_id"]): row for row in report.granular_rows()}

    def test_row_keeps_canonical_value_while_reader_can_extract_path(self) -> None:
        rows = self.rows_for(
            [point("P1", "测试公司甲", "C4", "判定闸-生产中(子代理起草;锚待复核)")]
        )
        row = rows[("测试公司甲", "C4")]
        self.assertIn("锚待复核", row["证据等级"])
        self.assertEqual(report.admission_path(row["证据等级"]), "判定闸-生产中")

    def test_bracketed_point_wins_over_weaker_unbracketed_point(self) -> None:
        rows = self.rows_for(
            [
                point("P1", "测试公司甲", "C4", "edge_backed", date="2026-07-20"),
                point("P2", "测试公司甲", "C4", "判定闸-生产中(锚待复核)", date="2026-07-26"),
            ]
        )
        row = rows[("测试公司甲", "C4")]
        self.assertEqual(report.admission_path(row["证据等级"]), "判定闸-生产中")
        self.assertEqual(row["证据日期"], "2026-07-26")

    def test_unlabelled_point_is_not_presented_as_a_grade(self) -> None:
        rows = self.rows_for([point("P1", "测试公司甲", "C4", "")])
        row = rows[("测试公司甲", "C4")]
        self.assertEqual(row["证据等级"], "")
        self.assertEqual(report.admission_path(row["证据等级"]) or report.UNKNOWN_ADMISSION_LABEL, report.UNKNOWN_ADMISSION_LABEL)

    def test_coarse_cell_does_not_inherit_node_enumeration_as_product(self) -> None:
        rows = self.rows_for(
            [point("P1", "测试公司甲", "C5", "edge_backed", quote="公司从事集成电路设计")]
        )
        product = rows[("测试公司甲", "C5")]["具体产品"]
        for token in ("DSP", "Driver", "TIA", "CDR", "MCU"):
            self.assertNotIn(token, product)
        self.assertIn(report.COARSE_CELL_BOUNDARY, product)
        self.assertIn("不推出具体产品供货", product)
        self.assertIn("也不构成完整路线能力", product)

    def test_coarse_cell_material_is_not_inherited_from_node_name(self) -> None:
        rows = self.rows_for(
            [point("P1", "测试公司乙", "M1", "edge_backed", quote="公司从事半导体材料业务")]
        )
        material = rows[("测试公司乙", "M1")]["材料与技术"]
        for token in ("InP", "GaAs", "Si/SOI"):
            self.assertNotIn(token, material)
        self.assertIn(report.COARSE_CELL_BOUNDARY, rows[("测试公司乙", "M1")]["具体产品"])

    def test_coarse_cell_still_reports_disclosure_backed_sub_capability(self) -> None:
        rows = self.rows_for(
            [
                point(
                    "P1",
                    "测试公司甲",
                    "C5",
                    "edge_backed",
                    quote="interconnect products include PAM DSP, laser driver and TIA chips",
                )
            ]
        )
        product = rows[("测试公司甲", "C5")]["具体产品"]
        self.assertIn("DSP", product)
        self.assertIn("TIA", product)
        self.assertNotIn("MCU", product)
        self.assertIn(report.COARSE_CELL_BOUNDARY, product)

    def test_fine_grained_cell_keeps_its_node_name(self) -> None:
        rows = self.rows_for([point("P1", "测试公司甲", "C4", "edge_backed")])
        row = rows[("测试公司甲", "C4")]
        self.assertEqual(row["细分节点"], "硅光PIC")
        self.assertNotIn(report.COARSE_CELL_BOUNDARY, row["具体产品"])

    def test_coarse_boundary_covers_the_three_audited_cells(self) -> None:
        for cell_id in ("C5", "M1", "MOD1"):
            note = report.coarse_cell_note(cell_id)
            self.assertTrue(note, cell_id)
            self.assertIn("不推出具体产品供货", note)
            self.assertIn("也不构成完整路线能力", note)
        self.assertEqual(report.coarse_cell_note("C4"), "")

    def test_coarse_boundary_never_names_cell_members(self) -> None:
        """边界提示不得把未披露的子能力词带进产品字段。"""
        members = ["DSP", "Driver", "TIA", "CDR", "MCU", "InP", "GaAs", "SOI", "800G", "1.6T"]
        for cell_id in ("C5", "M1", "MOD1"):
            note = report.coarse_cell_note(cell_id)
            for token in members:
                self.assertNotIn(token, note, f"{cell_id} 边界提示含子能力词 {token}")
        for value in report.COARSE_CELLS.values():
            for token in members:
                self.assertNotIn(token, value)

    def test_generic_coarse_row_has_no_sub_capability_token_at_all(self) -> None:
        rows = self.rows_for(
            [point("P1", "测试公司甲", "C5", "edge_backed", quote="公司从事集成电路设计")]
        )
        product = rows[("测试公司甲", "C5")]["具体产品"]
        for token in ("DSP", "Driver", "TIA", "CDR", "MCU"):
            self.assertNotIn(token, product)


class ReaderOutputTest(unittest.TestCase):
    """读者可见输出：不出现过程备注冒充等级，且粗粒度边界随卡片输出。"""

    def row(self, **overrides: str) -> dict[str, str]:
        base = {
            "公司代码": "000063",
            "公司": "测试公司甲",
            "市场": "深交所主板",
            "行业分类": "通信设备",
            "主环节": "芯片层",
            "cell_id": "C5",
            "细分节点": "电芯片(DSP/Driver/TIA/CDR/主控MCU)",
            "技术路线": "共用",
            "具体产品": "DSP｜" + report.coarse_cell_note("C5"),
            "材料与技术": "披露未细分",
            "工艺能力": "披露未细分",
            "规格与应用": "800G",
            "当前阶段": "生产中",
            "产业角色": "芯片设计或制造",
            "证据等级": "判定闸-生产中(过程备注不应展示)",
            "证据日期": "2026-07-26",
            "来源锚点": "https://example.com/report.pdf",
            "原始披露摘要": "自研DSP芯片已发货",
        }
        base.update(overrides)
        return base

    def test_capability_card_shows_admission_path_not_process_note(self) -> None:
        html = report.capability_section([self.row()], {})
        self.assertIn("判定闸-生产中", html)
        self.assertNotIn("锚待复核", html)

    def test_capability_card_carries_coarse_cell_boundary(self) -> None:
        html = report.capability_section([self.row()], {})
        self.assertIn(report.COARSE_CELL_BOUNDARY, html)
        self.assertIn("不推出具体产品供货", html)

    def test_section_description_states_admission_and_coarse_rules(self) -> None:
        html = report.capability_section([self.row()], {})
        self.assertIn("准入依据", html)
        self.assertIn("只说明该点以何种路径进入账本", html)
        self.assertIn("粗粒度格", html)


class TreeMetadataTest(unittest.TestCase):
    """tree.yaml 结构化解析：带 knowledge_ids/status/decision_ref 的叶不得落成「未标」。"""

    def test_real_tree_has_no_unlabelled_route(self) -> None:
        meta = report.tree_metadata()
        self.assertTrue(meta)
        self.assertEqual([cell for cell, node in meta.items() if node["route"] == "未标"], [])

    def test_leaves_with_extra_keys_are_parsed(self) -> None:
        meta = report.tree_metadata()
        for cell in ("C1", "D8", "D12", "M2a", "M2c", "EQ3", "EQ4", "EQ7", "EQ8", "P1"):
            with self.subTest(cell=cell):
                self.assertIn(cell, meta)
                self.assertTrue(meta[cell]["name"])
                self.assertNotEqual(meta[cell]["route"], "未标")
        self.assertEqual(meta["M2c"]["route"], "数通COB/硅光")
        self.assertEqual(meta["EQ8"]["route"], "电信气密")

    def test_enumeration_in_node_name_is_not_credited_as_product(self) -> None:
        self._read_rows = participation.read_rows
        self._universe = participation.unique_universe
        self._tree = report.tree_metadata
        try:
            participation.read_rows = lambda _path: [  # type: ignore[assignment]
                point("P1", "测试公司甲", "C1", "edge_backed", quote="公司从事半导体激光器芯片研发与生产")
            ]
            participation.unique_universe = lambda: list(UNIVERSE)  # type: ignore[assignment]
            report.tree_metadata = lambda: {  # type: ignore[assignment]
                "C1": {"name": "激光器芯片(EML/DFB/CW光源)", "route": "共用", "process_note": ""}
            }
            row = report.granular_rows()[0]
        finally:
            participation.read_rows = self._read_rows  # type: ignore[assignment]
            participation.unique_universe = self._universe  # type: ignore[assignment]
            report.tree_metadata = self._tree  # type: ignore[assignment]
        self.assertEqual(row["细分节点"], "激光器芯片(EML/DFB/CW光源)")
        for token in ("EML", "DFB", "CW光源"):
            self.assertNotIn(token, row["具体产品"])


class StageDetailTest(unittest.TestCase):
    """量产/交付证据优先于末尾的「研发」后备，不得误降为 研发/建设中。"""

    def test_scale_production_wins_over_rnd(self) -> None:
        text = "拥有覆盖磷化铟衬底、外延材料至光芯片的全流程研发与工艺体系。目前CWlaser已实现规模化量产"
        self.assertEqual(report.stage_detail(text, "生产中"), "规模量产/批量交付")

    def test_already_supplying_wins_over_in_development(self) -> None:
        text = "公司1.6T光模块PCB用板已经供货，3.2T光模块PCB用板目前与客户开发中"
        self.assertEqual(report.stage_detail(text, "生产中"), "量产/产业化")

    def test_batch_delivery_and_high_shipment(self) -> None:
        self.assertEqual(report.stage_detail("800G ZR/ZR+相干光模块实现批量交付", ""), "规模量产/批量交付")
        self.assertEqual(report.stage_detail("订单于本年度维持于较高的出貨水平；高出货", ""), "规模量产/批量交付")
        self.assertEqual(report.stage_detail("各类产品研发并实现800G量产", ""), "量产/产业化")

    def test_small_batch_is_not_promoted_to_scale(self) -> None:
        self.assertEqual(report.stage_detail("高频高速产品已在光模块客户中实现小批量出货", ""), "小批量/试产")
        self.assertEqual(report.stage_detail("样板及小批量交付，仍处于客户需求验证", ""), "小批量/试产")

    def test_rnd_with_production_is_operating(self) -> None:
        self.assertEqual(report.stage_detail("具备光缆、MPO预端接组件等产品研发与量产能力", ""), "生产经营中")
        self.assertEqual(report.stage_detail("公司研发和生产的相干光模块用于长距传输", ""), "生产经营中")

    def test_pure_rnd_falls_back(self) -> None:
        self.assertEqual(report.stage_detail("1.6T产品在研", ""), "研发/建设中")
        self.assertEqual(report.stage_detail("", "生产中"), "生产中")


class ResolveCompanyRealUniverseTest(unittest.TestCase):
    def test_real_universe_aliases(self) -> None:
        names = {row["名称"] for row in participation.unique_universe()}
        self.assertEqual(participation.resolve_company("南大光电", names), "江苏南大光电材料股份有限公司")
        self.assertEqual(participation.resolve_company("汇聚科技", names), "汇聚科技(Huiju Technology)")


if __name__ == "__main__":
    unittest.main()
