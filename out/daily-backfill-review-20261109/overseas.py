"""Read saved overseas staging, preserving exact observations and candidate boundaries."""

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

EMPTY_HASH = hashlib.sha256(b"").hexdigest()
TABLES = (
    "disclosure_candidates.csv", "claim_candidates.csv", "event_candidates.csv",
    "evidence_candidates.csv", "dedupe-manifest.csv", "failures.csv",
)
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")

STAGES = {
    "announced": "发布或计划",
    "sampling": "送样",
    "demonstrated": "完成演示",
    "qualifying": "验证中",
    "ramping": "爬坡",
    "not_applicable": "不适用",
}
EVENT_KINDS = {
    "product_stage": "产品阶段",
    "commercial_adoption": "商业采用",
    "capacity_constraint": "产能与卡点",
}
BOILERPLATE = re.compile(
    r"^(?:[\s'“”\"])*(?:all forward[- ]looking statements|forward[- ]looking statements "
    r"(?:are not guarantees|reflect our current estimates|contained in|are based on management)|"
    r"the statements in this (?:press )?release relating to|statements relating to our expectations|"
    r"these risks and uncertainties include|such statements are based on .+current expectations|"
    r"this (?:document|communication|press release) (?:is not (?:intended|a proxy)|does not constitute))"
    r"|\bqualifying for hedge accounting\b",
    re.I,
)
OPTICAL = re.compile(
    r"\b(?:optics?|optical|transceivers?|photonics?|photonic|CPO|LPO|InP|EML|MOCVD|"
    r"coherent|Infinera|photodetectors?|laser|fiber|fibre|lightwave|wafers?|lithography|"
    r"optical[- ]engine)\b",
    re.I,
)

# Existing events have named objects. Match only a specific product/project identifier
# and its registered subject. Generic same-company or same-stage hits are not joins.
PROGRAM_TOKENS = {
    "PRG_LITE_1P6_DEMO": (r"\b2\s*x\s*DR4\b", r"\b1\.6\s*T\b"),
    "PRG_AVGO_TAURUS": (r"\bTaurus\b|\bBCM83640\b",),
    "PRG_MRVL_ARA": (r"\bAra\b", r"\b(?:DSP|1\.6\s*T)\b"),
    "PRG_CIEN_WL6E": (r"\bWaveLogic\s*6\s*Extreme\b|\bWL6e\b",),
    "PRG_MTSI_448G": (r"\b448\s*G\b", r"\b(?:driver|PAM4)\b"),
    "PRG_CRDO_ZEROFLAP": (r"\bZeroFlap\b|\bZero\s+Flap\b",),
    "PRG_NOK_PSE6S": (r"\bPSE[-\s]?6s\b",),
    "PRG_CIEN_VESTA": (r"\bVesta\b", r"\b(?:CPX|CPO|6\.4\s*T|200)\b"),
    "PRG_MTSI_IQE": (r"\bIQE\b", r"\b(?:agreement|investment|supply)\b"),
    "PRG_CRDO_CARDINAL": (r"\bCardinal\b", r"\b(?:DSP|1\.6\s*T)\b"),
    "PRG_CRDO_DUST": (r"\bDustPhotonics\b",),
    "PRG_CIEN_HYPERRAIL": (r"\bHyper[-\s]?Rail\b",),
    "PRG_AXTI_LITE_INP": (r"\b(?:Lumentum|LITE)\b", r"\b(?:InP|indium phosphide)\b"),
    "PRG_GFS_US_SIPHO": (r"\b(?:CHIPS Act|CHIPS and Science Act|CHIPS for America)\b",
                         r"\bsilicon photonics\b"),
    "PRG_TSEM_JP_SIPHO": (r"\b(?:Japan|Uozu)\b", r"\bsilicon photonics\b", r"\b300\s*mm\b"),
    "PRG_VECO_LUMINAPLUS": (r"\bLUMINA\+|\bLUMINA\s*PLUS\b", r"\bEnnostar\b"),
    "PRG_LITE_GREENSBORO_INP": (r"\bGreensboro\b", r"\b(?:InP|indium phosphide)\b"),
    "PRG_GLW_NVDA_OPTICAL": (r"\bNVIDIA\b", r"\bCorning\b", r"\b(?:fiber|optical)\b"),
    "PRG_POET_LUMILENS": (r"\bLumilens\b",),
    "PRG_POET_CELESTIAL": (r"\bCelestial\s+AI\b", r"\b(?:cancel|cancellation|cancelled|canceled)\b"),
    "PRG_COHR_NVDA_20260302": (r"\bNVIDIA\b", r"\b(?:multibillion|multi-billion|capacity rights)\b"),
    "PRG_LITE_NVDA_20260302": (r"\bNVIDIA\b", r"\b(?:multibillion|multi-billion|capacity rights)\b"),
    "PRG_MOLEX_TERAMOUNT": (r"\bTeramount\b",),
}

# Cross-checks of the saved excerpts against the named question or ledger object.
# These narrow the proposed writeback. The original pages still need human review.
EXCERPT_REVIEW = {
    "CC_476EE9561DE3": (
        "calls/themes.csv · T021；calls/events.csv · EV005 可作相干发货对照",
        "把 Nokia 披露的 Telxius BRUSA 海缆 ICE-X 800G ZR+ 演示提议为独立事件。"
        "单独核实标题所述陆地部署，避免与海缆演示或 EV005 的美国客户发货合并。",
        "核对海缆演示日期、距离和配置，以及陆地部署的地区与启用日期。若拟交叉确认，补 Telxius 自己的同对象材料。",
    ),
    "CC_86EB77062155": (
        "calls/themes.csv · T021；calls/events.csv · EV005 可作相干发货对照",
        "本段只支持陆地网络扩容用途。核实全文有无已部署动作再提议增加 Telxius 部署事件。",
        "缺实际启用、装机规模或客户侧证据。能力描述不足以记为已增加容量。",
    ),
    "CC_E21215FC2F43": (
        "calls/watch_entities.csv · WATCH_IQE；calls/events.csv · EV014 仅作另一供应协议对照",
        "单列 IQE 参与 Quintessent 量子点激光器送样的公司主张。采购协议与客户送样应分别审。",
        "确认谁向谁送样、外延/激光器规格、样品何时交付和协议约束。EV014 的对手方是 MACOM。",
    ),
    "CC_5D1051DBCA79": (
        "calls/watch_entities.csv · WATCH_IQE；calls/events.csv · EV014 仅作另一供应协议对照",
        "标题含采购协议与送样两个动作。按全文把签约和送样分开提议，关联其各自锚点。",
        "需要签约段、供货范围及送样方。若要记独立确认，需要 Quintessent 单独披露。",
    ),
    "CC_9194824799D6": (
        "calls/themes.csv · T011；calls/events.csv · EV007（已录 448G/lane 驱动器发布）",
        "将 MACOM 的 3.2T 芯片组按新品发布候选复核。只有确认芯片型号一致，才给 EV007 或其项目补证。",
        "引文只称降低开发和验证工作量。缺具体器件型号、单 lane 速率、客户验证动作及送样状态。",
    ),
    "CC_0B92E6E9B38E": (
        "calls/themes.csv · T010/T017；calls/events.csv · EV024（日本 300mm 硅光目标，须分项目）",
        "把 Tower/NewPhotonics 所称 800G 至 1.6T 光引擎 PIC 已出货与 6.4T NPO 未来量产分成两条。",
        "核对已出货者、PIC 型号、供货平台、数量和地理口径。缺 6.4T 已兑现材料。",
    ),
    "CC_8C950F20E235": (
        "calls/themes.csv · T017；calls/events.csv · EV024（日本 300mm 硅光目标，须分项目）",
        "把 6.4T NPC505 的 2027 年上半年预计量产交付记为待核计划，和当前 800G 至 1.6T PIC 出货分开。",
        "需核 CPX-MSA 合规口径、适用项目及后续实际出货日期或客户收货。",
    ),
    "CC_A09131934AE2": (
        "calls/themes.csv · T013/T017",
        "为 Lumentum/Qualcomm/Corning 的 1060 nm VCSEL 光 D2D 提议加演示配置候选。32 Gb/s NRZ 只记作单通道演示口径。",
        "核实演示是否如期发生、通道数、链路长度、BER 与整链功耗，区分架构设想和实际配置。",
    ),
    "CC_2AD51EC438F5": (
        "calls/themes.csv · T013/T017；research_questions.yaml · TQ008",
        "增加 Wiwynn/GUC/Ayar 的 CPO 系统集成演示候选，注明 GUC ASIC、TeraPHY 光引擎和 SuperNova 光源角色。",
        "核实现场日期、系统配置、测量方式和可重复结果。商业部署另需客户验证及出货证据。",
    ),
    "CC_8BD5010669BF": (
        "calls/themes.csv · T004；research_questions.yaml · TQ005",
        "增加 Cisco 与 NVIDIA 拟开发 400 Gb/s/lane USFP 的技术计划候选，并留待后续与现有接口规范比较。",
        "缺公开规格或 MSA 文件、完成样品、实测互通和可用日期。",
    ),
    "CC_7A7EB3BF6986": (
        "calls/universe.csv · AXTI；calls/events.csv · EV022；calls/themes.csv · T007/T008",
        "把 Tongmei 的 InP 晶圆产能扩张用途记作融资披露中的计划。EV022 的 Lumentum 预留协议另行比对，现有引文不足以认定履约。",
        "缺资金实际到账、装机/稼动数据、新增有效产能及实际出货。需求超过供给是发行人陈述。",
    ),
    "CC_1C9FC05DDFA8": (
        "calls/universe.csv · LWLG；research_questions.yaml · TQ007/TQ013",
        "提议加入 Lightwave Logic 电光聚合物被用于鸿海光模块的演示候选。原文保留说话人属性。",
        "核对展会日期、模块速率及光路配置，补鸿海侧或现场记录。另需客户认证、良率或供货证明才能判断路线服务能力。",
    ),
}


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header in {path}")
        result = []
        while True:
            start = reader.reader.line_num + 1
            row = next(reader, None)
            if row is None:
                return result
            if None in row or None in row.values():
                raise ValueError(f"Invalid row in {path}:{start}")
            result.append((row, f"{path}#L{start}"))


def _table(repo, name):
    return [row for row, _ in _read(repo / "calls" / name)]


def _stable_key(*parts):
    content = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "O-" + hashlib.sha256(content.encode()).hexdigest()[:20]


def _valid_day(value):
    if not DATE_PATTERN.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _version(row):
    fields = ("disclosure_id", "canonical_url", "content_hash", "title", "published_at",
              "publisher_entity_id", "disclosure_type", "content_class", "provenance_class")
    return tuple(row[key] for key in fields)


def _decision_key(disclosure, claim, event, evidence):
    """One approval for the same excerpt and proposition on a moving source page."""
    claimant = tuple(claim[key] for key in ("claimant_entity_id", "claimant_role", "statement_kind"))
    event_key = tuple(event[key] for key in (
        "program_id", "event_category", "lifecycle_stage", "event_status", "primary_subject_id",
        "counterparty_ids", "site_country", "target_market", "policy_jurisdiction",
    )) if event else ()
    evidence_key = (evidence["independence_class"],) if evidence else ()
    source = disclosure["canonical_url"] or disclosure["disclosure_id"]
    quote = " ".join(claim["quote"].split())
    return _stable_key("claim-decision", source, claimant, quote, event_key, evidence_key)


def _keyed(rows, key, day):
    result = {}
    for row, ref in rows:
        if not row.get(key) or row[key] in result:
            raise ValueError(f"Missing or repeated {key} in {day} at {ref}")
        result[row[key]] = (row, ref)
    return result


def _url(value):
    if urlsplit(value).scheme in {"http", "https"} and urlsplit(value).hostname:
        return value
    return ""


def _normal(value):
    return " ".join(value.split()).casefold()


def _anchors(row, refs, position="", url_field="canonical_url"):
    anchors = []
    url = _url(row.get(url_field, ""))
    if url:
        suffix = f" · 采集定位 {position}（待核）" if position else " · 披露页"
        anchors.append({"label": "来源链接" + suffix, "ref": url})
    anchors.extend({"label": label, "ref": ref} for label, ref in sorted(refs.items()))
    return anchors


def _disclosure_targets(disclosure, canonical):
    url = disclosure["canonical_url"]
    content_hash = disclosure["content_hash"]
    targets = []
    for existing in canonical:
        same_url = bool(url and url == existing["canonical_url"])
        same_body = bool(content_hash and content_hash != EMPTY_HASH
                         and content_hash == existing["content_hash"])
        if same_url or same_body:
            reason = "同一URL" if same_url else "同一非空正文哈希"
            targets.append((existing["disclosure_id"], reason))
    return targets


def _entity_target(entity, registry):
    if entity in registry:
        path, name = registry[entity]
        return f"{path} · {entity} {name}（主体索引）"
    return f"旧主体未定位 · {entity or 'UNKNOWN'}"


def _program_targets(subject, title, quote, canonical):
    text = f"{title}\n{quote}"
    return [
        row for row in canonical
        if row["primary_subject_id"] == subject and row["program_id"] in PROGRAM_TOKENS
        and all(re.search(pattern, text, re.I) for pattern in PROGRAM_TOKENS[row["program_id"]])
    ]


def _theme_hint(kind, text):
    hints = []
    if re.search(r"\b(?:CPO|co[- ]packaged optics)\b", text, re.I):
        hints.append("T017 CPO商业化与采用阶段")
    if re.search(r"\b(?:ZR\+?|coherent)\b", text, re.I):
        hints.append("T021 相干光与AI数据中心互联采用阶段")
    if re.search(r"\b1\.6\s*T\b", text, re.I) and re.search(
        r"\b(?:transceiver|pluggable|optical module)s?\b", text, re.I
    ):
        hints.append("T010 1.6T可插拔双架构演示与商业爬坡")
    if kind == "capacity_constraint" and re.search(r"\b(?:InP|indium phosphide)\b", text, re.I):
        hints.append("T007 高速InP激光器制造能力 / T008 扩建InP激光器外延与芯片产能（先区分衬底、外延、芯片）")
    if hints:
        return "；问题候选 calls/themes.csv · " + "、".join(hints)
    return ""


def _registry(repo):
    result = {}
    for name, key, title in (
        ("universe.csv", "company_id", "company_name"),
        ("watch_entities.csv", "entity_id", "entity_name"),
        ("company_candidates.csv", "candidate_id", "entity_name"),
    ):
        for row in _table(repo, name):
            result[row[key]] = (f"calls/{name}", row[title])
    return result


def _claim_row(entry, canonical, claims, events, registry):
    disclosure = entry["disclosure"]
    claim = entry["claim"]
    event = entry["event"]
    evidence = entry["evidence"]
    subject = event["primary_subject_id"] if event else claim["claimant_entity_id"]
    title = disclosure["title"]
    quote = claim["quote"]
    event_kind = event["event_category"] if event else ""
    stage = event["lifecycle_stage"] if event else ""
    observed_stage = STAGES.get(stage, stage or "未生成事件")
    source_targets = _disclosure_targets(disclosure, canonical)
    old_ids = {row_id for row_id, _ in source_targets}
    same_claims = [
        row["event_claim_id"] for row in claims if row["disclosure_id"] in old_ids
        and row["claimant_entity_id"] == claim["claimant_entity_id"]
        and _normal(row["quote"]) == _normal(quote) and quote.strip()
    ]
    named_programs = _program_targets(subject, title, quote, events)
    target = _entity_target(subject, registry)
    if same_claims:
        target += "；同主体、来源及引文的旧主张 calls/event_claims.csv · " + "、".join(same_claims)
    elif source_targets:
        target += "；已见来源 calls/disclosures.csv · " + "、".join(
            f"{row_id}（{reason}）" for row_id, reason in source_targets
        )
    if named_programs:
        target += "；同名对象待比对 calls/events.csv · " + "、".join(
            f'{row["event_id"]}（{row["summary"]}）' for row in named_programs
        )
    elif not same_claims:
        target += "；旧事件条目未定位"
    target += _theme_hint(event_kind, f"{title}\n{quote}")
    statement_kind = claim["statement_kind"]
    variants = list(entry["variants"].values())
    publication_dates = sorted({variant["publication_date"] or "UNKNOWN" for variant in variants})
    date_hint = publication_dates[0] if len(publication_dates) == 1 else "多版本，待核"
    summary = f"{title}｜披露日 {date_hint}"
    if event:
        summary += f"｜{EVENT_KINDS.get(event_kind, event_kind)} · {observed_stage}（原日更提议）"
    proposal = (
        f"对照原文抽取 {subject} 的具体对象、口径和时态。若成立，先以已核锚第一方"
        "主张提议补入 calls/disclosures.csv / calls/event_claims.csv。"
    )
    gap = "回核完整段落、说话人、产品/设施/协议标识和事件日期，区分披露日与实际发生日。"
    if event and evidence:
        proposal += (
            f"同一对象和阶段有据时，以「{observed_stage}」的 asserted 候选另审 "
            "calls/events.csv / calls/event_evidence.csv。"
        )
        if evidence["independence_class"] == "first_party":
            gap += "若拟交叉确认，还需不同来源组的对手方、监管披露或可观察结果。"
    elif event is None:
        gap += "当日没有与该主张闭合的事件证据关系。"
    if named_programs:
        proposal += "核对命名项目、地域、产品代际和日期后，才决定给旧事件补证或新建后续事件。"
    if statement_kind == "forward_looking":
        proposal += "保留计划或预测原时态。"
        gap += "兑现需后续已发生材料。"
    if evidence and stage in {"ramping", "sampling", "qualifying", "demonstrated"}:
        gap += {
            "ramping": "核对爬坡的工厂、产品、期间和已实现量/出货；词语命中不足以成立。",
            "sampling": "核对送样对象、样品规格与交付动作。",
            "qualifying": "核对被验证对象、验证方及进度，区分正在验证和取得认证。",
            "demonstrated": "核对实际演示对象、配置和测试条件。",
        }[stage]

    disposition = "待逐条复核"
    if not claim["anchor"] or not quote.strip() or not _url(disclosure["canonical_url"]):
        disposition = "缺锚点"
        proposal = "先恢复原文地址及段落定位，再复审主张和目标条目。"
    elif same_claims:
        disposition = "已入账核对"
        proposal = "核对旧主张锚点及证据关系，只单独审有据的版本差或新事件。"
    elif BOILERPLATE.search(quote):
        disposition = "仅作线索"
        proposal = "摘录疑似免责、法务或会计用语。先寻找与对象直接对应的正文，当前段落搁置。"
    elif any(key in EXCERPT_REVIEW for key in entry["claim_ids"]):
        reviewed_id = next(key for key in sorted(entry["claim_ids"]) if key in EXCERPT_REVIEW)
        target, proposal, gap = EXCERPT_REVIEW[reviewed_id]
    elif not OPTICAL.search(f"{title}\n{quote}"):
        disposition = "仅作线索"
        proposal = "先确认与光互连、相关器件或产线的直接关系，当前只保留原始披露线索。"
        gap += "缺少可指认的光学对象或供应链作用。"
    elif not named_programs and not source_targets and not _theme_hint(event_kind, f"{title}\n{quote}"):
        disposition = "待定位"

    if len(variants) > 1:
        gap += f"同源同引文提议合并了 {len(variants)} 个采集版本。若原文上下文随版本变化，须按所批版本回读。"
    if len(publication_dates) > 1:
        gap += "历次采集披露日不一致（" + "、".join(publication_dates) + "），须核实原页发布日期。"
    relationships = {v["relationship"] for v in variants if v["relationship"]}
    if len(relationships) > 1:
        gap += "同一段引文历次被标为转述和支持，须回读判定证据关系。"
    for variant in variants:
        variant["dates"] = sorted(variant["dates"])
    return {
        "id": entry["id"], "stream": "海外", "category": "海外主张候选",
        "dates": sorted(entry["dates"]), "subject": subject, "claim": summary, "quote": quote,
        "anchors": _anchors(disclosure, entry["refs"], claim["anchor"]),
        "target": target, "proposal": proposal, "gap": gap, "disposition": disposition,
        "source_disclosure_id": disclosure["disclosure_id"], "source_content_hash": disclosure["content_hash"],
        "source_claim_id": claim["event_claim_id"], "source_anchor": claim["anchor"],
        "source_statement_kind": statement_kind, "source_event_id": event["event_id"] if event else "",
        "source_evidence_id": evidence["evidence_id"] if evidence else "",
        "source_versions": variants,
        "old_event_candidates": [row["event_id"] for row in named_programs],
        "old_claim_matches": same_claims,
    }


def _disclosure_row(entry, canonical, events, registry):
    disclosure = entry["disclosure"]
    subject = disclosure["publisher_entity_id"]
    title = disclosure["title"]
    old_targets = _disclosure_targets(disclosure, canonical)
    named_programs = _program_targets(subject, title, "", events)
    target = _entity_target(subject, registry)
    if old_targets:
        target += "；已见来源 calls/disclosures.csv · " + "、".join(
            f"{row_id}（{reason}）" for row_id, reason in old_targets
        )
    if named_programs:
        target += "；标题同名对象待比对 calls/events.csv · " + "、".join(
            row["event_id"] for row in named_programs
        )
    else:
        target += "；旧事件条目未定位"
    disposition = "已入账核对" if old_targets else "仅作线索"
    proposal = "按标题与原页核实是否有可入档的新增事实。若有，先为具体原文段落建立独立主张。"
    if not _url(disclosure["canonical_url"]) or disclosure["content_hash"] == EMPTY_HASH:
        disposition = "缺锚点"
        proposal = "先定位具体披露并恢复正文。"
    return {
        "id": entry["id"], "stream": "海外", "category": "海外披露线索",
        "dates": sorted(entry["dates"]), "subject": subject, "claim": title,
        "quote": "", "anchors": _anchors(disclosure, entry["refs"]),
        "target": target, "proposal": proposal,
        "gap": "这一正文版本没有观察到可关联的逐段候选。须确认原页是否为正文、正文日期、对象及支持该主张的具体段落。",
        "disposition": disposition, "source_disclosure_id": disclosure["disclosure_id"],
        "source_content_hash": disclosure["content_hash"],
    }


def _duplicate_row(entry, canonical):
    row = entry["row"]
    targets = [
        item["disclosure_id"] for item in canonical
        if item["disclosure_id"] == row["target_id"] or (
            row["content_hash"] and row["content_hash"] != EMPTY_HASH
            and item["content_hash"] == row["content_hash"]
        ) or item["canonical_url"] == row["item_url"]
    ]
    if targets:
        disposition = "已入账核对"
        target = "calls/disclosures.csv · " + "、".join(targets)
        proposal = "比对原文版本与已入账段落，重刊只归同源。"
        gap = "若页面同 URL 有实质更新，需单列更新段与版本日期。"
    elif row["content_hash"] == EMPTY_HASH:
        disposition = "缺锚点"
        target = "旧披露条目未定位 · 空正文哈希"
        proposal = "恢复该页面的独立正文，再判断是否重刊或新披露。"
        gap = "原采集以空正文哈希判重复。缺少正文，无法据此确认两个页面相同。"
    else:
        disposition = "仅作线索"
        target = f"同源目标待核 · {row['target_id'] or 'UNKNOWN'}"
        proposal = "核对所指候选的源版本。若正文一致，仅保留重刊来源。"
        gap = "尚未通过正式披露ID、同 URL 或非空正文哈希定位到旧账本。"
    return {
        "id": entry["id"], "stream": "海外", "category": "海外源去重记录",
        "dates": sorted(entry["dates"]), "subject": row["endpoint_id"],
        "claim": f"原采集标记 {row['decision']}",
        "quote": "", "anchors": _anchors(row, entry["refs"], url_field="item_url"),
        "target": target, "proposal": proposal, "gap": gap, "disposition": disposition,
    }


def collect(repo: Path, state: Path, cutoff: str):
    """Return deduplicated review rows and counted overseas input coverage."""
    overseas = state / "overseas"
    canonical = _table(repo, "disclosures.csv")
    old_claims = _table(repo, "event_claims.csv")
    old_events = _table(repo, "events.csv")
    registry = _registry(repo)
    disclosures, claim_groups, duplicates = {}, {}, {}
    full_claim_versions = set()
    evidence_versions, event_versions = set(), set()
    per_day = {}
    claim_observations = Counter()
    captured_claim_ids, captured_event_ids, captured_evidence_ids = set(), set(), set()
    for folder in sorted((overseas / "staging").iterdir()):
        day = folder.name
        if not folder.is_dir() or not _valid_day(day) or day > cutoff:
            continue
        files = {name: folder / name for name in TABLES}
        missing = [name for name, path in files.items() if not path.is_file()]
        tables = {name: _read(path) if path.is_file() else [] for name, path in files.items()}
        disc = _keyed(tables["disclosure_candidates.csv"], "disclosure_id", day)
        claims = _keyed(tables["claim_candidates.csv"], "event_claim_id", day)
        events = _keyed(tables["event_candidates.csv"], "event_id", day)
        captured_claim_ids.update(claims)
        captured_event_ids.update(events)
        links = defaultdict(list)
        for row, ref in tables["evidence_candidates.csv"]:
            evidence_versions.add(tuple(row.items()))
            captured_evidence_ids.add(row["evidence_id"])
            if row["event_claim_id"] not in claims or row["event_id"] not in events:
                raise ValueError(f"Unresolved historical evidence link at {ref}")
            links[row["event_claim_id"]].append((row, ref))
        event_versions.update(tuple(row.items()) for row, _ in events.values())
        failure_counts = Counter(row["failure_type"] for row, _ in tables["failures.csv"])
        for row, ref in disc.values():
            key = _version(row)
            entry = disclosures.setdefault(key, {
                "id": _stable_key("disclosure", key), "disclosure": row,
                "dates": set(), "refs": {}, "has_claim": False,
            })
            entry["dates"].add(day)
            entry["refs"][f"{day} · 披露候选行"] = ref

        for claim_id, (claim, claim_ref) in claims.items():
            claim_observations[claim_id] += 1
            if claim["disclosure_id"] not in disc:
                raise ValueError(f"Unresolved historical disclosure at {claim_ref}")
            disclosure, disclosure_ref = disc[claim["disclosure_id"]]
            version = _version(disclosure)
            disclosures[version]["has_claim"] = True
            for evidence, evidence_ref in links.get(claim_id, [(None, None)]):
                event, event_ref = events[evidence["event_id"]] if evidence else (None, None)
                variant_key = _stable_key("claim-version", version, claim, event, evidence)
                full_claim_versions.add(variant_key)
                stable_id = _decision_key(disclosure, claim, event, evidence)
                entry = claim_groups.setdefault(stable_id, {
                    "id": stable_id, "dates": set(), "refs": {}, "claim": claim,
                    "disclosure": disclosure, "event": event, "evidence": evidence,
                    "variants": {}, "claim_ids": set(),
                })
                entry["dates"].add(day)
                entry["claim_ids"].add(claim_id)
                variant = entry["variants"].setdefault(variant_key, {
                    "disclosure_id": disclosure["disclosure_id"],
                    "content_hash": disclosure["content_hash"],
                    "publication_date": disclosure["published_at"],
                    "claim_id": claim_id, "anchor": claim["anchor"],
                    "event_id": event["event_id"] if event else "",
                    "event_date": event["occurred_start"] if event else "",
                    "evidence_id": evidence["evidence_id"] if evidence else "",
                    "relationship": evidence["relationship"] if evidence else "",
                    "dates": set(),
                })
                variant["dates"].add(day)
                prefix = f"{day} · {claim_id}"
                if evidence:
                    prefix += f"/{evidence['evidence_id']}"
                entry["refs"].update({
                    f"{prefix} 主张候选行": claim_ref,
                    f"{prefix} 披露候选行": disclosure_ref,
                })
                if event_ref:
                    entry["refs"][f"{prefix} 事件候选行"] = event_ref
                    entry["refs"][f"{prefix} 证据候选行"] = evidence_ref

        linked_events = {r["event_id"] for r, _ in tables["evidence_candidates.csv"]}
        if set(events) - linked_events:
            raise ValueError(f"Unlinked historical events in {day}: {sorted(set(events) - linked_events)}")

        for row, ref in tables["dedupe-manifest.csv"]:
            if row["decision"] == "new_disclosure_candidate":
                continue
            identity = {key: value for key, value in row.items() if key != "run_date"}
            stable_id = _stable_key("source-decision", identity)
            entry = duplicates.setdefault(stable_id, {
                "id": stable_id, "row": row, "dates": set(), "refs": {},
            })
            entry["dates"].add(day)
            entry["refs"][f"{day} · 去重记录行"] = ref

        per_day[day] = {
            "missing_tables": missing,
            "disclosure_rows": len(disc),
            "claim_rows": len(claims),
            "event_rows": len(events),
            "evidence_rows": len(tables["evidence_candidates.csv"]),
            "dedupe_rows": len(tables["dedupe-manifest.csv"]),
            "failure_rows": sum(failure_counts.values()),
            "failure_types": dict(sorted(failure_counts.items())),
            "unlinked_claim_rows": len(set(claims) - set(links)),
        }

    reports = sorted(
        path.stem for path in (overseas / "daily").glob("*.txt")
        if _valid_day(path.stem) and path.stem <= cutoff
    )
    rows = [_claim_row(e, canonical, old_claims, old_events, registry) for e in claim_groups.values()]
    rows.extend(
        _disclosure_row(e, canonical, old_events, registry)
        for e in disclosures.values() if not e["has_claim"]
    )
    rows.extend(_duplicate_row(e, canonical) for e in duplicates.values())
    rows.sort(key=lambda row: (row["dates"][0], row["category"], row["subject"], row["id"]))
    counts = Counter(row["category"] for row in rows)
    coverage = {
        "staging_dates": sorted(per_day), "report_dates": reports,
        "report_only_dates": sorted(set(reports) - set(per_day)),
        "staging_only_dates": sorted(set(per_day) - set(reports)),
        "per_day": per_day,
        "disclosure_observations": sum(len(e["dates"]) for e in disclosures.values()),
        "disclosure_versions": len(disclosures),
        "distinct_disclosure_ids": len({e["disclosure"]["disclosure_id"] for e in disclosures.values()}),
        "disclosure_versions_with_claims": sum(e["has_claim"] for e in disclosures.values()),
        "claim_observations": sum(claim_observations.values()),
        "distinct_claim_ids": len(captured_claim_ids),
        "claim_evidence_versions": len(full_claim_versions),
        "claim_decisions": len(claim_groups),
        "distinct_event_ids": len(captured_event_ids),
        "distinct_event_versions": len(event_versions),
        "distinct_evidence_ids": len(captured_evidence_ids),
        "distinct_evidence_versions": len(evidence_versions),
        "review_rows_by_category": dict(counts),
        "source_decision_observations": sum(len(e["dates"]) for e in duplicates.values()),
        "failure_observations": sum(day["failure_rows"] for day in per_day.values()),
        "note": "同日先关联披露、主张和事件。相同来源页、引文、主张及事件判定只形成一个复核决定，保留全部采集版本；不同主张、事件或证据属性保留独立决定。披露日期不作为事件实发日期。",
    }
    return rows, coverage
