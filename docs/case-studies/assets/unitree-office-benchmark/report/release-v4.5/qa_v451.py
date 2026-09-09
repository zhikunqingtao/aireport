#!/usr/bin/env python3
"""Deterministic semantic QA for the v4.5.1 disclosure-only release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
DEFAULT_FILES = (
    HERE / "report_v4.5_final.json",
    REPORT_DIR / "activity-report-data-v4.5.json",
    REPORT_DIR / "portable-report-data-v4.5.json",
)
OFFICIAL = {"standalone_equalTask", "standalone_practical"}
DIAGNOSTIC = {"firstOrigin_equalTask", "firstOrigin_practical"}
ALL_RANKINGS = OFFICIAL | DIAGNOSTIC
EXPECTED_CLASS_COUNTS = {"mechanical": 9, "mixed_anchored_judgment": 36, "expert_judgment": 12}
EXPECTED_CLASS_WEIGHTS = {"mechanical": 98.0, "mixed_anchored_judgment": 353.0, "expert_judgment": 149.0}
EXPECTED_DECLARED_JUDGMENT_WEIGHTS = {"excel": 39.0, "word": 85.0, "ppt": 78.0, "image": 100.0, "ink": 100.0, "html": 100.0}
EXPECTED_EFFECTIVE_SENSITIVITY_WEIGHTS = {"excel": 39.0, "word": 60.0, "ppt": 53.0, "image": 75.0, "ink": 75.0, "html": 75.0}
ARTIFACT_SCORE_FINGERPRINT = "78c230a328e351f7728da6250399e1ffb16b4330c8bb7b4570054da9626057e8"
RANKING_SCORE_FINGERPRINT = "d4080cd5d8342dc4db388fe5f3b4b2674affe7aaca4ee37c28122686fe2e4ecb"
CRITERION_SCORE_LEDGER_FINGERPRINT = "69e20053543f74551f6675a91a8d84828ac30494a2b366a4263cf9cfc0f346c4"
RANKING_DETAIL_LEDGER_FINGERPRINT = "657788bc6d348aea8fc0a646d502b6d1a69ebaf95c0491c381126ef3a9cd144b"
SCORE_IMPACT_LEDGER_FINGERPRINT = "998500bed65dbf39824480654ec36d254e4844d6e2254a9b83a230e146636385"
CANONICAL_G2_RULE = "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL"
PROCESS_VIDEO_MANIFEST_URL = "https://zhikunqingtao.github.io/aireport/case-studies/assets/unitree-office-benchmark/manifests/process-video-index.json"
SENSITIVITY_CLASSES = {
    "mixed_anchored_judgment",
    "expert_judgment",
    "single_reviewer_anchored_judgment",
}
QA_TIMESTAMPS = {
    "candidate": "2026-09-09T12:30:00+08:00",
    "final": "2026-09-09T12:40:00+08:00",
}
PORTABLE_EQUAL_SUBTREES = (
    "criteriaDefinitions",
    "rankings",
    "rankingPerspectives",
    "scoreSensitivity",
    "sensitivity",
    "methodology",
    "testProtocol",
    "deliveryGates",
    "propagationStatus",
)


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    raise ValueError(f"cannot locate repository root above {start}")


REPO_ROOT = find_repo_root(HERE)


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def canonical_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, value: dict) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.fchmod(fd, 0o644)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def fail(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def criterion_definitions(data: dict) -> tuple[dict[str, dict], dict[str, str]]:
    definitions: dict[str, dict] = {}
    kind_by_criterion: dict[str, str] = {}
    for kind, raw_definitions in data["criteriaDefinitions"].items():
        items = raw_definitions.get("criteria", []) if isinstance(raw_definitions, dict) else raw_definitions
        for definition in items:
            definitions[definition["id"]] = definition
            kind_by_criterion[definition["id"]] = kind
    return definitions, kind_by_criterion


def artifact_score_map(data: dict, root: str = "qualityScores") -> dict:
    return {
        key: round(float(value["qualityScore"]), 6)
        for key, value in sorted(data[root]["artifacts"].items())
    }


def criterion_score_ledger(data: dict, root: str = "qualityScores") -> dict:
    return {
        artifact_id: {
            "qualityScore": record["qualityScore"],
            "criterionScores": [
                {
                    "criterionId": row["criterionId"],
                    "weighted": row["weighted"],
                    "rating": row.get("rating"),
                }
                for row in record["criterionScores"]
            ],
        }
        for artifact_id, record in sorted(data[root]["artifacts"].items())
    }


def ranking_score_map(data: dict) -> dict:
    return {
        ranking_id: [(row["tool"], round(float(row["score"]), 6)) for row in data["rankings"][ranking_id]["rows"]]
        for ranking_id in sorted(data["rankings"])
    }


def ranking_detail_ledger(data: dict) -> dict:
    return {
        ranking_id: [
            {"tool": row["tool"], "score": row["score"], "taskScores": row.get("taskScores")}
            for row in data["rankings"][ranking_id]["rows"]
        ]
        for ranking_id in sorted(data["rankings"])
    }


def score_impact_ledger(data: dict) -> list:
    return sorted(
        (
            row["artifactId"],
            row["criterionId"],
            row["maximumPoints"],
            row["standaloneEarnedPoints"],
            row["standaloneDelta"],
            row["firstOriginDelta"],
            row["lineageRole"],
        )
        for row in data["scoreImpacts"]
    )


def calculated_classification(data: dict) -> tuple[dict, dict, dict]:
    definitions, kind_by_criterion = criterion_definitions(data)
    counts: Counter = Counter()
    weights: Counter = Counter()
    declared_by_kind: Counter = Counter()
    for criterion_id, definition in definitions.items():
        assessment_class = definition["assessmentClass"]
        weight = float(definition["weight"])
        counts[assessment_class] += 1
        weights[assessment_class] += weight
        if assessment_class != "mechanical":
            declared_by_kind[kind_by_criterion[criterion_id]] += weight
    kinds = data["meta"]["kinds"]
    return (
        {key: counts[key] for key in EXPECTED_CLASS_COUNTS},
        {key: float(weights[key]) for key in EXPECTED_CLASS_WEIGHTS},
        {kind: float(declared_by_kind[kind]) for kind in kinds},
    )


def calculated_effective_weights(data: dict) -> dict:
    definitions, kind_by_criterion = criterion_definitions(data)
    kinds = data["meta"]["kinds"]
    per_artifact: dict[str, dict[str, set[str]]] = {}
    for artifact_id, score in data["qualityScores"]["artifacts"].items():
        eligible: dict[str, set[str]] = {kind: set() for kind in kinds}
        for row in score["criterionScores"]:
            criterion_id = row["criterionId"]
            effective_class = row.get("assessmentClassApplied") or definitions[criterion_id]["assessmentClass"]
            if effective_class in SENSITIVITY_CLASSES:
                eligible[kind_by_criterion[criterion_id]].add(criterion_id)
        per_artifact[artifact_id] = eligible

    effective: dict[str, float] = {}
    for kind in kinds:
        observed_sets = {frozenset(by_kind[kind]) for by_kind in per_artifact.values() if by_kind[kind]}
        if len(observed_sets) != 1:
            raise ValueError(f"effective sensitivity criteria differ across artifacts for {kind}")
        criterion_ids = next(iter(observed_sets))
        effective[kind] = float(sum(float(definitions[criterion_id]["weight"]) for criterion_id in criterion_ids))
    return effective


def recompute_local_audit(data: dict, ranking: dict, tool: str) -> dict:
    definitions, _ = criterion_definitions(data)
    impacts = {(row["artifactId"], row["criterionId"]): row for row in data["scoreImpacts"]}
    artifacts = {(row["tool"], row["kind"]): row["id"] for row in data["artifacts"]}
    components = []
    rating_step = float(data["scoreSensitivity"]["ratingStep0To5"])
    for kind, task_weight_raw in ranking["weights"].items():
        task_weight = float(task_weight_raw)
        artifact_id = artifacts[(tool, kind)]
        score = data["qualityScores"]["artifacts"][artifact_id]
        for criterion_score in score["criterionScores"]:
            criterion_id = criterion_score["criterionId"]
            definition = definitions[criterion_id]
            effective_class = criterion_score.get("assessmentClassApplied") or definition["assessmentClass"]
            if effective_class not in SENSITIVITY_CLASSES:
                continue
            maximum = float(definition["weight"])
            earned = float(criterion_score["weighted"])
            if ranking["perspective"] == "firstOrigin":
                impact = impacts.get((artifact_id, criterion_id))
                if impact is not None:
                    earned = float(impact["maximumPoints"]) + float(impact["firstOriginDelta"])
            step_points = maximum * rating_step / 5.0
            down = min(max(earned, 0.0), step_points) * task_weight
            up = min(max(maximum - earned, 0.0), step_points) * task_weight
            components.append(
                {
                    "artifactId": artifact_id,
                    "criterionId": criterion_id,
                    "effectiveAssessmentClass": effective_class,
                    "criterionPointStep": round(step_points, 6),
                    "taskWeight": task_weight,
                    "downwardRankingMovement": round(down, 6),
                    "upwardRankingMovement": round(up, 6),
                }
            )
    if not components:
        raise ValueError(f"no eligible sensitivity criteria for {ranking['id']}/{tool}")
    max_down = max(components, key=lambda item: item["downwardRankingMovement"])
    max_up = max(components, key=lambda item: item["upwardRankingMovement"])
    return {
        "eligibleCriterionCount": len(components),
        "components": components,
        "maxDownwardMovement": max_down["downwardRankingMovement"],
        "maxUpwardMovement": max_up["upwardRankingMovement"],
        "maxDownwardScenario": max_down,
        "maxUpwardScenario": max_up,
        "jointAllDownwardExtreme": round(sum(item["downwardRankingMovement"] for item in components), 6),
        "jointAllUpwardExtreme": round(sum(item["upwardRankingMovement"] for item in components), 6),
        "jointExtremeUsedForPublishedRange": False,
    }


def verify_sensitivity(data: dict, failures: list[str]) -> None:
    sensitivity_modes = data.get("scoreSensitivity", {}).get("modes", {})
    fail(set(sensitivity_modes) == ALL_RANKINGS, "sensitivity modes do not cover all four views", failures)
    for ranking_id in sorted(ALL_RANKINGS):
        ranking = data["rankings"][ranking_id]
        audits = {row["tool"]: recompute_local_audit(data, ranking, row["tool"]) for row in ranking["rows"]}
        for row in ranking["rows"]:
            audit = audits[row["tool"]]
            fail(row.get("localSensitivityAudit") == audit, f"sensitivity component drift for {ranking_id}/{row['tool']}", failures)
            score = float(row["score"])
            expected_lower = round(max(0.0, score - float(audit["maxDownwardMovement"])), 2)
            expected_upper = round(min(100.0, score + float(audit["maxUpwardMovement"])), 2)
            fail(row.get("reviewResolutionLower") == expected_lower, f"lower sensitivity bound drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("reviewResolutionUpper") == expected_upper, f"upper sensitivity bound drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("downwardOneStepMovement") == round(float(audit["maxDownwardMovement"]), 2), f"downward step drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("upwardOneStepMovement") == round(float(audit["maxUpwardMovement"]), 2), f"upward step drift for {ranking_id}/{row['tool']}", failures)

        baseline = {row["tool"]: float(row["score"]) for row in ranking["rows"]}
        scenarios = [baseline]
        for changed in ranking["rows"]:
            for component in audits[changed["tool"]]["components"]:
                for direction, movement in (
                    ("down", component["downwardRankingMovement"]),
                    ("up", component["upwardRankingMovement"]),
                ):
                    scenario = dict(baseline)
                    scenario[changed["tool"]] += -float(movement) if direction == "down" else float(movement)
                    scenarios.append(scenario)

        expected_mode_rows = []
        for row in ranking["rows"]:
            best_ranks = []
            worst_ranks = []
            for scenario in scenarios:
                target = scenario[row["tool"]]
                other_scores = [value for tool, value in scenario.items() if tool != row["tool"]]
                best_ranks.append(1 + sum(value > target + 1e-9 for value in other_scores))
                worst_ranks.append(1 + sum(value >= target - 1e-9 for value in other_scores))
            possible_best = min(best_ranks)
            possible_worst = max(worst_ranks)
            fail(row.get("possibleBestRank") == possible_best, f"possible best rank drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("possibleWorstRank") == possible_worst, f"possible worst rank drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("possibleBestPointOrder") == possible_best, f"possible best point order drift for {ranking_id}/{row['tool']}", failures)
            fail(row.get("possibleWorstPointOrder") == possible_worst, f"possible worst point order drift for {ranking_id}/{row['tool']}", failures)
            expected_mode_rows.append(
                {
                    "tool": row["tool"],
                    "score": row["score"],
                    "judgmentSensitivityLower": row["reviewResolutionLower"],
                    "judgmentSensitivityUpper": row["reviewResolutionUpper"],
                    "downwardOneStepMovement": row["downwardOneStepMovement"],
                    "upwardOneStepMovement": row["upwardOneStepMovement"],
                    "possibleBestPointOrder": possible_best,
                    "possibleWorstPointOrder": possible_worst,
                    "nearScoreGroup": row.get("nearScoreGroup"),
                    "localSensitivityAudit": audits[row["tool"]],
                }
            )
        expected_role = "exploratory_noncausal_diagnostic" if ranking_id in DIAGNOSTIC else "official_fixed_sample_ranking_after_qa"
        mode = sensitivity_modes.get(ranking_id, {})
        fail(mode.get("rankingRole") == expected_role, f"sensitivity ranking role drift for {ranking_id}", failures)
        fail(mode.get("rows") == expected_mode_rows, f"sensitivity mode row drift for {ranking_id}", failures)

    mirrored_modes = data.get("sensitivity", {}).get("singleRaterLocalStepV451", {}).get("modes")
    fail(mirrored_modes == sensitivity_modes, "top-level sensitivity mode mirror drift", failures)


def inspect(path: Path, phase: str) -> tuple[dict, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    failures: list[str] = []
    meta = data.get("meta", {})
    fail(meta.get("schemaVersion") == "4.5.1", "meta.schemaVersion is not 4.5.1", failures)
    fail(meta.get("dataVersion") == "4.5.1", "meta.dataVersion is not 4.5.1", failures)
    fail(meta.get("presentationVersion") == "4.5.1", "meta.presentationVersion is not 4.5.1", failures)
    expected_meta_status = "candidate_v451_pending_qa" if phase == "candidate" else "final_v451_offline_qa_passed"
    expected_publication_status = "candidate_v451_pending_qa" if phase == "candidate" else "published_v451_after_qa"
    fail(meta.get("status") == expected_meta_status, f"meta.status is not {expected_meta_status}", failures)
    fail(meta.get("publicationStatus") == expected_publication_status, f"meta.publicationStatus is not {expected_publication_status}", failures)
    fail(bool(meta.get("reviewerDisclosure")), "reviewer disclosure is missing", failures)

    quality_score_map = artifact_score_map(data, "qualityScores")
    score_map = artifact_score_map(data, "scores")
    fail(len(quality_score_map) == 30, f"expected 30 artifact scores, found {len(quality_score_map)}", failures)
    fail(canonical_hash(quality_score_map) == ARTIFACT_SCORE_FINGERPRINT, "one or more frozen quality-score point estimates changed", failures)
    fail(canonical_hash(score_map) == ARTIFACT_SCORE_FINGERPRINT, "one or more frozen score-mirror point estimates changed", failures)
    quality_ledger = criterion_score_ledger(data, "qualityScores")
    score_ledger = criterion_score_ledger(data, "scores")
    fail(canonical_hash(quality_ledger) == CRITERION_SCORE_LEDGER_FINGERPRINT, "quality-score criterion ledger changed", failures)
    fail(canonical_hash(score_ledger) == CRITERION_SCORE_LEDGER_FINGERPRINT, "score-mirror criterion ledger changed", failures)
    fail(data["qualityScores"]["artifacts"] == data["scores"]["artifacts"], "qualityScores/scores artifact mirrors differ", failures)

    ranking_map = ranking_score_map(data)
    ranking_details = ranking_detail_ledger(data)
    fail(set(ranking_map) == ALL_RANKINGS, "ranking set is not the expected four views", failures)
    fail(canonical_hash(ranking_map) == RANKING_SCORE_FINGERPRINT, "one or more frozen ranking point estimates changed", failures)
    fail(canonical_hash(ranking_details) == RANKING_DETAIL_LEDGER_FINGERPRINT, "ranking task-score ledger changed", failures)
    impact_ledger = score_impact_ledger(data)
    fail(canonical_hash(impact_ledger) == SCORE_IMPACT_LEDGER_FINGERPRINT, "score-impact ledger changed", failures)

    root = data.get("rankingPerspectives", {})
    expected_official = set() if phase == "candidate" else OFFICIAL
    expected_candidates = OFFICIAL if phase == "candidate" else set()
    fail(root.get("status") == expected_meta_status, "ranking-perspective status is incorrect", failures)
    fail(set(root.get("officialResultIds", [])) == expected_official, "official ranking IDs are incorrect", failures)
    fail(set(root.get("diagnosticResultIds", [])) == DIAGNOSTIC, "diagnostic ranking IDs are incorrect", failures)
    fail(set(root.get("candidateResultIds", [])) == expected_candidates, "candidate ranking IDs are incorrect", failures)
    for ranking_id, ranking in data["rankings"].items():
        is_diagnostic = ranking_id in DIAGNOSTIC
        expected_is_official = phase == "final" and not is_diagnostic
        expected_status = (
            "candidate_v451_pending_qa"
            if phase == "candidate"
            else ("final_v451_exploratory_diagnostic" if is_diagnostic else "final_v451_offline_qa_passed")
        )
        fail(ranking.get("status") == expected_status, f"{ranking_id} status is incorrect", failures)
        fail(ranking.get("isOfficial") is expected_is_official, f"{ranking_id} official flag is incorrect", failures)
        fail(
            ranking.get("publicationRole") == (
                "exploratory_noncausal_diagnostic"
                if is_diagnostic
                else ("official_candidate_fixed_sample_ranking" if phase == "candidate" else "official_fixed_sample_ranking")
            ),
            f"{ranking_id} publication role is incorrect",
            failures,
        )
        fail(root.get("results", {}).get(ranking_id) == ranking, f"nested ranking drift for {ranking_id}", failures)

    expected_score_status = "candidate_v451_point_estimates_frozen" if phase == "candidate" else "final_v451_point_estimates_frozen"
    for score_root_name in ("qualityScores", "scores"):
        score_root = data[score_root_name]
        fail(score_root.get("status") == expected_score_status, f"{score_root_name}.status is stale", failures)
        fail(
            all(record.get("scoreStatus") == expected_score_status for record in score_root.get("artifacts", {}).values()),
            f"{score_root_name} artifact scoreStatus drift",
            failures,
        )

    class_counts, class_weights, declared_weights = calculated_classification(data)
    fail(class_counts == EXPECTED_CLASS_COUNTS, "assessment-class definition counts are incorrect", failures)
    fail(class_weights == EXPECTED_CLASS_WEIGHTS, "assessment-class definition weights are incorrect", failures)
    fail(declared_weights == EXPECTED_DECLARED_JUDGMENT_WEIGHTS, "declared definition weights by artifact kind are incorrect", failures)
    classes = data.get("contentInventory", {}).get("assessmentClasses", {})
    fail(classes.get("criterionCount") == class_counts, "assessment-class criterion-count summary is stale", failures)
    fail(classes.get("aggregateWeightAcrossSixRubrics") == class_weights, "assessment-class weight summary is stale", failures)
    fail(classes.get("judgmentWeightByArtifactKind") == declared_weights, "declared judgment-weight summary is stale", failures)
    effective_weights = calculated_effective_weights(data)
    score_sensitivity = data.get("scoreSensitivity", {})
    fail(score_sensitivity.get("declaredJudgmentWeightsByArtifactKind") == declared_weights, "declared sensitivity classification weights are stale", failures)
    fail(effective_weights == EXPECTED_EFFECTIVE_SENSITIVITY_WEIGHTS, "effective sensitivity criteria or weights are incorrect", failures)
    fail(score_sensitivity.get("effectiveSensitivityWeightsByArtifactKind") == effective_weights, "effective sensitivity weight summary is stale", failures)
    fail(score_sensitivity.get("classifiedJudgmentWeightsByArtifactKind") == effective_weights, "legacy sensitivity weight field is stale", failures)
    try:
        verify_sensitivity(data, failures)
    except (KeyError, TypeError, ValueError) as error:
        failures.append(f"sensitivity recomputation failed: {error}")

    raw_text = path.read_text(encoding="utf-8")
    fail("G2-CORE-DIRECTION-REVERSAL" not in raw_text, "legacy G2 rule ID remains", failures)
    fail(CANONICAL_G2_RULE in raw_text, "canonical G2 rule ID is missing", failures)
    fail("report_v4.json" not in raw_text, "nonexistent report_v4.json source note remains", failures)
    post_rule = data.get("methodology", {}).get("postObservationRuleDisclosure", {})
    fail(post_rule.get("ruleId") == CANONICAL_G2_RULE and post_rule.get("preRegistered") is False, "post-observation G2 disclosure is incomplete", failures)

    process = data.get("testProtocol", {}).get("processRecording", {})
    fail(process.get("manifest") == PROCESS_VIDEO_MANIFEST_URL, "process recording manifest URL is incorrect", failures)
    fail(process.get("segmentCount") == 8, "process recording segment count is not 8", failures)
    fail(process.get("totalBytes") == 7_399_913_834, "process recording byte total is incorrect", failures)
    fail(process.get("publicAvailability") == "withheld_due_to_size", "process recording publication boundary is missing", failures)
    fail(process.get("requestUrl") == "https://github.com/zhikunqingtao/aireport/issues", "process recording request URL is incorrect", failures)
    activation_verification = next((row for row in data.get("verification", []) if row.get("id") == "verification:v451-activation"), {})
    if phase == "candidate":
        fail(not activation_verification, "candidate still contains a prior final activation record", failures)
    else:
        verification = activation_verification
        fail(verification.get("status") == "passed" and verification.get("phase") == "candidate_activation", "v4.5.1 activation verification is missing", failures)
        fail(len(str(verification.get("qaCanonicalSummarySha256", ""))) == 64, "canonical candidate-QA digest is missing", failures)

    registry = data.get("presentation", {}).get("visualRegistry", [])
    table_numbers = [item.get("number") for item in registry if item.get("type") == "table" and item.get("number")]
    duplicates = sorted({number for number in table_numbers if table_numbers.count(number) > 1})
    fail(not duplicates, f"duplicate publication table numbers: {duplicates}", failures)
    source_notes = [item.get("sourceNote", "") for item in registry]
    fail(not any("report_v4.json" in note for note in source_notes), "visual registry references nonexistent report_v4.json", failures)

    result = {
        "path": repo_relative(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "passed" if not failures else "failed",
        "checks": {
            "artifactPointEstimateCount": len(quality_score_map),
            "artifactPointEstimateFingerprint": canonical_hash(quality_score_map),
            "criterionScoreLedgerFingerprint": canonical_hash(quality_ledger),
            "rankingPointEstimateFingerprint": canonical_hash(ranking_map),
            "rankingDetailLedgerFingerprint": canonical_hash(ranking_details),
            "scoreImpactLedgerFingerprint": canonical_hash(impact_ledger),
            "scoreMirrorsEqual": data["qualityScores"]["artifacts"] == data["scores"]["artifacts"],
            "officialRankings": sorted(OFFICIAL),
            "exploratoryDiagnostics": sorted(DIAGNOSTIC),
            "assessmentClassCounts": class_counts,
            "assessmentClassWeights": class_weights,
            "declaredJudgmentWeights": declared_weights,
            "effectiveSensitivityWeights": effective_weights,
            "sensitivityModes": sorted(score_sensitivity.get("modes", {})),
            "processVideoSegments": process.get("segmentCount"),
            "processVideoBytes": process.get("totalBytes"),
        },
        "failures": failures,
    }
    return result, data


def cross_file_checks(paths: list[Path], data_by_path: dict[str, dict]) -> tuple[list[dict], list[str]]:
    checks: list[dict] = []
    failures: list[str] = []

    def check(name: str, condition: bool, detail: str) -> None:
        passed = bool(condition)
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            failures.append(f"{name}: {detail}")

    by_name = {path.name: path for path in paths}
    required_names = {"report_v4.5_final.json", "activity-report-data-v4.5.json", "portable-report-data-v4.5.json"}
    check("release-files:expected-three", set(by_name) == required_names, f"found={sorted(by_name)}")
    if set(by_name) != required_names:
        return checks, failures

    full_path = by_name["report_v4.5_final.json"]
    activity_path = by_name["activity-report-data-v4.5.json"]
    portable_path = by_name["portable-report-data-v4.5.json"]
    full = data_by_path[repo_relative(full_path)]
    activity = data_by_path[repo_relative(activity_path)]
    portable = data_by_path[repo_relative(portable_path)]

    check("release-files:full-activity-byte-identical", full_path.read_bytes() == activity_path.read_bytes(), "full and activity JSON must be exact mirrors")
    for key in PORTABLE_EQUAL_SUBTREES:
        check(f"portable-projection:{key}", portable.get(key) == full.get(key), "portable semantic subtree must equal full source")
    for root in ("qualityScores", "scores"):
        check(
            f"portable-projection:{root}-criterion-ledger",
            criterion_score_ledger(portable, root) == criterion_score_ledger(full, root),
            "portable paths may differ, scoring values may not",
        )
    check("portable-projection:score-impacts", score_impact_ledger(portable) == score_impact_ledger(full), "score-impact values must be identical")
    meta_fields = (
        "schemaVersion",
        "scoringVersion",
        "dataVersion",
        "presentationVersion",
        "version",
        "generatedAt",
        "status",
        "publicationStatus",
        "scoringNote",
        "reviewerDisclosure",
    )
    full_meta = {key: full.get("meta", {}).get(key) for key in meta_fields}
    portable_meta = {key: portable.get("meta", {}).get(key) for key in meta_fields}
    check("portable-projection:release-metadata", portable_meta == full_meta, "portable release metadata must match full source")
    portable_text = portable_path.read_text(encoding="utf-8")
    check("portable-hygiene:no-absolute-user-path", "/Users/" not in portable_text, "portable JSON must not contain macOS user paths")
    check("portable-hygiene:no-file-uri", "file://" not in portable_text, "portable JSON must not contain file URIs")
    check(
        "portable-hygiene:publication-variant",
        portable.get("meta", {}).get("publicationVariant") == "github_portable_v4.5.1",
        "portable publication variant must identify v4.5.1",
    )
    return checks, failures


def canonical_qa_summary(output: dict) -> dict:
    """Return the stable, release-binding portion of a QA report."""
    results = [
        {
            "path": result["path"],
            "sha256": result["sha256"],
            "status": result["status"],
            "checks": result["checks"],
            "failures": result["failures"],
        }
        for result in sorted(output.get("results", []), key=lambda item: item["path"])
    ]
    return {
        "schemaVersion": output.get("schemaVersion"),
        "phase": output.get("phase"),
        "status": output.get("status"),
        "results": results,
        "crossFileChecks": sorted(output.get("crossFileChecks", []), key=lambda item: item["name"]),
        "crossFileFailures": sorted(output.get("crossFileFailures", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=list(DEFAULT_FILES))
    parser.add_argument("--out", type=Path, default=HERE / "qa_v451.json")
    parser.add_argument("--phase", choices=("candidate", "final"), default="final")
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths]
    inspected = [inspect(path, args.phase) for path in paths]
    results = [item[0] for item in inspected]
    data_by_path = {result["path"]: data for result, data in inspected}
    cross_checks, cross_failures = cross_file_checks(paths, data_by_path)
    output = {
        "schemaVersion": "qa-v4.5.1-2.0",
        "generatedAt": QA_TIMESTAMPS[args.phase],
        "phase": args.phase,
        "status": "passed" if all(result["status"] == "passed" for result in results) and not cross_failures else "failed",
        "results": results,
        "crossFileChecks": cross_checks,
        "crossFileFailures": cross_failures,
    }
    output["canonicalSummarySha256"] = canonical_hash(canonical_qa_summary(output))
    atomic_write_json(args.out.resolve(), output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if output["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
