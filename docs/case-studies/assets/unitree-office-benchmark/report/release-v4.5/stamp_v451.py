#!/usr/bin/env python3
"""Activate v4.5.1 after deterministic candidate QA has passed."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
DEFAULT_FILES = (
    HERE / "report_v4.5_final.json",
    REPORT_DIR / "activity-report-data-v4.5.json",
    REPORT_DIR / "portable-report-data-v4.5.json",
)
OFFICIAL = ("standalone_equalTask", "standalone_practical")
DIAGNOSTIC = ("firstOrigin_equalTask", "firstOrigin_practical")
ACTIVATED_AT = "2026-09-09T12:35:00+08:00"


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    raise ValueError(f"cannot locate repository root above {start}")


REPO_ROOT = find_repo_root(HERE)


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def serialized(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_dump_group(values: list[tuple[Path, dict]]) -> None:
    resolved = [path.resolve() for path, _ in values]
    if len(set(resolved)) != len(resolved):
        raise ValueError("activation output paths must be unique")
    originals = {path.resolve(): path.read_bytes() for path, _ in values}
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for path, value in values:
            path = path.resolve()
            fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".activation.tmp", dir=path.parent)
            os.fchmod(fd, 0o644)
            temp_path = Path(temp_name)
            staged[path] = temp_path
            with os.fdopen(fd, "wb") as handle:
                handle.write(serialized(value))
                handle.flush()
                os.fsync(handle.fileno())
        for path, _ in values:
            path = path.resolve()
            os.replace(staged.pop(path), path)
            replaced.append(path)
    except Exception:
        for path in replaced:
            fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".rollback.tmp", dir=path.parent)
            os.fchmod(fd, 0o644)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(originals[path])
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, path)
            except Exception:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass
                raise
        raise
    finally:
        for temp_path in staged.values():
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def canonical_qa_summary(qa: dict) -> dict:
    results = [
        {
            "path": result["path"],
            "sha256": result["sha256"],
            "status": result["status"],
            "checks": result["checks"],
            "failures": result["failures"],
        }
        for result in sorted(qa.get("results", []), key=lambda item: item["path"])
    ]
    return {
        "schemaVersion": qa.get("schemaVersion"),
        "phase": qa.get("phase"),
        "status": qa.get("status"),
        "results": results,
        "crossFileChecks": sorted(qa.get("crossFileChecks", []), key=lambda item: item["name"]),
        "crossFileFailures": sorted(qa.get("crossFileFailures", [])),
    }


def validate_candidate_qa(qa_path: Path, paths: list[Path]) -> tuple[dict, str]:
    qa = load(qa_path)
    if qa.get("schemaVersion") != "qa-v4.5.1-2.0":
        raise ValueError("candidate QA schema is not qa-v4.5.1-2.0")
    if qa.get("status") != "passed" or qa.get("phase") != "candidate":
        raise ValueError("candidate QA has not passed")
    if qa.get("crossFileFailures") or not all(row.get("passed") for row in qa.get("crossFileChecks", [])):
        raise ValueError("candidate cross-file QA has not passed")
    canonical_digest = canonical_hash(canonical_qa_summary(qa))
    if qa.get("canonicalSummarySha256") != canonical_digest:
        raise ValueError("candidate QA canonical digest does not match its normalized summary")

    recorded = {result["path"]: result for result in qa.get("results", [])}
    expected_paths = {repo_relative(path) for path in paths}
    if set(recorded) != expected_paths:
        raise ValueError("candidate QA result set does not exactly match activation inputs")
    for path in paths:
        result = recorded[repo_relative(path)]
        if result.get("status") != "passed" or result.get("failures"):
            raise ValueError(f"candidate QA did not pass for {repo_relative(path)}")
        if result.get("sha256") != sha256(path):
            raise ValueError(f"candidate QA fingerprint mismatch for {repo_relative(path)}")
    return qa, canonical_digest


def activate(data: dict, qa_canonical_sha256: str) -> dict:
    meta = data["meta"]
    if meta.get("status") != "candidate_v451_pending_qa":
        raise ValueError("input is not a v4.5.1 candidate")
    meta["status"] = "final_v451_offline_qa_passed"
    meta["publicationStatus"] = "published_v451_after_qa"
    meta.setdefault("ui", {}).setdefault("hero", {})["statusNote"] = "两张终稿独立使用排名为正式结果；两张首次归责结果仅作探索性非因果诊断，不用于采购名次。"

    for score_root in (data["qualityScores"], data["scores"]):
        score_root["status"] = "final_v451_point_estimates_frozen"
        for record in score_root.get("artifacts", {}).values():
            record["scoreStatus"] = "final_v451_point_estimates_frozen"

    for ranking_id in OFFICIAL:
        ranking = data["rankings"][ranking_id]
        ranking["status"] = "final_v451_offline_qa_passed"
        ranking["isOfficial"] = True
        ranking["publicationRole"] = "official_fixed_sample_ranking"
    for ranking_id in DIAGNOSTIC:
        ranking = data["rankings"][ranking_id]
        ranking["status"] = "final_v451_exploratory_diagnostic"
        ranking["isOfficial"] = False
        ranking["publicationRole"] = "exploratory_noncausal_diagnostic"

    perspectives = data["rankingPerspectives"]
    perspectives["status"] = "final_v451_offline_qa_passed"
    perspectives["officialResultIds"] = list(OFFICIAL)
    perspectives["candidateResultIds"] = []
    perspectives["diagnosticResultIds"] = list(DIAGNOSTIC)
    perspectives["results"] = {
        ranking_id: copy.deepcopy(data["rankings"][ranking_id])
        for ranking_id in OFFICIAL + DIAGNOSTIC
    }

    for row in data.get("versionHistory", []):
        if row.get("version") == "4.5.1":
            row["status"] = "active_offline_qa_passed"
            row["activatedAt"] = ACTIVATED_AT
            row["candidateQaCanonicalSummarySha256"] = qa_canonical_sha256

    verification = data.setdefault("verification", [])
    if not isinstance(verification, list):
        raise ValueError("verification must remain a list")
    verification[:] = [row for row in verification if row.get("id") != "verification:v451-activation"]
    verification.append(
        {
            "id": "verification:v451-activation",
            "item": "v4.5.1候选数据一致性、排名角色与敏感性激活",
            "status": "passed",
            "phase": "candidate_activation",
            "qaReport": "report/release-v4.5/qa_v451_candidate.json",
            "qaCanonicalSummarySha256": qa_canonical_sha256,
            "activatedAt": ACTIVATED_AT,
            "artifactPointEstimatesChanged": False,
            "officialRankingIds": list(OFFICIAL),
            "exploratoryDiagnosticIds": list(DIAGNOSTIC),
        }
    )
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=list(DEFAULT_FILES))
    parser.add_argument("--qa", type=Path, default=HERE / "qa_v451_candidate.json")
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths]
    _, qa_digest = validate_candidate_qa(args.qa.resolve(), paths)
    activated = [(path, activate(load(path), qa_digest)) for path in paths]
    atomic_dump_group(activated)
    for path in paths:
        print(f"activated {repo_relative(path)}")
    print(f"candidate QA canonical summary SHA-256: {qa_digest}")


if __name__ == "__main__":
    main()
