#!/usr/bin/env python3
"""Build the v4.4 challenge-adjudicated report from the immutable v4.3 ledger.

This script changes only decisions that are supported by the fixed artifacts or
by a rule which is applied symmetrically to all five tools.  It also retires the
old mechanical propagation diagnostic from the active rankings and publishes a
non-statistical reviewer-resolution envelope for the two remaining rankings.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TOOLS = ["豆包", "千问", "Qoder", "WorkBuddy", "ZhikunCode"]
KINDS = ["excel", "word", "ppt", "image", "ink", "html"]
ASSESSMENT_CLASSES_SENSITIVE = {"mixed_anchored_judgment", "expert_judgment"}
# A definition is called fully mechanical only when the score is produced from
# retained atomic subtests for every fixed artifact to which it applies.  A
# one-off checklist for one tool does not turn the same criterion for the other
# four tools into a mechanical measurement.
FULLY_ATOMIZED_MECHANICAL_CRITERIA = {
    "criterion:excel:native-open",
    "criterion:excel:native-charts",
    "criterion:word:native-open",
    "criterion:word:retrieval-expression",
    "criterion:ppt:native-open-slideshow",
    "criterion:ppt:chart-data-editing",
}
HTML_POINTS = {
    "artifact:doubao:html": {"basic": 8.5, "analysis": 3.0, "integrity": 1.0},
    "artifact:qianwen:html": {"basic": 9.0, "analysis": 0.0, "integrity": 2.0},
    "artifact:qoder:html": {"basic": 9.0, "analysis": 0.0, "integrity": 2.0},
    "artifact:workbuddy:html": {"basic": 9.0, "analysis": 0.0, "integrity": 1.0},
    "artifact:zhikuncode:html": {"basic": 9.0, "analysis": 4.0, "integrity": 1.0},
}

HTML_OBSERVATIONS = {
    "artifact:doubao:html": {
        "basic": "页内导航与4个分析视图按钮可用；返回顶部按钮点击后未回到顶部，因此基础功能8.5/9。",
        "analysis": "四个分析视图能切换研究视角，取得3/4；未达到满分不代表缺少指定控件。",
        "integrity": "主要控件可键盘访问，但返回顶部控件存在假动作，取得1/2。",
    },
    "artifact:qianwen:html": {
        "basic": "8/8页内导航和8/8图表悬浮提示均通过，基础功能9/9。",
        "analysis": "没有改变筛选条件、比较口径或分析视图的增益控件，分析增益0/4；原Prompt没有指定必须采用哪一种控件。",
        "integrity": "现有导航可键盘访问且没有发现伪交互，取得2/2。",
    },
    "artifact:qoder:html": {
        "basic": "桌面端11/11导航与14/14图表提示均工作，现有控件真实有效，基础功能9/9。",
        "analysis": "没有改变筛选条件、比较口径或分析视图的增益控件，分析增益0/4；原Prompt没有指定必须采用哪一种控件。",
        "integrity": "桌面现有导航可键盘访问且没有发现伪交互，取得2/2；窄屏导航消失只在响应式维度计分。",
    },
    "artifact:workbuddy:html": {
        "basic": "9/9页内导航和8/8图表均工作，基础功能9/9。",
        "analysis": "没有改变筛选条件、比较口径或分析视图的增益控件，分析增益0/4。",
        "integrity": "优势卡使用可点击光标但点击无状态变化，且不能键盘聚焦，取得1/2。",
    },
    "artifact:zhikuncode:html": {
        "basic": "9/9导航、图表提示、折叠和返回顶部等鼠标操作均通过，基础功能9/9。",
        "analysis": "3组图表切换及12项折叠提供实质分析增益，取得4/4。",
        "integrity": "12个折叠标题不进入Tab顺序，键盘等效性未满，取得1/2。",
    },
}

HTML_EVIDENCE = {
    "artifact:doubao:html": ["evidence:native:972bb589875379423e", "evidence:native:d99f892a462d4dabba"],
    "artifact:qianwen:html": ["evidence:native:2ffe96da7a25f0dd7a", "evidence:native:7ae055c6e38ceb089b"],
    "artifact:qoder:html": ["evidence:native:bb4c8cb21b106e4c7b", "evidence:native:e12717d5cf1c6e2df9"],
    "artifact:workbuddy:html": ["evidence:native:71812293d4c55de983", "evidence:native:f4fac7a26ab602ceb5"],
    "artifact:zhikuncode:html": ["evidence:native:9db2c2e07ac00091b3", "evidence:native:82ad486ef4240966d7"],
}

PROMPTS = [
    ("Excel分析底稿", "请以2026年8月30日为资料截止时间，优先使用上海证券交易所披露的招股说明书、上市公告和宇树科技官方公开资料，对宇树科技的经营与财务表现进行分析，并生成一份可编辑的Excel分析底稿。请至少保留资料来源、原始数据、核心计算、趋势图表和分析结论；统一单位与报告期口径，不得把预测数据写成已经发生的事实。除文件外，请简要说明你的分析步骤和仍需人工核验的内容。"),
    ("Word公司研究报告", "基于刚才已经核验并写入Excel的数据和分析，生成一份可编辑的Word公司研究报告。不要新增无法追溯的数字；正文请讲清主营业务与产品结构、收入与盈利变化、研发投入、竞争优势、增长变量和主要风险，并在文末保留来源。"),
    ("PowerPoint内部汇报", "继续沿用前面Excel和Word中的数据、口径与核心判断，将内容压缩成一份适合内部汇报的可编辑PPT。每页只表达一个核心观点，重要图表优先复用已经核验的数据，并在页脚保留必要来源。我还希望PPT专业美观漂亮，效果惊艳高大上，图文并茂。"),
    ("普通信息图", "帮我生成一张图，要求是将前面资料里重点有价值的信息，浓缩到这一张图里，信息必须准确，排版必须精美高端专业精致，出版物级别，要用在给投资人汇报这种专业场景，不能有错。"),
    ("水墨信息图", "将前面生成的图片，调整为一张水墨浪漫中国风的风格，要极尽浪漫主义，但内容需要是正确的。"),
    ("交互HTML", "提取前面excel、word、ppt的全部重要有价值信息，帮我生成可交互式单一html文件，可联网访问即可，技术不限制，越酷炫越好，内容要准确。"),
]

SCREENSHOTS = {
    "ZhikunCode": ("zhikuncode-tool-self-response-display.webp", "7498eeda9ff987405d5cc3847365832a00bee04ec185d56bda79c59ab88613aa"),
    "豆包": ("doubao-tool-self-response-display.webp", "65be7ccc806af5c2d8ccc41e0286d217ed2d583f9f0cb0fab899e1dfa359fece"),
    "WorkBuddy": ("workbuddy-tool-self-response-display.webp", "53efd366e710aca6d6ef0c75101a8b9cd8e96fdebf58bfad35742413d167a180"),
    "Qoder": ("qoder-tool-self-response-display.webp", "0d2229277689142c5e8e66bcbbfa78bbebb10a4599a76829ce5231a25467ad6a"),
    "千问": ("qianwen-tool-self-response-display.webp", "ff035be730682830c1184bd923742af0060dff85b1877ccddf5d0dba0acfb1a8"),
}
ORIGINAL_SCREENSHOTS = {
    "ZhikunCode": ("zhikuncode-tool-self-response.png", "179ea05fda9943f956f93cb7a2de29593e698ca12c98746c6afb33037426eb85"),
    "豆包": ("doubao-tool-self-response.png", "d035062e3461746b197a99683348d0dc5578bf77d68e1cec8a80d29cde97bc40"),
    "WorkBuddy": ("workbuddy-tool-self-response.png", "e0099f776a5841c54c32b9dfe2c3ff4b3dad0b8d7adc00a7bbaba729354eac5f"),
    "Qoder": ("qoder-tool-self-response.png", "fee84fdf271c44b931c67ef4500e4a43d32001200ffd03333584aa7122b24e2d"),
    "千问": ("qianwen-tool-self-response.png", "d8ac86663dce4940eaec675e901945614a62b4abae2dbea40498159f213630e1"),
}


def rounded(value: float, digits: int = 2) -> float:
    return round(float(value) + 1e-12, digits)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def definitions(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for rows in report["criteriaDefinitions"].values() for row in rows}


def criterion(report: dict[str, Any], artifact_id: str, suffix: str) -> dict[str, Any]:
    return next(row for row in report["scores"]["artifacts"][artifact_id]["criterionScores"] if row["criterionId"].endswith(f":{suffix}"))


def finding(report: dict[str, Any], finding_id: str) -> dict[str, Any]:
    return next(row for row in report["findings"] if row["id"] == finding_id)


def stable_impact_id(value: str) -> str:
    return "impact:" + value.replace(":", "-").replace("/", "-")


def set_criterion(report: dict[str, Any], artifact_id: str, suffix: str, earned: float, *, basis: str, finding_ids: list[str], subitems: list[dict[str, Any]] | None = None) -> None:
    row = criterion(report, artifact_id, suffix)
    weight = definitions(report)[row["criterionId"]]["weight"]
    row["weighted"] = rounded(earned)
    row["rating0To5"] = rounded(earned / weight * 5, 6)
    row["basis"] = basis
    row["findingIds"] = finding_ids
    row["adjudicationVersion"] = "4.4"
    if subitems is not None:
        row["subitemScores"] = subitems


def retire_finding(report: dict[str, Any], finding_id: str, reason: str) -> None:
    row = finding(report, finding_id)
    row.update({
        "deducted": False,
        "severity": "info",
        "deliveryGateRequest": None,
        "terminalRiskCode": "G0",
        "gate": "G0",
        "adjudicationStatus": "superseded_by_v44",
        "scoreTreatmentStatus": "observation_only",
        "interpretation": reason,
    })


def apply_score_decisions(report: dict[str, Any]) -> None:
    # WorkBuddy Excel: two objections were substantiated by the fixed workbook.
    set_criterion(
        report, "artifact:workbuddy:excel", "external-facts", 24.0,
        basis=(
            "32项核心事实基准抽查显示主要方向与量级可用；保留的差异集中在旧申报稿精确尾数与明确标为约数的值。"
            "2025年2.78亿元归母与2.88亿元含少数股东已在固定工作簿中明确区分，不再作为未区分错误扣分。得24/30。"
        ),
        finding_ids=["WORKBUDDY-003"],
    )
    set_criterion(
        report, "artifact:workbuddy:excel", "sources", 3.2,
        basis=(
            "资料来源表列有7项名称、发行方、期间、链接栏及核验提示；但两项A级记录未保留报告级直链、页码或表号，"
            "且内部备注显示数据库/媒体转引并混入截止日后期间。按固定终稿内可追溯交付质量得3.2/8；不推断来源绝对不存在。"
        ),
        finding_ids=["WORKBUDDY-001", "WORKBUDDY-005"],
    )
    row = finding(report, "WORKBUDDY-003")
    row.update({
        "severity": "minor",
        "summary": "部分2024年数据沿用旧申报稿精确尾数，另有若干明确约数；2025年2.78亿元归母与2.88亿元含少数股东已在工作簿中清楚区分。",
        "observation": (
            "原始数据-财务!E3:E6保留2024年收入39,237.06、归母9,450.18、扣非7,750，"
            "与正式披露39,277.07、9,547.47、7,847.65存在约0.10%—1.24%差异；"
            "F4=27,800、F5=28,800，说明与口径!B12明确分别标为归母与含少数股东并提示待核验。"
        ),
        "interpretation": "只对可定位的旧稿尾差和约数精度评价；撤销‘2.78/2.88亿元未区分或无法回溯’的旧判断。",
        "causeStatus": "partially_confirmed_after_challenge",
        "falsificationCriteria": "以同一SHA工作簿及正式披露逐项证明上述旧稿尾差不存在，或证明这些数值未用于任何原始数据、计算、图表或结论。",
        "adjudicationStatus": "partially_upheld_and_narrowed",
        "challengeIds": ["CH-WB-FACT-278-288"],
    })
    row = finding(report, "WORKBUDDY-004")
    row.update({
        "severity": "minor",
        "criterionId": "criterion:excel:period-unit-prediction",
        "summary": "51.07%、41.05%和43.06%的算术分母是总营业收入，数值本身可复算；问题仅在区域标题写‘主营业务收入结构’，与实际分母范围不一致。",
        "observation": (
            "原始数据-业务区域含‘其他业务’并以总营业收入169,926.93万元为分母，所得51.07%、41.05%、43.06%算术正确；"
            "若改用主营业务收入167,611.09万元，则分别为51.78%、41.62%、43.65%。"
        ),
        "interpretation": "改定性为标题/口径标签不一致，不再称为错误数字或错误分母；同一口径维度已因更实质的预测语态问题扣分，本项不追加独立分值损失。",
        "causeStatus": "confirmed_label_denominator_scope_mismatch",
        "deducted": False,
        "scoreTreatmentStatus": "recorded_without_incremental_loss_same_criterion",
        "adjudicationStatus": "partially_upheld_and_reclassified",
        "challengeIds": ["CH-WB-DENOMINATOR-LABEL"],
    })

    # Qoder image: one layout root is scored only in readability.
    set_criterion(report, "artifact:qoder:image", "hierarchy-composition", 15.0,
                  basis="整体分区、叙事顺序与视觉层级清楚；标题叠印和下沿裁切只在100%可读性维度计分，避免同根重复扣分。",
                  finding_ids=[])
    set_criterion(report, "artifact:qoder:image", "readability-100pct", 10.5,
                  basis=(
                      "核心数字大多仍可读。逐标签表的9个预设区域均记录‘存在/可读/裁切/叠印’状态："
                      "Z2完整通过，Z1、Z3—Z6标题叠印，Z7—Z8局部裁切，Z9在适应窗口时字号过小。"
                      "按公开状态映射合计10.5/15；映射本身属锚定式混合判断，不冒充纯机械测量。"
                  ),
                  finding_ids=["Qoder-image-02"],
                  subitems=[
                      {"id": "Z1", "label": "上排左图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 1.25, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "75%"},
                      {"id": "Z2", "label": "上排中图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 5 / 3, "expected": "存在、可读、未裁切且无叠印", "actual": "存在且可读；未见裁切或叠印", "status": "pass", "statusCredit": "100%"},
                      {"id": "Z3", "label": "上排右图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 1.25, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "75%"},
                      {"id": "Z4", "label": "下排左图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 1.25, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "75%"},
                      {"id": "Z5", "label": "下排中图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 1.25, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "75%"},
                      {"id": "Z6", "label": "下排右图标题/副标题", "maxPoints": 5 / 3, "earnedPoints": 1.25, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "75%"},
                      {"id": "Z7", "label": "下排左图横轴/底栏边界", "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；局部裁切", "status": "partial_crop", "statusCredit": "60%"},
                      {"id": "Z8", "label": "下排中图横轴/底栏边界", "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；局部裁切", "status": "partial_crop", "statusCredit": "60%"},
                      {"id": "Z9", "label": "页脚来源与最小文字", "maxPoints": 5 / 3, "earnedPoints": 7 / 12, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；适应窗口时过小", "status": "too_small_when_fit", "statusCredit": "35%"},
                  ])
    criterion(report, "artifact:qoder:image", "readability-100pct").update({
        "subitemScoreFormula": "9区等权，每区5/3分；通过100%，叠印75%，局部裁切60%，适应窗口时过小35%。合计10.5/15。",
        "subitemScoringNature": "anchored_status_mapping_mixed_judgment",
        "checklistSource": {
            "path": "/Users/guoqingtao/Desktop/AI办公评测/codex/work/native_audit_v4/logs/qoder_png_layout_checklist.json",
            "sha256": "8d069a3a35b21a069f239822afd32422c02c1dc12a65002c91d91bcff2687f05",
            "kind": "ordinary",
        },
    })
    set_criterion(report, "artifact:qoder:image", "investor-visual", 10.0,
                  basis="配色、信息取舍与投资人汇报语境完整；同一叠印/裁切根因已在可读性计分，本维度不再重复扣分。",
                  finding_ids=[])

    # Qoder ink: layout preservation is not itself a defect.  Style intensity
    # and inherited/new legibility are scored in their own primary dimensions.
    set_criterion(report, "artifact:qoder:ink", "hierarchy-readability", 9.0,
                  basis=(
                      "核心数字可辨。逐标签表显示Z1—Z6标题叠印，Z7—Z8底栏边界侵入，"
                      "Z9来源区低对比且适应窗口时字号过小；按公开状态映射合计9/15。"
                      "该映射属锚定式混合判断；同一布局根因不在构图和完成度重复扣分。"
                  ),
                  finding_ids=["Qoder-ink-02"],
                  subitems=[
                      *[{"id": f"Z{index}", "label": label, "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；标题叠印", "status": "overlap", "statusCredit": "60%"} for index, label in enumerate([
                          "上排左图标题/副标题", "上排中图标题/副标题", "上排右图标题/副标题",
                          "下排左图标题/副标题", "下排中图标题/副标题", "下排右图标题/副标题",
                      ], 1)],
                      {"id": "Z7", "label": "下排左图横轴/底栏边界", "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；底栏边界侵入", "status": "footer_intrusion", "statusCredit": "60%"},
                      {"id": "Z8", "label": "下排中图横轴/底栏边界", "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；底栏边界侵入", "status": "footer_intrusion", "statusCredit": "60%"},
                      {"id": "Z9", "label": "页脚来源与最小文字", "maxPoints": 5 / 3, "earnedPoints": 1.0, "expected": "存在、可读、未裁切且无叠印", "actual": "存在；低对比且适应窗口时过小", "status": "low_contrast_too_small_when_fit", "statusCredit": "60%"},
                  ])
    criterion(report, "artifact:qoder:ink", "hierarchy-readability").update({
        "subitemScoreFormula": "9区等权，每区5/3分；本件9区局部缺陷均按60%信息保留度计分，合计9/15。",
        "subitemScoringNature": "anchored_status_mapping_mixed_judgment",
        "checklistSource": {
            "path": "/Users/guoqingtao/Desktop/AI办公评测/codex/work/native_audit_v4/logs/qoder_png_layout_checklist.json",
            "sha256": "8d069a3a35b21a069f239822afd32422c02c1dc12a65002c91d91bcff2687f05",
            "kind": "ink",
        },
    })
    set_criterion(report, "artifact:qoder:ink", "ink-romantic-style", 16.0,
                  basis="宣纸纹理、书法、朱砂印章和山形完成明确水墨转换；保留普通版几何用于内容一致性不作负项。图表网格仍占主导，‘极尽浪漫主义’的叙事张力尚非满分，得16/20。",
                  finding_ids=["Qoder-ink-03"])
    set_criterion(report, "artifact:qoder:ink", "professional-composition", 15.0,
                  basis="整体栅格、留白和色彩秩序完整；同一文字叠印根因已在层级与可读性维度计分，本维度不重复扣分。",
                  finding_ids=[])
    set_criterion(report, "artifact:qoder:ink", "output-finish", 5.0,
                  basis="PNG分辨率、画布和导出完整；同一叠印/裁切根因已在层级与可读性维度计分，本维度不重复扣分。",
                  finding_ids=[])
    row = finding(report, "Qoder-ink-03")
    row.update({
        "severity": "minor",
        "summary": "水墨转换要素明确，但数据图表网格仍主导画面，浪漫主义叙事张力未达该项满分。",
        "observation": "可见宣纸纹理、书法、朱砂印章、山形与低饱和配色；版面仍以六块数据图表为主体。",
        "interpretation": "与普通图共用几何布局是内容保持手段，本身不构成缺陷；仅评价最终风格强度与原Prompt‘极尽浪漫主义’的符合程度。",
        "deliveryGateRequest": None,
        "terminalRiskCode": "G0",
        "gate": "G0",
        "adjudicationStatus": "partially_upheld_and_reworded",
        "challengeIds": ["CH-QD-INK-LAYOUT"],
    })

    # HTML: apply the same evidence rule to all five files.
    for artifact_id, points in HTML_POINTS.items():
        subitems = []
        for key, maximum, label in [("basic", 9, "基础功能"), ("analysis", 4, "分析增益"), ("integrity", 2, "交互真实性与键盘等效")]:
            subitems.append({
                "id": key,
                "label": label,
                "maxPoints": maximum,
                "earnedPoints": points[key],
                "result": HTML_OBSERVATIONS[artifact_id][key],
                "evidenceIds": HTML_EVIDENCE[artifact_id],
            })
        total = sum(points.values())
        set_criterion(
            report, artifact_id, "effective-interaction", total,
            basis="；".join(HTML_OBSERVATIONS[artifact_id].values()) + f" 合计{total:g}/15。",
            finding_ids=criterion(report, artifact_id, "effective-interaction").get("findingIds", []),
            subitems=subitems,
        )
        criterion(report, artifact_id, "effective-interaction")["evidenceIds"] = copy.deepcopy(HTML_EVIDENCE[artifact_id])
        set_criterion(
            report, artifact_id, "chrome-load", 10.0,
            basis="联网冷启动和刷新均成功，核心内容与图表完成加载；耗时仅作观察，不进入排名，得10/10。",
            finding_ids=[],
        )
        criterion(report, artifact_id, "chrome-load")["evidenceIds"] = copy.deepcopy(HTML_EVIDENCE[artifact_id])
        set_criterion(
            report, artifact_id, "online-resilience", 5.0,
            basis="正常联网状态加载成功且未出现阻断核心功能的资源或脚本错误；按原Prompt‘可联网访问即可’，不因使用CDN本身扣分，得5/5。",
            finding_ids=[],
        )
        criterion(report, artifact_id, "online-resilience")["evidenceIds"] = copy.deepcopy(HTML_EVIDENCE[artifact_id])

    set_criterion(report, "artifact:qoder:html", "information-architecture", 10.0,
                  basis="桌面端11节叙事和来源分级清楚；窄屏导航缺失只在响应式维度计分，避免同根重复扣分。",
                  finding_ids=[])
    set_criterion(report, "artifact:workbuddy:html", "information-architecture", 9.0,
                  basis="桌面主题顺序清楚；来源未设独立导航产生1分检索摩擦。窄屏扫描问题只在响应式维度计分。",
                  finding_ids=["DIM-WORKBUDDY-HTML-INFORMATION-ARCHITECTURE"])

    for finding_id in [
        "DIM-QIANWEN-HTML-CHROME-LOAD", "DIM-QODER-HTML-CHROME-LOAD",
        "DIM-WORKBUDDY-HTML-CHROME-LOAD", "DIM-ZHIKUNCODE-HTML-CHROME-LOAD",
        "千问-html-03", "Qoder-html-04", "DIM-WORKBUDDY-HTML-ONLINE-RESILIENCE",
        "ZhikunCode-html-04", "DIM-QODER-HTML-INFORMATION-ARCHITECTURE",
    ]:
        retire_finding(report, finding_id, "v4.4按五家统一规则复核：正常联网加载成功，不因耗时或CDN依赖本身扣分；同一窄屏问题不跨维度重复扣分。原观察保留为非计分信息。")

    # Narrow old wording for interaction findings without pretending that a
    # particular optional widget was required by the prompt.
    interaction_updates = {
        "DIM-QIANWEN-HTML-EFFECTIVE-INTERACTION": "基础导航和图表提示全部通过；未提供能改变比较口径或分析视图的增益交互，因此只未取得分析增益4分。",
        "DIM-QODER-HTML-EFFECTIVE-INTERACTION": "基础导航和图表提示全部通过；未提供能改变比较口径或分析视图的增益交互，因此只未取得分析增益4分。",
        "HTML-WB-002": "基础导航和图表工作；优势卡呈现可点击外观但点击无状态变化且不能键盘聚焦，交互真实性未满。",
        "HTML-D-002": "主要导航和分析视图可用；返回顶部按钮点击后未回到顶部。",
        "DIM-ZHIKUNCODE-HTML-EFFECTIVE-INTERACTION": "导航、切换、折叠、返回顶部和图表提示有效；折叠标题未提供完整键盘等效。",
    }
    for finding_id, summary in interaction_updates.items():
        row = finding(report, finding_id)
        row["summary"] = summary
        row["observation"] = summary
        row["adjudicationStatus"] = "rescored_under_symmetric_atomic_interaction_rule"
        row.setdefault("challengeIds", []).append("CH-ALL-HTML-INTERACTION")

    # Qoder G2 remains, but the rule was not preregistered.
    qoder_ppt = finding(report, "QODER-P-N01")
    qoder_ppt["interpretation"] = (
        "投资人材料核心标题把绝对正负方向写反，按v4复核阶段形成并公开、随后对五款固定样本对称检查的"
        "G2-CORE-DIRECTION-REVERSAL规则进入G2。该规则不是事前预注册。影响1/20页且一处文字可修复；"
        "G2只表示原样文件不得未经复核交付，不等于整份PPT低质或难以修复。"
    )
    qoder_ppt["adjudicationStatus"] = "finding_upheld_gate_wording_corrected"
    qoder_ppt.setdefault("challengeIds", []).append("CH-QD-PPT-GATE")
    for rule in report.get("methodology", {}).get("gateRules", []):
        if rule.get("id") == "G2-CORE-DIRECTION-REVERSAL":
            rule.update({"preRegistered": False, "adoptionTiming": "v4_post_observation_symmetric_reassessment"})

    # Propagation label: no existential claim about sources.
    for row in report.get("propagation", []):
        if row.get("id") == "P-WB-SOURCES":
            row["summary"] = "固定终稿内来源可追溯颗粒度与A级标注不匹配，以及预测属性问题的传播。"
            row["label"] = row["summary"]

    # Word retrieval: all five fixed documents are scored by the same six-task
    # formula. Search success and first-hit correctness carry four of five
    # points because the prompt asked for an editable report, not a native
    # navigation pane. Native headings and pane navigation are one structural
    # convenience and are therefore not scored twice.
    word_locator_path = Path(__file__).resolve().parent / "word_locator_retest" / "word_locator_v44.json"
    word_locator = json.loads(word_locator_path.read_text(encoding="utf-8"))
    word_finding_ids = {
        "artifact:doubao:word": ["DIM-DOUBAO-WORD-RETRIEVAL-EXPRESSION"],
        "artifact:qianwen:word": ["DIM-QIANWEN-WORD-RETRIEVAL-EXPRESSION"],
        "artifact:qoder:word": ["NATIVE-WORD-QODER-NAV"],
        "artifact:workbuddy:word": ["NATIVE-WORD-WB-NAV"],
        "artifact:zhikuncode:word": ["NATIVE-WORD-ZHIKUN-NAV"],
    }
    for artifact_id, result in word_locator["artifacts"].items():
        navigation = int(result["navigationPassed"])
        ctrl_f = int(result["ctrlFPassed"])
        first_hit = int(result["firstHitPassed"])
        subitems = [
            {
                "id": "ctrl-f-find",
                "label": "Ctrl+F查找成功",
                "maxPoints": 2.0,
                "earnedPoints": rounded(ctrl_f / 6 * 2, 6),
                "result": f"{ctrl_f}/6",
                "formula": "通过主题数/6×2",
            },
            {
                "id": "first-hit-correct-section",
                "label": "首次命中正确章节",
                "maxPoints": 2.0,
                "earnedPoints": rounded(first_hit / 6 * 2, 6),
                "result": f"{first_hit}/6",
                "formula": "通过主题数/6×2",
            },
            {
                "id": "native-navigation",
                "label": "原生导航窗格两步内直达",
                "maxPoints": 1.0,
                "earnedPoints": rounded(navigation / 6, 6),
                "result": f"{navigation}/6",
                "formula": "通过主题数/6×1；不再与原生标题覆盖重复计分",
            },
        ]
        earned = rounded(sum(float(item["earnedPoints"]) for item in subitems))
        active_findings = word_finding_ids[artifact_id] if earned < 5 else []
        set_criterion(
            report,
            artifact_id,
            "retrieval-expression",
            earned,
            basis=(
                f"六项固定定位任务机械计分：Ctrl+F {ctrl_f}/6、首次命中{first_hit}/6、"
                f"原生导航{navigation}/6，合计{earned:g}/5；Prompt未要求的导航便利性最多1分。"
                "导航窗格两步直达最多1分；本测试不评价正文内容质量，也不单独触发G1/G2。"
            ),
            finding_ids=active_findings,
            subitems=subitems,
        )
        score_row = criterion(report, artifact_id, "retrieval-expression")
        score_row["evidenceIds"] = copy.deepcopy(result["evidence"])
        score_row["checklistSource"] = {
            "path": str(word_locator_path),
            "sha256": sha256(word_locator_path),
            "kind": "symmetric_word_locator_6_tasks",
        }
        score_row["taskResult"] = copy.deepcopy(result)

    for finding_id in ["DIM-DOUBAO-WORD-RETRIEVAL-EXPRESSION", "DIM-QIANWEN-WORD-RETRIEVAL-EXPRESSION"]:
        retire_finding(
            report,
            finding_id,
            "五家按同一六任务公式复测后，本件原生标题、两步导航、Ctrl+F和首次命中均通过；旧0.5分主观保留取消。",
        )
        finding(report, finding_id).setdefault("challengeIds", []).append("CH-ALL-WORD-LOCATOR")
    for finding_id in ["NATIVE-WORD-QODER-NAV", "NATIVE-WORD-WB-NAV", "NATIVE-WORD-ZHIKUN-NAV"]:
        row = finding(report, finding_id)
        row["adjudicationStatus"] = "mechanically_rescored_under_symmetric_six_task_rule"
        row.setdefault("challengeIds", []).append("CH-ALL-WORD-LOCATOR")
    finding(report, "NATIVE-WORD-QODER-NAV")["summary"] = "32页Word导航窗格无六项原生标题，但六项Ctrl+F及首次命中均通过；按用户定位任务机械得4/5。"
    finding(report, "NATIVE-WORD-WB-NAV")["summary"] = "8页Word原生导航覆盖2/6，六项正文搜索及首次命中通过；按用户定位任务机械得4.33/5。"
    finding(report, "NATIVE-WORD-ZHIKUN-NAV")["summary"] = "12页Word导航窗格无六项原生标题，但六项Ctrl+F及首次命中均通过；按用户定位任务机械得4/5。"

    # Native opening: the byte-identical first-open copy is always the scored
    # specimen.  A repaired copy can earn preservation/session/reopen points,
    # but it cannot restore the clean-entry points lost by the original file.
    special_native = {
        "artifact:doubao:excel": {
            "entry": 0.0,
            "preservation": 3.0,
            "session": 2.0,
            "reopen": 1.0,
            "findingIds": ["NATIVE-DOUBAO-EXCEL-REPAIR"],
            "actual": "Mac Excel首次打开要求修复；单独修复副本10/10 Sheet、6/6图保留，公式142→141，编辑与保存重开通过。",
        },
        "artifact:doubao:ppt": {
            "entry": 0.0,
            "preservation": 1.5,
            "session": 1.0,
            "reopen": 1.0,
            "findingIds": ["NATIVE-DOUBAO-PPT-REPAIR-LOSS"],
            "actual": "Mac PowerPoint首次打开要求修复；16页容器保留，但8/16页可见内容空白且7张图表、7个嵌入工作簿丢失；仍可遍历、保存和重开。",
        },
        "artifact:workbuddy:word": {
            "entry": 3.0,
            "preservation": 3.0,
            "session": 2.0,
            "reopen": 1.0,
            "findingIds": ["NATIVE-WORD-WB-FIELD"],
            "actual": "首次打开出现‘域可能引用其他文件，是否更新’选择；选择‘否’后8/8页完整可读，编辑、保存和重开通过。该提示不是修复提示。",
        },
    }
    office_artifacts = [row for row in report["artifacts"] if row["kind"] in {"excel", "word", "ppt"}]
    native_review_rows = []
    for artifact in office_artifacts:
        artifact_id = artifact["id"]
        suffix = "native-open-slideshow" if artifact["kind"] == "ppt" else "native-open"
        old_row = criterion(report, artifact_id, suffix)
        outcome = special_native.get(artifact_id, {
            "entry": 4.0,
            "preservation": 3.0,
            "session": 2.0,
            "reopen": 1.0,
            "findingIds": [],
            "actual": "字节一致首次打开副本无修复或选择提示，内容完整可遍历，保存关闭重开通过。",
        })
        subitems = [
            {"id": "first-entry-path", "label": "无需修复的首次进入", "maxPoints": 4.0, "earnedPoints": outcome["entry"], "rule": "无提示4；一次非修复选择3；必须修复或指定应用仍不可进入均为0；二者差异由内容保全和会话完成分体现"},
            {"id": "visible-content-preservation", "label": "可见内容保全", "maxPoints": 3.0, "earnedPoints": outcome["preservation"], "rule": "容器、核心文本/数据、图表/媒体三类各1分；按保全比例以0.5分为最小步长"},
            {"id": "native-session-completion", "label": "原生会话完成", "maxPoints": 2.0, "earnedPoints": outcome["session"], "rule": "可遍历全部Sheet、Word页或PPT页且应用不崩溃；不重复扣内容缺失"},
            {"id": "save-close-reopen", "label": "保存—关闭—重开", "maxPoints": 1.0, "earnedPoints": outcome["reopen"], "rule": "编辑副本可保存、关闭并重新打开"},
        ]
        earned = rounded(sum(float(item["earnedPoints"]) for item in subitems))
        set_criterion(
            report,
            artifact_id,
            suffix,
            earned,
            basis=f"统一原生打开四段式：{outcome['actual']} 得{earned:g}/10；修复副本不替代首次打开体验，且不叠加文件级固定罚分。",
            finding_ids=outcome["findingIds"],
            subitems=subitems,
        )
        criterion(report, artifact_id, suffix)["evidenceIds"] = copy.deepcopy(old_row.get("evidenceIds", []))
        native_review_rows.append({
            "artifactId": artifact_id,
            "tool": artifact["tool"],
            "kind": artifact["kind"],
            "scoredSpecimenSha256": artifact["auditCopies"]["firstOpen"]["copySha256"],
            "originalSha256": artifact["original"]["sha256"],
            "byteIdentical": artifact["auditCopies"]["firstOpen"]["copySha256"] == artifact["original"]["sha256"],
            "subitems": copy.deepcopy(subitems),
            "score": earned,
            "actual": outcome["actual"],
            "evidenceIds": copy.deepcopy(old_row.get("evidenceIds", [])),
        })
    report["nativeOpenAdjudication"] = {
        "version": "4.4",
        "scope": "15件Office固定终稿；图片与HTML另按各自技术完整性/加载维度评价",
        "scoredSpecimen": "与原件SHA-256一致的首次打开副本",
        "repairCopyRole": "仅评价可恢复性、内容保全与后续使用，不替代首次打开体验",
        "fixedPenaltyApplied": False,
        "rows": native_review_rows,
    }

    excel_repair = finding(report, "NATIVE-DOUBAO-EXCEL-REPAIR")
    excel_repair.update({
        "criterionId": "criterion:excel:native-open",
        "deductionMode": "criterion_subitems_only",
        "causeStatus": "observed_in_fixed_mac_excel_environment_cross_platform_cause_unverified",
        "summary": "Mac Excel首次打开要求修复；首次进入项0/4。修复副本保留10个Sheet和6张图，单元格/公式层确认G11被删除；修复后能力仅在保全、会话和保存重开项得分。",
        "interpretation": "按统一四段式计6/10；修复副本只能证明可恢复性，不能替代原件的首次打开结果，也不另加固定罚分。",
        "adjudicationStatus": "rescored_under_symmetric_native_open_rule",
    })
    excel_repair.setdefault("challengeIds", []).append("CH-ALL-NATIVE-FIRST-OPEN")
    ppt_repair = finding(report, "NATIVE-DOUBAO-PPT-REPAIR-LOSS")
    ppt_repair.update({
        "criterionId": "criterion:ppt:native-open-slideshow",
        "deductionMode": "criterion_subitems_only",
        "causeStatus": "observed_in_fixed_mac_powerpoint_environment_cross_platform_cause_unverified",
        "interpretation": "首次进入0/4、可见内容保全1.5/3、完整会话1/2、保存重开1/1，共3.5/10；图表对象编辑失败在独立图表编辑维度计分，不另加固定罚分。",
        "adjudicationStatus": "rescored_under_symmetric_native_open_rule",
    })
    ppt_repair.setdefault("challengeIds", []).append("CH-ALL-NATIVE-FIRST-OPEN")
    wb_field = finding(report, "NATIVE-WORD-WB-FIELD")
    wb_field.update({
        "criterionId": "criterion:word:native-open",
        "severity": "minor",
        "deductionMode": "criterion_subitems_only",
        "detectability": "immediate_on_first_open",
        "causeStatus": "prompt_observed_updateFields_true_external_target_not_confirmed",
        "summary": "首次打开出现域更新选择提示；选择‘否’后8页完整可用。只能确认提示与updateFields设置，不能证明存在真实外部目标。",
        "interpretation": "一次非修复选择使首次进入路径得3/4；内容保全、会话和保存重开均满分，不夸大为文件损坏。",
        "repairEffort": "one_user_choice_or_remove_updateFields_setting",
        "adjudicationStatus": "rescored_under_symmetric_native_open_rule",
    })
    wb_field.setdefault("challengeIds", []).append("CH-ALL-NATIVE-FIRST-OPEN")


def recompute_scores(report: dict[str, Any]) -> None:
    defs = definitions(report)
    artifacts = {row["id"]: row for row in report["artifacts"]}
    for artifact_id, score in report["scores"]["artifacts"].items():
        # Capture the immutable v4.3 point estimate before recalculating any
        # criterion.  This value is part of the public change ledger and must
        # never fall back to the newly calculated score.
        v43_quality_score = float(score["qualityScore"])
        v43_mechanical_score = score.get("causalQualityScore")
        v43_restored_points = score.get("causalRestoredPoints")
        total = 0.0
        for row in score["criterionScores"]:
            weight = float(defs[row["criterionId"]]["weight"])
            if row.get("subitemScores"):
                earned = sum(float(item["earnedPoints"]) for item in row["subitemScores"])
                maximum = sum(float(item["maxPoints"]) for item in row["subitemScores"])
                if abs(maximum - weight) > 1e-9:
                    raise ValueError(f"subitem maximum mismatch: {artifact_id}/{row['criterionId']}")
                row["weighted"] = rounded(earned)
                row["rating0To5"] = rounded(earned / maximum * 5, 6)
            else:
                row["weighted"] = rounded(float(row["rating0To5"]) / 5 * weight)
            total += float(row["weighted"])
        score["qualityScore"] = score["baseScore"] = score["weightedKnownSum"] = rounded(total)
        score["normalizedPartialScore"] = rounded(total)
        score["scoreModel"] = "v4.4_linear_adjudicated_no_cap_no_fixed_adjustment"
        score["scoreStatus"] = "final_after_v44_adjudication"
        score.setdefault("legacyDiagnostics", {})["v43MechanicalPropagation"] = {
            "score": v43_mechanical_score,
            "restoredPoints": v43_restored_points,
            "status": "retired_noncausal_not_an_active_score",
        }
        score["causalQualityScore"] = None
        score["causalRestoredPoints"] = None
        score["causalRestorationFindingIds"] = []
        score["v43ToV44"] = {
            "v43QualityScore": rounded(v43_quality_score),
            "v44QualityScore": score["qualityScore"],
            "delta": rounded(score["qualityScore"] - v43_quality_score),
            "changed": abs(score["qualityScore"] - v43_quality_score) > 1e-9,
            "reason": "仅在异议裁决表列明的维度按五家对称规则或固定原件反证重算。",
        }

        # Recalculate the two display/tie-break indices against the exact
        # criterion sets frozen in v4.3, and update the published numerator and
        # denominator at the same time.  This prevents an index label from
        # drifting away from the formula it claims to represent.
        rows_by_id = {row["criterionId"]: row for row in score["criterionScores"]}
        for index_field, basis_field in [
            ("nativeUsabilityIndex", "nativeUsabilityIndexBasis"),
            ("taskCompletionIndex", "taskCompletionIndexBasis"),
        ]:
            basis = score[basis_field]
            selected = [rows_by_id[criterion_id] for criterion_id in basis["criterionIds"]]
            maximum = sum(float(defs[row["criterionId"]]["weight"]) for row in selected)
            earned = sum(float(row["weighted"]) for row in selected)
            basis["earnedPoints"] = rounded(earned)
            basis["maximumPoints"] = rounded(maximum)
            score[index_field] = rounded(earned / maximum * 100) if maximum else None

    # Reconcile criterion gaps without presenting them as causal effects.
    by_id = {row["id"]: row for row in report["findings"]}
    for row in report["findings"]:
        row.setdefault("scoreImpact", {})["dimensionGapAttributionShare"] = 0.0
        row["scoreImpact"]["causalRestoration"] = 0.0
    for artifact_id, score in report["scores"]["artifacts"].items():
        for row in score["criterionScores"]:
            maximum = float(defs[row["criterionId"]]["weight"])
            deficit = max(0.0, maximum - float(row["weighted"]))
            cited = [by_id[fid] for fid in row.get("findingIds", []) if fid in by_id and by_id[fid].get("deducted")]
            if cited and deficit:
                share = deficit / len(cited)
                for item in cited:
                    item["scoreImpact"]["dimensionGapAttributionShare"] = rounded(item["scoreImpact"]["dimensionGapAttributionShare"] + share)
    for row in report["findings"]:
        share = row["scoreImpact"]["dimensionGapAttributionShare"]
        row.setdefault("criterionDelta", {})["points"] = rounded(-share)
        row["criterionDelta"]["semantic"] = "mechanical_criterion_gap_reconciliation_only"
        row["criterionDelta"]["definition"] = "把维度相对满分的缺口在该维度所引用的计分finding之间机械分摊，仅用于账面勾稽；不是因果贡献或删除finding后的反事实回分。"


def classify_assessment_modes(report: dict[str, Any]) -> None:
    """Separate genuinely atomized tests from anchored reviewer judgments.

    The v4.3 labels called many anchored-holistic rows "mechanical" although
    no item-by-item conversion was published.  v4.4 does not alter those point
    estimates; it only describes their epistemic status honestly and includes
    the mixed rows in the single-rater resolution stress test.
    """
    artifacts_by_kind = {
        kind: [row["id"] for row in report["artifacts"] if row["kind"] == kind]
        for kind in KINDS
    }
    for kind, rows in report["criteriaDefinitions"].items():
        for definition in rows:
            criterion_id = definition["id"]
            original_class = definition.get("assessmentClass")
            score_rows = [
                next(
                    row for row in report["scores"]["artifacts"][artifact_id]["criterionScores"]
                    if row["criterionId"] == criterion_id
                )
                for artifact_id in artifacts_by_kind[kind]
            ]
            fully_atomized = (
                criterion_id in FULLY_ATOMIZED_MECHANICAL_CRITERIA
                and all(row.get("subitemScores") for row in score_rows)
            )
            if original_class == "expert_judgment":
                applied_class = "expert_judgment"
                reason = "该维度依据公开0—5锚点进行专业判断。"
            elif fully_atomized:
                applied_class = "mechanical"
                reason = "五件同类固定样本均有保留的原子子测试，子项满分与维度权重一致。"
            else:
                applied_class = "mixed_anchored_judgment"
                reason = (
                    "观察事实可复核，但当前实得分由0—5锚点整体换算，未公开足以机械重算的"
                    "全量行项公式；因此归为锚定式混合判断。"
                )
            definition["assessmentClassV43"] = original_class
            definition["assessmentClass"] = applied_class
            definition["assessmentClassReason"] = reason
            definition["fullyAtomizedAcrossFiveSamples"] = fully_atomized
            for score_row in score_rows:
                # A partially atomized criterion (currently Word retrieval) is
                # mechanical only for the artifact with a retained complete
                # subtest table; the other four remain mixed until retested.
                if score_row.get("subitemScores") and criterion_id == "criterion:word:retrieval-expression":
                    score_row["assessmentClassApplied"] = "mechanical"
                    score_row["assessmentClassReason"] = "本件已保留完整的六任务原子定位结果。"
                else:
                    score_row["assessmentClassApplied"] = applied_class
                    score_row["assessmentClassReason"] = reason


def assign_impact_units(report: dict[str, Any]) -> None:
    """Give every scored finding-to-criterion link an explicit impact unit."""
    cited_by_finding: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for artifact_id, score in report["scores"]["artifacts"].items():
        for score_row in score["criterionScores"]:
            score_row["findingImpactLinks"] = []
            for finding_id in score_row.get("findingIds", []):
                cited_by_finding.setdefault(finding_id, []).append((artifact_id, score_row))

    for item in report["findings"]:
        base_unit = stable_impact_id(item.get("deduplicationKey") or item.get("rootCauseId") or item["id"])
        item["impactUnitId"] = base_unit
        item["impactUnits"] = []
        links = cited_by_finding.get(item["id"], [])
        for artifact_id, score_row in links:
            criterion_id = score_row["criterionId"]
            if item["id"] == "NATIVE-DOUBAO-PPT-REPAIR-LOSS":
                if criterion_id.endswith(":native-open-slideshow"):
                    impact_unit_id = stable_impact_id("doubao-ppt-open-slideshow-loss")
                    outcome = "Mac PowerPoint首次打开要求修复，修复后8/16页无法完整放映。"
                elif criterion_id.endswith(":chart-data-editing"):
                    impact_unit_id = stable_impact_id("doubao-ppt-chart-editability-loss")
                    outcome = "修复后7张图表及7个嵌入工作簿丢失，图表编辑任务失败。"
                else:
                    raise ValueError(f"unexpected Doubao PPT impact criterion: {criterion_id}")
            else:
                impact_unit_id = base_unit
                outcome = item.get("observation") or item.get("summary") or "见finding观察。"
            link = {
                "findingId": item["id"],
                "criterionId": criterion_id,
                "impactUnitId": impact_unit_id,
                "observableOutcome": outcome,
            }
            score_row["findingImpactLinks"].append(copy.deepcopy(link))
            if not any(unit["impactUnitId"] == impact_unit_id for unit in item["impactUnits"]):
                item["impactUnits"].append({
                    "impactUnitId": impact_unit_id,
                    "artifactId": artifact_id,
                    "criterionIds": [criterion_id],
                    "observableOutcome": outcome,
                })
            else:
                unit = next(unit for unit in item["impactUnits"] if unit["impactUnitId"] == impact_unit_id)
                if criterion_id not in unit["criterionIds"]:
                    unit["criterionIds"].append(criterion_id)
        if not item["impactUnits"]:
            item["impactUnits"] = [{
                "impactUnitId": base_unit,
                "artifactId": item.get("artifactId"),
                "criterionIds": [],
                "observableOutcome": item.get("observation") or item.get("summary") or "未进入连续分的观察。",
            }]


def ranking_weights(report: dict[str, Any]) -> dict[str, dict[str, float]]:
    models = report.get("methodology", {}).get("weightModels", [])
    return {row["id"]: row["weights"] for row in models}


def tie_indexes(report: dict[str, Any], tool: str) -> tuple[float, float, float]:
    artifacts = [a for a in report["artifacts"] if a["tool"] == tool]
    scores = [report["scores"]["artifacts"][a["id"]] for a in artifacts]
    native = sum(float(s.get("nativeUsabilityIndex") or 0) for s in scores) / len(scores)
    task = sum(float(s.get("taskCompletionIndex") or 0) for s in scores) / len(scores)
    excel = next(a for a in artifacts if a["kind"] == "excel")
    fact = criterion(report, excel["id"], "external-facts")["rating0To5"] / 5 * 100
    return rounded(native), rounded(fact), rounded(task)


def build_rankings(report: dict[str, Any]) -> None:
    defs = report["criteriaDefinitions"]
    judgment_weight = {
        kind: sum(float(row["weight"]) for row in defs[kind] if row.get("assessmentClass") in ASSESSMENT_CLASSES_SENSITIVE)
        for kind in KINDS
    }
    weights_by_mode = ranking_weights(report)
    rankings = {}
    for mode, label in [("equalTask", "六任务等权"), ("practical", "均衡投研实务")]:
        weights = weights_by_mode[mode]
        rows = []
        for tool in TOOLS:
            artifact_scores = {}
            lower_movement = 0.0
            upper_movement = 0.0
            sensitivity_components = []
            for artifact in report["artifacts"]:
                if artifact["tool"] == tool:
                    score_node = report["scores"]["artifacts"][artifact["id"]]
                    artifact_scores[artifact["kind"]] = score_node["qualityScore"]
                    for score_row in score_node["criterionScores"]:
                        applied_class = score_row.get("assessmentClassApplied") or definitions(report)[score_row["criterionId"]].get("assessmentClass")
                        if applied_class not in ASSESSMENT_CLASSES_SENSITIVE:
                            continue
                        definition = definitions(report)[score_row["criterionId"]]
                        maximum = float(definition["weight"])
                        earned = float(score_row["weighted"])
                        one_step = maximum * 0.1
                        down = min(earned, one_step) * float(weights[artifact["kind"]])
                        up = min(maximum - earned, one_step) * float(weights[artifact["kind"]])
                        lower_movement += down
                        upper_movement += up
                        sensitivity_components.append({
                            "artifactId": artifact["id"],
                            "criterionId": score_row["criterionId"],
                            "assessmentClass": applied_class,
                            "ratingStep0To5": 0.5,
                            "criterionPointStep": rounded(one_step, 6),
                            "modeWeight": float(weights[artifact["kind"]]),
                            "downwardRoomApplied": rounded(down, 6),
                            "upwardRoomApplied": rounded(up, 6),
                        })
            score = rounded(sum(float(artifact_scores[k]) * float(weights[k]) for k in KINDS))
            native, fact, task = tie_indexes(report, tool)
            joint_extreme_down = rounded(lower_movement)
            joint_extreme_up = rounded(upper_movement)
            # The displayed rank sensitivity changes one scored judgment at a
            # time by one published anchor step. Summing every subjective item
            # in the same favorable or unfavorable direction is retained as a
            # conservative appendix stress test, not presented as a plausible
            # rank interval.
            lower_movement = rounded(max((float(c["downwardRoomApplied"]) for c in sensitivity_components), default=0.0))
            upper_movement = rounded(max((float(c["upwardRoomApplied"]) for c in sensitivity_components), default=0.0))
            lower = rounded(max(0.0, score - lower_movement))
            upper = rounded(min(100.0, score + upper_movement))
            rows.append({
                "tool": tool,
                "score": score,
                "artifactScores": artifact_scores,
                "nativeUsabilityIndex": native,
                "excelFactIndex": fact,
                "taskCompletionIndex": task,
                "judgmentSensitivityLower": lower,
                "judgmentSensitivityUpper": upper,
                "downwardOneStepMovement": rounded(score - lower),
                "upwardOneStepMovement": rounded(upper - score),
                "jointExtremeDownwardMovement": joint_extreme_down,
                "jointExtremeUpwardMovement": joint_extreme_up,
                "jointExtremeLower": rounded(max(0.0, score - joint_extreme_down)),
                "jointExtremeUpper": rounded(min(100.0, score + joint_extreme_up)),
                "judgmentSensitivityComponents": sensitivity_components,
                # Compatibility aliases for v4.3 UI code.  They carry the
                # exact per-tool clipped values above, not a common ± amount.
                "reviewResolutionLower": lower,
                "reviewResolutionUpper": upper,
            })
        rows.sort(key=lambda row: (-row["score"], -row["nativeUsabilityIndex"], -row["excelFactIndex"], -row["taskCompletionIndex"], row["tool"]))
        for index, row in enumerate(rows, 1):
            row["pointEstimateOrder"] = index
            row["rank"] = index
        for row in rows:
            row["possibleBestPointOrder"] = 1 + sum(other["judgmentSensitivityLower"] > row["judgmentSensitivityUpper"] for other in rows if other is not row)
            row["possibleWorstPointOrder"] = len(rows) - sum(row["judgmentSensitivityLower"] > other["judgmentSensitivityUpper"] for other in rows if other is not row)
            row["possibleBestRank"] = row["possibleBestPointOrder"]
            row["possibleWorstRank"] = row["possibleWorstPointOrder"]

        remaining = list(rows)
        layer = 0
        while remaining:
            layer += 1
            frontier = [row for row in remaining if not any(other["judgmentSensitivityLower"] > row["judgmentSensitivityUpper"] for other in remaining if other is not row)]
            if not frontier:
                raise ValueError("uncertainty frontier did not advance")
            for row in frontier:
                row["sensitivityGroup"] = f"S{layer}"
                row["uncertaintyGroup"] = row["sensitivityGroup"]
                row["performanceBand"] = row["sensitivityGroup"]
                row["displayRank"] = f"点估计第{row['pointEstimateOrder']}；单项一步情景第{row['possibleBestRank']}—{row['possibleWorstRank']}"
                row["ordinalClaim"] = row["possibleBestRank"] == row["possibleWorstRank"]
            remaining = [row for row in remaining if row not in frontier]

        ranking_id = f"independent_{mode}"
        rankings[ranking_id] = {
            "id": ranking_id,
            "label": f"正式比较·{label}",
            "status": "final_v44_adjudicated",
            "isOfficial": True,
            "scoreField": "qualityScore",
            "weights": weights,
            "reviewResolutionPoints": None,
            "reviewResolutionPointsStatus": "retired_common_symmetric_amplitude",
            "judgmentSensitivityPolicy": "主图一次只改变一个锚定式混合判断或专家判断维度一个0.5/5评分步长，并在该维度边界截断；所有判断项同向变化的联合极端值仅留在附录。",
            "reviewResolutionMeaning": "单一评分判断改变一步时的局部情景重算；不是置信区间、抽样误差、评审者一致性、概率范围或厂商能力区间。",
            "rows": rows,
        }
    old_rankings = copy.deepcopy(report.get("rankings", {}))
    report.setdefault("legacyDiagnostics", {})["v43MechanicalPropagationRankings"] = {
        "status": "retired_noncausal",
        "reason": "旧值按维度缺口等额恢复完全传播项，不是严格因果分；v4.4不再作为活动排名或切换视角。",
        "rankings": {key: value for key, value in old_rankings.items() if key.startswith("rootCause_")},
    }
    report["rankings"] = rankings
    report["rankingPerspectives"] = {
        "status": "final_v44_adjudicated",
        "definitions": {
            "independent": "每件终稿按单独交付时的结果计分；重复出现的问题仍影响每件文件的独立可用性，但传播图按根因只计一次事件。",
            "equalTask": "六类任务各占1/6。",
            "practical": "Excel 25%、Word 20%、PPT 20%、普通图10%、水墨图10%、HTML 15%。",
        },
        "results": copy.deepcopy(rankings),
        "officialResultIds": list(rankings),
        "diagnosticResultIds": [],
        "ordinalClaim": False,
        "uncertaintyPolicy": "活动名称为‘判断步长敏感性’；旧‘不确定性’字段仅作界面兼容别名。不作统计显著或产品总体优劣主张。",
    }
    report["scoreSensitivity"] = {
        "method": "single_rater_one_judgment_dimension_at_a_time_one_step_sensitivity",
        "ratingStep0To5": 0.5,
        "notStatistical": True,
        "classificationScope": ["mixed_anchored_judgment", "expert_judgment"],
        "classifiedJudgmentWeightsByArtifactKind": judgment_weight,
        "boundaryRule": "主图一次只改变一个已分类判断维度一个0.5/5步长，取可造成的最大单项上下移动；每项均在0与该维度满分处截断。所有判断项同向变化的联合极端值另存档但不用于敏感组。",
        "interpretationLimit": "这是单一评分决定改变一步的局部情景重算，只检查小分差对单项判断的稳健性；不表示真值落在该区间，也不覆盖多个判断同时偏移。",
        "modes": {
            key: {
                "rows": [
                    {k: row[k] for k in [
                        "tool", "score", "judgmentSensitivityLower", "judgmentSensitivityUpper",
                        "downwardOneStepMovement", "upwardOneStepMovement",
                        "possibleBestPointOrder", "possibleWorstPointOrder", "sensitivityGroup",
                    ]}
                    for row in value["rows"]
                ]
            }
            for key, value in rankings.items()
        },
    }
    report["scoreUncertainty"] = {
        "status": "retired_misleading_terminology",
        "replacement": "scoreSensitivity",
        "reason": "没有抽样设计、多评审者数据或概率模型，不应把判断步长压力测试称为统计不确定性。",
    }


def sync_interfaces(report: dict[str, Any]) -> None:
    # Active artifact score interface.
    artifact_meta = {row["id"]: row for row in report["artifacts"]}
    report["qualityScores"] = {
        "version": "4.4",
        "status": "final_v44_adjudicated",
        "primaryField": "qualityScore",
        "capsApplied": False,
        "fixedAdjustmentsApplied": False,
        "artifacts": {
            artifact_id: {
                "artifactId": artifact_id,
                "tool": artifact_meta[artifact_id]["tool"],
                "kind": artifact_meta[artifact_id]["kind"],
                "qualityScore": score["qualityScore"],
                "deliveryGateCode": score.get("deliveryGateCode"),
                "legacyMechanicalDiagnosticStatus": "retired_noncausal",
            }
            for artifact_id, score in report["scores"]["artifacts"].items()
        },
    }
    # Keep criterion subitems in the public review interface without deleting
    # the already-published supplemental test lists.
    rubric = report.setdefault("rubricSubtests", {})
    rubric["version"] = "4.4.0"
    rubric["principle"] = (
        "原子子测试仅在已经留存任务级结果的维度使用；同一原子量表一经使用即保持相同分值上限。"
        "尚未取得逐任务结果的同类文件保留公开0—5锚点评分，并明确列为补测限制，不能伪造机械分项。"
    )
    rubric.setdefault("artifacts", {})
    for artifact_id, score in report["scores"]["artifacts"].items():
        target = rubric["artifacts"].setdefault(artifact_id, {})
        for row in score["criterionScores"]:
            if row.get("subitemScores"):
                target[row["criterionId"]] = {
                    "weightedPoints": row["weighted"],
                    "subitems": copy.deepcopy(row["subitemScores"]),
                    "evidenceIds": copy.deepcopy(row.get("evidenceIds", [])),
                }

    # Explicitly separate terminal file risk from chain-origin attribution for
    # every artifact.  Per-finding components avoid the false implication that
    # one artifact can have only one provenance role.
    findings_by_artifact: dict[str, list[dict[str, Any]]] = {}
    for item in report["findings"]:
        findings_by_artifact.setdefault(item.get("artifactId"), []).append(item)
    for artifact_id, gate in report.get("deliveryGates", {}).get("artifacts", {}).items():
        gate.pop("terminalRiskProvenance", None)
        gate.pop("chainAttributionGateCode", None)
        gate.pop("chainAttributionNote", None)
        components = []
        for item in findings_by_artifact.get(artifact_id, []):
            terminal_code = item.get("terminalRiskCode") or item.get("gate") or "G0"
            if terminal_code == "G0" and not item.get("standaloneRisk"):
                continue
            role = item.get("lineageRole") or "origin"
            components.append({
                "findingId": item["id"],
                "rootCauseId": item.get("rootCauseId") or item["id"],
                "impactUnitId": item.get("impactUnitId"),
                "impactUnitIds": [unit["impactUnitId"] for unit in item.get("impactUnits", [])],
                "lineageRole": role,
                "terminalGateCode": terminal_code,
                "chainAttributionTreatment": (
                    "propagation_display_only_no_new_root"
                    if role == "exact_propagation"
                    else "count_as_origin_mutation_or_independent_reintroduction"
                ),
            })
        gate["terminalRiskComponents"] = components
    report.setdefault("deliveryGates", {})["riskAndAttributionPolicy"] = {
        "terminalRisk": "逐件判断原样文件能否交付；完全继承也可能保留G2终端风险。",
        "chainAttribution": "逐finding判断根因角色；exact_propagation只显示传播范围，不新增根因归责。",
        "scoreEffect": "两者均不直接改写连续质量分。",
    }
    report["propagationStatus"] = {
        "activeLabel": "描述性问题簇与报告线索",
        "causalGraphValidated": False,
        "rankingUse": False,
        "reason": (
            "现有rootCauseId与lineageRole来自固定产物间的内容对照，未建立能证明生成时因果路径的封闭图。"
            "因此只用于展示相同或相似问题出现在哪些文件，不用于因果回分或名次。"
        ),
    }
    for cluster in report.get("propagation", []):
        cluster["displayType"] = "descriptive_issue_cluster"
        cluster["causalGraphValidated"] = False
        cluster["rankingUse"] = False


def challenge_item(cid: str, tool: str, claim_type: str, claim: str, status: str, rationale: str, *, artifacts: list[str] | None = None, findings: list[str] | None = None, before: Any = None, after: Any = None, symmetry: str | None = None) -> dict[str, Any]:
    return {
        "id": cid,
        "tool": tool,
        "claimType": claim_type,
        "claimText": claim,
        "artifactIds": artifacts or [],
        "findingIds": findings or [],
        "responseNature": "ai_generated_tool_self_review_not_vendor_statement",
        "disposition": {
            "status": status,
            "rationale": rationale,
            "evidenceSufficiency": "sufficient" if status != "pending_evidence" else "insufficient",
            "scoreEffectStatus": "recomputed" if before is not None and after is not None and before != after else "none",
            "before": before,
            "after": after,
        },
        "criterionIds": [],
        "decisionEvidenceIds": [],
        "decisionEvidenceRefs": [],
        "falsificationCriteria": "",
        "symmetryBatchId": symmetry,
        "versionEffective": "4.4",
    }


def build_challenges(report: dict[str, Any]) -> None:
    items = [
        challenge_item("CH-WB-SOURCE-BOUNDARY", "WorkBuddy", "evidence", "报告不能证明两份来源绝对不存在。", "accepted", "报告只保留固定终稿内A级标注与可追溯材料不匹配的判断，不再作存在性推断，并据此重评来源维度。", artifacts=["artifact:workbuddy:excel"], findings=["WORKBUDDY-001"], before={"来源维度": 1.6}, after={"来源维度": 3.2}),
        challenge_item("CH-WB-FACT-278-288", "WorkBuddy", "fact", "2.78亿元归母与2.88亿元含少数股东已在Excel明确区分。", "accepted", "固定工作簿F4/F5及说明与口径B12直接支持该主张；撤销旧判断并重评外部事实维度。", artifacts=["artifact:workbuddy:excel"], findings=["WORKBUDDY-003"], before={"criterion": 9.0, "excel": 61.5}, after={"criterion": 24.0, "excel": 78.1}),
        challenge_item("CH-WB-DENOMINATOR-LABEL", "WorkBuddy", "fact", "51.07%是披露口径选择，不应称为错误数字。", "partially_accepted", "51.07%以总营业收入为分母算术正确；只保留‘主营业务结构’标题与分母范围不一致的标签问题，不追加分值损失。", artifacts=["artifact:workbuddy:excel"], findings=["WORKBUDDY-004"], before="错误数字/错误分母", after="算术正确、标题与分母范围不一致且不追加扣分"),
        challenge_item("CH-WB-FUNDING-ATTRIBUTE", "WorkBuddy", "fact", "公司已经上市，42.02亿元可称到账。", "rejected", "本报告评价的是本工具链：Excel为拟募集420,200万元，Word首次改为42.02亿元到账；且正式披露实际募集总额与净额均非42.02亿元。该异议本身不改变连续分；Word总分的变化来自另行对五家对称适用的检索与首次打开规则。", artifacts=["artifact:workbuddy:word"], findings=["WORKBUDDY-W-N01"], before={"Word闸门":"G2","该异议对应分数影响":"无"}, after={"Word闸门":"G2","该异议对应分数影响":"无；文件总分变化来自其他对称方法修订"}),
        challenge_item("CH-WB-PROPAGATION", "WorkBuddy", "methodology", "同一根因传播到五件文件不应被当成五个根因。", "accepted", "传播图只在起点记一次事件；每件下游仍保留独立交付风险。旧机械恢复值不是因果分，v4.4已退出活动排名。", artifacts=["artifact:workbuddy:word", "artifact:workbuddy:ppt", "artifact:workbuddy:image", "artifact:workbuddy:ink", "artifact:workbuddy:html"], before="旧机械传播恢复值可切换为排名", after="退出活动排名，仅在历史技术附录保留非因果诊断"),
        challenge_item("CH-QD-CDN", "Qoder", "methodology", "原Prompt允许联网，不能仅因CDN依赖扣分。", "accepted", "五个HTML在正常联网下均成功加载；CDN依赖本身不扣分，统一恢复联网容错分。", artifacts=[f"artifact:{key}:html" for key in ["doubao", "qianwen", "qoder", "workbuddy", "zhikuncode"]], before={"豆包":5.0,"千问":3.0,"Qoder":3.0,"WorkBuddy":4.0,"ZhikunCode":4.5}, after={tool:5.0 for tool in TOOLS}, symmetry="SYM-HTML-RUNTIME"),
        challenge_item("CH-ALL-HTML-LOAD", "五款工具", "methodology", "操作耗时只作观察，不应进入排名。", "accepted", "五个HTML冷开和刷新均成功，统一将Chrome加载维度按成功结果计满；耗时保留为观察。", artifacts=[f"artifact:{key}:html" for key in ["doubao", "qianwen", "qoder", "workbuddy", "zhikuncode"]], before={"豆包":10.0,"千问":9.0,"Qoder":8.0,"WorkBuddy":8.0,"ZhikunCode":9.0}, after={tool:10.0 for tool in TOOLS}, symmetry="SYM-HTML-RUNTIME"),
        challenge_item("CH-ALL-HTML-INTERACTION", "五款工具", "methodology", "缺少筛选、折叠等特定控件不应被视为基础交互失败。", "accepted", "五家统一改为基础功能9、分析增益4、真实性与键盘等效2的原子计分；可选控件只影响增益上限。窄屏问题只在响应式维度计分。", artifacts=[f"artifact:{key}:html" for key in ["doubao", "qianwen", "qoder", "workbuddy", "zhikuncode"]], before={"豆包":10.5,"千问":6.0,"Qoder":6.0,"WorkBuddy":4.5,"ZhikunCode":13.5}, after={"豆包":12.5,"千问":11.0,"Qoder":11.0,"WorkBuddy":10.0,"ZhikunCode":14.0}, symmetry="SYM-HTML-INTERACTION"),
        challenge_item("CH-QD-IMAGE-DUPLICATION", "Qoder", "methodology", "同一叠印/裁切根因不应跨三个图片维度重复扣分。", "accepted", "该根因仅在100%可读性计分，层级构图和投资人视觉恢复满分；同一规则已扫描五家全部30件终稿。", artifacts=["artifact:qoder:image"], findings=["Qoder-image-02"], before=87.1, after=93.1, symmetry="SYM-SAME-ROOT-SCAN"),
        challenge_item("CH-QD-INK-LAYOUT", "Qoder", "methodology", "水墨图与普通图共用布局本身不是缺陷。", "accepted", "删除‘同构换肤即重大缺陷’定性；按成品可见水墨元素与浪漫叙事强度评分，同一叠印根因只在可读性计分；同一规则已扫描五家全部30件终稿。", artifacts=["artifact:qoder:ink"], findings=["Qoder-ink-02", "Qoder-ink-03"], before=79.5, after=88.0, symmetry="SYM-SAME-ROOT-SCAN"),
        challenge_item("CH-QD-PPT-GATE", "Qoder", "methodology", "1/20页且一处可修的方向错误不应被夸大。", "partially_accepted", "连续分82.2不变，明确范围和修复成本；核心标题绝对正负反转仍触发G2。更正为v4事后对称规则，非事前预注册。", artifacts=["artifact:qoder:ppt"], findings=["QODER-P-N01"], before={"score": 82.2, "gate": "G2"}, after={"score": 82.2, "gate": "G2"}, symmetry="SYM-G2-CORE-DIRECTION"),
        challenge_item("CH-QW-RANKING-TEXT", "千问", "wording", "报告中的两榜名次叙述与数据不一致。", "accepted", "旧回应段确将两榜名次写反；v4.4所有名次从JSON生成，且只称点估计顺序。", before="等权第1、实务第3（错误手填文案）", after="按v4.4活动JSON自动生成两榜点估计及敏感性名次"),
        challenge_item("CH-ALL-RANK-PRECISION", "五款工具", "methodology", "0.05—0.55分差不足以支持确定性名次。", "accepted", "保留可复算点估计顺序，同时发布单评审者对锚定式混合判断与专家判断维度的单步压力测试、情景重算次序和S组；它不是置信区间、概率区间或评审者一致性估计。", before="显示确定点估计顺序及相邻≤1分敏感组", after="显示点估计、按每家实际得分逐维度截断的判断步长压力测试、S组及情景重算次序", symmetry="SYM-RANK-JUDGMENT-SENSITIVITY"),
        challenge_item("CH-DB-PPT-PLATFORM", "豆包", "compatibility", "PPT问题可能是Mac PowerPoint特异兼容性。", "accepted", "继续只陈述macOS 26.5.2与PowerPoint 16.112.3观察并标G2-Mac；Windows与独立重新下载仍未验证。原始首开失败和修复后内容损失均已进入固定环境连续分，平台归因异议本身不改分。", artifacts=["artifact:doubao:ppt"], before={"分数":76.5,"闸门":"G2-Mac"}, after={"分数":76.5,"闸门":"G2-Mac；跨平台归因仍未验证"}),
        challenge_item("CH-ZK-CUTOFF-DISCLOSURE", "ZhikunCode", "fact", "8月31日估值模块已披露为补充，应取消截止日问题。", "rejected", "明示披露降低误导风险，但不能把8月31日事实变成符合8月30日截止口径；继续限定为局部、可删除的G1问题，不外推整本失真。", artifacts=["artifact:zhikuncode:excel"], findings=["ZHIKUN-001"], before={"分数":67.6,"闸门":"G1"}, after={"分数":67.6,"闸门":"G1"}),
        challenge_item(
            "CH-ALL-WORD-LOCATOR", "五款工具", "methodology",
            "Word检索便利性应按同一机械公式计算，且导航窗格不应被夸大为内容质量。",
            "accepted",
            "五件Word统一按六项任务计算：Ctrl+F成功2分、首次命中正确章节2分、原生导航两步直达1分。原生标题与导航属于同一结构能力，不重复计分；Prompt未要求的导航缺失不单独触发闸门，也不与可编辑结构重复扣分。",
            artifacts=[f"artifact:{key}:word" for key in ["doubao", "qianwen", "qoder", "workbuddy", "zhikuncode"]],
            findings=["DIM-DOUBAO-WORD-RETRIEVAL-EXPRESSION", "DIM-QIANWEN-WORD-RETRIEVAL-EXPRESSION", "NATIVE-WORD-QODER-NAV", "NATIVE-WORD-WB-NAV", "NATIVE-WORD-ZHIKUN-NAV"],
            before={"豆包":4.5,"千问":4.5,"Qoder":2.0,"WorkBuddy":3.0,"ZhikunCode":3.0},
            after={"豆包":5.0,"千问":5.0,"Qoder":4.0,"WorkBuddy":4.333333,"ZhikunCode":4.0},
            symmetry="SYM-WORD-LOCATOR",
        ),
        challenge_item(
            "CH-ALL-NATIVE-FIRST-OPEN", "五款工具", "methodology",
            "不能直接按最终修复版评分，原始文件的首次打开摩擦和修复后损失都必须进入分数。",
            "accepted",
            "15件Office固定终稿统一按首次进入4、内容保全3、会话完成2、保存重开1计分；计分对象为与原件SHA一致的首次打开副本，修复副本只评价可恢复性，且不叠加无公式固定罚分。",
            artifacts=[row["id"] for row in report["artifacts"] if row["kind"] in {"excel", "word", "ppt"}],
            findings=["NATIVE-DOUBAO-EXCEL-REPAIR", "NATIVE-DOUBAO-PPT-REPAIR-LOSS", "NATIVE-WORD-WB-FIELD"],
            before={"豆包Excel":6.0,"豆包PPT":3.5,"WorkBuddy Word":7.0},
            after={"豆包Excel":6.0,"豆包PPT":3.5,"WorkBuddy Word":9.0},
            symmetry="SYM-NATIVE-FIRST-OPEN",
        ),
    ]
    for item in items:
        if item["id"] in {"CH-ALL-WORD-LOCATOR", "CH-ALL-NATIVE-FIRST-OPEN"}:
            item["responseNature"] = "methodology_correction_from_symmetric_retest_not_vendor_claim"
    criterion_map = {
        "CH-WB-SOURCE-BOUNDARY": ["criterion:excel:sources"],
        "CH-WB-FACT-278-288": ["criterion:excel:external-facts"],
        "CH-WB-DENOMINATOR-LABEL": ["criterion:excel:period-unit-prediction"],
        "CH-WB-FUNDING-ATTRIBUTE": ["criterion:word:excel-consistency"],
        "CH-QD-CDN": ["criterion:html:online-resilience"],
        "CH-ALL-HTML-LOAD": ["criterion:html:chrome-load"],
        "CH-ALL-HTML-INTERACTION": ["criterion:html:effective-interaction", "criterion:html:information-architecture"],
        "CH-QD-IMAGE-DUPLICATION": ["criterion:image:hierarchy-composition", "criterion:image:readability-100pct", "criterion:image:investor-visual"],
        "CH-QD-INK-LAYOUT": ["criterion:ink:hierarchy-readability", "criterion:ink:ink-romantic-style", "criterion:ink:professional-composition", "criterion:ink:output-finish"],
        "CH-QD-PPT-GATE": ["criterion:ppt:excel-consistency"],
        "CH-DB-PPT-PLATFORM": ["criterion:ppt:native-open-slideshow", "criterion:ppt:chart-data-editing"],
        "CH-ZK-CUTOFF-DISCLOSURE": ["criterion:excel:period-unit-prediction"],
        "CH-ALL-WORD-LOCATOR": ["criterion:word:retrieval-expression"],
        "CH-ALL-NATIVE-FIRST-OPEN": ["criterion:excel:native-open", "criterion:word:native-open", "criterion:ppt:native-open-slideshow"],
    }
    score_change_ids = {
        "CH-WB-SOURCE-BOUNDARY", "CH-WB-FACT-278-288", "CH-QD-CDN",
        "CH-ALL-HTML-LOAD", "CH-ALL-HTML-INTERACTION",
        "CH-QD-IMAGE-DUPLICATION", "CH-QD-INK-LAYOUT",
        "CH-ALL-WORD-LOCATOR", "CH-ALL-NATIVE-FIRST-OPEN",
    }
    special_effects = {
        "CH-WB-PROPAGATION": "ranking_structure_changed_no_artifact_score_change",
        "CH-QW-RANKING-TEXT": "wording_corrected_no_score_change",
        "CH-ALL-RANK-PRECISION": "ranking_interpretation_changed_no_artifact_score_change",
        "CH-QD-PPT-GATE": "gate_wording_corrected_no_score_or_gate_change",
        "CH-DB-PPT-PLATFORM": "platform_attribution_confirmed_no_score_change",
        "CH-ZK-CUTOFF-DISCLOSURE": "finding_upheld_no_score_change",
        "CH-WB-DENOMINATOR-LABEL": "finding_reclassified_no_incremental_score_change",
        "CH-WB-FUNDING-ATTRIBUTE": "finding_upheld_no_score_change",
    }
    finding_by_id = {row["id"]: row for row in report["findings"]}
    score_by_artifact = report["scores"]["artifacts"]
    challenge_by_id = {row["id"]: row for row in items}

    # Close both directions of the challenge↔finding relationship before
    # deriving evidence.  This captures findings that were tagged during the
    # score decision pass (notably all five HTML interaction findings) even if
    # the challenge was initially declared at criterion level.
    for linked_finding in report["findings"]:
        for challenge_id in linked_finding.get("challengeIds", []):
            challenge = challenge_by_id.get(challenge_id)
            if challenge is not None and linked_finding["id"] not in challenge["findingIds"]:
                challenge["findingIds"].append(linked_finding["id"])
    for item in items:
        for finding_id in item.get("findingIds", []):
            linked_finding = finding_by_id.get(finding_id)
            if linked_finding is None:
                continue
            linked_finding.setdefault("challengeIds", [])
            if item["id"] not in linked_finding["challengeIds"]:
                linked_finding["challengeIds"].append(item["id"])
            criterion_id = linked_finding.get("criterionId")
            if criterion_id and criterion_id not in item["criterionIds"]:
                item["criterionIds"].append(criterion_id)

    evidence_index = {row["id"]: index for index, row in enumerate(report["evidence"])}
    evidence_by_id = {row["id"]: row for row in report["evidence"]}
    for item in items:
        item["criterionIds"] = criterion_map.get(item["id"], [])
        for finding_id in item.get("findingIds", []):
            linked_finding = finding_by_id.get(finding_id)
            criterion_id = linked_finding.get("criterionId") if linked_finding else None
            if criterion_id and criterion_id not in item["criterionIds"]:
                item["criterionIds"].append(criterion_id)
        evidence_ids: set[str] = set()
        falsification = []
        for finding_id in item.get("findingIds", []):
            linked_finding = finding_by_id.get(finding_id)
            if not linked_finding:
                continue
            evidence_ids.update(linked_finding.get("evidenceIds", []))
            if linked_finding.get("falsificationCriteria"):
                falsification.append(linked_finding["falsificationCriteria"])
        for artifact_id in item.get("artifactIds", []):
            score = score_by_artifact.get(artifact_id)
            if not score:
                continue
            for row in score["criterionScores"]:
                if row["criterionId"] in item["criterionIds"]:
                    evidence_ids.update(row.get("evidenceIds", []))
        item["decisionEvidenceIds"] = sorted(evidence_ids)
        item["decisionEvidenceRefs"] = [
            {"evidenceId": evidence_id, "jsonPointer": f"/evidence/{evidence_index[evidence_id]}"}
            for evidence_id in item["decisionEvidenceIds"]
            if evidence_id in evidence_index
        ]
        item["decisionCriterionLinks"] = []
        for artifact_id in item.get("artifactIds", []):
            score = score_by_artifact.get(artifact_id)
            if not score:
                continue
            for score_row in score["criterionScores"]:
                if score_row["criterionId"] not in item["criterionIds"]:
                    continue
                link_evidence_ids = set(score_row.get("evidenceIds", []))
                for finding_id in item["findingIds"]:
                    linked_finding = finding_by_id.get(finding_id)
                    if linked_finding and linked_finding.get("artifactId") == artifact_id:
                        link_evidence_ids.update(linked_finding.get("evidenceIds", []))
                if not link_evidence_ids:
                    link_evidence_ids.update(
                        evidence_id for evidence_id in item["decisionEvidenceIds"]
                        if evidence_by_id[evidence_id].get("artifactId") == artifact_id
                    )
                item["decisionCriterionLinks"].append({
                    "artifactId": artifact_id,
                    "criterionId": score_row["criterionId"],
                    "earnedPoints": score_row["weighted"],
                    "evidenceIds": sorted(link_evidence_ids),
                    "findingIds": [finding_id for finding_id in score_row.get("findingIds", []) if finding_id in item["findingIds"]],
                    "impactUnitIds": [link["impactUnitId"] for link in score_row.get("findingImpactLinks", []) if link["findingId"] in item["findingIds"]],
                })
        item["falsificationCriteria"] = "；".join(dict.fromkeys(falsification)) or (
            "以同一SHA-256固定终稿、同一原生环境和同一评分规则给出可复现反证；"
            "仅重复异议文本、提供修订后文件或改变比较口径不足以推翻本次固定样本裁决。"
        )
        if item["id"] in score_change_ids:
            item["disposition"]["scoreEffectStatus"] = "artifact_score_recomputed"
        else:
            item["disposition"]["scoreEffectStatus"] = special_effects.get(item["id"], "none")
        if item["symmetryBatchId"]:
            item["disposition"]["evidenceSufficiency"] = "rule_applied_to_5_of_5_fixed_samples"
        if item["disposition"]["before"] is None:
            item["disposition"]["before"] = "v4.3既有定性或方法状态"
        if item["disposition"]["after"] is None:
            item["disposition"]["after"] = "v4.4裁决后状态，详见理由与关联finding"
    response_summaries = {
        "ZhikunCode": {
            "summary": "对约数、Word导航和8月31日越界的观察与现有证据基本一致；披露越界并不改变截止口径，但报告继续限定为局部G1。",
            "conclusion": "主要事实观察维持；Word检索便利性按用户定位任务公式为4/5、Word总分保持92.4；排名并列展示点估计与敏感性情景重算次序，不把极小差异解释为确定性胜负。",
        },
        "豆包": {
            "summary": "Excel与Mac PowerPoint观察得到固定样本支持；跨平台归因和微小名次差的保留合理。",
            "conclusion": "Word检索便利性按统一公式为5/5；PPT保持76.5，原始首次打开失败与修复后损失均已计入；结论仍仅代表Mac固定环境并标G2-Mac，Windows结果保持未验证。",
        },
        "WorkBuddy": {
            "summary": "2.78/2.88亿元及51.07%两项异议有固定工作簿证据，已实质改定性并重评；42.02亿元属性改写仍成立。",
            "conclusion": "Excel由61.5更正为78.1；Word检索按用户定位任务重算且首次打开提示仍计入原生维度；传播只在起点记一次根因，但含错下游文件的独立使用风险继续显示。",
        },
        "Qoder": {
            "summary": "CDN、可选交互、图片重复扣分和水墨布局四项异议成立；PPT方向错误事实与G2仍成立，但规则时间表述已纠正。",
            "conclusion": "Word检索按用户定位任务由2/5重算为4/5；普通图87.1→93.1，水墨图79.5→88.0，HTML67.5→77.5；PPT保持82.2/G2。",
        },
        "千问": {
            "summary": "Excel图表配置问题仍由原生对象证据支持；关于可选交互和小分差名次的边界意见成立。旧回应段的两榜名次确曾写反。",
            "conclusion": "Word检索便利性按统一公式为5/5；HTML按五家统一规则由70.0→78.0；两榜点估计与敏感性情景重算次序全部由JSON实时生成。",
        },
    }
    responses = []
    for tool in ["ZhikunCode", "豆包", "WorkBuddy", "Qoder", "千问"]:
        filename, digest = SCREENSHOTS[tool]
        original_filename, original_digest = ORIGINAL_SCREENSHOTS[tool]
        relevant = [row["id"] for row in items if row["tool"] in {tool, "五款工具"}]
        responses.append({
            "tool": tool,
            "responseNature": "AI工具根据报告生成的自评，不是厂商、负责人或员工正式声明",
            "screenshotPath": f"stakeholder-responses/{filename}",
            "screenshotSha256": digest,
            "originalScreenshotPath": f"stakeholder-responses/{original_filename}",
            "originalScreenshotSha256": original_digest,
            "displayCopyNote": "HTML内嵌的是等比缩小的WebP显示副本；PNG原图及SHA-256保留在案例证据包。",
            "challengeIds": relevant,
            **response_summaries[tool],
        })
    tool_slug = {"\u8c46\u5305": "doubao", "\u5343\u95ee": "qianwen", "Qoder": "qoder", "WorkBuddy": "workbuddy", "ZhikunCode": "zhikuncode"}
    completed_at = datetime.now(ZoneInfo("Asia/Shanghai")).replace(microsecond=0).isoformat()
    evidence_by_artifact: dict[str, list[str]] = {}
    for evidence in report["evidence"]:
        if evidence.get("artifactId"):
            evidence_by_artifact.setdefault(evidence["artifactId"], []).append(evidence["id"])

    def batch_run(
        tool: str,
        artifact_ids: list[str],
        rule_id: str,
        before: Any,
        actual: Any,
        result: str,
        evidence_ids: list[str],
        score_change: float,
    ) -> dict[str, Any]:
        return {
            "tool": tool,
            "artifactIds": artifact_ids,
            "ruleId": rule_id,
            "before": before,
            "actual": actual,
            "result": result,
            "evidenceIds": sorted(dict.fromkeys(evidence_ids)),
            "scoreChange": rounded(score_change),
            "reviewer": "single_reviewer_fixed_environment_recheck",
            "completedAt": completed_at,
        }

    runtime_before = {
        "\u8c46\u5305": {"chromeLoad": 10.0, "onlineResilience": 5.0},
        "\u5343\u95ee": {"chromeLoad": 9.0, "onlineResilience": 3.0},
        "Qoder": {"chromeLoad": 8.0, "onlineResilience": 3.0},
        "WorkBuddy": {"chromeLoad": 8.0, "onlineResilience": 4.0},
        "ZhikunCode": {"chromeLoad": 9.0, "onlineResilience": 4.5},
    }
    interaction_before = {"\u8c46\u5305": 10.5, "\u5343\u95ee": 6.0, "Qoder": 6.0, "WorkBuddy": 4.5, "ZhikunCode": 13.5}
    runtime_runs = []
    interaction_runs = []
    same_root_runs = []
    gate_runs = []
    sensitivity_runs = []
    word_locator_runs = []
    native_open_runs = []
    baseline_word_locator = {"豆包":4.5,"千问":4.5,"Qoder":2.0,"WorkBuddy":3.0,"ZhikunCode":3.0}
    baseline_native = {
        "豆包": {"excel":6.0,"word":10.0,"ppt":3.5},
        "千问": {"excel":10.0,"word":10.0,"ppt":10.0},
        "Qoder": {"excel":10.0,"word":10.0,"ppt":10.0},
        "WorkBuddy": {"excel":10.0,"word":7.0,"ppt":10.0},
        "ZhikunCode": {"excel":10.0,"word":10.0,"ppt":10.0},
    }
    native_by_artifact = {row["artifactId"]: row for row in report["nativeOpenAdjudication"]["rows"]}
    for tool in TOOLS:
        slug = tool_slug[tool]
        html_artifact = f"artifact:{slug}:html"
        current_runtime = {
            "chromeLoad": criterion(report, html_artifact, "chrome-load")["weighted"],
            "onlineResilience": criterion(report, html_artifact, "online-resilience")["weighted"],
        }
        runtime_runs.append(batch_run(
            tool, [html_artifact], "SYM-HTML-RUNTIME", runtime_before[tool],
            "联网冷启动与刷新均成功；未见阻断核心内容的资源错误。",
            "passed", HTML_EVIDENCE[html_artifact],
            sum(current_runtime.values()) - sum(runtime_before[tool].values()),
        ))
        current_interaction = criterion(report, html_artifact, "effective-interaction")["weighted"]
        interaction_runs.append(batch_run(
            tool, [html_artifact], "SYM-HTML-INTERACTION", interaction_before[tool],
            HTML_OBSERVATIONS[html_artifact], "completed",
            HTML_EVIDENCE[html_artifact], current_interaction - interaction_before[tool],
        ))

        tool_artifacts = [row["id"] for row in report["artifacts"] if row["tool"] == tool]
        if tool == "Qoder":
            actual_root = "普通图和水墨图的同根布局问题只在各文件的主责可读性维度计分；重复维度已回分。"
            root_change = (93.1 - 87.1) + (88.0 - 79.5)
        elif tool == "豆包":
            actual_root = "PPT兼容故障映射为‘打开/放映’与‘图表编辑’两个独立用户任务结果；没有叠加文件级固定罚分。"
            root_change = 0.0
        else:
            actual_root = "已扫描本工具6件终稿的criterion—finding关联；未因本规则新增改分。"
            root_change = 0.0
        root_evidence = []
        for artifact_id in tool_artifacts:
            root_evidence.extend(evidence_by_artifact.get(artifact_id, [])[:1])
        same_root_runs.append(batch_run(
            tool, tool_artifacts, "SYM-SAME-ROOT-SCAN", "v4.3 criterion—finding关联",
            actual_root, "completed", root_evidence, root_change,
        ))

        ppt_artifact = f"artifact:{slug}:ppt"
        ppt_findings = [
            row for row in report["findings"]
            if row.get("artifactId") == ppt_artifact
            and row.get("summary")
            and any(token in row["summary"] for token in ["双双转负", "正负方向", "方向写反"])
        ]
        triggered = tool == "Qoder" and any(row["id"] == "QODER-P-N01" for row in ppt_findings)
        gate_evidence = []
        for row in ppt_findings:
            gate_evidence.extend(row.get("evidenceIds", []))
        if not gate_evidence:
            gate_evidence = evidence_by_artifact.get(ppt_artifact, [])[:2]
        gate_runs.append(batch_run(
            tool, [ppt_artifact], "SYM-G2-CORE-DIRECTION", "未按该事后对称规则逐家标记",
            {"triggered": triggered, "matchedFindingIds": [row["id"] for row in ppt_findings]},
            "triggered_G2" if triggered else "no_matching_direction_reversal_observed",
            gate_evidence, 0.0,
        ))

        sensitivity_actual = {}
        for ranking_id, ranking in report["rankings"].items():
            ranking_row = next(row for row in ranking["rows"] if row["tool"] == tool)
            sensitivity_actual[ranking_id] = {
                "score": ranking_row["score"],
                "lower": ranking_row["judgmentSensitivityLower"],
                "upper": ranking_row["judgmentSensitivityUpper"],
                "possiblePointOrder": [ranking_row["possibleBestPointOrder"], ranking_row["possibleWorstPointOrder"]],
                "sensitivityGroup": ranking_row["sensitivityGroup"],
            }
        sensitivity_runs.append(batch_run(
            tool, tool_artifacts, "SYM-RANK-JUDGMENT-SENSITIVITY", "只显示点估计次序",
            sensitivity_actual, "computed_no_score_change", [], 0.0,
        ))

        word_artifact = f"artifact:{slug}:word"
        word_score = criterion(report, word_artifact, "retrieval-expression")
        word_result = word_score["taskResult"]
        word_locator_runs.append(batch_run(
            tool,
            [word_artifact],
            "SYM-WORD-LOCATOR",
            baseline_word_locator[tool],
            {
                "nativeHeadingCoverage": f"{word_result['headingCoveragePassed']}/6",
                "navigationWithinTwoSteps": f"{word_result['navigationPassed']}/6",
                "ctrlFFind": f"{word_result['ctrlFPassed']}/6",
                "firstHitCorrectSection": f"{word_result['firstHitPassed']}/6",
                "score": word_score["weighted"],
            },
            "completed",
            word_score.get("evidenceIds", []),
            float(word_score["weighted"]) - baseline_word_locator[tool],
        ))

        native_artifacts = [f"artifact:{slug}:{kind}" for kind in ["excel", "word", "ppt"]]
        native_actual = []
        native_change = 0.0
        native_evidence = []
        for native_artifact in native_artifacts:
            kind = native_artifact.rsplit(":", 1)[1]
            native_row = native_by_artifact[native_artifact]
            native_actual.append({
                "artifactId": native_artifact,
                "byteIdentical": native_row["byteIdentical"],
                "subitems": native_row["subitems"],
                "score": native_row["score"],
                "actual": native_row["actual"],
            })
            native_change += float(native_row["score"]) - baseline_native[tool][kind]
            native_evidence.extend(native_row["evidenceIds"])
        native_open_runs.append(batch_run(
            tool,
            native_artifacts,
            "SYM-NATIVE-FIRST-OPEN",
            baseline_native[tool],
            native_actual,
            "completed",
            native_evidence,
            native_change,
        ))

    symmetry_batches = [
        {"id": "SYM-HTML-RUNTIME", "rule": "联网成功且无阻断错误即不因耗时或CDN依赖扣分", "tools": TOOLS, "status": "completed_5_of_5", "runs": runtime_runs},
        {"id": "SYM-HTML-INTERACTION", "rule": "基础9+分析增益4+真实性/键盘2", "tools": TOOLS, "status": "completed_5_of_5", "runs": interaction_runs},
        {"id": "SYM-RANK-JUDGMENT-SENSITIVITY", "rule": "对锚定式混合判断和专家判断维度执行0.5/5单步、逐维度0分/满分截断的非统计压力测试", "tools": TOOLS, "status": "completed_5_of_5", "runs": sensitivity_runs},
        {"id": "SYM-SAME-ROOT-SCAN", "rule": "同一文件的同一可见缺陷只在一个主维度计分；独立操作结果按各自子测试计分且不再叠加固定罚分", "tools": TOOLS, "status": "completed_5_of_5", "runs": same_root_runs},
        {"id": "SYM-G2-CORE-DIRECTION", "rule": "投资人材料的核心标题发生绝对正负方向反转时标G2；该规则于v4观察后形成，未事前预注册", "tools": TOOLS, "status": "completed_5_of_5", "runs": gate_runs},
        {"id": "SYM-WORD-LOCATOR", "rule": "六主题原生标题2分+两步导航1分+Ctrl+F 1分+首次命中1分；导航缺失不单独触发闸门", "tools": TOOLS, "status": "completed_5_of_5", "runs": word_locator_runs},
        {"id": "SYM-NATIVE-FIRST-OPEN", "rule": "15件Office均以字节一致首次打开副本计分：首次进入4+内容保全3+会话完成2+保存重开1；修复副本不替代首开体验", "tools": TOOLS, "status": "completed_5_of_5", "runs": native_open_runs},
    ]
    report["challenges"] = {
        "meta": {
            "schemaVersion": "1.0",
            "status": "completed_for_submitted_ai_self_reviews",
            "responseNaturePolicy": "工具自评只作为异议线索，证据权重为0；评分调整仅以固定原件、原生实测和五家对称规则为依据。",
            "formalVendorResponsesReceived": 0,
            "claimOfVendorAcceptance": False,
        },
        "items": items,
        "responses": responses,
        "symmetryBatches": symmetry_batches,
    }


def build_score_revision_ledger(report: dict[str, Any], baseline: dict[str, Any]) -> None:
    """Publish an exact, machine-recomputed v4.3→v4.4 score bridge."""
    artifacts = {row["id"]: row for row in report["artifacts"]}
    baseline_scores = baseline["scores"]["artifacts"]
    criterion_labels = {
        row["id"]: row["label"]
        for rows in report["criteriaDefinitions"].values()
        for row in rows
    }
    challenges = report["challenges"]["items"]

    def challenges_for_change(artifact_id: str, criterion_id: str, finding_ids: list[str]) -> list[dict[str, Any]]:
        matched = []
        finding_set = set(finding_ids)
        for challenge in challenges:
            artifact_match = artifact_id in challenge.get("artifactIds", [])
            criterion_match = criterion_id in challenge.get("criterionIds", [])
            finding_match = bool(finding_set & set(challenge.get("findingIds", [])))
            if (artifact_match and criterion_match) or finding_match:
                matched.append(challenge)
        return matched

    changes = []
    for artifact_id, current in report["scores"]["artifacts"].items():
        previous = baseline_scores[artifact_id]
        previous_criteria = {row["criterionId"]: row for row in previous["criterionScores"]}
        criterion_changes = []
        for row in current["criterionScores"]:
            old = previous_criteria[row["criterionId"]]
            before = rounded(old["weighted"])
            after = rounded(row["weighted"])
            if abs(after - before) <= 1e-9:
                continue
            linked_challenges = challenges_for_change(
                artifact_id, row["criterionId"], row.get("findingIds", [])
            )
            challenge_ids = sorted(challenge["id"] for challenge in linked_challenges)
            decision_evidence_ids = sorted({
                evidence_id
                for challenge in linked_challenges
                for link in challenge.get("decisionCriterionLinks", [])
                if link.get("artifactId") == artifact_id and link.get("criterionId") == row["criterionId"]
                for evidence_id in link.get("evidenceIds", [])
            })
            criterion_changes.append({
                "criterionId": row["criterionId"],
                "criterionLabel": criterion_labels[row["criterionId"]],
                "v43Earned": before,
                "v44Earned": after,
                "delta": rounded(after - before),
                "v43Basis": old.get("basis"),
                "v44Basis": row.get("basis"),
                "findingIds": row.get("findingIds", []),
                "impactUnitIds": [link["impactUnitId"] for link in row.get("findingImpactLinks", [])],
                "challengeIds": challenge_ids,
                "decisionEvidenceIds": decision_evidence_ids,
                "linkageStatus": "closed_criterion_challenge_evidence" if challenge_ids and decision_evidence_ids else "incomplete",
            })
        before_score = rounded(previous["qualityScore"])
        after_score = rounded(current["qualityScore"])
        if abs(after_score - before_score) <= 1e-9:
            continue
        artifact = artifacts[artifact_id]
        linked_challenge_ids = sorted({
            challenge_id
            for criterion_change in criterion_changes
            for challenge_id in criterion_change["challengeIds"]
        })
        changes.append({
            "artifactId": artifact_id,
            "tool": artifact["tool"],
            "kind": artifact["kind"],
            "v43Score": before_score,
            "v44Score": after_score,
            "delta": rounded(after_score - before_score),
            "criterionChanges": criterion_changes,
            "challengeIds": linked_challenge_ids,
        })

    ranking_changes = []
    for ranking_id, current in report["rankings"].items():
        previous = baseline.get("rankings", {}).get(ranking_id, {})
        previous_by_tool = {row["tool"]: row for row in previous.get("rows", [])}
        rows = []
        for row in current["rows"]:
            old = previous_by_tool.get(row["tool"], {})
            rows.append({
                "tool": row["tool"],
                "v43Score": old.get("score"),
                "v43PointOrder": old.get("rank"),
                "v44Score": row["score"],
                "v44PointOrder": row["pointEstimateOrder"],
                "scoreDelta": rounded(row["score"] - float(old.get("score", row["score"]))),
                "orderDelta": (int(old["rank"]) - int(row["pointEstimateOrder"])) if old.get("rank") is not None else None,
                "singleStepSensitivityPointOrder": f"{row['possibleBestPointOrder']}—{row['possibleWorstPointOrder']}",
                "sensitivityGroup": row["sensitivityGroup"],
            })
        ranking_changes.append({"rankingId": ranking_id, "rows": rows})

    report["scoreRevisionLedger"] = {
        "fromVersion": "4.3",
        "toVersion": "4.4",
        "status": "recomputed_from_criterion_rows",
        "changedArtifactCount": len(changes),
        "unchangedArtifactCount": len(report["artifacts"]) - len(changes),
        "artifactChanges": changes,
        "rankingChanges": ranking_changes,
        "statement": "所有改分均由逐维度实得分重算；异议文本本身证据权重为0，只有固定原件、原生实测或五家对称规则能改变分值。",
    }


def update_presentation(report: dict[str, Any], baseline_path: Path, output_path: Path, final: bool) -> None:
    meta = report["meta"]
    meta.update({
        "schemaVersion": "4.4.0",
        "dataVersion": "4.4-adjudication",
        "scoringVersion": "4.4-linear-adjudicated-symmetric-reassessment",
        "presentationVersion": "4.4",
        "publicationStatus": "published_after_v44_qa" if final else "candidate_qa_pending",
        "adjudicationStatus": "completed_for_submitted_ai_self_reviews_not_vendor_signoff",
        "status": "final_v4_4_fixed_environment" if final else "v4_4_candidate_qa_pending",
        "version": "报告版本 4.4 · 工具自评异议复核修订版",
        "subtitle": "固定样本、固定环境交付物比较；合理异议已按固定原件和五家对称规则复核并重算。",
        "statusNote": "已完成对五份AI工具自评的证据复核；未取得任何厂商正式签字或认可，Windows PowerPoint与独立重新下载仍未验证。",
        "generatedAt": datetime.now(ZoneInfo("Asia/Shanghai")).replace(microsecond=0).isoformat(),
    })
    release_status = "final_v4_4_fixed_environment" if final else "v4_4_candidate_qa_pending"
    ranking_status = "final_v44_adjudicated" if final else "candidate_v44_qa_pending"
    report["scores"]["status"] = release_status
    report["qualityScores"]["status"] = ranking_status
    report["rankingPerspectives"]["status"] = ranking_status
    for score in report["scores"]["artifacts"].values():
        score["scoreStatus"] = ranking_status
    for ranking in report["rankings"].values():
        ranking["status"] = ranking_status
    report["rubricSubtests"]["version"] = "4.4.0"
    report["rubricSubtests"]["wordLocatorCoverage"] = {
        "fullyMechanicalArtifactIds": [
            "artifact:doubao:word", "artifact:qianwen:word", "artifact:qoder:word",
            "artifact:workbuddy:word", "artifact:zhikuncode:word",
        ],
        "scoreFormula": "六项主题Ctrl+F成功2分+首次命中正确章节2分+原生导航窗格两步直达1分。",
        "scoreTreatment": "五件固定Word均按同一六任务公式重算；原生标题与导航视为同一结构能力，不重复计分。Prompt未要求的导航便利性最多1分，不单独触发G1/G2，也不与可编辑结构重复扣分。",
        "checklistPath": str((Path(__file__).resolve().parent / "word_locator_retest" / "word_locator_v44.json").resolve()),
        "checklistSha256": sha256(Path(__file__).resolve().parent / "word_locator_retest" / "word_locator_v44.json"),
    }
    report["methodology"]["rankingViews"] = ["independent_equalTask", "independent_practical"]
    report["methodology"]["mechanicalPropagationDiagnostic"].update({
        "status": "retired_noncausal_historical_appendix_only",
        "officialRankingUse": False,
        "reason": "维度缺口机械恢复不能证明删除某根因后的反事实得分，因此不再提供活动切换或正式名次。",
    })
    report["methodology"]["assessmentClassification"].update({
        "purpose": "区分已保留完整原子公式的机械项、观察可复核但换分仍使用整体锚点的混合判断项，以及专家判断项。分类不改变点估计或权重。",
        "mechanical": "五件同类固定样本均有可重算的原子子测试，或本件有完整且公开的任务级公式。",
        "mixed_anchored_judgment": "底层观察可复核，但当前得分是0—5锚点整体换算，未公开能从全量行项机械重算的公式。",
        "expert_judgment": "分析深度、信息取舍、叙事、视觉层级与构图等按公开0—5锚点判断。",
        "scoreEffect": "不影响点估计；混合判断与专家判断项进入单评审者判断步长压力测试，形成S组和情景重算次序。",
    })
    report["methodology"]["sameObservedDefectTreatment"] = {
        "sameDefectOnePrimaryDimension": "同一文件的同一可见质量缺陷只在一个主维度形成分值损失；其他维度只作交叉说明。",
        "distinctFunctionalOutcomes": "同一底层文件兼容故障若分别导致‘无法无损打开/放映’与‘图表对象无法编辑’两个独立必测操作失败，各子测试只按实际成功项得分；不再另加文件级固定罚分。这不是同一表现缺陷跨维度重复扣分。",
        "symmetricScope": "已对五款工具全部30件终稿的criterion—finding关联执行同一规则扫描；Qoder两张图片的重复计分已更正，豆包PPT保留的是两个独立操作结果。",
        "rawDuplicateFindingAcrossCriteria": ["NATIVE-DOUBAO-PPT-REPAIR-LOSS"],
        "exceptionExplanation": "该finding同时定位Mac修复后放映完整性与图表对象编辑性两个互不替代的任务结果；两个维度均按子项目实际得分，未叠加固定罚分。",
    }
    report["methodology"]["nativeOpenScoringPolicy"] = {
        "scoredSpecimen": "与原件SHA-256一致的首次打开审查副本。",
        "repairCopyRole": "修复副本只用于量化可恢复性、修复后内容损失和后续编辑能力，不替代首次打开体验。",
        "formula": "首次进入路径4分+可见内容保全3分+原生会话完成2分+保存关闭重开1分。",
        "entryRule": "无提示直接打开4分；一次非修复选择后完整打开3分；必须修复或指定应用仍不可进入均为0分。两者差异由修复后的内容保全、会话完成和保存重开分体现。",
        "preservationRule": "容器、核心文本/数据、图表/媒体三类各1分，按修复后保全比例以0.5分为最小步长。",
        "userFrictionTreatment": "打不开、修复提示、字段更新提示、修复后损失与保存重开分别落入上述四个子项；同一观察不叠加无公式的文件级固定罚分。",
        "platformBoundary": "只归因于已实测平台和应用版本；未复测平台保持‘未验证’。",
    }
    meta.setdefault("buildProvenance", {})["v44Baseline"] = {
        "path": str(baseline_path.resolve()),
        "sha256": sha256(baseline_path),
    }
    adjudication_script = Path(__file__).resolve()
    meta["buildProvenance"]["v44Adjudication"] = {
        "script": str(adjudication_script),
        "scriptSha256": sha256(adjudication_script),
        "input": str(baseline_path.resolve()),
        "inputSha256": sha256(baseline_path),
        "output": str(output_path.resolve()),
        "outputSha256Policy": "输出文件SHA-256写入发布清单；JSON不能自包含自身最终哈希，否则形成循环引用。",
        "executedAt": meta["generatedAt"],
    }
    limitations = [
        "五张回应截图是各AI工具阅读报告后生成的自评，不是产品公司、负责人或员工的正式声明；本报告不宣称任何厂商已认可。",
        "仅覆盖宇树科技主题的一次连续六任务链和30件固定终稿，不能外推为产品总体能力、稳定生成率或未来版本表现。",
        "五款均按用户确认使用测试时点各自可选的最强配置，但模型、算力、成本、工具权限和自动路由并未统一，因此不是严格控制实验。",
        "Excel只核对公开列示的32项核心事实；不等同于五本工作簿全部数字的逐项全量鉴证。",
        "原生应用体验固定在macOS 26.5.2、Office 16.112.3与Chrome 152；Windows PowerPoint和独立重新下载尚未交叉验证。",
        "本报告由单一评审者完成；判断步长压力测试不是置信区间、抽样误差、评审者一致性或厂商能力区间。",
    ]
    meta["limitations"] = limitations
    profiles = meta.get("toolProfiles", {})
    profiles["WorkBuddy"].update({
        "summary": "本次固定样本中，Excel核心方向和量级总体可用，但存在旧稿尾差、来源定位不足和预测语态问题；Word首次把42.02亿元拟募集改为到账，随后传播。",
        "friction": "Excel若干值使用旧申报稿尾数或约数，来源缺报告级直链与页码；预测完成语态和下游资金属性改写需要修正。",
        "critical": "2.78/2.88亿元与51.07%的旧定性已在异议裁决中更正；42.02亿元拟募集→到账的链路属性变化仍由原件支持。",
    })
    profiles["Qoder"].update({
        "summary": "本次固定样本中，Excel和Word信息深度强；PPT一处核心标题方向错误仍需修正，普通/水墨图的同根重复扣分与HTML量表已在v4.4更正。",
        "friction": "32页Word导航为空；PPT第10页把仍为正值写成‘转负’；两张图仍有局部叠印或裁切，HTML移动端适配不足。",
        "critical": "G2只针对投资人材料核心标题的绝对正负反转，并明确为1/20页、一次文字修改可修；不代表整份PPT低质。",
    })
    profiles["千问"]["friction"] = "5张Excel图均把年份当系列；HTML基础导航与悬浮有效，但没有改变分析视图的增益控件，移动端仍有裁切。"

    report["testProtocol"] = {
        "title": "六任务连续工作流与样本配置",
        "prompts": [{"step": index, "artifactKind": KINDS[index - 1], "title": title, "prompt": prompt} for index, (title, prompt) in enumerate(PROMPTS, 1)],
        "design": {
            "comparisonUnit": "五款工具各完成同一组六个连续Prompt，每款固定一件Excel、Word、PPT、普通图、水墨图和HTML终稿。",
            "configuration": "用户确认五款均选择测试时点各自可用的最强档；配置截图和用量旁证不计分。",
            "notControlled": "未统一基础模型、算力、成本、工具权限、自动路由、重复生成次数或随机顺序，因此是按实际配置开展的真实工作流比较，不是严格因果实验。",
        },
    }
    presentation = report.setdefault("presentation", {})
    presentation.setdefault("executiveSummary", {})["rankingPolicy"] = "显示可复算点估计顺序，同时给出单评审者对锚定式混合判断和专家判断项的单步压力测试、S组和情景重算次序；不主张统计显著、概率区间或产品普遍优劣。"
    presentation["executiveSummary"]["evidencePolicy"] = "合理异议只有在固定原件、原生实测或五家对称规则支持时才改分；每项变更保留改前、改后、理由和反证条件。"
    presentation.setdefault("navigationGroups", []).insert(0, {"id": "protocol", "label": "0 测试流程", "sectionIds": ["protocol"]}) if not any(row.get("id") == "protocol" for row in presentation.get("navigationGroups", [])) else None
    if not any(row.get("id") == "challenges" for row in presentation.get("navigationGroups", [])):
        presentation["navigationGroups"].append({"id": "challenges", "label": "8 异议裁决", "sectionIds": ["challenges"]})
    labels = presentation.setdefault("publicationLabels", {})
    labels.update({
        "ai_generated_tool_self_review_not_vendor_statement": "AI工具自评（非厂商正式声明）",
        "methodology_correction_from_symmetric_retest_not_vendor_claim": "对称复测后的方法更正（非厂商声明）",
        "accepted": "异议成立",
        "partially_accepted": "异议部分成立",
        "rejected": "异议不成立",
        "retired_noncausal": "已退出活动排名（非因果诊断）",
    })
    for visual in presentation.get("visualRegistry", []):
        if visual.get("id") in {"executive-rankings", "ranking-main"}:
            visual["scopeNote"] = "独立终稿点估计；横轴0—100分；同时展示单评审者判断步长压力测试、S组与情景重算次序。"
    presentation.setdefault("printPageFurniture", {})["version"] = "v4.4"
    presentation["printPageFurniture"]["summaryExcerptNote"] = "管理层摘要为完整报告节选；异议裁决、原始截图与逐条理由见第08章。"
    report.setdefault("contentInventory", {})["challenges"] = {"count": len(report["challenges"]["items"]), "entry": "第8章工具自评异议复核"}
    report["contentInventory"]["challengeResponses"] = {"count": len(report["challenges"]["responses"]), "entry": "第8章五张原始自评截图"}
    report["contentInventory"]["assessmentClasses"]["scoreEffect"] = "不改变点估计；混合判断和专家判断项用于单评审者判断步长压力测试。"
    revision_rows = report.get("scoreRevisionLedger", {}).get("artifactChanges", [])
    report.setdefault("versionHistory", []).append({
        "version": "4.4",
        "status": "published_after_qa" if final else "candidate_qa_pending",
        "title": "v4.4工具自评异议复核修订版",
        "summary": "接受有固定原件或对称规则支持的异议并重算；退休非因果传播排名；新增逐维度截断的单评审者判断步长压力测试、情景重算次序和逐项裁决台账。",
        "baselineV43JsonSha256": sha256(baseline_path),
        "scoreChanges": [
            {
                "artifactId": row["artifactId"],
                "tool": row["tool"],
                "kind": row["kind"],
                "from": row["v43Score"],
                "to": row["v44Score"],
                "delta": row["delta"],
            }
            for row in revision_rows
        ],
    })


def validate(report: dict[str, Any], baseline: dict[str, Any]) -> None:
    """Fail closed on conservation, references, score arithmetic and claims."""
    expected_scores = {
        "artifact:workbuddy:excel": 78.1,
        "artifact:qoder:image": 93.1,
        "artifact:qoder:ink": 88.0,
        "artifact:doubao:html": 89.0,
        "artifact:qianwen:html": 78.0,
        "artifact:qoder:html": 77.5,
        "artifact:workbuddy:html": 67.5,
        "artifact:zhikuncode:html": 93.5,
    }
    for artifact_id, expected in expected_scores.items():
        actual = report["scores"]["artifacts"][artifact_id]["qualityScore"]
        if actual != expected:
            raise ValueError(f"score mismatch {artifact_id}: {actual} != {expected}")
    conserved = {
        "artifacts": 30,
        "scenarios": 32,
        "scenarioRuns": 180,
        "coverageItems": 324,
        "findings": 200,
        "evidence": 741,
        "media": 710,
        "facts": 32,
        "sources": 11,
    }
    for key, expected in conserved.items():
        if len(report[key]) != expected:
            raise ValueError(f"content conservation failed for {key}: {len(report[key])} != {expected}")

    def indexed(rows: list[dict[str, Any]], entity: str) -> dict[str, dict[str, Any]]:
        result = {row["id"]: row for row in rows}
        if len(result) != len(rows):
            raise ValueError(f"duplicate {entity} id")
        return result

    indexes = {key: indexed(report[key], key) for key in conserved}
    baseline_indexes = {key: indexed(baseline[key], f"baseline {key}") for key in conserved}
    for key in conserved:
        if set(indexes[key]) != set(baseline_indexes[key]):
            missing = sorted(set(baseline_indexes[key]) - set(indexes[key]))
            added = sorted(set(indexes[key]) - set(baseline_indexes[key]))
            raise ValueError(f"{key} ID conservation failed: missing={missing[:3]}, added={added[:3]}")
    if {row["id"] for row in report.get("propagation", [])} != {row["id"] for row in baseline.get("propagation", [])}:
        raise ValueError("propagation cluster ID set changed")

    # Evidence inventories are immutable; adjudication may narrow a finding,
    # but may not silently replace its underlying files, facts or test records.
    for key in ["scenarios", "scenarioRuns", "coverageItems", "evidence", "media", "facts", "sources"]:
        if report[key] != baseline[key]:
            raise ValueError(f"immutable evidence inventory changed: {key}")
    for artifact_id, artifact in indexes["artifacts"].items():
        original = artifact["original"]
        baseline_artifact = baseline_indexes["artifacts"][artifact_id]
        if original != baseline_artifact["original"] or artifact.get("auditCopies") != baseline_artifact.get("auditCopies"):
            raise ValueError(f"artifact provenance changed: {artifact_id}")
        if original.get("sha256") != artifact.get("auditCopies", {}).get("firstOpen", {}).get("copySha256"):
            raise ValueError(f"first-open copy is not byte-identical: {artifact_id}")

    criterion_definitions = definitions(report)
    baseline_definition_ids = set(definitions(baseline))
    if set(criterion_definitions) != baseline_definition_ids:
        raise ValueError("criterion definition ID set changed")
    for criterion_id, definition in criterion_definitions.items():
        if float(definition["weight"]) != float(definitions(baseline)[criterion_id]["weight"]):
            raise ValueError(f"criterion weight changed: {criterion_id}")
        if definition.get("assessmentClass") == "mechanical" and not definition.get("fullyAtomizedAcrossFiveSamples"):
            raise ValueError(f"non-atomized criterion mislabeled mechanical: {criterion_id}")
    finding_ids = set(indexes["findings"])
    evidence_ids = set(indexes["evidence"])
    media_ids = set(indexes["media"])
    source_ids = set(indexes["sources"])
    artifact_ids = set(indexes["artifacts"])
    scenario_ids = set(indexes["scenarios"])
    coverage_ids = set(indexes["coverageItems"])

    for fact in report["facts"]:
        if fact["sourceId"] not in source_ids:
            raise ValueError(f"fact source missing: {fact['id']}")
    for evidence in report["evidence"]:
        if evidence.get("artifactId") and evidence["artifactId"] not in artifact_ids:
            raise ValueError(f"evidence artifact missing: {evidence['id']}")
        if evidence.get("mediaId") and evidence["mediaId"] not in media_ids:
            raise ValueError(f"evidence media missing: {evidence['id']}")
    for media in report["media"]:
        if media.get("artifactId") and media["artifactId"] not in artifact_ids:
            raise ValueError(f"media artifact missing: {media['id']}")
    for run in report["scenarioRuns"]:
        if run["artifactId"] not in artifact_ids or run["scenarioId"] not in scenario_ids:
            raise ValueError(f"scenario run target missing: {run['id']}")
        if not set(run.get("evidenceIds", [])) <= evidence_ids or not set(run.get("coverageItemIds", [])) <= coverage_ids:
            raise ValueError(f"scenario run evidence/coverage missing: {run['id']}")
    for coverage in report["coverageItems"]:
        if coverage["artifactId"] not in artifact_ids:
            raise ValueError(f"coverage artifact missing: {coverage['id']}")
        if not set(coverage.get("evidenceIds", [])) <= evidence_ids:
            raise ValueError(f"coverage evidence missing: {coverage['id']}")
    for item in report["findings"]:
        if item.get("artifactId") not in artifact_ids:
            raise ValueError(f"finding artifact missing: {item['id']}")
        if item.get("criterionId") and item["criterionId"] not in criterion_definitions:
            raise ValueError(f"finding criterion missing: {item['id']}")
        if not set(item.get("evidenceIds", [])) <= evidence_ids or not set(item.get("sourceIds", [])) <= source_ids:
            raise ValueError(f"finding evidence/source missing: {item['id']}")
        if item.get("immediateUpstreamArtifactId") and item["immediateUpstreamArtifactId"] not in artifact_ids:
            raise ValueError(f"finding upstream artifact missing: {item['id']}")
        if not item.get("impactUnitId") or not item.get("impactUnits"):
            raise ValueError(f"finding lacks impact unit: {item['id']}")

    score_artifacts = report["scores"]["artifacts"]
    if set(score_artifacts) != artifact_ids:
        raise ValueError("score artifact ID set changed")
    for artifact_id, score in score_artifacts.items():
        kind = indexes["artifacts"][artifact_id]["kind"]
        expected_criterion_ids = {row["id"] for row in report["criteriaDefinitions"][kind]}
        rows = score["criterionScores"]
        if {row["criterionId"] for row in rows} != expected_criterion_ids or len(rows) != len(expected_criterion_ids):
            raise ValueError(f"criterion score set mismatch: {artifact_id}")
        total = 0.0
        for score_row in rows:
            definition = criterion_definitions[score_row["criterionId"]]
            weight = float(definition["weight"])
            earned = float(score_row["weighted"])
            if not -1e-9 <= earned <= weight + 1e-9:
                raise ValueError(f"criterion score outside bounds: {artifact_id}/{score_row['criterionId']}")
            if score_row.get("subitemScores"):
                sub_max = sum(float(subitem["maxPoints"]) for subitem in score_row["subitemScores"])
                sub_earned = sum(float(subitem["earnedPoints"]) for subitem in score_row["subitemScores"])
                if abs(sub_max - weight) > 1e-8 or abs(rounded(sub_earned) - earned) > 1e-8:
                    raise ValueError(f"subitem arithmetic mismatch: {artifact_id}/{score_row['criterionId']}")
            if score_row.get("checklistSource"):
                checklist_path = Path(score_row["checklistSource"]["path"])
                if not checklist_path.is_file() or sha256(checklist_path) != score_row["checklistSource"]["sha256"]:
                    raise ValueError(f"checklist source missing or SHA mismatch: {artifact_id}/{score_row['criterionId']}")
            if not set(score_row.get("findingIds", [])) <= finding_ids:
                raise ValueError(f"criterion finding missing: {artifact_id}/{score_row['criterionId']}")
            if not set(score_row.get("evidenceIds", [])) <= evidence_ids:
                raise ValueError(f"criterion evidence missing: {artifact_id}/{score_row['criterionId']}")
            links = score_row.get("findingImpactLinks", [])
            if {link["findingId"] for link in links} != set(score_row.get("findingIds", [])):
                raise ValueError(f"criterion impact links not closed: {artifact_id}/{score_row['criterionId']}")
            for link in links:
                if link["criterionId"] != score_row["criterionId"] or not link.get("impactUnitId"):
                    raise ValueError(f"invalid impact link: {artifact_id}/{score_row['criterionId']}")
            total += earned
        if abs(rounded(total) - float(score["qualityScore"])) > 1e-9:
            raise ValueError(f"artifact score does not equal criterion sum: {artifact_id}")
        if score.get("causalQualityScore") is not None or score.get("causalRestoredPoints") is not None:
            raise ValueError(f"retired causal diagnostic remains active: {artifact_id}")

    gate_artifacts = report.get("deliveryGates", {}).get("artifacts", {})
    if set(gate_artifacts) != artifact_ids:
        raise ValueError("delivery-gate artifact set changed")
    for artifact_id, gate in gate_artifacts.items():
        if score_artifacts[artifact_id].get("deliveryGateCode") != gate.get("code"):
            raise ValueError(f"score/gate interface mismatch: {artifact_id}")
        if not set(gate.get("findingIds", [])) <= finding_ids:
            raise ValueError(f"gate finding missing: {artifact_id}")
        if {row["findingId"] for row in gate.get("terminalRiskComponents", [])} - finding_ids:
            raise ValueError(f"gate risk component finding missing: {artifact_id}")

    # The only finding cited by two score dimensions must resolve to two
    # explicitly different user-task outcomes; no other same-impact duplicate
    # is allowed to create two independent dimension losses.
    impact_links_by_finding: dict[str, list[dict[str, Any]]] = {}
    for score in score_artifacts.values():
        for score_row in score["criterionScores"]:
            for link in score_row.get("findingImpactLinks", []):
                impact_links_by_finding.setdefault(link["findingId"], []).append(link)
    for finding_id, links in impact_links_by_finding.items():
        if len(links) <= 1:
            continue
        impact_units = {link["impactUnitId"] for link in links}
        if finding_id != "NATIVE-DOUBAO-PPT-REPAIR-LOSS" or len(impact_units) != 2:
            raise ValueError(f"unresolved same-root multi-criterion scoring: {finding_id}")

    if report["contentInventory"]["scenarioRecords"]["count"] != 202:
        raise ValueError("published scenario-record count changed")
    if set(report["rankings"]) != {"independent_equalTask", "independent_practical"}:
        raise ValueError("active rankings must contain exactly two independent views")
    if report["challenges"]["meta"]["formalVendorResponsesReceived"] != 0:
        raise ValueError("vendor response claim must remain zero")
    challenge_items = indexed(report["challenges"]["items"], "challenge")
    for challenge in challenge_items.values():
        if not set(challenge.get("artifactIds", [])) <= artifact_ids:
            raise ValueError(f"challenge artifact missing: {challenge['id']}")
        if not set(challenge.get("findingIds", [])) <= finding_ids:
            raise ValueError(f"challenge finding missing: {challenge['id']}")
        if not set(challenge.get("criterionIds", [])) <= set(criterion_definitions):
            raise ValueError(f"challenge criterion missing: {challenge['id']}")
        if not set(challenge.get("decisionEvidenceIds", [])) <= evidence_ids:
            raise ValueError(f"challenge evidence missing: {challenge['id']}")
        if {row.get("evidenceId") for row in challenge.get("decisionEvidenceRefs", [])} != set(challenge.get("decisionEvidenceIds", [])):
            raise ValueError(f"challenge evidence references not closed: {challenge['id']}")
        for link in challenge.get("decisionCriterionLinks", []):
            if link.get("artifactId") not in artifact_ids or link.get("criterionId") not in criterion_definitions:
                raise ValueError(f"challenge criterion link target missing: {challenge['id']}")
            if not set(link.get("evidenceIds", [])) <= evidence_ids or not set(link.get("findingIds", [])) <= finding_ids:
                raise ValueError(f"challenge criterion link evidence missing: {challenge['id']}")
        for finding_id in challenge.get("findingIds", []):
            if challenge["id"] not in indexes["findings"][finding_id].get("challengeIds", []):
                raise ValueError(f"challenge→finding reverse link missing: {challenge['id']}/{finding_id}")
        if challenge["disposition"]["scoreEffectStatus"] == "artifact_score_recomputed":
            if not challenge["criterionIds"] or not challenge["decisionEvidenceIds"]:
                raise ValueError(f"score-changing challenge lacks criterion/evidence: {challenge['id']}")
    for item in report["findings"]:
        for challenge_id in item.get("challengeIds", []):
            if challenge_id not in challenge_items or item["id"] not in challenge_items[challenge_id].get("findingIds", []):
                raise ValueError(f"finding→challenge reverse link missing: {item['id']}/{challenge_id}")

    expected_batches = {
        "SYM-HTML-RUNTIME", "SYM-HTML-INTERACTION", "SYM-RANK-JUDGMENT-SENSITIVITY",
        "SYM-SAME-ROOT-SCAN", "SYM-G2-CORE-DIRECTION", "SYM-WORD-LOCATOR",
        "SYM-NATIVE-FIRST-OPEN",
    }
    batches = indexed(report["challenges"]["symmetryBatches"], "symmetry batch")
    if set(batches) != expected_batches:
        raise ValueError("symmetry batch set mismatch")
    required_run_fields = {"tool", "artifactIds", "ruleId", "before", "actual", "result", "evidenceIds", "scoreChange", "reviewer", "completedAt"}
    for batch in batches.values():
        if batch["status"] != "completed_5_of_5" or batch["tools"] != TOOLS:
            raise ValueError(f"incomplete symmetry batch: {batch['id']}")
        runs = batch.get("runs", [])
        if len(runs) != 5 or [run["tool"] for run in runs] != TOOLS:
            raise ValueError(f"symmetry batch does not contain five ordered tool runs: {batch['id']}")
        for run in runs:
            if not required_run_fields <= set(run) or run["ruleId"] != batch["id"]:
                raise ValueError(f"symmetry run schema mismatch: {batch['id']}/{run.get('tool')}")
            if not set(run["artifactIds"]) <= artifact_ids or not set(run["evidenceIds"]) <= evidence_ids:
                raise ValueError(f"symmetry run reference missing: {batch['id']}/{run['tool']}")
    if len(report["challenges"]["items"]) != 17 or len(report["challenges"]["responses"]) != 5:
        raise ValueError("challenge ledger inventory mismatch")
    for response in report["challenges"]["responses"]:
        screenshot = Path(__file__).resolve().parent / response["screenshotPath"]
        if not screenshot.is_file() or sha256(screenshot) != response["screenshotSha256"]:
            raise ValueError(f"challenge screenshot missing or SHA mismatch: {response['tool']}")
    revision = report["scoreRevisionLedger"]
    actual_changed = sum(
        abs(float(score["qualityScore"]) - float(baseline["scores"]["artifacts"][artifact_id]["qualityScore"])) > 1e-9
        for artifact_id, score in score_artifacts.items()
    )
    if revision["changedArtifactCount"] != actual_changed or revision["unchangedArtifactCount"] != 30 - actual_changed:
        raise ValueError("score revision ledger inventory mismatch")
    for artifact_change in revision["artifactChanges"]:
        criterion_delta = rounded(sum(float(row["delta"]) for row in artifact_change["criterionChanges"]))
        if criterion_delta != rounded(artifact_change["delta"]):
            raise ValueError(f"revision criterion deltas do not sum: {artifact_change['artifactId']}")
        for criterion_change in artifact_change["criterionChanges"]:
            if criterion_change.get("linkageStatus") != "closed_criterion_challenge_evidence":
                raise ValueError(f"revision linkage incomplete: {artifact_change['artifactId']}/{criterion_change['criterionId']}")

    for kind, definitions_for_kind in report["criteriaDefinitions"].items():
        total = sum(float(row["weight"]) for row in definitions_for_kind)
        if abs(total - 100.0) > 1e-9:
            raise ValueError(f"criterion weights do not sum to 100 for {kind}: {total}")
    if report.get("propagationStatus", {}).get("causalGraphValidated") is not False or report["propagationStatus"].get("rankingUse") is not False:
        raise ValueError("descriptive propagation clusters are still presented as causal/ranking data")

    for ranking_id, ranking in report["rankings"].items():
        if abs(sum(float(value) for value in ranking["weights"].values()) - 1.0) > 1e-9:
            raise ValueError(f"ranking weights do not sum to 1: {ranking_id}")
        expected_order = sorted(
            ranking["rows"],
            key=lambda row: (-row["score"], -row["nativeUsabilityIndex"], -row["excelFactIndex"], -row["taskCompletionIndex"], row["tool"]),
        )
        if [row["tool"] for row in expected_order] != [row["tool"] for row in ranking["rows"]]:
            raise ValueError(f"ranking order mismatch: {ranking_id}")
        for index, row in enumerate(ranking["rows"], 1):
            if row["pointEstimateOrder"] != index:
                raise ValueError(f"point order mismatch: {ranking_id}/{row['tool']}")
            recomputed_score = rounded(sum(
                float(row["artifactScores"][kind]) * float(ranking["weights"][kind]) for kind in KINDS
            ))
            if recomputed_score != row["score"]:
                raise ValueError(f"ranking score mismatch: {ranking_id}/{row['tool']}")
            down = rounded(max((float(component["downwardRoomApplied"]) for component in row["judgmentSensitivityComponents"]), default=0.0))
            up = rounded(max((float(component["upwardRoomApplied"]) for component in row["judgmentSensitivityComponents"]), default=0.0))
            joint_down = rounded(sum(float(component["downwardRoomApplied"]) for component in row["judgmentSensitivityComponents"]))
            joint_up = rounded(sum(float(component["upwardRoomApplied"]) for component in row["judgmentSensitivityComponents"]))
            for component in row["judgmentSensitivityComponents"]:
                score_row = next(
                    item for item in score_artifacts[component["artifactId"]]["criterionScores"]
                    if item["criterionId"] == component["criterionId"]
                )
                definition = criterion_definitions[component["criterionId"]]
                maximum = float(definition["weight"])
                earned = float(score_row["weighted"])
                step = maximum * 0.1
                kind = indexes["artifacts"][component["artifactId"]]["kind"]
                expected_down = rounded(min(earned, step) * float(ranking["weights"][kind]), 6)
                expected_up = rounded(min(maximum - earned, step) * float(ranking["weights"][kind]), 6)
                if component["assessmentClass"] not in ASSESSMENT_CLASSES_SENSITIVE:
                    raise ValueError(f"mechanical criterion entered sensitivity test: {ranking_id}/{row['tool']}/{component['criterionId']}")
                if component["downwardRoomApplied"] != expected_down or component["upwardRoomApplied"] != expected_up:
                    raise ValueError(f"sensitivity component mismatch: {ranking_id}/{row['tool']}/{component['criterionId']}")
            if rounded(row["score"] - row["judgmentSensitivityLower"]) != down:
                raise ValueError(f"lower sensitivity envelope mismatch: {ranking_id}/{row['tool']}")
            if rounded(row["judgmentSensitivityUpper"] - row["score"]) != up:
                raise ValueError(f"upper sensitivity envelope mismatch: {ranking_id}/{row['tool']}")
            if row.get("jointExtremeDownwardMovement") != joint_down or row.get("jointExtremeUpwardMovement") != joint_up:
                raise ValueError(f"joint extreme sensitivity mismatch: {ranking_id}/{row['tool']}")
            if not 0 <= row["judgmentSensitivityLower"] <= row["score"] <= row["judgmentSensitivityUpper"] <= 100:
                raise ValueError(f"sensitivity envelope outside bounds: {ranking_id}/{row['tool']}")
            expected_best = 1 + sum(
                other["judgmentSensitivityLower"] > row["judgmentSensitivityUpper"]
                for other in ranking["rows"] if other is not row
            )
            expected_worst = len(ranking["rows"]) - sum(
                row["judgmentSensitivityLower"] > other["judgmentSensitivityUpper"]
                for other in ranking["rows"] if other is not row
            )
            if row["possibleBestPointOrder"] != expected_best or row["possibleWorstPointOrder"] != expected_worst:
                raise ValueError(f"possible point-order range mismatch: {ranking_id}/{row['tool']}")

    release_status = "final_v4_4_fixed_environment" if report["meta"]["publicationStatus"] == "published_after_v44_qa" else "v4_4_candidate_qa_pending"
    ranking_status = "final_v44_adjudicated" if release_status.startswith("final") else "candidate_v44_qa_pending"
    if report["meta"]["status"] != release_status or report["scores"]["status"] != release_status:
        raise ValueError("meta/scores release status mismatch")
    if report["qualityScores"]["status"] != ranking_status or report["rankingPerspectives"]["status"] != ranking_status:
        raise ValueError("ranking interface status mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    baseline = copy.deepcopy(report)
    apply_score_decisions(report)
    recompute_scores(report)
    classify_assessment_modes(report)
    assign_impact_units(report)
    build_rankings(report)
    sync_interfaces(report)
    build_challenges(report)
    build_score_revision_ledger(report, baseline)
    update_presentation(report, args.input, args.output, args.final)
    validate(report, baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "sha256": sha256(args.output),
        "status": report["meta"]["status"],
        "rankings": {key: [(row["pointEstimateOrder"], row["tool"], row["score"], f"{row['possibleBestRank']}-{row['possibleWorstRank']}", row["uncertaintyGroup"]) for row in value["rows"]] for key, value in report["rankings"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
