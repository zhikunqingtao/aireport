#!/usr/bin/env python3
"""Build and verify the Pages/self-contained report pair as one release unit.

The default mode is a dry run: both variants are built twice in temporary
directories, checked for deterministic bytes and semantic equivalence, and
then discarded. Pass ``--write`` only after review to atomically replace the
two published HTML files. This presentation-only workflow never invokes the
revision or stamping scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

import build_report_v4 as report_builder


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[5]
REPORT_DIR = HERE.parent
CASE_DIR = REPO_ROOT / "docs" / "case-studies"
FINAL_DATA = HERE / "report_v4.5_final.json"
PORTABLE_DATA = REPORT_DIR / "portable-report-data-v4.5.json"
PATH_MAP = HERE.parents[1] / "manifests" / "path-map.json"
PORTABLE_TARGET = CASE_DIR / "AI办公工具对比测评_宇树科技_截至2026-08-30.html"
SELF_CONTAINED_TARGET = REPORT_DIR / "source-self-contained-v4.5.html"
EXPECTED_MEDIA = 710
ARTIFACT_SCORE_FINGERPRINT = "78c230a328e351f7728da6250399e1ffb16b4330c8bb7b4570054da9626057e8"
EXPECTED_COUNTS = {
    "artifacts": 30,
    "scenarioRuns": 180,
    "scenarioRecords": 202,
    "coverageItems": 324,
    "findings": 200,
    "evidence": 741,
    "media": 710,
    "facts": 32,
    "sources": 11,
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def descriptor(path: Path) -> dict:
    payload = path.read_bytes()
    return {"bytes": len(payload), "sha256": sha256_bytes(payload)}


def verify_frozen_inputs() -> str:
    data = report_builder.load_object(FINAL_DATA, "final report data")
    quality = data.get("qualityScores", {}).get("artifacts", {})
    mirror = data.get("scores", {}).get("artifacts", {})
    score_map = {
        artifact_id: round(float(record["qualityScore"]), 6)
        for artifact_id, record in sorted(quality.items())
    }
    score_fingerprint = report_builder.canonical_json_sha256(score_map)
    failures = []
    if len(score_map) != EXPECTED_COUNTS["artifacts"]:
        failures.append(f"artifact scores={len(score_map)} expected 30")
    if score_fingerprint != ARTIFACT_SCORE_FINGERPRINT:
        failures.append("one or more frozen artifact point estimates changed")
    if quality != mirror:
        failures.append("qualityScores/scores artifact mirrors differ")

    inventory = data.get("contentInventory", {})
    observed = {
        "artifacts": len(data.get("artifacts", [])),
        "scenarioRuns": len(data.get("scenarioRuns", [])),
        "scenarioRecords": int(inventory.get("scenarioRecords", {}).get("count", 0)),
        "coverageItems": len(data.get("coverageItems", [])),
        "findings": len(data.get("findings", [])),
        "evidence": len(data.get("evidence", [])),
        "media": len(data.get("media", [])),
        "facts": len(data.get("facts", [])),
        "sources": len(data.get("sources", [])),
    }
    for key, expected in EXPECTED_COUNTS.items():
        if observed[key] != expected:
            failures.append(f"{key}={observed[key]} expected {expected}")
    if failures:
        raise ValueError("frozen input QA failed:\n- " + "\n- ".join(failures))
    return score_fingerprint


def build_pair(root: Path) -> tuple[dict[str, dict], dict[str, Path]]:
    outputs = {
        "portable": root / "portable.html",
        "selfContained": root / "self-contained.html",
    }
    summaries = {
        "portable": report_builder.build(
            PORTABLE_DATA,
            outputs["portable"],
            compress_report_data=True,
            ui_path=report_builder.DEFAULT_UI_PATH,
            dynamic_hero_data_path=FINAL_DATA,
            path_map_path=PATH_MAP,
        ),
        "selfContained": report_builder.build(
            FINAL_DATA,
            outputs["selfContained"],
            compress_report_data=True,
            ui_path=report_builder.DEFAULT_UI_PATH,
            dynamic_hero_data_path=FINAL_DATA,
            path_map_path=PATH_MAP,
        ),
    }
    return summaries, outputs


def verify_pair(summaries: dict[str, dict]) -> None:
    portable = summaries["portable"]
    self_contained = summaries["selfContained"]
    failures: list[str] = []

    if portable["uiSha256"] != self_contained["uiSha256"]:
        failures.append("UI configuration differs across variants")
    if portable["semanticSha256"] != self_contained["semanticSha256"]:
        failures.append("normalized report semantics differ across variants")
    if portable["mediaTotal"] != EXPECTED_MEDIA or self_contained["mediaTotal"] != EXPECTED_MEDIA:
        failures.append("media inventory is not the frozen 710-item set")
    if portable["embeddedMedia"] != 0 or portable["externalMedia"] != EXPECTED_MEDIA:
        failures.append("Pages variant does not expose all 710 media records as portable references")
    if self_contained["embeddedMedia"] != EXPECTED_MEDIA or self_contained["externalMedia"] != 0:
        failures.append("self-contained variant does not inline all 710 media records")
    if portable["missingMedia"] or self_contained["missingMedia"]:
        failures.append("one or more media records are unresolved")
    if self_contained["bytes"] > report_builder.MAX_BYTES:
        failures.append("self-contained variant exceeds the 40 MiB acceptance limit")

    if failures:
        raise ValueError("variant QA failed:\n- " + "\n- ".join(failures))


def verify_determinism(
    first_summaries: dict[str, dict],
    first_outputs: dict[str, Path],
    repeat_root: Path,
) -> None:
    repeat_summaries, repeat_outputs = build_pair(repeat_root)
    verify_pair(repeat_summaries)
    failures = []
    for key in first_outputs:
        if first_outputs[key].read_bytes() != repeat_outputs[key].read_bytes():
            failures.append(key)
        if first_summaries[key]["sha256"] != repeat_summaries[key]["sha256"]:
            failures.append(f"{key} summary")
    if failures:
        raise ValueError(f"non-deterministic variant build: {', '.join(failures)}")


def replace_group(candidates: dict[Path, Path]) -> None:
    """Stage both candidates before replacing either target; roll back on error."""
    if len({path.resolve() for path in candidates}) != len(candidates):
        raise ValueError("release targets must be unique")
    originals = {
        target.resolve(): target.read_bytes() if target.is_file() else None
        for target in candidates
    }
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for target, candidate in candidates.items():
            target = target.resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".release.tmp", dir=target.parent
            )
            staged_path = Path(temp_name)
            staged[target] = staged_path
            mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
            os.fchmod(fd, mode)
            with os.fdopen(fd, "wb") as handle:
                handle.write(candidate.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
        for target in candidates:
            target = target.resolve()
            os.replace(staged.pop(target), target)
            replaced.append(target)
        for target, candidate in candidates.items():
            if target.read_bytes() != candidate.read_bytes():
                raise OSError(f"post-replacement byte mismatch: {target}")
    except Exception:
        for target in reversed(replaced):
            original = originals[target]
            if original is None:
                target.unlink(missing_ok=True)
                continue
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".rollback.tmp", dir=target.parent
            )
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(original)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, target)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Atomically replace both published HTML files after all checks pass.",
    )
    args = parser.parse_args()
    score_fingerprint = verify_frozen_inputs()

    with tempfile.TemporaryDirectory(prefix="unitree-report-variants-") as temp_name:
        temp_root = Path(temp_name)
        summaries, outputs = build_pair(temp_root / "candidate")
        verify_pair(summaries)
        verify_determinism(summaries, outputs, temp_root / "repeat")

        targets = {
            PORTABLE_TARGET: outputs["portable"],
            SELF_CONTAINED_TARGET: outputs["selfContained"],
        }
        changed = {
            "portable": not PORTABLE_TARGET.is_file()
            or PORTABLE_TARGET.read_bytes() != outputs["portable"].read_bytes(),
            "selfContained": not SELF_CONTAINED_TARGET.is_file()
            or SELF_CONTAINED_TARGET.read_bytes() != outputs["selfContained"].read_bytes(),
        }
        if args.write:
            replace_group(targets)

        output = {
            "status": "written_and_verified" if args.write else "dry_run_passed",
            "mode": "write" if args.write else "dry-run",
            "semanticSha256": summaries["portable"]["semanticSha256"],
            "uiSha256": summaries["portable"]["uiSha256"],
            "artifactScoreFingerprint": score_fingerprint,
            "deterministic": True,
            "reviseOrStampInvoked": False,
            "wouldChange": changed,
            "variants": {
                "portable": {
                    **descriptor(outputs["portable"]),
                    "target": str(PORTABLE_TARGET.relative_to(REPO_ROOT)),
                    "media": {
                        "total": summaries["portable"]["mediaTotal"],
                        "inline": summaries["portable"]["embeddedMedia"],
                        "external": summaries["portable"]["externalMedia"],
                        "missing": summaries["portable"]["missingMedia"],
                    },
                },
                "selfContained": {
                    **descriptor(outputs["selfContained"]),
                    "target": str(SELF_CONTAINED_TARGET.relative_to(REPO_ROOT)),
                    "under40MiB": summaries["selfContained"]["bytes"] <= report_builder.MAX_BYTES,
                    "media": {
                        "total": summaries["selfContained"]["mediaTotal"],
                        "inline": summaries["selfContained"]["embeddedMedia"],
                        "external": summaries["selfContained"]["externalMedia"],
                        "missing": summaries["selfContained"]["missingMedia"],
                    },
                },
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
