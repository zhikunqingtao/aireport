#!/usr/bin/env python3
"""Build the v4.5.2 presentation from frozen v4.5.1 report data.

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
DEFAULT_DATA = HERE / "report_v4.5_final.json"
DEFAULT_UI_PATH = HERE / "report.ui.json"
DEFAULT_PATH_MAP = HERE.parents[1] / "manifests" / "path-map.json"
MAX_BYTES = 40 * 1024 * 1024
DYNAMIC_HERO_FIELDS = ("title", "lead", "statusNote")
TRANSPORT_FIELDS = {
    "dataUri", "data_uri", "dataUriRef", "embedded", "externallyReferenced",
    "embedError", "embedPath", "embedMimeType", "embeddedMimeType",
    "embeddedSha256", "embeddedBytes", "displayCopyNote",
}
DISPLAY_MEDIA_FILES = {
    "media:native:8e71f292cb665ac44392": "zhikuncode_html_fullpage-display.webp",
    "media:native:9677746001be6e821b20": "workbuddy_html_fullpage-display.webp",
    "media:native:6d73e4498bd2cc235431": "doubao_html_fullpage-display.webp",
    "media:native:c570bafe068037a5154d": "qianwen_html_fullpage-display.webp",
    "media:native:ac6d0a14e3bcea3bf42b": "qoder_html_fullpage-display.webp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--ui",
        type=Path,
        default=DEFAULT_UI_PATH,
        help="Canonical UI configuration. Input JSON meta.ui is never merged into it.",
    )
    parser.add_argument(
        "--dynamic-hero-data",
        type=Path,
        default=DEFAULT_DATA,
        help="Final release data supplying only title/lead/statusNote hero overrides.",
    )
    parser.add_argument(
        "--path-map",
        type=Path,
        default=DEFAULT_PATH_MAP,
        help="Repository path map used when a local absolute media path is unavailable.",
    )
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


def load_object(path: Path, label: str) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def load_report_ui(ui_path: Path, dynamic_hero_data_path: Path) -> dict:
    """Load the sole UI configuration plus an allowlisted final-data override."""
    ui = copy.deepcopy(load_object(ui_path, "UI configuration"))
    release = ui.get("release")
    if not isinstance(release, dict):
        raise ValueError(f"UI configuration has no release object: {ui_path}")
    for field in ("presentationVersion", "version"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError(f"UI release field must be a non-empty string: {field}")
    variants = release.get("publicationVariants")
    if not isinstance(variants, dict):
        raise ValueError(f"UI release publicationVariants must be an object: {ui_path}")
    for field in ("portable", "selfContained"):
        if not isinstance(variants.get(field), str) or not variants[field].strip():
            raise ValueError(f"UI release publication variant must be a non-empty string: {field}")
    if not isinstance(ui.get("hero"), dict):
        raise ValueError(f"UI configuration has no hero object: {ui_path}")
    final_data = load_object(dynamic_hero_data_path, "dynamic hero data")
    dynamic_hero = final_data.get("meta", {}).get("ui", {}).get("hero", {})
    if dynamic_hero is not None and not isinstance(dynamic_hero, dict):
        raise ValueError("final data meta.ui.hero must be an object")
    for field in DYNAMIC_HERO_FIELDS:
        if field in dynamic_hero:
            if not isinstance(dynamic_hero[field], str) or not dynamic_hero[field].strip():
                raise ValueError(f"final data dynamic hero field must be a non-empty string: {field}")
            ui["hero"][field] = copy.deepcopy(dynamic_hero[field])
        if not isinstance(ui["hero"].get(field), str) or not ui["hero"][field].strip():
            raise ValueError(f"UI hero field must be a non-empty string: {field}")
    return ui


def load_path_map(path: Path | None) -> tuple[dict[str, str], Path | None]:
    if path is None:
        return {}, None
    path = path.resolve()
    mapping = load_object(path, "path map")
    if not all(isinstance(source, str) and isinstance(target, str) for source, target in mapping.items()):
        raise ValueError(f"path map keys and values must be strings: {path}")
    try:
        case_dir = path.parents[3]
    except IndexError as error:
        raise ValueError(f"cannot infer case-studies directory from path map: {path}") from error
    return mapping, case_dir


def resolve_media_path(
    value: str,
    data_dir: Path,
    path_map: dict[str, str] | None = None,
    path_map_root: Path | None = None,
) -> Path | None:
    if not value or value.startswith(("data:", "http://", "https://")):
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = data_dir / candidate
    candidate = candidate.resolve()
    if candidate.is_file():
        return candidate
    mapped_value = (path_map or {}).get(value) or (path_map or {}).get(str(candidate))
    if mapped_value and path_map_root:
        mapped = (path_map_root / mapped_value).resolve()
        try:
            mapped.relative_to(path_map_root.resolve())
        except ValueError as error:
            raise ValueError(f"mapped media path escapes case-studies directory: {mapped_value}") from error
        return mapped
    return candidate


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


def embed_media(
    data: dict,
    data_dir: Path,
    path_map: dict[str, str] | None = None,
    path_map_root: Path | None = None,
) -> dict:
    """Return a deep copy with all available local evidence embedded."""
    result = copy.deepcopy(data)
    normalized: dict[str, dict] = {}
    digest_to_media_id: dict[str, str] = {}

    for key, item in media_items(result):
        record = dict(item)
        existing = record.get("dataUri") or record.get("data_uri")
        if existing:
            record["dataUri"] = existing
        elif record.get("dataUriRef"):
            # Portable data intentionally deduplicates a few repeated payloads
            # through another media record. Do not misclassify a valid alias as
            # a missing local file merely because its original source path is
            # expressed relative to the published case-study page.
            record.pop("embedError", None)
        else:
            original_path_value = record.get("path") or record.get("file") or record.get("src")
            display_name = DISPLAY_MEDIA_FILES.get(key)
            display_path = data_dir / "embedded-display" / display_name if display_name else None
            embed_path_value = str(display_path) if display_path and display_path.is_file() else (record.get("embedPath") or original_path_value)
            path = resolve_media_path(
                str(embed_path_value or ""), data_dir, path_map, path_map_root
            )
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
        path = resolve_media_path(
            str(embed_path_value or ""), data_dir, path_map, path_map_root
        )
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
            path = resolve_media_path(
                str(source_value or ""), data_dir, path_map, path_map_root
            )
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

    for media_id, record in normalized.items():
        if not record.get("dataUriRef"):
            continue
        resolution = media_resolution_kind(normalized, media_id)
        record["embedded"] = resolution == "inline"
        record["externallyReferenced"] = resolution == "external"
        if resolution == "unresolved":
            record["embedError"] = "去重媒体引用不存在或形成循环"
        else:
            record.pop("embedError", None)

    result["evidence"] = evidence
    result["media"] = normalized
    return result


def media_resolution_kind(media: dict[str, dict], media_id: str) -> str:
    """Classify a media record as inline, external, or unresolved.

    ``dataUriRef`` aliases inherit the classification of their canonical
    record. Cycles and missing targets are treated as unresolved.
    """
    seen: set[str] = set()
    current = media_id
    while current and current not in seen:
        seen.add(current)
        record = media.get(current) or {}
        value = record.get("dataUri") or record.get("data_uri")
        if value:
            return "inline" if str(value).startswith("data:") else "external"
        current = str(record.get("dataUriRef") or "")
    return "unresolved"


def script_json(value: Any) -> str:
    # Prevent an embedded value from terminating the JSON script element.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def inline_css_assets(css: str, css_path: Path) -> str:
    """Inline local CSS assets and reject network-backed presentation assets."""
    without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    if re.search(r"@import\b", without_comments, flags=re.I):
        raise ValueError("report.css must not use @import; keep presentation assets local")

    def replace(match: re.Match[str]) -> str:
        raw = match.group("value").strip()
        if not raw or raw.startswith(("data:", "#")):
            return match.group(0)
        if raw.startswith(("http://", "https://", "//")) or re.match(r"^[a-z][a-z0-9+.-]*:", raw, flags=re.I):
            raise ValueError(f"external CSS asset is not allowed: {raw}")
        asset = (css_path.parent / raw).resolve()
        try:
            asset.relative_to(HERE)
        except ValueError as error:
            raise ValueError(f"CSS asset escapes the release source directory: {raw}") from error
        if not asset.is_file():
            raise FileNotFoundError(f"CSS asset is missing: {asset}")
        payload = asset.read_bytes()
        mime = {
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf",
            ".otf": "font/otf",
        }.get(asset.suffix.lower()) or mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(payload).decode("ascii")
        return f'url("data:{mime};base64,{encoded}")'

    return re.sub(
        r"url\(\s*(?P<quote>['\"]?)(?P<value>.*?)(?P=quote)\s*\)",
        replace,
        css,
        flags=re.I,
    )


def compact_css(value: str) -> str:
    """Losslessly remove comments and presentation-only whitespace."""
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*([{}:;,>])\s*", r"\1", value)
    return value.strip()


def compact_js(value: str) -> str:
    """Trim indentation and blank lines while retaining ASI-safe line breaks."""
    return "\n".join(line.lstrip() for line in value.splitlines() if line.strip())


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def semantic_projection(data: dict, path_map: dict[str, str]) -> dict:
    """Remove only transport differences before cross-variant comparison."""
    result = copy.deepcopy(data)
    meta = result.get("meta", {})
    meta.pop("publicationVariant", None)
    meta.pop("portablePackage", None)

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        if isinstance(value, str):
            return path_map.get(value, value)
        return value

    result = normalize(result)
    media = result.get("media", {})
    media_records = media if isinstance(media, dict) else {
        str(item.get("id") or index): item
        for index, item in enumerate(media)
        if isinstance(item, dict)
    }
    result["media"] = {
        media_id: {
            key: value
            for key, value in record.items()
            if key not in TRANSPORT_FIELDS
        }
        for media_id, record in media_records.items()
    }
    challenges = result.get("challenges")
    if isinstance(challenges, dict):
        for response in as_list(challenges.get("responses")):
            if not isinstance(response, dict):
                continue
            for field in (
                "screenshotPath", "screenshotEmbedPath", "screenshotDataUri",
                "screenshotMimeType", "screenshotEmbeddedSha256",
                "screenshotEmbeddedBytes", "screenshotEmbedded",
                "screenshotEmbedError",
            ):
                response.pop(field, None)
    return result


def prepare_report_data(
    raw: dict,
    data_path: Path,
    ui_path: Path,
    dynamic_hero_data_path: Path,
    path_map_path: Path | None,
) -> tuple[dict, dict[str, str]]:
    path_map, path_map_root = load_path_map(path_map_path)
    data = embed_media(raw, data_path.resolve().parent, path_map, path_map_root)
    data.setdefault("meta", {})
    if "toolOrder" not in data["meta"] and isinstance(data["meta"].get("tools"), list):
        data["meta"]["toolOrder"] = copy.deepcopy(data["meta"]["tools"])
    if "kindOrder" not in data["meta"] and isinstance(data["meta"].get("kinds"), list):
        data["meta"]["kindOrder"] = copy.deepcopy(data["meta"]["kinds"])
    data["meta"].setdefault(
        "kindLabels",
        {"excel": "Excel", "word": "Word", "ppt": "PPT", "image": "普通信息图", "ink": "水墨信息图", "html": "交互 HTML"},
    )
    data["meta"]["ui"] = load_report_ui(ui_path.resolve(), dynamic_hero_data_path.resolve())
    release = data["meta"]["ui"]["release"]
    data["meta"]["presentationVersion"] = release["presentationVersion"]
    data["meta"]["version"] = release["version"]
    variant_key = "portable" if raw.get("meta", {}).get("publicationVariant") else "selfContained"
    data["meta"]["publicationVariant"] = release["publicationVariants"][variant_key]
    hero = data["meta"]["ui"]["hero"]
    data["meta"]["title"] = str(hero["title"])
    data["meta"]["subtitle"] = str(hero["lead"])
    status_note = str(hero["statusNote"])
    data["meta"].setdefault("scoringNote", status_note)
    data["meta"]["statusNote"] = status_note
    return data, path_map


def build(
    data_path: Path,
    out_path: Path,
    allow_large: bool = False,
    compress_report_data: bool = False,
    ui_path: Path = DEFAULT_UI_PATH,
    dynamic_hero_data_path: Path = DEFAULT_DATA,
    path_map_path: Path | None = DEFAULT_PATH_MAP,
) -> dict:
    data_path = data_path.resolve()
    out_path = out_path.resolve()
    raw = load_object(data_path, "report data")
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
        raise ValueError(f"report data missing top-level keys: {', '.join(missing)}")

    data, path_map = prepare_report_data(
        raw,
        data_path,
        ui_path,
        dynamic_hero_data_path,
        path_map_path,
    )
    template = (HERE / "report.template.html").read_text(encoding="utf-8")
    css_path = HERE / "report.css"
    css = compact_css(inline_css_assets(css_path.read_text(encoding="utf-8"), css_path))
    js = compact_js((HERE / "report.js").read_text(encoding="utf-8"))
    title = str(data["meta"]["ui"]["hero"]["title"])
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
        # A fixed gzip timestamp keeps otherwise identical HTML builds byte-for-byte
        # reproducible across runs and machines.
        compressed = gzip.compress(report_json.encode("utf-8"), compresslevel=9, mtime=0)
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

    media_kinds = [media_resolution_kind(data["media"], media_id) for media_id in data["media"]]
    return {
        "path": str(out_path.resolve()),
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "mediaTotal": len(media_kinds),
        "embeddedMedia": media_kinds.count("inline"),
        "externalMedia": media_kinds.count("external"),
        "deduplicatedMediaReferences": sum(1 for item in data["media"].values() if item.get("dataUriRef")),
        "missingMedia": media_kinds.count("unresolved"),
        "reportDataEncoding": "gzip-base64" if compressed_report_data else "json",
        "uiSha256": canonical_json_sha256(data["meta"]["ui"]),
        "semanticSha256": canonical_json_sha256(semantic_projection(data, path_map)),
    }


def main() -> None:
    args = parse_args()
    summary = build(
        args.data.resolve(),
        args.out.resolve(),
        args.allow_over_40mb,
        args.compress_report_data,
        args.ui.resolve(),
        args.dynamic_hero_data.resolve(),
        args.path_map.resolve() if args.path_map else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
