#!/usr/bin/env python3
"""Build the v4 score ledger from the immutable v3 native-audit ledger.

v4 separates three questions which v3 mixed together:

* linear quality: a 0--100 score with no numerical cap or fixed adjustment;
* delivery gate: whether a file may be used directly, must be corrected, or has
  a platform-scoped compatibility hold;
* propagation diagnostic: a non-causal sensitivity value which mechanically
  restores exact-propagation gap allocations; it is never an official rank.

The transformation is deterministic and uses only the Python standard library.
It never modifies the v3 input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from copy import deepcopy
from pathlib import Path
from typing import Any


SCRIPT_VERSION = "4.2.0"
HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE.parent / "v3" / "report_v3.integrated.json"
DEFAULT_OUTPUT = HERE / "report_v4.json"
DEFAULT_SUPPLEMENT = HERE.parent.parent / "native_audit_v4" / "logs" / "merge_supplement.json"
NATIVE_V4_ROOT = HERE.parent.parent / "native_audit_v4"
DIRECT_EVIDENCE_LOG = NATIVE_V4_ROOT / "logs" / "direct_finding_evidence.json"
DEFAULT_RELEASE_VERIFICATION = NATIVE_V4_ROOT / "logs" / "report_v4_release_verification.json"
PROCESS_RECORDS_LOG = NATIVE_V4_ROOT / "logs" / "user_supplied_process_records.json"
CONFIGURATION_USAGE_LOG = NATIVE_V4_ROOT / "logs" / "configuration_usage_evidence.json"
QODER_WORD_LOCATOR_LOG = NATIVE_V4_ROOT / "logs" / "qoder_word_locator_tasks.json"
QODER_IMAGE_CHECKLIST_LOG = NATIVE_V4_ROOT / "logs" / "qoder_png_layout_checklist.json"


def direct_evidence_id(finding_id: str) -> str:
    """Stable, human-readable ID for a same-artifact structured extract."""

    return f"EV-DIRECT-{finding_id}"


def merge_user_supplied_process_records(report: dict[str, Any]) -> None:
    """Register user-supplied process links without letting them affect scores.

    These links document the task history around five fixed samples.  They are
    intentionally a separate evidence layer: a process transcript cannot replace
    the delivered file, native-application observations, or the Excel fact ledger.
    """

    payload = json.loads(PROCESS_RECORDS_LOG.read_text(encoding="utf-8"))
    records = deepcopy(payload.get("records", []))
    if {row.get("tool") for row in records} != {"豆包", "千问", "Qoder", "WorkBuddy", "ZhikunCode"}:
        raise ValueError("process record log must contain exactly the five supplied tools")
    if len(records) != 5 or len({row.get("id") for row in records}) != 5:
        raise ValueError("process record log must contain five unique records")
    for row in records:
        if row.get("scoreEffect") != "none":
            raise ValueError(f"process record may not affect score: {row.get('id')}")
        snapshot = row.get("localSnapshot")
        if snapshot:
            snapshot_path = Path(snapshot)
            if not snapshot_path.is_file():
                raise ValueError(f"missing process record snapshot: {snapshot_path}")
            if sha256(snapshot_path) != row.get("sha256"):
                raise ValueError(f"process record snapshot hash mismatch: {snapshot_path}")

    report["meta"]["processRecords"] = {
        "title": "用户补充的全过程记录",
        "introducedAt": payload.get("recordedAt"),
        "purpose": payload.get("purpose"),
        "policy": deepcopy(payload.get("evidencePolicy", {})),
        "records": records,
    }
    report["meta"].setdefault("buildProvenance", {})["processRecords"] = {
        "path": str(PROCESS_RECORDS_LOG.resolve()),
        "sha256": sha256(PROCESS_RECORDS_LOG),
        "schema": payload.get("schema"),
        "recordCount": len(records),
    }

    source_ids = {row.get("id") for row in report.get("sources", [])}
    for row in records:
        if row["id"] in source_ids:
            raise ValueError(f"duplicate process source id: {row['id']}")
        report.setdefault("sources", []).append(
            {
                "id": row["id"],
                "title": row["label"],
                "publisher": row["publisher"],
                "published": "2026-09-05",
                "url": row["url"],
                "priority": 4,
                "cutoffEligible": False,
                "sourceCategory": "user_supplied_process_record",
                "evidenceRole": "process_replay_context",
                "scoreEffect": "none",
                "verificationStatus": row["automatedStatus"],
                "localSnapshotSha256": row.get("sha256"),
            }
        )

    report.setdefault("verification", []).append(
        {
            "id": "verification:user-supplied-process-records",
            "item": "五款工具用户补充全过程记录的入口、归属和自动核验边界",
            "status": "verified_with_disclosed_limitations",
            "reason": (
                "豆包自动匹配六个原始提示；Qoder与千问Markdown已下载、哈希并检查消息块；"
                "WorkBuddy分享页可打开并读取正文，六个原始Prompt的特征句均自动命中；"
                "ZhikunCode滚动长截图已下载并核对文件指纹和尺寸，但未完成整图结构化OCR，六任务范围采用用户明确标注。"
                "五条记录均不直接影响评分。"
            ),
            "owner": "user_and_v4_release_qa",
            "sourceIds": [row["id"] for row in records],
            "scoreEffect": "none",
        }
    )


def merge_configuration_usage_evidence(report: dict[str, Any]) -> None:
    """Add non-scoring configuration/usage screenshots and extracted tables."""

    payload = json.loads(CONFIGURATION_USAGE_LOG.read_text(encoding="utf-8"))
    products = deepcopy(payload.get("products", []))
    images = deepcopy(payload.get("images", []))
    expected_tools = {"豆包", "千问", "Qoder", "WorkBuddy", "ZhikunCode"}
    if len(products) != 5 or {row.get("tool") for row in products} != expected_tools:
        raise ValueError("configuration/usage log must cover all five tools")
    if len(images) != 10 or {row.get("tool") for row in images} != expected_tools:
        raise ValueError("configuration/usage log must contain ten supplied screenshots for five tools")
    if any(row.get("type") not in {"configuration", "usage"} for row in images):
        raise ValueError("configuration/usage screenshot has an unsupported type")

    image_ids = {row.get("id") for row in images}
    if len(image_ids) != 10:
        raise ValueError("configuration/usage screenshot evidence IDs must be unique")
    for product in products:
        if product.get("configurationEvidenceId") not in image_ids:
            raise ValueError(f"product evidence references are incomplete: {product.get('tool')}")
        if product.get("usageEvidenceId") is not None and product.get("usageEvidenceId") not in image_ids:
            raise ValueError(f"product usage evidence reference is unknown: {product.get('tool')}")
    for row in images:
        path = Path(row["path"])
        if not path.is_file():
            raise FileNotFoundError(f"configuration/usage screenshot missing: {path}")
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise ValueError(f"configuration/usage screenshot identity mismatch: {path}")

    display_names = {
        "EV-CONTEXT-DOUBAO-USAGE": "doubao_usage.jpg",
        "EV-CONTEXT-DOUBAO-CONFIG": "doubao_config.jpg",
        "EV-CONTEXT-QIANWEN-USAGE": "qianwen_usage.jpg",
        "EV-CONTEXT-QIANWEN-CONFIG": "qianwen_config.jpg",
        "EV-CONTEXT-QODER-USAGE": "qoder_usage.jpg",
        "EV-CONTEXT-QODER-CONFIG": "qoder_config.jpg",
        "EV-CONTEXT-WORKBUDDY-USAGE": "workbuddy_usage.jpg",
        "EV-CONTEXT-WORKBUDDY-CONFIG": "workbuddy_config.jpg",
        "EV-CONTEXT-ZHIKUN-CONFIG": "zhikuncode_config.jpg",
        "EV-CONTEXT-ZHIKUN-KIMI-USAGE": "zhikuncode_kimi_usage.jpg",
    }
    display_root = NATIVE_V4_ROOT / "evidence" / "embedded" / "context"
    display_paths = {evidence_id: display_root / name for evidence_id, name in display_names.items()}
    if any(not path.is_file() for path in display_paths.values()):
        raise FileNotFoundError("one or more configuration/usage display derivatives are missing")

    report["meta"]["configurationUsageEvidence"] = {
        "title": payload.get("title"),
        "recordedAt": payload.get("recordedAt"),
        "scoreEffect": "none",
        "policy": deepcopy(payload.get("policy", {})),
        "products": products,
        "images": [
            {key: row[key] for key in ("id", "mediaId", "tool", "type", "title", "sha256", "bytes", "width", "height")}
            for row in images
        ],
    }
    report["meta"].setdefault("buildProvenance", {})["configurationUsageEvidence"] = {
        "path": str(CONFIGURATION_USAGE_LOG.resolve()),
        "sha256": sha256(CONFIGURATION_USAGE_LOG),
        "schema": payload.get("schema"),
        "productCount": len(products),
        "imageCount": len(images),
    }

    existing_media = {row["id"] for row in report.get("media", [])}
    existing_evidence = {row["id"] for row in report.get("evidence", [])}
    for row in images:
        if row["mediaId"] in existing_media or row["id"] in existing_evidence:
            raise ValueError(f"duplicate configuration/usage evidence identity: {row['id']}")
        report.setdefault("media", []).append(
            {
                "id": row["mediaId"],
                "path": row["path"],
                "mimeType": mimetypes.guess_type(row["path"])[0] or "application/octet-stream",
                "sha256": row["sha256"],
                "bytes": row["bytes"],
                "width": row["width"],
                "height": row["height"],
                "embedPath": str(display_paths[row["id"]].resolve()),
                "embedMimeType": "image/jpeg",
                "embedSha256": sha256(display_paths[row["id"]]),
                "embedBytes": display_paths[row["id"]].stat().st_size,
                "sourceCategory": "user_supplied_configuration_usage_screenshot",
                "embedded": False,
            }
        )
        report.setdefault("evidence", []).append(
            {
                "id": row["id"],
                "mediaId": row["mediaId"],
                "tool": row["tool"],
                "kind": "context",
                "title": row["title"],
                "description": "用户提供的原始截图；用于说明本次固定样本的配置或额度消耗，不参与评分。",
                "application": row["tool"],
                "locator": f"原图 {row['width']}×{row['height']}",
                "action": "读取原始像素并人工转录可见字段",
                "capturedAt": "2026-09-05",
                "sourceType": "user_supplied_screenshot",
                "evidenceRole": "configuration_and_usage_context",
                "scoreEffect": "none",
                "scoringEligible": False,
                "originalSha256": row["sha256"],
                "originalBytes": row["bytes"],
            }
        )

    report.setdefault("verification", []).append(
        {
            "id": "verification:configuration-usage-evidence",
            "item": "五款工具配置与现有额度截图的文件归属、原图指纹、表格转录与非计分隔离",
            "status": "verified_with_noncomparability_and_privacy_notice",
            "reason": (
                "按文件名映射5款工具，共5张配置截图、4张产品额度截图和1张ZhikunCode外部Kimi API账户日账单旁证；"
                "该账单不是ZhikunCode产品计费页面，且2026-09-04金额混有其他任务，不能归因于本次六任务。"
                "原文件大小与SHA-256在构建时复核。豆包、千问和WorkBuddy仅对单值含义明确的可见记录机械加总；"
                "Qoder双值Credits不加总。不同产品单位不折算，所有记录均不参与评分；"
                "用户确认五款均使用各自最强档，但这不是同模型、同算力或同成本控制实验。"
            ),
            "owner": "user_and_v4_release_qa",
            "evidenceIds": [row["id"] for row in images],
            "scoreEffect": "none",
        }
    )

SUPPLEMENT_FINDING_ALIASES = {
    "QODER-WORD-NAV-01": "NATIVE-WORD-QODER-NAV",
    "QODER-ORD-G1-LAYOUT": "Qoder-image-02",
    "QODER-INK-G1-LAYOUT": "Qoder-ink-02",
}

# The supplement intentionally keeps its evidence catalog artifact-neutral.
# Bind every record explicitly here so neither filenames nor descriptions are
# used as implicit scoring logic.
SUPPLEMENT_EVIDENCE_ARTIFACTS = {
    "EV-DBPPT-SOURCE-SHA": "artifact:doubao:ppt",
    "EV-DBPPT-MAC-REPAIR-PROMPT": "artifact:doubao:ppt",
    "EV-DBPPT-MAC-LOSS-NOTICE": "artifact:doubao:ppt",
    "EV-DBPPT-MAC-SORTER-LOSS": "artifact:doubao:ppt",
    "EV-DBPPT-REPAIR-DIFF": "artifact:doubao:ppt",
    "EV-DBPPT-ZIP-XML": "artifact:doubao:ppt",
    "EV-DBPPT-LO-16PAGE": "artifact:doubao:ppt",
    "EV-DBPPT-LO-RUNLOG": "artifact:doubao:ppt",
    "EV-QW-NAV-EMPTY": "artifact:qoder:word",
    "EV-QW-LOCATOR-LOG": "artifact:qoder:word",
    "EV-QI-ORD-100": "artifact:qoder:image",
    "EV-QI-ORD-1920": "artifact:qoder:image",
    "EV-QI-ORD-A4": "artifact:qoder:image",
    "EV-QI-INK-100": "artifact:qoder:ink",
    "EV-QI-INK-1920": "artifact:qoder:ink",
    "EV-QI-INK-A4": "artifact:qoder:ink",
    "EV-WB-EXCEL-SOURCES": "artifact:workbuddy:excel",
    "EV-WB-SSE-PERIODIC-QUERY": "artifact:workbuddy:excel",
    "EV-WB-SSE-ALL-CONTROL": "artifact:workbuddy:excel",
    "EV-WB-EXCEL-FUND-B48": "artifact:workbuddy:excel",
    "EV-WB-WORD-PAGE03": "artifact:workbuddy:word",
    "EV-WB-WORD-PAGE04": "artifact:workbuddy:word",
    "EV-WB-WORD-FUND-TEXT": "artifact:workbuddy:word",
    "EV-WB-OFFICIAL-FUND-FACTS": "artifact:workbuddy:word",
    "EV-QW-PAGE-MAIN-BUSINESS": "artifact:qoder:word",
    "EV-QW-PAGE-REVENUE-PROFIT": "artifact:qoder:word",
    "EV-QW-PAGE-RD": "artifact:qoder:word",
    "EV-QW-PAGE-ADVANTAGE": "artifact:qoder:word",
    "EV-QW-PAGE-GROWTH": "artifact:qoder:word",
    "EV-QW-PAGE-RISK": "artifact:qoder:word",
}

WORKBUDDY_FUND_LINEAGE_FINDINGS = [
    "WORKBUDDY-W-N01",
    "WORKBUDDY-P-N01",
    "WorkBuddy-image-01",
    "WorkBuddy-ink-01",
    "WorkBuddy-html-01",
]

WORKBUDDY_LOCAL_NATIVE_EVIDENCE = {
    "WORKBUDDY-W-N01": {
        "context": ["EV-WB-WORD-PAGE03", "EV-WB-WORD-PAGE04", "EV-WB-WORD-FUND-NATIVE-EXACT"],
        "exact": ["EV-WB-WORD-FUND-NATIVE-EXACT", direct_evidence_id("WORKBUDDY-W-N01")],
    },
    "WORKBUDDY-P-N01": {
        "context": ["evidence:native:9790ebe437508ec3ca"],
        "exact": ["evidence:native:9790ebe437508ec3ca"],
    },
    "WorkBuddy-image-01": {
        "context": ["evidence:native:e17ba23dad0c865536"],
        "exact": ["EV-WB-ORD-FUND-PIXEL-EXACT"],
    },
    "WorkBuddy-ink-01": {
        "context": ["evidence:native:f7ef0287189f8d22a6"],
        "exact": ["EV-WB-INK-FUND-PIXEL-EXACT"],
    },
    "WorkBuddy-html-01": {
        "context": ["evidence:native:7621492652eb862c25"],
        "exact": [direct_evidence_id("WorkBuddy-html-01")],
    },
}

WORD_NATIVE_PAGE_COUNTS = {
    "artifact:doubao:word": 9,
    "artifact:qianwen:word": 5,
    "artifact:qoder:word": 32,
    "artifact:workbuddy:word": 8,
    "artifact:zhikuncode:word": 12,
}

# Same-artifact native/runtime evidence added to older findings which
# previously pointed only at static extraction crops.  Structured direct
# extracts are added automatically when DIRECT_EVIDENCE_LOG reports `found`.
DIRECT_NATIVE_FINDING_LINKS = {
    "QODER-001": ["evidence:native:473be990ac3d4c5470"],
    "WORKBUDDY-W-N02": ["evidence:native:ccec85abdc6272e001"],
    "WORKBUDDY-P-N02": ["evidence:native:9790ebe437508ec3ca"],
    "WORKBUDDY-P-N04": ["evidence:native:832fbfed80dd05c96a"],
    "ZHIKUN-W-N01": ["evidence:native:b833ea9e3ab4771552"],
    "ZHIKUN-P-N01": ["evidence:native:f39432359313ae4088"],
    "ZhikunCode-image-03": ["evidence:native:e99caa6365e6e90647", "evidence:native:8173bf3ede16d59ff3"],
    "ZhikunCode-ink-03": ["evidence:native:521008faa0cdf97e98", "evidence:native:10359fb17696e08095"],
    "ZhikunCode-html-03": ["evidence:native:f00bf0a0eae75b0d79", "evidence:native:82ad486ef4240966d7"],
    "ZhikunCode-html-04": ["evidence:native:9db2c2e07ac00091b3"],
    "千问-html-01": ["evidence:native:2ffe96da7a25f0dd7a"],
    "千问-html-02": ["evidence:native:7ae055c6e38ceb089b"],
    "千问-html-03": ["evidence:native:2ffe96da7a25f0dd7a"],
    "WORKBUDDY-IMAGE-V2-FIGURE": ["evidence:native:e17ba23dad0c865536", "evidence:native:8206368f424bf2ee7e"],
    "WorkBuddy-ink-03": ["evidence:native:f7ef0287189f8d22a6", "evidence:native:a8e622323dc25bc6de"],
    "WORKBUDDY-INK-V2-FIGURE": ["evidence:native:f7ef0287189f8d22a6", "evidence:native:a8e622323dc25bc6de"],
    "WorkBuddy-html-04": ["evidence:native:71812293d4c55de983", "evidence:native:f4fac7a26ab602ceb5"],
    "WORKBUDDY-HTML-V2-FIGURE": ["evidence:native:7621492652eb862c25"],
    "Qoder-image-02": ["evidence:native:7515f3c2087cba0769", "evidence:native:7568287c5d411a072a"],
    "Qoder-image-03": ["evidence:native:57fff62bd18da78ade"],
    "Qoder-ink-02": ["evidence:native:651c1c2dc9dc42940e", "evidence:native:062bf562ddb9ce9dbd"],
    "Qoder-ink-03": ["evidence:native:0b7d83b3be298c3413"],
    "Qoder-html-01": ["evidence:native:bb4c8cb21b106e4c7b"],
    "Qoder-html-03": ["evidence:native:e12717d5cf1c6e2df9"],
    "Qoder-html-04": ["evidence:native:bb4c8cb21b106e4c7b"],
}

EMBED_DERIVATIVES = {
    "media:supplement:EV-DBPPT-LO-16PAGE": "doubao_libreoffice_contact.webp",
    "media:supplement:EV-QI-ORD-100": "qoder_ordinary_100pct_annotated.webp",
    "media:supplement:EV-QI-ORD-1920": "qoder_ordinary_screen_1920x1080.webp",
    "media:supplement:EV-QI-ORD-A4": "qoder_ordinary_a4_landscape_300dpi.webp",
    "media:supplement:EV-QI-INK-100": "qoder_ink_100pct_annotated.webp",
    "media:supplement:EV-QI-INK-1920": "qoder_ink_screen_1920x1080.webp",
    "media:supplement:EV-QI-INK-A4": "qoder_ink_a4_landscape_300dpi.webp",
    "media:native:6d73e4498bd2cc235431": "doubao_html_fullpage.webp",
    "media:native:c570bafe068037a5154d": "qianwen_html_fullpage.webp",
    "media:native:ac6d0a14e3bcea3bf42b": "qoder_html_fullpage.webp",
    "media:native:9677746001be6e821b20": "workbuddy_html_fullpage.webp",
    "media:native:8e71f292cb665ac44392": "zhikuncode_html_fullpage.webp",
    "media:v4:workbuddy-word-fund-exact": "workbuddy_word_fundraising_exact_native.webp",
    "media:v4:workbuddy-ordinary-fund-exact": "workbuddy_ordinary_fundraising_crop.webp",
    "media:v4:workbuddy-ink-fund-exact": "workbuddy_ink_fundraising_crop.webp",
}

HTML_INTERACTION_POINTS: dict[str, dict[str, float]] = {
    "artifact:doubao:html": {"basic": 7.5, "analysis": 2.0, "integrity": 1.0},
    "artifact:qianwen:html": {"basic": 5.0, "analysis": 0.0, "integrity": 1.0},
    "artifact:qoder:html": {"basic": 5.0, "analysis": 0.0, "integrity": 1.0},
    "artifact:workbuddy:html": {"basic": 4.0, "analysis": 0.0, "integrity": 0.5},
    "artifact:zhikuncode:html": {"basic": 8.5, "analysis": 3.5, "integrity": 1.5},
}

GATE_DEFINITIONS = [
    {
        "code": "G0",
        "order": 0,
        "label": "可按常规复核使用",
        "directUse": True,
        "definition": "没有发现需要在交付前修正的重大问题；不代表免除专业复核。",
    },
    {
        "code": "G1",
        "order": 1,
        "label": "修正后可用",
        "directUse": False,
        "definition": "存在明确的局部质量或可用性问题；完成针对性修正和常规复核后可以使用。",
    },
    {
        "code": "G2",
        "order": 2,
        "label": "禁止未经复核直接交付",
        "directUse": False,
        "definition": "存在核心事实、属性、来源或链路错误；必须修正并完成独立复核，禁止原样直接交付。",
    },
    {
        "code": "G2-Mac",
        "order": 2,
        "label": "Mac环境兼容性待交叉验证",
        "directUse": False,
        "definition": "在本次Mac原生环境发生核心内容损失；因尚无Windows交叉试验，只陈述Mac观察，不外推成全平台故障。",
    },
]

GATE_BY_CODE = {row["code"]: row for row in GATE_DEFINITIONS}

GATE_RULES = [
    {
        "id": "G2-CORE-DIRECTION-REVERSAL",
        "gate": "G2",
        "scope": "all_tools_symmetric",
        "rule": (
            "投资人材料的核心标题若把同页或上游Excel中核心财务指标的绝对正负方向写反，"
            "即使仅影响一页且可用一次文字修改修复，也进入G2；影响比例与修复难度另行披露，不改变闸门。"
        ),
        "appliesTo": "任一工具的PPT、图片、Word或HTML终稿",
    },
    {
        "id": "G1-DISCLOSED-LOCAL-CUTOFF-OVERRUN",
        "gate": "G1",
        "scope": "all_tools_symmetric",
        "rule": (
            "终稿若保留了超过资料截止日的数据，但已明确披露越界日期、"
            "问题仅局限于可单独删除的非强制模块，且没有发生语义恶化，统一标为G1；"
            "下游完全继承不自动升级为G2。"
        ),
        "appliesTo": "任一工具的Excel、Word、PPT、图片或HTML终稿",
    },
]

ZHIKUN_DISCLOSED_CUTOFF_FINDINGS = {
    "ZHIKUN-W-I01",
    "ZHIKUN-P-I01",
    "ZhikunCode-image-01",
    "ZhikunCode-ink-01",
    "ZhikunCode-html-01",
}

# These adjudications are explicit data, not inferred from legacy wording.
GATE_OVERRIDES = {
    "NATIVE-DOUBAO-PPT-REPAIR-LOSS": "G2-Mac",
    "QODER-P-N01": "G2",
    "WORKBUDDY-002": "G1",
    "WORKBUDDY-W-N01": "G2",
    "WORKBUDDY-P-N01": "G2",
    "WorkBuddy-image-01": "G2",
    "WorkBuddy-ink-01": "G2",
    "WorkBuddy-html-01": "G2",
    "Qoder-image-02": "G1",
    "Qoder-image-03": "G1",
    **{finding_id: "G1" for finding_id in ZHIKUN_DISCLOSED_CUTOFF_FINDINGS},
}

GATE_REASON_OVERRIDES = {
    "WORKBUDDY-W-N01": "募集资金属性由‘拟募集’改写为‘已到账’",
    "WORKBUDDY-P-N01": "完全继承Word中的募集资金属性改写",
    "WorkBuddy-image-01": "完全继承Word中的募集资金属性改写",
    "WorkBuddy-ink-01": "完全继承Word中的募集资金属性改写",
    "WorkBuddy-html-01": "完全继承Word中的募集资金属性改写",
    "ZHIKUN-W-I01": "继承Excel中已披露、可单独删除的8月31日估值模块",
    "ZHIKUN-P-I01": "继承Excel中已披露、可单独删除的8月31日估值模块",
    "ZhikunCode-image-01": "继承Excel中已披露的8月31日估值数据",
    "ZhikunCode-image-03": "图片来源仅保留类别和少量名称，无URL或页码",
    "ZhikunCode-ink-01": "继承Excel中已披露的8月31日估值数据",
    "ZhikunCode-ink-03": "水墨风格已重绘，但数据卡片布局仍较接近普通版",
    "ZhikunCode-html-01": "继承Excel中已披露的8月31日估值数据",
    "ZhikunCode-html-03": "HTML相较Excel压缩了来源清单，且仅1项可直接点击",
    "ZhikunCode-html-04": "图表依赖两个外部ECharts CDN，断网时只保留文字提示",
    "HTML-ZK-003": "未先浏览完整页面时直接打印可出现空白页",
    "NATIVE-WORD-ZHIKUN-NAV": "Word未建立可被导航窗格识别的原生标题层级",
}

ARTIFACT_GATE_REASON_OVERRIDES = {
    "artifact:workbuddy:excel": "来源链、报告期口径、预测属性和业务结构分母需局部修正",
    "artifact:zhikuncode:excel": "已披露的8月31日估值模块超过截止日；精确数、跨期口径与来源链仍需修正",
    "artifact:zhikuncode:word": "继承已披露的8月31日估值模块，未发生语义恶化；Word原生标题导航仍需修正",
    "artifact:zhikuncode:ppt": "继承已披露、可单独删除的8月31日估值模块，未发生语义恶化",
    "artifact:zhikuncode:image": "继承已披露的8月31日估值数据；图片来源定位被压缩",
    "artifact:zhikuncode:ink": "继承已披露的8月31日估值数据；水墨版数据卡片布局仍较接近普通版",
    "artifact:zhikuncode:html": "继承已披露的8月31日估值数据；来源、CDN依赖与直接打印仍有局部摩擦",
}

PROPAGATION_ROLES = {
    # Excel-origin issues already scored at Excel; every listed downstream
    # observation is an exact propagation and has no primary deduction.
    **{finding_id: "exact_propagation" for finding_id in [
        "DOUBAO-P-I01", "DOUBAO-W-I01", "DOUBAO-W-I02", "豆包-html-01",
        "豆包-html-02", "豆包-image-01", "豆包-image-02", "豆包-ink-01",
        "QODER-P-I01", "QODER-W-I01", "QODER-W-I02", "Qoder-html-02",
        "Qoder-image-01", "Qoder-ink-01", "WORKBUDDY-P-I01", "WORKBUDDY-W-I01",
        "WORKBUDDY-W-I02", "WORKBUDDY-W-I03", "WorkBuddy-html-02",
        "WorkBuddy-html-03", "WorkBuddy-image-02", "WorkBuddy-image-03",
        "WorkBuddy-ink-02", "ZHIKUN-P-I01", "ZHIKUN-W-I01",
        "ZhikunCode-html-01", "ZhikunCode-html-02", "ZhikunCode-image-01",
        "ZhikunCode-image-02", "ZhikunCode-ink-01", "ZhikunCode-ink-02",
    ]},
    # Qianwen image is the first introduction; the ink image copies it, while
    # the HTML independently introduces a broader, different set of facts.
    "千问-image-01": "origin",
    "千问-image-02": "origin",
    "千问-ink-01": "exact_propagation",
    "千问-html-01": "independently_reintroduced",
    "千问-html-02": "independently_reintroduced",
    # Qoder's two file-local issues originate in their respective final files.
    "QODER-P-N01": "origin",
    "Qoder-html-01": "origin",
    "Qoder-html-03": "origin",
    # WorkBuddy introduces both semantic errors in Word, then copies them.
    "WORKBUDDY-W-N01": "origin",
    "WORKBUDDY-P-N01": "exact_propagation",
    "WorkBuddy-image-01": "exact_propagation",
    "WorkBuddy-ink-01": "exact_propagation",
    "WorkBuddy-html-01": "exact_propagation",
    "WORKBUDDY-W-N02": "origin",
    "WORKBUDDY-P-N02": "exact_propagation",
    "WORKBUDDY-IMAGE-V2-FIGURE": "exact_propagation",
    "WORKBUDDY-INK-V2-FIGURE": "exact_propagation",
    "WORKBUDDY-HTML-V2-FIGURE": "exact_propagation",
}

ROOT_CAUSE_OVERRIDES = {
    # Split the old composite Qoder group into three independently reviewable roots.
    "QODER-P-I01": "RC-QODER-H1-RD-DISCLOSURE",
    "QODER-W-I01": "RC-QODER-H1-RD-DISCLOSURE",
    "QODER-W-I02": "RC-QODER-SOURCE-MIRROR",
    "Qoder-html-02": "RC-QODER-CASH-COLLECTION-TERM",
    "Qoder-image-01": "RC-QODER-CASH-COLLECTION-TERM",
    "Qoder-ink-01": "RC-QODER-CASH-COLLECTION-TERM",
    # Split the old WorkBuddy source/data composite group.
    "WORKBUDDY-P-I01": "RC-WB-EXCEL-COMPOSITE",
    "WORKBUDDY-W-I01": "RC-WB-LEGACY-DATA-AND-RATIO",
    "WORKBUDDY-W-I02": "RC-WB-Q2-PREDICTION",
    "WORKBUDDY-W-I03": "RC-WB-INTERNAL-TRACEABILITY-GAP",
    "WorkBuddy-html-02": "RC-WB-LEGACY-DATA-AND-RATIO",
    "WorkBuddy-html-03": "RC-WB-INTERNAL-TRACEABILITY-GAP",
    "WorkBuddy-image-02": "RC-WB-LEGACY-DATA-AND-RATIO",
    "WorkBuddy-image-03": "RC-WB-INTERNAL-TRACEABILITY-GAP",
    "WorkBuddy-ink-02": "RC-WB-LEGACY-DATA-AND-RATIO",
    # Make the Zhikun cutoff lineage explicit instead of relying on scoreMode text.
    "ZHIKUN-P-I01": "RC-ZHIKUN-CUTOFF-COMPOSITE",
    "ZHIKUN-W-I01": "RC-ZHIKUN-CUTOFF-COMPOSITE",
    "ZhikunCode-html-01": "RC-ZHIKUN-CUTOFF-0831",
    "ZhikunCode-image-01": "RC-ZHIKUN-CUTOFF-0831",
    "ZhikunCode-ink-01": "RC-ZHIKUN-CUTOFF-0831",
    "ZhikunCode-html-02": "RC-ZHIKUN-PRODUCTION-CLAIM",
    "ZhikunCode-image-02": "RC-ZHIKUN-EMPLOYEE-PERIOD",
    "ZhikunCode-ink-02": "RC-ZHIKUN-EMPLOYEE-PERIOD",
}

PROPAGATION_TREATMENTS = {
    "P-DOUBAO-PRODUCT": "excel_origin_scored; downstream_exact_propagation_observation_only",
    "P-QIANWEN-ADD": "origins_and_independent_reintroductions_scored; exact_image_to_ink_copy_restored_only_in_causal_view",
    "P-QODER-ROOT": "split_excel_roots_scored_at_origin; downstream_exact_propagation_observation_only",
    "P-QODER-PPT": "ppt_origin_scored_linearly_and_gated",
    "P-QODER-HTML": "html_origins_scored_linearly",
    "P-WB-SOURCES": "split_excel_roots_scored_at_origin; downstream_exact_propagation_observation_only",
    "P-WB-FUND": "word_origin_scored; downstream_files_scored_independently_and_restored_only_in_causal_view",
    "P-WB-FIGURE": "word_origin_scored; downstream_files_scored_independently_and_restored_only_in_causal_view",
    "P-ZHIKUN-CUTOFF": "excel_origin_scored; all_listed_downstream_findings_are_exact_propagation_observations",
}

NATIVE_INDEX_SUFFIXES = {
    "excel": {"native-open", "formula-recalc-reconciliation", "tab-navigation-editability", "native-charts"},
    "word": {"native-open", "editable-structure", "pagination-print"},
    # Projection readability is a delivery-use observation, not part of the
    # core open/object functionality index. This makes Doubao PPT 3.5/22.
    "ppt": {"native-open-slideshow", "chart-data-editing"},
    "image": {"technical-integrity", "readability-100pct"},
    "ink": {"technical-integrity", "hierarchy-readability"},
    "html": {"chrome-load", "effective-interaction", "responsive-accessibility", "online-resilience"},
}


def rounded(value: float, digits: int = 2) -> float:
    return round(float(value) + 1e-12, digits)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_supplement_reference(supplement_path: Path, reference: str) -> tuple[Path, str | None]:
    """Resolve the supplement package's root-relative evidence reference.

    `merge_supplement.json` lives in `<package>/logs`, while its paths begin
    with `logs/`, `evidence/`, or `../benchmark_...`; they are therefore rooted
    at `<package>`, not at the JSON file's immediate directory. The generated
    ledger stores an absolute path and keeps the original reference separately.
    """

    raw_path, separator, fragment = reference.partition("#")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = supplement_path.resolve().parent.parent / candidate
    return candidate.resolve(), fragment if separator else None


def json_fragment_exists(path: Path, fragment: str | None) -> bool:
    if fragment is None or fragment == "":
        return True
    if path.suffix.lower() != ".json":
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    if fragment.startswith("/"):
        current: Any = payload
        for raw_part in fragment[1:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return False
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True

    # The fact-ledger reference uses a comma-separated set of stable fact IDs
    # rather than JSON Pointer syntax.
    wanted = {item for item in fragment.split(",") if item}
    if not wanted:
        return False
    rows = payload.get("facts", []) if isinstance(payload, dict) else payload
    available = {str(row.get("id")) for row in rows if isinstance(row, dict)}
    return wanted <= available


def supplement_evidence_status(evidence_type: str) -> str:
    if evidence_type == "native_screenshot":
        return "native_verified"
    if evidence_type in {"annotated_source_pixels", "screen_simulation", "print_simulation"}:
        return "verified_derived_visual"
    if evidence_type == "cross_implementation_render":
        return "verified_cross_implementation"
    if evidence_type == "official_api_response":
        return "verified_official_response"
    if evidence_type == "fact_ledger_reference":
        return "verified_reference"
    if evidence_type == "hash_record":
        return "verified_hash_record"
    return "verified_structured_record"


def merge_supplement_evidence(
    report: dict[str, Any], supplement_path: Path | None
) -> dict[str, Any] | None:
    """Merge a read-only evidence supplement without changing score inputs."""

    provenance: dict[str, Any] = {
        "status": "not_loaded",
        "path": str(supplement_path.resolve()) if supplement_path is not None else None,
    }
    report["meta"]["buildProvenance"]["supplement"] = provenance
    if supplement_path is None or not supplement_path.exists():
        return None

    supplement_path = supplement_path.resolve()
    supplement = json.loads(supplement_path.read_text(encoding="utf-8"))
    if supplement.get("schema") != "native-audit-v4-merge-supplement-1.0":
        raise ValueError(f"unsupported supplement schema: {supplement.get('schema')!r}")

    finding_ids = {finding["id"] for finding in report["findings"]}
    artifact_ids = {artifact["id"] for artifact in report["artifacts"]}
    existing_evidence_ids = {evidence["id"] for evidence in report["evidence"]}
    existing_media_ids = {media["id"] for media in report["media"]}
    catalog_ids = {row["id"] for row in supplement.get("evidenceCatalog", [])}
    if len(catalog_ids) != len(supplement.get("evidenceCatalog", [])):
        raise ValueError("duplicate supplement evidence IDs")
    missing_bindings = catalog_ids - set(SUPPLEMENT_EVIDENCE_ARTIFACTS)
    stale_bindings = set(SUPPLEMENT_EVIDENCE_ARTIFACTS) - catalog_ids
    if missing_bindings or stale_bindings:
        raise ValueError(
            f"supplement artifact bindings mismatch: missing={sorted(missing_bindings)}, stale={sorted(stale_bindings)}"
        )

    for source_row in supplement.get("evidenceCatalog", []):
        evidence_id = source_row["id"]
        media_id = f"media:supplement:{evidence_id}"
        if evidence_id in existing_evidence_ids or media_id in existing_media_ids:
            raise ValueError(f"supplement ID collision: {evidence_id}")
        artifact_id = SUPPLEMENT_EVIDENCE_ARTIFACTS[evidence_id]
        if artifact_id not in artifact_ids:
            raise ValueError(f"supplement evidence references unknown artifact: {artifact_id}")
        evidence_path, fragment = resolve_supplement_reference(supplement_path, source_row["path"])
        if not evidence_path.is_file():
            raise FileNotFoundError(f"supplement evidence is unreadable: {evidence_path}")
        if not json_fragment_exists(evidence_path, fragment):
            raise ValueError(f"supplement evidence fragment does not resolve: {source_row['path']}")
        mime_type = mimetypes.guess_type(evidence_path.name)[0] or "application/octet-stream"
        report["media"].append(
            {
                "id": media_id,
                "artifactId": artifact_id,
                "path": str(evidence_path),
                "originalReferencePath": source_row["path"],
                "fragment": fragment,
                "mimeType": mime_type,
                "bytes": evidence_path.stat().st_size,
                "sha256": sha256(evidence_path),
                "embedded": False,
                "status": "supplement_verified",
                "sourceSupplement": str(supplement_path),
            }
        )
        evidence_row = {
                "id": evidence_id,
                "artifactId": artifact_id,
                "mediaId": media_id,
                "type": source_row["type"],
                "locator": source_row["path"],
                "description": source_row["description"],
                "capturedAt": "2026-09-05",
                "status": supplement_evidence_status(source_row["type"]),
                "action": "只读导入native-audit-v4补充证据并校验证据文件与片段定位",
                "application": "evidence supplement",
                "appVersion": supplement["schema"],
                "sourceEvidencePath": str(evidence_path),
                "sourceReferenceFragment": fragment,
                "originalReferencePath": source_row["path"],
                "sourceSupplement": str(supplement_path),
                "fragmentResolved": True,
            }
        if evidence_id == "EV-WB-OFFICIAL-FUND-FACTS":
            evidence_row.update(
                {
                    "nonScoring": True,
                    "evidenceRole": "external_actual_funding_context_only",
                    "scoringExclusionReason": (
                        "现实中募集资金是否到账不能替代Excel同值、同期间、同属性锚点，"
                        "不用于推翻Excel→下游链路判断。"
                    ),
                }
            )
        report["evidence"].append(evidence_row)

    normalized_links: dict[str, list[str]] = {}
    for raw_finding_id, evidence_ids in supplement.get("findingEvidenceLinks", {}).items():
        finding_id = SUPPLEMENT_FINDING_ALIASES.get(raw_finding_id, raw_finding_id)
        if finding_id not in finding_ids:
            raise ValueError(f"supplement links unknown finding: {raw_finding_id} -> {finding_id}")
        if not set(evidence_ids) <= catalog_ids:
            raise ValueError(f"supplement links unknown evidence for finding: {raw_finding_id}")
        normalized_links.setdefault(finding_id, []).extend(evidence_ids)

    normalized_subtests = []
    for source_row in supplement.get("rubricSubtests", []):
        row = deepcopy(source_row)
        row["findingId"] = SUPPLEMENT_FINDING_ALIASES.get(row["findingId"], row["findingId"])
        if row["findingId"] not in finding_ids:
            raise ValueError(f"supplement subtest links unknown finding: {row['findingId']}")
        if row["artifactId"] not in artifact_ids:
            raise ValueError(f"supplement subtest links unknown artifact: {row['artifactId']}")
        if not set(row.get("evidenceIds", [])) <= catalog_ids:
            raise ValueError(f"supplement subtest links unknown evidence: {row['subtestId']}")
        row["sourceSupplement"] = str(supplement_path)
        normalized_subtests.append(row)
        normalized_links.setdefault(row["findingId"], []).extend(row.get("evidenceIds", []))

    # The official SSE query and the all-announcements control support only the
    # WorkBuddy source-title observation.  They are not evidence for the
    # separate prediction-attribute finding.
    official_query_ids = ["EV-WB-SSE-PERIODIC-QUERY", "EV-WB-SSE-ALL-CONTROL"]
    normalized_links.setdefault("WORKBUDDY-001", []).extend(official_query_ids)
    normalized_links.setdefault("WORKBUDDY-001", []).append("EV-WB-EXCEL-SOURCES")

    # Every member of the funding lineage receives the upstream Excel anchor.
    # Local-file proof is adjudicated separately below; the upstream anchor
    # must never be mistaken for direct proof of a descendant's wording.
    for finding_id in WORKBUDDY_FUND_LINEAGE_FINDINGS:
        normalized_links.setdefault(finding_id, []).append("EV-WB-EXCEL-FUND-B48")

    finding_map = {finding["id"]: finding for finding in report["findings"]}
    all_evidence_ids = {evidence["id"] for evidence in report["evidence"]}
    for finding_id, local_roles in WORKBUDDY_LOCAL_NATIVE_EVIDENCE.items():
        # Direct v4 evidence is merged immediately after this supplement; only
        # bind IDs already present at this stage.
        local_ids = [evidence_id for evidence_id in local_roles["context"] if evidence_id in all_evidence_ids]
        finding_map[finding_id]["evidenceIds"] = list(
            dict.fromkeys(finding_map[finding_id].get("evidenceIds", []) + local_ids)
        )
    for finding_id, evidence_ids in normalized_links.items():
        unique_ids = list(dict.fromkeys(evidence_ids))
        finding = finding_map[finding_id]
        finding["evidenceIds"] = list(dict.fromkeys(finding.get("evidenceIds", []) + unique_ids))
        finding["supplementEvidenceIds"] = unique_ids

    provenance.update(
        {
            "status": "loaded_read_only",
            "path": str(supplement_path),
            "sha256": sha256(supplement_path),
            "schema": supplement["schema"],
            "evidenceCount": len(supplement.get("evidenceCatalog", [])),
            "rubricSubtestCount": len(normalized_subtests),
        }
    )
    return {
        "path": str(supplement_path),
        "schema": supplement["schema"],
        "sha256": provenance["sha256"],
        "catalogIds": sorted(catalog_ids),
        "findingEvidenceLinks": {
            finding_id: list(dict.fromkeys(evidence_ids))
            for finding_id, evidence_ids in normalized_links.items()
        },
        "rubricSubtests": normalized_subtests,
        "compatibilityMatrixRows": deepcopy(supplement.get("compatibilityMatrixRows", [])),
        "compatibilityUnverifiedRows": deepcopy(supplement.get("compatibilityUnverifiedRows", [])),
        "legacyPropagationScoreModeReview": deepcopy(supplement.get("propagationScoreModeReview", {})),
    }


def compact_extract(text: str, limit: int = 12000) -> str:
    """Keep exact text evidence while removing embedded binary/data-URI noise."""

    lines = []
    for line in str(text or "").splitlines():
        if len(line) > 1200:
            prefix = line[:240]
            lines.append(f"{prefix} … [超长内嵌资源省略；原行{len(line)}字符，源文件SHA已保留]")
        else:
            lines.append(line)
    result = "\n".join(lines)
    if len(result) > limit:
        result = result[:limit] + f"\n… [结构化摘录截断；完整摘录见证据日志，共{len(result)}字符]"
    return result


def add_file_evidence(
    report: dict[str, Any], *, evidence_id: str, artifact_id: str, evidence_type: str,
    path: Path, locator: str, description: str, status: str,
) -> None:
    """Append one immutable local visual and its media identity."""

    if not path.is_file():
        raise FileNotFoundError(f"required v4 evidence missing: {path}")
    media_id = {
        "EV-WB-WORD-FUND-NATIVE-EXACT": "media:v4:workbuddy-word-fund-exact",
        "EV-WB-ORD-FUND-PIXEL-EXACT": "media:v4:workbuddy-ordinary-fund-exact",
        "EV-WB-INK-FUND-PIXEL-EXACT": "media:v4:workbuddy-ink-fund-exact",
    }[evidence_id]
    report["media"].append(
        {
            "id": media_id,
            "artifactId": artifact_id,
            "path": str(path.resolve()),
            "mimeType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "embedded": False,
            "status": "v4_direct_evidence",
        }
    )
    report["evidence"].append(
        {
            "id": evidence_id,
            "artifactId": artifact_id,
            "mediaId": media_id,
            "type": evidence_type,
            "locator": locator,
            "description": description,
            "capturedAt": "2026-09-05",
            "status": status,
            "action": "在字节一致核验副本中定位争议表述；不更新外部域、不编辑、不保存",
            "application": "Microsoft Word 16.112.3" if artifact_id.endswith(":word") else "macOS Preview",
            "appVersion": "16.112.3" if artifact_id.endswith(":word") else "macOS 26.5.2",
            "exactLocator": True,
        }
    )


def add_structured_fragment_evidence(
    report: dict[str, Any], *, evidence_id: str, artifact_id: str, path: Path,
    fragment: str, evidence_type: str, locator: str, description: str,
    extracted: Any,
) -> None:
    if not path.is_file() or not json_fragment_exists(path, fragment):
        raise ValueError(f"structured evidence does not resolve: {path}#{fragment}")
    report["evidence"].append(
        {
            "id": evidence_id,
            "artifactId": artifact_id,
            "type": evidence_type,
            "locator": locator,
            "description": description,
            "capturedAt": "2026-09-05",
            "status": "verified_exact_structured",
            "action": "从原始Office OOXML/HTML或核验日志确定性提取并核对源文件SHA-256",
            "application": "deterministic read-only extractor",
            "appVersion": "direct-finding-evidence-1.0",
            "sourceEvidencePath": str(path.resolve()),
            "sourceReferenceFragment": fragment,
            "sourceEvidenceSha256": sha256(path),
            "fragmentResolved": True,
            "exactLocator": True,
            "extracted": extracted,
        }
    )


def merge_v4_direct_evidence(report: dict[str, Any]) -> None:
    """Add same-artifact direct evidence and disputed WorkBuddy exact views."""

    artifact_ids = {artifact["id"] for artifact in report["artifacts"]}
    finding_map = {finding["id"]: finding for finding in report["findings"]}
    evidence_ids = {row["id"] for row in report["evidence"]}

    direct_payload = json.loads(DIRECT_EVIDENCE_LOG.read_text(encoding="utf-8"))
    if direct_payload.get("schema") != "direct-finding-evidence-1.0":
        raise ValueError("unexpected direct evidence schema")
    for index, record in enumerate(direct_payload.get("records", [])):
        finding_id = record["findingId"]
        artifact_id = record["artifactId"]
        if finding_id not in finding_map or artifact_id not in artifact_ids:
            raise ValueError(f"direct evidence refers to unknown target: {finding_id}/{artifact_id}")
        if finding_map[finding_id]["artifactId"] != artifact_id:
            raise ValueError(f"direct evidence artifact mismatch: {finding_id}/{artifact_id}")
        if record.get("extractionStatus") != "found":
            continue
        evidence_id = direct_evidence_id(finding_id)
        if evidence_id in evidence_ids:
            raise ValueError(f"direct evidence ID collision: {evidence_id}")
        fragment = f"/records/{index}"
        source_path = Path(record["sourcePath"])
        if not source_path.is_file() or sha256(source_path) != record["sourceSha256"]:
            raise ValueError(f"direct evidence source identity mismatch: {finding_id}")
        extracted = {
            "sourceArtifactSha256": record["sourceSha256"],
            "extractionStatus": record["extractionStatus"],
            "extractionMethod": record["extractionMethod"],
            "extractedLocators": record.get("extractedLocators", []),
            "excerpt": compact_extract(record.get("excerpt", "")),
        }
        locator = record.get("locator", "")
        if finding_id == "WORKBUDDY-W-N01":
            locator = "DOCX OOXML中两处资金属性表述；原生页面定位以Word第6页截图为准"
        add_structured_fragment_evidence(
            report,
            evidence_id=evidence_id,
            artifact_id=artifact_id,
            path=DIRECT_EVIDENCE_LOG,
            fragment=fragment,
            evidence_type="same_artifact_structured_extract",
            locator=locator,
            description=f"{finding_id}：从同一终稿原件直接提取的可复核定位。",
            extracted=extracted,
        )
        evidence_ids.add(evidence_id)
        finding_map[finding_id]["evidenceIds"] = list(
            dict.fromkeys(finding_map[finding_id].get("evidenceIds", []) + [evidence_id])
        )

    # Exact Word and source-pixel crops created during the native re-check.
    add_file_evidence(
        report,
        evidence_id="EV-WB-WORD-FUND-NATIVE-EXACT",
        artifact_id="artifact:workbuddy:word",
        evidence_type="native_screenshot",
        path=NATIVE_V4_ROOT / "evidence" / "workbuddy_word_fundraising_exact_native.jpg",
        locator="Word原生第6页，查找结果高亮‘IPO募资42.02亿元到账’",
        description="Word 16.112.3原生打印布局；用户选择不更新外部域后，页面身份、页码和争议原句同屏可见。",
        status="native_verified",
    )
    add_file_evidence(
        report,
        evidence_id="EV-WB-ORD-FUND-PIXEL-EXACT",
        artifact_id="artifact:workbuddy:image",
        evidence_type="direct_source_pixel_crop",
        path=NATIVE_V4_ROOT / "evidence" / "workbuddy_ordinary_fundraising_crop.png",
        locator="普通信息图资金优势区，原始像素裁片",
        description="从原图无改字裁取，清晰显示‘IPO募资42.02亿元到账’；整图Preview证据另行关联。",
        status="verified_exact_visual",
    )
    add_file_evidence(
        report,
        evidence_id="EV-WB-INK-FUND-PIXEL-EXACT",
        artifact_id="artifact:workbuddy:ink",
        evidence_type="direct_source_pixel_crop",
        path=NATIVE_V4_ROOT / "evidence" / "workbuddy_ink_fundraising_crop.png",
        locator="水墨信息图资金优势区，原始像素裁片",
        description="从原图无改字裁取，清晰显示‘IPO募资42.02亿元到账’；整图Preview证据另行关联。",
        status="verified_exact_visual",
    )

    # Three-column prediction evidence: prediction input, completed-tense
    # conclusion and actual-number derivation are kept separate and explicit.
    wb_log = NATIVE_V4_ROOT / "logs" / "workbuddy_evidence_upgrade.json"
    wb_payload = json.loads(wb_log.read_text(encoding="utf-8"))
    prediction_fields = [
        ("EV-WB-PREDICTION-INPUT", "预测输入", "WorkBuddy预测输入及其预测属性"),
        ("EV-WB-PREDICTION-CONCLUSION", "底稿结论", "WorkBuddy结论页使用‘已回升’完成时"),
        ("EV-WB-PREDICTION-ACTUAL-DERIVATION", "截止日前实际/可复算结果", "用截止日前H1与Q1实际值复算Q2单季利润率"),
    ]
    for evidence_id, field, description in prediction_fields:
        extracted = wb_payload["predictionThreeColumn"]["row"][field]
        add_structured_fragment_evidence(
            report,
            evidence_id=evidence_id,
            artifact_id="artifact:workbuddy:excel",
            path=wb_log,
            fragment=f"/predictionThreeColumn/row/{field.replace('/', '~1')}",
            evidence_type="structured_cell_extract" if field != "截止日前实际/可复算结果" else "structured_derivation",
            locator=(extracted.get("sheet", "可复算结果") + (f"!{extracted['cell']}" if extracted.get("cell") else "")),
            description=description,
            extracted=extracted,
        )
        finding_map["WORKBUDDY-002"]["evidenceIds"] = list(
            dict.fromkeys(finding_map["WORKBUDDY-002"].get("evidenceIds", []) + [evidence_id])
        )
    finding_map["WORKBUDDY-002"]["evidenceIds"] = list(
        dict.fromkeys(
            finding_map["WORKBUDDY-002"].get("evidenceIds", [])
            + [
                "evidence:native:b1c9443bfc5f46b373",
                "evidence:native:741dd86f3097a5fd39",
                "evidence:native:76b550e3d1971eaaef",
                "evidence:native:4c025d3cf5995d85e0",
            ]
        )
    )

    # The source-title finding is a two-sided discrepancy: the workbook's
    # native source sheet plus the official channel search/corpus.  The control
    # query validates the request but is not described as a second independent
    # proof of non-existence.
    official_reference_id = "EV-WB-OFFICIAL-DISCLOSURE-CORPUS"
    report["evidence"].append(
        {
            "id": official_reference_id,
            "artifactId": "artifact:workbuddy:excel",
            "type": "official_source_reference",
            "locator": "SSE-PROSPECTUS / SSE-LISTING / SSE-NOTICE；截止日2026-08-30",
            "description": "一级来源账本实际采用招股说明书、上市公告书与上市通知；与底稿所列报告标题逐项对照。",
            "capturedAt": "2026-09-05",
            "status": "verified_reference",
            "action": "将底稿标题与上交所定期报告筛选、IPO披露和上市日期交叉对照",
            "application": "SSE official disclosures + fact ledger",
            "appVersion": "v4",
            "sourceIds": ["SSE-PROSPECTUS", "SSE-LISTING", "SSE-NOTICE"],
            "factIds": ["F-REV-2025", "F-H1-REV", "F-LISTING"],
            "exactLocator": True,
        }
    )
    finding_map["WORKBUDDY-001"]["evidenceIds"] = list(
        dict.fromkeys(finding_map["WORKBUDDY-001"].get("evidenceIds", []) + [official_reference_id])
    )

    evidence_map = {row["id"]: row for row in report["evidence"]}
    # Slide 14 visibly contains the full disputed phrase and slide identity;
    # mark this pre-existing native screenshot as an exact locator.
    evidence_map["evidence:native:9790ebe437508ec3ca"]["exactLocator"] = True
    for finding_id, roles in WORKBUDDY_LOCAL_NATIVE_EVIDENCE.items():
        all_local_ids = list(dict.fromkeys(roles["context"] + roles["exact"]))
        missing_exact = set(roles["exact"]) - set(evidence_map)
        if missing_exact:
            raise ValueError(f"missing exact v4 WorkBuddy evidence: {finding_id}/{sorted(missing_exact)}")
        all_local_ids = [evidence_id for evidence_id in all_local_ids if evidence_id in evidence_map]
        finding_map[finding_id]["evidenceIds"] = list(
            dict.fromkeys(finding_map[finding_id].get("evidenceIds", []) + all_local_ids)
        )
    for finding_id, link_ids in DIRECT_NATIVE_FINDING_LINKS.items():
        if finding_id not in finding_map:
            raise ValueError(f"native evidence map references unknown finding: {finding_id}")
        for evidence_id in link_ids:
            if evidence_id not in evidence_map:
                raise ValueError(f"native evidence map references unknown evidence: {finding_id}/{evidence_id}")
            if evidence_map[evidence_id].get("artifactId") != finding_map[finding_id]["artifactId"]:
                raise ValueError(f"native evidence artifact mismatch: {finding_id}/{evidence_id}")
        finding_map[finding_id]["evidenceIds"] = list(
            dict.fromkeys(finding_map[finding_id].get("evidenceIds", []) + link_ids)
        )


def update_native_word_page_metadata(report: dict[str, Any]) -> None:
    artifacts = {artifact["id"]: artifact for artifact in report["artifacts"]}
    for artifact_id, native_pages in WORD_NATIVE_PAGE_COUNTS.items():
        metadata = artifacts[artifact_id].setdefault("metadata", {})
        legacy_pages = metadata.get("pages")
        if legacy_pages != native_pages:
            metadata["legacyStaticPageEstimate"] = legacy_pages
            metadata["legacyEstimatedPages"] = legacy_pages
        metadata["pages"] = native_pages
        metadata["pageCountSource"] = "Microsoft Word 16.112.3 native print layout coverage"


def assign_embed_derivatives(report: dict[str, Any]) -> None:
    embedded_root = NATIVE_V4_ROOT / "evidence" / "embedded"
    media_map = {row["id"]: row for row in report["media"]}
    for media_id, filename in EMBED_DERIVATIVES.items():
        if media_id not in media_map:
            if media_id.startswith("media:supplement:"):
                continue
            raise ValueError(f"embed derivative references unknown media: {media_id}")
        derivative = embedded_root / filename
        if not derivative.is_file():
            raise FileNotFoundError(f"embed derivative missing: {derivative}")
        media_map[media_id]["embedPath"] = str(derivative.resolve())
        media_map[media_id]["embedMimeType"] = "image/webp"
        media_map[media_id]["embedSha256"] = sha256(derivative)
        media_map[media_id]["embedBytes"] = derivative.stat().st_size


def criterion(report: dict[str, Any], artifact_id: str, suffix: str) -> dict[str, Any]:
    rows = report["scores"]["artifacts"][artifact_id]["criterionScores"]
    return next(row for row in rows if row["criterionId"].endswith(suffix))


def definition_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        definition["id"]: definition
        for definitions in report["criteriaDefinitions"].values()
        for definition in definitions
    }


def add_subitem_schema(report: dict[str, Any]) -> None:
    report["criteriaAnchorSets"] = {
        "holistic-0-5-v4.1": {
            "scope": "all_holistic_criteria_all_tools",
            "anchors": {
                "0": "缺失、不可用或未完成",
                "1": "重大失败，仅少量可用",
                "2": "存在实质缺口，需较多返工",
                "3": "满足基本交付，但有明显摩擦",
                "4": "完成良好，仅有轻微缺陷",
                "5": "优秀，未观察到实质摩擦",
            },
            "increment": "整体判断通常使用0.5档；点数子测试按机械得分换算，可能产生其他小数。",
        }
    }
    for definitions in report["criteriaDefinitions"].values():
        for definition in definitions:
            definition.setdefault("scoringMode", "anchored_holistic")
            definition.setdefault("anchorSetId", "holistic-0-5-v4.1")
    for definition in report["criteriaDefinitions"]["html"]:
        if definition["id"] == "criterion:html:effective-interaction":
            definition["scoringMode"] = "point_subitems"
            definition["subitems"] = [
                {
                    "id": "basic",
                    "label": "基础交互合规",
                    "maxPoints": 9,
                    "anchor": "导航、悬浮和既有控件逐项真实工作；未要求的筛选器不作为负项。",
                },
                {
                    "id": "analysis",
                    "label": "分析增益",
                    "maxPoints": 4,
                    "anchor": "切换、筛选、折叠或钻取确实改变分析视图并降低查找成本。",
                },
                {
                    "id": "integrity",
                    "label": "键盘等效与交互诚信",
                    "maxPoints": 2,
                    "anchor": "核心交互可由键盘到达、状态反馈清楚且不存在无功能的点击暗示。",
                },
            ]
    for definition in report["criteriaDefinitions"]["excel"]:
        if definition["id"] == "criterion:excel:native-charts":
            definition["scoringMode"] = "point_subitems"
            definition["subitems"] = [
                {
                    "id": "native_editability",
                    "label": "原生对象与可编辑性",
                    "maxPoints": 2,
                    "anchor": "图表为原生对象，可正常打开并编辑数据。",
                },
                {
                    "id": "data_binding",
                    "label": "系列、横轴与数据引用",
                    "maxPoints": 2,
                    "anchor": "系列、分类轴、数据范围和顺序与底层数据一致。",
                },
                {
                    "id": "trend_readability",
                    "label": "单位、期间与趋势表达",
                    "maxPoints": 2,
                    "anchor": "单位、期间和标签足以让正常用户读出正确趋势。",
                },
            ]
        if definition["id"] == "criterion:excel:native-open":
            definition["subitemPolicy"] = "出现修复时按可观察结果分项，不使用文件级固定罚分。"
    for definition in report["criteriaDefinitions"]["ppt"]:
        if definition["id"] == "criterion:ppt:native-open-slideshow":
            definition["subitemPolicy"] = "出现修复时按干净打开、无损修复、完整放映、保存重开逐项计分。"
        if definition["id"] == "criterion:ppt:chart-data-editing":
            definition["subitemPolicy"] = "按对象保留、编辑数据、输入联动、保存重开逐项计分。"
    for definition in report["criteriaDefinitions"]["word"]:
        if definition["id"] == "criterion:word:retrieval-expression":
            definition["scoringMode"] = "point_subitems"
            definition["subitems"] = [
                {"id": "heading_coverage", "label": "六主题原生标题覆盖率", "maxPoints": 2},
                {"id": "two_step_navigation", "label": "导航窗格两步内直达成功率", "maxPoints": 1},
                {"id": "ctrl_f_success", "label": "Ctrl+F查找成功率", "maxPoints": 1},
                {"id": "first_hit_precision", "label": "首次命中正确章节精确率", "maxPoints": 1},
            ]


def set_point_subitems(
    row: dict[str, Any], subitems: list[dict[str, Any]], *, basis: str, finding_ids: list[str] | None = None
) -> None:
    maximum = sum(float(item["maxPoints"]) for item in subitems)
    earned = sum(float(item["earnedPoints"]) for item in subitems)
    if maximum <= 0:
        raise ValueError("subitem maximum must be positive")
    row["subitemScores"] = subitems
    row["rating0To5"] = rounded(earned / maximum * 5, 6)
    row["weighted"] = rounded(earned)
    row["basis"] = basis
    if finding_ids is not None:
        row["findingIds"] = finding_ids


def rebuild_subscores(report: dict[str, Any]) -> None:
    # HTML: preserve the native observations, but expose the previously opaque
    # 15-point judgement as three auditable point buckets.
    for artifact_id, points in HTML_INTERACTION_POINTS.items():
        row = criterion(report, artifact_id, "effective-interaction")
        subitems = [
            {"id": "basic", "maxPoints": 9, "earnedPoints": points["basic"]},
            {"id": "analysis", "maxPoints": 4, "earnedPoints": points["analysis"]},
            {"id": "integrity", "maxPoints": 2, "earnedPoints": points["integrity"]},
        ]
        set_point_subitems(row, subitems, basis=row["basis"])

    # Qoder Word: mechanical five-point locator test across the six required
    # themes.  This replaces the prior holistic 2.5/5 judgement.
    word_log = json.loads(QODER_WORD_LOCATOR_LOG.read_text(encoding="utf-8"))
    tasks = word_log["tasks"]
    task_count = len(tasks)
    if task_count != 6:
        raise ValueError("Qoder Word locator log must contain six required-theme tasks")
    heading_pass = sum(task["directHeadingNavigation"]["status"] == "passed" for task in tasks)
    ctrl_f_pass = sum(task["fullTextFallback"]["status"] == "passed" for task in tasks)
    first_hit_pass = sum(
        task["fullTextFallback"]["status"] == "passed"
        and task["fullTextFallback"].get("matches")
        and task["fullTextFallback"]["matches"][0].get("text") == task["targetQuery"]
        for task in tasks
    )
    row = criterion(report, "artifact:qoder:word", "retrieval-expression")
    set_point_subitems(
        row,
        [
            {"id": "heading_coverage", "label": "六主题原生标题覆盖率", "maxPoints": 2, "earnedPoints": 2 * heading_pass / task_count, "result": f"{heading_pass}/{task_count}"},
            {"id": "two_step_navigation", "label": "导航窗格两步内直达成功率", "maxPoints": 1, "earnedPoints": heading_pass / task_count, "result": f"{heading_pass}/{task_count}"},
            {"id": "ctrl_f_success", "label": "Ctrl+F查找成功率", "maxPoints": 1, "earnedPoints": ctrl_f_pass / task_count, "result": f"{ctrl_f_pass}/{task_count}"},
            {"id": "first_hit_precision", "label": "首次命中正确章节精确率", "maxPoints": 1, "earnedPoints": first_hit_pass / task_count, "result": f"{first_hit_pass}/{task_count}"},
        ],
        basis=(
            f"机械计分：原生标题覆盖{heading_pass}/{task_count}=0/2；两步内导航直达{heading_pass}/{task_count}=0/1；"
            f"Ctrl+F成功{ctrl_f_pass}/{task_count}=1/1；首次命中正确章节{first_hit_pass}/{task_count}=1/1；合计2/5。"
        ),
        finding_ids=["NATIVE-WORD-QODER-NAV"],
    )
    row["measurementLog"] = str(QODER_WORD_LOCATOR_LOG.resolve())
    row["taskIds"] = [task["taskId"] for task in tasks]

    # Excel charts: award Qianwen full credit for native/editable objects, but
    # no credit for five-of-five incorrect series/category configurations.
    for artifact in report["artifacts"]:
        if artifact["kind"] != "excel":
            continue
        row = criterion(report, artifact["id"], "native-charts")
        if artifact["id"] == "artifact:qianwen:excel":
            subitems = [
                {"id": "native_editability", "maxPoints": 2, "earnedPoints": 2},
                {"id": "data_binding", "maxPoints": 2, "earnedPoints": 0},
                {"id": "trend_readability", "maxPoints": 2, "earnedPoints": 0},
            ]
            basis = (
                "5/5图表均为可编辑原生对象，取得可编辑性2分；5/5均把年份误作系列且存在倒序引用，"
                "数据绑定和趋势表达各0分。配置错误是原Prompt所要求趋势图表的实质缺陷，但不抹去对象可编辑性。"
            )
            set_point_subitems(row, subitems, basis=basis, finding_ids=["QIANWEN-001"])
        else:
            subitems = [
                {"id": "native_editability", "maxPoints": 2, "earnedPoints": 2},
                {"id": "data_binding", "maxPoints": 2, "earnedPoints": 2},
                {"id": "trend_readability", "maxPoints": 2, "earnedPoints": 2},
            ]
            set_point_subitems(row, subitems, basis=row["basis"])

    # The same open/edit/save test is exposed for every workbook. Four files
    # pass all five observations; Doubao is overridden below from its repair
    # evidence. This prevents a tool-specific repair rubric.
    for artifact in report["artifacts"]:
        if artifact["kind"] != "excel":
            continue
        row = criterion(report, artifact["id"], "native-open")
        set_point_subitems(
            row,
            [
                {"id": "clean_open", "label": "无需修复直接打开", "maxPoints": 4, "earnedPoints": 4},
                {"id": "inventory_preserved", "label": "Sheet与图表保全", "maxPoints": 2, "earnedPoints": 2},
                {"id": "function_preserved", "label": "公式与图表功能保全", "maxPoints": 2, "earnedPoints": 2},
                {"id": "editability", "label": "可编辑", "maxPoints": 1, "earnedPoints": 1},
                {"id": "save_reopen", "label": "保存关闭重开", "maxPoints": 1, "earnedPoints": 1},
            ],
            basis=row["basis"],
        )

    # Doubao Excel: replace v3's fixed -8 with evidence-based native-open
    # subscores. It fails clean open, but its repaired copy preserves inventory,
    # formulas/charts, editing, and save/reopen behaviour.
    row = criterion(report, "artifact:doubao:excel", "native-open")
    set_point_subitems(
        row,
        [
            {"id": "clean_open", "label": "无需修复直接打开", "maxPoints": 4, "earnedPoints": 0},
            {"id": "inventory_preserved", "label": "修复后Sheet与图表保全", "maxPoints": 2, "earnedPoints": 2},
            {"id": "function_preserved", "label": "修复后公式与图表功能保全", "maxPoints": 2, "earnedPoints": 2},
            {"id": "editability", "label": "修复副本可编辑", "maxPoints": 1, "earnedPoints": 1},
            {"id": "save_reopen", "label": "保存关闭重开", "maxPoints": 1, "earnedPoints": 1},
        ],
        basis=(
            "首次打开必须修复，干净打开0/4；修复后10个Sheet、6张图、公式和编辑功能保留，且保存重开稳定，"
            "其余子项6/6。该6/10直接进入线性分，不再另扣固定8分。"
        ),
        finding_ids=["NATIVE-DOUBAO-EXCEL-REPAIR"],
    )

    # Likewise, apply the same native-open and chart-editing observations to
    # every presentation before replacing Doubao with its failed Mac results.
    for artifact in report["artifacts"]:
        if artifact["kind"] != "ppt":
            continue
        row = criterion(report, artifact["id"], "native-open-slideshow")
        set_point_subitems(
            row,
            [
                {"id": "clean_open", "label": "干净打开", "maxPoints": 3, "earnedPoints": 3},
                {"id": "lossless_repair", "label": "无需修复或修复无损", "maxPoints": 2, "earnedPoints": 2},
                {"id": "complete_slideshow", "label": "完整放映", "maxPoints": 3, "earnedPoints": 3},
                {"id": "save_reopen", "label": "保存重开", "maxPoints": 2, "earnedPoints": 2},
            ],
            basis=row["basis"],
        )
        row = criterion(report, artifact["id"], "chart-data-editing")
        set_point_subitems(
            row,
            [
                {"id": "objects_retained", "label": "图表对象保留", "maxPoints": 3, "earnedPoints": 3},
                {"id": "edit_data", "label": "编辑数据", "maxPoints": 5, "earnedPoints": 5},
                {"id": "linkage", "label": "数据联动", "maxPoints": 2, "earnedPoints": 2},
                {"id": "save_reopen", "label": "图表保存重开", "maxPoints": 2, "earnedPoints": 2},
            ],
            basis=row["basis"],
        )

    # Doubao PPT: the Mac observation is scored directly in the two affected
    # native criteria. No penalty and no cap is added afterwards.
    row = criterion(report, "artifact:doubao:ppt", "native-open-slideshow")
    set_point_subitems(
        row,
        [
            {"id": "clean_open", "label": "干净打开", "maxPoints": 3, "earnedPoints": 0},
            {"id": "lossless_repair", "label": "无损修复", "maxPoints": 2, "earnedPoints": 0},
            {"id": "complete_slideshow", "label": "完整放映", "maxPoints": 3, "earnedPoints": 1.5},
            {"id": "save_reopen", "label": "修复副本保存重开", "maxPoints": 2, "earnedPoints": 2},
        ],
        basis=(
            "Mac PowerPoint首次打开必须修复；修复并非无损，16页中8页可完整放映，修复副本可保存重开。"
            "得分0+0+1.5+2=3.5/10。Windows尚未交叉验证，因此归入G2-Mac而非全平台故障。"
        ),
        finding_ids=["NATIVE-DOUBAO-PPT-REPAIR-LOSS"],
    )
    row = criterion(report, "artifact:doubao:ppt", "chart-data-editing")
    set_point_subitems(
        row,
        [
            {"id": "objects_retained", "label": "图表对象保留", "maxPoints": 3, "earnedPoints": 0},
            {"id": "edit_data", "label": "编辑数据", "maxPoints": 5, "earnedPoints": 0},
            {"id": "linkage", "label": "数据联动", "maxPoints": 2, "earnedPoints": 0},
            {"id": "save_reopen", "label": "图表保存重开", "maxPoints": 2, "earnedPoints": 0},
        ],
        basis="Mac修复副本中7张图表和7个嵌入工作簿全部丢失，四项均无法完成，得0/12。",
        finding_ids=["NATIVE-DOUBAO-PPT-REPAIR-LOSS"],
    )

    # Qoder image: keep the v3 total unchanged, but place the observed layout
    # impact in the dimensions a normal office user actually experiences.
    # File decoding/canvas integrity remains full credit; hierarchy,
    # legibility and investor-use finish carry the 10.5-point loss.
    row = criterion(report, "artifact:qoder:image", "technical-integrity")
    row.update(
        rating0To5=5.0,
        weighted=5.0,
        basis="PNG可完整解码，4800×3000画布、像素与色彩文件技术属性正常；版面遮挡另在层级、可读性和投资人视觉维度评价。",
        findingIds=[],
    )
    row = criterion(report, "artifact:qoder:image", "hierarchy-composition")
    row.update(
        rating0To5=4.0,
        weighted=12.0,
        basis="整体分区和主次关系可辨，但多处标题叠印及底栏压住下排图表，削弱层级边界，得12/15。",
        findingIds=["Qoder-image-02"],
    )
    row = criterion(report, "artifact:qoder:image", "readability-100pct")
    row.update(
        rating0To5=3.5,
        weighted=10.5,
        basis="核心数字仍可读；标题重叠和部分横轴/底部标签受遮挡，在原像素100%、1920×1080适应窗口及A4模拟中均形成局部阅读摩擦，得10.5/15。",
        findingIds=["Qoder-image-02"],
    )
    row = criterion(report, "artifact:qoder:image", "investor-visual")
    row.update(
        rating0To5=3.5,
        weighted=7.0,
        basis="配色与数据密度接近汇报成品，但可见的标题叠印和下沿遮挡需修正后才适合直接给投资人展示，得7/10。",
        findingIds=["Qoder-image-02"],
    )

    # Qoder ink image: likewise preserve the 79.5 total.  Style judgement is
    # kept separate from the inherited layout/readability defect.
    row = criterion(report, "artifact:qoder:ink", "technical-integrity")
    row.update(
        rating0To5=5.0,
        weighted=5.0,
        basis="PNG可完整解码，4800×3000画布与像素文件属性正常；可读性问题不重复计入技术完整性。",
        findingIds=[],
    )
    row = criterion(report, "artifact:qoder:ink", "ordinary-image-preservation")
    row.update(
        basis="普通版的核心数字、六个图表和主要结论均保持；可读性与风格完成度分别在对应维度评价。"
    )
    row = criterion(report, "artifact:qoder:ink", "hierarchy-readability")
    row.update(
        rating0To5=3.0,
        weighted=9.0,
        basis="核心数字可辨，但标题叠印、下沿遮挡及部分浅灰文字对比不足影响分区阅读，得9/15。",
        findingIds=["Qoder-ink-02"],
    )
    row = criterion(report, "artifact:qoder:ink", "professional-composition")
    row.update(
        rating0To5=4.0,
        weighted=12.0,
        basis="宣纸、山形和印章形成统一视觉，但原版几何网格与水墨元素衔接有限，且局部叠印降低成品感，得12/15。",
        findingIds=["Qoder-ink-02"],
    )
    row = criterion(report, "artifact:qoder:ink", "output-finish")
    row.update(
        rating0To5=3.5,
        weighted=3.5,
        basis="分辨率和导出完整；若用于100%打印或投屏，仍需修正局部文字重叠和底部遮挡，得3.5/5。",
        findingIds=["Qoder-ink-02"],
    )


def artifact_population(report: dict[str, Any], artifact_id: str) -> tuple[int | None, str]:
    items = [item for item in report["coverageItems"] if item["artifactId"] == artifact_id]
    if not items:
        return None, "artifact"
    coverage_type = items[0].get("coverageType", "unit")
    return len(items), coverage_type


def lineage_roles(report: dict[str, Any]) -> dict[str, str]:
    finding_ids = {finding["id"] for finding in report["findings"]}
    unknown = set(PROPAGATION_ROLES) - finding_ids
    if unknown:
        raise ValueError(f"explicit lineage references unknown findings: {sorted(unknown)}")
    return dict(PROPAGATION_ROLES)


def upgrade_propagation(report: dict[str, Any]) -> dict[str, str]:
    """Replace v3 prose score modes with explicit v4 causal treatment."""

    legacy_modes: dict[str, str] = {}
    finding_ids = {finding["id"] for finding in report["findings"]}
    for propagation in report["propagation"]:
        propagation_id = propagation["id"]
        if propagation_id not in PROPAGATION_TREATMENTS:
            raise ValueError(f"missing explicit v4 propagation treatment: {propagation_id}")
        if "scoreMode" in propagation:
            legacy_modes[propagation_id] = propagation.pop("scoreMode")
        propagation["scoreTreatment"] = PROPAGATION_TREATMENTS[propagation_id]
        propagation["status"] = "v4_adjudicated"
        propagation["lineageRoleByFinding"] = {
            finding_id: PROPAGATION_ROLES[finding_id]
            for finding_id in propagation.get("findingIds", [])
            if finding_id in finding_ids
        }
        propagation["rootCauseIds"] = sorted(
            {
                ROOT_CAUSE_OVERRIDES.get(finding_id, propagation_id)
                for finding_id in propagation.get("findingIds", [])
            }
        )
        if propagation_id == "P-ZHIKUN-CUTOFF":
            propagation["lineageRole"] = "exact_propagation"
    return legacy_modes


def add_non_scoring_verification(report: dict[str, Any]) -> None:
    verification_id = "verification:v4:workbuddy-actual-funds-received"
    report["verification"] = [row for row in report["verification"] if row.get("id") != verification_id]
    report["verification"].append(
        {
            "id": verification_id,
            "status": "pending_manual_non_scoring",
            "nonScoring": True,
            "topic": "WorkBuddy所述42.02亿元现实中是否实际到账",
            "reason": (
                "v4计分只判断下游是否忠实沿用本工具Excel；现实中后来是否到账属于另一事实问题，"
                "不得用来推翻Excel→下游链路不一致。"
            ),
            "requiredEvidence": "截止日前正式发行结果、募集资金验资或上市公告中的到账信息及明确口径。",
        }
    )


def requested_gate(finding: dict[str, Any]) -> str | None:
    if finding["id"] in GATE_OVERRIDES:
        return GATE_OVERRIDES[finding["id"]]
    if finding.get("deducted") and finding.get("severity") in {"major", "critical"}:
        return "G1"
    return None


def extend_findings(report: dict[str, Any]) -> None:
    roles = lineage_roles(report)
    artifacts = {artifact["id"]: artifact for artifact in report["artifacts"]}
    for finding in report["findings"]:
        artifact = artifacts[finding["artifactId"]]
        if finding["id"] == "WORKBUDDY-002":
            finding["severity"] = "major"
        if finding["id"] in {"Qoder-image-02", "Qoder-image-03", "Qoder-ink-02"}:
            finding["severity"] = "major"
        if finding["id"] in ZHIKUN_DISCLOSED_CUTOFF_FINDINGS:
            # The overrun is explicit and isolated to a removable valuation
            # module. Exact propagation preserves G1 instead of creating G2.
            finding["severity"] = "major"
        population, unit = artifact_population(report, finding["artifactId"])
        legacy_adjustment = {
            "capPolicyId": finding.get("capPolicyId"),
            "penaltyPolicyId": finding.get("penaltyPolicyId"),
        }
        if any(legacy_adjustment.values()):
            finding["legacyV3Adjustment"] = legacy_adjustment
        finding["capPolicyId"] = None
        finding["penaltyPolicyId"] = None
        finding["lineageRole"] = roles.get(finding["id"], "origin")
        finding["scope"] = {
            "observedLocations": 1 if finding.get("locator") else 0,
            "population": population,
            "populationUnit": unit,
            "locator": finding.get("locator", ""),
        }
        finding["detectability"] = "requires_source_or_lineage_check"
        finding["repairEffort"] = "targeted_review"
        finding["deliveryGateRequest"] = requested_gate(finding)
        finding["gate"] = finding["deliveryGateRequest"] or "G0"
        finding["rootCauseId"] = ROOT_CAUSE_OVERRIDES.get(
            finding["id"],
            finding.get("propagationId")
            or finding.get("rootFindingId")
            or finding.get("deduplicationKey")
            or finding["id"],
        )
        immediate_kind = {
            "excel": None,
            "word": "excel",
            "ppt": "word",
            "image": "ppt",
            "ink": "image",
            "html": "ppt",
        }[artifact["kind"]]
        finding["immediateUpstreamArtifactId"] = (
            None if immediate_kind is None else f"artifact:{artifact['id'].split(':')[1]}:{immediate_kind}"
        )
        finding["observation"] = (
            f"在{finding.get('locator') or '所列文件位置'}观察到：{finding.get('summary', '')}"
        )
        finding["interpretation"] = (
            f"按统一规则归为{finding.get('classification', 'observation')}，严重度{finding.get('severity', 'info')}；"
            "该解释与原始观察分开记录。"
        )
        if finding["id"] == "NATIVE-DOUBAO-PPT-REPAIR-LOSS":
            finding["causeStatus"] = "confirmed_in_fixed_mac_environment_cross_platform_unresolved"
            finding["falsificationCriteria"] = (
                "用与原件SHA-256一致的副本在另一受支持PowerPoint环境干净打开，且16页、7图和7个嵌入工作簿全部保留；"
                "满足后仅推翻全平台归因，Mac本次观察仍保留。"
            )
        elif finding["lineageRole"] == "exact_propagation":
            finding["causeStatus"] = "confirmed_exact_propagation"
            finding["falsificationCriteria"] = (
                "证明该表述并非来自已定位上游，或提供文件内更早且独立的正确锚点，并经逐字/数值链路复核。"
            )
        elif finding["lineageRole"] == "mutated":
            finding["causeStatus"] = "confirmed_mutation"
            finding["falsificationCriteria"] = "证明下游语义和属性与立即上游完全相同，且没有扩大、改写或新增。"
        elif finding["lineageRole"] == "independently_reintroduced":
            finding["causeStatus"] = "confirmed_independent_reintroduction"
            finding["falsificationCriteria"] = "证明新增内容可直接回溯至本工具Excel中的同值、同期间、同属性锚点。"
        else:
            finding["causeStatus"] = "confirmed_origin" if finding.get("confidence") == "high" else "provisional_origin"
            finding["falsificationCriteria"] = (
                "提供与文件版本、位置和期间一致的反证，或在相同原生环境复测证明观察不存在。"
            )
        finding["scoreTreatmentV4"] = "linear_criterion_only"
        finding["criterionDelta"] = {
            "points": 0.0,
            "semantic": "dimension_gap_equal_attribution_share",
            "isFindingRemovalCounterfactual": False,
            "definition": "该finding在所属维度相对满分缺口中的等额归因份额；不是删除该finding后分数必然回升的反事实增量。",
        }
        finding["scoreImpact"] = {
            "dimensionGapAttributionShare": 0.0,
            "causalRestoration": 0.0,
            "v3CapImpact": 0.0,
            "v3PenaltyImpact": 0.0,
            "v3CapOrPenaltyImpact": 0.0,
        }

    overrides = {
        "QODER-P-N01": {
            "scope": {
                "observedLocations": 1,
                "population": 20,
                "populationUnit": "slides",
                "locator": "PPT第10页标题",
                "exposureZone": "content_slide_title",
            },
            "detectability": "high_same_slide_numeric_contradiction",
            "repairEffort": "single_text_edit_plus_revalidation",
            "falsificationCriteria": (
                "在SHA-256相同的PPT第10页证明标题并非‘双双转负’，或证明同页及Excel中的24,393.03万元和23,154.53万元为负值；"
                "仅说明同比为负不能推翻绝对值正负方向观察。"
            ),
        },
        "QIANWEN-001": {
            "scope": {
                "observedLocations": 5,
                "population": 5,
                "populationUnit": "charts",
                "locator": "趋势图表中的5张原生图表",
                "exposureZone": "required_trend_charts",
            },
            "detectability": "high_in_native_chart_legend",
            "repairEffort": "reconfigure_five_chart_series",
            "falsificationCriteria": (
                "在SHA-256相同工作簿中逐图证明5张图的年份位于分类轴、指标位于数据系列，且不存在倒序引用；"
                "需同时提供Excel原生‘选择数据’结果或等价OOXML系列公式。"
            ),
        },
        "NATIVE-DOUBAO-PPT-REPAIR-LOSS": {
            "scope": {
                "observedLocations": 8,
                "population": 16,
                "populationUnit": "slides",
                "additionalLostObjects": 7,
                "locator": "修复副本第5—9、11—13页及7张图表",
                "exposureZone": "core_file_content",
            },
            "detectability": "immediate_on_open_and_slideshow",
            "repairEffort": "rebuild_or_cross_platform_recover",
            "scoreTreatmentV4": "two_native_criteria_plus_platform_gate",
        },
        "NATIVE-DOUBAO-EXCEL-REPAIR": {
            "detectability": "immediate_on_open",
            "repairEffort": "one_repair_then_save_reopen",
            "scoreTreatmentV4": "native_open_subitems",
            "falsificationCriteria": (
                "在同一Mac Excel版本用SHA-256相同首次打开副本证明无需修复即可打开；修复后可用并不能推翻干净打开失败。"
            ),
        },
        "WORKBUDDY-001": {
            "summary": (
                "底稿把《宇树科技2025年年度报告》和《宇树科技2026年第一季度报告》列为A级来源；"
                "截至2026-08-30未能在指定上交所定期报告渠道定位这些标题，已定位的一级来源为IPO披露文件。"
            ),
            "observation": (
                "资料来源!B5:B6、E5:E6、I5:I6列出上述两个报告标题并标A级；"
                "同代码、同截止日的上交所定期报告筛选返回0条，全公告对照返回IPO公告。"
            ),
            "interpretation": (
                "仅判定‘作品给出的A级来源标题截至截止日未能在指定官方渠道定位’，不推断生成意图；"
                "全公告对照仅用于验证查询条件有效，不冒充第二项独立的缺失证明。"
            ),
            "causeStatus": "confirmed_source_title_nonlocation_in_designated_official_channel",
            "falsificationCriteria": (
                "提供截至2026-08-30已正式发布且可由上交所公告系统定位的《2025年年度报告》和《2026年第一季度报告》，"
                "并证明底稿关键数字确实来自这些文件；相近名称的招股材料不能替代。"
            ),
            "repairEffort": "replace_sources_and_retrace_all_dependent_numbers",
        },
        "WORKBUDDY-002": {
            "summary": "预测参考表中的31.11%—34.42%区间在核心结论中被改写为‘2026Q2扣非净利率已回升’的完成时。",
            "observation": (
                "预测参考(非事实)!B12:D12标明‘预告推算/据券商拆分’，分析结论!B9写‘已回升’；"
                "用截止日前H1与Q1披露实际数复算Q2单季约27.9237%。"
            ),
            "interpretation": "判定为预测属性在核心结论中变为完成时；不推断主观意图，且相邻预告区间提示使其按major/G1处理。",
            "causeStatus": "confirmed_prediction_attribute_changed_to_completed_tense",
            "falsificationCriteria": (
                "证明‘2026Q2扣非净利率已回升’在文件实际使用位置被持续标为预计/推算，或提供截止日前正式实现值；"
                "预测参考Sheet中的免责声明不能自动覆盖结论页的已实现语态。"
            ),
            "repairEffort": "rewrite_fact_attribute_and_revalidate_conclusion",
        },
    }
    for finding_id in [
        "WORKBUDDY-W-N01",
        "WORKBUDDY-P-N01",
        "WorkBuddy-image-01",
        "WorkBuddy-ink-01",
        "WorkBuddy-html-01",
    ]:
        overrides[finding_id] = {
            "falsificationCriteria": (
                "仅可通过证明WorkBuddy Excel在同值、同期间和同属性下已有‘42.02亿元到账’锚点来推翻本链路判断；"
                "Excel外的现实到账凭证不改变‘下游是否忠实沿用本工具Excel’这一计分问题。"
            ),
            "repairEffort": "correct_phrase_and_revalidate_all_funding_references",
        }
    by_id = {finding["id"]: finding for finding in report["findings"]}
    for finding_id, values in overrides.items():
        by_id[finding_id].update(values)


def apply_v41_adjudication(report: dict[str, Any]) -> None:
    """Apply defensible v4.1 wording, lineage and terminal-risk rules.

    Attribution answers where a defect first arose.  Terminal risk answers
    whether the bytes in the current file are safe to hand off.  Those are
    deliberately separate fields and must never be inferred from each other.
    """

    by_id = {finding["id"]: finding for finding in report["findings"]}
    workbuddy = by_id["WORKBUDDY-001"]
    workbuddy.update(
        {
            "severity": "major",
            "confidence": "high",
            "summary": (
                "资料来源表的A级标签与本工作簿内可复核颗粒度不一致：B5:B6给出报告名称，"
                "E5:E6仅显示上交所首页域名文字，未提供报告级可点击直链、页码或表号；I5:I6又注明为数据库/媒体转引并建议核对原文。"
            ),
            "observation": (
                "资料来源!B5:B6列出两个报告标题，E5:E6仅为‘www.sse.com.cn’文本且OOXML未发现对应超链接关系；"
                "I5:I6分别注明‘A股财务数据库转引’和‘媒体及行情数据库转引，建议核对原文’。"
            ),
            "interpretation": (
                "扣分只针对原Prompt要求的‘保留资料来源’在本次固定终稿内的可追溯交付质量；"
                "不对两份报告是否存在、报告名称真伪、相关数据的现实准确性或生成意图作不利判断。"
            ),
            "causeStatus": "confirmed_artifact_internal_traceability_gap",
            "claimBoundary": (
                "本finding只能证明‘作品的A级标注与工作簿内可追溯材料不匹配’，"
                "不能证明来源绝对不存在。WorkBuddy若在工作簿之外持有有效原文链接，也不改变固定终稿内尚未保留该定位信息的观察。"
            ),
            "falsificationCriteria": (
                "证明同一SHA-256工作簿在Excel原生界面或OOXML中已包含报告级可点击链接或等效定位，"
                "且能直达支撑关键数字的页码、表号或等效位置。"
            ),
            "remediationCriteria": (
                "后续补充报告级直链和页码可作为修复，但不回溯改写本次固定样本的原始交付状态；"
                "若提供新版终稿，可按同一规则另行复测。"
            ),
            "repairEffort": "add_direct_primary_links_page_locators_and_retrace_cited_values",
            "deliveryGateRequest": "G1",
            "gate": "G1",
            "externalTruthChecked": False,
            "independentEvidenceCount": 1,
            "evidenceIds": [
                evidence_id
                for evidence_id in workbuddy.get("evidenceIds", [])
                if evidence_id in {"evidence:native:a8c02381ed0feb0246", "evidence:native:b7f325003275f5f298", "EV-WB-EXCEL-SOURCES"}
            ],
        }
    )

    for finding in report["findings"]:
        role = finding.get("lineageRole", "origin")
        finding["attributionTreatment"] = {
            "origin": "origin_scored_if_criterion_cites_finding",
            "exact_propagation": "display_only_in_lineage_attribution",
            "mutated": "mutation_scored_if_criterion_cites_finding",
            "independently_reintroduced": "independent_reintroduction_scored_if_criterion_cites_finding",
        }.get(role, "review_required")
        finding["independentFinalTreatment"] = (
            "scored_if_criterion_cites_finding" if finding.get("deducted") else "observation_only"
        )
        requested = finding.get("deliveryGateRequest")
        if not requested and finding.get("severity") == "critical":
            requested = "G2"
        finding["terminalRiskCode"] = requested or "G0"
        finding["terminalRiskReason"] = (
            "终端文件仍含该问题，风险等级不因其是上游继承而消失；归责是否重复是另一问题。"
            if role == "exact_propagation"
            else "按本件问题的严重度、影响位置和统一闸门规则判断。"
        )
        if finding["id"] in ZHIKUN_DISCLOSED_CUTOFF_FINDINGS:
            finding["terminalRiskReason"] = (
                "终端仍保留了已明示超过截止日的局部估值数据，交付前需删除或替换；"
                "下游没有改写语义，因此保持G1，不因传播升级为G2。"
            )
        finding["deliveryGateRequest"] = finding["terminalRiskCode"] if finding["terminalRiskCode"] != "G0" else None
        finding["gate"] = finding["terminalRiskCode"]
        finding["criterionDelta"]["semantic"] = "mechanical_criterion_gap_allocation_share"
        finding["criterionDelta"]["definition"] = (
            "该数值只是把所属维度相对满分的缺口在同维度finding之间机械均分，"
            "用于解释分数构成；不是因果效应，也不是删除该finding后的反事实增量。"
        )
        if role == "exact_propagation":
            # Preserve the v3 label only as explicitly versioned history.  It
            # is not a second active classification and must never be used by
            # filters, scores, gates or prose in the v4.1 report.
            finding["v3ClassificationBeforeLineageReaudit"] = finding.get("classification")
            finding.pop("legacyClassification", None)
            finding["classification"] = "exact_propagation"
            finding["interpretation"] = (
                "经链路核对归为exact_propagation：该终稿仍含相同内容风险，但链路归责只回到已定位的起源节点；"
                "不称为下游新增，也不在归责统计中重复计算。"
            )

    # A fully inherited WorkBuddy Excel issue keeps the same G1 terminal-risk
    # class as its Excel origin unless a downstream file changes its meaning.
    # This prevents an inherited traceability or estimate-label gap from being
    # silently escalated to G2 merely because it appeared in another format.
    inherited_workbuddy_g1 = {
        "WORKBUDDY-W-I01",
        "WORKBUDDY-W-I02",
        "WORKBUDDY-W-I03",
        "WORKBUDDY-P-I01",
        "WorkBuddy-image-02",
        "WorkBuddy-image-03",
        "WorkBuddy-ink-02",
        "WorkBuddy-html-02",
        "WorkBuddy-html-03",
    }
    for finding_id in inherited_workbuddy_g1:
        finding = by_id[finding_id]
        finding.update(
            {
                "severity": "major",
                "terminalRiskCode": "G1",
                "deliveryGateRequest": "G1",
                "gate": "G1",
                "deducted": False,
            }
        )
    by_id["WORKBUDDY-W-I03"].update(
        {
            "summary": "Word沿用Excel资料来源表中的两个报告名称；本项只标示工作簿内部可追溯颗粒度不足的传播，不判定报告不存在。",
            "observation": "Word第1、5页沿用Excel资料来源!B5:B6的报告名称；没有发现Word独立新增不存在性主张。",
            "claimBoundary": "仅属exact_propagation，不重复扣分；不对报告是否存在作判断。",
        }
    )
    by_id["WorkBuddy-image-03"].update(
        {
            "summary": "图片沿用Excel资料来源!B5:B6的报告名称；本项仅记录内部可追溯颗粒度不足的传播。",
            "claimBoundary": "不判定报告不存在，不重复扣分。",
        }
    )
    by_id["WorkBuddy-html-03"].update(
        {
            "summary": "HTML沿用Excel资料来源表的报告名称与日期；本项仅记录内部可追溯颗粒度不足的传播。",
            "claimBoundary": "不判定报告不存在，不重复扣分。",
        }
    )

    qoder_ppt = by_id["QODER-P-N01"]
    qoder_ppt["gateRuleId"] = "G2-CORE-DIRECTION-REVERSAL"
    qoder_ppt["interpretation"] = (
        "投资人材料的核心标题把绝对正负方向写反；依据预先公开、对五款工具对称适用的"
        "G2-CORE-DIRECTION-REVERSAL规则进入G2。影响范围为1/20页，修复动作为一处标题修改；"
        "范围小和易修复不改变未经复核不得交付的风险判断。"
    )

    ordinary = by_id["Qoder-image-02"]
    ordinary.update(
        {
            "summary": "9个预设检查区中7区存在标题叠印或横轴/底栏裁切；核心数字大多仍可读。",
            "observation": "Z1、Z3—Z6标题叠印，Z7—Z8横轴/底栏边界被部分裁切；Z2通过，Z9另记为适应窗口时来源文字过小。",
            "scope": {"observedLocations": 7, "population": 9, "populationUnit": "predefined_image_zones", "locator": "Z1、Z3—Z8", "exposureZone": "titles_and_lower_axis_boundary"},
            "falsificationCriteria": "在同一SHA-256原图中逐区证明Z1、Z3—Z8不存在所列叠印或裁切；缩放查看不能改变源像素中已存在的重叠。",
        }
    )
    ink = by_id["Qoder-ink-02"]
    ink.update(
        {
            "summary": "9个预设检查区中8区出现标题叠印或底栏侵入；来源区另有低对比与适应窗口字号问题。",
            "observation": "Z1—Z6标题叠印，Z7—Z8记录为底栏边界侵入；Z9来源文字存在但低对比且适应窗口时过小。",
            "scope": {"observedLocations": 8, "population": 9, "populationUnit": "predefined_image_zones", "locator": "Z1—Z8", "exposureZone": "titles_and_lower_axis_boundary"},
            "falsificationCriteria": "在同一SHA-256水墨图中逐区证明Z1—Z8不存在所列叠印或底栏侵入；缩放查看不能改变源像素中的布局关系。",
        }
    )

    by_id["WORKBUDDY-W-N01"].update(
        {
            "locator": "Word原生第6页；OOXML中两处资金属性表述",
            "scope": {
                "observedLocations": 2,
                "population": 8,
                "populationUnit": "native_pages",
                "locator": "Word原生第6页；‘募集资金到位’与‘IPO募资42.02亿元到账’",
                "exposureZone": "body_and_competitive_advantage",
            },
            "observation": (
                "Word原生第6页出现‘IPO募资42.02亿元到账’，同一DOCX结构化提取另定位‘叠加IPO募集资金到位’；"
                "Excel上游仅列420,200万元为拟募集/计划金额。"
            ),
            "interpretation": "相较本工具Excel发生拟募集/计划金额→到位/到账的链路属性改写；不以现实世界后来到账与否替代该一致性判断。",
        }
    )

    # Link the two most disputed findings directly to the native evidence that
    # resolved them. Legacy crops remain available but are no longer the only
    # evidence attached to the finding itself.
    qianwen_chart_evidence = criterion(report, "artifact:qianwen:excel", "native-charts").get("evidenceIds", [])
    by_id["QIANWEN-001"]["evidenceIds"] = list(
        dict.fromkeys(by_id["QIANWEN-001"].get("evidenceIds", []) + qianwen_chart_evidence)
    )
    qoder_slide_10 = next(
        item
        for item in report["coverageItems"]
        if item["artifactId"] == "artifact:qoder:ppt" and item.get("ordinal") == 10
    )
    by_id["QODER-P-N01"]["evidenceIds"] = list(
        dict.fromkeys(by_id["QODER-P-N01"].get("evidenceIds", []) + qoder_slide_10.get("evidenceIds", []))
    )
    evidence_by_id = {evidence["id"]: evidence for evidence in report["evidence"]}
    for finding in report["findings"]:
        linked = [evidence_by_id[eid] for eid in finding.get("evidenceIds", []) if eid in evidence_by_id]
        finding["evidenceStatusV4"] = {
            "linkedCount": len(linked),
            "nativeOrRuntimeCount": sum(
                evidence.get("status") in {"verified_native", "native_verified", "verified_runtime"}
                or evidence.get("type", "").startswith("native")
                for evidence in linked
            ),
            "sameArtifactNonLegacyCount": sum(
                evidence.get("artifactId") == finding["artifactId"]
                and evidence.get("status") != "legacy_static"
                for evidence in linked
            ),
            "exactStructuredOrVisualCount": sum(
                evidence.get("artifactId") == finding["artifactId"]
                and bool(evidence.get("exactLocator"))
                for evidence in linked
            ),
            "legacyOnly": bool(linked) and all(evidence.get("status") == "legacy_static" for evidence in linked),
        }


def finalize_supplement_evidence_status(
    report: dict[str, Any], supplement_context: dict[str, Any] | None
) -> None:
    """Separate upstream proof, local context, and exact local proof.

    In particular, an Excel anchor cannot be reported as direct evidence of a
    downstream file's wording. Broad full-artifact screenshots are useful local
    context, but remain pending until the disputed phrase has an exact locator
    screenshot or equivalent native extract.
    """

    if supplement_context is None:
        return
    evidence_map = {evidence["id"]: evidence for evidence in report["evidence"]}
    finding_map = {finding["id"]: finding for finding in report["findings"]}

    for finding_id in WORKBUDDY_FUND_LINEAGE_FINDINGS:
        finding = finding_map[finding_id]
        declared = WORKBUDDY_LOCAL_NATIVE_EVIDENCE[finding_id]
        local_context_ids = declared["context"]
        exact_local_ids = declared["exact"]
        for evidence_id in local_context_ids:
            evidence = evidence_map[evidence_id]
            if evidence.get("artifactId") != finding["artifactId"]:
                raise ValueError(
                    f"local evidence artifact mismatch: {finding_id}/{evidence_id}/"
                    f"{evidence.get('artifactId')}"
                )
            if evidence.get("type") != "native_screenshot":
                raise ValueError(f"declared local native evidence is not a native screenshot: {evidence_id}")
        for evidence_id in exact_local_ids:
            evidence = evidence_map[evidence_id]
            if evidence.get("artifactId") != finding["artifactId"]:
                raise ValueError(
                    f"exact evidence artifact mismatch: {finding_id}/{evidence_id}/"
                    f"{evidence.get('artifactId')}"
                )
            if not evidence.get("exactLocator"):
                raise ValueError(f"declared exact evidence lacks exactLocator: {evidence_id}")

        upstream_ids = ["EV-WB-EXCEL-FUND-B48"]
        external_context_ids = (
            ["EV-WB-OFFICIAL-FUND-FACTS"] if finding_id == "WORKBUDDY-W-N01" else []
        )
        local_structured_ids = (
            ["EV-WB-WORD-FUND-TEXT"] if finding_id == "WORKBUDDY-W-N01" else []
        )
        exact_confirmed = bool(exact_local_ids) and bool(upstream_ids)
        status = (
            "verified_upstream_and_exact_local_native"
            if exact_confirmed
            else "pending_exact_local_native_evidence"
        )
        linked = [evidence_map[eid] for eid in finding.get("evidenceIds", []) if eid in evidence_map]
        finding["evidenceStatusV4"] = {
            "status": status,
            "linkedCount": len(linked),
            "nativeOrRuntimeCount": sum(
                evidence.get("status") in {"verified_native", "native_verified", "verified_runtime"}
                or evidence.get("type", "").startswith("native")
                for evidence in linked
            ),
            "sameArtifactNonLegacyCount": sum(
                evidence.get("artifactId") == finding["artifactId"]
                and evidence.get("status") != "legacy_static"
                for evidence in linked
            ),
            "exactStructuredOrVisualCount": sum(
                evidence.get("artifactId") == finding["artifactId"]
                and bool(evidence.get("exactLocator"))
                for evidence in linked
            ),
            "legacyOnly": bool(linked) and all(
                evidence.get("status") == "legacy_static" for evidence in linked
            ),
            "upstreamAnchorEvidenceIds": upstream_ids,
            "localNativeContextEvidenceIds": local_context_ids,
            "localExactEvidenceIds": exact_local_ids,
            "localStructuredEvidenceIds": local_structured_ids,
            "nonScoringExternalContextEvidenceIds": external_context_ids,
            "directEvidenceConfirmed": exact_confirmed,
            "pendingReason": (
                None
                if exact_confirmed
                else "已有本件原生整页/整图上下文，但尚缺争议文字的精确定位证据；不得标作direct。"
            ),
        }

    pending = [
        finding_id
        for finding_id in WORKBUDDY_FUND_LINEAGE_FINDINGS
        if not finding_map[finding_id]["evidenceStatusV4"]["directEvidenceConfirmed"]
    ]
    report["verification"] = [
        row
        for row in report["verification"]
        if row.get("id") != "verification:v4:workbuddy-fund-descendant-exact-native"
    ]
    report["verification"].append(
        {
            "id": "verification:v4:workbuddy-fund-descendant-exact-native",
            "status": "pending" if pending else "verified",
            "nonScoring": False,
            "topic": "WorkBuddy募资属性传播链的本件精确定位证据",
            "pendingFindingIds": pending,
            "reason": (
                "每个finding均已有Excel上游锚点和本件原生上下文；只有精确原生截图或同原件结构化定位齐备后，"
                "evidenceStatusV4才可标记direct。"
            ),
            "requiredEvidence": "在对应Word/PPT/普通图/水墨图/HTML中取得含争议表述的精确原生画面，或经SHA校验的同原件结构化定位。",
        }
    )


def recompute_linear_scores(report: dict[str, Any], source: dict[str, Any]) -> None:
    definitions = definition_map(report)
    findings = {finding["id"]: finding for finding in report["findings"]}
    source_scores = source["scores"]["artifacts"]
    artifacts = {artifact["id"]: artifact for artifact in report["artifacts"]}

    for artifact_id, score in report["scores"]["artifacts"].items():
        score["legacyV3"] = {
            "baseScore": source_scores[artifact_id].get("baseScore"),
            "repairPenalty": source_scores[artifact_id].get("repairPenalty"),
            "appliedCap": source_scores[artifact_id].get("appliedCap"),
            "finalScore": source_scores[artifact_id].get("finalScore"),
        }
        total = 0.0
        for row in score["criterionScores"]:
            weight = float(definitions[row["criterionId"]]["weight"])
            if "subitemScores" in row:
                earned = sum(float(item["earnedPoints"]) for item in row["subitemScores"])
                maximum = sum(float(item["maxPoints"]) for item in row["subitemScores"])
                if abs(maximum - weight) > 1e-9:
                    raise ValueError(f"subitem maximum != criterion weight: {artifact_id}/{row['criterionId']}")
                row["rating0To5"] = rounded(earned / maximum * 5, 6)
                row["weighted"] = rounded(earned)
            else:
                row["weighted"] = rounded(float(row["rating0To5"]) / 5 * weight)
            total += float(row["weighted"])

        score["baseScore"] = rounded(total)
        score["qualityScore"] = rounded(total)
        score["scoreStatus"] = "final"
        score["scoreModel"] = "v4_linear_no_cap_no_fixed_adjustment"
        score["knownWeight"] = rounded(sum(float(definitions[row["criterionId"]]["weight"]) for row in score["criterionScores"]))
        score["verifiedWeight"] = rounded(
            sum(
                float(definitions[row["criterionId"]]["weight"])
                for row in score["criterionScores"]
                if row.get("status", "").startswith("verified_")
            )
        )
        score["weightedKnownSum"] = rounded(total)
        score["normalizedPartialScore"] = rounded(total / score["knownWeight"] * 100)

        kind = artifacts[artifact_id]["kind"]
        native_rows = [
            row
            for row in score["criterionScores"]
            if row["criterionId"].rsplit(":", 1)[-1] in NATIVE_INDEX_SUFFIXES[kind]
        ]
        native_denominator = sum(float(definitions[row["criterionId"]]["weight"]) for row in native_rows)
        native_numerator = sum(float(row["weighted"]) for row in native_rows)
        score["nativeUsabilityIndex"] = rounded(native_numerator / native_denominator * 100)
        score["nativeUsabilityIndexBasis"] = {
            "earnedPoints": rounded(native_numerator),
            "maximumPoints": rounded(native_denominator),
            "criterionIds": [row["criterionId"] for row in native_rows],
        }

        task_rows = [
            row for row in score["criterionScores"] if definitions[row["criterionId"]].get("tieBreaker") == "task_completion"
        ]
        task_denominator = sum(float(definitions[row["criterionId"]]["weight"]) for row in task_rows)
        task_numerator = sum(float(row["weighted"]) for row in task_rows)
        score["taskCompletionIndex"] = rounded(task_numerator / task_denominator * 100) if task_denominator else None
        score["taskCompletionIndexBasis"] = {
            "earnedPoints": rounded(task_numerator),
            "maximumPoints": rounded(task_denominator),
            "criterionIds": [row["criterionId"] for row in task_rows],
        }

    # Attribute each criterion deficit equally to the eligible findings which
    # the criterion itself cites. This makes causal restoration deterministic.
    for artifact_id, score in report["scores"]["artifacts"].items():
        for row in score["criterionScores"]:
            maximum = float(definitions[row["criterionId"]]["weight"])
            deficit = max(0.0, maximum - float(row["weighted"]))
            cited = [
                findings[finding_id]
                for finding_id in row.get("findingIds", [])
                if finding_id in findings and findings[finding_id].get("deducted", False)
            ]
            if not cited or deficit == 0:
                continue
            allocation = deficit / len(cited)
            for finding in cited:
                finding["scoreImpact"]["dimensionGapAttributionShare"] = rounded(
                    finding["scoreImpact"]["dimensionGapAttributionShare"] + allocation
                )

    # Preserve v3 adjustment attribution without double-counting an artifact
    # that requested the same cap through multiple findings.
    for artifact_id, score in report["scores"]["artifacts"].items():
        legacy = score["legacyV3"]
        artifact_findings = [finding for finding in report["findings"] if finding["artifactId"] == artifact_id]
        cap_findings = [
            finding for finding in artifact_findings if finding.get("legacyV3Adjustment", {}).get("capPolicyId")
        ]
        penalty_findings = [
            finding for finding in artifact_findings if finding.get("legacyV3Adjustment", {}).get("penaltyPolicyId")
        ]
        pre_cap = float(legacy["baseScore"] or 0) - float(legacy["repairPenalty"] or 0)
        cap_impact = max(0.0, pre_cap - float(legacy["finalScore"] or 0))
        for finding in cap_findings:
            finding["scoreImpact"]["v3CapImpact"] = rounded(cap_impact / len(cap_findings))
        for finding in penalty_findings:
            finding["scoreImpact"]["v3PenaltyImpact"] = rounded(
                float(legacy["repairPenalty"] or 0) / len(penalty_findings)
            )
        for finding in artifact_findings:
            finding["scoreImpact"]["v3CapOrPenaltyImpact"] = rounded(
                finding["scoreImpact"]["v3CapImpact"] + finding["scoreImpact"]["v3PenaltyImpact"]
            )

    for finding in report["findings"]:
        if finding["lineageRole"] == "exact_propagation" and finding.get("deducted", False):
            finding["scoreImpact"]["causalRestoration"] = finding["scoreImpact"]["dimensionGapAttributionShare"]
        finding["criterionDelta"]["points"] = rounded(-finding["scoreImpact"]["dimensionGapAttributionShare"])

    for artifact_id, score in report["scores"]["artifacts"].items():
        restoration_findings = [
            finding
            for finding in report["findings"]
            if finding["artifactId"] == artifact_id
            and finding["scoreImpact"]["causalRestoration"] > 0
        ]
        restored = sum(finding["scoreImpact"]["causalRestoration"] for finding in restoration_findings)
        score["causalRestoredPoints"] = rounded(restored)
        score["causalRestorationFindingIds"] = [finding["id"] for finding in restoration_findings]
        score["causalQualityScore"] = rounded(min(100.0, score["qualityScore"] + restored))
        score["v3ToV4"] = {
            "v3FinalScore": score["legacyV3"]["finalScore"],
            "v4QualityScore": score["qualityScore"],
            "delta": rounded(float(score["qualityScore"]) - float(score["legacyV3"]["finalScore"])),
            "reason": "维度及子项线性重算；取消数值封顶与固定调整。",
        }

    report["scores"]["artifacts"]["artifact:doubao:excel"]["v3ToV4"]["reason"] = (
        "+4.0来自把v3固定-8改为五项对称原生打开测试：干净打开0/4，但修复后保全、功能、编辑和保存重开6/6；"
        "这不是为维持或改变排名而作的工具特例。"
    )
    report["scores"]["artifacts"]["artifact:qianwen:excel"]["v3ToV4"]["reason"] = (
        "+0.8来自图表6分拆项：5/5图虽配置错误，但5/5确为可编辑原生对象，取得2/6而非v3的1.2/6。"
    )
    report["scores"]["artifacts"]["artifact:doubao:ppt"]["v3ToV4"]["reason"] = (
        "修复现象直接进入两项对称子测试：原生打开与放映3.5/10、图表编辑0/12；不使用固定罚分或39分封顶。"
    )
    report["scores"]["artifacts"]["artifact:qoder:ppt"]["v3ToV4"]["reason"] = (
        "保留Excel一致性3/5造成的10分线性损失，取消同一错误额外触发的59分数值封顶；G2继续阻止直接交付。"
    )

    report["scores"]["status"] = "final"
    report["scores"]["calculation"] = {
        "qualityScore": "sum(rating0To5 / 5 * criterionWeight); no cap and no fixed adjustment",
        "causalQualityScore": "legacy field name: qualityScore plus mechanically equal-allocated criterion gaps for exact propagation; noncausal diagnostic only",
        "deliveryGateAffectsScore": False,
        "rounding": "criterion weighted points and reported scores use two decimals",
    }


def assign_delivery_gates(report: dict[str, Any]) -> None:
    findings_by_artifact: dict[str, list[dict[str, Any]]] = {}
    for finding in report["findings"]:
        findings_by_artifact.setdefault(finding["artifactId"], []).append(finding)
    gate_rows: dict[str, dict[str, Any]] = {}
    for artifact in report["artifacts"]:
        requests = [
            finding
            for finding in findings_by_artifact.get(artifact["id"], [])
            if finding.get("deliveryGateRequest")
        ]
        if requests:
            highest_order = max(GATE_BY_CODE[finding["deliveryGateRequest"]]["order"] for finding in requests)
            highest = [finding for finding in requests if GATE_BY_CODE[finding["deliveryGateRequest"]]["order"] == highest_order]
            code = "G2-Mac" if any(finding["deliveryGateRequest"] == "G2-Mac" for finding in highest) else highest[0]["deliveryGateRequest"]
        else:
            code = "G0"
            highest = []
        reasons: list[str] = []
        for finding in highest:
            reason = GATE_REASON_OVERRIDES.get(finding["id"], finding.get("terminalRiskReason", ""))
            if reason and reason not in reasons:
                reasons.append(reason)
        row = {
            "artifactId": artifact["id"],
            "code": code,
            "label": GATE_BY_CODE[code]["label"],
            "directUse": GATE_BY_CODE[code]["directUse"],
            "findingIds": [finding["id"] for finding in highest],
            "reason": ARTIFACT_GATE_REASON_OVERRIDES.get(artifact["id"], "；".join(reasons)),
            "platformScope": "macOS_26.5.2_Office_16.112.3_only" if code == "G2-Mac" else "content_or_general",
            "scoreEffect": 0,
        }
        gate_rows[artifact["id"]] = row
        report["scores"]["artifacts"][artifact["id"]]["deliveryGateCode"] = code

    tool_rows = {}
    for tool in report["meta"]["tools"]:
        rows = [gate_rows[artifact["id"]] for artifact in report["artifacts"] if artifact["tool"] == tool]
        tool_rows[tool] = {
            "counts": {code: sum(row["code"] == code for row in rows) for code in GATE_BY_CODE},
            "blockedArtifactIds": [row["artifactId"] for row in rows if not row["directUse"]],
        }
    report["deliveryGates"] = {
        "definitions": GATE_DEFINITIONS,
        "scoreIndependent": True,
        "artifacts": gate_rows,
        "tools": tool_rows,
    }


def tie_indexes(report: dict[str, Any], tool: str, mode: str) -> tuple[float, float, float]:
    artifacts = [artifact for artifact in report["artifacts"] if artifact["tool"] == tool]
    rows = [report["scores"]["artifacts"][artifact["id"]] for artifact in artifacts]
    native = sum(float(row.get("nativeUsabilityIndex") or 0) for row in rows) / len(rows)
    task = sum(float(row.get("taskCompletionIndex") or 0) for row in rows) / len(rows)
    excel_artifact = next(artifact for artifact in artifacts if artifact["kind"] == "excel")
    fact_row = criterion(report, excel_artifact["id"], "external-facts")
    fact = float(fact_row["rating0To5"]) / 5 * 100
    return rounded(native), rounded(fact), rounded(task)


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows.sort(
        key=lambda row: (
            -float(row["score"]),
            -float(row["nativeUsabilityIndex"]),
            -float(row["excelFactIndex"]),
            -float(row["taskCompletionIndex"]),
            row["tool"],
        )
    )
    prior = None
    prior_rank = 0
    for position, row in enumerate(rows, 1):
        key = (
            row["score"],
            row["nativeUsabilityIndex"],
            row["excelFactIndex"],
            row["taskCompletionIndex"],
        )
        if key != prior:
            prior_rank = position
            prior = key
        row["rank"] = prior_rank
    # Join adjacent rows whose continuous scores differ by at most one point.
    # This is a descriptive sensitivity grouping, not an equivalence relation,
    # confidence interval or statistical test.  In particular, a connected
    # group may span slightly more than one point from first to last.
    band_index = 0
    previous_score = None
    for row in rows:
        current_score = float(row["score"])
        if previous_score is None or current_score < previous_score - 1.0:
            band_index += 1
        row["performanceBand"] = chr(64 + band_index)
        row["displayRank"] = f"{row['performanceBand']}档"
        row["ordinalClaim"] = False
        row["bandRule"] = "与上一行连续分差不超过1.0分则归入同一敏感组；该组不代表统计等价"
        previous_score = current_score
    return rows


def build_ranking(
    report: dict[str, Any], *, ranking_id: str, label: str, score_field: str, weights: dict[str, float], is_official: bool
) -> dict[str, Any]:
    artifacts = {(artifact["tool"], artifact["kind"]): artifact for artifact in report["artifacts"]}
    rows = []
    for tool in report["meta"]["tools"]:
        kind_scores = {
            kind: float(report["scores"]["artifacts"][artifacts[(tool, kind)]["id"]][score_field])
            for kind in report["meta"]["kinds"]
        }
        native, fact, task = tie_indexes(report, tool, score_field)
        rows.append(
            {
                "tool": tool,
                "score": rounded(sum(kind_scores[kind] * float(weights[kind]) for kind in kind_scores)),
                "artifactScores": {kind: rounded(value) for kind, value in kind_scores.items()},
                "nativeUsabilityIndex": native,
                "excelFactIndex": fact,
                "taskCompletionIndex": task,
                "blockedArtifactCount": report["deliveryGates"]["tools"][tool]["counts"]["G2"]
                + report["deliveryGates"]["tools"][tool]["counts"]["G2-Mac"],
                "nonDirectUseArtifactCount": len(report["deliveryGates"]["tools"][tool]["blockedArtifactIds"]),
            }
        )
    return {
        "id": ranking_id,
        "label": label,
        "status": "final" if is_official else "diagnostic_noncausal",
        "isOfficial": is_official,
        "ordinalRankingPublished": False,
        "comparisonBandPoints": 1.0,
        "scoreField": score_field,
        "weights": weights,
        "deliveryGatesAffectRank": False,
        "rows": rank_rows(rows),
    }


def rebuild_rankings(report: dict[str, Any]) -> None:
    model_by_id = {model["id"]: model for model in report["methodology"]["rankingModels"]}
    equal = model_by_id["equalTask"]["weights"]
    practical = model_by_id["practical"]["weights"]
    configurations = [
        ("independent_equalTask", "正式比较·六任务等权", "qualityScore", equal, True),
        ("independent_practical", "正式比较·均衡投研实务", "qualityScore", practical, True),
        ("rootCause_equalTask", "机械缺口恢复诊断·六任务等权（非因果）", "causalQualityScore", equal, False),
        ("rootCause_practical", "机械缺口恢复诊断·均衡投研实务（非因果）", "causalQualityScore", practical, False),
    ]
    report["rankings"] = {
        ranking_id: build_ranking(
            report,
            ranking_id=ranking_id,
            label=label,
            score_field=score_field,
            weights=weights,
            is_official=is_official,
        )
        for ranking_id, label, score_field, weights, is_official in configurations
    }


def scenario_ranking(
    report: dict[str, Any], score_overrides: dict[str, float], weights: dict[str, float]
) -> list[dict[str, Any]]:
    rows = []
    for tool in report["meta"]["tools"]:
        artifacts = [artifact for artifact in report["artifacts"] if artifact["tool"] == tool]
        score = 0.0
        for artifact in artifacts:
            value = score_overrides.get(
                artifact["id"], report["scores"]["artifacts"][artifact["id"]]["qualityScore"]
            )
            score += float(value) * float(weights[artifact["kind"]])
        rows.append({"tool": tool, "score": rounded(score)})
    rows.sort(key=lambda row: (-row["score"], row["tool"]))
    for position, row in enumerate(rows, 1):
        row["rank"] = position
    return rows


def build_sensitivity(report: dict[str, Any], source: dict[str, Any]) -> None:
    models = {model["id"]: model["weights"] for model in report["methodology"]["rankingModels"]}
    interaction_sweep = []
    for interaction_weight in [0, 5, 10, 15, 20, 25]:
        overrides = {}
        for artifact in report["artifacts"]:
            if artifact["kind"] != "html":
                continue
            rows = report["scores"]["artifacts"][artifact["id"]]["criterionScores"]
            interaction = next(row for row in rows if row["criterionId"].endswith("effective-interaction"))
            other = sum(float(row["weighted"]) for row in rows if row is not interaction)
            value = other * (100 - interaction_weight) / 85 + float(interaction["rating0To5"]) / 5 * interaction_weight
            overrides[artifact["id"]] = rounded(value)
        interaction_sweep.append(
            {
                "interactionWeight": interaction_weight,
                "redistribution": "其余HTML维度按原权重同比例归一",
                "equalTask": scenario_ranking(report, overrides, models["equalTask"]),
                "practical": scenario_ranking(report, overrides, models["practical"]),
            }
        )

    qianwen_full_chart = report["scores"]["artifacts"]["artifact:qianwen:excel"]["qualityScore"] + 4
    qianwen_overrides = {"artifact:qianwen:excel": rounded(qianwen_full_chart)}
    same_base_legacy_caps = {}
    for artifact in report["artifacts"]:
        old = source["scores"]["artifacts"][artifact["id"]]
        v4_score = float(report["scores"]["artifacts"][artifact["id"]]["qualityScore"])
        legacy_cap = old.get("appliedCap")
        same_base_legacy_caps[artifact["id"]] = min(v4_score, float(legacy_cap)) if legacy_cap is not None else v4_score

    report["sensitivity"] = {
        "htmlInteractionWeightSweep": {
            "range": "0—25分",
            "primaryWeight": 15,
            "theoreticalOverallImpactPoints": {"equalTask": 2.5, "practical": 2.25},
            "result": "实务榜在0—25分全区间次序不变；等权榜在0或5分时豆包第一，10—25分时ZhikunCode第一，说明榜首接近且需同时披露权重敏感性。",
            "cases": interaction_sweep,
        },
        "qianwenExcelChart": {
            "primaryExcelScore": report["scores"]["artifacts"]["artifact:qianwen:excel"]["qualityScore"],
            "counterfactualAllFiveChartsCorrect": rounded(qianwen_full_chart),
            "delta": 4.0,
            "equalTask": scenario_ranking(report, qianwen_overrides, models["equalTask"]),
            "practical": scenario_ranking(report, qianwen_overrides, models["practical"]),
        },
        "legacyCapToggle": {
            "description": "在完全相同的v4线性基分上，仅切换v3数值上限；不混入v3固定罚分或旧维度评级。",
            "sameV4BaseWithLegacyCaps": {
                "equalTask": scenario_ranking(report, same_base_legacy_caps, models["equalTask"]),
                "practical": scenario_ranking(report, same_base_legacy_caps, models["practical"]),
            },
            "sameV4BaseWithoutCaps": {
                "equalTask": report["rankings"]["independent_equalTask"]["rows"],
                "practical": report["rankings"]["independent_practical"]["rows"],
            },
            "qoderPpt": {
                "v3": source["scores"]["artifacts"]["artifact:qoder:ppt"]["finalScore"],
                "v4": report["scores"]["artifacts"]["artifact:qoder:ppt"]["qualityScore"],
                "gate": report["deliveryGates"]["artifacts"]["artifact:qoder:ppt"]["code"],
            },
        },
        "v3HistoricalPublishedResults": {
            "description": "这是冻结v3账本曾发布的历史结果，不与上述同基分开关混算。",
            "equalTask": deepcopy(source["rankings"]["equalTask"]["rows"]),
            "practical": deepcopy(source["rankings"]["practical"]["rows"]),
            "sourceInputJsonSha256": report["meta"]["buildProvenance"]["sourceSha256"],
        },
        "mechanicalPropagationDiagnostic": {
            "description": "旧字段causalQualityScore仅按维度缺口等额恢复完全继承项，是非因果敏感性诊断；不作为正式名次。",
            "independentEqual": report["rankings"]["independent_equalTask"]["rows"],
            "causalEqual": report["rankings"]["rootCause_equalTask"]["rows"],
            "independentPractical": report["rankings"]["independent_practical"]["rows"],
            "causalPractical": report["rankings"]["rootCause_practical"]["rows"],
        },
        "doubaoPptPlatform": {
            "observedMacScore": report["scores"]["artifacts"]["artifact:doubao:ppt"]["qualityScore"],
            "gate": "G2-Mac",
            "windowsResult": "pending_user_or_vendor_cross_test",
            "counterfactualPolicy": "Windows若字节一致副本干净打开并完整保留16页、7图和7工作簿，才可按同一子项规则重算；不得预设结果。",
        },
    }


def update_methodology(report: dict[str, Any], input_hash: str) -> None:
    methodology = report["methodology"]
    methodology["scoreScale"]["formula"] = "rating / 5 * weight; no numerical cap; no fixed adjustment"
    methodology["v4Principles"] = {
        "linearQuality": "所有主分只来自维度和子项线性加总，不使用59/69/39等数值封顶。",
        "deliveryGate": "重大错误决定能否直接交付，但不改变质量分。",
        "twoPerspectives": "独立终稿分用于正式比较；传播链回答问题从哪里产生和传播，不发布所谓因果分名次。",
        "platformAttribution": "单一Mac环境观察仅标G2-Mac；在字节一致副本完成Windows交叉试验前不得外推。",
        "toolNeutrality": "相同证据、范围、传播角色和原生结果适用相同规则，不按工具身份调整。",
    }
    methodology["deliveryGateDefinitions"] = GATE_DEFINITIONS
    methodology["mechanicalPropagationDiagnostic"] = {
        "status": "noncausal_sensitivity_only",
        "eligibleRole": "exact_propagation",
        "restorationFormula": (
            "恢复该finding在其本件criterion deficit中的等额归因；"
            "origin、mutated、independently_reintroduced均不恢复。"
        ),
        "criterionAllocation": "同一criterion引用多个有效finding时机械均分该criterion相对满分的缺口；不代表因果贡献。",
        "individualRiskPreserved": True,
        "officialRankingUse": False,
    }
    methodology.pop("causalDeduplication", None)
    methodology["gateRules"] = deepcopy(GATE_RULES)
    methodology["rankingViews"] = [
        "independent_equalTask",
        "independent_practical",
        "rootCause_equalTask",
        "rootCause_practical",
    ]
    methodology["weightModels"] = deepcopy(methodology["rankingModels"])
    methodology["supersededAdjustments"] = deepcopy(methodology.get("adjustmentPolicies", []))
    methodology["adjustmentPolicies"] = []
    methodology["symmetricNativeSubtests"] = {
        "excelOpen": "五款均使用4+2+2+1+1分：干净打开、结构保全、功能保全、编辑、保存重开。",
        "pptOpen": "五款均使用3+2+3+2分：干净打开、无需/无损修复、完整放映、保存重开。",
        "pptCharts": "五款均使用3+5+2+2分：对象保留、编辑数据、联动、保存重开。",
        "note": "无修复的文件取得对应通过分；出现修复的文件按同一观察项实得分，不作工具身份调整。",
    }
    methodology["v3ToV4MaterialChanges"] = [
        "豆包Excel 77.6→81.6：取消固定-8，改按对称原生打开子测试计6/10。",
        "千问Excel 88.8→89.6：图表维度显式承认可编辑对象2/6，同时保留配置错误。",
        "豆包PPT 39→76.5：Mac修复损失进入两个原生子测试，另标G2-Mac，不再固定罚分或封顶。",
        "Qoder PPT 59→82.2：保留线性一致性扣分并标G2，取消59分封顶。",
        "WorkBuddy来源问题改为底稿可追溯性缺陷，不再以单次零结果证明来源不存在；传播恢复值仅作非因果诊断。",
        "ZhikunCode下游完全继承已披露、可单独删除的8月31日估值模块：与Excel一致标G1，不因传播自动升级为G2。",
    ]
    report["versionHistory"] = [
        {
            "version": "3.1",
            "status": "superseded_scoring_preserved_as_source",
            "inputJsonSha256": input_hash,
            "archivedHtmlSha256": "03c432022efe3352421894e2ffbe53488e09696793be398d67fa857187348636",
            "hashClarification": "inputJsonSha256是v4构建所用数据账本；archivedHtmlSha256是用户可见v3主报告归档，两者不是同一文件。",
            "summary": "原生核验证据、事实账本、覆盖记录和v3封顶评分。",
        },
        {
            "version": "4.1",
            "status": "qa_pending_evidence_merge",
            "builderVersion": SCRIPT_VERSION,
            "summary": "正式排名仅保留独立终稿两种权重并使用1分同档带；根因恢复降级为非因果诊断，新增机械Word检索分、逐标签图片清单与32项事实覆盖边界；更正ZhikunCode下游完全继承项从G2自动升级为G1一致闸门。",
            "reproducibility": "同一v3输入和本脚本产生字节稳定的JSON。",
        },
    ]

    for profile in report["meta"].get("toolProfiles", {}).values():
        for field in ["summary", "strength", "friction", "critical"]:
            value = profile.get(field)
            if value and not value.startswith("本次固定样本中"):
                profile[field] = f"本次固定样本中，{value}"
        recommendation = profile.pop("bestFit", "")
        if recommendation:
            profile["sampleUseRecommendation"] = f"本样本使用建议：{recommendation}"
    zhikun = report["meta"].get("toolProfiles", {}).get("ZhikunCode", {})
    zhikun["summary"] = zhikun.get("summary", "").replace(
        "按统一重大性阈值定为主要问题而非封顶项", "按统一重大性阈值判为主要期间问题"
    )
    zhikun["critical"] = zhikun.get("critical", "").replace(
        "取消59分封顶不等于认定合规：", "该问题没有消失："
    )
    report["meta"]["limitations"] = [
        "尚未向千问、豆包办公、Qoder、WorkBuddy或ZhikunCode征求厂商回应或反证。",
        "仅覆盖宇树科技主题的一次连续六任务链和30件固定终稿，不能外推为产品总体能力或稳定生成率。",
        "用户确认五款均使用各产品当时可用的最强档配置；这仍不是同一模型、同一算力、同一成本或同一工具权限的严格控制实验。",
        "ZhikunCode本轮新增的是配置截图；未提供完整过程分享链接或额度明细，因此对应字段明确记为未提供，不作推断。",
        "原生应用体验固定在macOS 26.5.2、Office 16.112.3及Chrome 152环境。",
        "尚未完成Windows版Office交叉验证。",
        "尚未从各产品重新下载同一任务产物进行字节或可打开性复核。",
    ]
    report["meta"]["status"] = "qa_pending"
    report["meta"]["statusNote"] = "未征求厂商正式回应；Windows PowerPoint与独立重新下载未验证。"

    # Replace the v3 score-engine verification claim in the active interface.
    # The historical wording remains recoverable from the immutable v3 input
    # identified by buildProvenance and from the archived legacy namespace.
    verification = next(
        (row for row in report.get("verification", []) if row.get("id") == "verification:ranking-recompute"),
        None,
    )
    if verification is not None:
        verification.update(
            {
                "item": "四个排名视角、线性质量分、交付闸门与权重可重算",
                "status": "automated_v4_qa_passed_data_only",
                "reason": "build_report_v4.py与qa_v4.py基于同一输入完成确定性重建和逐项断言；证据合并前整体仍为qa_pending。",
                "owner": "v4_data_engine",
            }
        )


def migrate_legacy_namespace(
    report: dict[str, Any],
    source: dict[str, Any],
    propagation_score_modes: dict[str, str],
    supplement_context: dict[str, Any] | None,
) -> None:
    """Remove v3 scoring controls from active interfaces and archive them."""

    methodology = report["methodology"]
    legacy_methodology = {}
    for key in [
        "adjustmentPolicies",
        "supersededAdjustments",
        "materialityThreshold",
        "sensitivityAnalysis",
        "scoreStatus",
        "repairPolicy",
        "causalRules",
        "rankingModels",
        "v3ToV4MaterialChanges",
    ]:
        if key in methodology:
            legacy_methodology[key] = methodology.pop(key)

    artifact_scores = {}
    artifact_transitions = {}
    for artifact_id, score in report["scores"]["artifacts"].items():
        artifact_scores[artifact_id] = score.pop("legacyV3")
        artifact_transitions[artifact_id] = score.pop("v3ToV4")
        for key in [
            "repairPenalty",
            "appliedPenalties",
            "requestedCaps",
            "appliedCap",
            "provisionalScore",
            "finalScore",
        ]:
            score.pop(key, None)

    artifact_baselines = {}
    for artifact in report["artifacts"]:
        if "legacyBaseline" in artifact:
            artifact_baselines[artifact["id"]] = artifact.pop("legacyBaseline")

    finding_adjustments = {}
    finding_legacy = {}
    finding_cap_decisions = {}
    finding_legacy_score_impacts = {}
    for finding in report["findings"]:
        if "legacyV3Adjustment" in finding:
            finding_adjustments[finding["id"]] = finding.pop("legacyV3Adjustment")
        if "legacy" in finding:
            finding_legacy[finding["id"]] = finding.pop("legacy")
        if "capDecision" in finding:
            finding_cap_decisions[finding["id"]] = finding.pop("capDecision")
        finding.pop("capPolicyId", None)
        finding.pop("penaltyPolicyId", None)
        finding_legacy_score_impacts[finding["id"]] = {
            key: finding["scoreImpact"].pop(key)
            for key in ["v3CapImpact", "v3PenaltyImpact", "v3CapOrPenaltyImpact"]
        }
        for text_key in ["summary", "observation", "interpretation"]:
            if isinstance(finding.get(text_key), str):
                finding[text_key] = (
                    finding[text_key]
                    .replace("、不触发cap", "")
                    .replace("且不得触发cap", "")
                    .replace("，取消下游事实扣分", "")
                    .replace("，撤销该项下游事实扣分和cap", "")
                    .replace("、不触发封顶", "")
                    .replace("且不触发封顶", "")
                )

    report["legacyV3"] = {
        "namespaceStatus": "historical_not_active_scoring",
        "inputJsonSha256": report["meta"]["buildProvenance"]["sourceSha256"],
        "scoreEngineCalculation": deepcopy(source["scores"].get("calculation", {})),
        "methodology": legacy_methodology,
        "publishedRankings": deepcopy(source["rankings"]),
        "artifactScores": artifact_scores,
        "artifactTransitions": artifact_transitions,
        "artifactBaselines": artifact_baselines,
        "findingAdjustments": finding_adjustments,
        "findingLegacy": finding_legacy,
        "findingCapDecisions": finding_cap_decisions,
        "findingScoreAdjustments": finding_legacy_score_impacts,
        "propagationScoreModes": propagation_score_modes,
        "supplementPropagationScoreModeReview": (
            deepcopy(supplement_context["legacyPropagationScoreModeReview"])
            if supplement_context is not None
            else None
        ),
    }
    report["scores"]["status"] = "qa_pending"
    for ranking in report["rankings"].values():
        ranking["status"] = "qa_pending"


def publish_v4_interfaces(report: dict[str, Any]) -> None:
    """Expose concise, versioned top-level interfaces for the v4 report UI."""

    subtest_artifacts: dict[str, dict[str, Any]] = {}
    for artifact in report["artifacts"]:
        rows = {}
        for row in report["scores"]["artifacts"][artifact["id"]]["criterionScores"]:
            if row.get("subitemScores"):
                rows[row["criterionId"]] = {
                    "weightedPoints": row["weighted"],
                    "subitems": deepcopy(row["subitemScores"]),
                    "evidenceIds": deepcopy(row.get("evidenceIds", [])),
                }
        if rows:
            subtest_artifacts[artifact["id"]] = rows
    report["rubricSubtests"] = {
        "version": SCRIPT_VERSION,
        "principle": "相同产物类型使用相同子测试、分值上限和证据要求。",
        "artifacts": subtest_artifacts,
    }

    artifact_meta = {artifact["id"]: artifact for artifact in report["artifacts"]}
    report["qualityScores"] = {
        "version": SCRIPT_VERSION,
        "status": "qa_pending",
        "primaryField": "qualityScore",
        "capsApplied": False,
        "fixedAdjustmentsApplied": False,
        "artifacts": {
            artifact_id: {
                "artifactId": artifact_id,
                "tool": artifact_meta[artifact_id]["tool"],
                "kind": artifact_meta[artifact_id]["kind"],
                "qualityScore": score["qualityScore"],
                "causalQualityScore": score["causalQualityScore"],
                "causalRestoredPoints": score["causalRestoredPoints"],
                "mechanicalPropagationDiagnosticScore": score["causalQualityScore"],
                "mechanicalRestoredPoints": score["causalRestoredPoints"],
                "deliveryGateCode": score["deliveryGateCode"],
            }
            for artifact_id, score in report["scores"]["artifacts"].items()
        },
    }
    report["rankingPerspectives"] = {
        "status": "qa_pending",
        "definitions": {
            "independent": "每件终稿按其独立使用结果计分；同一错误出现在多件文件时，各文件仍显示其质量影响。",
            "rootCause": "非正式、非因果诊断：机械恢复exact_propagation被分摊到的维度缺口；仅用于观察传播口径敏感性。",
            "equalTask": "六类任务各占1/6。",
            "practical": "Excel 25%、Word 20%、PPT 20%、普通图10%、水墨图10%、HTML 15%。",
        },
        "results": deepcopy(report["rankings"]),
        "officialResultIds": ["independent_equalTask", "independent_practical"],
        "diagnosticResultIds": ["rootCause_equalTask", "rootCause_practical"],
        "comparisonBandPoints": 1.0,
        "ordinalClaim": False,
    }

    application = {
        "excel": "Microsoft Excel 16.112.3",
        "word": "Microsoft Word 16.112.3",
        "ppt": "Microsoft PowerPoint 16.112.3",
        "image": "macOS Preview",
        "ink": "macOS Preview",
        "html": "Google Chrome 152.0.7977.77",
    }
    rows = []
    for artifact in report["artifacts"]:
        if artifact["id"] == "artifact:doubao:ppt":
            observation = "repair_required_then_8_of_16_slides_and_7_charts_lost"
        elif artifact["id"] == "artifact:doubao:excel":
            observation = "repair_required_then_content_and_functions_preserved"
        else:
            observation = "native_runtime_review_completed"
        rows.append(
            {
                "artifactId": artifact["id"],
                "tool": artifact["tool"],
                "kind": artifact["kind"],
                "testedApplication": application[artifact["kind"]],
                "testedEnvironment": "macOS 26.5.2 arm64",
                "observation": observation,
                "gate": report["deliveryGates"]["artifacts"][artifact["id"]]["code"],
                "crossPlatformStatus": "not_tested_outside_fixed_environment",
            }
        )
    report["compatibilityMatrix"] = {
        "scope": "固定Mac环境的真实体验；不把单环境故障外推为全平台结论。",
        "windowsCrossTest": "pending",
        "rows": rows,
    }


def merge_supplement_interfaces(
    report: dict[str, Any], supplement_context: dict[str, Any] | None
) -> None:
    if supplement_context is None:
        report["evidenceSupplement"] = {
            "status": "not_loaded",
            "note": "未加载可选native-audit-v4证据补充包；不影响线性评分重算。",
        }
        return

    evidence_ids = {evidence["id"] for evidence in report["evidence"]}
    verified_checks = deepcopy(supplement_context["compatibilityMatrixRows"])
    pending_checks = deepcopy(supplement_context["compatibilityUnverifiedRows"])
    for row in verified_checks + pending_checks:
        if not set(row.get("evidenceIds", [])) <= evidence_ids:
            raise ValueError(f"compatibility check has unknown evidence: {row['rowId']}")
        row["artifactId"] = "artifact:doubao:ppt"
        row["sourceSupplement"] = supplement_context["path"]

    report["rubricSubtests"]["supplement"] = {
        "status": "loaded_read_only",
        "path": supplement_context["path"],
        "sha256": supplement_context["sha256"],
        "schema": supplement_context["schema"],
    }
    report["rubricSubtests"]["scenarioRecords"] = deepcopy(
        supplement_context["rubricSubtests"]
    )
    report["compatibilityMatrix"]["verifiedChecks"] = verified_checks
    report["compatibilityMatrix"]["pendingChecks"] = pending_checks
    doubao_row = next(
        row
        for row in report["compatibilityMatrix"]["rows"]
        if row["artifactId"] == "artifact:doubao:ppt"
    )
    doubao_row["verifiedCheckIds"] = [row["rowId"] for row in verified_checks]
    doubao_row["pendingCheckIds"] = [row["rowId"] for row in pending_checks]

    pending_direct = [
        finding["id"]
        for finding in report["findings"]
        if finding["id"] in WORKBUDDY_FUND_LINEAGE_FINDINGS
        and not finding["evidenceStatusV4"]["directEvidenceConfirmed"]
    ]
    report["evidenceSupplement"] = {
        "status": "qa_pending_exact_screenshots" if pending_direct else "merged",
        "path": supplement_context["path"],
        "sha256": supplement_context["sha256"],
        "schema": supplement_context["schema"],
        "catalogIds": supplement_context["catalogIds"],
        "findingEvidenceLinks": deepcopy(supplement_context["findingEvidenceLinks"]),
        "rubricSubtestIds": [
            row["subtestId"] for row in supplement_context["rubricSubtests"]
        ],
        "compatibilityVerifiedCheckIds": [row["rowId"] for row in verified_checks],
        "compatibilityPendingCheckIds": [row["rowId"] for row in pending_checks],
        "pendingExactNativeFindingIds": pending_direct,
        "scoreEffect": "none; evidence merge only",
    }
    report["meta"]["status"] = "qa_pending"
    report["meta"]["statusNote"] = "未征求厂商正式回应；Windows PowerPoint与独立重新下载未验证。"


def enrich_v41_interfaces(report: dict[str, Any]) -> None:
    """Publish the claim-coverage boundary and Qoder checklist evidence."""

    fact_count = len(report.get("facts", []))
    fact_ids = [fact.get("id") for fact in report.get("facts", [])]
    sourced = sum(bool(fact.get("sourceId")) for fact in report.get("facts", []))
    report["factAuditUniverse"] = {
        "version": "4.1",
        "benchmarkFactCount": fact_count,
        "factsWithSourceLocator": sourced,
        "benchmarkLedgerCoverageRate": rounded(sourced / fact_count * 100) if fact_count else None,
        "selectionTiming": "核验基准由正式披露与原Prompt必需主题定义，评分时不按工具增删。",
        "selectionRules": [
            "纳入会实质影响收入、利润、现金流、研发、产品结构、IPO/上市与募资判断的核心数字或属性。",
            "纳入能以截止日前一级官方资料确定报告期、单位及事实/计划/预测属性的项目。",
            "年度与半年度分开；金额统一为万元，展示换算另行标注。",
        ],
        "exclusions": [
            "未穷举每份工作簿中的所有附带数字、文字数字和第三方市场份额；这些不得据此宣称已全量核验。",
            "未纳入无法用指定一级来源统一口径的偶发、非核心或纯展示性数字。",
        ],
        "claimUniverseStatus": "not_enumerated",
        "toolLevelWholeWorkbookNumericCoverage": {tool: "未测量，禁止表述为全量数字准确" for tool in report["meta"]["tools"]},
        "factIds": fact_ids,
        "publicationClaim": "本报告核对32项核心基准事实；不等同于对五本Excel全部数字的逐项全量鉴证。",
    }

    checklist_log = json.loads(QODER_IMAGE_CHECKLIST_LOG.read_text(encoding="utf-8"))
    label_records = []
    simulation_lookup = {}
    artifact_ids = {"ordinary": "artifact:qoder:image", "ink": "artifact:qoder:ink"}
    finding_ids = {"ordinary": "Qoder-image-02", "ink": "Qoder-ink-02"}
    evidence_ids = {
        "ordinary": ["EV-QI-ORD-100", "EV-QI-ORD-1920", "EV-QI-ORD-A4"],
        "ink": ["EV-QI-INK-100", "EV-QI-INK-1920", "EV-QI-INK-A4"],
    }
    for artifact in checklist_log["artifacts"]:
        kind = artifact["kind"]
        for zone in artifact["checklist"]:
            label_records.append(
                {
                    "subtestId": f"QI-{kind.upper()}-{zone['zoneId']}",
                    "artifactId": artifact_ids[kind],
                    "findingId": finding_ids[kind],
                    "zoneId": zone["zoneId"],
                    "label": zone["label"],
                    "bboxPx": zone["bboxPx"],
                    "expected": "区域内容存在、可读、未被裁切且无叠印。",
                    "actual": zone["status"],
                    "status": zone["status"],
                    "evidenceIds": evidence_ids[kind],
                }
            )
        for simulation in artifact["simulations"]:
            simulation_lookup[(kind, simulation["scenario"])] = simulation
    report["rubricSubtests"]["labelChecklistRecords"] = label_records
    report["rubricSubtests"]["qoderImageChecklist"] = {
        "path": str(QODER_IMAGE_CHECKLIST_LOG.resolve()),
        "sha256": sha256(QODER_IMAGE_CHECKLIST_LOG),
        "expectedFieldPolicy": "每个预设标签区都必须存在、可读、未裁切且无叠印。",
        "recordCount": len(label_records),
    }
    for row in report["rubricSubtests"].get("scenarioRecords", []):
        sid = row.get("subtestId", "")
        if sid.startswith("QI-ORD-S"):
            kind = "ordinary"
        elif sid.startswith("QI-INK-S"):
            kind = "ink"
        else:
            continue
        scenario_name = row.get("scenario") or row.get("test") or row.get("name")
        simulation = simulation_lookup.get((kind, scenario_name))
        if simulation is None:
            # Preserve deterministic order used by the three supplement rows.
            index = int(sid.rsplit("S", 1)[-1]) - 1
            simulation = checklist_log["artifacts"][0 if kind == "ordinary" else 1]["simulations"][index]
        row["expected"] = "在该使用尺度下，标题、轴标签、核心数字与来源区均可读且无裁切或叠印。"
        row["actual"] = simulation["observation"]
        row["resultStatus"] = simulation["status"]

    report["methodology"]["gateRules"] = deepcopy(GATE_RULES)
    report["methodology"]["raterModel"] = {
        "raters": 1,
        "interRaterReliability": "not_measured",
        "subjectiveCriterionPolicy": "凡无机械子测试者使用公开0—5锚点并链接证据；不把小数差解释为稳定或可外推的差异。",
        "comparisonBandPoints": 1.0,
        "bandMeaning": "按排序后相邻分差≤1.0组成描述性敏感组；组内不主张确定性先后。该分组可能经相邻连接而首尾差略超1分，不是置信区间、统计检验或等价性结论。",
    }
    report["methodology"]["workBuddyAdjudicationBoundary"] = {
        "sourceClaim": (
            "仅评价固定工作簿内A级标签与可追溯材料的匹配度；"
            "不判定两份报告绝对不存在，不判定来源真伪，不推断生成意图。"
        ),
        "sourceScoreBasis": "原Prompt明示要求‘保留资料来源’，因此只在Excel来源可追溯性维度计入3.2分缺口。",
        "processRecord": (
            "2026-09-06复测时Chrome 152已读取WorkBuddy分享页正文，"
            "六个原始Prompt特征句均命中；过程记录本身不参与评分。"
        ),
        "responseStatus": "未征求WorkBuddy厂商正式回应；报告提供反证条件与新版终稿复测通道。",
    }
    legacy_workbuddy = (
        report.get("legacyV3", {})
        .get("findingCapDecisions", {})
        .get("WORKBUDDY-001")
    )
    if isinstance(legacy_workbuddy, dict):
        legacy_workbuddy["v41Status"] = "superseded_historical_rule_not_active"
        legacy_workbuddy["v41Correction"] = (
            "v3的‘虚构/不存在权威来源’触发标签证据过度，已在v4.1撤销；"
            "当前只保留固定工作簿内可追溯颗粒度不足的评价。"
        )


def enrich_v42_presentation(report: dict[str, Any]) -> None:
    """Add presentation-only metadata without changing adjudication results."""

    title = "五款AI办公工具固定样本交付物比较评测与证据复核报告——宇树科技六任务，截至2026年8月30日"
    report["meta"].update(
        {
            "schemaVersion": "4.2.0",
            "presentationVersion": "4.2",
            "title": title,
            "subtitle": "固定样本、固定环境的交付物比较；分数与闸门沿用v4.1证据账本，本版仅重构信息架构、视觉呈现与打印输出。",
            "version": "报告版本 4.2 · 固定样本证据复核",
        }
    )
    report["meta"]["buildProvenance"]["builderVersion"] = SCRIPT_VERSION
    report["meta"]["limitations"] = [
        "尚未向千问办公、豆包办公、Qoder、WorkBuddy或ZhikunCode征求厂商正式回应或反证。",
        "仅覆盖宇树科技主题的一次连续六任务链和30件固定终稿，不能外推为产品总体能力、稳定生成率或其他任务表现。",
        "用户确认五款均使用各产品当时可用的最强档配置；仍不是同一模型、同一算力、同一成本或同一工具权限的严格控制实验。",
        "原生应用体验固定在macOS 26.5.2、Office 16.112.3及Chrome 152环境；尚未完成Windows版Office交叉验证或独立重新下载复核。",
        "全过程记录与配置、额度或费用截图由用户补充，只用于说明样本上下文，不参与评分。WorkBuddy分享页正文的自动抽取边界按过程记录原文披露。",
        "ZhikunCode为开源方案，没有本次样本对应的独立商业计费页；Kimi API日账单混有当天其他任务，只能作为账户级旁证，不能归因于本次六任务。",
        "本报告由单一评审者完成；敏感组只提示名次对权重与判断变化较敏感，不代表置信区间或评审者间一致性结果。",
    ]

    expert_tokens = {
        "analysis-decision-value", "one-point-narrative", "visual-hierarchy",
        "information-selection", "hierarchy-composition", "investor-visual",
        "ink-romantic-style", "professional-composition", "output-finish",
        "information-architecture", "visual-performance", "conclusions-verification",
    }
    assessment_counts = {"mechanical": 0, "expert_judgment": 0}
    assessment_weights = {"mechanical": 0.0, "expert_judgment": 0.0}
    for definitions in report["criteriaDefinitions"].values():
        for definition in definitions:
            suffix = definition["id"].rsplit(":", 1)[-1]
            assessment_class = "expert_judgment" if suffix in expert_tokens else "mechanical"
            definition["assessmentClass"] = assessment_class
            assessment_counts[assessment_class] += 1
            assessment_weights[assessment_class] += float(definition.get("weight", 0))

    coverage_summary: dict[str, dict[str, int]] = {}
    for item in report.get("coverageItems", []):
        coverage_type = item.get("coverageType", "other")
        row = coverage_summary.setdefault(coverage_type, {"reviewed": 0, "total": 0})
        row["total"] += 1
        if item.get("status") == "reviewed":
            row["reviewed"] += 1

    combined_scenarios: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(report.get("scenarioRuns", [])):
        key = item.get("id") or item.get("runId") or f"scenario:{index}"
        combined_scenarios.setdefault(str(key), item)
    supplemental_rows = []
    for key in ["crossArtifactTests", "list", "scenarioRecords", "labelChecklistRecords"]:
        value = report.get("rubricSubtests", {}).get(key, [])
        if isinstance(value, list):
            supplemental_rows.extend((key, item) for item in value)
    supplemental_unique: dict[str, dict[str, Any]] = {}
    for index, (collection_id, item) in enumerate(supplemental_rows):
        cross_key = item.get("id") or (
            f"{collection_id}:{item.get('label') or item.get('name') or item.get('test') or index}"
        )
        supplemental_unique.setdefault(str(cross_key), item)
    for index, item in enumerate(supplemental_unique.values()):
        if not (item.get("artifactId") or item.get("artifactIds")):
            continue
        key = item.get("id") or item.get("runId") or item.get("subtestId") or (
            f"{item.get('artifactId', 'scenario')}:"
            f"{item.get('action') or item.get('test') or item.get('scenario') or item.get('title') or index}"
        )
        combined_scenarios.setdefault(str(key), item)

    report["contentInventory"] = {
        "artifacts": {"count": len(report.get("artifacts", [])), "entry": "第3章逐文件矩阵及文件详情"},
        "scenarioRecords": {"count": len(combined_scenarios), "entry": "第7章全量复核浏览器/场景实测"},
        "coverageItems": {"count": len(report.get("coverageItems", [])), "entry": "第7章全量复核浏览器/覆盖记录"},
        "findings": {"count": len(report.get("findings", [])), "entry": "第5章问题与传播、第7章全量复核浏览器"},
        "evidence": {"count": len(report.get("evidence", [])), "entry": "第7章证据索引"},
        "media": {"count": len(report.get("media", [])), "entry": "第7章证据索引及证据弹窗"},
        "facts": {"count": len(report.get("facts", [])), "entry": "第6章事实基准母表"},
        "sources": {"count": len(report.get("sources", [])), "entry": "第6章来源索引及第7章过程记录"},
        "coverageByType": coverage_summary,
        "assessmentClasses": {
            "criterionCount": assessment_counts,
            "aggregateWeightAcrossSixRubrics": assessment_weights,
            "scoreEffect": "classification_only_no_score_change",
        },
    }
    report["presentation"] = {
        "executiveSummary": {
            "scope": "5款工具、6类任务、30件固定终稿；Excel对照独立事实基准，下游按本工具Excel一致性评价。",
            "rankingPolicy": "展示名次与一位小数分数；相邻分差不超过1分的项目同时标记为敏感组，不把小分差解释为稳定或可外推的差异。",
            "gatePolicy": "连续质量分与交付闸门并列呈现；G0/G1/G2不参与分数计算，G2-Mac仅描述固定Mac环境观察。",
            "evidencePolicy": "所有数字、闸门、排名、矩阵与摘要从同一JSON生成；过程与配置旁证不计分。",
        },
        "navigationGroups": [
            {"id": "executive", "label": "1 执行摘要", "sectionIds": ["executive"]},
            {"id": "results", "label": "2 比较结果", "sectionIds": ["ranking", "heatmap"]},
            {"id": "profiles", "label": "3 逐工具与逐文件表现", "sectionIds": ["profiles"]},
            {"id": "native", "label": "4 原生应用与兼容性", "sectionIds": ["compatibility", "coverage"]},
            {"id": "issues", "label": "5 问题、闸门与传播链", "sectionIds": ["gates", "lineage", "sensitivity"]},
            {"id": "facts", "label": "6 事实基准与来源", "sectionIds": ["facts"]},
            {"id": "evidence", "label": "7 方法、过程与全量证据", "sectionIds": ["method", "browser", "evidence", "process", "context", "appendix"]},
        ],
        "printProfiles": {
            "summary": {"label": "管理层摘要", "targetPages": "10–15", "description": "报告眉首、限制、两榜、质量矩阵、闸门、工具画像与核心结论。"},
            "formal": {"label": "正式报告", "targetPages": "25–35", "description": "增加兼容性、传播链、事实基准、方法与主要问题。"},
            "full": {"label": "全量证据", "targetPages": "约149", "description": "打印全部记录、来源、配置、截图索引、原件指纹与技术字段。"},
        },
        "assessmentClassLabels": {"mechanical": "机械验证项", "expert_judgment": "专家判断项"},
    }
    report["methodology"]["assessmentClassification"] = {
        "purpose": "区分可由规则或操作直接验证的项目与需要专业判断的项目；仅披露评分构成，不改变权重或得分。",
        "mechanical": "文件打开、公式/引用、报告期与单位、来源链、编辑性、覆盖、加载、响应式等可按预设动作和结果记录的项目。",
        "expert_judgment": "分析深度、信息取舍、叙事、视觉层级、专业构图与表达完成度等使用公开0—5锚点的项目。",
        "raterDisclosure": "单一评审者；未测量评审者间一致性。",
    }
    report["versionHistory"].append(
        {
            "version": "4.2",
            "status": "presentation_restructure_score_locked",
            "title": "v4.2专业化改版",
            "before": "13个平铺栏目、深色卡片式呈现、单一全量打印",
            "after": "7章机构投研简报结构、浅色默认、三种打印模式与内容守恒索引",
            "summary": "仅调整呈现、信息架构、打印与评价类型披露；30件分数、闸门、两张正式榜、finding判断及证据结论全部冻结。",
            "frozenV41HtmlSha256": "d3c4d969aaa16df8441c3e577130fec90e55dda859c0c0541e054f3595c32f17",
            "frozenV41JsonSha256": "b616869fc5b9b13688f4c411e29900f5e5f483b082573fab96512917d237fe51",
            "builderVersion": SCRIPT_VERSION,
        }
    )


def neutralize_attribution_language(value: Any) -> Any:
    """Remove intent-attributing wording from the active v4 payload.

    The byte-immutable v3 HTML remains the historical record.  v4 describes
    only what was observed or could/could not be traced.
    """

    if isinstance(value, dict):
        return {key: neutralize_attribution_language(item) for key, item in value.items()}
    if isinstance(value, list):
        return [neutralize_attribution_language(item) for item in value]
    if not isinstance(value, str):
        return value
    replacements = [
        ("列出截至截止日并不存在的", "列出截至截止日未能在指定官方披露渠道定位的"),
        ("当时并不存在的", "截至截止日未能在指定官方披露渠道定位的"),
        ("并不存在的报告", "截至截止日未能在指定官方披露渠道定位的报告"),
        ("并不存在的", "截至截止日未能在指定官方披露渠道定位的"),
        ("并不存在", "未能在指定官方披露渠道定位"),
        ("虚构来源", "未能在指定官方披露渠道定位的来源"),
        ("虚构财务数据", "未能回溯至指定披露的财务数据"),
        ("虚构净利润", "未能回溯至指定披露的净利润"),
        ("虚构", "未能回溯"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    return value


def finalize_release(report: dict[str, Any], release_log_path: Path | None) -> None:
    """Promote a QA-pending build only when an explicit release log passes.

    The normal build remains QA-pending.  Publication therefore requires an
    auditable, separately hashed record of the report-runtime checks.
    """

    if release_log_path is None:
        return
    release_log_path = release_log_path.resolve()
    release_log = json.loads(release_log_path.read_text(encoding="utf-8"))
    if release_log.get("allRequiredPassed") is not True:
        raise ValueError("release verification does not certify all required checks")
    checks = release_log.get("checks", [])
    required_ids = {
        "release:chrome-load",
        "release:ranking-two-official-plus-diagnostic",
        "release:scenario-browser",
        "release:finding-browser",
        "release:compatibility-matrix",
        "release:dialogs-and-evidence",
        "release:responsive",
        "release:keyboard-theme-anchor",
        "release:console",
        "release:official-links",
        "release:process-records",
        "release:configuration-usage-evidence",
        "release:print",
        "release:content-conservation",
        "release:terminology",
        "release:print-summary",
        "release:print-formal",
        "release:print-full",
        "release:visual-regression",
    }
    rows_by_id = {row.get("id"): row for row in checks}
    missing = required_ids - set(rows_by_id)
    if missing:
        raise ValueError(f"release verification missing checks: {sorted(missing)}")
    failed = [
        check_id
        for check_id in required_ids
        if not str(rows_by_id[check_id].get("status", "")).startswith("passed")
    ]
    if failed:
        raise ValueError(f"release verification has non-passing checks: {sorted(failed)}")

    release_sha = sha256(release_log_path)
    final_status = "final_v4_2_fixed_environment"
    report["meta"]["status"] = final_status
    report["meta"]["statusNote"] = (
        "固定样本、固定Mac环境发布版；未征求厂商正式回应，"
        "Windows PowerPoint与独立重新下载仍未验证。"
    )
    report["meta"]["buildProvenance"]["releaseVerification"] = {
        "path": str(release_log_path),
        "sha256": release_sha,
        "executedAt": release_log.get("executedAt"),
    }
    report["scores"]["status"] = final_status
    report["qualityScores"]["status"] = final_status
    report["rankingPerspectives"]["status"] = final_status
    for ranking in report["rankings"].values():
        if ranking.get("isOfficial", True):
            ranking["status"] = final_status
        else:
            ranking["status"] = "diagnostic_noncausal"
    report["rankingPerspectives"]["results"] = deepcopy(report["rankings"])
    for artifact in report["artifacts"]:
        artifact["scoreStatus"] = "native_review_completed_fixed_environment"
    for row in report.get("versionHistory", []):
        if row.get("version") == "4.2":
            row["status"] = "published_fixed_environment"
            row["releaseVerificationSha256"] = release_sha
            row["publicationManifestPath"] = str(
                HERE.parents[2]
                / "outputs"
                / "01a06a55-0c63-7c62-bf17-9f46fd6b3e81"
                / "AI办公工具对比测评_宇树科技_截至2026-08-30_v4_发布清单.json"
            )
            row["publishedHtmlSha256Convention"] = (
                "完整发布HTML的SHA-256登记在同目录发布清单；HTML无法在不改变自身哈希的前提下嵌入其最终完整文件哈希。"
            )
    ranking_check = next(
        (row for row in report.get("verification", []) if row.get("id") == "verification:ranking-recompute"),
        None,
    )
    if ranking_check is not None:
        ranking_check["status"] = "verified"
        ranking_check["reason"] = (
            "build_report_v4.py与qa_v4.py完成确定性重建和逐项断言；"
            "报告自身Chrome运行、响应式、交互与打印验收见发布核验日志。"
        )
    report.setdefault("verification", []).append(
        {
            "id": "verification:v4-report-release-runtime",
            "item": "v4.2报告自身Chrome运行、三档响应式、交互、来源、内容守恒与三种打印验收",
            "status": "verified",
            "reason": (
                f"发布核验日志包含{len(checks)}项检查且allRequiredPassed=true；"
                "两份上交所PDF的自动导航等待行为已单独披露，不归责任何参评样本。"
            ),
            "owner": "v4_release_qa",
            "logPath": str(release_log_path),
            "logSha256": release_sha,
        }
    )


def build(
    input_path: Path,
    supplement_path: Path | None = DEFAULT_SUPPLEMENT,
    release_log_path: Path | None = None,
) -> dict[str, Any]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    report = deepcopy(source)
    input_hash = sha256(input_path)
    report["meta"].update(
        {
            "schemaVersion": "4.1.0",
            "scoringVersion": "4.1-linear-gates-banded-noncausal-lineage",
            "generatedAt": "2026-09-06T12:00:00+08:00",
            "status": "final_v4_data",
            "title": "五款AI办公工具固定样本交付物比较评测与证据复核报告——宇树科技六任务，截至2026年8月30日",
            "subtitle": "固定样本、固定环境的交付物比较；正式比较采用独立终稿连续分与1分敏感组。",
            "buildProvenance": {
                "source": str(input_path.resolve()),
                "sourceSha256": input_hash,
                "builder": str(Path(__file__).resolve()),
                "builderVersion": SCRIPT_VERSION,
            },
        }
    )
    merge_user_supplied_process_records(report)
    merge_configuration_usage_evidence(report)
    supplement_context = merge_supplement_evidence(report, supplement_path)
    merge_v4_direct_evidence(report)
    update_native_word_page_metadata(report)
    propagation_score_modes = upgrade_propagation(report)
    add_non_scoring_verification(report)
    add_subitem_schema(report)
    rebuild_subscores(report)
    extend_findings(report)
    apply_v41_adjudication(report)
    finalize_supplement_evidence_status(report, supplement_context)
    recompute_linear_scores(report, source)
    assign_delivery_gates(report)
    rebuild_rankings(report)
    build_sensitivity(report, source)
    update_methodology(report, input_hash)
    migrate_legacy_namespace(report, source, propagation_score_modes, supplement_context)
    publish_v4_interfaces(report)
    merge_supplement_interfaces(report, supplement_context)
    enrich_v41_interfaces(report)
    enrich_v42_presentation(report)
    assign_embed_derivatives(report)
    finalize_release(report, release_log_path)
    report = neutralize_attribution_language(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the deterministic v4 evaluation ledger")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument(
        "--release-log",
        type=Path,
        default=None,
        help="promote to the fixed-environment release only after this verification log passes",
    )
    parser.add_argument(
        "--no-supplement",
        action="store_true",
        help="build without the optional evidence supplement",
    )
    args = parser.parse_args()
    report = build(
        args.input,
        None if args.no_supplement else args.supplement,
        args.release_log,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"sha256={sha256(args.output)}")
    for ranking_id, ranking in report["rankings"].items():
        print(ranking_id, [(row["rank"], row["tool"], row["score"]) for row in ranking["rows"]])


if __name__ == "__main__":
    main()
