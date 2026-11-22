#!/usr/bin/env python3
"""Step 2 Shard A: 2023年报与v16文本收编 + 实体国别代码表 + 海关四维表/HS映射 + 宏观MC033–035.

幂等构建脚本：可安全重复运行，重复运行前后输出字节级一致。
严格遵守写入边界，不删除 archive/ 原件，不修改 corpus/_frozen.csv 或 points.csv 的 P031/P209。
"""

from __future__ import annotations

import csv
import glob
import hashlib
import io
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path("/Users/jowang/Downloads/optical-module-research")
OUT_DIR = ROOT / "out" / "step2-archive-salvage-20261121"
SALVAGED_DIR = ROOT / "corpus" / "salvaged"
CUSTOMS_DIR = ROOT / "corpus" / "customs"
BUILD_DATE = "2026-11-21"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text_if_changed(path: Path, content: str, encoding: str = "utf-8") -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = content.encode(encoding)
    if path.exists() and path.read_bytes() == raw:
        return False
    path.write_bytes(raw)
    return True


def write_bytes_if_changed(path: Path, raw: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == raw:
        return False
    path.write_bytes(raw)
    return True


# ---------------------------------------------------------------------------
# Task 1: 2023年报去重清单与 v16 全文旁车补齐
# ---------------------------------------------------------------------------
def build_demo_dedupe_and_v16_sidecars() -> dict[str, Any]:
    demo_dir = ROOT / "archive" / "demo" / "data"
    demo_pdfs = sorted(
        Path(dp) / fn
        for dp, _, fns in os.walk(demo_dir, followlinks=True)
        for fn in sorted(fns)
        if fn.lower().endswith(".pdf")
    )
    assert len(demo_pdfs) == 30, f"Expected 30 demo PDFs, got {len(demo_pdfs)}"

    corpus_pdf_index: dict[str, list[str]] = defaultdict(list)
    annual_2023_count = 0
    for sub in ("corpus/annual", "corpus/annual-2024", "corpus/annual-2023"):
        base = ROOT / sub
        if not base.exists():
            continue
        for dp, _, fns in os.walk(base, followlinks=True):
            for fn in sorted(fns):
                if fn.lower().endswith(".pdf"):
                    full = Path(dp) / fn
                    rel = os.path.relpath(full, ROOT)
                    digest = sha256_file(full)
                    if rel not in corpus_pdf_index[digest]:
                        corpus_pdf_index[digest].append(rel)
                    if sub == "corpus/annual-2023":
                        annual_2023_count += 1

    entries = []
    matched_count = 0
    demo_2023_count = 0
    for pdf_path in demo_pdfs:
        rel_demo = os.path.relpath(pdf_path, ROOT)
        digest = sha256_file(pdf_path)
        size_bytes = pdf_path.stat().st_size
        matches = sorted(corpus_pdf_index.get(digest, []))
        is_matched = len(matches) > 0
        if is_matched:
            matched_count += 1
        year_m = re.search(r"_(202\d)_", pdf_path.name)
        report_year = year_m.group(1) if year_m else ""
        if report_year == "2023":
            demo_2023_count += 1
        entries.append(
            {
                "demo_path": rel_demo,
                "stock_code": pdf_path.parent.name,
                "report_year": report_year,
                "size_bytes": size_bytes,
                "sha256": digest,
                "corpus_matches": matches,
                "matched": is_matched,
            }
        )

    assert matched_count == 30, f"Expected 30/30 demo PDFs matched, got {matched_count}/30"

    manifest = {
        "schema_version": 1,
        "generated_date": BUILD_DATE,
        "demo_dir": "archive/demo/data",
        "demo_pdf_count": len(demo_pdfs),
        "demo_2023_pdf_count": demo_2023_count,
        "corpus_annual_2023_pdf_count": annual_2023_count,
        "matched_count": matched_count,
        "unmatched_count": len(demo_pdfs) - matched_count,
        "all_30_matched": matched_count == 30,
        "archive_files_preserved": True,
        "entries": entries,
    }
    manifest_path = OUT_DIR / "demo-pdf-dedupe-manifest.json"
    write_text_if_changed(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )

    # v16 Grok full-text sidecars -> corpus/legacy-input/v16/<code>/<code>/<pdf>.txt
    grok_dir = ROOT / "archive" / "flows" / "out" / "_v16_txt_grok"
    grok_txts = sorted(grok_dir.glob("*.txt"))
    assert len(grok_txts) == 11, f"Expected 11 grok txt files, got {len(grok_txts)}"

    v16_pdfs = {
        p.stem: p
        for p in sorted((ROOT / "corpus" / "legacy-input" / "v16").rglob("*.pdf"))
    }
    sidecar_records = []
    copied_new_or_updated = 0
    for src_txt in grok_txts:
        stem = src_txt.stem
        assert stem in v16_pdfs, f"Missing v16 PDF for {src_txt.name}"
        pdf_path = v16_pdfs[stem]
        dst_txt = Path(f"{pdf_path}.txt")
        src_bytes = src_txt.read_bytes()
        changed = write_bytes_if_changed(dst_txt, src_bytes)
        if changed:
            copied_new_or_updated += 1
        assert sha256_file(dst_txt) == sha256_file(src_txt)
        sidecar_records.append(
            {
                "source_archive_txt": os.path.relpath(src_txt, ROOT),
                "target_sidecar_txt": os.path.relpath(dst_txt, ROOT),
                "sha256": sha256_file(dst_txt),
                "size_bytes": len(src_bytes),
            }
        )

    return {
        "demo_pdf_count": len(demo_pdfs),
        "demo_matched_count": matched_count,
        "demo_2023_pdf_count": demo_2023_count,
        "corpus_annual_2023_pdf_count": annual_2023_count,
        "v16_sidecars_total": len(sidecar_records),
        "v16_sidecars_verified": len(sidecar_records),
        "v16_sidecars": sidecar_records,
    }


# ---------------------------------------------------------------------------
# Task 2: truth.json 16条真值核对 + points.csv 归档悬空引用修复
# ---------------------------------------------------------------------------
def build_truth_assertions_and_fix_points() -> dict[str, Any]:
    truth_path = ROOT / "archive" / "demo" / "truth.json"
    truth_doc = json.loads(truth_path.read_text(encoding="utf-8"))
    checks = truth_doc["checks"]
    assert len(checks) == 16, f"Expected 16 truth checks, got {len(checks)}"

    with (ROOT / "edges.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        edges = list(csv.DictReader(fh))
    edges_by_id = {e["edge_id"]: e for e in edges}

    # Explicit deterministic mapping from demo/truth.json (demo 300-row schema)
    # to canonical root edges.csv (236-row schema)
    canonical_map: dict[str, dict[str, str]] = {
        "T01": {
            "edge_id": "E055",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "demo 备注'客户 A'在根级 edges.csv 升格为 需方='客户A(匿名)'，字段名为'占比或金额原文'",
        },
        "T02": {
            "edge_id": "E055",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "中际旭创2025客户A销售额 9201495755.91 元载于 E055 占比或金额原文",
        },
        "T03": {
            "edge_id": "E056",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "demo 备注'客户 B'在根级 edges.csv 对应 E056 需方='客户B(匿名)'",
        },
        "T04": {
            "edge_id": "E057",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "demo 备注'客户 C'在根级 edges.csv 对应 E057 需方='客户C(匿名)'",
        },
        "T05": {
            "edge_id": "E058",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "demo 备注'客户 D'在根级 edges.csv 对应 E058 需方='客户D(匿名)'",
        },
        "T06": {
            "edge_id": "E044",
            "canonical_field": "备注",
            "normalize_commas": "true",
            "schema_note": "中际旭创2025客户E已解匿并入 E044 需方='PINEWAVE(关联方)'(43378万美元)，Step 1 已在 E044 备注补齐前五大表人民币精确值 3,096,780,769.22 元(去千分位后与 3096780769.22 完全一致)",
        },
        "T07": {
            "edge_id": "E059",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "中际旭创2025年报原文按字母称'供应商A'，根级 edges.csv 记为 E059 供方='供应商A(匿名)'",
        },
        "T08": {
            "edge_id": "E060",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "新易盛2025第一名客户载于 E060 需方='客户第一名(匿名)'",
        },
        "T09": {
            "edge_id": "E060",
            "canonical_field": "备注",
            "normalize_commas": "false",
            "schema_note": "新易盛2024第一名客户占比 31.74%(2744287306.63元) 合并记载于 E060 多期备注中",
        },
        "T10": {
            "edge_id": "E015",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "新易盛2023第一名客户载于 E015 需方='客户一(匿名)'",
        },
        "T11": {
            "edge_id": "E015",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "新易盛2023第一名客户销售额 1139711326.47 元载于 E015 占比或金额原文",
        },
        "T12": {
            "edge_id": "E064",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "新易盛2025第一名供应商载于 E064 供方='供应商第一名(匿名)'",
        },
        "T13": {
            "edge_id": "E043",
            "canonical_field": "边等级",
            "normalize_commas": "false",
            "schema_note": "天孚通信2025对 Fabrinet 实名实边载于 E043(63.31%)",
        },
        "T14": {
            "edge_id": "E043",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "天孚通信2025对 Fabrinet 销售额 3268843594.94 元载于 E043 占比或金额原文",
        },
        "T15": {
            "edge_id": "E065",
            "canonical_field": "占比或金额原文",
            "normalize_commas": "false",
            "schema_note": "天孚通信2025第二名客户载于 E065 需方='客户2(匿名)'",
        },
        "T16": {
            "edge_id": "E044",
            "canonical_field": "备注",
            "normalize_commas": "false",
            "expected_canonical_substring": "判例#002",
            "schema_note": "demo 阶段'关联方锁定候选'在根级 E044 已完成正式关联交易锚定(需方='PINEWAVE(关联方)', 备注载明客户E占比8.10%=前五大关联方销售占比8.10%且金额指纹吻合(判例#002))",
        },
    }

    assertion_results = []
    passed_count = 0
    for chk in checks:
        cid = chk["id"]
        spec = canonical_map[cid]
        edge = edges_by_id[spec["edge_id"]]
        field_name = spec["canonical_field"]
        raw_val = edge.get(field_name, "")
        cmp_val = raw_val.replace(",", "") if spec["normalize_commas"] == "true" else raw_val
        expected_sub = spec.get("expected_canonical_substring", chk["expect"]["contains"])
        passed = expected_sub in cmp_val
        if passed:
            passed_count += 1
        assertion_results.append(
            {
                "id": cid,
                "desc": chk["desc"],
                "legacy_where": chk["where"],
                "legacy_expect": chk["expect"],
                "canonical_edge_id": spec["edge_id"],
                "canonical_supplier": edge["供方"],
                "canonical_customer": edge["需方"],
                "canonical_period": edge["财年"],
                "canonical_field": field_name,
                "expected_substring": expected_sub,
                "normalize_commas": spec["normalize_commas"] == "true",
                "actual_field_value": raw_val,
                "passed": passed,
                "schema_evolution_note": spec["schema_note"],
            }
        )

    assert passed_count == 16, f"Truth assertions failed: {passed_count}/16"

    truth_out = {
        "schema_version": 1,
        "generated_date": BUILD_DATE,
        "source_truth_file": "archive/demo/truth.json",
        "target_ledger": "edges.csv",
        "total_count": len(checks),
        "passed_count": passed_count,
        "status": f"{passed_count}/{len(checks)} PASSED",
        "all_passed": passed_count == len(checks),
        "assertions": assertion_results,
    }
    write_text_if_changed(
        SALVAGED_DIR / "truth_regression_assertions.json",
        json.dumps(truth_out, ensure_ascii=False, indent=2) + "\n",
    )

    # Fix dangling archive / flows / bare ledger-* references in points.csv
    # Preserve exact UTF-8 BOM + '\n' and NEVER modify P031 / P209!
    points_path = ROOT / "points.csv"
    orig_bytes = points_path.read_bytes()
    assert orig_bytes.startswith(b"\xef\xbb\xbf"), "points.csv must start with UTF-8 BOM"
    assert b"\r\n" not in orig_bytes, "points.csv must use LF line endings"

    pts_text = orig_bytes.decode("utf-8-sig")
    pts_rows = list(csv.reader(io.StringIO(pts_text)))
    header = pts_rows[0]
    idx_pid = header.index("point_id")
    idx_anchor = header.index("锚点URL")

    # Save P031 and P209 snapshots to assert zero change
    protected_before = {
        r[idx_pid]: list(r) for r in pts_rows[1:] if r[idx_pid] in ("P031", "P209")
    }

    updated_pids = []
    for row in pts_rows[1:]:
        pid = row[idx_pid]
        assert pid not in ("P031", "P209") or row == protected_before[pid]
        anchor = row[idx_anchor]
        new_anchor = anchor

        if pid == "P013":
            new_anchor = new_anchor.replace(
                "（ledger-SJZ SJZ284/286）",
                "（corpus/legacy-input/v16/prospectus/688313_仕佳光子_招股说明书_注册稿.txt#SJZ24；corpus/content_ledger/content_ledger.csv#SJZ24）",
            ).replace(
                "（ledger-SJ24 SJ24-32起）",
                "（corpus/annual-2024/688313/688313__em_仕佳光子_em__2024_2024年年度报告.pdf.txt#SJ24-18；corpus/content_ledger/content_ledger.csv#SJ24-18）",
            )
        elif pid == "P025":
            new_anchor = new_anchor.replace(
                "（ledger-TCG24 TCG24-产品应用表段）",
                "（corpus/annual-2024/300570/300570__em_太辰光_em__2024_2024年年度报告.pdf.txt#L446；corpus/content_ledger/content_ledger.csv#TCG24-09）",
            )
        elif pid == "P026":
            new_anchor = new_anchor.replace(
                "（ledger-TCG24 TCG24研发投入表，2024年报）",
                "（corpus/annual-2024/300570/300570__em_太辰光_em__2024_2024年年度报告.pdf.txt#L860；corpus/content_ledger/content_ledger.csv#TCG24-19，2024年报研发投入表）",
            )
        elif pid == "P058":
            new_anchor = new_anchor.replace(
                "T1并入候选来自`flows/out/t1-leaf-fill.md`",
                "本地全文见 corpus/annual/002222/002222/002222__em_福晶科技_em__2025_2025年年度报告.pdf.txt#L289（历史T1叶格补强批次）",
            )

        if new_anchor != anchor:
            row[idx_anchor] = new_anchor
            updated_pids.append(pid)

    for pid, snap in protected_before.items():
        cur = next(r for r in pts_rows[1:] if r[idx_pid] == pid)
        assert cur == snap, f"Protected row {pid} was unexpectedly altered!"

    # Verify zero remaining dangling flows/out or bare ledger-TCG24/SJZ/SJ24 references
    for row in pts_rows[1:]:
        blob = " ".join(row)
        assert "flows/out/" not in blob, f"Dangling flows/out/ in {row[idx_pid]}"
        assert "ledger-TCG24" not in blob, f"Dangling ledger-TCG24 in {row[idx_pid]}"
        assert "ledger-SJZ" not in blob, f"Dangling ledger-SJZ in {row[idx_pid]}"
        assert "ledger-SJ24" not in blob, f"Dangling ledger-SJ24 in {row[idx_pid]}"

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerows(pts_rows)
    new_points_bytes = b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")
    points_changed = write_bytes_if_changed(points_path, new_points_bytes)

    return {
        "truth_total": len(checks),
        "truth_passed": passed_count,
        "points_rows_total": len(pts_rows) - 1,
        "points_remediated_target_ids": ["P013", "P025", "P026", "P058"],
        "points_dangling_refs_remaining": 0,
    }


# ---------------------------------------------------------------------------
# Task 3: 节点国别/代码/夹层统一表 (entity_nodes.csv + refs/entity-registry.yaml)
# ---------------------------------------------------------------------------
INTERMEDIARY_SPECS: dict[str, str] = {
    "N17": "出口代理贸易商夹层(浙江省粮油食品进出口股份有限公司;新易盛2023-2025年报收入确认政策点名E016,非终端客户)",
    "N23": "CATV分销商夹层(AAOI下游分销商E012,终端MSO运营商在报表中被遮蔽)",
    "N29": "关联方境外销售/结算平台夹层(中际旭创关联自然人任职E044,2025销售额4.3378亿美元对应客户E=30.97亿元/8.10%,非终端云厂)",
    "N36": "日系精密滑台进口代理商夹层(猎奇智能上游代理商,穿透原厂为日本滑台厂商)",
    "N37": "日本神津精机(Kohzu)代理商夹层(猎奇智能高精度运动台代理供应商)",
    "N45": "测试测量设备经销商夹层(联讯仪器经销渠道客户,非终端模块/芯片产线用户)",
    "N50": "发行人自设境外销售子公司结算平台(长芯博创/博创科技英国全资销售平台E145/E147)",
    "N66": "客户自设境外采购控股平台(仕佳光子招股书p.1-1-310明示为AAOI境外子公司E113)",
    "N84": "外资原厂在华商贸结算子公司(京瓷株式会社Kyocera在华商贸主体E169)",
    "N88": "匿名分销商夹层槽位(仅披露分销渠道身份,终端客户未具名)",
    "N117": "匿名分销商夹层槽位(仅披露分销商槽位,终端客户未具名)",
    "N164": "贸易/进出口代理及委托加工商务结算平台(源杰科技交易对手方E199)",
}

EVAPORATED_PANAMA_NOTES: dict[str, str] = {
    "N17": "panorama两头蒸发归宿:原leaf-029贸易/代理非BOM节点,在edges.csv#E016以EXT保留出口代理身份,不入BOM生产点",
    "N28": "panorama两头蒸发归宿:原leaf-030跨行业科研院所(仅edges.csv#E013边schema参考),不入光模块BOM能力点",
    "N29": "panorama两头蒸发归宿:原leaf-031关联方境外销售结算主体(edges.csv#E044),穿透终端前禁作终端算力客户",
    "N30": "panorama两头蒸发归宿:原leaf-030跨行业汽车电机客户(edges.csv#E046猎奇非光通信客户),不入光模块BOM能力点",
    "N158": "panorama两头蒸发归宿:原leaf-028下游线缆连接器客户(edges.csv#E128 EXT),修复原nodes.csv名称左半截截断并补齐创业板代码300252",
    "N166": "panorama两头蒸发归宿:原leaf-029物流承运服务商(edges.csv#E200,顺丰控股子公司),修复原nodes.csv误标光/电芯片,不入BOM能力点",
}

NODE_OVERRIDES: dict[str, dict[str, str]] = {
    "N05": {"code_or_ticker": "NASDAQ:ACIA(已退市)", "listing_status": "已退市(2021被Cisco收购并表)"},
    "N06": {"code_or_ticker": "NASDAQ:INFN(已退市)", "listing_status": "已退市(2025-02被Nokia收购并表)"},
    "N07": {"code_or_ticker": "NYSE:NPTN(已退市)", "listing_status": "已退市(2022-08被Lumentum收购并表)"},
    "N08": {"aliases": "华为|海思|华为+海思|华为技术有限公司", "code_or_ticker": "", "listing_status": "未上市私企"},
    "N13": {"code_or_ticker": "", "listing_status": "创业板IPO在审"},
    "N14": {"aliases": "罗博特科|ficonTEC|ficonTEC(罗博特科)", "code_or_ticker": "300757", "listing_status": "A股上市(创业板:300757,含并购标的德国ficonTEC)"},
    "N17": {
        "canonical_name": "浙江粮油",
        "aliases": "浙江省粮油食品进出口股份有限公司|浙江粮油(出口代理)",
        "code_or_ticker": "",
        "listing_status": "未上市国企控股",
    },
    "N19": {"aliases": "AAOI|Applied Optoelectronics", "code_or_ticker": "NASDAQ:AAOI"},
    "N23": {"aliases": "Digicomm International", "code_or_ticker": "", "listing_status": "未上市私企"},
    "N28": {
        "canonical_name": "等离子体所",
        "aliases": "中国科学院合肥物质科学研究院等离子体物理研究所|等离子体所(客户)",
        "code_or_ticker": "",
        "listing_status": "科研事业单位(非上市)",
    },
    "N29": {
        "canonical_name": "PINEWAVE",
        "aliases": "PINEWAVE(关联方)",
        "entity_role": "旭创关联方(境外销售/结算主体)",
        "country": "境外(注册地待核)",
        "code_or_ticker": "",
        "listing_status": "未上市",
    },
    "N30": {
        "canonical_name": "索恩格(SEG Automotive)",
        "aliases": "索恩格|SEG Automotive",
        "code_or_ticker": "",
        "listing_status": "未上市",
    },
    "N31": {
        "canonical_name": "索尔思(Source Photonics)",
        "aliases": "索尔思光电|Source Photonics",
        "entity_role": "光模块/光芯片厂",
        "country": "中国/美国",
        "code_or_ticker": "002384(东山精密并表)",
        "listing_status": "东山精密002384收购并表子公司(未单独上市)",
        "extra_note": "东山精密(002384)已完成收购并表,并表后能力点见东山精密P130-P133(P200/P201为历史锚)",
    },
    "N43": {
        "canonical_name": "联讯仪器",
        "aliases": "苏州联讯仪器股份有限公司",
        "code_or_ticker": "688808",
        "listing_status": "科创板已上市(688808,2026-04-24上市;points P061待v6同步)",
        "extra_note": "科创板2026-04-24上市(688808),points P061暂保未上市私企标签待v6宇宙扩容同步",
    },
    "N49": {"country": "土耳其", "listing_status": "境外未上市"},
    "N50": {"country": "英国", "code_or_ticker": "300548(英国子)", "listing_status": "长芯博创(300548)境外全资子公司"},
    "N51": {"country": "中国香港", "code_or_ticker": "NASDAQ:LITE(并表子)", "listing_status": "Lumentum(NASDAQ:LITE)2023-11收购并表子公司"},
    "N52": {"country": "美国", "code_or_ticker": "NYSE:GLW", "listing_status": "美股上市(NYSE:GLW)"},
    "N53": {"country": "美国", "code_or_ticker": "NYSE:GLW", "listing_status": "美股上市(NYSE:GLW,解匿映射实体)"},
    "N54": {"country": "德国/欧洲", "listing_status": "境外未上市"},
    "N55": {"country": "巴西", "listing_status": "境外未上市"},
    "N56": {"country": "日本", "code_or_ticker": "TSE:5801", "listing_status": "日股上市(TSE:5801,古河电工)"},
    "N57": {"country": "境外", "listing_status": "缩写待核(剑桥科技客户HTI)"},
    "N58": {"country": "美国", "code_or_ticker": "NASDAQ:INTC", "listing_status": "美股上市(NASDAQ:INTC,含成都封测厂等代工体系)"},
    "N59": {"country": "马来西亚", "listing_status": "境外未上市"},
    "N60": {"country": "美国", "listing_status": "已破产重整(博创科技坏账核销对象E146)"},
    "N61": {"country": "日本", "code_or_ticker": "TSE:5344", "listing_status": "日股上市(TSE:5344)"},
    "N62": {"country": "美国", "code_or_ticker": "NASDAQ:MRVL", "listing_status": "美股上市(NASDAQ:MRVL)"},
    "N63": {"country": "美国", "listing_status": "境外未上市"},
    "N64": {"country": "日本", "code_or_ticker": "TSE:5218(Ohara子)", "listing_status": "Ohara Inc(TSE:5218)子公司"},
    "N65": {"country": "意大利", "listing_status": "境外未上市"},
    "N66": {"country": "境外(AAOI子)", "code_or_ticker": "NASDAQ:AAOI(子)", "listing_status": "AAOI(NASDAQ:AAOI)境外子公司"},
    "N67": {"country": "美国/境外", "listing_status": "境外未上市"},
    "N74": {"country": "中国(中外合资)", "code_or_ticker": "NYSE:NOK(合资子)", "listing_status": "诺基亚与中国华信合资旗舰企业"},
    "N77": {"aliases": "铭普光磁"},
    "N80": {"aliases": "中天科技"},
    "N82": {"aliases": "中航光电"},
    "N83": {"aliases": "亨通光电"},
    "N84": {"aliases": "京瓷", "country": "中国(日资)", "code_or_ticker": "TSE:6971(在华商贸子)", "listing_status": "京瓷株式会社(TSE:6971)在华商贸子公司"},
    "N88": {"listing_status": "匿名槽位"},
    "N90": {"listing_status": "匿名槽位"},
    "N93": {"code_or_ticker": "NASDAQ:AXTI(控股子)", "listing_status": "AXT Inc(NASDAQ:AXTI)控股子公司(科创板IPO终止)"},
    "N95": {"aliases": "长芯博创|博创科技股份有限公司", "code_or_ticker": "300548", "listing_status": "A股上市(创业板:300548,现更名长芯博创)"},
    "N96": {"aliases": "长芯博创|博创科技", "code_or_ticker": "300548", "listing_status": "A股上市(创业板:300548,现更名长芯博创)"},
    "N103": {"aliases": "大阳日酸特殊气体", "country": "中国(日资)", "code_or_ticker": "TSE:4091(子)", "listing_status": "日本酸素HD(TSE:4091)子公司"},
    "N106": {"code_or_ticker": "837597", "listing_status": "新三板挂牌(837597)"},
    "N107": {"country": "德国/中国", "listing_status": "德国Rosenberger集团主体"},
    "N109": {"aliases": "储翰科技|成都储翰科技股份有限公司", "code_or_ticker": "831964(已摘牌/300308子)", "listing_status": "新三板已摘牌(中际旭创300308控股子公司)"},
    "N111": {"aliases": "成都智禾光通|成都智禾光通科技有限公司", "code_or_ticker": "300308(全资子)", "listing_status": "中际旭创(300308)全资子公司"},
    "N115": {"code_or_ticker": "600206(全资子)", "listing_status": "有研新材(600206)全资子公司"},
    "N116": {"country": "美国/中国", "code_or_ticker": "NYSE:DD", "listing_status": "美股上市(NYSE:DD)及在华关联方"},
    "N117": {"listing_status": "匿名槽位"},
    "N119": {
        "aliases": "武汉云岭光电股份有限公司",
        "code_or_ticker": "874775(股改后)",
        "listing_status": "武汉云岭光电股份有限公司(874775)股改前身",
    },
    "N120": {"code_or_ticker": "874775", "listing_status": "新三板挂牌(874775)"},
    "N121": {"code_or_ticker": "874868", "listing_status": "新三板挂牌(874868)"},
    "N122": {"canonical_name": "武汉昱升光电股份有限公司", "aliases": "武汉昱升光电(原昱升光器件,同主体待补工商锚)|武汉昱升光器件有限公司|武汉昱升光电(原昱升光器件)", "listing_status": "未上市(IPO辅导中)"},
    "N123": {"code_or_ticker": "000988(子)", "listing_status": "华工科技(000988)子公司"},
    "N125": {"code_or_ticker": "601869(关联子)", "listing_status": "长飞光纤系子公司"},
    "N127": {"aliases": "汇聚科技|汇聚科技(Huiju Technology)", "country": "中国香港/中国", "code_or_ticker": "01729.HK", "listing_status": "港股上市(01729.HK汇聚科技境内全资子公司)"},
    "N130": {
        "canonical_name": "波若威光纤通讯有限公司",
        "aliases": "波若威|波若威光纤通讯（中山）有限公司|Browave",
        "entity_role": "光器件厂",
        "country": "中国台湾/中国",
        "code_or_ticker": "台股上柜3163",
        "listing_status": "台股上柜3163(母公司波若威科技;大陆子公司)",
        "extra_note": "母公司台湾波若威科技股份有限公司为台股上柜3163(points P264/P265已同步台股标签)",
    },
    "N132": {"country": "瑞士/美国/中国", "code_or_ticker": "NYSE:TEL", "listing_status": "美股上市(NYSE:TEL,TE Connectivity)及关联方"},
    "N140": {"aliases": "路维光电"},
    "N143": {"aliases": "炬光|炬光科技", "code_or_ticker": "688167(子)", "listing_status": "炬光科技(688167)子公司"},
    "N144": {"listing_status": "匿名槽位"},
    "N145": {"aliases": "腾景科技"},
    "N148": {"code_or_ticker": "300308(全资子)", "listing_status": "中际旭创(300308)核心全资运营子公司"},
    "N156": {"aliases": "诺力昂化学品", "country": "荷兰/中国", "listing_status": "跨国化工企业(Nouryon)在华子公司"},
    "N157": {"code_or_ticker": "688313(子)", "listing_status": "仕佳光子(688313)子公司"},
    "N158": {
        "canonical_name": "金信诺及其关联方",
        "aliases": "金信诺|深圳金信诺高新技术股份有限公司|金信诺及其关联方轨道信号系统科技有限公司、赣州金信诺电缆技术有限公司、金信诺光纤光缆有限公司、东莞金信诺电子有限公司）",
        "entity_role": "线缆/连接器系统商",
        "country": "中国",
        "code_or_ticker": "300252",
        "listing_status": "A股上市(创业板:300252)",
    },
    "N161": {"aliases": "长飞光纤|长飞光纤合并|YOFC", "code_or_ticker": "601869/06869.HK", "listing_status": "A+H股上市(601869.SH/06869.HK,合并口径)"},
    "N162": {"aliases": "长飞光纤|长飞光纤光缆股份有限公司", "code_or_ticker": "601869/06869.HK", "listing_status": "A+H股上市(601869.SH/06869.HK,单体口径)"},
    "N163": {"listing_status": "未上市国企(延长石油系,下属兴化股份002109)"},
    "N165": {"aliases": "海信宽带", "listing_status": "海信集团控股子公司(未单独上市)"},
    "N166": {
        "canonical_name": "顺丰速运",
        "aliases": "顺丰速运(源杰释义:西安顺丰及其咸阳分公司)|顺丰速运(西安顺丰及其咸阳分公司)|西安顺丰速运",
        "entity_role": "物流承运服务商",
        "country": "中国",
        "code_or_ticker": "002352(顺丰控股子)",
        "listing_status": "顺丰控股(002352.SZ/06936.HK)全资子公司",
    },
    "N168": {
        "canonical_name": "飞顿国际",
        "aliases": "飞顿国际有限公司、飞顿国际科技有限公司|飞顿贸易（北京）有限公司|飞顿国际科技（北京）有限公司|飞顿国际有限公司、飞顿国际科技有限公司）",
        "country": "以色列/中国",
        "listing_status": "复锐医疗科技(01696.HK/Alma Lasers)关联业务主体",
    },
    "N169": {"country": "中国香港", "listing_status": "香港未上市"},
}


def build_entity_nodes_and_registry() -> dict[str, Any]:
    with (ROOT / "archive" / "output" / "nodes.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        raw_nodes = list(csv.DictReader(fh))
    assert len(raw_nodes) == 169, f"Expected 169 nodes.csv rows, got {len(raw_nodes)}"

    pdata = json.loads((ROOT / "archive" / "output" / "panorama-data.json").read_text(encoding="utf-8"))
    pcomp_by_nid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comp in pdata.get("companies", []):
        if comp.get("node_id"):
            pcomp_by_nid[comp["node_id"]].append(comp)

    with (ROOT / "corpus" / "_frozen.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        frozen_rows = list(csv.DictReader(fh))
    frozen_codes = {r["代码"].strip(): r for r in frozen_rows}
    frozen_names = {r["名称"].strip(): r for r in frozen_rows}

    with (ROOT / "points.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        points_rows = list(csv.DictReader(fh))
    points_by_company: dict[str, list[str]] = defaultdict(list)
    for pt in points_rows:
        points_by_company[pt["公司"].strip()].append(pt["point_id"].strip())

    def extract_clean_code(raw_code: str, p_codes: list[str]) -> str:
        c = raw_code.strip()
        if c and c not in ("未上市", "已退市", "—", "-") and "IPO" not in c:
            return c
        for pc in p_codes:
            pc = pc.strip()
            if not pc or pc.startswith("未上市"):
                continue
            if ":" in pc:
                prefix, val = pc.split(":", 1)
                if prefix in ("科创", "创业", "沪主板", "深主板"):
                    return val.strip()
                return pc
            return pc
        return ""

    def infer_listing_status(raw_code: str, code_or_ticker: str, p_codes: list[str]) -> str:
        rc = raw_code.strip()
        if rc == "已退市":
            return "已退市"
        if "IPO" in rc:
            return rc
        if code_or_ticker:
            if re.fullmatch(r"\d{6}", code_or_ticker):
                if code_or_ticker.startswith("688"):
                    return f"A股上市(科创板:{code_or_ticker})"
                if code_or_ticker.startswith(("300", "301")):
                    return f"A股上市(创业板:{code_or_ticker})"
                if code_or_ticker.startswith("6"):
                    return f"A股上市(沪主板:{code_or_ticker})"
                if code_or_ticker.startswith(("00", "002")):
                    return f"A股上市(深主板:{code_or_ticker})"
            if code_or_ticker.startswith(("NYSE:", "NASDAQ:")):
                return f"美股上市({code_or_ticker})"
            return f"已挂牌/上市({code_or_ticker})"
        return "未上市"

    def check_in_frozen(canon: str, aliases_list: list[str], code_or_ticker: str) -> bool:
        # Check exact 6-digit code or overseas key in _frozen.csv
        m6 = re.fullmatch(r"(\d{6})", code_or_ticker)
        if m6 and m6.group(1) in frozen_codes:
            return True
        if "/" in code_or_ticker:
            first_part = code_or_ticker.split("/")[0].strip()
            if first_part in frozen_codes:
                return True
        for cand in [canon, *aliases_list]:
            c = cand.strip()
            if not c:
                continue
            if c in frozen_codes or c in frozen_names:
                return True
            for fn in frozen_names:
                if len(c) >= 4 and (c == fn):
                    return True
        # Check ticker tail like NASDAQ:NVDA vs frozen_codes (e.g., Fabrinet, Ciena, Cisco, Coherent, Lumentum, AAOI, Marvell, Intel, Nokia, 博通(Broadcom), 汇聚科技)
        if code_or_ticker == "01729.HK" and "汇聚科技" in frozen_codes:
            return True
        return False

    def match_point_ids(nid: str, canon: str, aliases_list: list[str]) -> list[str]:
        # Avoid matching group/subsidiary duplicates falsely unless exact/alias match
        if nid in ("N148", "N111", "N109"):  # 旭创子公司不重复绑母公司P点
            return []
        if nid == "N53":  # Corning(解匿) 映射槽位
            return sorted(set(points_by_company.get("Corning Incorporated", [])))
        matched: list[str] = []
        search_names = [canon, *aliases_list]
        for sn in search_names:
            sn = sn.strip()
            if not sn:
                continue
            if sn in points_by_company:
                for pid in points_by_company[sn]:
                    if pid not in matched:
                        matched.append(pid)
        if not matched:
            for comp_name, pids in points_by_company.items():
                if comp_name == canon:
                    matched.extend(p for p in pids if p not in matched)
        return sorted(matched, key=lambda x: int(x[1:]))

    entity_rows: list[dict[str, str]] = []
    for rn in raw_nodes:
        nid = rn["node_id"].strip()
        raw_name = rn["名称"].strip()
        raw_role = rn["类型"].strip()
        raw_country = rn["国别"].strip()
        raw_code = rn["代码"].strip()
        raw_note = rn["备注"].strip()

        pcomps = pcomp_by_nid.get(nid, [])
        p_names = [c["name"].strip() for c in pcomps if c.get("name")]
        p_codes = [
            c["market_code"].strip()
            for c in pcomps
            if c.get("market_code") and c["market_code"].strip() != "未上市/未识别"
        ]

        ov = NODE_OVERRIDES.get(nid, {})
        canon = ov.get("canonical_name", raw_name)

        alias_set: list[str] = []
        if ov.get("aliases"):
            for a in ov["aliases"].split("|"):
                a = a.strip()
                if a and a != canon and a not in alias_set:
                    alias_set.append(a)
        if raw_name != canon and raw_name not in alias_set:
            alias_set.append(raw_name)
        for pn in p_names:
            if pn != canon and pn not in alias_set:
                alias_set.append(pn)

        role = ov.get("entity_role", raw_role)
        country = ov.get("country", raw_country or "待核")
        code_or_ticker = ov.get("code_or_ticker", extract_clean_code(raw_code, p_codes))
        listing_status = ov.get(
            "listing_status", infer_listing_status(raw_code, code_or_ticker, p_codes)
        )

        is_intermediary = nid in INTERMEDIARY_SPECS
        in_frozen = check_in_frozen(canon, alias_set, code_or_ticker)
        # Explicit safeguard: N43 联讯仪器 688808 is NOT yet in _frozen.csv (pending v6)
        if nid in ("N31", "N43", "N50", "N123", "N125", "N143", "N148", "N157"):
            in_frozen = False

        pids = match_point_ids(nid, canon, alias_set)

        note_parts: list[str] = []
        if is_intermediary:
            note_parts.append(f"[夹层:{INTERMEDIARY_SPECS[nid]}]")
        if nid in EVAPORATED_PANAMA_NOTES:
            note_parts.append(f"[{EVAPORATED_PANAMA_NOTES[nid]}]")
        if ov.get("extra_note"):
            note_parts.append(ov["extra_note"])
        if raw_note and raw_note != "v1.6r结构补全(修复轮重装)":
            note_parts.append(raw_note)

        entity_rows.append(
            {
                "node_id": nid,
                "canonical_name": canon,
                "aliases": "|".join(alias_set),
                "entity_role": role,
                "country": country,
                "code_or_ticker": code_or_ticker,
                "listing_status": listing_status,
                "is_intermediary_layer": "true" if is_intermediary else "false",
                "in_frozen_universe": "true" if in_frozen else "false",
                "point_ids": "|".join(pids),
                "notes": "；".join(note_parts),
            }
        )

    entity_cols = [
        "node_id",
        "canonical_name",
        "aliases",
        "entity_role",
        "country",
        "code_or_ticker",
        "listing_status",
        "is_intermediary_layer",
        "in_frozen_universe",
        "point_ids",
        "notes",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=entity_cols, lineterminator="\n")
    writer.writeheader()
    writer.writerows(entity_rows)
    write_text_if_changed(SALVAGED_DIR / "entity_nodes.csv", buf.getvalue(), encoding="utf-8")

    # Update refs/entity-registry.yaml in-place WITHOUT creating any extra file in refs/!
    reg_path = ROOT / "refs" / "entity-registry.yaml"
    reg_orig_text = reg_path.read_text(encoding="utf-8")
    marker = "\n# ====================== 节点目录层（Step 2 收编：169节点 + 6蒸发主体 + 夹层标识） ======================\n"
    base_text = reg_orig_text.split(marker)[0].rstrip() + "\n"

    # Verify preserved top-level keys exist in base_text
    base_doc = yaml.safe_load(base_text)
    for req_key in (
        "schema_version",
        "identity_layer",
        "observation_scope_layer",
        "supplemental_resolutions",
    ):
        assert req_key in base_doc, f"Missing required key {req_key} in refs/entity-registry.yaml!"

    intermediary_summary = [
        {
            "node_id": r["node_id"],
            "canonical_name": r["canonical_name"],
            "country": r["country"],
            "intermediary_note": INTERMEDIARY_SPECS[r["node_id"]],
        }
        for r in entity_rows
        if r["is_intermediary_layer"] == "true"
    ]
    evaporated_summary = [
        {
            "node_id": r["node_id"],
            "canonical_name": r["canonical_name"],
            "aliases": r["aliases"].split("|") if r["aliases"] else [],
            "code_or_ticker": r["code_or_ticker"],
            "is_intermediary_layer": r["is_intermediary_layer"] == "true",
            "disposition": EVAPORATED_PANAMA_NOTES[r["node_id"]],
        }
        for r in entity_rows
        if r["node_id"] in EVAPORATED_PANAMA_NOTES
    ]
    compact_nodes = [
        {
            "node_id": r["node_id"],
            "canonical_name": r["canonical_name"],
            "aliases": [a for a in r["aliases"].split("|") if a],
            "entity_role": r["entity_role"],
            "country": r["country"],
            "code_or_ticker": r["code_or_ticker"],
            "listing_status": r["listing_status"],
            "is_intermediary_layer": r["is_intermediary_layer"] == "true",
            "intermediary_note": INTERMEDIARY_SPECS.get(r["node_id"], ""),
            "in_frozen_universe": r["in_frozen_universe"] == "true",
            "point_ids": [p for p in r["point_ids"].split("|") if p],
        }
        for r in entity_rows
    ]

    node_directory_payload = {
        "node_directory": {
            "source_table": "corpus/salvaged/entity_nodes.csv",
            "updated_date": BUILD_DATE,
            "total_nodes": len(entity_rows),
            "in_frozen_universe_count": sum(
                1 for r in entity_rows if r["in_frozen_universe"] == "true"
            ),
            "with_points_count": sum(1 for r in entity_rows if r["point_ids"]),
            "intermediary_count": len(intermediary_summary),
            "evaporated_panorama_entities_count": len(evaporated_summary),
            "status_corrections_2026": {
                "联讯仪器": {
                    "node_id": "N43",
                    "code_or_ticker": "688808",
                    "status": "科创板2026-04-24上市(points.csv P061待v6宇宙扩容同步切为A股)",
                },
                "索尔思(Source Photonics)": {
                    "node_id": "N31",
                    "code_or_ticker": "002384(东山精密并表)",
                    "status": "东山精密002384完成收购并表(并表后能力点见P130-P133,历史锚P200/P201)",
                },
                "波若威": {
                    "node_id": "N130",
                    "code_or_ticker": "台股上柜3163",
                    "status": "台湾波若威科技(上柜3163)大陆子公司波若威光纤通讯(points P264/P265标台股)",
                },
            },
            "evaporated_panorama_entities": evaporated_summary,
            "intermediary_entities": intermediary_summary,
            "edge_only_supplemental_entities": [
                {
                    "canonical_name": "苏世博",
                    "source_edge_id": "E050",
                    "entity_role": "汽车底盘零部件客户(跨行业)",
                    "country": "德国/中国",
                    "disposition": "猎奇智能汽车自动化线客户(E050),原nodes.csv未编号,非光模块BOM节点",
                }
            ],
            "nodes": compact_nodes,
        }
    }

    dumped_dir_yaml = yaml.safe_dump(
        node_directory_payload,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    combined_reg_text = base_text + marker + dumped_dir_yaml

    # Validate YAML in memory BEFORE writing in-place!
    parsed_check = yaml.safe_load(combined_reg_text)
    assert isinstance(parsed_check, dict)
    assert len(parsed_check["node_directory"]["nodes"]) == 169
    assert len(parsed_check["node_directory"]["evaporated_panorama_entities"]) == 6

    reg_changed = write_text_if_changed(reg_path, combined_reg_text, encoding="utf-8")
    refs_files = os.listdir(ROOT / "refs")
    assert len(refs_files) == 8, f"refs/ file count must be 8, got {len(refs_files)}: {refs_files}"

    return {
        "entity_nodes_total": len(entity_rows),
        "in_frozen_count": sum(1 for r in entity_rows if r["in_frozen_universe"] == "true"),
        "with_points_count": sum(1 for r in entity_rows if r["point_ids"]),
        "intermediary_count": len(intermediary_summary),
        "evaporated_entities_count": len(evaporated_summary),
        "entity_registry_yaml_valid": True,
        "refs_file_count": len(refs_files),
    }


# ---------------------------------------------------------------------------
# Task 4: 海关四维明细表、HS 85177950 映射字典与 macro_evidence MC033–MC035
# ---------------------------------------------------------------------------
def build_customs_and_macro() -> dict[str, Any]:
    flows_out = ROOT / "archive" / "flows" / "out"

    def read_clean_customs(src_name: str) -> tuple[list[str], list[dict[str, str]], int]:
        src_path = flows_out / src_name
        with src_path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = [f.strip() for f in (reader.fieldnames or [])]
            cleaned_rows: list[dict[str, str]] = []
            embedded_newlines_cleaned = 0
            for raw_row in reader:
                clean_row: dict[str, str] = {}
                for k, v in raw_row.items():
                    ck = k.strip()
                    val = v or ""
                    if "\n" in val or "\r" in val:
                        embedded_newlines_cleaned += 1
                    cv = val.strip()
                    if ck == "来源文件":
                        cv = cv.replace("flows/out/", "corpus/customs/")
                    clean_row[ck] = cv
                cleaned_rows.append(clean_row)
        return fieldnames, cleaned_rows, embedded_newlines_cleaned

    m_cols, m_rows, m_nl = read_clean_customs("customs-monthly.csv")
    pa_cols, pa_rows, pa_nl = read_clean_customs("customs-partners.csv")
    pr_cols, pr_rows, pr_nl = read_clean_customs("customs-province.csv")
    tm_cols, tm_rows, tm_nl = read_clean_customs("customs-trademode.csv")

    assert pa_nl == 61, f"Expected 61 embedded newlines in customs-partners.csv, got {pa_nl}"
    assert m_nl == 0 and pr_nl == 0 and tm_nl == 0

    # Reconcile 202501-202606 (18 months) across all 4 tables (both USD and kg)
    m_usd = {r["月份"]: int(r["金额"]) for r in m_rows}
    m_kg = {r["月份"]: int(r["出口量kg"]) for r in m_rows}

    pa_usd: dict[str, int] = defaultdict(int)
    pr_usd: dict[str, int] = defaultdict(int)
    tm_usd: dict[str, int] = defaultdict(int)
    pa_kg: dict[str, int] = defaultdict(int)
    pr_kg: dict[str, int] = defaultdict(int)
    tm_kg: dict[str, int] = defaultdict(int)

    for r in pa_rows:
        pa_usd[r["月份"]] += int(r["金额"])
        pa_kg[r["月份"]] += int(r["出口量kg"])
    for r in pr_rows:
        pr_usd[r["月份"]] += int(r["金额USD"])
        pr_kg[r["月份"]] += int(r["出口量kg"])
    for r in tm_rows:
        tm_usd[r["月份"]] += int(r["金额USD"])
        tm_kg[r["月份"]] += int(r["出口量kg"])

    months_18 = sorted(pa_usd.keys())
    assert len(months_18) == 18 and months_18[0] == "202501" and months_18[-1] == "202606"

    max_usd_err_pct = 0.0
    max_kg_err_pct = 0.0
    for ym in months_18:
        mu, mk = m_usd[ym], m_kg[ym]
        u_err = max(abs(pa_usd[ym] - mu), abs(pr_usd[ym] - mu), abs(tm_usd[ym] - mu)) / mu * 100.0
        k_err = max(abs(pa_kg[ym] - mk), abs(pr_kg[ym] - mk), abs(tm_kg[ym] - mk)) / mk * 100.0
        max_usd_err_pct = max(max_usd_err_pct, u_err)
        max_kg_err_pct = max(max_kg_err_pct, k_err)
        assert mu == pa_usd[ym] == pr_usd[ym] == tm_usd[ym], f"USD mismatch at {ym}"
        assert mk == pa_kg[ym] == pr_kg[ym] == tm_kg[ym], f"KG mismatch at {ym}"

    def write_clean_csv(dst_path: Path, cols: list[str], rows_data: list[dict[str, str]]) -> None:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows_data)
        text = buf.getvalue()
        phys_lines = len(text.splitlines())
        assert phys_lines == len(rows_data) + 1, (
            f"{dst_path.name}: physical lines {phys_lines} != rows+1 ({len(rows_data)+1})"
        )
        write_text_if_changed(dst_path, text, encoding="utf-8")

    write_clean_csv(CUSTOMS_DIR / "customs_monthly.csv", m_cols, m_rows)
    write_clean_csv(CUSTOMS_DIR / "customs_partners.csv", pa_cols, pa_rows)
    write_clean_csv(CUSTOMS_DIR / "customs_province.csv", pr_cols, pr_rows)
    write_clean_csv(CUSTOMS_DIR / "customs_trademode.csv", tm_cols, tm_rows)

    # Clean catalog.csv (25 rows) -> hs85177950_product_catalog.csv
    cat_cols, cat_rows, _ = read_clean_customs("catalog.csv")
    assert len(cat_rows) == 25, f"Expected 25 catalog rows, got {len(cat_rows)}"
    write_clean_csv(CUSTOMS_DIR / "hs85177950_product_catalog.csv", cat_cols, cat_rows)

    # Clean linkage.csv (27 rows) -> hs85177950_company_linkage.csv
    lnk_cols, lnk_rows, _ = read_clean_customs("linkage.csv")
    assert len(lnk_rows) == 27, f"Expected 27 linkage rows, got {len(lnk_rows)}"
    for r in lnk_rows:
        anchor = r["证据锚点"]
        anchor = anchor.replace("flows/out/customs-partners.csv", "corpus/customs/customs_partners.csv")
        anchor = re.sub(
            r"\bflows-seed (FL01[3-6])\b",
            r"flows-seed \1 (来源: corpus/customs/ & archive/flows/)",
            anchor,
        )
        r["证据锚点"] = anchor
        assert "flows/out/" not in r["证据锚点"]
    write_clean_csv(CUSTOMS_DIR / "hs85177950_company_linkage.csv", lnk_cols, lnk_rows)

    # Compute exact figures for README and macro_evidence MC033–MC034
    usd_2024 = sum(v for ym, v in m_usd.items() if ym.startswith("2024"))
    usd_2025 = sum(v for ym, v in m_usd.items() if ym.startswith("2025"))
    kg_2025 = sum(v for ym, v in m_kg.items() if ym.startswith("2025"))
    usd_2026h1 = sum(v for ym, v in m_usd.items() if ym.startswith("2026"))
    kg_2026h1 = sum(v for ym, v in m_kg.items() if ym.startswith("2026"))

    partner_2025: dict[str, int] = defaultdict(int)
    partner_2026h1: dict[str, int] = defaultdict(int)
    for r in pa_rows:
        ym = r["月份"]
        p = r["贸易伙伴"]
        amt = int(r["金额"])
        if ym.startswith("2025"):
            partner_2025[p] += amt
        elif ym.startswith("2026"):
            partner_2026h1[p] += amt

    my_25_pct = partner_2025["马来西亚"] / usd_2025 * 100.0
    us_25_pct = partner_2025["美国"] / usd_2025 * 100.0
    th_25_pct = partner_2025["泰国"] / usd_2025 * 100.0
    tw_25_pct = partner_2025["中国台湾"] / usd_2025 * 100.0

    my_26_pct = partner_2026h1["马来西亚"] / usd_2026h1 * 100.0
    tw_26_pct = partner_2026h1["中国台湾"] / usd_2026h1 * 100.0
    th_26_pct = partner_2026h1["泰国"] / usd_2026h1 * 100.0
    us_26_pct = partner_2026h1["美国"] / usd_2026h1 * 100.0
    us_diff_pp = us_26_pct - us_25_pct  # -9.7695pp; 1-decimal 6.9 - 16.6 = -9.7pp

    customs_readme = f"""# 中国海关 HS `85177950` 四维统计底表与产品口径说明

## 1. 严格边界声明（遵守 `docs/control/PROJECT_CHARTER.md` §3）

1. **统计口径说明而非产品登记表**：本目录下的 `hs85177950_product_catalog.csv` 与 `hs85177950_company_linkage.csv` **仅作中国海关税则号列 HS `85177950`（“光通信设备的激光收发模块”）统计商品范围与公开目录型号的口径边界对照说明**，不构成产品登记表（product registry），亦**不构成任何 `offers_product` 或 `implements_route` 领域主张**。
2. **海关数据不分公司归属**：海关总署在线查询平台（`http://stats.customs.gov.cn/`）公开数据仅按月度、贸易伙伴、境内注册地省份、贸易方式汇总中国关境货物报关出口额与重量，**不含企业级提单字段，绝不可由此推导单一公司的出口额、市场份额或特定客户流向**（参见 `refs/解匿判例库.md` 判例 `#005` 反面教材）。
3. **关境边界**：本表仅涵盖从**中国境内关境报关出口**的激光收发模块，不包含中国厂商在泰国、马来西亚等海外工厂组装后直接发往第三国的出货。

## 2. 数据文件清单与对账结果

| 文件名 | 数据行数 | 时间跨度 | 说明 |
|---|---:|---|---|
| `customs_monthly.csv` | {len(m_rows)} | `202401–202606` | 全国月度出口总量与美元金额主表 |
| `customs_partners.csv` | {len(pa_rows)} | `202501–202606` | 分贸易伙伴国/地区明细（已清除原归档表 61 处国家名内嵌换行符，物理行 = {len(pa_rows)+1}） |
| `customs_province.csv` | {len(pr_rows)} | `202501–202606` | 分境内注册地省份 × 伙伴国明细 |
| `customs_trademode.csv` | {len(tm_rows)} | `202501–202606` | 分伙伴国 × 贸易方式明细 |
| `hs85177950_product_catalog.csv` | {len(cat_rows)} | 抓取日 `2026-07-23` | 官网公开模块系列名摘录（仅作税号商品形态参考） |
| `hs85177950_company_linkage.csv` | {len(lnk_rows)} | 抓取日 `2026-07-23` | 公开产品线与 HS `85177950` 税目边界对照（含非本税目的设备负样本 `LNK024–LNK027`） |

## 3. 四维底表精确汇总核验（对应 `macro_evidence.csv` `MC033–MC034`）

- **`202501–202606`（18 个月）四表逐月对账**：`partners`、`province`、`trademode` 每月美元汇总及出口重量（kg）与 `monthly` 逐月完全一致，最大相对误差 **`0.000%`**（逐月差值 `0` 美元、`0` 千克）。
- **2024 全年（`202401–202412`）**：`${usd_2024:,}` 美元（约 `{usd_2024/1e8:.2f}` 亿美元）。
- **2025 全年（`202501–202512`，`MC033`）**：`${usd_2025:,}` 美元（约 `{usd_2025/1e8:.2f}` 亿美元，`{kg_2025:,}` kg）；前四大伙伴为马来西亚 `{my_25_pct:.2f}%`（`${partner_2025["马来西亚"]:,}`）、美国 `{us_25_pct:.2f}%`（`${partner_2025["美国"]:,}`）、泰国 `{th_25_pct:.2f}%`（`${partner_2025["泰国"]:,}`）、中国台湾 `{tw_25_pct:.2f}%`（`${partner_2025["中国台湾"]:,}`）。
- **2026 上半年（`202601–202606`，`MC034`）**：`${usd_2026h1:,}` 美元（约 `{usd_2026h1/1e8:.2f}` 亿美元，`{kg_2026h1:,}` kg）；主要伙伴为马来西亚 `{my_26_pct:.2f}%`（`${partner_2026h1["马来西亚"]:,}`）、中国台湾 `{tw_26_pct:.2f}%`（`${partner_2026h1["中国台湾"]:,}`）、泰国 `{th_26_pct:.2f}%`（`${partner_2026h1["泰国"]:,}`）、直接对美降至 `{us_26_pct:.2f}%`（`${partner_2026h1["美国"]:,}`，精确较 2025 全年 `{us_25_pct:.2f}%` 下降 `{abs(us_diff_pp):.2f}pp`，一位小数口径 `{us_26_pct:.1f}%` vs `{us_25_pct:.1f}%` 下降 `{round(us_25_pct,1)-round(us_26_pct,1):.1f}pp`）。
"""
    write_text_if_changed(CUSTOMS_DIR / "README.md", customs_readme, encoding="utf-8")

    # Update macro_evidence.csv idempotently (preserve UTF-8 BOM + \r\n!)
    macro_path = ROOT / "macro_evidence.csv"
    macro_orig = macro_path.read_bytes()
    assert macro_orig.startswith(b"\xef\xbb\xbf"), "macro_evidence.csv must start with UTF-8 BOM"
    assert b"\r\n" in macro_orig, "macro_evidence.csv must use CRLF line endings"

    macro_rows = list(csv.reader(io.StringIO(macro_orig.decode("utf-8-sig"))))
    m_header = macro_rows[0]
    assert m_header == [
        "claim_id",
        "量化结论",
        "证据等级",
        "证据类型",
        "处理方式",
        "来源描述",
        "链接",
        "口径备注",
    ]
    kept_macro_rows = [
        r for r in macro_rows[1:] if r and r[0] not in ("MC033", "MC034", "MC035")
    ]

    us_drop_1d = round(us_25_pct, 1) - round(us_26_pct, 1)  # 16.6 - 6.9 = 9.7
    new_mc_rows = [
        [
            "MC033",
            f"2025年中国关境HS 85177950光通信激光收发模块全年出口额{usd_2025/1e8:.2f}亿美元(12个月四维底表精确汇总;不含海外基地直接出货)",
            "A",
            "内部证据账本可重算",
            "首页展示或正文引用(须附中国关境口径)",
            f"中华人民共和国海关总署统计在线查询平台(HS 85177950“光通信设备的激光收发模块”,202501-202512月度及伙伴/省/贸易方式四维底表精确汇总={usd_2025:,}美元,出口量{kg_2025:,}千克)",
            "http://stats.customs.gov.cn/",
            f"由corpus/customs/customs_monthly.csv精确汇总(202501-202512={usd_2025:,}美元={usd_2025/1e8:.4f}亿美元,与customs_partners/province/trademode三表逐月对账误差0.000%;不含海外工厂直发)",
        ],
        [
            "MC034",
            f"2026H1中国关境HS 85177950出口额{usd_2026h1/1e8:.2f}亿美元(马来西亚占{my_26_pct:.1f}%/泰国{th_26_pct:.1f}%/直美降至{us_26_pct:.1f}%,较2025全年降{us_drop_1d:.1f}pp)",
            "A",
            "内部证据账本可重算",
            "正文引用(须附中国关境与不分公司口径)",
            f"中华人民共和国海关总署统计在线查询平台(HS 85177950,202601-202606总额{usd_2026h1:,}美元:马来西亚{partner_2026h1['马来西亚']:,}美元[{my_26_pct:.2f}%]、中国台湾{partner_2026h1['中国台湾']:,}美元[{tw_26_pct:.2f}%]、泰国{partner_2026h1['泰国']:,}美元[{th_26_pct:.2f}%]、美国{partner_2026h1['美国']:,}美元[{us_26_pct:.2f}%])",
            "http://stats.customs.gov.cn/",
            f"由corpus/customs/customs_partners.csv与corpus/customs/customs_monthly.csv精确汇总(直美占比由2025全年{us_25_pct:.2f}%[{partner_2025['美国']:,}/{usd_2025:,}]降至2026H1的{us_26_pct:.2f}%,精确变动{us_diff_pp:.2f}pp,一位小数口径{us_26_pct:.1f}%-{us_25_pct:.1f}%=-{us_drop_1d:.1f}pp)",
        ],
        [
            "MC035",
            "Yole CPO市场预测2030年54亿美元/CAGR 121%为机柜内(Scale-Up)自洽口径,新闻稿137%系跨表口径拼接",
            "C",
            "机构报告口径核查",
            "二手汇总,仅方向性参考不上首页",
            "Yole Group CPO市场报告与官方新闻稿跨口径核查(原卖方溯源F-016与diff-log D002质检裁决)",
            "",
            "吸收自原diff-log.csv D002对Yole原报告与新闻稿之口径核查",
        ],
    ]

    all_macro_rows = [m_header, *kept_macro_rows, *new_mc_rows]
    m_buf = io.StringIO()
    m_writer = csv.writer(m_buf, lineterminator="\r\n")
    m_writer.writerows(all_macro_rows)
    new_macro_bytes = b"\xef\xbb\xbf" + m_buf.getvalue().encode("utf-8")
    macro_changed = write_bytes_if_changed(macro_path, new_macro_bytes)

    return {
        "customs_monthly_rows": len(m_rows),
        "customs_partners_rows": len(pa_rows),
        "customs_partners_physical_lines": len(pa_rows) + 1,
        "customs_partners_newlines_stripped": pa_nl,
        "customs_province_rows": len(pr_rows),
        "customs_trademode_rows": len(tm_rows),
        "reconciled_months": len(months_18),
        "max_usd_reconciliation_error_pct": max_usd_err_pct,
        "max_kg_reconciliation_error_pct": max_kg_err_pct,
        "hs85177950_catalog_rows": len(cat_rows),
        "hs85177950_linkage_rows": len(lnk_rows),
        "usd_2024_total": usd_2024,
        "usd_2025_total": usd_2025,
        "kg_2025_total": kg_2025,
        "usd_2026h1_total": usd_2026h1,
        "kg_2026h1_total": kg_2026h1,
        "shares_2025_pct": {
            "马来西亚": round(my_25_pct, 4),
            "美国": round(us_25_pct, 4),
            "泰国": round(th_25_pct, 4),
            "中国台湾": round(tw_25_pct, 4),
        },
        "shares_2026h1_pct": {
            "马来西亚": round(my_26_pct, 4),
            "中国台湾": round(tw_26_pct, 4),
            "泰国": round(th_26_pct, 4),
            "美国": round(us_26_pct, 4),
            "美国较2025变动_pp": round(us_diff_pp, 4),
        },
        "macro_evidence_total_rows": len(all_macro_rows) - 1,
        "macro_added_ids": ["MC033", "MC034", "MC035"],
        "macro_encoding": "UTF-8-BOM+CRLF",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SALVAGED_DIR.mkdir(parents=True, exist_ok=True)
    CUSTOMS_DIR.mkdir(parents=True, exist_ok=True)

    t1 = build_demo_dedupe_and_v16_sidecars()
    t2 = build_truth_assertions_and_fix_points()
    t3 = build_entity_nodes_and_registry()
    t4 = build_customs_and_macro()

    summary = {
        "shard": "A",
        "agent": "carbon-customs-entity",
        "generated_date": BUILD_DATE,
        "script": "out/step2-archive-salvage-20261121/build_customs_and_entities.py",
        "task1_demo_and_v16": t1,
        "task2_truth_and_points": t2,
        "task3_entities_and_registry": t3,
        "task4_customs_and_macro": t4,
    }
    write_text_if_changed(
        OUT_DIR / "shard-a-summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
