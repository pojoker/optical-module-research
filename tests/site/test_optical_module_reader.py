from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "out" / "光模块知识体系"
SITE_PAGES = ROOT / "site" / "optical-module" / "pages.yaml"


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


if __name__ == "__main__":
    unittest.main()
