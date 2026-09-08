#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_unitree_interactive.py
生成《宇树科技 688836.SH 交互式数据报告》单文件 HTML。
- 数据来源（唯一基准）：unitree_excel_spec.md（资料截止 2026-08-30，单位：万元）
- 主视觉图：ppt_cover.png（base64 内嵌）
- 外部依赖仅 ECharts 5 CDN（jsdelivr，失败回退 unpkg）
输出：宇树科技_交互式数据报告.html
"""
import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a"
COVER_PNG = os.path.join(SCRATCH, "ppt_cover.png")
OUT_HTML = os.path.join(BASE_DIR, "宇树科技_交互式数据报告.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宇树科技 688836.SH · 交互式数据报告</title>
<meta name="description" content="宇树科技（688836.SH）科创板人形机器人第一股 · 交互式数据报告，资料截止 2026-08-30">
<style>
:root{
  --navy:#0A1F44; --navy-2:#0D2A5C; --cyan:#19C2FF; --cyan-soft:rgba(25,194,255,.16);
  --violet:#7B61FF; --teal:#2DE2C5; --amber:#FFB020; --rose:#FF6B81;
  --text:#DCE7F5; --sub:#8FA8C9; --card:rgba(255,255,255,.045); --border:rgba(25,194,255,.16);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  background:linear-gradient(180deg,#071228 0%,var(--navy) 34%,#081830 78%,#060F22 100%);
  color:var(--text);
  font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
  line-height:1.8; font-variant-numeric:tabular-nums; overflow-x:hidden;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--cyan);text-decoration:none}
a:hover{text-decoration:underline}
::selection{background:rgba(25,194,255,.32)}

/* 滚动进度条 */
#progressBar{position:fixed;top:0;left:0;height:3px;width:0;z-index:1200;
  background:linear-gradient(90deg,var(--cyan),var(--violet));box-shadow:0 0 12px rgba(25,194,255,.8)}

/* CDN 失败提示条 */
#cdnBanner{display:none;position:fixed;top:3px;left:0;right:0;z-index:1190;
  background:rgba(255,176,32,.14);border-bottom:1px solid rgba(255,176,32,.5);color:#FFD98A;
  text-align:center;font-size:14px;padding:10px 16px;backdrop-filter:blur(10px)}
#cdnBanner.show{display:block}

/* 吸顶导航 */
#topnav{position:sticky;top:0;z-index:1100;backdrop-filter:blur(14px);
  background:rgba(7,15,34,.82);border-bottom:1px solid var(--border)}
#topnav .nav-inner{max-width:1240px;margin:0 auto;display:flex;align-items:center;gap:6px;
  padding:12px 20px;overflow-x:auto;scrollbar-width:none}
#topnav .nav-inner::-webkit-scrollbar{display:none}
#topnav .brand{font-weight:700;letter-spacing:.06em;white-space:nowrap;margin-right:14px;
  color:#fff;font-size:15px}
#topnav .brand em{font-style:normal;color:var(--cyan)}
#topnav a.nav-link{color:var(--sub);font-size:14px;white-space:nowrap;padding:6px 12px;
  border-radius:99px;border:1px solid transparent;transition:all .25s}
#topnav a.nav-link:hover{color:var(--text);text-decoration:none}
#topnav a.nav-link.active{color:#061224;background:linear-gradient(90deg,var(--cyan),#6ED6FF);
  font-weight:600}

/* Hero */
header.hero{position:relative;min-height:100vh;display:flex;flex-direction:column;justify-content:flex-end;
  background-image:linear-gradient(180deg,rgba(7,15,34,.62) 0%,rgba(10,31,68,.78) 46%,rgba(7,15,34,.96) 100%),
    url("data:image/png;base64,__PPT_COVER_B64__");
  background-size:cover;background-position:center 30%;overflow:hidden}
#particles{position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none}
.hero-content{position:relative;z-index:2;max-width:1240px;margin:0 auto;width:100%;
  padding:150px 24px 42px;text-align:left}
.hero-badge{display:inline-block;font-size:13px;letter-spacing:.28em;color:var(--cyan);
  border:1px solid rgba(25,194,255,.45);border-radius:99px;padding:6px 18px;margin-bottom:26px;
  background:rgba(25,194,255,.08)}
.hero-content h1{font-size:clamp(40px,6.4vw,76px);line-height:1.14;color:#fff;font-weight:800;
  letter-spacing:.02em;text-shadow:0 6px 40px rgba(0,0,0,.5)}
.hero-content h1 .ticker{color:var(--cyan);font-weight:700;white-space:nowrap}
.hero-sub{margin-top:16px;font-size:clamp(17px,2.2vw,24px);color:#BFD6F2;letter-spacing:.1em}
.hero-meta{margin-top:14px;font-size:14px;color:var(--sub);letter-spacing:.04em}
.hero-meta b{color:#BFD6F2;font-weight:600}

/* KPI 计数带 */
.kpi-band{position:relative;z-index:2;max-width:1240px;margin:26px auto 0;width:100%;
  padding:0 24px 56px;display:grid;grid-template-columns:repeat(6,1fr);gap:14px}
.kpi-card{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:18px 16px 14px;backdrop-filter:blur(12px);position:relative;overflow:hidden}
.kpi-card::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),transparent);opacity:.7}
.kpi-label{font-size:12.5px;color:var(--sub);letter-spacing:.03em;min-height:34px}
.kpi-value{margin-top:6px;font-size:clamp(20px,1.9vw,27px);font-weight:800;color:#fff;line-height:1.25;
  white-space:nowrap}
.kpi-value .kpi-unit{font-size:13px;color:var(--cyan);font-weight:600;margin-left:4px}
.kpi-note{margin-top:6px;font-size:12px;color:#A9C3E4}
.kpi-card .tag{margin-top:8px}

/* 标签 */
.tag{display:inline-block;font-size:11.5px;line-height:1.6;padding:2px 10px;border-radius:99px;
  border:1px solid var(--border);color:var(--sub);letter-spacing:.02em;white-space:nowrap}
.tag-official{color:#7FD8FF;border-color:rgba(25,194,255,.45);background:rgba(25,194,255,.08)}
.tag-org{color:#C2B6FF;border-color:rgba(123,97,255,.5);background:rgba(123,97,255,.1)}
.tag-mgmt{color:#FFD98A;border-color:rgba(255,176,32,.5);background:rgba(255,176,32,.09)}
.tag-mkt{color:#FFB3C0;border-color:rgba(255,107,129,.5);background:rgba(255,107,129,.09)}
.tag-check{color:#8FF0DC;border-color:rgba(45,226,197,.45);background:rgba(45,226,197,.08)}

/* 主体布局 */
main{position:relative;z-index:2}
section{max-width:1240px;margin:0 auto;padding:96px 24px 30px;scroll-margin-top:84px}
.sec-head{margin-bottom:34px}
.sec-kicker{font-size:13px;letter-spacing:.3em;color:var(--cyan);margin-bottom:10px}
.sec-head h2{font-size:clamp(26px,3.4vw,38px);color:#fff;font-weight:800;letter-spacing:.02em}
.sec-head h2::after{content:"";display:block;width:64px;height:3px;margin-top:14px;border-radius:2px;
  background:linear-gradient(90deg,var(--cyan),transparent)}
.sec-desc{margin-top:12px;color:var(--sub);font-size:15px;max-width:860px}

.glass{background:var(--card);border:1px solid var(--border);border-radius:18px;backdrop-filter:blur(12px)}
.grid{display:grid;gap:18px}
.grid-2{grid-template-columns:1fr 1fr}
.grid-3{grid-template-columns:repeat(3,1fr)}
.grid-4{grid-template-columns:repeat(4,1fr)}
.card{padding:24px}
.card h3{font-size:17px;color:#fff;font-weight:700;margin-bottom:10px}
.card p{font-size:14.5px;color:#C6D6EC}
.card .num{font-weight:800;color:#fff}
.muted{color:var(--sub);font-size:13px}
.accent{color:var(--cyan)}
.chart-card{padding:20px 14px 10px}
.chart-title{padding:0 10px 6px;font-size:15.5px;font-weight:700;color:#fff}
.chart-caption{padding:6px 10px 12px;font-size:12.5px;color:var(--sub)}
.echart{width:100%;height:400px}
.echart-tall{height:440px}

/* 时间线 */
.timeline{position:relative;padding-left:30px}
.timeline::before{content:"";position:absolute;left:8px;top:6px;bottom:6px;width:2px;
  background:linear-gradient(180deg,var(--cyan),rgba(25,194,255,.08))}
.tl-item{position:relative;padding:0 0 26px 16px}
.tl-item::before{content:"";position:absolute;left:-28px;top:8px;width:12px;height:12px;border-radius:50%;
  background:#0A1F44;border:3px solid var(--cyan);box-shadow:0 0 12px rgba(25,194,255,.7)}
.tl-date{font-size:13px;color:var(--cyan);letter-spacing:.05em;font-weight:700}
.tl-title{font-size:16.5px;color:#fff;font-weight:700;margin:2px 0 2px}
.tl-desc{font-size:13.5px;color:var(--sub)}

/* 事实列表 */
.fact-list{list-style:none}
.fact-list li{padding:12px 0;border-bottom:1px dashed rgba(143,168,201,.18);font-size:14.5px;color:#C6D6EC}
.fact-list li:last-child{border-bottom:none}
.fact-list .k{color:#fff;font-weight:700}

/* Tab */
.tabs{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.tab-btn{cursor:pointer;font-size:14px;color:var(--sub);background:rgba(255,255,255,.04);
  border:1px solid var(--border);border-radius:99px;padding:8px 20px;font-family:inherit;transition:all .25s}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{color:#061224;font-weight:700;background:linear-gradient(90deg,var(--cyan),#6ED6FF);
  border-color:transparent}
.tab-panel{display:none}
.tab-panel.active{display:block;animation:fadeIn .45s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

/* 大数字卡 */
.big-card{padding:26px 22px;position:relative;overflow:hidden}
.big-card::after{content:"";position:absolute;right:-40px;top:-40px;width:130px;height:130px;border-radius:50%;
  background:radial-gradient(circle,rgba(25,194,255,.16),transparent 70%)}
.big-num{font-size:clamp(26px,2.6vw,36px);font-weight:800;color:#fff;line-height:1.2}
.big-num .u{font-size:15px;color:var(--cyan);font-weight:700;margin-left:4px}
.big-label{margin-top:8px;font-size:14px;color:#C6D6EC;font-weight:600}
.big-note{margin-top:8px;font-size:12.5px;color:var(--sub)}

/* 表格 */
.table-wrap{overflow-x:auto;border-radius:16px;border:1px solid var(--border)}
table.data{width:100%;border-collapse:collapse;font-size:13.8px;min-width:760px}
table.data th,table.data td{padding:12px 14px;text-align:right;border-bottom:1px solid rgba(143,168,201,.12);white-space:nowrap}
table.data th{background:rgba(25,194,255,.08);color:#BFE6FF;font-weight:700}
table.data th:first-child,table.data td:first-child{text-align:left;color:#fff;font-weight:600}
table.data tr:last-child td{border-bottom:none}
table.data td .cell-note{display:block;font-size:11px;color:var(--sub)}

/* 手风琴 */
.acc-item{border:1px solid var(--border);border-radius:14px;margin-bottom:10px;overflow:hidden;
  background:rgba(255,255,255,.03)}
.acc-head{cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:14px;
  padding:15px 20px;font-size:14.5px;color:#fff;font-weight:600;user-select:none}
.acc-head .ic{flex:none;width:22px;height:22px;border-radius:50%;border:1px solid var(--cyan);color:var(--cyan);
  display:flex;align-items:center;justify-content:center;font-size:15px;transition:transform .3s}
.acc-item.open .acc-head .ic{transform:rotate(45deg)}
.acc-body{max-height:0;overflow:hidden;transition:max-height .4s ease}
.acc-body .inner{padding:0 20px 16px;font-size:13.8px;color:#C6D6EC}

/* 资料来源 */
.src-list{counter-reset:src;list-style:none}
.src-list li{counter-increment:src;position:relative;padding:14px 0 14px 58px;
  border-bottom:1px dashed rgba(143,168,201,.16);font-size:14px;color:#C6D6EC}
.src-list li::before{content:counter(src,decimal-leading-zero);position:absolute;left:0;top:14px;
  font-weight:800;color:var(--cyan);font-size:15px}
.src-list .src-name{color:#fff;font-weight:700}
.src-list .src-type{margin-right:8px}
.src-list .src-url{word-break:break-all;font-size:12.5px}

/* 页脚 */
footer{margin-top:80px;border-top:1px solid var(--border);background:rgba(6,12,26,.7)}
.footer-inner{max-width:1240px;margin:0 auto;padding:44px 24px 54px;color:var(--sub);font-size:13px;line-height:2}
.footer-inner b{color:#BFD6F2}

/* 回到顶部 */
#backTop{position:fixed;right:26px;bottom:26px;z-index:1150;width:46px;height:46px;border-radius:50%;
  border:1px solid rgba(25,194,255,.5);background:rgba(10,31,68,.85);color:var(--cyan);cursor:pointer;
  display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;
  transition:opacity .3s,transform .3s;transform:translateY(12px)}
#backTop.show{opacity:1;pointer-events:auto;transform:none}
#backTop:hover{background:rgba(25,194,255,.18)}
#backTop svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}

/* 滚动渐入 */
.reveal{opacity:0;transform:translateY(26px);transition:opacity .7s ease,transform .7s ease}
.reveal.in{opacity:1;transform:none}

@media (max-width:1080px){
  .kpi-band{grid-template-columns:repeat(3,1fr)}
  .grid-4{grid-template-columns:repeat(2,1fr)}
  .grid-3{grid-template-columns:1fr 1fr}
}
@media (max-width:760px){
  .kpi-band{grid-template-columns:repeat(2,1fr)}
  .grid-2,.grid-3,.grid-4{grid-template-columns:1fr}
  section{padding:64px 16px 20px}
  .echart{height:340px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .reveal{transition:none;opacity:1;transform:none}
}
</style>
</head>
<body>
<div id="progressBar"></div>
<div id="cdnBanner">提示：当前网络无法加载 ECharts 图表库（CDN 不可达），页面中的图表暂不可见；全部文字与数据内容不受影响，可正常阅读。</div>

<nav id="topnav">
  <div class="nav-inner">
    <span class="brand">宇树科技 <em>688836.SH</em></span>
    <a class="nav-link" href="#overview">概览</a>
    <a class="nav-link" href="#history">公司历程</a>
    <a class="nav-link" href="#business">业务结构</a>
    <a class="nav-link" href="#finance">财务表现</a>
    <a class="nav-link" href="#rd">研发投入</a>
    <a class="nav-link" href="#market">市场地位</a>
    <a class="nav-link" href="#ipo">IPO与市场</a>
    <a class="nav-link" href="#growth">增长与风险</a>
    <a class="nav-link" href="#sources">口径与来源</a>
  </div>
</nav>

<header class="hero" id="overview">
  <canvas id="particles"></canvas>
  <div class="hero-content">
    <span class="hero-badge">科创板 · 人形机器人第一股</span>
    <h1>宇树科技 <span class="ticker">688836.SH</span></h1>
    <p class="hero-sub">科创板人形机器人第一股 · 交互式数据报告</p>
    <p class="hero-meta">单位：人民币<b>万元</b>（每股价格为元/股，市值另标注为亿元） · 口径：招股说明书注册稿为主、申报稿补充 · 资料截止 <b>2026-08-30</b></p>
  </div>
  <div class="kpi-band" id="kpiBand"></div>
</header>

<main>

<!-- 公司历程 -->
<section id="history">
  <div class="sec-head reveal">
    <div class="sec-kicker">MILESTONES</div>
    <h2>公司历程：从创立到科创板上市</h2>
    <p class="sec-desc">自杭州起步的四足机器人团队，到科创板预先审阅机制下快速过会的人形机器人第一股，关键节点如下。</p>
  </div>
  <div class="grid grid-2">
    <div class="glass card reveal">
      <div class="timeline" id="timeline"></div>
    </div>
    <div class="glass card reveal">
      <h3>关键事实</h3>
      <ul class="fact-list" id="historyFacts"></ul>
    </div>
  </div>
</section>

<!-- 业务结构 -->
<section id="business">
  <div class="sec-head reveal">
    <div class="sec-kicker">BUSINESS MIX</div>
    <h2>业务结构：人形机器人接棒第一增长曲线</h2>
    <p class="sec-desc">收入结构三年内完成从四足机器人主导到人形机器人主导的切换；下游仍以科研教育为主，商业消费与行业应用渐次打开。</p>
  </div>
  <div class="tabs reveal">
    <button class="tab-btn active" data-tab="tabProduct">分产品收入（堆叠）</button>
    <button class="tab-btn" data-tab="tabDownstream">下游应用结构（9M2025）</button>
    <button class="tab-btn" data-tab="tabHumanoid">人形销量 × 均价</button>
  </div>
  <div class="tab-panel active" id="tabProduct">
    <div class="glass chart-card reveal">
      <div class="chart-title">分产品收入（2023–2025，注册稿口径）</div>
      <div id="chartProduct" class="echart"></div>
      <div class="chart-caption">单位：万元。「组件及其他」为倒算约数；2025 年人形机器人收入占比升至 51.78%，成为第一大产品。</div>
    </div>
  </div>
  <div class="tab-panel" id="tabDownstream">
    <div class="glass chart-card reveal">
      <div class="chart-title">下游应用结构（2025 年 1-9 月，申报稿口径）</div>
      <div id="chartDownstream" class="echart"></div>
      <div class="chart-caption">人形机器人 73.60% 收入来自科研教育，行业应用仅 9.01%（其中真实生产场景约 1,570 万元、占主营 2.64%，单一来源待核验）；四足机器人商业消费占 42.30%、已超科研教育。</div>
    </div>
  </div>
  <div class="tab-panel" id="tabHumanoid">
    <div class="glass chart-card reveal">
      <div class="chart-title">人形机器人销量与平均单价（申报稿口径）</div>
      <div id="chartHumanoid" class="echart"></div>
      <div class="chart-caption">以价换量路径清晰：平均单价由 59.34 万元降至 16.76 万元，销量由 5 台增至 3,551 台（2025 年 1-9 月）。</div>
    </div>
  </div>
  <div class="grid grid-2" style="margin-top:18px">
    <div class="glass card reveal"><h3>销量与份额</h3><ul class="fact-list" id="bizFacts1"></ul></div>
    <div class="glass card reveal"><h3>地区结构</h3><ul class="fact-list" id="bizFacts2"></ul></div>
  </div>
</section>

<!-- 财务表现 -->
<section id="finance">
  <div class="sec-head reveal">
    <div class="sec-kicker">FINANCIALS</div>
    <h2>财务表现：高增长、扭亏与盈利质量</h2>
    <p class="sec-desc">2023–2025 年营收复合增速约 226.8%，2024 年整体扭亏，毛利率持续上行；2025 年归母与扣非的差异主要来自一次性股份支付。</p>
  </div>
  <div class="grid grid-2">
    <div class="glass chart-card reveal">
      <div class="chart-title">营业收入 × 主营毛利率</div>
      <div id="chartRevenue" class="echart"></div>
      <div class="chart-caption">2022、2024 年营收为约数（2024 年由 2025 年 +332.64% 倒算，待核验）；毛利率线自 2023 年起（注册稿口径）。</div>
    </div>
    <div class="glass chart-card reveal">
      <div class="chart-title">归母净利润 vs 扣非归母净利润</div>
      <div id="chartProfit" class="echart"></div>
      <div class="chart-caption">2025 年归母低于扣非约 31,254 万元，主因一次性股份支付 34,906.55 万元计入管理费用（非经常性损益）。</div>
    </div>
  </div>
  <div class="grid grid-2" style="margin-top:18px">
    <div class="glass chart-card reveal">
      <div class="chart-title">经营活动现金流净额</div>
      <div id="chartOCF" class="echart"></div>
      <div class="chart-caption">黄色柱为待核验口径（2022/2023 申报稿数值，精确值待核验）；2025 年经营现金流约 67,000 万元，高于扣非净利润。</div>
    </div>
    <div class="glass card reveal">
      <h3>口径注释</h3>
      <ul class="fact-list" id="finNotes"></ul>
    </div>
  </div>
  <div class="glass card reveal" style="margin-top:18px">
    <h3>主要财务数据一览（万元）</h3>
    <div class="table-wrap"><table class="data" id="finTable"></table></div>
    <p class="muted" style="margin-top:10px">2022 年为申报稿口径（不在注册稿报告期内）；2026H1 取自上市公告书，正式半年报截至 2026-08-30 尚未披露。</p>
  </div>
</section>

<!-- 研发投入 -->
<section id="rd">
  <div class="sec-head reveal">
    <div class="sec-kicker">R&amp;D</div>
    <h2>研发投入：全栈自研的降本路径</h2>
    <p class="sec-desc">研发费用率随收入放量快速摊薄，显著低于可比公司均值；募投资金约 85% 投向研发，押注具身大模型。</p>
  </div>
  <div class="grid grid-2">
    <div class="glass chart-card reveal">
      <div class="chart-title">研发费用 × 费用率</div>
      <div id="chartRD" class="echart"></div>
      <div class="chart-caption">参考线为可比公司研发费用率均值 27.92%（2025 年 1-9 月）；2025 年研发费约 14,500 万元（同比 +107%）。</div>
    </div>
    <div class="glass chart-card reveal">
      <div class="chart-title">募投项目构成（万元）</div>
      <div id="chartFund" class="echart"></div>
      <div class="chart-caption" id="fundCaption"></div>
    </div>
  </div>
  <div class="glass card reveal" style="margin-top:18px">
    <h3>研发事实</h3>
    <ul class="fact-list" id="rdFacts"></ul>
  </div>
</section>

<!-- 市场地位 -->
<section id="market">
  <div class="sec-head reveal">
    <div class="sec-kicker">MARKET POSITION</div>
    <h2>市场地位：双料全球第一</h2>
    <p class="sec-desc">四足机器人份额 60–70%（管理层表态），人形机器人 2025 年出货全球第一（机构数据）；管理层表态与机构口径均已标注性质。</p>
  </div>
  <div class="grid grid-4" id="marketCards"></div>
  <div class="grid grid-2" style="margin-top:18px">
    <div class="glass card reveal">
      <h3>竞争力要点</h3>
      <ul class="fact-list" id="marketEdge"></ul>
    </div>
    <div class="glass card reveal">
      <h3>第三方口径差异（并列备注）</h3>
      <ul class="fact-list" id="marketDiff"></ul>
    </div>
  </div>
</section>

<!-- IPO与市场 -->
<section id="ipo">
  <div class="sec-head reveal">
    <div class="sec-kicker">IPO &amp; SECONDARY MARKET</div>
    <h2>IPO 与二级市场表现</h2>
    <p class="sec-desc">发行市盈率 219.23 倍、首日上涨 460.34% 后逐步回落；本节市值与行情数据均为二级市场数据，并已逐点标注口径。</p>
  </div>
  <div class="glass chart-card reveal">
    <div class="chart-title">市值轨迹（亿元，二级市场数据）</div>
    <div id="chartCap" class="echart echart-tall"></div>
    <div class="chart-caption">「首日收盘」= 845 元 × 总股本 40,446.434 万股；08-20 / 08-26 为收盘价（687 元 / 591.53 元）× 总股本推算；08-24、08-31 为披露约值；08-31 交易日略晚于 2026-08-30 资料截止日，标注为补充。</div>
  </div>
  <div class="grid grid-2" style="margin-top:18px">
    <div class="glass card reveal">
      <h3>发行与上市要素</h3>
      <ul class="fact-list" id="ipoFacts"></ul>
    </div>
    <div class="glass card reveal">
      <h3>机构观点 <span class="tag tag-org">机构观点 · 非公司披露事实</span></h3>
      <ul class="fact-list" id="ipoViews"></ul>
    </div>
  </div>
</section>

<!-- 增长与风险 -->
<section id="growth">
  <div class="sec-head reveal">
    <div class="sec-kicker">GROWTH &amp; RISKS</div>
    <h2>增长变量与风险清单</h2>
    <p class="sec-desc">预测、管理层表态与机构观点均以标签标注性质，不作为事实或业绩指引。</p>
  </div>
  <div class="grid grid-2">
    <div>
      <h3 style="color:#fff;margin-bottom:14px;font-size:18px">增长变量</h3>
      <div class="grid" id="growthCards"></div>
    </div>
    <div>
      <h3 style="color:#fff;margin-bottom:14px;font-size:18px">风险清单</h3>
      <div class="grid" id="riskCards"></div>
    </div>
  </div>
</section>

<!-- 口径与来源 -->
<section id="sources">
  <div class="sec-head reveal">
    <div class="sec-kicker">METHODOLOGY &amp; SOURCES</div>
    <h2>口径说明、待核验事项与资料来源</h2>
  </div>
  <div class="glass card reveal">
    <h3>口径说明</h3>
    <ul class="fact-list" id="methodNotes"></ul>
  </div>
  <div class="glass card reveal" style="margin-top:18px">
    <h3>待核验事项（点击展开，共 <span class="accent" id="pendingCount"></span> 条）</h3>
    <div id="pendingList"></div>
  </div>
  <div class="glass card reveal" style="margin-top:18px">
    <h3>资料来源</h3>
    <ol class="src-list" id="srcList"></ol>
  </div>
</section>

</main>

<footer>
  <div class="footer-inner">
    <p><b>免责声明</b>：本页面基于公开信息整理，仅供参考，不构成任何投资建议。除另标注外，金额单位均为人民币万元；标注「机构数据 / 管理层表态 / 机构观点 / 预测 / 二级市场数据 / 待核验」的内容均非公司经审计披露事实，请注意甄别。页面头图为 AI 生成图像，仅作装饰用途。</p>
    <p style="margin-top:8px">数据与 Excel / Word / PPT 底稿同源（资料截止 <b>2026-08-30</b>） · 宇树科技 688836.SH 交互式数据报告</p>
  </div>
</footer>

<button id="backTop" aria-label="回到顶部"><svg viewBox="0 0 24 24"><polyline points="6 14 12 8 18 14"/></svg></button>

<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>window.echarts||document.write('<script src="https://unpkg.com/echarts@5/dist/echarts.min.js">\x3C/script>');</script>
<script>
/* ===================== 数据（唯一事实源：unitree_excel_spec.md，资料截止 2026-08-30） ===================== */
const DATA = {
  "meta": {"cutoff": "2026-08-30", "unit": "万元", "ticker": "688836.SH", "name": "宇树科技"},
  "kpi": [
    {"label": "2025年营业收入（注册稿）", "value": 169926.93, "decimals": 2, "prefix": "", "unit": "万元", "note": "同比 +332.64%", "tag": "注册稿", "tagType": "official"},
    {"label": "2025年扣非归母净利润", "value": 59075.28, "decimals": 2, "prefix": "", "unit": "万元", "note": "归母净利润 27821.05 万元", "tag": "注册稿", "tagType": "official"},
    {"label": "2025年主营业务毛利率", "value": 60.13, "decimals": 2, "prefix": "", "unit": "%", "note": "2023 年为 44.22%", "tag": "注册稿", "tagType": "official"},
    {"label": "2025年人形机器人出货", "value": 5500, "decimals": 0, "prefix": "超", "unit": "台", "note": "全球第一 · 份额 32.4%", "tag": "赛迪顾问 · 机构数据", "tagType": "org"},
    {"label": "四足机器人全球份额", "value": 70, "decimals": 0, "prefix": "60–", "unit": "%", "note": "王兴兴 2025-07-15 国新办表态", "tag": "管理层表态", "tagType": "mgmt"},
    {"label": "发行市值", "value": 609.93, "decimals": 2, "prefix": "", "unit": "亿元", "note": "发行价 150.80 元/股", "tag": "发行公告", "tagType": "official"}
  ],
  "timeline": [
    {"date": "2016-08-26", "title": "公司成立", "desc": "王兴兴创立宇树科技，自四足机器人起步。"},
    {"date": "2025-07-08", "title": "辅导备案", "desc": "启动科创板上市辅导。"},
    {"date": "2026-03-20", "title": "获受理", "desc": "科创板预先审阅第 2 单。"},
    {"date": "2026-06-01", "title": "过会", "desc": "自受理起 73 天。"},
    {"date": "2026-07-02", "title": "注册生效", "desc": "证监许可〔2026〕1612 号，自受理起 104 天。"},
    {"date": "2026-08-10", "title": "网上申购", "desc": "网上中签率 0.01809759%。"},
    {"date": "2026-08-19", "title": "上市", "desc": "首日收盘 845 元，上涨 460.34%。"}
  ],
  "historyFacts": [
    {"k": "实际控制人", "v": "王兴兴，发行后合计控制表决权 65.31%（直接持股 21.4395%，-W 表决权差异安排）"},
    {"k": "员工与研发", "v": "员工 480 人，其中研发 175 人（占 36.46%，2025-09-30）"},
    {"k": "专利", "v": "专利权 262 项（含境内发明专利 20 项，截至 2026-01-31，路演口径）"},
    {"k": "上市前融资", "v": "十年累计约 18.92 亿元；C 轮投后 127 亿元（2025-06，腾讯、中移动、阿里、蚂蚁、吉利等）"},
    {"k": "主要机构股东（发行前）", "v": "美团系 9.6488%、红杉中国 7.1149%、经纬 5.4528%、顺为 4.4245%"}
  ],
  "business": {
    "productYears": ["2023", "2024", "2025"],
    "productSeries": [
      {"name": "四足机器人", "data": [11900, 23100, 69800]},
      {"name": "人形机器人", "data": [296.71, 10700, 86800]},
      {"name": "组件及其他（倒算）", "data": [3500, 5000, 11100]}
    ],
    "downstreamHumanoid": [
      {"name": "科研教育", "value": 73.60},
      {"name": "商业消费", "value": 17.39},
      {"name": "行业应用", "value": 9.01}
    ],
    "downstreamQuadruped": [
      {"name": "科研教育", "value": 31.58},
      {"name": "商业消费", "value": 42.30},
      {"name": "行业应用", "value": 26.12}
    ],
    "humanoidPeriods": ["2023", "2024", "2025年1-9月"],
    "humanoidVolume": [5, 410, 3551],
    "humanoidPrice": [59.34, 26.07, 16.76],
    "factsVolume": [
      {"k": "四足销量（台）", "v": "2403 / 3121 / 7136 / 17946（2022 / 2023 / 2024 / 2025年1-9月，申报稿）"},
      {"k": "四足累计", "v": "报告期累计超 3 万台，截至 2025 年末超 3.3 万台（官方口径）"},
      {"k": "人形出货", "v": "2025 年出货超 5500 台、全球第一、份额 32.4%（赛迪顾问 · 机构数据）"},
      {"k": "人形收入", "v": "2023 年 296.71 万元 → 2025 年 86800 万元"}
    ],
    "factsRegion": [
      {"k": "境外收入占比", "v": "57.21% → 55.63% → 55.70% → 39.20%（2022 / 2023 / 2024 / 2025年1-9月，申报稿）"},
      {"k": "9M2025 境内", "v": "境内收入 70200 万元（+445.69%），占比 60.80%，国内放量摊薄境外占比"},
      {"k": "9M2025 境外", "v": "境外收入 45300 万元（+179.88%）"},
      {"k": "口径提示", "v": "组件及其他收入为倒算约数；2025 全年分地区数据待核验"}
    ]
  },
  "finance": {
    "years": ["2022", "2023", "2024", "2025"],
    "revenue": [12300, 15913.44, 39276.6, 169926.93],
    "grossMargin": [null, 44.22, 56.74, 60.13],
    "netProfit": [-2210.05, -1114.51, 9547.47, 27821.05],
    "netProfitDeducted": [-807, -1801.91, 7847.65, 59075.28],
    "ocf": [-3019.73, 494.25, 19200, 67000],
    "ocfFlags": ["待核验", "待核验", "约", "约"],
    "notes": [
      {"k": "股份支付", "v": "2025 年一次性股份支付 34906.55 万元计入管理费用，致归母（27821.05）低于扣非（59075.28）约 31254 万元（非经常性损益）"},
      {"k": "2026H1（上市公告书）", "v": "营收约 115200 万元（+48.54%）、归母约 27400 万元、扣非约 24400 万元（-19.34%）"},
      {"k": "2026Q1（经审阅）", "v": "营收 42284.05 万元（+68.49%）、扣非 4025.36 万元（-52.55%）"},
      {"k": "复合增速", "v": "2023–2025 年营收 CAGR 约 226.8%；2025 年扣非净利率约 34.8%"},
      {"k": "盈利质量", "v": "2025 年经营现金流约 67000 万元高于扣非净利润，含金量高；2026H1 扣非 -19.34%，费用扩张快于收入的利润承压信号"}
    ],
    "tableCols": ["指标", "2022（申报稿）", "2023", "2024", "2025（注册稿）", "2026H1（上市公告书）"],
    "tableRows": [
      {"label": "营业收入", "cells": [{"v": 12300, "d": 0, "note": "约"}, {"v": 15913.44, "d": 2}, {"v": 39276.6, "d": 1, "note": "约 · 倒算"}, {"v": 169926.93, "d": 2}, {"v": 115200, "d": 0, "note": "约，+48.54%"}]},
      {"label": "归母净利润", "cells": [{"v": -2210.05, "d": 2}, {"v": -1114.51, "d": 2}, {"v": 9547.47, "d": 2}, {"v": 27821.05, "d": 2}, {"v": 27400, "d": 0, "note": "约"}]},
      {"label": "扣非归母净利润", "cells": [{"v": -807, "d": 0, "note": "约"}, {"v": -1801.91, "d": 2}, {"v": 7847.65, "d": 2}, {"v": 59075.28, "d": 2}, {"v": 24400, "d": 0, "note": "约，-19.34%"}]},
      {"label": "毛利率", "cells": [{"v": 44.18, "d": 2, "suf": "%", "note": "申报稿"}, {"v": 44.22, "d": 2, "suf": "%"}, {"v": 56.74, "d": 2, "suf": "%"}, {"v": 60.13, "d": 2, "suf": "%"}, {"v": 56.01, "d": 2, "suf": "%", "note": "综合口径 · 单一来源"}]},
      {"label": "研发费用", "cells": [{"v": 2998.48, "d": 2}, {"v": 4995.18, "d": 2}, {"v": 7001.70, "d": 2}, {"v": 14500, "d": 0, "note": "约，+107%"}, {"v": 13600, "d": 0, "note": "约"}]},
      {"label": "经营现金流净额", "cells": [{"v": -3019.73, "d": 2, "note": "待核验"}, {"v": 494.25, "d": 2, "note": "待核验"}, {"v": 19200, "d": 0, "note": "约"}, {"v": 67000, "d": 0, "note": "约"}, {"text": "未披露"}]}
    ]
  },
  "rd": {
    "years": ["2022", "2023", "2024", "2025"],
    "expense": [2998.48, 4995.18, 7001.70, 14500],
    "ratio": [24.39, 31.39, 17.84, 8.53],
    "peerAvg": 27.92,
    "fund": [
      {"name": "智能机器人模型研发", "value": 202245.93},
      {"name": "机器人本体研发", "value": 110973.80},
      {"name": "新型产品开发", "value": 44540.00},
      {"name": "制造基地", "value": 62411.39}
    ],
    "fundTotal": 420171.12,
    "fundRdShare": 85,
    "facts": [
      {"k": "研发人员", "v": "175 人，占员工总数 36.46%（2025-09-30）"},
      {"k": "专利", "v": "专利权 262 项（截至 2026-01-31，路演口径）"},
      {"k": "技术路线", "v": "WMA / VLA 具身大模型路线 + 硬件全栈自研"},
      {"k": "大模型进展", "v": "自研 UnifoLM-X1-0 已开展工厂试点（2026 年，路演披露）"},
      {"k": "2026H1 研发费", "v": "约 13600 万元，同比增加 8203.74 万元（上市公告书）"},
      {"k": "费用率对比", "v": "2025 年研发费用率 8.53%，显著低于可比公司均值 27.92%（9M2025）——全栈自研降本路径"}
    ]
  },
  "market": {
    "cards": [
      {"num": "60–70", "unit": "%", "label": "四足机器人全球销量份额", "note": "王兴兴 2025-07-15 国新办见面会表态；GGII 2023 年销量份额 69.75%", "tag": "管理层表态 / 机构数据", "tagType": "mgmt"},
      {"num": "32.4", "unit": "%", "label": "人形机器人全球份额第一", "note": "2025 年出货超 5500 台、全球第一（赛迪顾问，被注册批复报道引用）", "tag": "机构数据", "tagType": "org"},
      {"num": "约18000", "unit": "台", "label": "纯双足人形累计下线", "note": "截至 2026-07（官方）；G1 单款截至 2026-05 下线约 11000 台", "tag": "官方口径", "tagType": "official"},
      {"num": "59.34→16.76", "unit": "万元", "label": "人形平均单价两年下探", "note": "2023 → 2025年1-9月，以价换量", "tag": "申报稿", "tagType": "official"}
    ],
    "edge": [
      {"k": "全栈自研", "v": "电机、减速器、控制器、算法全链路自研，支撑低成本快速迭代"},
      {"k": "盈利为正", "v": "2024 年扭亏（归母 9547.47 万元），2025 年扣非净利率约 34.8%，区别于多数未盈利同业"},
      {"k": "现金流为正", "v": "2025 年经营现金流约 67000 万元（+248.24%），高于扣非净利润"},
      {"k": "双产品矩阵", "v": "四足全球份额 60–70%（管理层表态）+ 人形全球出货第一 32.4%（机构数据）"}
    ],
    "diff": [
      {"k": "Omdia", "v": "2025 年人形出货口径 4200 台（机构数据，与官方出货超 5500 台口径存在差异）"},
      {"k": "Counterpoint", "v": "2025 年人形份额口径 26.4%（机构数据，与赛迪 32.4% 口径存在差异）"},
      {"k": "处理方式", "v": "第三方口径差异并列备注，不纳入公司事实口径；以注册稿及官方披露为准"}
    ]
  },
  "ipo": {
    "capLabels": ["发行定价", "首日收盘", "08-20", "08-24", "08-26", "08-31"],
    "capValues": [609.93, 3417.72, 2779, 2439, 2393, 2285],
    "facts": [
      {"k": "发行价", "v": "150.80 元/股；新发 4044.6434 万股（占发行后总股本 10%），发行后总股本 40446.434 万股"},
      {"k": "募资", "v": "募资总额 609932.22 万元（净额 591714.92 万元，发行费用 18217.31 万元）；计划募资 420171.12 万元，超募约 171500 万元"},
      {"k": "发行估值", "v": "发行市盈率 219.23 倍（行业均值 38.56 倍）；静态市销率 35.89 倍"},
      {"k": "上市首日", "v": "开盘 1100 元（+629.44%）、最低 800.08 元、收盘 845 元（+460.34%），成交约 231.6 亿元（二级市场数据）"},
      {"k": "流通盘", "v": "上市初流通股 3008.772 万股，仅占总股本 7.44%；网上中签率 0.01809759%"},
      {"k": "8月底估值", "v": "2026-08-31 市值约 2285 亿元，对应 2025 年归母净利润 PE 约 821 倍（二级市场数据）"}
    ],
    "views": [
      {"k": "中信证券", "v": "合理市值区间 506–559 亿元（机构观点，非事实）"},
      {"k": "野村", "v": "目标价 370 元（机构观点，非事实）"},
      {"k": "建银国际", "v": "目标价 269 元（机构观点，非事实）"},
      {"k": "提示", "v": "机构目标市值显著低于现价，分歧巨大；本页面不构成投资建议"}
    ]
  },
  "growth": [
    {"title": "产能扩张", "body": "募投制造基地规划年产 7.5 万台人形机器人 + 11.5 万台四足机器人（制造基地投入 62411.39 万元）。", "tag": "募投规划", "tagType": "official"},
    {"title": "场景渗透", "body": "人形下游科研教育占 73.60%、行业应用仅 9.01%（真实生产场景约 1570 万元、占主营 2.64%，单一来源待核验）；科教 → 工业 / 消费的渗透是核心看点。", "tag": "申报稿口径", "tagType": "official"},
    {"title": "海外市场", "body": "出口占比约 40–50%（管理层表态）；2026-07-28 美国 FCC 禁令（禁新型号进口）构成海外扩张不确定性。", "tag": "管理层表态", "tagType": "mgmt"},
    {"title": "具身大模型", "body": "WMA / VLA 路线 + UnifoLM-X1-0 工厂试点；王兴兴表态「快则 2–3 年、慢则 5–10 年」；「2026 年出货至少翻一番」（管理层表态，非业绩指引）。", "tag": "管理层表态 / 非业绩指引", "tagType": "mgmt"}
  ],
  "risks": [
    {"title": "估值消化", "body": "发行 PE 219.23 倍（行业 38.56 倍）；8 月底市值约 2285 亿元对应 2025 年归母 PE 约 821 倍（二级市场数据），高估值依赖高增长持续兑现。"},
    {"title": "增收不增利", "body": "2026H1 扣非约 24400 万元（-19.34%）、2026Q1 扣非 -52.55%；研发（+152%）、销售（约 +250%，单一来源）费用高速扩张。"},
    {"title": "场景集中", "body": "人形 73.60% 收入来自科研教育，真实工业场景占比极低，商业化仍处早期。"},
    {"title": "地缘政治", "body": "FCC 禁令（2026-07-28）+ 涉军清单 + 美国市场收入占比 13.3%（单一来源，待核验）。"},
    {"title": "竞争加剧", "body": "2026H1 第三方口径智元出货反超（机构口径差异，待核验）；行业价格竞争或以价换量侵蚀毛利。"},
    {"title": "流动性与数据缺口", "body": "流通盘仅 7.44%，2027 年起限售解禁；正式半年报截至 2026-08-30 未披露，2026H1 明细数据存在缺口。"}
  ],
  "methodNotes": [
    {"k": "单位", "v": "除另标注外，财务金额一律为人民币万元；每股价格为元/股；市值标注处为亿元"},
    {"k": "报告期口径", "v": "以招股说明书注册稿 / 上市公告书口径（2023–2025 年度经审计）为主分析口径；申报稿数据（2022 年度、2025 年 1-9 月）作补充并注明"},
    {"k": "2026H1 口径", "v": "取自上市公告书；正式半年报截至 2026-08-30 未披露（上交所公告列表核验）"},
    {"k": "权益口径", "v": "公司无少数股东权益，净利润 = 归母净利润"},
    {"k": "性质标注", "v": "凡标注「机构数据 / 机构观点 / 管理层表态 / 预测 / 二级市场数据 / 待核验 / 倒算约数」者，均非公司经审计披露事实"}
  ],
  "pending": [
    {"title": "2024 年营收注册稿精确值", "body": "现采用 39276.6（由 2025 年 +332.64% 倒算）；申报稿审计值为 39237.06，两口径差异待以注册稿原文核验。"},
    {"title": "2025 年末资产负债明细", "body": "总资产 321500 / 总负债 60200 / 所有者权益 261300（长江商报单一来源），应收、存货、合同负债等明细待核验。"},
    {"title": "2025 全年分地区收入", "body": "一说境外 73200（占 43.65%），但与「同比 +109.91%」自相矛盾，未纳入计算，列待核验。"},
    {"title": "美国市场收入占比 13.3%", "body": "单一来源（称出自招股意向书风险章节），待核验。"},
    {"title": "2025 年费用明细", "body": "研发费 +107%、销售费用增速约 +250% 等口径为约数或单一来源，费用明细待定期报告核验。"},
    {"title": "人形销量口径", "body": "5215 台（芝能科技，待核验）与官方「出货超 5500 台」并存；报告期口径 2025 年 1-9 月为 3551 台。"},
    {"title": "2022 / 2023 经营现金流精确值", "body": "现采用 -3019.73 / 494.25（待核验），建议以公告原文复核。"},
    {"title": "2025 年末员工 516 人", "body": "猎聘单一来源（研发 184 / 销售 154 / 生产 123）；本报告统一采用 2025-09-30 口径 480 人。"},
    {"title": "2026H1 毛利率 56.01%", "body": "综合毛利率口径、单一来源，与主营毛利率口径差异待核验。"},
    {"title": "超募资金投向", "body": "计划募资 420171.12 万元，实际募资总额 609932.22 万元，超募约 171500 万元，投向待公司公告。"},
    {"title": "人形毛利率约 62.9%", "body": "期间口径待核验，未纳入正式计算。"},
    {"title": "2025 年四足销量约 25500 台", "body": "单一来源；另官方口径截至 2025 年末四足累计超 3.3 万台。"}
  ],
  "sources": [
    {"type": "官方披露", "name": "上交所 688836 公告列表", "date": "2026-08-30 核验", "desc": "含招股说明书正式稿（2026-08-14）、上市公告书（2026-08-18）；确认截至 2026-08-30 未披露 2026 年半年报", "url": "https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId=688836"},
    {"type": "权威媒体", "name": "新华社", "date": "2026-06-01", "desc": "宇树科技科创板 IPO 过会报道", "url": "未获取"},
    {"type": "权威媒体", "name": "澎湃新闻", "date": "2026-03-20", "desc": "IPO 受理（预先审阅第 2 单）报道", "url": "未获取"},
    {"type": "权威媒体", "name": "长江商报", "date": "2026-03-23", "desc": "资产负债与经营数据报道（部分为单一来源）", "url": "未获取"},
    {"type": "权威媒体", "name": "证券时报 · 券商中国", "date": "2026-05-25", "desc": "审核进展报道", "url": "未获取"},
    {"type": "权威媒体", "name": "证券时报 · 券商中国", "date": "2026-08-17", "desc": "上市前瞻报道", "url": "未获取"},
    {"type": "权威媒体", "name": "中新经纬", "date": "2026-07-02", "desc": "注册生效报道", "url": "未获取"},
    {"type": "权威媒体", "name": "金融时报", "date": "2026-03-21", "desc": "IPO 受理相关报道", "url": "未获取"},
    {"type": "权威媒体", "name": "金融时报", "date": "2026-05-26", "desc": "审核进展报道", "url": "未获取"},
    {"type": "权威媒体", "name": "第一财经", "date": "2026-08-19", "desc": "上市首日行情报道", "url": "未获取"},
    {"type": "权威媒体", "name": "21 世纪经济报道", "date": "2026-08-29", "desc": "上市后表现与机构观点报道", "url": "未获取"},
    {"type": "权威媒体", "name": "潮新闻", "date": "2026-03-20", "desc": "受理报道", "url": "未获取"},
    {"type": "权威媒体", "name": "财联社", "date": "2026-08-19", "desc": "上市首日报道", "url": "未获取"},
    {"type": "权威媒体", "name": "中国上市公司网", "date": "2026-08-18", "desc": "上市公告书要点", "url": "未获取"},
    {"type": "官方披露", "name": "宇树科技官方 X 声明", "date": "2025-09-02", "desc": "经营与产品口径声明", "url": "未获取"},
    {"type": "管理层表态", "name": "国新办中外记者见面会", "date": "2025-07-15", "desc": "王兴兴：四足机器人全球份额 60–70% 等表态", "url": "未获取"},
    {"type": "机构数据", "name": "赛迪顾问", "date": "2025 年度", "desc": "人形机器人 2025 年出货超 5500 台、全球第一、份额 32.4%（被注册批复报道引用）", "url": "未获取"},
    {"type": "机构数据", "name": "GGII 高工机器人", "date": "2023 年度及预测", "desc": "四足机器人 2023 年销量份额 69.75%；2030 年行业预测（预测仅作标注）", "url": "未获取"}
  ]
};
</script>
<script>
/* ===================== 交互逻辑 ===================== */
(function(){
"use strict";
function $(s,c){return (c||document).querySelector(s);}
function $all(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s));}
function fmt(n,d){return Number(n).toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d});}
var TAG_CLS={official:"tag-official",org:"tag-org",mgmt:"tag-mgmt",mkt:"tag-mkt",check:"tag-check"};

/* ---------- 渲染：KPI ---------- */
(function(){
  var band=$("#kpiBand");
  DATA.kpi.forEach(function(k){
    var card=document.createElement("div");
    card.className="kpi-card reveal";
    card.innerHTML='<div class="kpi-label">'+k.label+'</div>'+
      '<div class="kpi-value"><span class="count" data-value="'+k.value+'" data-decimals="'+k.decimals+'" data-prefix="'+k.prefix+'">0</span><span class="kpi-unit">'+k.unit+'</span></div>'+
      '<div class="kpi-note">'+k.note+'</div>'+
      '<span class="tag '+(TAG_CLS[k.tagType]||"")+'">'+k.tag+'</span>';
    band.appendChild(card);
  });
})();

/* ---------- 渲染：时间线 / 通用事实列表 ---------- */
function renderFacts(id,items){
  var ul=$(id); if(!ul) return;
  items.forEach(function(it){
    var li=document.createElement("li");
    li.innerHTML='<span class="k">'+it.k+'：</span>'+it.v;
    ul.appendChild(li);
  });
}
(function(){
  var tl=$("#timeline");
  DATA.timeline.forEach(function(t){
    var d=document.createElement("div");
    d.className="tl-item";
    d.innerHTML='<div class="tl-date">'+t.date+'</div><div class="tl-title">'+t.title+'</div><div class="tl-desc">'+t.desc+'</div>';
    tl.appendChild(d);
  });
  renderFacts("#historyFacts",DATA.historyFacts);
  renderFacts("#bizFacts1",DATA.business.factsVolume);
  renderFacts("#bizFacts2",DATA.business.factsRegion);
  renderFacts("#finNotes",DATA.finance.notes);
  renderFacts("#rdFacts",DATA.rd.facts);
  renderFacts("#marketEdge",DATA.market.edge);
  renderFacts("#marketDiff",DATA.market.diff);
  renderFacts("#ipoFacts",DATA.ipo.facts);
  renderFacts("#ipoViews",DATA.ipo.views);
  renderFacts("#methodNotes",DATA.methodNotes);
})();

/* ---------- 渲染：财务表格 ---------- */
(function(){
  var t=$("#finTable");
  var html="<thead><tr>"+DATA.finance.tableCols.map(function(c){return "<th>"+c+"</th>";}).join("")+"</tr></thead><tbody>";
  DATA.finance.tableRows.forEach(function(r){
    html+="<tr><td>"+r.label+"</td>";
    r.cells.forEach(function(c){
      if(c.text){html+="<td>"+c.text+"</td>";return;}
      var v=fmt(c.v,c.d)+(c.suf||"");
      html+="<td>"+v+(c.note?'<span class="cell-note">'+c.note+"</span>":"")+"</td>";
    });
    html+="</tr>";
  });
  t.innerHTML=html+"</tbody>";
})();

/* ---------- 渲染：市场大数字卡 ---------- */
(function(){
  var wrap=$("#marketCards");
  DATA.market.cards.forEach(function(c){
    var d=document.createElement("div");
    d.className="glass big-card reveal";
    d.innerHTML='<div class="big-num">'+c.num+'<span class="u">'+c.unit+'</span></div>'+
      '<div class="big-label">'+c.label+'</div>'+
      '<div class="big-note">'+c.note+'</div>'+
      '<div style="margin-top:10px"><span class="tag '+(TAG_CLS[c.tagType]||"")+'">'+c.tag+'</span></div>';
    wrap.appendChild(d);
  });
})();

/* ---------- 渲染：增长 / 风险卡 ---------- */
(function(){
  var g=$("#growthCards"),r=$("#riskCards");
  DATA.growth.forEach(function(c){
    var d=document.createElement("div");
    d.className="glass card reveal";
    d.innerHTML="<h3>"+c.title+' <span class="tag '+(TAG_CLS[c.tagType]||"")+'">'+c.tag+"</span></h3><p>"+c.body+"</p>";
    g.appendChild(d);
  });
  DATA.risks.forEach(function(c){
    var d=document.createElement("div");
    d.className="glass card reveal";
    d.innerHTML="<h3>"+c.title+' <span class="tag tag-mkt">风险</span></h3><p>'+c.body+"</p>";
    r.appendChild(d);
  });
})();

/* ---------- 渲染：待核验手风琴 / 资料来源 ---------- */
(function(){
  $("#pendingCount").textContent=DATA.pending.length;
  var box=$("#pendingList");
  DATA.pending.forEach(function(p,i){
    var item=document.createElement("div");
    item.className="acc-item";
    item.innerHTML='<div class="acc-head"><span>'+(i+1)+". "+p.title+'</span><span class="ic">+</span></div>'+
      '<div class="acc-body"><div class="inner">'+p.body+"</div></div>";
    box.appendChild(item);
  });
  $all(".acc-head").forEach(function(h){
    h.addEventListener("click",function(){
      var item=h.parentElement,body=item.querySelector(".acc-body");
      item.classList.toggle("open");
      body.style.maxHeight=item.classList.contains("open")?body.scrollHeight+"px":"0";
    });
  });
  var ol=$("#srcList");
  DATA.sources.forEach(function(s){
    var li=document.createElement("li");
    var urlHtml=s.url.indexOf("http")===0?'<div class="src-url"><a href="'+s.url+'" target="_blank" rel="noopener">'+s.url+"</a></div>":'<div class="src-url muted">URL：'+s.url+"</div>";
    li.innerHTML='<span class="src-type tag tag-official">'+s.type+'</span><span class="src-name">'+s.name+"</span> · "+s.date+"<br>"+s.desc+urlHtml;
    ol.appendChild(li);
  });
  $("#fundCaption").textContent="募投合计 "+fmt(DATA.rd.fundTotal,2)+" 万元，其中约 "+DATA.rd.fundRdShare+"% 投向研发（模型研发占约 48%）。";
})();

/* ---------- 滚动进度条 / 回到顶部 / 导航高亮 ---------- */
var navLinks=$all("#topnav a.nav-link");
var sections=navLinks.map(function(a){return $(a.getAttribute("href"));});
function spy(){
  var y=window.scrollY+140,cur=0;
  sections.forEach(function(s,i){if(s&&s.offsetTop<=y)cur=i;});
  navLinks.forEach(function(a,i){a.classList.toggle("active",i===cur);});
}
function onScroll(){
  var h=document.documentElement;
  var p=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;
  $("#progressBar").style.width=p+"%";
  $("#backTop").classList.toggle("show",h.scrollTop>600);
  spy();
}
window.addEventListener("scroll",onScroll,{passive:true});
onScroll();
$("#backTop").addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"});});

/* ---------- 滚动渐入 ---------- */
var io=new IntersectionObserver(function(es){
  es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);}});
},{threshold:0.12});
$all(".reveal").forEach(function(el){io.observe(el);});

/* ---------- KPI 数字滚动 ---------- */
function countUp(el){
  var target=parseFloat(el.getAttribute("data-value"));
  var d=parseInt(el.getAttribute("data-decimals")||"0",10);
  var pre=el.getAttribute("data-prefix")||"";
  var dur=1600,t0=null;
  function step(ts){
    if(!t0)t0=ts;
    var p=Math.min((ts-t0)/dur,1),e=1-Math.pow(1-p,3);
    el.textContent=pre+fmt(target*e,d);
    if(p<1)requestAnimationFrame(step);else el.textContent=pre+fmt(target,d);
  }
  requestAnimationFrame(step);
}
var cio=new IntersectionObserver(function(es){
  es.forEach(function(e){if(e.isIntersecting){countUp(e.target);cio.unobserve(e.target);}});
},{threshold:0.4});
$all(".count").forEach(function(el){cio.observe(el);});

/* ---------- Tab 切换 ---------- */
$all(".tab-btn").forEach(function(b){
  b.addEventListener("click",function(){
    $all(".tab-btn").forEach(function(x){x.classList.remove("active");});
    $all(".tab-panel").forEach(function(x){x.classList.remove("active");});
    b.classList.add("active");
    var panel=$("#"+b.getAttribute("data-tab"));
    panel.classList.add("active");
    var ch=panel.querySelector(".echart");
    if(ch){initChartById(ch.id);if(charts[ch.id])charts[ch.id].resize();}
  });
});

/* ---------- ECharts ---------- */
function showCdnBanner(){var b=$("#cdnBanner");if(b)b.classList.add("show");}
window.addEventListener("load",function(){setTimeout(function(){if(!window.echarts)showCdnBanner();},6000);});
function whenEcharts(ok){
  var waited=0;
  (function poll(){
    if(window.echarts){ok();return;}
    waited+=120;
    if(waited>7000){showCdnBanner();return;}
    setTimeout(poll,120);
  })();
}
var PALETTE=["#19C2FF","#7B61FF","#2DE2C5","#FFB020","#FF6B81"];
var CTEXT="#DCE7F5",CSUB="#8FA8C9";
function ax(extra){
  var base={axisLine:{lineStyle:{color:"rgba(143,168,201,.35)"}},axisTick:{show:false},
    axisLabel:{color:CSUB},splitLine:{lineStyle:{color:"rgba(143,168,201,.12)"}}};
  for(var k in extra)base[k]=extra[k];
  return base;
}
function tt(unit){
  return {trigger:"axis",backgroundColor:"rgba(8,18,40,.94)",borderColor:"rgba(25,194,255,.4)",
    textStyle:{color:CTEXT},axisPointer:{type:"shadow"},
    valueFormatter:function(v){return v==null?"—":fmt(v,2)+(unit||"");}};
}
var charts={},chartStarted={};
var CHART_BUILDERS={
  chartProduct:function(){
    var D=DATA.business;
    return {color:PALETTE,tooltip:tt(" 万元"),
      legend:{top:4,textStyle:{color:CTEXT}},
      grid:{left:76,right:24,top:52,bottom:36},
      xAxis:ax({type:"category",data:D.productYears}),
      yAxis:ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
      series:D.productSeries.map(function(s){
        return {name:s.name,type:"bar",stack:"total",barWidth:"46%",data:s.data,
          label:{show:true,color:"#EAF4FF",fontSize:11,formatter:function(p){return p.value>=2000?fmt(p.value,0):"";}},
          emphasis:{focus:"series"}};
      })};
  },
  chartDownstream:function(){
    var D=DATA.business;
    function pie(name,data,cx){
      return {name:name,type:"pie",radius:["40%","64%"],center:[cx,"58%"],
        itemStyle:{borderColor:"#0A1F44",borderWidth:2},
        label:{color:CTEXT,fontSize:12,formatter:"{b}\n{d}%"},
        labelLine:{lineStyle:{color:"rgba(143,168,201,.5)"}},
        data:data};
    }
    return {color:PALETTE,
      tooltip:{trigger:"item",backgroundColor:"rgba(8,18,40,.94)",borderColor:"rgba(25,194,255,.4)",textStyle:{color:CTEXT},formatter:"{a}<br>{b}：{c}%"},
      title:[
        {text:"人形机器人下游",left:"26%",top:8,textAlign:"center",textStyle:{color:"#fff",fontSize:14}},
        {text:"四足机器人下游",left:"74%",top:8,textAlign:"center",textStyle:{color:"#fff",fontSize:14}}
      ],
      series:[pie("人形机器人",D.downstreamHumanoid,"26%"),pie("四足机器人",D.downstreamQuadruped,"74%")]};
  },
  chartHumanoid:function(){
    var D=DATA.business;
    return {color:[PALETTE[0],PALETTE[3]],tooltip:tt(""),
      legend:{top:4,textStyle:{color:CTEXT}},
      grid:{left:70,right:76,top:52,bottom:36},
      xAxis:ax({type:"category",data:D.humanoidPeriods}),
      yAxis:[
        ax({type:"value",name:"销量（台）",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
        ax({type:"value",name:"均价（万元/台）",nameTextStyle:{color:CSUB},splitLine:{show:false},axisLabel:{color:CSUB}})
      ],
      series:[
        {name:"销量",type:"bar",barWidth:"42%",data:D.humanoidVolume,
          label:{show:true,color:"#EAF4FF",formatter:function(p){return fmt(p.value,0);}}},
        {name:"平均单价",type:"line",yAxisIndex:1,data:D.humanoidPrice,symbol:"circle",symbolSize:9,
          lineStyle:{width:3},label:{show:true,color:"#FFD98A",formatter:function(p){return fmt(p.value,2);}}}
      ]};
  },
  chartRevenue:function(){
    var F=DATA.finance;
    return {color:[PALETTE[0],PALETTE[4]],tooltip:tt(""),
      legend:{top:4,textStyle:{color:CTEXT}},
      grid:{left:76,right:64,top:52,bottom:36},
      xAxis:ax({type:"category",data:F.years}),
      yAxis:[
        ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
        ax({type:"value",name:"毛利率",nameTextStyle:{color:CSUB},splitLine:{show:false},axisLabel:{color:CSUB,formatter:"{value}%"}})
      ],
      series:[
        {name:"营业收入",type:"bar",barWidth:"44%",data:F.revenue,
          label:{show:true,color:"#EAF4FF",fontSize:11,formatter:function(p){return fmt(p.value,0);}}},
        {name:"主营毛利率（2023 起）",type:"line",yAxisIndex:1,data:F.grossMargin,symbol:"circle",symbolSize:9,
          lineStyle:{width:3},label:{show:true,color:"#FFB3C0",formatter:function(p){return p.value==null?"":fmt(p.value,2)+"%";}}}
      ]};
  },
  chartProfit:function(){
    var F=DATA.finance;
    return {color:[PALETTE[0],PALETTE[2]],tooltip:tt(" 万元"),
      legend:{top:4,textStyle:{color:CTEXT}},
      grid:{left:76,right:24,top:52,bottom:36},
      xAxis:ax({type:"category",data:F.years}),
      yAxis:ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
      series:[
        {name:"归母净利润",type:"bar",barWidth:"30%",data:F.netProfit,
          label:{show:true,color:"#EAF4FF",fontSize:10,formatter:function(p){return fmt(p.value,0);}}},
        {name:"扣非归母净利润",type:"bar",barWidth:"30%",data:F.netProfitDeducted,
          label:{show:true,color:"#EAF4FF",fontSize:10,formatter:function(p){return fmt(p.value,0);}}}
      ]};
  },
  chartOCF:function(){
    var F=DATA.finance;
    return {tooltip:tt(" 万元"),
      grid:{left:76,right:24,top:40,bottom:36},
      xAxis:ax({type:"category",data:F.years}),
      yAxis:ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
      series:[{name:"经营现金流净额",type:"bar",barWidth:"46%",
        data:F.ocf.map(function(v,i){
          return {value:v,itemStyle:{color:i<2?"#FFB020":"#19C2FF"}};
        }),
        label:{show:true,color:"#EAF4FF",fontSize:11,formatter:function(p){return fmt(p.value,0);}}}]};
  },
  chartRD:function(){
    var R=DATA.rd;
    return {color:[PALETTE[0],PALETTE[3]],tooltip:tt(""),
      legend:{top:4,textStyle:{color:CTEXT}},
      grid:{left:70,right:64,top:52,bottom:36},
      xAxis:ax({type:"category",data:R.years}),
      yAxis:[
        ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
        ax({type:"value",name:"费用率",nameTextStyle:{color:CSUB},splitLine:{show:false},axisLabel:{color:CSUB,formatter:"{value}%"}})
      ],
      series:[
        {name:"研发费用",type:"bar",barWidth:"42%",data:R.expense,
          label:{show:true,color:"#EAF4FF",fontSize:11,formatter:function(p){return fmt(p.value,0);}}},
        {name:"研发费用率",type:"line",yAxisIndex:1,data:R.ratio,symbol:"circle",symbolSize:9,
          lineStyle:{width:3},label:{show:true,color:"#FFD98A",formatter:function(p){return fmt(p.value,2)+"%";}},
          markLine:{symbol:"none",lineStyle:{color:"#FF6B81",type:"dashed",width:2},
            label:{color:"#FFB3C0",formatter:"同业均值 27.92%（9M2025）"},
            data:[{yAxis:R.peerAvg}]}}
      ]};
  },
  chartFund:function(){
    var R=DATA.rd;
    return {tooltip:tt(" 万元"),
      grid:{left:150,right:90,top:24,bottom:36},
      xAxis:ax({type:"value",name:"万元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
      yAxis:ax({type:"category",inverse:true,data:R.fund.map(function(f){return f.name;}),
        axisLabel:{color:CTEXT,fontSize:12.5}}),
      series:[{type:"bar",barWidth:"52%",
        data:R.fund.map(function(f,i){return {value:f.value,itemStyle:{color:PALETTE[i%PALETTE.length]}};}),
        label:{show:true,position:"right",color:"#EAF4FF",formatter:function(p){return fmt(p.value,2);}}}]};
  },
  chartCap:function(){
    var I=DATA.ipo;
    return {tooltip:{trigger:"axis",backgroundColor:"rgba(8,18,40,.94)",borderColor:"rgba(25,194,255,.4)",
        textStyle:{color:CTEXT},valueFormatter:function(v){return fmt(v,2)+" 亿元";}},
      grid:{left:80,right:40,top:40,bottom:40},
      xAxis:ax({type:"category",data:I.capLabels,boundaryGap:false}),
      yAxis:ax({type:"value",name:"亿元",nameTextStyle:{color:CSUB},axisLabel:{color:CSUB,formatter:function(v){return fmt(v,0);}}}),
      series:[{name:"市值",type:"line",data:I.capValues,symbol:"circle",symbolSize:10,
        lineStyle:{width:3,color:"#19C2FF"},itemStyle:{color:"#19C2FF"},
        areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,
          colorStops:[{offset:0,color:"rgba(25,194,255,.35)"},{offset:1,color:"rgba(25,194,255,.02)"}]}},
        label:{show:true,color:"#EAF4FF",formatter:function(p){return fmt(p.value,p.value<1000?2:0);}},
        markLine:{symbol:"none",lineStyle:{color:"rgba(255,176,32,.7)",type:"dashed"},
          label:{color:"#FFD98A",formatter:"发行市值 609.93 亿元"},
          data:[{yAxis:I.capValues[0]}]}}]};
  }
};
function initChartById(id){
  if(chartStarted[id])return;
  chartStarted[id]=true;
  var el=document.getElementById(id);
  if(!el||!CHART_BUILDERS[id])return;
  whenEcharts(function(){
    if(!window.echarts)return;
    var c=echarts.init(el,null,{renderer:"canvas"});
    c.setOption(CHART_BUILDERS[id]());
    charts[id]=c;
  });
}
var chartIO=new IntersectionObserver(function(es){
  es.forEach(function(e){if(e.isIntersecting){initChartById(e.target.id);chartIO.unobserve(e.target);}});
},{threshold:0.2});
$all(".echart").forEach(function(el){chartIO.observe(el);});
window.addEventListener("resize",function(){
  for(var k in charts)charts[k].resize();
});

/* ---------- Hero 粒子网络 ---------- */
(function(){
  var cv=$("#particles");if(!cv)return;
  var ctx=cv.getContext("2d"),W=0,H=0,pts=[];
  var N=window.innerWidth<720?36:72;
  var reduced=window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function resize(){
    W=cv.width=cv.offsetWidth;H=cv.height=cv.offsetHeight;
  }
  window.addEventListener("resize",resize);resize();
  for(var i=0;i<N;i++){
    pts.push({x:Math.random()*W,y:Math.random()*H,
      vx:(Math.random()-0.5)*0.42,vy:(Math.random()-0.5)*0.42,
      r:Math.random()*1.8+0.7});
  }
  var LINK=140;
  function frame(){
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<pts.length;i++){
      var p=pts[i];
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1;
      if(p.y<0||p.y>H)p.vy*=-1;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle="rgba(25,194,255,.75)";ctx.fill();
      for(var j=i+1;j<pts.length;j++){
        var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<LINK){
          ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);
          ctx.strokeStyle="rgba(25,194,255,"+(0.22*(1-d/LINK)).toFixed(3)+")";
          ctx.lineWidth=1;ctx.stroke();
        }
      }
    }
    if(!reduced)requestAnimationFrame(frame);
  }
  frame();
})();
})();
</script>
</body>
</html>
"""


def main():
    with open(COVER_PNG, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    html = TEMPLATE.replace("__PPT_COVER_B64__", b64)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = os.path.getsize(OUT_HTML) / 1024 / 1024
    print("输出文件: %s" % OUT_HTML)
    print("文件大小: %.2f MB（限制 < 8 MB）" % size_mb)
    assert size_mb < 8, "文件超出 8MB 限制"


if __name__ == "__main__":
    main()
