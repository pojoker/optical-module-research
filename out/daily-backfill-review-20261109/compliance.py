"""Topic labels and evidence requirements for Gemini's regulatory leads."""
import re

RULES = [
    ('FCC / 美国准入',
     r'FCC|covered\s+list|联邦公报|65\s*%[^。；]{0,16}(?:物料|含量|本土)|S\.\s*5548|3\.2T[^。；]{0,28}(?:豁免|管制|限制|情景)|情景推演[^。；]{0,18}(?:法规|法令)',
     '核对文件编号、发布日期、程序阶段、设备适用范围。区分议程、提案、最终规则、清单与研报情景。',
     'FCC 案卷、决议或清单原件及有效日期。涉及国会提案时另取法案编号、版本及议事状态。'),
    ('美国出口管制',
     r'\b(?:BIS|EAR|FDPR|ECCN)\b|实体清单|外国直接产品|出口管制|转口合规|出口许可',
     '按法域、物项、目的地和最终用户核实受控范围，并区分芯片、测试设备与光模块整机。',
     '主管机关原文、适用分类及条款、规则版本、目的地和最终用途。'),
    ('原产地 / 关税',
     r'原产地|实质性(?:转变|改变|转型)|substantial\s+transformation|\bCBP\b|section\s+301|关税|经贸休战',
     '把工厂工序、产品原产地认定、归类和适用税率分开记录。',
     '具体型号或批次的物料和工序流、HS/HTSUS 编码及适用时点。涉及美国原产地裁定时需核对同产品的 CBP 裁定及事实条件。'),
    ('中国两用物项',
     r'两用物项|两用镜片|两用光学',
     '核对受控物项的技术门槛与个案对象，标明许可要求适用的范围。',
     '中国主管部门清单、条例与版本，产品参数、用途以及诉讼或处罚文号。'),
    ('欧盟能效',
     r'\bEED\b|欧盟[^。；]{0,15}(?:能效|碳足迹)|数据中心[^。；]{0,14}PUE',
     '分开申报指标、适用主体和采购影响，注明法域和报告期。',
     '欧盟指令、实施文件或成员国规则的条款、日期、指标和规模门槛。采购影响另需采购或企业披露。'),
    ('ITC 337 / 知识产权',
     r'(?:USITC|ITC|Section)\s*337|337[- ]TA|337\s*调查|专利诉讼',
     '把调查启动、裁决、救济及涉案产品逐项记载。',
     'USITC 调查编号、立案或裁决原文、涉案产品及最终处置。'),
    ('其他合规 / 地缘政策',
     r'合规|贸易禁令|监管(?:风险|政策|限制|动向|环境)|(?:正式|官方)法(?:规|令)|出口限制',
     '先拆清政策、企业披露与评论中的推断，标注各自适用对象和时点。',
     '可定位的法规或主管机关文号和原文。若是企业能力或客户要求，需发行人或客户原始披露。'),
]


def matches(text):
    specific = [r for r in RULES[:-1] if re.search(r[1], text, re.I)]
    if specific:
        # Generic export-control wording in a PRC-specific paragraph should not
        # become a second US label without a US identifier.
        if any(r[0]=='中国两用物项' for r in specific) and not re.search(r'\b(?:BIS|EAR|FDPR|ECCN)\b|美国',text,re.I):
            specific = [r for r in specific if r[0]!='美国出口管制']
        return specific
    return [RULES[-1]] if re.search(RULES[-1][1], text, re.I) else []


def apply(row, topics, entry_date):
    row.update(
        stream='Gemini 合规',
        category='合规日更' if entry_date else '合规背景（无纪要日期）',
        topics=[r[0] for r in topics],
        target='UNKNOWN · 尚未定位到同法域、同条款或同一产品个案的旧问题或账本条目',
        target_anchors=[],
        proposal=' '.join(r[2] for r in topics),
        gap='Gemini 汇编仅提供线索。'+' '.join(r[3] for r in topics),
    )
