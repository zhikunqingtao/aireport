#!/usr/bin/env python3
"""Build v4.5: symmetric fact scoring and claim-lineage adjudication.

The script starts from the frozen v4.4 JSON.  It does not reopen Office files,
does not use vendor self-reviews as evidence, and does not run browser tests.
Only retained workbook cells/XML/text, the existing evidence ledger and the 32
published official benchmark facts are used.
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
WEIGHTS = {
    "equalTask": {kind: 1 / 6 for kind in KINDS},
    "practical": {"excel": .25, "word": .20, "ppt": .20, "image": .10, "ink": .10, "html": .15},
}


def r(value: float, digits: int = 2) -> float:
    return round(float(value) + 1e-12, digits)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def artifact_id(tool: str, kind: str) -> str:
    slugs = {"豆包": "doubao", "千问": "qianwen", "Qoder": "qoder", "WorkBuddy": "workbuddy", "ZhikunCode": "zhikuncode"}
    return f"artifact:{slugs[tool]}:{kind}"


def definitions(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for rows in report["criteriaDefinitions"].values() for row in rows}


def criterion(report: dict[str, Any], aid: str, suffix: str) -> dict[str, Any]:
    return next(row for row in report["scores"]["artifacts"][aid]["criterionScores"] if row["criterionId"].endswith(f":{suffix}"))


def set_criterion(report: dict[str, Any], aid: str, suffix: str, earned: float, basis: str,
                  subitems: list[dict[str, Any]], finding_ids: list[str] | None = None) -> None:
    row = criterion(report, aid, suffix)
    weight = definitions(report)[row["criterionId"]]["weight"]
    row.update({
        "weighted": r(earned),
        "rating0To5": r(earned / weight * 5, 6),
        "basis": basis,
        "subitemScores": subitems,
        "findingIds": finding_ids if finding_ids is not None else row.get("findingIds", []),
        "adjudicationVersion": "4.5",
        "assessmentClassApplied": "mechanical",
        "assessmentClassReason": "按v4.5公开的原子子项与固定分母直接重算。",
    })


# Every asserted benchmark row receives two independent credits.  Numerical
# credit follows {1, .8, .5, 0}; scope credit follows {1, .5, 0}.  Unasserted
# benchmark rows never enter the denominator.
EXACT = (1.0, 1.0, "与正式基准一致", "exact")


FACT_RULE = {
    "value": {"exact": 1.0, "labelled_approx_le_0_5pct": .8, "unlabelled_le_0_5pct": .5, "wrong": 0.0},
    "scope": {"exact": 1.0, "ambiguous_disclosed": .5, "mixed_or_wrong": 0.0},
    "weights": {"value": .7, "scope": .3},
}


LOCATORS = {
    "豆包": {
        "rev": "02_原始数据_年度!C5:E5", "np": "02_原始数据_年度!C9:E9", "adj": "02_原始数据_年度!C10:E10",
        "cfo": "02_原始数据_年度!C24:E24", "gm": "02_原始数据_年度!C12:E13", "rd": "02_原始数据_年度!C17:E18",
        "product": "04_业务经营数据!C5:G18", "employee": "02_原始数据_年度!E26:E27", "h1": "03_原始数据_期间!H5:H10",
        "ipo": "06_IPO与募投!C5:C27", "official": "04_业务经营数据!C34:C36",
    },
    "千问": {
        "rev": "原始数据-年度!C4:E4", "np": "原始数据-年度!C10:E10", "adj": "原始数据-年度!C15:E15",
        "cfo": "原始数据-年度!C21:E21", "gm": "原始数据-年度!C22:E24", "rd": "原始数据-年度!C26:E28",
        "product": "原始数据-年度!C35:E41", "employee": "原始数据-年度（人员行）", "h1": "原始数据-期间与IPO!C4:F14",
        "ipo": "原始数据-期间与IPO!C23:F36", "official": "原始数据-年度（人形出货行）",
    },
    "Qoder": {
        "rev": "03_财务原始数据!C5:E5", "np": "03_财务原始数据!C13:E15", "adj": "03_财务原始数据!C13:E15",
        "cfo": "03_财务原始数据!C48:E51", "gm": "03_财务原始数据!C37:E37", "rd": "03_财务原始数据!C50:E54",
        "product": "04_业务结构原始数据", "employee": "04_业务结构原始数据（人员行）", "h1": "03_财务原始数据!C88:C106",
        "ipo": "02_发行上市原始数据", "official": "04_业务结构原始数据（出货行）",
    },
    "WorkBuddy": {
        "rev": "原始数据-财务!C3:E3", "np": "原始数据-财务!C4:E4", "adj": "原始数据-财务!C5:E5",
        "cfo": "原始数据-财务!C6:E6", "gm": "原始数据-财务（毛利率行）", "rd": "原始数据-财务（费用行）",
        "product": "原始数据-业务!B5:F30", "employee": "原始数据-业务（人员行）", "h1": "原始数据-财务（2026H1区）",
        "ipo": "原始数据-业务!B43:F50", "official": "原始数据-业务（人形出货行）",
    },
    "ZhikunCode": {
        "rev": "原始数据_财务!C5:F5", "np": "原始数据_财务!C6:F6", "adj": "原始数据_财务!C7:F7",
        "cfo": "原始数据_财务!C11:F11", "gm": "原始数据_财务!C8:F8", "rd": "原始数据_财务!C9:F9",
        "product": "原始数据_财务!B28:H31", "employee": "原始数据_财务!B65:G68", "h1": "原始数据_财务!F5:F11",
        "ipo": "原始数据_IPO与股东!B6:B49", "official": "原始数据_财务!F49:G49",
    },
}

SOURCE_SHEETS = {
    "豆包": "01_资料来源",
    "千问": "说明与来源",
    "Qoder": "01_资料来源",
    "WorkBuddy": "资料来源",
    "ZhikunCode": "资料来源",
}

CONSISTENCY_SUBTESTS = [
    ("key-values", "关键数值忠实度", "关键数值相对允许上游未发生错误或替换"),
    ("definition-period", "定义与报告期忠实度", "指标定义、分母和报告期相对允许上游未发生改变"),
    ("fact-attribute", "事实/预测/计划属性忠实度", "实际、预测、计划和到账等属性相对允许上游未发生改变"),
    ("new-claim-provenance", "新增重要主张来源合规", "新增重要主张来自该节点允许使用的上游文件或截止日前可直接追溯的官方材料"),
    ("new-claim-cutoff", "新增重要主张截止日合规", "新增重要主张未使用2026-08-30之后发布的材料"),
]

# 25分一致性维度统一拆为五个5分子项。这里只列失败子项；未列明即通过。
# G0/G1/G2是独立使用安全闸门，不参与本表的连续分换算。
CONSISTENCY_FAILURES = {
    ("Qoder", "ppt"): {
        "key-values": {
            "findingIds": ["QODER-P-N01"],
            "reason": "第10页核心标题把两项仍为正值的指标写成‘双双转负’，发生绝对正负方向反转。",
        },
    },
    ("Qoder", "html"): {
        "key-values": {
            "findingIds": ["Qoder-html-01"],
            "reason": "把净差额31,254.23万元与股份支付34,906.55万元混为同一数值。",
        },
    },
    ("WorkBuddy", "word"): {
        "fact-attribute": {
            "findingIds": ["WORKBUDDY-W-N01"],
            "reason": "首次把上游Excel的42.02亿元拟募集/计划金额改写为已到账。",
        },
        "new-claim-cutoff": {
            "findingIds": ["WORKBUDDY-W-N02"],
            "reason": "首次引入明确标注来源日期为2026-09-02的Figure AI比较，晚于截止日。",
        },
    },
}
for _kind, _fund_finding, _figure_finding in [
    ("ppt", "WORKBUDDY-P-N01", "WORKBUDDY-P-N02"),
    ("image", "WorkBuddy-image-01", "WORKBUDDY-IMAGE-V2-FIGURE"),
    ("ink", "WorkBuddy-ink-01", "WORKBUDDY-INK-V2-FIGURE"),
    ("html", "WorkBuddy-html-01", "WORKBUDDY-HTML-V2-FIGURE"),
]:
    CONSISTENCY_FAILURES[("WorkBuddy", _kind)] = {
        "fact-attribute": {
            "findingIds": [_fund_finding],
            "reason": "完全继承Word节点已经发生的‘拟募集/计划→已到账’属性改写；终稿独立使用视角仍显示该风险。",
        },
        "new-claim-cutoff": {
            "findingIds": [_figure_finding],
            "reason": "完全继承Word节点首次引入的2026-09-02 Figure AI比较；终稿独立使用视角仍显示该风险。",
        },
    }


def fact_group(fact_id: str) -> str:
    if fact_id.startswith("F-REV"): return "rev"
    if fact_id.startswith("F-NP"): return "np"
    if fact_id.startswith("F-ADJ"): return "adj"
    if fact_id.startswith("F-CFO"): return "cfo"
    if fact_id.startswith("F-GM"): return "gm"
    if fact_id in {"F-RD", "F-SELL-2025"}: return "rd"
    if fact_id.startswith("F-HUM") or fact_id == "F-QUAD-REV": return "product"
    if fact_id == "F-EMPLOYEE": return "employee"
    if fact_id.startswith("F-H1"): return "h1"
    if fact_id in {"F-IPO", "F-FUND-RAISED", "F-FUND-PLAN", "F-LISTING"}: return "ipo"
    return "official"


# Only benchmark facts actually asserted in the workbook are listed.  Exact
# rows inherit the official benchmark display value; exceptions preserve the
# workbook wording and the precise reason for partial or zero credit.
UNCLAIMED = {
    "豆包": {"F-H1-PL", "F-H1-BS", "F-OFFICIAL-SHIP"},
    "千问": {"F-OFFICIAL-SHIP"},
    "Qoder": {"F-OFFICIAL-SHIP"},
    "WorkBuddy": {"F-CFO-2023", "F-EMPLOYEE", "F-H1-CFO", "F-FUND-RAISED", "F-OFFICIAL-SHIP"},
    "ZhikunCode": {"F-GM-TOTAL", "F-SELL-2025", "F-H1-BS", "F-OFFICIAL-SHIP"},
}


OVERRIDES: dict[str, dict[str, tuple[float, float, str, str]]] = {
    "豆包": {
        "F-SELL-2025": (.8, 1, "14,120.93万元；标注按费用率反推且待核", "labelled_approx_le_0_5pct"),
        "F-HUM-REV": (.75, 1, "已主张2024年收入10,689.76万元/占比约27.60%（均未标注尾差），2025年收入/占比精确", "component_average_0_5_0_5_1_1"),
        "F-HUM-VOLUME": (.9, 1, "确认收入口径销量5,215台；另标注官方出货超5,500台（未主张产量）", "component_average_exact_and_labelled_approx"),
        "F-FUND-RAISED": (.5, 1, "60.99/59.17亿元，未标注约数", "unlabelled_le_0_5pct"),
        "F-FUND-PLAN": (.8, 1, "分项约数合计420,100万元；备注保留精确总额420,171.12万元", "labelled_approx_le_0_5pct"),
    },
    "千问": {},
    "Qoder": {},
    "WorkBuddy": {
        "F-REV-2024": (.5, 1, "39,237.06万元，未标注为旧稿数，偏差0.10%", "unlabelled_le_0_5pct"),
        "F-NP-2024": (0, 1, "9,450.18万元，偏差1.02%", "wrong_gt_0_5pct"),
        "F-NP-2025": (.8, 1, "27,800万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-ADJ-2024": (0, 1, "7,750万元，偏差1.24%", "wrong_gt_0_5pct"),
        "F-CFO-2024": (0, 1, "19,000万元，偏差1.24%", "wrong_gt_0_5pct"),
        "F-CFO-2025": (.8, 1, "67,000万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-GM-MAIN": (.6, 1, "2023精确；2024年56.41%偏差超0.5%；2025年60.27%已明示版本差异与60.13%正式口径", "component_average_1_0_0_8"),
        "F-GM-TOTAL": (.833333, 1, "2023/2025精确；2024年56.98%未标注尾差", "component_average_1_0_5_1"),
        "F-RD": (.933333, 1, "2023/2025精确；2024年6,983万元明确标注为反算", "component_average_1_0_8_1"),
        "F-SELL-2025": (.8, 1, "14,100万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-HUM-REV": (.5, 0, "2024占比27.6%为未标注尾差；2025收入精确但占比51.07%错用总营收分母，表题却称主营业务口径", "component_average_0_5_1_0_scope_mixed"),
        "F-QUAD-REV": (.5, 0, "2025收入精确；41.05%错用总营收分母，表题却称主营业务口径", "component_average_1_0_scope_mixed"),
        "F-HUM-VOLUME": (.8, 1, "只主张人形出货超5,500台且标注约数；未主张产量或确认收入销量", "labelled_approx_asserted_subset"),
        "F-H1-REV": (1, 1, "115,224.56万元，精确值", "exact"),
        "F-H1-NP": (.8, 1, "27,400万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-H1-ADJ": (.5, 1, "24,400万元，未明确标注尾差", "unlabelled_le_0_5pct"),
        "F-H1-PL": (.9, 1, "已主张的子项为研发13,590.65万元（精确）和销售费用16,400万元（标注约数）", "component_average_1_0_8"),
        "F-H1-BS": (.8, 1, "已主张的母表子项为总资产384,500万元，备注明确为38.45亿元披露换算", "labelled_approx_asserted_subset"),
        "F-IPO": (.9, 1, "已主张发行价150.80元和发行市盈率约219倍；未主张发行后总股本", "component_average_exact_and_labelled_approx"),
        "F-FUND-PLAN": (.5, 1, "420,200万元，未标注约数", "unlabelled_le_0_5pct"),
    },
    "ZhikunCode": {
        "F-REV-2024": (.8, 1, "39,276.6万元，明确标注倒算", "labelled_approx_le_0_5pct"),
        "F-CFO-2024": (.8, 1, "19,200万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-CFO-2025": (.8, 1, "67,000万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-GM-MAIN": (1, 0, "2023—2025主营毛利率精确，但同一指标行的2026H1列放入综合毛利率56.01%", "annual_values_exact_but_row_scope_mixed"),
        "F-RD": (.933333, 1, "2023/2024精确；2025年14,500万元明确标注约数", "component_average_1_1_0_8"),
        "F-HUM-REV": (.9, 1, "2024/2025收入10,700/86,800万元均明确标注约数；两期占比精确", "component_average_0_8_1_0_8_1"),
        "F-QUAD-REV": (.9, 1, "2025收入69,800万元明确标注约数；占比精确", "component_average_0_8_1"),
        "F-HUM-VOLUME": (.9, 1, "确认收入口径销量5,215台；另标注官方出货超5,500台（未主张产量）", "component_average_exact_and_labelled_approx"),
        "F-H1-REV": (.8, 1, "115,200万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-H1-NP": (.8, 1, "27,400万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-H1-ADJ": (.8, 1, "24,400万元，明确约数", "labelled_approx_le_0_5pct"),
        "F-H1-CFO": (0, 1, "写为‘未披露’，正式上市公告书已披露23,154.53万元", "wrong_disclosure_status"),
        "F-H1-PL": (.8, 1, "已主张的母表子项仅为研发费用13,600万元，明确标注约数", "labelled_approx_asserted_subset"),
    },
}

# Qoder的原始数据区保留了2026H1披露值，但“核心计算”又明确宣称研发费用
# 绝对值“未披露”。同一事实内部冲突时，v4.5对五家均取最低的实质性表述。
OVERRIDES["Qoder"]["F-H1-PL"] = (0, 1, "原始数据区保留披露值，但核心计算!J77又称2026H1研发费用绝对值未披露", "internal_conflict_wrong_disclosure_status")


def source_category(tool: str, fact_id: str) -> str:
    # Categories describe the path actually retained in the workbook, not the
    # truth of the underlying claim.  A broad domain home page is not treated
    # as a direct locator; a source-list URL still receives the separate URL
    # point even when the fact row lacks a PDF page/table pointer.
    if tool == "豆包":
        if fact_id == "F-SELL-2025":
            return "mixed_official_secondary_url_no_locator"
        return "official_named_url_no_page"
    if tool in {"千问", "Qoder"}:
        return "official_named_url_no_page"
    if tool == "WorkBuddy":
        if fact_group(fact_id) in {"rev", "np", "adj", "cfo", "gm", "rd"} or fact_id == "F-SELL-2025":
            return "claimed_official_internal_material_mismatch"
        return "official_named_no_actionable_locator"
    if fact_group(fact_id) == "ipo":
        return "official_named_url_no_page"
    if fact_id in {"F-EMPLOYEE", "F-HUM-VOLUME"}:
        return "secondary_named_no_url"
    return "official_vague_url_no_locator"


SOURCE_FLAGS = {
    "official_named_url_no_page": {"identity": 1, "priority": 1, "locator": 0, "actionable": 1},
    "mixed_official_secondary_url_no_locator": {"identity": 1, "priority": .5, "locator": 0, "actionable": 1},
    "official_vague_url_no_locator": {"identity": .5, "priority": 1, "locator": 0, "actionable": 1},
    "official_named_no_actionable_locator": {"identity": 1, "priority": 1, "locator": 0, "actionable": 0},
    "claimed_official_internal_material_mismatch": {"identity": .5, "priority": 1, "locator": 0, "actionable": 0},
    "secondary_named_no_url": {"identity": 1, "priority": 0, "locator": 0, "actionable": 0},
}


FACT_FINDINGS = {
    "豆包": {"F-HUM-REV": ["DOUBAO-001"], "F-SELL-2025": ["DOUBAO-003"], "F-FUND-RAISED": ["DOUBAO-003"]},
    "千问": {},
    "Qoder": {"F-H1-PL": ["QODER-X-V2-01"]},
    "WorkBuddy": {fid: ["WORKBUDDY-003"] for fid in {
        "F-REV-2024", "F-NP-2024", "F-NP-2025", "F-ADJ-2024", "F-CFO-2024", "F-CFO-2025",
        "F-GM-MAIN", "F-GM-TOTAL", "F-RD", "F-SELL-2025", "F-HUM-REV", "F-QUAD-REV",
        "F-H1-NP", "F-H1-ADJ", "F-H1-PL", "F-H1-BS", "F-FUND-PLAN"
    }},
    "ZhikunCode": {fid: ["ZHIKUN-002"] for fid in {
        "F-REV-2024", "F-CFO-2024", "F-CFO-2025", "F-H1-REV", "F-H1-NP", "F-H1-ADJ", "F-H1-CFO", "F-H1-PL"
    }} | {"F-GM-MAIN": ["ZHIKUN-003"]},
}


COMPONENTS = {
    ("豆包", "F-HUM-REV"): [("2024收入", .5), ("2024占比", .5), ("2025收入", 1), ("2025占比", 1)],
    ("豆包", "F-HUM-VOLUME"): [("销量5,215台", 1), ("出货超5,500台", .8)],
    ("WorkBuddy", "F-GM-MAIN"): [("2023", 1), ("2024", 0), ("2025", .8)],
    ("WorkBuddy", "F-GM-TOTAL"): [("2023", 1), ("2024", .5), ("2025", 1)],
    ("WorkBuddy", "F-RD"): [("2023", 1), ("2024", .8), ("2025", 1)],
    ("WorkBuddy", "F-HUM-REV"): [("2024占比", .5), ("2025收入", 1), ("2025占比", 0)],
    ("WorkBuddy", "F-QUAD-REV"): [("2025收入", 1), ("2025占比", 0)],
    ("WorkBuddy", "F-H1-PL"): [("研发费用", 1), ("销售费用", .8)],
    ("WorkBuddy", "F-IPO"): [("发行价", 1), ("发行市盈率", .8)],
    ("ZhikunCode", "F-RD"): [("2023", 1), ("2024", 1), ("2025", .8)],
    ("ZhikunCode", "F-HUM-REV"): [("2024收入", .8), ("2024占比", 1), ("2025收入", .8), ("2025占比", 1)],
    ("ZhikunCode", "F-QUAD-REV"): [("2025收入", .8), ("2025占比", 1)],
    ("ZhikunCode", "F-HUM-VOLUME"): [("销量5,215台", 1), ("出货超5,500台", .8)],
}


def finding_evidence_ids(report: dict[str, Any], finding_ids: list[str]) -> list[str]:
    return sorted({
        evidence_id
        for finding_id in finding_ids
        for evidence_id in (find_finding(report, finding_id) or {}).get("evidenceIds", [])
    })


def sheet_name_from_locator(locator: str) -> str:
    """Extract the workbook sheet label from an exact or descriptive locator."""
    head = locator.split("!", 1)[0]
    head = head.split("（", 1)[0]
    return head.strip()


def sheet_evidence_ids(report: dict[str, Any], tool: str, locator: str) -> list[str]:
    aid = artifact_id(tool, "excel")
    sheet = sheet_name_from_locator(locator)
    result = []
    for evidence in report["evidence"]:
        evidence_locator = str(evidence.get("locator") or evidence.get("location") or "")
        if evidence.get("artifactId") == aid and f"· {sheet} ·" in evidence_locator:
            result.append(evidence["id"])
    return sorted(result)


def source_evidence_ids(report: dict[str, Any], tool: str) -> list[str]:
    return sheet_evidence_ids(report, tool, SOURCE_SHEETS[tool])


def source_assessment_items(report: dict[str, Any], tool: str, flags: dict[str, float],
                            claim_evidence: list[str]) -> list[dict[str, Any]]:
    labels = {
        "identity": "来源名称或编号明确",
        "priority": "符合指定官方来源优先级",
        "locator": "有PDF页码、表号或网页定位",
        "actionable": "有可操作URL或原生超链接",
    }
    evidence_ids = sorted(set(claim_evidence + source_evidence_ids(report, tool)))
    return [{
        "id": key,
        "label": labels[key],
        "maxPoints": 2,
        "credit0To1": float(flags[key]),
        "earnedPoints": r(2 * float(flags[key]), 6),
        "decisionRule": "2×该事实—来源关系的编码信用；1=满足，0.5=部分满足，0=不满足。",
        "evidenceIds": evidence_ids,
        "inputEvidenceClass": "single_reviewer_coded_observation",
        "calculationClass": "mechanical_after_coding",
    } for key in ["identity", "priority", "locator", "actionable"]]


def build_fact_claims(report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    facts = {row["id"]: row for row in report["facts"]}
    claims: list[dict[str, Any]] = []
    scores: dict[str, dict[str, float]] = {}
    for tool in TOOLS:
        tool_rows = []
        for fid, fact in facts.items():
            if fid in UNCLAIMED[tool]:
                continue
            value_credit, scope_credit, actual, precision = OVERRIDES[tool].get(fid, EXACT)
            earned_fraction = .7 * value_credit + .3 * scope_credit
            category = source_category(tool, fid)
            flags = SOURCE_FLAGS[category]
            components = [{"label": label, "valueCredit": credit} for label, credit in COMPONENTS.get((tool, fid), [("已主张子项", value_credit)])]
            finding_ids = FACT_FINDINGS[tool].get(fid, [])
            locator = LOCATORS[tool][fact_group(fid)]
            evidence_ids = sorted(set(
                finding_evidence_ids(report, finding_ids)
                + sheet_evidence_ids(report, tool, locator)
                + source_evidence_ids(report, tool)
            ))
            assessment_items = source_assessment_items(report, tool, flags, evidence_ids)
            row = {
                "id": f"claim:{artifact_id(tool, 'excel')}:{fid}",
                "tool": tool,
                "artifactId": artifact_id(tool, "excel"),
                "kind": "excel",
                "factId": fid,
                "metric": fact.get("metric"),
                "period": fact.get("period"),
                "officialValue": fact.get("value"),
                "actualClaim": ("作品在所列定位主张的子项与固定母表一致" if actual == EXACT[2] else actual),
                "locator": locator,
                "valueCredit": value_credit,
                "scopeCredit": scope_credit,
                "assertedComponents": components,
                "factEarnedFraction": r(earned_fraction, 6),
                "precisionStatus": precision,
                "scopeStatus": "exact" if scope_credit == 1 else ("ambiguous_disclosed" if scope_credit == .5 else "mixed_or_wrong"),
                "sourceCategory": category,
                "sourceAssessment": dict(flags),
                "sourceAssessmentItems": assessment_items,
                "sourceAssessmentNote": {
                    "official_named_url_no_page": "事实行与明确的官方文件名或编号关联，有可操作URL，但没有PDF页码/表号。",
                    "mixed_official_secondary_url_no_locator": "同一主张混合使用官方与二手材料，有URL，但没有原文页码/表号。",
                    "official_vague_url_no_locator": "标注‘注册稿为主/披露’并保留官方公告列表URL，但未通过逐行编号把事实绑定到具体PDF。",
                    "official_named_no_actionable_locator": "明确指向招股书/上市公告书，但仅给官网域名，无页码、表号或可直达文件链接。",
                    "claimed_official_internal_material_mismatch": "作品标注为官方材料，但文件名/时点与包内可追溯材料不匹配；这不等于断言该来源绝对不存在。",
                    "secondary_named_no_url": "明确使用二手来源，但没有可操作URL和原文定位。",
                }[category],
                "officialSourceId": fact.get("sourceId"),
                "officialPage": fact.get("page"),
                "benchmarkScopeStatus": "within_fixed_32_fact_universe",
                "lineageRole": "origin",
                "standaloneScoreUse": earned_fraction < 1 or any(value < 1 for value in flags.values()),
                "firstOriginScoreUse": earned_fraction < 1 or any(value < 1 for value in flags.values()),
                "cutoffStatus": "within_cutoff",
                "evidenceBasis": "保留的原工作簿单元格/公式文本+正式事实母表",
                "findingIds": finding_ids,
                "evidenceIds": evidence_ids,
                "evidenceLocator": {
                    "artifactId": artifact_id(tool, "excel"),
                    "exactLocator": locator,
                    "sheetEvidenceIds": sheet_evidence_ids(report, tool, locator),
                    "sourceSheetEvidenceIds": source_evidence_ids(report, tool),
                    "directness": "retained_workbook_cell_locator_plus_native_sheet_screenshots",
                },
                "falsificationCriteria": "以同一SHA-256原工作簿证明定位不包含该主张，或以更高优先级截止日前官方材料更正母表。",
            }
            claims.append(row)
            tool_rows.append(row)
        fact_score = 30 * sum(row["factEarnedFraction"] for row in tool_rows) / len(tool_rows)
        scores[tool] = {
            "claimedFacts": len(tool_rows),
            "benchmarkFacts": len(facts),
            "unclaimedFacts": len(facts) - len(tool_rows),
            "earned": r(fact_score),
        }
    # The quadruped-volume observation is valid but is outside the frozen 32
    # benchmark facts.  It remains visible and cannot silently affect fact30.
    outside_locator = "原始数据_财务!F48:G48"
    outside_evidence = sorted(set(
        sheet_evidence_ids(report, "ZhikunCode", outside_locator)
        + finding_evidence_ids(report, ["ZHIKUN-004"])
    ))
    claims.append({
        "id": "claim:artifact:zhikuncode:excel:F-QUAD-VOLUME-OUTSIDE32",
        "tool": "ZhikunCode", "artifactId": artifact_id("ZhikunCode", "excel"), "kind": "excel",
        "factId": None, "metric": "2025年四足机器人销量", "period": "2025年度",
        "officialValue": "23,037台", "actualClaim": "25,500台（约，待核）", "locator": outside_locator,
        "benchmarkScopeStatus": "outside_fixed_32_fact_universe", "factEarnedFraction": None,
        "scoreTreatment": "不进入Excel事实30分；保留为母表外观察与人工核验项",
        "lineageRole": "origin", "cutoffStatus": "within_cutoff",
        "standaloneScoreUse": False, "firstOriginScoreUse": False,
        "findingIds": ["ZHIKUN-004"], "evidenceIds": outside_evidence,
        "evidenceLocator": {"artifactId": artifact_id("ZhikunCode", "excel"), "exactLocator": outside_locator,
                            "sheetEvidenceIds": sheet_evidence_ids(report, "ZhikunCode", outside_locator),
                            "directness": "retained_workbook_cell_locator_plus_native_sheet_screenshots"},
        "falsificationCriteria": "扩展事实母表时须对五家同类经营数据对称补入，不能只加入本项。",
    })
    return claims, scores


def source_scores(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for tool in TOOLS:
        rows = [row for row in claims if row.get("tool") == tool and row.get("benchmarkScopeStatus") == "within_fixed_32_fact_universe"]
        subitems = []
        total = 0.0
        for key, label in [("identity", "来源名称或编号"), ("priority", "官方优先级"), ("locator", "PDF页码/表号/网页定位"), ("actionable", "可操作URL或原生超链接")]:
            credits = [float(row["sourceAssessment"][key]) for row in rows]
            numerator = sum(credits)
            rate = numerator / len(rows)
            earned = 2 * rate
            total += earned
            subitems.append({
                "id": key, "label": label, "maxPoints": 2, "earnedPoints": r(earned),
                "passRate": r(rate * 100, 1), "numeratorCredits": r(numerator, 6),
                "denominator": len(rows), "formula": f"2×({r(numerator, 6)}/{len(rows)})",
                "claimIds": [row["id"] for row in rows],
                "evidenceIds": sorted({eid for row in rows for item in row["sourceAssessmentItems"] if item["id"] == key for eid in item["evidenceIds"]}),
                "inputEvidenceClass": "single_reviewer_coded_observation",
                "calculationClass": "mechanical_after_coding",
            })
        result[tool] = {
            "earned": r(total), "subitems": subitems, "denominator": len(rows),
            "formula": "+".join(item["formula"] for item in subitems),
            "inputEvidenceClass": "single_reviewer_coded_observation",
            "calculationClass": "mechanical_after_coding",
        }
    return result


PERIOD_SUBITEMS = {
    "豆包": [2, 2, 2, 1],
    "千问": [2, 2, 2, 1],
    "Qoder": [2, 2, 2, 1],
    "WorkBuddy": [2, 2, 0, 1],
    "ZhikunCode": [2, 2, 2, 0],
}
PERIOD_BASIS = {
    "豆包": "年度/H1分列，万元与亿元换算可识别，预测区独立标E，未用截止日后数据。",
    "千问": "年度/H1分列，单位一致，实际/预测属性和截止日处理清楚。",
    "Qoder": "期间、单位、属性和截止日四项均符合固定规则。",
    "WorkBuddy": "年度/H1与单位可识别；预测区间在核心结论中被写为‘已回升’，属性子项0/2；Excel本身未把Word的9月2日Figure AI材料写入，截止日子项不因下游问题扣分。",
    "ZhikunCode": "年度/H1、单位及预测属性均有标识；二级市场模块纳入2026-08-31数据，截止日子项0/1，不再通过整体0—5换档放大。",
}


def update_excel_scores(report: dict[str, Any], claims: list[dict[str, Any]], fact_scores: dict[str, dict[str, float]], source_results: dict[str, dict[str, Any]]) -> None:
    labels = ["报告期分离", "单位与换算", "实际/预测/计划属性", "截止日合规"]
    maxes = [2, 2, 2, 1]
    for tool in TOOLS:
        aid = artifact_id(tool, "excel")
        tool_claims = [row for row in claims if row.get("tool") == tool and row.get("benchmarkScopeStatus") == "within_fixed_32_fact_universe"]
        fact_subitems = [{
            "id": row["factId"], "label": f"{row['metric']}｜{row['period']}", "maxPoints": r(30 / len(tool_claims), 6),
            "earnedPoints": r(30 / len(tool_claims) * row["factEarnedFraction"], 6),
            "valueCredit": row["valueCredit"], "scopeCredit": row["scopeCredit"], "locator": row["locator"],
            "actual": row["actualClaim"], "official": row["officialValue"], "assertedComponents": row["assertedComponents"],
            "findingIds": row["findingIds"], "evidenceIds": row["evidenceIds"],
            "formula": "0.7×数值/陈述正确性+0.3×定义与范围",
        } for row in tool_claims]
        fact_finding_ids = sorted({fid for row in tool_claims for fid in row["findingIds"]})
        set_criterion(
            report, aid, "external-facts", fact_scores[tool]["earned"],
            f"在32项固定事实母表中，该Excel实际主张{len(tool_claims)}项；未主张{32-len(tool_claims)}项不进入准确率分母。每项按70%数值/陈述+30%定义/范围重算，得{fact_scores[tool]['earned']:.2f}/30。",
            fact_subitems,
            fact_finding_ids,
        )
        set_criterion(
            report, aid, "sources", source_results[tool]["earned"],
            f"仅对实际使用的{source_results[tool]['denominator']}条事实—来源关系计分；按来源身份、官方优先级、原文定位和可操作链接各2分机械重算，得{source_results[tool]['earned']:.2f}/8。未使用的占位行不拉低分数。",
            source_results[tool]["subitems"],
        )
        values = PERIOD_SUBITEMS[tool]
        subitems = [{"id": f"period-{i+1}", "label": labels[i], "maxPoints": maxes[i], "earnedPoints": values[i]} for i in range(4)]
        set_criterion(report, aid, "period-unit-prediction", sum(values), PERIOD_BASIS[tool], subitems)
        for suffix in ["external-facts", "sources", "period-unit-prediction"]:
            defn = definitions(report)[criterion(report, aid, suffix)["criterionId"]]
            defn.update({"scoringMode": "point_subitems", "assessmentClass": "mechanical", "fullyAtomizedAcrossFiveSamples": True, "adjudicationVersion": "4.5"})


def find_finding(report: dict[str, Any], fid: str) -> dict[str, Any] | None:
    return next((row for row in report["findings"] if row["id"] == fid), None)


def fix_allowed_upstream(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply one atomic 5×5 consistency rubric to all 25 downstream files."""
    changes = []
    for tool in TOOLS:
        for kind in KINDS[1:]:
            aid = artifact_id(tool, kind)
            row = criterion(report, aid, "excel-consistency")
            old = float(row["weighted"])
            failures = CONSISTENCY_FAILURES.get((tool, kind), {})
            subitems = []
            finding_ids = []
            for subtest_id, label, pass_rule in CONSISTENCY_SUBTESTS:
                failure = failures.get(subtest_id)
                ids = list((failure or {}).get("findingIds", []))
                passed = failure is None
                subitems.append({
                    "id": subtest_id, "label": label, "maxPoints": 5,
                    "earnedPoints": 5 if passed else 0,
                    "status": "pass" if passed else "fail",
                    "decisionRule": pass_rule,
                    "actual": pass_rule if passed else failure["reason"],
                    "findingIds": ids,
                    "evidenceIds": finding_evidence_ids(report, ids),
                    "assessmentClass": "mechanical_binary_after_evidence_coding",
                })
                finding_ids.extend(ids)
            earned = sum(item["earnedPoints"] for item in subitems)
            failures_text = "；".join(item["actual"] for item in subitems if item["status"] == "fail")
            basis = (
                "五个5分原子子项全部通过；下游可使用的上游范围按任务链统一定义。"
                if not failures else
                f"五个5分原子子项中{len(failures)}项未通过：{failures_text} G0/G1/G2闸门与连续分分别记录。"
            )
            set_criterion(report, aid, "excel-consistency", earned, basis, subitems, sorted(set(finding_ids)))
            row["consistencyRuleVersion"] = "v4.5-five-binary-subtests"
            if abs(earned - old) > 1e-9:
                changes.append({
                    "artifactId": aid, "criterionId": row["criterionId"], "oldScore": old,
                    "newScore": earned, "delta": r(earned-old),
                    "rule": "five_equal_binary_consistency_subtests_applied_to_all_downstream_artifacts",
                    "failedSubtests": sorted(failures),
                })
    f = find_finding(report, "千问-html-01")
    if f:
        f.update({"lineageRole": "exact_propagation", "classification": "allowed_upstream_reuse", "deducted": False,
                  "severity": "info", "scoreTreatmentStatus": "superseded_by_v45_allowed_upstream",
                  "interpretation": "原观察‘Excel未收录’仍成立，但HTML Prompt允许复用Word/PPT；因而不构成HTML一致性扣分。",
                  "criterionDelta": {"standalonePoints": 0, "firstOriginPoints": 0, "definition": "v4.5允许上游规则"}})
    for fid in ["千问-image-01", "千问-ink-01"]:
        f = find_finding(report, fid)
        if f:
            f.update({"lineageRole": "exact_propagation", "classification": "allowed_upstream_reuse", "deducted": False,
                      "severity": "info", "scoreTreatmentStatus": "superseded_by_v45_allowed_upstream",
                      "interpretation": "该数据已存在于允许的Word/PPT上游，不再以‘Excel外新增’扣一致性分；来源定位颗粒度单独评价。"})

    for fid, role, root, treatment in [
        ("WORKBUDDY-W-N01", "mutated", "P-WB-FUND", "事实/预测/计划属性忠实度0/5"),
        ("WORKBUDDY-W-N02", "origin", "P-WB-FIGURE", "新增重要主张截止日合规0/5"),
        ("QODER-P-N01", "mutated", "P-QODER-PPT", "关键数值/正负方向忠实度0/5"),
        ("Qoder-html-01", "mutated", "P-QODER-HTML-NET-DIFFERENCE", "关键数值忠实度0/5"),
    ]:
        finding = find_finding(report, fid)
        if finding:
            finding.update({
                "lineageRole": role, "rootCauseId": root,
                "scoreTreatmentStatus": "v45_atomic_downstream_consistency_subtest",
                "continuousScoreTreatment": treatment,
                "gateScoreSeparation": "闸门只表达独立交付安全性，不决定连续扣分幅度。",
            })

    downstream_wording = {
        "WORKBUDDY-P-N01": "PPT第14页沿用Word首次产生的‘IPO募资42.02亿元到账’；相对Word没有再次改变语义，属于完全继承。",
        "WORKBUDDY-P-N02": "PPT第14页沿用Word首次引入的Figure AI约150台比较及其2026-09-02来源；相对Word没有再次新增或改写。",
        "WorkBuddy-image-01": "普通信息图沿用Word/PPT中的‘42.02亿元到账’；相对直接上游没有再次改变属性，属于完全继承。",
        "WORKBUDDY-IMAGE-V2-FIGURE": "普通信息图沿用Word/PPT中的Figure AI约150台比较；相对直接上游没有再次新增或改写。",
        "WorkBuddy-ink-01": "水墨信息图沿用普通图中的‘42.02亿元到账’；转换节点没有再次改变属性。",
        "WORKBUDDY-INK-V2-FIGURE": "水墨信息图沿用普通图中的Figure AI约150台比较；转换节点没有再次新增或改写。",
        "WorkBuddy-html-01": "HTML沿用Word/PPT中的‘42.02亿元到账’；相对允许上游没有再次改变属性。",
        "WORKBUDDY-HTML-V2-FIGURE": "HTML沿用Word/PPT中的Figure AI约150台比较；相对允许上游没有再次新增或改写。",
    }
    for fid, observation in downstream_wording.items():
        finding = find_finding(report, fid)
        if finding:
            finding.update({
                "observation": observation, "summary": observation, "basis": observation,
                "lineageRole": "exact_propagation",
                "scoreTreatmentStatus": "v45_standalone_risk_only_exact_propagation",
                "continuousScoreTreatment": "终稿独立使用的一致性原子子项未通过；链路首次归责增量为0。",
            })
    return changes


def recalc_artifact_score(report: dict[str, Any], aid: str) -> float:
    score = r(sum(row["weighted"] for row in report["scores"]["artifacts"][aid]["criterionScores"]))
    target = report["scores"]["artifacts"][aid]
    old = target.get("qualityScore")
    target.update({
        "weightedKnownSum": score, "normalizedPartialScore": score, "baseScore": score, "qualityScore": score,
        "scoreStatus": "candidate_v45_pending_qa", "scoreModel": "v4.5_atomic_fact_source_period_and_dual_lineage",
        "v44ToV45": {"v44QualityScore": old, "v45QualityScore": score, "delta": r(score - old), "changed": abs(score-old) > 1e-9},
    })
    if isinstance(report.get("qualityScores", {}).get("artifacts"), dict):
        report["qualityScores"]["artifacts"][aid] = copy.deepcopy(target)
    return score


def build_score_impacts(report: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    defs = definitions(report)
    finding_map = {row["id"]: row for row in report["findings"]}
    impacts = []
    first_origin_scores = {}
    source_suffixes = {"sources"}
    consistency_suffixes = {"excel-consistency", "period-unit-attribute", "upstream-preservation", "ordinary-image-preservation", "cross-artifact-reuse"}
    for aid, score in report["scores"]["artifacts"].items():
        first_total = 100.0
        for row in score["criterionScores"]:
            maximum = float(defs[row["criterionId"]]["weight"])
            gap = r(maximum - float(row["weighted"]), 6)
            if gap <= 1e-9:
                continue
            suffix = row["criterionId"].split(":")[-1]
            linked = [finding_map[fid] for fid in row.get("findingIds", []) if fid in finding_map and finding_map[fid].get("deducted", True)]
            roles = {item.get("lineageRole") for item in linked}
            exact_only = bool(linked) and roles == {"exact_propagation"} and suffix in consistency_suffixes
            first_gap = 0.0 if exact_only else gap
            evidence_ids = sorted({eid for item in linked for eid in item.get("evidenceIds", [])} | set(row.get("evidenceIds", [])))
            impacts.append({
                "id": f"impact:v45:{aid}:{suffix}", "artifactId": aid, "criterionId": row["criterionId"],
                "maximumPoints": maximum, "standaloneEarnedPoints": row["weighted"],
                "standaloneDelta": -gap, "firstOriginDelta": -first_gap,
                "lineageRole": "exact_propagation" if exact_only else (next(iter(roles)) if len(roles) == 1 else "artifact_local_or_mixed"),
                "findingIds": [item["id"] for item in linked], "evidenceIds": evidence_ids,
                "rule": "来源定位与文件自身可用性始终是终端文件责任；只有合法上游的完全继承且无语义改写时，链路首次归责增量为0。",
                "atomicBasis": row.get("subitemScores") or [{"id": suffix, "maxPoints": maximum, "earnedPoints": row["weighted"]}],
            })
            first_total -= first_gap
        first_origin_scores[aid] = r(first_total)
        score["firstOriginQualityScore"] = r(first_total)
        score["standaloneQualityScore"] = score["qualityScore"]
        if isinstance(report.get("qualityScores", {}).get("artifacts"), dict):
            report["qualityScores"]["artifacts"][aid]["firstOriginQualityScore"] = r(first_total)
            report["qualityScores"]["artifacts"][aid]["standaloneQualityScore"] = score["qualityScore"]
    return impacts, first_origin_scores


def ranking(report: dict[str, Any], perspective: str, mode: str, first_scores: dict[str, float]) -> dict[str, Any]:
    artifact_map = {row["id"]: row for row in report["artifacts"]}
    rows = []
    for tool in TOOLS:
        scores = {}
        total = 0.0
        for kind, weight in WEIGHTS[mode].items():
            aid = artifact_id(tool, kind)
            value = first_scores[aid] if perspective == "firstOrigin" else report["scores"]["artifacts"][aid]["qualityScore"]
            scores[kind] = value
            total += value * weight
        excel_row = criterion(report, artifact_id(tool, "excel"), "external-facts")
        rows.append({"tool": tool, "score": r(total), "artifactScores": scores,
                     "excelFactIndex": r(excel_row["weighted"] / 30 * 100),
                     "ordinalClaim": False})
    rows.sort(key=lambda row: (-row["score"], TOOLS.index(row["tool"])))
    group = 1
    for i, row in enumerate(rows):
        if i and rows[i-1]["score"] - row["score"] > 1.0:
            group += 1
        row.update({"rank": i+1, "pointEstimateOrder": i+1, "sensitivityGroup": f"S{group}", "uncertaintyGroup": f"S{group}",
                    "performanceBand": f"S{group}", "displayRank": f"点估计第{i+1}；相邻≤1分敏感组S{group}"})
    pid = "standalone" if perspective == "standalone" else "firstOrigin"
    return {"id": f"{pid}_{mode}", "label": f"{'终稿独立使用' if perspective=='standalone' else '链路首次归责'}·{'六任务等权' if mode=='equalTask' else '均衡投研实务'}",
            "status": "candidate_v45_pending_qa", "isOfficial": False, "perspective": perspective, "scoreField": "qualityScore" if perspective == "standalone" else "firstOriginQualityScore",
            "weights": WEIGHTS[mode], "rows": rows, "ordinalClaim": False,
            "groupMeaning": "按排序后相邻分差≤1.0形成描述性敏感组；不是置信区间、统计检验、并列或产品总体结论。"}


def add_lineage_claims(report: dict[str, Any], claim_ledger: list[dict[str, Any]]) -> None:
    def add(cid: str, tool: str, kind: str, claim: str, role: str, upstream: str | None,
            allowed: bool, source: str, locator: str, evidence_ids: list[str],
            finding_ids: list[str] | None = None) -> None:
        family = None
        if cid.startswith("L-QW-"):
            family = {
                "PATENT": "patents", "SPEED": "speed-record",
                "GEN3": "gen3-trial", "PROXY": "proxy-share",
            }.get(cid.split("-")[2])
        claim_ledger.append({
            "id": f"claim:{cid}", "tool": tool, "artifactId": artifact_id(tool, kind), "kind": kind,
            "claim": claim, "claimFamily": family, "locator": locator, "lineageRole": role,
            "immediateUpstreamArtifactId": upstream, "allowedUpstream": allowed,
            "officialSourceOrUpstream": source,
            "strictExcelLineagePass": bool(kind == "excel" or (role == "exact_propagation" and upstream == artifact_id(tool, "excel"))),
            "standaloneScoreUse": not allowed,
            "firstOriginScoreUse": role != "exact_propagation" and not allowed,
            "cutoffStatus": "outside_cutoff" if "09-02" in source or "08-31" in claim else "within_cutoff_or_not_applicable",
            "findingIds": finding_ids or [], "evidenceIds": sorted(set(evidence_ids)),
            "evidenceLocator": {"artifactId": artifact_id(tool, kind), "exactLocator": locator,
                                "directness": "retained_native_screenshot_or_exact_offline_text_locator"},
            "falsificationCriteria": "提供同一SHA终稿的更早允许上游定位，或证明当前节点发生了新的语义改写。",
        })

    # 千问：四组补充数据逐条列出真实出现节点，不把未出现于图片的内容虚构为传播。
    qianwen = [
        ("PATENT", "262项专利/20项境内发明", "Word原生第2页", "PPT第9页", "HTML第176行", "招股说明书p.21、p.153", "evidence:native:f91f873e5507f1faac", "evidence:native:281e5baa44492ca513"),
        ("SPEED", "H1奔跑达到10米/秒", "Word原生第2页", "PPT第10页", "HTML第176行", "招股说明书p.34", "evidence:native:f91f873e5507f1faac", "evidence:native:010300212eb654a0db"),
        ("GEN3", "Optimus Gen-3小批量试产", "Word原生第3页", "PPT第11页", "HTML第209行", "招股说明书p.20、上市公告书p.7", "evidence:native:7cfc48a9b964a5ae2a", "evidence:native:f22d17e8e2857cc567"),
        ("PROXY", "约20%原材料经代理商进口", "Word原生第3页", "PPT第11页", "HTML第209行", "招股说明书p.24、上市公告书p.10", "evidence:native:7cfc48a9b964a5ae2a", "evidence:native:f22d17e8e2857cc567"),
    ]
    for slug, claim, word_loc, ppt_loc, html_loc, source, word_eid, ppt_eid in qianwen:
        add(f"L-QW-{slug}-W", "千问", "word", claim, "origin", None, True, source, word_loc, [word_eid])
        add(f"L-QW-{slug}-P", "千问", "ppt", claim, "exact_propagation", artifact_id("千问", "word"), True, "上游Word", ppt_loc, [ppt_eid])
        if slug == "GEN3":
            add(f"L-QW-{slug}-I", "千问", "image", claim, "exact_propagation", artifact_id("千问", "ppt"), True, "上游Word/PPT", "主要风险模块", ["evidence:native:24e0d49acff420f559", "evidence:native:4ba76cb4da933c7c04"])
            add(f"L-QW-{slug}-K", "千问", "ink", claim, "exact_propagation", artifact_id("千问", "image"), True, "上游普通信息图", "主要风险模块", ["evidence:native:8de79cf80dccb098b1", "evidence:native:e53f89857a967d2ec0"])
        add(f"L-QW-{slug}-H", "千问", "html", claim, "exact_propagation", artifact_id("千问", "ppt"), True, "上游Word/PPT", html_loc, ["EV-DIRECT-千问-html-01", "evidence:native:7ae055c6e38ceb089b"])

    wb_nodes = [
        ("W", "word", artifact_id("WorkBuddy", "excel"), "Word原生第6页；OOXML两处资金属性表述", "WORKBUDDY-W-N01", "mutated"),
        ("P", "ppt", artifact_id("WorkBuddy", "word"), "PPT第14页", "WORKBUDDY-P-N01", "exact_propagation"),
        ("I", "image", artifact_id("WorkBuddy", "ppt"), "盈利质量右侧及资金股东资源", "WorkBuddy-image-01", "exact_propagation"),
        ("K", "ink", artifact_id("WorkBuddy", "image"), "盈利质量与竞争优势伍", "WorkBuddy-ink-01", "exact_propagation"),
        ("H", "html", artifact_id("WorkBuddy", "ppt"), "HTML第208、212、379行附近", "WorkBuddy-html-01", "exact_propagation"),
    ]
    for suffix, kind, upstream, locator, fid, role in wb_nodes:
        add(f"L-WB-FUND-{suffix}", "WorkBuddy", kind, "42.02亿元拟募集/计划→已到账" if role != "exact_propagation" else "42.02亿元已到账", role, upstream, False,
            "工具Excel与招股说明书" if role != "exact_propagation" else "上游文件", locator, finding_evidence_ids(report, [fid]), [fid])
    wb_fig_nodes = [
        ("W", "word", artifact_id("WorkBuddy", "excel"), "Word第4页竞争优势及第5页来源", "WORKBUDDY-W-N02", "origin"),
        ("P", "ppt", artifact_id("WorkBuddy", "word"), "PPT第14页", "WORKBUDDY-P-N02", "exact_propagation"),
        ("I", "image", artifact_id("WorkBuddy", "ppt"), "竞争优势/出货量全球第一模块", "WORKBUDDY-IMAGE-V2-FIGURE", "exact_propagation"),
        ("K", "ink", artifact_id("WorkBuddy", "image"), "竞争优势/出货量全球第一模块", "WORKBUDDY-INK-V2-FIGURE", "exact_propagation"),
        ("H", "html", artifact_id("WorkBuddy", "ppt"), "竞争优势/出货量全球第一模块", "WORKBUDDY-HTML-V2-FIGURE", "exact_propagation"),
    ]
    for suffix, kind, upstream, locator, fid, role in wb_fig_nodes:
        add(f"L-WB-FIG-{suffix}", "WorkBuddy", kind, "Figure AI约150台/约为宇树1/36", role, upstream, False,
            "2026-09-02材料，超截止日" if role == "origin" else "上游文件", locator, finding_evidence_ids(report, [fid]), [fid])

    add("L-QD-3943", "Qoder", "html", "收现比39.43%", "exact_propagation", artifact_id("Qoder", "excel"), True,
        "上游Excel", "HTML第267行", ["preview:qoder:html", "evidence:native:bb4c8cb21b106e4c7b"])
    add("L-QD-SIGN", "Qoder", "ppt", "扣非净利/现金流标题双双转负", "mutated", artifact_id("Qoder", "excel"), False,
        "同页数值及上游Excel为正", "PPT第10页标题", finding_evidence_ids(report, ["QODER-P-N01"]), ["QODER-P-N01"])
    add("L-QD-NETDIFF", "Qoder", "html", "净差额31,254.23万元被写成股份支付34,906.55万元", "mutated", artifact_id("Qoder", "excel"), False,
        "上游Excel", "HTML第313行附近", finding_evidence_ids(report, ["Qoder-html-01"]), ["Qoder-html-01"])

    add("L-ZK-CUTOFF-X", "ZhikunCode", "excel", "2026-08-31二级市场数据", "origin", None, False,
        "超越2026-08-30截止日", "资料来源!D18；原始数据_IPO与股东!A57:D57；核心计算!A47:F47；趋势图表图7；分析结论!A33",
        finding_evidence_ids(report, ["ZHIKUN-001"]), ["ZHIKUN-001"])
    zk_nodes = [
        ("W", "word", "Word第3—8页", "ZHIKUN-W-I01", artifact_id("ZhikunCode", "excel")),
        ("P", "ppt", "PPT第5、7、10、12—14页", "ZHIKUN-P-I01", artifact_id("ZhikunCode", "excel")),
        ("I", "image", "IPO与二级市场模块", "ZhikunCode-image-01", artifact_id("ZhikunCode", "ppt")),
        ("K", "ink", "伍·发行与市场", "ZhikunCode-ink-01", artifact_id("ZhikunCode", "image")),
        ("H", "html", "HTML第403、606行及capLabels附近", "ZhikunCode-html-01", artifact_id("ZhikunCode", "ppt")),
    ]
    for suffix, kind, locator, fid, upstream in zk_nodes:
        evidence_ids = finding_evidence_ids(report, [fid])
        if not evidence_ids:
            evidence_ids = [f"preview:zhikuncode:{kind}"]
        add(f"L-ZK-CUTOFF-{suffix}", "ZhikunCode", kind, "2026-08-31二级市场数据", "exact_propagation", upstream, False,
            "上游Excel已标注为补充但仍超截止日", locator, evidence_ids, [fid])


def strict_lineage_diagnostic(claims: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for tool in TOOLS:
        for kind in KINDS[1:]:
            items = [row for row in claims if row.get("tool") == tool and row.get("kind") == kind and str(row.get("id", "")).startswith("claim:L-")]
            if not items:
                rows.append({"tool": tool, "artifactId": artifact_id(tool, kind), "kind": kind, "enumeratedContentiousClaims": 0, "strictExcelPass": 0, "strictExcelPassRate": None, "status": "not_enumerated_not_scored"})
                continue
            passed = sum(bool(row.get("strictExcelLineagePass")) for row in items)
            rows.append({"tool": tool, "artifactId": artifact_id(tool, kind), "kind": kind, "enumeratedContentiousClaims": len(items), "strictExcelPass": passed, "strictExcelPassRate": r(passed/len(items)*100, 1), "status": "diagnostic_only"})
    return {
        "status": "diagnostic_only_not_in_formal_scores",
        "scope": "仅统计v4.5已枚举的争议主张，不代表终稿全部数字的血缘覆盖率。",
        "definition": "严格Excel血缘只回答‘是否直接来自本工具Excel’；原Prompt允许的Word/PPT官方补充不因此诊断扣分。",
        "rows": rows,
    }


def fact_coverage_diagnostics(report: dict[str, Any], claims: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for tool in TOOLS:
        claimed = sum(
            row.get("tool") == tool and row.get("benchmarkScopeStatus") == "within_fixed_32_fact_universe"
            for row in claims
        )
        coverage = criterion(report, artifact_id(tool, "excel"), "requirements-richness")
        fact_score = criterion(report, artifact_id(tool, "excel"), "external-facts")
        rows.append({
            "tool": tool, "claimedFacts": claimed, "benchmarkFacts": 32,
            "unclaimedFacts": 32 - claimed, "claimCoverageRate": r(claimed / 32 * 100, 1),
            "factCorrectnessPoints": fact_score["weighted"], "factCorrectnessMax": 30,
            "requirementsRichnessPoints": coverage["weighted"], "requirementsRichnessMax": 10,
            "requirementsCriterionId": coverage["criterionId"],
            "scoreUse": "事实正确率与要求覆盖分别计分；未主张事实不进入事实正确率分母，也不在覆盖维度重复按错误扣分。",
        })
    return {
        "status": "diagnostic_and_boundary_disclosure",
        "definition": "32项母表主张覆盖率用于解释事实正确率分母；内容完整度仍由Excel‘要求覆盖与数据丰富度’10分维度评价。",
        "rows": rows,
    }


def scenario_record_composition(report: dict[str, Any]) -> dict[str, Any]:
    primary = len(report["scenarioRuns"])
    supplemental = report.get("rubricSubtests", {}).get("scenarioRecords", [])
    labels = report.get("rubricSubtests", {}).get("labelChecklistRecords", [])
    zone_families = sorted({row.get("zoneId") for row in labels if row.get("zoneId")})
    total = primary + len(supplemental) + len(zone_families)
    return {
        "reportedTotal": total,
        "formula": f"{primary}项主场景运行 + {len(supplemental)}项补充规则场景 + {len(zone_families)}组普通图/水墨图配对标签区 = {total}项综合复核记录",
        "primaryScenarioRuns": {"count": primary, "ids": [row.get("id") or row.get("runId") for row in report["scenarioRuns"]]},
        "supplementalScenarioRecords": {"count": len(supplemental), "ids": [row.get("id") or row.get("subtestId") for row in supplemental]},
        "pairedImageZoneFamilies": {
            "count": len(zone_families), "zoneIds": zone_families,
            "underlyingExecutions": len(labels),
            "definition": "普通图与水墨图的同编号标签区按一个配对复核族计入202；18条具体执行仍在标签清单逐条保留。",
        },
    }


def annotate_image_judgment(report: dict[str, Any]) -> None:
    checklist = report.get("rubricSubtests", {}).get("labelChecklistRecords", [])
    for aid, suffix in [
        (artifact_id("Qoder", "image"), "readability-100pct"),
        (artifact_id("Qoder", "ink"), "hierarchy-readability"),
    ]:
        row = criterion(report, aid, suffix)
        linked = [item for item in checklist if item.get("artifactId") == aid]
        status_counts: dict[str, int] = {}
        for item in linked:
            status = item.get("status") or item.get("actual") or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
            item["assessmentClass"] = "single_reviewer_anchored_judgment"
            item["measurementBoundary"] = "bbox与标签状态可复核；可读/叠印/边界侵入的状态编码由单一评审者判定。"
        weight = definitions(report)[row["criterionId"]]["weight"]
        step = r(weight / 5 * .5, 2)
        row.update({
            "assessmentClassApplied": "single_reviewer_anchored_judgment",
            "assessmentClassReason": "三档截图与逐标签清单是可复核输入；从状态到0—5锚点的换算包含单一评审判断。",
            "labelChecklistSummary": {"records": len(linked), "statusCounts": status_counts},
            "singleRaterSensitivity": {
                "oneHalfAnchorStepPoints": step,
                "lower": r(max(0, row["weighted"] - step)),
                "pointEstimate": row["weighted"],
                "upper": r(min(weight, row["weighted"] + step)),
                "scoreEffect": "披露区间，不改变当前点估计。",
            },
        })
    report["methodology"]["imageReadabilityJudgmentV45"] = {
        "assessmentClass": "single_reviewer_expert_judgment",
        "observableInputs": "原像素100%、1920×1080适应窗口、A4缩放模拟与逐标签状态清单。",
        "judgmentBoundary": "文字是否存在、裁切、叠印可由截图复核；最小字是否可读及状态到锚点的换算由单一评审者判定。",
        "sensitivityRangePoints": [-1.5, 1.5],
        "sensitivityMeaning": "对Qoder两张图的可读性点估计按一个0.5级锚点步长上下浮动；不改变当前分数，不表示评审者间一致性。",
    }


def score_revision_bridge(report: dict[str, Any], base_scores: dict[str, Any]) -> list[dict[str, Any]]:
    revisions = []
    for aid, current in report["scores"]["artifacts"].items():
        base = base_scores[aid]
        old_score = float(base["qualityScore"])
        new_score = float(current["qualityScore"])
        if abs(new_score - old_score) <= 1e-9:
            continue
        old_by_id = {row["criterionId"]: row for row in base["criterionScores"]}
        bridge = []
        for row in current["criterionScores"]:
            old_points = float(old_by_id[row["criterionId"]]["weighted"])
            new_points = float(row["weighted"])
            if abs(new_points - old_points) <= 1e-9:
                continue
            bridge.append({
                "criterionId": row["criterionId"], "oldPoints": old_points,
                "newPoints": new_points, "delta": r(new_points-old_points),
                "subitemScores": row.get("subitemScores", []),
                "evidenceIds": sorted(set(row.get("evidenceIds", [])) | {
                    eid for item in row.get("subitemScores", []) for eid in item.get("evidenceIds", [])
                }),
            })
        revisions.append({
            "artifactId": aid, "oldScore": old_score, "newScore": new_score,
            "delta": r(new_score-old_score),
            "oldRule": "v4.4整体0—5换档或严格Excel单一血缘",
            "newRule": "v4.5事实/来源/期间原子子项与五项下游一致性规则",
            "criterionBridge": bridge,
            "bridgeCheck": r(sum(item["delta"] for item in bridge)),
            "symmetricScan": "五家全部同类项执行",
        })
    return revisions


def normalize_reclassified_findings(report: dict[str, Any], claims: list[dict[str, Any]]) -> None:
    """Keep historical observations, but make their v4.5 score role unambiguous."""
    scored_by_finding: dict[str, list[dict[str, Any]]] = {}
    for row in claims:
        if row.get("benchmarkScopeStatus") != "within_fixed_32_fact_universe":
            continue
        loss = 30 / sum(1 for item in claims if item.get("tool") == row.get("tool") and item.get("benchmarkScopeStatus") == "within_fixed_32_fact_universe") * (1 - row["factEarnedFraction"])
        if loss <= 1e-9:
            continue
        for fid in row.get("findingIds", []):
            scored_by_finding.setdefault(fid, []).append({"factId": row["factId"], "points": r(loss, 6), "locator": row["locator"]})

    excluded = {
        "DOUBAO-002": "2025年组件及其他主营收入缺失是有效观察，但不属于32项固定事实母表；v4.5不将它暗中并入事实30分。",
        "QODER-003": "注册批复落款日/网页披露日的区分不在32项固定事实母表中，作为非计分日期观察保留。",
        "QODER-X-V2-02": "‘收现比’术语口径是有效分析提示，但不属于32项固定事实母表，不在事实30分内重复扣分。",
        "ZHIKUN-004": "四足销量及2024年人形销量版本差异继续保留，但其中的四足全年销量不在32项固定事实母表；若扩展母表必须对五家同类销量对称加入。",
    }
    for finding in report["findings"]:
        fid = finding["id"]
        if fid in scored_by_finding:
            items = scored_by_finding[fid]
            total = r(sum(item["points"] for item in items), 6)
            finding.update({
                "deducted": True,
                "scoreTreatmentStatus": "v45_atomic_fact_subtests",
                "criterionDelta": {"standalonePoints": -total, "firstOriginPoints": -total,
                                   "definition": "仅汇总本finding直接关联的v4.5事实原子子测试；不是删除finding后的反事实回分。",
                                   "atomicItems": items},
            })
        elif fid in excluded:
            finding.update({
                "deducted": False,
                "scoreTreatmentStatus": "v45_observation_outside_fixed_fact_universe",
                "interpretation": excluded[fid],
                "criterionDelta": {"standalonePoints": 0, "firstOriginPoints": 0,
                                   "definition": "保留观察与证据，不进入v4.5固定32项事实分。"},
            })

    wording = {
        "千问-image-02": "页脚仅列文件级来源；该图中的技术、竞品与股东数字虽已存在于允许的Word/PPT上游，但本图没有逐项页码或可点击定位。v4.5仅在本图来源维度评价定位颗粒度，不再以‘Excel外新增’扣一致性分。",
        "千问-html-02": "来源区保留文件级来源名称，但262/20项专利、10米/秒、Gen-3试产及代理进口比例没有逐项页码或可点击定位。上述内容已存在于允许的Word/PPT上游，v4.5仅在本HTML来源维度评价定位颗粒度。",
    }
    for fid, observation in wording.items():
        finding = find_finding(report, fid)
        if finding:
            finding["observation"] = observation
            finding["basis"] = observation
            finding["summary"] = observation
            finding["lineageRole"] = "origin"
            finding["rootCauseId"] = fid
            finding["scoreTreatmentStatus"] = "v45_file_level_source_traceability_only"

    ink_source = find_finding(report, "DIM-QIANWEN-INK-SOURCES")
    if ink_source:
        observation = "水墨信息图仅保留文件级来源名称，未对关键技术、竞品和股东数字提供逐项页码或可点击定位；这些内容已存在于允许的Word/PPT上游，因此只评价本图来源可追溯性，不以Excel未收录扣一致性分。"
        ink_source.update({
            "observation": observation,
            "basis": observation,
            "summary": observation,
            "rootCauseId": "DIM-QIANWEN-INK-SOURCES",
            "lineageRole": "origin",
            "scoreTreatmentStatus": "v45_file_level_source_traceability_only",
        })


def reconcile_delivery_gates_v45(report: dict[str, Any]) -> None:
    """Remove superseded findings from terminal-risk explanations.

    Gate codes remain evidence-based and score-independent.  A valid upstream
    reuse finding cannot itself remain a gate reason, while an independently
    observable issue outside the fixed fact universe may still inform G1.
    """
    finding_map = {row["id"]: row for row in report["findings"]}
    gates = report.get("deliveryGates", {}).get("artifacts", {})
    for aid, gate in gates.items():
        kept_ids = []
        for fid in gate.get("findingIds", []):
            finding = finding_map.get(fid, {})
            if finding.get("scoreTreatmentStatus") in {
                "superseded_by_v45_allowed_upstream",
                "observation_only",
            }:
                continue
            kept_ids.append(fid)
        gate["findingIds"] = kept_ids
        gate["terminalRiskComponents"] = [
            item for item in gate.get("terminalRiskComponents", [])
            if item.get("findingId") in kept_ids
        ]
        gate["scoreEffect"] = 0
        gate["v45Definition"] = "终端独立使用风险；与事实严重度、连续分及链路首次归责分别记录。"

    # These codes are unchanged, but the reasons must reflect the active v4.5
    # findings rather than the retired strict-Excel lineage interpretation.
    reason_updates = {
        artifact_id("千问", "image"): "允许上游复用已通过；G1仅因图内来源缺少逐项页码或可点击定位。",
        artifact_id("千问", "ink"): "允许上游复用已通过；G1来自水墨转换完成度，不由Excel血缘触发。",
        artifact_id("千问", "html"): "允许上游复用已通过；G1来自移动端核心图表可访问性及文件级来源定位颗粒度。",
        artifact_id("ZhikunCode", "excel"): "H1经营现金流披露判断、毛利率范围、8月31日截止日和来源定位仍需局部修正。",
        artifact_id("ZhikunCode", "ppt"): "终稿含已披露但超过截止日的8月31日估值模块；链路首次归责为0，独立使用前仍应删除或更新截止日。",
        artifact_id("Qoder", "ppt"): "投资人材料的核心标题发生绝对正负方向反转；按五家统一G2规则，未经复核不得直接交付。连续分仅在关键数值/方向忠实度子项扣5分。",
    }
    for aid, reason in reason_updates.items():
        if aid in gates:
            gates[aid]["reason"] = reason

    qoder_gate = gates.get(artifact_id("Qoder", "ppt"))
    if qoder_gate:
        qoder_gate.update({
            "ruleId": "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL",
            "ruleText": "投资人材料的核心标题把仍为正的核心业绩指标写成负值，或把负值写成正值，即使只影响一页且易于修复，也进入G2；对五款工具对称适用。",
            "scope": "1/20页；同页数字仍为正；修复动作为更正一处标题。",
            "continuousScoreTreatment": "不由G2反推扣分；按五个一致性原子子项，仅关键数值/正负方向忠实度0/5。",
        })

    report["methodology"]["deliveryGatePolicyV45"] = {
        "scoreIndependence": "G0/G1/G2不参与连续分计算，严重度也不机械映射为固定扣分。",
        "qoderRule": "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL",
        "qoderRuleText": "投资人材料的核心标题发生绝对正负方向反转时进入G2；对五款工具对称适用。",
        "continuousRule": "同一问题只在对应原子子项计分；Qoder PPT本项影响5/25，而不是由G2决定10分或其他幅度。",
    }


def separate_finding_severity_and_terminal_gate(report: dict[str, Any]) -> None:
    gates = report.get("deliveryGates", {}).get("artifacts", {})
    for finding in report["findings"]:
        aid = finding.get("artifactId")
        gate = gates.get(aid, {})
        if "gate" in finding:
            finding["legacyFindingGateCodeV44"] = finding.pop("gate")
        finding["observationSeverity"] = finding.get("severity", "info")
        finding["chainAttributionRole"] = finding.get("lineageRole", "origin")
        finding["terminalIndependentUseGate"] = gate.get("code", "G0")
        finding["severityGateRelationship"] = (
            "问题严重度描述单条观察的性质；终端闸门描述整件文件能否未经复核直接交付。"
            "两者分别判定，不能用critical/major机械推出G2，也不能用G0否定已记录观察。"
        )


def mark_vendor_self_reviews_as_context(report: dict[str, Any]) -> None:
    """Retain the five screenshots while preventing stale replies becoming evidence."""
    challenges = report.get("challenges", {})
    challenges.setdefault("meta", {}).update({
        "scoreUse": "none",
        "evidenceUse": "none",
        "status": "historical_context_only_not_independently_verified",
        "v45Note": "五张图及回复不再进行内容核验，不作为改分或定性证据；仅保留为异议背景。",
    })
    for row in challenges.get("responses", []):
        tool_slug = {
            "豆包": "doubao", "千问": "qianwen", "Qoder": "qoder",
            "WorkBuddy": "workbuddy", "ZhikunCode": "zhikuncode",
        }.get(row.get("tool"))
        display_path = Path(__file__).resolve().parent / "stakeholder-responses" / f"{tool_slug}-tool-self-response-display.webp"
        if tool_slug and display_path.is_file():
            row["screenshotEmbedPath"] = str(display_path)
        if "historicalConclusionV44" not in row:
            row["historicalConclusionV44"] = row.get("conclusion")
        row["conclusion"] = (
            "该回复产生于v4.4阶段，且由参评AI工具生成，不是厂商负责人或员工声明。"
            "v4.5仅将其作为历史异议背景，未将图片、说明或其中的分数建议用作证据。"
        )
        row["v45ScoringUse"] = False
        row["v45EvidenceUse"] = False


def update_presentation_v45(report: dict[str, Any]) -> None:
    presentation = report.setdefault("presentation", {})
    registry = presentation.setdefault("visualRegistry", [])
    by_id = {row.get("id"): row for row in registry}
    # The explicit list avoids presentation labels leaking into scoring data.
    entries = [
        ("executive-rankings", "图1-1", "四组可复算比较概览", "report_v4.json·rankings", "终稿独立使用/链路首次归责 × 六任务等权/均衡投研实务；0–100分"),
        ("ranking-main", "图2-1", "固定样本当前视角比较", "report_v4.json·rankings", "按当前评价视角和权重模式实时重算；敏感组不是统计检验"),
        ("v45-fact-summary", "表6-3", "五家Excel事实、来源与期间机械重算汇总", "report_v4.json·claimLedger/scores", "32项母表中仅将各Excel实际主张事实纳入准确率分母"),
        ("v45-claim-ledger", "表6-4", "Excel逐事实主张与得分账本", "同一SHA-256工作簿保留单元格、32项官方母表及已登记原生证据", "单项=70%数值/陈述+30%定义/范围；复合事实只评作品已主张子项"),
        ("strict-lineage", "表6-5", "严格Excel血缘诊断", "report_v4.json·claimLedger", "仅对已枚举争议主张统计；不进入任何正式分数"),
        ("fact-coverage-boundary", "表6-6", "事实正确率与内容完整度边界", "report_v4.json·factCoverageDiagnostics", "事实准确率分母与要求覆盖/丰富度分开计算，不重复扣分"),
        ("v45-revisions", "表6-7", "v4.4至v4.5逐维度分数桥接", "report_v4.json·scoreRevisionsV45", "旧分+逐维度变化=新分；五家同类项执行同一规则"),
        ("scenario-composition", "表7-1", "202项综合复核记录构成", "report_v4.json·contentInventory.scenarioRecordComposition", "180项主场景+13项补充规则场景+9组普通图/水墨图配对标签区"),
    ]
    for vid, number, title, source_note, scope_note in entries:
        node = by_id.get(vid)
        payload = {"id": vid, "number": number, "title": title, "sourceNote": source_note, "scopeNote": scope_note,
                   "printProfiles": ["summary", "formal", "full"]}
        if node:
            node.update(payload)
        else:
            registry.append(payload)
    presentation.setdefault("executiveSummary", {}).update({
        "scope": "5款工具、6类任务、30件固定终稿；Excel对照32项固定事实母表，下游按各节点允许的上游文件复核。",
        "rankingPolicy": "并列公布终稿独立使用与链路首次归责两种视角，各有等权与实务权重；不指定唯一主榜。",
        "evidencePolicy": "事实分只核验Excel实际主张；严格Excel血缘是不计分诊断；工具自评回复不作为评分证据。",
    })
    presentation.setdefault("publicationLabels", {}).update({
        "standalone": "终稿独立使用",
        "firstOrigin": "链路首次归责",
        "artifact_local_or_mixed": "文件自身或混合影响",
        "allowed_upstream_reuse": "允许的上游复用",
        "not_enumerated_not_scored": "本轮未枚举，不计分",
        "diagnostic_only": "仅作诊断，不计分",
        "within_fixed_32_fact_universe": "固定32项母表范围内",
        "outside_fixed_32_fact_universe": "固定32项母表范围外观察",
        "final_v45_recomputed": "v4.5已重算",
        "v45_atomic_fact_subtests": "v4.5事实原子子测试",
        "v45_file_level_source_traceability_only": "仅评价本文件来源可追溯性",
        "candidate_v45_pending_qa": "v4.5候选版，待离线验收",
        "single_reviewer_anchored_judgment": "单一评审者锚定判断",
    })


def update_meta(report: dict[str, Any], base_sha: str, fact_scores: dict[str, dict[str, float]], upstream_changes: list[dict[str, Any]]) -> None:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    report["meta"].update({
        "presentationVersion": "4.5", "version": "报告版本 4.5 · 五家统一事实与数据血缘重评",
        "status": "candidate_v45_pending_qa", "generatedAt": now,
        "scoringNote": "v4.5按同一事实容差、来源原子子项和允许上游规则重算五家；分数与排名允许变化，原件和证据观察不变。",
    })
    report["methodology"]["factAuthority"]["downstream"] = "Word可用Excel+截止日前可直接追溯的官方补充；PPT可用Excel+Word；普通图可用Excel+Word+PPT；水墨图应保持普通图；HTML可用Excel+Word+PPT。"
    report["methodology"]["v45FactScoring"] = {
        "universe": "32项固定事实母表", "denominator": "仅计各Excel实际主张的母表事实；未主张不进准确率分母",
        "factRule": FACT_RULE, "sourceRule": "来源身份/官方优先/原文定位/可操作链接各2分",
        "periodRule": "期间分离2+单位2+事实属性2+截止日1",
        "sameFactRule": "同一事实多处冲突时取最低实质性表述；传播到公式/图表/结论不重复扣事实分。",
        "coverageBoundary": "事实30分只评作品实际主张的32项母表事实；主题覆盖与数据丰富度在独立10分维度评价。两项同时披露但不重复扣分。",
        "sourcePrecisionDisclosure": "来源得分的加总在编码后为机械计算；来源身份、优先级、定位和链接是否满足由单一评审者依据保留证据编码，精确小数不代表统计精度。",
    }
    report["methodology"]["v45LineageScoring"] = {
        "standalone": "每件终稿按独立交付风险评价。",
        "firstOrigin": "同一错误只在首次产生/首次语义改变节点归责；完全继承的链路归责增量为0。",
        "sources": "来源定位是每件终稿的独立交付责任，可在不同终稿分别扣分。",
        "strictExcelLineage": "另行诊断，不进入正式分数。",
    }
    report.setdefault("meta", {}).setdefault("ui", {}).setdefault("hero", {}).update({
        "lead": "对5款工具共30件固定终稿的单次、固定环境复核；Excel按32项事实母表机械重算，下游按任务允许的上游文件核验。",
        "statusNote": "并列公布终稿独立使用与链路首次归责两种视角，各提供六任务等权和均衡投研实务权重；不指定唯一主榜。",
    })
    report["factAuditUniverse"].update({
        "benchmarkFactCount": 32, "claimUniverseStatus": "enumerated_for_five_excel_workbooks_v45",
        "publicationClaim": "32项母表是固定的核心事实范围；准确率分母仅包含各Excel实际主张的母表事实。未被主张的事实不当作错误，也不得据此宣称工作簿全部数字正确。",
        "perToolClaimCounts": {tool: fact_scores[tool] for tool in TOOLS},
        "outsideUniverseObservations": ["ZhikunCode 2025年四足销量25,500台与正式23,037台的差异保留为母表外观察，未进入事实30分；若扩展母表，须对五家同类经营数对称补入。"],
    })
    report["versionHistory"].append({
        "version": "4.5", "date": now, "status": "candidate_pending_qa", "previousVersion": "4.4", "previousJsonSha256": base_sha,
        "scope": "五家Excel事实/来源/期间统一机械重算；合法上游血缘对称复核；发布终稿独立使用与链路首次归责两种并列视角。",
        "upstreamConsistencyCorrections": upstream_changes,
        "officeFilesReopened": False, "browserEffectRetested": False, "vendorSelfReviewUsedAsEvidence": False,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_bytes = args.input.read_bytes()
    base_sha = hashlib.sha256(base_bytes).hexdigest()
    report = json.loads(base_bytes)
    frozen = {key: len(report[key]) for key in ["artifacts", "scenarioRuns", "coverageItems", "findings", "evidence", "media", "facts", "sources"]}
    base_scores = copy.deepcopy(report["scores"]["artifacts"])
    old_scores = {aid: row["qualityScore"] for aid, row in base_scores.items()}

    fact_claims, fact_scores = build_fact_claims(report)
    source_results = source_scores(fact_claims)
    update_excel_scores(report, fact_claims, fact_scores, source_results)
    upstream_changes = fix_allowed_upstream(report)
    normalize_reclassified_findings(report, fact_claims)
    reconcile_delivery_gates_v45(report)
    separate_finding_severity_and_terminal_gate(report)
    mark_vendor_self_reviews_as_context(report)
    annotate_image_judgment(report)

    new_scores = {aid: recalc_artifact_score(report, aid) for aid in report["scores"]["artifacts"]}

    add_lineage_claims(report, fact_claims)
    impacts, first_scores = build_score_impacts(report)
    report["claimLedger"] = {
        "status": "v45_enumerated_benchmark_and_contested_downstream_claims",
        "factScoringRule": FACT_RULE,
        "records": fact_claims,
        "limitations": "Excel部分穷举32项母表中已主张事实；下游部分穷举v4.5争议主张，不冒充终稿全部数字的穷举。",
    }
    report["scoreImpacts"] = impacts
    report["strictExcelLineage"] = strict_lineage_diagnostic(fact_claims)
    report["factCoverageDiagnostics"] = fact_coverage_diagnostics(report, fact_claims)

    rankings = {}
    for perspective in ["standalone", "firstOrigin"]:
        for mode in ["equalTask", "practical"]:
            node = ranking(report, perspective, mode, first_scores)
            rankings[node["id"]] = node
    report["rankings"] = rankings
    report["rankingPerspectives"] = {
        "status": "candidate_v45_pending_qa", "officialResultIds": [], "candidateResultIds": list(rankings), "diagnosticResultIds": [],
        "definitions": {"standalone": "终稿独立使用视角", "firstOrigin": "链路首次归责视角", "equalTask": "六任务各占1/6", "practical": "Excel25%、Word20%、PPT20%、普通图10%、水墨图10%、HTML15%"},
        "results": rankings, "ordinalClaim": False,
        "uncertaintyPolicy": "相邻≤1分只标记敏感组，不解释为确定性优劣。",
    }
    report["methodology"]["rankingViews"] = list(rankings)

    # Recompute score-change ledger after all updates.  This is the only table
    # allowed to state the old/new score and ranking impact.
    report["scoreRevisionsV45"] = score_revision_bridge(report, base_scores)

    update_meta(report, base_sha, fact_scores, upstream_changes)
    update_presentation_v45(report)
    composition = scenario_record_composition(report)
    report["contentInventory"]["scenarioRecordComposition"] = composition
    report["contentInventory"]["scenarioRecords"] = {
        "count": composition["reportedTotal"],
        "entry": "第7章全量复核浏览器；由180项主场景运行、13项补充规则场景和9组配对图片标签区组成",
    }
    report["contentInventory"].update({
        "claimLedgerRecords": {"count": len(fact_claims), "entry": "第6章逐主张事实与数据血缘账本"},
        "scoreImpacts": {"count": len(impacts), "entry": "第6章评分影响账本"},
        "strictExcelLineageRows": {"count": len(report["strictExcelLineage"]["rows"]), "entry": "第6章严格Excel血缘诊断"},
    })
    verification_entry = {
        "id": "verification:v45", "status": "candidate_generated_pending_external_qa", "baseJsonSha256": base_sha,
        "frozenCounts": frozen, "officeFilesReopened": False, "browserEffectTested": False,
        "vendorSelfReviewUsed": False,
    }
    if isinstance(report.get("verification"), list):
        report["verification"].append(verification_entry)
    else:
        report.setdefault("verification", {})["v45"] = verification_entry
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": sha256(args.output), "factScores": fact_scores,
                      "sourceScores": {k:v["earned"] for k,v in source_results.items()},
                      "periodScores": {k:sum(v) for k,v in PERIOD_SUBITEMS.items()},
                      "changedScores": report["scoreRevisionsV45"],
                      "rankings": {k:[(x["tool"],x["score"]) for x in v["rows"]] for k,v in rankings.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
