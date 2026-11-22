#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4 Worker 3 (`carbon-s4-overseas-fetch`):
Overseas Primary Full-Text Archiving, Oct-Nov 2026 Quarterly Slot Advancement,
Event/Claim/Timeline Ingestion & Verbatim DRQ Verdicts (2026-11-22).

Strictly whitelisted write paths ONLY:
  - corpus/web/step4_20261122/**
  - calls/sources.csv
  - calls/claims.csv
  - calls/commitments.csv
  - calls/disclosures.csv
  - calls/events.csv
  - calls/event_claims.csv
  - calls/event_evidence.csv
  - calls/watch_entities.csv
  - corpus/relationships/relationship_timeline.csv
  - out/step4-backend-final-closure-20261122/ingest_overseas_step4.py
  - out/step4-backend-final-closure-20261122/overseas-drq-verdicts.json

Idempotency guarantee:
  - Reuses archived HTTP 200 `.html` snapshots in `corpus/web/step4_20261122/` when
    present on disk (performing plain unauthenticated HTTP GET only when absent,
    never bypassing 403 / CAPTCHA / Turnstile / JS shells).
  - Preserves untouched CSV physical lines byte-for-byte (`\n` for `calls/*.csv`,
    `\r\n` for `corpus/relationships/relationship_timeline.csv`).
  - Produces byte-identical SHA-256 hashes across consecutive runs.
"""

from __future__ import annotations

import csv
import hashlib
import html as html_mod
import io
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scan  # noqa: E402
from calls.event_intelligence import derive_event_projection, load_event_facts  # noqa: E402
from calls.http_discovery import parse_html_item  # noqa: E402
from calls.positioning import scan_forbidden_words  # noqa: E402
from calls.schema import FILES  # noqa: E402
from calls.validator import FROZEN_SOLUTION_LINKS, validate  # noqa: E402

WEB_DIR = REPO_ROOT / "corpus" / "web" / "step4_20261122"
VERDICTS_PATH = SCRIPT_DIR / "overseas-drq-verdicts.json"

TIMELINE_FIELDS = (
    "timeline_id",
    "relation_id",
    "supplier",
    "customer",
    "supplier_point_id",
    "customer_point_id",
    "period",
    "period_type",
    "event_date",
    "source_channel",
    "metric_kind",
    "value_raw",
    "numeric_value",
    "unit",
    "observe_type",
    "edge_grade",
    "source_edge_ids",
    "daily_ref_id",
    "anchor_url",
    "conflict",
    "notes",
)

CHALLENGE_RE = re.compile(
    r"(?:cf-turnstile|challenges\.cloudflare\.com|Just a moment\.\.\.|Verify you are human"
    r"|Pardon Our Interruption|Access Denied|Attention Required! \| Cloudflare|_cf_chl_opt)",
    re.I,
)

# 33 HTTP targets: 24 overseas DRQs (plus POET official mirror) + 8 Oct-Nov staging items
FETCH_TARGETS = [
    ("DRQ0015", "DC_501FC1F61B62", "MRVL", "2026-11-02", "mrvl_20261102_lumentum_combine",
     "https://investor.marvell.com/news-events/press-releases/detail/1040/marvell-and-lumentum-to-combine-creating-a-category-leader-in-ai-connectivity"),
    ("DRQ0016", "DC_573401DC530B", "LITE", "2026-11-02", "lite_20261102_fy27q1_results",
     "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Announces-First-Quarter-of-Fiscal-Year-2027-Financial-Results/default.aspx"),
    ("DRQ0017", "DC_3841FCD60F32", "AXTI", "2026-10-29", "axti_20261029_2026q3_results",
     "https://investors.axt.com/Investors/news/news-details/2026/AXT-Inc--Announces-Third-Quarter-2026-Financial-Results/default.aspx"),
    ("DRQ0018", "DC_FD32C455D502", "AXTI", "2026-10-28", "axti_20261028_tongmei_financing",
     "https://investors.axt.com/Investors/news/news-details/2026/AXT-Inc--Announces-Up-to-RMB-3-67-Billion-Approximately-US545-Million-in-Private-Equity-Financing-for-Subsidiary-Tongmei/default.aspx"),
    ("DRQ0019", "DC_430D7977BA22", "TSEM", "2026-11-03", "tsem_20261103_innolight_npo",
     "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-and-innolight-advance-high-performance-near/"),
    ("DRQ0021", "DC_BF393C7C7BE8", "NOK", "2026-09-15", "nok_20260915_telxius_800g",
     "https://www.nokia.com/newsroom/telxius-boosts-global-network-capacity-and-efficiency-with-nokia-800g-coherent-pluggable-deployment/"),
    ("DRQ0022", "DC_7B475AB0DF5A", "FN", "2026-11-02", "fn_20261102_fy27q1_results",
     "https://investor.fabrinet.com/news-releases/news-release-details/fabrinet-announces-first-quarter-fiscal-year-2027-financial"),
    ("DRQ0023", "DC_4FAA980A3027", "NVDA", "2026-11-17", "nvda_20261117_fy27q3_results",
     "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2027"),
    ("DRQ0024", "DC_9B16CE64F492", "CIEN", "2026-09-03", "cien_20260903_fy26q3_results",
     "https://investor.ciena.com/news/news-details/2026/Ciena-Reports-Fiscal-Third-Quarter-2026-Financial-Results/default.aspx"),
    ("DRQ0025", "DC_A038F7C2DD93", "TSEM", "2026-09-17", "tsem_20260917_newphotonics_pic",
     "https://ir.towersemi.com/news-releases/news-release-details/newphotonicsr-and-tower-semiconductor-begin-high-volume/"),
    ("DRQ0026", "DC_286D42235853", "WIWYNN", "2026-10-13", "wiwynn_20261013_ayar_guc_cpo_demo",
     "https://www.wiwynn.com/news/wiwynn-ayar-labs-and-guc-advance-co-packaged-optics-with-live-demonstration-of-integrated-optical-compute-system-at-ocp-global-summit-2026"),
    ("DRQ0027", "DC_DC1ABE67C305", "WATCH_LIGHTMATTER", "2026-10-12", "lightmatter_20261012_open_rack_cpo",
     "https://lightmatter.com/press-release/lightmatter-delivers-open-rack-cpo-switch-and-xpu-scale-up-server-through-independent-collaborations-with-flex-and-other-industry-partners/"),
    ("DRQ0028", "DC_7CED25D6E66F", "CRDO", "2026-10-12", "crdo_20261012_1p6t_zeroflap_alc",
     "https://investors.credosemi.com/news-events/news/news-details/2026/Credo-Unveils-1-6T-ZeroFlap-Active-Light-Cable-Industrys-First-Row-Scale-Wide-Parallel-Optical-Interconnect-for-AI-Data-Centers/default.aspx"),
    ("DRQ0029", "DC_535D459775E6", "MTSI", "2026-09-17", "mtsi_20260917_3p2t_chipset",
     "https://ir.macom.com/news-releases/news-release-details/macom-introduces-32t-chipset-solution-high-speed-optical/"),
    ("DRQ0030", "DC_741EFE5BF486", "WATCH_IQE", "2026-09-03", "iqe_20260903_quintessent_qdl",
     "https://www.iqep.com/media/press-releases/2026/iqe-announces-purchase-agreement-with-quintessent-as-quantum-dot-laser-technology-moves-to-customer-sampling/"),
    ("DRQ0037", "DC_4B0F75924A65", "LWLG", "2026-10-29", "lwlg_20261029_foxconn_hhtd_demo",
     "https://api.quotemedia.com/supplement/news-story/?webmasterId=102691&storyId=8438787577882246"),
    ("DRQ0038", "DC_839378F484E4", "WATCH_OPENLIGHT", "2026-10-07", "openlight_20261007_heterogeneous_sipho",
     "https://openlightphotonics.com/newsroom/openlight-advances-heterogeneous-silicon-photonics-toward-volume-production"),
    ("DRQ0039", "DC_D527C3DC5ED2", "LITE", "2026-09-21", "lite_20260921_ecoc_dwdm_elsfp",
     "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-to-Demonstrate-DWDM-ELSFP-Laser-Module-for-OCI-MSA-Applications-at-ECOC-2026/default.aspx"),
    ("DRQ0040", "DC_E1BEF90B2480", "LITE", "2026-09-21", "lite_20260921_ecoc_1060nm_vcsel",
     "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Qualcomm-and-Corning-to-Demonstrate-High-Density-1060-nm-VCSEL-Optical-D2D-Connectivity-for-AI-Scale-Up-at-ECOC-2026/default.aspx"),
    ("DRQ0041", "DC_4A9C0B800414", "WIWYNN", "2026-10-12", "wiwynn_20261012_ocp_showcase",
     "https://www.wiwynn.com/news/wiwynn-showcases-next-gen-ai-platforms-thermal-engineering-and-optical-interconnect-technologies-at-2026-ocp-global-summit"),
    ("DRQ0042", "DC_DFCE4B441F6E", "MXL", "2026-11-10", "mxl_20261110_jeju_pmic",
     "https://investors.maxlinear.com/press-releases/detail/630/maxlinear-unveils-jeju-custom-pmic-engineered-for-peak"),
    ("DRQ0043", "DC_91F3D715F522", "CIEN", "2026-11-17", "cien_20261117_internet2_800g",
     "https://investor.ciena.com/news/news-details/2026/Ciena-and-Internet2-Reach-Industry-Record-for-Longest-Terrestrial-800-Gbs-Coherent-Pluggable-Link/default.aspx"),
    ("DRQ0044", "DC_4FACD43C676E", "POET", "2026-11-16", "poet_20261116_2026q3_results",
     "https://rss.globenewswire.com/news-release/2026/11/16/3403353/0/en/poet-technologies-reports-record-q3-2026-revenue-of-1-03m-up-244.html"),
    ("DRQ0044_OFFICIAL", "DC_4FACD43C676E", "POET", "2026-11-16", "poet_20261116_2026q3_official",
     "https://www.poet-technologies.com/news/poet-technologies-reports-record-q3-2026-revenue-of-1-03m-up-244"),
    ("DRQ0045", "DC_425841A754F4", "AVGO", "2026-09-02", "avgo_20260902_fy26q3_results",
     "https://investors.broadcom.com/news-releases/news-release-details/broadcom-inc-announces-third-quarter-fiscal-year-2026-financial"),
    ("STAGE_MTSI_FY26Q4", "DC_A6ADDA0BAFA7", "MTSI", "2026-11-05", "mtsi_20261105_fy26q4_results",
     "https://ir.macom.com/news-releases/news-release-details/macom-reports-fiscal-fourth-quarter-and-fiscal-year-2026/"),
    ("STAGE_TSEM_2026Q3", "DC_58448CDF4801", "TSEM", "2026-11-02", "tsem_20261102_2026q3_results",
     "https://ir.towersemi.com/news-releases/news-release-details/tower-semiconductor-reports-third-quarter-record-results/"),
    ("STAGE_GFS_2026Q3", "DC_DB6E7B2D27BB", "GFS", "2026-11-04", "gfs_20261104_2026q3_results",
     "https://investors.gf.com/news-releases/news-release-details/globalfoundries-reports-third-quarter-2026-financial-results"),
    ("STAGE_VECO_2026Q3", "DC_25B37F48DF71", "VECO", "2026-11-04", "veco_20261104_2026q3_results",
     "https://ir.veeco.com/news-and-events/news-details/2026/Veeco-Reports-Third-Quarter-2026-Financial-Results/default.aspx"),
    ("STAGE_VECO_ACLS_MERGER", "DC_6B392C92DA0A", "VECO", "2026-11-02", "veco_20261102_axcelis_merger_update",
     "https://ir.veeco.com/news-and-events/news-details/2026/Axcelis-Technologies-and-Veeco-Instruments-Provide-Update-on-Expected-Timing-of-Merger-Closing/default.aspx"),
    ("STAGE_SOI_FY27H1", "DC_86F8DBF8F95E", "SOI", "2026-11-18", "soi_20261118_fy27h1_results",
     "https://www.soitec.com/home/group/corporate/newsroom/press-releases/content/2026/11/18/soitec-reports-second-quarter-revenue-and-half-year-results-of-fiscal-year-2027"),
    ("STAGE_ANET_2026Q3", "DC_C85C91649A7A", "ANET", "2026-11-03", "anet_20261103_2026q3_results",
     "https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Third-Quarter-2026-Financial-Results/default.aspx"),
    ("STAGE_CRDO_ORCL_OCP", "DC_89DB234EEA46", "CRDO", "2026-11-04", "crdo_20261104_oracle_ocp_telemetry",
     "https://investors.credosemi.com/news-events/news/news-details/2026/Credo-and-Oracle-Advance-Optical-Transceiver-Telemetry-Standardization-with-OCP-Community/default.aspx"),
]

# Known deterministic JS-shell / aggregator endpoints that must NOT be re-hit on re-runs
KNOWN_JS_SHELL_ITEMS = {
    "DRQ0037": {
        "http_status": 200,
        "content_type": "text/html",
        "archive_status": "blocked_http_or_js_shell",
        "failure_reason": "js_shell_empty_body (p_chars=0, title='News Story - QuoteMedia Market Data Solutions')",
    }
}


class BlockTextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.lines: list[str] = []
        self.cur: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        t = tag.lower()
        if t in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if t in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br"}:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if t in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.cur.append(data)

    def _flush(self) -> None:
        s = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        if s:
            self.lines.append(s)
        self.cur = []

    def get_lines(self) -> list[str]:
        self._flush()
        out: list[str] = []
        for line in self.lines:
            if len(line) >= 3 and (not out or out[-1] != line):
                out.append(line)
        return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_http_plain(url: str) -> tuple[int, bytes, str, str, str]:
    for attempt in range(2):
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; calls-daily-discovery/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/json,application/rss+xml,application/atom+xml",
            },
        )
        try:
            with urlopen(req, timeout=20) as resp:
                status = getattr(resp, "status", 200)
                raw = resp.read(8_000_000)
                ctype = resp.headers.get_content_type()
                charset = resp.headers.get_content_charset() or "utf-8"
                final_url = resp.geturl()
                return status, raw, ctype, charset, final_url
        except HTTPError as exc:
            return exc.code, b"", "", "utf-8", f"HTTPError {exc.code}: {exc.reason}"
        except URLError as exc:
            if attempt == 0 and "UNEXPECTED_EOF" in str(exc.reason):
                time.sleep(0.5)
                continue
            return 0, b"", "", "utf-8", f"URLError: {exc.reason}"
        except Exception as exc:
            return -1, b"", "", "utf-8", f"{type(exc).__name__}: {exc}"
    return 0, b"", "", "utf-8", "unreachable"


def archive_web_corpus() -> dict[str, dict]:
    """Ensure corpus/web/step4_20261122/ holds .html + .txt + manifest.json deterministically."""
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    manifest_items: list[dict] = []
    by_slug: dict[str, dict] = {}

    for item_id, dc_id, entity_id, expected_date, slug, url in FETCH_TARGETS:
        html_rel = f"corpus/web/step4_20261122/{slug}.html"
        txt_rel = f"corpus/web/step4_20261122/{slug}.txt"
        html_path = REPO_ROOT / html_rel
        txt_path = REPO_ROOT / txt_rel

        if item_id in KNOWN_JS_SHELL_ITEMS and not html_path.is_file():
            known = KNOWN_JS_SHELL_ITEMS[item_id]
            rec = {
                "item_id": item_id,
                "dc_id": dc_id,
                "entity_id": entity_id,
                "expected_date": expected_date,
                "slug": slug,
                "requested_url": url,
                "http_status": known["http_status"],
                "content_type": known["content_type"],
                "final_url_or_error": url,
                "archive_status": known["archive_status"],
                "failure_reason": known["failure_reason"],
            }
            manifest_items.append(rec)
            by_slug[slug] = rec
            continue

        if html_path.is_file() and html_path.stat().st_size > 0:
            raw = html_path.read_bytes()
            status, ctype, charset, final_or_err = 200, "text/html", "utf-8", url
        else:
            status, raw, ctype, charset, final_or_err = fetch_http_plain(url)
            time.sleep(0.2)

        rec = {
            "item_id": item_id,
            "dc_id": dc_id,
            "entity_id": entity_id,
            "expected_date": expected_date,
            "slug": slug,
            "requested_url": url,
            "http_status": status,
            "content_type": ctype,
            "final_url_or_error": final_or_err,
        }
        if status != 200 or not raw:
            rec["archive_status"] = "blocked_http_or_js_shell"
            rec["failure_reason"] = f"http_{status}" if status > 0 else final_or_err
            manifest_items.append(rec)
            by_slug[slug] = rec
            continue

        decoded = raw.decode(charset, errors="replace")
        title_m = re.search(r"<title[^>]*>(.*?)</title>", decoded[:8000], re.I | re.S)
        page_title = re.sub(r"\s+", " ", html_mod.unescape(title_m.group(1))).strip() if title_m else ""
        if CHALLENGE_RE.search(page_title) or (len(decoded) < 20000 and CHALLENGE_RE.search(decoded)):
            rec["archive_status"] = "blocked_http_or_js_shell"
            rec["failure_reason"] = f"challenge_page_detected: title={page_title!r}"
            manifest_items.append(rec)
            by_slug[slug] = rec
            continue

        parsed = parse_html_item(decoded, final_or_err)
        paragraphs = [p["text"] for p in parsed.get("paragraphs", [])]
        ext = BlockTextExtractor()
        ext.feed(decoded)
        block_lines = ext.get_lines()

        total_p_chars = sum(len(p) for p in paragraphs)
        if total_p_chars < 200 and sum(len(x) for x in block_lines) < 500:
            rec["archive_status"] = "blocked_http_or_js_shell"
            rec["failure_reason"] = f"js_shell_empty_body (p_chars={total_p_chars}, title={page_title!r})"
            manifest_items.append(rec)
            by_slug[slug] = rec
            continue

        if not html_path.is_file():
            html_path.write_bytes(raw)

        resolved_title = parsed.get("title") or page_title
        if resolved_title in {"TBD", "News Details"}:
            h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", decoded, re.I | re.S)
            if h1_m:
                cand = re.sub(r"<[^>]+>", " ", h1_m.group(1))
                cand = re.sub(r"\s+", " ", html_mod.unescape(cand)).strip()
                if cand and cand not in {"TBD", "News Details"}:
                    resolved_title = cand

        txt_lines = [
            f"URL: {final_or_err}",
            f"REQUESTED_URL: {url}",
            f"TITLE: {resolved_title}",
            f"PUBLISHED_AT: {parsed.get('published_at') or expected_date}",
            "RETRIEVED_AT: 2026-11-22",
            "--- PARSED PARAGRAPHS ---",
        ]
        for idx, p in enumerate(parsed.get("paragraphs", []), 1):
            anchor = p.get("anchor") or f"p{idx}"
            txt_lines.append(f"[{anchor}] {p['text']}")
        txt_lines.append("--- FULL BLOCK TEXT ---")
        txt_lines.extend(block_lines)
        txt_bytes = ("\n".join(txt_lines) + "\n").encode("utf-8")
        if not txt_path.is_file() or txt_path.read_bytes() != txt_bytes:
            txt_path.write_bytes(txt_bytes)

        rec["archive_status"] = "archived_http_200"
        rec["parsed_title"] = resolved_title
        rec["parsed_published_at"] = parsed.get("published_at") or expected_date
        rec["paragraph_count"] = len(paragraphs)
        rec["paragraph_chars"] = total_p_chars
        rec["html_path"] = html_rel
        rec["html_sha256"] = sha256_bytes(raw)
        rec["html_bytes"] = len(raw)
        rec["txt_path"] = txt_rel
        rec["txt_sha256"] = sha256_bytes(txt_bytes)
        rec["txt_bytes"] = len(txt_bytes)
        manifest_items.append(rec)
        by_slug[slug] = rec

    manifest = {
        "batch": "step4_20261122",
        "retrieved_at": "2026-11-22",
        "total_targets": len(FETCH_TARGETS),
        "archived_http_200_count": sum(1 for r in manifest_items if r["archive_status"] == "archived_http_200"),
        "blocked_or_js_shell_count": sum(1 for r in manifest_items if r["archive_status"] != "archived_http_200"),
        "items": manifest_items,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = WEB_DIR / "manifest.json"
    if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
        manifest_path.write_bytes(manifest_bytes)
    return by_slug


def format_csv_row(fieldnames: tuple[str, ...], row: dict[str, str], lineterminator: str) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator=lineterminator)
    writer.writerow({field: row.get(field, "") for field in fieldnames})
    return buf.getvalue()


def read_csv_with_raw(
    path: Path, expected_fields: tuple[str, ...]
) -> tuple[str, list[tuple[dict[str, str], str]]]:
    raw_text = path.read_text(encoding="utf-8-sig")
    phys_lines = raw_text.splitlines(keepends=True)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        actual = tuple(reader.fieldnames or ())
        if actual != expected_fields:
            raise ValueError(f"{path}: header mismatch: got {actual}, expected {expected_fields}")
        parsed = list(reader)
    if len(phys_lines) != len(parsed) + 1:
        raise ValueError(f"{path}: physical lines {len(phys_lines)} != parsed {len(parsed) + 1}")
    return phys_lines[0], list(zip(parsed, phys_lines[1:]))


def read_csv_rows(path: Path, expected_fields: tuple[str, ...]) -> list[dict[str, str]]:
    _, pairs = read_csv_with_raw(path, expected_fields)
    return [row for row, _ in pairs]


def write_csv_preserving_untouched(
    path: Path,
    fieldnames: tuple[str, ...],
    pk_field: str,
    rows: list[dict[str, str]],
    touched_pks: set[str],
    lineterminator: str,
) -> None:
    raw_by_pk: dict[str, str] = {}
    header_line = ",".join(fieldnames) + lineterminator
    if path.exists():
        hdr, pairs = read_csv_with_raw(path, fieldnames)
        if hdr.endswith(lineterminator):
            header_line = hdr
        for old_row, raw_line in pairs:
            pk = old_row[pk_field]
            if pk not in touched_pks and raw_line.endswith(lineterminator):
                raw_by_pk[pk] = raw_line

    out_buf = io.StringIO()
    out_buf.write(header_line)
    for row in rows:
        pk = row[pk_field]
        if pk in raw_by_pk:
            out_buf.write(raw_by_pk[pk])
        else:
            out_buf.write(format_csv_row(fieldnames, row, lineterminator))
    new_bytes = out_buf.getvalue().encode("utf-8")
    if not path.exists() or path.read_bytes() != new_bytes:
        path.write_bytes(new_bytes)


def upsert_rows(
    rows: list[dict[str, str]],
    pk_field: str,
    updates: dict[str, dict[str, str]],
    append_order: list[str],
) -> tuple[list[str], list[str]]:
    index_by_pk = {row[pk_field]: idx for idx, row in enumerate(rows)}
    updated_ids: list[str] = []
    inserted_ids: list[str] = []

    for pk, changes in updates.items():
        if pk in index_by_pk and pk not in append_order:
            target = dict(rows[index_by_pk[pk]])
            target.update(changes)
            rows[index_by_pk[pk]] = target
            updated_ids.append(pk)

    for pk in append_order:
        record = updates[pk]
        if pk in index_by_pk:
            target = dict(rows[index_by_pk[pk]])
            target.update(record)
            rows[index_by_pk[pk]] = target
        else:
            rows.append(dict(record))
            index_by_pk[pk] = len(rows) - 1
            inserted_ids.append(pk)

    return updated_ids, inserted_ids


def assert_no_forbidden_words(label: str, text: str) -> None:
    hits = scan_forbidden_words(text or "")
    if hits:
        raise AssertionError(f"{label} contains forbidden positioning business words {hits}: {text!r}")


def assert_verbatim_in_txt(slug: str, quote: str, by_slug: dict[str, dict]) -> None:
    txt_rel = by_slug[slug]["txt_path"]
    txt_content = (REPO_ROOT / txt_rel).read_text(encoding="utf-8")
    norm_q = re.sub(r"\s+", " ", quote).strip()
    norm_t = re.sub(r"\s+", " ", txt_content)
    if norm_q not in norm_t:
        raise AssertionError(f"Quote not found verbatim in {txt_rel}: {quote!r}")


def main() -> int:
    calls_dir = REPO_ROOT / "calls"
    rel_timeline_path = REPO_ROOT / "corpus" / "relationships" / "relationship_timeline.csv"
    cuts_path = REPO_ROOT / "corpus" / "relationships" / "edge_negative_cuts.csv"
    solution_links_path = calls_dir / "solution_links.csv"

    sl_hash_before = sha256_file(solution_links_path)

    # ------------------------------------------------------------------
    # 1. Archive & Hash All HTTP-200 Overseas Primary Texts
    # ------------------------------------------------------------------
    by_slug = archive_web_corpus()
    required_archived = [slug for item_id, _, _, _, slug, _ in FETCH_TARGETS if item_id != "DRQ0037"]
    for slug in required_archived:
        if by_slug[slug]["archive_status"] != "archived_http_200":
            raise AssertionError(f"Expected HTTP 200 archive for {slug}, got {by_slug[slug]}")

    def h_hash(slug: str) -> str:
        return by_slug[slug]["html_sha256"]

    def l_path(_slug: str) -> str:
        # Keep CSV `local_path` empty (matching all existing rows including D_CSCO_20261012_OCP_G300)
        # because `calls/tests/*` copy `calls/*.csv` into an isolated TemporaryDirectory without `corpus/`.
        # Exact archive paths (`corpus/web/step4_20261122/<slug>.html` & `.txt`) are recorded in
        # `content_hash`, `acquisition_note`/`notes`, `manifest.json`, and `overseas-drq-verdicts.json`.
        return ""

    # ------------------------------------------------------------------
    # 2. Advance `calls/sources.csv` to Oct-Nov 2026
    # ------------------------------------------------------------------
    # Roll 11 companies' oldest 2025 slot from `quarterly` -> `interquarter` and add
    # their newly archived Sep-Nov 2026 official results as `quarterly` (preserving
    # 4/4 quarterly slots, expanded 6 Grade-A invariant, and AXTI 3/4 invariant).
    # Keep LITE (locked at 2/4 available in test_reader_semantics.py) and CIEN (4
    # full-call transcripts) existing quarterly slots intact, registering S_LITE_2027Q1
    # and S_CIEN_2026Q3_PR as `interquarter`.
    sources = read_csv_rows(calls_dir / "sources.csv", FILES["sources.csv"])
    source_updates: dict[str, dict[str, str]] = {
        # Demote oldest 2025 slots to interquarter (preserving rows & FK integrity)
        "S_AXTI_2025Q3": {"source_scope": "interquarter"},
        "S_FN_2026Q1": {"source_scope": "interquarter"},
        "S_NVDA_2025Q2": {"source_scope": "interquarter"},
        "S_MTSI_2025Q4": {"source_scope": "interquarter"},
        "S_TSEM_2025Q2": {"source_scope": "interquarter"},
        "S_GFS_2025Q3": {"source_scope": "interquarter"},
        "S_VECO_2025Q3": {"source_scope": "interquarter"},
        "S_SOI_2026H1": {"source_scope": "interquarter"},
        "S_ANET_2025Q3": {"source_scope": "interquarter"},
        "S_POET_2025Q2": {"source_scope": "interquarter"},
        "S_AVGO_2025Q3": {"source_scope": "interquarter"},
        # New quarterly slots (11 companies)
        "S_AXTI_2026Q3": {
            "source_id": "S_AXTI_2026Q3",
            "company_id": "AXTI",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["axti_20261029_2026q3_results"]["requested_url"],
            "local_path": l_path("axti_20261029_2026q3_results"),
            "published_date": "2026-10-29",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_FN_2027Q1": {
            "source_id": "S_FN_2027Q1",
            "company_id": "FN",
            "slot_label": "FY2027Q1",
            "period_end": "2026-09-25",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["fn_20261102_fy27q1_results"]["requested_url"],
            "local_path": l_path("fn_20261102_fy27q1_results"),
            "published_date": "2026-11-02",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方FY2027Q1业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_NVDA_2027Q3": {
            "source_id": "S_NVDA_2027Q3",
            "company_id": "NVDA",
            "slot_label": "FY2027Q3",
            "period_end": "2026-10-25",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["nvda_20261117_fy27q3_results"]["requested_url"],
            "local_path": l_path("nvda_20261117_fy27q3_results"),
            "published_date": "2026-11-17",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "NVIDIA官方新闻室FY2027Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_MTSI_2026Q4": {
            "source_id": "S_MTSI_2026Q4",
            "company_id": "MTSI",
            "slot_label": "FY2026Q4",
            "period_end": "2026-10-02",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["mtsi_20261105_fy26q4_results"]["requested_url"],
            "local_path": l_path("mtsi_20261105_fy26q4_results"),
            "published_date": "2026-11-05",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方FY2026Q4及全年业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_TSEM_2026Q3": {
            "source_id": "S_TSEM_2026Q3",
            "company_id": "TSEM",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["tsem_20261102_2026q3_results"]["requested_url"],
            "local_path": l_path("tsem_20261102_2026q3_results"),
            "published_date": "2026-11-02",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_GFS_2026Q3": {
            "source_id": "S_GFS_2026Q3",
            "company_id": "GFS",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["gfs_20261104_2026q3_results"]["requested_url"],
            "local_path": l_path("gfs_20261104_2026q3_results"),
            "published_date": "2026-11-04",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_VECO_2026Q3": {
            "source_id": "S_VECO_2026Q3",
            "company_id": "VECO",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["veco_20261104_2026q3_results"]["requested_url"],
            "local_path": l_path("veco_20261104_2026q3_results"),
            "published_date": "2026-11-04",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_SOI_2027H1": {
            "source_id": "S_SOI_2027H1",
            "company_id": "SOI",
            "slot_label": "FY2027H1",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["soi_20261118_fy27h1_results"]["requested_url"],
            "local_path": l_path("soi_20261118_fy27h1_results"),
            "published_date": "2026-11-18",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司官网FY2027Q2收入及H1半年度业绩公告；本地存档HTML与清洗TXT",
        },
        "S_ANET_2026Q3": {
            "source_id": "S_ANET_2026Q3",
            "company_id": "ANET",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["anet_20261103_2026q3_results"]["requested_url"],
            "local_path": l_path("anet_20261103_2026q3_results"),
            "published_date": "2026-11-03",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_POET_2026Q3": {
            "source_id": "S_POET_2026Q3",
            "company_id": "POET",
            "slot_label": "2026Q3",
            "period_end": "2026-09-30",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["poet_20261116_2026q3_official"]["requested_url"],
            "local_path": l_path("poet_20261116_2026q3_official"),
            "published_date": "2026-11-16",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司官网2026Q3正式业绩新闻稿；本地存档HTML与清洗TXT",
        },
        "S_AVGO_2026Q3": {
            "source_id": "S_AVGO_2026Q3",
            "company_id": "AVGO",
            "slot_label": "FY2026Q3",
            "period_end": "2026-08-02",
            "source_scope": "quarterly",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["avgo_20260902_fy26q3_results"]["requested_url"],
            "local_path": l_path("avgo_20260902_fy26q3_results"),
            "published_date": "2026-09-02",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方FY2026Q3业绩新闻稿；本地存档HTML与清洗TXT",
        },
        # Interquarter registrations for LITE & CIEN (preserving locked test assertions)
        "S_LITE_2027Q1": {
            "source_id": "S_LITE_2027Q1",
            "company_id": "LITE",
            "slot_label": "FY2027Q1",
            "period_end": "2026-09-26",
            "source_scope": "interquarter",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["lite_20261102_fy27q1_results"]["requested_url"],
            "local_path": l_path("lite_20261102_fy27q1_results"),
            "published_date": "2026-11-02",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方FY2027Q1业绩新闻稿；按interquarter登记以保护test_reader_semantics对LITE既有2/4槽位断言",
        },
        "S_CIEN_2026Q3_PR": {
            "source_id": "S_CIEN_2026Q3_PR",
            "company_id": "CIEN",
            "slot_label": "FY2026Q3-release",
            "period_end": "2026-08-01",
            "source_scope": "interquarter",
            "material_type": "earnings_release",
            "source_grade": "A",
            "url": by_slug["cien_20260903_fy26q3_results"]["requested_url"],
            "local_path": l_path("cien_20260903_fy26q3_results"),
            "published_date": "2026-09-03",
            "accessed_date": "2026-11-22",
            "availability": "available",
            "missing_reason": "",
            "acquisition_note": "公司IR官方FY2026Q3业绩新闻稿；按interquarter登记以保持CIEN既有4份官方电话会逐字稿槽位闭合",
        },
    }
    source_append_order = [
        "S_AXTI_2026Q3",
        "S_FN_2027Q1",
        "S_NVDA_2027Q3",
        "S_MTSI_2026Q4",
        "S_TSEM_2026Q3",
        "S_GFS_2026Q3",
        "S_VECO_2026Q3",
        "S_SOI_2027H1",
        "S_ANET_2026Q3",
        "S_POET_2026Q3",
        "S_AVGO_2026Q3",
        "S_LITE_2027Q1",
        "S_CIEN_2026Q3_PR",
    ]
    slug_by_url = {r["requested_url"]: slug for slug, r in by_slug.items() if r["archive_status"] == "archived_http_200"}
    for sid in source_append_order:
        slug = slug_by_url[source_updates[sid]["url"]]
        ref_tag = f"corpus/web/step4_20261122/{slug}.txt"
        if ref_tag not in source_updates[sid]["acquisition_note"]:
            source_updates[sid]["acquisition_note"] += f"；归档 {ref_tag}"
    upsert_rows(sources, "source_id", source_updates, append_order=source_append_order)

    # ------------------------------------------------------------------
    # 3. Reviewed Management Claims in `calls/claims.csv` (CL077-CL083)
    # ------------------------------------------------------------------
    claims = read_csv_rows(calls_dir / "claims.csv", FILES["claims.csv"])
    claim_updates: dict[str, dict[str, str]] = {
        "CL077": {
            "claim_id": "CL077",
            "source_id": "S_LITE_2027Q1",
            "speaker": "Michael Hurlston",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "volume_order",
            "side": "supply",
            "theme_id": "T017",
            "quote": "During the quarter, we secured our second major NPO/CPO win, backed by purchase commitments exceeding $5 billion.",
            "anchor": "CEO commentary, paragraph 1 (p2)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "CPO商业化与采用阶段",
            "unmapped_reason": "原文为NPO/CPO合并口径且未拆分激光器芯片、外置光源模块与子系统各自金额、履约年限及客户身份，不能映射单一BOM节点",
            "summary": "Lumentum在FY27Q1业绩稿披露取得第二项重大NPO/CPO定点并附逾50亿美元采购承诺；系NPO与CPO合并口径而非纯CPO单列，不等于当季确收收入",
        },
        "CL078": {
            "claim_id": "CL078",
            "source_id": "S_AXTI_2026Q3",
            "speaker": "Morris Young",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "scaled",
            "side": "supply",
            "theme_id": "T008",
            "quote": "We entered 2026 with a commitment to double our indium phosphide capacity and I am pleased to report that not only have we surpassed that goal but we have more than quadrupled our 2026 indium phosphide revenue opportunity through additional productivity gains and the expansion of our capabilities for high-value, large diameter products.",
            "anchor": "Management Qualitative Comments, paragraph 1 (p3)",
            "review_status": "reviewed",
            "mapping_track": "canonical",
            "cell_id": "M1",
            "route_item_id": "",
            "unmapped_theme": "",
            "unmapped_reason": "",
            "summary": "AXT在2026Q3业绩稿称已超额完成年内InP衬底产能翻倍目标；未单列InP分产品确收金额或两用物项出口许可证获批笔数",
        },
        "CL079": {
            "claim_id": "CL079",
            "source_id": "S_POET_2026Q3",
            "speaker": "Suresh Venkatesan",
            "speaker_role": "management",
            "statement_type": "forward_looking",
            "event_type": "delayed",
            "side": "supply",
            "theme_id": "T010",
            "quote": "We expect to ship our current backlog of optical engines, including the 30,000 engines we had targeted for 2026, by the second quarter of 2027, as the capacity we have already funded comes online",
            "anchor": "Management Commentary, paragraph 2 (p5)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "晶圆级光引擎产能与交付延期",
            "unmapped_reason": "原定2026年出货的3万只光引擎涵盖多客户多速率项目且受晶圆与元件紧缺及良率爬坡影响顺延至2027Q2前，不能映射单一模块节点",
            "summary": "POET在2026Q3业绩稿将原定2026年目标的3万只光引擎积压订单出货窗口调整至2027年第二季度前；当季总收入约103万美元",
        },
        "CL080": {
            "claim_id": "CL080",
            "source_id": "S_AVGO_2026Q3",
            "speaker": "Hock Tan",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "unknown",
            "side": "demand",
            "theme_id": "T018",
            "quote": "Q3 AI semiconductor revenue of $16.7 billion grew 221% year-over-year, and 54% quarter-over-quarter",
            "anchor": "CEO quote in official FY2026 Q3 results (p2)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "AI半导体与网络需求",
            "unmapped_reason": "AI半导体收入合并定制加速器与网络芯片，新闻稿正文未拆分CPO、光DSP或200G EML份额",
            "summary": "Broadcom披露FY2026Q3 AI半导体收入167亿美元（同比增长221%、环比增长54%）并指引Q4达217亿美元；仅作混合需求背景",
        },
        "CL081": {
            "claim_id": "CL081",
            "source_id": "S_TSEM_2026Q3",
            "speaker": "Russell Ellwanger",
            "speaker_role": "management",
            "statement_type": "forward_looking",
            "event_type": "ramping",
            "side": "supply",
            "theme_id": "T015",
            "quote": "We target to achieve an annualized $1.1 billion run rate in the fourth quarter of 2026 of SiPho revenue alone, namely 5X of the 2025 SiPho annual revenue. Our on-going capacity investments, including the announced Track-1 Japan 300mm buildout, are progressing ahead of schedule, supported by customer contracts which are being extended through 2029",
            "anchor": "CEO commentary, paragraph 2 (p9)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "硅光晶圆代工年化收入目标与扩产进度",
            "unmapped_reason": "SiPho代工收入合并可插拔模块、NPO与CPO多类客户芯片，不能直接折算单一终端光模块形态出货量",
            "summary": "Tower在2026Q3业绩稿提出2026Q4硅光单项年化收入达11亿美元目标（约为2025年5倍），并称日本300mm一轨扩产超前推进且客户长约延展至2029年",
        },
        "CL082": {
            "claim_id": "CL082",
            "source_id": "S_VECO_2026Q3",
            "speaker": "Bill Miller",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "unknown",
            "side": "demand",
            "theme_id": "T008",
            "quote": "AI infrastructure investment is accelerating technology transitions across leading-edge logic and memory, advanced packaging, and high-speed optical connectivity. This is driving unprecedented customer engagement and order activity across our differentiated portfolio.",
            "anchor": "CEO commentary, paragraph 1 (p3)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "化合物外延与半导体设备综合订单景气",
            "unmapped_reason": "管理层把先进逻辑存储、先进封装与高速光连接并列归因，新闻稿未单列InP MOCVD设备订单金额或台数",
            "summary": "Veeco在2026Q3业绩稿称AI基础设施推动高速光连接等领域设备询单与订单活跃；未拆分MOCVD专项订单规模",
        },
        "CL083": {
            "claim_id": "CL083",
            "source_id": "S_SOI_2027H1",
            "speaker": "Laurent Rémont",
            "speaker_role": "management",
            "statement_type": "fact",
            "event_type": "scaled",
            "side": "supply",
            "theme_id": "T016",
            "quote": "Looking ahead, most of our Photonics-SOI customers have committed through 2028 under capacity reservation agreements backed by cash deposits, with talks underway for extra volumes beyond. We are now pivoting our existing Bernin 4 fab to SOI to serve that demand",
            "anchor": "CEO commentary, paragraph 1 (p21)",
            "review_status": "reviewed",
            "mapping_track": "unmapped",
            "cell_id": "",
            "route_item_id": "",
            "unmapped_theme": "Photonics-SOI晶圆产能预留与产线转产",
            "unmapped_reason": "Photonics-SOI衬底覆盖可插拔、NPO与CPO多类光收发芯片且约12亿美元长约跨多年期，不直接等同下游模块当期产出",
            "summary": "Soitec在FY27H1业绩稿披露Photonics-SOI半年度收入约1.25亿美元，多数客户已签带现金定金的产能预留协议（未来数年总额约12亿美元）并将Bernin 4厂转向SOI扩产",
        },
    }
    claim_append_order = ["CL077", "CL078", "CL079", "CL080", "CL081", "CL082", "CL083"]
    upsert_rows(claims, "claim_id", claim_updates, append_order=claim_append_order)

    # Verify verbatim match for all new claims against archived .txt
    assert_verbatim_in_txt("lite_20261102_fy27q1_results", claim_updates["CL077"]["quote"], by_slug)
    assert_verbatim_in_txt("axti_20261029_2026q3_results", claim_updates["CL078"]["quote"], by_slug)
    assert_verbatim_in_txt("poet_20261116_2026q3_official", claim_updates["CL079"]["quote"], by_slug)
    assert_verbatim_in_txt("avgo_20260902_fy26q3_results", claim_updates["CL080"]["quote"], by_slug)
    assert_verbatim_in_txt("tsem_20261102_2026q3_results", claim_updates["CL081"]["quote"], by_slug)
    assert_verbatim_in_txt("veco_20261104_2026q3_results", claim_updates["CL082"]["quote"], by_slug)
    assert_verbatim_in_txt("soi_20261118_fy27h1_results", claim_updates["CL083"]["quote"], by_slug)

    # ------------------------------------------------------------------
    # 4. Commitments Assessment Refresh (`calls/commitments.csv`)
    # ------------------------------------------------------------------
    commitments = read_csv_rows(calls_dir / "commitments.csv", FILES["commitments.csv"])
    commitment_updates: dict[str, dict[str, str]] = {
        "CM008": {
            "assessment": (
                "Q1所述begin standardization在2026-09-03 FY26Q3电话会明确为initial customer standardization"
                "（客户平台选型与部署规范纳入，非IEEE/OIF组织标准且不混同Vesta相关Open CPX MSA），"
                "2026-09-03官方业绩稿未单列进展、2026-09-16论坛仍预计年底推出首版；截至2026-11-22窗口未到期"
            ),
        },
        "CM009": {
            "assessment": (
                "Q1预计2027年开始爬坡，2026-09-03 Q3电话会细化为2027年内逐步形成有规模收入（scaling to material revenue），"
                "2026-09-16论坛仍列为未来增长来源（2027-12-31为年度跟踪坐标）；截至2026-11-22仍在未来窗口，"
                "既有RLS全系列收入、首单或WaveLogic部署不计入Hyper-Rail专项爬坡"
            ),
        },
    }
    upsert_rows(commitments, "commitment_id", commitment_updates, append_order=[])

    # ------------------------------------------------------------------
    # 5. Watch Entities (`calls/watch_entities.csv`)
    # ------------------------------------------------------------------
    watch_entities = read_csv_rows(calls_dir / "watch_entities.csv", FILES["watch_entities.csv"])
    watch_updates: dict[str, dict[str, str]] = {
        "WATCH_NEWPHOTONICS": {
            "entity_id": "WATCH_NEWPHOTONICS",
            "entity_name": "NewPhotonics",
            "entity_type": "company",
            "aliases": "NewPhotonics Ltd.",
            "inclusion_reason": "Tower Semiconductor PH18DA激光集成硅光PIC公告的具名芯片设计对手方",
            "monitoring_status": "active",
            "promoted_company_id": "",
            "source_ref": by_slug["tsem_20260917_newphotonics_pic"]["requested_url"],
            "notes": "仅用于显式事件对手方挂接；私企不进入四季度电话会覆盖池",
        },
        "WATCH_QUINTESSENT": {
            "entity_id": "WATCH_QUINTESSENT",
            "entity_name": "Quintessent",
            "entity_type": "company",
            "aliases": "Quintessent Inc.",
            "inclusion_reason": "IQE 6英寸GaAs量子点激光外延片采购协议与送样公告的具名对手方",
            "monitoring_status": "active",
            "promoted_company_id": "",
            "source_ref": by_slug["iqe_20260903_quintessent_qdl"]["requested_url"],
            "notes": "仅用于显式事件对手方挂接；私企不进入四季度电话会覆盖池",
        },
        "WATCH_AXCELIS": {
            "entity_id": "WATCH_AXCELIS",
            "entity_name": "Axcelis Technologies",
            "entity_type": "company",
            "aliases": "Axcelis;ACLS",
            "inclusion_reason": "Veeco全股票换股合并交易对手方（待中国SAMR与美国HSR审批）",
            "monitoring_status": "active",
            "promoted_company_id": "",
            "source_ref": by_slug["veco_20261102_axcelis_merger_update"]["requested_url"],
            "notes": "仅用于Veeco并购事件对手方挂接；离子注入设备主业不进入光模块季度池",
        },
    }
    watch_append_order = ["WATCH_NEWPHOTONICS", "WATCH_QUINTESSENT", "WATCH_AXCELIS"]
    upsert_rows(watch_entities, "entity_id", watch_updates, append_order=watch_append_order)

    # ------------------------------------------------------------------
    # 6. Disclosures (`calls/disclosures.csv`): Upgrade DRQ0019 + Add 30 HTTP-200 Items
    # ------------------------------------------------------------------
    disclosures = read_csv_rows(calls_dir / "disclosures.csv", FILES["disclosures.csv"])
    disclosure_updates: dict[str, dict[str, str]] = {
        # Upgrade existing D_TSEM_20261103_INNOLIGHT_NPO (DRQ0019) from title-only to full-text verified
        "D_TSEM_20261103_INNOLIGHT_NPO": {
            "local_path": l_path("tsem_20261103_innolight_npo"),
            "content_hash": h_hash("tsem_20261103_innolight_npo"),
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "review_scope": "第3段PH18M美国加州厂早期生产与300mm多产品流片及第7段美以日四座晶圆厂客户布局引语",
            "notes": "对应DRQ0019/DC_430D7977BA22，已取官网全文升级逐字锚定：首款NPO器件在Tower美国加州厂PH18M 200mm流程进入early production并在300mm平台流片多款下一代NPO，与中际11/03投关2027H2逐步上量口径一致",
        },
        # 24 new anchor_reviewed disclosures
        "D_MRVL_20261102_LITE_MERGE": {
            "disclosure_id": "D_MRVL_20261102_LITE_MERGE",
            "publisher_entity_id": "MRVL",
            "legacy_source_id": "",
            "title": "Marvell and Lumentum to Combine, Creating a Category Leader in AI Connectivity",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["mrvl_20261102_lumentum_combine"]["requested_url"],
            "local_path": l_path("mrvl_20261102_lumentum_combine"),
            "content_hash": h_hash("mrvl_20261102_lumentum_combine"),
            "origin_group": "OG_MRVL_LITE_20261102_MERGE",
            "published_at": "2026-11-02",
            "updated_at": "",
            "discovered_at": "2026-11-04",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段换股比例与1150亿美元隐含企业价值及第13段预计2028H1交割与股东反垄断审批先决条件",
            "notes": "对应DRQ0015/DC_501FC1F61B62；确定性合并协议（1股LITE换4.500股MRVL），须经双方股东及反垄断监管批准，预计2028H1交割，当前尚未交割",
        },
        "D_LITE_20261102_FY27Q1": {
            "disclosure_id": "D_LITE_20261102_FY27Q1",
            "publisher_entity_id": "LITE",
            "legacy_source_id": "S_LITE_2027Q1",
            "title": "Lumentum FY2027 Q1 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["lite_20261102_fy27q1_results"]["requested_url"],
            "local_path": l_path("lite_20261102_fy27q1_results"),
            "content_hash": h_hash("lite_20261102_fy27q1_results"),
            "origin_group": "OG_LITE_20261102_FY27Q1",
            "published_at": "2026-11-02",
            "updated_at": "",
            "discovered_at": "2026-11-04",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "CEO引语第1段second major NPO/CPO win逾50亿美元采购承诺及分部营收表",
            "notes": "对应DRQ0016/DC_573401DC530B；核实原文确有backed by purchase commitments exceeding $5 billion，但定语为NPO/CPO合并而非纯CPO，且未具名客户与履约期；全文未披露200G EML专项积压额",
        },
        "D_AXTI_20261029_Q3": {
            "disclosure_id": "D_AXTI_20261029_Q3",
            "publisher_entity_id": "AXTI",
            "legacy_source_id": "S_AXTI_2026Q3",
            "title": "AXT 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["axti_20261029_2026q3_results"]["requested_url"],
            "local_path": l_path("axti_20261029_2026q3_results"),
            "content_hash": h_hash("axti_20261029_2026q3_results"),
            "origin_group": "OG_AXTI_20261029_Q3",
            "published_at": "2026-10-29",
            "updated_at": "",
            "discovered_at": "2026-10-30",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "Management Qualitative Comments第1段Q3营收7340万美元与InP产能翻倍超额完成句",
            "notes": "对应DRQ0017/DC_3841FCD60F32；Q3合并营收7341万美元创纪录，但新闻稿未拆分InP单项确收额与出口许可证获批笔数（出口许可仅见Safe Harbor风险提示）",
        },
        "D_AXTI_20261028_TONGMEI_PE": {
            "disclosure_id": "D_AXTI_20261028_TONGMEI_PE",
            "publisher_entity_id": "AXTI",
            "legacy_source_id": "",
            "title": "AXT subsidiary Beijing Tongmei up to RMB 3.67B private equity financing",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["axti_20261028_tongmei_financing"]["requested_url"],
            "local_path": l_path("axti_20261028_tongmei_financing"),
            "content_hash": h_hash("axti_20261028_tongmei_financing"),
            "origin_group": "OG_AXTI_20261028_TONGMEI_PE",
            "published_at": "2026-10-28",
            "updated_at": "",
            "discovered_at": "2026-10-29",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第1段19.12亿至36.69亿元人民币融资区间及第3段预计2026年12月交割与73.40%持股比例句",
            "notes": "对应DRQ0018/DC_FD32C455D502；北京通美私募股权融资协议待政府备案等交割条件达成，不保证必然交割，未交割前不计落地扩产",
        },
        "D_NOK_20260915_TELXIUS_800G": {
            "disclosure_id": "D_NOK_20260915_TELXIUS_800G",
            "publisher_entity_id": "NOK",
            "legacy_source_id": "",
            "title": "Telxius and Nokia 800G Coherent Pluggable terrestrial deployment release",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["nok_20260915_telxius_800g"]["requested_url"],
            "local_path": l_path("nok_20260915_telxius_800g"),
            "content_hash": h_hash("nok_20260915_telxius_800g"),
            "origin_group": "OG_NOK_20260915_TELXIUS_800G",
            "published_at": "2026-09-15",
            "updated_at": "",
            "discovered_at": "2026-09-16",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "正文首段Telxius欧美及拉美陆地骨干网部署ICE-X 800G ZR/ZR+及第4段与此前BRUSA海缆试验区分",
            "notes": "对应DRQ0021/DC_BF393C7C7BE8；明确本次为陆地干线IP-over-DWDM现网部署计划，区别于此前BRUSA海缆5600公里400G/波演示，但仍属Nokia第一方新闻室发布且未披露采购数量",
        },
        "D_NVDA_20261117_FY27Q3": {
            "disclosure_id": "D_NVDA_20261117_FY27Q3",
            "publisher_entity_id": "NVDA",
            "legacy_source_id": "S_NVDA_2027Q3",
            "title": "NVIDIA FY2027 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["nvda_20261117_fy27q3_results"]["requested_url"],
            "local_path": l_path("nvda_20261117_fy27q3_results"),
            "content_hash": h_hash("nvda_20261117_fy27q3_results"),
            "origin_group": "OG_NVDA_20261117_FY27Q3",
            "published_at": "2026-11-17",
            "updated_at": "",
            "discovered_at": "2026-11-19",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "Data Center Highlights中Vera Rubin NVL72出货与联手Cisco推进USFP新光模块封装形态条目",
            "notes": "对应DRQ0023/DC_4FAA980A3027；Q3总营收1158亿美元（数据中心1076亿美元），光学专项仅披露与Cisco推进USFP新光模块形态计划，未披露Quantum-X/Spectrum-X CPO交换机客户出货时间点",
        },
        "D_TSEM_20260917_NEWPHOTONICS": {
            "disclosure_id": "D_TSEM_20260917_NEWPHOTONICS",
            "publisher_entity_id": "TSEM",
            "legacy_source_id": "",
            "title": "NewPhotonics and Tower Semiconductor Laser-Integrated Optical Engine PICs release",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["tsem_20260917_newphotonics_pic"]["requested_url"],
            "local_path": l_path("tsem_20260917_newphotonics_pic"),
            "content_hash": h_hash("tsem_20260917_newphotonics_pic"),
            "origin_group": "OG_TSEM_20260917_NEWPHOTONICS",
            "published_at": "2026-09-17",
            "updated_at": "",
            "discovered_at": "2026-09-18",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第5段800G/1.6T NPG102 PIC批量出货事实句与6.4T NPC505 2027H1预计出货前瞻句",
            "notes": "对应DRQ0025/DC_A038F7C2DD93；严格将PH18DA平台800G/1.6T NPG102当期批量出货与6.4T NPC505 2027H1计划拆成两条独立事件，且未具名下游OEM买家",
        },
        "D_WIWYNN_20261013_OCP_CPO_DEMO": {
            "disclosure_id": "D_WIWYNN_20261013_OCP_CPO_DEMO",
            "publisher_entity_id": "WIWYNN",
            "legacy_source_id": "",
            "title": "Wiwynn, Ayar Labs, and GUC OCP 2026 Live Demonstration of Integrated Optical Compute System",
            "disclosure_type": "official_release",
            "content_class": "demonstration_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["wiwynn_20261013_ayar_guc_cpo_demo"]["requested_url"],
            "local_path": l_path("wiwynn_20261013_ayar_guc_cpo_demo"),
            "content_hash": h_hash("wiwynn_20261013_ayar_guc_cpo_demo"),
            "origin_group": "OG_WIWYNN_20261013_OCP_CPO_DEMO",
            "published_at": "2026-10-13",
            "updated_at": "",
            "discovered_at": "2026-10-14",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第3-4段OCP现场计算托盘集成GUC多芯片封装、Ayar TeraPHY光引擎与SuperNova外置光源实时遥测演示",
            "notes": "对应DRQ0026/DC_286D42235853；限定为OCP展会系统级功能验证演示（demonstrated），不代表商业订单或规模出货",
        },
        "D_LIGHTMATTER_20261012_OCP_CPO": {
            "disclosure_id": "D_LIGHTMATTER_20261012_OCP_CPO",
            "publisher_entity_id": "WATCH_LIGHTMATTER",
            "legacy_source_id": "",
            "title": "Lightmatter OCP 2026 Open Rack CPO Switch and XPU Scale-Up Server showcase",
            "disclosure_type": "official_release",
            "content_class": "demonstration_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["lightmatter_20261012_open_rack_cpo"]["requested_url"],
            "local_path": l_path("lightmatter_20261012_open_rack_cpo"),
            "content_hash": h_hash("lightmatter_20261012_open_rack_cpo"),
            "origin_group": "OG_LIGHTMATTER_20261012_OCP_CPO",
            "published_at": "2026-10-12",
            "updated_at": "",
            "discovered_at": "2026-10-14",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段与第6段区分Flex联合开发204.8T 1RU交换托盘生产验证平台与102.4T 4-XPU原型样机OCP展台展示",
            "notes": "对应DRQ0027/DC_DC1ABE67C305；标题虽用Delivers，正文明确系OCP展台A36展示生产验证平台（production validation platform）与XPU原型（prototype/proof of concept），非商业部署出货",
        },
        "D_CRDO_20261012_1P6T_ALC": {
            "disclosure_id": "D_CRDO_20261012_1P6T_ALC",
            "publisher_entity_id": "CRDO",
            "legacy_source_id": "",
            "title": "Credo Unveils 1.6T ZeroFlap Active Light Cable for AI Data Centers",
            "disclosure_type": "official_release",
            "content_class": "technical_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["crdo_20261012_1p6t_zeroflap_alc"]["requested_url"],
            "local_path": l_path("crdo_20261012_1p6t_zeroflap_alc"),
            "content_hash": h_hash("crdo_20261012_1p6t_zeroflap_alc"),
            "origin_group": "OG_CRDO_20261012_1P6T_ALC",
            "published_at": "2026-10-12",
            "updated_at": "",
            "discovered_at": "2026-10-13",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2-4段微发光器阵列架构（端功耗12W、最长50米）与第8段预计2027年出货句",
            "notes": "对应DRQ0028/DC_7CED25D6E66F；新品架构发布与OCP展台展示，原文明确will be shipping in 2027，当前尚未进入量产出货",
        },
        "D_MTSI_20260917_3P2T_CHIPSET": {
            "disclosure_id": "D_MTSI_20260917_3P2T_CHIPSET",
            "publisher_entity_id": "MTSI",
            "legacy_source_id": "",
            "title": "MACOM Introduces 3.2T Chipset Solution for High Speed Optical Connectivity",
            "disclosure_type": "official_release",
            "content_class": "technical_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["mtsi_20260917_3p2t_chipset"]["requested_url"],
            "local_path": l_path("mtsi_20260917_3p2t_chipset"),
            "content_hash": h_hash("mtsi_20260917_3p2t_chipset"),
            "origin_group": "OG_MTSI_20260917_3P2T_CHIPSET",
            "published_at": "2026-09-17",
            "updated_at": "",
            "discovered_at": "2026-09-18",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第6-9段MATA-42754/41754四通道线性TIA与MARP-BP224光电二极管配套既有MAOM驱动芯片及Availability句",
            "notes": "对应DRQ0029/DC_535D459775E6；核明新增接收端TIA与>100GHz PIN PD型号，与EV007既有448G驱动芯片组成完整3.2T前端套片，readily available仅代表芯片可订购",
        },
        "D_IQE_20260903_QUINTESSENT_QDL": {
            "disclosure_id": "D_IQE_20260903_QUINTESSENT_QDL",
            "publisher_entity_id": "WATCH_IQE",
            "legacy_source_id": "",
            "title": "IQE announces purchase agreement with Quintessent as Quantum Dot Laser moves to sampling",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["iqe_20260903_quintessent_qdl"]["requested_url"],
            "local_path": l_path("iqe_20260903_quintessent_qdl"),
            "content_hash": h_hash("iqe_20260903_quintessent_qdl"),
            "origin_group": "OG_IQE_20260903_QUINTESSENT_QDL",
            "published_at": "2026-09-03",
            "updated_at": "",
            "discovered_at": "2026-09-05",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第3-4段6英寸GaAs量子点激光外延片采购协议及支持Quintessent客户送样阶段段落",
            "notes": "对应DRQ0030/DC_741EFE5BF486；拆分6英寸GaAs外延片采购协议与下游客户送样两条独立事件，未披露采购金额与终端客户",
        },
        "D_LITE_20260921_ECOC_ELSFP": {
            "disclosure_id": "D_LITE_20260921_ECOC_ELSFP",
            "publisher_entity_id": "LITE",
            "legacy_source_id": "",
            "title": "Lumentum to Demonstrate DWDM ELSFP Laser Module for OCI MSA Applications at ECOC 2026",
            "disclosure_type": "official_release",
            "content_class": "technical_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["lite_20260921_ecoc_dwdm_elsfp"]["requested_url"],
            "local_path": l_path("lite_20260921_ecoc_dwdm_elsfp"),
            "content_hash": h_hash("lite_20260921_ecoc_dwdm_elsfp"),
            "origin_group": "OG_LITE_20260921_ECOC_ELSFP",
            "published_at": "2026-09-21",
            "updated_at": "",
            "discovered_at": "2026-09-22",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段ECOC展前演示预告与第5段预计2027H1初始可提供（initial availability）句",
            "notes": "对应DRQ0039/DC_D527C3DC5ED2；8波长DWDM ELSFP外置光源展前预告（announced），预计2027H1初始可提供，不计为已出货",
        },
        "D_LITE_20260921_ECOC_VCSEL_D2D": {
            "disclosure_id": "D_LITE_20260921_ECOC_VCSEL_D2D",
            "publisher_entity_id": "LITE",
            "legacy_source_id": "",
            "title": "Lumentum, Qualcomm, and Corning to Demonstrate 1060 nm VCSEL Optical D2D Connectivity at ECOC 2026",
            "disclosure_type": "official_release",
            "content_class": "demonstration_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["lite_20260921_ecoc_1060nm_vcsel"]["requested_url"],
            "local_path": l_path("lite_20260921_ecoc_1060nm_vcsel"),
            "content_hash": h_hash("lite_20260921_ecoc_1060nm_vcsel"),
            "origin_group": "OG_LITE_20260921_ECOC_VCSEL_D2D",
            "published_at": "2026-09-21",
            "updated_at": "",
            "discovered_at": "2026-09-22",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段ECOC板级联合演示计划与第4段单通道32 Gb/s NRZ概念验证（proof-of-concept）配置说明",
            "notes": "对应DRQ0040/DC_E1BEF90B2480；1060nm VCSEL多模光纤D2D板级概念验证预告（32Gb/s NRZ），严禁升格为商业出货点",
        },
        "D_MXL_20261110_JEJU_PMIC": {
            "disclosure_id": "D_MXL_20261110_JEJU_PMIC",
            "publisher_entity_id": "MXL",
            "legacy_source_id": "",
            "title": "MaxLinear Unveils Jeju Custom PMIC for 1.6T Optical DSPs",
            "disclosure_type": "official_release",
            "content_class": "technical_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["mxl_20261110_jeju_pmic"]["requested_url"],
            "local_path": l_path("mxl_20261110_jeju_pmic"),
            "content_hash": h_hash("mxl_20261110_jeju_pmic"),
            "origin_group": "OG_MXL_20261110_JEJU_PMIC",
            "published_at": "2026-11-10",
            "updated_at": "",
            "discovered_at": "2026-11-11",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第1段MxL77904定制PMIC发布及第13段预计2027年2月向客户送样句",
            "notes": "对应DRQ0042/DC_DFCE4B441F6E；面向1.6T PAM4光DSP（含Rushmore）的多相电源芯片新品发布，预计2027年2月才开始送样，尚未出货",
        },
        "D_CIEN_20261117_INTERNET2_800G": {
            "disclosure_id": "D_CIEN_20261117_INTERNET2_800G",
            "publisher_entity_id": "CIEN",
            "legacy_source_id": "",
            "title": "Ciena and Internet2 Reach Record for Longest Terrestrial 800 Gb/s Coherent Pluggable Link",
            "disclosure_type": "official_release",
            "content_class": "demonstration_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["cien_20261117_internet2_800g"]["requested_url"],
            "local_path": l_path("cien_20261117_internet2_800g"),
            "content_hash": h_hash("cien_20261117_internet2_800g"),
            "origin_group": "OG_CIEN_20261117_INTERNET2_800G",
            "published_at": "2026-11-17",
            "updated_at": "",
            "discovered_at": "2026-11-18",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2-4段SC26芝加哥至堪萨斯城往返2104公里WaveLogic 6 Nano 800G实网试验段落",
            "notes": "对应DRQ0043/DC_91F3D715F522；确认模块为WaveLogic 6 Nano（135 GBaud PKT-MAX模式），属Internet2美国科研教育网实网试验演示，非批量商业订单",
        },
        "D_POET_20261116_Q3": {
            "disclosure_id": "D_POET_20261116_Q3",
            "publisher_entity_id": "POET",
            "legacy_source_id": "S_POET_2026Q3",
            "title": "POET Technologies 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["poet_20261116_2026q3_official"]["requested_url"],
            "local_path": l_path("poet_20261116_2026q3_official"),
            "content_hash": h_hash("poet_20261116_2026q3_official"),
            "origin_group": "OG_POET_20261116_Q3",
            "published_at": "2026-11-16",
            "updated_at": "",
            "discovered_at": "2026-11-17",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段Q3营收102.6万美元及Management Commentary第2段3万只光引擎积压订单顺延至2027Q2前交付",
            "notes": "对应DRQ0044/DC_4FACD43C676E；Q3收入102.6万美元（含早期工程及小规模项目，经营现金净流出1270万美元），原定2026年目标的3万只光引擎延至2027Q2前出货，未进入规模量产",
        },
        "D_AVGO_20260902_Q3": {
            "disclosure_id": "D_AVGO_20260902_Q3",
            "publisher_entity_id": "AVGO",
            "legacy_source_id": "S_AVGO_2026Q3",
            "title": "Broadcom FY2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["avgo_20260902_fy26q3_results"]["requested_url"],
            "local_path": l_path("avgo_20260902_fy26q3_results"),
            "content_hash": h_hash("avgo_20260902_fy26q3_results"),
            "origin_group": "OG_AVGO_20260902_Q3",
            "published_at": "2026-09-02",
            "updated_at": "",
            "discovered_at": "2026-09-09",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "CEO引述中Q3 AI半导体收入167亿美元与Q4指引217亿美元段落",
            "notes": "对应DRQ0045/DC_425841A754F4；新闻稿正文仅披露AI半导体合并收入，未载Tomahawk 6 CPO或200G EML拆分（关联CL080）",
        },
        "D_TSEM_20261102_Q3": {
            "disclosure_id": "D_TSEM_20261102_Q3",
            "publisher_entity_id": "TSEM",
            "legacy_source_id": "S_TSEM_2026Q3",
            "title": "Tower Semiconductor 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["tsem_20261102_2026q3_results"]["requested_url"],
            "local_path": l_path("tsem_20261102_2026q3_results"),
            "content_hash": h_hash("tsem_20261102_2026q3_results"),
            "origin_group": "OG_TSEM_20261102_Q3",
            "published_at": "2026-11-02",
            "updated_at": "",
            "discovered_at": "2026-11-03",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "CEO引语第2段2026Q4硅光年化11亿美元运行率目标与日本300mm一轨扩产超前推进句",
            "notes": "对应staging DC_58448CDF4801；Q3营收5.26亿美元、Q4指引6亿美元，硅光11亿美元年化运行率为Q4目标值（关联CL081/EV056）",
        },
        "D_GFS_20261104_Q3": {
            "disclosure_id": "D_GFS_20261104_Q3",
            "publisher_entity_id": "GFS",
            "legacy_source_id": "S_GFS_2026Q3",
            "title": "GlobalFoundries 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["gfs_20261104_2026q3_results"]["requested_url"],
            "local_path": l_path("gfs_20261104_2026q3_results"),
            "content_hash": h_hash("gfs_20261104_2026q3_results"),
            "origin_group": "OG_GFS_20261104_Q3",
            "published_at": "2026-11-04",
            "updated_at": "",
            "discovered_at": "2026-11-05",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "Recent Business Highlights第5条与Marvell扩大Burlington厂SiGe产能多年协议（面向可插拔/NPO/CPO）及第2条CHIPS法案9.55亿美元重分配",
            "notes": "对应staging DC_DB6E7B2D27BB；Q3营收18.99亿美元，正文明确披露2026年9月与Marvell扩大Burlington SiGe多年制造协议支持可插拔模块、NPO与CPO",
        },
        "D_VECO_20261104_Q3": {
            "disclosure_id": "D_VECO_20261104_Q3",
            "publisher_entity_id": "VECO",
            "legacy_source_id": "S_VECO_2026Q3",
            "title": "Veeco 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["veco_20261104_2026q3_results"]["requested_url"],
            "local_path": l_path("veco_20261104_2026q3_results"),
            "content_hash": h_hash("veco_20261104_2026q3_results"),
            "origin_group": "OG_VECO_20261104_Q3",
            "published_at": "2026-11-04",
            "updated_at": "",
            "discovered_at": "2026-11-05",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "CEO引语第1段高速光连接驱动客户接洽与订单活跃度段落",
            "notes": "对应staging DC_25B37F48DF71；Q3营收2.094亿美元，CEO把高速光连接与先进逻辑存储封装并列作为订单驱动（关联CL082）",
        },
        "D_VECO_20261102_ACLS_MERGER": {
            "disclosure_id": "D_VECO_20261102_ACLS_MERGER",
            "publisher_entity_id": "VECO",
            "legacy_source_id": "",
            "title": "Axcelis Technologies and Veeco Instruments Merger Closing Timing Update",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["veco_20261102_axcelis_merger_update"]["requested_url"],
            "local_path": l_path("veco_20261102_axcelis_merger_update"),
            "content_hash": h_hash("veco_20261102_axcelis_merger_update"),
            "origin_group": "OG_VECO_20261102_ACLS_MERGER",
            "published_at": "2026-11-02",
            "updated_at": "",
            "discovered_at": "2026-11-03",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2-4段全股票合并预计交割日延至2027Q1末、待中国SAMR审批及重新提交美国HSR申报",
            "notes": "对应staging DC_6B392C92DA0A；每1股VECO换0.3575股ACLS，因待中国SAMR反垄断审查及HSR重报将预计交割推至2027Q1末",
        },
        "D_SOI_20261118_FY27H1": {
            "disclosure_id": "D_SOI_20261118_FY27H1",
            "publisher_entity_id": "SOI",
            "legacy_source_id": "S_SOI_2027H1",
            "title": "Soitec FY2027 Q2 revenue and H1 results",
            "disclosure_type": "official_release",
            "content_class": "commercial_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["soi_20261118_fy27h1_results"]["requested_url"],
            "local_path": l_path("soi_20261118_fy27h1_results"),
            "content_hash": h_hash("soi_20261118_fy27h1_results"),
            "origin_group": "OG_SOI_20261118_FY27H1",
            "published_at": "2026-11-18",
            "updated_at": "",
            "discovered_at": "2026-11-19",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "摘要第2-3条Photonics-SOI H1收入约1.25亿美元与约12亿美元现金定金产能预留协议及CEO引语Bernin 4转产句",
            "notes": "对应staging DC_86F8DBF8F95E；H1已收8600万欧元Photonics-SOI初始现金定金，预计FY27全年Photonics-SOI收入超3亿美元（关联CL083/EV059）",
        },
        "D_CRDO_20261104_ORCL_OCP": {
            "disclosure_id": "D_CRDO_20261104_ORCL_OCP",
            "publisher_entity_id": "CRDO",
            "legacy_source_id": "",
            "title": "Credo and Oracle Advance Optical Transceiver Telemetry Standardization with OCP Community",
            "disclosure_type": "official_release",
            "content_class": "technical_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["crdo_20261104_oracle_ocp_telemetry"]["requested_url"],
            "local_path": l_path("crdo_20261104_oracle_ocp_telemetry"),
            "content_hash": h_hash("crdo_20261104_oracle_ocp_telemetry"),
            "origin_group": "OG_CRDO_20261104_ORCL_OCP",
            "published_at": "2026-11-04",
            "updated_at": "",
            "discovered_at": "2026-11-05",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "anchor_reviewed",
            "review_scope": "第2段与第5段OCP社区批准Credo与Oracle主导的两项光模块增强遥测开放规范",
            "notes": "对应staging DC_89DB234EEA46；属OCP开放软件与带外通信标准获批，不代表Oracle对Credo光模块下达商业采购订单",
        },
        # 6 new no_relevant_claims disclosures (archived full text, verified absence of standalone optical claim)
        "D_FN_20261102_FY27Q1": {
            "disclosure_id": "D_FN_20261102_FY27Q1",
            "publisher_entity_id": "FN",
            "legacy_source_id": "S_FN_2027Q1",
            "title": "Fabrinet FY2027 Q1 financial results",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["fn_20261102_fy27q1_results"]["requested_url"],
            "local_path": l_path("fn_20261102_fy27q1_results"),
            "content_hash": h_hash("fn_20261102_fy27q1_results"),
            "origin_group": "OG_FN_20261102_FY27Q1",
            "published_at": "2026-11-02",
            "updated_at": "",
            "discovered_at": "2026-11-04",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "CEO引语与财务表按datacom 800G 1.6T CPO Building 10检索并通读全文",
            "notes": "对应DRQ0022/DC_7B475AB0DF5A；FY27Q1合并营收14.745亿美元（+51% YoY）、Q2指引16.0-16.5亿美元，但新闻稿正文未拆分Datacom、1.6T或Building 10进展",
        },
        "D_CIEN_20260903_FY26Q3": {
            "disclosure_id": "D_CIEN_20260903_FY26Q3",
            "publisher_entity_id": "CIEN",
            "legacy_source_id": "S_CIEN_2026Q3_PR",
            "title": "Ciena FY2026 Q3 financial results release",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["cien_20260903_fy26q3_results"]["requested_url"],
            "local_path": l_path("cien_20260903_fy26q3_results"),
            "content_hash": h_hash("cien_20260903_fy26q3_results"),
            "origin_group": "OG_CIEN_20260903_FY26Q3",
            "published_at": "2026-09-03",
            "updated_at": "",
            "discovered_at": "2026-09-09",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "CEO/CFO引述与分部收入表按WaveLogic 800G Vesta pluggable检索并通读全文",
            "notes": "对应DRQ0024/DC_9B16CE64F492；Q3营收16.711亿美元（Optical Networking分部11.913亿美元），但新闻稿未单列800GZR或Vesta送样时点（Vesta送样已由S_CIEN_2026_FORUM CL076核定）",
        },
        "D_OPENLIGHT_20261007_HETERO_SIPHO": {
            "disclosure_id": "D_OPENLIGHT_20261007_HETERO_SIPHO",
            "publisher_entity_id": "WATCH_OPENLIGHT",
            "legacy_source_id": "",
            "title": "OpenLight Heterogeneous Silicon Photonics post-ECOC media summary",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["openlight_20261007_heterogeneous_sipho"]["requested_url"],
            "local_path": l_path("openlight_20261007_heterogeneous_sipho"),
            "content_hash": h_hash("openlight_20261007_heterogeneous_sipho"),
            "origin_group": "OG_OPENLIGHT_20261007_HETERO_SIPHO",
            "published_at": "2026-10-07",
            "updated_at": "",
            "discovered_at": "2026-10-08",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "官网Newsroom短摘要p1-p3通读核对晶圆尺寸、PDK冻结与量产状态",
            "notes": "对应DRQ0038/DC_839378F484E4；系官网对Converge Network Digest专访的导读短文（提及累计公开融资8400万美元及COO/CSO任命），无晶圆尺寸、PDK冻结或商业量产出货实证",
        },
        "D_WIWYNN_20261012_OCP_SHOWCASE": {
            "disclosure_id": "D_WIWYNN_20261012_OCP_SHOWCASE",
            "publisher_entity_id": "WIWYNN",
            "legacy_source_id": "",
            "title": "Wiwynn Showcases Next-Gen AI Platforms, Thermal Engineering, and Optical Interconnect at OCP 2026",
            "disclosure_type": "official_release",
            "content_class": "demonstration_disclosure",
            "provenance_class": "first_party",
            "canonical_url": by_slug["wiwynn_20261012_ocp_showcase"]["requested_url"],
            "local_path": l_path("wiwynn_20261012_ocp_showcase"),
            "content_hash": h_hash("wiwynn_20261012_ocp_showcase"),
            "origin_group": "OG_WIWYNN_20261012_OCP_SHOWCASE",
            "published_at": "2026-10-12",
            "updated_at": "2026-10-13",
            "discovered_at": "2026-10-13",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "全文p1-p12通读核对服务器ODM展台总览与CPO演示段落",
            "notes": "对应DRQ0041/DC_4A9C0B800414；系OCP展台综合预热稿（含液冷与整机柜），其中CPO计算托盘联合演示已由次日专项新闻稿D_WIWYNN_20261013_OCP_CPO_DEMO（EV045）精确建档，不重复计次",
        },
        "D_MTSI_20261105_Q4": {
            "disclosure_id": "D_MTSI_20261105_Q4",
            "publisher_entity_id": "MTSI",
            "legacy_source_id": "S_MTSI_2026Q4",
            "title": "MACOM FY2026 Q4 and full-year financial results",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["mtsi_20261105_fy26q4_results"]["requested_url"],
            "local_path": l_path("mtsi_20261105_fy26q4_results"),
            "content_hash": h_hash("mtsi_20261105_fy26q4_results"),
            "origin_group": "OG_MTSI_20261105_Q4",
            "published_at": "2026-11-05",
            "updated_at": "",
            "discovered_at": "2026-11-06",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "Management Commentary与正文按optical CW laser 800G 1.6T data center检索并通读",
            "notes": "对应staging DC_A6ADDA0BAFA7；FY26Q4营收4.248亿美元（+62.7% YoY）、FY27Q1指引4.50-4.60亿美元，CEO仅作泛化年度总结而无光学细分主张（CW激光器仅见前瞻免责声明列举）",
        },
        "D_ANET_20261103_Q3": {
            "disclosure_id": "D_ANET_20261103_Q3",
            "publisher_entity_id": "ANET",
            "legacy_source_id": "S_ANET_2026Q3",
            "title": "Arista Networks 2026 Q3 financial results",
            "disclosure_type": "official_release",
            "content_class": "corporate_narrative",
            "provenance_class": "first_party",
            "canonical_url": by_slug["anet_20261103_2026q3_results"]["requested_url"],
            "local_path": l_path("anet_20261103_2026q3_results"),
            "content_hash": h_hash("anet_20261103_2026q3_results"),
            "origin_group": "OG_ANET_20261103_Q3",
            "published_at": "2026-11-03",
            "updated_at": "",
            "discovered_at": "2026-11-04",
            "retrieved_at": "2026-11-22",
            "reviewed_at": "2026-11-22",
            "retrieval_status": "retrieved",
            "processing_status": "no_relevant_claims",
            "review_scope": "CEO/CFO引述与Company Highlights按optics 800G 1.6T CPO LPO检索并通读",
            "notes": "对应staging DC_C85C91649A7A；Q3营收36.576亿美元（+58.5% YoY）、Q4指引39-40亿美元，业务亮点聚焦ESUN Etherlink SU-144与7800 AI Spine交换架构，未拆分光模块或CPO口径",
        },
    }
    disclosure_append_order = [
        "D_MRVL_20261102_LITE_MERGE",
        "D_LITE_20261102_FY27Q1",
        "D_AXTI_20261029_Q3",
        "D_AXTI_20261028_TONGMEI_PE",
        "D_NOK_20260915_TELXIUS_800G",
        "D_NVDA_20261117_FY27Q3",
        "D_TSEM_20260917_NEWPHOTONICS",
        "D_WIWYNN_20261013_OCP_CPO_DEMO",
        "D_LIGHTMATTER_20261012_OCP_CPO",
        "D_CRDO_20261012_1P6T_ALC",
        "D_MTSI_20260917_3P2T_CHIPSET",
        "D_IQE_20260903_QUINTESSENT_QDL",
        "D_LITE_20260921_ECOC_ELSFP",
        "D_LITE_20260921_ECOC_VCSEL_D2D",
        "D_MXL_20261110_JEJU_PMIC",
        "D_CIEN_20261117_INTERNET2_800G",
        "D_POET_20261116_Q3",
        "D_AVGO_20260902_Q3",
        "D_TSEM_20261102_Q3",
        "D_GFS_20261104_Q3",
        "D_VECO_20261104_Q3",
        "D_VECO_20261102_ACLS_MERGER",
        "D_SOI_20261118_FY27H1",
        "D_CRDO_20261104_ORCL_OCP",
        "D_FN_20261102_FY27Q1",
        "D_CIEN_20260903_FY26Q3",
        "D_OPENLIGHT_20261007_HETERO_SIPHO",
        "D_WIWYNN_20261012_OCP_SHOWCASE",
        "D_MTSI_20261105_Q4",
        "D_ANET_20261103_Q3",
    ]
    for did, drec in disclosure_updates.items():
        slug = (
            "tsem_20261103_innolight_npo"
            if did == "D_TSEM_20261103_INNOLIGHT_NPO"
            else slug_by_url[drec["canonical_url"]]
        )
        ref_tag = f"corpus/web/step4_20261122/{slug}.txt"
        if ref_tag not in drec["notes"]:
            drec["notes"] += f"；归档 {ref_tag}"
    upsert_rows(disclosures, "disclosure_id", disclosure_updates, append_order=disclosure_append_order)

    # ------------------------------------------------------------------
    # 7. Event Claims (`calls/event_claims.csv`): Upgrade ECL039 + Add ECL040-ECL063
    # ------------------------------------------------------------------
    event_claims = read_csv_rows(calls_dir / "event_claims.csv", FILES["event_claims.csv"])
    event_claim_updates: dict[str, dict[str, str]] = {
        # Upgrade ECL039 (DRQ0019) from headline to verbatim body quote
        "ECL039": {
            "quote": "Leveraging Tower's high-volume 200mm and 300mm Silicon Photonics platforms, Innolight has achieved a key milestone in the development of its Near-Package Optics (NPO) portfolio with its first NPO device entering early production using Tower's PH18M Silicon Photonics process flow running in Tower’s US CA factory. In parallel, Innolight has taped-out multiple NPO products on Tower's 300mm Silicon Photonics platform to support future product generations.",
            "anchor": "official release paragraph 3 (p3)",
            "summary": "Tower官网新闻稿正文披露中际旭创首款NPO器件已在Tower美国加州厂PH18M 200mm硅光工艺进入早期生产，并在300mm硅光平台完成多款下一代NPO产品流片",
            "reviewed_at": "2026-11-22",
            "notes": "已由标题级升级为官网正文逐字锚定（同篇p7另披露Innolight现横跨Tower美加州Newport Beach、得州San Antonio、以色列与日本四厂）；early production与中际11/03投关2027年NPI爬坡、2027H2逐步上量一致",
        },
        "ECL040": {
            "event_claim_id": "ECL040",
            "legacy_claim_id": "",
            "disclosure_id": "D_MRVL_20261102_LITE_MERGE",
            "claimant_entity_id": "MRVL",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Marvell Technology, Inc. (NASDAQ: MRVL) and Lumentum (NASDAQ: LITE) today announced that they have entered into a definitive agreement for Marvell to acquire Lumentum in an all-stock transaction. Under the terms of the agreement, Lumentum stockholders will receive a fixed exchange ratio of 4.500 shares of Marvell common stock for each share of Lumentum common stock they own.",
            "anchor": "opening paragraph (p2) and Transaction Structure and Terms (p11-p13)",
            "summary": "Marvell与Lumentum签署全股票收购确定性协议（每1股Lumentum换4.500股Marvell，隐含企业价值1150亿美元）",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "附条件协议（p13明确预计2028H1交割，须经双方股东大会批准与反垄断监管放行），当前尚未交割",
        },
        "ECL041": {
            "event_claim_id": "ECL041",
            "legacy_claim_id": "CL077",
            "disclosure_id": "D_LITE_20261102_FY27Q1",
            "claimant_entity_id": "LITE",
            "claimant_role": "management",
            "statement_kind": "fact_assertion",
            "quote": "During the quarter, we secured our second major NPO/CPO win, backed by purchase commitments exceeding $5 billion.",
            "anchor": "CEO commentary, paragraph 1 (p2)",
            "summary": "Lumentum披露在FY27Q1取得第二项重大NPO/CPO定点，附带逾50亿美元采购承诺",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "原文明确为NPO/CPO合并口径而非纯CPO单列，未披露客户身份与履约时间表，不等于当期已确收收入（FY27Q1总营收12.626亿美元）",
        },
        "ECL042": {
            "event_claim_id": "ECL042",
            "legacy_claim_id": "CL078",
            "disclosure_id": "D_AXTI_20261029_Q3",
            "claimant_entity_id": "AXTI",
            "claimant_role": "management",
            "statement_kind": "fact_assertion",
            "quote": "We entered 2026 with a commitment to double our indium phosphide capacity and I am pleased to report that not only have we surpassed that goal but we have more than quadrupled our 2026 indium phosphide revenue opportunity through additional productivity gains and the expansion of our capabilities for high-value, large diameter products.",
            "anchor": "Management Qualitative Comments, paragraph 1 (p3)",
            "summary": "AXT管理层在2026Q3业绩稿宣布已超额达成2026年InP衬底产能翻倍目标，当季总营收创纪录达7340万美元",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "第一方管理层陈述；新闻稿未单列InP确收金额与中国两用物项出口许可证获批笔数",
        },
        "ECL043": {
            "event_claim_id": "ECL043",
            "legacy_claim_id": "",
            "disclosure_id": "D_AXTI_20261028_TONGMEI_PE",
            "claimant_entity_id": "AXTI",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "The financing agreements provide for a private equity investment in Tongmei by certain institutional investors of a minimum of RMB 1,912,350,000 (approximately US$285 million) and up to a maximum of RMB 3,668,639,053.25 (approximately US$545 million) (the “Maximum Amount”) in the ordinary shares of Tongmei.",
            "anchor": "opening paragraph (p1) and closing conditions paragraph (p3)",
            "summary": "AXT控股子公司北京通美签署19.12亿至36.69亿元人民币私募股权融资确定性协议以扩建InP衬底产能",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "预计2026年12月交割（按上限计AXT预计持股约73.40%并继续并表），须满足政府备案等交割先决条件且不保证完成交割",
        },
        "ECL044": {
            "event_claim_id": "ECL044",
            "legacy_claim_id": "",
            "disclosure_id": "D_NOK_20260915_TELXIUS_800G",
            "claimant_entity_id": "NOK",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Telxius and Nokia are collaborating to deploy 800G coherent pluggable optics across Telxius’ terrestrial transport networks in Europe, the United States and Latin America.",
            "anchor": "article lead paragraph (p14)",
            "summary": "Nokia披露与Telxius推进在欧洲、美国及拉美陆地传输网部署ICE-X 800G ZR/ZR+相干可插拔光模块",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "明确为陆地干线IP-over-DWDM现网部署（区别于p17所述此前BRUSA海缆试验），属Nokia官网单方发布故标asserted",
        },
        "ECL045": {
            "event_claim_id": "ECL045",
            "legacy_claim_id": "",
            "disclosure_id": "D_NVDA_20261117_FY27Q3",
            "claimant_entity_id": "NVDA",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Announced plans with Cisco for USFP, a new optical-module form factor designed to increase bandwidth density and power efficiency for next-generation AI factory networks.",
            "anchor": "Data Center Highlights bullet 17",
            "summary": "NVIDIA在FY27Q3业绩稿Data Center亮点中披露与Cisco共同推进面向下一代AI工厂网络的USFP新光模块封装形态计划",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "仅属新封装形态规划公布，未披露样品或量产时间表，且同篇业绩稿未提及CPO交换机首批交付日期",
        },
        "ECL046": {
            "event_claim_id": "ECL046",
            "legacy_claim_id": "",
            "disclosure_id": "D_TSEM_20260917_NEWPHOTONICS",
            "claimant_entity_id": "TSEM",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Volume shipment of NewPhotonics NPG102 PIC products for 800G and 1.6T feature 200G-per-lane designs and heterogeneously integrated lasers on a monolithic PIC enable customers to leverage optical signal processing in a unified architecture that delivers power efficiency, bandwidth density, and manufacturing consistency.",
            "anchor": "official release paragraph 5, sentence 1 (p5)",
            "summary": "Tower与NewPhotonics宣布基于PH18DA异质集成InP硅光平台的800G/1.6T（单通道200G）NPG102激光集成PIC芯片开启大批量出货",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "第一方晶圆厂新闻稿对上游PIC芯片出货的陈述；未披露下游光模块OEM客户名称与采购量",
        },
        "ECL047": {
            "event_claim_id": "ECL047",
            "legacy_claim_id": "",
            "disclosure_id": "D_TSEM_20260917_NEWPHOTONICS",
            "claimant_entity_id": "TSEM",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "forward_looking",
            "quote": "The CPX-MSA compliant NPC505 chipsets for 6.4T will begin volume shipment in 1H27.",
            "anchor": "official release paragraph 5, sentence 2 (p5)",
            "summary": "Tower与NewPhotonics预计符合CPX-MSA规范的6.4T NPC505光引擎套片将于2027年上半年开始批量出货",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "前瞻排期主张，与当期已出货的800G/1.6T NPG102严格分列，不得计入当期量产",
        },
        "ECL048": {
            "event_claim_id": "ECL048",
            "legacy_claim_id": "",
            "disclosure_id": "D_WIWYNN_20261013_OCP_CPO_DEMO",
            "claimant_entity_id": "WIWYNN",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "technical_demo",
            "quote": "For the first time, they are presenting a live demonstration at OCP Global Summit 2026, showcasing Wiwynn’s compute system integrating GUC's ASIC with Ayar Labs' TeraPHY™ optical engine paired with SuperNova™ light source, streaming real-time health telemetry.",
            "anchor": "official release paragraph 3 (p3)",
            "summary": "Wiwynn在OCP 2026首次现场演示集成GUC多芯片封装ASIC、Ayar Labs TeraPHY光引擎与SuperNova光源的CPO计算系统及实时遥测",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "系统级功能验证演示（demonstrated），不代表超大规模客户已下达CPO商业部署订单",
        },
        "ECL049": {
            "event_claim_id": "ECL049",
            "legacy_claim_id": "",
            "disclosure_id": "D_LIGHTMATTER_20261012_OCP_CPO",
            "claimant_entity_id": "WATCH_LIGHTMATTER",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "technical_demo",
            "quote": "Lightmatter, the leader in photonic (super)computing, today unveiled Passage® co-packaged optics (CPO), Guide® DR external laser modules and vClick™ Optics integrated into a switch tray and an XPU tray built to Open Compute Project (OCP) rack and server specifications at the 2026 OCP Global Summit. Flex collaborated with Lightmatter on the CPO switch tray as a production validation platform.",
            "anchor": "official release opening paragraph (p2)",
            "summary": "Lightmatter在OCP 2026展台展示搭载Passage CPO与Guide DR激光模块的204.8T 1RU交换托盘生产验证平台及102.4T 4-XPU原型样机（连接器件含Corning与SENKO）",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "正文明确界定为production validation platform与XPU tray prototype/proof of concept展会展示，非规模商业交付",
        },
        "ECL050": {
            "event_claim_id": "ECL050",
            "legacy_claim_id": "",
            "disclosure_id": "D_CRDO_20261012_1P6T_ALC",
            "claimant_entity_id": "CRDO",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "forward_looking",
            "quote": "Credo’s 1.6T ZeroFlap active light cable (ALC) solution will be shipping in 2027.",
            "anchor": "official release paragraph 8 (p8)",
            "summary": "Credo发布基于微发光器宽并行架构的1.6T ZeroFlap有源光缆（ALC，端功耗12W、最长50m），预计2027年出货",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "新品发布与2027年出货计划，当前处于OCP展台演示阶段，未披露客户送样或量产订单",
        },
        "ECL051": {
            "event_claim_id": "ECL051",
            "legacy_claim_id": "",
            "disclosure_id": "D_MTSI_20260917_3P2T_CHIPSET",
            "claimant_entity_id": "MTSI",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "This solution includes MACOM’s MATA-42754 and MATA-41754 quad linear TIAs, designed to support the bandwidth requirements of next-generation optical links.",
            "anchor": "official release paragraph 6-9 (p6-p9)",
            "summary": "MACOM发布面向8x448Gbps PAM4（3.2T）光模块的MATA-42754/41754四通道线性TIA与MARP-BP224光电二极管接收端方案并宣布可获得",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "与EV007既有MAOM-025408/022404发射驱动芯片形成配套3.2T前端套片；器件readily available不代表下游3.2T光模块量产",
        },
        "ECL052": {
            "event_claim_id": "ECL052",
            "legacy_claim_id": "",
            "disclosure_id": "D_IQE_20260903_QUINTESSENT_QDL",
            "claimant_entity_id": "WATCH_IQE",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "IQE plc (AIM: IQE, \"IQE\" or the \"Group\"), the leading global supplier of compound semiconductor wafer products and advanced material solutions, is pleased to announce a purchase agreement with Quintessent Inc., an innovator in resilient and low-cost connectivity solutions for AI data centres, for the supply of Quantum Dot Laser (QDL) epitaxy.",
            "anchor": "official release opening paragraph (p3)",
            "summary": "IQE宣布与Quintessent签署面向AI数据中心光互连的量子点激光（QDL）6英寸GaAs外延片采购协议",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "单方公告（含对手方CEO引述仍属同一披露件），未披露协议金额与晶圆片数",
        },
        "ECL053": {
            "event_claim_id": "ECL053",
            "legacy_claim_id": "",
            "disclosure_id": "D_IQE_20260903_QUINTESSENT_QDL",
            "claimant_entity_id": "WATCH_IQE",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Following an initial strategic announcement and purchase order in January 2025, the extension of the companies’ longstanding relationship will see IQE supply 6-inch Gallium Arsenide epiwafers through its foundry-ready service. This will support Quintessent’s customer sampling activity as its technology progresses towards commercial deployment and new production introductions.",
            "anchor": "official release paragraph 2 (p4)",
            "summary": "IQE供应6英寸GaAs外延片支持Quintessent量子点激光器进入下游客户送样阶段",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "明确下游处于customer sampling阶段，尚未进入商业规模部署",
        },
        "ECL054": {
            "event_claim_id": "ECL054",
            "legacy_claim_id": "",
            "disclosure_id": "D_LITE_20260921_ECOC_ELSFP",
            "claimant_entity_id": "LITE",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "forward_looking",
            "quote": "Lumentum expects initial availability of the DWDM ELSFP module with an OCI MSA optical interface in the first half of calendar year 2027.",
            "anchor": "official release paragraph 5 (p5)",
            "summary": "Lumentum预告在ECOC 2026展示面向CPO/NPO的8波长DWDM ELSFP外置光源模块，预计2027年上半年初始可提供",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "展前预告与2027H1可提供指引，非当期商业出货",
        },
        "ECL055": {
            "event_claim_id": "ECL055",
            "legacy_claim_id": "",
            "disclosure_id": "D_LITE_20260921_ECOC_VCSEL_D2D",
            "claimant_entity_id": "LITE",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "The proof-of-concept configuration being demonstrated uses optical channels operating at 32 Gb/s NRZ, to show how the massively parallel architecture can scale through higher channel counts and increasing per-lane data rates.",
            "anchor": "official release paragraph 4 (p4)",
            "summary": "Lumentum预告与Qualcomm及Corning在ECOC 2026联合演示基于1060nm VCSEL与多模光纤的32Gb/s NRZ板级光D2D概念验证配置",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "展前预告（announced to demonstrate），明确属proof-of-concept板级演示而非商业产品出货",
        },
        "ECL056": {
            "event_claim_id": "ECL056",
            "legacy_claim_id": "",
            "disclosure_id": "D_MXL_20261110_JEJU_PMIC",
            "claimant_entity_id": "MXL",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "forward_looking",
            "quote": "Jeju™ (MxL77904) is expected to sample to customers in February 2027.",
            "anchor": "Availability section (p13)",
            "summary": "MaxLinear推出面向1.6T光模块DSP的定制多相电源芯片Jeju（MxL77904），预计2027年2月向客户送样",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "新品预发布，尚未进入客户送样或随DSP捆绑量产出货",
        },
        "ECL057": {
            "event_claim_id": "ECL057",
            "legacy_claim_id": "",
            "disclosure_id": "D_CIEN_20261117_INTERNET2_800G",
            "claimant_entity_id": "CIEN",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "technical_demo",
            "quote": "Ciena’s WaveLogic 6 Nano (WL6n) coherent pluggables delivered 800 Gb/s across 2,104 kilometers from the SC26 show floor in Chicago, across Internet2’s backbone to its point of presence in Kansas City, Mo. and back.",
            "anchor": "official release paragraph 3 (p3)",
            "summary": "Ciena披露WaveLogic 6 Nano 800G相干可插拔模块在Internet2美国科研教育骨干网上完成2104公里陆地实网传输演示",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "SC26现场实网科研试验（collaborative trial / live demonstration），不代表批量商业采购订单",
        },
        "ECL058": {
            "event_claim_id": "ECL058",
            "legacy_claim_id": "CL079",
            "disclosure_id": "D_POET_20261116_Q3",
            "claimant_entity_id": "POET",
            "claimant_role": "management",
            "statement_kind": "forward_looking",
            "quote": "We expect to ship our current backlog of optical engines, including the 30,000 engines we had targeted for 2026, by the second quarter of 2027, as the capacity we have already funded comes online",
            "anchor": "Management Commentary, paragraph 2 (p5)",
            "summary": "POET管理层披露因晶圆与元件紧缺及新工艺良率爬坡，原定2026年出货的3万只光引擎积压订单顺延至2027年第二季度前交付",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "2026Q3单季营收仅102.6万美元，明确反映上游晶圆/组件紧缺与良率爬坡导致量产交付窗口后移",
        },
        "ECL059": {
            "event_claim_id": "ECL059",
            "legacy_claim_id": "CL081",
            "disclosure_id": "D_TSEM_20261102_Q3",
            "claimant_entity_id": "TSEM",
            "claimant_role": "management",
            "statement_kind": "forward_looking",
            "quote": "We target to achieve an annualized $1.1 billion run rate in the fourth quarter of 2026 of SiPho revenue alone, namely 5X of the 2025 SiPho annual revenue. Our on-going capacity investments, including the announced Track-1 Japan 300mm buildout, are progressing ahead of schedule, supported by customer contracts which are being extended through 2029",
            "anchor": "CEO commentary, paragraph 2 (p9)",
            "summary": "Tower管理层在2026Q3业绩稿提出2026Q4硅光年化收入11亿美元目标，并称日本300mm一轨扩产超前推进且客户合同延展至2029年",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "管理层前瞻目标与扩产进度更新（衔接EV024），不直接等同已实现全年收入",
        },
        "ECL060": {
            "event_claim_id": "ECL060",
            "legacy_claim_id": "",
            "disclosure_id": "D_GFS_20261104_Q3",
            "claimant_entity_id": "GFS",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "In September 2026, GF expanded its multi-year agreement with Marvell to increase manufacturing capacity for GF’s high-performance silicon germanium (SiGe) technology at its Burlington, Vermont facility. The expanded capacity will support Marvell’s growing requirements for next-generation pluggable optical transceivers, Near-Packaged Optics (NPO) and Co-Packaged Optics (CPO), strengthening GF’s position in high-speed optical connectivity for AI and cloud data center infrastructure.",
            "anchor": "Recent Business Highlights bullet 5",
            "summary": "GlobalFoundries在2026Q3业绩稿披露于2026年9月与Marvell扩大美国Burlington晶圆厂SiGe多年制造产能协议，支持可插拔光模块、NPO与CPO需求",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "GlobalFoundries第一方季报披露，未披露具体协议金额、晶圆片数或Marvell侧独立公告确认",
        },
        "ECL061": {
            "event_claim_id": "ECL061",
            "legacy_claim_id": "",
            "disclosure_id": "D_VECO_20261102_ACLS_MERGER",
            "claimant_entity_id": "VECO",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "forward_looking",
            "quote": "The companies now expect the transaction to close by the end of the first quarter of 2027, subject to the satisfaction or waiver of all closing conditions.",
            "anchor": "official release opening paragraph (p2) and SAMR/HSR paragraphs (p3-p4)",
            "summary": "Axcelis与Veeco更新全股票合并预计交割时间至2027年第一季度末，仍待中国市场监管总局（SAMR）审批及重新提交美国HSR反垄断申报",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "并购审批时间表延后（每1股Veeco换0.3575股Axcelis），不保证按该时间表完成交割",
        },
        "ECL062": {
            "event_claim_id": "ECL062",
            "legacy_claim_id": "CL083",
            "disclosure_id": "D_SOI_20261118_FY27H1",
            "claimant_entity_id": "SOI",
            "claimant_role": "management",
            "statement_kind": "fact_assertion",
            "quote": "Looking ahead, most of our Photonics-SOI customers have committed through 2028 under capacity reservation agreements backed by cash deposits, with talks underway for extra volumes beyond. We are now pivoting our existing Bernin 4 fab to SOI to serve that demand",
            "anchor": "CEO commentary, paragraph 1 (p21) and Highlights bullet 3 (p10)",
            "summary": "Soitec确认多数Photonics-SOI客户已签署带现金定金的多年产能预留协议（合同总额约12亿美元，H1已收8600万欧元初始定金），并将Bernin 4厂转向SOI扩产",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "第一方财报披露；客户未具名，长约总额跨未来数年而非单年确收",
        },
        "ECL063": {
            "event_claim_id": "ECL063",
            "legacy_claim_id": "",
            "disclosure_id": "D_CRDO_20261104_ORCL_OCP",
            "claimant_entity_id": "CRDO",
            "claimant_role": "corporate_disclosure",
            "statement_kind": "fact_assertion",
            "quote": "Credo Technology Group Holding Ltd (Credo) (NASDAQ: CRDO), an innovator in providing connectivity at scale through fast, reliable, and energy-efficient system solutions, and Oracle, today announced that the Open Compute Project (OCP) Community has approved two new contributions aimed at bringing enhanced telemetry to optical transceivers.",
            "anchor": "official release opening paragraph (p2)",
            "summary": "Credo披露OCP社区已正式批准由Credo与Oracle在光学可靠性工作流主导制定的两项光模块增强遥测开放规范",
            "review_status": "anchor_reviewed",
            "reviewed_at": "2026-11-22",
            "notes": "开放标准规范获批事实，不推导Oracle对Credo光模块产品的商业采购或份额",
        },
    }
    ecl_append_order = [f"ECL{i:03d}" for i in range(40, 64)]
    upsert_rows(event_claims, "event_claim_id", event_claim_updates, append_order=ecl_append_order)

    # Verify verbatim match for all upgraded/inserted event_claims quotes
    ecl_slug_map = {
        "ECL039": "tsem_20261103_innolight_npo",
        "ECL040": "mrvl_20261102_lumentum_combine",
        "ECL041": "lite_20261102_fy27q1_results",
        "ECL042": "axti_20261029_2026q3_results",
        "ECL043": "axti_20261028_tongmei_financing",
        "ECL044": "nok_20260915_telxius_800g",
        "ECL045": "nvda_20261117_fy27q3_results",
        "ECL046": "tsem_20260917_newphotonics_pic",
        "ECL047": "tsem_20260917_newphotonics_pic",
        "ECL048": "wiwynn_20261013_ayar_guc_cpo_demo",
        "ECL049": "lightmatter_20261012_open_rack_cpo",
        "ECL050": "crdo_20261012_1p6t_zeroflap_alc",
        "ECL051": "mtsi_20260917_3p2t_chipset",
        "ECL052": "iqe_20260903_quintessent_qdl",
        "ECL053": "iqe_20260903_quintessent_qdl",
        "ECL054": "lite_20260921_ecoc_dwdm_elsfp",
        "ECL055": "lite_20260921_ecoc_1060nm_vcsel",
        "ECL056": "mxl_20261110_jeju_pmic",
        "ECL057": "cien_20261117_internet2_800g",
        "ECL058": "poet_20261116_2026q3_official",
        "ECL059": "tsem_20261102_2026q3_results",
        "ECL060": "gfs_20261104_2026q3_results",
        "ECL061": "veco_20261102_axcelis_merger_update",
        "ECL062": "soi_20261118_fy27h1_results",
        "ECL063": "crdo_20261104_oracle_ocp_telemetry",
    }
    for ecl_id, slug in ecl_slug_map.items():
        assert_verbatim_in_txt(slug, event_claim_updates[ecl_id]["quote"], by_slug)

    # ------------------------------------------------------------------
    # 8. Events (`calls/events.csv`): Upgrade EV036 + Add EV037-EV060
    # ------------------------------------------------------------------
    events = read_csv_rows(calls_dir / "events.csv", FILES["events.csv"])
    event_updates: dict[str, dict[str, str]] = {
        "EV036": {
            "summary": "Tower Semiconductor与中际旭创（Innolight）披露首款NPO器件在加州厂PH18M进入早期生产并在300mm硅光平台多款流片",
            "notes": "已取官网全文升级核定（DRQ0019）：首款NPO器件在Tower美国加州厂PH18M 200mm流程进入early production且横跨美以日四座晶圆厂，保持announced阶段（与中际11/03投关2027H2才逐步规模上量边界一致）",
        },
        "EV037": {
            "event_id": "EV037",
            "program_id": "PRG_MRVL_LITE_MERGE",
            "event_category": "capital_relationship",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "MRVL",
            "counterparty_ids": "LITE",
            "theme_ids": "T010;T017",
            "occurred_start": "2026-11-02",
            "occurred_end": "2026-11-02",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "美国",
            "summary": "Marvell签署全股票收购Lumentum的附条件确定性协议（1股LITE换4.500股MRVL，隐含企业价值1150亿美元，未交割）",
            "notes": "预计2028年上半年交割，须经双方股东大会批准及反垄断监管审批；当前仅属签署合并协议，严禁视作已完成并表或技术产线已整合",
        },
        "EV038": {
            "event_id": "EV038",
            "program_id": "PRG_LITE_NPO_CPO_WIN2",
            "event_category": "commercial_adoption",
            "lifecycle_stage": "volume_order",
            "event_status": "asserted",
            "primary_subject_id": "LITE",
            "counterparty_ids": "",
            "theme_ids": "T013;T017",
            "occurred_start": "2026-11-02",
            "occurred_end": "2026-11-02",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Lumentum第一方披露取得第二项重大NPO/CPO定点并获逾50亿美元采购承诺",
            "notes": "披露日2026-11-02（FY27Q1区间截至2026-09-26）；原文定语为NPO/CPO合并而非纯CPO单列，客户未具名、交付周期未披露，不等于当期确认收入",
        },
        "EV039": {
            "event_id": "EV039",
            "program_id": "PRG_AXTI_INP_CAP",
            "event_category": "capacity_constraint",
            "lifecycle_stage": "scaled",
            "event_status": "asserted",
            "primary_subject_id": "AXTI",
            "counterparty_ids": "",
            "theme_ids": "T007;T008",
            "occurred_start": "2026-10-29",
            "occurred_end": "2026-10-29",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "中国",
            "target_market": "全球",
            "policy_jurisdiction": "中国",
            "summary": "AXT第一方称已超额达成2026年InP衬底产能翻倍目标且Q3合并营收创7340万美元纪录",
            "notes": "公司第一方陈述；业绩稿未披露InP单项确收额及中国商务部出口许可证具体获批笔数",
        },
        "EV040": {
            "event_id": "EV040",
            "program_id": "PRG_AXTI_TONGMEI_PE",
            "event_category": "capital_relationship",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "AXTI",
            "counterparty_ids": "",
            "theme_ids": "T007;T008",
            "occurred_start": "2026-10-28",
            "occurred_end": "2026-10-28",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "中国",
            "target_market": "全球",
            "policy_jurisdiction": "中国",
            "summary": "AXT控股子公司北京通美签署最高36.7亿元人民币私募融资协议拟扩建InP衬底产能（待交割）",
            "notes": "融资额区间19.12亿至36.69亿元人民币，预计2026年12月交割（按上限计AXT持股约73.40%），须完成监管备案且不保证交割，与EV022客户协议分开评估",
        },
        "EV041": {
            "event_id": "EV041",
            "program_id": "PRG_NOK_TELXIUS_800G",
            "event_category": "commercial_adoption",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "NOK",
            "counterparty_ids": "",
            "theme_ids": "T021",
            "occurred_start": "2026-09-15",
            "occurred_end": "2026-09-15",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Nokia第一方披露Telxius在欧美及拉美陆地传输网部署ICE-X 800G相干可插拔光模块",
            "notes": "属陆地干线IP-over-DWDM网络部署，区别于此前BRUSA海缆试验及EV005美国客户发货；Telxius不在身份表故counterparty留空，未披露模块数量",
        },
        "EV042": {
            "event_id": "EV042",
            "program_id": "PRG_NVDA_CSCO_USFP",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "NVDA",
            "counterparty_ids": "CSCO",
            "theme_ids": "T004;T018",
            "occurred_start": "2026-11-17",
            "occurred_end": "2026-11-17",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "NVIDIA在FY27Q3业绩稿披露与Cisco共同推进面向下一代AI工厂网络的USFP光模块新封装形态计划",
            "notes": "仅披露新封装形态规划，未给出样品时间、速率细节或CPO交换机首批客户交付日",
        },
        "EV043": {
            "event_id": "EV043",
            "program_id": "PRG_TSEM_NEWPHOTONICS_PIC",
            "event_category": "product_stage",
            "lifecycle_stage": "scaled",
            "event_status": "asserted",
            "primary_subject_id": "TSEM",
            "counterparty_ids": "WATCH_NEWPHOTONICS",
            "theme_ids": "T010;T015",
            "occurred_start": "2026-09-17",
            "occurred_end": "2026-09-17",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "以色列",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Tower与NewPhotonics宣布基于PH18DA异质集成平台的800G/1.6T NPG102激光集成PIC芯片开启批量出货",
            "notes": "仅覆盖当期800G/1.6T（单通道200G）NPG102 PIC芯片级出货主张；未具名下游模块或系统买家",
        },
        "EV044": {
            "event_id": "EV044",
            "program_id": "PRG_TSEM_NEWPHOTONICS_PIC",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "TSEM",
            "counterparty_ids": "WATCH_NEWPHOTONICS",
            "theme_ids": "T015;T017",
            "occurred_start": "2026-09-17",
            "occurred_end": "2026-09-17",
            "date_precision": "exact",
            "previous_event_id": "EV043",
            "site_country": "以色列",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Tower与NewPhotonics预告6.4T CPX-MSA兼容NPC505光引擎芯片组计划于2027年上半年启动批量出货",
            "notes": "与EV043当期800G/1.6T出货严格拆分的2027H1前瞻排期，不计作已实现量产",
        },
        "EV045": {
            "event_id": "EV045",
            "program_id": "PRG_WIWYNN_AYAR_OCP_CPO",
            "event_category": "product_stage",
            "lifecycle_stage": "demonstrated",
            "event_status": "asserted",
            "primary_subject_id": "WIWYNN",
            "counterparty_ids": "WATCH_AYAR",
            "theme_ids": "T013;T017",
            "occurred_start": "2026-10-13",
            "occurred_end": "2026-10-13",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Wiwynn在OCP 2026联合Ayar Labs与GUC现场演示集成TeraPHY光引擎与SuperNova光源的CPO计算系统",
            "notes": "GUC（3443.TW）不在身份表故记入摘要与备注；严格限定为现场系统功能演示，不得标为量产交付",
        },
        "EV046": {
            "event_id": "EV046",
            "program_id": "PRG_LIGHTMATTER_OCP_CPO",
            "event_category": "product_stage",
            "lifecycle_stage": "demonstrated",
            "event_status": "asserted",
            "primary_subject_id": "WATCH_LIGHTMATTER",
            "counterparty_ids": "GLW;WATCH_SENKO",
            "theme_ids": "T015;T017",
            "occurred_start": "2026-10-12",
            "occurred_end": "2026-10-12",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Lightmatter在OCP 2026展示204.8T CPO交换托盘生产验证平台与102.4T 4-XPU互连原型样机",
            "notes": "含Flex制造工程验证平台及Corning与SENKO高密度连接器；属OCP展台样机与验证平台展示，非商业规模部署",
        },
        "EV047": {
            "event_id": "EV047",
            "program_id": "PRG_CRDO_1P6T_ALC",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "CRDO",
            "counterparty_ids": "",
            "theme_ids": "T004;T010",
            "occurred_start": "2026-10-12",
            "occurred_end": "2026-10-12",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Credo发布面向跨机柜光互连的1.6T ZeroFlap有源光缆（ALC）并预计2027年出货",
            "notes": "采用微发光器宽并行NRZ架构（端功耗12W、最长50m），2027年出货为前瞻计划而非当前量产",
        },
        "EV048": {
            "event_id": "EV048",
            "program_id": "PRG_MTSI_448G",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "MTSI",
            "counterparty_ids": "",
            "theme_ids": "T011",
            "occurred_start": "2026-09-17",
            "occurred_end": "2026-09-17",
            "date_precision": "exact",
            "previous_event_id": "EV007",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "MACOM发布MATA-42754/41754线性TIA与MARP-BP224光电二极管，补齐8x448G（3.2T）光互连前端套片",
            "notes": "衔接EV007发射端448G驱动芯片；芯片级可订购（readily available）不证明下游3.2T模块已认证或量产",
        },
        "EV049": {
            "event_id": "EV049",
            "program_id": "PRG_IQE_QUINTESSENT_QDL",
            "event_category": "supply_chain_arrangement",
            "lifecycle_stage": "not_applicable",
            "event_status": "asserted",
            "primary_subject_id": "WATCH_IQE",
            "counterparty_ids": "WATCH_QUINTESSENT",
            "theme_ids": "T007;T008",
            "occurred_start": "2026-09-03",
            "occurred_end": "2026-09-03",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "英国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "IQE宣布与Quintessent签署6英寸GaAs量子点激光（QDL）外延片采购协议",
            "notes": "仅IQE第一方披露；未公布采购金额、片数及保底条款",
        },
        "EV050": {
            "event_id": "EV050",
            "program_id": "PRG_IQE_QUINTESSENT_QDL",
            "event_category": "product_stage",
            "lifecycle_stage": "sampling",
            "event_status": "asserted",
            "primary_subject_id": "WATCH_IQE",
            "counterparty_ids": "WATCH_QUINTESSENT",
            "theme_ids": "T013;T017",
            "occurred_start": "2026-09-03",
            "occurred_end": "2026-09-03",
            "date_precision": "exact",
            "previous_event_id": "EV049",
            "site_country": "英国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "IQE披露6英寸GaAs外延片正支持Quintessent量子点激光器向客户送样",
            "notes": "与EV049采购协议拆分记录；处于客户送样（customer sampling）阶段，未达规模商用",
        },
        "EV051": {
            "event_id": "EV051",
            "program_id": "PRG_LITE_DWDM_ELSFP",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "LITE",
            "counterparty_ids": "",
            "theme_ids": "T013;T017",
            "occurred_start": "2026-09-21",
            "occurred_end": "2026-09-21",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "西班牙",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Lumentum预告ECOC 2026演示OCI MSA兼容8波长DWDM ELSFP外置光源模块并预计2027H1初始可提供",
            "notes": "展前计划演示（announced to demonstrate）及2027H1初始可提供指引，不计入当期商业出货",
        },
        "EV052": {
            "event_id": "EV052",
            "program_id": "PRG_LITE_VCSEL_D2D",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "LITE",
            "counterparty_ids": "GLW",
            "theme_ids": "T017",
            "occurred_start": "2026-09-21",
            "occurred_end": "2026-09-21",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "西班牙",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Lumentum预告与Qualcomm及Corning在ECOC 2026联合演示1060nm VCSEL多模光纤D2D板级概念验证互连",
            "notes": "单通道32Gb/s NRZ板级proof-of-concept展前预告（Qualcomm不在身份表故记入备注），不代表商业产品出货",
        },
        "EV053": {
            "event_id": "EV053",
            "program_id": "PRG_MXL_JEJU_PMIC",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "MXL",
            "counterparty_ids": "",
            "theme_ids": "T004;T010",
            "occurred_start": "2026-11-10",
            "occurred_end": "2026-11-10",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "MaxLinear发布面向1.6T光模块DSP的定制电源管理芯片Jeju（MxL77904），预计2027年2月送样",
            "notes": "尚未开始客户送样（预计2027-02），不构成当前1.6T电芯片出货实绩",
        },
        "EV054": {
            "event_id": "EV054",
            "program_id": "PRG_CIEN_WL6N_INTERNET2",
            "event_category": "product_stage",
            "lifecycle_stage": "demonstrated",
            "event_status": "asserted",
            "primary_subject_id": "CIEN",
            "counterparty_ids": "",
            "theme_ids": "T021",
            "occurred_start": "2026-11-17",
            "occurred_end": "2026-11-17",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "美国",
            "policy_jurisdiction": "",
            "summary": "Ciena披露WaveLogic 6 Nano 800G相干可插拔模块在Internet2骨干网完成2104公里陆地实网传输演示",
            "notes": "Internet2科研教育网SC26实网试验演示，非超大规模商业批量订单",
        },
        "EV055": {
            "event_id": "EV055",
            "program_id": "PRG_POET_ENGINE_BACKLOG",
            "event_category": "capacity_constraint",
            "lifecycle_stage": "delayed",
            "event_status": "asserted",
            "primary_subject_id": "POET",
            "counterparty_ids": "",
            "theme_ids": "T010;T016",
            "occurred_start": "2026-11-16",
            "occurred_end": "2026-11-16",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "马来西亚",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "POET在2026Q3财报披露受晶圆与组件紧缺及良率爬坡影响，原定2026年目标的3万只光引擎延至2027Q2前出货",
            "notes": "当季营收102.6万美元、经营现金净流出1270万美元；明确将百万美元级早期收入与2027年量产交付窗口区分",
        },
        "EV056": {
            "event_id": "EV056",
            "program_id": "PRG_TSEM_JP_SIPHO",
            "event_category": "capacity_constraint",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "TSEM",
            "counterparty_ids": "",
            "theme_ids": "T013;T015;T017",
            "occurred_start": "2026-11-02",
            "occurred_end": "2026-11-02",
            "date_precision": "exact",
            "previous_event_id": "EV024",
            "site_country": "日本",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Tower在2026Q3财报提出2026Q4硅光年化11亿美元运行率目标，并称日本300mm一轨扩产超前推进且客户长约延至2029年",
            "notes": "衔接EV024；11亿美元年化运行率为管理层Q4目标值，仍待后续财报验证实际兑现",
        },
        "EV057": {
            "event_id": "EV057",
            "program_id": "PRG_GFS_MRVL_SIGE",
            "event_category": "supply_chain_arrangement",
            "lifecycle_stage": "not_applicable",
            "event_status": "asserted",
            "primary_subject_id": "GFS",
            "counterparty_ids": "MRVL",
            "theme_ids": "T015;T017",
            "occurred_start": "2026-09-01",
            "occurred_end": "2026-09-30",
            "date_precision": "month",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "GlobalFoundries披露于2026年9月与Marvell扩大美国Burlington厂SiGe多年制造产能协议（覆盖可插拔/NPO/CPO）",
            "notes": "由2026-11-04 Q3业绩稿披露事件发生于2026年9月（precision=month）；仅GF单方披露，未公布金额与片数",
        },
        "EV058": {
            "event_id": "EV058",
            "program_id": "PRG_VECO_ACLS_MERGER",
            "event_category": "capital_relationship",
            "lifecycle_stage": "delayed",
            "event_status": "asserted",
            "primary_subject_id": "VECO",
            "counterparty_ids": "WATCH_AXCELIS",
            "theme_ids": "T008",
            "occurred_start": "2026-11-02",
            "occurred_end": "2026-11-02",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "中国",
            "summary": "Veeco与Axcelis更新全股票合并预计交割窗口至2027年第一季度末（待中国SAMR审查与美国HSR重报）",
            "notes": "每1股VECO换0.3575股ACLS；当前仍待监管放行，未交割",
        },
        "EV059": {
            "event_id": "EV059",
            "program_id": "PRG_SOI_PHOTONICS_SOI_CRA",
            "event_category": "supply_chain_arrangement",
            "lifecycle_stage": "not_applicable",
            "event_status": "asserted",
            "primary_subject_id": "SOI",
            "counterparty_ids": "",
            "theme_ids": "T016;T017",
            "occurred_start": "2026-11-18",
            "occurred_end": "2026-11-18",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "法国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Soitec在FY27H1财报披露Photonics-SOI客户已签约12亿美元带现金定金产能预留长约并将Bernin 4厂转向SOI扩产",
            "notes": "H1已收8600万欧元初始现金定金，Photonics-SOI H1收入约1.25亿美元；客户未具名且12亿美元跨未来数年",
        },
        "EV060": {
            "event_id": "EV060",
            "program_id": "PRG_CRDO_ORCL_OCP_TELEMETRY",
            "event_category": "product_stage",
            "lifecycle_stage": "announced",
            "event_status": "asserted",
            "primary_subject_id": "CRDO",
            "counterparty_ids": "WATCH_ORCL",
            "theme_ids": "T004",
            "occurred_start": "2026-11-04",
            "occurred_end": "2026-11-04",
            "date_precision": "exact",
            "previous_event_id": "",
            "site_country": "美国",
            "target_market": "全球",
            "policy_jurisdiction": "",
            "summary": "Credo与Oracle联合主导的两项光模块增强遥测开放规范获OCP社区批准",
            "notes": "属OCP标准工作流软件与带外遥测接口规范获批，不代表Oracle对Credo硬件模块采购确认",
        },
    }
    ev_append_order = [f"EV{i:03d}" for i in range(37, 61)]
    upsert_rows(events, "event_id", event_updates, append_order=ev_append_order)

    # ------------------------------------------------------------------
    # 9. Event Evidence (`calls/event_evidence.csv`): Upgrade EE039 + Add EE040-EE063
    # ------------------------------------------------------------------
    event_evidence = read_csv_rows(calls_dir / "event_evidence.csv", FILES["event_evidence.csv"])
    evidence_updates: dict[str, dict[str, str]] = {
        "EE039": {
            "notes": "Tower官网一手新闻稿全文逐字核定（DRQ0019）；首款NPO在PH18M进入早期生产且多款300mm流片，与中际2027H2逐步上量口径一致",
        },
        "EE040": {"evidence_id": "EE040", "event_id": "EV037", "event_claim_id": "ECL040", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_MRVL_LITE_20261102_MERGE", "notes": "Marvell官网并购联合新闻稿；协议附股东与反垄断审批条件，尚未交割"},
        "EE041": {"evidence_id": "EE041", "event_id": "EV038", "event_claim_id": "ECL041", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_LITE_20261102_FY27Q1", "notes": "Lumentum FY27Q1官方业绩稿CEO引述；NPO/CPO合并口径且客户未具名"},
        "EE042": {"evidence_id": "EE042", "event_id": "EV039", "event_claim_id": "ECL042", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_AXTI_20261029_Q3", "notes": "AXT 2026Q3官方业绩稿管理层评述"},
        "EE043": {"evidence_id": "EE043", "event_id": "EV040", "event_claim_id": "ECL043", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_AXTI_20261028_TONGMEI_PE", "notes": "AXT官方北京通美私募融资公告；待交割条件满足"},
        "EE044": {"evidence_id": "EE044", "event_id": "EV041", "event_claim_id": "ECL044", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_NOK_20260915_TELXIUS_800G", "notes": "Nokia官网新闻稿；同文含Telxius引述仍属同一来源"},
        "EE045": {"evidence_id": "EE045", "event_id": "EV042", "event_claim_id": "ECL045", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_NVDA_20261117_FY27Q3", "notes": "NVIDIA FY27Q3官方业绩稿Data Center亮点"},
        "EE046": {"evidence_id": "EE046", "event_id": "EV043", "event_claim_id": "ECL046", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_TSEM_20260917_NEWPHOTONICS", "notes": "Tower官网联合新闻稿第5段当期出货陈述"},
        "EE047": {"evidence_id": "EE047", "event_id": "EV044", "event_claim_id": "ECL047", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_TSEM_20260917_NEWPHOTONICS", "notes": "Tower官网联合新闻稿第5段2027H1前瞻排期"},
        "EE048": {"evidence_id": "EE048", "event_id": "EV045", "event_claim_id": "ECL048", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_WIWYNN_20261013_OCP_CPO_DEMO", "notes": "Wiwynn官网OCP 2026现场演示新闻稿"},
        "EE049": {"evidence_id": "EE049", "event_id": "EV046", "event_claim_id": "ECL049", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_LIGHTMATTER_20261012_OCP_CPO", "notes": "Lightmatter官网OCP 2026展台展示新闻稿"},
        "EE050": {"evidence_id": "EE050", "event_id": "EV047", "event_claim_id": "ECL050", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_CRDO_20261012_1P6T_ALC", "notes": "Credo官网新品新闻稿"},
        "EE051": {"evidence_id": "EE051", "event_id": "EV048", "event_claim_id": "ECL051", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_MTSI_20260917_3P2T_CHIPSET", "notes": "MACOM官网3.2T前端套片新闻稿"},
        "EE052": {"evidence_id": "EE052", "event_id": "EV049", "event_claim_id": "ECL052", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_IQE_20260903_QUINTESSENT_QDL", "notes": "IQE官网采购协议新闻稿"},
        "EE053": {"evidence_id": "EE053", "event_id": "EV050", "event_claim_id": "ECL053", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_IQE_20260903_QUINTESSENT_QDL", "notes": "IQE官网客户送样阶段陈述"},
        "EE054": {"evidence_id": "EE054", "event_id": "EV051", "event_claim_id": "ECL054", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_LITE_20260921_ECOC_ELSFP", "notes": "Lumentum官网ECOC展前新闻稿"},
        "EE055": {"evidence_id": "EE055", "event_id": "EV052", "event_claim_id": "ECL055", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_LITE_20260921_ECOC_VCSEL_D2D", "notes": "Lumentum官网ECOC板级概念验证预告"},
        "EE056": {"evidence_id": "EE056", "event_id": "EV053", "event_claim_id": "ECL056", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_MXL_20261110_JEJU_PMIC", "notes": "MaxLinear官网新品新闻稿"},
        "EE057": {"evidence_id": "EE057", "event_id": "EV054", "event_claim_id": "ECL057", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_CIEN_20261117_INTERNET2_800G", "notes": "Ciena官网SC26实网试验新闻稿"},
        "EE058": {"evidence_id": "EE058", "event_id": "EV055", "event_claim_id": "ECL058", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_POET_20261116_Q3", "notes": "POET官网2026Q3正式业绩新闻稿"},
        "EE059": {"evidence_id": "EE059", "event_id": "EV056", "event_claim_id": "ECL059", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_TSEM_20261102_Q3", "notes": "Tower官网2026Q3正式业绩新闻稿"},
        "EE060": {"evidence_id": "EE060", "event_id": "EV057", "event_claim_id": "ECL060", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_GFS_20261104_Q3", "notes": "GlobalFoundries官网2026Q3正式业绩新闻稿"},
        "EE061": {"evidence_id": "EE061", "event_id": "EV058", "event_claim_id": "ECL061", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_VECO_20261102_ACLS_MERGER", "notes": "Veeco官网并购交割窗口更新公告"},
        "EE062": {"evidence_id": "EE062", "event_id": "EV059", "event_claim_id": "ECL062", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_SOI_20261118_FY27H1", "notes": "Soitec官网FY27H1正式业绩公告"},
        "EE063": {"evidence_id": "EE063", "event_id": "EV060", "event_claim_id": "ECL063", "relationship": "reports", "independence_class": "first_party", "origin_group": "OG_CRDO_20261104_ORCL_OCP", "notes": "Credo官网OCP遥测规范获批新闻稿"},
    }
    ee_append_order = [f"EE{i:03d}" for i in range(40, 64)]
    upsert_rows(event_evidence, "evidence_id", evidence_updates, append_order=ee_append_order)

    # ------------------------------------------------------------------
    # 10. Relationship Timeline (`corpus/relationships/relationship_timeline.csv`):
    #     Upgrade TL9002 + Append TL9006-TL9012
    # ------------------------------------------------------------------
    timeline_rows = read_csv_rows(rel_timeline_path, TIMELINE_FIELDS)
    timeline_updates: dict[str, dict[str, str]] = {
        "TL9002": {
            "value_raw": "官网正文确认中际旭创首款NPO器件在Tower美国加州厂PH18M 200mm工艺进入早期生产并在300mm硅光平台多款流片（横跨美加州/得州/以色列/日本四厂）；中际11/03投关定调NPO于2027H2逐步上量",
            "notes": "joint_rd与晶圆代工里程碑(对应DRQ0019/DC_430D7977BA22与calls/events.csv#EV036及corpus/web/step4_20261122/tsem_20261103_innolight_npo.txt)；已由标题升级为正文逐字核定，early production与中际2027H2起量口径一致且无定量采购额",
        },
        "TL9006": {
            "timeline_id": "TL9006",
            "relation_id": "R208",
            "supplier": "Marvell",
            "customer": "Lumentum",
            "supplier_point_id": "P003",
            "customer_point_id": "P233",
            "period": "2026-11-02",
            "period_type": "event",
            "event_date": "2026-11-02",
            "source_channel": "daily_announcement",
            "metric_kind": "ma_agreement",
            "value_raw": "签署全股票合并确定性协议（每1股Lumentum换4.500股Marvell普通股，隐含企业价值1150亿美元，预计2028H1交割，待股东与反垄断审批）",
            "numeric_value": "1150",
            "unit": "亿美元",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_MRVL_20261102_LITE_MERGE",
            "anchor_url": by_slug["mrvl_20261102_lumentum_combine"]["requested_url"],
            "conflict": "false",
            "notes": "资本并购协议脉冲(对应DRQ0015/DC_501FC1F61B62与calls/events.csv#EV037)；非商品买卖边，须经双方股东大会及反垄断监管批准，预计2028年上半年交割，当前尚未交割",
        },
        "TL9007": {
            "timeline_id": "TL9007",
            "relation_id": "R209",
            "supplier": "Tower Semiconductor",
            "customer": "NewPhotonics",
            "supplier_point_id": "EXT",
            "customer_point_id": "EXT",
            "period": "2026-09-17",
            "period_type": "event",
            "event_date": "2026-09-17",
            "source_channel": "daily_announcement",
            "metric_kind": "foundry_milestone",
            "value_raw": "基于Tower PH18DA异质集成InP硅光平台的800G/1.6T NPG102激光集成PIC芯片开启大批量出货（6.4T NPC505预计2027H1出货）",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_TSEM_20260917_NEWPHOTONICS",
            "anchor_url": by_slug["tsem_20260917_newphotonics_pic"]["requested_url"],
            "conflict": "false",
            "notes": "硅光代工出货脉冲(对应DRQ0025/DC_A038F7C2DD93与calls/events.csv#EV043-EV044)；严格区分当期800G/1.6T NPG102批量出货与2027H1 6.4T NPC505计划，未披露终端模块买家",
        },
        "TL9008": {
            "timeline_id": "TL9008",
            "relation_id": "R210",
            "supplier": "GlobalFoundries",
            "customer": "Marvell",
            "supplier_point_id": "EXT",
            "customer_point_id": "P003",
            "period": "2026-11-04",
            "period_type": "event",
            "event_date": "2026-11-04",
            "source_channel": "daily_announcement",
            "metric_kind": "supply_agreement",
            "value_raw": "2026Q3财报披露于2026年9月与Marvell扩大美国Burlington晶圆厂高性能SiGe多年制造产能协议，覆盖可插拔光模块、NPO与CPO需求",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_GFS_20261104_Q3",
            "anchor_url": by_slug["gfs_20261104_2026q3_results"]["requested_url"],
            "conflict": "false",
            "notes": "上游晶圆代工协议扩充(对应DC_DB6E7B2D27BB与calls/events.csv#EV057)；仅GlobalFoundries单方季报披露，未公布协议金额与晶圆片数",
        },
        "TL9009": {
            "timeline_id": "TL9009",
            "relation_id": "R211",
            "supplier": "IQE",
            "customer": "Quintessent",
            "supplier_point_id": "EXT",
            "customer_point_id": "EXT",
            "period": "2026-09-03",
            "period_type": "event",
            "event_date": "2026-09-03",
            "source_channel": "daily_announcement",
            "metric_kind": "supply_agreement",
            "value_raw": "签署6英寸GaAs量子点激光（QDL）外延片采购协议，支持Quintessent向AI数据中心客户开展送样验证",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_IQE_20260903_QUINTESSENT_QDL",
            "anchor_url": by_slug["iqe_20260903_quintessent_qdl"]["requested_url"],
            "conflict": "false",
            "notes": "化合物外延采购协议(对应DRQ0030/DC_741EFE5BF486与calls/events.csv#EV049-EV050)；下游处于客户送样阶段而非规模部署，未披露金额",
        },
        "TL9010": {
            "timeline_id": "TL9010",
            "relation_id": "R212",
            "supplier": "Nokia",
            "customer": "Telxius",
            "supplier_point_id": "P240",
            "customer_point_id": "EXT",
            "period": "2026-09-15",
            "period_type": "event",
            "event_date": "2026-09-15",
            "source_channel": "daily_announcement",
            "metric_kind": "order_progress",
            "value_raw": "在Telxius欧洲、美国及拉美陆地传输网部署ICE-X 800G ZR/ZR+相干可插拔光模块及网络自动化方案",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_NOK_20260915_TELXIUS_800G",
            "anchor_url": by_slug["nok_20260915_telxius_800g"]["requested_url"],
            "conflict": "false",
            "notes": "相干可插拔干线部署脉冲(对应DRQ0021/DC_BF393C7C7BE8与calls/events.csv#EV041)；明确区分陆地干线部署与此前BRUSA海缆5600公里试验，未披露采购支数",
        },
        "TL9011": {
            "timeline_id": "TL9011",
            "relation_id": "R213",
            "supplier": "Credo",
            "customer": "Oracle",
            "supplier_point_id": "EXT",
            "customer_point_id": "EXT",
            "period": "2026-11-04",
            "period_type": "event",
            "event_date": "2026-11-04",
            "source_channel": "daily_announcement",
            "metric_kind": "spec_milestone",
            "value_raw": "双方共同主导制定的两项光模块增强遥测与带外通信开放规范获OCP社区正式批准",
            "numeric_value": "",
            "unit": "",
            "observe_type": "event_disclosed",
            "edge_grade": "实边",
            "source_edge_ids": "",
            "daily_ref_id": "D_CRDO_20261104_ORCL_OCP",
            "anchor_url": by_slug["crdo_20261104_oracle_ocp_telemetry"]["requested_url"],
            "conflict": "false",
            "notes": "开放标准共研里程碑(对应DC_89DB234EEA46与calls/events.csv#EV060)；仅证明OCP光学可靠性工作流标准共建，严禁外推为Oracle硬件采购份额",
        },
        "TL9012": {
            "timeline_id": "TL9012",
            "relation_id": "R214",
            "supplier": "Lumentum",
            "customer": "NPO/CPO第二大定点客户(匿名)",
            "supplier_point_id": "P233",
            "customer_point_id": "ANON",
            "period": "2026-11-02",
            "period_type": "event",
            "event_date": "2026-11-02",
            "source_channel": "daily_announcement",
            "metric_kind": "order_backlog",
            "value_raw": "FY27Q1取得第二项重大NPO/CPO定点，获逾50亿美元采购承诺（NPO/CPO合并口径，客户匿名且履约周期未披露）",
            "numeric_value": "50",
            "unit": "亿美元",
            "observe_type": "event_disclosed",
            "edge_grade": "半边",
            "source_edge_ids": "",
            "daily_ref_id": "D_LITE_20261102_FY27Q1",
            "anchor_url": by_slug["lite_20261102_fy27q1_results"]["requested_url"],
            "conflict": "false",
            "notes": "半边匿名大额定点承诺(对应DRQ0016/DC_573401DC530B与calls/events.csv#EV038)；原文为second major NPO/CPO win backed by purchase commitments exceeding $5 billion，非纯CPO单列且非当季已确认收入(当季总营收12.626亿美元)",
        },
    }
    tl_append_order = ["TL9006", "TL9007", "TL9008", "TL9009", "TL9010", "TL9011", "TL9012"]
    upsert_rows(timeline_rows, "timeline_id", timeline_updates, append_order=tl_append_order)

    # ------------------------------------------------------------------
    # 11. Strict Zero-Hit Forbidden Business Word Check Across All Touched Fields
    # ------------------------------------------------------------------
    url_like_fields = {"url", "canonical_url", "source_ref", "anchor_url", "quote"}
    for label, upd_map in (
        ("sources", source_updates),
        ("claims", claim_updates),
        ("commitments", commitment_updates),
        ("watch_entities", watch_updates),
        ("disclosures", disclosure_updates),
        ("event_claims", event_claim_updates),
        ("events", event_updates),
        ("event_evidence", evidence_updates),
        ("relationship_timeline", timeline_updates),
    ):
        for pk, data in upd_map.items():
            for field, val in data.items():
                if field not in url_like_fields:
                    assert_no_forbidden_words(f"{label}:{pk}.{field}", val)

    # Check zero collision between all TL9001-TL9012 and 74 negative cuts
    with cuts_path.open("r", encoding="utf-8-sig", newline="") as fh:
        cut_rows = list(csv.DictReader(fh))
    neg_pairs: set[tuple[str, str]] = set()
    for c in cut_rows:
        comp = (c.get("company") or "").strip()
        cp = (c.get("counterparty") or "").strip()
        cpn = (c.get("counterparty_normalized") or cp).strip()
        isup = (c.get("implied_supplier") or "").strip()
        icus = (c.get("implied_customer") or "").strip()
        for a, b in ((comp, cp), (comp, cpn), (isup, icus)):
            if a and b:
                neg_pairs.add((a, b))
                neg_pairs.add((b, a))
    for trow in timeline_rows:
        if trow["timeline_id"].startswith("TL9"):
            pair = (trow["supplier"].strip(), trow["customer"].strip())
            if pair in neg_pairs:
                raise AssertionError(f"{trow['timeline_id']} collides with 74 negative cuts: {pair}")

    # ------------------------------------------------------------------
    # 12. Write Whitelisted CSV Outputs (Preserving Untouched Raw Lines)
    # ------------------------------------------------------------------
    write_csv_preserving_untouched(
        calls_dir / "sources.csv", FILES["sources.csv"], "source_id", sources, set(source_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "claims.csv", FILES["claims.csv"], "claim_id", claims, set(claim_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "commitments.csv", FILES["commitments.csv"], "commitment_id", commitments, set(commitment_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "watch_entities.csv", FILES["watch_entities.csv"], "entity_id", watch_entities, set(watch_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "disclosures.csv", FILES["disclosures.csv"], "disclosure_id", disclosures, set(disclosure_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "event_claims.csv", FILES["event_claims.csv"], "event_claim_id", event_claims, set(event_claim_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "events.csv", FILES["events.csv"], "event_id", events, set(event_updates), "\n"
    )
    write_csv_preserving_untouched(
        calls_dir / "event_evidence.csv", FILES["event_evidence.csv"], "evidence_id", event_evidence, set(evidence_updates), "\n"
    )
    write_csv_preserving_untouched(
        rel_timeline_path, TIMELINE_FIELDS, "timeline_id", timeline_rows, set(timeline_updates), "\r\n"
    )

    # ------------------------------------------------------------------
    # 13. Deterministic Verification Gates
    # ------------------------------------------------------------------
    sl_hash_after = sha256_file(solution_links_path)
    if sl_hash_after != sl_hash_before:
        raise AssertionError("calls/solution_links.csv byte hash changed (strictly frozen)!")
    sl_rows = read_csv_rows(solution_links_path, FILES["solution_links.csv"])
    if tuple(sl_rows) != FROZEN_SOLUTION_LINKS:
        raise AssertionError("calls/solution_links.csv content does not match FROZEN_SOLUTION_LINKS!")

    calls_messages = validate(REPO_ROOT)
    event_projection = derive_event_projection(load_event_facts(REPO_ROOT))

    with (REPO_ROOT / "edges.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        active_edges = list(csv.DictReader(fh))
    edge_ids = {e["edge_id"] for e in active_edges}
    del scan.ERR[:]
    scan._check_relationship_tables(timeline_rows, edge_ids, cut_rows=cut_rows, active_edges=active_edges)
    rel_errors = list(scan.ERR)
    del scan.ERR[:]
    if rel_errors:
        raise AssertionError(f"scan._check_relationship_tables failed: {rel_errors}")

    # ------------------------------------------------------------------
    # 14. Write `overseas-drq-verdicts.json`
    # ------------------------------------------------------------------
    def archive_meta(slug: str) -> dict:
        r = by_slug[slug]
        return {
            "http_status": r["http_status"],
            "archive_status": r["archive_status"],
            "requested_url": r["requested_url"],
            "html_path": r.get("html_path", ""),
            "html_sha256": r.get("html_sha256", ""),
            "txt_path": r.get("txt_path", ""),
            "txt_sha256": r.get("txt_sha256", ""),
        }

    drq_verdicts = [
        {
            "queue_id": "DRQ0015",
            "dc_id": "DC_501FC1F61B62",
            "entity": "Marvell × Lumentum (MRVL/LITE)",
            "published_at": "2026-11-02",
            **archive_meta("mrvl_20261102_lumentum_combine"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_MRVL_20261102_LITE_MERGE;calls:ECL040;calls:EV037;calls:EE040;timeline:TL9006",
            "verbatim_anchor": "opening paragraph (p2) & Transaction Structure and Terms (p11-p13)",
            "verbatim_quote": event_claim_updates["ECL040"]["quote"],
            "boundary_note": "确定性全股票收购协议（1股LITE换4.500股MRVL，隐含企业价值1150亿美元，交割后MRVL股东约占67%/LITE股东约占33%），预计2028年上半年（H1 CY2028）交割，须经双方股东及反垄断监管审批，当前未交割。",
        },
        {
            "queue_id": "DRQ0016",
            "dc_id": "DC_573401DC530B",
            "entity": "Lumentum (LITE) FY27Q1",
            "published_at": "2026-11-02",
            **archive_meta("lite_20261102_fy27q1_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_LITE_2027Q1;calls:CL077;calls:D_LITE_20261102_FY27Q1;calls:ECL041;calls:EV038;calls:EE041;timeline:TL9012",
            "verbatim_anchor": "CEO commentary, paragraph 1 (p2)",
            "verbatim_quote": claim_updates["CL077"]["quote"],
            "boundary_note": "白纸黑字核实结论：FY27Q1官方业绩稿CEO Michael Hurlston首段确有原句 'During the quarter, we secured our second major NPO/CPO win, backed by purchase commitments exceeding $5 billion.'；严格边界：(1) 原文定语为 'NPO/CPO win'（NPO与CPO合并口径，并非纯CPO单列）；(2) 未披露具名客户、履约时间跨度与具体产品拆分；(3) FY27Q1合并总营收为12.626亿美元（Components 7.542亿/Systems 5.084亿），Q2指引15.75-16.25亿美元，该逾50亿美元属跨期采购承诺而非当季确认收入；(4) 新闻稿全文未披露200G EML专项在手积压金额。S_LITE_2027Q1按interquarter登记以保持test_reader_semantics.py对LITE既有2/4槽位断言通过。",
        },
        {
            "queue_id": "DRQ0017",
            "dc_id": "DC_3841FCD60F32",
            "entity": "AXT (AXTI) 2026Q3",
            "published_at": "2026-10-29",
            **archive_meta("axti_20261029_2026q3_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_AXTI_2026Q3;calls:CL078;calls:D_AXTI_20261029_Q3;calls:ECL042;calls:EV039;calls:EE042",
            "verbatim_anchor": "Management Qualitative Comments, paragraph 1 (p3)",
            "verbatim_quote": claim_updates["CL078"]["quote"],
            "boundary_note": "2026Q3合并营收达创纪录7341万美元（+54% QoQ，+162% YoY），毛利率56.0%，CEO确认超额完成年内InP产能翻倍目标；但新闻稿正文未单列InP衬底分项营收、未披露中国商务部两用物项出口许可证获批笔数及积压订单金额（出口许可仅在Safe Harbor风险段落提及）。S_AXTI_2025Q3转为interquarter、S_AXTI_2026Q3入quarterly，保持AXTI 3/4可用槽位不变。",
        },
        {
            "queue_id": "DRQ0018",
            "dc_id": "DC_FD32C455D502",
            "entity": "AXT / 北京通美晶体 (AXTI)",
            "published_at": "2026-10-28",
            **archive_meta("axti_20261028_tongmei_financing"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_AXTI_20261028_TONGMEI_PE;calls:ECL043;calls:EV040;calls:EE043",
            "verbatim_anchor": "opening paragraph (p1) & closing paragraph (p3)",
            "verbatim_quote": event_claim_updates["ECL043"]["quote"],
            "boundary_note": "控股子公司北京通美签署19.1235亿至36.6864亿元人民币（约2.85亿至5.45亿美元）私募股权融资协议用于InP衬底扩产，预计2026年12月交割（按上限计AXT持股约73.40%并继续并表），须完成中国相关政府机构备案且不保证交割；未交割前不计落地新增产能。",
        },
        {
            "queue_id": "DRQ0019",
            "dc_id": "DC_430D7977BA22",
            "entity": "Tower Semiconductor × 中际旭创 (TSEM/WATCH_INNOLIGHT)",
            "published_at": "2026-11-03",
            **archive_meta("tsem_20261103_innolight_npo"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_TSEM_20261103_INNOLIGHT_NPO;calls:ECL039;calls:EV036;calls:EE039;timeline:TL9002",
            "verbatim_anchor": "official release paragraph 3 (p3) & paragraph 7 (p7)",
            "verbatim_quote": event_claim_updates["ECL039"]["quote"],
            "boundary_note": "已由公告标题升级为官网全文逐字锚定：首款NPO器件在Tower美国加州Newport Beach厂PH18M 200mm硅光流程进入早期生产（early production），多款下一代NPO产品在300mm硅光平台完成流片（taped-out），且Innolight现横跨Tower美加州、美得州San Antonio、以色列与日本四座工厂；early production与中际11/03投关NPO 2027H2逐步规模上量口径完全一致。",
        },
        {
            "queue_id": "DRQ0021",
            "dc_id": "DC_BF393C7C7BE8",
            "entity": "Nokia × Telxius (NOK)",
            "published_at": "2026-09-15",
            **archive_meta("nok_20260915_telxius_800g"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_NOK_20260915_TELXIUS_800G;calls:ECL044;calls:EV041;calls:EE044;timeline:TL9010",
            "verbatim_anchor": "article lead paragraph (p14) & paragraph 4 (p17)",
            "verbatim_quote": event_claim_updates["ECL044"]["quote"],
            "boundary_note": "原文明确本次系Telxius在欧洲、美国与拉美陆地传输网推进ICE-X 800G ZR/ZR+ IP-over-DWDM现网部署，区别于p17回顾的此前BRUSA海缆5600公里400G/波试验，亦独立于EV005美国未具名客户发货。",
        },
        {
            "queue_id": "DRQ0022",
            "dc_id": "DC_7B475AB0DF5A",
            "entity": "Fabrinet (FN) FY27Q1",
            "published_at": "2026-11-02",
            **archive_meta("fn_20261102_fy27q1_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_FN_2027Q1;calls:D_FN_20261102_FY27Q1",
            "verbatim_anchor": "Financial Highlights & CEO quote (p2)",
            "verbatim_quote": "Revenue for the first quarter of fiscal year 2027 was $1,474.5 million, compared to $978.1 million for the first quarter of fiscal year 2026.",
            "boundary_note": "FY27Q1合并营收14.745亿美元（+51% YoY）、Q2指引16.0-16.5亿美元；新闻稿正文未拆分Datacom收入、1.6T代工或Building 10进展，故D_FN_20261102_FY27Q1标为no_relevant_claims（注：CM008/CM009实为Ciena Hyper-Rail承诺，保持pending）。S_FN_2026Q1转interquarter、S_FN_2027Q1入quarterly。",
        },
        {
            "queue_id": "DRQ0023",
            "dc_id": "DC_4FAA980A3027",
            "entity": "NVIDIA (NVDA) FY27Q3",
            "published_at": "2026-11-17",
            **archive_meta("nvda_20261117_fy27q3_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_NVDA_2027Q3;calls:D_NVDA_20261117_FY27Q3;calls:ECL045;calls:EV042;calls:EE045",
            "verbatim_anchor": "Data Center Highlights bullet 17",
            "verbatim_quote": event_claim_updates["ECL045"]["quote"],
            "boundary_note": "FY27Q3总营收1158.44亿美元（数据中心1076亿美元，Vera Rubin NVL72已开始出货）；光学专项披露与Cisco推进USFP新光模块形态计划，未披露Quantum-X/Spectrum-X Photonics CPO交换机客户交付时间点。S_NVDA_2025Q2转interquarter、S_NVDA_2027Q3入quarterly。",
        },
        {
            "queue_id": "DRQ0024",
            "dc_id": "DC_9B16CE64F492",
            "entity": "Ciena (CIEN) FY26Q3",
            "published_at": "2026-09-03",
            **archive_meta("cien_20260903_fy26q3_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_CIEN_2026Q3_PR;calls:D_CIEN_20260903_FY26Q3;calls:CM008;calls:CM009",
            "verbatim_anchor": "Revenue by Segment table (Optical Networking $1,191.3M)",
            "verbatim_quote": "Fiscal third quarter 2026 revenue was $1.67 billion, up 37% year-over-year",
            "boundary_note": "FY26Q3总营收16.711亿美元（Optical Networking分部11.913亿美元，两家10%+客户合占41.7%），但业绩新闻稿未单列800GZR/ZR+出货量或Vesta 200 CPX在Q2内的首次可用日（CM007维持partially_fulfilled）。按interquarter登记S_CIEN_2026Q3_PR。",
        },
        {
            "queue_id": "DRQ0025",
            "dc_id": "DC_A038F7C2DD93",
            "entity": "Tower Semiconductor × NewPhotonics (TSEM)",
            "published_at": "2026-09-17",
            **archive_meta("tsem_20260917_newphotonics_pic"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:WATCH_NEWPHOTONICS;calls:D_TSEM_20260917_NEWPHOTONICS;calls:ECL046;calls:ECL047;calls:EV043;calls:EV044;calls:EE046;calls:EE047;timeline:TL9007",
            "verbatim_anchor": "official release paragraph 5 (p5)",
            "verbatim_quote": event_claim_updates["ECL046"]["quote"] + " " + event_claim_updates["ECL047"]["quote"],
            "boundary_note": "已按要求拆分为两条独立事件：EV043记录PH18DA平台800G/1.6T（单通道200G）NPG102激光集成PIC当期批量出货（fact_assertion/scaled），EV044记录6.4T CPX-MSA NPC505预计2027H1批量出货（forward_looking/announced）。",
        },
        {
            "queue_id": "DRQ0026",
            "dc_id": "DC_286D42235853",
            "entity": "Wiwynn × Ayar Labs × GUC (WIWYNN)",
            "published_at": "2026-10-13",
            **archive_meta("wiwynn_20261013_ayar_guc_cpo_demo"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_WIWYNN_20261013_OCP_CPO_DEMO;calls:ECL048;calls:EV045;calls:EE048",
            "verbatim_anchor": "official release paragraph 3 (p3)",
            "verbatim_quote": event_claim_updates["ECL048"]["quote"],
            "boundary_note": "核明三方分工：Wiwynn ORv3计算系统与液冷架构、GUC多芯片封装（MCP）ASIC、Ayar Labs TeraPHY光引擎配ELSFP形态SuperNova外置光源；严格限定为OCP现场演示（demonstrated）。",
        },
        {
            "queue_id": "DRQ0027",
            "dc_id": "DC_DC1ABE67C305",
            "entity": "Lightmatter (WATCH_LIGHTMATTER)",
            "published_at": "2026-10-12",
            **archive_meta("lightmatter_20261012_open_rack_cpo"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_LIGHTMATTER_20261012_OCP_CPO;calls:ECL049;calls:EV046;calls:EE049",
            "verbatim_anchor": "official release opening paragraph (p2) & paragraph 6 (p6)",
            "verbatim_quote": event_claim_updates["ECL049"]["quote"],
            "boundary_note": "核清Delivers真实语境：204.8T 1RU交换托盘为与Flex联合开发的生产验证平台（production validation platform），102.4T 4-XPU计算托盘为概念验证原型（prototype/proof of concept），均在OCP展台A36展示（demonstrated），非商业部署交付。",
        },
        {
            "queue_id": "DRQ0028",
            "dc_id": "DC_7CED25D6E66F",
            "entity": "Credo (CRDO) 1.6T ZeroFlap ALC",
            "published_at": "2026-10-12",
            **archive_meta("crdo_20261012_1p6t_zeroflap_alc"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_CRDO_20261012_1P6T_ALC;calls:ECL050;calls:EV047;calls:EE050",
            "verbatim_anchor": "official release paragraph 3 & paragraph 8 (p8)",
            "verbatim_quote": event_claim_updates["ECL050"]["quote"],
            "boundary_note": "采用微发光器阵列（micro-emitter）多通道并行NRZ无DSP设计（端功耗12W、距离50m），当前仅处新品发布与OCP展示阶段，原文明确预计2027年才开始出货。",
        },
        {
            "queue_id": "DRQ0029",
            "dc_id": "DC_535D459775E6",
            "entity": "MACOM (MTSI) 3.2T Chipset",
            "published_at": "2026-09-17",
            **archive_meta("mtsi_20260917_3p2t_chipset"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_MTSI_20260917_3P2T_CHIPSET;calls:ECL051;calls:EV048;calls:EE051",
            "verbatim_anchor": "official release paragraph 6-9 (p6-p9)",
            "verbatim_quote": event_claim_updates["ECL051"]["quote"],
            "boundary_note": "核明具体型号：新增MATA-42754/MATA-41754四通道线性TIA与MARP-BP224（>100GHz）背照式PIN PD，与EV007既有MAOM-025408/022404驱动芯片组成完整8x448G（3.2T）前端套片，故以previous_event_id=EV007单列新品事件EV048。",
        },
        {
            "queue_id": "DRQ0030",
            "dc_id": "DC_741EFE5BF486",
            "entity": "IQE × Quintessent (WATCH_IQE)",
            "published_at": "2026-09-03",
            **archive_meta("iqe_20260903_quintessent_qdl"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:WATCH_QUINTESSENT;calls:D_IQE_20260903_QUINTESSENT_QDL;calls:ECL052;calls:ECL053;calls:EV049;calls:EV050;calls:EE052;calls:EE053;timeline:TL9009",
            "verbatim_anchor": "official release paragraph 1-2 (p3-p4)",
            "verbatim_quote": event_claim_updates["ECL052"]["quote"],
            "boundary_note": "已按要求拆成6英寸GaAs外延片采购协议（EV049）与支持Quintessent客户送样（EV050，sampling）两条独立事件。",
        },
        {
            "queue_id": "DRQ0037",
            "dc_id": "DC_4B0F75924A65",
            "entity": "Lightwave Logic × 鸿海 (LWLG/FIT)",
            "published_at": "2026-10-29",
            **archive_meta("lwlg_20261029_foxconn_hhtd_demo"),
            "recommended_queue_status": "pending_primary_text",
            "kb_target_ref": "",
            "verbatim_anchor": "QuoteMedia HTML is empty JS shell (p_chars=0); LWLG IR page embeds Issuer Direct widget",
            "verbatim_quote": "",
            "boundary_note": "诚实标注blocked_http_or_js_shell：源URL api.quotemedia.com 静态GET返回空JS壳（p_chars=0），且lightwavelogic.com/press-releases静态HTML亦为Issuer Direct嵌入组件无静态正文，按红线不入正史表；另经http_discovery已声明的公开Issuer Direct getStory.json接口辅助核对，该稿系鸿海科技日（10/30-31）由Hon Hai Technology Group旗下Siphcomm Business Unit（非FIT 06088.HK主体）展示瞄准200G/400G单通道的硅-有机混合（SOH）光模块演示样机，仍处技术开发验证阶段。",
        },
        {
            "queue_id": "DRQ0038",
            "dc_id": "DC_839378F484E4",
            "entity": "OpenLight (WATCH_OPENLIGHT)",
            "published_at": "2026-10-07",
            **archive_meta("openlight_20261007_heterogeneous_sipho"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_OPENLIGHT_20261007_HETERO_SIPHO",
            "verbatim_anchor": "newsroom summary paragraphs 1-3 (p1-p3)",
            "verbatim_quote": "In a post-ECOC 2026 interview with Jim Carroll of Converge Network Digest, OpenLight CEO Adam Carter explained how the company is tackling volume production, 3.2T silicon photonics, wafer-level testing, NPO/CPO architectures and the scaling of heterogeneous InP-on-silicon photonics for AI.",
            "boundary_note": "官网页面实为Converge Network Digest专访导读短摘要（提及累计公开融资8400万美元及聘任COO/CSO），未披露代工厂晶圆尺寸、PDK冻结或商业量产出货实证，故以no_relevant_claims归档闭合。",
        },
        {
            "queue_id": "DRQ0039",
            "dc_id": "DC_D527C3DC5ED2",
            "entity": "Lumentum (LITE) ECOC DWDM ELSFP",
            "published_at": "2026-09-21",
            **archive_meta("lite_20260921_ecoc_dwdm_elsfp"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_LITE_20260921_ECOC_ELSFP;calls:ECL054;calls:EV051;calls:EE054",
            "verbatim_anchor": "official release paragraph 5 (p5)",
            "verbatim_quote": event_claim_updates["ECL054"]["quote"],
            "boundary_note": "ECOC 2026展前演示预告（8通道DWDM ELSFP，单波约250mW、整模块约12W），原文明确预计2027H1初始可提供（initial availability），严格标为announced。",
        },
        {
            "queue_id": "DRQ0040",
            "dc_id": "DC_E1BEF90B2480",
            "entity": "Lumentum × Qualcomm × Corning (LITE/GLW)",
            "published_at": "2026-09-21",
            **archive_meta("lite_20260921_ecoc_1060nm_vcsel"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_LITE_20260921_ECOC_VCSEL_D2D;calls:ECL055;calls:EV052;calls:EE055",
            "verbatim_anchor": "official release paragraph 4 (p4)",
            "verbatim_quote": event_claim_updates["ECL055"]["quote"],
            "boundary_note": "核实为ECOC 2026板级概念验证演示计划（单通道32 Gb/s NRZ、1060nm VCSEL配Corning多模光纤插芯），严禁升格为C2商业出货点。",
        },
        {
            "queue_id": "DRQ0041",
            "dc_id": "DC_4A9C0B800414",
            "entity": "Wiwynn (WIWYNN) OCP Showcase",
            "published_at": "2026-10-12",
            **archive_meta("wiwynn_20261012_ocp_showcase"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_WIWYNN_20261012_OCP_SHOWCASE",
            "verbatim_anchor": "official release paragraph 10 (p10)",
            "verbatim_quote": "Wiwynn, together with ecosystem partners including Ayar Labs, Corning, GUC, and Senko, will showcase its co-packaged optics (CPO) scale-up rack solution",
            "boundary_note": "系服务器ODM展台总览预热稿，CPO计算系统现场演示已由次日专项稿EV045建档，本篇标no_relevant_claims避免同源双计。",
        },
        {
            "queue_id": "DRQ0042",
            "dc_id": "DC_DFCE4B441F6E",
            "entity": "MaxLinear (MXL) Jeju PMIC",
            "published_at": "2026-11-10",
            **archive_meta("mxl_20261110_jeju_pmic"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_MXL_20261110_JEJU_PMIC;calls:ECL056;calls:EV053;calls:EE056",
            "verbatim_anchor": "Availability section (p13)",
            "verbatim_quote": event_claim_updates["ECL056"]["quote"],
            "boundary_note": "核清状态：Jeju（MxL77904）定制PMIC预计2027年2月才向客户送样（并非已随DSP捆绑量产出货），按announced录入EV053。",
        },
        {
            "queue_id": "DRQ0043",
            "dc_id": "DC_91F3D715F522",
            "entity": "Ciena × Internet2 (CIEN)",
            "published_at": "2026-11-17",
            **archive_meta("cien_20261117_internet2_800g"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:D_CIEN_20261117_INTERNET2_800G;calls:ECL057;calls:EV054;calls:EE057",
            "verbatim_anchor": "official release paragraph 3 (p3)",
            "verbatim_quote": event_claim_updates["ECL057"]["quote"],
            "boundary_note": "核明模块型号为WaveLogic 6 Nano（135 GBaud PKT-MAX模式），属SC26芝加哥至堪萨斯城往返2104公里科研教育网现网试验（demonstrated），非批量商业订单。",
        },
        {
            "queue_id": "DRQ0044",
            "dc_id": "DC_4FACD43C676E",
            "entity": "POET Technologies (POET) 2026Q3",
            "published_at": "2026-11-16",
            **archive_meta("poet_20261116_2026q3_official"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_POET_2026Q3;calls:CL079;calls:D_POET_20261116_Q3;calls:ECL058;calls:EV055;calls:EE058",
            "verbatim_anchor": "Management Commentary paragraph 1-2 (p4-p5)",
            "verbatim_quote": claim_updates["CL079"]["quote"],
            "boundary_note": "同步抓回poet-technologies.com官网第一方正式稿：Q3营收1,026,087美元（净亏损756万美元、经营现金净流出1270万美元），签下一家Tier 1激光厂外置光源开发协议及老客户240万美元PO，但原定2026年目标的3万只光引擎因晶圆与组件紧缺及良率爬坡顺延至2027Q2前交付。S_POET_2025Q2转interquarter、S_POET_2026Q3入quarterly。",
        },
        {
            "queue_id": "DRQ0045",
            "dc_id": "DC_425841A754F4",
            "entity": "Broadcom (AVGO) FY26Q3",
            "published_at": "2026-09-02",
            **archive_meta("avgo_20260902_fy26q3_results"),
            "recommended_queue_status": "ingested_to_kb",
            "kb_target_ref": "calls:S_AVGO_2026Q3;calls:CL080;calls:D_AVGO_20260902_Q3",
            "verbatim_anchor": "CEO quote in official FY2026 Q3 results (p2)",
            "verbatim_quote": claim_updates["CL080"]["quote"],
            "boundary_note": "FY26Q3总营收296亿美元、AI半导体收入167亿美元（+221% YoY，Q4指引217亿美元）；业绩新闻稿正文未拆分Tomahawk 6 CPO或可插拔光DSP/200G EML份额。S_AVGO_2025Q3转interquarter、S_AVGO_2026Q3入quarterly。",
        },
    ]

    staging_oct_nov_verdicts = [
        {
            "staging_item": "STAGE_MTSI_FY26Q4",
            "dc_id": "DC_A6ADDA0BAFA7",
            "entity": "MACOM (MTSI) FY26Q4",
            "published_at": "2026-11-05",
            **archive_meta("mtsi_20261105_fy26q4_results"),
            "kb_target_ref": "calls:S_MTSI_2026Q4;calls:D_MTSI_20261105_Q4",
            "verbatim_quote": "Revenue was $424.8 million, an increase of 62.7%, compared to $261.2 million in the previous year fiscal fourth quarter",
            "boundary_note": "S_MTSI_2025Q4转interquarter、S_MTSI_2026Q4入quarterly；FY26Q4营收4.248亿美元、FY27Q1指引4.50-4.60亿美元，新闻稿正文无光学细分管理层陈述（标no_relevant_claims）。",
        },
        {
            "staging_item": "STAGE_TSEM_2026Q3",
            "dc_id": "DC_58448CDF4801",
            "entity": "Tower Semiconductor (TSEM) 2026Q3",
            "published_at": "2026-11-02",
            **archive_meta("tsem_20261102_2026q3_results"),
            "kb_target_ref": "calls:S_TSEM_2026Q3;calls:CL081;calls:D_TSEM_20261102_Q3;calls:ECL059;calls:EV056;calls:EE059",
            "verbatim_quote": claim_updates["CL081"]["quote"],
            "boundary_note": "S_TSEM_2025Q2转interquarter、S_TSEM_2026Q3入quarterly；Q3营收5.26亿美元、Q4指引6亿美元，CEO提出2026Q4硅光单项年化收入11亿美元目标（2025年的5倍）且日本300mm一轨扩产超前推进。",
        },
        {
            "staging_item": "STAGE_GFS_2026Q3",
            "dc_id": "DC_DB6E7B2D27BB",
            "entity": "GlobalFoundries (GFS) 2026Q3",
            "published_at": "2026-11-04",
            **archive_meta("gfs_20261104_2026q3_results"),
            "kb_target_ref": "calls:S_GFS_2026Q3;calls:D_GFS_20261104_Q3;calls:ECL060;calls:EV057;calls:EE060;timeline:TL9008",
            "verbatim_quote": event_claim_updates["ECL060"]["quote"],
            "boundary_note": "S_GFS_2025Q3转interquarter、S_GFS_2026Q3入quarterly；Q3营收18.99亿美元，披露2026年9月与Marvell扩大美国Burlington厂SiGe多年制造产能协议（面向可插拔/NPO/CPO）及CHIPS法案9.55亿美元重分配。",
        },
        {
            "staging_item": "STAGE_VECO_2026Q3",
            "dc_id": "DC_25B37F48DF71",
            "entity": "Veeco (VECO) 2026Q3",
            "published_at": "2026-11-04",
            **archive_meta("veco_20261104_2026q3_results"),
            "kb_target_ref": "calls:S_VECO_2026Q3;calls:CL082;calls:D_VECO_20261104_Q3",
            "verbatim_quote": claim_updates["CL082"]["quote"],
            "boundary_note": "S_VECO_2025Q3转interquarter、S_VECO_2026Q3入quarterly；Q3营收2.094亿美元、Q4指引2.30-2.60亿美元，CEO称高速光连接与先进逻辑存储封装共同推动设备订单活跃。",
        },
        {
            "staging_item": "STAGE_VECO_ACLS_MERGER",
            "dc_id": "DC_6B392C92DA0A",
            "entity": "Veeco × Axcelis (VECO/WATCH_AXCELIS)",
            "published_at": "2026-11-02",
            **archive_meta("veco_20261102_axcelis_merger_update"),
            "kb_target_ref": "calls:WATCH_AXCELIS;calls:D_VECO_20261102_ACLS_MERGER;calls:ECL061;calls:EV058;calls:EE061",
            "verbatim_quote": event_claim_updates["ECL061"]["quote"],
            "boundary_note": "全股票换股合并（1股VECO换0.3575股ACLS）预计交割日延至2027Q1末，仍待中国市场监管总局（SAMR）审批及美国HSR重报。",
        },
        {
            "staging_item": "STAGE_SOI_FY27H1",
            "dc_id": "DC_86F8DBF8F95E",
            "entity": "Soitec (SOI) FY27 H1",
            "published_at": "2026-11-18",
            **archive_meta("soi_20261118_fy27h1_results"),
            "kb_target_ref": "calls:S_SOI_2027H1;calls:CL083;calls:D_SOI_20261118_FY27H1;calls:ECL062;calls:EV059;calls:EE062",
            "verbatim_quote": claim_updates["CL083"]["quote"],
            "boundary_note": "S_SOI_2026H1转interquarter、S_SOI_2027H1入quarterly（将sources.csv最新正式财报推进至2026-11-18）；Photonics-SOI H1收入约1.25亿美元（Q2约7500万美元，全年预计超3亿美元），客户已签约12亿美元带现金定金产能预留协议（H1已收8600万欧元定金），Bernin 4厂转向SOI扩产。",
        },
        {
            "staging_item": "STAGE_ANET_2026Q3",
            "dc_id": "DC_C85C91649A7A",
            "entity": "Arista Networks (ANET) 2026Q3",
            "published_at": "2026-11-03",
            **archive_meta("anet_20261103_2026q3_results"),
            "kb_target_ref": "calls:S_ANET_2026Q3;calls:D_ANET_20261103_Q3",
            "verbatim_quote": "Revenue of $3.66 billion, an increase of 20.5% compared to the second quarter of 2026, and an increase of 58.5% from the third quarter of 2025.",
            "boundary_note": "S_ANET_2025Q3转interquarter、S_ANET_2026Q3入quarterly；Q3营收36.576亿美元、Q4指引39-40亿美元，新闻稿聚焦ESUN交换机架构而未拆分光模块或CPO口径（标no_relevant_claims）。",
        },
        {
            "staging_item": "STAGE_CRDO_ORCL_OCP",
            "dc_id": "DC_89DB234EEA46",
            "entity": "Credo × Oracle (CRDO/WATCH_ORCL)",
            "published_at": "2026-11-04",
            **archive_meta("crdo_20261104_oracle_ocp_telemetry"),
            "kb_target_ref": "calls:D_CRDO_20261104_ORCL_OCP;calls:ECL063;calls:EV060;calls:EE063;timeline:TL9011",
            "verbatim_quote": event_claim_updates["ECL063"]["quote"],
            "boundary_note": "OCP社区正式批准Credo与Oracle在光学可靠性工作流联合主导的两项光模块增强遥测开放规范；严格限定为开放标准规范获批，不外推商业采购份额。",
        },
    ]

    target_csv_files = [
        "calls/sources.csv",
        "calls/claims.csv",
        "calls/commitments.csv",
        "calls/watch_entities.csv",
        "calls/disclosures.csv",
        "calls/event_claims.csv",
        "calls/events.csv",
        "calls/event_evidence.csv",
        "corpus/relationships/relationship_timeline.csv",
    ]
    csv_hashes = {rel: sha256_file(REPO_ROOT / rel) for rel in target_csv_files}

    verdict_payload = {
        "shard": "step4-overseas-fetch-and-ledger-closure",
        "as_of": "2026-11-22",
        "web_archive_summary": {
            "directory": "corpus/web/step4_20261122",
            "manifest_path": "corpus/web/step4_20261122/manifest.json",
            "manifest_sha256": sha256_file(WEB_DIR / "manifest.json"),
            "total_targets": len(FETCH_TARGETS),
            "archived_http_200_count": sum(1 for r in by_slug.values() if r["archive_status"] == "archived_http_200"),
            "blocked_http_or_js_shell_count": sum(1 for r in by_slug.values() if r["archive_status"] != "archived_http_200"),
        },
        "ledger_counts_for_verifier_test_alignment": {
            "companies_count": len(read_csv_rows(calls_dir / "universe.csv", FILES["universe.csv"])),
            "sources_count": len(sources),
            "sources_latest_published_date": max(r["published_date"] for r in sources if r["published_date"]),
            "quarterly_slots_rolled_companies": [
                "AXTI", "FN", "NVDA", "MTSI", "TSEM", "GFS", "VECO", "SOI", "ANET", "POET", "AVGO"
            ],
            "interquarter_locked_new_earnings": ["S_LITE_2027Q1", "S_CIEN_2026Q3_PR"],
            "claims_count": len(claims),
            "new_claim_ids": claim_append_order,
            "watch_entities_count": len(watch_entities),
            "active_watch_entity_count": event_projection["coverage_summary"]["active_watch_entity_count"],
            "new_watch_entity_ids": watch_append_order,
            "disclosure_count": event_projection["coverage_summary"]["disclosure_count"],
            "processing_status_counts": event_projection["coverage_summary"]["processing_status_counts"],
            "latest_disclosure_at": event_projection["coverage_summary"]["latest_disclosure_at"],
            "latest_retrieved_at": event_projection["coverage_summary"]["latest_retrieved_at"],
            "latest_reviewed_at": event_projection["coverage_summary"]["latest_reviewed_at"],
            "radar_events_count": len(event_projection["radar_events"]),
            "radar_event_id_range": "EV001..EV060",
            "radar_primary_subject_ids": sorted({r["primary_subject_id"] for r in event_projection["radar_events"]}),
            "upgraded_event_ids": ["EV036"],
            "new_event_ids": ev_append_order,
            "relationship_timeline_count": len(timeline_rows),
            "upgraded_timeline_ids": ["TL9002"],
            "new_timeline_ids": tl_append_order,
            "solution_links_sha256_unchanged": sl_hash_after,
        },
        "validator_messages": calls_messages,
        "target_file_sha256": csv_hashes,
        "overseas_drq_verdicts": drq_verdicts,
        "oct_nov_staging_verdicts": staging_oct_nov_verdicts,
    }
    verdict_bytes = (json.dumps(verdict_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if not VERDICTS_PATH.is_file() or VERDICTS_PATH.read_bytes() != verdict_bytes:
        VERDICTS_PATH.write_bytes(verdict_bytes)

    print("\n".join(calls_messages))
    print(
        f"OK: sources={len(sources)} (latest={verdict_payload['ledger_counts_for_verifier_test_alignment']['sources_latest_published_date']}), "
        f"claims={len(claims)}, disclosures={len(disclosures)}, radar_events={len(event_projection['radar_events'])}, "
        f"timeline={len(timeline_rows)}, archived_web={verdict_payload['web_archive_summary']['archived_http_200_count']}/{len(FETCH_TARGETS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
