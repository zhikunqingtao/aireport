#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { gunzipSync } from "node:zlib";

const args = process.argv.slice(2);
const repoArg = args.indexOf("--repo");
const repo = resolve(repoArg >= 0 ? args[repoArg + 1] : ".");
const caseDir = join(repo, "docs", "case-studies");
const packageRoot = join(caseDir, "assets", "unitree-office-benchmark");
const reportPath = join(caseDir, "AI办公工具对比测评_宇树科技_截至2026-08-30.html");
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };
const sha = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

check(existsSync(packageRoot), "single-version evidence package is missing");
check(!existsSync(join(caseDir, "assets", "unitree-office-benchmark-v4.3")), "legacy versioned package directory still exists");
check(existsSync(reportPath), "portable report is missing");
check(!existsSync(join(packageRoot, ".DS_Store")), "Finder .DS_Store remains at package root");
check(!existsSync(join(packageRoot, "report", ".DS_Store")), "Finder .DS_Store remains in report directory");

const html = readFileSync(reportPath, "utf8");
check(!html.includes("/Users/"), "portable report contains /Users/ path");
check(!html.includes("file://"), "portable report contains file:// URL");
check(!html.includes("unitree-office-benchmark-v4.3"), "portable report references legacy package directory");
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

const report = join(packageRoot, "report");
for (const required of [
  "source-self-contained-v4.5.html",
  "activity-report-data-v4.5.json",
  "portable-report-data-v4.5.json",
  "release-v4.5/report_v4.5_final.json",
  "release-v4.5/qa_report_postpublication_hardened.json",
]) check(existsSync(join(report, required)), `required v4.5 file missing: ${required}`);
for (const forbidden of [
  "history", "pdfs", "build-and-qa", "release-v4.3", "release-v4.4",
  "source-self-contained-v4.3.html", "source-self-contained-v4.4.html",
  "activity-report-data-v4.3.json", "activity-report-data-v4.4.json",
  "portable-report-data-v4.3.json", "portable-report-data-v4.4.json",
  "release-v4.5/history", "release-v4.5/v4.4-v4.5_变更表.md",
  "release-v4.5/AI办公工具对比测评_宇树科技_截至2026-08-30_v4.5_自包含版.html",
]) check(!existsSync(join(report, forbidden)), `historical or duplicate report artifact remains: ${forbidden}`);

const pathMap = JSON.parse(readFileSync(join(packageRoot, "manifests", "path-map.json"), "utf8"));
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

const manifest = JSON.parse(readFileSync(join(packageRoot, "manifests", "files.json"), "utf8"));
check(manifest.activeVersion === "4.5", "files manifest activeVersion is not 4.5");
check(manifest.publicationMode === "single_version", "files manifest is not marked single_version");
check(manifest.packageDirectory === "unitree-office-benchmark", "files manifest packageDirectory mismatch");
for (const item of manifest.files || []) {
  const path = resolve(packageRoot, item.relativePath);
  check(existsSync(path), `manifest target missing: ${item.relativePath}`);
  if (existsSync(path)) {
    check(statSync(path).size === item.bytes, `size mismatch: ${item.relativePath}`);
    check(sha(path) === item.sha256, `SHA mismatch: ${item.relativePath}`);
    check(statSync(path).size < 100 * 1024 * 1024, `file reaches GitHub 100 MiB threshold: ${item.relativePath}`);
    check(!/\.(mp4|mov|m4v|avi|mkv|webm)$/i.test(item.relativePath), `video file included: ${item.relativePath}`);
  }
}

const sumsPath = join(packageRoot, "manifests", "SHA256SUMS.txt");
for (const line of readFileSync(sumsPath, "utf8").trim().split("\n")) {
  const match = line.match(/^([0-9a-f]{64})  (.+)$/);
  check(Boolean(match), `invalid SHA256SUMS line: ${line}`);
  if (!match) continue;
  const path = join(packageRoot, match[2]);
  check(existsSync(path), `SHA256SUMS target missing: ${match[2]}`);
  if (existsSync(path)) check(sha(path) === match[1], `SHA256SUMS mismatch: ${match[2]}`);
}

if (failures.length) {
  console.error(JSON.stringify({ status: "failed", failureCount: failures.length, failures }, null, 2));
  process.exit(1);
}
console.log(JSON.stringify({
  status: "passed",
  activeVersion: "4.5",
  publicationMode: "single_version",
  reportSha256: sha(reportPath),
  manifestRecords: count(manifest.files),
  pathMapEntries: count(pathMap),
}, null, 2));
