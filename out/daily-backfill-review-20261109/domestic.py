"""Reconstruct the evidence that the existing domestic Daily artifacts actually retain."""

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from domestic_daily.core import IR_KW, _key


REPORT_DATE = re.compile(r"20\d\d-\d\d-\d\d")
ANNOUNCEMENT = re.compile(r"(.+?) \| (.*?) \| \[(.*)\]\((https?://[^)]*)\)$")
DOCUMENT = re.compile(r"(.+?) \| (.*?) \| (.+)$")
QA_TOTAL = re.compile(r"(.+?) \+(\d+)条$")
WATCH = re.compile(r"(.+?) \[([^|]+)\|([^\]]*)\] (.+?) \| (.*)$")
RECALL = re.compile(r"\[([^|]+)\|([^\]]+)\] (.+?) \| (.*)$")
BASE_DATE = "2026-09-04"
BACKFILL = "2026-09-11"
MIRROR_SUFFIX = re.compile(r"\s*[（(]来自[：:]\s*深交所互动易[）)]\s*$")
SECTIONS = {
    "投关表新增": "投关表",
    "互动易增量": "问答计数",
    "公告流": "公告",
    "重启复核": "复核触发",
    "召回净队列差分": "召回候选",
    "补录候选": "宇宙外补录",
}
CELL_PATTERNS = {
    "M1": r"SOI|磷化铟衬底|砷化镓衬底",
    "M2a": r"InP外延|磷化铟外延|再生长",
    "M3": r"光刻胶|特气|靶材",
    "M5": r"高速板材|覆铜板|CCL",
    "C1": r"激光器芯片|EML|DFB|CW光源",
    "C2": r"VCSEL",
    "C3": r"探测器芯片|APD",
    "C4": r"硅光芯片|硅光PIC|光子集成芯片",
    "C5": r"光模块.{0,10}(DSP|Driver|TIA|电芯片)|相干DSP|跨阻放大器",
    "C6": r"可调谐激光器|可调谐光源|WSS|DBR可调",
    "D1": r"TOSA",
    "D2": r"ROSA",
    "D3": r"BOSA",
    "D12": r"光引擎|光模块COB",
    "EQ3": r"固晶|贴片设备|光子器件.{0,8}贴装",
    "EQ4": r"光纤.{0,8}耦合设备|光器件耦合",
    "EQ7": r"光.{0,10}封测设备|光模块.{0,8}测试设备",
    "B1": r"PCB",
    "MOD1": r"数通光模块|高速光模块|[48]00G光模块|1\.6T光模块",
    "MOD2": r"相干光模块|400ZR|ZR\+",
    "MOD3": r"PON|电信光模块",
}
OPTICAL = re.compile(
    IR_KW.pattern + r"|SOI|InP|磷化铟|EML|DFB|VCSEL|TOSA|ROSA|BOSA|FAU|MPO|光互连|光纤",
    re.I,
)


def compact(value):
    return re.sub(r"\s+", "", value or "").replace("Ａ", "A")


def anchor(label, path, line=None):
    return {"label": label, "ref": str(path) + (f"#L{line}" if line else "")}


def stable_id(category, *key):
    digest = hashlib.sha256(json.dumps([category, *key], ensure_ascii=False).encode())
    return "D-" + digest.hexdigest()[:14]


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        while True:
            next_line = reader.line_num + 1
            try:
                row = next(reader)
            except StopIteration:
                return
            yield (max(2, next_line), row)


def json_lines(path, parse_errors):
    if path.is_file():
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    yield line_number, json.loads(line)
                except json.JSONDecodeError:
                    parse_errors.append(str(path) + f"#L{line_number}")


def company_lookup(repo):
    names, codes = {}, {}
    for line, row in csv_rows(repo / "corpus/_frozen.csv"):
        names[compact(row["名称"])] = row["代码"]
        codes[row["代码"]] = (row["名称"], line)
    for line, row in csv_rows(repo / "corpus/_restart_watchlist.csv"):
        code, name = row["代码"], row["公司"]
        if code:
            names.setdefault(compact(name), code)
    return names, codes


class Targets:
    def __init__(self, repo, names, codes):
        self.repo = repo
        self.names, self.codes = names, codes
        self.index = defaultdict(list)
        for filename, id_key, status_key in (
            ("points.csv", "point_id", "状态"),
            ("triage.csv", "hit_id", "处置"),
        ):
            for line, row in csv_rows(repo / filename):
                key = compact(row["公司"])
                self.index[key].append(
                    (filename, line, row[id_key], row["cell_id"], row[status_key], row)
                )

    def select(self, subject, content="", cell="", broad=False):
        normalized = compact(subject)
        code = self.names.get(normalized, subject)
        company = self.codes.get(code, (subject, 0))[0]
        entries = self.index.get(compact(company), []) or self.index.get(normalized, [])
        cells = {cell.removesuffix("边")} - {"", "ANY"}
        if not cells:
            cells = {key for key, pattern in CELL_PATTERNS.items() if re.search(pattern, content, re.I)}
        selected = [entry for entry in entries if entry[3] in cells]
        if selected:
            selected.sort(key=lambda x: (x[0] != "points.csv", x[1]))
            refs = [anchor(f"现有 {entry[2]}", self.repo / entry[0], entry[1]) for entry in selected[:6]]
            summary = "；".join(
                f"{entry[0]} {entry[2]} / {entry[3]}（{entry[4]}）" for entry in selected[:6]
            )
            return "同主体同叶格的复核候选：" + summary, refs, cells
        if cells:
            return "现有 tree.yaml 叶格候选 " + "、".join(sorted(cells)) + "，同主体旧点待定位", [
                anchor("现有产业树", self.repo / "tree.yaml")
            ], cells
        if broad and entries:
            selected = sorted(entries, key=lambda x: (x[0] != "points.csv", x[1]))[:3]
            return "同主体旧记录，仅供定位，未证实同业务：" + "；".join(
                f"{x[0]} {x[2]} / {x[3]}" for x in selected
            ), [anchor(f"现有 {x[2]}", self.repo / x[0], x[1]) for x in selected], cells
        if code in self.codes:
            return f"corpus/_frozen.csv {code}（主体坐标，具体知识条目待定位）", [
                anchor("现有主体", self.repo / "corpus/_frozen.csv", self.codes[code][1])
            ], cells
        return "UNKNOWN，现有账本无可唯一定位的主体和叶格", [], cells

    def same_anchor(self, subject, url):
        entries = self.index.get(compact(subject), [])
        return [
            (line, point_id, cell)
            for filename, line, point_id, cell, _, row in entries
            if filename == "points.csv" and url in (row.get("锚点URL") or "")
        ]


def review_row(category, key, subject, dates, claim, quote, refs, match, proposal, gap, disposition):
    target, old_refs, _ = match
    return dict(id=stable_id(category, *key), stream="国内", category=category, dates=sorted(set(dates)),
                subject=subject, claim=claim, quote=quote, anchors=refs, target=target,
                target_anchors=old_refs, proposal=proposal, gap=gap, disposition=disposition)


def report_sections(path, day):
    section = None
    declared = {}
    observed = defaultdict(list)
    if not path.is_file():
        return declared, observed
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## "):
            section = next((kind for prefix, kind in SECTIONS.items() if line[3:].startswith(prefix)), None)
            if section:
                count = re.search(r"(?:新增\s*)?(\d+)\s*[份条/]", line)
                if count:
                    declared[section] = {"count": int(count.group(1)), "ref": str(path) + f"#L{number}"}
        if section and line.startswith("- "):
            observed[section].append((day, path, number, line[2:]))
    return declared, observed


def evidence_text(path):
    if not path.is_file():
        return "", None
    # Prefer optical text in a company response over a question, preserving page layout lines.
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    matches = []
    for i, line in enumerate(lines):
        if OPTICAL.search(line):
            lookback = "".join(lines[max(0, i - 5):i + 1])
            response = max(lookback.rfind("回复"), lookback.rfind("答："))
            question = max(lookback.rfind("问题"), lookback.rfind("问："))
            matches.append((response <= question, i))
    if matches:
        _, i = min(matches)
        return "\n".join(lines[max(0, i - 2):i + 3]).strip(), max(0, i - 2) + 1
    return "", None


def read_reports(domestic, combined, cutoff):
    native = {p.stem: p for p in domestic.glob("daily/*.txt") if REPORT_DATE.fullmatch(p.stem)}
    combined_days = {p.stem: p for p in combined.glob("daily/*.md") if REPORT_DATE.fullmatch(p.stem)}
    daily = {}
    observed = defaultdict(list)
    for day in sorted(native.keys() | combined_days.keys()):
        if day > cutoff:
            continue
        path = native.get(day) or combined_days[day]
        declared, entries = report_sections(path, day)
        if not declared:
            continue
        daily[day] = {"file": str(path), "from_combined_only": day not in native, "sections": declared}
        for section, section_rows in entries.items():
            observed[section].extend(section_rows)
    return daily, observed


def collect_documents(domestic, targets, observed, cutoff):
    rows = []
    docs = sorted(domestic.glob("ir/*/*.pdf"))
    state_docs = defaultdict(list)
    for path in docs:
        match = re.match(r"(\d{6})_(\d{4}-\d{2}-\d{2})_(.*)", path.stem)
        if match and match[2] <= cutoff:
            state_docs[(match[1], match[2])].append((path, match[3]))
    unbound_reports = []
    linked = defaultdict(list)
    for day, path, line, entry in observed["投关表"]:
        match = DOCUMENT.fullmatch(entry)
        if not match:
            continue
        subject, published, title = match.groups()
        code = targets.names.get(compact(subject))
        normalized = re.sub(r"[^\w\-.一-龥]", "_", title)
        pool = state_docs[(code, published)]
        matches = [(pdf, name) for pdf, name in pool if name == normalized]
        if not matches:
            matches = [(pdf, name) for pdf, name in pool if name.startswith(normalized)]
        if len(matches) == 1:
            linked[matches[0][0]].append((day, path, line))
        else:
            unbound_reports.append((day, path, line, subject, published, title, len(matches)))
    for (code, published), matches in state_docs.items():
        subject = targets.codes.get(code, (code, 0))[0]
        for pdf, name in matches:
            text = pdf.with_suffix(".pdf.txt")
            quote, quote_line = evidence_text(text)
            date_refs = linked.get(pdf, [])
            refs = [anchor("投关表原件", pdf)]
            if quote_line:
                refs.append(anchor("提取文本定位，需回原 PDF 核对", text, quote_line))
            refs.extend(anchor("日更投关记录", p, line) for _, p, line in date_refs)
            target = targets.select(subject, compact(quote), broad=True)
            proposal = "核对该段的披露主体、产品和阶段，符合原判定口径时补充相应点的带日期证据。"
            gap = "需核对 PDF 页码、问答上下文及主体归属。区分产能规划、客户验证和真实交付。"
            disposition = "待逐条复核" if quote else "仅作线索"
            if not quote:
                proposal = "先从 PDF 定位与光通信或对应叶格有关的发行人陈述，再判断是否补证。"
                gap = "本地文本未定位相关原句。需回读原件查页码、发言人与具体产品或工艺。"
            if code == "002384" and published == "2026-11-02" and text.is_file():
                chip = "公司今年已有小批量光芯片"
                text_lines = text.read_text(encoding="utf-8").split("\n")
                for i, content in enumerate(text_lines):
                    if chip in content:
                        quote = "\n".join(text_lines[i:i + 4]).strip()
                        refs.append(anchor("投关表第 3 问公司回复", text, i + 1))
                        target = targets.select(subject, quote, cell="C1")
                        proposal = "给 P130 补一条独立的外售进展候选。11 月投关称光芯片已有小批量外售，原点是 CW 量产能力，两种口径分别记录。"
                        gap = "回读 PDF 第 3 问，确认小批量外售的芯片类型、客户及数量。原句的光芯片口径暂不能缩成 CW。"
                        break
            if not date_refs:
                gap += "日报未能唯一匹配本件，文件名日期仅为披露日期。"
            row = review_row("投关表", (code, published, name), subject, [d for d, _, _ in date_refs],
                             name, quote, refs, target, proposal, gap, disposition)
            row["publication_date"] = published
            row["date_basis"] = "日报原项" if date_refs else "仅现存状态库，采集日未知"
            rows.append(row)
    for day, path, line, subject, published, title, n in unbound_reports:
        row = review_row(
            "投关表", (subject, published, title), subject, [day], title, "",
            [anchor("日更投关标题", path, line)], targets.select(subject, title, broad=True),
            "找回标题对应的投关原件，再决定是否补充旧点。",
            f"只保留标题，匹配到 {n} 个文件。缺唯一原件和能支持业务主张的页码及引文。", "缺锚点"
        )
        row.update(publication_date=published, date_basis="日报原项，未绑定原件")
        rows.append(row)
    return rows, len(linked), len(unbound_reports)


def qa_content(row):
    return (
        compact(row.get("question")),
        compact(MIRROR_SUFFIX.sub("", row.get("answer") or "")),
        row.get("ask_date") or "",
    )


def qa_identity(row):
    content = qa_content(row)
    if all(content):
        return ("content", *content)
    return _key(row)


def collect_qa(repo, domestic, targets, reported, cutoff):
    rows = []
    parse_errors = []
    counts = Counter()
    recovered_by_fetch = Counter()
    reported_by_subject = defaultdict(list)
    for day, report, number, entry in reported:
        match = QA_TOTAL.fullmatch(entry)
        if match:
            reported_by_subject[compact(match[1])].append(dict(
                date=day, count=int(match[2]), ref=str(report) + f"#L{number}", subject=match[1]
            ))
    for path in sorted(domestic.glob("qa/*/qa.jsonl")):
        code = path.parent.name
        subject = targets.codes.get(code, (code, 0))[0]
        canonical = repo / "corpus/qa" / code / "qa.jsonl"
        base_by_identity = defaultdict(list)
        base_by_storage_key = defaultdict(list)
        for base_line, base in json_lines(canonical, parse_errors):
            item = (base_line, base)
            base_by_identity[qa_identity(base)].append(item)
            base_by_storage_key[_key(base)].append(item)
        delta = defaultdict(list)
        for number, item in json_lines(path, parse_errors):
            counts["snapshot_rows"] += 1
            date = item.get("fetch_date", "")
            if not REPORT_DATE.fullmatch(date) or not BASE_DATE <= date <= cutoff:
                counts["outside_daily_fetch_date_window"] += 1
                continue
            storage_key = _key(item)
            key = qa_identity(item)
            base_matches = base_by_identity[key] + base_by_storage_key[storage_key]
            if any(
                qa_content(old)[:2] == qa_content(item)[:2]
                and (old.get("answer_date") == item.get("answer_date") or not item.get("answer_date"))
                for _, old in base_matches
            ):
                counts["already_in_source_corpus"] += 1
                continue
            if date == BACKFILL and str(item.get("source", "")).startswith("ir.p5w.net"):
                counts["separate_backfill_excluded"] += 1
                continue
            delta[key].append((number, item))
        for key, snapshots in delta.items():
            by_date = defaultdict(list)
            for number, item in snapshots:
                by_date[item.get("answer_date") or ""].append((number, item))
            # An undated variant of the same question and answer adds no independent evidence.
            if "" in by_date and len(by_date) == 2:
                missing_date = by_date.pop("")
                next(iter(by_date.values())).extend(missing_date)
            for answer_date, variants in sorted(by_date.items()):
                number, item = max(variants, key=lambda pair: (
                    bool(pair[1].get("answer_date")), not str(pair[1].get("source", "")).startswith("ir.p5w.net"),
                    pair[1].get("fetch_date", ""), pair[0],
                ))
                counts["snapshot_duplicate_variants"] += len(variants) - 1
                date = item.get("fetch_date", "")
                recovered_by_fetch[date] += 1
                question, answer = item.get("question") or "", item.get("answer") or ""
                refs = [anchor("问答快照原行", path, i) for i, _ in variants]
                base_rows = base_by_identity[key] or base_by_storage_key[_key(item)]
                if base_rows:
                    refs.append(anchor("原知识库的语料版本", canonical, base_rows[0][0]))
                match = targets.select(subject, compact(answer))
                lead_only = not (answer and not item.get("empty") and OPTICAL.search(answer))
                disposition = "仅作线索" if lead_only else ("待逐条复核" if match[2] else "待定位")
                proposal = (
                    "保留问答来源。公司回复没有直接提供可定位的光通信事实，暂缓业务点修改。"
                    if lead_only else
                    "核对公司回复是否明确覆盖同一产品、工序和阶段，再选择补证或修正旧点。"
                )
                gap = "日报没有问答逐条 ID。回查交易所原帖与回复日期，并核对提问与公司回答的边界。"
                if str(item.get("source", "")).startswith("ir.p5w.net"):
                    gap += "当前快照来自全景网，需查对应交易所原帖或发行人正式披露。"
                if not answer_date:
                    gap += "缺回复日期。"
                if base_rows:
                    gap += "原库已有同内容键或同帖 ID，先复核是否只是日期补齐或原帖更正。"
                claim = (question[:210] or answer[:210] or "问答正文为空")
                row = review_row(
                    "问答快照", (code, *key, answer_date), subject, [], claim, answer, refs, match, proposal,
                    gap, disposition,
                )
                row.update(
                    question=question, fetch_date=date, source=item.get("source", ""),
                    publication_date=answer_date, ask_date=item.get("ask_date", ""),
                    original_id=item.get("index_id", ""),
                    date_basis="累计快照最后抓取日，不能确定首次写入或归属哪一期日报",
                )
                rows.append(row)
    counts["reconstructed_snapshot_candidates"] = len(rows)
    coverage = dict(counts=counts, latest_fetch_date_counts=recovered_by_fetch,
                    reported_company_counts=sorted(
                        (item for values in reported_by_subject.values() for item in values),
                        key=lambda x: (x["date"], x["subject"])),
                    jsonl_parse_errors=parse_errors)
    return rows, coverage


def collect_report_items(repo, domestic, targets, observed):
    rows = []
    grouped = defaultdict(list)
    for category in ("公告", "复核触发", "召回候选", "宇宙外补录"):
        pattern = {
            "公告": ANNOUNCEMENT, "复核触发": WATCH, "召回候选": RECALL, "宇宙外补录": DOCUMENT,
        }[category]
        for day, path, number, entry in observed[category]:
            match = pattern.fullmatch(entry)
            if not match:
                continue
            groups = match.groups()
            if category == "公告":
                key = (groups[3],)
            elif category == "复核触发":
                key = (day, *groups)
            elif category == "召回候选" and groups[0] == "汇绿生态" and "150万" in groups[3]:
                key = (groups[0], "一期150万只年产能规划")
            else:
                key = groups
            grouped[(category, key)].append((day, path, number, groups))

    sources = defaultdict(list)
    for text in sorted(domestic.glob("ir/*/*.pdf.txt")):
        sources[text.parent.name].append((text, compact(text.read_text(encoding="utf-8", errors="replace"))))
    for (category, key), observations in sorted(grouped.items()):
        refs = [anchor("日报原项", path, line) for _, path, line, _ in observations]
        dates = [d for d, *_ in observations]
        groups = observations[0][3]
        subject = groups[0]
        extra = {}
        if category == "公告":
            _, published, title, url = groups
            refs.insert(0, anchor("巨潮公告原件入口", url))
            extra["publication_date"] = published
            claim, quote = title, ""
            target = targets.select(subject, title, broad=True)
            if re.search("向特定对象|定增|募集|发行股票|保荐|法律意见|审计报告", title):
                proposal = "核对募集说明书或公告的募投项目。若有可量化的同产品扩产，补时间、规模和项目阶段。"
                gap = "缺正文页码、募投项目是否属于同一光通信产品、资金批准与项目实际进度。"
            elif re.search("收购|重组", title):
                proposal = "核对收购标的及交易阶段。只有标的业务与旧记录有关时才补主体或能力归属。"
                gap = "缺正文页码、交易标的业务、控制权和完成状态。"
            elif re.search("业绩预告|业绩快报", title):
                proposal = "核对是否披露光通信业务的独立口径。仅在口径一致时补有证据的业务变化。"
                gap = "缺正文页码、业务分项与期间口径。"
            else:
                proposal = "核对公告中的具体业务动作，再判断是否能为同主体旧点补证。"
                gap = "缺正文页码、产品或工序归属，以及能支持旧点变化的原句。"
            disposition = "仅作线索"
            prior = targets.same_anchor(subject, url)
            if prior:
                prior_refs = [anchor(f"现有 {point_id}", repo / "points.csv", line)
                              for line, point_id, _ in prior]
                target = ("同一公告已被旧点引用：" + "、".join(f"{p} / {c}" for _, p, c in prior),
                          prior_refs, {c for _, _, c in prior})
                proposal = "先比对旧点已引用的具体段落，只有原件另有新信息才补证。"
                disposition = "已入账核对"
        elif category == "复核触发":
            _, state, cell, claim, quote = groups
            target = targets.select(subject, quote, cell=cell)
            if quote.startswith("http"):
                refs.insert(0, anchor("公告原件入口", quote))
                quote = ""
            proposal = f"复核 {state} 对应的同主体记录。达到原重启条件才提交判定修正。"
            gap = "日报触发是机械匹配。缺可独立核验的证据锚、重启条件的实质变化及前后口径。"
            if claim.startswith("互动易"):
                gap += "日报只留公司计数，没有逐条问答 ID。"
            if subject == "沪硅产业" and cell == "M1":
                proposal = "对照 P196 的 12 英寸 SOI 中试线、客户认证及小批量供应，检查新增材料是否给出硅光用 SOI 批量出货进展。"
                gap += "需同一产品规格、硅光应用、量产或实际交付数量。"
            disposition = "仅作线索"
        elif category == "召回候选":
            _, cell, term, quote = groups
            claim = "机械召回命中 " + "、".join(sorted({x[3][2] for x in observations}))
            target = targets.select(subject, quote, cell=cell, broad=True)
            code = targets.names.get(compact(subject), subject)
            segment = compact(quote)
            hits = [p for p, text in sources.get(code, []) if len(segment) >= 12 and segment in text]
            if len(hits) == 1:
                refs.insert(0, anchor("候选片段定位到唯一投关提取文本", hits[0]))
                refs.insert(0, anchor("投关表原件", hits[0].with_suffix("")))
                gap = "需在原件核对页码、完整主语和上下文。机械命中可能来自提问、客户或子公司。"
                disposition = "待逐条复核"
            else:
                gap = f"现存投关提取文本中有 {len(hits)} 个候选来源。缺唯一原件及段落上下文。"
                disposition = "缺锚点"
            proposal = "先区分发行人自有业务、客户业务与技术名词，再判断是否补充现有叶格。"
            if subject == "汇绿生态" and "150万" in quote:
                target = targets.select("武汉钧恒科技有限公司", quote, cell="MOD1")
                proposal = "给 P039 增补一期产能的带日期候选。原片段涉及一期投产和约 150 万只年产能规划，应分别记录两项口径。"
                gap += "需要核对一期项目主体、达产进度和实际出货量。"
        else:
            _, published, claim = groups
            quote = ""
            extra["publication_date"] = published
            target = targets.select(subject, claim)
            proposal = "确认主体、市场、主营产品和与光通信的关系后，再决定是否进入现有观察名录。"
            gap = "日报仅保留标题。缺原始披露链接及业务正文，还需核对同分类可比主体。"
            disposition = "缺锚点"
        row = review_row(category, key, subject, dates, claim, quote, refs, target, proposal, gap, disposition)
        row.update(date_basis="日报原项", **extra)
        rows.append(row)
    return rows


def collect(repo: Path, state: Path, cutoff: str):
    domestic, combined = state / "domestic", state / "combined"
    names, codes = company_lookup(repo)
    targets = Targets(repo, names, codes)
    daily, observed = read_reports(domestic, combined, cutoff)
    docs, linked, unbound = collect_documents(domestic, targets, observed, cutoff)
    qa, qa_coverage = collect_qa(repo, domestic, targets, observed["问答计数"], cutoff)
    events = collect_report_items(repo, domestic, targets, observed)
    result = {}
    for row in [*docs, *qa, *events]:
        other = result.get(row["id"])
        if other:
            other["dates"] = sorted(set(other["dates"] + row["dates"]))
            other["anchors"].extend(row["anchors"])
        else:
            result[row["id"]] = row

    unlisted = []
    date_observations = Counter(
        (category, day) for category, items in observed.items() for day, *_ in items
    )
    for day, report in daily.items():
        for category, item in report["sections"].items():
            if category == "问答计数":
                continue
            visible = date_observations[category, day]
            if item["count"] > visible:
                unlisted.append(
                    dict(date=day, category=category, declared=item["count"], visible=visible,
                         difference=item["count"] - visible, ref=item["ref"])
                )
    coverage = dict(
        report_days=daily,
        category_counts=Counter(row["category"] for row in result.values()),
        qa=qa_coverage,
        linked_ir_pdfs=linked,
        unmatched_ir_report_items=unbound,
        unlisted_report_items=unlisted,
        qa_count_note=(
            "历史日报仅保留公司与问答计数。状态 qa.jsonl 是累计镜像，抓取时间会被重叠窗口覆盖。"
            "相对当前 corpus 的可定位差集不能逐期抵扣日报计数。"
            "9 月 11 日全景网专项历史回填独立计数，排除出日更候选。"
        ),
        announcement_count_note=(
            "公告是滚动窗口发现，按原公告 URL 去重。保留所有看到它的日报日期，发布日期另列。"
            "日报截断清单计的是未显示的日次观察数，其中可能含滚动重复。"
        ),
    )
    return sorted(result.values(), key=lambda r: (r["category"], r["subject"], r["id"])), coverage
