#!/usr/bin/env python3
"""Step 3 工人 3 构建脚本: v6 宇宙分母对称扩容与持久 Daily 95/5 审核池建设.

幂等可重跑: 二次运行所有目标文件 SHA-256 零漂移;
外部只读目录 (/Users/jowang/Downloads/workflow-rehearsal{,-daily-state}) 零修改;
refs/ 严格保持 8 个文件。
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import csv
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path("/Users/jowang/Downloads/optical-module-research")
WR_ANNUAL = Path("/Users/jowang/Downloads/workflow-rehearsal/corpus/annual")
WR_YNG = Path("/Users/jowang/Downloads/workflow-rehearsal/tmp/yng/002428")
OUT_SUMMARY = ROOT / "out" / "step3-daily-and-v6-20261121" / "shard-universe-queue-summary.json"
BUILD_DATE = "2026-11-21"
FORBIDDEN_PHRASES = ("已覆盖", "已完成", "已回答")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_bytes_if_changed(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def write_text_if_changed(path: Path, text: str, encoding: str = "utf-8") -> bool:
    return write_bytes_if_changed(path, text.encode(encoding))


def copy_file_idempotent(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_hash = sha256_file(src)
    if dst.exists() and not dst.is_symlink() and sha256_file(dst) == src_hash:
        return False
    shutil.copy2(src, dst)
    return True


def extract_pdftotext_idempotent(pdf_path: Path, txt_path: Path) -> bool:
    """使用 pdftotext -layout 提取确定性 .pdf.txt 旁车; 若已存在且非空则校验后保持幂等."""
    res = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        check=True,
    )
    expected_bytes = res.stdout
    if len(expected_bytes.strip()) == 0:
        raise RuntimeError(f"pdftotext 提取结果为空: {pdf_path}")
    return write_bytes_if_changed(txt_path, expected_bytes)


# ---------------------------------------------------------------------------
# A.1 安全展开 corpus/annual 顶层软链 -> 463 个逐公司软链
# ---------------------------------------------------------------------------
def expand_annual_top_symlink() -> dict[str, Any]:
    assert WR_ANNUAL.is_dir(), f"外部年报源目录不存在: {WR_ANNUAL}"
    wr_before = sorted(os.listdir(WR_ANNUAL))
    assert len(wr_before) == 463, f"外部年报源目录项数异常(期望463): {len(wr_before)}"

    annual_dir = ROOT / "corpus" / "annual"
    was_top_symlink = os.path.islink(annual_dir)
    if was_top_symlink:
        assert os.path.realpath(annual_dir) == os.path.realpath(WR_ANNUAL), (
            f"corpus/annual 软链目标非预期: {os.path.realpath(annual_dir)}"
        )
        # 严禁 shutil.rmtree! 仅使用 os.unlink 解除顶层软链
        os.unlink(annual_dir)
        os.makedirs(annual_dir, exist_ok=True)
    else:
        assert annual_dir.is_dir() and not os.path.islink(annual_dir), (
            "corpus/annual 必须为真实目录"
        )

    created_links = 0
    verified_links = 0
    for code in wr_before:
        target = WR_ANNUAL / code
        dst = annual_dir / code
        if os.path.islink(dst):
            assert os.path.realpath(dst) == os.path.realpath(target), (
                f"软链目标不一致: {dst} -> {os.readlink(dst)}"
            )
            verified_links += 1
        elif not dst.exists():
            os.symlink(str(target), str(dst))
            created_links += 1
            verified_links += 1
        else:
            raise RuntimeError(f"原有463代码位置出现非软链实体冲突: {dst}")

    wr_after = sorted(os.listdir(WR_ANNUAL))
    assert wr_after == wr_before and len(wr_after) == 463, (
        "外部 workflow-rehearsal/corpus/annual 项数发生变化!"
    )
    return {
        "corpus_annual_is_top_symlink": os.path.islink(annual_dir),
        "corpus_annual_is_real_dir": annual_dir.is_dir() and not os.path.islink(annual_dir),
        "per_company_symlinks_verified": verified_links,
        "workflow_rehearsal_annual_count": len(wr_after),
    }


# ---------------------------------------------------------------------------
# A.2 落盘 v6 新增代码 (688808, 002428, 002957) 年报/招股书与 .pdf.txt 旁车
# ---------------------------------------------------------------------------
def populate_v6_annual_dirs() -> dict[str, Any]:
    annual_dir = ROOT / "corpus" / "annual"

    # 1) 688808 联讯仪器
    d_688808 = annual_dir / "688808"
    assert not os.path.islink(d_688808), "688808 必须为真实子目录而非软链"
    d_688808.mkdir(parents=True, exist_ok=True)

    src_lx_pdf = ROOT / "corpus" / "legacy-input" / "lianxun_prospectus.pdf"
    src_lx_txt = ROOT / "corpus" / "legacy-input" / "lianxun_prospectus.txt"
    dst_lx_pdf = d_688808 / "688808_联讯仪器_2026_招股说明书.pdf"
    dst_lx_txt = d_688808 / "688808_联讯仪器_2026_招股说明书.pdf.txt"
    copy_file_idempotent(src_lx_pdf, dst_lx_pdf)
    copy_file_idempotent(src_lx_txt, dst_lx_txt)

    # 顺带抓取 2026 半年报存作参考 (仅当本地尚未落盘时拉取，保证二次重跑零网络抖动与零字节漂移)
    lx_h1_url = "https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF"
    dst_lx_h1_pdf = d_688808 / "688808_联讯仪器_2026_2026年半年度报告.pdf"
    dst_lx_h1_txt = d_688808 / "688808_联讯仪器_2026_2026年半年度报告.pdf.txt"
    lx_h1_downloaded = False
    if dst_lx_h1_pdf.exists() and dst_lx_h1_pdf.stat().st_size > 100_000:
        with dst_lx_h1_pdf.open("rb") as fh:
            if fh.read(4) == b"%PDF":
                lx_h1_downloaded = True
    if not lx_h1_downloaded:
        try:
            resp = requests.get(
                lx_h1_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "Referer": "https://www.cninfo.com.cn/",
                },
                timeout=25,
            )
            if resp.status_code == 200 and resp.content.startswith(b"%PDF"):
                write_bytes_if_changed(dst_lx_h1_pdf, resp.content)
                lx_h1_downloaded = True
        except Exception:
            lx_h1_downloaded = False
    if lx_h1_downloaded:
        extract_pdftotext_idempotent(dst_lx_h1_pdf, dst_lx_h1_txt)

    # 2) 002428 云南锗业
    d_002428 = annual_dir / "002428"
    assert not os.path.islink(d_002428), "002428 必须为真实子目录而非软链"
    d_002428.mkdir(parents=True, exist_ok=True)

    yng_files_copied: list[str] = []
    for fn in (
        "002428__em_云南锗业_em__2025_2025年年度报告.pdf",
        "002428__em_云南锗业_em__2024_2024年年度报告.pdf",
    ):
        src_p = WR_YNG / fn
        assert src_p.exists(), f"缺失云南锗业年报源文件: {src_p}"
        dst_p = d_002428 / fn
        copy_file_idempotent(src_p, dst_p)
        dst_txt = d_002428 / f"{fn}.txt"
        extract_pdftotext_idempotent(dst_p, dst_txt)
        yng_files_copied.append(str(dst_p.relative_to(ROOT)))

    # 核验 2025 年报旁车确含磷化铟晶片 10.01 万片原文
    yng_2025_txt = (d_002428 / "002428__em_云南锗业_em__2025_2025年年度报告.pdf.txt").read_text(
        encoding="utf-8", errors="ignore"
    )
    assert "10.01" in yng_2025_txt and "磷化铟晶片" in re.sub(r"\s+", "", yng_2025_txt), (
        "002428 2025年报旁车未检出磷化铟晶片10.01万片关键句"
    )

    # 3) 002957 科瑞技术: 优先复用已验证落盘文件，缺失时调用 corpus/_fetch.py 下载 2025 年报
    d_002957 = annual_dir / "002957"
    assert not os.path.islink(d_002957), "002957 不可为软链"
    kerui_valid_pdfs: list[Path] = []

    def _find_valid_pdfs(folder: Path) -> list[Path]:
        if not folder.is_dir():
            return []
        found: list[Path] = []
        for dp, _, fns in os.walk(folder, followlinks=False):
            for fn in sorted(fns):
                if fn.lower().endswith(".pdf"):
                    fp = Path(dp) / fn
                    if fp.stat().st_size > 100_000:
                        with fp.open("rb") as fh:
                            if fh.read(4) == b"%PDF":
                                found.append(fp)
        return found

    kerui_valid_pdfs = _find_valid_pdfs(d_002957)
    if not kerui_valid_pdfs:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "corpus" / "_fetch.py"),
                "--stock-code",
                "002957",
                "--year",
                "2025",
                "--output",
                str(d_002957),
            ],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        kerui_valid_pdfs = _find_valid_pdfs(d_002957)

    kerui_included = False
    kerui_pdf_rels: list[str] = []
    if kerui_valid_pdfs:
        for kp in kerui_valid_pdfs:
            ktxt = Path(f"{kp}.txt")
            extract_pdftotext_idempotent(kp, ktxt)
            assert ktxt.exists() and ktxt.stat().st_size > 10_000
            kerui_pdf_rels.append(str(kp.relative_to(ROOT)))
        kerui_included = True
    else:
        # 明确规则: 未取到真实有效 PDF 时必须删除空目录，绝不留空缺口
        if d_002957.exists() and not os.path.islink(d_002957):
            resolved = d_002957.resolve()
            expected_prefix = (ROOT / "corpus" / "annual" / "002957").resolve()
            assert resolved == expected_prefix
            shutil.rmtree(resolved)

    # 确认未上市私企 微见智能、镭神技术 不在 corpus/annual
    for unlisted in ("微见智能", "镭神技术"):
        assert not (annual_dir / unlisted).exists()

    # 再次校验外部源目录零改动
    assert len(os.listdir(WR_ANNUAL)) == 463

    return {
        "688808_files": sorted(str(p.relative_to(ROOT)) for p in d_688808.rglob("*") if p.is_file()),
        "688808_h1_downloaded": lx_h1_downloaded,
        "002428_pdfs": yng_files_copied,
        "002957_included_in_frozen": kerui_included,
        "002957_pdfs": kerui_pdf_rels,
    }


# ---------------------------------------------------------------------------
# A.3 更新 _frozen.csv, tree.yaml, participation.py, entity_nodes.csv, entity-registry.yaml
# ---------------------------------------------------------------------------
def update_frozen_tree_participation_and_entities(kerui_included: bool) -> dict[str, Any]:
    # 1) corpus/_frozen.csv (保留基线前 463 家原始字节与 UTF-8 BOM，幂等重放 v6 新增行)
    frozen_path = ROOT / "corpus" / "_frozen.csv"
    raw_bytes = frozen_path.read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf"), "_frozen.csv 必须带 UTF-8 BOM"

    v6_codes = {"688808", "002428", "002957", "微见智能", "镭神技术"}
    kept_raw_lines: list[bytes] = []
    for raw_line in raw_bytes[3:].splitlines(keepends=True):
        line_str = raw_line.decode("utf-8").strip()
        if not line_str:
            continue
        first_col = next(csv.reader([line_str]))[0].strip()
        if first_col in v6_codes:
            continue
        kept_raw_lines.append(raw_line)

    if kept_raw_lines and not kept_raw_lines[-1].endswith((b"\n", b"\r\n")):
        kept_raw_lines[-1] = kept_raw_lines[-1] + b"\n"

    v6_rows: list[list[str]] = [
        [
            "688808",
            "联讯仪器",
            "上交所科创板",
            "宇宙外补录v6",
            "v6补录2026-11-21:点层需要(EQ7格,P061联讯仪器已于2026-04-24科创板上市,1.6T光模块核心测试仪器量产供货),申万仪器仪表/专用设备不在四行业初始快照;对称性:EQ7测试仪器层普源精电688337已在册;出处=科创板招股书+2026半年报 https://static.cninfo.com.cn/finalpage/2026-08-27/1225511954.PDF",
        ],
        [
            "002428",
            "云南锗业",
            "深交所主板",
            "宇宙外补录v6",
            "v6补录2026-11-21:点层与母子公司对称补录(M1格,控股84.53%子公司云南鑫耀P202生产磷化铟/砷化镓衬底,2025年报披露全年生产磷化铟晶片10.01万片),申万有色金属(金属新材料)不在四行业分母;对称性:M1衬底股东博杰股份/有研新材已核,未上市通美/兴光留观察;出处=巨潮2025年报 https://static.cninfo.com.cn/finalpage/2026-04-23/1225152695.PDF",
        ],
    ]
    if kerui_included:
        v6_rows.append(
            [
                "002957",
                "科瑞技术",
                "深交所主板",
                "宇宙外补录v6",
                "v6补录2026-11-21:设备层对称性补录(EQ3/EQ4格P275/P276,11/19审阅N03检出12家核心光模块设备商漏收),申万机械设备(自动化设备)不在四行业分母;对称性:罗博特科/奥特维/快克/天准/凯格/博众/普源/联讯已在_frozen,猎奇/微见智能/镭神技术未上市入observation_list,A股已上市仅漏科瑞技术故补齐分母(2025年报p.15已核出光模块芯片共晶贴片与50nm光耦合设备,客户匿名不具名Lumentum/Coherent);出处=巨潮2025年报 https://static.cninfo.com.cn/finalpage/2026-04-24/1225165073.PDF#page=15",
            ]
        )

    v6_buf = io.StringIO()
    v6_writer = csv.writer(v6_buf, lineterminator="\n")
    v6_writer.writerows(v6_rows)
    new_frozen_bytes = b"\xef\xbb\xbf" + b"".join(kept_raw_lines) + v6_buf.getvalue().encode("utf-8")
    write_bytes_if_changed(frozen_path, new_frozen_bytes)

    with frozen_path.open("r", encoding="utf-8-sig", newline="") as fh:
        frozen_records = list(csv.DictReader(fh))
    unique_codes = {r["代码"].strip() for r in frozen_records}
    n_frozen = len(unique_codes)
    expected_n = 466 if kerui_included else 465
    assert n_frozen == expected_n, f"_frozen 唯一代码数异常: {n_frozen} != {expected_n}"
    assert "微见智能" not in unique_codes and "镭神技术" not in unique_codes

    # 2) tree.yaml: 更新 universe.frozen_date / count / 补录 与 observation_list
    tree_path = ROOT / "tree.yaml"
    tree_text = tree_path.read_text(encoding="utf-8")

    tree_text = re.sub(
        r'^(\s*frozen_date:\s*)"[^"]*"',
        f'\\1"{BUILD_DATE}"',
        tree_text,
        count=1,
        flags=re.M,
    )
    tree_text = re.sub(
        r"^(\s*count:\s*)\d+",
        f"\\g<1>{n_frozen}",
        tree_text,
        count=1,
        flags=re.M,
    )

    v6_note = (
        f"v6=3家({BUILD_DATE},联讯仪器688808科创板IPO转正+云南锗业002428磷化铟母公司归并+科瑞技术002957设备层12家对称补齐;未上市微见智能/镭神技术同步入observation_list)"
        if kerui_included
        else f"v6=2家({BUILD_DATE},联讯仪器688808科创板IPO转正+云南锗业002428磷化铟母公司归并;科瑞技术002957待年报原件暂留review_queue,未上市微见智能/镭神技术入observation_list)"
    )

    def _update_bulu_line(match: re.Match[str]) -> str:
        prefix = re.sub(r",\s*v6=.*$", "", match.group(1).rstrip())
        return f"{prefix}, {v6_note}"

    tree_text = re.sub(
        r"^(\s*补录:\s*.*)$",
        _update_bulu_line,
        tree_text,
        count=1,
        flags=re.M,
    )

    # 幂等增补 observation_list 中的 微见智能 与 镭神技术 (严格单行花括号格式以兼容 scan.observation_names 正则!)
    obs_lines_filtered = [
        ln
        for ln in tree_text.splitlines()
        if not re.match(r"^\s*-\s*\{名称:\s*(微见智能|镭神技术)\b", ln)
    ]
    tree_idx = next(i for i, ln in enumerate(obs_lines_filtered) if ln.startswith("tree:"))
    insert_at = tree_idx
    while insert_at > 0 and obs_lines_filtered[insert_at - 1].strip() == "":
        insert_at -= 1

    new_obs_entries = [
        '  - {名称: 微见智能, 市场: 未上市私企, 理由: "高精度共晶贴片/固晶设备(EQ3对称性观察,微见智能封装技术(深圳)有限公司,待一手官网或客户锚过闸)"}',
        '  - {名称: 镭神技术, 市场: 未上市私企, 理由: "高精度光耦合封装设备(EQ4对称性观察,镭神技术(深圳)有限公司,猎奇招股书引F&S列2024全球耦合台数27%居首,待独立一手锚过闸)"}',
    ]
    rebuilt_tree_lines = (
        obs_lines_filtered[:insert_at]
        + new_obs_entries
        + [""]
        + obs_lines_filtered[tree_idx:]
    )
    new_tree_text = "\n".join(rebuilt_tree_lines) + "\n"

    tree_doc = yaml.safe_load(new_tree_text)
    assert isinstance(tree_doc, dict) and tree_doc["universe"]["count"] == n_frozen
    write_text_if_changed(tree_path, new_tree_text, encoding="utf-8")

    # 3) participation.py: 确保 COMPANY_ALIASES 含 "云南鑫耀半导体材料有限公司": "云南锗业"
    part_path = ROOT / "participation.py"
    part_text = part_path.read_text(encoding="utf-8")
    if '"云南鑫耀半导体材料有限公司": "云南锗业"' not in part_text:
        part_text = part_text.replace(
            '    "Intel": "Intel(含其代工厂)",\n}',
            '    "Intel": "Intel(含其代工厂)",\n    "云南鑫耀半导体材料有限公司": "云南锗业",\n}',
        )
        write_text_if_changed(part_path, part_text, encoding="utf-8")

    # 4) corpus/salvaged/entity_nodes.csv & refs/entity-registry.yaml
    nodes_path = ROOT / "corpus" / "salvaged" / "entity_nodes.csv"
    with nodes_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        node_cols = list(reader.fieldnames or [])
        existing_nodes = list(reader)

    v6_new_node_ids = {"N170", "N171", "N172", "N173"}
    base_nodes: list[dict[str, str]] = []
    for r in existing_nodes:
        nid = r["node_id"].strip()
        if nid in v6_new_node_ids:
            continue
        if nid == "N43":
            r = dict(r)
            r["code_or_ticker"] = "688808"
            r["listing_status"] = "A股上市(科创板:688808,2026-04-24上市;v6已纳入_frozen并同步P061)"
            r["in_frozen_universe"] = "true"
            r["point_ids"] = "P061"
            r["notes"] = (
                "科创板2026-04-24上市(688808),v6宇宙扩容已纳入_frozen.csv且points P061切为A股；第二家双侧实名IPO样本"
            )
        base_nodes.append(r)

    assert len(base_nodes) == 169, f"基线节点数应为169, 实际 {len(base_nodes)}"

    v6_entity_rows = [
        {
            "node_id": "N170",
            "canonical_name": "云南锗业",
            "aliases": "云南临沧鑫圆锗业股份有限公司|云南鑫耀半导体材料有限公司|云南鑫耀",
            "entity_role": "化合物半导体衬底母公司(锗/磷化铟/砷化镓)",
            "country": "中国",
            "code_or_ticker": "002428",
            "listing_status": "A股上市(深主板:002428,控股84.53%子公司云南鑫耀)",
            "is_intermediary_layer": "false",
            "in_frozen_universe": "true",
            "point_ids": "P202",
            "notes": "v6宇宙对称补录母公司;控股84.53%子公司云南鑫耀(P202,华为哈勃参股9.35%)2025年报披露全年生产磷化铟晶片10.01万片",
        },
        {
            "node_id": "N171",
            "canonical_name": "科瑞技术",
            "aliases": "深圳科瑞技术股份有限公司",
            "entity_role": "自动化封测设备商(共晶贴片EQ3/光耦合EQ4)",
            "country": "中国",
            "code_or_ticker": "002957",
            "listing_status": "A股上市(深主板:002957)",
            "is_intermediary_layer": "false",
            "in_frozen_universe": "true" if kerui_included else "false",
            "point_ids": "P275;P276",
            "notes": "11/19审阅N03设备层12家对称补录A股标的;2025年报p.15已核出光模块芯片共晶贴片设备(P275)与50nm精度光耦合设备(P276),客户匿名表述海外头部客户/海外光器件品牌企业(未具名Lumentum/Coherent)",
        },
        {
            "node_id": "N172",
            "canonical_name": "微见智能",
            "aliases": "微见智能封装技术（深圳）有限公司|微见智能封装技术(深圳)有限公司",
            "entity_role": "高精度固晶/共晶贴片设备商",
            "country": "中国",
            "code_or_ticker": "",
            "listing_status": "未上市私企(observation_list)",
            "is_intermediary_layer": "false",
            "in_frozen_universe": "false",
            "point_ids": "",
            "notes": "11/19审阅N03设备层对称观察主体(猎奇招股书释义列示);已入tree.yaml观察名单与daily_review待补一手锚",
        },
        {
            "node_id": "N173",
            "canonical_name": "镭神技术",
            "aliases": "镭神技术（深圳）有限公司|镭神技术(深圳)有限公司",
            "entity_role": "高精度光耦合封装设备商",
            "country": "中国",
            "code_or_ticker": "",
            "listing_status": "未上市私企(observation_list)",
            "is_intermediary_layer": "false",
            "in_frozen_universe": "false",
            "point_ids": "",
            "notes": "11/19审阅N03设备层对称观察主体(猎奇招股书引F&S列2024全球光耦合设备台数份额27%居首);已入tree.yaml观察名单与daily_review待补独立一手锚",
        },
    ]
    all_nodes = base_nodes + v6_entity_rows

    nbuf = io.StringIO()
    nwriter = csv.DictWriter(nbuf, fieldnames=node_cols, lineterminator="\n")
    nwriter.writeheader()
    nwriter.writerows(all_nodes)
    write_text_if_changed(nodes_path, nbuf.getvalue(), encoding="utf-8")

    # 5) 原地更新 refs/entity-registry.yaml 的 node_directory 段，严禁在 refs/ 下建任何临时文件
    reg_path = ROOT / "refs" / "entity-registry.yaml"
    reg_full_text = reg_path.read_text(encoding="utf-8")
    current_reg_doc = yaml.safe_load(reg_full_text)
    old_nd = current_reg_doc["node_directory"]

    split_re = re.compile(r"\n# ====================== 节点目录层.*?\n", flags=re.S)
    m_split = split_re.search(reg_full_text)
    assert m_split is not None, "未找到 refs/entity-registry.yaml 节点目录层分隔标记"
    base_reg_text = reg_full_text[: m_split.start()].rstrip() + "\n"
    marker = "\n# ====================== 节点目录层（Step 2 收编 + Step 3 v6 对称扩容同步） ======================\n"

    intermediary_map = {
        item["node_id"]: item["intermediary_note"]
        for item in old_nd.get("intermediary_entities", [])
    }

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
            "intermediary_note": intermediary_map.get(r["node_id"], ""),
            "in_frozen_universe": r["in_frozen_universe"] == "true",
            "point_ids": [p for p in re.split(r"[|;]", r["point_ids"]) if p],
        }
        for r in all_nodes
    ]

    status_corr = dict(old_nd.get("status_corrections_2026", {}))
    status_corr["联讯仪器"] = {
        "node_id": "N43",
        "code_or_ticker": "688808",
        "status": "科创板2026-04-24上市(v6已纳入corpus/_frozen.csv并落盘招股书/半年报,points.csv P061切为A股)",
    }
    status_corr["云南锗业(归并云南鑫耀)"] = {
        "node_id": "N170",
        "code_or_ticker": "002428",
        "status": "深主板002428纳入v6分母,participation.py建立控股84.53%子公司云南鑫耀(P202)别名归并",
    }
    status_corr["科瑞技术"] = {
        "node_id": "N171",
        "code_or_ticker": "002957",
        "status": "深主板002957纳入v6分母,2025年报p.15核出共晶贴片(P275)与50nm光耦合(P276)能力点,具名客户归属留DRQ0050待核",
    }

    new_nd_payload = {
        "node_directory": {
            "source_table": "corpus/salvaged/entity_nodes.csv",
            "updated_date": BUILD_DATE,
            "total_nodes": len(all_nodes),
            "in_frozen_universe_count": sum(
                1 for r in all_nodes if r["in_frozen_universe"] == "true"
            ),
            "with_points_count": sum(1 for r in all_nodes if r["point_ids"]),
            "intermediary_count": len(old_nd.get("intermediary_entities", [])),
            "evaporated_panorama_entities_count": len(
                old_nd.get("evaporated_panorama_entities", [])
            ),
            "status_corrections_2026": status_corr,
            "evaporated_panorama_entities": old_nd.get("evaporated_panorama_entities", []),
            "intermediary_entities": old_nd.get("intermediary_entities", []),
            "edge_only_supplemental_entities": old_nd.get(
                "edge_only_supplemental_entities", []
            ),
            "nodes": compact_nodes,
        }
    }

    dumped_nd = yaml.safe_dump(
        new_nd_payload,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    new_reg_text = base_reg_text + marker + dumped_nd
    verified_doc = yaml.safe_load(new_reg_text)
    assert isinstance(verified_doc, dict)
    assert len(verified_doc["node_directory"]["nodes"]) == 173
    write_text_if_changed(reg_path, new_reg_text, encoding="utf-8")

    refs_entries = sorted(os.listdir(ROOT / "refs"))
    assert len(refs_entries) == 8, f"refs/ 必须严格保持8个文件, 实际 {len(refs_entries)}: {refs_entries}"

    return {
        "frozen_unique_count": n_frozen,
        "frozen_total_rows": len(frozen_records),
        "v6_added_codes": [r[0] for r in v6_rows],
        "observation_added": ["微见智能", "镭神技术"],
        "entity_nodes_total": len(all_nodes),
        "entity_nodes_in_frozen": sum(1 for r in all_nodes if r["in_frozen_universe"] == "true"),
        "refs_file_count": len(refs_entries),
    }


def run_sync_daily_queue() -> dict[str, Any]:
    from corpus.daily_review import sync_daily_queue

    rc_build = sync_daily_queue.main(["--build"])
    assert rc_build == 0, "sync_daily_queue.py --build 失败"
    rc_check = sync_daily_queue.main(["--check"])
    assert rc_check == 0, "sync_daily_queue.py --check 失败"

    stats = json.loads(
        (ROOT / "corpus" / "daily_review" / "triage_stats.json").read_text(encoding="utf-8")
    )
    return stats


def verify_staleness_and_participation_in_memory(expected_universe: int) -> dict[str, Any]:
    import participation
    import scan

    # 校验 scan.staleness 分母缺席年报数 == 0
    frozen_codes = {r["代码"].strip() for r in scan.rows("corpus/_frozen.csv")}
    have_codes = {
        os.path.basename(d)
        for d in glob.glob(str(ROOT / "corpus" / "annual" / "*"))
        if os.path.isdir(d) and glob.glob(d + "/**/*.pdf", recursive=True)
    }
    missing_annual = sorted(frozen_codes - have_codes)
    assert missing_annual == [], f"宇宙内存在缺席年报公司: {missing_annual}"

    # 校验 tree.yaml universe.count 与 observation_names
    tree_doc = yaml.safe_load((ROOT / "tree.yaml").read_text(encoding="utf-8"))
    del scan.ERR[:]
    scan._check_tree_universe(tree_doc, len(frozen_codes))
    tree_errs = list(scan.ERR)
    del scan.ERR[:]
    assert tree_errs == [], f"_check_tree_universe 失败: {tree_errs}"

    obs_names = scan.observation_names()
    assert "微见智能" in obs_names and "镭神技术" in obs_names

    # 纯内存核验 participation.build_register() (不覆写 out/参与识别.*)
    reg_rows, reg_stats = participation.build_register()
    part_errs = participation.validate(reg_rows, reg_stats)
    assert part_errs == [], f"participation.validate 失败: {part_errs}"
    assert reg_stats["公司总数"] == expected_universe
    assert reg_stats.get("未覆盖", 0) == 0

    by_code = {r["代码"]: r for r in reg_rows}
    assert by_code["688808"]["结论"] == "已确认参与"
    assert by_code["002428"]["结论"] == "已确认参与"
    assert "M1" in by_code["002428"]["参与环节"]
    if "002957" in by_code:
        assert by_code["002957"]["结论"] == "已确认参与"
        assert "EQ3" in by_code["002957"]["参与环节"] and "EQ4" in by_code["002957"]["参与环节"]

    return {
        "missing_annual_reports_count": len(missing_annual),
        "participation_total_universe": reg_stats["公司总数"],
        "participation_confirmed_count": reg_stats.get("已确认参与", 0),
        "participation_pending_count": reg_stats.get("待确认", 0),
        "participation_uncovered_count": reg_stats.get("未覆盖", 0),
        "688808_conclusion": by_code["688808"]["结论"],
        "002428_conclusion": by_code["002428"]["结论"],
        "002957_conclusion": by_code["002957"]["结论"] if "002957" in by_code else "not_in_frozen",
    }


def main() -> int:
    symlink_info = expand_annual_top_symlink()
    annual_v6_info = populate_v6_annual_dirs()
    kerui_included = annual_v6_info["002957_included_in_frozen"]
    ledger_info = update_frozen_tree_participation_and_entities(kerui_included=kerui_included)
    daily_stats = run_sync_daily_queue()
    gate_info = verify_staleness_and_participation_in_memory(
        expected_universe=ledger_info["frozen_unique_count"]
    )

    tracked_outputs = [
        "corpus/_frozen.csv",
        "tree.yaml",
        "participation.py",
        "corpus/salvaged/entity_nodes.csv",
        "refs/entity-registry.yaml",
        "corpus/daily_review/sync_daily_queue.py",
        "corpus/daily_review/review_queue.csv",
        "corpus/daily_review/triage_stats.json",
        "corpus/daily_review/README.md",
        *annual_v6_info["688808_files"],
        *annual_v6_info["002428_pdfs"],
        *[f"{p}.txt" for p in annual_v6_info["002428_pdfs"]],
        *annual_v6_info["002957_pdfs"],
        *[f"{p}.txt" for p in annual_v6_info["002957_pdfs"]],
    ]
    file_hashes = {rel: sha256_file(ROOT / rel) for rel in sorted(set(tracked_outputs))}

    summary = {
        "worker": "carbon-universe-queue",
        "workpack_id": "OPTICAL-STEP3-DAILY-AND-V6-20261121",
        "generated_date": BUILD_DATE,
        "annual_symlink_expansion": symlink_info,
        "v6_annual_corpus": annual_v6_info,
        "v6_universe_and_entities": ledger_info,
        "in_memory_gate_checks": gate_info,
        "daily_review_triage": daily_stats,
        "output_sha256": file_hashes,
    }
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    for bad in FORBIDDEN_PHRASES:
        assert bad not in summary_text, f"summary 出现禁用词 {bad!r}"

    write_text_if_changed(OUT_SUMMARY, summary_text, encoding="utf-8")
    print(
        f"build_v6_and_daily_queue OK | universe={ledger_info['frozen_unique_count']} | "
        f"missing_annual={gate_info['missing_annual_reports_count']} | "
        f"entity_nodes={ledger_info['entity_nodes_total']} | "
        f"refs={ledger_info['refs_file_count']} | "
        f"queue={daily_stats['persistent_queue']['total_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
