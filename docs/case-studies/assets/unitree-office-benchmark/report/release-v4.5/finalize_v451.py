#!/usr/bin/env python3
"""Finalize the deterministic v4.5.2 presentation and integrity manifests.

The repository intentionally retains the public/internal ``v4.5`` filenames so
existing links remain stable.  The frozen scoring data remains ``4.5.1`` while
this script records ``4.5.2`` as the presentation release, refreshes hashes and sizes, and closes the
package-wide SHA-256 inventory without creating a self-referential hash cycle.

The default mode is read-only.  Pass ``--write`` to replace the four generated
files atomically, then run the script again (without flags) to verify that the
result is idempotent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


REPORT_VERSION = "4.5.2"
DATA_VERSION = "4.5.1"
COMPATIBILITY_FILENAME_VERSION = "4.5"
PACKAGE_RELATIVE = Path(
    "docs/case-studies/assets/unitree-office-benchmark"
)
RELEASE_RELATIVE = Path("report/release-v4.5")
PORTABLE_REPORT_NAME = "AI办公工具对比测评_宇树科技_截至2026-08-30.html"
HISTORICAL_V45_FILES = {
    "adjudicate_v45.py",
    "qa_interaction_affordance.json",
    "qa_report_postpublication_hardened.json",
    "qa_v45.py",
    "recompute_summary.json",
    "stamp_v45.py",
}


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_descriptor(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def bytes_descriptor(value: bytes) -> dict[str, Any]:
    return {"bytes": len(value), "sha256": sha256_bytes(value)}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def count(value: Any) -> int:
    if isinstance(value, (list, dict)):
        return len(value)
    return 0


def report_counts(data: dict[str, Any]) -> dict[str, int]:
    inventory = data.get("contentInventory") or {}
    scenario_records = inventory.get("scenarioRecords") or {}
    return {
        "artifacts": count(data.get("artifacts")),
        "scenarioRecords": int(scenario_records.get("count", 0)),
        "coverageItems": count(data.get("coverageItems")),
        "findings": count(data.get("findings")),
        "evidence": count(data.get("evidence")),
        "media": count(data.get("media")),
        "facts": count(data.get("facts")),
        "sources": count(data.get("sources")),
    }


def resolve_repo(explicit_repo: str | None) -> Path:
    if explicit_repo:
        repo = Path(explicit_repo).expanduser().resolve()
    else:
        # finalize_v451.py lives at:
        # <repo>/docs/case-studies/assets/unitree-office-benchmark/
        # report/release-v4.5/finalize_v451.py
        repo = Path(__file__).resolve().parents[6]
    package_root = repo / PACKAGE_RELATIVE
    if not package_root.is_dir():
        raise FileNotFoundError(f"package root not found: {package_root}")
    return repo


def assert_content_version(path: Path, data: dict[str, Any]) -> None:
    meta = data.get("meta") or {}
    observed = {
        str(meta.get("schemaVersion", "")),
        str(meta.get("presentationVersion", "")),
        str(meta.get("dataVersion", "")),
    }
    if DATA_VERSION not in observed:
        raise ValueError(
            f"{path} does not identify frozen data version {DATA_VERSION}; "
            f"observed={sorted(observed)}"
        )


def release_files(release_dir: Path, manifest_path: Path) -> list[Path]:
    transient_names = {".DS_Store"}
    result: list[Path] = []
    for path in release_dir.rglob("*"):
        if not path.is_file() or path == manifest_path:
            continue
        relative = path.relative_to(release_dir)
        if (
            path.name in transient_names
            or path.suffix in {".pyc", ".tmp", ".swp"}
            or "__pycache__" in relative.parts
        ):
            raise ValueError(f"transient file must be removed before finalization: {path}")
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(release_dir).as_posix())


def release_file_descriptor(
    path: Path,
    release_dir: Path,
    overrides: dict[Path, bytes],
) -> dict[str, Any]:
    content = overrides.get(path)
    descriptor = bytes_descriptor(content) if content is not None else file_descriptor(path)
    relative = path.relative_to(release_dir).as_posix()
    if relative in HISTORICAL_V45_FILES:
        role = "historical_v4.5_reference_not_current_v4.5.2_release"
    elif relative.startswith("provenance-inputs/"):
        role = "calculation_provenance_input"
    elif "v451" in path.name or path.name == "report_v4.5_final.json":
        role = "frozen_v4.5.1_semantic_qa_or_data_for_v4.5.2"
    else:
        role = "current_v4.5.2_presentation_source"
    return {"path": relative, "role": role, **descriptor}


def mime_type(path: Path) -> str:
    return {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "text/javascript",
        ".json": "application/json",
        ".py": "text/x-python",
        ".txt": "text/plain",
    }.get(path.suffix.lower(), "application/octet-stream")


def new_release_record(package_root: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(package_root).as_posix()
    if path.name.startswith("qa_"):
        roles = ["v4.5.2发布校验材料"]
    elif path.suffix == ".py":
        roles = ["v4.5.2可复现构建与发布脚本"]
    else:
        roles = ["v4.5.2本地发布材料"]
    return {
        "sourcePathAtPackaging": f"repository:{PACKAGE_RELATIVE.as_posix()}/{relative}",
        "relativePath": relative,
        "category": ["v4.5.1_release"],
        "roles": roles,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "mimeType": mime_type(path),
        "jsonPointers": [],
        "kind": "generated_release",
        "duplicateOf": None,
    }


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = path.stat() if path.exists() else None
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if descriptor is not None:
            os.chmod(temp_name, descriptor.st_mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def build_expected(repo: Path) -> tuple[dict[Path, bytes], dict[str, Any]]:
    package_root = repo / PACKAGE_RELATIVE
    report_dir = package_root / "report"
    release_dir = package_root / RELEASE_RELATIVE
    manifests_dir = package_root / "manifests"
    case_dir = repo / "docs/case-studies"

    paths = {
        "summary": release_dir / "build_summary_final.json",
        "release_manifest": release_dir / "release_manifest_v4.5.json",
        "files_manifest": manifests_dir / "files.json",
        "sums": manifests_dir / "SHA256SUMS.txt",
        "video_index": manifests_dir / "process-video-index.json",
        "source_html": report_dir / "source-self-contained-v4.5.html",
        "portable_html": case_dir / PORTABLE_REPORT_NAME,
        "activity_data": report_dir / "activity-report-data-v4.5.json",
        "portable_data": report_dir / "portable-report-data-v4.5.json",
        "final_data": release_dir / "report_v4.5_final.json",
    }
    missing = [str(path) for key, path in paths.items() if key != "sums" and not path.is_file()]
    if missing:
        raise FileNotFoundError("required finalization inputs missing:\n" + "\n".join(missing))

    final_data = load_json(paths["final_data"])
    activity_data = load_json(paths["activity_data"])
    portable_data = load_json(paths["portable_data"])
    for path, data in (
        (paths["final_data"], final_data),
        (paths["activity_data"], activity_data),
        (paths["portable_data"], portable_data),
    ):
        assert_content_version(path, data)

    final_meta = final_data.get("meta") or {}
    deterministic_time = str(final_meta.get("generatedAt") or "")
    if not deterministic_time:
        raise ValueError("final report data has no deterministic meta.generatedAt")

    video_index = load_json(paths["video_index"])
    if video_index.get("reportVersion") != DATA_VERSION:
        raise ValueError(f"process-video-index reportVersion is not frozen data version {DATA_VERSION}")
    video_summary = video_index.get("summary") or {}
    if video_summary.get("fileCount") != 8 or video_summary.get("totalBytes") != 7_399_913_834:
        raise ValueError("process-video-index summary is not the confirmed 8-file/7,399,913,834-byte set")
    video_publication = video_index.get("publication") or {}
    if video_publication.get("included") is not False or not video_publication.get("requestUrl"):
        raise ValueError("process-video-index must declare non-public status and a request URL")

    official_result_ids = ["standalone_equalTask", "standalone_practical"]
    diagnostic_result_ids = ["firstOrigin_equalTask", "firstOrigin_practical"]
    ranking_ids = set((final_data.get("rankings") or {}).keys())
    missing_ranking_ids = [
        result_id
        for result_id in official_result_ids + diagnostic_result_ids
        if result_id not in ranking_ids
    ]
    if missing_ranking_ids:
        raise ValueError(f"final report data is missing ranking results: {missing_ranking_ids}")

    source_html_descriptor = file_descriptor(paths["source_html"])
    portable_html_descriptor = file_descriptor(paths["portable_html"])
    activity_descriptor = file_descriptor(paths["activity_data"])
    portable_data_descriptor = file_descriptor(paths["portable_data"])
    final_data_descriptor = file_descriptor(paths["final_data"])
    video_descriptor = file_descriptor(paths["video_index"])

    summary = deepcopy(load_json(paths["summary"]))
    summary.update(
        {
            "version": REPORT_VERSION,
            "compatibilityFilenameVersion": COMPATIBILITY_FILENAME_VERSION,
            "path": "report/source-self-contained-v4.5.html",
            **source_html_descriptor,
            "mediaTotal": 710,
            "embeddedMedia": 710,
            "externalMedia": 0,
            "deduplicatedMediaReferences": 3,
            "missingMedia": 0,
            "reportCounts": report_counts(final_data),
            "dataFiles": {
                "final": {
                    "path": "report/release-v4.5/report_v4.5_final.json",
                    **final_data_descriptor,
                },
                "activity": {
                    "path": "report/activity-report-data-v4.5.json",
                    **activity_descriptor,
                },
                "portable": {
                    "path": "report/portable-report-data-v4.5.json",
                    **portable_data_descriptor,
                },
            },
            "processVideoIndex": {
                "path": "manifests/process-video-index.json",
                **video_descriptor,
                "fileCount": 8,
                "totalBytes": 7_399_913_834,
                "videosIncludedInRepository": 0,
                "publicAvailability": "hash_index_only_videos_withheld_by_owner",
                "requestUrl": str(video_publication["requestUrl"]),
            },
            "rankingPublication": {
                "officialResultIds": official_result_ids,
                "diagnosticResultIds": diagnostic_result_ids,
                "artifactPointEstimatesChanged": False,
            },
            "changeScope": (
                "v4.5.2仅升级出版物级视觉系统、执行摘要、导航、表格、弹窗、"
                "打印与无障碍交互；沿用v4.5.1冻结数据，30件终稿点估计及排名未改变。"
            ),
        }
    )
    portable_build = deepcopy(summary.get("portablePagesBuild") or {})
    portable_build.update(
        {
            "path": f"../../../../{PORTABLE_REPORT_NAME}",
            **portable_html_descriptor,
            "mediaTotal": 710,
            "embeddedMedia": 0,
            "externalMedia": 710,
            "deduplicatedMediaReferences": 3,
            "missingMedia": 0,
        }
    )
    summary["portablePagesBuild"] = portable_build
    artifact_access = deepcopy(summary.get("artifactAccess") or {})
    artifact_access["publishedAssetHeadChecks"] = (
        "carried_forward_30_of_30_from_prior_release; asset paths unchanged"
    )
    summary["artifactAccess"] = artifact_access
    desktop_experience = deepcopy(summary.get("desktopExperience") or {})
    desktop_experience["browserValidation"] = (
        "v4.5.2_runtime_and_responsive_checks_passed; print_smoke_passed"
    )
    summary["desktopExperience"] = desktop_experience
    summary_bytes = json_bytes(summary)

    release_manifest = deepcopy(load_json(paths["release_manifest"]))
    release_manifest.update(
        {
            "version": REPORT_VERSION,
            "compatibilityFilenameVersion": COMPATIBILITY_FILENAME_VERSION,
            "status": "v452_release_files_finalized",
            "finalizedAt": deterministic_time,
            "publicationMode": "single_version",
            "compatibilityNote": (
                "展示版本为v4.5.2，冻结评分数据版本为v4.5.1；为保持既有GitHub Pages与证据引用稳定，"
                "内部目录及文件名继续使用release-v4.5和*-v4.5.*。"
            ),
            "active": {
                "portableHtml": f"../../../../{PORTABLE_REPORT_NAME}",
                "sourceSelfContained": "../source-self-contained-v4.5.html",
                "activityData": "../activity-report-data-v4.5.json",
                "portableData": "../portable-report-data-v4.5.json",
                "finalData": "report_v4.5_final.json",
                "processVideoIndex": "../../manifests/process-video-index.json",
            },
            "activeHashes": {
                "portableHtml": portable_html_descriptor,
                "sourceSelfContained": source_html_descriptor,
                "activityData": activity_descriptor,
                "portableData": portable_data_descriptor,
                "finalData": final_data_descriptor,
                "processVideoIndex": video_descriptor,
            },
            "provenanceNote": (
                "provenance-inputs仅保存当前报告直接引用的精确计算输入和脚本；"
                "兼容路径中的v4.5字样不是并行发布的旧版报告。"
            ),
            "historicalReferencePolicy": (
                "adjudicate_v45.py、stamp_v45.py、qa_v45.py、"
                "qa_interaction_affordance.json、qa_report_postpublication_hardened.json和"
                "recompute_summary.json仅保留为v4.5历史参考；v451脚本和QA保留为v4.5.1"
                "冻结数据依据，旧HTML哈希与浏览器QA不代表v4.5.2当前展示构建。"
            ),
            # These booleans describe the instant at which this deterministic
            # manifest is finalized; the Git commit and push happen afterwards.
            "gitCommitPerformed": False,
            "gitPushPerformed": False,
            "publicationStateNote": "清单在Git提交与推送前闭合；发布结果由tag与GitHub Release记录。",
            "presentationUpdate": {
                "scope": "研究出版与科技数据视觉系统；真实数据首屏、四榜直显、30项矩阵、可折叠固定侧栏、证据弹窗与打印版式统一升级。",
                "scoringChanged": False,
                "reportDataChanged": False,
                "reportDataChangeBoundary": "沿用v4.5.1冻结评分数据；30件点估计不变，排名、闸门、事实、证据与来源均不变。",
                "browserRuntimeRetest": "passed_v452_preview_validator_and_user_visual_review",
                "desktopSidebar": "248px_at_1440_plus_216px_at_1180_to_1439_collapsible_to_72px",
                "rankingPresentation": "two_official_plus_two_exploratory_static_panels_no_switch_controls",
                "heatmapAffordance": "30_full_cell_click_targets_with_once_only_motion_and_reduced_motion_support",
                "publishedAssetHeadChecks": "carried_forward_30_of_30_asset_paths_unchanged",
            },
        }
    )
    release_overrides = {paths["summary"]: summary_bytes}
    release_manifest["releaseFiles"] = [
        release_file_descriptor(path, release_dir, release_overrides)
        for path in release_files(release_dir, paths["release_manifest"])
    ]
    release_manifest_bytes = json_bytes(release_manifest)

    files_manifest = deepcopy(load_json(paths["files_manifest"]))
    records = files_manifest.get("files")
    if not isinstance(records, list):
        raise ValueError("files.json .files is not an array")

    # The video index is a package-generated manifest.  It is deliberately
    # covered by SHA256SUMS, not by the copied-source records in files.json.
    records = [
        item
        for item in records
        if item.get("relativePath") != "manifests/process-video-index.json"
    ]
    record_paths = [str(item.get("relativePath", "")) for item in records]
    duplicates = sorted({path for path in record_paths if record_paths.count(path) > 1})
    if duplicates:
        raise ValueError(f"duplicate files.json relativePath entries: {duplicates}")

    existing = {str(item["relativePath"]): item for item in records}
    for path in release_files(release_dir, paths["release_manifest"]):
        relative = path.relative_to(package_root).as_posix()
        if relative not in existing:
            record = new_release_record(package_root, path)
            records.append(record)
            existing[relative] = record

    generated_overrides = {
        paths["summary"]: summary_bytes,
        paths["release_manifest"]: release_manifest_bytes,
    }
    for item in records:
        relative = str(item["relativePath"])
        path = (package_root / relative).resolve()
        try:
            path.relative_to(repo)
        except ValueError as exc:
            raise ValueError(f"files.json path escapes repository: {relative}") from exc
        if not path.is_file():
            raise FileNotFoundError(f"files.json target missing: {relative}")
        content = generated_overrides.get(path)
        descriptor = bytes_descriptor(content) if content is not None else file_descriptor(path)
        item.update(descriptor)
        release_relative = (
            path.relative_to(release_dir).as_posix()
            if path.is_relative_to(release_dir)
            else None
        )
        if release_relative in HISTORICAL_V45_FILES:
            item["category"] = ["v4.5_historical_reference"]
            item["roles"] = ["v4.5历史参考；不是v4.5.2当前展示QA或构建结论"]
            item["kind"] = "historical_release_reference"
        elif release_relative and (
            "v451" in Path(release_relative).name
            or Path(release_relative).name == "report_v4.5_final.json"
        ):
            item["category"] = ["v4.5.1_frozen_data_basis"]
            item["roles"] = ["v4.5.1冻结评分数据、语义QA或复算脚本；供v4.5.2展示层沿用"]
            item["kind"] = "frozen_semantic_release_basis"
        elif release_relative:
            item["category"] = ["v4.5.2_release"]
            item["roles"] = ["v4.5.2展示层、构建、字体、配置或发布校验材料"]
            item["kind"] = "generated_release"

    files_manifest.update(
        {
            "generatedAt": deterministic_time,
            "activeVersion": REPORT_VERSION,
            "compatibilityFilenameVersion": COMPATIBILITY_FILENAME_VERSION,
            "frozenReport": {
                "relativePath": "report/source-self-contained-v4.5.html",
                **source_html_descriptor,
            },
            "portableReport": {
                "relativePath": f"../../{PORTABLE_REPORT_NAME}",
                **portable_html_descriptor,
            },
            "reportCounts": report_counts(final_data),
            "sourceAbsolutePathOccurrences": paths["final_data"].read_text(
                encoding="utf-8"
            ).count("/Users/"),
            "copiedRecordCount": len(records),
            "uniqueContentCount": len({str(item["sha256"]) for item in records}),
            "copiedBytes": sum(int(item["bytes"]) for item in records),
            "activeVersionBoundary": (
                "活动展示版本为v4.5.2，冻结评分数据版本为v4.5.1；兼容路径保留v4.5文件名。"
                "process-video-index.json属于包内生成清单，仅由SHA256SUMS覆盖。"
            ),
            "v45PackagingBoundary": (
                "历史兼容字段：基础证据包沿用v4.5目录与文件名；v4.5.2仅升级展示层，"
                "评分数据沿用v4.5.1。8段完整过程录屏仅发布哈希索引，视频本体及其余排除项"
                "不纳入仓库。"
            ),
            "inventoryScope": (
                "files.json records copied source files, HTML-extracted media payloads, "
                "packaging-time external snapshots, and reproducible release inputs. "
                "Package-generated README/manifests (including process-video-index.json) "
                "are covered by SHA256SUMS.txt instead, avoiding self-referential hashes."
            ),
            "gitCommitPerformed": False,
            "gitPushPerformed": False,
            "files": records,
        }
    )
    files_manifest_bytes = json_bytes(files_manifest)

    overrides = {
        paths["summary"]: summary_bytes,
        paths["release_manifest"]: release_manifest_bytes,
        paths["files_manifest"]: files_manifest_bytes,
    }
    physical_files = sorted(
        (path for path in package_root.rglob("*") if path.is_file() and path != paths["sums"]),
        key=lambda item: item.relative_to(package_root).as_posix(),
    )
    sums_lines: list[str] = []
    for path in physical_files:
        content = overrides.get(path)
        digest = sha256_bytes(content) if content is not None else sha256_file(path)
        sums_lines.append(f"{digest}  {path.relative_to(package_root).as_posix()}")
    sums_bytes = ("\n".join(sums_lines) + "\n").encode("utf-8")

    expected = {
        paths["summary"]: summary_bytes,
        paths["release_manifest"]: release_manifest_bytes,
        paths["files_manifest"]: files_manifest_bytes,
        paths["sums"]: sums_bytes,
    }
    details = {
        "reportVersion": REPORT_VERSION,
        "compatibilityFilenameVersion": COMPATIBILITY_FILENAME_VERSION,
        "releaseFileCount": len(release_manifest["releaseFiles"]),
        "filesManifestRecordCount": len(records),
        "sha256SumsRecordCount": len(sums_lines),
        "packagePhysicalFileCount": len(physical_files) + 1,
        "processVideoIndexInFilesManifest": any(
            item.get("relativePath") == "manifests/process-video-index.json"
            for item in records
        ),
        "targets": {
            path.relative_to(repo).as_posix(): bytes_descriptor(content)
            for path, content in expected.items()
        },
    }
    return expected, details


def compare(expected: dict[Path, bytes]) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for path, content in expected.items():
        actual = path.read_bytes() if path.is_file() else None
        if actual == content:
            continue
        differences.append(
            {
                "path": str(path),
                "actual": None if actual is None else bytes_descriptor(actual),
                "expected": bytes_descriptor(content),
            }
        )
    return differences


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        help="repository root (defaults to the root inferred from this script)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="atomically replace generated summaries/manifests; default is check-only",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="explicit alias for the default read-only consistency check",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    repo = resolve_repo(args.repo)
    expected, details = build_expected(repo)
    differences = compare(expected)
    if args.write:
        for path, content in expected.items():
            atomic_write(path, content)
        # Recompute from disk to prove that the just-written graph is closed and
        # deterministic rather than merely trusting the pre-write calculation.
        second_expected, second_details = build_expected(repo)
        residual = compare(second_expected)
        if residual:
            print(
                json.dumps(
                    {
                        "status": "failed_after_write",
                        "differences": residual,
                        "details": second_details,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1
        print(json.dumps({"status": "written_and_verified", **second_details}, ensure_ascii=False, indent=2))
        return 0

    if differences:
        print(
            json.dumps(
                {"status": "out_of_date", "differences": differences, "details": details},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps({"status": "verified", **details}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
