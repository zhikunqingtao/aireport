#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_unitree_onepager_ink.py — 宇树科技(688836.SH) 投资人一页纸 · 水墨浪漫中国风版
纯代码排版：HTML+CSS+SVG（SVG坐标由本脚本计算），意境主图 ink_hero.png base64 内嵌。
内容与数字与原版（宇树科技_投资人一页纸.html）逐位一致，唯一数据依据：unitree_excel_spec.md。
输出：宇树科技_投资人一页纸_水墨版.html（1280×1810，供无头Chrome @2x 截图成 2560×3620 PNG）
"""
import base64, math, random

HERO = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a/ink_hero.png"
OUT_HTML = "/Users/guoqingtao/Desktop/AI办公评测/zhikuncode/宇树科技_投资人一页纸_水墨版.html"

# ---------- 水墨色板 ----------
PAPER1 = "#F7F1E3"   # 宣纸米白
PAPER2 = "#FCF8EE"   # 宣纸亮白
INK    = "#24211C"   # 主文字墨色
SUB    = "#6E6759"   # 次要
HQ     = "#3D5A6C"   # 花青
CIN    = "#B03A2E"   # 朱砂（印章/毛利率线/人形/风险饰条点睛）
OCHRE  = "#8B6F47"   # 赭石
LIGHT  = "#A39B8A"   # 淡墨灰
OCH_L  = "#C4B69B"   # 淡赭（组件分段）
BART   = "#3A362F"   # 柱形墨色渐变顶
BARB   = "#6E6759"   # 柱形墨色渐变底
CARD   = "rgba(253,251,244,0.78)"  # 宣纸白卡
BORDER = "#D9CFB9"   # 淡墨卡边框

KAITI = "'Kaiti SC','STKaiti','KaiTi','BiauKai',serif"
SONG  = "'Songti SC','STSong','SimSun',serif"
NUMF  = "'Helvetica Neue','PingFang SC',Arial,sans-serif"
# 数字/拉丁→Helvetica Neue（现代无衬线保可读），中文→宋体：出版级混搭
MIXF  = "'Helvetica Neue','Songti SC','STSong','PingFang SC',serif"

# CSS 纸纹噪点（feTurbulence data-URI，极轻）
NOISE = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
         "width='240' height='240'%3E%3Cfilter id='n'%3E%3CfeTurbulence "
         "type='fractalNoise' baseFrequency='0.85' numOctaves='2' "
         "stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='240' height='240' "
         "filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E\")")

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def stext(x, y, s, size=9.5, fill=INK, anchor="middle", weight="600", fam=None, cls=""):
    """SVG 文本；cls='tick' 标记坐标轴刻度（版式标尺，非数据，自检脚本单列）。"""
    c = ' class="%s"' % cls if cls else ""
    f = fam or NUMF
    return ('<text x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s" font-family="%s" style="font-variant-numeric:tabular-nums"%s>%s</text>'
            % (x, y, size, fill, anchor, weight, f, c, s))

# ============================================================
# 手写感墨迹线条（随机抖动，固定种子可复现）
# ============================================================
def _wobble_pts(w, y, amp, seg, seed, wave=0.0, wavek=7.0):
    rnd = random.Random(seed)
    pts = []
    for i in range(seg + 1):
        x = w * i / seg
        yy = y + wave * math.sin(i / wavek + seed) + rnd.uniform(-amp, amp)
        pts.append((x, yy))
    return pts

def _path(pts):
    return "M" + " L".join("%.1f %.1f" % p for p in pts)

def hero_brush():
    """头图下缘收边：双层不规则墨迹笔触线 + 墨点（一点朱砂点睛）。"""
    w, y = 1280, 9.0
    d1 = _path(_wobble_pts(w, y, 1.7, 110, 20260819, wave=2.0, wavek=9.5))
    d2 = _path(_wobble_pts(w, y + 2.6, 1.2, 110, 688836, wave=1.4, wavek=12.0))
    p = ['<svg width="1280" height="18" viewBox="0 0 1280 18" xmlns="http://www.w3.org/2000/svg">']
    p.append('<path d="%s" fill="none" stroke="#6E6759" stroke-opacity="0.34" '
             'stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>' % d1)
    p.append('<path d="%s" fill="none" stroke="#4A463D" stroke-opacity="0.42" '
             'stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/>' % d2)
    for cx, cy, r, col, op in [(58, 8.2, 2.6, "#4A463D", 0.38), (436, 10.8, 1.7, "#6E6759", 0.4),
                               (903, 7.6, 2.1, "#6E6759", 0.36), (1148, 9.4, 1.6, "#B03A2E", 0.55)]:
        p.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="%.2f"/>' % (cx, cy, r, col, op))
    p.append('</svg>')
    return "".join(p)

def rule_svg(seed, color=LIGHT, op=0.5):
    """节标题下细墨线（100×7 viewBox 拉伸铺满，stroke 用 non-scaling-stroke 保真）。"""
    d = _path(_wobble_pts(100.0, 3.5, 1.7, 70, seed))
    return ('<svg class="rule" viewBox="0 0 100 7" preserveAspectRatio="none" '
            'xmlns="http://www.w3.org/2000/svg"><path d="%s" fill="none" stroke="%s" '
            'stroke-opacity="%.2f" stroke-width="1" vector-effect="non-scaling-stroke" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>' % (d, color, op))

# ============================================================
# 图1：壹·增长轨迹 —— 柱=营业收入(万元,左轴,墨色渐变) + 折线=主营毛利率(%,右轴,朱砂)
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
    p.append('<defs><linearGradient id="gbar" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
             '</linearGradient></defs>' % (BART, BARB))
    for t in ticks_l:                                        # 左轴网格+刻度
        y = yl(t)
        p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-opacity="0.45" stroke-width="0.75"/>' % (L, y, W - Rm, y, LIGHT))
        p.append(stext(L - 7, y + 3, format(t, ","), 8, SUB, "end", "400", NUMF, "tick"))
    for t in ticks_r:                                        # 右轴刻度（朱砂，呼应毛利率线）
        p.append(stext(W - Rm + 7, yr(t) + 3, "%d%%" % t, 8, CIN, "start", "400", NUMF, "tick"))
    p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#8B8474" stroke-width="1"/>' % (L, yl(0), W - Rm, yl(0)))
    for i, (v, lb) in enumerate(zip(rev, rlbl)):             # 柱+数值标签+年份
        x = L + i * gw + (gw - bw) / 2
        y = yl(v); h = yl(0) - y
        p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="url(#gbar)"/>' % (x, y, bw, h))
        p.append(stext(x + bw / 2, y - 7, lb, 9.5, INK, "middle", "700"))
        p.append(stext(L + i * gw + gw / 2, H - 9, years[i], 9, SUB, "middle", "400", SONG))
    pts = [(L + i * gw + gw / 2, yr(v), v) for i, v in enumerate(gm) if v is not None]
    p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>'
             % (" ".join("%.1f,%.1f" % (x, y) for x, y, _ in pts), CIN))
    for x, y, v in pts:                                      # 折线点+毛利率标签
        p.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s" stroke="%s" stroke-width="1.8"/>' % (x, y, PAPER2, CIN))
        p.append(stext(x, y - 9.5, "%.2f%%" % v, 9.5, CIN, "middle", "700"))
    p.append('</svg>')
    return "".join(p)

# ============================================================
# 图2：贰·盈利质量 —— 分组柱：归母(淡墨) vs 扣非(浓墨)（万元，2022–2025）
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
            p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-opacity="0.45" stroke-width="0.75"/>' % (L, yy, W - Rm, yy, LIGHT))
        p.append(stext(L - 7, yy + 3, format(t, ","), 8, SUB, "end", "400", NUMF, "tick"))
    p.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#8B8474" stroke-width="1"/>' % (L, y(0), W - Rm, y(0)))
    for i in range(n):
        x0 = L + i * gw + (gw - pair) / 2
        for j, (v, lb, col) in enumerate([(gm[i], gml[i], LIGHT), (kf[i], kfl[i], INK)]):
            x = x0 + j * (bw + gap)
            y0, y1 = y(max(v, 0)), y(min(v, 0))
            p.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y0, bw, max(y1 - y0, 1.2), col))
            if v >= 0:
                p.append(stext(x + bw / 2, y0 - 6, lb, 8.5, INK, "middle", "700"))
            else:
                p.append(stext(x + bw / 2, y1 + 12, lb, 8.5, SUB, "middle", "700"))
        p.append(stext(L + i * gw + gw / 2, H - 9, years[i], 9, SUB, "middle", "400", SONG))
    p.append('</svg>')
    return "".join(p)

# ============================================================
# 图3：叁·收入结构 —— 3条100%堆叠横条（人形=朱砂/四足=花青/组件=淡赭）
# 宽度按精确占比排布，标签用底稿披露占比；组件及其他为倒算约数（待核验）
# ============================================================
def stacked_bars():
    rows = [
        ("2023", [(1.88, CIN, "", False), (75.78, HQ, "75.78%", True), (22.34, OCH_L, "约22.3%", True)],
                 [("1.88%", 0.0, "l", CIN)]),
        ("2024", [(27.68, CIN, "27.68%", True), (59.47, HQ, "59.47%", True), (12.85, OCH_L, "约12.9%", True)],
                 []),
        ("2025", [(51.78, CIN, "51.78%", True), (41.62, HQ, "41.62%", True), (6.60, OCH_L, "", False)],
                 [("约6.6%", 100.0, "r", OCHRE)]),
    ]
    h = []
    for yr, segs, outs in rows:
        h.append('<div class="srow"><div class="syr">%s</div><div class="swrap">' % yr)
        for lb, pos, side, col in outs:                      # 微小分段的外置标签（段色系+小刻度线）
            st = ("left:%.2f%%" % pos) if side == "l" else ("left:%.2f%%;transform:translateX(-100%%)" % pos)
            h.append('<div class="sout" style="%s;color:%s">%s<i></i></div>' % (st, col, lb))
        h.append('<div class="sbar">')
        for w, col, lb, inside in segs:
            txtcls = "inn" if col == OCH_L else "inw"        # 淡赭上用墨色，深色段用宣纸白
            h.append('<div class="seg" style="width:%.2f%%;background:%s">%s</div>'
                     % (w, col, ('<span class="%s">%s</span>' % (txtcls, lb)) if inside else ""))
        h.append('</div></div></div>')
    return "".join(h)

# ---------- KPI 六卡（内容与原版一致） ----------
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

# ---------- 肆·商业化与研发 4行（内容与原版一致） ----------
FACTS = [
    ("人形收入 <b>73.60%</b> 来自科研教育", "9M2025·申报稿"),
    ("境外收入占比 <b>39.20%</b>（2022–2024 年均 55%+）", "9M2025·申报稿"),
    ("2025 研发费用约 <b>14,500</b> 万元·费率 <b>8.53%</b>", "同业均值 27.92%·9M2025"),
    ("纯双足人形累计下线约 <b>18,000</b> 台", "截至 2026-07·公司官方"),
]
def fact_rows():
    return "".join('<div class="frow"><div class="ftxt">%s</div><div class="fsrc">%s</div></div>' % (t, s) for t, s in FACTS)

# ---------- 伍·发行与市场 5行表（内容与原版一致） ----------
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

def sechead(num, ttl, eng, seed):
    return ('<div class="sechead"><div class="sh1"><span class="sdot"></span>'
            '<span class="sttl">%s · %s</span><span class="seng">%s</span></div>%s</div>'
            % (num, ttl, eng, rule_svg(seed)))

# ============================================================
# HTML 模板（%%TOKEN%% 占位，避免 f-string 与 CSS 花括号冲突）
# ============================================================
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>宇树科技（688836.SH）投资人一页纸 · 水墨版</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1280px; background:#F7F1E3; }
  body { font-family:%%MIXF%%; color:#24211C; font-variant-numeric:tabular-nums;
         -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; }
  .page { width:1280px; height:1810px; overflow:hidden; position:relative;
          display:flex; flex-direction:column;
          background:%%NOISE%%,
            radial-gradient(1150px 520px at 14% -8%, rgba(139,111,71,0.055), rgba(139,111,71,0) 60%),
            radial-gradient(900px 620px at 106% 42%, rgba(61,90,108,0.045), rgba(61,90,108,0) 55%),
            radial-gradient(760px 520px at 52% 110%, rgba(176,58,46,0.028), rgba(176,58,46,0) 62%),
            linear-gradient(158deg, #F7F1E3 0%, #FCF8EE 55%, #F6EFDE 100%); }
  b, strong { font-weight:700; }
  .kval, .ksub, .ival, .ilabel, .ftxt, .fsrc, .btxt, .syr, .seg span, .sout, .kfact, .fmeta, .note, .concl {
    font-family:%%MIXF%%; font-variant-numeric:tabular-nums; }

  /* ---------- 1. 头部 · 水墨意境主图 ---------- */
  .hero { position:relative; height:320px; flex:0 0 320px; overflow:hidden;
          background-image:url("data:image/png;base64,%%HERO%%");
          background-size:cover; background-position:center 38%; }
  .hero::before { content:""; position:absolute; inset:0;
          background:linear-gradient(90deg, rgba(247,241,227,0.93) 0%, rgba(247,241,227,0.72) 22%,
                      rgba(247,241,227,0.20) 46%, rgba(247,241,227,0.05) 66%, rgba(247,241,227,0.14) 100%); }
  .hero::after { content:""; position:absolute; inset:0;
          background:linear-gradient(180deg, rgba(247,241,227,0.42) 0%, rgba(247,241,227,0) 16%,
                      rgba(247,241,227,0) 80%, rgba(252,248,238,0.5) 100%); }
  .kick { position:absolute; left:46px; top:20px; z-index:3; font-family:%%NUMF%%;
          font-size:8.5px; font-weight:600; color:#6E6759; letter-spacing:2.4px; }
  .vtitle { position:absolute; left:66px; top:44px; z-index:3; writing-mode:vertical-rl;
            font-family:%%KAITI%%; font-size:40px; font-weight:700; color:#24211C;
            letter-spacing:13px; line-height:1; }
  .vtitle i { display:block; width:8px; height:8px; background:#B03A2E; border-radius:1px;
              margin:0 auto 12px auto; }
  .vsub { position:absolute; left:34px; top:50px; z-index:3; writing-mode:vertical-rl;
          font-family:%%NUMF%%; font-size:10px; font-weight:500; color:#3D5A6C; letter-spacing:2px; }
  .sealbox { position:absolute; right:44px; bottom:24px; z-index:3; display:flex; align-items:center; }
  .seal { width:38px; height:38px; background:#B03A2E; border-radius:3px; transform:rotate(-2deg);
          display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr 1fr; padding:4.5px;
          position:relative; box-shadow:0 1px 4px rgba(36,33,28,0.25); }
  .seal::after { content:""; position:absolute; left:2.5px; right:2.5px; top:2.5px; bottom:2.5px;
                 border:1px solid rgba(252,248,238,0.9); border-radius:1.5px; pointer-events:none; }
  .seal span { font-family:%%KAITI%%; font-size:12.5px; font-weight:700; color:#FCF8EE;
               display:flex; align-items:center; justify-content:center; line-height:1; }
  .sealnote { margin-left:11px; font-size:9px; color:#24211C; letter-spacing:0.4px;
              background:rgba(247,241,227,0.6); padding:3px 8px; border-radius:2px; }
  .hbrush { position:relative; height:0; z-index:5; margin-top:-9px; }
  .hbrush svg { display:block; position:absolute; left:0; top:0; }

  /* ---------- 头部事实条 ---------- */
  .fstrip { flex:0 0 auto; display:flex; align-items:baseline; justify-content:space-between;
            padding:5px 44px 10px 44px; }
  .kfacts { display:flex; gap:30px; }
  .kfact { font-size:9.5px; color:#6E6759; letter-spacing:0.3px; white-space:nowrap; }
  .kfact b { color:#24211C; font-weight:700; }
  .kfact .sep { color:#A39B8A; margin:0 2px; }
  .fmeta { font-size:8.5px; color:#6E6759; letter-spacing:0.3px; white-space:nowrap; }

  /* ---------- 2. KPI 六卡 ---------- */
  .kpis { flex:0 0 auto; display:flex; gap:12px; padding:8px 44px 4px 44px; }
  .kcard { flex:1; min-width:0; background:%%CARD%%; border:1px solid %%BORDER%%;
           border-top:2px solid #B03A2E; padding:12px 12px 10px 12px; }
  .klabel { font-size:9.5px; color:#6E6759; letter-spacing:0.2px; white-space:nowrap;
            overflow:hidden; text-overflow:ellipsis; }
  .kval { margin-top:8px; font-size:30px; line-height:1; font-weight:700; color:#24211C; white-space:nowrap; }
  .kunit { font-size:12px; font-weight:600; color:#24211C; margin-left:3px; }
  .ksub { margin-top:8px; font-size:8.5px; line-height:1.55; color:#6E6759; }
  .ksub .up { color:#B03A2E; font-weight:700; }

  /* ---------- 主体两栏 ---------- */
  .body { flex:1 1 auto; display:flex; gap:24px; padding:12px 44px 0 44px; min-height:0; }
  .col-l { width:686px; flex:0 0 686px; display:flex; flex-direction:column; }
  .col-r { flex:1; min-width:0; display:flex; flex-direction:column; }
  .sec { margin-bottom:22px; }
  .sechead { margin-bottom:10px; }
  .sh1 { display:flex; align-items:baseline; padding-bottom:6px; }
  .sdot { flex:0 0 auto; width:7px; height:7px; background:#B03A2E; border-radius:1px;
          align-self:center; margin-right:9px; }
  .sttl { font-family:%%KAITI%%; font-size:16px; font-weight:700; color:#24211C; letter-spacing:1.5px; }
  .seng { margin-left:auto; font-family:%%NUMF%%; font-size:8px; font-weight:600;
          color:#A39B8A; letter-spacing:2px; }
  .rule { display:block; width:100%; height:7px; }
  .card { background:%%CARD%%; border:1px solid %%BORDER%%; padding:13px 16px 12px 16px; }
  .legend { display:flex; justify-content:flex-end; gap:16px; font-size:9px; color:#6E6759; margin-bottom:4px; }
  .legend i { display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:-1px; }
  .legend .ln { display:inline-block; width:14px; height:0; border-top:2px solid #B03A2E;
                margin-right:4px; vertical-align:2px; }
  .note { margin-top:8px; font-size:8.5px; line-height:1.6; color:#6E6759; }
  .concl { margin-top:10px; padding:9px 12px; background:rgba(61,90,108,0.07);
           border-left:2px solid #3D5A6C; font-size:10.5px; font-weight:600; color:#24211C; }

  /* ---------- 右栏：堆叠条 ---------- */
  .shead { display:flex; font-size:8.5px; color:#6E6759; margin-bottom:8px; }
  .shead .l { width:40px; flex:0 0 40px; }
  .shead .r { flex:1; text-align:right; letter-spacing:0.3px; }
  .srow { display:flex; align-items:flex-start; margin-bottom:17px; }
  .srow:last-of-type { margin-bottom:10px; }
  .syr { width:40px; flex:0 0 40px; font-size:9.5px; font-weight:700; color:#24211C; padding-top:19px; }
  .swrap { position:relative; flex:1; padding-top:16px; }
  .sbar { display:flex; height:28px; }
  .seg { display:flex; align-items:center; justify-content:center; overflow:hidden; }
  .seg span { font-size:9px; font-weight:700; white-space:nowrap; }
  .seg .inw { color:#FCF8EE; } .seg .inn { color:#24211C; }
  .sout { position:absolute; top:0; font-size:9px; font-weight:700; white-space:nowrap;
          font-family:%%NUMF%%; font-variant-numeric:tabular-nums; }
  .sout i { display:block; width:1px; height:5px; background:currentColor; opacity:0.55; margin:1px auto 0; }
  .slegend { margin-top:4px; padding-top:10px; border-top:1px solid #DDD3BE;
             display:flex; gap:16px; font-size:9px; color:#6E6759; }
  .slegend i { display:inline-block; width:8px; height:8px; margin-right:4px; vertical-align:-1px; }

  /* ---------- 右栏：事实行 / 发行与市场表 ---------- */
  .frow { display:flex; align-items:baseline; justify-content:space-between; gap:10px;
          padding:10.5px 0; border-bottom:1px solid #DDD3BE; }
  .frow:last-child { border-bottom:none; padding-bottom:2px; }
  .frow:first-child { padding-top:2px; }
  .ftxt { font-size:10.5px; color:#24211C; line-height:1.45; }
  .ftxt::before { content:""; display:inline-block; width:4px; height:4px; background:#A39B8A;
                  border-radius:1px; margin-right:7px; vertical-align:2px; }
  .ftxt b { color:#24211C; }
  .fsrc { flex:0 0 auto; font-size:8.5px; color:#6E6759; text-align:right; }
  .irow { display:flex; align-items:baseline; justify-content:space-between; gap:10px;
          padding:10.5px 0; border-bottom:1px solid #DDD3BE; }
  .irow:last-child { border-bottom:none; padding-bottom:2px; }
  .irow:first-child { padding-top:2px; }
  .ilabel { flex:0 0 auto; font-size:10px; color:#6E6759; }
  .ival { font-size:11px; font-weight:700; color:#24211C; text-align:right; }
  .ival .inote { display:block; margin-top:2px; font-size:8.5px; font-weight:400; color:#6E6759; }

  /* ---------- 5. 底部双栏带（亮点=花青饰条 / 风险=朱砂饰条） ---------- */
  .band { flex:0 0 auto; display:flex; gap:24px; padding:2px 44px 0 44px; }
  .bcard { flex:1; background:%%CARD%%; border:1px solid %%BORDER%%; padding:13px 16px 11px 16px; }
  .bcard.hl { border-left:3px solid #3D5A6C; }
  .bcard.rk { border-left:3px solid #B03A2E; }
  .bhead { display:flex; align-items:baseline; padding-bottom:7px; margin-bottom:8px;
           border-bottom:1px solid #DDD3BE; }
  .bhead .sdot.hq { background:#3D5A6C; }
  .bhead .ttl { font-family:%%KAITI%%; font-size:14px; font-weight:700; color:#24211C; letter-spacing:2px; }
  .bhead .eng { margin-left:auto; font-family:%%NUMF%%; font-size:8px; font-weight:600; letter-spacing:2px; }
  .hl .bhead .eng { color:#3D5A6C; } .rk .bhead .eng { color:#B03A2E; }
  .brow { display:flex; align-items:baseline; padding:6px 0; }
  .bnum { flex:0 0 auto; width:15px; height:15px; margin-right:8px; border-radius:50%;
          font-size:9px; font-weight:700; color:#FCF8EE; text-align:center; line-height:15px;
          font-family:%%NUMF%%; font-variant-numeric:tabular-nums; transform:translateY(1px); }
  .bnum.h { background:#3D5A6C; } .bnum.r { background:#B03A2E; }
  .btxt { font-size:10.5px; line-height:1.55; color:#24211C; }
  .btxt b { color:#24211C; }

  /* ---------- 6. 页脚 ---------- */
  .foot { flex:0 0 auto; margin:14px 44px 0 44px; padding:9px 0 13px 0; border-top:1px solid #CFC4AC; }
  .foot p { font-size:8.5px; line-height:1.7; color:#6E6759; }
  .foot p + p { margin-top:7px; padding-top:8px; border-top:1px solid #DDD3BE; }
</style>
</head>
<body>
<div class="page">

  <!-- 1 头部 · 水墨意境主图 -->
  <div class="hero">
    <div class="kick">INVESTOR ONE-PAGER ｜ 投资人一页纸</div>
    <div class="vtitle"><i></i>宇樹科技</div>
    <div class="vsub">UNITREE ROBOTICS ｜ 688836.SH</div>
    <div class="sealbox">
      <div class="seal"><span style="grid-area:1/2">宇</span><span style="grid-area:2/2">树</span><span style="grid-area:1/1">科</span><span style="grid-area:2/1">技</span></div>
      <div class="sealnote">上交所科创板 ｜ 2026-08-19 上市</div>
    </div>
  </div>
  <div class="hbrush">%%HEROBRUSH%%</div>

  <!-- 头部事实条 -->
  <div class="fstrip">
    <div class="kfacts">
      <div class="kfact">公司成立 <b>2016</b></div>
      <div class="kfact">员工 <b>480</b> 人 <span class="sep">·</span> 研发 <b>175</b> 人（2025-09）</div>
      <div class="kfact">专利权 <b>262</b> 项（截至 2026-01）</div>
    </div>
    <div class="fmeta">投资人一页纸速览 ｜ 资料截止：2026年8月30日 ｜ 单位：人民币万元（另有注明除外）</div>
  </div>

  <!-- 2 KPI 六卡 -->
  <div class="kpis">%%KPIS%%</div>

  <!-- 3+4 主体两栏 -->
  <div class="body">
    <div class="col-l">
      <div class="sec">
        %%SEC1%%
        <div class="card">
          <div class="legend"><span><i style="background:#4A463D"></i>营业收入（万元）</span><span><span class="ln"></span>主营毛利率（%，右轴）</span></div>
          %%CHART1%%
          <div class="note">注：营业收入 2022 / 2024 为约数（2024 系按 2025 年 +332.64% 倒算，待核验）；2022 为申报稿口径，2023–2025 为注册稿口径。</div>
          <div class="concl">2023–2025 营收 CAGR 约 226.8%；2026H1 营收约 115,200 万元（+48.54%·上市公告书口径）</div>
        </div>
      </div>
      <div class="sec">
        %%SEC2%%
        <div class="card">
          <div class="legend"><span><i style="background:#A39B8A"></i>归母净利润</span><span><i style="background:#24211C"></i>扣非归母净利润</span></div>
          %%CHART2%%
          <div class="note">注：2025 年归母低于扣非约 31,254 万元，系一次性股份支付 34,906.55 万元计入管理费用（非经常性）；2025 年经营现金流净额约 67,000 万元＞扣非净利；2026H1 扣非约 24,400 万元（-19.34%）。2022 为申报稿口径（扣非为约数）。</div>
        </div>
      </div>
    </div>
    <div class="col-r">
      <div class="sec">
        %%SEC3%%
        <div class="card">
          <div class="shead"><div class="l"></div><div class="r">占主营业务收入比重（%，注册稿口径）</div></div>
          %%STACKED%%
          <div class="slegend"><span><i style="background:#B03A2E"></i>人形机器人</span><span><i style="background:#3D5A6C"></i>四足机器人</span><span><i style="background:#C4B69B"></i>组件及其他</span></div>
          <div class="note">注：组件及其他占比为倒算约数（待核验）。</div>
        </div>
      </div>
      <div class="sec">
        %%SEC4%%
        <div class="card">%%FACTS%%</div>
      </div>
      <div class="sec">
        %%SEC5%%
        <div class="card">%%IPO%%</div>
      </div>
    </div>
  </div>

  <!-- 5 底部双栏带 -->
  <div class="band">
    <div class="bcard hl">
      <div class="bhead"><span class="sdot hq"></span><span class="ttl">投资亮点</span><span class="eng">INVESTMENT HIGHLIGHTS</span></div>
      %%HLS%%
    </div>
    <div class="bcard rk">
      <div class="bhead"><span class="sdot"></span><span class="ttl">风险提示</span><span class="eng">KEY RISKS</span></div>
      %%RISKS%%
    </div>
  </div>

  <!-- 6 页脚 -->
  <div class="foot">
    <p>资料来源：招股说明书（注册稿/申报稿）、上市公告书（2026-08-18）、上交所 688836 公告列表（2026-08-30 核验）、赛迪顾问、国新办中外记者见面会（2025-07-15）、新华社/证券时报/第一财经/长江商报等公开报道（2026-03 至 2026-08）</p>
    <p>口径：金额单位为人民币万元；注册稿为主、申报稿补充；2026H1 数据取自上市公告书（正式半年报截至 2026-08-30 未披露）；标注“约/待核验”数据为约数、倒算或单一来源。本材料基于公开信息整理，不构成投资建议。头图由 AI 生成，仅作装饰。</p>
  </div>

</div>
</body>
</html>
"""

def main():
    html = (TPL
            .replace("%%HERO%%", b64(HERO))
            .replace("%%MIXF%%", MIXF)
            .replace("%%NUMF%%", NUMF)
            .replace("%%KAITI%%", KAITI)
            .replace("%%NOISE%%", NOISE)
            .replace("%%CARD%%", CARD)
            .replace("%%BORDER%%", BORDER)
            .replace("%%HEROBRUSH%%", hero_brush())
            .replace("%%KPIS%%", kpi_cards())
            .replace("%%SEC1%%", sechead("壹", "增长轨迹：营收与毛利率", "GROWTH TRAJECTORY", 11))
            .replace("%%SEC2%%", sechead("贰", "盈利质量：归母 vs 扣非（万元）", "EARNINGS QUALITY", 23))
            .replace("%%SEC3%%", sechead("叁", "收入结构：人形接棒", "REVENUE MIX", 37))
            .replace("%%SEC4%%", sechead("肆", "商业化与研发", "COMMERCIALIZATION &amp; R&amp;D", 41))
            .replace("%%SEC5%%", sechead("伍", "发行与市场", "IPO &amp; SECONDARY MARKET", 53))
            .replace("%%CHART1%%", chart_growth())
            .replace("%%CHART2%%", chart_profit())
            .replace("%%STACKED%%", stacked_bars())
            .replace("%%FACTS%%", fact_rows())
            .replace("%%IPO%%", ipo_rows())
            .replace("%%HLS%%", band_items(HIGHLIGHTS, "h"))
            .replace("%%RISKS%%", band_items(RISKS, "r")))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("written:", OUT_HTML, "%.1f KB" % (len(html.encode("utf-8")) / 1024))

if __name__ == "__main__":
    main()
