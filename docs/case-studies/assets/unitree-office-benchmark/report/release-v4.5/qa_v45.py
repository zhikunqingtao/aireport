#!/usr/bin/env python3
"""Offline acceptance checks for the v4.5 symmetric reassessment."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


TOOLS = ["豆包", "千问", "Qoder", "WorkBuddy", "ZhikunCode"]
KINDS = ["excel", "word", "ppt", "image", "ink", "html"]


def close(a: float, b: float, tolerance: float = 0.011) -> bool:
    return math.isclose(float(a), float(b), abs_tol=tolerance)


def q(value: float, digits: int = 2) -> float:
    return round(float(value) + 1e-12, digits)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_embedded_report(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    match = re.search(r'<script id="report-data"[^>]*>(.*?)</script>', html, re.S)
    assert match, "missing embedded report data"
    payload = match.group(1).strip()
    if 'data-encoding="gzip-base64"' in match.group(0):
        payload = gzip.decompress(base64.b64decode(payload)).decode("utf-8")
    return json.loads(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-status", choices=["candidate", "final"], default="candidate")
    args = parser.parse_args()

    base = json.loads(args.base.read_text(encoding="utf-8"))
    report = json.loads(args.candidate.read_text(encoding="utf-8"))
    failures: list[str] = []
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            failures.append(f"{name}: {detail}")

    expected_counts = {
        "artifacts": 30,
        "scenarioRuns": len(base["scenarioRuns"]),
        "coverageItems": 324,
        "findings": 200,
        "evidence": 741,
        "media": 710,
        "facts": 32,
        "sources": 11,
    }
    for key, expected in expected_counts.items():
        check(f"count:{key}", len(report[key]) == expected, f"{len(report[key])} != {expected}")
    pairs = Counter((row["tool"], row["kind"]) for row in report["artifacts"])
    check("artifact-grid", len(pairs) == 30 and all(pairs[(tool, kind)] == 1 for tool in TOOLS for kind in KINDS), str(pairs))

    # Original artifact identity and paths are immutable across the reassessment.
    old_artifacts = {row["id"]: row for row in base["artifacts"]}
    new_artifacts = {row["id"]: row for row in report["artifacts"]}
    original_equal = set(old_artifacts) == set(new_artifacts) and all(
        old_artifacts[aid].get("original") == new_artifacts[aid].get("original")
        for aid in old_artifacts
    )
    check("artifact-originals-frozen", original_equal)

    definitions = {row["id"]: row for rows in report["criteriaDefinitions"].values() for row in rows}
    for kind, rows in report["criteriaDefinitions"].items():
        check(f"rubric-weight:{kind}", close(sum(float(row["weight"]) for row in rows), 100, 1e-9))

    # Every artifact score is the sum of its criterion points.
    for aid, score in report["scores"]["artifacts"].items():
        total = q(sum(float(row["weighted"]) for row in score["criterionScores"]), 2)
        check(f"artifact-score:{aid}", close(total, score["qualityScore"]), f"{total} vs {score['qualityScore']}")
        check(f"artifact-rubric-complete:{aid}", close(sum(definitions[row["criterionId"]]["weight"] for row in score["criterionScores"]), 100, 1e-9))

    # Publication state must be unambiguous.  A candidate cannot masquerade as
    # final, and a final can only exist after a separately recorded QA pass.
    meta_status = str(report.get("meta", {}).get("status", ""))
    score_statuses = {str(row.get("scoreStatus", "")) for row in report["scores"]["artifacts"].values()}
    ranking_statuses = {str(row.get("status", "")) for row in report["rankings"].values()}
    if args.expect_status == "candidate":
        check("publication-state:candidate-meta", "candidate" in meta_status and "final" not in meta_status, meta_status)
        check("publication-state:candidate-scores", all("candidate" in x and "final" not in x for x in score_statuses), str(score_statuses))
        check("publication-state:candidate-rankings", all("candidate" in x and "final" not in x for x in ranking_statuses), str(ranking_statuses))
        check("publication-state:no-official-results", report["rankingPerspectives"].get("officialResultIds") == [])
    else:
        check("publication-state:final-meta", meta_status == "final_v45_offline_qa_passed", meta_status)
        check("publication-state:final-scores", score_statuses == {"final_v45_offline_qa_passed"}, str(score_statuses))
        check("publication-state:final-rankings", ranking_statuses == {"final_v45_offline_qa_passed"}, str(ranking_statuses))
        check("publication-state:official-results", set(report["rankingPerspectives"].get("officialResultIds", [])) == set(report["rankings"]))

    fact_rows = [row for row in report["claimLedger"]["records"] if row.get("benchmarkScopeStatus") == "within_fixed_32_fact_universe"]
    evidence_ids = {row["id"] for row in report["evidence"]}
    finding_ids = {row["id"] for row in report["findings"]}
    claim_ids = {row["id"] for row in report["claimLedger"]["records"]}
    check("claim-ledger:unique-ids", len(claim_ids) == len(report["claimLedger"]["records"]))
    check("claim-ledger:all-locators", all(str(row.get("locator", "")).strip() for row in report["claimLedger"]["records"]))
    check("claim-ledger:all-evidence-linked", all(row.get("evidenceIds") for row in report["claimLedger"]["records"]))
    check("claim-ledger:evidence-resolves", all(eid in evidence_ids for row in report["claimLedger"]["records"] for eid in row.get("evidenceIds", [])))
    check("claim-ledger:finding-resolves", all(fid in finding_ids for row in report["claimLedger"]["records"] for fid in row.get("findingIds", [])))
    for tool in TOOLS:
        rows = [row for row in fact_rows if row["tool"] == tool]
        fact_score = q(30 * sum(float(row["factEarnedFraction"]) for row in rows) / len(rows), 2)
        source_score = q(sum(2 * sum(float(row["sourceAssessment"][key]) for key in ["identity", "priority", "locator", "actionable"]) for row in rows) / len(rows), 2)
        aid = next(row["id"] for row in report["artifacts"] if row["tool"] == tool and row["kind"] == "excel")
        criterion_map = {row["criterionId"].split(":")[-1]: row for row in report["scores"]["artifacts"][aid]["criterionScores"]}
        check(f"fact-recalc:{tool}", close(fact_score, criterion_map["external-facts"]["weighted"]), f"{fact_score}")
        check(f"source-recalc:{tool}", close(source_score, criterion_map["sources"]["weighted"]), f"{source_score}")
        for suffix in ["external-facts", "sources", "period-unit-prediction"]:
            row = criterion_map[suffix]
            sub_total = q(sum(float(item["earnedPoints"]) for item in row.get("subitemScores", [])), 2)
            check(f"atomic-subitems:{tool}:{suffix}", close(sub_total, row["weighted"]), f"{sub_total} vs {row['weighted']}")
        source_items = criterion_map["sources"].get("subitemScores", [])
        check(f"source-four-subtests:{tool}", [x.get("id") for x in source_items] == ["identity", "priority", "locator", "actionable"])
        for item in source_items:
            expected_points = q(2 * float(item["numeratorCredits"]) / float(item["denominator"]), 2)
            check(f"source-mechanical:{tool}:{item['id']}", close(expected_points, item["earnedPoints"]), f"{expected_points} vs {item['earnedPoints']}")
            check(f"source-claims-resolve:{tool}:{item['id']}", set(item.get("claimIds", [])).issubset(claim_ids))
            check(f"source-evidence-resolves:{tool}:{item['id']}", bool(item.get("evidenceIds")) and set(item["evidenceIds"]).issubset(evidence_ids))
            check(f"source-input-class:{tool}:{item['id']}", item.get("inputEvidenceClass") == "single_reviewer_coded_observation")

    # Accuracy and completeness have different denominators and may not be
    # silently blended.  The public diagnostic makes both visible.
    coverage_rows = report.get("factCoverageDiagnostics", {}).get("rows", [])
    check("fact-coverage:five-tools", len(coverage_rows) == 5 and {x["tool"] for x in coverage_rows} == set(TOOLS))
    for row in coverage_rows:
        check(f"fact-coverage:denominator:{row['tool']}", row["benchmarkFacts"] == 32 and row["claimedFacts"] + row["unclaimedFacts"] == 32)
        check(f"fact-coverage:rate:{row['tool']}", close(row["claimCoverageRate"], q(100 * row["claimedFacts"] / 32, 1), .11))
        check(f"fact-coverage:separate-criterion:{row['tool']}", row.get("requirementsCriterionId") == "criterion:excel:requirements-richness")

    # The v4.5 consistency score is a fully mechanical five-by-five grid for
    # every downstream artifact.  Only a failed subtest may lose its five points.
    expected_consistency = {
        ("WorkBuddy", "word"): 15, ("WorkBuddy", "ppt"): 15,
        ("WorkBuddy", "image"): 15, ("WorkBuddy", "ink"): 15,
        ("WorkBuddy", "html"): 15, ("Qoder", "ppt"): 20,
        ("Qoder", "html"): 20,
    }
    for tool in TOOLS:
        for kind in ["word", "ppt", "image", "ink", "html"]:
            aid = next(row["id"] for row in report["artifacts"] if row["tool"] == tool and row["kind"] == kind)
            consistency = next(row for row in report["scores"]["artifacts"][aid]["criterionScores"] if row["criterionId"].endswith("consistency"))
            subitems = consistency.get("subitemScores", [])
            check(f"consistency-five-subtests:{tool}:{kind}", len(subitems) == 5 and all(x.get("maxPoints") == 5 for x in subitems))
            check(f"consistency-binary:{tool}:{kind}", all(x.get("earnedPoints") in [0, 5] for x in subitems))
            check(f"consistency-sum:{tool}:{kind}", close(sum(x["earnedPoints"] for x in subitems), consistency["weighted"]))
            check(f"consistency-expected:{tool}:{kind}", close(consistency["weighted"], expected_consistency.get((tool, kind), 25)), str(consistency["weighted"]))
            check(f"consistency-fail-evidence:{tool}:{kind}", all(x.get("evidenceIds") and set(x["evidenceIds"]).issubset(evidence_ids) for x in subitems if x.get("status") == "fail"))

    # Qoder's safety gate is independent of the continuous loss: one symmetric
    # prepublished rule, one failed 5-point direction subtest, one page of 20.
    qoder_gate = report["deliveryGates"]["artifacts"]["artifact:qoder:ppt"]
    check("qoder-g2:code", qoder_gate.get("code") == "G2")
    check("qoder-g2:symmetric-rule", qoder_gate.get("ruleId") == "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL")
    check("qoder-g2:scope", "1/20" in qoder_gate.get("scope", ""))
    check("qoder-g2:separate-score", qoder_gate.get("scoreEffect") == 0 and "0/5" in qoder_gate.get("continuousScoreTreatment", ""))

    # WorkBuddy's two independent roots are explicit rather than a bundled
    # fifteen-point expert deduction.
    wb_word = report["scores"]["artifacts"]["artifact:workbuddy:word"]
    wb_consistency = next(x for x in wb_word["criterionScores"] if x["criterionId"].endswith("consistency"))
    failed_wb = {x["id"]: x for x in wb_consistency["subitemScores"] if x["status"] == "fail"}
    check("workbuddy-word:two-atomic-roots", set(failed_wb) == {"fact-attribute", "new-claim-cutoff"} and close(wb_consistency["weighted"], 15))
    check("workbuddy-word:distinct-findings", set(failed_wb["fact-attribute"]["findingIds"]).isdisjoint(failed_wb["new-claim-cutoff"]["findingIds"]))

    # The old-to-new bridge is exhaustive and must explain the full +19.93 for
    # ZhikunCode instead of merely stating the resulting score.
    zk_bridge = next(row for row in report["scoreRevisionsV45"] if row["artifactId"] == "artifact:zhikuncode:excel")
    bridge_sum = q(sum(float(x["delta"]) for x in zk_bridge.get("criterionBridge", [])), 2)
    check("zhikun-bridge:old-new", close(zk_bridge["oldScore"], 67.6) and close(zk_bridge["newScore"], 87.53) and close(zk_bridge["delta"], 19.93))
    check("zhikun-bridge:sum", close(bridge_sum, 19.93) and close(bridge_sum, zk_bridge.get("bridgeCheck", -1)), str(bridge_sum))
    check("zhikun-bridge:criteria", {x["criterionId"].split(":")[-1] for x in zk_bridge["criterionBridge"]} == {"external-facts", "sources", "period-unit-prediction"})

    # Qianwen's disputed additions require concrete locations at every actual
    # appearance.  Absence from the two images for three claims is recorded as
    # non-applicable, not inferred as an error.
    qianwen_claims = [x for x in report["claimLedger"]["records"] if x.get("tool") == "千问" and x.get("claimFamily") in {"patents", "speed-record", "gen3-trial", "proxy-share"}]
    check("qianwen-lineage:expected-records", len(qianwen_claims) == 14, str([(x.get('claimFamily'), x.get('artifactId')) for x in qianwen_claims]))
    check("qianwen-lineage:located-and-evidenced", all(x.get("locator") and x.get("evidenceIds") for x in qianwen_claims))
    check("qianwen-lineage:html-not-origin", all(x.get("lineageRole") != "origin" for x in qianwen_claims if x.get("artifactId") == "artifact:qianwen:html"))

    # Image readability is retained as a single-reviewer coded judgment with a
    # visible sensitivity range; it is never presented as a mechanical fact.
    image_judgment = report.get("methodology", {}).get("imageReadabilityJudgmentV45", {})
    check("image-judgment:single-reviewer", image_judgment.get("assessmentClass") == "single_reviewer_expert_judgment")
    check("image-judgment:sensitivity", image_judgment.get("sensitivityRangePoints") == [-1.5, 1.5])

    # 202 is a disclosed composite inventory, not a hidden disagreement with
    # the 180 primary scenarioRuns table.
    comp = report["contentInventory"]["scenarioRecordComposition"]
    check("scenario-composition:arithmetic", comp["primaryScenarioRuns"]["count"] == 180 and comp["supplementalScenarioRecords"]["count"] == 13 and comp["pairedImageZoneFamilies"]["count"] == 9 and comp["reportedTotal"] == 202)
    check("scenario-composition:ids", len(comp["primaryScenarioRuns"]["ids"]) == 180 and len(comp["supplementalScenarioRecords"]["ids"]) == 13 and len(comp["pairedImageZoneFamilies"]["zoneIds"]) == 9)

    check("four-rankings", set(report["rankings"]) == {"standalone_equalTask", "standalone_practical", "firstOrigin_equalTask", "firstOrigin_practical"})
    artifact_map = {row["id"]: row for row in report["artifacts"]}
    for rid, node in report["rankings"].items():
        perspective = node["perspective"]
        expected = []
        for tool in TOOLS:
            total = 0.0
            for kind, weight in node["weights"].items():
                aid = next(aid for aid, artifact in artifact_map.items() if artifact["tool"] == tool and artifact["kind"] == kind)
                score = report["scores"]["artifacts"][aid]
                value = score["qualityScore"] if perspective == "standalone" else score["firstOriginQualityScore"]
                total += float(value) * float(weight)
            expected.append((tool, q(total, 2)))
        actual = [(row["tool"], row["score"]) for row in node["rows"]]
        check(f"ranking-recalc:{rid}", sorted(expected) == sorted(actual), f"{expected} vs {actual}")

    exact_impacts = [row for row in report["scoreImpacts"] if row.get("lineageRole") == "exact_propagation"]
    check("exact-propagation-zero-first-origin", bool(exact_impacts) and all(close(row.get("firstOriginDelta", 0), 0, 1e-9) for row in exact_impacts), str([(x['id'], x.get('firstOriginDelta')) for x in exact_impacts]))
    exact_claims = [row for row in report["claimLedger"]["records"] if row.get("lineageRole") == "exact_propagation"]
    check("exact-claims-no-first-origin-use", all(not row.get("firstOriginScoreUse") for row in exact_claims))
    check("strict-lineage-diagnostic-only", report["strictExcelLineage"]["status"] == "diagnostic_only_not_in_formal_scores" and not any("strictExcelLineage" in json.dumps(row, ensure_ascii=False) for row in report["scores"]["artifacts"].values()))

    # A critical factual observation may coexist with a G0 terminal gate only
    # if the two fields are explicitly separated.  No finding may use a single
    # ambiguous generic `gate` field in v4.5.
    check("finding-gate-separation", all("terminalIndependentUseGate" in row and "chainAttributionRole" in row and "gate" not in row for row in report["findings"]))

    v45_history = report["versionHistory"][-1]
    check("no-word-reopen", v45_history.get("officeFilesReopened") is False)
    check("no-browser-retest", v45_history.get("browserEffectRetested") is False)
    check("vendor-self-review-not-evidence", v45_history.get("vendorSelfReviewUsedAsEvidence") is False)

    embedded = extract_embedded_report(args.html)
    check("html-json-version", embedded.get("meta", {}).get("presentationVersion") == "4.5")
    check("html-counts", all(len(embedded[key]) == expected for key, expected in expected_counts.items()))
    check("html-rankings-match", embedded["rankings"] == report["rankings"])
    check("html-publication-status-match", embedded.get("meta", {}).get("status") == report.get("meta", {}).get("status"))
    check("html-under-40MiB", args.html.stat().st_size <= 40 * 1024 * 1024, str(args.html.stat().st_size))
    check("html-self-contained-media", sum(bool(row.get("embedded")) for row in embedded["media"].values()) == 710)
    response_rows = embedded.get("challenges", {}).get("responses", [])
    check("html-self-review-context-not-scoring-evidence", len(response_rows) == 5 and all(row.get("v45ScoringUse") is False and row.get("v45EvidenceUse") is False for row in response_rows))
    check("html-self-review-context-images-embedded", len(response_rows) == 5 and all(row.get("screenshotEmbedded") is True and str(row.get("screenshotDataUri", "")).startswith("data:image/") for row in response_rows))

    result = {
        "status": "passed" if not failures else "failed",
        "candidateJson": str(args.candidate),
        "candidateJsonSha256": digest(args.candidate),
        "candidateHtml": str(args.html),
        "candidateHtmlSha256": digest(args.html),
        "checks": checks,
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks), "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
