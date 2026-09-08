# -*- coding: utf-8 -*-
"""生成宇树科技交互式单文件 HTML 看板（内联 ECharts，离线可开）。数据全部来自已核验底稿。"""
from pathlib import Path
ROOT=Path('/Users/guoqingtao/Desktop/AI办公评测/豆包办公')
ech=(ROOT/'assets/echarts.min.js').read_text(encoding='utf-8')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>宇树科技 688836.SH · 经营财务交互看板（截至 2026-08-30）</title>
<style>
:root{
 --bg0:#081423; --bg1:#0E2238; --panel:rgba(20,40,63,.72); --panel2:rgba(30,55,84,.55);
 --line:rgba(138,162,188,.20); --line2:rgba(138,162,188,.38);
 --txt:#E9F0F7; --sub:#9DB2C6; --faint:#6E8499;
 --blue:#7FB2D9; --blue2:#4C7BA6; --blue3:#2F5578; --gold:#E0B267; --red:#DE7264; --green:#63B89E;
 --shadow:0 18px 50px -18px rgba(0,0,0,.65);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
 background:linear-gradient(180deg,#07111F 0%,var(--bg1) 38%,#0A1B2E 100%) fixed;
 color:var(--txt);line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
 background-image:linear-gradient(rgba(138,162,188,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(138,162,188,.05) 1px,transparent 1px);
 background-size:46px 46px;mask-image:radial-gradient(ellipse at 50% 0%,#000 30%,transparent 78%)}
a{color:var(--blue);text-decoration:none}
.wrap{max-width:1240px;margin:0 auto;padding:0 26px;position:relative;z-index:2}
/* progress */
#prog{position:fixed;top:0;left:0;height:3px;width:0;z-index:99;
 background:linear-gradient(90deg,var(--blue),var(--gold));box-shadow:0 0 12px var(--blue)}
/* nav */
nav{position:fixed;top:0;left:0;right:0;z-index:90;backdrop-filter:blur(14px);
 background:rgba(8,18,31,.78);border-bottom:1px solid var(--line)}
.navin{max-width:1240px;margin:0 auto;display:flex;align-items:center;gap:4px;padding:10px 22px;overflow-x:auto}
.brand{font-weight:700;letter-spacing:.5px;margin-right:14px;white-space:nowrap;font-size:14.5px}
.brand b{color:var(--gold)}
.navin a{color:var(--sub);font-size:12.5px;padding:5px 10px;border-radius:20px;white-space:nowrap;transition:.25s}
.navin a:hover,.navin a.on{color:var(--txt);background:rgba(127,178,217,.14)}
/* hero */
header.hero{position:relative;min-height:92vh;display:flex;align-items:center;padding:110px 0 60px}
#stars{position:absolute;inset:0;z-index:1}
.hero-in{position:relative;z-index:3;width:100%}
.tag{display:inline-flex;gap:10px;align-items:center;font-size:12.5px;color:var(--sub);
 border:1px solid var(--line2);border-radius:30px;padding:6px 16px;background:rgba(20,40,63,.5)}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green);animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.35}}
h1{font-size:clamp(30px,5vw,54px);line-height:1.18;margin:20px 0 14px;font-weight:800;letter-spacing:1px}
h1 .g{background:linear-gradient(90deg,#BFD9EE,var(--blue) 45%,var(--gold));-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{color:var(--sub);max-width:820px;font-size:15.5px}
.lead b{color:var(--txt)}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-top:42px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 16px;position:relative;overflow:hidden;
 transition:.35s;box-shadow:var(--shadow)}
.kpi::after{content:"";position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,var(--blue),transparent);opacity:.7}
.kpi:hover{transform:translateY(-5px);border-color:var(--line2)}
.kpi .v{font-size:27px;font-weight:800;letter-spacing:.5px;font-variant-numeric:tabular-nums}
.kpi .v small{font-size:13px;font-weight:600;color:var(--sub);margin-left:2px}
.kpi .l{font-size:12px;color:var(--sub);margin-top:5px}
.kpi .d{font-size:11px;color:var(--faint);margin-top:7px;line-height:1.5}
.gold{color:var(--gold)}.red{color:var(--red)}.green{color:var(--green)}.blue{color:var(--blue)}
/* sections */
section{padding:64px 0 18px;position:relative}
.sec-h{display:flex;align-items:baseline;gap:16px;margin-bottom:8px}
.sec-no{font-size:13px;color:var(--gold);letter-spacing:3px;font-weight:700}
h2{font-size:clamp(21px,2.6vw,30px);font-weight:800;letter-spacing:.5px}
.sec-sub{color:var(--sub);font-size:13.5px;margin-bottom:26px;max-width:900px}
.grid{display:grid;gap:16px}
.g2{grid-template-columns:1.25fr 1fr}.g2e{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px;backdrop-filter:blur(8px);box-shadow:var(--shadow)}
.card h3{font-size:15.5px;margin-bottom:14px;display:flex;align-items:center;gap:9px;font-weight:700}
.card h3::before{content:"";width:4px;height:15px;border-radius:2px;background:linear-gradient(var(--blue),var(--gold))}
.chart{width:100%;height:330px}
.chart.sm{height:280px}
.note{font-size:11.5px;color:var(--faint);margin-top:10px;line-height:1.6}
/* profile */
.pgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.pitem{background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:13px 15px}
.pitem .k{font-size:11.5px;color:var(--faint)}.pitem .val{font-size:14.5px;font-weight:700;margin-top:3px}
.pitem .val small{color:var(--sub);font-weight:500;font-size:11.5px}
/* toggle */
.seg{display:inline-flex;background:rgba(8,18,31,.6);border:1px solid var(--line2);border-radius:10px;overflow:hidden;margin-bottom:8px}
.seg button{background:transparent;border:0;color:var(--sub);padding:7px 16px;font-size:12.5px;cursor:pointer;transition:.25s;font-family:inherit}
.seg button.on{background:linear-gradient(135deg,var(--blue2),var(--blue3));color:#fff;font-weight:700}
/* table */
table{width:100%;border-collapse:collapse;font-size:12.8px;font-variant-numeric:tabular-nums}
th,td{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left;color:var(--sub)}
thead th{color:var(--sub);font-weight:600;font-size:11.5px;border-bottom:1px solid var(--line2)}
tbody tr:hover{background:rgba(127,178,217,.07)}
td.hl{color:var(--gold);font-weight:700}
/* A vs E */
.ae{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.ae .b{border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--panel2)}
.ae .b .t{font-size:12px;color:var(--sub);margin-bottom:6px}
.ae .b .e{font-size:12px;color:var(--faint)}
.ae .b .a{font-size:19px;font-weight:800;margin:4px 0}
.tagpill{display:inline-block;font-size:10.5px;padding:2px 9px;border-radius:20px;margin-left:8px;vertical-align:middle}
.p-a{background:rgba(99,184,158,.16);color:var(--green);border:1px solid rgba(99,184,158,.4)}
.p-e{background:rgba(224,178,103,.14);color:var(--gold);border:1px solid rgba(224,178,103,.38)}
/* points / risks */
.pts{display:grid;gap:11px}
.pt{display:flex;gap:13px;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;transition:.3s;cursor:default}
.pt:hover{transform:translateX(5px);border-color:var(--line2)}
.pt .n{flex:0 0 30px;height:30px;border-radius:9px;display:grid;place-items:center;font-weight:800;font-size:13.5px}
.pt.g .n{background:linear-gradient(135deg,#356084,#4C7BA6);color:#DCE9F5}
.pt.r .n{background:linear-gradient(135deg,#8C3B32,#B8554A);color:#F6DDD9}
.pt .h{font-weight:700;font-size:13.8px;margin-bottom:2px}
.pt .b{font-size:12.3px;color:var(--sub)}
/* judgments */
.jlist{display:grid;grid-template-columns:repeat(3,1fr);gap:13px;counter-reset:j}
.j{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:16px;position:relative;transition:.3s}
.j:hover{border-color:var(--gold);transform:translateY(-3px)}
.j .jn{font-size:11px;color:var(--gold);letter-spacing:2px;font-weight:700;margin-bottom:7px}
.j .jh{font-weight:700;font-size:13.8px;margin-bottom:6px}
.j .jb{font-size:12.2px;color:var(--sub)}
/* driver A/E */
.drv{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.drv .col{border-radius:14px;padding:18px;border:1px solid var(--line)}
.drv .done{background:linear-gradient(160deg,rgba(99,184,158,.10),rgba(20,40,63,.4))}
.drv .todo{background:linear-gradient(160deg,rgba(224,178,103,.10),rgba(20,40,63,.4))}
.drv h4{font-size:14px;margin-bottom:12px;display:flex;gap:8px;align-items:center}
.drv li{list-style:none;font-size:12.6px;color:var(--sub);padding:7px 0 7px 18px;position:relative;border-bottom:1px dashed var(--line)}
.drv li::before{content:"";position:absolute;left:0;top:14px;width:7px;height:7px;border-radius:50%}
.done li::before{background:var(--green)}.todo li::before{background:var(--gold)}
.drv li b{color:var(--txt)}
/* sources */
.src{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 22px;font-size:12.2px}
.src div{padding:7px 0;border-bottom:1px solid var(--line);color:var(--sub);word-break:break-all}
.src b{color:var(--txt)}
.disc{margin-top:20px;padding:16px 18px;border:1px solid rgba(222,114,100,.4);border-radius:12px;background:rgba(222,114,100,.08);font-size:12.3px;color:#E8C4BF}
footer{padding:46px 0 70px;color:var(--faint);font-size:11.8px;text-align:center}
#top{position:fixed;right:26px;bottom:26px;width:44px;height:44px;border-radius:50%;z-index:80;cursor:pointer;
 background:linear-gradient(135deg,var(--blue2),var(--blue3));border:1px solid var(--line2);color:#fff;font-size:18px;
 opacity:0;pointer-events:none;transition:.3s;box-shadow:var(--shadow)}
#top.show{opacity:1;pointer-events:auto}
.reveal{opacity:0;transform:translateY(34px);transition:opacity .8s cubic-bezier(.2,.7,.2,1),transform .8s cubic-bezier(.2,.7,.2,1)}
.reveal.in{opacity:1;transform:none}
@media(max-width:980px){.kpis{grid-template-columns:repeat(2,1fr)}.g2,.g2e,.g3,.g4,.pgrid,.jlist,.ae,.drv,.src{grid-template-columns:1fr}}
</style>
</head>
<body>
<div id="prog"></div>
<nav><div class="navin">
 <span class="brand">宇树科技 <b>688836.SH</b></span>
 <a href="#overview">概览</a><a href="#ipo">公司与IPO</a><a href="#growth">增长</a><a href="#product">产品</a>
 <a href="#profit">盈利</a><a href="#market">市场</a><a href="#rd">研发</a><a href="#cash">现金流</a>
 <a href="#pr">要点·风险</a><a href="#driver">增长变量</a><a href="#src">来源</a>
</div></nav>

<header class="hero" id="overview">
 <canvas id="stars"></canvas>
 <div class="wrap hero-in">
  <span class="tag"><span class="dot"></span>科创板通用机器人龙头 · 2026-08-19 上市 · 资料截止 2026-08-30 · A=已实现 / E=预测严格分列</span>
  <h1>宇树科技 <span class="g">经营与财务全景交互看板</span></h1>
  <p class="lead">三年营收 <b>1.59 → 16.99 亿元</b>（两年 CAGR 约 226.8%），2025 年人形机器人收入反超四足成为第一大产品；
   <b>扣非净利润 5.91 亿、扣非净利率 34.8%、主营毛利率 60.13%</b>。2026H1 收入 +48.54% 但扣非同比 -19.34%——高增长换挡、人形切换、扣非盈利与费用扩张的赛跑。</p>
  <div class="kpis">
   <div class="kpi"><div class="v blue"><span data-c="16.99" data-d="2">0</span><small>亿</small></div><div class="l">2025 营业收入</div><div class="d">同比 +332.64%，两年 CAGR 约 226.8%</div></div>
   <div class="kpi"><div class="v"><span data-c="5.91" data-d="2">0</span><small>亿</small></div><div class="l">2025 扣非归母净利</div><div class="d">扣非净利率 34.8%；归母 2.78 亿受股份支付扰动</div></div>
   <div class="kpi"><div class="v gold"><span data-c="60.13" data-d="2">0</span><small>%</small></div><div class="l">2025 主营毛利率</div><div class="d">44.22%→56.74%→60.13% 逐年抬升</div></div>
   <div class="kpi"><div class="v"><span data-c="51.78" data-d="2">0</span><small>%</small></div><div class="l">2025 人形收入占主营</div><div class="d">1.88%→27.60%→51.78%，两年成为第一大产品</div></div>
   <div class="kpi"><div class="v blue"><span data-c="11.52" data-d="2">0</span><small>亿</small></div><div class="l">2026H1 营收（未审计）</div><div class="d">同比 +48.54%；扣非 2.44 亿、同比 <span class="red">-19.34%</span></div></div>
   <div class="kpi"><div class="v gold"><span data-c="59.17" data-d="2">0</span><small>亿</small></div><div class="l">IPO 募资净额</div><div class="d">发行市值 609.93 亿，发行价 150.80 元</div></div>
  </div>
 </div>
</header>

<!-- 公司与 IPO -->
<section id="ipo"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">01</span><h2>公司画像与发行结构</h2></div>
 <p class="sec-sub reveal">宇树科技股份有限公司，科创板（688836.SH），按“预计市值≥100 亿元”标准上市，设表决权差异安排。</p>
 <div class="grid g2e">
  <div class="card reveal"><h3>发行与上市关键数据</h3>
   <div class="pgrid">
    <div class="pitem"><div class="k">上市日期 / 板块</div><div class="val">2026-08-19 <small>科创板</small></div></div>
    <div class="pitem"><div class="k">发行价</div><div class="val">150.80 <small>元/股</small></div></div>
    <div class="pitem"><div class="k">发行股数</div><div class="val">4,044.6434 <small>万股（发行后 10%）</small></div></div>
    <div class="pitem"><div class="k">发行后总股本</div><div class="val">40,446.4340 <small>万股</small></div></div>
    <div class="pitem"><div class="k">募资总额 / 净额</div><div class="val">60.99 / 59.17 <small>亿元</small></div></div>
    <div class="pitem"><div class="k">发行市值</div><div class="val">609.93 <small>亿元</small></div></div>
    <div class="pitem"><div class="k">发行市盈率</div><div class="val">219.23 <small>倍 · 媒体口径待核</small></div></div>
    <div class="pitem"><div class="k">实控人王兴兴</div><div class="val">发行后持股 21.44%<small> · 表决权差异安排</small></div></div>
    <div class="pitem"><div class="k">Pre-IPO（2025-06）</div><div class="val">投前 120 / 投后 127 <small>亿元</small></div></div>
   </div>
   <p class="note">注：发行市盈率 219.23 倍为媒体口径，需以公告原文复核；其余为注册稿/上市公告口径。</p>
  </div>
  <div class="card reveal"><h3>募投方向：约 85% 投向研发（原拟募集约 42.02 亿，分项为约数待核）</h3>
   <div id="c_mu" class="chart sm"></div>
   <p class="note">模型研发 20.22 亿、本体研发 11.10 亿、新产品开发 4.45 亿（研发三项合计约 35.77 亿、约 85%），制造基地 6.24 亿。制造基地达产规划：人形 7.5 万台 + 四足 11.5 万台/年——<b>为规划，非已实现产能</b>。</p>
  </div>
 </div>
</div></section>

<!-- 增长 -->
<section id="growth"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">02</span><h2>增长轨迹：三年十倍级，增速逐期换挡</h2></div>
 <p class="sec-sub reveal">2023–2025 营收 1.59/3.93/16.99 亿元，同比 +146.82%/+332.64%；进入 2026 年斜率回落至中高速区间（2026Q1 +68.49%、H1 +48.54%）。</p>
 <div class="grid g2">
  <div class="card reveal"><h3>年度营收与同比增速（亿元，A）</h3><div id="c_rev" class="chart"></div>
   <p class="note">2026H1 营收 11.52 亿元为半年数（未审计），不与全年直接比较；其略超 2026-05 上会稿业绩预告上限 11.28 亿（E）。</p></div>
  <div class="card reveal"><h3>单季节奏：单季营收 & 累计扣非（亿元，累计相减）</h3><div id="c_q" class="chart"></div>
   <p class="note">单季值由累计数相减得到；2025H1 曾含约 3.49 亿股份支付形成低基数。2026Q2 单季营收 7.29 亿为历史最高单季。</p></div>
 </div>
 <div class="card reveal" style="margin-top:16px"><h3>2026H1：业绩预告区间（E）vs 实际（A）</h3>
  <div class="ae">
   <div class="b"><div class="t">营业收入</div><div class="e">E：10.52–11.28 亿（+35.62%~45.41%）</div><div class="a green">A：11.52 亿（+48.54%）</div><span class="tagpill p-a">略超预告上限</span></div>
   <div class="b"><div class="t">归母净利润</div><div class="e">E：2.58–3.06 亿</div><div class="a">A：2.74 亿</div><span class="tagpill p-a">落区间内 · 未审计</span></div>
   <div class="b"><div class="t">扣非归母净利</div><div class="e">E：2.36–2.83 亿（-21.97%~-6.43%）</div><div class="a red">A：2.44 亿（-19.34%）</div><span class="tagpill p-a">落区间内 · 未审计</span></div>
  </div>
 </div>
</div></section>

<!-- 产品 -->
<section id="product"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">03</span><h2>产品切换：人形两年间成为第一大产品，量增价减</h2></div>
 <p class="sec-sub reveal">人形主营收入 0.03→1.07→8.68 亿元，占比 1.88%→27.60%→51.78%；2025 年确认收入口径销量 5,215 台，公司称纯人形出货超 5,500 台、全球第一。</p>
 <div class="grid g2e">
  <div class="card reveal"><h3>主营收入分产品占比（%，100% 堆叠）</h3><div id="c_prod" class="chart"></div>
   <p class="note">组件及其他 2025 占约 6.6%（由主营轧差，组件约 1.04 亿、精确拆分待核）。</p></div>
  <div class="card reveal"><h3>销量与平均单价（切换查看）</h3>
   <div class="seg" id="seg_prod"><button class="on" data-k="h">人形机器人</button><button data-k="q">四足机器人</button></div>
   <div id="c_pq" class="chart"></div>
   <p class="note" id="pq_note"></p></div>
 </div>
</div></section>

<!-- 盈利 -->
<section id="profit"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">04</span><h2>盈利质量：扣非强劲，归母受股份支付扰动</h2></div>
 <p class="sec-sub reveal">2025 非经常性净损失 -3.13 亿元（主要为股份支付），使归母 2.78 亿低于扣非 5.91 亿；评估盈利能力应以扣非为主线。</p>
 <div class="grid g2">
  <div class="card reveal"><h3>归母/扣非净利与主营毛利率（亿元 / %）</h3><div id="c_pf" class="chart"></div>
   <p class="note">2023 年归母 -0.11 亿、扣非 -0.18 亿；毛利率线为右轴。</p></div>
  <div class="card reveal"><h3>盈利能力指标明细（%，A）</h3>
   <table><thead><tr><th>指标</th><th>2023A</th><th>2024A</th><th>2025A</th></tr></thead><tbody>
    <tr><td>主营毛利率</td><td>44.22</td><td>56.74</td><td class="hl">60.13</td></tr>
    <tr><td>综合毛利率</td><td>44.75</td><td>57.22</td><td>60.44</td></tr>
    <tr><td>销售净利率</td><td>-7.00</td><td>24.31</td><td>16.37</td></tr>
    <tr><td>扣非净利率</td><td>-11.32</td><td>19.98</td><td class="hl">34.77</td></tr>
    <tr><td>扣非加权 ROE</td><td>-5.92</td><td>8.60</td><td class="hl">28.70</td></tr>
    <tr><td>研发费用率</td><td>31.39</td><td>17.83</td><td>8.53</td></tr>
    <tr><td>基本 EPS（元，2025）</td><td colspan="3" class="hl">0.76</td></tr>
   </tbody></table>
   <p class="note">销售净利率 2025 回落主因股份支付等非经常项；扣非净利率持续上行至 34.77%。</p>
  </div>
 </div>
</div></section>

<!-- 市场 -->
<section id="market"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">05</span><h2>市场结构：2025 境内反超境外；下游仍以科研教育为主</h2></div>
 <p class="sec-sub reveal">境内主营占比 44.4%→44.3%→56.4%，2025 年反超；境外 7.32 亿、占 43.65%，仍是重要市场并带来汇率敞口。</p>
 <div class="grid g2e">
  <div class="card reveal"><h3>境内 / 境外收入（切换金额或占比）</h3>
   <div class="seg" id="seg_reg"><button class="on" data-k="pct">占比 %</button><button data-k="amt">金额（亿元）</button></div>
   <div id="c_reg" class="chart sm"></div></div>
  <div class="card reveal"><h3>下游应用场景（2025 年 1–9M，申报稿口径）</h3><div id="c_scn" class="chart sm"></div>
   <p class="note">人形约 73.6% 来自科研教育、行业应用仅约 9.01%——商业化场景集中是核心风险之一；该结构为 1–9M 口径，非全年。</p></div>
 </div>
</div></section>

<!-- 研发与组织 -->
<section id="rd"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">06</span><h2>研发投入：绝对额持续上升，费率被规模摊薄</h2></div>
 <p class="sec-sub reveal">研发费用 0.50→0.70→1.45 亿元、三年累计 2.65 亿；费率 31.39%→8.53% 是规模摊薄而非收缩，IPO 募投约 85% 继续投向研发。</p>
 <div class="grid g2">
  <div class="card reveal"><h3>研发费用与费用率（亿元 / %）</h3><div id="c_rd" class="chart"></div></div>
  <div class="card reveal"><h3>组织与人均效率（2025 年末，A）</h3>
   <div class="grid g4" style="margin-bottom:14px">
    <div class="pitem"><div class="k">员工总数</div><div class="val">516 <small>人</small></div></div>
    <div class="pitem"><div class="k">研发人员</div><div class="val">184 <small>人 · 35.66%</small></div></div>
    <div class="pitem"><div class="k">人均营收</div><div class="val">329.32 <small>万元/人</small></div></div>
    <div class="pitem"><div class="k">劳务外包（2025）</div><div class="val">0.68 <small>亿元</small></div></div>
   </div>
   <table><thead><tr><th>期间费用（亿元）</th><th>2023A</th><th>2024A</th><th>2025A</th></tr></thead><tbody>
    <tr><td>研发费用</td><td>0.50</td><td>0.70</td><td class="hl">1.45</td></tr>
    <tr><td>销售费用</td><td>0.38</td><td>0.59</td><td>1.41</td></tr>
    <tr><td>劳务外包采购</td><td>0.12</td><td>0.19</td><td>0.68</td></tr>
   </tbody></table>
   <p class="note">2026H1 研发费用同比增加 0.82 亿、销售费用 1.64 亿，是扣非承压的费用侧原因；2025 销售费用为按费率反推约数（待核）。</p>
  </div>
 </div>
</div></section>

<!-- 现金流 -->
<section id="cash"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">07</span><h2>现金流与资产负债表：经营造血良好、杠杆低</h2></div>
 <p class="sec-sub reveal">2025 经营现金流净额 6.70 亿、CFO/营收 39.43%，资产负债率仅 18.82%；IPO 后资金更充裕，2026H1 末总资产 38.45 亿。</p>
 <div class="grid g2">
  <div class="card reveal"><h3>经营现金流净额与资产负债率（亿元 / %）</h3><div id="c_cfo" class="chart"></div></div>
  <div class="card reveal"><h3>资产负债与现金流明细</h3>
   <table><thead><tr><th>指标</th><th>2023A</th><th>2024A</th><th>2025A</th><th>2026H1</th></tr></thead><tbody>
    <tr><td>总资产（亿元）</td><td>3.91</td><td>15.28</td><td>32.09</td><td class="hl">38.45</td></tr>
    <tr><td>归母权益（亿元）</td><td>2.99</td><td>12.81</td><td>26.05</td><td>—</td></tr>
    <tr><td>资产负债率 %</td><td>23.57</td><td>16.19</td><td>18.82</td><td>25.11</td></tr>
    <tr><td>经营现金流（亿元）</td><td>0.05</td><td>1.92</td><td class="hl">6.70</td><td>2.32</td></tr>
    <tr><td>CFO/营收 %</td><td>3.11</td><td>48.98</td><td>39.43</td><td>—</td></tr>
   </tbody></table>
   <p class="note">2026H1 末总资产较年初 +19.85%、负债较年初 +59.88%、负债率 25.11%；H1 经营现金流 2.32 亿、同比 -32.53%（未审计）。</p>
  </div>
 </div>
</div></section>

<!-- 要点与风险 -->
<section id="pr"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">08</span><h2>投资要点 与 主要风险</h2></div>
 <p class="sec-sub reveal">悬停可查看细节；要点与风险一一对应，便于在路演中同时呈现多空两面。</p>
 <div class="grid g2e">
  <div class="card reveal"><h3>五条投资要点</h3><div class="pts" id="bulls"></div></div>
  <div class="card reveal"><h3>六类主要风险</h3><div class="pts" id="risks"></div></div>
 </div>
 <div class="card reveal" style="margin-top:16px"><h3>九条核心判断（与 Excel 底稿、Word 报告、PPT 完全一致）</h3>
  <div class="jlist" id="judges"></div></div>
</div></section>

<!-- 增长变量 -->
<section id="driver"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">09</span><h2>增长变量：事实（A）与计划/待验证（E）分列</h2></div>
 <p class="sec-sub reveal">严格区分已兑现事实与规划/预测，预测不作为已实现事实。</p>
 <div class="drv reveal">
  <div class="col done"><h4><span class="tagpill p-a">A 已兑现</span></h4><ul>
   <li>人形放量至主营 <b>51.78%</b>，2025 确认收入 5,215 台、公司称纯人形出货超 5,500 台全球第一</li>
   <li>境内收入反超至 <b>56.35%</b>，境外占 43.65%、收入 7.32 亿</li>
   <li>IPO 募资净额 <b>59.17 亿</b>到位，发行市值 609.93 亿</li>
   <li>2025 扣非净利 5.91 亿、<b>扣非净利率 34.8%</b>、主营毛利率 60.13%</li>
   <li>经营现金流 6.70 亿、资产负债率仅 18.82%</li>
  </ul></div>
  <div class="col todo"><h4><span class="tagpill p-e">E 待验证 / 规划</span></h4><ul>
   <li>行业场景渗透提速：当前人形行业应用仅约 <b>9.01%</b>（2025 1–9M）</li>
   <li>募投研发转化：模型/本体/新产品约 35.77 亿投入的产品化兑现</li>
   <li>制造基地达产规划：人形 7.5 万 + 四足 11.5 万台/年（<b>规划，非已实现</b>）</li>
   <li>海外扩张与汇率管理（境外占 43.65%）</li>
   <li>价格带下探：G1 进入 10 万元级后“以价换量”的规模弹性</li>
  </ul></div>
 </div>
</div></section>

<!-- 来源 -->
<section id="src"><div class="wrap">
 <div class="sec-h reveal"><span class="sec-no">10</span><h2>资料来源与口径说明</h2></div>
 <div class="card reveal">
  <div class="src">
   <div><b>S1</b> 招股说明书（注册稿）·上交所项目页 auditId=2178<br><a href="https://star.sse.com.cn/listing/renewal/ipo/index_listing_detail.shtml?auditId=2178" target="_blank">star.sse.com.cn/…/index_listing_detail.shtml?auditId=2178</a></div>
   <div><b>S2</b> 上市保荐书（注册稿）<br><a href="http://static.sse.com.cn/stock/disclosure/announcement/c/202606/002178_20260602_VI1W.pdf" target="_blank">static.sse.com.cn/…/002178_20260602_VI1W.pdf</a></div>
   <div><b>S3</b> 审核落实函回复<br><a href="http://static.sse.com.cn/stock/disclosure/announcement/c/202605/002178_20260525_V4H0.pdf" target="_blank">static.sse.com.cn/…/002178_20260525_V4H0.pdf</a></div>
   <div><b>S4</b> 招股意向书（新浪财经披露）<br><a href="https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?CompanyCode=82494861&gather=1&id=12470775" target="_blank">vip.stock.finance.sina.com.cn/…id=12470775</a></div>
   <div><b>S5</b> 上市公告书提示（上海证券报）<br><a href="http://paper.cnstock.com/html/2026-08/18/content_2255912.htm" target="_blank">paper.cnstock.com/…/content_2255912.htm</a></div>
   <div><b>S6</b> 发行/投资风险特别公告（巨潮）<br><a href="https://static.cninfo.com.cn/finalpage/2026-08-07/1225462415.PDF" target="_blank">static.cninfo.com.cn/…/1225462415.PDF</a></div>
   <div><b>S7</b> 浦银国际研究 <a href="https://www.spdbi.com" target="_blank">spdbi.com</a></div>
   <div><b>S8/S9</b> 兴业证券 / 国信证券研报转引（慧博）<a href="https://www.hibor.com.cn" target="_blank">hibor.com.cn</a></div>
   <div><b>S10</b> 东方财富 / 证券时报数据中心（交叉核对）<br><a href="https://data.eastmoney.com/stockdata/688836.html" target="_blank">data.eastmoney.com/stockdata/688836.html</a></div>
   <div><b>S11</b> 宇树科技官网 <a href="https://www.unitree.com" target="_blank">unitree.com</a></div>
  </div>
  <div class="disc">口径说明：金额除注明外为万元（图表换算为亿元）；2023–2025 为经审计年度数（注册稿口径），2026Q1 经审阅、2026H1 为上市公告书披露且<b>未经审计</b>；E 为 2026-05 上会稿业绩预告，预测不作为已实现事实；占比/同比/CAGR 由原始数据现算，“约/待核”为原始披露未直接给出或需以原文复核项（发行市盈率媒体口径、2025 销售费用约数、募投分项约数、组件收入精确拆分）。本看板仅用于内部投资研究汇报，<b>不构成任何投资建议</b>；二级市场行情截至 2026-08-30，其后数据不纳入。</div>
 </div>
</div></section>

<footer>宇树科技 688836.SH · 经营财务交互看板 · 单文件离线版 · 数据截止 2026-08-30 · 与 Excel 底稿 / Word 报告 / PPT 同源同口径</footer>
<button id="top" onclick="scrollTo({top:0,behavior:'smooth'})">↑</button>

<script>__ECHARTS__</script>
<script>
const C={ink:'#0E2238',blue:'#7FB2D9',blue2:'#4C7BA6',blue3:'#2F5578',gold:'#E0B267',red:'#DE7264',green:'#63B89E',sub:'#9DB2C6',line:'rgba(138,162,188,.22)',grid:'rgba(138,162,18,.14)'};
const yrs=['2023A','2024A','2025A'];
const baseTip={backgroundColor:'rgba(10,24,40,.94)',borderColor:C.line,textStyle:{color:'#E9F0F7',fontSize:12},confine:true};
const axCommon={axisLine:{lineStyle:{color:C.line}},axisLabel:{color:C.sub,fontSize:11,fontFamily:'inherit'},axisTick:{show:false}};
const splitLine={lineStyle:{color:'rgba(138,162,188,.12)'}};
function mk(id){const el=document.getElementById(id);if(!el)return null;const ch=echarts.init(el,null,{renderer:'canvas'});return ch;}
const charts={};
const R={};
function reg(id,fn){R[id]=fn;}
function bindLazy(){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting&&R[e.id]){R[e.id]();delete R[e.id];io.unobserve(e.target);}}),{threshold:.12});
 document.querySelectorAll('.chart').forEach(el=>io.observe(el));}
function growOpt(series,opt){return Object.assign({animationDuration:1400,animationEasing:'cubicOut',grid:{left:46,right:opt&&opt.r?52:18,top:opt&&opt.top||42,bottom:30},tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'}},baseTip)},series);}

/* C1 年度营收 + 同比 */
charts.rev=mk('c_rev');
function optRev(){return growOpt({xAxis:Object.assign({type:'category',data:[...yrs,'2026H1*']},axCommon),
 yAxis:[Object.assign({type:'value',name:'亿元',nameTextStyle:{color:C.sub},max:19.5,splitLine},axCommon),
        Object.assign({type:'value',name:'同比%',nameTextStyle:{color:C.sub},max:450,interval:150,splitLine:{show:false}},axCommon)],
 series:[
  {type:'bar',barWidth:'46%',data:[
    {value:1.59,itemStyle:{color:C.blue3}},{value:3.93,itemStyle:{color:C.blue2}},
    {value:16.99,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#9CC4E4'},{offset:1,color:C.blue2}])}},
    {value:11.52,itemStyle:{color:'rgba(224,178,103,.35)',borderColor:C.gold,borderWidth:1,borderType:'dashed'}}],
   label:{show:true,position:'top',distance:4,color:'#E9F0F7',fontWeight:700,formatter:p=>p.value}},
  {type:'line',yAxisIndex:1,data:[null,146.82,332.64,null],smooth:false,symbolSize:9,
   lineStyle:{color:C.gold,width:2.5},itemStyle:{color:C.gold},
   label:{show:true,position:'top',distance:8,color:C.gold,fontWeight:700,formatter:p=>p.value?('+'+p.value+'%'):''}}
 ]},{r:1});}

/* C2 单季 */
charts.q=mk('c_q');
const qlabs=['25Q1','25Q2','25Q3','25Q4','26Q1','26Q2'];
reg('c_q',()=>charts.q.setOption(growOpt({xAxis:Object.assign({type:'category',data:qlabs},axCommon),
 yAxis:[Object.assign({type:'value',name:'亿元',splitLine},axCommon),Object.assign({type:'value',name:'累计扣非',splitLine:{show:false}},axCommon)],
 series:[
  {type:'bar',barWidth:'48%',data:[2.51,5.25,3.92,5.32,4.23,7.29],
   itemStyle:{color:p=>p.dataIndex>=4?C.gold:C.blue2,borderRadius:[3,3,0,0]},
   label:{show:true,position:'top',color:'#E9F0F7',fontSize:10}},
  {type:'line',yAxisIndex:1,smooth:true,symbolSize:7,data:[0.85,3.02,4.31,5.91,0.40,2.44],
   lineStyle:{color:C.blue,width:2.5},itemStyle:{color:C.blue}}
 ]},{r:1})));

/* C3 产品堆叠 */
charts.prod=mk('c_prod');
reg('c_prod',()=>charts.prod.setOption(growOpt({
 legend:{top:4,textStyle:{color:C.sub,fontSize:11},itemWidth:12,itemHeight:8},
 xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:Object.assign({type:'value',max:100,name:'%',splitLine},axCommon),
 series:[
  {name:'人形',type:'bar',stack:'t',barWidth:'46%',data:[1.88,27.60,51.78],itemStyle:{color:C.blue},label:{show:true,formatter:'{c}%',color:'#081423',fontWeight:700,fontSize:10}},
  {name:'四足',type:'bar',stack:'t',data:[75.78,59.53,41.62],itemStyle:{color:C.blue2},label:{show:true,formatter:'{c}%',color:'#fff',fontSize:10}},
  {name:'组件及其他',type:'bar',stack:'t',data:[22.34,12.87,6.60],itemStyle:{color:'rgba(157,178,198,.55)'},label:{show:true,formatter:'{c}%',color:'#E9F0F7',fontSize:10}}
 ]})));

/* C4 量价切换 */
charts.pq=mk('c_pq');
const PQ={h:{vol:[5,412,5215],asp:[59.34,26.04,16.64],name:'人形机器人',
  note:'人形销量 5→412→5,215 台；平均单价 59.34→26.04→16.64 万元/台，以价换量、G1 进入 10 万元级。2025 公司称纯人形出货超 5,500 台、全球第一。'},
 q:{vol:[3121,7136,23037],asp:[3.83,3.23,3.03],name:'四足机器人',
  note:'四足销量 3,121→7,136→23,037 台（三年累计超 3.3 万台）；单价 3.83→3.23→3.03 万元/台，同样量增价减。'}};
function optPQ(k){const d=PQ[k];return growOpt({xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:[Object.assign({type:'value',name:'销量(台)',splitLine},axCommon),Object.assign({type:'value',name:'单价(万元)',splitLine:{show:false}},axCommon)],
 series:[
  {type:'bar',barWidth:'44%',data:d.vol,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:C.blue},{offset:1,color:C.blue3}]),borderRadius:[3,3,0,0]},label:{show:true,position:'top',color:'#E9F0F7',fontSize:10}},
  {type:'line',yAxisIndex:1,data:d.asp,smooth:true,symbolSize:9,lineStyle:{color:C.gold,width:2.5},itemStyle:{color:C.gold},label:{show:true,color:C.gold,formatter:'{c}'}}
 ]},{r:1});}
reg('c_pq',()=>{charts.pq.setOption(optPQ('h'));});
document.getElementById('pq_note').textContent=PQ.h.note;
document.querySelectorAll('#seg_prod button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('#seg_prod button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 const k=b.dataset.k;charts.pq.setOption(optPQ(k));document.getElementById('pq_note').textContent=PQ[k].note;});

/* C5 盈利 */
charts.pf=mk('c_pf');
reg('c_pf',()=>charts.pf.setOption(growOpt({
 legend:{top:4,textStyle:{color:C.sub,fontSize:11},itemWidth:12,itemHeight:8},
 xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:[Object.assign({type:'value',name:'亿元',splitLine},axCommon),Object.assign({type:'value',name:'毛利率%',min:30,max:75,splitLine:{show:false}},axCommon)],
 series:[
  {name:'归母净利',type:'bar',barWidth:'30%',data:[-0.11,0.95,2.78],itemStyle:{color:'rgba(157,178,198,.6)'},label:{show:true,position:'top',color:C.sub,fontSize:10}},
  {name:'扣非归母',type:'bar',barWidth:'30%',data:[-0.18,0.78,5.91],itemStyle:{color:C.blue2},label:{show:true,position:'top',color:'#E9F0F7',fontWeight:700,fontSize:10}},
  {name:'主营毛利率',type:'line',yAxisIndex:1,data:[44.22,56.74,60.13],smooth:true,symbolSize:9,lineStyle:{color:C.red,width:2.5},itemStyle:{color:C.red},label:{show:true,color:C.red,formatter:'{c}%'}}
 ]},{r:1})));

/* C6 地区切换 */
charts.reg=mk('c_reg');
const REG={pct:{inb:[44.37,44.26,56.35],out:[55.63,55.74,43.65],u:'%',max:100},
 amt:{inb:[0.70,1.71,9.44],out:[0.88,2.16,7.32],u:'亿元',max:null}};
function optReg(k){const d=REG[k];return growOpt({
 legend:{top:0,textStyle:{color:C.sub,fontSize:11},itemWidth:12,itemHeight:8},
 xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:Object.assign({type:'value',name:d.u,max:d.max,splitLine},axCommon),
 series:[
  {name:'境内',type:k==='pct'?'bar':'bar',stack:k==='pct'?'r':null,barWidth:'46%',data:d.inb,itemStyle:{color:C.blue},label:{show:k==='pct',formatter:'{c}'+(k==='pct'?'%':''),color:'#081423',fontWeight:700,fontSize:10}},
  {name:'境外',type:'bar',stack:k==='pct'?'r':null,data:d.out,itemStyle:{color:C.gold},label:{show:k==='pct',formatter:'{c}%',color:'#081423',fontSize:10}}
 ]});}
reg('c_reg',()=>charts.reg.setOption(optReg('pct')));
document.querySelectorAll('#seg_reg button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('#seg_reg button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 charts.reg.setOption(optReg(b.dataset.k),true);});

/* C7 场景 */
charts.scn=mk('c_scn');
reg('c_scn',()=>charts.scn.setOption(growOpt({
 legend:{top:0,textStyle:{color:C.sub,fontSize:10.5},itemWidth:11,itemHeight:8},
 xAxis:Object.assign({type:'category',data:['人形','四足']},axCommon),
 yAxis:Object.assign({type:'value',max:100,name:'%',splitLine},axCommon),
 series:[
  {name:'科研教育',type:'bar',stack:'s',barWidth:'38%',data:[73.60,31.58],itemStyle:{color:C.blue},label:{show:true,formatter:'{c}%',color:'#081423',fontSize:10,fontWeight:700}},
  {name:'商业消费',type:'bar',stack:'s',data:[17.39,42.30],itemStyle:{color:C.blue2},label:{show:true,formatter:'{c}%',color:'#fff',fontSize:10}},
  {name:'行业应用',type:'bar',stack:'s',data:[9.01,26.12],itemStyle:{color:C.gold},label:{show:true,formatter:'{c}%',color:'#081423',fontSize:10}}
 ]})));

/* C8 研发 */
charts.rd=mk('c_rd');
reg('c_rd',()=>charts.rd.setOption(growOpt({xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:[Object.assign({type:'value',name:'亿元',splitLine},axCommon),Object.assign({type:'value',name:'费率%',splitLine:{show:false},max:40,interval:10},axCommon)],
 series:[
  {type:'bar',barWidth:'42%',data:[0.50,0.70,1.45],itemStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#9CC4E4'},{offset:1,color:C.blue3}]),borderRadius:[3,3,0,0]},label:{show:true,position:'top',distance:4,color:'#E9F0F7',fontWeight:700}},
  {type:'line',yAxisIndex:1,data:[31.39,17.83,8.53],smooth:true,symbolSize:9,lineStyle:{color:C.gold,width:2.5},itemStyle:{color:C.gold},label:{show:true,position:'top',distance:8,color:C.gold,formatter:'{c}%'}}
 ]},{r:1})));

/* C9 CFO + 负债率 */
charts.cfo=mk('c_cfo');
reg('c_cfo',()=>charts.cfo.setOption(growOpt({xAxis:Object.assign({type:'category',data:yrs},axCommon),
 yAxis:[Object.assign({type:'value',name:'亿元',splitLine},axCommon),Object.assign({type:'value',name:'负债率%',splitLine:{show:false},max:30},axCommon)],
 series:[
  {type:'bar',barWidth:'42%',data:[0.05,1.92,6.70],itemStyle:{color:C.green,borderRadius:[3,3,0,0]},label:{show:true,position:'top',color:'#E9F0F7',fontWeight:700}},
  {type:'line',yAxisIndex:1,data:[23.57,16.19,18.82],smooth:true,symbolSize:9,lineStyle:{color:C.gold,width:2.5},itemStyle:{color:C.gold},label:{show:true,color:C.gold,formatter:'{c}%'}}
 ]},{r:1})));

/* C10 募投 */
charts.mu=mk('c_mu');
reg('c_mu',()=>charts.mu.setOption({animationDuration:1300,grid:{left:78,right:40,top:14,bottom:24},
 tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v+' 亿元'},baseTip),
 xAxis:Object.assign({type:'value',splitLine},axCommon),
 yAxis:Object.assign({type:'category',data:['制造基地','新产品开发','本体研发','模型研发'],inverse:true},axCommon),
 series:[{type:'bar',barWidth:'52%',data:[6.24,4.45,11.10,20.22],
  itemStyle:{color:p=>[C.gold,'rgba(157,178,198,.6)',C.blue2,C.blue][p.dataIndex],borderRadius:[0,4,4,0]},
  label:{show:true,position:'right',color:'#E9F0F7',formatter:'{c} 亿',fontSize:11}}]}));

/* 要点 / 风险 / 判断 */
const bulls=[
 ['全栈自研','电机/控制器/感知算法/整机/具身模型垂直整合，支撑 60.13% 毛利率与主动降价空间'],
 ['出货领先','2025 人形确认收入 5,215 台、公司称纯人形出货超 5,500 台全球第一；四足三年超 3.3 万台'],
 ['产销顺畅','2025 年前三季度人形产销率超 95%，基本满产满销'],
 ['价格带下探','人形单价降至 16.64 万元、G1 进入 10 万元级，扩大装机与开发者生态'],
 ['资金弹药','低杠杆、经营现金流为正；IPO 募资净额 59.17 亿元支撑研发与制造投入']];
const risks=[
 ['商业化场景集中','人形 2025 1–9M 约 73.6% 收入来自科研教育，行业应用仅约 9.01%'],
 ['价格下行/竞争','两类产品单价逐年走低，价格战或进一步压缩单价与毛利'],
 ['股份支付扰动','2025 非经常性净损失 -3.13 亿，后续激励或继续扰动归母'],
 ['费用扩张','2026H1 扣非 -19.34%、CFO -32.53%，费用刚性下利润率承压'],
 ['高估值波动','发行市值 609.93 亿、媒体口径 PE 219.23 倍（待核），对兑现高度敏感'],
 ['外包/供应链/外销','劳务外包升至 6,802.65 万；境外占 43.65%，汇率与供应链风险并存']];
const judges=[
 ['高增长但增速换挡','三年营收十倍级、CAGR 约 226.8%；2026H1 增速回落至 +48.54%，进入中高速区间'],
 ['盈利看扣非','2025 扣非 5.91 亿 > 归母 2.78 亿，差异主因 -3.13 亿股份支付等非经常项'],
 ['2026 收入增、扣非承压','H1 营收 +48.54% 但扣非 -19.34%，研发/销售费用扩张吞噬利润弹性'],
 ['人形超四足、量增价减','人形占比升至 51.78%；销量 5→5,215 台，单价 59.34→16.64 万元'],
 ['境内反超境外','境内占比 2025 升至 56.35%，境外 43.65% 仍是重要市场'],
 ['研发绝对额升、费率降','研发 1.45 亿、费率降至 8.53%；募投约 85% 投向研发'],
 ['现金流好、低杠杆','2025 CFO 6.70 亿、CFO/营收 39.43%，资产负债率 18.82%'],
 ['六类风险需盯紧','场景集中、价格战、股份支付、费用扩张、高估值、外包与汇率'],
 ['A/E 严格分列','实际与预测分开呈现，规划产能与业绩预告绝不写成已实现事实']];
document.getElementById('bulls').innerHTML=bulls.map((x,i)=>`<div class="pt g"><div class="n">${i+1}</div><div><div class="h">${x[0]}</div><div class="b">${x[1]}</div></div></div>`).join('');
document.getElementById('risks').innerHTML=risks.map((x,i)=>`<div class="pt r"><div class="n">!</div><div><div class="h">${x[0]}</div><div class="b">${x[1]}</div></div></div>`).join('');
document.getElementById('judges').innerHTML=judges.map((x,i)=>`<div class="j"><div class="jn">JUDGMENT ${String(i+1).padStart(2,'0')}</div><div class="jh">${x[0]}</div><div class="jb">${x[1]}</div></div>`).join('');

/* 首屏营收图随首屏直接渲染 */
reg('c_rev',()=>charts.rev.setOption(optRev()));

/* 滚动：显现 + 懒渲染（其余图在进入视口时已 setOption，仅做 resize 保障）+ count-up */
const io=new IntersectionObserver(es=>es.forEach(e=>{
 if(e.isIntersecting){e.target.classList.add('in');
  if(e.target.dataset&&e.target.dataset.cinit!=='1'){e.target.dataset.cinit='1';}
 }
}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

/* KPI 数字滚动 */
function countUp(el){const target=parseFloat(el.dataset.c),d=parseInt(el.dataset.d||0),t0=performance.now(),dur=1600;
 function step(t){const p=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-p,3);el.textContent=(target*e).toFixed(d);if(p<1)requestAnimationFrame(step);}
 requestAnimationFrame(step);}
const cio=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){countUp(e.target);cio.unobserve(e.target);}}),{threshold:.4});
document.querySelectorAll('[data-c]').forEach(el=>cio.observe(el));
/* 保险：2 秒后强制落到终值，防止后台节流导致动画定格在中途 */
setTimeout(()=>document.querySelectorAll('[data-c]').forEach(el=>el.textContent=parseFloat(el.dataset.c).toFixed(parseInt(el.dataset.d||0))),2100);

/* 进度条 / 导航高亮 / 回到顶部 */
function flushVisible(){document.querySelectorAll('.chart').forEach(el=>{if(R[el.id]){const r=el.getBoundingClientRect();if(r.top<innerHeight*1.1&&r.bottom>-40){R[el.id]();delete R[el.id];}}});}
bindLazy(); flushVisible(); addEventListener('scroll',flushVisible,{passive:true});
setTimeout(flushVisible,400);
/* 首屏粒子网络 */
(function(){const cv=document.getElementById('stars'),ctx=cv.getContext('2d');let W,H,ps;
 function rs(){const r=cv.parentElement.getBoundingClientRect();W=cv.width=r.width*devicePixelRatio;H=cv.height=r.height*devicePixelRatio;
  const n=Math.min(64,Math.floor(W*H/26000*devicePixelRatio));ps=Array.from({length:n},()=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.22*devicePixelRatio,vy:(Math.random()-.5)*.22*devicePixelRatio,r:(Math.random()*1.6+0.6)*devicePixelRatio}));}
 rs();addEventListener('resize',rs);
 (function loop(){ctx.clearRect(0,0,W,H);
  for(const p of ps){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1;
   ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle='rgba(127,178,217,.55)';ctx.fill();}
  for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++){const a=ps[i],b=ps[j],dx=a.x-b.x,dy=a.y-b.y,d=Math.hypot(dx,dy),lim=130*devicePixelRatio;
   if(d<lim){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle='rgba(127,178,217,'+(0.13*(1-d/lim))+')';ctx.lineWidth=devicePixelRatio;ctx.stroke();}}
  requestAnimationFrame(loop);})();})();
const prog=document.getElementById('prog'),topBtn=document.getElementById('top');
const secs=[...document.querySelectorAll('section')];
addEventListener('scroll',()=>{const h=document.documentElement;const sc=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;prog.style.width=sc+'%';
 topBtn.classList.toggle('show',h.scrollTop>700);
 let cur='overview';secs.forEach(s=>{if(s.offsetTop-160<=h.scrollTop)cur=s.id;});
 document.querySelectorAll('.navin a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+cur));});
addEventListener('resize',()=>Object.values(charts).forEach(c=>c&&c.resize()));
</script>
</body></html>'''

html=HTML.replace('__ECHARTS__',ech)
out=ROOT/'宇树科技经营财务交互看板_截至20260830.html'
out.write_text(html,encoding='utf-8')
print('SAVED',out,round(len(html)/1024),'KB')
