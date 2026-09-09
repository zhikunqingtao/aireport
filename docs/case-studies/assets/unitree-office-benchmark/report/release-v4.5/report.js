(async () => {
  "use strict";

  const reportDataNode = document.getElementById("report-data");
  let reportDataText = reportDataNode.textContent;
  if (reportDataNode.dataset.encoding === "gzip-base64") {
    if (typeof DecompressionStream !== "function") {
      throw new Error("当前浏览器不支持内嵌报告数据的无损解压；请使用核验环境中的Chrome打开。");
    }
    const binary = atob(reportDataText.trim());
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    reportDataText = await new Response(stream).text();
  }
  const RAW = JSON.parse(reportDataText);
  const UI = RAW.meta?.ui || {};
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const arr = (value) => Array.isArray(value) ? value : value && typeof value === "object" ? Object.values(value) : [];
  const obj = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};
  const esc = (value) => String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  const num = (value) => Number.isFinite(Number(value)) ? Number(value) : null;
  const fmt = (value, digits = 1) => num(value) === null ? "—" : Number(value).toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
  const slug = (value) => String(value ?? "").replace(/[^a-zA-Z0-9_-]/g, "-");
  const compact = (values) => [...new Set(values.filter((value) => value !== undefined && value !== null && value !== ""))];
  const safeHttpUrl = (value) => { try { const url = new URL(String(value)); return ["http:", "https:"].includes(url.protocol) ? url.href : ""; } catch (_) { return ""; } };
  const safeAssetUrl = (value) => {
    const raw = String(value || "").trim();
    if (!raw) return "";
    if (/^data:image\/(?:png|jpe?g|webp|gif);base64,/i.test(raw)) return raw;
    const remote = safeHttpUrl(raw);
    if (remote) return remote;
    const normalized = raw.replaceAll("\\", "/");
    if (normalized.startsWith("/") || normalized.split("/").includes("..") || normalized.includes("\0")) return "";
    return normalized;
  };
  const text = (path, fallback = "") => {
    let current = UI;
    for (const part of path.split(".")) current = current?.[part];
    return current ?? fallback;
  };
  const bytes = (value) => {
    const n = num(value);
    if (n === null) return "—";
    if (n >= 1024 ** 3) return `${fmt(n / 1024 ** 3, 2)} GB`;
    if (n >= 1024 ** 2) return `${fmt(n / 1024 ** 2, 2)} MB`;
    if (n >= 1024) return `${fmt(n / 1024, 1)} KB`;
    return `${n} B`;
  };
  const asEntries = (value) => Array.isArray(value)
    ? value.map((item, index) => [String(item?.id || item?.key || index), item])
    : Object.entries(obj(value));

  const artifacts = arr(RAW.artifacts);
  const artifactById = new Map(artifacts.map((item, index) => {
    if (!item.id) item.id = `artifact:${slug(item.tool)}:${item.kind || index}`;
    return [item.id, item];
  }));
  const tools = RAW.meta?.toolOrder || RAW.meta?.tools || compact(artifacts.map((item) => item.tool));
  const kinds = RAW.meta?.kindOrder || RAW.meta?.kinds || ["excel", "word", "ppt", "image", "ink", "html"].filter((kind) => artifacts.some((item) => item.kind === kind));
  const kindLabels = { excel: "Excel", word: "Word", ppt: "PPT", image: "普通信息图", ink: "水墨信息图", html: "交互 HTML", ...(RAW.meta?.kindLabels || {}) };
  const toolColor = new Map(tools.map((tool, index) => [tool, `var(--tool-${(index % 5) + 1})`]));
  const findings = arr(RAW.findings);
  const scenarios = arr(RAW.scenarios);
  const scenarioMap = new Map(scenarios.map((item) => [item.id, item]));
  const scenarioRuns = arr(RAW.scenarioRuns);
  const coverageItems = arr(RAW.coverageItems);
  const evidence = arr(RAW.evidence);
  const media = arr(RAW.media);
  const processRecords = arr(RAW.meta?.processRecords?.records);
  const configurationUsage = RAW.meta?.configurationUsageEvidence || {};
  const presentation = RAW.presentation || {};
  const testProtocol = obj(RAW.testProtocol);
  const challengeRoot = obj(RAW.challenges);
  const challengeItems = arr(challengeRoot.items);
  const challengeResponses = arr(challengeRoot.responses);
  const symmetryBatches = arr(challengeRoot.symmetryBatches);
  const publicationLabels = { ...(presentation.publicationLabels || {}) };
  const visualRegistry = new Map(arr(presentation.visualRegistry).map((item) => [item.id, item]));
  const contentInventory = RAW.contentInventory || {};
  const evidenceMap = new Map(evidence.map((item) => [item.id, item]));
  const mediaMap = new Map(Array.isArray(RAW.media)
    ? media.map((item, index) => [item.id || `media:${index}`, item])
    : Object.entries(obj(RAW.media)));
  const criteriaByKind = obj(RAW.criteriaDefinitions);
  const criteriaDefinitionMap = new Map(Object.values(criteriaByKind).flatMap((value) => arr(value.criteria || value)).map((item) => [item.id, item]));
  const rubricSubtests = Array.isArray(RAW.rubricSubtests) ? RAW.rubricSubtests : [];

  const state = {
    weightMode: "practical",
    rankingPerspective: "standalone",
    browserType: "finding",
    tool: "all",
    kind: "all",
    gate: "all",
    severity: "all",
    query: "",
    evidenceLimit: 36,
    printProfile: new URLSearchParams(location.search).get("print") || "formal",
  };
  const dialogReturnFocus = new WeakMap();
  const materializedSections = new Set();
  let currentArtifactIndex = -1;
  let currentEvidenceIndex = -1;
  let printClosedDetails = [];
  let fullPrintPreparation = null;

  function announce(message) {
    const target = $("#app-status");
    if (!target) return;
    target.textContent = "";
    window.requestAnimationFrame(() => { target.textContent = String(message || ""); });
  }

  function publicationLabel(value) {
    if (value === null || value === undefined) return "";
    const key = String(value);
    return publicationLabels[key] || key;
  }

  function humanizeText(value) {
    let output = String(value ?? "");
    Object.entries(publicationLabels)
      .sort(([a], [b]) => b.length - a.length)
      .forEach(([key, label]) => { output = output.replaceAll(key, label); });
    return output;
  }

  function visualMeta(id) {
    return visualRegistry.get(id) || { id, number: "", title: "", sourceNote: "", scopeNote: "" };
  }

  function figureCaption(id) {
    const item = visualMeta(id);
    return `<figcaption class="publication-caption" id="caption-${esc(id)}"><strong><span>${esc(item.number)}</span>${esc(item.title)}</strong><small><b>口径：</b>${esc(item.scopeNote || "—")}</small><small><b>来源：</b>${esc(item.sourceNote || "—")}</small></figcaption>`;
  }

  function tableCaption(id) {
    const item = visualMeta(id);
    return `<caption class="publication-caption" id="caption-${esc(id)}"><strong><span>${esc(item.number)}</span>${esc(item.title)}</strong><small><b>口径：</b>${esc(item.scopeNote || "—")}</small><small><b>来源：</b>${esc(item.sourceNote || "—")}</small></caption>`;
  }

  function axisMarkup(className = "score-axis") {
    return `<span class="${className}" aria-hidden="true">${[0, 25, 50, 75, 100].map((tick) => `<i style="--tick:${tick}%"><b>${tick}</b></i>`).join("")}</span>`;
  }

  function sensitivityGroupLabel(row) {
    return row?.sensitivityGroup || row?.uncertaintyGroup ? `近分组 ${row.sensitivityGroup || row.uncertaintyGroup}` : "";
  }

  function sensitivityRankLabel(row) {
    const best = num(row?.possibleBestRank);
    const worst = num(row?.possibleWorstRank);
    if (best === null || worst === null) return row?.displayRank || `点估计第${row?.rank || "—"}`;
    return best === worst ? `单项一步情景：第${best}` : `单项一步情景：第${best}—${worst}`;
  }

  function reviewResolution(row) {
    const score = num(row?.score) ?? 0;
    const lower = Math.max(0, Math.min(100, num(row?.reviewResolutionLower) ?? score));
    const upper = Math.max(lower, Math.min(100, num(row?.reviewResolutionUpper) ?? score));
    return { lower, upper };
  }

  function rankingStyle(row, extra = "") {
    const range = reviewResolution(row);
    return `--score:${num(row?.score) ?? 0};--lower:${range.lower};--upper:${range.upper};--range:${range.upper - range.lower};${extra}`;
  }

  function shortSourceTitle(source) {
    const title = String(source?.title || source?.name || source?.id || "来源");
    if (title.includes("招股说明书")) return "招股说明书";
    if (title.includes("上市公告书")) return "上市公告书";
    if (title.includes("上市通知")) return "上交所上市通知";
    if (title.includes("官方") || title.includes("Unitree")) return "宇树科技官方资料";
    return title;
  }

  function factAttribute(fact) {
    return compact([publicationLabel(fact.status), publicationLabel(fact.factClass), publicationLabel(fact.auditState)]).join("｜") || "—";
  }

  function factSourceLocator(fact, source) {
    const page = fact.page || fact.locator;
    return `${shortSourceTitle(source)}${page ? ` p.${page}` : "（网页）"}`;
  }

  function shortReason(value, limit = 34) {
    const raw = String(value || "").replace(/\s+/g, " ").trim();
    const first = raw.split(/[。；;]/)[0] || raw;
    return first.length > limit ? `${first.slice(0, limit)}…` : first;
  }

  function artifactFor(tool, kind) {
    return artifacts.find((item) => item.tool === tool && item.kind === kind);
  }

  function valueForFormalScore(record) {
    if (!record) return null;
    const keys = ["independentScore", "standaloneScore", "continuousScore", "qualityScore", "score", "finalScore", "baseScore"];
    for (const key of keys) if (num(record[key]) !== null) return num(record[key]);
    const nested = record.independent || record.perspectives?.independent;
    if (num(nested) !== null) return num(nested);
    if (nested && typeof nested === "object") return valueForFormalScore(nested);
    return null;
  }

  function qualityRecord(artifact) {
    const source = RAW.qualityScores?.artifacts ?? RAW.qualityScores;
    if (Array.isArray(source)) return source.find((item) => (item.artifactId || item.id) === artifact.id) || null;
    return obj(source)[artifact.id] || null;
  }

  function legacyScoreRecord(artifact) {
    const source = RAW.scores?.artifacts || {};
    if (Array.isArray(source)) return source.find((item) => (item.artifactId || item.id) === artifact.id) || null;
    return obj(source)[artifact.id] || null;
  }

  function artifactScore(artifact) {
    return valueForFormalScore(qualityRecord(artifact))
      ?? valueForFormalScore(legacyScoreRecord(artifact))
      ?? valueForFormalScore(artifact);
  }

  function gateRecord(artifact) {
    const source = RAW.deliveryGates?.artifacts ?? RAW.deliveryGates;
    if (Array.isArray(source)) return source.find((item) => (item.artifactId || item.id) === artifact.id) || {};
    const found = obj(source)[artifact.id];
    if (typeof found === "string") return { gate: found };
    return found || {};
  }

  function gateCode(artifact) {
    const record = gateRecord(artifact);
    return String(record.gate || record.code || record.level || artifact.deliveryGate || "G0").toUpperCase();
  }

  function gateBase(code) {
    const match = String(code || "").toUpperCase().match(/G[012]/);
    return match ? match[0] : "G0";
  }

  function gateDisplay(code) {
    const raw = String(code || "").toUpperCase();
    return raw === "G2-MAC" ? "G2-Mac" : raw;
  }

  function gateChip(code, note = "") {
    const base = gateBase(code);
    const labels = { G0: "G0 · 可按常规复核使用", G1: "G1 · 修正后可用", G2: "G2 · 禁止未复核交付" };
    return `<span class="gate-chip" data-gate="${base}" title="${esc(note)}">${esc(String(code).toUpperCase() === base ? labels[base] : gateDisplay(code))}</span>`;
  }

  function gateCounts() {
    const counts = { G0: 0, G1: 0, G2: 0 };
    artifacts.forEach((artifact) => { counts[gateBase(gateCode(artifact))] += 1; });
    return counts;
  }

  function gateSummaryMarkup(extraClass = "") {
    const meanings = {
      G0: "未发现交付前必须修正的重大问题，仍需常规专业复核。",
      G1: "存在明确局部问题，完成针对性修正和复核后使用。",
      G2: "存在核心错误或重大交付风险，禁止未经独立复核直接使用。",
    };
    return `<div class="gate-summary ${esc(extraClass)}">${Object.entries(gateCounts()).map(([gate, count]) => `<article class="gate-summary-card panel" data-gate="${gate}">${gateChip(gate)}<strong>${count}</strong><span>件终稿${gate === "G2" ? "（含G2-Mac）" : ""}</span><p>${esc(meanings[gate])}</p></article>`).join("")}</div>`;
  }

  function gateSymbol(code) {
    const raw = String(code || "").toUpperCase();
    if (raw.includes("MAC")) return "◇";
    return ({ G0: "✓", G1: "△", G2: "!" })[gateBase(raw)] || "·";
  }

  function allScenarioRecords() {
    const merged = [...scenarioRuns, ...crossArtifactRubricItems().filter((item) => item.artifactId || item.artifactIds)];
    const seen = new Set();
    return merged.filter((item, index) => {
      const key = item?.id || item?.runId || item?.subtestId || `${item?.artifactId || arr(item?.artifactIds).join("+") || "scenario"}:${item?.action || item?.test || item?.scenario || item?.title || index}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function rankingNode(perspective, mode) {
    const normalized = perspective === "firstOrigin" ? "firstOrigin" : "standalone";
    const officialKey = `${normalized}_${mode}`;
    if (RAW.rankings?.[officialKey]) return RAW.rankings[officialKey];
    const legacyKey = mode === "practical" ? "independent_practical" : "independent_equalTask";
    if (normalized === "standalone" && RAW.rankings?.[legacyKey]) return RAW.rankings[legacyKey];
    const root = RAW.rankingPerspectives || {};
    const results = root.results || root;
    const modeAliases = mode === "practical" ? ["practical", "balanced", "practicalWeighted"] : ["equalTask", "equal", "equal_task"];
    const aliases = normalized === "standalone" ? ["standalone", "independent", "independentFinal"] : ["firstOrigin", "rootCause", "deduplicated"];
    for (const alias of aliases) {
      const branch = results[alias] || root.perspectives?.[alias] || root.rankings?.[alias];
      if (!branch) continue;
      for (const modeAlias of modeAliases) if (branch[modeAlias]) return branch[modeAlias];
    }
    for (const key of [`${normalized}:${mode}`, `${normalized}_${mode}`, `${normalized}-${mode}`]) if (results[key]) return results[key];
    return null;
  }

  function weightsFor(mode, perspective = state.rankingPerspective) {
    const node = rankingNode(perspective, mode);
    if (node?.weights) return node.weights;
    if (RAW.rankings?.[mode]?.weights) return RAW.rankings[mode].weights;
    if (mode === "practical") return { excel: .25, word: .20, ppt: .20, image: .10, ink: .10, html: .15 };
    return Object.fromEntries(kinds.map((kind) => [kind, 1 / kinds.length]));
  }

  function rankingRows(perspective = state.rankingPerspective, mode = state.weightMode) {
    const node = rankingNode(perspective, mode);
    const supplied = arr(node?.rows || node);
    if (supplied.length && supplied.every((row) => row.tool && num(row.score) !== null)) {
      return supplied.slice().sort((a, b) => (num(a.rank) ?? 999) - (num(b.rank) ?? 999) || num(b.score) - num(a.score));
    }
    const weights = weightsFor(mode, perspective);
    return tools.map((tool) => {
      const artifactScores = {};
      let total = 0;
      let knownWeight = 0;
      kinds.forEach((kind) => {
        const artifact = artifactFor(tool, kind);
        const score = artifact ? artifactScore(artifact) : null;
        artifactScores[kind] = score;
        if (score !== null) { total += score * Number(weights[kind] || 0); knownWeight += Number(weights[kind] || 0); }
      });
      return { tool, score: knownWeight ? total / knownWeight : null, artifactScores };
    }).sort((a, b) => (b.score ?? -1) - (a.score ?? -1)).map((row, index) => ({ ...row, rank: index + 1 }));
  }

  function executiveSnapshotMarkup() {
    const counts = gateCounts();
    const total = artifacts.length;
    const meta = RAW.meta || {};
    const summary = presentation.executiveSummary || {};
    const boundary = summary.scope || meta.sampleBoundary || meta.scopeStatement || "5款工具、6类任务、30件固定终稿；仅代表本次固定样本。";
    const gateLabels = new Map(arr(RAW.deliveryGates?.definitions || RAW.methodology?.deliveryGateDefinitions).map((item) => [item.code, item.label]));
    const gateGuide = ["G0", "G1", "G2"].map((code) => `${code}${gateLabels.get(code) || ""}`).join("；");
    const rankingSummary = (mode, label) => {
      const rows = rankingRows("standalone", mode).slice(0, 2);
      return `<article class="hero-ranking-brief" data-snapshot="ranking"><header><span>${esc(label)}</span><small>正式固定终稿排名</small></header><ol>${rows.map((row) => `<li><span class="hero-rank-position">${esc(row.rank)}</span><span><strong>${esc(row.tool)}</strong><small>${esc(`${sensitivityGroupLabel(row)} · ${sensitivityRankLabel(row)}`)}</small></span><b>${fmt(row.score, 1)}</b></li>`).join("")}</ol></article>`;
    };
    const gateCodes = ["G0", "G1", "G2"];
    const gateAria = gateCodes.map((code) => `${code} ${counts[code] || 0}件`).join("，");
    return `<section class="executive-snapshot" aria-labelledby="executive-snapshot-title"><header class="executive-snapshot-head"><span>核心摘要</span><h2 id="executive-snapshot-title">先判断交付风险，再阅读正式排名</h2></header><div class="executive-data-cover">
      <article class="hero-gate-figure" data-snapshot="gates"><header><span>${total}件终稿</span><strong>交付闸门分布</strong></header><dl class="hero-gate-values">${gateCodes.map((code) => `<div data-gate="${code}"><dt>${code}</dt><dd><strong>${counts[code] || 0}</strong><span>${esc(gateLabels.get(code) || "")}</span></dd></div>`).join("")}</dl><div class="hero-gate-bar" role="img" aria-label="${esc(gateAria)}">${gateCodes.map((code) => `<i data-gate="${code}" style="--gate-count:${counts[code] || 0}" aria-hidden="true"></i>`).join("")}</div><p>${esc(gateGuide)}</p></article>
      <div class="hero-summary-detail"><div class="hero-ranking-pair">${rankingSummary("practical", "均衡投研实务")}${rankingSummary("equalTask", "六任务等权")}</div><article class="hero-reading-path" data-snapshot="scope"><div><span>阅读顺序</span><strong>闸门 → 连续质量分 → 证据与方法</strong></div><p>${esc(boundary)} 完整限制见下方“关键限制”。</p></article></div>
    </div></section>`;
  }

  function resolveMedia(id) {
    let item = mediaMap.get(id); const seen = new Set();
    while (item && !item.dataUri && !item.data_uri && item.dataUriRef && !seen.has(item.dataUriRef)) {
      seen.add(item.dataUriRef); item = mediaMap.get(item.dataUriRef);
    }
    return item;
  }

  function mediaUri(id) {
    const item = resolveMedia(id);
    return item?.dataUri || item?.data_uri || "";
  }

  function evidenceUri(item) {
    return mediaUri(item?.mediaId || item?.media_id) || item?.dataUri || item?.data_uri || "";
  }

  function evidenceIsImage(item, uri = evidenceUri(item)) {
    const media = resolveMedia(item?.mediaId || item?.media_id);
    const mime = String(item?.mimeType || item?.mime_type || media?.mimeType || media?.mime_type || "").toLowerCase();
    return mime.startsWith("image/") || /^data:image\//i.test(uri) || /\.(?:avif|gif|jpe?g|png|svg|webp)(?:[?#]|$)/i.test(uri);
  }

  function evidenceIds(value) {
    return compact(arr(value).map((item) => typeof item === "string" ? item : item?.id));
  }

  function artifactPath(artifact) {
    return artifact?.path || artifact?.original?.path || "";
  }

  function artifactSha256(artifact) {
    return artifact?.sha256 || artifact?.original?.sha256 || "";
  }

  function artifactBytes(artifact) {
    return artifact?.bytes || artifact?.size || artifact?.original?.bytes || 0;
  }

  function artifactFileName(artifact) {
    const path = artifactPath(artifact).replaceAll("\\", "/");
    return artifact?.name || artifact?.filename || path.split("/").pop() || artifact?.id || "原件";
  }

  function artifactExtension(artifact) {
    const match = artifactFileName(artifact).toLowerCase().match(/\.([a-z0-9]+)$/);
    return match?.[1] || "";
  }

  function artifactHref(artifact) {
    const raw = artifactPath(artifact).trim().replaceAll("\\", "/");
    if (!raw || raw.includes("\0")) return "";
    const normalized = raw.replace(/^\.\/+/, "");
    const segments = normalized.split("/");
    if (!normalized.startsWith("assets/unitree-office-benchmark/") || segments.some((segment) => !segment || segment === "." || segment === "..")) return "";
    return segments.map((segment) => encodeURIComponent(segment)).join("/");
  }

  function artifactAccessProfile(artifact) {
    const extension = artifactExtension(artifact);
    const image = ["image", "ink"].includes(artifact?.kind) || ["png", "jpg", "jpeg", "webp", "gif"].includes(extension);
    const html = artifact?.kind === "html" || ["html", "htm"].includes(extension);
    const pdf = extension === "pdf";
    const office = ["excel", "word", "ppt"].includes(artifact?.kind) || ["xlsx", "xls", "docx", "doc", "pptx", "ppt"].includes(extension);
    return { extension, image, html, pdf, office, previewable: image || html || pdf };
  }

  function artifactActionLabel(artifact) {
    const profile = artifactAccessProfile(artifact);
    return profile.previewable ? "预览 / 下载" : "下载原件";
  }

  function artifactInlineLink(artifact) {
    const href = artifactHref(artifact);
    const name = artifactFileName(artifact);
    if (!href) return esc(name);
    const profile = artifactAccessProfile(artifact);
    const action = profile.previewable ? "打开" : "下载";
    const behavior = profile.previewable ? 'target="_blank" rel="noopener noreferrer"' : `download="${esc(name)}"`;
    return `<a class="table-link artifact-manifest-link" href="${esc(href)}" ${behavior} aria-label="${esc(`${action}${name}`)}">${esc(name)}<span>${action}</span></a>`;
  }

  function artifactFileCard(artifact) {
    const href = artifactHref(artifact);
    const name = artifactFileName(artifact);
    const path = artifactPath(artifact);
    const sha256 = artifactSha256(artifact) || "—";
    if (!href) return `<div class="artifact-file-card"><div class="artifact-file-meta"><strong>${esc(name)}</strong>${path ? `<span class="mono">${esc(path)}</span>` : ""}<span class="mono">SHA-256 ${esc(sha256)}</span></div><p class="artifact-file-unavailable">当前版本未登记可安全访问的发布路径。</p></div>`;
    const profile = artifactAccessProfile(artifact);
    const preview = profile.image ? `<a class="artifact-preview" href="${esc(href)}" target="_blank" rel="noopener noreferrer" aria-label="打开${esc(name)}原图"><img src="${esc(href)}" alt="${esc(name)}" loading="lazy" decoding="async"><span>点击查看原图</span></a>` : "";
    const openLabel = profile.image ? "新窗口查看原图" : profile.html ? "打开交互 HTML" : profile.pdf ? "在线查看 PDF" : "";
    const downloadLabel = profile.office ? `下载 ${esc(kindLabels[artifact.kind] || "Office")} 原件` : profile.image ? "下载原图" : profile.html ? "下载 HTML" : profile.pdf ? "下载 PDF" : "下载原件";
    const openAction = openLabel ? `<a class="artifact-action primary" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${openLabel} ↗</a>` : "";
    return `<div class="artifact-file-card">${preview}<div class="artifact-file-meta"><strong>${esc(name)}</strong><span class="mono">${esc(path)}</span><span class="mono">SHA-256 ${esc(sha256)}</span></div><div class="artifact-file-actions">${openAction}<a class="artifact-action" href="${esc(href)}" download="${esc(name)}">${downloadLabel} ↓</a></div><p class="artifact-file-note">图片、HTML 与 PDF 可在线打开；Office 文件将下载到本机后使用相应应用查看。</p></div>`;
  }

  function statusChip(value) {
    const normalized = String(value || "pending").toLowerCase();
    const labels = { pass: "通过", passed: "通过", success: "通过", complete: "完成", verified: "已验证", warn: "有警告", partial: "部分通过", repair: "需修复", fail: "失败", failed: "失败", error: "错误", blocked: "需协助", pending: "待验" };
    return `<span class="status-chip" data-status="${esc(normalized)}">${esc(labels[normalized] || publicationLabel(value) || "待验")}</span>`;
  }

  const sectionFallbacks = {
    ranking: ["两张正式排名与两张探索性诊断", "终稿独立使用视角形成两张正式排名；首次归责仅去重已枚举完全继承项，作为非因果探索性诊断。"],
    heatmap: ["逐文件质量分与交付闸门", "同一矩阵并列显示30件终稿的连续分和独立使用风险。"],
    compatibility: ["兼容性实测矩阵", "观察只适用于记录的操作系统、应用和版本；未验证平台不外推。"],
    native: ["覆盖完成度", "以明确分母显示Sheet、页面、幻灯片、图片区和HTML行为的实际检查范围。"],
    gates: ["交付闸门", "G0/G1/G2描述独立交付风险，不替代连续质量分。"],
    lineage: ["错误传播链", "区分根因起点、完全继承、语义改变和独立重新引入。"],
    sensitivity: ["规则与权重敏感性", "展示反事实重算和历史规则影响；不作为额外正式榜单。"],
    facts: ["事实基准、主张账本与数据血缘", "32项核心事实仅用于Excel中实际主张的项目；下游按允许上游判定，严格Excel血缘只作诊断。"],
    browser: ["全量复核记录", "按工具、产物、闸门、严重度和关键词检索场景、覆盖与问题记录。"],
    evidence: ["证据与媒体索引", "证据定位、原生应用截图和媒体对象保留可复核入口。"],
    process: ["连续任务全过程旁证", "展示用户提供的任务记录；动态分享页的固化限制另行说明。"],
    context: ["配置、额度与费用旁证", "仅说明测试时点所见配置和用量，不参与评分或跨产品成本比较。"],
    appendix: ["版本、指纹与技术附录", "保存规则变更、文件SHA-256、评分维度和待核验事项。"],
  };

  function sectionHead(key) {
    const fallback = sectionFallbacks[key] || [key, ""];
    return `<header class="subsection-head"><h3>${esc(humanizeText(text(`sections.${key}.title`, fallback[0])))}</h3><p>${esc(humanizeText(text(`sections.${key}.copy`, fallback[1])))}</p></header>`;
  }

  function chapterHead(number, title, copy) {
    return `<header class="chapter-head"><span>${esc(number)}</span><div><h2>${esc(title)}</h2>${copy ? `<p>${esc(copy)}</p>` : ""}</div></header>`;
  }

  function navItems() {
    return [
      ["executive", "执行摘要"], ["results", "比较结果"], ["profiles", "逐工具与逐文件"], ["native", "原生应用与兼容性"],
      ["issues", "问题、闸门与传播链"], ["facts", "事实基准与来源"], ["evidence", "方法、过程与全量证据"],
    ];
  }

  function navSubItems(chapterId) {
    return {
      executive: [["protocol", "测试协议"]],
      results: [["ranking", "正式与探索性排名"], ["heatmap", "逐文件矩阵"]],
      native: [["compatibility", "兼容性实测"], ["coverage", "覆盖完成度"]],
      issues: [["gates", "交付闸门"], ["lineage", "错误传播链"], ["sensitivity", "规则与权重敏感性"], ["challenges", "异议复核"]],
      evidence: [["method", "方法与内容守恒"], ["browser", "全量复核记录"], ["evidence-index", "证据与媒体索引"], ["process", "全过程记录"], ["context", "配置与用量旁证"], ["appendix", "版本与技术附录"]],
    }[chapterId] || [];
  }

  function mobileNavMarkup() {
    return navItems().map(([id, fallback], index) => {
      const label = text(`nav.${id}`, fallback);
      const children = navSubItems(id);
      return `<option value="${id}">${String(index + 1).padStart(2, "0")} ${esc(label)}</option>${children.map(([childId, childLabel]) => `<option value="${childId}">　${esc(childLabel)}</option>`).join("")}`;
    }).join("");
  }

  function navMarkup() {
    return navItems().map(([id, fallback], index) => {
      const label = text(`nav.${id}`, fallback);
      const children = navSubItems(id);
      return `<div class="nav-group" data-nav-chapter="${id}"><a class="nav-chapter-link" href="#${id}" aria-label="${esc(label)}" title="${esc(label)}"><span class="nav-index">${String(index + 1).padStart(2, "0")}</span><span class="nav-label">${esc(label)}</span></a>${children.length ? `<div class="nav-subnav" aria-label="${esc(`${label}子章节`)}">${children.map(([childId, childLabel]) => `<a class="nav-subsection-link" href="#${childId}" data-parent-chapter="${id}" ${["browser", "evidence-index", "process", "context", "appendix"].includes(childId) ? `data-reveal-section="${childId}"` : ""}>${esc(childLabel)}</a>`).join("")}</div>` : ""}</div>`;
    }).join("");
  }

  const affordanceTitles = {
    detail: "查看文件评分、闸门与证据明细",
    evidence: "点击查看证据原图与元数据",
    file: "下载或打开该原件",
    expand: "展开或收起此部分",
    external: "在新窗口打开外部来源",
    switch: "切换评价视角、权重或筛选条件",
    navigation: "前往报告对应章节",
    control: "执行此操作",
  };
  let affordanceObserver;

  function affordanceType(element) {
    if (element.matches("[data-open-evidence], .challenge-image")) return "evidence";
    if (element.matches("a[download]")) return "file";
    if (element.matches(".flow-node[data-open-artifact]")) return "file";
    if (element.matches("[data-open-artifact]")) return "detail";
    if (element.matches("summary")) return "expand";
    if (element.matches("select, input")) return "switch";
    if (element.matches("a[href]")) {
      const href = element.getAttribute("href") || "";
      return /^(https?:)?\/\//i.test(href) || element.target === "_blank" ? "external" : "navigation";
    }
    return "control";
  }

  function ensureAffordanceObserver() {
    if (affordanceObserver || !("IntersectionObserver" in window)) return;
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    affordanceObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-affordance-visible");
        affordanceObserver.unobserve(entry.target);
      });
    }, { threshold: 0.18, rootMargin: "0px 0px -4%" });
    if (reduceMotion) affordanceObserver.disconnect();
  }

  function decorateInteractiveElements(root = document) {
    const elements = [];
    if (root instanceof Element && root.matches("a[href], button, summary, select, input")) elements.push(root);
    if (root.querySelectorAll) elements.push(...root.querySelectorAll("a[href], button, summary, select, input"));
    ensureAffordanceObserver();
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    elements.forEach((element) => {
      if (element.dataset.affordanceReady === "true") return;
      const type = affordanceType(element);
      element.dataset.affordance = type;
      element.dataset.affordanceReady = "true";
      if (type === "detail" && element.dataset.openArtifact) {
        const artifact = artifactById.get(element.dataset.openArtifact);
        if (artifact) element.dataset.fileAction = artifactActionLabel(artifact);
      }
      if (type === "external" && (element.textContent || "").includes("↗")) element.dataset.affordanceSymbol = "present";
      if (!element.title) element.title = affordanceTitles[type];
      if (element.matches("summary")) {
        const details = element.closest("details");
        element.setAttribute("aria-expanded", String(Boolean(details?.open)));
      }
      if (reduceMotion || !affordanceObserver) element.classList.add("is-affordance-visible");
      else affordanceObserver.observe(element);
    });
  }

  let tableLabelSequence = 0;

  function decorateTableSemantics(root = document) {
    const tables = [];
    if (root instanceof Element && root.matches("table")) tables.push(root);
    if (root.querySelectorAll) tables.push(...root.querySelectorAll("table"));
    tables.forEach((table) => {
      table.querySelectorAll("thead th").forEach((cell) => cell.setAttribute("scope", "col"));
      table.querySelectorAll("tbody th").forEach((cell) => cell.setAttribute("scope", "row"));
      if (table.querySelector(":scope > caption") || table.hasAttribute("aria-labelledby") || table.hasAttribute("aria-label")) return;
      const figure = table.closest("figure");
      const details = table.closest("details");
      const article = table.closest("article");
      const section = table.closest("section, .subsection");
      const label = figure?.querySelector(":scope > figcaption")
        || figure?.querySelector(":scope > h3, :scope > header h3, :scope > header h4")
        || details?.querySelector(":scope > summary")
        || article?.querySelector(":scope > h3, :scope > header h3, :scope > header h4")
        || section?.querySelector(":scope > .subsection-head h3, :scope > header h2, :scope > header h3");
      if (label) {
        if (!label.id) { tableLabelSequence += 1; label.id = `table-context-${tableLabelSequence}`; }
        table.setAttribute("aria-labelledby", label.id);
      } else {
        table.setAttribute("aria-label", "报告数据表");
      }
    });
  }

  function configureNavigationFeedback() {
    const chapters = navItems().map(([id]) => document.getElementById(id)).filter(Boolean);
    const links = new Map($$(".nav a[href^='#']").map((link) => [link.getAttribute("href").slice(1), link]));
    const labels = new Map(navItems().map(([id, fallback]) => [id, text(`nav.${id}`, fallback)]));
    navItems().forEach(([id]) => navSubItems(id).forEach(([childId, childLabel]) => labels.set(childId, childLabel)));
    const currentLabel = $("#nav-current-label");
    const progress = $("#nav-progress");
    const progressLabel = $("#nav-progress-label");
    const mobileNav = $("#mobile-nav");
    let scheduled = false;
    const update = () => {
      scheduled = false;
      const marker = Math.min(180, window.innerHeight * .22);
      let active = chapters[0];
      chapters.forEach((chapter) => { if (chapter.getBoundingClientRect().top <= marker) active = chapter; });
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) active = chapters.at(-1);
      if (!active) return;
      let activeSubsection = null;
      navSubItems(active.id).forEach(([id]) => {
        const section = document.getElementById(id);
        if (section && section.getBoundingClientRect().top <= marker) activeSubsection = section;
      });
      const activeId = activeSubsection?.id || active.id;
      links.forEach((link, id) => {
        const isChapter = link.classList.contains("nav-chapter-link");
        const isSubsection = link.classList.contains("nav-subsection-link");
        if ((isChapter && id === active.id) || (isSubsection && id === activeId)) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
        if (isSubsection) link.dataset.current = String(id === activeId);
      });
      $$(".nav-group").forEach((group) => { group.dataset.current = String(group.dataset.navChapter === active.id); });
      const chapterIndex = Math.max(0, chapters.indexOf(active)) + 1;
      const chapterLabel = `${String(chapterIndex).padStart(2, "0")} · ${labels.get(active.id) || active.id}`;
      if (currentLabel) currentLabel.textContent = activeSubsection ? `${chapterLabel} / ${labels.get(activeId) || activeId}` : chapterLabel;
      if (mobileNav && [...mobileNav.options].some((option) => option.value === activeId)) mobileNav.value = activeId;
      const scrollRoot = document.scrollingElement || document.documentElement;
      const maximum = Math.max(1, scrollRoot.scrollHeight - window.innerHeight);
      const percent = Math.max(0, Math.min(100, Math.round(scrollRoot.scrollTop / maximum * 100)));
      if (progress) { progress.value = percent; progress.textContent = `${percent}%`; progress.setAttribute("aria-valuenow", String(percent)); }
      if (progressLabel) progressLabel.textContent = `${percent}%`;
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(update);
    };
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    update();
  }

  function setNavigationCollapsed(collapsed, persist = false) {
    document.documentElement.dataset.navCollapsed = String(Boolean(collapsed));
    const button = $("#nav-collapse");
    if (button) {
      button.setAttribute("aria-expanded", String(!collapsed));
      button.setAttribute("aria-label", collapsed ? "展开章节导航" : "折叠章节导航");
      button.title = collapsed ? "展开章节导航" : "折叠章节导航";
      const label = button.querySelector(".nav-collapse-label");
      if (label) label.textContent = collapsed ? "展开导航" : "折叠导航";
    }
    if (persist) {
      try { localStorage.setItem("report-v4-nav-collapsed", collapsed ? "true" : "false"); } catch (_) { /* local file privacy mode */ }
    }
  }

  function restoreNavigationState() {
    let collapsed = false;
    try { collapsed = localStorage.getItem("report-v4-nav-collapsed") === "true"; } catch (_) { /* local file privacy mode */ }
    setNavigationCollapsed(collapsed);
  }

  function renderShell() {
    const meta = RAW.meta || {};
    const darkTheme = document.documentElement.dataset.theme === "dark";
    const boundary = meta.sampleBoundary || meta.scopeStatement || "5款工具 × 6类任务 × 各1件固定终稿；单次任务链，不代表工具的一般表现。";
    const profiles = presentation.printProfiles || {};
    const titleParts = presentation.titleParts || { main: meta.title, subtitle: "宇树科技六任务 · 证据复核报告", cutoff: "资料截至2026年8月30日", accessibleFullTitle: meta.title };
    const pageFurniture = presentation.printPageFurniture || {};
    const toolLinks = arr(UI.toolLinks).map((item) => ({ label: String(item?.label || "").trim(), url: safeHttpUrl(item?.url) })).filter((item) => item.label && item.url);
    $("#app").innerHTML = `
      <a class="skip-link" href="#main">跳至正文</a>
      <header class="topbar"><div class="shell topbar-inner">
        <div class="nav-heading"><div class="brand"><span class="brand-mark"></span><span class="brand-text">${esc(text("brand", "固定样本交付物比较"))}</span></div><button id="nav-collapse" class="nav-collapse" type="button" aria-controls="primary-nav" aria-expanded="true"><span class="nav-collapse-icon" aria-hidden="true">‹</span><span class="nav-collapse-label">折叠导航</span></button></div>
        <div class="nav-status"><span>当前章节 <b id="nav-progress-label">0%</b></span><strong id="nav-current-label">01 · 执行摘要</strong><progress id="nav-progress" max="100" value="0" aria-label="报告阅读进度">0%</progress></div>
        <nav id="primary-nav" class="nav" aria-label="主导航">${navMarkup()}</nav>
        <select id="mobile-nav" class="mobile-nav" aria-label="章节导航">${mobileNavMarkup()}</select>
        <div class="topbar-tools"><nav class="nav-utilities" aria-label="报告工具"><a href="#artifact-manifest" data-reveal-section="appendix">原件与指纹</a><a href="#evidence-index" data-reveal-section="evidence-index">证据索引</a><a href="#process" data-reveal-section="process">过程记录</a><a href="#main" class="back-to-top">返回顶部 ↑</a></nav><label class="print-profile"><span>打印</span><select id="print-profile" aria-label="打印模式">${Object.entries(profiles).map(([key, item]) => `<option value="${esc(key)}" ${state.printProfile === key ? "selected" : ""}>${esc(item.label || key)}</option>`).join("")}</select></label>
          <button id="print-report" class="text-button topbar-print" type="button" aria-label="打印报告">打印</button>
          <button id="theme-toggle" class="icon-button" type="button" aria-label="${darkTheme ? "切换到浅色主题" : "切换到深色主题"}" aria-pressed="${darkTheme}">◐</button></div>
      </div></header>
      <main id="main">
        <header class="report-masthead"><div class="shell">
          <div class="report-series">${esc(meta.version || "报告版本 4.5.2 · 固定样本证据复核")}</div>
          <h1 aria-label="${esc(titleParts.accessibleFullTitle || meta.title)}"><span>${esc(titleParts.main)}</span><small>${esc(titleParts.subtitle)}</small></h1>
          <p class="report-cutoff">${esc(titleParts.cutoff)}</p>
          ${toolLinks.length ? `<nav class="participant-links" aria-label="参评工具官方网站"><span>参评工具</span>${toolLinks.map((item) => `<a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer">${esc(item.label)}<i aria-hidden="true">↗</i></a>`).join("")}</nav>` : ""}
          <div id="executive-snapshot"></div>
          <a class="mobile-rank-jump" href="#executive-content">先看交付闸门与正式排名 ↓</a>
          <details class="report-boundary" open><summary>样本与核验边界</summary><dl class="report-meta"><div><dt>样本边界</dt><dd>${esc(boundary)}</dd></div><div><dt>资料截止</dt><dd>${esc(meta.cutoffDate || "2026-08-30")}</dd></div><div><dt>核验环境</dt><dd>${esc(meta.environmentSummary || "macOS 26.5.2 / Office 16.112.3 / Chrome 152")}</dd></div><div><dt>回应状态</dt><dd>${challengeRoot.meta ? `未收到厂商正式回应；已记录${challengeResponses.length}款工具的AI自评` : "未征求厂商正式回应"}</dd></div></dl></details>
          <aside class="interaction-guide" aria-label="阅览方式"><strong>阅览方式</strong><span><b>分数卡</b>评分、风险与原件</span><span><b>⌕ 证据</b>查看图片</span><span><b>⌄ 折叠项</b>展开附录</span><span><b>↗ 来源</b>打开外部网页</span><span><b>↔ 筛选</b>缩小记录范围</span></aside>
        </div></header>
        <section id="executive" class="chapter" data-print-level="summary"><div class="shell">${chapterHead("01", "执行摘要", "先看交付闸门与两张正式排名；小分差须结合近分组和判断敏感性阅读。")}<p class="summary-excerpt-note">${esc(pageFurniture.summaryExcerptNote || "")}</p><div id="executive-content"></div><div id="protocol" class="subsection"><div id="protocol-content"></div></div></div></section>
        <section id="results" class="chapter" data-print-level="summary"><div class="shell">${chapterHead("02", "比较结果", "正式排名、判断敏感性与交付闸门均来自同一冻结数据集；连续分不采用历史数值封顶。")}<div id="ranking" class="subsection">${sectionHead("ranking")}<div id="ranking-content"></div></div><div id="heatmap" class="subsection">${sectionHead("heatmap")}<div id="heatmap-content"></div></div></div></section>
        <section id="profiles" class="chapter" data-print-level="summary"><div class="shell">${chapterHead("03", "逐工具与逐文件表现", "逐件查看连续分、交付闸门、评分明细与证据入口。")}<div id="profiles-content"></div></div></section>
        <section id="native" class="chapter" data-print-level="formal"><div class="shell">${chapterHead("04", "原生应用与兼容性", "记录指定应用中的打开、编辑、保存、重开与展示结果。")}<div id="compatibility" class="subsection">${sectionHead("compatibility")}<div id="compatibility-content"></div></div><div id="coverage" class="subsection"><div id="coverage-content"></div></div></div></section>
        <section id="issues" class="chapter" data-print-level="summary"><div class="shell">${chapterHead("05", "问题、闸门与传播链", "连续分回答质量差距，交付闸门回答能否直接交付，传播链回答错误从何处产生。")}<div id="gates" class="subsection">${sectionHead("gates")}<div id="gates-content"></div></div><div id="lineage" class="subsection" data-print-level="formal">${sectionHead("lineage")}<div id="lineage-content"></div></div><div id="sensitivity" class="subsection" data-print-level="formal">${sectionHead("sensitivity")}<div id="sensitivity-content"></div></div><div id="challenges" class="subsection" data-print-level="formal"><div id="challenges-content"></div></div></div></section>
        <section id="facts" class="chapter" data-print-level="formal"><div class="shell">${chapterHead("06", "事实基准与来源", "列示32项事实母表、逐主张重算及来源定位。")}${sectionHead("facts")}<div id="facts-content"></div></div></section>
        <section id="evidence" class="chapter" data-print-level="formal"><div class="shell">${chapterHead("07", "方法、过程与全量证据", "评分构成、操作记录、覆盖项、证据媒体、过程旁证与样本指纹均在本章完整保留。")}
          <div id="method" class="subsection"><div id="method-content"></div></div>
          <details id="browser" class="evidence-index-block" data-print-level="full" data-lazy-render="browser"><summary>全量场景、覆盖与问题复核浏览器</summary><div class="details-body">${sectionHead("browser")}${browserControls()}<div id="record-content" aria-busy="true"></div></div></details>
          <details id="evidence-index" class="evidence-index-block" data-print-level="full" data-lazy-render="evidence-index"><summary>741项证据与710个媒体对象索引</summary><div class="details-body">${sectionHead("evidence")}<div id="evidence-content" aria-busy="true"></div></div></details>
          <details id="process" class="evidence-index-block" data-print-level="formal" data-lazy-render="process"><summary>用户补充的全过程记录</summary><div class="details-body">${sectionHead("process")}<div id="process-content" aria-busy="true"></div></div></details>
          <details id="context" class="evidence-index-block" data-print-level="formal" data-lazy-render="context"><summary>配置、额度与费用旁证（不计分）</summary><div class="details-body">${sectionHead("context")}<div id="context-content" aria-busy="true"></div></div></details>
          <details id="appendix" class="evidence-index-block" data-print-level="formal" data-lazy-render="appendix"><summary>版本、原件指纹与完整技术附录</summary><div class="details-body">${sectionHead("appendix")}<div id="appendix-content" aria-busy="true"></div></div></details>
          <div id="full-record-print" aria-hidden="true"></div>
        </div></section>
      </main>
      <footer class="footer"><div class="shell">${esc(text("footer", "评测截止日与评分口径以方法说明为准；本报告不构成投资建议。"))}</div></footer>
      ${dialogsMarkup()}`;
    document.documentElement.dataset.printProfile = ["summary", "formal", "full"].includes(state.printProfile) ? state.printProfile : "formal";
  }

  function renderProtocol() {
    const target = $("#protocol-content");
    if (!target) return;
    const prompts = arr(testProtocol.prompts).slice().sort((a, b) => (num(a.step) ?? 99) - (num(b.step) ?? 99));
    const design = obj(testProtocol.design);
    if (!prompts.length && !Object.keys(design).length) { target.innerHTML = ""; return; }
    const designRows = [
      ["比较单元", design.comparisonUnit],
      ["配置口径", design.configuration],
      ["实验边界", design.notControlled],
    ].filter(([, value]) => value);
    target.innerHTML = `<div class="protocol-overview"><header><span>测试协议</span><h3>${esc(testProtocol.title || "六任务连续工作流与样本配置")}</h3><p>五款工具依次接收同一组六条连续指令。后续任务承接本工具此前产物，构成从底稿到终端呈现的真实办公链路。</p></header><dl>${designRows.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl></div>
      <div class="prompt-flow" aria-label="六任务连续工作流">${prompts.map((item, index) => `<details class="prompt-step" open><summary><span class="prompt-number">${esc(item.step ?? index + 1)}</span><span><small>${esc(kindLabels[item.artifactKind] || item.artifactKind || "任务")}</small><strong>${esc(item.title || `任务${index + 1}`)}</strong></span><em>原始指令</em></summary><div class="prompt-body"><p>${esc(item.prompt || "—")}</p></div></details>`).join("")}</div>`;
  }

  function challengeStatusLabel(status) {
    return ({ accepted: "采纳", partially_accepted: "部分采纳", rejected: "不采纳", pending: "待核验" })[status] || publicationLabel(status) || "待核验";
  }

  function challengeEffectLabel(status) {
    return ({ recomputed: "已按对称规则重算", none: "不调整评分", pending: "待核验" })[status] || publicationLabel(status) || "未说明";
  }

  function challengeArtifactLinks(ids) {
    const linked = arr(ids).map((id) => artifactById.get(id)).filter(Boolean);
    return linked.length ? `<div class="challenge-artifacts">${linked.map((artifact) => `<button class="text-button" type="button" data-open-artifact="${esc(artifact.id)}">${esc(`${artifact.tool} · ${kindLabels[artifact.kind]}`)}</button>`).join("")}</div>` : "";
  }

  function responseScreenshot(response) {
    const path = safeAssetUrl(response.screenshotDataUri || response.screenshotPath);
    if (!path) return `<div class="challenge-image-missing">未登记可安全打开的截图路径</div>`;
    return `<a class="challenge-image" href="${esc(path)}" target="_blank" rel="noopener"><img loading="lazy" src="${esc(path)}" alt="${esc(`${response.tool}工具自评截图`)}"><span>打开原图</span></a>`;
  }

  function renderChallenges() {
    const target = $("#challenges-content");
    if (!target) return;
    if (!challengeItems.length && !challengeResponses.length) { target.innerHTML = ""; return; }
    const meta = obj(challengeRoot.meta);
    const statusCounts = challengeItems.reduce((counts, item) => {
      const status = item?.disposition?.status || "pending";
      counts[status] = (counts[status] || 0) + 1;
      return counts;
    }, {});
    const formalCount = num(meta.formalVendorResponsesReceived) ?? 0;
    target.innerHTML = `<header class="subsection-head"><h3>工具自评异议与复核处理（首次）</h3><p>${challengeItems.length}项异议逐项保留原始回复、裁决理由与评分处理。</p></header>
      <div class="challenge-policy"><strong>回应性质边界</strong><p>${esc(meta.responseNaturePolicy || "以下内容由五款AI工具读取报告后生成，不是相关厂商、负责人或员工的正式声明。工具自评仅作为异议线索，证据权重为0。")} 已收到厂商正式回应：${formalCount}；本报告不宣称厂商已认可。</p><div class="challenge-counts"><span>${challengeItems.length}项异议</span>${Object.entries(statusCounts).map(([status, count]) => `<span data-disposition="${esc(status)}">${esc(challengeStatusLabel(status))} ${count}</span>`).join("")}</div><p class="mono technical-only">结构版本 ${esc(meta.schemaVersion || "—")} · 处理状态 ${esc(meta.status || "—")} · 声称厂商认可 ${esc(displayScalar(meta.claimOfVendorAcceptance))}</p></div>
      <div class="challenge-response-grid">${challengeResponses.map((response) => `<article class="challenge-response" style="--tool:${toolColor.get(response.tool) || "var(--accent-2)"}">${responseScreenshot(response)}<div><header><span class="tool-label"><i class="tool-dot"></i>${esc(response.tool)}</span><small>${esc(response.responseNature || "AI工具自评 · 非厂商正式回应")}</small></header><p>${esc(response.summary || "—")}</p><dl><div><dt>复核结论</dt><dd>${esc(response.conclusion || "—")}</dd></div><div><dt>涉及异议</dt><dd>${arr(response.challengeIds).length}项</dd></div></dl><p class="mono technical-only">异议编号 ${esc(arr(response.challengeIds).join("、") || "—")} · 截图 SHA-256 ${esc(response.screenshotSha256 || "—")}</p></div></article>`).join("")}</div>
      <div class="challenge-ledger">${challengeItems.map((item, index) => {
        const disposition = obj(item.disposition);
        const before = disposition.before;
        const after = disposition.after;
        const scoreEffect = challengeEffectLabel(disposition.scoreEffectStatus);
        return `<details class="challenge-item" ${index < 3 ? "open" : ""}><summary><span class="challenge-seq">${index + 1}</span><span><small>${esc(item.tool || "五款工具")}</small><strong>${esc(item.claimText || item.id || "异议")}</strong></span><b data-disposition="${esc(disposition.status || "pending")}">${esc(challengeStatusLabel(disposition.status || "pending"))}</b></summary><div class="challenge-body"><dl><div><dt>裁决理由</dt><dd>${esc(disposition.rationale || "—")}</dd></div><div><dt>证据充分性</dt><dd>${esc(disposition.evidenceSufficiency === "sufficient" ? "足以支持本次裁决" : publicationLabel(disposition.evidenceSufficiency) || "待核验")}</dd></div><div><dt>评分处理</dt><dd>${esc(scoreEffect)}${disposition.scoreEffectStatus === "recomputed" ? `；调整前：${esc(displayScalar(before))}；调整后：${esc(displayScalar(after))}` : ""}</dd></div></dl>${challengeArtifactLinks(item.artifactIds)}<p class="mono technical-only">异议编号 ${esc(item.id || "—")} · 异议类型 ${esc(item.claimType || "—")} · 回应性质 ${esc(item.responseNature || "—")} · 问题编号 ${esc(arr(item.findingIds).join("、") || "—")} · 对称批次 ${esc(item.symmetryBatchId || "—")} · 生效版本 ${esc(item.versionEffective || "—")}</p></div></details>`;
      }).join("")}</div>
      <div class="symmetry-batches"><h4>五家对称复核批次</h4>${symmetryBatches.map((batch) => `<article><strong>${esc(batch.rule || batch.id || "对称规则")}</strong><span>${esc(arr(batch.tools).join("、") || "—")}</span><b>${esc(batch.status === "completed_5_of_5" ? "5/5完成" : publicationLabel(batch.status) || "待核验")}</b><small class="mono technical-only">${esc(batch.id || "")}</small></article>`).join("")}</div>`;
  }

  function rankingMini(perspective, mode) {
    const modeLabels = { practical: "均衡投研实务", equalTask: "六任务等权" };
    const perspectiveLabels = { standalone: "正式固定终稿排名", firstOrigin: "探索性首次归责诊断" };
    const rows = rankingRows(perspective, mode);
    const role = perspective === "standalone" ? "official" : "diagnostic";
    const roleLabel = perspective === "standalone" ? "正式" : "探索性 · 非因果";
    return `<article class="executive-ranking" data-ranking-role="${role}"><header><div><span class="ranking-role-badge" data-role="${role}">${roleLabel}</span><h3>${perspectiveLabels[perspective]} · ${modeLabels[mode]}</h3></div><span>连续分点估计 · 0–100分</span></header><ol>${rows.map((row) => `<li><span class="rank-number">${esc(row.rank)}</span><span class="tool-label" style="--tool:${toolColor.get(row.tool)}"><i class="tool-dot"></i>${esc(row.tool)}</span><span class="dot-axis" style="${rankingStyle(row)}" aria-label="${esc(`点估计${fmt(row.score, 1)}分，${sensitivityGroupLabel(row)}`)}"><i class="score-point"></i></span><strong>${fmt(row.score, 1)}</strong><small>${esc(`${sensitivityGroupLabel(row)} · ${sensitivityRankLabel(row)}`)}</small></li>`).join("")}</ol>${axisMarkup("mini-score-axis")}</article>`;
  }

  function rankingStaticPanel(perspective, mode) {
    const modeLabels = { practical: "均衡投研实务", equalTask: "六任务等权" };
    const rows = rankingRows(perspective, mode);
    const weights = weightsFor(mode, perspective);
    const role = perspective === "standalone" ? "official" : "diagnostic";
    const roleLabel = perspective === "standalone" ? "正式排名" : "探索性次序 · 非因果";
    return `<article class="executive-ranking ranking-static-card panel" data-ranking-view="${perspective}:${mode}" data-ranking-role="${role}"><header><div><span>权重模式</span><h3>${esc(modeLabels[mode])}</h3></div><span class="ranking-role-badge" data-role="${role}">${roleLabel}</span></header><ol>${rows.map((row) => `<li><span class="rank-number">${esc(row.rank)}</span><span class="tool-label" style="--tool:${toolColor.get(row.tool)}"><i class="tool-dot"></i>${esc(row.tool)}</span><span class="dot-axis" style="${rankingStyle(row)}" aria-label="${esc(`点估计${fmt(row.score, 1)}分，已分类专家/混合判断敏感性范围${fmt(reviewResolution(row).lower, 1)}至${fmt(reviewResolution(row).upper, 1)}分`)}"><i class="review-range"></i><i class="score-point"></i></span><strong>${fmt(row.score, 1)}</strong><small>${esc(`${sensitivityGroupLabel(row)} · ${sensitivityRankLabel(row)}`)}</small></li>`).join("")}</ol>${axisMarkup("mini-score-axis")}<div class="ranking-static-weights"><strong>六类任务权重</strong><div class="weight-list">${kinds.map((kind) => `<div class="weight-line"><span>${esc(kindLabels[kind])}</span><i style="width:${Number(weights[kind] || 0) * 100}%"></i><b>${fmt(Number(weights[kind] || 0) * 100, 1)}%</b></div>`).join("")}</div></div></article>`;
  }

  function renderExecutive() {
    const summary = presentation.executiveSummary || {};
    const meta = RAW.meta || {};
    const execution = obj(testProtocol.executionDisclosure);
    const recording = obj(testProtocol.processRecording);
    const recordingSize = num(recording.totalBytes) === null ? "约7.40 GB" : `${(Number(recording.totalBytes) / 1e9).toFixed(2)} GB`;
    const summaryRows = [
      ["评价对象", summary.scope], ["排名口径", summary.rankingPolicy], ["闸门口径", summary.gatePolicy], ["证据口径", summary.evidencePolicy],
      ["过程录屏", summary.processPolicy || `${recording.segmentCount || 8}段完整过程录屏合计${recordingSize}，暂不公开；发布SHA-256索引，需要时通过GitHub Issues联系提供。`],
      ["执行与选择", execution.interventionBoundary || "未事前登记统一的重试、超时、人工干预与多版本终稿选择规则；结果不代表生成稳定性。"],
      ["评审者披露", summary.reviewerDisclosure || meta.reviewerDisclosure || RAW.methodology?.assessmentClassification?.raterDisclosure],
    ];
    const snapshot = $("#executive-snapshot");
    if (snapshot) snapshot.innerHTML = executiveSnapshotMarkup();
    $("#executive-content").innerHTML = `<section class="executive-gate-priority" aria-labelledby="executive-gate-title"><header><div><span>交付风险概览</span><h3 id="executive-gate-title">30件终稿闸门分布</h3></div><p>G0/G1/G2标示独立交付风险，不参与连续质量分计算。</p></header>${gateSummaryMarkup("executive-gate-summary")}</section>
      <div class="executive-layout"><figure class="publication-figure" id="visual-executive-rankings" aria-describedby="caption-executive-rankings"><div class="executive-rankings">${["practical", "equalTask"].map((mode) => rankingMini("standalone", mode)).join("")}</div>${figureCaption("executive-rankings")}</figure><aside class="executive-policy"><h3>阅读边界与披露</h3><dl>${summaryRows.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value || "—")}</dd></div>`).join("")}</dl></aside></div>
      <div class="limitation-block" id="key-limitations"><h3>关键限制</h3><ol>${arr(meta.limitations).map((item) => `<li>${esc(item)}</li>`).join("")}</ol></div>`;
  }

  function renderProfiles() {
    const profileMap = obj(RAW.meta?.toolProfiles);
    $("#profiles-content").innerHTML = `<figure class="publication-figure publication-table-block profile-directory" id="visual-tool-profiles" aria-describedby="caption-tool-profiles"><div class="profile-ledger profile-dossier-list">${tools.map((tool) => {
      const profile = profileMap[tool] || {};
      const rows = kinds.map((kind) => { const artifact = artifactFor(tool, kind); return artifact ? `<button class="profile-artifact-card" type="button" data-open-artifact="${esc(artifact.id)}" aria-label="${esc(`${tool} ${kindLabels[kind]}，${fmt(artifactScore(artifact), 1)}分，${gateDisplay(gateCode(artifact))}，查看详情与原件`)}"><span>${esc(kindLabels[kind])}</span><strong>${fmt(artifactScore(artifact), 1)}</strong><small data-gate="${gateBase(gateCode(artifact))}">${esc(gateDisplay(gateCode(artifact)))} ${gateSymbol(gateCode(artifact))}</small></button>` : ""; }).join("");
      return `<article class="profile-row profile-dossier" data-tool="${esc(tool)}"><header class="profile-dossier-intro"><span class="tool-label" style="--tool:${toolColor.get(tool)}"><i class="tool-dot"></i>${esc(tool)}</span><p>${esc(profile.summary || "")}</p></header><div class="profile-scores profile-dossier-scores" aria-label="${esc(`${tool}六类终稿分数与闸门`)}">${rows}</div><dl class="profile-dossier-insights"><div class="profile-insight profile-insight-strength"><dt>本样本优势</dt><dd>${esc(profile.strength || "—")}</dd></div><div class="profile-insight profile-insight-friction"><dt>主要摩擦</dt><dd>${esc(profile.friction || "—")}</dd></div><div class="profile-insight profile-insight-critical"><dt>不可忽视事项</dt><dd>${esc(profile.critical || "—")}</dd></div><div class="profile-insight profile-insight-recommendation"><dt>使用建议</dt><dd>${esc(profile.sampleUseRecommendation || "—")}</dd></div></dl></article>`;
    }).join("")}</div>${figureCaption("tool-profiles")}</figure>`;
  }

  function renderCoverage() {
    const rows = Object.entries(obj(contentInventory.coverageByType));
    const labels = { sheet: "Excel Sheet", page: "Word原生页", slide: "PPT幻灯片", image_region: "图片检查区", viewport: "HTML视口", html_behavior: "HTML交互行为" };
    const byArtifact = new Map();
    coverageItems.forEach((item) => { const row = byArtifact.get(item.artifactId) || { reviewed: 0, total: 0 }; row.total += 1; if (item.status === "reviewed") row.reviewed += 1; byArtifact.set(item.artifactId, row); });
    $("#coverage-content").innerHTML = `${sectionHead("native")}<figure class="publication-figure" id="visual-coverage-summary" aria-describedby="caption-coverage-summary"><div class="coverage-strip">${rows.map(([key, value]) => `<div><span>${esc(labels[key] || key)}</span><strong>${esc(value.reviewed)} / ${esc(value.total)}</strong><i style="--ratio:${value.total ? value.reviewed / value.total * 100 : 0}%"></i></div>`).join("")}</div>${figureCaption("coverage-summary")}</figure>
      <details class="panel appendix-block"><summary>展开30件终稿逐文件覆盖率</summary><div class="appendix-body"><div class="table-wrap"><table><thead><tr><th>工具</th><th>产物</th><th>已检查/总数</th><th>覆盖单位</th></tr></thead><tbody>${artifacts.map((artifact) => { const row = byArtifact.get(artifact.id) || { reviewed: 0, total: 0 }; const types = compact(coverageItems.filter((item) => item.artifactId === artifact.id).map((item) => labels[item.coverageType] || item.coverageType)); return `<tr data-artifact-id="${esc(artifact.id)}"><td>${esc(artifact.tool)}</td><td><button class="table-link" data-open-artifact="${esc(artifact.id)}">${esc(kindLabels[artifact.kind])}</button></td><td>${row.reviewed} / ${row.total}</td><td>${esc(types.join("、"))}</td></tr>`; }).join("")}</tbody></table></div></div></details>`;
  }

  function renderMethod() {
    const classification = RAW.methodology?.assessmentClassification || {};
    const counts = classification.summary || contentInventory.assessmentClasses || {};
    const criterionCounts = obj(counts.criterionCount);
    const classWeights = obj(counts.aggregateWeightAcrossSixRubrics);
    const assessmentClasses = [
      ["mechanical", "机械项", classification.mechanical],
      ["mixed_anchored_judgment", "混合锚定判断", classification.mixed_anchored_judgment],
      ["expert_judgment", "专家判断", classification.expert_judgment],
    ];
    const scenarioComposition = contentInventory.scenarioRecordComposition || {};
    const inventoryRows = ["artifacts", "scenarioRecords", "coverageItems", "findings", "evidence", "media", "facts", "sources"].map((key) => [key, contentInventory[key]]).filter(([, value]) => value);
    const invLabels = { artifacts: "终稿", scenarioRecords: "综合复核记录", coverageItems: "覆盖项", findings: "复核发现", evidence: "证据", media: "媒体对象", facts: "事实基准", sources: "来源" };
    $("#method-content").innerHTML = `<figure class="publication-figure publication-table-block" id="visual-method-inventory" aria-describedby="caption-method-inventory"><div class="method-ledger"><article><h3>评分项分类与单评审者限制</h3><p>${esc(classification.purpose || "")}</p><div class="assessment-class-grid">${assessmentClasses.map(([key, label, definition]) => `<section data-assessment-class="${esc(key)}"><header><strong>${esc(label)}</strong><b>${esc(criterionCounts[key] ?? "—")}项</b><span>合计权重 ${esc(classWeights[key] ?? "—")} / 600</span></header><p>${esc(definition || "—")}</p></section>`).join("")}</div><div class="reviewer-disclosure"><strong>评审者披露</strong><p>${esc(classification.raterDisclosure || RAW.meta?.reviewerDisclosure || "单一评审者；未测量评审者间一致性。")}</p></div><p class="method-count">${esc(counts.scoreEffect || classification.scoreEffect || "分类不改变点估计；混合锚定判断与专家判断项进入局部一步敏感性重算。")}</p></article><article><h3>报告数据总览</h3><table><thead><tr><th>对象</th><th>数量</th><th>所在章节</th></tr></thead><tbody>${inventoryRows.map(([key, value]) => `<tr><td>${esc(invLabels[key] || key)}</td><td>${esc(value.count)}</td><td>${esc(value.entry)}</td></tr>`).join("")}</tbody></table></article></div>${figureCaption("method-inventory")}</figure>
      <figure class="publication-figure publication-table-block" id="visual-scenario-composition" aria-describedby="caption-scenario-composition"><h3>202项综合复核记录的组成</h3><p>${esc(scenarioComposition.formula || "")}</p><div class="table-wrap"><table><thead><tr><th>组成</th><th>计数</th><th>说明</th></tr></thead><tbody><tr><td>主场景运行</td><td class="numeric">${esc(scenarioComposition.primaryScenarioRuns?.count ?? "—")}</td><td>scenarioRuns逐次操作记录</td></tr><tr><td>补充规则场景</td><td class="numeric">${esc(scenarioComposition.supplementalScenarioRecords?.count ?? "—")}</td><td>Word检索、图片三档等补充规则</td></tr><tr><td>配对图片标签区族</td><td class="numeric">${esc(scenarioComposition.pairedImageZoneFamilies?.count ?? "—")}</td><td>${esc(scenarioComposition.pairedImageZoneFamilies?.definition || "")}</td></tr></tbody></table></div>${figureCaption("scenario-composition")}</figure>`;
  }

  function renderFullPrintLedger() {
    const compactRow = (record, type) => {
      const artifact = recordArtifact(record);
      const id = record.id || record.runId || record.subtestId || "—";
      let title = record.title || record.summary || record.scenario || record.item || record.label || record.locator || "—";
      let result = type === "finding" ? record.observation || record.interpretation || record.summary : record.actual || record.result || record.notes || record.description || "—";
      let locator = record.locator || record.location || "—";
      if (type === "evidence") {
        title = record.title || record.caption || record.type || record.id;
        result = [record.description, record.mediaId ? `媒体：${record.mediaId}` : "", record.status ? `状态：${record.status}` : ""].filter(Boolean).join("；") || "—";
      }
      if (type === "media") {
        title = record.mimeType || "媒体对象";
        locator = record.path || "—";
        result = [`${record.bytes ?? "—"} bytes`, record.sha256 ? `SHA-256 ${record.sha256}` : "", record.status ? `状态：${record.status}` : ""].filter(Boolean).join("；");
      }
      return `<tr data-record-id="${esc(id)}"><td class="mono">${esc(id)}</td><td>${esc(artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : record.tool || "—")}</td><td>${esc(locator)}</td><td>${esc(title)}</td><td>${esc(displayScalar(result))}</td></tr>`;
    };
    const rowUnits = (row) => {
      const raw = [
        row.id, row.runId, row.subtestId, row.tool, row.kind, row.locator, row.location,
        row.title, row.summary, row.scenario, row.item, row.label, row.observation,
        row.interpretation, row.actual, row.result, row.notes, row.description,
        row.path, row.sha256, row.status,
      ].filter(Boolean).map((value) => displayScalar(value)).join(" ");
      return Math.max(1, Math.ceil(raw.length / 150));
    };
    const chunkRows = (rows, maxUnits = 12) => {
      const chunks = []; let current = []; let units = 0;
      rows.forEach((row) => {
        const next = Math.min(rowUnits(row), maxUnits);
        if (current.length && units + next > maxUnits) { chunks.push(current); current = []; units = 0; }
        current.push(row); units += next;
      });
      if (current.length) chunks.push(current);
      return chunks;
    };
    const groups = [["场景记录", allScenarioRecords(), "scenario"], ["覆盖记录", coverageItems, "coverage"], ["问题记录", findings, "finding"], ["证据记录", evidence, "evidence"], ["媒体对象登记", media, "media"]];
    let tableIndex = 0;
    $("#full-record-print").innerHTML = `<p class="technical-ledger-label">以下为全量技术附录，保留原始机器ID用于复核；正文不使用这些字段。</p>${groups.map(([label, rows, type]) => {
      tableIndex += 1;
      const chunks = chunkRows(rows);
      return chunks.map((chunk, index) => `<section class="full-ledger-group"><h3>附表A-${tableIndex} ${esc(label)}（续${index + 1}/${chunks.length}）</h3><table><caption>附表A-${tableIndex} ${esc(label)}（续${index + 1}/${chunks.length}） · 共${rows.length}条</caption><thead><tr><th>ID</th><th>文件</th><th>定位</th><th>项目</th><th>结果/观察</th></tr></thead><tbody>${chunk.map((row) => compactRow(row, type)).join("")}</tbody></table></section>`).join("");
    }).join("")}`;
  }

  function renderProcessRecords() {
    const root = RAW.meta?.processRecords || {};
    const recording = obj(testProtocol.processRecording);
    const execution = obj(testProtocol.executionDisclosure);
    const manifestHref = safeAssetUrl(recording.manifest);
    const requestUrl = safeHttpUrl(recording.requestUrl);
    const recordingSize = num(recording.totalBytes) === null ? "约7.40 GB" : `${(Number(recording.totalBytes) / 1e9).toFixed(2)} GB`;
    const statusLabel = (record) => {
      const labels = {
        accessible_and_six_prompts_matched: "页面可读 · 六提示均命中",
        downloaded_and_content_sampled: "已下载、哈希并抽样",
        downloaded_and_six_prompts_matched: "已下载、哈希 · 六提示均命中",
        downloaded_hashed_and_visually_sampled_scope_user_confirmed: "已下载、哈希并抽样 · 六任务范围由用户确认",
        share_page_accessible_and_six_prompts_matched: "页面可读 · 六提示均自动命中",
        share_page_accessible_content_extraction_limited: "用户确认可访问 · 自动抽取受限",
      };
      return labels[record.automatedStatus] || record.automatedStatus || "已登记";
    };
    const layers = [
      ["过程记录", "还原输入、回复与任务链；分享记录和过程录屏均不直接计分。"],
      ["终稿原件与原生实测", "决定各产物连续质量分、交付闸门与兼容性结论。"],
      ["独立事实基准", "仅用于Excel事实核验；过程记录不能覆盖上交所等一级来源。"],
    ];
    $("#process-content").innerHTML = `<div class="evidence-layer-grid">${layers.map(([title, copy], index) => `<article><span>层级 ${index + 1}</span><strong>${esc(title)}</strong><p>${esc(copy)}</p></article>`).join("")}</div>
      <div class="process-policy"><strong>证据使用规则</strong><span>${esc(root.policy?.completenessRule || "全过程是用户提供的标注；自动检查范围单独披露。")}</span></div>
      ${recording.segmentCount ? `<section class="process-recording-disclosure" aria-labelledby="process-recording-title"><header><div><span>完整过程录屏</span><h3 id="process-recording-title">${esc(recording.segmentCount)}段 · ${esc(recordingSize)}</h3></div><b>暂不公开视频文件</b></header><p>${esc(recording.coverage || "用户确认：这些视频合计完整记录本次5款AI办公软件完成6项连续任务的全过程。")}</p><div class="process-recording-actions">${manifestHref ? `<a href="${esc(manifestHref)}" target="_blank" rel="noopener">查看文件名、字节数与SHA-256索引 ↗</a>` : ""}${requestUrl ? `<a href="${esc(requestUrl)}" target="_blank" rel="noopener noreferrer">通过GitHub Issues联系申请核验 ↗</a>` : ""}</div><dl>${[["评分影响", "不计分；用于核验任务链"], ["干预边界", execution.interventionBoundary], ["Qoder继续消息", execution.qoderContinuationMessages], ["终稿选择", execution.selectionBoundary]].filter(([, value]) => value).map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl></section>` : ""}
      ${processRecords.length ? `<div class="process-grid">${processRecords.map((record) => {
        const url = safeHttpUrl(record.url);
        const sha = record.sha256 ? String(record.sha256).slice(0, 16) + "…" : "动态页面，未固化全文哈希";
        const prompts = record.observedUserPromptCount === null || record.observedUserPromptCount === undefined ? "自动计数受限" : `${record.observedUserPromptCount}个用户消息块`;
        return `<article class="panel process-card" data-process-id="${esc(record.id || "")}" style="--tool:${toolColor.get(record.tool)}"><div class="process-card-head"><span class="tool-badge">${esc(record.tool)}</span><span class="chip">不计分</span></div><h3>${esc(record.label || record.observedTitle || record.id)}</h3><p class="process-status">${esc(statusLabel(record))}</p><dl><div><dt>自动观察</dt><dd>${esc(prompts)}</dd></div><div><dt>内容指纹</dt><dd class="mono">${esc(sha)}</dd></div><div><dt>页面标题</dt><dd>${esc(record.observedTitle || "—")}</dd></div></dl><p class="small muted">${esc(record.verificationNote || "")}</p>${url ? `<a class="process-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">打开全过程记录 ↗</a>` : ""}</article>`;
      }).join("")}</div>` : empty("尚无用户补充的过程记录。")}`;
  }

  function renderConfigurationUsage() {
    const products = arr(configurationUsage.products);
    const images = arr(configurationUsage.images);
    const policy = configurationUsage.policy || {};
    const imageById = new Map(images.map((item) => [item.id, item]));
    const totalLabel = (product) => product.visibleUsageTotal === null || product.visibleUsageTotal === undefined
      ? "不加总"
      : Number(product.visibleUsageTotal).toLocaleString("zh-CN", {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const evidenceFigure = (id) => {
      const item = imageById.get(id); if (!item) return "";
      const uri = mediaUri(item.mediaId);
      return `<figure class="context-image"><button type="button" data-open-evidence="${esc(id)}" aria-label="查看${esc(item.title)}证据图">${uri ? `<img src="${uri}" alt="${esc(item.title)}" loading="lazy">` : `<span class="evidence-missing">证据图未内嵌</span>`}</button><figcaption><strong>${esc(item.title)}</strong><span>${esc(`原件 ${item.width}×${item.height} · ${bytes(item.bytes)} · SHA-256 ${String(item.sha256).slice(0,16)}… · 页面内嵌高质量显示副本`)}</span></figcaption></figure>`;
    };
    const detailRows = (product) => arr(product.usageRecords).map((row) => `<tr><td>${esc(row.time)}</td><td>${esc(row.request)}</td><td>${esc(row.model)}</td><td class="mono">${esc(row.usageDisplay)}</td></tr>`).join("");
    $("#context-content").innerHTML = `<div class="context-notes"><div><strong>不参与评分</strong><span>${esc(policy.comparisonRule || "不同产品单位不作横向换算。")}</span></div><div class="privacy-warning"><strong>隐私提示</strong><span>${esc(policy.privacyNote || "原图可能含账号标识。")}</span></div></div>
      <div class="table-wrap"><table class="context-summary-table"><thead><tr><th>产品</th><th>任务 / 工作区</th><th>配置与模型</th><th>截图时段 / 可见记录</th><th>可见用量 / 费用摘要</th><th>余额或套餐快照</th></tr></thead><tbody>${products.map((product) => `<tr><td><strong>${esc(product.productLabel || product.tool)}</strong><small>${esc(product.tool)}</small></td><td>${esc(product.taskOrWorkspace)}</td><td>${esc(product.configuration)}<small>${esc(product.modelsObserved)}</small></td><td>${esc(product.usagePeriod || "未提供用量或费用明细")}<small>${esc(product.visibleRecordCount == null ? "未提供" : `${product.visibleRecordCount}条`)}</small></td><td><strong>${esc(totalLabel(product))}</strong><small>${esc(product.usageUnit || "—")}</small><small>${esc(product.totalMethod)}</small></td><td>${esc(product.balanceSnapshot)}</td></tr>`).join("")}</tbody></table></div>
      <p class="small muted context-scope-note">${esc(policy.scopeRule || "截图只代表拍摄时点。")} ${esc(policy.thirdPartyBillingRule || "")} ${esc(policy.experimentalDesign || "")}</p>
      <div class="context-products">${products.map((product) => `<article class="panel context-product" style="--tool:${toolColor.get(product.tool)}"><header><div><span class="tool-badge">${esc(product.tool)}</span><h3>${esc(product.productLabel || product.tool)}</h3></div><span class="chip">不计分</span></header><div class="context-image-grid">${evidenceFigure(product.configurationEvidenceId)}${evidenceFigure(product.usageEvidenceId)}</div>${product.visibleRecordCount == null ? `<p class="small muted">未提供该产品的用量或费用截图，不推断用量或成本。</p>` : `<details><summary>展开${esc(product.visibleRecordCount)}条截图可见用量/费用记录</summary><div class="table-wrap"><table class="context-detail-table"><thead><tr><th>时间</th><th>截图中的请求/操作</th><th>模型</th><th>用量/费用显示</th></tr></thead><tbody>${detailRows(product)}</tbody></table></div></details>`}</article>`).join("")}</div>`;
  }

  function browserControls() {
    const option = (value, label) => `<option value="${esc(value)}">${esc(label)}</option>`;
    return `<div class="panel browser-panel"><div class="filter-grid">
      <label class="filter-field"><span>记录类型</span><select id="filter-record-type">
        ${option("finding", "复核发现")}${option("scenario", "场景实测")}${option("coverage", "覆盖记录")}</select></label>
      <label class="filter-field"><span>工具</span><select id="filter-tool">${option("all", "全部")}${tools.map((tool) => option(tool, tool)).join("")}</select></label>
      <label class="filter-field"><span>产物</span><select id="filter-kind">${option("all", "全部")}${kinds.map((kind) => option(kind, kindLabels[kind])).join("")}</select></label>
      <label class="filter-field"><span>闸门</span><select id="filter-gate">${option("all", "全部")}${option("G0", "G0")}${option("G1", "G1")}${option("G2", "G2")}</select></label>
      <label class="filter-field"><span>严重度</span><select id="filter-severity">${option("all", "全部")}${option("critical", "关键")}${option("major", "主要")}${option("minor", "轻微")}${option("info", "信息")}</select></label>
      <label class="filter-field wide"><span>全文检索</span><input id="filter-query" type="search" placeholder="观察、解读、反证条件、页码、Sheet……"></label>
    </div></div>`;
  }

  function dialogsMarkup() {
    return `<dialog id="artifact-dialog" aria-labelledby="artifact-dialog-title"><div class="modal-head"><div class="modal-head-copy"><h2 id="artifact-dialog-title">文件详情</h2><span id="artifact-dialog-position" class="modal-position" aria-live="polite"></span></div><div class="modal-head-tools"><button class="text-button modal-step" type="button" data-dialog-kind="artifact" data-dialog-step="-1" aria-label="上一件终稿">上一件</button><button class="text-button modal-step" type="button" data-dialog-kind="artifact" data-dialog-step="1" aria-label="下一件终稿">下一件</button><span id="artifact-dialog-primary-action" class="modal-primary-action"></span><button class="modal-close" type="button" data-close-dialog aria-label="关闭文件详情">×</button></div></div><div class="modal-body" id="artifact-dialog-body"></div></dialog>
      <dialog id="evidence-dialog" aria-labelledby="evidence-dialog-title"><div class="modal-head"><div class="modal-head-copy"><h2 id="evidence-dialog-title">证据</h2><span id="evidence-dialog-position" class="modal-position" aria-live="polite"></span></div><div class="modal-head-tools"><button class="text-button modal-step" type="button" data-dialog-kind="evidence" data-dialog-step="-1" aria-label="上一条证据">上一条</button><button class="text-button modal-step" type="button" data-dialog-kind="evidence" data-dialog-step="1" aria-label="下一条证据">下一条</button><div class="evidence-zoom-controls" role="group" aria-label="证据图片缩放"><button class="text-button" type="button" data-evidence-zoom="fit" aria-pressed="true">适合窗口</button><button class="text-button" type="button" data-evidence-zoom="100" aria-pressed="false">100%</button></div><span id="evidence-dialog-primary-action" class="modal-primary-action"></span><button class="modal-close" type="button" data-close-dialog aria-label="关闭证据详情">×</button></div></div><div class="modal-body" id="evidence-dialog-body"></div></dialog>`;
  }

  function renderRanking() {
    const perspectiveLabels = { standalone: "正式固定终稿排名", firstOrigin: "探索性首次归责诊断" };
    const perspectiveMeanings = {
      standalone: "每件冻结终稿按独立使用质量评价；同一问题传播至多件终稿时，各终稿分别反映使用风险。",
      firstOrigin: "仅对已枚举的完全继承项去重，用于观察归责口径变化；不是因果结论或采购排名。",
    };
    $("#ranking-content").innerHTML = `<div class="ranking-all-guide"><strong>阅读口径</strong><span>正式排名与首次归责诊断均分别列示均衡投研实务和六任务等权结果。</span></div>
      <figure class="publication-figure" id="visual-ranking-main" aria-describedby="caption-ranking-main"><div class="ranking-perspective-stack">${["standalone", "firstOrigin"].map((perspective, perspectiveIndex) => { const role = perspective === "standalone" ? "official" : "diagnostic"; const emphasis = role === "official" ? "primary" : "secondary"; return `<section class="ranking-perspective-group ranking-perspective-${emphasis}" data-ranking-role="${role}" data-visual-priority="${emphasis}" aria-labelledby="ranking-perspective-${perspective}"><header class="ranking-perspective-head"><span>评价视角 ${String(perspectiveIndex + 1).padStart(2, "0")}</span><div><div class="ranking-perspective-title"><h4 id="ranking-perspective-${perspective}">${esc(perspectiveLabels[perspective])}</h4><b class="ranking-role-badge" data-role="${role}">${role === "official" ? "正式结果" : "探索性 · 非因果"}</b></div><p>${esc(perspectiveMeanings[perspective])}</p></div></header><div class="ranking-static-grid">${["practical", "equalTask"].map((mode) => rankingStaticPanel(perspective, mode)).join("")}</div></section>`; }).join("")}</div>${figureCaption("ranking-main")}</figure>
      <div class="uncertainty-legend ranking-shared-legend"><span><i class="legend-point"></i>圆点为连续分点估计，浅色线段为已分类专家/混合判断敏感性范围</span><span>近分组仅表示排序后相邻分差≤1分；不等于并列、统计检验或产品总体结论</span></div>`;
  }

  function renderHeatmap() {
    $("#heatmap-content").innerHTML = `<div class="matrix-click-guide" role="note"><strong><span aria-hidden="true">↗</span> 打开评分卡</strong><span>选择任一单元格，查看逐项评分、问题、闸门、证据及对应原件。</span><em>查看详情 →</em></div><div class="matrix-legend"><span>当前：独立终稿正式分</span><span>连续分不应用数值封顶</span><span>闸门另行显示</span></div><div class="table-wrap"><table class="heat-table" id="visual-quality-matrix" aria-describedby="caption-quality-matrix">${tableCaption("quality-matrix")}<thead><tr><th>工具</th>${kinds.map((kind) => `<th>${esc(kindLabels[kind])}</th>`).join("")}</tr></thead><tbody>
      ${tools.map((tool, toolIndex) => `<tr><th><span class="tool-label" style="--tool:${toolColor.get(tool)}"><i class="tool-dot"></i>${esc(tool)}</span></th>${kinds.map((kind, kindIndex) => {
        const artifact = artifactFor(tool, kind); if (!artifact) return "<td>—</td>";
        const score = artifactScore(artifact); const gate = gateCode(artifact);
        return `<td class="heat-cell-shell" data-artifact-cell="${esc(artifact.id)}"><button type="button" class="heat-cell" data-open-artifact="${esc(artifact.id)}" style="--score:${score ?? 0};--hint-delay:${((toolIndex * kinds.length + kindIndex) * .07).toFixed(2)}s" aria-label="${esc(`${tool} ${kindLabels[kind]} ${fmt(score, 1)}分 ${gateDisplay(gate)}，点击查看详情与原件`)}"><strong>${fmt(score, 1)}</strong><small>${esc(gateDisplay(gate))} ${gateSymbol(gate)}</small></button></td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function renderGates() {
    const definitions = arr(RAW.deliveryGates?.definitions || RAW.methodology?.deliveryGateDefinitions).filter((item) => ["G0", "G1", "G2", "G2-Mac"].includes(item.code));
    const postObservation = obj(RAW.methodology?.postObservationRuleDisclosure);
    $("#gates-content").innerHTML = `${gateSummaryMarkup()}
      ${definitions.length ? `<div class="gate-definitions">${definitions.map((item) => `<article><strong>${esc(item.code)} · ${esc(item.label || "")}</strong><p>${esc(item.definition || "")}</p></article>`).join("")}</div>` : ""}
      ${postObservation.ruleId || postObservation.statement ? `<aside class="gate-rule-disclosure" role="note"><div><span>观察后规则披露</span><strong>${esc(postObservation.statement || "该G2规则不是事前预注册规则，而是在观察样本问题后制定并对五家对称复核。")}</strong></div><dl><div><dt>规范规则ID</dt><dd class="mono">${esc(postObservation.ruleId || "—")}</dd></div><div><dt>预注册</dt><dd>${postObservation.preRegistered === false ? "否" : esc(displayScalar(postObservation.preRegistered))}</dd></div><div><dt>分数影响</dt><dd>${esc(postObservation.scoreEffect === "none" ? "不改变连续分" : displayScalar(postObservation.scoreEffect))}</dd></div></dl></aside>` : ""}
      <div class="table-wrap"><table class="gate-table" id="visual-delivery-gates" aria-describedby="caption-delivery-gates">${tableCaption("delivery-gates")}<thead><tr><th>工具</th>${kinds.map((kind) => `<th>${esc(kindLabels[kind])}</th>`).join("")}</tr></thead><tbody>${tools.map((tool) => `<tr><th>${esc(tool)}</th>${kinds.map((kind) => {
        const artifact = artifactFor(tool, kind); if (!artifact) return "<td>—</td>";
        const record = gateRecord(artifact); const code = gateCode(artifact);
        const reason = record.reason || record.summary || record.note || "";
        return `<td><button type="button" class="gate-cell" data-gate="${gateBase(code)}" data-open-artifact="${esc(artifact.id)}" title="${esc(reason)}"><strong>${esc(gateDisplay(code))} ${gateSymbol(code)}</strong><small>${esc(shortReason(reason))}</small></button></td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function compatibilityRows() {
    const root = RAW.compatibilityMatrix;
    if (Array.isArray(root)) return root;
    const primary = arr(root?.entries || root?.rows || root?.tests);
    const crossChecks = arr(root?.crossChecks || root?.crossValidation || root?.platformChecks);
    const verified = arr(root?.verifiedChecks);
    const pending = arr(root?.pendingChecks);
    const seen = new Set();
    return [...primary, ...crossChecks, ...verified, ...pending].filter((row, index) => {
      const key = row?.rowId || row?.id || `${row?.artifactId || "compat"}:${row?.test || row?.observation || index}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function codeLabel(value) {
    const labels = {
      repair_required_then_content_and_functions_preserved: "首次打开要求修复；修复后内容与功能保全",
      repair_required_then_8_of_16_slides_and_7_charts_lost: "首次打开要求修复；修复后16页中8页空白且丢失7张图表",
      native_runtime_review_completed: "已完成指定原生应用审查",
      not_tested_outside_fixed_environment: "固定环境以外未验证",
      pending: "待验证",
    };
    return labels[value] || publicationLabel(value) || displayScalar(value);
  }

  function compatibilityArtifactLabel(row, artifact) {
    if (artifact) return `${artifact.tool} · ${kindLabels[artifact.kind]}`;
    if (row.artifactLabel || row.label || row.title) return row.artifactLabel || row.label || row.title;
    const shortKinds = { excel: "Excel", word: "Word", ppt: "PPT", image: "普通图", ink: "水墨图", html: "HTML" };
    if (row.tool || row.kind) return `${row.tool || ""}${shortKinds[row.kind] || row.kind || ""}专项验证`;
    const marker = `${row.rowId || ""} ${row.test || ""}`.toLowerCase();
    if (marker.includes("doubao") && (marker.includes("ppt") || marker.includes("powerpoint"))) return "豆包PPT专项验证";
    return "专项兼容验证";
  }

  function repairWorkflowRows() {
    const compatibility = compatibilityRows();
    const firstOpenRuns = scenarioRuns.filter((run) => {
      const marker = String(run.scenarioId || run.scenario || run.id || "").toLowerCase();
      return marker.includes("first-open") && (run.measurements?.repairRequired === true || /repair_required|要求修复|需修复/i.test(String(run.actual || run.result || "")));
    });
    return firstOpenRuns.map((firstOpen) => {
      const artifact = artifactById.get(firstOpen.artifactId);
      const integrity = scenarioRuns.find((run) => run.artifactId === firstOpen.artifactId && (
        run.measurements?.firstOpenByteIdentical === true || /sample-integrity/.test(String(run.scenarioId || run.id || ""))
      )) || {};
      const base = compatibility.find((row) => row.artifactId === firstOpen.artifactId && /^repair_required/.test(String(row.observation || ""))) || {};
      const repairCheck = compatibility.find((row) => row.artifactId === firstOpen.artifactId && /修复副本|修复后|内容保持/.test(String(row.test || row.title || ""))) || {};
      const postRepair = scenarioRuns.filter((run) => run.artifactId === firstOpen.artifactId && run.id !== firstOpen.id && (
        run.copyRole === "repair" || run.measurements?.repairDerived === true || run.measurements?.derivedFromRepair === true || run.measurements?.derivedFromRole === "repair"
      ));
      const failedPost = postRepair.filter((run) => !["pass", "passed", "success", "verified", "complete"].includes(String(run.status || "").toLowerCase()));
      const notablePost = failedPost[0] || postRepair.find((run) => /#name|residual|error|错误|丢失|空白|失败/i.test(String(run.actual || run.result || ""))) || postRepair[0] || {};
      const repairObservation = base.observation || repairCheck.result || repairCheck.observation || "已在单独修复副本上执行修复";
      const repairStatus = /lost|丢失|空白|unavailable|widespread/i.test(String(repairObservation)) ? "fail" : "repair";
      const firstIds = evidenceIds([
        ...evidenceIds(integrity.evidenceIds || integrity.evidence),
        ...evidenceIds(firstOpen.evidenceIds || firstOpen.evidence),
      ]);
      const repairIds = evidenceIds(repairCheck.evidenceIds || repairCheck.evidence);
      const postIds = evidenceIds(postRepair.flatMap((run) => evidenceIds(run.evidenceIds || run.evidence)));
      return {
        artifact,
        integrity,
        firstOpen,
        repairObservation,
        repairStatus,
        firstIds,
        repairIds: repairIds.length ? repairIds : firstIds,
        postIds,
        postRepair,
        failedPost,
        notablePost,
      };
    });
  }

  function renderCompatibility() {
    const rows = compatibilityRows();
    if (!rows.length) { $("#compatibility-content").innerHTML = empty("未登记兼容性证据。"); return; }
    const repairWorkflows = repairWorkflowRows();
    const grouped = new Map();
    rows.forEach((row) => {
      const artifact = artifactById.get(row.artifactId);
      const group = artifact?.tool || row.tool || "专项交叉验证";
      if (!grouped.has(group)) grouped.set(group, []);
      grouped.get(group).push(row);
    });
    const renderedRows = [...grouped.entries()].map(([group, groupRows]) => `<tr class="compat-group-row"><th colspan="7">${esc(group)}</th></tr>${groupRows.map((row) => {
      const artifact = artifactById.get(row.artifactId); const gate = artifact ? gateRecord(artifact) : {};
      const findingEvidence = arr(gate.findingIds).flatMap((findingId) => evidenceIds(findings.find((finding) => finding.id === findingId)?.evidenceIds));
      const directEvidence = evidenceIds(row.evidenceIds || row.evidence);
      const ids = directEvidence.length ? directEvidence : evidenceIds(findingEvidence);
      const code = row.gate || (artifact ? gateCode(artifact) : "");
      const derivedStatus = !code ? "pending" : gateBase(code) === "G0" ? "pass" : gateBase(code) === "G1" ? "warn" : "fail";
      const context = [row.testedEnvironment || row.platform, row.testedApplication || row.application].filter(Boolean).join(" / ") || row.test || "—";
      const label = compatibilityArtifactLabel(row, artifact);
      return `<tr><td><strong>${esc(label)}</strong>${row.rowId ? `<small class="mono compat-row-id technical-only">${esc(row.rowId)}</small>` : ""}</td><td>${esc(codeLabel(context))}</td><td>${esc(row.version || row.applicationVersion || "—")}</td><td>${statusChip(row.status || row.resultStatus || derivedStatus)} ${code ? gateChip(code) : ""}</td><td>${esc(codeLabel(row.observation || row.result || row.summary || "—"))}</td><td>${esc(codeLabel(row.causeStatus || row.crossPlatformStatus || (row.status === "pending" ? "待验证" : "证据不足")))}</td><td>${evidenceButtons(ids, 2)}</td></tr>`;
    }).join("")}`).join("");
    $("#compatibility-content").innerHTML = `<div class="compat-note panel panel-pad"><strong>归因与评分原则</strong><p>已观察结果只对应记录中的应用、版本与系统；“未验证”不视为失败，亦不能用于推断跨平台原因。首次打开必须使用与原件字节一致的副本；修复只在单独副本上执行，用于检验可恢复性，不能用修复后版本替代原件的首次交付体验。修复后的内容损失或功能失败只计入对应原生子测试，不再叠加同根固定罚分。</p></div>
      ${repairWorkflows.length ? `<section class="repair-workflow" aria-label="首次打开、修复与修复后验证"><header><h4>需修复文件的三阶段证据链</h4><p>分阶段披露用户首次交付体验和修复后可恢复性；两者不互相替代。</p></header><div class="table-wrap"><table class="repair-chain-table"><thead><tr><th>文件</th><th>① 首次打开（字节一致副本）</th><th>② 单独修复副本</th><th>③ 修复后正常使用验证</th></tr></thead><tbody>${repairWorkflows.map((item) => {
        const firstText = [item.integrity.actual || item.integrity.result, item.firstOpen.actual || item.firstOpen.result || "首次打开要求修复"].filter(Boolean).join("；");
        const passedPost = item.postRepair.length - item.failedPost.length;
        const postSummary = item.postRepair.length ? `${item.postRepair.length}项修复后场景：${passedPost}项通过、${item.failedPost.length}项失败。${item.notablePost.actual || item.notablePost.result || ""}` : "未登记修复后正常使用场景。";
        const postStatus = !item.postRepair.length ? "pending" : item.failedPost.length ? "fail" : "pass";
        return `<tr><th>${esc(item.artifact ? `${item.artifact.tool} · ${kindLabels[item.artifact.kind]}` : item.firstOpen.artifactId)}</th><td>${statusChip(item.firstOpen.status || "fail")}<p>${esc(codeLabel(firstText))}</p>${evidenceButtons(item.firstIds, 2)}</td><td>${statusChip(item.repairStatus)}<p>${esc(codeLabel(item.repairObservation))}</p>${evidenceButtons(item.repairIds, 2)}</td><td>${statusChip(postStatus)}<p>${esc(codeLabel(postSummary))}</p>${evidenceButtons(item.postIds, 3)}</td></tr>`;
      }).join("")}</tbody></table></div></section>` : ""}
      <div class="table-wrap"><table class="compat-table" id="visual-compatibility-matrix" aria-describedby="caption-compatibility-matrix">${tableCaption("compatibility-matrix")}<thead><tr><th>文件</th><th>平台 / 应用</th><th>版本</th><th>状态</th><th>观察结果</th><th>原因状态</th><th>证据</th></tr></thead><tbody>${renderedRows}</tbody></table></div>`;
  }

  function displayScalar(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "是" : "否";
    if (typeof value === "number") return fmt(value);
    if (Array.isArray(value)) return value.map(displayScalar).join(" · ");
    if (typeof value === "object") {
      const labels = { observedLocations: "已观察", population: "总体", populationUnit: "单位", locator: "定位", v4PrimaryPointImpact: "v4主分影响", v4CausalRestoration: "去重恢复", v3CapOrPenaltyImpact: "v3封顶/罚分影响", criterion: "相关维度", excel: "Excel", score: "分数", gate: "闸门" };
      return Object.entries(value).map(([key, item]) => `${labels[key] || publicationLabel(key)}：${displayScalar(item)}`).join(" · ");
    }
    return humanizeText(value);
  }

  function findingAttribution(record) {
    const structured = obj(record.criterionDelta);
    const rawPoints = num(structured.points)
      ?? num(record.scoreImpact?.dimensionGapAttributionShare)
      ?? num(record.criterionDelta)
      ?? num(record.scoreImpact?.v4PrimaryPointImpact);
    if (rawPoints === null) return null;
    return {
      points: Math.abs(rawPoints),
      semantic: structured.semantic || "dimension_gap_equal_attribution_share",
      isCounterfactual: structured.isFindingRemovalCounterfactual === true,
      definition: structured.definition || "该finding在所属维度相对满分缺口中的归因份额；不是删除该finding后分数必然回升的反事实增量。",
    };
  }

  function sensitivityGroups() {
    const primary = RAW.sensitivity;
    const root = (Array.isArray(primary) ? primary.length : Object.keys(obj(primary)).length) ? primary : RAW.sensitivityAnalysis;
    const source = root?.scenarios || root?.analyses || root?.items || root;
    return asEntries(source).filter(([key]) => !["status", "method", "generatedAt"].includes(key)).map(([key, value]) => ({ id: key, ...(typeof value === "object" ? value : { value }) }));
  }

  function sensitivityTable(group) {
    const values = arr(group.values || group.rows || group.cases || group.results);
    if (!values.length) {
      const ignored = new Set(["id", "label", "title", "description", "summary", "headline", "result"]);
      const scalars = Object.entries(group).filter(([key, value]) => !ignored.has(key) && (value === null || typeof value !== "object"));
      const rankingCollections = [];
      const walk = (value, prefix = "", depth = 0) => {
        if (depth > 2 || !value || typeof value !== "object") return;
        Object.entries(value).forEach(([key, item]) => {
          const label = prefix ? `${prefix} / ${publicationLabel(key)}` : publicationLabel(key);
          if (Array.isArray(item) && item.length && item.every((row) => row && typeof row === "object" && row.tool)) rankingCollections.push([label, item]);
          else if (!Array.isArray(item) && typeof item === "object") walk(item, label, depth + 1);
        });
      };
      walk(group);
      return `${scalars.length ? `<dl class="sensitivity-kv">${scalars.map(([key, value]) => `<div><dt>${esc(publicationLabel(key))}</dt><dd>${esc(displayScalar(value))}</dd></div>`).join("")}</dl>` : ""}${rankingCollections.length ? `<div class="sensitivity-rankings">${rankingCollections.map(([label, rows]) => `<article><strong>${esc(label)}</strong><ol>${rows.slice().sort((a, b) => (a.rank || 99) - (b.rank || 99)).map((row) => `<li><span>${esc(row.tool)}</span><b>${fmt(row.score)}</b><small>${esc(sensitivityGroupLabel(row))}</small></li>`).join("")}</ol></article>`).join("")}</div>` : (!scalars.length ? `<p>${esc(group.summary || group.description || displayScalar(group.value))}</p>` : "")}`;
    }
    const columns = compact(values.flatMap((item) => Object.keys(obj(item))))
      .filter((key) => !["rankings", "rows", "artifactScores"].includes(key) && values.some((item) => item[key] === null || typeof item[key] !== "object"))
      .slice(0, 6);
    return `<div class="table-wrap"><table class="sensitivity-table"><thead><tr>${columns.map((key) => `<th>${esc(publicationLabel(key))}</th>`).join("")}<th>排名 / 影响</th></tr></thead><tbody>${values.map((item) => {
      const rankLists = Object.entries(item).filter(([, value]) => Array.isArray(value) && value.length && value.every((row) => row && typeof row === "object" && row.tool));
      const ranks = rankLists.map(([label, rows]) => `${publicationLabel(label)}：${rows.slice().sort((a, b) => (a.rank || 99) - (b.rank || 99)).map((row) => `${row.rank || ""}${row.rank ? ". " : ""}${row.tool} ${num(row.score) !== null ? fmt(row.score) : ""} ${sensitivityGroupLabel(row)}`).join(" · ")}`).join(" | ") || arr(item.rankings || item.rows).map((row) => `${row.rank || ""}${row.rank ? ". " : ""}${row.tool || row.label || ""} ${num(row.score) !== null ? fmt(row.score) : ""} ${sensitivityGroupLabel(row)}`).join(" · ");
      return `<tr>${columns.map((key) => `<td>${esc(displayScalar(item[key]))}</td>`).join("")}<td>${esc(ranks || item.impact || item.summary || "—")}</td></tr>`;
    }).join("")}</tbody></table></div>`;
  }

  function renderSensitivity() {
    const groups = sensitivityGroups();
    $("#sensitivity-content").innerHTML = groups.length ? `<figure class="publication-figure publication-table-block" id="visual-sensitivity" aria-describedby="caption-sensitivity"><div class="sensitivity-grid">${groups.map((group, index) => `<details class="panel sensitivity-card" ${index < 2 ? "open" : ""}><summary><span>${esc(publicationLabel(group.label || group.title || group.id))}</span><strong>${esc(displayScalar(group.headline || group.result || "查看重算"))}</strong></summary><div class="details-body">${group.description ? `<p class="muted">${esc(displayScalar(group.description))}</p>` : ""}${sensitivityTable(group)}</div></details>`).join("")}</div>${figureCaption("sensitivity")}</figure>` : empty("未登记敏感性重算结果。");
  }

  function recordArtifact(record) {
    return artifactById.get(record.artifactId) || null;
  }

  function recordsForBrowser() {
    const source = state.browserType === "scenario"
      ? allScenarioRecords()
      : state.browserType === "coverage" ? coverageItems : findings;
    return source.filter((record) => {
      const artifact = recordArtifact(record); const tool = record.tool || artifact?.tool || ""; const kind = record.kind || artifact?.kind || "";
      const gate = gateBase(record.gate || (artifact ? gateCode(artifact) : "G0"));
      if (state.tool !== "all" && tool !== state.tool) return false;
      if (state.kind !== "all" && kind !== state.kind) return false;
      if (state.gate !== "all" && gate !== state.gate) return false;
      if (state.severity !== "all" && String(record.severity || "info").toLowerCase() !== state.severity) return false;
      if (state.query) {
        const haystack = JSON.stringify(record).toLowerCase();
        if (!haystack.includes(state.query.toLowerCase())) return false;
      }
      return true;
    });
  }

  function evidenceButtons(ids, direct = 3) {
    if (!ids.length) return `<span class="muted small">无图像证据</span>`;
    const buttons = ids.map((id, index) => `<button class="text-button" type="button" data-open-evidence="${esc(id)}">证据${index + 1}</button>`);
    if (buttons.length <= direct) return buttons.join("");
    return `${buttons.slice(0, direct).join("")}<details class="record-evidence-more"><summary>全部证据（${buttons.length}）</summary><div class="record-evidence-menu">${buttons.join("")}</div></details>`;
  }

  function findingBody(record) {
    const attribution = findingAttribution(record);
    const rows = [
      ["可复现观察", record.observation || record.summary], ["谨慎解读", record.interpretation], ["原因状态", record.causeStatus],
      ["判断边界", record.claimBoundary],
      ["影响范围", record.scope], ["发现难度", record.detectability], ["修复动作", record.repairEffort], ["反证条件", record.falsificationCriteria],
      ["补救/复测条件", record.remediationCriteria],
      ["缺口归因说明", attribution?.definition],
    ].filter(([, value]) => value);
    return `<dl class="finding-fields">${rows.map(([label, value]) => `<div><dt>${label}</dt><dd>${esc(displayScalar(value))}</dd></div>`).join("")}</dl>`;
  }

  function renderRecords() {
    const records = recordsForBrowser();
    $("#record-content").innerHTML = `<div class="browser-summary"><span class="chip">${state.browserType === "finding" ? "复核发现" : state.browserType === "scenario" ? "场景实测" : "覆盖记录"}</span><span class="result-count">${records.length} 条</span></div><div class="record-list">${records.map((record) => {
      const artifact = recordArtifact(record); const ids = evidenceIds(record.evidenceIds || record.evidence); const gate = record.gate || record.deliveryGateRequest || (artifact ? gateCode(artifact) : "G0");
      const title = record.title || record.summary || record.scenario || record.item || record.locator || record.subtestId || record.id;
      const expected = record.expected ? `<p><strong>预期：</strong>${esc(record.expected)}</p>` : "";
      const actual = state.browserType === "finding" ? findingBody(record) : `<p>${esc(record.actual || record.result || record.note || record.description || "")}</p>${expected}`;
      const attribution = findingAttribution(record);
      return `<article class="record" data-record-id="${esc(record.id || record.runId || record.subtestId || "")}" data-severity="${esc(record.severity || "info")}"><div>${statusChip(record.status || (record.deducted ? "warn" : "pass"))}<div class="record-meta">${gateChip(record.terminalRiskCode || gate)}<span class="chip">${esc(record.severity || "info")}</span></div></div><div><h3>${esc(artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : record.tool || "未关联文件")}</h3><p>${esc(record.locator || record.location || "")}</p></div><div><h3>${esc(title)}</h3>${actual}<div class="finding-impact">${attribution ? `<span class="attribution-share" title="${esc(attribution.definition)}">机械缺口分摊 ${fmt(attribution.points)} 分</span>` : ""}${record.rootCauseId ? `<span>归责根节点 ${esc(record.rootCauseId)}</span>` : ""}${record.lineageRole ? `<span>${esc(lineageRoleLabel(record.lineageRole))}</span>` : ""}${record.immediateUpstreamArtifactId ? `<span>直接上游 ${esc(record.immediateUpstreamArtifactId)}</span>` : ""}</div></div><div class="record-actions">${artifact ? `<button class="text-button" type="button" data-open-artifact="${esc(artifact.id)}">文件详情</button>` : ""}${evidenceButtons(ids)}</div></article>`;
    }).join("")}</div>`;
  }

  function renderEvidence() {
    const visible = evidence.slice(0, state.evidenceLimit);
    const eager = document.documentElement.dataset.printProfile === "full";
    const imageAttributes = eager ? 'loading="eager" decoding="sync" fetchpriority="high"' : 'loading="lazy" decoding="async"';
    $("#evidence-content").innerHTML = evidence.length ? `<div class="evidence-grid">${visible.map((item) => {
      const uri = evidenceUri(item); const artifact = artifactById.get(item.artifactId); const image = evidenceIsImage(item, uri);
      const preview = uri && image ? `<img ${imageAttributes} src="${uri}" alt="${esc(item.title || item.caption || item.id)}">` : `<span class="evidence-missing">${uri ? "结构化记录 · 无图像缩略图" : "证据已登记 · 无图像缩略图"}</span>`;
      return `<article class="evidence-card" data-evidence-id="${esc(item.id)}"><button type="button" data-open-evidence="${esc(item.id)}"><div class="evidence-thumb">${preview}</div><div class="evidence-copy"><h3>${esc(item.title || item.caption || item.id)}</h3><p>${esc(artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : item.application || item.locator || "")}</p></div></button></article>`;
    }).join("")}</div>${visible.length < evidence.length ? `<div class="load-more"><button id="load-more-evidence" class="text-button" type="button">显示更多（${visible.length}/${evidence.length}）</button><button id="show-all-evidence" class="text-button" type="button">显示全部</button></div>` : ""}` : empty("尚无已登记证据。");
  }

  function lineageRoleLabel(role) {
    return ({ origin: "根因起点", exact_propagation: "完全继承", mutated: "语义恶化", independently_reintroduced: "独立重新引入" })[role] || role || "待分类";
  }

  function renderLineage() {
    const flows = arr(RAW.propagation);
    $("#lineage-content").innerHTML = flows.length ? `<figure class="publication-figure" id="visual-propagation" aria-describedby="caption-propagation"><div class="lineage-legend">${["origin", "exact_propagation", "mutated", "independently_reintroduced"].map((role) => `<span class="chip" data-lineage="${role}">${lineageRoleLabel(role)}</span>`).join("")}</div><div class="flow-list">${flows.map((flow) => {
      const nodes = arr(flow.nodes || flow.steps);
      const linkedFindings = arr(flow.findingIds).map((findingId) => findings.find((finding) => finding.id === findingId)).filter(Boolean);
      const fallbackNodes = [flow.originArtifactId, ...arr(flow.spreadArtifactIds)].filter(Boolean).map((id, index) => {
        const linked = linkedFindings.find((finding) => finding.artifactId === id);
        return { artifactId: id, lineageRole: linked?.lineageRole || (index ? "exact_propagation" : "origin") };
      });
      const actualNodes = nodes.length ? nodes : fallbackNodes;
      const roleCounts = actualNodes.reduce((counts, node) => { const role = node.lineageRole || node.role || "unknown"; counts[role] = (counts[role] || 0) + 1; return counts; }, {});
      const scoreMode = "v4：根因起点、语义恶化和独立重引归责；完全继承仅显示终端风险";
      const impact = `本链包含 ${roleCounts.origin || 0} 个起点、${roleCounts.exact_propagation || 0} 个完全继承、${roleCounts.mutated || roleCounts.mutated_or_new || 0} 个语义恶化、${roleCounts.independently_reintroduced || 0} 个独立重引。`;
      return `<article class="flow-card" style="--tool:${toolColor.get(flow.tool)}"><div><strong>${esc(flow.tool || "")}</strong><p class="small muted">${esc(flow.label || flow.id)}</p></div><div><div class="flow-path">${actualNodes.map((node, index) => {
        const artifact = artifactById.get(node.artifactId || node.id); const role = node.lineageRole || node.role;
        return `${index ? `<span class="flow-arrow">→</span>` : ""}<button type="button" class="flow-node" data-lineage="${esc(role || "")}" ${artifact ? `data-open-artifact="${esc(artifact.id)}"` : ""}><span>${esc(artifact ? kindLabels[artifact.kind] : node.label || node.artifactId)}</span><small>${esc(lineageRoleLabel(role))}</small></button>`;
      }).join("")}</div><p>${esc(impact)}</p></div><div><p class="small muted">${esc(scoreMode)}</p></div></article>`;
    }).join("")}</div>${figureCaption("propagation")}</figure>` : empty("尚无传播链记录。");
  }

  function renderFacts() {
    const facts = arr(RAW.facts); const sources = arr(RAW.sources).filter((source) => source.evidenceRole !== "process_replay_context");
    const sourceMap = new Map(sources.map((source) => [source.id, source]));
    const universe = RAW.factAuditUniverse || {};
    const claimRows = arr(RAW.claimLedger?.records);
    const scoredClaims = claimRows.filter((row) => row.benchmarkScopeStatus === "within_fixed_32_fact_universe");
    const strictRows = arr(RAW.strictExcelLineage?.rows);
    const revisions = arr(RAW.scoreRevisionsV45);
    const factSummaryRows = tools.map((tool) => {
      const excel = artifactFor(tool, "excel");
      const score = excel ? legacyScoreRecord(excel) : null;
      const fact = arr(score?.criterionScores).find((row) => row.criterionId?.endsWith(":external-facts"));
      const source = arr(score?.criterionScores).find((row) => row.criterionId?.endsWith(":sources"));
      const period = arr(score?.criterionScores).find((row) => row.criterionId?.endsWith(":period-unit-prediction"));
      const richness = arr(score?.criterionScores).find((row) => row.criterionId?.endsWith(":requirements-richness"));
      return { tool, claimed: scoredClaims.filter((row) => row.tool === tool).length, fact: fact?.weighted, source: source?.weighted, period: period?.weighted, richness: richness?.weighted, total: excel ? artifactScore(excel) : null };
    });
    $("#facts-content").innerHTML = `<div class="panel panel-pad"><h3>核验母表边界</h3><p>${esc(universe.publicationClaim || "仅核验公开列示的核心事实，不代表全部数字鉴证。")}</p><div class="metric-strip"><span><strong>${esc(universe.benchmarkFactCount ?? facts.length)}</strong>项核心基准</span><span><strong>${esc(universe.factsWithSourceLocator ?? "—")}</strong>项带来源定位</span><span><strong>未测量</strong>全工作簿数字覆盖率</span></div><details><summary>展开选取规则与排除项</summary><div class="details-body"><h4>选取规则</h4><ul>${arr(universe.selectionRules).map((item) => `<li>${esc(item)}</li>`).join("")}</ul><h4>未覆盖</h4><ul>${arr(universe.exclusions).map((item) => `<li>${esc(item)}</li>`).join("")}</ul></div></details></div>${facts.length ? `<div class="table-wrap"><table class="fact-table" id="visual-fact-ledger" aria-describedby="caption-fact-ledger">${tableCaption("fact-ledger")}<thead><tr><th>指标</th><th>报告期</th><th>值</th><th>单位</th><th>事实属性 / 财务披露状态</th><th>来源定位</th></tr></thead><tbody>${facts.map((fact) => { const source = sourceMap.get(fact.sourceId); return `<tr data-fact-id="${esc(fact.id || "")}"><td>${esc(fact.metric || fact.name)}</td><td>${esc(fact.period || "—")}</td><td class="numeric">${esc(fact.value ?? "—")}</td><td>${esc(fact.unit || "—")}</td><td>${esc(factAttribute(fact))}</td><td>${esc(factSourceLocator(fact, source))}</td></tr>`; }).join("")}</tbody></table></div>` : empty("尚无事实账本数据。")} 
      <div class="table-wrap"><table class="fact-table" id="visual-v45-fact-summary" aria-describedby="caption-v45-fact-summary">${tableCaption("v45-fact-summary")}<thead><tr><th>工具</th><th>实际主张/母表</th><th>主张覆盖率</th><th>事实正确性</th><th>来源</th><th>期间、单位与属性</th><th>要求覆盖与丰富度</th><th>Excel总分</th></tr></thead><tbody>${factSummaryRows.map((row) => `<tr><td>${esc(row.tool)}</td><td class="numeric">${row.claimed}/32</td><td class="numeric">${fmt(row.claimed / 32 * 100, 1)}%</td><td class="numeric">${fmt(row.fact, 2)}/30</td><td class="numeric">${fmt(row.source, 2)}/8</td><td class="numeric">${fmt(row.period, 2)}/7</td><td class="numeric">${fmt(row.richness, 2)}/10</td><td class="numeric"><strong>${fmt(row.total, 2)}</strong></td></tr>`).join("")}</tbody></table></div>
      <p class="small muted">主张覆盖率只解释事实正确性分母，不直接计分；内容完整度在“要求覆盖与数据丰富度”10分中单独评价。</p>
      <details class="ledger-details"><summary>展开五家Excel逐事实机械重算账本（${scoredClaims.length}条主张—事实关系）</summary><div class="details-body"><p>${esc(RAW.claimLedger?.limitations || "")}</p><div class="table-wrap"><table class="fact-table" id="visual-v45-claim-ledger" aria-describedby="caption-v45-claim-ledger">${tableCaption("v45-claim-ledger")}<thead><tr><th>工具</th><th>事实</th><th>期间</th><th>作品定位</th><th>作品主张</th><th>数值信用</th><th>定义信用</th><th>事实得分率</th><th>来源关系得分</th><th>证据</th></tr></thead><tbody>${scoredClaims.map((row) => { const sf = obj(row.sourceAssessment); const sourcePoints = 2 * ["identity", "priority", "locator", "actionable"].reduce((sum, key) => sum + Number(sf[key] || 0), 0); return `<tr><td>${esc(row.tool)}</td><td>${esc(row.metric || row.factId)}</td><td>${esc(row.period || "—")}</td><td>${esc(row.locator || "—")}</td><td>${esc(row.actualClaim || "—")}</td><td class="numeric">${fmt(Number(row.valueCredit || 0) * 100, 0)}%</td><td class="numeric">${fmt(Number(row.scopeCredit || 0) * 100, 0)}%</td><td class="numeric">${fmt(Number(row.factEarnedFraction || 0) * 100, 1)}%</td><td class="numeric" title="${esc(row.sourceAssessmentNote || "")}">${fmt(sourcePoints, 1)}/8</td><td>${evidenceButtons(evidenceIds(row.evidenceIds))}</td></tr>`; }).join("")}</tbody></table></div></div></details>
      <details class="ledger-details"><summary>展开严格Excel血缘诊断（仅诊断，不进入正式分数）</summary><div class="details-body"><p>${esc(RAW.strictExcelLineage?.definition || "")}</p><p>${esc(RAW.strictExcelLineage?.scope || "")}</p><div class="table-wrap"><table class="fact-table" id="visual-strict-lineage" aria-describedby="caption-strict-lineage">${tableCaption("strict-lineage")}<thead><tr><th>工具</th><th>文件</th><th>已枚举争议主张</th><th>直接来自Excel</th><th>诊断通过率</th><th>状态</th></tr></thead><tbody>${strictRows.map((row) => `<tr><td>${esc(row.tool)}</td><td>${esc(kindLabels[row.kind] || row.kind)}</td><td class="numeric">${esc(row.enumeratedContentiousClaims ?? 0)}</td><td class="numeric">${esc(row.strictExcelPass ?? 0)}</td><td class="numeric">${row.strictExcelPassRate === null ? "—" : `${fmt(row.strictExcelPassRate, 1)}%`}</td><td>${esc(publicationLabel(row.status))}</td></tr>`).join("")}</tbody></table></div></div></details>
      <details class="ledger-details"><summary>展开v4.4→v4.5逐维度分数桥接（${revisions.length}件终稿）</summary><div class="details-body"><div class="table-wrap"><table class="fact-table" id="visual-v45-revisions" aria-describedby="caption-v45-revisions">${tableCaption("v45-revisions")}<thead><tr><th>文件</th><th>旧分</th><th>逐维度变化</th><th>新分</th><th>合计变化</th><th>桥接校验</th></tr></thead><tbody>${revisions.map((row) => { const artifact = artifactById.get(row.artifactId); const bridge = arr(row.criterionBridge).map((item) => `${item.criterionId.split(":").pop()} ${Number(item.delta) >= 0 ? "+" : ""}${fmt(item.delta, 2)}`).join("；"); return `<tr><td>${esc(artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : row.artifactId)}</td><td class="numeric">${fmt(row.oldScore, 2)}</td><td>${esc(bridge || "—")}</td><td class="numeric">${fmt(row.newScore, 2)}</td><td class="numeric">${Number(row.delta) >= 0 ? "+" : ""}${fmt(row.delta, 2)}</td><td class="numeric">${fmt(row.bridgeCheck, 2)}</td></tr>`; }).join("")}</tbody></table></div></div></details>
      <div class="table-wrap source-summary"><table class="source-index-table" id="visual-source-index" aria-describedby="caption-source-index">${tableCaption("source-index")}<thead><tr><th>编号</th><th>来源短标题</th><th>发布机构</th><th>发布日期</th><th>来源层级</th></tr></thead><tbody>${sources.map((source, index) => `<tr><td>S${index + 1}</td><td>${esc(shortSourceTitle(source))}</td><td>${esc(source.publisher || "—")}</td><td>${esc(source.date || source.publishedAt || "—")}</td><td>${esc(publicationLabel(source.tier || source.type || "来源"))}</td></tr>`).join("")}</tbody></table></div><div class="source-grid">${sources.map((source) => { const url = safeHttpUrl(source.url); return `<article class="panel source-card" data-source-id="${esc(source.id || "")}"><span class="chip">${esc(publicationLabel(source.tier || source.type || "来源"))}</span><h3>${esc(source.title || source.name || source.id)}</h3><p>${esc(source.publisher || source.date || source.publishedAt || "")}</p>${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">打开原始来源 ↗</a>` : `<span class="muted small">无外部链接</span>`}</article>`; }).join("")}</div>`;
  }

  function criterionRows() {
    return Object.entries(criteriaByKind).flatMap(([kind, value]) => arr(value.criteria || value).map((item) => ({ kind, ...item })));
  }

  function normalizeRubricCollection(value, inherited = {}) {
    if (!value) return [];
    if (Array.isArray(value)) return value.flatMap((item) => normalizeRubricCollection(item, inherited));
    if (typeof value !== "object") return [];
    const childKeys = ["subitems", "items", "tests", "tasks", "list"];
    const children = childKeys.flatMap((key) => arr(value[key]));
    const own = Object.fromEntries(Object.entries(value).filter(([key]) => !childKeys.includes(key)));
    const looksLikeTest = ["id", "label", "name", "test", "maxPoints", "earnedPoints", "result", "status", "artifactId", "artifactIds", "kind", "tool"].some((key) => key in own);
    if (children.length) return children.flatMap((item) => normalizeRubricCollection(item, { ...inherited, ...own }));
    if (looksLikeTest) return [{ ...inherited, ...own }];
    return Object.entries(value).flatMap(([key, item]) => normalizeRubricCollection(item, { ...inherited, collectionId: inherited.collectionId || key }));
  }

  function crossArtifactRubricItems() {
    const root = obj(RAW.rubricSubtests);
    const combined = [
      ...normalizeRubricCollection(root.crossArtifactTests),
      ...normalizeRubricCollection(root.list),
      ...normalizeRubricCollection(root.scenarioRecords),
      ...normalizeRubricCollection(root.labelChecklistRecords),
    ];
    const seen = new Set();
    return combined.filter((item, index) => {
      const key = item.id || `${item.collectionId || "cross"}:${item.label || item.name || item.test || index}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function rubricAppliesToArtifact(item, artifact) {
    const ids = evidenceIds(item.artifactIds || item.artifacts);
    if (ids.length) return ids.includes(artifact.id);
    if (item.artifactId) return item.artifactId === artifact.id;
    if (item.tool && item.tool !== artifact.tool) return false;
    if (item.kind && item.kind !== artifact.kind) return false;
    return Boolean(item.tool || item.kind);
  }

  function rubricAppendixRows() {
    const seen = new Set();
    const rows = [];
    Object.entries(obj(RAW.rubricSubtests?.artifacts)).forEach(([artifactId, criteria]) => {
      const artifact = artifactById.get(artifactId);
      Object.entries(obj(criteria)).forEach(([criterionId, criterion]) => {
        arr(criterion.subitems || criterion.items).forEach((item) => {
          const key = `${artifact?.kind || ""}:${criterionId}:${item.id || item.label}`;
          if (seen.has(key)) return;
          seen.add(key);
          rows.push({ kind: artifact?.kind, criterionId, ...item });
        });
      });
    });
    const combined = [...(rows.length ? rows : rubricSubtests), ...crossArtifactRubricItems()];
    const deduped = new Map();
    combined.forEach((row, index) => deduped.set(row.id || `${row.criterionId || ""}:${row.label || row.name || row.test || index}`, row));
    return [...deduped.values()];
  }

  function versionRows() {
    if (Array.isArray(RAW.versionHistory)) return RAW.versionHistory;
    return arr(RAW.versionHistory?.entries || RAW.versionHistory?.changes || RAW.versionHistory);
  }

  function versionDescription(row) {
    const hashes = [
      row.inputJsonSha256 ? `输入JSON SHA-256: ${row.inputJsonSha256}` : "",
      row.archivedHtmlSha256 ? `归档HTML SHA-256: ${row.archivedHtmlSha256}` : "",
      row.outputJsonSha256 ? `输出JSON SHA-256: ${row.outputJsonSha256}` : "",
      row.releaseVerificationSha256 ? `发布核验日志 SHA-256: ${row.releaseVerificationSha256}` : "",
      row.publicationManifestPath ? `最终HTML SHA-256发布清单: ${row.publicationManifestPath}` : "",
      row.publishedHtmlSha256Convention || "",
      row.hashClarification || "",
    ].filter(Boolean).join(" · ");
    return [row.reason, row.impact, row.description, row.summary, hashes].filter(Boolean).join(" · ") || "—";
  }

  function renderAppendix() {
    const methods = Object.entries(obj(RAW.methodology?.v4Principles)).map(([id, rule]) => ({ id, rule }));
    const verification = arr(RAW.verification);
    $("#appendix-content").innerHTML = `<div class="method-grid">
      <article class="panel panel-pad"><h3>现行固定评分原则</h3><ol>${methods.map((item) => `<li>${esc(item.rule)}</li>`).join("")}</ol></article>
      <article class="panel panel-pad"><h3>限制与边界索引</h3><p>完整限制集中列于执行摘要；平台范围、回应性质与评分方法分别见对应章节。</p><ul><li><a href="#key-limitations">关键限制</a></li><li><a href="#compatibility">平台兼容证据</a></li><li><a href="#challenges">工具自评异议</a></li><li><a href="#method">评分方法</a></li></ul></article>
    </div>
    <details class="panel appendix-block" open><summary>v3 → v4 规则变更与版本指纹</summary><div class="appendix-body">${versionRows().length ? `<div class="table-wrap"><table><thead><tr><th>版本 / 变更</th><th>旧规则</th><th>新规则</th><th>摘要、理由与指纹</th></tr></thead><tbody>${versionRows().map((row) => `<tr><td>${esc(row.title || row.id || row.version || "—")}</td><td>${esc(row.before || row.v3 || row.old || "—")}</td><td>${esc(row.after || row.v4 || row.new || "—")}</td><td class="mono small">${esc(versionDescription(row))}</td></tr>`).join("")}</tbody></table></div>` : empty("未登记版本变更。")}</div></details>
    <details class="panel appendix-block"><summary>评分维度与子测试</summary><div class="appendix-body">${RAW.rubricSubtests?.principle ? `<p class="muted">${esc(RAW.rubricSubtests.principle)}</p>` : ""}<div class="table-wrap"><table class="criterion-table"><thead><tr><th>产物</th><th>维度 / 子测试</th><th>权重 / 满分</th><th>评价类型</th><th>验收方式</th></tr></thead><tbody>${criterionRows().map((row) => `<tr><td>${esc(kindLabels[row.kind])}</td><td>${esc(row.label || row.name || row.id)}</td><td>${esc(row.weight ?? "—")}</td><td>${esc(presentation.assessmentClassLabels?.[row.assessmentClass] || row.assessmentClass || "—")}</td><td>${esc(row.anchor || row.description || "—")}</td></tr>`).join("")}${rubricAppendixRows().map((row) => `<tr><td>${esc(kindLabels[row.kind] || row.kind || "子测试")}</td><td>${esc(`${row.criterionId || ""} / ${row.label || row.name || row.test || row.id || "子测试"}`)}</td><td>${esc(row.maxPoints ?? row.weight ?? "—")}</td><td>机械子测试</td><td>${esc(row.expected || row.anchor || row.description || row.result || "按原生实测结果得分")}</td></tr>`).join("")}</tbody></table></div></div></details>
    <details class="panel appendix-block"><summary>待人工复核与未验证项</summary><div class="appendix-body"><div class="verify-list">${verification.map((item) => `<div class="verify-item"><div>${statusChip(item.status)}</div><div><h3>${esc(item.item || item.title || item.id)}</h3><p>${esc(item.reason || item.description || "")}</p></div></div>`).join("")}</div></div></details>
    <details id="artifact-manifest" class="panel appendix-block"><summary>30件终稿原件指纹与完整本地路径</summary><div class="appendix-body"><div class="table-wrap"><table class="manifest-table"><thead><tr><th>工具</th><th>产物</th><th>文件 / 完整路径</th><th>大小</th><th>SHA-256</th><th>闸门</th></tr></thead><tbody>${artifacts.map((artifact) => `<tr><td>${esc(artifact.tool)}</td><td>${esc(kindLabels[artifact.kind])}</td><td>${artifactInlineLink(artifact)}${artifactPath(artifact) ? `<div class="mono small">${esc(artifactPath(artifact))}</div>` : ""}</td><td>${bytes(artifactBytes(artifact))}</td><td class="mono">${esc(artifactSha256(artifact) || "—")}</td><td>${gateChip(gateCode(artifact))}</td></tr>`).join("")}</tbody></table></div></div></details>`;
  }

  function empty(message) { return `<div class="empty">${esc(message)}</div>`; }

  function artifactFindings(artifact) { return findings.filter((finding) => finding.artifactId === artifact.id); }
  function artifactSubtests(artifact) {
    const structured = RAW.rubricSubtests?.artifacts?.[artifact.id];
    if (structured && typeof structured === "object") {
      const local = Object.entries(structured).flatMap(([criterionId, criterion]) => arr(criterion.subitems || criterion.items).map((item) => ({
        ...item, criterionId, criterionPoints: criterion.weightedPoints, evidenceIds: criterion.evidenceIds,
      })));
      return [...local, ...crossArtifactRubricItems().filter((item) => rubricAppliesToArtifact(item, artifact))];
    }
    return [
      ...rubricSubtests.filter((item) => item.artifactId === artifact.id || (!item.artifactId && item.kind === artifact.kind)),
      ...crossArtifactRubricItems().filter((item) => rubricAppliesToArtifact(item, artifact)),
    ];
  }

  function updateDialogNavigation(kind, index, total) {
    const dialog = $(`#${kind}-dialog`);
    if (!dialog) return;
    const position = $(`#${kind}-dialog-position`);
    if (position) position.textContent = `${index + 1} / ${total}`;
    $$(`[data-dialog-kind="${kind}"]`, dialog).forEach((button) => {
      const direction = Number(button.dataset.dialogStep || 0);
      button.disabled = direction < 0 ? index <= 0 : index >= total - 1;
    });
  }

  function artifactPrimaryActionMarkup(artifact) {
    const href = artifactHref(artifact);
    if (!href) return "";
    const profile = artifactAccessProfile(artifact);
    const name = artifactFileName(artifact);
    if (profile.previewable) return `<a class="artifact-action primary modal-cta" href="${esc(href)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(`打开${name}`)}">打开原件 ↗</a>`;
    return `<a class="artifact-action primary modal-cta" href="${esc(href)}" download="${esc(name)}">下载原件 ↓</a>`;
  }

  function evidenceDialogTitle(item, artifact) {
    return item.title || item.caption || compact([
      artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : item.application,
      item.locator || item.location || "证据",
    ]).join("｜") || "证据";
  }

  function evidencePrimaryActionMarkup(uri, title, image = true) {
    const action = image ? "打开原图" : "打开证据文件";
    return uri ? `<a class="artifact-action primary modal-cta" href="${esc(uri)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(`${action}：${title}`)}">${action} ↗</a>` : "";
  }

  function setEvidenceZoom(mode, shouldAnnounce = true) {
    const normalized = mode === "100" ? "100" : "fit";
    const dialog = $("#evidence-dialog");
    if (!dialog) return;
    const image = $(".modal-image img", dialog);
    if (!image) return;
    dialog.dataset.imageMode = normalized;
    image.dataset.zoom = normalized;
    image.style.maxWidth = normalized === "fit" ? "100%" : "none";
    image.style.maxHeight = normalized === "fit" ? "72vh" : "none";
    image.style.width = "auto";
    image.style.height = "auto";
    $$('[data-evidence-zoom]', dialog).forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.evidenceZoom === normalized)));
    if (shouldAnnounce) announce(normalized === "fit" ? "证据图片已适合窗口显示" : "证据图片已按原始尺寸显示");
  }

  function stepDialog(kind, direction) {
    if (kind === "artifact") {
      const next = currentArtifactIndex + direction;
      if (next >= 0 && next < artifacts.length) openArtifact(artifacts[next].id);
      return;
    }
    const next = currentEvidenceIndex + direction;
    if (next >= 0 && next < evidence.length) openEvidence(evidence[next].id);
  }

  function openArtifact(id) {
    const artifact = artifactById.get(id); if (!artifact) return;
    currentArtifactIndex = artifacts.findIndex((item) => item.id === artifact.id);
    const legacy = legacyScoreRecord(artifact) || {};
    const qualityV4 = qualityRecord(artifact) || {};
    const quality = { ...legacy, ...qualityV4, criterionScores: qualityV4.criterionScores || legacy.criterionScores };
    const criteria = arr(quality.criterionScores || quality.criteria || quality.dimensions);
    const gate = gateRecord(artifact); const itemFindings = artifactFindings(artifact); const subtests = artifactSubtests(artifact);
    $("#artifact-dialog-title").textContent = `${artifact.tool} · ${kindLabels[artifact.kind]}`;
    $("#artifact-dialog-primary-action").innerHTML = artifactPrimaryActionMarkup(artifact);
    updateDialogNavigation("artifact", currentArtifactIndex, artifacts.length);
    $("#artifact-dialog-body").innerHTML = `<div class="artifact-modal-content"><nav class="modal-section-nav" aria-label="文件详情内容"><a href="#artifact-modal-file">原件</a><a href="#artifact-modal-scores">逐项评分</a><a href="#artifact-modal-subtests">子测试</a><a href="#artifact-modal-findings">发现与风险</a></nav><div class="artifact-summary"><div><span>独立终稿连续分</span><strong>${fmt(artifactScore(artifact, "independent"), 2)}</strong><small>用于两张正式排名</small></div><div><span>终端独立使用闸门</span>${gateChip(gateCode(artifact), gate.reason || gate.summary)}<small>闸门描述交付风险，不是第二套分数</small></div></div>
      <div id="artifact-modal-file" class="modal-section"><h3>查看或下载原件</h3>${artifactFileCard(artifact)}</div>
      <div id="artifact-modal-scores" class="modal-section"><h3>逐项评分</h3><div class="score-list">${criteria.length ? criteria.map((item) => { const definition = criteriaDefinitionMap.get(item.criterionId || item.id) || {}; const maximum = num(definition.weight) ?? num(item.weight) ?? 0; const earned = num(item.weighted) ?? 0; return `<article class="score-item"><header><strong>${esc(item.label || item.criterionLabel || definition.label || item.criterionId || item.id)}</strong><span>${fmt(earned, 2)} / ${fmt(maximum, 2)}分</span><b>${num(item.rating0To5) !== null ? `${fmt(item.rating0To5, 2)}/5` : ""}</b></header><i class="score-meter" style="--ratio:${maximum ? earned / maximum * 100 : 0}%"><i></i></i><p>${esc(item.basis || item.description || "")}</p></article>`; }).join("") : empty("无维度明细。")}</div></div>
      <div id="artifact-modal-subtests" class="modal-section"><h3>子测试</h3>${subtests.length ? `<div class="subtest-list">${subtests.map((item) => { const ids = evidenceIds(item.evidenceIds || item.evidence); const scored = num(item.earnedPoints) !== null || num(item.maxPoints) !== null; const expected = item.expected ? `预期：${item.expected}` : ""; const actual = item.actual || item.basis || item.description || ""; const detail = [item.criterionId || "", expected, actual ? `实际：${actual}` : ""].filter(Boolean).join(" · "); return `<div><span>${esc(item.label || item.name || item.test || item.id || "子测试")}</span><strong>${scored ? `${fmt(item.earnedPoints, 1)} / ${fmt(item.maxPoints, 1)}` : esc(displayScalar(item.status ?? item.result ?? item.score))}</strong><small>${esc(detail)}</small>${ids.length ? `<footer>${evidenceButtons(ids, 2)}</footer>` : ""}</div>`; }).join("")}</div>` : empty("无子测试记录。")}</div>
      <div id="artifact-modal-findings" class="modal-section"><h3>复核发现、终端风险与归责</h3>${itemFindings.length ? `<div class="finding-detail-list">${itemFindings.map((finding) => { const attribution = findingAttribution(finding); return `<article data-severity="${esc(finding.severity || "info")}" data-finding-id="${esc(finding.id || "")}"><header>${gateChip(finding.terminalRiskCode || finding.gate || finding.deliveryGateRequest || gateCode(artifact))}<span class="chip">${esc(finding.severity || "info")}</span><span class="chip">${esc(finding.attributionTreatment || finding.lineageRole || "未归类")}</span>${attribution ? `<strong class="attribution-share" title="${esc(attribution.definition)}">机械缺口分摊 ${fmt(attribution.points)}分</strong>` : ""}</header><h4>${esc(finding.summary || finding.title || finding.id)}</h4>${findingBody(finding)}<footer>${evidenceButtons(evidenceIds(finding.evidenceIds || finding.evidence))}</footer></article>`; }).join("")}</div>` : empty("未登记问题。")}</div></div>`;
    showDialog($("#artifact-dialog"), `已打开${artifact.tool}${kindLabels[artifact.kind]}文件详情，第${currentArtifactIndex + 1}件，共${artifacts.length}件`);
  }

  function openEvidence(id) {
    const item = evidenceMap.get(id); if (!item) return;
    currentEvidenceIndex = evidence.findIndex((entry) => entry.id === item.id);
    const uri = safeAssetUrl(evidenceUri(item)); const imageUri = evidenceIsImage(item, uri) ? uri : ""; const artifact = artifactById.get(item.artifactId);
    const dialog = $("#evidence-dialog");
    const title = evidenceDialogTitle(item, artifact);
    $("#evidence-dialog-title").textContent = title;
    $("#evidence-dialog-primary-action").innerHTML = evidencePrimaryActionMarkup(uri, title, Boolean(imageUri));
    updateDialogNavigation("evidence", currentEvidenceIndex, evidence.length);
    $("#evidence-dialog-body").innerHTML = `<div class="modal-layout evidence-modal-layout"><div class="modal-image evidence-modal-image">${imageUri ? `<img src="${esc(imageUri)}" alt="${esc(title)}" data-zoom="fit">` : `<span class="evidence-missing">${uri ? "该证据为结构化记录，无图像预览" : "未内嵌图像文件"}</span>`}</div><div class="evidence-modal-copy"><h3>${esc(artifact ? `${artifact.tool} · ${kindLabels[artifact.kind]}` : item.application || "证据元数据")}</h3><dl class="evidence-meta">${[["证据ID", item.id], ["定位", item.locator || item.location], ["动作", item.action], ["应用", item.application], ["版本", item.applicationVersion || item.version], ["采集时间", item.capturedAt || item.captured], ["SHA-256", item.sha256]].filter(([, value]) => value).map(([label, value]) => `<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl><p>${esc(item.description || item.caption || "")}</p>${uri ? `<p class="evidence-original-action"><a href="${esc(uri)}" target="_blank" rel="noopener noreferrer">${imageUri ? "打开证据原图" : "打开证据文件"} ↗</a></p>` : ""}</div></div>`;
    const zoomControls = $(".evidence-zoom-controls", dialog);
    if (zoomControls) zoomControls.hidden = !imageUri;
    $$('[data-evidence-zoom]', dialog).forEach((button) => {
      button.disabled = !imageUri;
      if (!imageUri) button.setAttribute("aria-pressed", "false");
    });
    if (imageUri) setEvidenceZoom("fit", false);
    else delete dialog.dataset.imageMode;
    showDialog(dialog, `已打开第${currentEvidenceIndex + 1}条证据，共${evidence.length}条`);
  }

  function showDialog(dialog, message = "已打开详情") {
    if (!dialog) return;
    const firstOpen = !dialog.open;
    if (firstOpen) {
      dialogReturnFocus.set(dialog, document.activeElement instanceof HTMLElement ? document.activeElement : null);
      dialog.showModal();
    }
    const body = $(".modal-body", dialog);
    if (body) body.scrollTop = 0;
    if (firstOpen) $("[data-close-dialog]", dialog)?.focus({ preventScroll: true });
    announce(message);
  }

  function closeDialog(dialog) {
    if (!dialog?.open) return;
    dialog.close();
    const returnFocus = dialogReturnFocus.get(dialog);
    if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
    dialogReturnFocus.delete(dialog);
    announce("详情已关闭");
  }

  function materializeSection(key) {
    if (materializedSections.has(key)) return;
    const renderers = {
      browser: renderRecords,
      "evidence-index": renderEvidence,
      process: renderProcessRecords,
      context: renderConfigurationUsage,
      appendix: renderAppendix,
      "full-record-print": renderFullPrintLedger,
    };
    const renderer = renderers[key];
    if (!renderer) return;
    renderer();
    materializedSections.add(key);
    const containerId = { browser: "record-content", "evidence-index": "evidence-content", process: "process-content", context: "context-content", appendix: "appendix-content" }[key];
    const container = containerId ? document.getElementById(containerId) : null;
    if (container) container.setAttribute("aria-busy", "false");
    if (container) { decorateInteractiveElements(container); decorateTableSemantics(container); }
  }

  function materializeForPrint(profile = "formal") {
    if (profile === "full") {
      const evidenceWasMaterialized = materializedSections.has("evidence-index");
      state.evidenceLimit = evidence.length;
      ["browser", "evidence-index", "process", "context", "appendix", "full-record-print"].forEach(materializeSection);
      if (evidenceWasMaterialized) renderEvidence();
      primeImagesForPrint(profile);
      return;
    }
    if (profile === "formal") ["process", "context", "appendix"].forEach(materializeSection);
  }

  function primeImagesForPrint(profile) {
    if (profile !== "full") return [];
    const images = $$("#app img");
    images.forEach((image) => {
      image.loading = "eager";
      image.decoding = "sync";
      try { image.fetchPriority = "high"; } catch (_) { /* optional browser hint */ }
    });
    return images;
  }

  function waitForImage(image) {
    if (image.complete) return image.decode?.().catch(() => undefined) || Promise.resolve();
    return new Promise((resolve) => {
      const finish = () => {
        image.removeEventListener("load", finish);
        image.removeEventListener("error", finish);
        Promise.resolve(image.decode?.()).catch(() => undefined).finally(resolve);
      };
      image.addEventListener("load", finish, { once: true });
      image.addEventListener("error", finish, { once: true });
    });
  }

  function prepareForPrint(profile = state.printProfile) {
    materializeForPrint(profile);
    if (profile !== "full") return Promise.resolve();
    if (fullPrintPreparation) return fullPrintPreparation;
    const images = primeImagesForPrint(profile);
    document.documentElement.dataset.printReady = "loading";
    fullPrintPreparation = Promise.race([
      Promise.allSettled(images.map(waitForImage)),
      new Promise((resolve) => setTimeout(resolve, 30000)),
    ]).finally(() => { document.documentElement.dataset.printReady = "true"; });
    return fullPrintPreparation;
  }

  async function requestPrint() {
    const profile = document.documentElement.dataset.printProfile || state.printProfile;
    announce(profile === "full" ? "正在准备全部证据与打印台账" : "正在准备打印版");
    await prepareForPrint(profile);
    announce("打印内容已准备完成");
    window.print();
  }

  function detailsBelongsToPrintProfile(details, profile) {
    if (profile === "full") return true;
    if (profile === "formal") return !details.closest('[data-print-level="full"]');
    return !details.closest('[data-print-level="formal"], [data-print-level="full"]');
  }

  function revealSection(sectionId, targetId = sectionId) {
    const section = document.getElementById(sectionId);
    if (section?.matches("details")) section.open = true;
    materializeSection(sectionId);
    const target = document.getElementById(targetId) || section;
    if (target?.matches("details")) target.open = true;
    window.requestAnimationFrame(() => target?.scrollIntoView({ block: "start" }));
    announce(`已前往${target?.querySelector?.(":scope > summary")?.textContent || target?.id || "目标部分"}`);
  }

  function renderAll() {
    renderProtocol(); renderExecutive(); renderRanking(); renderHeatmap(); renderProfiles(); renderCompatibility(); renderCoverage();
    renderGates(); renderLineage(); renderSensitivity(); renderChallenges(); renderFacts(); renderMethod();
  }

  function bindEvents() {
    document.addEventListener("click", (event) => {
      const artifact = event.target.closest("[data-open-artifact]"); if (artifact) { openArtifact(artifact.dataset.openArtifact); return; }
      const artifactCell = event.target.closest("[data-artifact-cell]"); if (artifactCell) { openArtifact(artifactCell.dataset.artifactCell); return; }
      const evidenceButton = event.target.closest("[data-open-evidence]"); if (evidenceButton) { openEvidence(evidenceButton.dataset.openEvidence); return; }
      const close = event.target.closest("[data-close-dialog]"); if (close) { closeDialog(close.closest("dialog")); return; }
      const step = event.target.closest("[data-dialog-step]"); if (step) { stepDialog(step.dataset.dialogKind, Number(step.dataset.dialogStep)); return; }
      const zoom = event.target.closest("[data-evidence-zoom]"); if (zoom) { setEvidenceZoom(zoom.dataset.evidenceZoom); return; }
      const reveal = event.target.closest("[data-reveal-section]");
      if (reveal) { event.preventDefault(); revealSection(reveal.dataset.revealSection, (reveal.getAttribute("href") || "").replace(/^#/, "")); return; }
      if (event.target.id === "load-more-evidence") { state.evidenceLimit += 36; renderEvidence(); announce(`已显示${Math.min(state.evidenceLimit, evidence.length)}条证据，共${evidence.length}条`); return; }
      if (event.target.id === "show-all-evidence") { state.evidenceLimit = evidence.length; renderEvidence(); announce(`已显示全部${evidence.length}条证据`); return; }
      if (event.target.id === "print-report") { void requestPrint(); return; }
      if (event.target.id === "theme-toggle") {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = next;
        event.target.setAttribute("aria-pressed", String(next === "dark"));
        event.target.setAttribute("aria-label", next === "dark" ? "切换到浅色主题" : "切换到深色主题");
        try { localStorage.setItem("report-v4-theme", next); } catch (_) { /* local file privacy mode */ }
        announce(next === "dark" ? "已切换为深色主题" : "已切换为浅色主题");
      }
      const navCollapse = event.target.closest("#nav-collapse");
      if (navCollapse) { const collapsed = document.documentElement.dataset.navCollapsed !== "true"; setNavigationCollapsed(collapsed, true); announce(collapsed ? "章节导航已折叠" : "章节导航已展开"); }
    });
    document.addEventListener("change", (event) => {
      if (event.target.id === "mobile-nav" && event.target.value) {
        const target = document.getElementById(event.target.value);
        if (target?.matches("details[data-lazy-render]")) revealSection(event.target.value);
        else target?.scrollIntoView({ block: "start" });
        history.replaceState(null, "", `#${event.target.value}`);
        announce(`已前往${event.target.selectedOptions[0]?.textContent?.trim() || "所选章节"}`);
        return;
      }
      const map = { "filter-record-type": "browserType", "filter-tool": "tool", "filter-kind": "kind", "filter-gate": "gate", "filter-severity": "severity" };
      if (map[event.target.id]) { state[map[event.target.id]] = event.target.value; renderRecords(); announce(`筛选后显示${recordsForBrowser().length}条记录`); }
      if (event.target.id === "print-profile") {
        state.printProfile = event.target.value;
        document.documentElement.dataset.printProfile = state.printProfile;
        if (state.printProfile === "full") void prepareForPrint("full");
        announce(`打印模式已切换为${event.target.selectedOptions[0]?.textContent || state.printProfile}`);
      }
    });
    document.addEventListener("input", (event) => { if (event.target.id === "filter-query") { state.query = event.target.value.trim(); renderRecords(); announce(`检索后显示${recordsForBrowser().length}条记录`); } });
    document.addEventListener("toggle", (event) => {
      if (!event.target.matches?.("details")) return;
      const summary = event.target.querySelector(":scope > summary");
      if (summary) summary.setAttribute("aria-expanded", String(event.target.open));
      if (event.target.open && event.target.dataset.lazyRender) materializeSection(event.target.dataset.lazyRender);
    }, true);
    $$('dialog').forEach((dialog) => {
      dialog.addEventListener("click", (event) => { if (event.target === dialog) closeDialog(dialog); });
      dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDialog(dialog); });
    });
    window.addEventListener("beforeprint", () => {
      state.printProfile = document.documentElement.dataset.printProfile || state.printProfile;
      materializeForPrint(state.printProfile);
      primeImagesForPrint(state.printProfile);
      printClosedDetails = $$('details:not([open])').filter((details) => detailsBelongsToPrintProfile(details, state.printProfile));
      printClosedDetails.forEach((details) => { details.open = true; });
    });
    window.addEventListener("afterprint", () => {
      printClosedDetails.forEach((details) => { details.open = false; });
      printClosedDetails = [];
      const ledger = $("#full-record-print");
      if (ledger) ledger.innerHTML = "";
      materializedSections.delete("full-record-print");
    });
  }

  function configureInitialViewport() {
    const query = window.matchMedia?.("screen and (max-width: 480px)");
    const apply = (matches) => { const boundary = $(".report-boundary"); if (boundary && matches) boundary.open = false; };
    if (query) { apply(query.matches); query.addEventListener?.("change", (event) => apply(event.matches)); }
  }

  function restoreTheme() {
    let stored = ""; try { stored = localStorage.getItem("report-v4-theme") || ""; } catch (_) { /* local file privacy mode */ }
    document.documentElement.dataset.theme = stored || "light";
  }

  function observeDynamicInteractions() {
    const app = $("#app");
    if (!app || !("MutationObserver" in window)) return;
    const observer = new MutationObserver((records) => records.forEach((record) => record.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        decorateInteractiveElements(node);
        decorateTableSemantics(node);
      }
    })));
    observer.observe(app, { childList: true, subtree: true });
  }

  function revealInitialHash() {
    const id = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (!id) return;
    if (id === "artifact-manifest") { revealSection("appendix", id); return; }
    const target = document.getElementById(id);
    if (target?.matches("details[data-lazy-render]")) revealSection(id);
  }

  restoreTheme(); renderShell(); restoreNavigationState(); configureInitialViewport(); renderAll(); bindEvents(); decorateInteractiveElements(); decorateTableSemantics(); configureNavigationFeedback(); observeDynamicInteractions();
  if (state.printProfile === "full") void prepareForPrint("full");
  const app = $("#app");
  if (app) app.setAttribute("aria-busy", "false");
  announce("报告已载入");
  window.requestAnimationFrame(revealInitialHash);
})().catch((error) => {
  const app = document.getElementById("app");
  const status = document.getElementById("app-status");
  if (app) {
    app.setAttribute("aria-busy", "false");
    app.textContent = `报告载入失败：${error?.message || "未知错误"}`;
  }
  if (status) status.textContent = "报告载入失败";
  console.error(error);
});
