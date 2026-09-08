// 宇树科技内部汇报PPT —— 深色科技风；数据全部来自已核验底稿（招股书上会稿/上市公告书，截止2026-08-30）
// 视觉指纹: palette 深海军蓝底+电光青+琥珀金; motif 细青色accent线+角标; 字体 微软雅黑; 图表原生可编辑
const PptxGenJS = require("pptxgenjs");
const path = require("path");
const ASSETS = path.join(__dirname, "assets");
const OUT = "/Users/guoqingtao/.qwenworkcn/workspace/mtlqdnun26b6cmrm/outputs/宇树科技内部汇报.pptx";

const BG = "0A1626", PANEL = "10233C", PANEL2 = "0C1B30", EDGE = "1E3A5C";
const CYAN = "00C2FF", GOLD = "F7B731", WHITE = "F5F8FC", MUTED = "8CA3BF", RED = "FF7A6B", GREEN = "35D0A5";
const HEAD = "Microsoft YaHei", BODY = "Microsoft YaHei";
const SRC = "来源：宇树科技招股说明书(上会稿)/科创板上市公告书，上交所披露　|　数据截止 2026-08-30";
const TOTAL = 12;

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.title = "宇树科技(688836.SH)内部研究简报";
pres.author = "QwenWork";

function chrome(s, kicker, title, page) {
  s.background = { color: BG };
  // 顶部motif细线
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.06, fill: { color: CYAN } });
  s.addText(kicker, { x: 0.6, y: 0.32, w: 8, h: 0.3, fontFace: HEAD, fontSize: 11, color: CYAN, charSpacing: 3, bold: true, margin: 0 });
  s.addText(title, { x: 0.6, y: 0.62, w: 12.2, h: 0.75, fontFace: HEAD, fontSize: 24, bold: true, color: WHITE, margin: 0, valign: "top" });
  s.addShape(pres.ShapeType.rect, { x: 0.62, y: 1.42, w: 1.1, h: 0.05, fill: { color: GOLD } });
  // 页脚
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 6.98, w: 12.13, h: 0.012, fill: { color: EDGE } });
  s.addText(SRC, { x: 0.6, y: 7.03, w: 9.6, h: 0.32, fontFace: BODY, fontSize: 8.5, color: MUTED, margin: 0 });
  s.addText(`内部汇报材料 · 不构成投资建议　${page}/${TOTAL}`, { x: 10.2, y: 7.03, w: 2.53, h: 0.32, fontFace: BODY, fontSize: 8.5, color: MUTED, align: "right", margin: 0 });
}
function card(s, x, y, w, h) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.06, fill: { color: PANEL }, line: { color: EDGE, width: 1 } });
}
function kpi(s, x, y, w, h, label, value, sub, color, vsize) {
  card(s, x, y, w, h);
  s.addText(label, { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: 0.3, fontFace: BODY, fontSize: 10.5, color: MUTED, margin: 0 });
  s.addText(value, { x: x + 0.18, y: y + 0.44, w: w - 0.36, h: 0.62, fontFace: HEAD, fontSize: vsize || 27, bold: true, color: color || WHITE, margin: 0 });
  s.addText(sub, { x: x + 0.18, y: y + h - 0.42, w: w - 0.36, h: 0.3, fontFace: BODY, fontSize: 9.5, color: MUTED, margin: 0 });
}
function bullets(s, x, y, w, h, items, size) {
  s.addText(items.map(t => ({ text: t, options: { bullet: { code: "2022", indent: 14 }, paraSpaceAfter: 8, breakLine: true } })),
    { x, y, w, h, fontFace: BODY, fontSize: size || 12, color: "D7E3F2", lineSpacingMultiple: 1.05, valign: "top", margin: 0 });
}
const CH = {
  catAxisLabelColor: MUTED, catAxisLabelFontSize: 10,
  valAxisLabelColor: MUTED, valAxisLabelFontSize: 9,
  catGridLine: { style: "none" }, valGridLine: { color: EDGE, style: "solid", size: 0.75 },
  showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 9,
  fill: PANEL,
};

// ---------- P1 封面 ----------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addImage({ path: path.join(ASSETS, "cover.png"), x: 0, y: 0, w: 13.333, h: 7.5, sizing: { type: "cover", w: 13.333, h: 7.5 } });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: "04101F", transparency: 38 } });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 7.6, h: 7.5, fill: { color: "04101F", transparency: 22 } });
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.06, fill: { color: CYAN } });
  s.addText("内部研究简报　|　资料截止 2026-08-30", { x: 0.8, y: 1.55, w: 7, h: 0.35, fontFace: HEAD, fontSize: 13, color: CYAN, charSpacing: 3, bold: true, margin: 0 });
  s.addText("宇树科技", { x: 0.78, y: 2.05, w: 7, h: 1.05, fontFace: HEAD, fontSize: 54, bold: true, color: WHITE, margin: 0 });
  s.addText("688836.SH　科创板 · 2026-08-19 上市", { x: 0.82, y: 3.12, w: 7, h: 0.4, fontFace: BODY, fontSize: 14, color: MUTED, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: 0.84, y: 3.62, w: 2.2, h: 0.05, fill: { color: GOLD } });
  s.addText("人形机器人第一股的账本：高增长 · 高毛利 · 高投入", { x: 0.8, y: 3.85, w: 7.4, h: 0.5, fontFace: HEAD, fontSize: 21, bold: true, color: GOLD, margin: 0 });
  s.addText("基于上海证券交易所披露的招股说明书、上市公告书及公司官方公开资料", { x: 0.82, y: 4.45, w: 7.6, h: 0.35, fontFace: BODY, fontSize: 11, color: "B9CBDF", margin: 0 });
  s.addText(SRC, { x: 0.8, y: 6.95, w: 10, h: 0.3, fontFace: BODY, fontSize: 8.5, color: MUTED, margin: 0 });
}

// ---------- P2 核心结论 ----------
{
  const s = pres.addSlide();
  chrome(s, "CORE TAKEAWAYS · 核心结论", "罕见“高增长、高毛利、正现金流”样本；短期核心矛盾是高投入与利润的取舍", 2);
  const y = 1.75, w = 2.9, g = 0.178;
  kpi(s, 0.6, y, w, 1.62, "2025 营业收入", "16.99亿元", "2023-2025 CAGR 226.8%", CYAN);
  kpi(s, 0.6 + (w + g), y, w, 1.62, "2025 扣非归母净利润", "5.91亿元", "扣非净利率约 34.8%", GREEN);
  kpi(s, 0.6 + 2 * (w + g), y, w, 1.62, "2025 主营业务毛利率", "60.13%", "同行业可比均值 44.44%", GOLD);
  kpi(s, 0.6 + 3 * (w + g), y, w, 1.62, "2025 人形机器人出货", "5,511台", "全球第一 · 销量5,215台", WHITE);
  card(s, 0.6, 3.62, 12.13, 1.5);
  s.addText("2026H1（未经审计）", { x: 0.82, y: 3.76, w: 4, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true, color: CYAN, margin: 0 });
  bullets(s, 0.82, 4.05, 11.7, 1.0, [
    "营业收入 115,224.56 万元、同比 +48.54%，增速自报告期高位中枢下移；扣非归母净利润 24,393.03 万元、同比 -19.34%。",
    "研发费用同比 +8,203.74 万元、叠加春晚等品牌推广，高投入期利润承压；营收实际数高于招股书预计上限（105,200-112,800 万元）。",
  ], 11.5);
  card(s, 0.6, 5.32, 12.13, 1.42);
  s.addText("一句话判断", { x: 0.82, y: 5.45, w: 4, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true, color: GOLD, margin: 0 });
  s.addText("成长逻辑（人形放量+全栈自研）清晰，估值锚定高成长预期（发行市盈率219.23倍）；跟踪重点是增速中枢、人形毛利率与具身大模型进展。",
    { x: 0.82, y: 5.78, w: 11.7, h: 0.85, fontFace: BODY, fontSize: 12.5, color: "EAF2FB", valign: "top", margin: 0 });
}

// ---------- P3 发行与资本 ----------
{
  const s = pres.addSlide();
  chrome(s, "IPO & CAPITAL · 发行与资本", "募资净额59.17亿元、对应市值约609.93亿元，估值锚定高成长预期", 3);
  const y = 1.75, w = 2.9, g = 0.178;
  kpi(s, 0.6, y, w, 1.55, "发行价格", "150.80元", "新股4,044.6434万股·占10%", WHITE);
  kpi(s, 0.6 + (w + g), y, w, 1.55, "发行后市值", "609.93亿元", "上市标准：市值≥100亿元", CYAN, 22);
  kpi(s, 0.6 + 2 * (w + g), y, w, 1.55, "发行市盈率(扣非孰低)", "219.23x", "行业平均静态PE 38.56x", GOLD);
  kpi(s, 0.6 + 3 * (w + g), y, w, 1.55, "P/S (2025, 按底稿测算)", "≈35.9x", "市值/2025营收", GOLD);
  bullets(s, 0.62, 3.62, 7.6, 3.1, [
    "募集资金总额 609,932.22 万元、净额 591,714.92 万元，高于拟使用募集资金 420,171.12 万元；募投以智能机器人模型/本体研发为主（合计约31.32亿元）。",
    "战略配售占20%：全国社保基金、深度求索（锁定36个月）、昆仑资本、南网产融、天翼资本、启善投资（腾讯关联）、中证投资跟投、员工资管计划。",
    "特别表决权安排：王兴兴发行前表决权68.7816%，发行后降至≤65.3090%；每股特别表决权10票。",
    "发行前最后一轮（2025-06）投后估值127亿元；发行后市值约为其4.8倍（按底稿测算）。",
  ], 12);
  card(s, 8.6, 3.62, 4.13, 3.1);
  s.addText("发行费用明细（不含税）", { x: 8.8, y: 3.76, w: 3.7, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true, color: CYAN, margin: 0 });
  s.addText([
    { text: "承销及保荐费　14,499.32 万元\n", options: { breakLine: true } },
    { text: "审计及验资费　1,828.30 万元\n", options: { breakLine: true } },
    { text: "律师费　1,100.00 万元\n", options: { breakLine: true } },
    { text: "信息披露费　603.77 万元\n", options: { breakLine: true } },
    { text: "其他　185.91 万元\n", options: { breakLine: true } },
    { text: "合计　18,217.31 万元", options: { bold: true, color: GOLD } },
  ], { x: 8.8, y: 4.12, w: 3.75, h: 2.4, fontFace: BODY, fontSize: 11, color: "D7E3F2", paraSpaceAfter: 6, valign: "top", margin: 0 });
}

// ---------- P4 产品结构 ----------
{
  const s = pres.addSlide();
  chrome(s, "PRODUCT MIX · 产品结构", "2025年人形机器人收入占比51.78%，首次超越四足成为第一收入来源", 4);
  s.addChart(pres.ChartType.bar, [
    { name: "四足机器人", labels: ["2023", "2024", "2025"], values: [1.1938, 2.3054, 6.9763] },
    { name: "人形机器人", labels: ["2023", "2024", "2025"], values: [0.0297, 1.073, 8.6783] },
    { name: "组件及其他", labels: ["2023", "2024", "2025"], values: [0.3519, 0.4983, 1.1065] },
  ], { ...CH, x: 0.6, y: 1.7, w: 7.3, h: 4.9, barDir: "col", barGrouping: "stacked", chartColors: [CYAN, GOLD, "5B7A9D"], showValue: false, valAxisTitle: "亿元", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 9 });
  card(s, 8.2, 1.7, 4.53, 4.9);
  s.addText("主营业务收入构成（占比）", { x: 8.4, y: 1.85, w: 4.1, h: 0.3, fontFace: HEAD, fontSize: 12.5, bold: true, color: CYAN, margin: 0 });
  s.addText([
    { text: "2025：人形 86,783.19 万元（51.78%）＞四足 69,762.56 万元（41.62%）＞组件 10,373.67 万元（6.19%）\n\n", options: {} },
    { text: "2024：四足 59.47% ＞ 人形 27.68%\n\n", options: {} },
    { text: "2023：四足 75.78%，人形仅 1.88%（H1首年面市，销量5台）\n\n", options: {} },
    { text: "结构切换是毛利率与估值叙事的核心驱动。", options: { bold: true, color: GOLD } },
  ], { x: 8.4, y: 2.25, w: 4.15, h: 4.1, fontFace: BODY, fontSize: 11.5, color: "D7E3F2", valign: "top", paraSpaceAfter: 4, margin: 0 });
}

// ---------- P5 量价 ----------
{
  const s = pres.addSlide();
  chrome(s, "VOLUME & PRICE · 量价", "“降本—降价—放量”在两条产品线均得到验证：四足累计超33,000台", 5);
  s.addChart(pres.ChartType.bar, [
    { name: "四足机器人销量(台)", labels: ["2023", "2024", "2025"], values: [3121, 7136, 23037] },
    { name: "人形机器人销量(台)", labels: ["2023", "2024", "2025"], values: [5, 412, 5215] },
  ], { ...CH, x: 0.6, y: 1.7, w: 7.3, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: [CYAN, GOLD], showValue: true, dataLabelColor: WHITE, dataLabelFontSize: 8.5 });
  card(s, 8.2, 1.7, 4.53, 2.32);
  s.addText("平均单价走势（万元/台）", { x: 8.4, y: 1.84, w: 4.1, h: 0.3, fontFace: HEAD, fontSize: 12.5, bold: true, color: CYAN, margin: 0 });
  s.addText("四足：3.83 → 3.23 → 3.03\n人形：59.34 → 26.04 → 16.64", { x: 8.4, y: 2.25, w: 4.15, h: 1.5, fontFace: BODY, fontSize: 13, color: "EAF2FB", valign: "top", margin: 0, lineSpacingMultiple: 1.2 });
  card(s, 8.2, 4.22, 4.53, 2.38);
  s.addText("2025 产销", { x: 8.4, y: 4.36, w: 4.1, h: 0.3, fontFace: HEAD, fontSize: 12.5, bold: true, color: GOLD, margin: 0 });
  bullets(s, 8.4, 4.72, 4.15, 1.8, [
    "人形销量5,215台、出货5,511台（全球第一）；出货＞销量系部分尚未签收验收。",
    "四足销量23,037台，报告期累计超33,000台。",
  ], 11);
}

// ---------- P6 收入与盈利 ----------
{
  const s = pres.addSlide();
  chrome(s, "GROWTH · 收入与盈利", "营收CAGR 226.8%至16.99亿元；2025扣非归母5.91亿元，扭亏后快速放大", 6);
  s.addChart(pres.ChartType.bar, [
    { name: "营业收入(亿元)", labels: ["2023", "2024", "2025"], values: [1.5913, 3.9277, 16.9927] },
  ], { ...CH, x: 0.6, y: 1.7, w: 6.0, h: 4.35, barDir: "col", chartColors: [CYAN], showValue: true, dataLabelColor: WHITE, dataLabelFontSize: 10, showLegend: false });
  s.addChart(pres.ChartType.line, [
    { name: "营收YoY(%)", labels: ["2024", "2025"], values: [146.8, 332.6] },
  ], { ...CH, x: 6.75, y: 1.7, w: 5.98, h: 4.35, chartColors: [GOLD], lineSize: 3, showValue: true, dataLabelColor: GOLD, dataLabelFontSize: 10, showLegend: false });
  s.addText("口径提示：2025年归母净利润27,821.05万元与扣非59,075.28万元差异主因股份支付34,906.55万元（非经常性、无现金流出）；2024归母9,547.47万元、2023归母-1,114.51万元。盈利能力分析以扣非口径为主。",
    { x: 0.62, y: 6.2, w: 12.1, h: 0.7, fontFace: BODY, fontSize: 10.5, color: MUTED, valign: "top", margin: 0 });
}

// ---------- P7 盈利质量 ----------
{
  const s = pres.addSlide();
  chrome(s, "QUALITY · 盈利质量", "主营业务毛利率升至60.13%、普遍高于同行；2025经营现金流≈扣非净利1.13倍", 7);
  s.addChart(pres.ChartType.line, [
    { name: "主营业务", labels: ["2023", "2024", "2025"], values: [44.22, 56.74, 60.13] },
    { name: "四足机器人", labels: ["2023", "2024", "2025"], values: [43.71, 51.65, 56.72] },
    { name: "人形机器人", labels: ["2023", "2024", "2025"], values: [87.67, 69.26, 63.18] },
  ], { ...CH, x: 0.6, y: 1.7, w: 7.3, h: 4.9, chartColors: [WHITE, CYAN, GOLD], lineSize: 3, showValue: false, valAxisMaxVal: 100, valAxisMinVal: 0 });
  bullets(s, 8.2, 1.75, 4.55, 4.9, [
    "2025综合毛利率60.44% vs 同行业均值44.44%（优必选37.67%、越疆46.49%、云深处52.83%、乐聚40.78%）。",
    "人形毛利率87.67%→63.18%：G1成为主力（单价/成本/毛利率低于H1）+主动降价巩固地位。",
    "四足毛利率43.71%→56.72%：工艺/采购降本+B2等行业级产品占比提升。",
    "2025销售费用率8.31% vs 行业均值23.88%，规模效应与品牌拉力突出。",
    "2025经营活动现金流净额66,998.18万元，盈利现金含量高。",
  ], 11.5);
}

// ---------- P8 2026中期 ----------
{
  const s = pres.addSlide();
  chrome(s, "2026 INTERIM · 中期跟踪", "增速中枢下移+高投入挤压利润：2026H1营收+48.5%、扣非-19.3%（未经审计）", 8);
  const w = 3.93, g = 0.2;
  kpi(s, 0.6, 1.75, w, 1.5, "2026Q1 营收YoY（审阅）", "+68.49%", "扣非归母 4,025.36 万元、-52.55%", CYAN);
  kpi(s, 0.6 + (w + g), 1.75, w, 1.5, "2026H1 营收（未审计）", "11.52亿元", "同比 +48.54%", CYAN);
  kpi(s, 0.6 + 2 * (w + g), 1.75, w, 1.5, "2026H1 扣非归母（未审计）", "2.44亿元", "同比 -19.34%", RED);
  kpi(s, 0.6, 3.45, w, 1.5, "2026H1 归母（未审计）", "2.74亿元", "上年同期 -3,202.45 万元(含股份支付)", GREEN);
  kpi(s, 0.6 + (w + g), 3.45, w, 1.5, "2026H1 经营现金流（未审计）", "2.32亿元", "同比 -32.53%（备货+费用付现）", GOLD);
  kpi(s, 0.6 + 2 * (w + g), 3.45, w, 1.5, "2026H1 研发费用（未审计）", "1.36亿元", "同比 +8,203.74 万元", GOLD);
  card(s, 0.6, 5.15, 12.13, 1.6);
  s.addText("预测 vs 实际（招股书预计为管理层估计，不构成盈利预测）", { x: 0.82, y: 5.28, w: 9, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true, color: GOLD, margin: 0 });
  bullets(s, 0.82, 5.6, 11.7, 1.1, [
    "预计营收105,200-112,800万元 → 实际115,224.56万元，高于预计上限；预计扣非23,600-28,300万元 → 实际24,393.03万元，区间内。",
    "利润承压主因：研发加大（本体/具身大模型/运动控制）+ 2026央视春晚等品牌推广带来的销售费用大增。",
  ], 11);
}

// ---------- P9 研发投入 ----------
{
  const s = pres.addSlide();
  chrome(s, "R&D · 研发投入", "累计研发2.65亿元、由“本体+小脑”走向“大脑”；募投42.02亿元聚焦模型与本体", 9);
  s.addChart(pres.ChartType.bar, [
    { name: "研发费用(百万元)", labels: ["2023", "2024", "2025", "2026H1"], values: [49.95, 70.02, 144.97, 135.91] },
  ], { ...CH, x: 0.6, y: 1.7, w: 6.0, h: 4.9, barDir: "col", chartColors: [CYAN], showValue: true, dataLabelColor: WHITE, dataLabelFontSize: 9.5, showLegend: false });
  bullets(s, 6.9, 1.75, 5.85, 4.9, [
    "研发费用率31.39%→17.83%→8.53%（收入放大）；2026H1约11.8%（按底稿测算），投入再提速。",
    "截至2025年末研发人员184人、占516人的35.66%；截至2026-01-31注册专利262项（境内发明专利20项）。",
    "2024年起加强具身大模型投入，2025年下半年发布自研通用WMA与VLA模型；尚未规模化应用于产品，自有工厂试点验证。",
    "募投：模型研发202,245.93万元、本体研发110,973.80万元、新产品开发44,540.00万元、制造基地62,411.39万元。",
    "风险口：专利数量偏少；大规模数据采集与场景实训尚未展开。",
  ], 11.5);
}

// ---------- P10 竞争优势 ----------
{
  const s = pres.addSlide();
  chrome(s, "MOAT · 竞争优势", "全栈自研+性能标杆+全球市场地位，构成高毛利、低销售费用率的护城河", 10);
  bullets(s, 0.62, 1.75, 6.6, 4.9, [
    "全栈自研：电机、减速器、灵巧手、激光雷达、关节模组、能源/计算/运动控制/感知系统，成本与集成度领先。",
    "性能标杆：H1奔跑2025年超5米/秒、2026年达10米/秒，连续刷新全尺寸人形世界纪录；2025春晚16台H1《秧BOT》、2026年初24台G1+1台H2《武BOT》；首届世界机器人运动会11枚奖牌（金牌/总奖牌数最多）。",
    "市场地位：四足报告期累计销量超33,000台；2025人形出货全球第一；境外收入占比超40%。",
    "高性价比+生态：科研/消费广覆盖、客户集中度低（前五大12.08%）；战投引入社保基金、深度求索、腾讯关联等。",
  ], 12);
  s.addImage({ path: path.join(ASSETS, "sprint.png"), x: 7.55, y: 1.7, w: 5.18, h: 2.91, sizing: { type: "cover", w: 5.18, h: 2.91 } });
  s.addShape(pres.ShapeType.rect, { x: 7.55, y: 4.61, w: 5.18, h: 0.03, fill: { color: CYAN } });
  s.addText("H1：10米/秒奔跑速度（2026），全尺寸人形世界纪录", { x: 7.55, y: 4.64, w: 5.18, h: 0.28, fontFace: BODY, fontSize: 9.5, color: MUTED, margin: 0 });
  card(s, 7.55, 4.98, 5.18, 1.77);
  s.addText([
    { text: "60.44%　", options: { bold: true, color: GOLD, fontSize: 17 } },
    { text: "2025综合毛利率，高于全部同行可比公司\n", options: { fontSize: 9.5, color: "D7E3F2", breakLine: true } },
    { text: "8.31%　", options: { bold: true, color: CYAN, fontSize: 17 } },
    { text: "2025销售费用率，行业均值23.88%", options: { fontSize: 9.5, color: "D7E3F2" } },
  ], { x: 7.75, y: 5.1, w: 4.8, h: 1.55, fontFace: BODY, valign: "top", margin: 0 });
}

// ---------- P11 增长变量与风险 ----------
{
  const s = pres.addSlide();
  chrome(s, "OUTLOOK · 增长变量与风险", "成长期权在具身大模型与场景渗透；风险在增速、竞争、贸易与治理", 11);
  card(s, 0.6, 1.7, 5.96, 5.05);
  s.addText("增长变量", { x: 0.82, y: 1.84, w: 5, h: 0.35, fontFace: HEAD, fontSize: 14, bold: true, color: CYAN, margin: 0 });
  bullets(s, 0.82, 2.28, 5.55, 4.3, [
    "人形机器人下游场景渗透（科研、表演、巡检救援、智能服务等），2026H1人形收入仍较快增长。",
    "具身大模型（WMA/VLA）突破与数据采集、场景实训投入，决定工业/服务/家庭大市场期权。",
    "制造基地扩产+超募资金弹性；“降本—降价—放量”路径由四足向人形复制。",
  ], 11.5);
  card(s, 6.77, 1.7, 5.96, 5.05);
  s.addText("主要风险", { x: 6.99, y: 1.84, w: 5, h: 0.35, fontFace: HEAD, fontSize: 14, bold: true, color: RED, margin: 0 });
  bullets(s, 6.99, 2.28, 5.55, 4.3, [
    "增速放缓与业绩波动：2026Q1扣非-52.55%；租赁等短期需求热度或退潮。",
    "竞争加剧：特斯拉Optimus Gen-3小批量试产；国内整车/消费电子企业入局；人形毛利率已降至63.18%。",
    "贸易管制：FCC 2026-07-28新规限制新型号认证；2025美国收入占13.30%；约20%原材料经代理进口。",
    "治理与估值：特别表决权集中；后续股份支付将再增费用；上市初期流通股仅7.44%、PE 219.23倍。",
  ], 11.5);
}

// ---------- P12 结论与口径 ----------
{
  const s = pres.addSlide();
  chrome(s, "CONCLUSION · 结论与口径", "成长逻辑清晰、短期看投入与利润取舍；估值兑现要求高", 12);
  bullets(s, 0.62, 1.72, 12.1, 2.2, [
    "定位：通用机器人行业少有的“高增长、高毛利、正现金流”样本；2025人形出货全球第一，全栈自研构筑成本与性能优势。",
    "矛盾：高投入期（研发+品牌）挤压短期利润，增速中枢自226.8%下移至2026H1的48.5%；人形毛利率下行待观察。",
    "跟踪：人形放量与毛利率企稳、具身大模型规模化进展、海外贸易政策、股份支付后续确认。",
  ], 12.5);
  card(s, 0.6, 4.05, 12.13, 1.55);
  s.addText("数据口径（重要）", { x: 0.82, y: 4.18, w: 6, h: 0.3, fontFace: HEAD, fontSize: 12, bold: true, color: GOLD, margin: 0 });
  bullets(s, 0.82, 4.5, 11.7, 1.05, [
    "2023-2025经审计（容诚审字[2026]230Z1692号）；2026Q1经审阅；2026H1未经审计；招股书2026H1预计数据仅为管理层估计、不构成盈利预测。",
    "本材料仅基于上交所披露文件整理，供内部讨论，不构成投资建议。",
  ], 10.5);
  s.addText([
    { text: "主要来源：", options: { bold: true, color: CYAN } },
    { text: "[1]上市公告书(2026-08-18, 上交所披露)　[2]招股说明书(上会稿, 上交所披露)　[3]注册批复 证监许可〔2026〕1612号　[4]审计/审阅报告(容诚)　[5]上市公告书附件二 2026年1-6月报表(未经审计)　[6]配套《宇树科技经营与财务分析底稿.xlsx》", options: { color: MUTED } },
  ], { x: 0.62, y: 5.75, w: 12.1, h: 1.0, fontFace: BODY, fontSize: 9.5, valign: "top", margin: 0 });
}

pres.writeFile({ fileName: OUT }).then(f => console.log("saved", f));
