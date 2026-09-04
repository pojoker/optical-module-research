# 产业链 v2 开发工包

所有工包以 `SPEC.md` 与 `schema/CONTRACT.md` 为唯一契约。代理不得修改这两份文件。

## WP-GROK：产品路线与BOM骨架

所有者：Grok 4.5 High

写入范围：

- `work/grok/structure_nodes.csv`
- `work/grok/structure_edges.csv`
- `work/grok/notes.md`

任务：

1. 为800G DR8、800G 2×FR4、400ZR建立应用→路线→功能→部件/材料骨架；
2. 严格区分架构、功能、部件、材料；
3. 标出共同节点与路线特有节点；
4. 重要性仅给初判，瓶颈一律区分 verified/hypothesis/unknown；
5. 不映射公司、不写供货关系。

验收：

- 三路线可达；
- 无工序混入 component；
- 无公司节点；
- 所有 `bottleneck_candidate` 有依据状态；
- notes 列出争议分类与待核技术问题。

## WP-CLAUDE：制造工序与设备轴

所有者：Claude

写入范围：

- `work/claude/process_nodes.csv`
- `work/claude/process_edges.csv`
- `work/claude/notes.md`

任务：

1. 建立光芯片/硅光或III-V相关工序、光组件/封装、模块组装与测试流程；
2. 将设备类别作为 process 的 `enabled_by` 节点；
3. 标注路线共用与特有工序；
4. 不把设备商公司名写成设备类别，不写商业关系。

验收：

- 工序有先后关系；
- 芯片制造与模块组装不混为一条无分支线；
- `equipment_category` 与 `process` 类型正确；
- notes 明示流程简化与路线差异。

## WP-HY3：校验器、重要性与缺口状态机

所有者：CodeBuddy `--model hy3`

写入范围：

- `work/hy3/validate_model.py`
- `work/hy3/generate_gaps.py`
- `work/hy3/test_validate_model.py`
- `work/hy3/README.md`

任务：

1. 只用Python标准库实现CSV validator；
2. 校验ID、字段、合法类型/关系、引用、evidence用途、重要性纪律与状态机；
3. 从结构节点、能力和交易覆盖生成缺口；
4. 测试至少含一组正例和六组反例。

验收：

- 非法关系、孤儿、重复ID、混层、瓶颈无依据、非法状态转换、缺口分母消失均能拦截；
- 失败返回非零；
- 不写死光模块公司名；
- 不修改其他工包。

## WP-KIMI：读者输出

所有者：Kimi

写入范围：

- `work/kimi/render_report.py`
- `work/kimi/report_template.html`
- `work/kimi/README.md`

任务：

1. 输入 canonical CSV，输出自包含 HTML；
2. 首屏回答产业组成、三路线差异、关键节点与P0缺口；
3. 结构图、公司能力、供货关系分层切换，不混成一张图；
4. 显示 evidence use 与置信状态；
5. 无外链依赖，确定性输出。

验收：

- 10分钟读者任务对应明确；
- P0缺口和 unknown 不被隐藏；
- capability 不渲染为 trade；
- 零外链；
- 输入缺失时明确报错。

## Codex：总设计、集成与审核

Codex负责：

- 契约与范围冻结；
- 四工包独立验收；
- canonical `data/` 集成；
- 最小光模块样板数据；
- 端到端命令与终验报告；
- 最终提交。
