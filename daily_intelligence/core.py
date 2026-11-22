from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"missing: {path}"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON: {path}: {type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return None, f"invalid JSON object: {path}"
    return value, None


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if not path.is_file():
        return None, f"missing: {path}"
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeError) as exc:
        return None, f"unreadable: {path}: {type(exc).__name__}: {exc}"


def _count(value: Any) -> int:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with source.open("rb") as source_handle, tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as destination_handle:
            temporary = destination_handle.name
            while chunk := source_handle.read(1024 * 1024):
                destination_handle.write(chunk)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_date(run_date: str) -> None:
    try:
        parsed = date.fromisoformat(run_date)
    except ValueError as exc:
        raise ValueError(f"run_date must be YYYY-MM-DD, got {run_date!r}") from exc
    if parsed.isoformat() != run_date:
        raise ValueError(f"run_date must be YYYY-MM-DD, got {run_date!r}")


def _require_disjoint_output(output_root: Path, *input_roots: Path) -> None:
    for input_root in input_roots:
        if output_root == input_root or output_root.is_relative_to(input_root) or input_root.is_relative_to(output_root):
            raise ValueError(
                "output_root must be disjoint from domestic and overseas state roots: "
                f"output={output_root}, input={input_root}"
            )


def _int_field(mapping: dict[str, Any] | None, key: str) -> int | None:
    if not isinstance(mapping, dict) or key not in mapping:
        return None
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


RUN_STATUSES = ("running", "complete", "partial", "failed")
_COLLECTION_SEVERITY = {"complete": 0, "unknown": 1, "partial": 2, "failed": 3}


def _worse_collection(left: str, right: str) -> str:
    return left if _COLLECTION_SEVERITY[left] >= _COLLECTION_SEVERITY[right] else right


NONFAILURE_FAILURE_TYPES = {"no_relevant_content"}
COVERAGE_FIELDS = (
    "endpoint_count",
    "endpoint_failed",
    "configured_entity_count",
    "monitored_entity_count",
    "missing_endpoint_count",
)


def _domestic_collection_state(
    manifest: dict[str, Any] | None,
    run_status: dict[str, Any] | None,
    report_present: bool,
) -> dict[str, Any]:
    manifest_status = manifest.get("run_status") if manifest else None
    if manifest_status not in RUN_STATUSES or manifest_status == "running":
        manifest_status = None
    doc_status = run_status.get("status") if isinstance(run_status, dict) else None
    if doc_status not in RUN_STATUSES:
        doc_status = None
    doc_errors = 0
    if isinstance(run_status, dict):
        raw_errors = run_status.get("errors")
        if isinstance(raw_errors, (list, tuple)):
            doc_errors = len(raw_errors)
        elif isinstance(raw_errors, int) and not isinstance(raw_errors, bool):
            doc_errors = raw_errors
    manifest_log_failures = 0
    if isinstance(manifest, dict) and isinstance(manifest.get("logs"), list):
        manifest_log_failures = sum(
            1 for entry in manifest["logs"] if isinstance(entry, str) and "失败" in entry
        )
    processed = _int_field(run_status, "processed")
    total = _int_field(run_status, "total")
    updated_at = run_status.get("updated_at") if isinstance(run_status, dict) else None
    if not isinstance(updated_at, str):
        updated_at = None
    notes: list[str] = []

    if doc_status == "running":
        # 遗留/当前 running 只证明未完成，不能被 manifest 的 complete 声明覆盖。
        status = "unknown" if report_present else "partial"
        if not report_present:
            notes.append(
                "国内采集未完成：run-status=running；遗留 running 只证明未完成，"
                "不能推断进程仍在运行或已被终止"
            )
        elif manifest_status == "complete":
            notes.append(
                "manifest 声称 complete 但当前 run-status=running："
                "running 只证明未完成，完成度存疑"
            )
        else:
            notes.append("当日报告已存在但 run-status 仍为 running：完成度无法确认")
    else:
        claims = [s for s in (manifest_status, doc_status) if s is not None]
        if not claims:
            status = "unknown"
            notes.append(
                "缺少当日国内日报且无采集完成信息，不推断采集成功"
                if not report_present
                else "国内输入未提供 run_status 完成字段，不推断采集成功"
            )
        else:
            status = max(claims, key=lambda s: _COLLECTION_SEVERITY[s])
            if len(set(claims)) > 1:
                notes.append(
                    f"manifest run_status={manifest_status} 与 run-status status={doc_status} "
                    "冲突，按更保守结果记录"
                )
            if not report_present:
                if status == "complete":
                    status = "unknown"
                    notes.append("存在 complete 声明但当日报告缺失，完成度存疑")
                elif status == "unknown":
                    notes.append("缺少当日国内日报且无采集完成信息，不推断采集成功")
                else:
                    notes.append("当日国内日报缺失，按 run 状态记录为未完成")

    if doc_errors:
        if status == "complete":
            status = "partial"
        notes.append(f"run-status 记录 {doc_errors} 条错误摘要，完成度存疑")
    if manifest_log_failures:
        if status == "complete":
            status = "partial"
        notes.append(f"manifest logs 记录 {manifest_log_failures} 条失败条目，完成度存疑")

    progress = None
    if processed is not None or total is not None:
        progress = f"{processed if processed is not None else '?'}/{total if total is not None else '?'}"
    return {
        "status": status,
        "manifest_run_status": manifest_status,
        "run_status_file": doc_status,
        "processed": processed,
        "total": total,
        "updated_at": updated_at,
        "progress": progress,
        "notes": notes,
    }


def _overseas_collection_state(summary: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {
        "status": "unknown",
        "endpoint_count": None,
        "endpoint_failed": None,
        "endpoint_succeeded": None,
        "configured_entity_count": None,
        "monitored_entity_count": None,
        "missing_endpoint_count": None,
        "article_fetch_failure": None,
        "invalid_item": None,
        "notes": [],
    }
    if not summary:
        state["notes"] = ["缺少海外 run-summary，采集健康度未知，不推断采集成功"]
        return state
    state["endpoint_count"] = _int_field(summary, "endpoint_count")
    state["endpoint_failed"] = _int_field(summary, "endpoint_failed")
    state["endpoint_succeeded"] = _int_field(summary, "endpoint_succeeded")
    state["configured_entity_count"] = _int_field(summary, "configured_entity_count")
    state["monitored_entity_count"] = _int_field(summary, "monitored_entity_count")
    state["missing_endpoint_count"] = _int_field(summary, "missing_endpoint_count")
    if "failure_types" not in summary:
        failure_types: dict[str, Any] = {}
        failure_types_unknown = True
    elif isinstance(summary["failure_types"], dict):
        failure_types = summary["failure_types"]
        failure_types_unknown = False
    else:
        failure_types = {}
        failure_types_unknown = True
    state["article_fetch_failure"] = _int_field(summary, "article_fetch_failure")
    if state["article_fetch_failure"] is None:
        state["article_fetch_failure"] = _int_field(failure_types, "article_fetch_failure")
    state["invalid_item"] = _int_field(failure_types, "invalid_item")

    notes: list[str] = []
    degraded = False
    unknown = False
    if state["endpoint_failed"] is None:
        unknown = True
        notes.append("run-summary 缺少 endpoint_failed，不能默认端点全部成功")
    elif state["endpoint_failed"] > 0:
        degraded = True
    if state["endpoint_succeeded"] is None:
        notes.append("endpoint_succeeded 未提供：端点成功数为 UNKNOWN（已配置不等于成功）")
    for field in COVERAGE_FIELDS:
        if _int_field(summary, field) is None:
            unknown = True
            notes.append(f"run-summary 缺少 {field}，采集覆盖不完整程度未知")
    if state["missing_endpoint_count"] and state["missing_endpoint_count"] > 0:
        degraded = True
    if (
        state["configured_entity_count"] is not None
        and state["monitored_entity_count"] is not None
        and state["configured_entity_count"] < state["monitored_entity_count"]
    ):
        degraded = True
        notes.append(
            f"仅 {state['configured_entity_count']}/{state['monitored_entity_count']} 个监控实体配置了端点；"
            "这是配置覆盖，不代表采集成功或研究覆盖"
        )
    if state["article_fetch_failure"]:
        degraded = True
    if state["invalid_item"]:
        degraded = True
    for failure_type, count in failure_types.items():
        if failure_type in NONFAILURE_FAILURE_TYPES:
            continue
        if _int_field(failure_types, str(failure_type)):
            degraded = True
            notes.append(f"failure_types 记录 {failure_type}×{count}，采集存在未归类的获取失败")
    if failure_types_unknown:
        unknown = True
        notes.append("run-summary 缺少 failure_types 或格式异常，失败诊断未知，不推断无失败")
    state["status"] = "partial" if degraded else ("unknown" if unknown else "complete")
    state["notes"] = notes
    return state


def _load_domestic(root: Path, run_date: str) -> dict[str, Any]:
    report_path = root / "daily" / f"{run_date}.txt"
    manifest_path = root / "manifest.json"
    run_status_path = root / "run-status.json"
    report, report_error = _read_text(report_path)
    manifest, manifest_error = _read_json(manifest_path)
    run_status, run_status_error = _read_json(run_status_path)
    errors = [error for error in (report_error, manifest_error) if error]
    if run_status_error and not run_status_error.startswith("missing:"):
        errors.append(f"run-status.json invalid: {run_status_error}")
        run_status = None
    if run_status is not None and run_status.get("run_date") != run_date:
        errors.append(
            f"run-status date mismatch: expected {run_date}, got {run_status.get('run_date')!r}"
        )
        run_status = None
    if manifest is not None and manifest.get("date") != run_date:
        errors.append(
            f"manifest date mismatch: expected {run_date}, got {manifest.get('date')!r}"
        )
        manifest = None
    collection = _domestic_collection_state(manifest, run_status, report is not None)

    digest = manifest.get("digest", {}) if manifest else {}
    if not isinstance(digest, dict):
        digest = {}
    summary = {
        "watched_codes": _count(manifest.get("watched_codes")) if manifest else 0,
        "ir_new": _count(digest.get("ir_new")),
        "qa_new": _count(digest.get("qa_new")),
        "announcements": _count(digest.get("ann")),
        "queue_added": _count(digest.get("q_delta_new")),
        "queue_removed": _count(digest.get("q_delta_gone")),
        "restart_hits": _count(manifest.get("restart_hits")) if manifest else 0,
        "outlier_hits": _count(manifest.get("outlier_hits")) if manifest else 0,
        "log_entries": _count(manifest.get("logs")) if manifest else 0,
    }
    summary["gate_review_suggested"] = any(
        summary[key]
        for key in (
            "ir_new",
            "qa_new",
            "announcements",
            "queue_added",
            "restart_hits",
            "outlier_hits",
        )
    )
    return {
        "available": report is not None,
        "report": report,
        "report_path": str(report_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "run_status_path": str(run_status_path.resolve()),
        "collection": collection,
        "summary": summary,
        "errors": errors,
    }


def _load_overseas(root: Path, run_date: str) -> dict[str, Any]:
    report_path = root / "daily" / f"{run_date}.txt"
    summary_path = root / "staging" / run_date / "run-summary.json"
    candidates_path = root / "staging" / run_date / "candidates.json"
    report, report_error = _read_text(report_path)
    summary, summary_error = _read_json(summary_path)
    candidates, candidates_error = _read_json(candidates_path)
    errors = [error for error in (report_error, summary_error, candidates_error) if error]
    if summary is not None and summary.get("run_date") != run_date:
        errors.append(
            f"run-summary date mismatch: expected {run_date}, got {summary.get('run_date')!r}"
        )
        summary = None
    collection = _overseas_collection_state(summary or {})
    return {
        "available": report is not None,
        "report": report,
        "report_path": str(report_path.resolve()),
        "summary_path": str(summary_path.resolve()),
        "candidates_path": str(candidates_path.resolve()),
        "collection": collection,
        "summary": summary or {},
        "candidates": candidates or {},
        "errors": errors,
    }


EVENT_CATEGORY_LABELS = {
    "product_stage": "产品阶段",
    "capacity_constraint": "产能与卡点",
    "commercial_adoption": "商业采用",
    "capital_relationship": "资本与关系",
    "policy_access": "政策与准入",
}

LIFECYCLE_STAGE_LABELS = {
    "announced": "已宣布",
    "demonstrated": "完成演示",
    "sampling": "送样",
    "qualifying": "验证中",
    "first_shipment": "首次出货",
    "volume_order": "批量订单",
    "scaled": "规模化",
}


def _overseas_event_line(event: dict[str, Any]) -> str:
    category = EVENT_CATEGORY_LABELS.get(str(event.get("event_category")), "其他事件")
    stage = LIFECYCLE_STAGE_LABELS.get(
        str(event.get("lifecycle_stage")), str(event.get("lifecycle_stage") or "阶段未知")
    )
    suggestion = (
        "建议交叉确认"
        if event.get("suggested_event_status") == "corroborated"
        else "待人工核验"
    )
    return (
        f"- {event.get('primary_subject_id') or '主体未解析'} | {category}·{stage} | "
        f"{event.get('occurred_start') or '时间未知'} | 已声称；{suggestion}"
    )


def _fmt_count(value: int | None) -> str:
    return "UNKNOWN" if value is None else str(value)


def _domestic_collection_lines(collection: dict[str, Any]) -> list[str]:
    details: list[str] = []
    if collection.get("run_status_file"):
        details.append(f"run-status={collection['run_status_file']}")
    if collection.get("manifest_run_status"):
        details.append(f"manifest run_status={collection['manifest_run_status']}")
    if collection.get("progress"):
        details.append(f"已处理 {collection['progress']}")
    if collection.get("updated_at"):
        details.append(f"更新于 {collection['updated_at']}")
    line = f"- 国内采集状态：{collection['status']}"
    if details:
        line += f"（{'，'.join(details)}）"
    return [line] + [f"- {note}" for note in collection["notes"]]


def _render_markdown(
    run_date: str,
    domestic: dict[str, Any],
    overseas: dict[str, Any],
    assembly_status: str,
) -> str:
    domestic_collection = domestic["collection"]
    overseas_collection = overseas["collection"]
    collection_status = _worse_collection(
        domestic_collection["status"], overseas_collection["status"]
    )
    overseas_summary = overseas["summary"]
    if domestic["report"] is None:
        lines = [f"# 日报 {run_date}", "", f"> 国内日报未生成：`{domestic['report_path']}`"]
    else:
        lines = [domestic["report"].rstrip()]

    if not overseas["available"] or not overseas["summary"] or not overseas["candidates"]:
        lines.extend(
            ["", "## 海外事件增量 未生成", "- 缺少海外日报或候选清单，请检查海外日更任务。"]
        )
    else:
        events = overseas["candidates"].get("event_candidates", [])
        if not isinstance(events, list):
            events = []
        lines.extend(["", f"## 海外事件增量 {len(events)} 条"])
        fetch_mode = (
            overseas_summary.get("fetch_mode")
            or overseas["candidates"].get("fetch_mode")
            or "unknown"
        )
        if fetch_mode == "fixture":
            lines.append("> 海外数据模式：fixture 演练数据，不代表当日真实采集。")
        elif fetch_mode != "http":
            lines.append(f"> 海外数据模式：{fetch_mode}，来源模式未确认。")
        lines.extend(_overseas_event_line(event) for event in events)
        if not events:
            if overseas_collection["status"] == "complete":
                lines.append("- 无事件增量")
            else:
                lines.append("- 本次未提取到事件，采集不完整，不能判断无新消息")
        lines.extend(
            [
                "",
                "### 海外采集状态",
                (
                    f"- 披露候选 {_count(overseas_summary.get('disclosure_candidates'))} 份 / "
                    f"原子主张 {_count(overseas_summary.get('claim_candidates'))} 条 / "
                    f"证据 {_count(overseas_summary.get('evidence_candidates'))} 条"
                ),
                (
                    f"- 端点 {_fmt_count(overseas_collection['endpoint_count'])} 个："
                    f"成功 {_fmt_count(overseas_collection['endpoint_succeeded'])} / "
                    f"失败 {_fmt_count(overseas_collection['endpoint_failed'])}"
                ),
                (
                    f"- 已配置端点覆盖 {_fmt_count(overseas_collection['configured_entity_count'])}/"
                    f"{_fmt_count(overseas_collection['monitored_entity_count'])} 个监控实体"
                    "（配置覆盖，不代表采集成功或研究覆盖）；"
                    f"缺端点 {_fmt_count(overseas_collection['missing_endpoint_count'])} 个"
                ),
                (
                    f"- 详情抓取失败 {_fmt_count(overseas_collection['article_fetch_failure'])} 条；"
                    f"格式拒收（invalid_item）{_fmt_count(overseas_collection['invalid_item'])} 条"
                ),
                f"- 交叉确认建议 {_count(overseas_summary.get('corroboration_suggestions'))} 条，等待人工批准",
                "> 海外自动结果均为候选，未写入正式账本。",
            ]
        )
    lines.extend(
        [
            "",
            "## 汇总状态",
            f"- 组装状态 assembly_status：{assembly_status}"
            "（两份日报与输入文件是否齐全、可读、日期匹配）",
            f"- 采集状态 collection_status：{collection_status}"
            "（采集健康度，与组装完整性分开评估；unknown 表示字段缺失、不推断成功）",
        ]
    )
    lines.extend(_domestic_collection_lines(domestic_collection))
    lines.append(f"- 海外采集状态：{overseas_collection['status']}")
    lines.extend(f"- {note}" for note in overseas_collection["notes"])
    for error in domestic["errors"]:
        lines.append(f"- 国内输入异常：{error}")
    for error in overseas["errors"]:
        lines.append(f"- 海外输入异常：{error}")
    lines.append("")
    return "\n".join(lines)


def combine_daily_reports(
    *,
    run_date: str,
    domestic_state_root: str | Path,
    overseas_state_root: str | Path,
    output_root: str | Path,
) -> dict[str, Any]:
    _validate_date(run_date)
    domestic_state_root = Path(domestic_state_root).resolve()
    overseas_state_root = Path(overseas_state_root).resolve()
    output_root = Path(output_root).resolve()
    _require_disjoint_output(output_root, domestic_state_root, overseas_state_root)
    domestic = _load_domestic(domestic_state_root, run_date)
    overseas = _load_overseas(overseas_state_root, run_date)
    markdown_path = output_root / "daily" / f"{run_date}.md"
    json_path = output_root / "daily" / f"{run_date}.json"
    assembly_status = (
        "complete"
        if domestic["available"]
        and overseas["available"]
        and not domestic["errors"]
        and not overseas["errors"]
        else "partial"
    )
    collection_status = _worse_collection(
        domestic["collection"]["status"], overseas["collection"]["status"]
    )

    payload = {
        "run_date": run_date,
        "assembly_status": assembly_status,
        "collection_status": collection_status,
        "collection": {
            "domestic": domestic["collection"],
            "overseas": overseas["collection"],
        },
        "domestic": {key: value for key, value in domestic.items() if key != "report"},
        "overseas": {
            key: value for key, value in overseas.items() if key not in {"report", "candidates"}
        },
    }
    _atomic_write(
        markdown_path, _render_markdown(run_date, domestic, overseas, assembly_status)
    )
    _atomic_write(
        json_path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return {
        **payload,
        "markdown_path": str(markdown_path),
        "json_path": str(json_path),
    }


def _render_original_artifact_index(run_date: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>国内与海外每日更新 · {run_date}</title>
  <style>
    :root {{ color-scheme: light; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f5f7fb; color: #17233d; }}
    header {{ padding: 18px 24px 12px; background: white; border-bottom: 1px solid #dfe5ef; }}
    h1 {{ margin: 0 0 6px; font-size: 20px; }}
    p {{ margin: 0; color: #667085; font-size: 13px; }}
    nav {{ display: flex; gap: 10px; padding: 14px 24px; }}
    button,a.open {{ border: 1px solid #cbd5e1; border-radius: 999px; background: white; color: #213a75; padding: 8px 13px; cursor: pointer; text-decoration: none; font-size: 14px; }}
    button.active {{ background: #213a75; color: white; border-color: #213a75; }}
    main {{ padding: 0 18px 18px; }}
    section {{ display: none; height: calc(100vh - 126px); background: white; border: 1px solid #dfe5ef; border-radius: 12px; overflow: hidden; }}
    section.active {{ display: block; }}
    iframe {{ width: 100%; height: 100%; border: 0; background: white; }}
    pre {{ height: 100%; margin: 0; padding: 24px; overflow: auto; white-space: pre-wrap; font: 14px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace; color: #16213a; }}
  </style>
</head>
<body>
  <header>
    <h1>国内与海外每日更新 · {run_date}</h1>
    <p>统一入口只负责导航；国内 TXT 与海外 HTML 均保持原始内容，不做重写或摘要。</p>
  </header>
  <nav>
    <button class="active" data-target="domestic">国内增量日报（原始 TXT）</button>
    <button data-target="overseas">海外情报全景（原始 HTML）</button>
    <a class="open" href="domestic.txt" target="_blank">单独打开 TXT</a>
    <a class="open" href="overseas.html" target="_blank">单独打开海外网页</a>
  </nav>
  <main>
    <section id="domestic" class="active"><pre id="domestic-content">正在读取原始 TXT…</pre></section>
    <section id="overseas"><iframe src="overseas.html" title="海外情报全景"></iframe></section>
  </main>
  <script>
    fetch('domestic.txt')
      .then((response) => {{ if (!response.ok) throw new Error(response.status); return response.text(); }})
      .then((text) => {{ document.getElementById('domestic-content').textContent = text; }})
      .catch((error) => {{ document.getElementById('domestic-content').textContent = '国内 TXT 读取失败：' + error; }});
    for (const button of document.querySelectorAll('button[data-target]')) {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('button[data-target], main section').forEach((node) => node.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(button.dataset.target).classList.add('active');
      }});
    }}
  </script>
</body>
</html>
"""


def publish_daily_artifacts(
    *,
    run_date: str,
    domestic_txt: str | Path,
    overseas_html: str | Path,
    output_root: str | Path,
) -> dict[str, Any]:
    """Publish both accepted reader artifacts without rewriting either source."""
    _validate_date(run_date)
    domestic_txt = Path(domestic_txt).resolve()
    overseas_html = Path(overseas_html).resolve()
    output_root = Path(output_root).resolve()
    for source, suffix in ((domestic_txt, ".txt"), (overseas_html, ".html")):
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.suffix.lower() != suffix:
            raise ValueError(f"expected {suffix} source, got {source}")
        if source == output_root or source.is_relative_to(output_root):
            raise ValueError(
                "output_root must be disjoint from domestic and overseas sources: "
                f"output={output_root}, source={source}"
            )

    artifact_root = output_root / "daily" / run_date
    domestic_path = artifact_root / "domestic.txt"
    overseas_path = artifact_root / "overseas.html"
    index_path = artifact_root / "index.html"
    manifest_path = artifact_root / "manifest.json"
    source_hashes = {
        "domestic": _sha256(domestic_txt),
        "overseas": _sha256(overseas_html),
    }
    _atomic_copy(domestic_txt, domestic_path)
    _atomic_copy(overseas_html, overseas_path)
    _atomic_write(index_path, _render_original_artifact_index(run_date))
    published_hashes = {
        "domestic": _sha256(domestic_path),
        "overseas": _sha256(overseas_path),
    }
    if published_hashes != source_hashes:
        raise OSError("published artifact hash mismatch")
    manifest = {
        "run_date": run_date,
        "content_policy": "verbatim",
        "sources": {
            "domestic": {"path": str(domestic_txt), "sha256": source_hashes["domestic"]},
            "overseas": {"path": str(overseas_html), "sha256": source_hashes["overseas"]},
        },
        "published": {
            "domestic": str(domestic_path),
            "overseas": str(overseas_path),
            "index": str(index_path),
        },
    }
    _atomic_write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return {
        "run_date": run_date,
        "domestic_path": str(domestic_path),
        "overseas_path": str(overseas_path),
        "index_path": str(index_path),
        "manifest_path": str(manifest_path),
    }
