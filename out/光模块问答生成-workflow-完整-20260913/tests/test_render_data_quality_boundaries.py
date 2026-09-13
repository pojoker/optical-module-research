# -*- coding: utf-8 -*-
"""WP-C 数据质量边界测试：出货观察非比较面、非URL锚不生成假链接、关系边措辞不越级。

夹具自含（不读仓库 canonical 数据），通过覆写 render.ROOT 指向临时夹具目录后调用 build()。
仅断言读者可见边界，不新增任何 schema / relation type / product scope。
"""
import csv, os, filecmp, importlib.util

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_RENDER_PATH = os.path.join(os.path.dirname(_HERE), 'render.py')


def _load_render():
    spec = importlib.util.spec_from_file_location('render_wp_c', _RENDER_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TREE_YAML = """universe:
  count: 5
  frozen_date: '2026-01-01'
tree:
- id: root
  名称: 根
  children:
  - cell_id: MOD1
    名称: 光模块
    路线: 共用
  - cell_id: D8
    名称: 光芯片
    路线: 共用
flows:
- from: D8
  to: [MOD1]
"""

POINTS_HEADER = ['point_id', 'cell_id', '公司', '状态', '上市标签', '命中引语', '锚点URL', '检索日期']
POINTS_ROWS = [
    ['P001', 'MOD1', '甲公司', '生产中', 'A股', '披露引语A', 'https://example.com/10k.pdf', '2026-01-01'],
    ['P002', 'D8', '乙公司', '生产中', 'A股', '披露引语B', '有锚；发行人自述（X 10-K）', '2026-01-01'],
    ['P003', 'D8', '丙公司', '在建', 'A股', '披露引语C', '同上', '2026-01-01'],
    ['P004', 'D8', '丁公司', '生产中', 'A股', '披露引语D', '[2025年年度报告](https://example.com/md.pdf)', '2026-01-01'],
    ['P005', 'D8', '戊公司', '生产中', 'A股', '披露引语E', 'https://example.com/report.pdf；年度报告第10页', '2026-01-01'],
]

EDGES_HEADER = ['edge_id', '供方', '需方', '供方point_id', '需方point_id', '数值类型', '数值', '单位',
                '占比或金额原文', '财年', '边等级', '证据文件', '锚点', '验证状态', '备注']
EDGES_ROWS = [
    ['E001', '丁公司', '甲公司', 'P001', 'P004', '占比', '30', '', '30%', 'FY2025', '实边',
     'X 10-K', 'https://example.com/edge.pdf', '会话端抽检逐字命中', ''],
    ['E002', 'L公司', 'A客户', 'EXT', 'EXT', '占比', '20', '', '20%', 'FY2025', '实边',
     'Y 10-K', 'https://example.com/edge2.pdf', '会话端抽检逐字命中', '3D传感/消费端非光通信'],
]

SHIPS_HEADER = ['row_id', '公司', 'cell_id', '期间', '出货量', '单位', '推导式', '证据等级', '情景标记',
                '校准实际值', '误差', '校准日期', '检索日期', '收入锚']
SHIPS_ROWS = [
    ['SE001', '甲公司', 'MOD1', '2025年度', '2109', '万只', '年报产销表直接披露(光通信收发模块)', 'B', 'base', '', '', '', '2026-01-01', 'https://example.com/revenue-a.pdf'],
    ['SE002', '乙公司', 'MOD1', '2025年度', '1603', '万只', '年报产销表直接披露(光互联产品)', 'B', 'base', '', '', '', '2026-01-01', '年报收入表第8页'],
    ['SE003', '丙公司', 'D系聚合', '2025年度', '500', '万只', '跨层聚合披露', 'B', 'base', '', '', '', '2026-01-01', ''],
    ['SE004', '丁公司', 'D8', '2025年度', '120', '台', '设备出货台数', 'B', 'base', '', '', '', '2026-01-01', ''],
    ['SE005', '戊公司', 'D8', '2026H1基准', '99', '万件', '情景口径披露', 'B', 'scenario-FCC', '', '', '', '2026-01-01', ''],
]


def _write_csv(path, header, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


@pytest.fixture
def env(tmp_path):
    m = _load_render()
    (tmp_path / 'tree.yaml').write_text(TREE_YAML, encoding='utf-8')
    _write_csv(tmp_path / 'points.csv', POINTS_HEADER, POINTS_ROWS)
    _write_csv(tmp_path / 'edges.csv', EDGES_HEADER, EDGES_ROWS)
    _write_csv(tmp_path / 'shipments.csv', SHIPS_HEADER, SHIPS_ROWS)
    m.ROOT = str(tmp_path)
    out = tmp_path / 'out'
    m.build(str(out))
    with open(out / '全景.md', encoding='utf-8') as f:
        md = f.read()
    return md, out


def test_http_anchor_still_renders_as_link(env):
    md, _ = env
    assert '[锚](https://example.com/10k.pdf)' in md


def test_non_http_anchor_is_explanatory_text_not_fake_link(env):
    md, _ = env
    # 占位“有锚”不得被渲染成超链接
    assert '[锚](有锚' not in md
    assert '非URL锚（说明文本，非超链接）：有锚；发行人自述（X 10-K）' in md
    # markdown 内嵌链接形式也按说明文本渲染，且括号被转义、不重新解释成可用链接
    assert '\\[2025年年度报告\\](https://example.com/md.pdf)' in md
    assert '[锚](https://example.com/report.pdf；年度报告第10页)' not in md
    assert '非URL锚（说明文本，非超链接）：https://example.com/report.pdf；年度报告第10页' in md


def test_tongshang_anchor_not_an_independent_anchor(env):
    md, _ = env
    assert '[锚](同上' not in md
    assert '锚点为“同上”——沿用上一行锚点，**非独立锚点**，不可独立核验' in md


def test_bom_flow_is_relationship_observation_not_supply_claim(env):
    md, _ = env
    # 不再出现“已证N边”这类供货宣称
    assert '已证' not in md
    assert '关系观察' in md
    assert '非默认光模块供货' in md
    assert '骨架外关系观察' in md


def test_shipment_section_expresses_unit_and_business_scope(env):
    md, _ = env
    # 按单位分组 + 业务范围(cell)列
    assert '### 单位：万只（3 行）' in md
    assert '### 单位：台（1 行）' in md
    assert '### 单位：万件（1 行）' in md
    assert '| SE001 | 甲公司 | MOD1 光模块 | 年报产销表直接披露(光通信收发模块) | [锚](https://example.com/revenue-a.pdf) | 2025年度 | 2109 万只 | B | base |' in md
    assert '| SE002 | 乙公司 | MOD1 光模块 | 年报产销表直接披露(光互联产品) | 非URL锚（说明文本，非超链接）：年报收入表第8页 |' in md
    # 聚合行与非 base 情景行有显式标记
    assert '⚠跨层聚合' in md
    assert '⚠非base' in md


def test_shipment_section_forbids_sum_rank_share(env):
    md, _ = env
    assert '明确禁止' in md
    assert '求和、排名或份额推导' in md
    # 不产生任何派生数值：2109+1603=3712 等任何合计不得出现
    assert '3712' not in md
    assert '| 合计' not in md
    assert '| 小计' not in md


def test_build_is_deterministic(tmp_path):
    m = _load_render()
    (tmp_path / 'tree.yaml').write_text(TREE_YAML, encoding='utf-8')
    _write_csv(tmp_path / 'points.csv', POINTS_HEADER, POINTS_ROWS)
    _write_csv(tmp_path / 'edges.csv', EDGES_HEADER, EDGES_ROWS)
    _write_csv(tmp_path / 'shipments.csv', SHIPS_HEADER, SHIPS_ROWS)
    m.ROOT = str(tmp_path)
    left, right = tmp_path / 'left', tmp_path / 'right'
    m.build(str(left))
    m.build(str(right))
    for f in ('全景.md', '全景.html', '知识库.md', '知识库.html', '问题队列.md'):
        assert (left / f).exists() and (right / f).exists(), f
        assert filecmp.cmp(left / f, right / f, shallow=False), f
