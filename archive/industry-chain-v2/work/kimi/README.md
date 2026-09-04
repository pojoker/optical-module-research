# WP-KIMI：读者输出渲染器

## 文件

- `render_report.py` — 渲染器主程序（Python 3 标准库）。
- `report_template.html` — 自包含 HTML 模板，零外链。
- `tests/` — 最小自测 fixture 与测试脚本（非 canonical 数据）。

## 用法

```bash
python work/kimi/render_report.py data report.html
```

- `data`：包含七份 canonical CSV 的目录。
- `report.html`：输出路径（默认 `report.html`）。
- `--template`：可指定自定义模板（默认读取同目录 `report_template.html`）。

输入缺失任意一份 CSV 时，脚本会打印明确错误并返回非零退出码。

## 输出特性

1. 首屏即执行摘要，回答：产业组成、三路线差异、关键节点、P0 缺口。
2. 结构 / 能力 / 交易 / 证据 / 缺口 五层标签切换，不混层。
3. unknown 节点高亮；首屏显示P0总数与前10项，完整P0队列保留在缺口页。
4. 零外链依赖（CSS、JS 全部内联）。
5. 相同输入产生相同输出（不写入生成时间戳，按 ID 排序）。
6. 页头记录输入七份 CSV 的 SHA-256 哈希。

## 输入 CSV 清单（按 schema/CONTRACT.md）

- `structure_nodes.csv`
- `structure_edges.csv`
- `organizations.csv`
- `capabilities.csv`
- `trade_observations.csv`
- `evidence.csv`
- `gaps.csv`

## 自测

```bash
cd work/kimi
python tests/test_render.py
```

该脚本会：
- 用 `tests/fixtures/` 下的最小数据运行渲染器；
- 校验输出 HTML 存在且包含首屏关键要素（产业组成、三路线、关键节点、P0 缺口）；
- 校验结构 / 能力 / 交易 / 证据 / 缺口五个标签片段均存在；
- 校验确定性和缺失输入报错。

## 当前假设与未解决问题

1. **数据完整性**：渲染器仅做引用存在性检查，不执行 schema/CONTRACT.md 的完整校验；非法输入可能导致渲染异常或引用显示为缺失。完整校验应由 `work/hy3/validate_model.py` 在集成阶段执行。
2. **路线差异算法**：当前按 `implements` / `requires` 两层展开部件/材料；若后续 canonical 数据增加更多层级，需同步调整摘要生成逻辑。
3. **匿名端点**：交易层优先展示 `supplier_org_id` / `customer_org_id`，若 `anonymous_endpoint` 存在则覆盖，确保不伪造 org_id。
4. **1.6T / LPO / CPO**：SPEC 明确列为后续路线，当前渲染器不特殊处理，仅作为普通 `product_route` 节点渲染。
5. **字段编码**：所有 CSV 均按 UTF-8 读取，未做 BOM 处理；若输入文件带 BOM，表头可能错位。
