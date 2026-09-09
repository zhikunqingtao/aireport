#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { gunzipSync } from "node:zlib";

const args = process.argv.slice(2);
const repoArg = args.indexOf("--repo");
const repo = resolve(repoArg >= 0 ? args[repoArg + 1] : ".");
const caseDir = join(repo, "docs", "case-studies");
const packageRoot = join(caseDir, "assets", "unitree-office-benchmark");
const reportPath = join(caseDir, "AI办公工具对比测评_宇树科技_截至2026-08-30.html");
const evidencePagePath = join(repo, "docs", "evidence.html");
const report = join(packageRoot, "report");
const releaseDir = join(report, "release-v4.5");
const manifestsDir = join(packageRoot, "manifests");
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const shaCache = new Map();
const sha = (path) => {
  if (!shaCache.has(path)) shaCache.set(path, createHash("sha256").update(readFileSync(path)).digest("hex"));
  return shaCache.get(path);
};
const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));
const posixRelative = (from, path) => relative(from, path).split(sep).join("/");
const staysWithin = (root, path) => {
  const value = relative(root, path);
  return value === "" || (!value.startsWith(`..${sep}`) && value !== ".." && !value.startsWith(sep));
};
const isSafeRepoRelativePath = (value) => {
  if (typeof value !== "string" || !value || value.startsWith("/") || value.startsWith("./") || value.includes("\\") || value.includes("\0")) return false;
  if (value.includes("file://") || value.split("/").includes("..")) return false;
  const target = resolve(repo, value);
  return staysWithin(repo, target) && posixRelative(repo, target) === value;
};
const descriptorMatches = (record, path, label) => {
  check(Boolean(record && typeof record === "object"), `${label} descriptor is missing`);
  check(existsSync(path), `${label} target is missing`);
  if (!record || typeof record !== "object" || !existsSync(path)) return;
  check(Number.isInteger(record.bytes) && record.bytes === statSync(path).size, `${label} byte size mismatch`);
  check(/^[0-9a-f]{64}$/.test(record.sha256 || ""), `${label} SHA-256 is invalid`);
  check(record.sha256 === sha(path), `${label} SHA-256 mismatch`);
};
const isPublicHttpsUrl = (value) => {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && Boolean(url.hostname) && !url.username && !url.password && !["localhost", "127.0.0.1", "::1"].includes(url.hostname);
  } catch { return false; }
};
const walkFiles = (root) => readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
  const path = join(root, entry.name);
  return entry.isDirectory() ? walkFiles(path) : entry.isFile() ? [path] : [];
});

check(existsSync(packageRoot), "single-version evidence package is missing");
check(!existsSync(join(caseDir, "assets", "unitree-office-benchmark-v4.3")), "legacy versioned package directory still exists");
check(existsSync(reportPath), "portable report is missing");
check(existsSync(evidencePagePath), "evidence landing page is missing");
check(!existsSync(join(packageRoot, ".DS_Store")), "Finder .DS_Store remains at package root");
check(!existsSync(join(packageRoot, "report", ".DS_Store")), "Finder .DS_Store remains in report directory");

const html = readFileSync(reportPath, "utf8");
check(!html.includes("/Users/"), "portable report contains /Users/ path");
check(!html.includes("file://"), "portable report contains file:// URL");
check(!html.includes("unitree-office-benchmark-v4.3"), "portable report references legacy package directory");
const evidencePage = readFileSync(evidencePagePath, "utf8");
check(evidencePage.includes("<strong>1,604</strong><span>清单记录</span>"), "evidence landing page manifest count is not 1,604");
check(evidencePage.includes("manifests/process-video-index.json"), "evidence landing page omits the process-video index");
for (const requiredText of [
  "先看G0/G1/G2交付风险和两张正式排名",
  "两张正式排名 + 两张探索性诊断已全部展开",
  "探索性 · 非因果",
  "观察后规则披露",
  "规范规则ID",
  "完整过程录屏",
  "通过GitHub Issues联系申请核验",
  "近分组",
  "报告版本 4.5.1",
  "<details class=\"prompt-step\" open>",
  "sourceNote",
  "decorateTableSemantics",
  "aria-labelledby=\"executive-gate-title\"",
  "aria-labelledby=\"process-recording-title\"",
]) check(html.includes(requiredText), `portable report is missing v4.5.1 UI/ARIA marker: ${requiredText}`);
check(/setAttribute\(["']scope["'],\s*["']col["']\)/.test(html), "portable report does not decorate column headers with scope=col");
check(/setAttribute\(["']scope["'],\s*["']row["']\)/.test(html), "portable report does not decorate row headers with scope=row");
check(/setAttribute\(["']aria-labelledby["']/.test(html), "portable report does not bind unlabeled tables to a nearby heading");
for (const forbiddenText of [
  "四组结果已全部展开",
  "并列公布终稿独立使用与链路首次归责两种视角",
  "不指定唯一主榜",
  "每组均列出五款工具的完整排名",
]) check(!html.includes(forbiddenText), `portable report retains misleading pre-v4.5.1 copy: ${forbiddenText}`);
const payloadMatch = html.match(/<script id="report-data" type="application\/json" data-encoding="gzip-base64">([\s\S]*?)<\/script>/);
check(Boolean(payloadMatch), "portable report-data payload is missing");
let data = {};
if (payloadMatch) {
  try { data = JSON.parse(gunzipSync(Buffer.from(payloadMatch[1].trim(), "base64")).toString("utf8")); }
  catch (error) { failures.push(`portable report-data decode failed: ${error.message}`); }
}

const count = (value) => Array.isArray(value) ? value.length : Object.keys(value || {}).length;
check(count(data.artifacts) === 30, `artifacts=${count(data.artifacts)} expected 30`);
check(count(data.scenarioRuns) === 180, `scenarioRuns=${count(data.scenarioRuns)} expected 180`);
check(data.contentInventory?.scenarioRecords?.count === 202, `scenario records=${data.contentInventory?.scenarioRecords?.count ?? 0} expected 202`);
check(data.contentInventory?.scenarioRecordComposition?.primaryScenarioRuns?.count === 180, "scenario composition primary run count is not 180");
check(data.contentInventory?.scenarioRecordComposition?.supplementalScenarioRecords?.count === 13, "scenario composition supplemental count is not 13");
check(data.contentInventory?.scenarioRecordComposition?.pairedImageZoneFamilies?.count === 9, "scenario composition paired image-zone count is not 9");
check(count(data.coverageItems) === 324, `coverageItems=${count(data.coverageItems)} expected 324`);
check(count(data.findings) === 200, `findings=${count(data.findings)} expected 200`);
check(count(data.evidence) === 741, `evidence=${count(data.evidence)} expected 741`);
check(count(data.media) === 710, `media=${count(data.media)} expected 710`);
check(count(data.facts) === 32, `facts=${count(data.facts)} expected 32`);
check(count(data.sources) === 11, `sources=${count(data.sources)} expected 11`);
check(count(data.claimLedger?.records) === 180, `claimLedger=${count(data.claimLedger?.records)} expected 180`);
check(data.meta?.schemaVersion === "4.5.1", `report schemaVersion=${data.meta?.schemaVersion ?? "missing"} expected 4.5.1`);
check(data.meta?.dataVersion === "4.5.1", `report dataVersion=${data.meta?.dataVersion ?? "missing"} expected 4.5.1`);
check(data.meta?.status === "final_v451_offline_qa_passed", `report status=${data.meta?.status ?? "missing"} expected final v4.5.1`);
const portableDataPath = join(report, "portable-report-data-v4.5.json");
const portableDataFileText = existsSync(portableDataPath) ? readFileSync(portableDataPath, "utf8") : "{}";
const portableData = JSON.parse(portableDataFileText);
check(!portableDataFileText.includes("/Users/"), "portable-report-data contains a local absolute path");
check(!portableDataFileText.includes("file://"), "portable-report-data contains a file URL");
check(!JSON.stringify(data).includes("/Users/"), "embedded payload contains a local absolute path");
check(!JSON.stringify(data).includes("file://"), "embedded payload contains a file URL");
const expectedProcessManifestUrl = "https://zhikunqingtao.github.io/aireport/case-studies/assets/unitree-office-benchmark/manifests/process-video-index.json";
const embeddedScoringNote = data.meta?.scoringNote;
check(typeof embeddedScoringNote === "string" && embeddedScoringNote.includes("不改变30件终稿点估计"), "embedded payload scoringNote is missing the v4.5.1 score-freeze disclosure");
check(embeddedScoringNote !== data.meta?.statusNote, "embedded payload scoringNote was overwritten by statusNote");
check(embeddedScoringNote === portableData.meta?.scoringNote, "embedded payload scoringNote differs from portable-report-data");
check(data.meta?.statusNote === portableData.meta?.ui?.hero?.statusNote, "embedded payload statusNote does not match the published UI status note");
for (const [label, payload] of [["embedded payload", data], ["portable data", portableData]]) {
  const manifestUrl = payload.testProtocol?.processRecording?.manifest;
  check(isPublicHttpsUrl(manifestUrl), `${label} process-recording manifest is not a public HTTPS URL`);
  check(manifestUrl === expectedProcessManifestUrl, `${label} process-recording manifest URL is not the canonical GitHub Pages URL`);
}
check(JSON.stringify(data.rankingPerspectives?.officialResultIds || []) === JSON.stringify(["standalone_equalTask", "standalone_practical"]), "official ranking IDs are not the two standalone views");
check(JSON.stringify(data.rankingPerspectives?.diagnosticResultIds || []) === JSON.stringify(["firstOrigin_equalTask", "firstOrigin_practical"]), "exploratory diagnostic IDs are incorrect");
check(data.rankings?.firstOrigin_equalTask?.isOfficial === false && data.rankings?.firstOrigin_practical?.isOfficial === false, "first-origin diagnostics are incorrectly marked official");
check(data.rankings?.firstOrigin_equalTask?.publicationRole === "exploratory_noncausal_diagnostic" && data.rankings?.firstOrigin_practical?.publicationRole === "exploratory_noncausal_diagnostic", "first-origin rankings lack the exploratory noncausal role");
check(data.contentInventory?.assessmentClasses?.criterionCount?.mechanical === 9, "mechanical criterion count is not 9");
check(data.contentInventory?.assessmentClasses?.criterionCount?.mixed_anchored_judgment === 36, "mixed anchored criterion count is not 36");
check(data.contentInventory?.assessmentClasses?.criterionCount?.expert_judgment === 12, "expert criterion count is not 12");
check(data.contentInventory?.assessmentClasses?.aggregateWeightAcrossSixRubrics?.mechanical === 98, "mechanical aggregate weight is not 98");
check(data.contentInventory?.assessmentClasses?.aggregateWeightAcrossSixRubrics?.mixed_anchored_judgment === 353, "mixed anchored aggregate weight is not 353");
check(data.contentInventory?.assessmentClasses?.aggregateWeightAcrossSixRubrics?.expert_judgment === 149, "expert aggregate weight is not 149");
check(typeof data.meta?.reviewerDisclosure === "string" && data.meta.reviewerDisclosure.includes("单一评审者"), "single-reviewer disclosure is missing");
check(data.methodology?.postObservationRuleDisclosure?.ruleId === "G2-CORE-HEADLINE-ABSOLUTE-DIRECTION-REVERSAL", "canonical post-observation G2 rule ID is missing");
check(data.methodology?.postObservationRuleDisclosure?.preRegistered === false, "post-observation G2 rule is not explicitly marked unregistered");
check(Object.keys(data.scoreSensitivity?.modes || {}).length === 4, "current score sensitivity does not cover four views");

for (const required of [
  "source-self-contained-v4.5.html",
  "activity-report-data-v4.5.json",
  "portable-report-data-v4.5.json",
  "release-v4.5/report_v4.5_final.json",
  "release-v4.5/qa_report_postpublication_hardened.json",
  "release-v4.5/revise_v451.py",
  "release-v4.5/stamp_v451.py",
  "release-v4.5/finalize_v451.py",
  "release-v4.5/qa_v451.py",
  "release-v4.5/qa_v451_candidate.json",
  "release-v4.5/qa_v451.json",
]) check(existsSync(join(report, required)), `required v4.5 file missing: ${required}`);
for (const forbidden of [
  "history", "pdfs", "build-and-qa", "release-v4.3", "release-v4.4",
  "source-self-contained-v4.3.html", "source-self-contained-v4.4.html",
  "activity-report-data-v4.3.json", "activity-report-data-v4.4.json",
  "portable-report-data-v4.3.json", "portable-report-data-v4.4.json",
  "release-v4.5/history", "release-v4.5/v4.4-v4.5_变更表.md",
  "release-v4.5/AI办公工具对比测评_宇树科技_截至2026-08-30_v4.5_自包含版.html",
]) check(!existsSync(join(report, forbidden)), `historical or duplicate report artifact remains: ${forbidden}`);

const finalDataPath = join(releaseDir, "report_v4.5_final.json");
const sourceSelfContainedPath = join(report, "source-self-contained-v4.5.html");
const activityDataPath = join(report, "activity-report-data-v4.5.json");
const processVideoIndexPath = join(manifestsDir, "process-video-index.json");
const finalDataText = readFileSync(finalDataPath, "utf8");
const finalData = JSON.parse(finalDataText);

const buildSummaryPath = join(releaseDir, "build_summary_final.json");
const buildSummaryText = readFileSync(buildSummaryPath, "utf8");
const buildSummary = JSON.parse(buildSummaryText);
check(!buildSummaryText.includes("/Users/"), "build summary contains a local absolute path");
check(!buildSummaryText.includes("file://"), "build summary contains a file URL");
check(buildSummary.version === "4.5.1", "build summary version is not 4.5.1");
check(buildSummary.compatibilityFilenameVersion === "4.5", "build summary compatibility filename version is not 4.5");
check(buildSummary.path === "report/source-self-contained-v4.5.html", "build summary source HTML path is incorrect");
descriptorMatches(buildSummary, sourceSelfContainedPath, "build summary source HTML");
check(buildSummary.mediaTotal === 710 && buildSummary.embeddedMedia === 710 && buildSummary.externalMedia === 0 && buildSummary.missingMedia === 0, "build summary self-contained media resolution is incorrect");
check(buildSummary.deduplicatedMediaReferences === 3, "build summary self-contained deduplicated-media count is not 3");
check(buildSummary.portablePagesBuild?.path === "../../../../AI办公工具对比测评_宇树科技_截至2026-08-30.html", "build summary portable HTML path is incorrect");
descriptorMatches(buildSummary.portablePagesBuild, reportPath, "build summary portable HTML");
check(buildSummary.portablePagesBuild?.mediaTotal === 710 && buildSummary.portablePagesBuild?.embeddedMedia === 0 && buildSummary.portablePagesBuild?.externalMedia === 710 && buildSummary.portablePagesBuild?.missingMedia === 0, "build summary portable media resolution is incorrect");
check(buildSummary.portablePagesBuild?.deduplicatedMediaReferences === 3, "build summary portable deduplicated-media count is not 3");
const expectedReportCounts = {
  artifacts: 30,
  scenarioRecords: 202,
  coverageItems: 324,
  findings: 200,
  evidence: 741,
  media: 710,
  facts: 32,
  sources: 11,
};
check(JSON.stringify(buildSummary.reportCounts) === JSON.stringify(expectedReportCounts), "build summary reportCounts are incomplete or incorrect");
const expectedBuildDataFiles = {
  final: ["report/release-v4.5/report_v4.5_final.json", finalDataPath],
  activity: ["report/activity-report-data-v4.5.json", activityDataPath],
  portable: ["report/portable-report-data-v4.5.json", portableDataPath],
};
for (const [key, [expectedPath, target]] of Object.entries(expectedBuildDataFiles)) {
  const record = buildSummary.dataFiles?.[key];
  check(record?.path === expectedPath, `build summary ${key} data path is incorrect`);
  descriptorMatches(record, target, `build summary ${key} data`);
}
check(buildSummary.processVideoIndex?.path === "manifests/process-video-index.json", "build summary process-video index path is incorrect");
descriptorMatches(buildSummary.processVideoIndex, processVideoIndexPath, "build summary process-video index");
check(buildSummary.processVideoIndex?.fileCount === 8, "build summary process-video count is not 8");
check(buildSummary.processVideoIndex?.totalBytes === 7399913834, "build summary process-video bytes are incorrect");
check(buildSummary.processVideoIndex?.videosIncludedInRepository === 0, "build summary incorrectly says videos are included");
check(buildSummary.processVideoIndex?.publicAvailability === "hash_index_only_videos_withheld_by_owner", "build summary process-video publication role is incorrect");
check(buildSummary.processVideoIndex?.requestUrl === "https://github.com/zhikunqingtao/aireport/issues", "build summary process-video request URL is incorrect");
check(JSON.stringify(buildSummary.rankingPublication?.officialResultIds || []) === JSON.stringify(["standalone_equalTask", "standalone_practical"]), "build summary official ranking roles are incorrect");
check(JSON.stringify(buildSummary.rankingPublication?.diagnosticResultIds || []) === JSON.stringify(["firstOrigin_equalTask", "firstOrigin_practical"]), "build summary diagnostic ranking roles are incorrect");
check(buildSummary.rankingPublication?.artifactPointEstimatesChanged === false, "build summary does not freeze artifact point estimates");
check(typeof buildSummary.changeScope === "string" && buildSummary.changeScope.includes("30件固定终稿的点估计未改变"), "build summary change scope omits the frozen point-estimate boundary");
check(buildSummary.desktopExperience?.browserValidation === "user_reported_ok; not rerun by the v4.5.1 release pipeline", "build summary browser-validation provenance is incorrect");
check(buildSummary.artifactAccess?.publishedAssetHeadChecks === "carried_forward_30_of_30_from_prior_release; asset paths unchanged", "build summary does not distinguish carried-forward asset checks");

const releaseManifestPath = join(releaseDir, "release_manifest_v4.5.json");
const releaseManifestText = readFileSync(releaseManifestPath, "utf8");
const releaseManifest = JSON.parse(releaseManifestText);
check(!releaseManifestText.includes("/Users/"), "release manifest contains a local absolute path");
check(!releaseManifestText.includes("file://"), "release manifest contains a file URL");
check(releaseManifest.version === "4.5.1", "release manifest version is not 4.5.1");
check(releaseManifest.compatibilityFilenameVersion === "4.5", "release manifest compatibility filename version is not 4.5");
check(releaseManifest.status === "v451_release_files_finalized", "release manifest status is not v451_release_files_finalized");
check(releaseManifest.finalizedAt === finalData.meta?.generatedAt, "release manifest finalizedAt differs from deterministic report generation time");
check(releaseManifest.publicationMode === "single_version", "release manifest is not marked single_version");
check(releaseManifest.gitCommitPerformed === false && releaseManifest.gitPushPerformed === false, "release manifest must describe the pre-commit/pre-push finalization instant");
check(typeof releaseManifest.compatibilityNote === "string" && releaseManifest.compatibilityNote.includes("v4.5.1") && releaseManifest.compatibilityNote.includes("v4.5"), "release manifest compatibility role explanation is missing");
check(typeof releaseManifest.provenanceNote === "string" && releaseManifest.provenanceNote.includes("provenance-inputs") && releaseManifest.provenanceNote.includes("不是并行发布"), "release manifest provenance role explanation is missing");
check(typeof releaseManifest.historicalReferencePolicy === "string" && releaseManifest.historicalReferencePolicy.includes("仅保留为v4.5历史参考") && releaseManifest.historicalReferencePolicy.includes("不代表v4.5.1当前构建"), "release manifest does not distinguish historical v4.5 QA from current v4.5.1 QA");
check(typeof releaseManifest.publicationStateNote === "string" && releaseManifest.publicationStateNote.includes("Git提交与推送前") && releaseManifest.publicationStateNote.includes("GitHub Release"), "release manifest publication-state role explanation is missing");
check(releaseManifest.presentationUpdate?.scoringChanged === false, "release manifest incorrectly reports a score change");
check(releaseManifest.presentationUpdate?.reportDataChanged === true, "release manifest fails to disclose the v4.5.1 semantic data revision");
check(typeof releaseManifest.presentationUpdate?.reportDataChangeBoundary === "string" && releaseManifest.presentationUpdate.reportDataChangeBoundary.includes("30件点估计不变"), "release manifest data-change boundary is missing");
check(releaseManifest.presentationUpdate?.browserRuntimeRetest === "not_rerun_user_reported_ok", "release manifest browser retest provenance is incorrect");
const expectedActiveTargets = {
  portableHtml: ["../../../../AI办公工具对比测评_宇树科技_截至2026-08-30.html", reportPath],
  sourceSelfContained: ["../source-self-contained-v4.5.html", sourceSelfContainedPath],
  activityData: ["../activity-report-data-v4.5.json", activityDataPath],
  portableData: ["../portable-report-data-v4.5.json", portableDataPath],
  finalData: ["report_v4.5_final.json", finalDataPath],
  processVideoIndex: ["../../manifests/process-video-index.json", processVideoIndexPath],
};
check(JSON.stringify(Object.keys(releaseManifest.active || {}).sort()) === JSON.stringify(Object.keys(expectedActiveTargets).sort()), "release manifest active target set is incorrect");
check(JSON.stringify(Object.keys(releaseManifest.activeHashes || {}).sort()) === JSON.stringify(Object.keys(expectedActiveTargets).sort()), "release manifest active hash set is incorrect");
for (const [key, [expectedPath, target]] of Object.entries(expectedActiveTargets)) {
  const declaredPath = releaseManifest.active?.[key];
  check(declaredPath === expectedPath, `release manifest active.${key} path is incorrect`);
  if (typeof declaredPath === "string") {
    const resolvedTarget = resolve(releaseDir, declaredPath);
    check(staysWithin(repo, resolvedTarget), `release manifest active.${key} escapes the repository`);
    check(resolvedTarget === resolve(target), `release manifest active.${key} does not resolve to its declared role target`);
  }
  descriptorMatches(releaseManifest.activeHashes?.[key], target, `release manifest activeHashes.${key}`);
}
const releaseRecords = Array.isArray(releaseManifest.releaseFiles) ? releaseManifest.releaseFiles : [];
const releaseRecordPaths = releaseRecords.map((item) => item.path);
check(new Set(releaseRecordPaths).size === releaseRecordPaths.length, "release manifest contains duplicate releaseFiles paths");
const transientReleaseFiles = walkFiles(releaseDir).filter((path) => path !== releaseManifestPath && (path.includes(`${sep}__pycache__${sep}`) || [".pyc", ".tmp", ".swp"].includes(path.slice(path.lastIndexOf("."))) || path.endsWith(`${sep}.DS_Store`)));
check(transientReleaseFiles.length === 0, `transient release files remain: ${transientReleaseFiles.map((path) => posixRelative(releaseDir, path)).join(", ")}`);
const releasePhysicalPaths = new Set(walkFiles(releaseDir)
  .filter((path) => path !== releaseManifestPath)
  .map((path) => posixRelative(releaseDir, path)));
for (const item of releaseRecords) {
  check(typeof item.path === "string" && item.path && !item.path.startsWith("/") && !item.path.split("/").includes(".."), `unsafe releaseFiles path: ${item.path ?? "missing"}`);
  if (typeof item.path !== "string" || !item.path || item.path.startsWith("/") || item.path.split("/").includes("..")) continue;
  const target = resolve(releaseDir, item.path);
  check(staysWithin(releaseDir, target), `releaseFiles path escapes release directory: ${item.path}`);
  descriptorMatches(item, target, `releaseFiles ${item.path}`);
}
for (const path of releasePhysicalPaths) check(releaseRecordPaths.includes(path), `physical release file omitted from release manifest: ${path}`);
for (const path of releaseRecordPaths) check(releasePhysicalPaths.has(path), `release manifest lists a non-physical release file: ${path}`);
for (const requiredReleaseFile of ["finalize_v451.py", "qa_v451.py", "qa_v451.json", "report_v4.5_final.json", "build_summary_final.json"]) {
  check(releaseRecordPaths.includes(requiredReleaseFile), `release manifest omits required v4.5.1 release file: ${requiredReleaseFile}`);
}
for (const historicalFile of ["adjudicate_v45.py", "stamp_v45.py", "qa_v45.py", "qa_interaction_affordance.json", "qa_report_postpublication_hardened.json", "recompute_summary.json"]) {
  const record = releaseRecords.find((item) => item.path === historicalFile);
  check(record?.role === "historical_v4.5_reference_not_current_v4.5.1_qa", `release manifest does not mark historical v4.5 material: ${historicalFile}`);
}

const finalQaPath = join(releaseDir, "qa_v451.json");
const finalQaText = readFileSync(finalQaPath, "utf8");
const finalQa = JSON.parse(finalQaText);
check(!finalQaText.includes("/Users/"), "final QA contains a local absolute path");
check(!finalQaText.includes("file://"), "final QA contains a file URL");
check(finalQa.schemaVersion === "qa-v4.5.1-2.0", "final QA schemaVersion is not qa-v4.5.1-2.0");
check(finalQa.generatedAt === "2026-09-09T12:40:00+08:00", "final QA does not use the fixed final timestamp");
check(finalQa.phase === "final", "final QA phase is not final");
check(finalQa.status === "passed", "final QA status is not passed");
check(/^[0-9a-f]{64}$/.test(finalQa.canonicalSummarySha256 || ""), "final QA canonical summary digest is missing or invalid");
check(Array.isArray(finalQa.crossFileChecks) && finalQa.crossFileChecks.length > 0 && finalQa.crossFileChecks.every((item) => item.passed === true), "final QA cross-file checks are absent or not all passed");
check(Array.isArray(finalQa.crossFileFailures) && finalQa.crossFileFailures.length === 0, "final QA has cross-file failures");
const expectedQaTargets = new Map([
  [posixRelative(repo, finalDataPath), finalDataPath],
  [posixRelative(repo, activityDataPath), activityDataPath],
  [posixRelative(repo, portableDataPath), portableDataPath],
]);
const qaResults = Array.isArray(finalQa.results) ? finalQa.results : [];
check(qaResults.length === expectedQaTargets.size, "final QA does not contain exactly the three release-data results");
check(new Set(qaResults.map((item) => item.path)).size === qaResults.length, "final QA contains duplicate result paths");
for (const result of qaResults) {
  check(isSafeRepoRelativePath(result.path), `final QA result path is not repository-relative: ${result.path ?? "missing"}`);
  check(expectedQaTargets.has(result.path), `final QA result path is unexpected: ${result.path ?? "missing"}`);
  const target = expectedQaTargets.get(result.path);
  if (target) {
    check(result.sha256 === sha(target), `final QA SHA mismatch: ${result.path}`);
    check(result.status === "passed", `final QA result did not pass: ${result.path}`);
    check(Array.isArray(result.failures) && result.failures.length === 0, `final QA result has failures: ${result.path}`);
  }
}

const pathMap = readJson(join(manifestsDir, "path-map.json"));
for (const [source, target] of Object.entries(pathMap)) {
  check(existsSync(join(caseDir, target)), `path-map target missing for ${source}: ${target}`);
}
for (const tool of ["doubao", "qianwen", "qoder", "workbuddy", "zhikuncode"]) {
  const sourceSuffix = `${tool}-tool-self-response-display.webp`;
  check(Object.keys(pathMap).some((path) => path.endsWith(sourceSuffix)), `display WebP source mapping missing: ${sourceSuffix}`);
}

const portableText = JSON.stringify(data);
const portableRefs = new Set(portableText.match(/assets\/unitree-office-benchmark\/[^\n\r\"'<>|]+/g) || []);
for (const raw of portableRefs) {
  const target = raw.split("#")[0].split("?")[0];
  check(existsSync(join(caseDir, target)), `portable data target missing: ${target}`);
}

const manifest = readJson(join(manifestsDir, "files.json"));
check(manifest.activeVersion === "4.5.1", "files manifest activeVersion is not 4.5.1");
check(manifest.compatibilityFilenameVersion === "4.5", "files manifest compatibility filename version is not 4.5");
check(manifest.generatedAt === finalData.meta?.generatedAt, "files manifest generatedAt differs from deterministic report generation time");
check(manifest.publicationMode === "single_version", "files manifest is not marked single_version");
check(manifest.packageDirectory === "unitree-office-benchmark", "files manifest packageDirectory mismatch");
check(typeof manifest.activeVersionBoundary === "string" && manifest.activeVersionBoundary.includes("v4.5.1") && manifest.activeVersionBoundary.includes("兼容路径") && manifest.activeVersionBoundary.includes("SHA256SUMS"), "files manifest active-version/compatibility role boundary is missing");
check(typeof manifest.v45PackagingBoundary === "string" && manifest.v45PackagingBoundary.includes("历史兼容字段") && manifest.v45PackagingBoundary.includes("8段完整过程录屏仅发布哈希索引"), "files manifest retains a stale v4.5 packaging boundary");
const finalDataAbsolutePathOccurrences = finalDataText.split("/Users/").length - 1;
check(manifest.sourceAbsolutePathOccurrences === finalDataAbsolutePathOccurrences, "files manifest absolute-path occurrence count differs from the intentionally preserved full final data");
check(manifest.gitCommitPerformed === false && manifest.gitPushPerformed === false, "files manifest must describe the pre-commit/pre-push finalization instant");
check(manifest.frozenReport?.relativePath === "report/source-self-contained-v4.5.html", "files manifest frozen report path is incorrect");
descriptorMatches(manifest.frozenReport, sourceSelfContainedPath, "files manifest frozen report");
check(manifest.portableReport?.relativePath === "../../AI办公工具对比测评_宇树科技_截至2026-08-30.html", "files manifest portable report path is incorrect");
descriptorMatches(manifest.portableReport, reportPath, "files manifest portable report");
const manifestPaths = (manifest.files || []).map((item) => item.relativePath);
check(new Set(manifestPaths).size === manifestPaths.length, "files manifest contains duplicate relativePath values");
check(!manifestPaths.includes("manifests/process-video-index.json"), "process-video-index must be covered by SHA256SUMS rather than self-referential files.json records");
for (const requiredRecord of [
  "report/release-v4.5/finalize_v451.py",
  "report/release-v4.5/revise_v451.py",
  "report/release-v4.5/stamp_v451.py",
  "report/release-v4.5/qa_v451.py",
  "report/release-v4.5/qa_v451_candidate.json",
  "report/release-v4.5/qa_v451.json",
]) {
  const record = (manifest.files || []).find((item) => item.relativePath === requiredRecord);
  check(Boolean(record), `files manifest omits v4.5.1 role record: ${requiredRecord}`);
  check(Array.isArray(record?.roles) && record.roles.some((role) => String(role).includes("v4.5.1")), `files manifest v4.5.1 role explanation is missing: ${requiredRecord}`);
  check(typeof record?.sourcePathAtPackaging === "string" && record.sourcePathAtPackaging.startsWith("repository:"), `files manifest source role is not repository-relative: ${requiredRecord}`);
}
for (const historicalFile of ["adjudicate_v45.py", "stamp_v45.py", "qa_v45.py", "qa_interaction_affordance.json", "qa_report_postpublication_hardened.json", "recompute_summary.json"]) {
  const relativePath = `report/release-v4.5/${historicalFile}`;
  const record = (manifest.files || []).find((item) => item.relativePath === relativePath);
  check(record?.kind === "historical_release_reference", `files manifest historical kind is missing: ${relativePath}`);
  check(Array.isArray(record?.roles) && record.roles.some((role) => String(role).includes("不是v4.5.1当前QA")), `files manifest historical role is missing: ${relativePath}`);
}
for (const item of manifest.files || []) {
  check(typeof item.relativePath === "string" && item.relativePath && !item.relativePath.startsWith("/") && !item.relativePath.includes("\\") && !item.relativePath.includes("\0"), `unsafe files manifest path: ${item.relativePath ?? "missing"}`);
  const path = resolve(packageRoot, item.relativePath || "__missing__");
  check(staysWithin(repo, path), `files manifest path escapes repository: ${item.relativePath ?? "missing"}`);
  check(existsSync(path), `manifest target missing: ${item.relativePath}`);
  if (existsSync(path)) {
    check(statSync(path).size === item.bytes, `size mismatch: ${item.relativePath}`);
    check(sha(path) === item.sha256, `SHA mismatch: ${item.relativePath}`);
    check(statSync(path).size < 100 * 1024 * 1024, `file reaches GitHub 100 MiB threshold: ${item.relativePath}`);
    check(!/\.(mp4|mov|m4v|avi|mkv|webm)$/i.test(item.relativePath), `video file included: ${item.relativePath}`);
  }
}

const videoIndexPath = processVideoIndexPath;
check(existsSync(videoIndexPath), "process video index is missing");
const videoIndexText = existsSync(videoIndexPath) ? readFileSync(videoIndexPath, "utf8") : "{}";
let videoIndex = {};
try { videoIndex = JSON.parse(videoIndexText); } catch (error) { failures.push(`process video index is invalid JSON: ${error.message}`); }
check(!videoIndexText.includes("/Users/"), "process video index contains a local absolute path");
check(!videoIndexText.includes("file://"), "process video index contains a file URL");
check(videoIndex.reportVersion === "4.5.1", "process video index reportVersion is not 4.5.1");
check(videoIndex.scope?.toolCount === 5 && videoIndex.scope?.taskCount === 6, "process video scope is not 5 tools x 6 tasks");
check(videoIndex.summary?.fileCount === 8, "process video index file count is not 8");
check(videoIndex.summary?.totalBytes === 7399913834, "process video index total bytes mismatch");
check(videoIndex.publication?.included === false, "process videos are incorrectly marked as included");
check(videoIndex.publication?.requestUrl === "https://github.com/zhikunqingtao/aireport/issues", "process video request URL mismatch");
check(Array.isArray(videoIndex.files) && videoIndex.files.length === 8, "process video index does not contain exactly 8 file records");
check(new Set((videoIndex.files || []).map((item) => item.fileName)).size === 8, "process video index contains duplicate file names");
check((videoIndex.files || []).every((item) => typeof item.fileName === "string" && item.fileName && !item.fileName.startsWith("/") && !item.fileName.includes("/") && !item.fileName.includes("\\")), "process video index contains a path instead of a portable file name");
check((videoIndex.files || []).every((item) => /^[0-9a-f]{64}$/.test(item.sha256 || "")), "process video index contains an invalid SHA-256");
check((videoIndex.files || []).reduce((sum, item) => sum + Number(item.bytes || 0), 0) === 7399913834, "process video item bytes do not sum to declared total");

const excluded = readJson(join(manifestsDir, "excluded-files.json"));
const excludedVideos = new Map((excluded.files || [])
  .filter((item) => item.reason === "video_explicitly_excluded")
  .map((item) => [item.relativeToSourceRoot, item]));
check(excludedVideos.size === 8, `excluded video count=${excludedVideos.size} expected 8`);
for (const item of videoIndex.files || []) {
  const excludedItem = excludedVideos.get(item.fileName);
  check(Boolean(excludedItem), `process video is absent from excluded-files: ${item.fileName}`);
  if (excludedItem) {
    check(excludedItem.bytes === item.bytes, `process video byte mismatch against excluded-files: ${item.fileName}`);
    check(excludedItem.sha256 === item.sha256, `process video SHA mismatch against excluded-files: ${item.fileName}`);
  }
}

const sumsPath = join(packageRoot, "manifests", "SHA256SUMS.txt");
const sumPaths = new Set();
for (const line of readFileSync(sumsPath, "utf8").trim().split("\n")) {
  const match = line.match(/^([0-9a-f]{64})  (.+)$/);
  check(Boolean(match), `invalid SHA256SUMS line: ${line}`);
  if (!match) continue;
  check(!sumPaths.has(match[2]), `duplicate SHA256SUMS path: ${match[2]}`);
  sumPaths.add(match[2]);
  const path = join(packageRoot, match[2]);
  check(existsSync(path), `SHA256SUMS target missing: ${match[2]}`);
  if (existsSync(path)) check(sha(path) === match[1], `SHA256SUMS mismatch: ${match[2]}`);
}

const actualFiles = walkFiles(packageRoot);
const actualRelativePaths = new Set(actualFiles
  .map((path) => relative(packageRoot, path).split(sep).join("/"))
  .filter((path) => path !== "manifests/SHA256SUMS.txt"));
for (const path of actualRelativePaths) check(sumPaths.has(path), `physical file omitted from SHA256SUMS: ${path}`);
for (const path of sumPaths) check(actualRelativePaths.has(path), `SHA256SUMS lists a non-physical file: ${path}`);
for (const path of actualFiles) {
  const relativePath = relative(packageRoot, path).split(sep).join("/");
  check(statSync(path).size < 100 * 1024 * 1024, `physical file reaches GitHub 100 MiB threshold: ${relativePath}`);
  check(!/\.(mp4|mov|m4v|avi|mkv|webm)$/i.test(relativePath), `physical video file included: ${relativePath}`);
}

if (failures.length) {
  console.error(JSON.stringify({ status: "failed", failureCount: failures.length, failures }, null, 2));
  process.exit(1);
}
console.log(JSON.stringify({
  status: "passed",
  activeVersion: "4.5.1",
  publicationMode: "single_version",
  reportSha256: sha(reportPath),
  manifestRecords: count(manifest.files),
  pathMapEntries: count(pathMap),
  processVideoIndexRecords: count(videoIndex.files),
  sha256Entries: sumPaths.size,
}, null, 2));
