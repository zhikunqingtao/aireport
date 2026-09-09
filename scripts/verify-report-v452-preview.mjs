#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve, join } from "node:path";
import { gunzipSync } from "node:zlib";

const args = process.argv.slice(2);
const repoIndex = args.indexOf("--repo");
const repo = resolve(repoIndex >= 0 ? args[repoIndex + 1] : ".");
const release = join(repo, "docs", "case-studies", "assets", "unitree-office-benchmark", "report", "release-v4.5");
const portablePath = join(repo, "docs", "case-studies", "AI办公工具对比测评_宇树科技_截至2026-08-30.html");
const selfContainedPath = join(release, "..", "source-self-contained-v4.5.html");
const finalDataPath = join(release, "report_v4.5_final.json");
const uiPath = join(release, "report.ui.json");
const cssPath = join(release, "report.css");
const jsPath = join(release, "report.js");
const templatePath = join(release, "report.template.html");
const fontPath = join(release, "fonts", "aireport-editorial-serif-semibold-subset.woff2");
const pathMapPath = join(repo, "docs", "case-studies", "assets", "unitree-office-benchmark", "manifests", "path-map.json");
const failures = [];
const pass = [];
const check = (condition, message) => {
  if (condition) pass.push(message);
  else failures.push(message);
};
const count = (value) => Array.isArray(value) ? value.length : Object.keys(value || {}).length;
const stable = (value) => {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  return value;
};
const equal = (left, right) => JSON.stringify(stable(left)) === JSON.stringify(stable(right));
const sha = (value) => createHash("sha256").update(value).digest("hex");

function decodeReport(path) {
  const html = readFileSync(path, "utf8");
  const match = html.match(/<script id="report-data" type="application\/json"([^>]*)>([\s\S]*?)<\/script>/);
  if (!match) throw new Error(`report-data payload missing: ${path}`);
  const source = match[2].trim();
  const json = match[1].includes('data-encoding="gzip-base64"')
    ? gunzipSync(Buffer.from(source, "base64")).toString("utf8")
    : source;
  return { html, data: JSON.parse(json) };
}

for (const path of [portablePath, selfContainedPath, finalDataPath, uiPath, cssPath, jsPath, templatePath, fontPath, pathMapPath]) {
  check(existsSync(path), `存在：${path.slice(repo.length + 1)}`);
}

if (!failures.length) {
  const portable = decodeReport(portablePath);
  const selfContained = decodeReport(selfContainedPath);
  const finalData = JSON.parse(readFileSync(finalDataPath, "utf8"));
  const ui = JSON.parse(readFileSync(uiPath, "utf8"));
  const pathMap = JSON.parse(readFileSync(pathMapPath, "utf8"));
  const css = readFileSync(cssPath, "utf8");
  const js = readFileSync(jsPath, "utf8");
  const template = readFileSync(templatePath, "utf8");
  const expectedCounts = {
    artifacts: 30,
    scenarioRuns: 180,
    coverageItems: 324,
    findings: 200,
    evidence: 741,
    media: 710,
    facts: 32,
    sources: 11,
  };
  const expectedLimitations = [
    "五张回应截图是各AI工具阅读报告后生成的自评，不是产品公司、负责人或员工的正式声明；本报告不宣称任何厂商已认可。",
    "仅覆盖宇树科技主题的一次连续六任务链和30件固定终稿，不能外推为产品总体能力、稳定生成率或未来版本表现。",
    "五款均按用户确认使用测试时点各自可选的最强配置，但模型、算力、成本、工具权限和自动路由并未统一，因此不是严格控制实验。",
    "Excel只核对公开列示的32项核心事实；不等同于五本工作簿全部数字的逐项全量鉴证。",
    "原生应用体验固定在macOS 26.5.2、Office 16.112.3与Chrome 152；Windows PowerPoint和独立重新下载尚未交叉验证。",
    "本报告由单一评审者完成；判断步长压力测试不是置信区间、抽样误差、评审者一致性或厂商能力区间。",
  ];
  const reviewerDisclosure = "单一评审者；未测量评审者间一致性。现有公开材料未具体列明评测者与参评工具之间是否存在开发、雇佣、投资、代理或委托关系。请结合冻结原件与可复算数据独立判断。";
  const normalizePaths = (value) => {
    if (Array.isArray(value)) return value.map(normalizePaths);
    if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizePaths(item)]));
    return typeof value === "string" && pathMap[value] ? pathMap[value] : value;
  };

  for (const [key, expected] of Object.entries(expectedCounts)) {
    check(count(portable.data[key]) === expected, `Pages ${key}=${expected}`);
    check(count(selfContained.data[key]) === expected, `自包含 ${key}=${expected}`);
  }
  check(portable.data.contentInventory?.scenarioRecords?.count === 202, "Pages 综合记录=202");
  check(selfContained.data.contentInventory?.scenarioRecords?.count === 202, "自包含 综合记录=202");

  for (const key of ["qualityScores", "scores", "rankings", "deliveryGates", "rankingPerspectives", "facts", "methodology", "contentInventory"]) {
    check(equal(normalizePaths(portable.data[key]), normalizePaths(finalData[key])), `Pages 冻结子树未变：${key}`);
    check(equal(normalizePaths(selfContained.data[key]), normalizePaths(finalData[key])), `自包含冻结子树未变：${key}`);
  }
  check(equal(portable.data.meta?.ui, selfContained.data.meta?.ui), "双版本 UI 配置完全一致");
  check(equal(portable.data.meta?.ui, { ...ui, hero: portable.data.meta.ui.hero }), "嵌入 UI 使用唯一配置源（仅动态 Hero 白名单）");
  check(equal(ui.toolLinks, [
    { label: "千问办公", url: "https://qwenwork.cn/" },
    { label: "Qoder", url: "https://qoder.cn/" },
    { label: "豆包办公", url: "https://www.doubao.com/work/group" },
    { label: "WorkBuddy", url: "https://www.workbuddy.cn/" },
    { label: "ZhikunCode", url: "https://github.com/zhikunqingtao/zhikuncode/" },
  ]), "五款参评工具链接对应正确");
  check(portable.data.meta?.schemaVersion === "4.5.1" && portable.data.meta?.dataVersion === "4.5.1", "Pages 沿用 v4.5.1 冻结数据版本");
  check(selfContained.data.meta?.schemaVersion === "4.5.1" && selfContained.data.meta?.dataVersion === "4.5.1", "自包含版沿用 v4.5.1 冻结数据版本");
  check(portable.data.meta?.presentationVersion === "4.5.2" && portable.data.meta?.version.includes("4.5.2"), "Pages 展示版本为 v4.5.2");
  check(selfContained.data.meta?.presentationVersion === "4.5.2" && selfContained.data.meta?.version.includes("4.5.2"), "自包含版展示版本为 v4.5.2");
  check(portable.data.meta?.publicationVariant === "github_portable_v4.5.2", "Pages 发布变体标识正确");
  check(selfContained.data.meta?.publicationVariant === "self_contained_v4.5.2", "自包含发布变体标识正确");
  check(equal(finalData.meta?.limitations, expectedLimitations), "六条关键限制原文完整保留");
  check(equal(portable.data.meta?.limitations, expectedLimitations) && equal(selfContained.data.meta?.limitations, expectedLimitations), "双版本均完整保留六条关键限制");
  check(finalData.meta?.reviewerDisclosure === reviewerDisclosure && portable.data.meta?.reviewerDisclosure === reviewerDisclosure && selfContained.data.meta?.reviewerDisclosure === reviewerDisclosure, "单评审者与未具体列明关系的披露一致");
  check(finalData.contentInventory?.challenges?.entry === "第5章工具自评异议与复核处理", "异议复核入口指向第5章");
  check(finalData.contentInventory?.challengeResponses?.entry === "第5章五张工具自评原始截图", "工具自评截图入口指向第5章");
  check(finalData.presentation?.printPageFurniture?.version === "v4.5.2", "打印配置版本为 v4.5.2");
  check(finalData.presentation?.printPageFurniture?.summaryExcerptNote?.includes("第05章") && !finalData.presentation?.printPageFurniture?.summaryExcerptNote?.includes("第08章"), "摘要打印提示使用当前章节编号");

  const gateCounts = { G0: 0, G1: 0, G2: 0 };
  for (const gate of Object.values(portable.data.deliveryGates?.artifacts || {})) {
    const base = String(gate.code || "G1").startsWith("G2") ? "G2" : String(gate.code || "G1");
    if (base in gateCounts) gateCounts[base] += 1;
  }
  check(equal(gateCounts, { G0: 3, G1: 20, G2: 7 }), "交付闸门分布保持 G0 3 / G1 20 / G2 7");

  const requiredHooks = [
    "executive-snapshot", "nav-progress", "nav-subnav", "key-limitations", "heat-cell-shell",
    "modal-position", "data-dialog-step", "data-evidence-zoom", "data-lazy-render",
  ];
  for (const hook of requiredHooks) check(js.includes(hook) || portable.html.includes(hook), `交互标记存在：${hook}`);
  check(template.includes('id="app" aria-busy="true"') && !template.includes('id="app" aria-live='), "全应用不再使用 aria-live");
  check(template.includes('id="app-status"') && template.includes('role="status"'), "独立状态播报区存在");
  check(js.includes('<details class="prompt-step" open>'), "六项任务协议默认展开");
  check(js.includes('ranking-perspective-${emphasis}') && js.includes('data-ranking-role="${role}"') && js.includes("探索性 · 非因果"), "正式与探索性排名角色分离");
  check(js.includes("materializeForPrint") && js.includes('"full-record-print"'), "完整打印前物化懒加载内容");
  check(js.includes("state.evidenceLimit = evidence.length"), "完整打印自动展开全部741条证据");
  check(js.includes('loading="eager" decoding="sync" fetchpriority="high"'), "完整打印证据图禁用离屏懒加载");
  check(js.includes('dataset.printReady = "true"') && js.includes("await prepareForPrint(profile)"), "打印按钮等待证据图准备完成");
  check(js.includes("function evidenceIsImage") && js.includes("结构化记录 · 无图像缩略图"), "结构化证据不会被误渲染为破损图片");
  check(!js.includes("无需点击切换") && !js.includes("已全部展开"), "报告不再使用界面实现说明腔");
  check(js.includes('text("footer"'), "页脚使用共享 UI 配置");
  check(!String(ui.sections?.evidence?.copy || "").includes("全部内嵌"), "共享证据文案不误称 Pages 媒体全部内嵌");
  check(js.includes('class="participant-links"') && js.includes('target="_blank" rel="noopener noreferrer"'), "参评工具链接具有明确入口与安全的新窗口属性");
  check(css.includes(".participant-links { display: none !important; }"), "参评工具网页入口不进入打印版");

  const numericWeights = [...css.matchAll(/font-weight:\s*(\d+)/g)].map((match) => Number(match[1]));
  check(numericWeights.every((weight) => [400, 500, 600, 700].includes(weight)), "CSS 数字字重仅使用 400/500/600/700");
  check(!/font-size:\s*(?:8|9|10)px\b/.test(css), "屏幕 CSS 不再声明 8–10px 微型文字");
  const elevenPixelLines = css.split("\n").filter((line) => /font-size:\s*11px\b/.test(line));
  check(elevenPixelLines.length === 2 && elevenPixelLines.every((line) => line.includes("score-axis")), "11px 仅用于分数坐标轴");
  check(css.includes('@font-face') && css.includes('font-family: "Aireport Editorial Serif"'), "出版标题字体已声明");
  check(portable.html.includes("data:font/woff2;base64,"), "Pages HTML 内嵌标题字体，无网络请求");
  check(selfContained.html.includes("data:font/woff2;base64,"), "自包含 HTML 内嵌标题字体，无网络请求");
  check(!/@import\b/i.test(css.replace(/\/\*[\s\S]*?\*\//g, "")), "CSS 不使用远程 @import");
  check(statSync(fontPath).size <= 350 * 1024, "标题字体子集不超过 350 KiB");
  check(statSync(selfContainedPath).size <= 40 * 1024 * 1024, "自包含 HTML 不超过 40 MiB");
  check(!portable.html.includes("/Users/") && !portable.html.includes("file://"), "Pages HTML 无本机绝对路径或 file URL");
  const scoreMap = (data) => Object.fromEntries(Object.entries(data.qualityScores?.artifacts || {}).sort(([left], [right]) => left.localeCompare(right)).map(([id, record]) => [id, Number(record.qualityScore)]));
  const scoreFingerprint = sha(JSON.stringify(stable(scoreMap(portable.data))));
  check(scoreFingerprint === "8d3d3bdd8af763c6a3c0e3ec64d38798971a9d5097de1c3db81b932c630d393c", "30件终稿评分指纹保持一致");
}

const result = { status: failures.length ? "failed" : "passed", checks: pass.length + failures.length, passed: pass.length, failures };
console.log(JSON.stringify(result, null, 2));
if (failures.length) process.exit(1);
