# -*- coding: utf-8 -*-
"""
宇树科技（688836.SH）公司研究汇报 PPT 生成脚本
数据唯一依据：unitree_excel_spec.md（已核验数据底稿）
设计系统：深海军蓝 #0A1F44 / 科技青 #19C2FF / 浅底 #F7F9FC / 白 #FFFFFF
输出：宇树科技_公司研究汇报.pptx（16:9，15页，全部元素可编辑）
"""
import os
import shutil
import subprocess
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import (XL_CHART_TYPE, XL_LEGEND_POSITION,
                             XL_LABEL_POSITION, XL_MARKER_STYLE)
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.dml import MSO_LINE_DASH_STYLE as MSO_LINE
from pptx.oxml.ns import qn
from lxml import etree

def OxmlElement(tag):
    return etree.Element(qn(tag))

# ---------------------------------------------------------------- 常量
SCRATCH = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a"
COVER_IMG = os.path.join(SCRATCH, "ppt_cover.png")
BACK_IMG = os.path.join(SCRATCH, "ppt_backcover.png")
OUT_DIR = "/Users/guoqingtao/Desktop/AI办公评测/zhikuncode"
OUT_PPTX = os.path.join(OUT_DIR, "宇树科技_公司研究汇报.pptx")
OUT_PDF = os.path.join(SCRATCH, "ppt_preview.pdf")

NAVY = RGBColor(0x0A, 0x1F, 0x44)      # 主色 深海军蓝
CYAN = RGBColor(0x19, 0xC2, 0xFF)      # 强调 科技青
BG = RGBColor(0xF7, 0xF9, 0xFC)        # 内容页背景
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x23, 0x32, 0x4D)      # 正文深灰蓝
MUTED = RGBColor(0x6B, 0x7A, 0x90)     # 次要文字
GREEN = RGBColor(0x17, 0xB8, 0x90)     # 正向青绿
ORANGE = RGBColor(0xE8, 0x54, 0x3F)    # 警示橙红
GRAYBLUE = RGBColor(0x8F, 0xA3, 0xBF)  # 组件及其他系列色
LIGHT_CYAN = RGBColor(0x9E, 0xDF, 0xFF)
CARD_LINE = RGBColor(0xE3, 0xE9, 0xF2)
HAIRLINE = RGBColor(0xD8, 0xE0, 0xEA)
AXIS_GRAY = RGBColor(0xD9, 0xE1, 0xEC)
FONT = "微软雅黑"

PAGE_W, PAGE_H = 13.333, 7.5
MARGIN = 0.55
CONTENT_W = PAGE_W - 2 * MARGIN        # 12.233
FOOT_LINE_Y = 7.13

IN = Inches

# ---------------------------------------------------------------- 基础辅助
def style_run(run, size, bold=False, color=TEXT, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = FONT
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            rPr.append(el)
        el.set("typeface", FONT)

def add_text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, name=None):
    """paras: list of (text, size, bold, color, align[, space_after[, line_spacing]])"""
    tb = slide.shapes.add_textbox(IN(x), IN(y), IN(w), IN(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, spec in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        text, size, bold, color, align = spec[:5]
        para.alignment = align
        if len(spec) > 5 and spec[5]:
            para.space_after = Pt(spec[5])
        if len(spec) > 6 and spec[6]:
            para.line_spacing = spec[6]
        run = para.add_run()
        run.text = text
        style_run(run, size, bold, color)
    return tb

def add_rich(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.15):
    """单段落多 run：runs = [(text, size, bold, color), ...]"""
    tb = slide.shapes.add_textbox(IN(x), IN(y), IN(w), IN(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    para = tf.paragraphs[0]
    para.alignment = align
    para.line_spacing = line_spacing
    for text, size, bold, color in runs:
        run = para.add_run()
        run.text = text
        style_run(run, size, bold, color)
    return tb

def add_rect(slide, x, y, w, h, fill, line=None, line_w=0.75, shape=MSO_SHAPE.RECTANGLE, adj=None):
    sp = slide.shapes.add_shape(shape, IN(x), IN(y), IN(w), IN(h))
    if adj is not None:
        try:
            sp.adjustments[0] = adj
        except Exception:
            pass
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    return sp

def add_card(slide, x, y, w, h, accent=CYAN, fill=WHITE, accent_top=True):
    card = add_rect(slide, x, y, w, h, fill, line=CARD_LINE, line_w=0.75,
                    shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.055)
    if accent is not None:
        if accent_top:
            add_rect(slide, x + 0.18, y, w - 0.36, 0.042, accent)
        else:
            add_rect(slide, x, y + 0.14, 0.05, h - 0.28, accent)
    return card

def set_cell(cell, text, size=9.5, bold=False, color=TEXT, align=PP_ALIGN.LEFT,
             fill=WHITE, anchor=MSO_ANCHOR.MIDDLE):
    cell.vertical_anchor = anchor
    cell.margin_left = IN(0.08)
    cell.margin_right = IN(0.06)
    cell.margin_top = IN(0.02)
    cell.margin_bottom = IN(0.02)
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    tf = cell.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    style_run(run, size, bold, color)

def set_cell_borders(cell, color="D8E0EA", width=9525):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    order = ("a:lnL", "a:lnR", "a:lnT", "a:lnB")
    for tag in order:
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
    for tag in reversed(order):          # 逆序插到最前，保持 schema 顺序
        ln = OxmlElement(tag)
        ln.set("w", str(width))
        ln.set("cap", "flat")
        ln.set("cmpd", "sng")
        ln.set("algn", "ctr")
        sf = OxmlElement("a:solidFill")
        c = OxmlElement("a:srgbClr")
        c.set("val", color)
        sf.append(c)
        ln.append(sf)
        tcPr.insert(0, ln)

# ---------------------------------------------------------------- 图表辅助
def style_axes(chart, cat_size=9.5, val_size=9, val_fmt='#,##0', hide_val=False):
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(cat_size)
    ca.tick_labels.font.color.rgb = MUTED
    ca.tick_labels.font.name = FONT
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = AXIS_GRAY
    va = chart.value_axis
    va.has_major_gridlines = False
    va.format.line.color.rgb = AXIS_GRAY
    if hide_val:
        va.visible = False
    else:
        va.tick_labels.font.size = Pt(val_size)
        va.tick_labels.font.color.rgb = MUTED
        va.tick_labels.font.name = FONT
        va.tick_labels.number_format = val_fmt
        va.tick_labels.number_format_is_linked = False

def color_series(ser, rgb, line_chart=False, width=2.5, dash=None, marker=True):
    if line_chart:
        ser.format.line.color.rgb = rgb
        ser.format.line.width = Pt(width)
        if dash:
            ser.format.line.dash_style = dash
        ser.smooth = False
        if marker:
            ser.marker.style = XL_MARKER_STYLE.CIRCLE
            ser.marker.size = 6
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = rgb
            ser.marker.format.line.color.rgb = WHITE
            ser.marker.format.line.width = Pt(1.0)
    else:
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = rgb
        ser.format.line.fill.background()

def add_labels(plot, fmt='#,##0', size=9, color=TEXT, pos=None, bold=False):
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.font.size = Pt(size)
    dl.font.bold = bold
    dl.font.color.rgb = color
    dl.font.name = FONT
    if pos is not None:
        dl.position = pos

def set_legend(chart, size=9.5):
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(size)
    chart.legend.font.color.rgb = TEXT
    chart.legend.font.name = FONT

def chart_title(slide, x, y, w, text):
    add_text(slide, x, y, w, 0.3,
             [(text, 12, True, NAVY, PP_ALIGN.LEFT)])

# ---------------------------------------------------------------- 版式骨架
def new_content_slide(prs, kicker, title, page_no, source):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, PAGE_W, PAGE_H, BG).name = "page_bg"
    add_text(slide, MARGIN, 0.30, 9.0, 0.30,
             [(kicker, 11, True, CYAN, PP_ALIGN.LEFT)], name="kicker")
    add_text(slide, MARGIN, 0.60, CONTENT_W, 0.78,
             [(title, 21, True, NAVY, PP_ALIGN.LEFT)],
             anchor=MSO_ANCHOR.MIDDLE, name="action_title")
    add_rect(slide, MARGIN + 0.02, 1.46, 1.2, 0.032, CYAN)
    # 页脚
    add_rect(slide, MARGIN, FOOT_LINE_Y, CONTENT_W, 0.0104, HAIRLINE)
    add_text(slide, MARGIN, 7.19, 7.45, 0.26,
             [(source, 8, False, MUTED, PP_ALIGN.LEFT)], name="footer_source")
    add_text(slide, 8.05, 7.19, 4.73, 0.26,
             [("资料截止：2026-08-30 ｜ 第%d页 ｜ 内部汇报材料·不构成投资建议" % page_no,
               8, False, MUTED, PP_ALIGN.RIGHT)], name="footer_page")
    return slide

def warn_strip(slide, x, y, w, h, text):
    add_rect(slide, x, y, w, h, RGBColor(0xFD, 0xEC, 0xE8),
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.18)
    add_rect(slide, x + 0.06, y + 0.08, 0.05, h - 0.16, ORANGE)
    add_text(slide, x + 0.22, y + 0.05, w - 0.36, h - 0.10,
             [(text, 9.5, True, RGBColor(0xB5, 0x3A, 0x28), PP_ALIGN.LEFT)],
             anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ 幻灯片 1：封面
def slide_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(COVER_IMG, 0, 0, IN(PAGE_W), IN(PAGE_H))
    add_rect(slide, 0.72, 1.62, 1.2, 0.045, CYAN)
    add_text(slide, 0.72, 1.92, 8.1, 1.75,
             [("宇树科技（688836.SH）", 40, True, WHITE, PP_ALIGN.LEFT),
              ("公司研究汇报", 40, True, WHITE, PP_ALIGN.LEFT)],
             name="cover_title")
    add_text(slide, 0.72, 3.78, 7.6, 0.95,
             [("科创板“人形机器人第一股”：", 16, False, RGBColor(0xD6, 0xE4, 0xF5), PP_ALIGN.LEFT),
              ("爆发式增长与高光估值下的冷思考", 16, False, RGBColor(0xD6, 0xE4, 0xF5), PP_ALIGN.LEFT)])
    add_text(slide, 0.72, 4.92, 8.4, 0.35,
             [("资料截止：2026年8月30日 ｜ 内部汇报材料 ｜ 数据口径：招股说明书注册稿/上市公告书",
               10.5, False, RGBColor(0xA8, 0xBB, 0xD4), PP_ALIGN.LEFT)])
    add_text(slide, 0.72, 6.98, 7.8, 0.3,
             [("资料来源：招股说明书（注册稿）、上市公告书（2026-08-18）、上海证券交易所",
               8, False, RGBColor(0x8F, 0xA3, 0xBF), PP_ALIGN.LEFT)], name="footer_source")
    add_text(slide, 9.55, 6.98, 3.3, 0.3,
             [("封面图片由AI生成，仅作装饰", 8, False, RGBColor(0x8F, 0xA3, 0xBF), PP_ALIGN.RIGHT)])

# ================================================================ 幻灯片 2：核心观点
def slide_summary(prs):
    slide = new_content_slide(
        prs, "01 核心观点 · SUMMARY",
        "五句话看懂宇树：爆发增长、结构切换、盈利兑现、高光估值、风险并存",
        2, "资料来源：招股说明书（注册稿）、上市公告书（2026-08-18）、上海证券交易所")
    rows = [
        ("1", "爆发式增长：", "2025年营收169,926.93万元（+332.64%），2023–2025 CAGR约226.8%", CYAN),
        ("2", "结构切换：", "人形机器人收入占比1.88%→51.78%，跃居第一大产品", CYAN),
        ("3", "盈利兑现：", "2024年扭亏，2025年扣非59,075.28万元、主营毛利率60.13%", GREEN),
        ("4", "隐忧并存：", "2026H1扣非-19.34%“增收不增利”，科教客户占比73.6%", ORANGE),
        ("5", "高光估值：", "发行PE 219.23倍，首日+460.34%后回落近半（二级市场数据）", ORANGE),
    ]
    y = 1.66
    for num, lead, body, chip in rows:
        add_card(slide, MARGIN, y, CONTENT_W, 0.98, accent=None)
        add_rect(slide, MARGIN, y + 0.12, 0.05, 0.74, chip)
        circ = add_rect(slide, 0.86, y + 0.30, 0.38, 0.38, NAVY, shape=MSO_SHAPE.OVAL)
        tf = circ.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num
        style_run(r, 14, True, WHITE)
        add_rich(slide, 1.48, y + 0.13, 11.1, 0.72,
                 [(lead, 12.5, True, NAVY), (body, 11.5, False, TEXT)])
        y += 1.07

# ================================================================ 幻灯片 3：公司速览与IPO
def slide_profile(prs):
    slide = new_content_slide(
        prs, "02 公司概况 · PROFILE & IPO",
        "成立十年登陆科创板：104天过会注册，发行市值609.93亿元",
        3, "资料来源：上市公告书、上交所公告（2026-08）")
    facts = [
        ("成立日期", "2016-08-26", "2026年8月上市，创业整十年"),
        ("实际控制人", "王兴兴 · 表决权65.31%", "发行后口径（直接21.4395%+一致行动安排）"),
        ("员工规模（2025-09-30）", "480人 · 研发175人", "研发人员占比36.46%"),
        ("专利（截至2026-01-31）", "262项", "含境内发明专利20项（路演口径）"),
    ]
    y = 1.66
    for label, value, note in facts:
        add_card(slide, MARGIN, y, 5.15, 1.22, accent=CYAN, accent_top=False)
        add_text(slide, 0.80, y + 0.13, 4.75, 0.26, [(label, 9.5, False, MUTED, PP_ALIGN.LEFT)])
        add_text(slide, 0.80, y + 0.40, 4.75, 0.42, [(value, 15.5, True, NAVY, PP_ALIGN.LEFT)])
        add_text(slide, 0.80, y + 0.87, 4.75, 0.26, [(note, 8.5, False, MUTED, PP_ALIGN.LEFT)])
        y += 1.36
    # 右栏：IPO时间线
    add_text(slide, 6.15, 1.62, 6.6, 0.3,
             [("IPO历程：受理至注册生效仅104天", 11.5, True, NAVY, PP_ALIGN.LEFT)])
    axis_y = 2.62
    add_rect(slide, 6.40, axis_y, 5.95, 0.022, RGBColor(0xC9, 0xD6, 0xE6))
    nodes = [("2025-07-08", "辅导备案"), ("2026-03-20", "受理"), ("2026-06-01", "过会"),
             ("2026-07-02", "注册生效"), ("2026-08-19", "上市")]
    xs = [6.55, 7.72, 8.89, 10.06, 11.23]
    for i, ((date, evt), cx) in enumerate(zip(nodes, xs)):
        last = i == len(nodes) - 1
        d = 0.20 if last else 0.15
        add_rect(slide, cx - d / 2, axis_y + 0.011 - d / 2, d, d,
                 CYAN if last else NAVY, shape=MSO_SHAPE.OVAL)
        add_text(slide, cx - 0.58, axis_y - 0.42, 1.16, 0.26,
                 [(date, 9.5, True, NAVY, PP_ALIGN.CENTER)])
        add_text(slide, cx - 0.58, axis_y + 0.18, 1.16, 0.26,
                 [(evt, 9, False, MUTED, PP_ALIGN.CENTER)])
    # 发行要素（定义列表式小表）
    add_text(slide, 6.15, 3.30, 6.6, 0.3,
             [("发行要素（上市公告书/发行公告）", 11.5, True, NAVY, PP_ALIGN.LEFT)])
    items = [
        ("发行价", "150.80元/股"),
        ("新发股份", "4,044.6434万股（占发行后10%）"),
        ("募资总额", "609,932.22万元"),
        ("发行市盈率", "219.23倍（行业均值38.56倍）"),
        ("网上中签率", "0.01809759%"),
    ]
    y = 3.68
    for label, value in items:
        add_text(slide, 6.15, y, 2.3, 0.30, [(label, 10, False, MUTED, PP_ALIGN.LEFT)])
        add_text(slide, 8.45, y, 4.33, 0.30, [(value, 10.5, True, NAVY, PP_ALIGN.RIGHT)])
        add_rect(slide, 6.15, y + 0.375, 6.63, 0.008, HAIRLINE)
        y += 0.46
    add_text(slide, 6.15, y + 0.04, 6.63, 0.3,
             [("代码688836（-W表决权差异）；发行后总股本40,446.4340万股",
               8.5, False, MUTED, PP_ALIGN.LEFT)])

# ================================================================ 幻灯片 4：产品结构
def slide_mix(prs):
    slide = new_content_slide(
        prs, "03 产品结构 · REVENUE MIX",
        "人形机器人两年内从1.9%跃升至51.8%，接棒四足成为第一大收入来源",
        4, "资料来源：招股说明书（注册稿）、中新经纬（2026-07-02）")
    chart_title(slide, MARGIN, 1.62, 7.2, "分产品收入（万元，注册稿口径）")
    cd = CategoryChartData()
    cd.categories = ["2023", "2024", "2025"]
    cd.add_series("四足机器人", (11900, 23100, 69800))
    cd.add_series("人形机器人", (296.71, 10700, 86800))
    cd.add_series("组件及其他(倒算)", (3500, 5000, 11100))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, IN(MARGIN), IN(1.95),
                                IN(7.2), IN(4.55), cd)
    gf.name = "chart_mix"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 70
    plot.vary_by_categories = False
    for ser, rgb in zip(ch.series, (NAVY, CYAN, GRAYBLUE)):
        color_series(ser, rgb)
    style_axes(ch)
    add_labels(plot, fmt='#,##0', size=9, color=WHITE, pos=XL_LABEL_POSITION.CENTER, bold=True)
    set_legend(ch)
    # 右侧占比卡
    cards = [
        ("人形机器人收入占比", "1.88% → 27.68% → 51.78%", CYAN),
        ("四足机器人收入占比", "75.78% → 59.47% → 41.62%", NAVY),
        ("组件及其他占比（倒算）", "≈22.3% → ≈12.9% → ≈6.6%", GRAYBLUE),
    ]
    y = 1.95
    for label, prog, rgb in cards:
        add_card(slide, 8.0, y, 4.78, 1.24, accent=rgb)
        add_text(slide, 8.25, y + 0.16, 4.3, 0.28, [(label, 10.5, True, TEXT, PP_ALIGN.LEFT)])
        add_text(slide, 8.25, y + 0.47, 4.3, 0.40, [(prog, 16, True, NAVY, PP_ALIGN.LEFT)])
        add_text(slide, 8.25, y + 0.92, 4.3, 0.24,
                 [("2023 → 2024 → 2025", 8.5, False, MUTED, PP_ALIGN.LEFT)])
        y += 1.40
    add_card(slide, 8.0, y, 4.78, 0.92, accent=None, fill=RGBColor(0xEF, 0xF4, 0xFA))
    add_text(slide, 8.20, y + 0.10, 4.4, 0.74,
             [("注：组件及其他收入、主营合计均为倒算值（待核验）；"
               "9M2025人形占比51.53%（申报稿）。", 8.5, False, MUTED, PP_ALIGN.LEFT, 0, 1.2)])

# ================================================================ 幻灯片 5：收入增长
def slide_revenue(prs):
    slide = new_content_slide(
        prs, "04 收入增长 · GROWTH",
        "营收三年增长近13倍：2025年+332.6%，2026H1增速回落至+48.5%",
        5, "资料来源：招股说明书、上市公告书（2026-08-18）")
    chart_title(slide, MARGIN, 1.62, 8.9, "营业收入（万元，2022–2025年度 + 2026H1）")
    cd = CategoryChartData()
    cd.categories = ["2022", "2023", "2024", "2025", "2026H1(半年)"]
    cd.add_series("营业收入", (12300, 15913.44, 39276.6, 169926.93, 115200))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(MARGIN), IN(1.95),
                                IN(8.9), IN(4.55), cd)
    gf.name = "chart_revenue"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.vary_by_categories = False
    ser = ch.series[0]
    color_series(ser, NAVY)
    pt = ser.points[4]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = LIGHT_CYAN
    pt.format.line.fill.background()
    style_axes(ch)
    add_labels(plot, fmt='#,##0', size=9.5, color=NAVY, pos=XL_LABEL_POSITION.OUTSIDE_END, bold=True)
    # CAGR 标注形状
    tag = add_rect(slide, 6.05, 2.25, 2.35, 0.52, RGBColor(0xE3, 0xF6, 0xFF),
                   line=CYAN, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
    tf = tag.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "2023–2025 CAGR ≈ 226.8%"
    style_run(r, 10.5, True, NAVY)
    # 右侧注释卡
    add_card(slide, 9.75, 1.95, 3.03, 3.55, accent=CYAN)
    add_text(slide, 10.0, 2.12, 2.55, 3.2,
             [("口径注释", 10.5, True, NAVY, PP_ALIGN.LEFT, 8),
              ("· 2022/2024为约数（申报稿/倒算）", 9.5, False, TEXT, PP_ALIGN.LEFT, 7),
              ("· 2024申报稿审计值39,237.06万元", 9.5, False, TEXT, PP_ALIGN.LEFT, 7),
              ("· 2026H1约11.52亿（+48.54%），取自上市公告书", 9.5, False, TEXT, PP_ALIGN.LEFT, 7),
              ("· 2026H1为半年数据（浅色柱），与全年不可直接比较", 9.5, False, TEXT, PP_ALIGN.LEFT, 0)])

# ================================================================ 幻灯片 6：盈利变化
def slide_profit(prs):
    slide = new_content_slide(
        prs, "05 盈利变化 · PROFITABILITY",
        "2024年扭亏、2025年扣非5.9亿：剔除一次性股份支付后盈利成色更足",
        6, "资料来源：招股说明书（注册稿/申报稿）、上市公告书")
    chart_title(slide, MARGIN, 1.62, 8.1, "归母净利润 vs 扣非归母净利润（万元，2022–2025）")
    cd = CategoryChartData()
    cd.categories = ["2022", "2023", "2024", "2025"]
    cd.add_series("归母净利润", (-2210.05, -1114.51, 9547.47, 27821.05))
    cd.add_series("扣非归母净利润", (-807, -1801.91, 7847.65, 59075.28))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(MARGIN), IN(1.95),
                                IN(8.15), IN(4.25), cd)
    gf.name = "chart_profit"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 70
    plot.vary_by_categories = False
    for ser, rgb in zip(ch.series, (NAVY, GREEN)):
        color_series(ser, rgb)
    style_axes(ch)
    add_labels(plot, fmt='#,##0', size=8.5, color=TEXT, pos=XL_LABEL_POSITION.OUTSIDE_END)
    set_legend(ch)
    # 右侧橙色注释卡
    add_card(slide, 8.95, 1.95, 3.83, 2.06, accent=ORANGE)
    add_text(slide, 9.20, 2.10, 3.35, 1.8,
             [("为何2025年归母＜扣非？", 10.5, True, ORANGE, PP_ALIGN.LEFT, 6),
              ("一次性股份支付34,906.55万元计入管理费用，"
               "致归母低于扣非约31,254万元（非经常性）。", 9.5, False, TEXT, PP_ALIGN.LEFT, 0, 1.25)])
    add_card(slide, 8.95, 4.16, 3.83, 2.04, accent=GREEN)
    add_text(slide, 9.20, 4.31, 3.35, 1.8,
             [("盈利成色", 10.5, True, GREEN, PP_ALIGN.LEFT, 6),
              ("2025年扣非净利率约34.8%；2024年归母9,547.47万元实现扭亏；"
               "2022年扣非约-807万元（约数）。", 9.5, False, TEXT, PP_ALIGN.LEFT, 0, 1.25)])
    warn_strip(slide, MARGIN, 6.38, CONTENT_W, 0.55,
               "⚠ 2026Q1扣非-52.55%、2026H1扣非-19.34%（上市公告书）——费用高速扩张，规模扩张期利润承压")

# ================================================================ 幻灯片 7：盈利质量
def slide_quality(prs):
    slide = new_content_slide(
        prs, "06 盈利质量 · EARNINGS QUALITY",
        "毛利率升至60.1%、经营现金流6.7亿超扣非净利，盈利含金量高",
        7, "资料来源：招股说明书、金融时报（2026-05-26）、长江商报（2026-03-23）")
    # 左：毛利率折线
    chart_title(slide, MARGIN, 1.62, 5.9, "主营业务毛利率（%，2023–2025）")
    cd = CategoryChartData()
    cd.categories = ["2023", "2024", "2025"]
    cd.add_series("主营毛利率", (44.22, 56.74, 60.13))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, IN(MARGIN), IN(1.95),
                                IN(5.9), IN(4.5), cd)
    gf.name = "chart_margin"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.vary_by_categories = False
    color_series(ch.series[0], GREEN, line_chart=True, width=2.75)
    style_axes(ch, val_fmt='0"%"')
    ch.value_axis.minimum_scale = 30
    ch.value_axis.maximum_scale = 70
    add_labels(plot, fmt='0.00"%"', size=10, color=GREEN, pos=XL_LABEL_POSITION.ABOVE, bold=True)
    # 右：经营现金流柱
    chart_title(slide, 6.75, 1.62, 6.03, "经营活动现金流净额（万元，2022–2025）")
    cd2 = CategoryChartData()
    cd2.categories = ["2022", "2023", "2024", "2025"]
    cd2.add_series("经营现金流净额", (-3019.73, 494.25, 19200, 67000))
    gf2 = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(6.75), IN(1.95),
                                 IN(6.03), IN(4.5), cd2)
    gf2.name = "chart_cashflow"
    ch2 = gf2.chart
    ch2.has_title = False
    plot2 = ch2.plots[0]
    plot2.gap_width = 60
    plot2.vary_by_categories = False
    ser2 = ch2.series[0]
    color_series(ser2, NAVY)
    for i in (0, 1):
        p = ser2.points[i]
        p.format.fill.solid()
        p.format.fill.fore_color.rgb = GRAYBLUE
        p.format.line.fill.background()
    style_axes(ch2)
    add_labels(plot2, fmt='#,##0', size=9.5, color=NAVY, pos=XL_LABEL_POSITION.OUTSIDE_END, bold=True)
    add_text(slide, 6.75, 6.52, 6.03, 0.45,
             [("注：2022/2023为单一来源（待核验，灰蓝色柱）；2024/2025为披露约数（1.92亿/6.70亿）。",
               8.5, False, MUTED, PP_ALIGN.LEFT, 0, 1.15)])

# ================================================================ 幻灯片 8：研发投入
def slide_rd(prs):
    slide = new_content_slide(
        prs, "07 研发投入 · R&D",
        "研发费率8.5%低于同业均值，但绝对额三年近5倍增长、募投85%加码研发",
        8, "资料来源：招股说明书、长江商报、金融时报")
    # 左：研发费用柱
    chart_title(slide, MARGIN, 1.60, 5.7, "研发费用（万元，2022–2025）")
    cd = CategoryChartData()
    cd.categories = ["2022", "2023", "2024", "2025"]
    cd.add_series("研发费用", (2998.48, 4995.18, 7001.70, 14500))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(MARGIN), IN(1.92),
                                IN(5.7), IN(3.72), cd)
    gf.name = "chart_rd_exp"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.vary_by_categories = False
    color_series(ch.series[0], NAVY)
    style_axes(ch)
    add_labels(plot, fmt='#,##0', size=9.5, color=NAVY, pos=XL_LABEL_POSITION.OUTSIDE_END, bold=True)
    # 右：费用率折线 + 同业参考线
    chart_title(slide, 6.55, 1.60, 6.23, "研发费用率（%）与同业均值（9M2025）")
    cd2 = CategoryChartData()
    cd2.categories = ["2022", "2023", "2024", "2025"]
    cd2.add_series("研发费用率", (24.39, 31.39, 17.84, 8.53))
    cd2.add_series("9M2025同业均值27.92%", (27.92, 27.92, 27.92, 27.92))
    gf2 = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, IN(6.55), IN(1.92),
                                 IN(6.23), IN(3.72), cd2)
    gf2.name = "chart_rd_ratio"
    ch2 = gf2.chart
    ch2.has_title = False
    plot2 = ch2.plots[0]
    plot2.vary_by_categories = False
    color_series(ch2.series[0], ORANGE, line_chart=True, width=2.75)
    color_series(ch2.series[1], GRAYBLUE, line_chart=True, width=1.75,
                 dash=MSO_LINE.DASH, marker=False)
    style_axes(ch2, val_fmt='0"%"')
    ch2.value_axis.minimum_scale = 0
    ch2.value_axis.maximum_scale = 40
    add_labels(plot2, fmt='0.0"%"', size=8.5, color=ORANGE, pos=XL_LABEL_POSITION.ABOVE)
    set_legend(ch2, size=9)
    # 底部：募投四项目横条（形状）
    add_text(slide, MARGIN, 5.74, 12.2, 0.28,
             [("募投项目投向（万元，合计420,171.12，约85%投向研发）", 11, True, NAVY, PP_ALIGN.LEFT)])
    projects = [
        ("智能机器人模型研发", 202245.93, NAVY),
        ("机器人本体研发", 110973.80, CYAN),
        ("制造基地（年产7.5万台人形+11.5万台四足）", 62411.39, GREEN),
        ("新型产品开发", 44540.00, GRAYBLUE),
    ]
    y = 6.08
    max_v = 202245.93
    for name, val, rgb in projects:
        add_text(slide, MARGIN, y, 3.05, 0.24, [(name, 9, False, TEXT, PP_ALIGN.LEFT)])
        bw = val / max_v * 6.55
        add_rect(slide, 3.70, y + 0.015, bw, 0.20, rgb,
                 shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.5)
        add_text(slide, 3.70 + bw + 0.10, y, 1.75, 0.24,
                 [("{:,.2f}".format(val), 9, True, NAVY, PP_ALIGN.LEFT)])
        y += 0.255

# ================================================================ 幻灯片 9：竞争优势
def slide_moat(prs):
    slide = new_content_slide(
        prs, "08 竞争优势 · MOAT",
        "全栈自研+规模量产：四足份额60–70%，人形出货全球第一",
        9, "资料来源：国新办见面会（2025-07-15）、赛迪顾问、公司官方公告（2026-08）")
    cards = [
        ("60–70%", "四足机器人全球销量份额", "王兴兴国新办表态（2025-07-15），管理层口径"),
        ("5,500+台", "人形2025年出货全球第一", "份额32.4%（赛迪顾问，机构数据）"),
        ("≈18,000台", "纯双足人形累计下线", "截至2026-07，公司官方口径"),
        ("59.34→16.76万", "人形平均单价（万元/台）", "2023→9M2025，全栈自研以价换量"),
    ]
    xs = [0.55, 3.65, 6.75, 9.85]
    for (big, label, note), x in zip(cards, xs):
        add_card(slide, x, 1.85, 2.92, 3.30, accent=CYAN)
        add_text(slide, x + 0.22, 2.30, 2.48, 0.95,
                 [(big, 27, True, NAVY, PP_ALIGN.LEFT)])
        add_text(slide, x + 0.22, 3.38, 2.48, 0.62,
                 [(label, 11, True, TEXT, PP_ALIGN.LEFT, 0, 1.15)])
        add_text(slide, x + 0.22, 4.12, 2.48, 0.85,
                 [(note, 8.5, False, MUTED, PP_ALIGN.LEFT, 0, 1.2)])
    add_rect(slide, MARGIN, 5.55, CONTENT_W, 0.72, RGBColor(0xE6, 0xF8, 0xF3),
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, adj=0.16)
    add_rect(slide, MARGIN + 0.06, 5.65, 0.05, 0.52, GREEN)
    add_text(slide, MARGIN + 0.25, 5.62, 11.8, 0.58,
             [("2025年归母净利润与经营现金流双为正（扣非5.91亿、经营现金流6.70亿），区别于多数未盈利同业。",
               10.5, True, RGBColor(0x0E, 0x7A, 0x62), PP_ALIGN.LEFT)],
             anchor=MSO_ANCHOR.MIDDLE)

# ================================================================ 幻灯片 10：商业化结构
def slide_commercial(prs):
    slide = new_content_slide(
        prs, "09 商业化结构 · COMMERCIALIZATION",
        "人形73.6%销往科研教育、工业场景仅9.0%，境外占比降至39.2%",
        10, "资料来源：招股说明书（申报稿）、潮新闻（2026-03-20）")
    pie_colors = (NAVY, CYAN, ORANGE)
    cats = ["科研教育", "商业消费", "行业应用"]
    add_text(slide, MARGIN, 1.60, 6.4, 0.3,
             [("下游应用结构（9M2025，申报稿，占各自收入比）", 11.5, True, NAVY, PP_ALIGN.LEFT)])
    pies = [("人形机器人下游", (73.60, 17.39, 9.01), 0.45, "chart_pie_humanoid"),
            ("四足机器人下游", (31.58, 42.30, 26.12), 3.80, "chart_pie_quadruped")]
    for title, vals, x, nm in pies:
        add_text(slide, x, 1.95, 3.2, 0.28, [(title, 10.5, True, TEXT, PP_ALIGN.CENTER)])
        cd = CategoryChartData()
        cd.categories = cats
        cd.add_series(title, vals)
        gf = slide.shapes.add_chart(XL_CHART_TYPE.PIE, IN(x), IN(2.25),
                                    IN(3.2), IN(3.15), cd)
        gf.name = nm
        ch = gf.chart
        ch.has_title = False
        plot = ch.plots[0]
        plot.vary_by_categories = True
        ser = ch.series[0]
        for i, rgb in enumerate(pie_colors):
            p = ser.points[i]
            p.format.fill.solid()
            p.format.fill.fore_color.rgb = rgb
            p.format.line.color.rgb = WHITE
            p.format.line.width = Pt(1.0)
        add_labels(plot, fmt='0.00"%"', size=9, color=TEXT,
                   pos=XL_LABEL_POSITION.OUTSIDE_END, bold=True)
        set_legend(ch, size=9)
    add_text(slide, 0.55, 5.55, 6.4, 0.35,
             [("注：四足商业消费占比42.30%首超科研教育31.58%。", 8.5, False, MUTED, PP_ALIGN.LEFT)])
    # 右：境外占比柱
    add_text(slide, 7.35, 1.60, 5.43, 0.3,
             [("境外收入占比（%，申报稿口径）", 11.5, True, NAVY, PP_ALIGN.LEFT)])
    cd2 = CategoryChartData()
    cd2.categories = ["2022", "2023", "2024", "9M2025"]
    cd2.add_series("境外收入占比", (57.21, 55.63, 55.70, 39.20))
    gf2 = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, IN(7.35), IN(2.25),
                                 IN(5.43), IN(3.55), cd2)
    gf2.name = "chart_overseas"
    ch2 = gf2.chart
    ch2.has_title = False
    plot2 = ch2.plots[0]
    plot2.gap_width = 60
    plot2.vary_by_categories = False
    ser2 = ch2.series[0]
    color_series(ser2, NAVY)
    p = ser2.points[3]
    p.format.fill.solid()
    p.format.fill.fore_color.rgb = CYAN
    p.format.line.fill.background()
    style_axes(ch2, val_fmt='0"%"')
    ch2.value_axis.minimum_scale = 0
    ch2.value_axis.maximum_scale = 70
    add_labels(plot2, fmt='0.00"%"', size=9.5, color=NAVY,
               pos=XL_LABEL_POSITION.OUTSIDE_END, bold=True)
    warn_strip(slide, MARGIN, 6.18, CONTENT_W, 0.62,
               "⚠ 真实生产场景（智能制造/巡检）9M2025收入仅1,570万元、占主营2.64%（单一来源，待核验）；"
               "9M2025境外占比39.20%系国内放量摊薄。")

# ================================================================ 幻灯片 11：增长变量
def slide_drivers(prs):
    slide = new_content_slide(
        prs, "10 增长变量 · GROWTH DRIVERS",
        "四大变量决定增长持续性：产能、场景、海外、大模型（含前瞻表述，非业绩指引）",
        11, "资料来源：招股说明书、管理层公开表态（已标注）、媒体报道")
    cards = [
        ("① 产能", CYAN,
         ["募投制造基地规划产能：", "年产7.5万台人形", "11.5万台四足（招股书）",
          "若顺利达产，可支撑放量"]),
        ("② 场景", CYAN,
         ["科研教育→工业/消费渗透", "节奏仍待观察：", "当前行业应用占比仅9.01%",
          "真实生产场景尚在早期"]),
        ("③ 海外", ORANGE,
         ["2026-07-28美国FCC禁令", "（限新型号进口）带来", "海外扩张不确定性；",
          "管理层称出口占比约40–50%（表态）"]),
        ("④ 大模型", CYAN,
         ["募投押注WMA/VLA路线；", "“ChatGPT时刻快则2–3年、", "慢则5–10年”（王兴兴表态）；",
          "“2026年出货至少翻一番”（表态，非业绩指引）"]),
    ]
    xs = [0.55, 3.65, 6.75, 9.85]
    for (title, accent, lines), x in zip(cards, xs):
        add_card(slide, x, 1.78, 2.92, 4.55, accent=accent)
        add_text(slide, x + 0.22, 2.02, 2.48, 0.36, [(title, 13.5, True, NAVY, PP_ALIGN.LEFT)])
        paras = []
        for ln in lines:
            paras.append((ln, 9.5, False, TEXT, PP_ALIGN.LEFT, 7, 1.18))
        add_text(slide, x + 0.22, 2.50, 2.48, 3.7, paras)
    add_text(slide, MARGIN, 6.55, CONTENT_W, 0.35,
             [("注：本页含前瞻/表态性表述，均为条件式措辞，不构成业绩指引或投资建议。",
               8.5, False, MUTED, PP_ALIGN.LEFT)])

# ================================================================ 幻灯片 12：上市后表现与估值
def slide_market(prs):
    slide = new_content_slide(
        prs, "11 市场表现与估值 · VALUATION",
        "首日+460%后回落近半：8月底市值约2,285亿元，仍对应2025年归母PE约821倍",
        12, "资料来源：上交所、发行结果公告（2026-08-14）、二级市场数据（截至2026-08-31）")
    chart_title(slide, MARGIN, 1.62, 7.6, "市值轨迹（亿元，二级市场数据）")
    cd = CategoryChartData()
    cd.categories = ["发行价", "首日收盘", "08-20", "08-24", "08-26", "08-31"]
    cd.add_series("总市值", (609.93, 3417.72, 2779, 2439, 2393, 2285))
    gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, IN(MARGIN), IN(1.95),
                                IN(7.6), IN(4.35), cd)
    gf.name = "chart_mktcap"
    ch = gf.chart
    ch.has_title = False
    plot = ch.plots[0]
    plot.vary_by_categories = False
    color_series(ch.series[0], NAVY, line_chart=True, width=2.75)
    style_axes(ch)
    add_labels(plot, fmt='#,##0', size=9.5, color=NAVY, pos=XL_LABEL_POSITION.ABOVE, bold=True)
    add_text(slide, MARGIN, 6.40, 7.6, 0.5,
             [("注：市值=收盘价×总股本40,446.434万股；08-31收盘564.90元略晚于8-30截止日，作补充标注。",
               8.5, False, MUTED, PP_ALIGN.LEFT, 0, 1.15)])
    cards = [
        ("219.23×", "发行市盈率", "行业均值38.56倍（发行公告），发行价150.80元"),
        ("7.44%", "上市初流通盘占比", "流通股仅3,008.772万股，波动或被放大"),
        ("506–559亿", "机构目标市值（中信）【机构观点】", "野村目标价370元、建银国际269元，与现价分歧大"),
    ]
    y = 1.95
    for big, label, note in cards:
        add_card(slide, 8.45, y, 4.33, 1.52, accent=CYAN)
        add_text(slide, 8.70, y + 0.13, 3.9, 0.45, [(big, 20, True, NAVY, PP_ALIGN.LEFT)])
        add_text(slide, 8.70, y + 0.62, 3.9, 0.28, [(label, 9.5, True, TEXT, PP_ALIGN.LEFT)])
        add_text(slide, 8.70, y + 0.93, 3.9, 0.5,
                 [(note, 8.5, False, MUTED, PP_ALIGN.LEFT, 0, 1.15)])
        y += 1.68

# ================================================================ 幻灯片 13：主要风险
def slide_risks(prs):
    slide = new_content_slide(
        prs, "12 主要风险 · RISKS",
        "六大风险：估值消化、盈利承压、客户集中、地缘、竞争与解禁",
        13, "资料来源：招股说明书、上市公告书、媒体报道")
    risks = [
        ("① 高估值消化", "发行PE 219.23倍；8月底市值对应2025年归母PE约821倍，依赖高增长持续兑现。"),
        ("② 增收不增利", "2026H1扣非-19.34%；研发+152%、销售+250%（费用增速待核验），利润承压。"),
        ("③ 客户集中科教", "人形73.6%销往科研教育，对科研采购预算波动敏感。"),
        ("④ 地缘风险", "FCC禁令（限新型号）、涉军清单；美国收入占比13.3%（待核验）。"),
        ("⑤ 竞争加剧", "2026H1第三方口径智元出货反超（机构口径差异，待核验）。"),
        ("⑥ 流动性与解禁", "流通盘仅7.44%波动大；2027年起限售解禁；正式半年报未披露存数据缺口。"),
    ]
    xs = [0.55, 4.66, 8.77]
    ys = [1.72, 4.42]
    for i, (title, body) in enumerate(risks):
        x, y = xs[i % 3], ys[i // 3]
        add_card(slide, x, y, 3.99, 2.55, accent=ORANGE)
        add_text(slide, x + 0.22, y + 0.18, 3.55, 0.35, [(title, 12, True, NAVY, PP_ALIGN.LEFT)])
        add_text(slide, x + 0.22, y + 0.62, 3.55, 1.8,
                 [(body, 9.5, False, TEXT, PP_ALIGN.LEFT, 0, 1.3)])

# ================================================================ 幻灯片 14：口径说明与待核验
def slide_notes(prs):
    slide = new_content_slide(
        prs, "13 口径说明 · DATA NOTES",
        "数据口径：注册稿为准；七类事项仍需人工核验",
        14, "资料来源：上交所688836公告列表（2026-08-30核验）")
    add_card(slide, MARGIN, 1.70, 4.95, 4.85, accent=CYAN)
    add_text(slide, 0.85, 1.92, 4.4, 4.5,
             [("口径说明", 12, True, NAVY, PP_ALIGN.LEFT, 10),
              ("· 金额单位：人民币万元（市值另注亿元）", 10, False, TEXT, PP_ALIGN.LEFT, 9),
              ("· 以招股说明书注册稿/上市公告书为主口径，申报稿数据作补充", 10, False, TEXT, PP_ALIGN.LEFT, 9),
              ("· 2026H1数据取自上市公告书；正式半年报截至2026-08-30未披露", 10, False, TEXT, PP_ALIGN.LEFT, 9),
              ("· 公司无少数股东权益，净利润=归母净利润", 10, False, TEXT, PP_ALIGN.LEFT, 9),
              ("· ⚠=单一来源/倒算/约数；🔮=第三方预测，不写成事实", 10, False, TEXT, PP_ALIGN.LEFT, 0)])
    # 右：待核验清单表
    add_text(slide, 5.85, 1.62, 6.93, 0.3,
             [("待核验清单（7项）", 11.5, True, NAVY, PP_ALIGN.LEFT)])
    rows = [
        ("1", "2024年营收注册稿精确值", "暂用约39,276.6（倒算）"),
        ("2", "2025年末资产负债明细", "总资产321,500等（申报稿口径）"),
        ("3", "2025全年分地区收入", "73,200一说自相矛盾，未纳入"),
        ("4", "美国收入占比13.3%", "单一来源（招股意向书风险章节）"),
        ("5", "2025年费用明细", "研发费用14,500（约）等"),
        ("6", "人形2025销量5,215台 vs 出货5,500台", "采用官方出货量口径"),
        ("7", "正式半年报与定期报告", "截至2026-08-30未披露"),
    ]
    gf = slide.shapes.add_table(8, 3, IN(5.85), IN(1.95), IN(6.93), IN(4.55))
    gf.name = "table_todo"
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    tbl.columns[0].width = IN(0.45)
    tbl.columns[1].width = IN(3.55)
    tbl.columns[2].width = IN(2.93)
    tbl.rows[0].height = IN(0.42)
    for i in range(1, 8):
        tbl.rows[i].height = IN(0.59)
    heads = ("#", "待核验事项", "当前采用值/说明")
    for j, htxt in enumerate(heads):
        set_cell(tbl.cell(0, j), htxt, size=9.5, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER if j == 0 else PP_ALIGN.LEFT, fill=NAVY)
    for i, (no, item, cur) in enumerate(rows, start=1):
        band = WHITE if i % 2 else RGBColor(0xF1, 0xF5, 0xFB)
        set_cell(tbl.cell(i, 0), no, size=9, bold=True, color=CYAN,
                 align=PP_ALIGN.CENTER, fill=band)
        set_cell(tbl.cell(i, 1), item, size=9, color=TEXT, fill=band)
        set_cell(tbl.cell(i, 2), cur, size=9, color=MUTED, fill=band)
    for i in range(8):
        for j in range(3):
            set_cell_borders(tbl.cell(i, j))

# ================================================================ 幻灯片 15：封底
def slide_backcover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(BACK_IMG, 0, 0, IN(PAGE_W), IN(PAGE_H))
    add_text(slide, 1.5, 2.35, 10.333, 0.9,
             [("谢谢审阅", 36, True, WHITE, PP_ALIGN.CENTER)], name="back_title")
    add_text(slide, 1.5, 3.35, 10.333, 0.45,
             [("本材料基于公开信息整理，不构成投资建议", 14, False,
               RGBColor(0xD6, 0xE4, 0xF5), PP_ALIGN.CENTER)])
    add_rect(slide, 6.166, 4.05, 1.0, 0.035, CYAN)
    add_text(slide, 1.5, 4.35, 10.333, 0.35,
             [("核心资料来源", 11, True, CYAN, PP_ALIGN.CENTER)], name="footer_source")
    add_text(slide, 1.5, 4.78, 10.333, 1.35,
             [("上海证券交易所688836公告列表（2026-08-30核验）", 10.5, False,
               RGBColor(0xC9, 0xD6, 0xE8), PP_ALIGN.CENTER, 6),
              ("招股说明书（注册稿/申报稿）、上市公告书（2026-08-18）", 10.5, False,
               RGBColor(0xC9, 0xD6, 0xE8), PP_ALIGN.CENTER, 6),
              ("新华社、证券时报、第一财经、长江商报等公开报道（2026-03至2026-08）",
               10.5, False, RGBColor(0xC9, 0xD6, 0xE8), PP_ALIGN.CENTER, 0)])
    add_text(slide, 9.55, 6.98, 3.3, 0.3,
             [("封底图片由AI生成，仅作装饰", 8, False, RGBColor(0x8F, 0xA3, 0xBF), PP_ALIGN.RIGHT)])

# ================================================================ 主流程
def build():
    prs = Presentation()
    prs.slide_width = IN(PAGE_W)
    prs.slide_height = IN(PAGE_H)
    slide_cover(prs)
    slide_summary(prs)
    slide_profile(prs)
    slide_mix(prs)
    slide_revenue(prs)
    slide_profit(prs)
    slide_quality(prs)
    slide_rd(prs)
    slide_moat(prs)
    slide_commercial(prs)
    slide_drivers(prs)
    slide_market(prs)
    slide_risks(prs)
    slide_notes(prs)
    slide_backcover(prs)
    prs.save(OUT_PPTX)
    return OUT_PPTX

# ================================================================ 自检
EXPECTED_TITLES = {
    2: "五句话看懂宇树：爆发增长、结构切换、盈利兑现、高光估值、风险并存",
    3: "成立十年登陆科创板：104天过会注册，发行市值609.93亿元",
    4: "人形机器人两年内从1.9%跃升至51.8%，接棒四足成为第一大收入来源",
    5: "营收三年增长近13倍：2025年+332.6%，2026H1增速回落至+48.5%",
    6: "2024年扭亏、2025年扣非5.9亿：剔除一次性股份支付后盈利成色更足",
    7: "毛利率升至60.1%、经营现金流6.7亿超扣非净利，盈利含金量高",
    8: "研发费率8.5%低于同业均值，但绝对额三年近5倍增长、募投85%加码研发",
    9: "全栈自研+规模量产：四足份额60–70%，人形出货全球第一",
    10: "人形73.6%销往科研教育、工业场景仅9.0%，境外占比降至39.2%",
    11: "四大变量决定增长持续性：产能、场景、海外、大模型（含前瞻表述，非业绩指引）",
    12: "首日+460%后回落近半：8月底市值约2,285亿元，仍对应2025年归母PE约821倍",
    13: "六大风险：估值消化、盈利承压、客户集中、地缘、竞争与解禁",
    14: "数据口径：注册稿为准；七类事项仍需人工核验",
}
SPOT_NUMBERS = ["169,926.93", "332.64%", "226.8%", "51.78%", "59,075.28",
                "60.13%", "219.23", "460.34%", "34,906.55", "609,932.22",
                "0.01809759%", "2,285", "150.80", "65.31%"]

def self_check(path):
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    tol = Emu(int(0.02 * 914400))
    report = []
    ok = True

    n = len(prs.slides._sldIdLst)
    report.append("页数：%d（期望15）%s" % (n, "✓" if n == 15 else "✗"))
    ok &= (n == 15)

    charts = 0
    oob = []
    foot_missing = []
    title_bad = []
    all_text = []
    chart_value_checks = {"chart_mix": 86800, "chart_revenue": 169926.93,
                          "chart_profit": 59075.28, "chart_mktcap": 3417.72}
    chart_value_found = {k: False for k in chart_value_checks}

    for idx, slide in enumerate(prs.slides, start=1):
        texts = []
        has_source = False
        for shape in slide.shapes:
            try:
                l, t = shape.left, shape.top
                w, h = shape.width, shape.height
                if l is not None and (l < -tol or t < -tol or
                                      l + w > sw + tol or t + h > sh + tol):
                    oob.append("第%d页 %s" % (idx, shape.name))
            except Exception:
                pass
            if shape.has_chart:
                charts += 1
                for ser in shape.chart.plots[0].series:
                    for v in ser.values:
                        for k, target in chart_value_checks.items():
                            if shape.name == k and abs(v - target) < 0.01:
                                chart_value_found[k] = True
            if shape.has_text_frame:
                txt = shape.text_frame.text
                texts.append(txt)
                if "资料来源" in txt or "核心资料来源" in txt:
                    has_source = True
                if shape.name == "action_title" and idx in EXPECTED_TITLES:
                    if txt.strip() != EXPECTED_TITLES[idx]:
                        title_bad.append(idx)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        texts.append(cell.text_frame.text)
        if not has_source:
            foot_missing.append(idx)
        all_text.append("\n".join(texts))

    report.append("图表数量：%d（要求≥8）%s" % (charts, "✓" if charts >= 8 else "✗"))
    ok &= (charts >= 8)
    report.append("页脚来源行缺失页：%s" % (foot_missing if foot_missing else "无 ✓"))
    ok &= (not foot_missing)
    report.append("越界形状：%s" % (oob if oob else "无 ✓"))
    ok &= (not oob)
    report.append("行动标题逐字校验：%s" % ("全部一致 ✓" if not title_bad else "第%s页不符 ✗" % title_bad))
    ok &= (not title_bad)
    joined = "\n".join(all_text)
    missing = [s for s in SPOT_NUMBERS if s not in joined]
    report.append("数字抽查（文本%d个）：%s" % (len(SPOT_NUMBERS),
                                               "全部命中 ✓" if not missing else "缺失%s ✗" % missing))
    ok &= (not missing)
    chart_missing = [k for k, v in chart_value_found.items() if not v]
    report.append("数字抽查（图表数据%d个）：%s" % (len(chart_value_checks),
                                                  "全部命中 ✓" if not chart_missing else "缺失%s ✗" % chart_missing))
    ok &= (not chart_missing)
    report.append("总体：%s" % ("通过 ✓" if ok else "存在未通过项 ✗"))
    return "\n".join(report), ok

def make_pdf():
    soffice = shutil.which("soffice")
    if not soffice:
        cand = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        soffice = cand if os.path.exists(cand) else None
    if not soffice:
        print("[PDF] 未检测到 LibreOffice（soffice），跳过 PDF 预览生成。")
        return False
    subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                    "--outdir", SCRATCH, OUT_PPTX], check=True, timeout=300)
    gen = os.path.join(SCRATCH, "宇树科技_公司研究汇报.pdf")
    if os.path.exists(gen):
        os.replace(gen, OUT_PDF)
        print("[PDF] 已生成：%s" % OUT_PDF)
        return True
    return False

if __name__ == "__main__":
    path = build()
    print("[PPTX] 已生成：%s" % path)
    rep, ok = self_check(path)
    print("---- 自检报告 ----")
    print(rep)
    make_pdf()
