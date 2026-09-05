from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ANN_PAT = re.compile(r"重大合同|向特定对象|定增|业绩预告|业绩快报|问询|回复|收购|资产重组")
IR_KW = re.compile(r"光模块|光通信|光通讯|CPO|光芯片|光器件|光引擎|硅光|800G|1\.6T|相干", re.I)
QA_KEYS = ("code", "question", "answer", "answer_date", "index_id", "empty", "fetch_date")
IR_ENDPOINT = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
BACKFILL_START = "2023-01-01"
QA_OVERLAP_DAYS = 7


def _rows(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _clean(value):
    return re.sub(r"<[^>]+>", "", str(value or "")).replace("&nbsp;", " ").replace("&amp;", "&").strip()


def _date(value):
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000).date().isoformat()
    return str(value or "")[:10]


def _key(row):
    return ("id", str(row.get("index_id"))) if row.get("index_id") else (
        "content", row.get("question", ""), row.get("answer", ""), row.get("ask_date", ""), row.get("answer_date", ""))


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


class RequestsClient:
    """Small network adapter. Tests replace it with FixtureClient."""

    def __init__(self, source_root):
        import requests
        self.source_root = Path(source_root).resolve()
        self.session = requests.Session()

    def _post(self, data):
        return self.session.post(IR_ENDPOINT, data=data, timeout=40).json().get("announcements", [])

    def query_ir(self, tab, category, since, until):
        found = []
        for page in (1, 2, 3):
            data = {"pageNum": str(page), "pageSize": "30", "column": "", "tabName": tab,
                    "plate": "", "stock": "", "searchkey": "", "secid": "", "category": category,
                    "trade": "", "seDate": f"{since}~{until}", "sortName": "", "sortType": "", "isHLtitle": "true"}
            rows = self._post(data)
            if not rows:
                break
            found.extend(rows)
        return found

    def download(self, url):
        if not url.startswith("http"):
            url = "https://static.cninfo.com.cn/" + url.lstrip("/")
        response = self.session.get(url, headers={"Referer": "https://www.cninfo.com.cn/"}, timeout=60)
        response.raise_for_status()
        return response.content

    def _fetch_module(self):
        """按客户端（即按运行）缓存抓取模块。

        此前每家都 reload：_p5w_down 熔断与 _LAST_REQUEST 限速状态被逐家重置，
        运行级熔断形同虚设（2026-08-21 p5w 不可达 → 60min 超时的成因之一）。
        """
        cached = getattr(self, "_fetch_module_cache", None)
        if cached is None:
            fetcher_path = self.source_root / "corpus/_fetch_qa.py"
            spec = importlib.util.spec_from_file_location("_domestic_daily_fetch_qa", fetcher_path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            cached = self._fetch_module_cache = module
        return cached

    def fetch_qa(self, code, since, existing):
        """Run the repository's exact SSE/IRM/P5W fetcher against an isolated seed."""
        module = self._fetch_module()
        with tempfile.TemporaryDirectory(prefix="domestic-qa-") as temp:
            isolated_root = Path(temp)
            qpath = isolated_root / "corpus/qa" / code / "qa.jsonl"
            qpath.parent.mkdir(parents=True, exist_ok=True)
            qpath.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing),
                encoding="utf-8",
            )
            module.ROOT = str(isolated_root)
            module.fetch(code, since)
            return DailyMirror._read_qa(qpath)

    def query_announcements(self, code, since, until):
        data = {"pageNum": "1", "pageSize": "15", "column": "", "tabName": "fulltext",
                "plate": "", "stock": "", "searchkey": code, "secid": "", "category": "",
                "trade": "", "seDate": f"{since}~{until}", "sortName": "", "sortType": "", "isHLtitle": "true"}
        return self._post(data)

    def rescreen(self, code, until):
        response = self.session.get("https://webapi.cninfo.com.cn/api/stock/p_stock2110", params={"scode": code, "sdate": "1990-01-01", "edate": until}, timeout=30)
        if response.status_code == 401 or "未经授权" in response.text or '"resultcode":401' in response.text:
            raise RuntimeError("p_stock2110 需token(401)")
        try: records = response.json()
        except ValueError: return None
        if isinstance(records, dict): records = records.get("result") or records.get("data") or []
        for row in records:
            if str(row.get("F001V") or row.get("f001v") or "") == "008003" and str(row.get("F008C") or row.get("f008c") or "") == "1":
                return str(row.get("F005V") or row.get("f005v") or "").strip() or None
        return None


class FixtureClient:
    """Deterministic adapter used by tests and local fixture runs."""

    def __init__(self, **kwargs):
        self.data = kwargs
        self.calls = []
        self.qa_since = {}

    def _get(self, name, *args):
        self.calls.append((name,) + args)
        value = self.data.get(name, {})
        result = value.get(args[0], []) if isinstance(value, dict) else value
        if isinstance(result, Exception):
            raise result
        return result

    def query_ir(self, tab, category, since, until): return self.data.get("ir", {}).get(tab, [])
    def download(self, url): return self.data.get("downloads", {}).get(url, b"%PDF-fixture")
    def fetch_qa(self, code, since, existing=None):
        self.qa_since[code] = since
        return self._get("qa", code)
    def query_announcements(self, code, since, until): return self._get("announcements", code)
    def rescreen(self, code, until): return self._get("rescreen", code)


class DailyMirror:
    def __init__(self, source_root, state_root, client):
        self.source = Path(source_root).resolve()
        self.state = Path(state_root).resolve()
        if self.state == self.source or self.source in self.state.parents:
            raise ValueError("state_root must be outside source_root")
        self.client = client
        self.frozen = {r["代码"]: r["名称"] for r in _rows(self.source / "corpus/_frozen.csv")}
        self.watch = []
        for row in _rows(self.source / "corpus/_restart_watchlist.csv"):
            try:
                row["_pat"] = re.compile(row.get("触发词", ""), re.I)
            except re.error:
                continue
            self.watch.append(row)

    def watched_codes(self):
        names = {code: name for code, name in self.frozen.items()}
        codes = set()
        for row in _rows(self.source / "triage.csv"):
            if row.get("处置") == "待判":
                codes.update(c for c, n in names.items() if n == row.get("公司"))
        for row in _rows(self.source / "points.csv"):
            if row.get("状态") in ("生产中", "在建"):
                codes.update(c for c, n in names.items() if n == row.get("公司"))
        codes.update(r["代码"] for r in self.watch if r.get("车道") == "日更" and r.get("代码"))
        # This module talks only to mainland disclosure/Q&A adapters. The
        # shared frozen universe also contains overseas identifiers, which
        # belong to calls.daily_discovery and must not reach these adapters.
        return sorted(code for code in codes if re.fullmatch(r"\d{6}", code))

    def _protected_fingerprint(self):
        digest = hashlib.sha256()
        exact = [
            "corpus/_frozen.csv", "corpus/_restart_watchlist.csv", "triage.csv",
            "points.csv", "words.txt", "scan.py",
        ]
        paths = [self.source / name for name in exact]
        for dirname in ("corpus/qa", "corpus/ir"):
            root = self.source / dirname
            if root.exists():
                paths.extend(path for path in root.rglob("*") if path.is_file())
        for path in sorted(path for path in paths if path.exists()):
            digest.update(str(path.relative_to(self.source)).encode())
            digest.update(path.read_bytes())
        annual = self.source / "corpus/annual"
        if annual.exists():
            for path in sorted(path for path in annual.rglob("*") if path.is_file()):
                stat = path.stat()
                digest.update(str(path.relative_to(self.source)).encode())
                digest.update(f"{stat.st_size}:{stat.st_mtime_ns}".encode())
        return digest.hexdigest()

    def _source_check_lines(self):
        scan = self.source / "scan.py"
        if not scan.is_file():
            return ["源仓库只读;镜像独立运行"], ["source_root 内容指纹前后相同"]
        try:
            result = subprocess.run(
                [sys.executable, str(scan), "--check"],
                cwd=self.source,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return (
                ["源仓库只读;镜像独立运行"],
                [f"scan.py --check 未完成: {type(exc).__name__}"],
            )
        ansi = re.compile(r"\x1b\[[0-9;]*m")
        lines = [ansi.sub("", line).strip() for line in result.stdout.splitlines() if line.strip()]
        corpus = [line for line in lines if "语料" in line]
        checks = [line for line in lines if "全绿" in line or line.startswith("[")]
        return (
            corpus or ["源仓库只读;镜像独立运行"],
            checks[:3] or ["source_root 内容指纹前后相同"],
        )

    @contextmanager
    def _lock(self):
        self.state.mkdir(parents=True, exist_ok=True)
        lock_path = self.state / ".lock"
        import fcntl
        with lock_path.open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError(f"state root is locked: {lock_path}") from exc
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _source_qa(self, code):
        path = self.source / "corpus/qa" / code / "qa.jsonl"
        return self._read_qa(path)

    @staticmethod
    def _read_qa(path):
        rows = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                    if all(k in row for k in QA_KEYS): rows.append(row)
                except json.JSONDecodeError:
                    continue
        return rows

    def _old_qa(self, code):
        return self._read_qa(self.state / "qa" / code / "qa.jsonl")

    def _scan(self, added_ir):
        words = []
        for line in (self.source / "words.txt").read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                word, cell, exclude, context = [x.strip() for x in line.split("|", 3)]
                words.append((word, cell, exclude, context))
        done = {r.get("hit_id") for r in _rows(self.source / "triage.csv")}
        filled = {r.get("cell_id") for r in _rows(self.source / "points.csv")}
        known = {r.get("公司") for r in _rows(self.source / "points.csv")}
        texts = []
        for pdf in sorted((self.source / "corpus/annual").glob("**/*.pdf")):
            text_path = Path(str(pdf) + ".txt")
            if not text_path.exists():
                continue
            company = re.search(r"_([^_]+)_em_", pdf.name)
            texts.append((company.group(1) if company else pdf.parent.name, pdf.name, text_path.read_text(errors="ignore")))
        for root in (self.source / "corpus/ir", self.state / "ir"):
            if not root.exists():
                continue
            for path in sorted(root.glob("*/*")):
                code = path.parent.name
                if path.suffix == ".pdf":
                    text_path = Path(str(path) + ".txt")
                    if text_path.exists():
                        texts.append((self.frozen.get(code, code), path.name, text_path.read_text(errors="ignore")))
                elif path.suffix == ".docx":
                    text_path = Path(str(path) + ".txt")
                    if text_path.exists():
                        texts.append((self.frozen.get(code, code), path.name, text_path.read_text(errors="ignore")))
        for code, path, text in added_ir:
            texts.append((self.frozen.get(code, code), path.name, text))
        queue = []
        for company, filename, original in texts:
            text = re.sub(r"\s+", "", original)
            for word, cell, exclude, context in words:
                if cell == "ANY" and company in known: continue
                match = re.search(re.escape(word), text)
                if not match: continue
                segment = text[max(0, match.start()-40):match.end()+40]
                if exclude and re.search(exclude, segment): continue
                if context and context not in segment: continue
                hit = f"{company}+{cell}+{filename[:40]}"
                if hit in done: continue
                priority = 1 if cell == "ANY" else (0 if cell not in filled else 2)
                queue.append((priority, f"{company}|{cell}|{word}|{segment[:50]}", company, cell, word, segment[:50]))
        return [x[1] for x in sorted(queue)]

    def _write_json(self, relative, payload):
        path = self.state / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(_json_bytes(payload))
        os.replace(tmp, path)

    def _read_json(self, relative):
        path = self.state / relative
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        # 非 dict（list/str/数字）一律视为不可信，回落到"无状态"，不能拿去 .get()
        return payload if isinstance(payload, dict) else None

    def _flush_logs(self):
        """日志在轮次进行中即落盘，不等整轮结束才可见。"""
        logs = getattr(self, "_logs", [])
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "run.log").write_text("\n".join(logs) + ("\n" if logs else ""), encoding="utf-8")

    def _extract_pdf(self, code, path, text_path):
        """从 PDF 抽取正文；失败/无文本层均登记为降级（partial），不静默成空白成功。

        pdftotext 退出码 0 但输出文件缺失或仅含空白（扫描件/无文本层/换页符）也要降级，
        并把正文规范为空串，确保调用方 new_ir 读取不会 FileNotFoundError、且不会把空白误判有正文。
        """
        try:
            proc = subprocess.run(["pdftotext", "-layout", str(path), str(text_path)], capture_output=True)
            failed = bool(proc.returncode)
        except OSError:
            failed = True  # pdftotext 未安装/无法执行
        if failed:
            text_path.write_text("", encoding="utf-8")
            self._emit(f"[投关表] {code} PDF文本提取失败,正文不参与扫描: {path.name[:40]}")
            return
        text = text_path.read_text(errors="ignore") if text_path.exists() else ""
        if not text.strip():  # 退出 0 但无正文（空白/换行），按无文本层降级
            text_path.write_text("", encoding="utf-8")
            self._emit(f"[投关表] {code} PDF无文本层(空白正文),正文不参与扫描: {path.name[:40]}")

    def _emit(self, message):
        """记录一条失败：进 logs、进错误摘要，并立即落盘。"""
        self._logs.append(message)
        self._errors.append(message)
        self._flush_logs()

    def _write_run_status(self, status, extra=None):
        progress = getattr(self, "_progress", None) or {"processed": 0, "total": 0, "stage": "启动"}
        payload = {
            "run_date": getattr(self, "_run_date", None),
            "status": status,
            "updated_at": _now_iso(),
            "processed": progress.get("processed", 0),
            "total": progress.get("total", 0),
            "stage": progress.get("stage", "启动"),
            "error_count": len(getattr(self, "_errors", [])),
            "errors": list(getattr(self, "_errors", [])),
            "prior_run_interrupted": bool(getattr(self, "_interrupted", False)),
        }
        if extra:
            payload.update(extra)
        self._write_json("run-status.json", payload)

    @staticmethod
    def _qa_since(stored, day):
        """互动易起始日期 = 上次成功水位 - 重叠窗口。

        无水位（首次或被中断后重试）或水位非法 → 退回 BACKFILL_START 全量回填。
        水位在未来（时钟偏移、回填日倒退）时取 min(水位, run_date)：绝不返回零宽或未来窗口，
        否则会跳过从未抓取过的区间。水位只在抓取成功后推进（见 run），失败不推进。
        """
        floor = dt.date.fromisoformat(BACKFILL_START)
        if not stored:
            return BACKFILL_START
        try:
            base = dt.date.fromisoformat(str(stored)[:10])
        except ValueError:
            return BACKFILL_START
        target = min(base, day) - dt.timedelta(days=QA_OVERLAP_DAYS)
        if target <= floor:
            return BACKFILL_START
        return target.isoformat()

    def run(self, run_date, backfill_since=None):
        """跑一轮国内日更。

        backfill_since: 显式回填起点；给出时忽略互动易成功水位，仅用于补历史，不用于日常增量。
        返回 manifest 带 run_status(complete/partial/failed)；失败项同时落在 run.log 与 run-status.json。
        """
        day = dt.date.fromisoformat(run_date)
        today, since = day.isoformat(), (day - dt.timedelta(days=3)).isoformat()
        if backfill_since:
            backfill_since = dt.date.fromisoformat(str(backfill_since)).isoformat()
        with self._lock():
            before = self._protected_fingerprint()
            staging = Path(tempfile.mkdtemp(prefix=".run-", dir=self.state))
            try:
                self._run_date = today
                self._logs = []
                self._errors = []
                self._progress = {"processed": 0, "total": 0, "stage": "启动"}
                logs = self._logs
                errors = self._errors
                ir_tabs = (("relation", "category_dyhd_szdy"), ("fulltext", ""))
                prior_status = self._read_json("run-status.json")
                self._interrupted = bool(prior_status and prior_status.get("status") == "running")
                if self._interrupted:
                    logs.append(f"[运行状态] 上一次运行遗留 running(run_date={prior_status.get('run_date')})：仅证明上次未正常结束，不据此推断终止原因")
                self._flush_logs()
                prior_manifest = self._read_json("manifest.json")
                codes = self.watched_codes(); digest = {"ir_new": [], "qa_new": [], "ann": [], "q_delta_new": [], "q_delta_gone": []}
                qa_watermarks = self._read_json("qa_watermarks.json") or {}
                qa_failed = []; qa_backfill = []
                new_ir = []; added_qa = []; outliers = []
                seen = set(); seen_outliers = set()
                self._progress = {"processed": 0, "total": len(ir_tabs) + 2 * len(codes), "stage": "投关表"}
                self._write_run_status("running")
                for tab, category in ir_tabs:
                    try:
                        ir_rows = self.client.query_ir(tab, category, since, today) or []
                    except Exception as exc:
                        self._emit(f"[投关表] {tab} 查询失败: {str(exc)[:80]}")
                        continue
                    finally:
                        self._progress["processed"] += 1
                        self._write_run_status("running")
                    for item in ir_rows:
                        code, name, title = str(item.get("secCode", "")), str(item.get("secName", "")), _clean(item.get("announcementTitle"))
                        url = str(item.get("adjunctUrl", ""))
                        if tab == "fulltext" and "投资者关系" not in title: continue
                        if code in self.frozen and url.lower().endswith(".pdf"):
                            key = code + title
                            if key in seen: continue
                            seen.add(key)
                            try:
                                content = self.client.download(url)
                            except Exception as exc:
                                self._emit(f"[投关表] {code} PDF下载失败: {str(exc)[:80]}")
                                continue
                            if not content.startswith(b"%PDF"):
                                self._emit(f"[投关表] {code} 非PDF响应,未入库: {title[:40]}")
                                continue
                            path = staging / "ir" / code / (re.sub(r"[^\w\-.一-龥]", "_", f"{code}_{_date(item.get('announcementTime'))}_{title}") + ".pdf")
                            path.parent.mkdir(parents=True, exist_ok=True)
                            existing_path = self.state / path.relative_to(staging)
                            existing_text = existing_path.with_suffix(path.suffix + ".txt")
                            # 仅当 PDF 与正文都已落盘才跳过；正文缺失/空白每轮重试提取，
                            # 否则一次提取失败留下空 txt，下次 existing_path 命中即永久跳过（2026-09-05 复审）。
                            if existing_path.exists() and existing_text.exists() and existing_text.stat().st_size > 0:
                                continue
                            path.write_bytes(content)
                            text_path = path.with_suffix(path.suffix + ".txt")
                            text = str(item.get("text", ""))
                            if text: text_path.write_text(text, encoding="utf-8")
                            elif content.startswith(b"%PDF"):
                                self._extract_pdf(code, path, text_path)
                            else: text_path.write_text("", encoding="utf-8")
                            digest["ir_new"].append((self.frozen[code], _date(item.get("announcementTime")), title)); new_ir.append((code, path, text_path.read_text(errors="ignore")))
                        elif url.lower().endswith(".pdf") and name and IR_KW.search(title):
                            key = name + title
                            if key not in seen_outliers:
                                seen_outliers.add(key)
                                outliers.append((name, _date(item.get("announcementTime")), title))
                self._progress["stage"] = "互动易"
                self._write_run_status("running", {"qa_failed": qa_failed, "qa_backfill": qa_backfill})
                for code in codes:
                    existing = self._source_qa(code) + self._old_qa(code); prior = {_key(x) for x in existing}
                    qa_since = backfill_since or self._qa_since(qa_watermarks.get(code), day)
                    if code not in qa_watermarks:
                        qa_backfill.append(code)
                    try:
                        fetched = self.client.fetch_qa(code, qa_since, existing) or []
                    except Exception as exc:
                        self._emit(f"[互动易] {code} 抓取失败(since={qa_since}): {str(exc)[:80]}")
                        qa_failed.append(code)
                        fetched = []
                    else:
                        qa_watermarks[code] = today
                    merged = { _key(x): x for x in existing }
                    for row in fetched:
                        if _key(row) not in merged: added_qa.append((code, row))
                        merged[_key(row)] = row
                    if len(merged) > len(prior): digest["qa_new"].append((self.frozen.get(code, code), len(merged) - len(prior)))
                    qpath = staging / "qa" / code / "qa.jsonl"; qpath.parent.mkdir(parents=True, exist_ok=True)
                    qpath.write_text("".join(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n" for v in merged.values()), encoding="utf-8")
                    self._progress["processed"] += 1
                    self._write_run_status("running", {"qa_failed": qa_failed, "qa_backfill": qa_backfill})
                self._progress["stage"] = "公告流"
                self._write_run_status("running", {"qa_failed": qa_failed, "qa_backfill": qa_backfill})
                for code in codes:
                    try:
                        announcements = self.client.query_announcements(code, since, today) or []
                    except Exception as exc:
                        self._emit(f"[公告流] {code} 查询失败: {str(exc)[:80]}")
                        continue
                    finally:
                        self._progress["processed"] += 1
                        self._write_run_status("running", {"qa_failed": qa_failed, "qa_backfill": qa_backfill})
                    for item in announcements:
                        if str(item.get("secCode", code)) != code: continue
                        title = _clean(item.get("announcementTitle"))
                        if ANN_PAT.search(title):
                            url = str(item.get("adjunctUrl", ""))
                            if url and not url.startswith("http"):
                                url = "https://static.cninfo.com.cn/" + url.lstrip("/")
                            digest["ann"].append((self.frozen.get(code, code), _date(item.get("announcementTime")), title, url))
                restart = []
                for code, path, text in new_ir:
                    for w in self.watch:
                        match = w["_pat"].search(text) if w.get("车道") == "日更" and w.get("代码") == code else None
                        if match:
                            start = max(0, match.start() - 50)
                            context = re.sub(r"\s+", "", text[start:match.start() + 70])
                            restart.append((w, f"投关表《{path.stem[:30]}》", context))
                for company, date, title, url in digest["ann"]:
                    restart.extend((w, f"公告流({date}): {title[:40]}", url) for w in self.watch if w.get("车道") == "日更" and w.get("公司") == company)
                for company, count in digest["qa_new"]:
                    restart.extend((w, f"互动易+{count}条", "增量内容未逐条匹配,需人工过内容") for w in self.watch if w.get("车道") == "日更" and w.get("公司") == company)
                current = self._scan(new_ir); latest = self.state / "daily/queue-latest.txt"; queue_baseline_initialized = not latest.exists(); previous = latest.read_text(encoding="utf-8").splitlines() if latest.exists() else []
                keys = lambda lines: {x.split("|", 2)[0] + "|" + x.split("|", 2)[1] for x in lines}
                if queue_baseline_initialized:
                    digest["q_delta_new"] = []
                    digest["q_delta_gone"] = []
                else:
                    digest["q_delta_new"] = [x for x in current if x.split("|", 2)[0] + "|" + x.split("|", 2)[1] not in keys(previous)]
                    digest["q_delta_gone"] = [x for x in previous if x.split("|", 2)[0] + "|" + x.split("|", 2)[1] not in keys(current)]
                rescreen = None
                marker = self.state / "monthly" / f".rescreen-{today[:7]}.done"
                if not marker.exists() and (day.day == 1 or not (self.state / "daily" / f"{today}.txt").exists()):
                    rescreen = {"month": today[:7], "checked": 0, "moved_out": [], "unresolved": 0, "blocked": False}
                    self._progress["stage"] = "月度重筛"
                    self._progress["total"] += len(self.frozen)
                    for code in self.frozen:
                        try:
                            result = self.client.rescreen(code, today)
                            rescreen["checked"] += 1
                            if result and result not in ("半导体", "光学光电子", "通信设备", "元件"): rescreen["moved_out"].append((code, self.frozen[code], result))
                        except Exception as exc:
                            message = str(exc)
                            if "401" in message or "token" in message or "未经授权" in message:
                                rescreen["blocked"] = True
                                rescreen["unresolved"] = len(self.frozen) - rescreen["checked"]
                                self._emit("[重筛] p_stock2110 需token(401), 本月重筛未完成(降级,不计为成功)")
                                break
                            rescreen["unresolved"] += 1
                            self._emit(f"[重筛] {code} 失败: {message[:50]}")
                        finally:
                            self._progress["processed"] += 1
                            self._write_run_status("running", {"qa_failed": qa_failed, "qa_backfill": qa_backfill})
                    if not rescreen["blocked"]:
                        staged_marker = staging / "monthly" / marker.name
                        staged_marker.parent.mkdir(parents=True, exist_ok=True)
                        staged_marker.write_text(today, encoding="utf-8")
                if not rescreen and day.day == 1: logs.append("[重筛] 本月已存在标记,跳过")
                # 只在"持久化的 manifest 本身也是 complete"时才复用：旧的 partial / 升级前无
                # run_status 的遗留 manifest 必须被重写，否则磁盘产物与本次运行状态不一致。
                prior_complete = bool(prior_manifest and prior_manifest.get("run_status") == "complete")
                unchanged_replay = bool(
                    prior_complete
                    and prior_manifest.get("date") == today
                    and prior_manifest.get("source_fingerprint") == before
                    and not digest["ir_new"] and not digest["qa_new"]
                    and json.loads(json.dumps(digest["ann"], ensure_ascii=False)) == prior_manifest.get("digest", {}).get("ann", [])
                    and json.loads(json.dumps(outliers, ensure_ascii=False)) == prior_manifest.get("outliers", [])
                    and hashlib.sha256("\n".join(current).encode()).hexdigest() == prior_manifest.get("queue_sha256")
                    and not errors
                )
                if unchanged_replay:
                    after = self._protected_fingerprint()
                    if before != after: raise RuntimeError("source_root changed during run")
                    self._progress["processed"] = self._progress["total"]
                    self._write_json("qa_watermarks.json", qa_watermarks)
                    self._write_run_status("complete", {"qa_failed": qa_failed, "qa_backfill": qa_backfill, "unchanged_replay": True})
                    return {"daily_path": str(self.state / "daily" / f"{today}.txt"), "manifest_path": str(self.state / "manifest.json"),
                            "manifest": dict(prior_manifest, run_status="complete", errors=errors, qa_failed_codes=qa_failed)}
                evidence = bool(digest["ir_new"] or digest["qa_new"] or digest["ann"] or digest["q_delta_new"] or restart)
                run_status = "partial" if errors else "complete"
                corpus_lines, check_lines = self._source_check_lines()
                out = [f"# 日报 {today}", "", f"## 运行状态 {run_status}"]
                if run_status != "complete":
                    out.append(f"- 本次运行有 {len(errors)} 项失败，下列栏目不完整；不能据此判断今日无新增。")
                    out += [f"  - {x}" for x in errors[:10]]
                out += ["", "## 语料", *[f"- {line}" for line in corpus_lines], "", f"## 投关表新增 {len(digest['ir_new'])} 份"]
                out += [f"- {n} | {d} | {t[:60]}" for n, d, t in digest["ir_new"][:20]] + [f"\n## 互动易增量 {sum(x[1] for x in digest['qa_new'])} 条"]
                out += [f"- {n} +{k}条" for n, k in digest["qa_new"]] + [f"\n## 公告流(关注公司) {len(digest['ann'])} 条"] + [f"- {n} | {d} | [{t[:50]}]({u})" for n, d, t, u in digest["ann"][:15]]
                out += [f"\n## 重启复核(待判/待确认监视) {len(restart)} 条", "> 机械匹配，不构成判定"] + ([f"- {w['公司']} [{w['类别']}|{w.get('cell_id','')}] {src} | {ctx[:80]}" for w, src, ctx in restart[:20]] or ["- 无触发"])
                if queue_baseline_initialized:
                    out.append(f"\n## 召回队列基线初始化: {len(current)} 条（不计为当日新增）")
                else:
                    out.append(f"\n## 召回净队列差分: 新增{len(digest['q_delta_new'])} / 消失{len(digest['q_delta_gone'])}")
                    for item in digest["q_delta_new"][:15]:
                        company, cell, word, segment = item.split("|", 3)
                        out.append(f"- [{company}|{cell}] {word} | {segment[:60]}")
                gate = "有增量,值得开闸复核" if evidence else ("本次运行不完整，不能判断无新增" if run_status != "complete" else "无实质增量,今日免开闸")
                out += ["\n## 校验", *[f"- {line}" for line in check_lines], f"\n> 判定闸建议: {gate}", f"\n## 补录候选(宇宙外·光通信命中) {len(outliers)} 条"] + ([f"- {n} | {d} | {t[:60]}" for n, d, t in outliers[:30]] or ["- 无"])
                if rescreen: out += [f"\n## 分母差分(月度重筛 {rescreen['month']})", f"- 复核存量 {rescreen['checked']} 家 / 移出 {len(rescreen['moved_out'])} 家 / 新增 0 家", "- 仅报 diff,不改 _frozen.csv"]
                if logs: out += ["\n## 日志"] + [f"- {x}" for x in logs]
                daily = staging / "daily"; daily.mkdir(parents=True, exist_ok=True); (daily / f"{today}.txt").write_text("\n".join(out), encoding="utf-8"); (daily / "queue-latest.txt").write_text("\n".join(current), encoding="utf-8"); (daily / "queue-prev.txt").write_text("\n".join(previous), encoding="utf-8")
                (staging / "qa_watermarks.json").write_bytes(_json_bytes(qa_watermarks))
                manifest = {"date": today, "source_fingerprint": before, "queue_sha256": hashlib.sha256("\n".join(current).encode()).hexdigest(), "queue_baseline_initialized": queue_baseline_initialized, "watched_codes": codes, "digest": digest, "restart_hits": len(restart), "outlier_hits": len(outliers), "outliers": outliers, "rescreen": rescreen, "logs": logs, "run_status": run_status, "errors": errors, "qa_failed_codes": qa_failed, "qa_backfill_codes": qa_backfill, "prior_run_interrupted": self._interrupted}
                (staging / "manifest.json").write_bytes(_json_bytes(manifest))
                (staging / "run.log").write_text("\n".join(logs) + ("\n" if logs else ""), encoding="utf-8")
                for path in sorted(staging.rglob("*")):
                    if path.is_file():
                        target = self.state / path.relative_to(staging); target.parent.mkdir(parents=True, exist_ok=True); os.replace(path, target)
                after = self._protected_fingerprint()
                if before != after: raise RuntimeError("source_root changed during run")
                self._progress["processed"] = self._progress["total"]
                self._write_run_status(run_status, {"qa_failed": qa_failed, "qa_backfill": qa_backfill, "daily_path": str(self.state / "daily" / f"{today}.txt")})
                return {"daily_path": str(self.state / "daily" / f"{today}.txt"), "manifest_path": str(self.state / "manifest.json"), "manifest": manifest}
            except Exception:
                try:
                    self._write_run_status("failed")
                except Exception:
                    pass
                raise
            finally:
                shutil.rmtree(staging, ignore_errors=True)
