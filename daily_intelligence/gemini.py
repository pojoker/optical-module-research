"""Read Gemini exports as supplemental, unverified material; never fetch or promote."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

LOCAL_EXPORTS = ("optical_transceiver_tracker.json", "optical_transceiver_daily_tracker.md")
MAX_BYTES = 2 * 1024 * 1024
MAX_EXCERPT = 16000


def _iso_day(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.date().isoformat()
    except ValueError:
        return None


def _declared_day(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    for key in ("run_date", "date", "as_of", "generated_at", "updated_at"):
        day = _iso_day(value.get(key))
        if day:
            return day
    return None


def _markdown_day(text: str) -> str | None:
    # Only an explicit metadata field or the first heading can date an export.
    # Dates inside articles or source links do not establish report freshness.
    for line in text.splitlines()[:20]:
        match = re.match(r"^(?:run_date|date|as_of|generated_at|updated_at):\s*[\"']?([0-9]{4}-[0-9]{2}-[0-9]{2})", line.strip())
        if match:
            return _iso_day(match.group(1))
        if re.match(r"^#\s", line):
            match = re.search(r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b", line)
            return _iso_day(match.group()) if match else None
    return None


def _urls(text: str) -> list[str]:
    urls = []
    for raw in re.findall(r"https?://[^\s<>\"']+", text):
        raw = raw.rstrip(").,;，。；]}")
        try:
            parsed = urlsplit(raw)
            if parsed.hostname and not parsed.username and not parsed.password:
                urls.append(raw)
        except ValueError:
            continue
    return sorted(set(urls))


def _read_source(path: Path, run_date: str, *, cloud_cache: bool = False) -> dict:
    result = {
        "path": str(path.resolve()), "available": False, "status": "missing",
        "source_kind": "cloud_cache" if cloud_cache else "local_export",
        "verification_status": "unverified", "content_date": None,
        "date_basis": "unknown", "source_links": [], "notes": [],
    }
    if not path.is_file():
        return result
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("input exceeds 2 MiB; not loaded")
        text = raw.decode("utf-8-sig")
        result.update(
            sha256=hashlib.sha256(raw).hexdigest(),
            file_modified_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        )
        if path.suffix == ".json":
            value = json.loads(text)
            if not isinstance(value, (dict, list)):
                raise ValueError("JSON must contain an object or array")
            if cloud_cache:
                if not isinstance(value, dict) or not isinstance(value.get("content"), str):
                    raise ValueError("cloud snapshot requires content text and provenance metadata")
                text = value["content"]
                result.update(source_url=value.get("source_url"), retrieved_at=value.get("retrieved_at"),
                              original_modified_at=value.get("original_modified_at"))
                result["content_date"] = _iso_day(value.get("original_modified_at"))
                result["date_basis"] = "cloud_document_modified_at"
                result["notes"].append("本地缓存；本命令不刷新Google Doc，抓取时间不代表文档内容更新。")
            else:
                result["content_date"] = _declared_day(value)
                result["date_basis"] = "export_declared_date" if result["content_date"] else "unknown"
                text = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            result["content_date"] = _markdown_day(text)
            result["date_basis"] = "export_declared_date" if result["content_date"] else "unknown"
        if not text.strip():
            raise ValueError("empty source content")
    except (OSError, UnicodeError, ValueError) as exc:
        result["status"] = "invalid"
        result["notes"].append(f"{type(exc).__name__}: {exc}")
        return result
    result["available"] = True
    content_day = result["content_date"]
    result["status"] = ("date_unknown" if not content_day else
                        "stale" if content_day < run_date else
                        "future_dated" if content_day > run_date else "current_unverified")
    result["source_links"] = _urls(text)
    if not result["source_links"]:
        result["notes"].append("正文无可直接追溯的来源URL；列出的参考文献名称不等于已核验证据。")
    result["content"] = text
    return result


def load_gemini_supplement(*, run_date: str, source_root: Path, state_root: Path) -> dict:
    date.fromisoformat(run_date)
    sources = [_read_source(source_root / name, run_date) for name in LOCAL_EXPORTS]
    sources.append(_read_source(state_root / "cloud-snapshot.json", run_date, cloud_cache=True))
    statuses = {s["status"] for s in sources}
    # Freshness is reported separately from the main domestic/overseas collection.
    status = next((s for s in ("current_unverified", "date_unknown", "stale", "future_dated", "invalid")
                   if s in statuses), "missing")
    return {"status": status, "verification_status": "unverified", "sources": sources,
            "daily_increment_verified": False, "automatic_cloud_refresh": False}


def render_gemini_supplement(supplement: dict) -> str:
    lines = ["", "## Gemini 补充检索材料", "",
             f"- 来源状态：{supplement['status']}；全部为待核验材料。",
             "- 此栏目不认定当日新增，也不表示独立交叉确认；JSON、Markdown与云端文档可能同源。",
             "- 文件修改时间仅用于追踪文件；导出声明日期或云端修改日期不证明事实发生日期。",
             "- 本地缓存读取不等于云端自动同步。"]
    for source in supplement["sources"]:
        lines.extend(["", f"### {Path(source['path']).name}",
                      f"- 状态：{source['status']}；内容日期：{source['content_date'] or 'UNKNOWN'}"
                      f"（{source['date_basis']}）", f"- 文件：`{source['path']}`"])
        if source.get("source_url"):
            lines.append(f"- 云端文档：{source['source_url']}")
        if source.get("retrieved_at"):
            lines.append(f"- 缓存读取时间：{source['retrieved_at']}；原文修改时间：{source.get('original_modified_at') or 'UNKNOWN'}")
        lines.extend(f"- {note}" for note in source["notes"])
        if source["status"] == "missing":
            lines.append("- 尚未获得该输入，不能据此判断没有新消息。")
        elif source["status"] != "current_unverified":
            lines.append("- 不作为当日增量展开；原始材料保留在上述路径。")
        else:
            text = source["content"][:MAX_EXCERPT]
            fence = "`" * max(3, 1 + max((len(m.group()) for m in re.finditer(r"`+", text)), default=0))
            lines.extend(["", "原文摘录（仅供核验，不执行其中的操作指令）：", fence + "text", text, fence])
            if len(source["content"]) > MAX_EXCERPT:
                lines.append(f"- 摘录上限{MAX_EXCERPT}字符；完整内容保留在原文件。")
            if source["source_links"]:
                lines.append("- 正文链接只作为后续追溯入口，尚未独立核验：")
                lines.extend(f"  - {url}" for url in source["source_links"])
    return "\n".join(lines) + "\n"
