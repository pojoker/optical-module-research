from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "out" / "光模块知识体系"
SITE_PAGES = ROOT / "site" / "optical-module" / "pages.yaml"
SITE_SECTIONS = ROOT / "site" / "optical-module" / "sections"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag == "img" and values.get("src"):
            self.images.append(values["src"] or "")


class OpticalModuleReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = yaml.safe_load((OUTPUT / "build-manifest.yaml").read_text(encoding="utf-8"))
        cls.pages: dict[str, PageParser] = {}
        for filename in cls.manifest["pages"]:
            parser = PageParser()
            parser.feed((OUTPUT / filename).read_text(encoding="utf-8"))
            parser.close()
            cls.pages[filename] = parser

    def test_manifest_declares_reader_only_build(self) -> None:
        self.assertFalse(self.manifest["canonical_write"])
        page_config = yaml.safe_load(SITE_PAGES.read_text(encoding="utf-8"))
        self.assertEqual(self.manifest["page_count"], len(page_config["pages"]) + 1)
        section_ids = {
            section_id
            for page in page_config["pages"]
            for section_id in page.get("sections", [])
        }
        self.assertEqual(self.manifest["section_count"], len(section_ids))

    def test_research_page_has_promoted_foundation_golden_path(self) -> None:
        research_text = (OUTPUT / "06-research.html").read_text(encoding="utf-8")
        self.assertIn('id="candidate-foundation"', research_text)
        for token in ["KN008", "KN009", "KN010"]:
            self.assertIn(token, research_text)

        section_start = research_text.index('id="candidate-foundation"')
        section_end = research_text.index("</section>", section_start)
        candidate_section = research_text[section_start:section_end]
        self.assertIn("用户明确批准", candidate_section)
        self.assertNotIn("atomic_all_or_none", candidate_section)
        self.assertNotIn("canonical_write=3", candidate_section)
        self.assertNotIn("user_decision=approved", candidate_section)
        self.assertNotIn("KN011", candidate_section)

    def test_decision_dossier_is_built_as_conditional_product(self) -> None:
        text = (OUTPUT / "07-decision-dossier.html").read_text(encoding="utf-8")
        self.assertIn('id="decision-dossier-01"', text)
        self.assertIn("qualitative_boundary_map_no_numeric_system_model", text)
        for token in [
            "FP-RETIMED",
            "FP-LPO",
            "NPO-CONDITIONAL",
            "CPO-CONDITIONAL",
            "R01",
            "R02",
            "R03",
            "R04",
            "R05",
        ]:
            self.assertIn(token, text)
        self.assertIn("没有无条件冠军", text)
        self.assertIn('href="08-concept-primer.html#placement-primer"', text)

    def test_concept_primer_explains_placement_and_pareto(self) -> None:
        text = (OUTPUT / "08-concept-primer.html").read_text(encoding="utf-8")
        for token in [
            'id="placement-primer"',
            'id="decision-glossary"',
            "Front-panel",
            "NPO / OBO",
            "CPO",
            "Pareto frontier",
            "Active constraint",
            "Failure domain",
            "MTTR",
            "TCO",
            "UNKNOWN",
        ]:
            self.assertIn(token, text)

    def test_page_ids_are_unique(self) -> None:
        for filename, parser in self.pages.items():
            self.assertEqual(len(parser.ids), len(set(parser.ids)), filename)

    def test_local_html_links_and_anchors_resolve(self) -> None:
        for filename, parser in self.pages.items():
            for href in parser.hrefs:
                if href.startswith(("http://", "https://", "javascript:")):
                    continue
                path_part, _, anchor = href.partition("#")
                target_name = unquote(path_part) if path_part else filename
                target = (OUTPUT / target_name).resolve()
                if target.suffix == ".html":
                    self.assertTrue(target.exists(), f"{filename}: missing {href}")
                    if anchor:
                        target_parser = self.pages.get(target.name)
                        self.assertIsNotNone(target_parser, f"{filename}: unknown page {target.name}")
                        self.assertIn(anchor, target_parser.ids, f"{filename}: missing anchor {href}")

    def test_shared_assets_exist(self) -> None:
        for asset in ["content.css", "site-shell.css", "site.js"]:
            self.assertTrue((OUTPUT / "assets" / asset).is_file(), asset)
            self.assertRegex(self.manifest["asset_versions"][asset], r"^[0-9a-f]{12}$")

    def test_pages_use_versioned_shared_assets(self) -> None:
        for filename in self.manifest["pages"]:
            text = (OUTPUT / filename).read_text(encoding="utf-8")
            for asset, version in self.manifest["asset_versions"].items():
                self.assertIn(f"assets/{asset}?v={version}", text, filename)

    def test_generated_text_has_no_trailing_whitespace(self) -> None:
        for path in OUTPUT.rglob("*"):
            if not path.is_file() or path.suffix not in {".html", ".css", ".js", ".svg", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"), str(path))
            for line_number, line in enumerate(text.splitlines(), start=1):
                self.assertEqual(line, line.rstrip(), f"{path}:{line_number}")

    def test_reference_figures_resolve(self) -> None:
        seen: set[str] = set()
        for filename, parser in self.pages.items():
            for source in parser.images:
                if source.startswith(("http://", "https://")):
                    continue
                seen.add(source)
                self.assertTrue((OUTPUT / unquote(source)).is_file(), f"{filename}: missing {source}")
        self.assertEqual(len(seen), 5)
        self.assertIn("assets/figures/05-placement-primer.svg", seen)

    def test_foundation_has_physical_gallery(self) -> None:
        parser = self.pages["01-foundation.html"]
        remote_images = [source for source in parser.images if source.startswith("https://")]
        self.assertIn("physical-gallery", parser.ids)
        self.assertGreaterEqual(len(remote_images), 8)

    def test_demand_page_has_constraint_cascade(self) -> None:
        parser = self.pages["02-demand.html"]
        for section_id in ["demand", "scaling", "constraints", "cascade"]:
            self.assertIn(section_id, parser.ids)

    def test_routes_page_explains_link_requirements(self) -> None:
        parser = self.pages["03-routes.html"]
        self.assertIn("link-requirements", parser.ids)

    def test_each_module_has_one_active_global_nav_item(self) -> None:
        for filename in self.manifest["pages"]:
            text = (OUTPUT / filename).read_text(encoding="utf-8")
            self.assertEqual(text.count('class="active"'), 1, filename)

    def test_status_section_semantics_and_evidence_tiers(self) -> None:
        status_path = SITE_SECTIONS / "status.html"
        self.assertTrue(status_path.is_file(), "status.html must exist")
        text = status_path.read_text(encoding="utf-8")

        # Verify section ID and data certainty
        self.assertIn('id="status"', text)
        self.assertIn('data-certainty="open"', text)

        # Verify four certainty/knowledge reading tiers are explicitly explained
        for token in ["事实（Fact）", "派生（Derived）", "候选（Candidate）", "UNKNOWN（未知"]:
            self.assertIn(token, text)

        # Verify four "cannot infer" boundaries are explicitly articulated
        self.assertIn("Capability Overlap", text)
        self.assertIn("不能推出供货或路线能力", text)
        self.assertIn("Source Slot", text)
        self.assertIn("不能推出研究结论覆盖", text)
        self.assertIn("Reviewed Event", text)
        self.assertIn("不能推出独立证实或真实出货", text)
        self.assertIn("Shipment Observation", text)
        self.assertIn("不能推出横向比较或市场份额", text)

        # Verify no state machine or automated control plane keywords
        self.assertNotIn("auto-close", text)
        self.assertNotIn("auto-reopen", text)
        self.assertNotIn("snapshot_lineage", text)
        self.assertNotIn("receipt", text)

    def test_audit_section_semantics_and_boundaries(self) -> None:
        audit_path = SITE_SECTIONS / "audit.html"
        self.assertTrue(audit_path.is_file(), "audit.html must exist")
        text = audit_path.read_text(encoding="utf-8")

        # Verify section ID and data certainty
        self.assertIn('id="audit"', text)
        self.assertIn('data-certainty="open"', text)

        # Verify distinction between what can be answered and what cannot be answered
        self.assertIn("已经连起来的内容", text)
        self.assertIn("当前能回答什么", text)
        self.assertIn("仍然不能确定的内容", text)
        self.assertIn("当前不能回答与不可外推", text)

        # Verify four "cannot infer" boundaries
        self.assertIn("Capability Overlap", text)
        self.assertIn("Source Slot", text)
        self.assertIn("Reviewed Event", text)
        self.assertIn("Shipment Observation", text)
        self.assertIn("corroborated", text)

        # Verify audit hypotheses are not asserted as canonical facts
        self.assertIn("仅属审查契约输入", text)
        self.assertNotIn("H1已成立为事实", text)
        self.assertNotIn("H2已成立为事实", text)

        # Verify knowledge reading rules and canonical boundary
        self.assertIn("KN008–KN010", text)
        self.assertIn("KN011", text)
        self.assertIn("候选", text)
        self.assertIn("UNKNOWN", text)

        # Verify links to audit documents
        self.assertIn("data-quality-ablation-independent-review-brief.md", text)
        self.assertIn("kimi-data-quality-semantic-audit.md", text)
        self.assertIn("cursor-data-quality-contract-ablation-audit.md", text)
        self.assertIn("lights-out-remediation-outsourcing-plan.md", text)

    def test_site_contract_nine_pages_and_twenty_seven_sections(self) -> None:
        page_config = yaml.safe_load(SITE_PAGES.read_text(encoding="utf-8"))
        # 8 modular pages + 1 home page (index.html) = 9 pages
        pages = page_config["pages"]
        self.assertEqual(len(pages), 8, "Expected exactly 8 modular pages in pages.yaml")
        total_pages = len(pages) + 1
        self.assertEqual(total_pages, 9, "Total reader site must have exactly 9 pages (no 10th page)")

        # Total sections across all modular pages must be exactly 27
        all_sections = [sec for page in pages for sec in page.get("sections", [])]
        self.assertEqual(len(all_sections), 27, "Total section count must remain exactly 27")
        self.assertEqual(len(all_sections), len(set(all_sections)), "Section IDs must be strictly unique")

        # Confirm research page contains both status and audit sections
        research_page = next((p for p in pages if p["id"] == "research"), None)
        self.assertIsNotNone(research_page)
        self.assertEqual(
            research_page["sections"],
            ["status", "candidate-foundation", "questions", "sources", "audit"],
        )

    def test_modular_sections_build_cleanly(self) -> None:
        import sys

        sys.path.insert(0, str(ROOT / "tools" / "site"))
        import build_optical_module_site as site_builder

        config = site_builder.load_config()
        sections = site_builder.load_sections(config)
        self.assertEqual(len(sections), 27)

        pages = config["pages"]
        section_to_page = {
            section: page["file"] for page in pages for section in page["sections"]
        }
        research_page = next(p for p in pages if p["id"] == "research")
        body = "\n".join(
            site_builder.rewrite_links(sections[s_id], research_page, section_to_page)
            for s_id in research_page["sections"]
        )
        self.assertIn('id="status"', body)
        self.assertIn('id="audit"', body)
        self.assertIn("Capability Overlap", body)
        self.assertIn("Source Slot", body)
        self.assertIn("Reviewed Event", body)
        self.assertIn("Shipment Observation", body)
        self.assertIn("事实（Fact）", body)
        self.assertIn("派生（Derived）", body)
        self.assertIn("候选（Candidate）", body)
        self.assertIn("UNKNOWN", body)


if __name__ == "__main__":
    unittest.main()
