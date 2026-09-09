#!/usr/bin/env python3
"""Build the self-contained fixed-sample evidence-review report from report_v4.json.

The source JSON is never modified. Local evidence/media files referenced by the
JSON are converted to data URIs in the in-memory copy before the single HTML is
written. The output is written atomically.
"""

from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
from html import escape as html_escape
import json
import mimetypes
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_DATA = HERE.parent / "v4" / "report_v4.json"
MAX_BYTES = 40 * 1024 * 1024
DISPLAY_MEDIA_FILES = {
    "media:native:8e71f292cb665ac44392": "zhikuncode_html_fullpage-display.webp",
    "media:native:9677746001be6e821b20": "workbuddy_html_fullpage-display.webp",
    "media:native:6d73e4498bd2cc235431": "doubao_html_fullpage-display.webp",
    "media:native:c570bafe068037a5154d": "qianwen_html_fullpage-display.webp",
    "media:native:ac6d0a14e3bcea3bf42b": "qoder_html_fullpage-display.webp",
}

DEFAULT_UI = {
    "brand": "固定样本交付物比较",
    "hero": {
        "title": "五款AI办公工具固定样本交付物比较评测与证据复核报告——宇树科技六任务，截至2026年8月30日",
        "lead": "对5款工具共30件固定终稿（每款6件）的单次、单环境复核；结论仅代表本次样本表现，不外推为工具的一般表现。",
        "statusNote": "正式比较只使用独立终稿连续分；点估计顺序同时配套单评审、非统计的单项一步判断敏感性，避免把微小分差解释为确定性优劣。",
    },
    "nav": {"protocol": "测试流程", "executive": "执行摘要", "results": "比较结果", "profiles": "逐工具与逐文件", "native": "原生应用与兼容性", "issues": "问题、闸门与传播链", "facts": "事实基准与来源", "evidence": "方法、过程与全量证据", "challenges": "异议裁决"},
    "metrics": {
        "artifacts": "终稿样本", "artifactsNote": "5款 × 6类", "scenarios": "场景实测", "scenariosNote": "已完成/总数",
        "coverage": "覆盖项", "coverageNote": "Sheet、页、幻灯片及视口", "nativePass": "原生打开通过", "nativePassNote": "指定应用首次打开",
        "editSuccess": "编辑任务通过", "editSuccessNote": "编辑、联动、保存及重开",
        "repairs": "修复提示", "repairsNote": "按文件特异性判定",
    },
    "sections": {
        "process": {"kicker": "", "title": "用户补充的全过程记录", "copy": "五条分享记录用于还原任务上下文与提供复核入口；它们不替代终稿原件、原生应用实测或Excel独立事实账本，也不直接参与评分。"},
        "context": {"kicker": "", "title": "本次任务配置与用量/费用旁证", "copy": "五款均有配置证据；四款有产品自身额度截图，ZhikunCode另有一张Kimi API账户日账单旁证。该账单混有其他任务，不能归因于本次六任务。全部资料均不计分，也不把本次比较误称为同模型、同算力或同成本控制实验。"},
        "ranking": {"kicker": "", "title": "独立终稿点估计比较", "copy": "仅发布六任务等权和均衡投研实务两种正式比较；同步展示一次改变一个已分类专家/混合判断维度的非统计敏感性范围、S组和情景重算次序。旧传播恢复值仅留在历史附录，不再作为活动排名。"},
        "heatmap": {"kicker": "", "title": "30件终稿连续质量分", "copy": "分数仅0–100线性加权，不应用59/39/69数值封顶；点击查看子测试、问题、闸门和证据。"},
        "gates": {"kicker": "", "title": "G0 / G1 / G2 交付安全矩阵", "copy": "闸门不改写连续分：G0可按常规复核使用，G1修正后可用，G2禁止未经复核直接交付。完全继承不重复归责，也不自动升级闸门；只有符合已公开的对称G2规则才可升级。"},
        "compatibility": {"kicker": "", "title": "平台兼容证据矩阵", "copy": "区分已观察的环境结果与未验证平台，不把Mac特定表现外推为通用文件结论。"},
        "sensitivity": {"kicker": "", "title": "规则与权重敏感性", "copy": "展示HTML交互权重、千问Excel图表、v3历史封顶以及传播归责口径改变时的排名变化。"},
        "native": {"kicker": "", "title": "原生打开与修复矩阵", "copy": "指定应用首次打开、修复提示和编辑任务在这里逐件可见；环境共性问题与文件特异问题分开记录。"},
        "browser": {"kicker": "", "title": "场景、覆盖与问题复核浏览器", "copy": "按工具、产物、闸门、严重度和关键词查找可复现观察、谨慎解读与反证条件。"},
        "evidence": {"kicker": "", "title": "原生实测证据", "copy": "缩略图全部内嵌并按内容哈希去重；点击可查看高清局部、应用版本、动作、定位和关联结论。"},
        "lineage": {"kicker": "", "title": "根因与传播链（非计分归责）", "copy": "origin、exact_propagation、mutated和independently_reintroduced分开展示；完全继承不重复归责，但终端文件风险仍独立显示。"},
        "risk": {"kicker": "", "title": "终端独立使用风险", "copy": "这是一层不计分的安全提示：下游产物即使忠实继承Excel，也可能在脱离底稿单独使用时传播错误。"},
        "facts": {"kicker": "", "title": "Excel核心事实基准与覆盖边界", "copy": "公开32项基准的选取规则、来源定位与未覆盖范围；只称为核心事实核对，不宣称对工作簿全部数字完成全量鉴证。"},
        "appendix": {"kicker": "", "title": "规则、版本变更、样本指纹与待核验", "copy": "每项扣分必须能回到子测试、finding和证据；v3→v4规则变化与旧新SHA公开。"},
    },
    "ranking": {
        "equal": "六任务等权榜", "practical": "均衡投研实务榜", "provisional": "临时排名 · 原生实测未完", "final": "最终排名 · 验收完成", "provisionalLeader": "临时第1", "finalLeader": "本次样本第1",
        "equalTaskNote": "六类终稿各占1/6；适合评价六个连续提示的总体完成度。",
        "practicalNote": "Excel 25%、Word 20%、PPT 20%、普通图10%、水墨图10%、HTML 15%。",
        "sensitivityTitle": "重大性判断敏感性",
    },
    "browser": {
        "scenario": "场景实测", "coverage": "覆盖记录", "finding": "发现与扣分",
        "scenarioNote": "一条记录对应一次真实操作：打开、重算、编辑、放映、缩放、点击或响应式测试。",
        "coverageNote": "一条记录对应一个已复核或待复核的Sheet、原生页面、幻灯片、图片区域或HTML视口。",
        "findingNote": "同一根因在同一文件只扣一个主维度；继承型finding强制不扣分、不封顶。",
    },
    "filters": {"tool": "工具", "kind": "产物", "status": "状态", "severity": "严重度", "search": "全文检索", "searchPlaceholder": "Sheet、页码、动作、问题、证据……"},
    "status": {"pass": "通过", "warn": "有警告", "repair": "需修复", "fail": "失败", "blocked": "需协助", "pending": "待实测", "complete": "通过", "legacyStatic": "历史静态参考", "superseded": "由v3实测替代", "automated": "自动校验通过"},
    "severity": {"critical": "关键", "major": "主要", "minor": "轻微", "info": "信息"},
    "groups": {"reliability": "可靠性", "native_usability": "原生可用性", "delivery": "交付质量"},
    "labels": {
        "skip": "跳至正文", "mainNav": "主导航", "theme": "切换明暗主题", "close": "关闭", "all": "全部", "tool": "工具",
        "rankingMode": "排名口径", "recordType": "记录类型", "pendingScore": "待实测", "final": "最终", "provisional": "临时/待验",
        "noNativeRecord": "尚无原生打开记录", "records": "条记录", "scenario": "场景实测", "coverage": "覆盖记录", "finding": "复核发现",
        "expected": "预期", "artifactDetail": "文件详情", "evidence": "证据", "evidencePending": "证据图片待嵌入", "propagation": "传播记录",
        "noPath": "路径待登记", "notDeducted": "不计分", "source": "来源", "openSource": "打开原始来源 ↗", "yes": "是", "no": "否",
        "artifact": "产物", "locator": "定位", "action": "动作", "application": "应用", "captured": "采集时间",
        "cutoff": "资料截止", "environment": "实测环境",
    },
    "facts": {"metric": "指标", "period": "报告期", "value": "基准值", "unit": "统一单位", "attribute": "属性/财务审计状态", "source": "来源定位"},
    "criteria": {"kind": "产物", "dimension": "评分维度", "weight": "权重", "group": "分组", "external": "可用外部事实"},
    "manifest": {"tool": "工具", "kind": "产物", "file": "原件", "size": "大小", "hash": "SHA-256", "copies": "核验副本", "status": "评分状态"},
    "modal": {"native": "原生实测与覆盖", "runs": "场景记录", "coverage": "覆盖记录", "findings": "发现", "fileIdentity": "文件标识", "fingerprintAppendix": "完整本地路径与SHA-256仅在折叠附录展示。", "scoring": "逐项评分", "baseScore": "基础分", "repairPenalty": "修复扣分", "cap": "封顶", "evidenceMeta": "证据元数据"},
    "appendix": {"methodology": "固定评分原则", "verification": "仍需人工协助或核验", "criteria": "展开六类评分维度与权重", "manifest": "展开30件终稿原件指纹与核验副本"},
    "empty": {"rankings": "暂无可计算排名。", "records": "当前筛选条件下没有记录。", "evidence": "尚无已登记证据。", "propagation": "尚无传播链记录。", "risks": "未登记终端独立使用风险。", "facts": "尚无事实账本数据。", "sources": "尚无来源记录。", "verification": "没有待人工处理事项。", "scores": "原生实测完成后生成逐项分。"},
    "footer": "评测截止日与评分口径以本页方法说明为准。工具自评仅提供异议线索，不具有证据权重；本报告未取得厂商正式签字或认可，也不构成投资建议。",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--allow-over-40mb",
        action="store_true",
        help="Build even when the resulting HTML exceeds the 40 MiB acceptance target.",
    )
    parser.add_argument(
        "--compress-report-data",
        action="store_true",
        help="Always gzip the embedded JSON payload, including portable Pages builds below 40 MiB.",
    )
    return parser.parse_args()


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []


def resolve_media_path(value: str, data_dir: Path) -> Path | None:
    if not value or value.startswith(("data:", "http://", "https://")):
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = data_dir / candidate
    return candidate.resolve()


def sniff_mime(payload: bytes, path: Path, declared_mime: str | None = None) -> str:
    """Return the payload MIME, preferring file signatures over metadata.

    Source media can retain an original filename while using a compact display
    derivative, and some legacy screenshots have a ``.png`` suffix despite
    containing JPEG bytes.  A data URI must describe the bytes actually embedded.
    """
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return "image/webp"
    if payload.startswith(b"%PDF-"):
        return "application/pdf"
    return declared_mime or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def encode_file(path: Path, declared_mime: str | None = None) -> tuple[str, str, str, int]:
    payload = path.read_bytes()
    mime = sniff_mime(payload, path, declared_mime)
    digest = hashlib.sha256(payload).hexdigest()
    data_uri = f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"
    return data_uri, mime, digest, len(payload)


def media_items(data: dict) -> Iterable[tuple[str, dict]]:
    media = data.get("media", [])
    if isinstance(media, dict):
        for key, raw in media.items():
            item = raw if isinstance(raw, dict) else {"path": raw}
            item.setdefault("id", str(key))
            yield str(key), item
    elif isinstance(media, list):
        for index, raw in enumerate(media):
            item = raw if isinstance(raw, dict) else {"path": raw}
            key = str(item.get("id") or f"media:{index + 1}")
            item.setdefault("id", key)
            yield key, item


def embed_media(data: dict, data_dir: Path) -> dict:
    """Return a deep copy with all available local evidence embedded."""
    result = copy.deepcopy(data)
    normalized: dict[str, dict] = {}
    digest_to_media_id: dict[str, str] = {}

    for key, item in media_items(result):
        record = dict(item)
        existing = record.get("dataUri") or record.get("data_uri")
        if existing:
            record["dataUri"] = existing
        else:
            original_path_value = record.get("path") or record.get("file") or record.get("src")
            display_name = DISPLAY_MEDIA_FILES.get(key)
            display_path = data_dir / "embedded-display" / display_name if display_name else None
            embed_path_value = str(display_path) if display_path and display_path.is_file() else (record.get("embedPath") or original_path_value)
            path = resolve_media_path(str(embed_path_value or ""), data_dir)
            if path and path.is_file():
                mime_hint = record.get("embedMimeType") or record.get("mime") or record.get("mimeType")
                data_uri, mime, digest, size = encode_file(path, mime_hint)
                canonical_id = digest_to_media_id.get(digest)
                if canonical_id:
                    record["dataUriRef"] = canonical_id
                else:
                    record["dataUri"] = data_uri
                    digest_to_media_id[digest] = key
                record["mime"] = mime
                record["embeddedMimeType"] = mime
                record["embeddedSha256"] = digest
                record["embeddedBytes"] = size
                record.setdefault("bytes", size)
                if display_path and path == display_path:
                    record["displayCopyNote"] = "HTML显示副本；活动JSON中的原始证据路径、字节数与SHA-256保持不变。"
                if not record.get("embedPath"):
                    record.setdefault("sha256", digest)
                record["embedded"] = True
            else:
                record["embedded"] = False
                if embed_path_value:
                    record["embedError"] = "本地媒体文件不存在或不可读取"
        normalized[key] = record

    evidence = as_list(result.get("evidence"))
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            continue
        media_id = str(item.get("mediaId") or item.get("media_id") or "")
        if media_id and media_id in normalized:
            continue
        direct_uri = item.get("dataUri") or item.get("data_uri")
        if direct_uri:
            key = media_id or str(item.get("id") or f"evidence:{index + 1}")
            normalized[key] = {"id": key, "dataUri": direct_uri, "embedded": True}
            item["mediaId"] = key
            continue
        original_path_value = item.get("path") or item.get("file") or item.get("src")
        embed_path_value = item.get("embedPath") or original_path_value
        path = resolve_media_path(str(embed_path_value or ""), data_dir)
        if path and path.is_file():
            mime_hint = item.get("embedMimeType") or item.get("mime") or item.get("mimeType")
            data_uri, mime, digest, size = encode_file(path, mime_hint)
            key = media_id or f"evidence-media:{item.get('id') or index + 1}"
            record = {
                "id": key,
                "mime": mime,
                "embeddedMimeType": mime,
                "embeddedSha256": digest,
                "embeddedBytes": size,
                "embedded": True,
            }
            canonical_id = digest_to_media_id.get(digest)
            if canonical_id:
                record["dataUriRef"] = canonical_id
            else:
                record["dataUri"] = data_uri
                digest_to_media_id[digest] = key
            for field in ("path", "file", "src", "sha256", "bytes", "embedPath", "embedMimeType"):
                if field in item:
                    record[field] = item[field]
            if not item.get("embedPath"):
                record.setdefault("path", str(path))
                record.setdefault("sha256", digest)
                record.setdefault("bytes", size)
            normalized[key] = record
            item["mediaId"] = key

    # These five images are challenge submissions, not scoring evidence, so
    # they remain outside the frozen 710-item media ledger.  Embed a display
    # copy for the self-contained report without changing ledger counts.
    challenges = result.get("challenges")
    if isinstance(challenges, dict):
        for response in as_list(challenges.get("responses")):
            if not isinstance(response, dict):
                continue
            source_value = response.get("screenshotEmbedPath") or response.get("screenshotPath")
            path = resolve_media_path(str(source_value or ""), data_dir)
            if not path or not path.is_file():
                response["screenshotEmbedded"] = False
                if source_value:
                    response["screenshotEmbedError"] = "原始自评截图不存在或不可读取"
                continue
            data_uri, mime, digest, size = encode_file(path)
            expected = response.get("screenshotSha256")
            if expected and expected != digest:
                raise ValueError(f"self-review screenshot SHA-256 mismatch: {path}")
            response.update({
                "screenshotDataUri": data_uri,
                "screenshotMimeType": mime,
                "screenshotEmbeddedSha256": digest,
                "screenshotEmbeddedBytes": size,
                "screenshotEmbedded": True,
            })

    result["evidence"] = evidence
    result["media"] = normalized
    return result


def script_json(value: Any) -> str:
    # Prevent an embedded value from terminating the JSON script element.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def compact_css(value: str) -> str:
    """Losslessly remove comments and presentation-only whitespace."""
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*([{}:;,>])\s*", r"\1", value)
    return value.strip()


def compact_js(value: str) -> str:
    """Trim indentation and blank lines while retaining ASI-safe line breaks."""
    return "\n".join(line.lstrip() for line in value.splitlines() if line.strip())


def merge_defaults(target: dict, defaults: dict) -> None:
    for key, value in defaults.items():
        if key not in target:
            target[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(target[key], dict):
            merge_defaults(target[key], value)


def build(
    data_path: Path,
    out_path: Path,
    allow_large: bool = False,
    compress_report_data: bool = False,
) -> dict:
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    required = {
        "meta", "methodology", "sources", "facts", "artifacts", "scenarios",
        "scenarioRuns", "coverageItems", "criteriaDefinitions", "findings",
        "scores", "rankings", "propagation", "evidence", "media", "verification",
        "rubricSubtests", "qualityScores", "deliveryGates", "rankingPerspectives",
        "compatibilityMatrix", "sensitivity", "versionHistory", "presentation",
        "contentInventory",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"report_v4.json missing top-level keys: {', '.join(missing)}")

    data = embed_media(raw, data_path.resolve().parent)
    data.setdefault("meta", {})
    if "toolOrder" not in data["meta"] and isinstance(data["meta"].get("tools"), list):
        data["meta"]["toolOrder"] = copy.deepcopy(data["meta"]["tools"])
    if "kindOrder" not in data["meta"] and isinstance(data["meta"].get("kinds"), list):
        data["meta"]["kindOrder"] = copy.deepcopy(data["meta"]["kinds"])
    data["meta"].setdefault(
        "kindLabels",
        {"excel": "Excel", "word": "Word", "ppt": "PPT", "image": "普通信息图", "ink": "水墨信息图", "html": "交互 HTML"},
    )
    data["meta"].setdefault("ui", {})
    merge_defaults(data["meta"]["ui"], DEFAULT_UI)
    data["meta"].setdefault("version", "报告版本 4.2 · 固定样本证据复核")
    # The fixed-sample framing is an invariant, not optional presentation copy:
    # a single fixed sample must never be relabelled as general product ability.
    data["meta"]["title"] = "五款AI办公工具固定样本交付物比较评测与证据复核报告——宇树科技六任务，截至2026年8月30日"
    data["meta"]["subtitle"] = data["meta"]["ui"]["hero"]["lead"]
    scoring_note = data["meta"]["ui"]["hero"]["statusNote"]
    data["meta"]["scoringNote"] = scoring_note
    if not str(data["meta"].get("status", "")).startswith("final"):
        data["meta"]["statusNote"] = scoring_note
    else:
        data["meta"].setdefault("statusNote", scoring_note)
    template = (HERE / "report.template.html").read_text(encoding="utf-8")
    css = compact_css((HERE / "report.css").read_text(encoding="utf-8"))
    js = compact_js((HERE / "report.js").read_text(encoding="utf-8"))
    title = str(data.get("meta", {}).get("title") or DEFAULT_UI["hero"]["title"])
    report_json = script_json(data)

    def assemble(report_payload: str, data_attributes: str = "") -> str:
        return (
            template.replace("__REPORT_TITLE__", html_escape(title))
            .replace("__REPORT_CSS__", css)
            .replace("__REPORT_JSON__", report_payload)
            .replace("__REPORT_DATA_ATTRIBUTES__", data_attributes)
            .replace("__REPORT_JS__", js.replace("</script", "<\\/script"))
        )

    html = assemble(report_json)
    encoded = html.encode("utf-8")
    compressed_report_data = False
    if len(encoded) > MAX_BYTES or compress_report_data:
        # Losslessly compress the complete in-page JSON.  This preserves every
        # evidence byte while keeping the single-file deliverable below the
        # repository limit; the report script inflates it before parsing.
        compressed = gzip.compress(report_json.encode("utf-8"), compresslevel=9)
        report_payload = base64.b64encode(compressed).decode("ascii")
        html = assemble(report_payload, 'data-encoding="gzip-base64"')
        encoded = html.encode("utf-8")
        compressed_report_data = True
    if len(encoded) > MAX_BYTES and not allow_large:
        raise ValueError(
            f"built HTML is {len(encoded):,} bytes, above the 40 MiB target; "
            "deduplicate/compress media or use --allow-over-40mb for diagnosis"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{out_path.name}.", suffix=".tmp", dir=out_path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, out_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise

    return {
        "path": str(out_path.resolve()),
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "embeddedMedia": sum(1 for item in data["media"].values() if item.get("embedded")),
        "missingMedia": sum(1 for item in data["media"].values() if item.get("embedded") is False),
        "reportDataEncoding": "gzip-base64" if compressed_report_data else "json",
    }


def main() -> None:
    args = parse_args()
    summary = build(
        args.data.resolve(),
        args.out.resolve(),
        args.allow_over_40mb,
        args.compress_report_data,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
