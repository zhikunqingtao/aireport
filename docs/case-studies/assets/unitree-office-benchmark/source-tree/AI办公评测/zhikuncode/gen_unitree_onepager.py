#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_unitree_onepager.py — 宇树科技(688836.SH) 投资人一页纸（出版物级 tear-sheet）
纯代码排版：HTML+CSS+SVG（SVG坐标由本脚本计算），封面图 base64 内嵌。
数据唯一依据：unitree_excel_spec.md（已核验底稿）。所有数值与底稿逐位一致。
输出：宇树科技_投资人一页纸.html（1280×1810，供无头Chrome @2x 截图成 2560×3620 PNG）
"""
import base64, os

COVER = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a/ppt_cover.png"
OUT_HTML = "/Users/guoqingtao/Desktop/AI办公评测/zhikuncode/宇树科技_投资人一页纸.html"

# ---------- 色板（严格执行设计规范） ----------
NAVY = "#0A1F44"   # 深海军蓝主色
CYAN = "#19C2FF"   # 科技青强调
PAPER = "#FFFFFF"  # 纸面白
DIV = "#E5EAF2"    # 浅灰蓝分隔
INK = "#23324D"    # 正文
SUB = "#6B7A90"    # 次要
POS = "#17B890"    # 正向
WARN = "#E8543F"   # 警示
GB = "#8FA3BF"     # 灰蓝（第三系列）

NUMF = "'Helvetica Neue','PingFang SC',Arial,'Microsoft YaHei',sans-serif"

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def stext(x, y, s, size=9.5, fill=INK, anchor="middle", weight="600", cls=""):
    """SVG 文本；cls='tick' 标记坐标轴刻度（版式标尺，非数据，自检脚本单列）。"""
    c = ' class="%s"' % cls if cls else ""
    return ('<text x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s" font-family="%s" style="font-variant-numeric:tabular-nums"%s>%s</text>'
            % (x, y, size, fill, anchor, weight, NUMF, c, s))

# ============================================================
# 图1：增长轨迹 —— 柱=营业收入(万元,左轴) + 折线=主营毛利率(%,右轴,2023–2025)
# ============================================================
def chart_growth():
    W, H = 654, 370
    L, Rm, T, B = 48, 36, 24, 30
    pw, ph = W - L - Rm, H - T - B
    vmax_l, ticks_l = 250000, [0, 50000, 100000, 150000, 200000, 250000]
    vmax_r, ticks_r = 80, [0, 20, 40, 60, 80]
    yl = lambda v: T + ph * (1 - v / vmax_l)
    yr = lambda v: T + ph * (1 - v / vmax_r)
    years  = ["2022", "2023", "2024", "2025"]
    rev    = [12300, 15913.44, 39276.6, 169926.93]           # 万元（2022/2024为约数）
    rlbl   = ["约12,300", "15,913.44", "约39,276.6", "169,926.93"]
    gm     = [None, 44.22, 56.74, 60.13]                     # 主营毛利率 %
    n = 4; gw = pw / n; bw = 60
    p = ['<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    for t in ticks_l:                                        # 左轴网格+刻度
        y = yl(t)
        p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (L, y, W - Rm, y, DIV))
        p.append(stext(L - 7, y + 3, format(t, ","), 8, SUB, "end", "400", "tick"))
    for t in ticks_r:                                        # 右轴刻度（青）
        p.append(stext(W - Rm + 7, yr(t) + 3, "%d%%" % t, 8, CYAN, "start", "400", "tick"))
    p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.4"/>' % (L, yl(0), W - Rm, yl(0), GB))
    for i, (v, lb) in enumerate(zip(rev, rlbl)):             # 柱+数值标签+年份
        x = L + i * gw + (gw - bw) / 2
        y = yl(v); h = yl(0) - y
        p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y, bw, h, NAVY))
        p.append(stext(x + bw / 2, y - 7, lb, 9.5, NAVY, "middle", "700"))
        p.append(stext(L + i * gw + gw / 2, H - 9, years[i], 9.5, SUB, "middle", "400"))
    pts = [(L + i * gw + gw / 2, yr(v), v) for i, v in enumerate(gm) if v is not None]
    p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2"/>'
             % (" ".join("%.1f,%.1f" % (x, y) for x, y, _ in pts), CYAN))
    for x, y, v in pts:                                      # 折线点+毛利率标签
        p.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="#FFFFFF" stroke="%s" stroke-width="2"/>' % (x, y, CYAN))
        p.append(stext(x, y - 9.5, "%.2f%%" % v, 9.5, CYAN, "middle", "700"))
    p.append('</svg>')
    return "".join(p)

# ============================================================
# 图2：盈利质量 —— 分组柱：归母净利润 vs 扣非归母净利润（万元，2022–2025）
# ============================================================
def chart_profit():
    W, H = 654, 356
    L, Rm, T, B = 48, 12, 20, 30
    pw, ph = W - L - Rm, H - T - B
    vmin, vmax = -8000, 64000
    rng = vmax - vmin
    y = lambda v: T + ph * (vmax - v) / rng
    ticks = [0, 20000, 40000, 60000]
    years = ["2022", "2023", "2024", "2025"]
    gm  = [-2210.05, -1114.51, 9547.47, 27821.05]            # 归母
    kf  = [-807, -1801.91, 7847.65, 59075.28]                # 扣非（2022约）
    gml = ["-2,210.05", "-1,114.51", "9,547.47", "27,821.05"]
    kfl = ["约-807", "-1,801.91", "7,847.65", "59,075.28"]
    n = 4; gw = pw / n; bw = 44; gap = 12; pair = 2 * bw + gap
    p = ['<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">' % (W, H, W, H)]
    for t in ticks:
        yy = y(t)
        if t > 0:
            p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (L, yy, W - Rm, yy, DIV))
        p.append(stext(L - 7, yy + 3, format(t, ","), 8, SUB, "end", "400", "tick"))
    p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.4"/>' % (L, y(0), W - Rm, y(0), GB))
    for i in range(n):
        x0 = L + i * gw + (gw - pair) / 2
        for j, (v, lb, col) in enumerate([(gm[i], gml[i], NAVY), (kf[i], kfl[i], CYAN)]):
            x = x0 + j * (bw + gap)
            y0, y1 = y(max(v, 0)), y(min(v, 0))
            p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y0, bw, max(y1 - y0, 1.2), col))
            if v >= 0:
                p.append(stext(x + bw / 2, y0 - 6, lb, 8.5, INK, "middle", "700"))
            else:
                p.append(stext(x + bw / 2, y1 + 12, lb, 8.5, SUB, "middle", "700"))
        p.append(stext(L + i * gw + gw / 2, H - 9, years[i], 9.5, SUB, "middle", "400"))
    p.append('</svg>')
    return "".join(p)

# ============================================================
# 图3：收入结构 —— 3条100%堆叠横条（人形/四足/组件及其他）
# 宽度按精确占比排布，标签用底稿披露占比；组件及其他为倒算约数（待核验）
# ============================================================
def stacked_bars():
    rows = [
        ("2023", [(1.88, CYAN, "", False), (75.78, NAVY, "75.78%", True), (22.34, GB, "约22.3%", True)],
                 [("1.88%", 0.0, "l", CYAN)]),
        ("2024", [(27.68, CYAN, "27.68%", True), (59.47, NAVY, "59.47%", True), (12.85, GB, "约12.9%", True)],
                 []),
        ("2025", [(51.78, CYAN, "51.78%", True), (41.62, NAVY, "41.62%", True), (6.60, GB, "", False)],
                 [("约6.6%", 100.0, "r", GB)]),
    ]
    h = []
    for yr, segs, outs in rows:
        h.append('<div class="srow"><div class="syr">%s</div><div class="swrap">' % yr)
        for lb, pos, side, col in outs:                      # 微小分段的外置标签（段色+小刻度线）
            st = ("left:%.2f%%" % pos) if side == "l" else ("left:%.2f%%;transform:translateX(-100%%)" % pos)
            h.append('<div class="sout" style="%s;color:%s">%s<i></i></div>' % (st, col, lb))
        h.append('<div class="sbar">')
        for w, col, lb, inside in segs:
            txtcls = "inn" if col == CYAN else "inw"
            h.append('<div class="seg" style="width:%.2f%%;background:%s">%s</div>'
                     % (w, col, ('<span class="%s">%s</span>' % (txtcls, lb)) if inside else ""))
        h.append('</div></div></div>')
    return "".join(h)

# ---------- KPI 卡 ----------
KPIS = [
    ("2025年营业收入（万元）", "169,926.93", "", '<span class="up">+332.64%</span> 同比（注册稿口径）'),
    ("2025年扣非归母净利润（万元）", "59,075.28", "", '归母净利润 27,821.05 万元'),
    ("主营业务毛利率", "60.13", "%", '2023年 44.22% → 2024年 56.74%'),
    ("2025人形机器人出货", "超 5,500", "台", '全球第一·份额 32.4%（赛迪顾问·机构数据）'),
    ("四足机器人全球份额", "60–70", "%", '王兴兴国新办表态·管理层口径（2025-07-15）'),
    ("发行市值", "609.93", "亿元", '发行价 150.80 元 × 总股本 40,446.4340 万股'),
]

def kpi_cards():
    h = []
    for label, val, unit, sub in KPIS:
        u = '<span class="kunit">%s</span>' % unit if unit else ""
        h.append('<div class="kcard"><div class="klabel">%s</div>'
                 '<div class="kval">%s%s</div><div class="ksub">%s</div></div>' % (label, val, u, sub))
    return "".join(h)

# ---------- 商业化与研发 4行 ----------
FACTS = [
    ("人形收入 <b>73.60%</b> 来自科研教育", "9M2025·申报稿"),
    ("境外收入占比 <b>39.20%</b>（2022–2024 年均 55%+）", "9M2025·申报稿"),
    ("2025 研发费用约 <b>14,500</b> 万元·费率 <b>8.53%</b>", "同业均值 27.92%·9M2025"),
    ("纯双足人形累计下线约 <b>18,000</b> 台", "截至 2026-07·公司官方"),
]
def fact_rows():
    return "".join('<div class="frow"><div class="ftxt">%s</div><div class="fsrc">%s</div></div>' % (t, s) for t, s in FACTS)

# ---------- IPO 与二级市场表 ----------
IPO_ROWS = [
    ("发行价 ｜ 募资总额", "150.80 元 ｜ 609,932.22 万元", ""),
    ("发行市盈率", "219.23 倍", "行业均值 38.56 倍"),
    ("上市首日收盘", "+460.34%", "收盘市值 3,417.72 亿元"),
    ("2026-08-31 收盘市值", "约 2,285 亿元", "二级市场数据·略晚于截止日"),
    ("网上中签率", "0.01809759%", "科创板新低"),
]
def ipo_rows():
    h = []
    for lb, val, note in IPO_ROWS:
        n = '<span class="inote">%s</span>' % note if note else ""
        h.append('<div class="irow"><div class="ilabel">%s</div><div class="ival">%s%s</div></div>' % (lb, val, n))
    return "".join(h)

HIGHLIGHTS = [
    "营收三年 CAGR 约 <b>226.8%</b>，2026H1 仍 <b>+48.54%</b>",
    "人形出货<b>全球第一</b>，收入结构切换完成",
    "毛利率 <b>60.13%</b>，经营现金流为正",
]
RISKS = [
    "发行 PE <b>219.23 倍</b>；8月底对应 2025 归母 PE 约 <b>821 倍</b>（二级市场数据）",
    "2026H1 扣非 <b>-19.34%</b>，费用高速扩张",
    "科教客户集中 <b>73.60%</b>；美国 FCC 禁令（2026-07-28）",
]
def band_items(items, sym_cls):
    return "".join('<div class="brow"><span class="bnum %s">%d</span><span class="btxt">%s</span></div>'
                   % (sym_cls, i + 1, t) for i, t in enumerate(items))

# ============================================================
# HTML 模板（%%TOKEN%% 占位，避免 f-string 与 CSS 花括号冲突）
# ============================================================
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>宇树科技（688836.SH）投资人一页纸</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1280px; background:#FFFFFF; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; color:#23324D;
         -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; }
  .page { width:1280px; height:1810px; background:#FFFFFF; overflow:hidden;
          display:flex; flex-direction:column; }
  b, strong { font-weight:700; }
  .num, .kval, .ksub, .ival, .ilabel, .ftxt, .fsrc, .btxt, .syr, .seg span, .sout, .kfact b, .kfact span {
    font-family:'Helvetica Neue','PingFang SC',Arial,'Microsoft YaHei',sans-serif;
    font-variant-numeric:tabular-nums; }

  /* ---------- 1. 头部主视觉带 ---------- */
  .hero { position:relative; height:300px; flex:0 0 300px; overflow:hidden;
          background-image:url("data:image/png;base64,%%COVER%%");
          background-size:cover; background-position:82% 38%; }
  .hero::before { content:""; position:absolute; inset:0;
          background:linear-gradient(100deg, rgba(10,31,68,0.97) 0%, rgba(10,31,68,0.88) 30%,
                      rgba(10,31,68,0.52) 58%, rgba(10,31,68,0.14) 100%); }
  .hero-in { position:absolute; inset:0; padding:40px 44px 0 44px; display:flex; }
  .hero-l { flex:1; }
  .kicker { font-size:10.5px; font-weight:700; color:#19C2FF; letter-spacing:2.5px; }
  .hero h1 { margin-top:10px; font-size:26px; font-weight:700; color:#FFFFFF; letter-spacing:0.5px; }
  .hero .sub { margin-top:9px; font-size:11px; color:rgba(255,255,255,0.88); letter-spacing:0.4px;
               font-family:'Helvetica Neue','PingFang SC',Arial,sans-serif; font-variant-numeric:tabular-nums; }
  .hero-r { width:300px; padding-top:34px; text-align:right; }
  .hf { padding:7px 0 7px 0; border-bottom:1px solid rgba(255,255,255,0.22); }
  .hf:first-child { border-top:1px solid rgba(255,255,255,0.22); }
  .hf b { display:block; font-size:13px; font-weight:700; color:#FFFFFF;
          font-family:'Helvetica Neue','PingFang SC',Arial,sans-serif; font-variant-numeric:tabular-nums; }
  .hf span { display:block; margin-top:2px; font-size:9px; color:rgba(255,255,255,0.72); letter-spacing:0.3px; }
  .hero-foot { position:absolute; left:44px; right:44px; bottom:13px; padding-top:8px;
               border-top:1px solid rgba(255,255,255,0.25);
               font-size:9px; color:rgba(255,255,255,0.75); letter-spacing:0.3px; }

  /* ---------- 2. KPI 带 ---------- */
  .kpis { flex:0 0 auto; display:flex; gap:12px; padding:22px 44px 6px 44px; }
  .kcard { flex:1; min-width:0; background:#FFFFFF; border:1px solid #E5EAF2; border-top:2px solid #19C2FF;
           padding:13px 12px 11px 12px; }
  .klabel { font-size:9.5px; color:#6B7A90; letter-spacing:0.2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .kval { margin-top:8px; font-size:30px; line-height:1; font-weight:700; color:#0A1F44; white-space:nowrap; }
  .kunit { font-size:12px; font-weight:600; color:#23324D; margin-left:3px; }
  .ksub { margin-top:9px; font-size:9px; line-height:1.5; color:#6B7A90; }
  .ksub .up { color:#17B890; font-weight:700; }

  /* ---------- 主体两栏 ---------- */
  .body { flex:1 1 auto; display:flex; gap:26px; padding:18px 44px 0 44px; min-height:0; }
  .col-l { width:686px; flex:0 0 686px; display:flex; flex-direction:column; }
  .col-r { flex:1; min-width:0; display:flex; flex-direction:column; }
  .sec { margin-bottom:26px; }
  .sechead { border-bottom:1px solid #E5EAF2; padding-bottom:8px; margin-bottom:12px; }
  .sechead .kick { font-size:10.5px; font-weight:700; color:#19C2FF; letter-spacing:2px; }
  .sechead .ttl { margin-top:3px; font-size:14px; font-weight:700; color:#0A1F44; letter-spacing:0.3px; }
  .card { background:#FFFFFF; border:1px solid #E5EAF2; padding:15px 18px 14px 18px; }
  .legend { display:flex; justify-content:flex-end; gap:16px; font-size:9px; color:#6B7A90; margin-bottom:4px; }
  .legend i { display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:-1px; }
  .legend .ln { display:inline-block; width:14px; height:0; border-top:2.2px solid #19C2FF; margin-right:4px; vertical-align:2px; }
  .note { margin-top:10px; font-size:9px; line-height:1.6; color:#6B7A90; }
  .concl { margin-top:12px; padding:10px 12px; background:rgba(229,234,242,0.42); border-left:2px solid #19C2FF;
           font-size:11px; font-weight:600; color:#0A1F44; font-variant-numeric:tabular-nums; }

  /* ---------- 右栏：堆叠条 ---------- */
  .shead { display:flex; font-size:8.5px; color:#6B7A90; margin-bottom:8px; }
  .shead .l { width:40px; flex:0 0 40px; }
  .shead .r { flex:1; text-align:right; letter-spacing:0.3px; }
  .srow { display:flex; align-items:flex-start; margin-bottom:17px; }
  .srow:last-of-type { margin-bottom:10px; }
  .syr { width:40px; flex:0 0 40px; font-size:9.5px; font-weight:700; color:#0A1F44; padding-top:19px; }
  .swrap { position:relative; flex:1; padding-top:16px; }
  .sbar { display:flex; height:28px; }
  .seg { display:flex; align-items:center; justify-content:center; overflow:hidden; }
  .seg span { font-size:9px; font-weight:700; white-space:nowrap; }
  .seg .inw { color:#FFFFFF; } .seg .inn { color:#0A1F44; }
  .sout { position:absolute; top:0; font-size:9px; font-weight:700; white-space:nowrap;
          font-family:'Helvetica Neue',Arial,sans-serif; font-variant-numeric:tabular-nums; }
  .sout i { display:block; width:1px; height:5px; background:currentColor; opacity:0.55; margin:1px auto 0; }
  .slegend { margin-top:4px; padding-top:10px; border-top:1px solid #E5EAF2;
             display:flex; gap:16px; font-size:9px; color:#6B7A90; }
  .slegend i { display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:-1px; }

  /* ---------- 右栏：事实行 / IPO表 ---------- */
  .frow { display:flex; align-items:baseline; justify-content:space-between; gap:10px;
          padding:11.5px 0; border-bottom:1px solid #E5EAF2; }
  .frow:last-child { border-bottom:none; padding-bottom:2px; }
  .frow:first-child { padding-top:2px; }
  .ftxt { font-size:10.5px; color:#23324D; line-height:1.45; }
  .ftxt b { color:#0A1F44; }
  .fsrc { flex:0 0 auto; font-size:8.5px; color:#6B7A90; text-align:right; }
  .irow { display:flex; align-items:baseline; justify-content:space-between; gap:10px;
          padding:11.5px 0; border-bottom:1px solid #E5EAF2; }
  .irow:last-child { border-bottom:none; padding-bottom:2px; }
  .irow:first-child { padding-top:2px; }
  .ilabel { flex:0 0 auto; font-size:10px; color:#6B7A90; }
  .ival { font-size:11px; font-weight:700; color:#0A1F44; text-align:right; }
  .ival .inote { display:block; margin-top:2px; font-size:8.5px; font-weight:400; color:#6B7A90; }

  /* ---------- 5. 底部双栏带 ---------- */
  .band { flex:0 0 auto; display:flex; gap:26px; padding:4px 44px 0 44px; }
  .bcard { flex:1; background:#FFFFFF; border:1px solid #E5EAF2; padding:15px 18px 13px 18px; }
  .bcard.hl { border-left:3px solid #19C2FF; }
  .bcard.rk { border-left:3px solid #E8543F; }
  .bhead { display:flex; align-items:baseline; gap:10px; margin-bottom:10px; }
  .bhead .kick { font-size:10.5px; font-weight:700; letter-spacing:2px; }
  .hl .bhead .kick { color:#19C2FF; } .rk .bhead .kick { color:#E8543F; }
  .bhead .ttl { font-size:13px; font-weight:700; color:#0A1F44; }
  .brow { display:flex; align-items:baseline; padding:6.5px 0; }
  .bnum { flex:0 0 auto; width:15px; height:15px; margin-right:8px; border-radius:50%;
          font-size:9px; font-weight:700; color:#FFFFFF; text-align:center; line-height:15px;
          font-family:'Helvetica Neue',Arial,sans-serif; transform:translateY(1px); }
  .bnum.c { background:#19C2FF; } .bnum.o { background:#E8543F; }
  .btxt { font-size:10.5px; line-height:1.55; color:#23324D; }
  .btxt b { color:#0A1F44; }

  /* ---------- 6. 页脚 ---------- */
  .foot { flex:0 0 auto; margin:16px 44px 0 44px; padding:10px 0 14px 0; border-top:1px solid #E5EAF2; }
  .foot p { font-size:9px; line-height:1.7; color:#6B7A90; }
  .foot p + p { margin-top:7px; padding-top:8px; border-top:1px solid #E5EAF2; }
</style>
</head>
<body>
<div class="page">

  <!-- 1 头部主视觉带 -->
  <div class="hero">
    <div class="hero-in">
      <div class="hero-l">
        <div class="kicker">INVESTOR ONE-PAGER ｜ 投资人一页纸</div>
        <h1>宇树科技 UNITREE ROBOTICS</h1>
        <div class="sub">688836.SH ｜ 上交所科创板 ｜ 2026-08-19 上市</div>
      </div>
      <div class="hero-r">
        <div class="hf"><b>2016</b><span>公司成立</span></div>
        <div class="hf"><b>480 人 · 175 人</b><span>员工 · 研发（2025-09）</span></div>
        <div class="hf"><b>262 项</b><span>专利权（截至 2026-01）</span></div>
      </div>
    </div>
    <div class="hero-foot">投资人一页纸速览 ｜ 资料截止：2026年8月30日 ｜ 单位：人民币万元（另有注明除外） ｜ 头图由 AI 生成，仅作装饰</div>
  </div>

  <!-- 2 KPI 带 -->
  <div class="kpis">%%KPIS%%</div>

  <!-- 3+4 主体两栏 -->
  <div class="body">
    <div class="col-l">
      <div class="sec">
        <div class="sechead"><div class="kick">GROWTH TRAJECTORY</div><div class="ttl">增长轨迹：营收与毛利率</div></div>
        <div class="card">
          <div class="legend"><span><i style="background:#0A1F44"></i>营业收入（万元）</span><span><span class="ln"></span>主营毛利率（%，右轴）</span></div>
          %%CHART1%%
          <div class="note">注：营业收入 2022 / 2024 为约数（2024 系按 2025 年 +332.64% 倒算，待核验）；2022 为申报稿口径，2023–2025 为注册稿口径。</div>
          <div class="concl">2023–2025 营收 CAGR 约 226.8%；2026H1 营收约 115,200 万元（+48.54%·上市公告书口径）</div>
        </div>
      </div>
      <div class="sec">
        <div class="sechead"><div class="kick">EARNINGS QUALITY</div><div class="ttl">盈利质量：归母 vs 扣非（万元）</div></div>
        <div class="card">
          <div class="legend"><span><i style="background:#0A1F44"></i>归母净利润</span><span><i style="background:#19C2FF"></i>扣非归母净利润</span></div>
          %%CHART2%%
          <div class="note">注：2025 年归母低于扣非约 31,254 万元，系一次性股份支付 34,906.55 万元计入管理费用（非经常性）；2025 年经营现金流净额约 67,000 万元＞扣非净利；2026H1 扣非约 24,400 万元（-19.34%）。2022 为申报稿口径（扣非为约数）。</div>
        </div>
      </div>
    </div>
    <div class="col-r">
      <div class="sec">
        <div class="sechead"><div class="kick">REVENUE MIX</div><div class="ttl">收入结构：人形接棒</div></div>
        <div class="card">
          <div class="shead"><div class="l"></div><div class="r">占主营业务收入比重（%，注册稿口径）</div></div>
          %%STACKED%%
          <div class="slegend"><span><i style="background:#19C2FF"></i>人形机器人</span><span><i style="background:#0A1F44"></i>四足机器人</span><span><i style="background:#8FA3BF"></i>组件及其他</span></div>
          <div class="note">注：组件及其他占比为倒算约数（待核验）。</div>
        </div>
      </div>
      <div class="sec">
        <div class="sechead"><div class="kick">COMMERCIALIZATION &amp; R&amp;D</div><div class="ttl">商业化与研发</div></div>
        <div class="card">%%FACTS%%</div>
      </div>
      <div class="sec">
        <div class="sechead"><div class="kick">IPO &amp; SECONDARY MARKET</div><div class="ttl">IPO 与二级市场</div></div>
        <div class="card">%%IPO%%</div>
      </div>
    </div>
  </div>

  <!-- 5 底部双栏带 -->
  <div class="band">
    <div class="bcard hl">
      <div class="bhead"><span class="kick">INVESTMENT HIGHLIGHTS</span><span class="ttl">投资亮点</span></div>
      %%HLS%%
    </div>
    <div class="bcard rk">
      <div class="bhead"><span class="kick">KEY RISKS</span><span class="ttl">风险提示</span></div>
      %%RISKS%%
    </div>
  </div>

  <!-- 6 页脚 -->
  <div class="foot">
    <p>资料来源：招股说明书（注册稿/申报稿）、上市公告书（2026-08-18）、上交所 688836 公告列表（2026-08-30 核验）、赛迪顾问、国新办中外记者见面会（2025-07-15）、新华社/证券时报/第一财经/长江商报等公开报道（2026-03 至 2026-08）</p>
    <p>口径：金额单位为人民币万元；注册稿为主、申报稿补充；2026H1 数据取自上市公告书（正式半年报截至 2026-08-30 未披露）；标注“约/待核验”数据为约数、倒算或单一来源。本材料基于公开信息整理，不构成投资建议。</p>
  </div>

</div>
</body>
</html>
"""

def main():
    html = (TPL
            .replace("%%COVER%%", b64(COVER))
            .replace("%%KPIS%%", kpi_cards())
            .replace("%%CHART1%%", chart_growth())
            .replace("%%CHART2%%", chart_profit())
            .replace("%%STACKED%%", stacked_bars())
            .replace("%%FACTS%%", fact_rows())
            .replace("%%IPO%%", ipo_rows())
            .replace("%%HLS%%", band_items(HIGHLIGHTS, "c"))
            .replace("%%RISKS%%", band_items(RISKS, "o")))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("written:", OUT_HTML, "%.1f KB" % (len(html) / 1024))

if __name__ == "__main__":
    main()
