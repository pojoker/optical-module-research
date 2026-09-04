#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-tests for WP-KIMI render_report.py.

Runs the renderer against the local fixtures and asserts:
- output is produced and non-empty
- the first-screen elements are present
- all five layers are present
- output is deterministic (same bytes for same input)
- missing input files are clearly rejected
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
RENDERER = os.path.join(ROOT, "render_report.py")
TEMPLATE = os.path.join(ROOT, "report_template.html")


def run_renderer(data_dir, output, extra_args=None):
    cmd = [sys.executable, RENDERER, data_dir, output, "--template", TEMPLATE]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


def test_basic_render():
    out = os.path.join(tempfile.gettempdir(), "kimi_test_report.html")
    result = run_renderer(FIXTURES, out)
    assert result.returncode == 0, f"renderer failed: {result.stderr}"
    assert os.path.exists(out), "output file not created"
    with open(out, "r", encoding="utf-8") as fh:
        html = fh.read()
    assert len(html) > 0, "output is empty"

    # first-screen contents
    assert "产业组成" in html, "missing 产业组成"
    assert "三路线差异" in html, "missing 三路线差异"
    assert "关键节点" in html, "missing 关键节点"
    assert "P0 缺口" in html, "missing P0 缺口"

    # layers
    assert "结构层" in html, "missing 结构层"
    assert "能力层" in html, "missing 能力层"
    assert "交易层" in html, "missing 交易层"
    assert "证据层" in html, "missing 证据层"
    assert "研究缺口" in html, "missing 研究缺口"

    # P0 gap should be visible
    assert "GAP-001" in html, "P0 gap not rendered"
    assert "PIN supplier not mapped" in html, "P0 gap reason not rendered"

    # unknown visibility: an unknown confidence node should appear
    assert "unknown" in html, "unknown confidence not rendered"

    # no external links
    assert 'href="http' not in html, "external link found in output"
    assert 'src="http' not in html, "external script src found in output"

    # input hash
    assert "输入哈希" in html, "input hash not shown"
    print("test_basic_render: PASS")
    return out


def test_determinism():
    out1 = os.path.join(tempfile.gettempdir(), "kimi_test_det1.html")
    out2 = os.path.join(tempfile.gettempdir(), "kimi_test_det2.html")
    r1 = run_renderer(FIXTURES, out1)
    r2 = run_renderer(FIXTURES, out2)
    assert r1.returncode == 0 and r2.returncode == 0, "renderer failed in determinism test"
    with open(out1, "rb") as f1, open(out2, "rb") as f2:
        assert f1.read() == f2.read(), "output is not deterministic"
    print("test_determinism: PASS")


def test_missing_input():
    empty_dir = os.path.join(tempfile.gettempdir(), "kimi_test_empty")
    if os.path.exists(empty_dir):
        shutil.rmtree(empty_dir)
    os.makedirs(empty_dir)
    out = os.path.join(tempfile.gettempdir(), "kimi_test_missing.html")
    result = run_renderer(empty_dir, out)
    assert result.returncode != 0, "expected non-zero exit for missing input"
    assert "缺少" in result.stderr or "missing" in result.stderr.lower(), "missing input error not clear"
    print("test_missing_input: PASS")


def main():
    test_basic_render()
    test_determinism()
    test_missing_input()
    print("\nAll tests passed.")


if __name__ == "__main__":
    main()
