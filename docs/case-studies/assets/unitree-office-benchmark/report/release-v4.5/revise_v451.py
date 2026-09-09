#!/usr/bin/env python3
"""Apply the v4.5.1 consistency and disclosure revision.

This revision intentionally preserves all 30 artifact point estimates and all
four published point-order calculations.  It fixes metadata, classification,
ranking roles, and the local one-rater sensitivity calculation.
"""

from __future__ import annotations

import argparse
import copy
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
OFFICIAL_RANKINGS = ("standalone_equalTask", "standalone_practical")
DIAGNOSTIC_RANKINGS = ("firstOrigin_equalTask", "firstOrigin_practical")
ALL_RANKINGS = OFFICIAL_RANKINGS + DIAGNOSTIC_RANKINGS
CLASS_ORDER = ("mechanical", "mixed_anchored_judgment", "expert_judgment")
CANONICAL_G2_RULE = "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL"
LEGACY_G2_RULE = "G2-CORE-DIRECTION-REVERSAL"
DATA_SOURCE_LABEL = "report/release-v4.5/report_v4.5_final.json"
PROCESS_VIDEO_BYTES = 7_399_913_834
PROCESS_VIDEO_MANIFEST = "https://zhikunqingtao.github.io/aireport/case-studies/assets/unitree-office-benchmark/manifests/process-video-index.json"
REQUEST_URL = "https://github.com/zhikunqingtao/aireport/issues"
REVISION_TIMESTAMP = "2026-09-09T12:24:00+08:00"
SENSITIVITY_CLASSES = {
    "mixed_anchored_judgment",
    "expert_judgment",
    "single_reviewer_anchored_judgment",
}


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def serialized(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_dump_group(values: list[tuple[Path, dict]]) -> None:
    """Stage every candidate before replacing any input file.

    ``os.replace`` is atomic per file.  Staging all payloads first and restoring
    already replaced files on an exceptional failure gives this three-file
    release the practical all-or-nothing behaviour a directory of plain files
    can provide without changing its public paths.
    """
    resolved = [path.resolve() for path, _ in values]
    if len(set(resolved)) != len(resolved):
        raise ValueError("candidate output paths must be unique")

    originals = {path.resolve(): path.read_bytes() for path, _ in values}
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for path, value in values:
            path = path.resolve()
            fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".candidate.tmp", dir=path.parent)
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


def artifact_point_estimates(data: dict) -> dict[str, float]:
    return {
        artifact_id: round(float(record["qualityScore"]), 6)
        for artifact_id, record in data["qualityScores"]["artifacts"].items()
    }


def ranking_point_estimates(data: dict) -> dict[str, tuple[tuple[str, float], ...]]:
    return {
        ranking_id: tuple((row["tool"], round(float(row["score"]), 6)) for row in data["rankings"][ranking_id]["rows"])
        for ranking_id in ALL_RANKINGS
    }


def replace_legacy_references(value):
    if isinstance(value, dict):
        return {key: replace_legacy_references(item) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_legacy_references(item) for item in value]
    if isinstance(value, str):
        value = value.replace(LEGACY_G2_RULE, CANONICAL_G2_RULE)
        value = value.replace("report_v4.json·", f"{DATA_SOURCE_LABEL}·")
    return value


def criterion_definitions(data: dict) -> tuple[dict[str, dict], dict[str, str]]:
    definitions: dict[str, dict] = {}
    kind_by_criterion: dict[str, str] = {}
    for kind, raw_definitions in data["criteriaDefinitions"].items():
        items = raw_definitions.get("criteria", []) if isinstance(raw_definitions, dict) else raw_definitions
        for definition in items:
            definitions[definition["id"]] = definition
            kind_by_criterion[definition["id"]] = kind
    return definitions, kind_by_criterion


def fix_assessment_classification(data: dict) -> None:
    definitions, kind_by_criterion = criterion_definitions(data)
    count = Counter()
    weight = Counter()
    weight_by_kind: dict[str, float] = Counter()
    for criterion_id, definition in definitions.items():
        assessment_class = definition["assessmentClass"]
        criterion_weight = float(definition["weight"])
        count[assessment_class] += 1
        weight[assessment_class] += criterion_weight
        if assessment_class != "mechanical":
            weight_by_kind[kind_by_criterion[criterion_id]] += criterion_weight
        if assessment_class == "mechanical" and "锚定式混合判断" in definition.get("assessmentClassReason", ""):
            definition["assessmentClassReason"] = "按v4.5公开的原子子项与固定分母直接重算；五件同类样本采用同一机械规则。"

    expected_count = {"mechanical": 9, "mixed_anchored_judgment": 36, "expert_judgment": 12}
    expected_weight = {"mechanical": 98.0, "mixed_anchored_judgment": 353.0, "expert_judgment": 149.0}
    if {key: count[key] for key in CLASS_ORDER} != expected_count:
        raise ValueError(f"unexpected assessment-class counts: {dict(count)}")
    if {key: weight[key] for key in CLASS_ORDER} != expected_weight:
        raise ValueError(f"unexpected assessment-class weights: {dict(weight)}")

    summary = {
        "criterionCount": expected_count,
        "aggregateWeightAcrossSixRubrics": expected_weight,
        "judgmentWeightByArtifactKind": {kind: float(weight_by_kind[kind]) for kind in data["meta"]["kinds"]},
        "totalCriterionCount": sum(expected_count.values()),
        "totalWeightAcrossSixRubrics": sum(expected_weight.values()),
        "scoreEffect": "分类修正不改变点估计；混合锚定判断和专家判断项进入单评审者局部一步敏感性重算。",
    }
    data.setdefault("contentInventory", {})["assessmentClasses"] = copy.deepcopy(summary)
    classification = data.setdefault("methodology", {}).setdefault("assessmentClassification", {})
    classification.update(
        {
            "purpose": "区分可按公开原子公式复算的机械项、观察可复核但换分仍依赖整体锚点的混合判断项，以及专家判断项。分类不改变点估计或权重。",
            "mechanical": "已公开原子子项、固定分母与换分公式，可对五件同类固定样本机械复算。",
            "mixed_anchored_judgment": "底层观察可复核，但当前得分仍按0—5整体锚点换算，未公开能从全量行项机械重算的完整公式。",
            "expert_judgment": "分析深度、信息取舍、叙事、视觉层级与构图等按公开0—5锚点判断。",
            "raterDisclosure": "单一评审者；未测量评审者间一致性。评测者可能与部分参评工具存在未公开的利益相关，读者应结合冻结原件与可复算数据独立判断。",
            "summary": copy.deepcopy(summary),
            "scoreEffect": summary["scoreEffect"],
        }
    )
    data["scoreSensitivity"]["declaredJudgmentWeightsByArtifactKind"] = summary["judgmentWeightByArtifactKind"]


def impact_map(data: dict) -> dict[tuple[str, str], dict]:
    return {(item["artifactId"], item["criterionId"]): item for item in data["scoreImpacts"]}


def local_movement(data: dict, tool: str, ranking: dict) -> dict:
    definitions, _ = criterion_definitions(data)
    impacts = impact_map(data)
    artifacts_by_tool_kind = {(item["tool"], item["kind"]): item["id"] for item in data["artifacts"]}
    components = []
    perspective = ranking["perspective"]
    for kind, task_weight in ranking["weights"].items():
        artifact_id = artifacts_by_tool_kind[(tool, kind)]
        quality = data["qualityScores"]["artifacts"][artifact_id]
        for criterion_score in quality["criterionScores"]:
            criterion_id = criterion_score["criterionId"]
            definition = definitions[criterion_id]
            effective_class = criterion_score.get("assessmentClassApplied") or definition["assessmentClass"]
            if effective_class not in SENSITIVITY_CLASSES:
                continue
            maximum = float(definition["weight"])
            earned = float(criterion_score["weighted"])
            if perspective == "firstOrigin":
                impact = impacts.get((artifact_id, criterion_id))
                if impact:
                    earned = float(impact["maximumPoints"]) + float(impact["firstOriginDelta"])
            step_points = maximum * float(data["scoreSensitivity"]["ratingStep0To5"]) / 5.0
            down = min(max(earned, 0.0), step_points) * float(task_weight)
            up = min(max(maximum - earned, 0.0), step_points) * float(task_weight)
            components.append(
                {
                    "artifactId": artifact_id,
                    "criterionId": criterion_id,
                    "effectiveAssessmentClass": effective_class,
                    "criterionPointStep": round(step_points, 6),
                    "taskWeight": float(task_weight),
                    "downwardRankingMovement": round(down, 6),
                    "upwardRankingMovement": round(up, 6),
                }
            )
    best_down_component = max(components, key=lambda item: item["downwardRankingMovement"])
    best_up_component = max(components, key=lambda item: item["upwardRankingMovement"])
    return {
        "eligibleCriterionCount": len(components),
        "components": components,
        "maxDownwardMovement": best_down_component["downwardRankingMovement"],
        "maxUpwardMovement": best_up_component["upwardRankingMovement"],
        "maxDownwardScenario": best_down_component,
        "maxUpwardScenario": best_up_component,
        "jointAllDownwardExtreme": round(sum(item["downwardRankingMovement"] for item in components), 6),
        "jointAllUpwardExtreme": round(sum(item["upwardRankingMovement"] for item in components), 6),
        "jointExtremeUsedForPublishedRange": False,
    }


def fix_ranking_roles_and_sensitivity(data: dict) -> None:
    modes: dict[str, dict] = {}
    for ranking_id in ALL_RANKINGS:
        ranking = data["rankings"][ranking_id]
        diagnostic = ranking_id in DIAGNOSTIC_RANKINGS
        ranking["status"] = "candidate_v451_pending_qa"
        ranking["isOfficial"] = False
        ranking["publicationRole"] = "exploratory_noncausal_diagnostic" if diagnostic else "official_candidate_fixed_sample_ranking"
        ranking["label"] = ranking["label"].replace("链路首次归责", "探索性首次归责诊断")
        ranking["interpretation"] = (
            "仅对当前证据中已枚举的完全继承缺口去重；未建立生成时因果图，不用于正式采购名次。"
            if diagnostic
            else "本次固定终稿在指定环境下的正式点估计次序；不外推为产品一般能力。"
        )
        for row in ranking["rows"]:
            audit = local_movement(data, row["tool"], ranking)
            down = float(audit["maxDownwardMovement"])
            up = float(audit["maxUpwardMovement"])
            score = float(row["score"])
            row["reviewResolutionLower"] = round(max(0.0, score - down), 2)
            row["reviewResolutionUpper"] = round(min(100.0, score + up), 2)
            row["downwardOneStepMovement"] = round(down, 2)
            row["upwardOneStepMovement"] = round(up, 2)
            row["nearScoreGroup"] = row.get("sensitivityGroup") or row.get("uncertaintyGroup")
            row["localSensitivityAudit"] = audit
        scenarios = [{row["tool"]: float(row["score"]) for row in ranking["rows"]}]
        for changed in ranking["rows"]:
            for component in changed["localSensitivityAudit"]["components"]:
                for direction, movement in (
                    ("down", component["downwardRankingMovement"]),
                    ("up", component["upwardRankingMovement"]),
                ):
                    scenario = dict(scenarios[0])
                    scenario[changed["tool"]] += -float(movement) if direction == "down" else float(movement)
                    scenarios.append(scenario)
        for row in ranking["rows"]:
            best_ranks = []
            worst_ranks = []
            for scenario in scenarios:
                target = scenario[row["tool"]]
                other_scores = [score for tool, score in scenario.items() if tool != row["tool"]]
                best_ranks.append(1 + sum(score > target + 1e-9 for score in other_scores))
                worst_ranks.append(1 + sum(score >= target - 1e-9 for score in other_scores))
            row["possibleBestRank"] = min(best_ranks)
            row["possibleWorstRank"] = max(worst_ranks)
            row["possibleBestPointOrder"] = row["possibleBestRank"]
            row["possibleWorstPointOrder"] = row["possibleWorstRank"]
            prefix = "探索性点估计" if diagnostic else "正式点估计"
            row["displayRank"] = f"{prefix}第{row['rank']}；相邻≤1分近分组{row['nearScoreGroup']}"
        modes[ranking_id] = {
            "rankingRole": "exploratory_noncausal_diagnostic" if diagnostic else "official_fixed_sample_ranking_after_qa",
            "rows": [
                {
                    "tool": row["tool"],
                    "score": row["score"],
                    "judgmentSensitivityLower": row["reviewResolutionLower"],
                    "judgmentSensitivityUpper": row["reviewResolutionUpper"],
                    "downwardOneStepMovement": row["downwardOneStepMovement"],
                    "upwardOneStepMovement": row["upwardOneStepMovement"],
                    "possibleBestPointOrder": row["possibleBestRank"],
                    "possibleWorstPointOrder": row["possibleWorstRank"],
                    "nearScoreGroup": row["nearScoreGroup"],
                    "localSensitivityAudit": row["localSensitivityAudit"],
                }
                for row in ranking["rows"]
            ],
        }

    sensitivity = data["scoreSensitivity"]
    effective_weights = effective_sensitivity_weights(data)
    sensitivity.update(
        {
            "version": "4.5.1",
            "method": "single_rater_one_classified_judgment_criterion_at_a_time_half_point_step",
            "classifiedJudgmentWeightsByArtifactKind": effective_weights,
            "effectiveSensitivityWeightsByArtifactKind": effective_weights,
            "classificationApplicationRule": "敏感性资格以每件终稿评分行的assessmentClassApplied为准；已机械化的下游一致性项排除，single_reviewer_anchored_judgment纳入。定义层三类权重另见declaredJudgmentWeightsByArtifactKind。",
            "boundaryRule": "一次只改变任一工具一个实际采用为混合锚定判断、专家判断或单评审者锚定判断维度的0.5/5步长，并按当前排名权重传播；在0与该维度满分处截断。名次范围枚举基准情景及任一工具的单项最大上下移动，不允许多项同时变化。",
            "interpretationLimit": "这是单一评分决定改变一步的局部情景重算，不是置信区间；不覆盖多个判断同时偏移，也不证明探索性首次归责诊断具有因果效力。",
            "modes": modes,
        }
    )
    data.setdefault("sensitivity", {})["singleRaterLocalStepV451"] = {
        "label": "v4.5.1 单评审者局部一步敏感性",
        "headline": "四种视角已按当前点估计重算",
        "description": sensitivity["interpretationLimit"],
        "modes": copy.deepcopy(modes),
    }

    root = data.setdefault("rankingPerspectives", {})
    root.update(
        {
            "status": "candidate_v451_pending_qa",
            "officialResultIds": [],
            "candidateResultIds": list(OFFICIAL_RANKINGS),
            "diagnosticResultIds": list(DIAGNOSTIC_RANKINGS),
            "definitions": {
                "standalone": "正式固定终稿独立使用排名",
                "firstOrigin": "探索性首次归责诊断：仅去重已枚举完全继承项，不作因果排名",
                "equalTask": "六任务各占1/6",
                "practical": "Excel25%、Word20%、PPT20%、普通图10%、水墨图10%、HTML15%",
            },
            "results": {ranking_id: copy.deepcopy(data["rankings"][ranking_id]) for ranking_id in ALL_RANKINGS},
        }
    )


def effective_sensitivity_weights(data: dict) -> dict[str, float]:
    definitions, kind_by_criterion = criterion_definitions(data)
    eligible_by_kind: dict[str, set[str]] = {kind: set() for kind in data["meta"]["kinds"]}
    for quality in data["qualityScores"]["artifacts"].values():
        for criterion_score in quality["criterionScores"]:
            criterion_id = criterion_score["criterionId"]
            effective_class = criterion_score.get("assessmentClassApplied") or definitions[criterion_id]["assessmentClass"]
            if effective_class in SENSITIVITY_CLASSES:
                eligible_by_kind[kind_by_criterion[criterion_id]].add(criterion_id)
    return {
        kind: float(sum(float(definitions[criterion_id]["weight"]) for criterion_id in criterion_ids))
        for kind, criterion_ids in eligible_by_kind.items()
    }


def fix_disclosures_and_presentation(data: dict) -> None:
    meta = data["meta"]
    meta.update(
        {
            "schemaVersion": "4.5.1",
            "scoringVersion": "4.5.1-consistency-and-disclosure-no-point-change",
            "dataVersion": "4.5.1",
            "version": "报告版本 4.5.1 · 固定样本证据复核",
            "generatedAt": REVISION_TIMESTAMP,
            "presentationVersion": "4.5.1",
            "status": "candidate_v451_pending_qa",
            "publicationStatus": "candidate_v451_pending_qa",
            "scoringNote": "v4.5.1不改变30件终稿点估计；修正分类汇总、当前敏感性、排名角色和方法披露。",
            "reviewerDisclosure": "单一评审者；评测者可能与部分参评工具存在未公开的利益相关。请结合冻结原件与可复算数据独立判断。",
        }
    )
    if "publicationVariant" in meta:
        meta["publicationVariant"] = "github_portable_v4.5.1"
    if "portablePackage" in meta:
        meta["portablePackage"]["note"] = "为保持公开URL与证据路径稳定，仓库目录及兼容文件名沿用v4.5；活动数据版本为v4.5.1。"

    data["qualityScores"]["version"] = "4.5.1"
    data["qualityScores"]["status"] = "candidate_v451_point_estimates_frozen"
    data["scores"]["status"] = "candidate_v451_point_estimates_frozen"
    for score_root in (data["qualityScores"], data["scores"]):
        for record in score_root.get("artifacts", {}).values():
            record["scoreStatus"] = "candidate_v451_point_estimates_frozen"
    data["propagationStatus"]["rankingUse"] = False
    data["propagationStatus"]["publicationRole"] = "exploratory_noncausal_diagnostic_only"
    data["propagationStatus"]["interpretationLimit"] = "未建立生成时因果图；只对已枚举完全继承项作探索性去重，不用于正式采购名次。"

    methodology = data["methodology"]
    methodology["rankingViews"] = list(ALL_RANKINGS)
    methodology["rankingPolicyV451"] = {
        "official": list(OFFICIAL_RANKINGS),
        "exploratoryDiagnostic": list(DIAGNOSTIC_RANKINGS),
        "reason": "传播结构不是生成时记录的因果图；首次归责只保留为已枚举继承项的非因果诊断。",
    }
    methodology["postObservationRuleDisclosure"] = {
        "ruleId": CANONICAL_G2_RULE,
        "preRegistered": False,
        "adoptionTiming": "v4_post_observation_symmetric_reassessment",
        "statement": "核心标题绝对方向反转的G2规则是在观察到样本问题后制定，再对五家固定样本对称复核；它不是事前预注册规则。",
        "scoreEffect": "none",
    }

    process_recording = {
        "manifest": PROCESS_VIDEO_MANIFEST,
        "segmentCount": 8,
        "totalBytes": PROCESS_VIDEO_BYTES,
        "coverage": "用户确认：8段视频合计完整记录本次5款AI办公软件完成6项连续任务的全过程。",
        "publicAvailability": "withheld_due_to_size",
        "publicationPolicy": "视频暂不公开；GitHub仅发布文件名、字节数与SHA-256索引。需要核验时可通过仓库Issues联系提供。",
        "requestUrl": REQUEST_URL,
        "scoreEffect": "none",
    }
    data["testProtocol"]["processRecording"] = process_recording
    data["testProtocol"]["executionDisclosure"] = {
        "recordingCoverage": process_recording["coverage"],
        "qoderContinuationMessages": "Qoder记录含3次用户“继续”消息；该差异已披露但不单独计分。",
        "interventionBoundary": "未事前登记统一的重试次数、超时、人工干预与多版本终稿选择规则；固定终稿比较不应被解读为生成稳定性或完全受控实验。",
        "selectionBoundary": "计分对象为已冻结并留存SHA-256的30件终稿；过程视频用于核验任务链，不改变点估计。",
    }

    summary = data["presentation"].setdefault("executiveSummary", {})
    summary.update(
        {
            "rankingPolicy": "两张终稿独立使用排名为正式结果；两张首次归责结果仅是探索性非因果诊断，不用于采购名次。",
            "gatePolicy": "先读G0/G1/G2交付闸门，再读连续分；闸门不参与分数计算。核心方向反转G2规则为观察后制定并对五家对称复核。",
            "processPolicy": "8段完整过程录屏因约7.40GB暂不公开；已发布SHA-256索引，需要时通过GitHub Issues联系提供。",
            "reviewerDisclosure": meta["reviewerDisclosure"],
        }
    )
    hero = meta.setdefault("ui", {}).setdefault("hero", {})
    hero["statusNote"] = "两张终稿独立使用排名为正式结果候选；首次归责仅作探索性非因果诊断。所有发布状态须经v4.5.1 QA盖章后生效。"
    labels = data["presentation"].setdefault("assessmentClassLabels", {})
    labels.update(
        {
            "mechanical": "机械验证项",
            "mixed_anchored_judgment": "混合锚定判断项",
            "expert_judgment": "专家判断项",
        }
    )

    for visual in data["presentation"].get("visualRegistry", []):
        if visual.get("id") == "executive-rankings":
            visual.update(
                {
                    "title": "正式固定终稿排名与交付风险概览",
                    "scopeNote": "正式排名只含终稿独立使用视角；G0/G1/G2独立显示且不参与分数计算。",
                }
            )
        elif visual.get("id") == "ranking-main":
            visual.update(
                {
                    "title": "两张正式排名与两张探索性诊断",
                    "scopeNote": "终稿独立使用为正式结果；首次归责仅去重已枚举完全继承项，不作因果或采购排名。",
                }
            )
        elif visual.get("id") == "scenario-composition":
            visual["number"] = "表7-2"

    gate_policy = data["deliveryGates"].setdefault("policyV451", {})
    gate_policy.update(methodology["postObservationRuleDisclosure"])

    verification = data.get("verification", [])
    if not isinstance(verification, list):
        raise ValueError("verification must remain a list")
    data["verification"] = [
        row for row in verification if row.get("id") != "verification:v451-activation"
    ]

    history = [row for row in data.get("versionHistory", []) if row.get("version") != "4.5.1"]
    history.append(
        {
            "version": "4.5.1",
            "date": REVISION_TIMESTAMP,
            "status": "candidate_pending_qa",
            "previousVersion": "4.5",
            "title": "v4.5.1方法一致性与披露修订",
            "summary": "不改变30件终稿点估计；修正三类评分项汇总，重算四种单评审者局部一步敏感性，将首次归责降为探索性非因果诊断，并补充后观察G2规则、过程录屏、干预边界与评审者限制。",
            "artifactPointEstimatesChanged": False,
            "officialRankings": list(OFFICIAL_RANKINGS),
            "exploratoryDiagnostics": list(DIAGNOSTIC_RANKINGS),
        }
    )
    data["versionHistory"] = history


def revise(data: dict) -> dict:
    before_scores = artifact_point_estimates(data)
    before_rankings = ranking_point_estimates(data)
    revised = replace_legacy_references(copy.deepcopy(data))
    fix_assessment_classification(revised)
    fix_ranking_roles_and_sensitivity(revised)
    fix_disclosures_and_presentation(revised)
    if artifact_point_estimates(revised) != before_scores:
        raise ValueError("v4.5.1 revision changed artifact point estimates")
    if ranking_point_estimates(revised) != before_rankings:
        raise ValueError("v4.5.1 revision changed ranking point estimates")
    return revised


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=list(DEFAULT_FILES))
    args = parser.parse_args()
    paths = list(args.paths)
    revised_values = [(path, revise(load(path))) for path in paths]
    atomic_dump_group(revised_values)
    for path in paths:
        print(f"revised {path}")


if __name__ == "__main__":
    main()
