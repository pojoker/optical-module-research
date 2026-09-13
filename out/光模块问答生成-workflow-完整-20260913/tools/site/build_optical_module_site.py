#!/Users/jowang/miniconda3/bin/python3
"""Build the modular optical-module reader site.

This builder only reads research presentation fragments and writes the reader
artifact under out/光模块知识体系/. It never promotes or edits canonical YAML.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import shutil
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site" / "optical-module"
LEGACY_PAGE = ROOT / "out" / "光模块知识体系第一里程碑.html"
OUTPUT = ROOT / "out" / "光模块知识体系"
CANONICAL = ROOT / "knowledge.yaml"

SECTION_RE = re.compile(
    r'(?P<section><section class="section" id="(?P<id>[^"]+)"[^>]*>.*?</section>)',
    re.DOTALL,
)
STYLE_RE = re.compile(r"<style>(?P<style>.*?)</style>", re.DOTALL)
H2_RE = re.compile(r"<h2>(?P<title>.*?)</h2>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain_text(value: str) -> str:
    return html.unescape(TAG_RE.sub("", value)).strip()


def refresh_sections() -> None:
    source_text = LEGACY_PAGE.read_text(encoding="utf-8")
    matches = list(SECTION_RE.finditer(source_text))
    if len(matches) != 18:
        raise SystemExit(f"Expected 18 legacy sections, found {len(matches)}")

    section_dir = SOURCE / "sections"
    section_dir.mkdir(parents=True, exist_ok=True)
    for match in matches:
        section_id = match.group("id")
        (section_dir / f"{section_id}.html").write_text(
            match.group("section").strip() + "\n", encoding="utf-8"
        )

    style_match = STYLE_RE.search(source_text)
    if not style_match:
        raise SystemExit("Legacy page has no embedded style block")
    (SOURCE / "assets" / "content.css").write_text(
        style_match.group("style").strip() + "\n", encoding="utf-8"
    )


def load_config() -> dict:
    config = yaml.safe_load((SOURCE / "pages.yaml").read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not config.get("pages"):
        raise SystemExit("pages.yaml must define at least one page")
    return config


def load_sections(config: dict) -> dict[str, str]:
    required = {section for page in config["pages"] for section in page["sections"]}
    sections: dict[str, str] = {}
    for section_id in required:
        path = SOURCE / "sections" / f"{section_id}.html"
        if not path.exists():
            raise SystemExit(f"Missing section source: {path}")
        value = path.read_text(encoding="utf-8").strip()
        if f'id="{section_id}"' not in value:
            raise SystemExit(f"Section id mismatch in {path}")
        sections[section_id] = value
    return sections


def global_nav(pages: list[dict], active_id: str) -> str:
    links = [
        f'<a class="{"active" if active_id == "home" else ""}" href="index.html">总览</a>'
    ]
    for page in pages:
        active = "active" if page["id"] == active_id else ""
        links.append(f'<a class="{active}" href="{page["file"]}">{page["nav"]}</a>')
    return "".join(links)


def local_nav(section_ids: list[str], sections: dict[str, str]) -> str:
    links = []
    for section_id in section_ids:
        title_match = H2_RE.search(sections[section_id])
        title = plain_text(title_match.group("title")) if title_match else section_id
        links.append(f'<a href="#{section_id}">{title}</a>')
    return '<nav class="local-nav" aria-label="本页小节"><span>本页内容</span>' + "".join(links) + "</nav>"


def rewrite_links(fragment: str, current_page: dict, section_to_page: dict[str, str]) -> str:
    fragment = fragment.replace('href="../docs/', 'href="../../docs/')
    fragment = fragment.replace('href="../corpus/', 'href="../../corpus/')

    def replace_anchor(match: re.Match[str]) -> str:
        section_id = match.group(1)
        target_page = section_to_page.get(section_id)
        if not target_page or target_page == current_page["file"]:
            return match.group(0)
        return f'href="{target_page}#{section_id}"'

    return re.sub(r'href="#([A-Za-z0-9_-]+)"', replace_anchor, fragment)


def module_cards(pages: list[dict]) -> str:
    cards = []
    for page in pages:
        cards.append(
            f'''<a class="module-card" data-module="{page['id']}" href="{page['file']}">
  <div class="card-top"><span class="card-number">{page['number']}</span><span class="card-arrow">→</span></div>
  <h2>{page['nav']}</h2>
  <p>{page['description']}</p>
  <div class="card-question">回答：{page['question']}</div>
</a>'''
        )
    return "\n".join(cards)


def prev_next(pages: list[dict], index: int) -> str:
    previous = pages[index - 1] if index > 0 else None
    following = pages[index + 1] if index + 1 < len(pages) else None
    links = []
    if previous:
        links.append(f'<a href="{previous["file"]}"><small>← 上一模块</small><b>{previous["nav"]}</b></a>')
    else:
        links.append('<a href="index.html"><small>← 回到入口</small><b>知识体系总览</b></a>')
    if following:
        links.append(f'<a href="{following["file"]}"><small>下一模块 →</small><b>{following["nav"]}</b></a>')
    else:
        links.append('<a href="index.html"><small>完成阅读 →</small><b>回到知识体系总览</b></a>')
    return '<nav class="prev-next" aria-label="模块翻页">' + "".join(links) + "</nav>"


def render(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", result)))
    if leftovers:
        raise SystemExit(f"Unresolved template tokens: {leftovers}")
    return "\n".join(line.rstrip() for line in result.splitlines()) + "\n"


def build() -> None:
    config = load_config()
    pages = config["pages"]
    site = config["site"]
    sections = load_sections(config)
    section_to_page = {section: page["file"] for page in pages for section in page["sections"]}
    template = (SOURCE / "templates" / "page.html").read_text(encoding="utf-8")
    asset_versions = {
        asset: digest(SOURCE / "assets" / asset)[:12]
        for asset in ["content.css", "site-shell.css", "site.js"]
    }
    asset_tokens = {
        "CONTENT_CSS_VERSION": asset_versions["content.css"],
        "SITE_SHELL_CSS_VERSION": asset_versions["site-shell.css"],
        "SITE_JS_VERSION": asset_versions["site.js"],
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "assets").mkdir(parents=True, exist_ok=True)
    for asset in ["content.css", "site-shell.css", "site.js"]:
        shutil.copy2(SOURCE / "assets" / asset, OUTPUT / "assets" / asset)
    shutil.copytree(
        SOURCE / "assets" / "figures",
        OUTPUT / "assets" / "figures",
        dirs_exist_ok=True,
    )

    home_body = (SOURCE / "home.html").read_text(encoding="utf-8").replace(
        "{{MODULE_CARDS}}", module_cards(pages)
    )
    home = render(
        template,
        {
            "META_DESCRIPTION": "从基础结构、提速需求、技术路线、对象案例、公司投影到研究台账的模块化光模块知识体系。",
            "PAGE_TITLE": "总览",
            "PAGE_ID": "home",
            "PAGE_NUMBER": "00",
            "PAGE_KICKER": "Overview · 从问题进入知识体系",
            "PAGE_DESCRIPTION": "不再从头滚到尾。先选择你要回答的问题，再进入可以独立阅读、独立复核的主题模块。",
            "GLOBAL_NAV": global_nav(pages, "home"),
            "LOCAL_NAV": "",
            "BODY": home_body,
            "PREV_NEXT": "",
            "EDITION": site["edition"],
            **asset_tokens,
        },
    )
    (OUTPUT / "index.html").write_text(home, encoding="utf-8")

    for index, page in enumerate(pages):
        body = "\n".join(
            rewrite_links(sections[section_id], page, section_to_page)
            for section_id in page["sections"]
        )
        document = render(
            template,
            {
                "META_DESCRIPTION": page["description"],
                "PAGE_TITLE": page["title"],
                "PAGE_ID": page["id"],
                "PAGE_NUMBER": page["number"],
                "PAGE_KICKER": page["question"],
                "PAGE_DESCRIPTION": page["description"],
                "GLOBAL_NAV": global_nav(pages, page["id"]),
                "LOCAL_NAV": local_nav(page["sections"], sections),
                "BODY": body,
                "PREV_NEXT": prev_next(pages, index),
                "EDITION": site["edition"],
                **asset_tokens,
            },
        )
        (OUTPUT / page["file"]).write_text(document, encoding="utf-8")

    manifest = {
        "schema_version": "optical_module_reader_manifest_v1",
        "source": "site/optical-module",
        "output": "out/光模块知识体系",
        "page_count": len(pages) + 1,
        "section_count": len(sections),
        "canonical_write": False,
        "asset_versions": asset_versions,
        "pages": ["index.html", *[page["file"] for page in pages]],
    }
    (OUTPUT / "build-manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh-sections",
        action="store_true",
        help="Overwrite modular section sources from the legacy single page.",
    )
    args = parser.parse_args()
    canonical_before = digest(CANONICAL)
    if args.refresh_sections:
        refresh_sections()
    build()
    canonical_after = digest(CANONICAL)
    if canonical_before != canonical_after:
        raise SystemExit("Canonical knowledge.yaml changed during a reader-only build")
    print(
        yaml.safe_dump(
            {
                "status": "PASS",
                "output": str(OUTPUT),
                "canonical_unchanged": True,
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
    )


if __name__ == "__main__":
    main()
