"""问题完成语义契约测试。

背景：研究问题树曾用 `acceptance` 字段 + “已覆盖”措辞，把“有一条 KN/WHY 引用该问题”
读成了“问题已回答/已完成”。本测试锁住修正后的契约：

1. `research_questions.yaml` 不再使用 `acceptance`，改用 `minimum_writeback_contract`；
2. `meta.completion_semantics` 显式声明“已有材料 ≠ 已完成，完成只由人工复核判定”；
3. 读者可见的 `研究问题树.md` 用“已有材料”，不出现“已覆盖”。

机器门只锁结构与措辞；问题是否真正完成由人工复核判定，本文件不做该判断。
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_QUESTIONS = ROOT / "research_questions.yaml"

# 直接执行本测试文件时，Python 只把 tests/research 放进 sys.path；显式加入仓库根目录，
# 保证与 unittest discover 两种入口都能导入根级 render.py。
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class QuestionCompletionSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rq = yaml.safe_load(RESEARCH_QUESTIONS.read_text(encoding="utf-8"))

    def test_field_is_renamed_and_present_on_every_question(self) -> None:
        raw = RESEARCH_QUESTIONS.read_text(encoding="utf-8")
        # 注释里可以解释旧名，但不得再出现旧字段定义行。
        self.assertIsNone(
            re.search(r"^\s*acceptance\s*:", raw, flags=re.M),
            "research_questions.yaml 仍有旧字段 acceptance",
        )

        questions = self.rq.get("questions") or []
        why_questions = self.rq.get("why_questions") or []
        self.assertTrue(questions and why_questions)

        for q in questions + why_questions:
            self.assertTrue(
                str(q.get("minimum_writeback_contract") or "").strip(),
                f"{q.get('id')} 缺少 minimum_writeback_contract",
            )
            self.assertNotIn("acceptance", q, f"{q.get('id')} 仍带 acceptance 字段")

    def test_completion_semantics_is_declared_explicitly(self) -> None:
        semantics = (self.rq.get("meta") or {}).get("completion_semantics") or {}
        self.assertEqual(semantics.get("linked_kn_or_why_means"), "已有材料")
        self.assertEqual(semantics.get("linked_kn_or_why_does_not_mean"), "已完成")
        self.assertIn("人工复核", str(semantics.get("completion_is") or ""))
        self.assertIn("已覆盖", semantics.get("forbidden_phrasing_when_describing_question_state") or [])
        self.assertIn("已有材料", semantics.get("required_phrasing_when_describing_question_state") or [])

    def test_minimum_writeback_contract_does_not_claim_completion(self) -> None:
        for q in (self.rq.get("questions") or []) + (self.rq.get("why_questions") or []):
            contract = str(q.get("minimum_writeback_contract") or "")
            for forbidden in ("已完成", "已覆盖", "已回答"):
                self.assertNotIn(forbidden, contract, f"{q.get('id')} 的回填最低条件不得声称完成")

    def test_rendered_question_tree_uses_material_wording(self) -> None:
        import render  # 模块级无副作用；build() 只在 __main__ 下执行

        with tempfile.TemporaryDirectory() as tmp:
            render.write_research_tree(tmp)
            text = (Path(tmp) / "研究问题树.md").read_text(encoding="utf-8")

        # “已有材料”应作为问题状态标记出现；“已覆盖”只可出现在否定说明里，不得作为状态标记。
        self.assertIn("[已有材料: ", text)
        self.assertNotIn("[已覆盖", text)
        self.assertNotIn("已覆盖的", text)
        self.assertIn("不等于问题已回答或已完成", text)
        self.assertIsNone(re.search(r"^\s*acceptance\s*:", text, flags=re.M))

    def test_workpack_declares_zero_architecture_budget(self) -> None:
        workpack = yaml.safe_load((ROOT / "docs" / "control" / "ACTIVE_WORKPACK.yaml").read_text(encoding="utf-8"))
        budget = workpack["architecture_budget"]
        self.assertEqual(budget["new_relation_types"], [])
        self.assertEqual(budget["new_top_level_systems"], [])
        self.assertEqual(budget["new_schema_fields"], [])
        self.assertEqual(budget["new_engines"], [])
        self.assertEqual(workpack["workpack"]["id"], "OM-PHYS-001")
        self.assertEqual(
            workpack["completion_semantics"]["forbidden_phrasing"],
            ["已覆盖", "已完成", "已回答"],
        )
        self.assertTrue(os.path.exists(ROOT / "docs" / "research" / "光模块知识体系-历史综合-v1.30.md"))
        self.assertFalse(os.path.exists(ROOT / "docs" / "research" / "光模块知识体系-当前任务控制文稿.md"))


if __name__ == "__main__":
    unittest.main()
