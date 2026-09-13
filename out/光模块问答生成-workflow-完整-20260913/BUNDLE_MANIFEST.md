# 光模块问答生成 Workflow 完整包

快照日期：2026-09-13

## 目的

这是“原始 GPT 问答 → 研究/审核 → 网页源文件 → HTML 构建”的可复现交接包。
目录结构保持仓库相对路径，解压后可从包根目录阅读文档、检查数据并运行构建脚本。

## 推荐阅读顺序

1. `WORKFLOW.md`：真实链路、证据边界和当前缺口；
2. `AGENTS.md`、`docs/control/PROJECT_CHARTER.md`、`docs/control/ACTIVE_WORKPACK.yaml`：执行边界；
3. `docs/source-conversations/README.md` 和三份 Markdown/raw JSON：原始研究起点；
4. `docs/reviews/`：研究、因果链和审阅记录；优先看 2026-09-09 的光模块相关文件；
5. `tree.yaml`、`knowledge.yaml`、`research_questions.yaml` 及其他根级账本：骨架、知识和产品投影数据；
6. `site/optical-qa/`、`site/optical-module/`：网页源文件；
7. `tools/site/build_optical_module_site.py`、`tests/site/`：构建和页面校验；
8. `out/光模块知识体系/`：当前已生成的 HTML 快照。

## 纳入范围

- 三段 GPT 原始对话的可读版 Markdown 和完整 raw JSON；
- 完整 `docs/` 控制、研究、审核和来源记录；
- `tree.yaml`、`knowledge.yaml`、问题树和根级研究账本；
- `contracts/`、`refs/`；
- `site/` 网页源文件；
- `tools/`、`tests/` 和根级 Python 构建/校验脚本；
- 当前模块化网页、连续问答页以及 `out/` 根级生成投影；
- `FILE-LIST.txt` 和 `SHA256SUMS.txt`，用于核对包内文件是否完整、是否被改动。

## 有意排除范围

以下内容不属于本问答网页生成链，且会把独立日更或历史状态混入当前 workflow，因此没有纳入：

- `.git/`、Python 缓存和测试缓存；
- `archive/` 旧结构冷冻区；
- `corpus/`、`annual_reports/`、`calls/`、`domestic_daily/`、`daily_intelligence/` 等独立日更/采集链；
- 私有配置、密钥、keychain 和旧 agent 全量轨迹；
- `out/` 中的旧代码包和旧网页包，只保留当前生成结果。

## 当前边界

包内 HTML 是当前可生成、可审阅的快照，不等于已完成正式发布。构建器保持
`canonical_write: false`；研究稿中的候选结论不会因构建网页自动晋升为 canonical。

## 重建命令

从包根目录运行：

```bash
/Users/jowang/miniconda3/bin/python3 tools/site/build_optical_module_site.py
/Users/jowang/miniconda3/bin/python3 tests/site/test_optical_module_reader.py
```

`render.py`、`scan.py`、`participation.py` 等根级脚本属于更大的研究账本层；其依赖和边界见 `README.md` 与 `AGENTS.md`。
