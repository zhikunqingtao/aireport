# -*- coding: utf-8 -*-
"""宇树科技内部汇报 PPT 生成。数据仅来自已核验 Excel/Word；图表为原生可编辑图表。"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK, XL_LABEL_POSITION, XL_MARKER_STYLE, XL_AXIS_CROSSES
from pptx.oxml.ns import qn
import copy

# ---------------- 设计系统 ----------------
INK   = RGBColor(0x13,0x31,0x4E)   # 主色 深藏青
P60   = RGBColor(0x3E,0x5E,0x80)
P30   = RGBColor(0x8A,0xA2,0xBC)
P15   = RGBColor(0xD7,0xE0,0xEA)
TEXT  = RGBColor(0x25,0x25,0x25)
AUX   = RGBColor(0x76,0x76,0x76)
HAIR  = RGBColor(0xD8,0xD8,0xD8)
GRID  = RGBColor(0xEA,0xED,0xF1)
LIGHT = RGBColor(0xF4,0xF6,0xF8)
ACC   = RGBColor(0xB8,0x4C,0x3A)   # 单点强调 暖赤
WHITE = RGBColor(0xFF,0xFF,0xFF)
CN, EN = "PingFang SC", "Helvetica Neue"

EMU_W, EMU_H = Inches(13.333), Inches(7.5)
ML = Inches(0.55); CW = Inches(13.333-1.1)
prs = Presentation(); prs.slide_width=EMU_W; prs.slide_height=EMU_H
BLANK = prs.slide_layouts[6]

def slide():
    return prs.slides.add_slide(BLANK)

def _ea(run, cn=CN, en=EN):
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:latin','a:ea','a:cs'):
        e = rPr.find(qn(tag))
        if e is None:
            e = rPr.makeelement(qn(tag), {}); rPr.append(e)
        e.set('typeface', en if tag!='a:ea' else cn)

def box(s, x,y,w,h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(x,y,w,h); tf = tb.text_frame
    tf.word_wrap=True; tf.vertical_anchor=anchor
    tf.margin_left=0; tf.margin_right=0; tf.margin_top=0; tf.margin_bottom=0
    return tb, tf

def para(tf, text, size=13, bold=False, color=TEXT, align=PP_ALIGN.LEFT, first=False,
         space_after=4, space_before=0, line=1.12, cn=CN, en=EN, italic=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment=align; p.space_after=Pt(space_after); p.space_before=Pt(space_before)
    p.line_spacing=line
    r=p.add_run(); r.text=text
    r.font.size=Pt(size); r.font.bold=bold; r.font.italic=italic
    r.font.color.rgb=color; r.font.name=en; _ea(r,cn,en)
    return p

def rect(s,x,y,w,h,fill=None,line=None,lw=0.75):
    sp=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x,y,w,h)
    sp.shadow.inherit=False
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb=fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb=line; sp.line.width=Pt(lw)
    return sp

def line_h(s,x,y,w,color=HAIR,lw=0.75):
    return rect(s,x,y,w,Emu(6350),fill=color)

def title_block(s, eyebrow, title, page):
    rect(s, ML, Inches(0.46), Inches(0.32), Inches(0.055), fill=INK)
    _,tf=box(s, ML, Inches(0.56), Inches(11.5), Inches(0.3))
    para(tf, eyebrow, size=10.5, bold=True, color=P60, first=True, space_after=0)
    _,tf=box(s, ML, Inches(0.86), Inches(12.2), Inches(0.9))
    para(tf, title, size=21, bold=True, color=INK, first=True, line=1.05, space_after=0)
    line_h(s, ML, Inches(1.62), CW, HAIR)

def footer(s, source, page, dark=False):
    c = RGBColor(0xC9,0xD3,0xE0) if dark else AUX
    line_h(s, ML, Inches(7.06), CW, RGBColor(0x39,0x4B,0x63) if dark else HAIR)
    _,tf=box(s, ML, Inches(7.12), Inches(9.6), Inches(0.3))
    para(tf, source, size=8, color=c, first=True, space_after=0)
    _,tf=box(s, Inches(10.4), Inches(7.12), Inches(2.38), Inches(0.3))
    para(tf, f"宇树科技 688836.SH    {page:02d}", size=8, color=c, align=PP_ALIGN.RIGHT, first=True, space_after=0)

# ---------------- 图表样式工具 ----------------
def _style_axes(chart, num_fmt='0.0'):
    chart.font.size=Pt(9); chart.font.name=EN; chart.font.color.rgb=AUX
    try:
        ca=chart.category_axis; ca.tick_labels.font.size=Pt(9.5); ca.tick_labels.font.color.rgb=TEXT
        ca.format.line.color.rgb=HAIR; ca.major_tick_mark=XL_TICK_MARK.NONE; ca.minor_tick_mark=XL_TICK_MARK.NONE
    except Exception: pass
    try:
        va=chart.value_axis; va.has_major_gridlines=True
        va.major_gridlines.format.line.color.rgb=GRID; va.major_gridlines.format.line.width=Pt(0.5)
        va.format.line.fill.background(); va.major_tick_mark=XL_TICK_MARK.NONE
        va.tick_labels.font.size=Pt(8.5); va.tick_labels.number_format=num_fmt; va.tick_labels.number_format_is_linked=False
    except Exception: pass

def _fill_series(plot, colors):
    for i,sr in enumerate(plot.series):
        sr.format.fill.solid(); sr.format.fill.fore_color.rgb=colors[i%len(colors)]
        sr.format.line.fill.background()

def _end_labels(plot, color=TEXT, fmt='0.00', size=9, bold=True):
    for sr in plot.series:
        pts=list(sr.points); n=len(pts)
        for j,pt in enumerate(pts):
            if j==n-1:
                dl=pt.data_label; dl.show_value=True; dl.number_format=fmt; dl.number_format_is_linked=False
                dl.font.size=Pt(size); dl.font.bold=bold; dl.font.color.rgb=color
                dl.position=XL_LABEL_POSITION.OUTSIDE_END

def _line_series(plot, colors, width=2.4, markers=True, labels=True, fmt='0.0%'):
    for i,sr in enumerate(plot.series):
        c=colors[i%len(colors)]
        sr.format.line.color.rgb=c; sr.format.line.width=Pt(width); sr.smooth=False
        if markers:
            sr.marker.style=XL_MARKER_STYLE.CIRCLE; sr.marker.size=5
            sr.marker.format.fill.solid(); sr.marker.format.fill.fore_color.rgb=c
            sr.marker.format.line.color.rgb=c
        if labels:
            pts=list(sr.points)
            for j,pt in enumerate(pts):
                if j==len(pts)-1:
                    dl=pt.data_label; dl.show_value=True; dl.number_format=fmt; dl.number_format_is_linked=False
                    dl.font.size=Pt(9); dl.font.bold=True; dl.font.color.rgb=c
                    dl.position=XL_LABEL_POSITION.ABOVE

def add_bar(s, x,y,w,h, cats, series, colors, stacked=False, num_fmt='0.0', end_fmt='0.00'):
    cd=CategoryChartData(); cd.categories=cats
    for nm,vals in series: cd.add_series(nm, vals)
    typ = XL_CHART_TYPE.COLUMN_STACKED if stacked else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf=s.shapes.add_chart(typ,x,y,w,h,cd); ch=gf.chart
    ch.has_legend=True; ch.legend.position=XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout=False
    ch.legend.font.size=Pt(9)
    plot=ch.plots[0]; plot.gap_width=70 if not stacked else 0; plot.overlap=100 if stacked else 0
    _fill_series(plot, colors); _style_axes(ch,num_fmt); _end_labels(plot,fmt=end_fmt)
    return ch

def _ctag(t): return qn('c:'+t)

def _combine_twin_axis(bar_gf, line_gf):
    """把折线图并入柱图形成双轴组合图，并移除多余的折线图形框。"""
    bpa = bar_gf.chart._chartSpace.find('.//'+_ctag('plotArea'))
    lpa = line_gf.chart._chartSpace.find('.//'+_ctag('plotArea'))
    bplot = bpa.find(_ctag('barChart')); lplot = lpa.find(_ctag('lineChart'))
    b_ids=[e.get('val') for e in bplot.findall(_ctag('axId'))]
    l_ids=[e.get('val') for e in lplot.findall(_ctag('axId'))]
    b_cat, b_val = b_ids[0], b_ids[1]
    l_cat, l_val = l_ids[0], l_ids[1]
    # 折线图：类别轴与柱图共享，数值轴换一个唯一新 id
    NEW='990099'
    lplot.findall(_ctag('axId'))[0].set('val', b_cat)
    lplot.findall(_ctag('axId'))[1].set('val', NEW)
    lvalax=None
    for ax in lpa.findall(_ctag('valAx')):
        if ax.find(_ctag('axId')).get('val')==l_val: lvalax=ax
    lvalax.find(_ctag('axId')).set('val', NEW)
    lvalax.find(_ctag('crossAx')).set('val', b_cat)
    for g in lvalax.findall(_ctag('majorGridlines')): lvalax.remove(g)
    # 次坐标显式放右侧，并在 crossAx 之后按 schema 顺序写入 crosses=max
    lvalax.find(_ctag('axPos')).set('val','r')
    old=lvalax.find(_ctag('crosses'))
    if old is not None: lvalax.remove(old)
    crossax=lvalax.find(_ctag('crossAx'))
    crosses=lvalax.makeelement(_ctag('crosses'),{'val':'max'}); crossax.addnext(crosses)
    # 共享类别轴：删除折线自带 catAx
    for ax in list(lpa.findall(_ctag('catAx'))): lpa.remove(ax)
    # 迁移元素：lineChart 紧随 barChart；次值轴紧随主值轴
    bplot.addnext(lplot)
    bpa.find(_ctag('valAx')).addnext(lvalax)
    # 删除折线图形框，并断开其 slide 关系（使孤立图表部件不被打包）
    rid=None
    cchart=line_gf._element.find('.//'+qn('c:chart'))
    if cchart is not None: rid=cchart.get(qn('r:id'))
    sp=line_gf._element; sp.getparent().remove(sp)
    if rid:
        bar_gf.part.drop_rel(rid)
    return bar_gf.chart

def add_combo(s,x,y,w,h,cats,bar_series,bar_colors,line_series,line_colors,bar_fmt='0.00',line_fmt='0.0%',secondary=True):
    # 柱
    cd=CategoryChartData(); cd.categories=cats
    for nm,vals in bar_series: cd.add_series(nm,vals)
    gf=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,x,y,w,h,cd); bar=gf.chart
    bar.has_legend=True; bar.legend.position=XL_LEGEND_POSITION.BOTTOM; bar.legend.include_in_layout=False; bar.legend.font.size=Pt(9)
    bp=bar.plots[0]; bp.gap_width=55; _fill_series(bp,bar_colors); _style_axes(bar,bar_fmt)
    _end_labels(bp,fmt='0.00')
    # 线
    ld=CategoryChartData(); ld.categories=cats
    for nm,vals in line_series: ld.add_series(nm,vals)
    gf2=s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS,x,y,w,h,ld); ln=gf2.chart
    _line_series(ln.plots[0],line_colors,fmt=line_fmt)
    lva=ln.value_axis
    lva.crosses=XL_AXIS_CROSSES.MAXIMUM
    lva.tick_labels.font.size=Pt(8.5); lva.tick_labels.number_format=line_fmt; lva.tick_labels.number_format_is_linked=False
    lva.has_major_gridlines=False
    return _combine_twin_axis(gf,gf2)

def insight(s, x, y, w, items, gap=0.78, num_size=24):
    """侧栏解读：每条 = 小色条 + 加粗短判断 + 说明"""
    for i,(head,body) in enumerate(items):
        yy=y+Inches(i*gap)
        rect(s,x,yy+Inches(0.05),Inches(0.07),Inches(0.34),fill=INK)
        _,tf=box(s,x+Inches(0.18),yy,w-Inches(0.18),Inches(gap-0.06))
        para(tf,head,size=12.5,bold=True,color=INK,first=True,space_after=2,line=1.05)
        para(tf,body,size=10.5,color=TEXT,line=1.12,space_after=0)

# ============================================================ P1 封面
s=slide()
s.shapes.add_picture("ppt_assets/cover_hero.png",0,0,EMU_W,EMU_H)
# 左侧深色渐隐条（保证文字可读）
ov=rect(s,0,0,Inches(8.2),EMU_H,fill=RGBColor(0x0B,0x1E,0x33)); 
ov.fill.fore_color.rgb=RGBColor(0x0B,0x1E,0x33)
# 透明度
sp=ov.fill._xPr.find(qn('a:solidFill')).find(qn('a:srgbClr'))
a=sp.makeelement(qn('a:alpha'),{'val':'52000'}); sp.append(a)
rect(s,Inches(0.7),Inches(2.35),Inches(0.55),Inches(0.07),fill=RGBColor(0x7F,0xB0,0xE0))
_,tf=box(s,Inches(0.7),Inches(2.6),Inches(7.4),Inches(2.2))
para(tf,"宇树科技（688836.SH）",size=18,bold=True,color=RGBColor(0xBF,0xD3,0xE8),first=True,space_after=8)
para(tf,"经营与财务表现分析",size=40,bold=True,color=WHITE,space_after=6,line=1.05)
para(tf,"高增长换挡期：人形切换、扣非盈利与费用扩张的赛跑",size=15,color=RGBColor(0xD7,0xE0,0xEA),space_after=0)
_,tf=box(s,Inches(0.7),Inches(6.35),Inches(8),Inches(0.6))
para(tf,"内部汇报  |  资料截止 2026-08-30  |  金额单位：人民币万元（图表换算为亿元）  |  A=已实现，E=预测",
     size=10.5,color=RGBColor(0xB8,0xC6,0xD8),first=True,space_after=0)

# ============================================================ P2 目录
s=slide()
title_block(s,"CONTENTS","目录",2)
secs=[("01","业务与产品结构","主营定位 · 产品/量价/地区结构"),
      ("02","收入与盈利变化","增长换挡 · 扣非盈利 · 2026H1 · 现金流"),
      ("03","研发与竞争力","研发投入 · 五项竞争优势"),
      ("04","增长变量与风险","事实与计划分列 · 六项主要风险"),
      ("05","结论与资料来源","核心判断 · 口径说明 · 来源清单")]
x0=ML; y0=Inches(2.05); cw=Inches(6.0); ch=Inches(1.25)
for i,(n,t,d) in enumerate(secs):
    col=i//3; row=i%3
    x=x0+col*Inches(6.25); y=y0+row*Inches(1.5)
    _,tf=box(s,x,y,Inches(1.1),Inches(1.0))
    para(tf,n,size=34,bold=True,color=P30,first=True,en=EN)
    _,tf=box(s,x+Inches(1.15),y+Inches(0.06),cw-Inches(1.2),Inches(1.1))
    para(tf,t,size=17,bold=True,color=INK,first=True,space_after=3)
    para(tf,d,size=10.5,color=AUX,space_after=0)
    line_h(s,x+Inches(1.15),y+Inches(0.92),Inches(4.6),HAIR)
footer(s,"来源：本汇报数据均取自上交所披露文件及公司公开资料，详见末页来源清单",2)

# ============================================================ P3 核心判断
s=slide()
title_block(s,"EXECUTIVE SUMMARY","核心判断：高增长仍在，但进入“收入快、扣非承压”的换挡期",3)
takeaways=[
 ("两年营收 CAGR 约 226.8%，增速逐期回落","2023→2025 营收 1.59→16.99 亿元；同比由 2025 全年 +332.6% 回落至 2026H1 +48.5%。"),
 ("人形取代四足成为第一大产品","人形收入占主营 1.88%→51.78%，销量 5→5,215 台，单价 59.34→16.64 万元，量增价减。"),
 ("盈利质量看扣非：2025 扣非 5.91 亿、扣非净利率 34.8%","归母仅 2.78 亿，差额 -3.13 亿为股份支付等非经常损失；主营毛利率升至 60.13%。"),
 ("2026 利润端承压，费用扩张是主因","2026H1 扣非 2.44 亿、同比 -19.34%；研发与销售费用快速增加，CFO 同比 -32.53%。"),
]
y=Inches(1.95)
for i,(h,b) in enumerate(takeaways):
    yy=y+Inches(i*1.22)
    _,tf=box(s,ML,yy,Inches(0.55),Inches(0.6))
    para(tf,f"0{i+1}",size=20,bold=True,color=P30,first=True,en=EN)
    _,tf=box(s,ML+Inches(0.75),yy,Inches(11.4),Inches(1.1))
    cc = ACC if i==3 else INK
    para(tf,h,size=15,bold=True,color=cc,first=True,space_after=3,line=1.05)
    para(tf,b,size=11.5,color=TEXT,line=1.15,space_after=0)
    if i<3: line_h(s,ML+Inches(0.75),yy+Inches(1.02),Inches(11.3),HAIR)
footer(s,"来源：上市保荐书（注册稿）、上市公告书（底稿 S2/S5）；CAGR、占比、净利率由原始数据现算",3)

# ============================================================ P4 公司速览
s=slide()
title_block(s,"COMPANY OVERVIEW","公司速览：全球通用机器人龙头，2026-08-19 登陆科创板",4)
_,tf=box(s,ML,Inches(1.95),Inches(6.0),Inches(4.6))
para(tf,"主营业务",size=12,bold=True,color=P60,first=True,space_after=4)
para(tf,"高性能通用人形机器人、四足机器人、机器人组件及具身智能模型的研发、生产与销售，覆盖“本体—核心零部件—具身智能模型”全栈。",size=13,color=TEXT,space_after=12,line=1.25)
para(tf,"产品矩阵",size=12,bold=True,color=P60,space_after=4)
para(tf,"人形：H1/G1 等系列，价格带下探至 10 万元级；四足：Go2/B2 等系列，为当前收入基本盘；另对外销售机器人组件。",size=13,color=TEXT,space_after=12,line=1.25)
para(tf,"治理结构",size=12,bold=True,color=P60,space_after=4)
para(tf,"设置表决权差异安排，实控人王兴兴发行后持股 21.44%；按“预计市值≥100 亿元”科创板标准上市。",size=13,color=TEXT,line=1.25,space_after=0)
# 右侧发行数据
rx=Inches(7.05); rw=Inches(5.73)
rect(s,rx,Inches(1.95),rw,Inches(4.55),fill=LIGHT)
rect(s,rx,Inches(1.95),Inches(0.08),Inches(4.55),fill=INK)
_,tf=box(s,rx+Inches(0.32),Inches(2.18),rw-Inches(0.5),Inches(0.4))
para(tf,"本次发行关键数据",size=13,bold=True,color=INK,first=True)
facts=[("发行价格","150.80 元/股"),("发行数量 / 占比","4,044.6434 万股 / 发行后 10.00%"),
       ("募资总额 / 净额","60.99 / 59.17 亿元"),("发行价对应市值","609.93 亿元"),
       ("发行市盈率","219.23 倍（媒体口径，待核）"),("上市前最近一轮估值","2025-06 Pre-IPO 投后 127 亿元")]
yy=Inches(2.72)
for k,v in facts:
    _,tf=box(s,rx+Inches(0.32),yy,Inches(2.5),Inches(0.4)); para(tf,k,size=10.5,color=AUX,first=True,space_after=0)
    _,tf=box(s,rx+Inches(2.75),yy,rw-Inches(3.0),Inches(0.4)); para(tf,v,size=11.5,bold=True,color=TEXT,first=True,space_after=0)
    yy=yy+Inches(0.6)
footer(s,"来源：发行公告/上市公告书/上市保荐书（底稿 S2/S5/S6）；发行市盈率需以发行公告原文核验",4)

# ============================================================ P5 产品结构
s=slide()
title_block(s,"PRODUCT MIX","人形机器人两年间从 1.9% 升至 51.8%，取代四足成为第一大产品",5)
cats=['2023A','2024A','2025A']
prod=[("人形",[0.03,1.07,8.68]),("四足",[1.19,2.31,6.98]),("组件及其他",[0.35,0.50,1.11])]
add_bar(s,ML,Inches(2.0),Inches(7.0),Inches(4.6),cats,prod,[INK,P60,P30],stacked=True,num_fmt='0',end_fmt='0.00')
_,tf=box(s,ML,Inches(6.55),Inches(7),Inches(0.3)); para(tf,"图1  主营业务收入分产品（亿元，堆叠）",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("人形：第一增长曲线","296.71 万→8.68 亿元，占主营 51.78%。"),
 ("四足：基本盘但占比回落","6.98 亿元、占比由 75.78% 降至 41.62%。"),
 ("组件及其他","2025 年轧差约 1.11 亿元、占约 6.6%，精确拆分待核。"),
 ("结论","结构切换完成，人形决定下一阶段弹性。"),
],gap=1.05)
footer(s,"来源：招股说明书（注册稿）及研报转引（底稿 S1/S7/S8）；万元换算为亿元，占比以主营收入为分母",5)

# ============================================================ P6 量增价减
s=slide()
title_block(s,"VOLUME × PRICE","人形销量爆发至 5,215 台，平均单价降至 16.64 万元——以价换量",6)
add_combo(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,
          [("人形销量（台）",[5,412,5215])],[INK],
          [("人形平均单价（万元/台）",[59.34,26.04,16.64])],[ACC],
          bar_fmt='#,##0',line_fmt='0.00')
_,tf=box(s,ML,Inches(6.55),Inches(7.2),Inches(0.3)); para(tf,"图2  人形机器人销量（柱，左轴）与平均单价（线，右轴，披露口径）",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("销量三年千倍级增长","5→412→5,215 台；公司称 2025 纯人形出货超 5,500 台、全球第一。"),
 ("单价持续下探","59.34→26.04→16.64 万元/台，G1 下探至 10 万元级，扩大装机基数。"),
 ("四足同步量增价减","销量 3,121→23,037 台，单价 3.83→3.03 万元，三年累计超 3.3 万台。"),
],gap=1.25)
footer(s,"来源：底稿 S1/S7/S8；销量为确认收入口径，出货量为公司口径，二者统计范围不同",6)

# ============================================================ P7 地区
s=slide()
title_block(s,"GEOGRAPHY","2025 年境内收入反超：占比 56.35%，国内人形需求集中放量",7)
reg=[("境内",[0.70,1.71,9.44]),("境外",[0.88,2.16,7.32])]
add_bar(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,reg,[INK,P30],stacked=True,num_fmt='0',end_fmt='0.00')
_,tf=box(s,ML,Inches(6.55),Inches(7),Inches(0.3)); para(tf,"图3  主营业务收入分地区（亿元，100% 堆叠）",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("2023–2024 境外为主","境外占主营 55.63%→55.74%。"),
 ("2025 境内反超","境内 9.44 亿（56.35%），境外 7.32 亿（43.65%）。"),
 ("驱动与风险","国内人形需求与品牌外溢拉动；海外仍为重要市场，关注汇率与外销结算。"),
],gap=1.25)
footer(s,"来源：招股意向书/招股说明书（底稿 S4/S1）；2024 年境内为主营减境外轧差数",7)

# ============================================================ P8 收入与换挡
s=slide()
title_block(s,"REVENUE GROWTH","营收两年 CAGR 约 226.8%，但同比增速已从 332.6% 换挡至 48.5%",8)
add_combo(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,
          [("营业收入（亿元）",[1.59,3.93,16.99])],[INK],
          [("营业收入同比",[None,1.4682,3.3264])],[P60],
          bar_fmt='0',line_fmt='0.0%')
_,tf=box(s,ML,Inches(6.55),Inches(7.2),Inches(0.3)); para(tf,"图4  营业收入（柱，左轴）与同比增速（线，右轴）；2023 为基期无同比",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("两年复合增速 226.78%","2024、2025 同比 +146.82%、+332.64%。"),
 ("2026 增速继续回落","2026Q1 +68.49%、2026H1 +48.54%。"),
 ("公司归因","基数抬高、行业热度缓和、竞争加剧。"),
 ("含义","高斜率阶段过去，进入中高速增长区间。"),
],gap=1.05)
footer(s,"来源：上市保荐书/落实函回复/上市公告书（底稿 S2/S3/S5）；2026H1 未经审计",8)

# ============================================================ P9 盈利质量
s=slide()
title_block(s,"PROFIT QUALITY","扣非盈利强劲，归母被股份支付扰动：分析盈利应以扣非为主",9)
pr=[("归母净利润",[-0.11,0.95,2.78]),("扣非归母净利润",[-0.18,0.78,5.91])]
add_combo(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,pr,[P30,INK],
          [("主营毛利率",[0.4422,0.5674,0.6013])],[P60],bar_fmt='0.00',line_fmt='0.0%')
_,tf=box(s,ML,Inches(6.55),Inches(7.2),Inches(0.3)); para(tf,"图5  归母/扣非归母（亿元，柱）与主营毛利率（线）",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("毛利率持续抬升","44.22%→56.74%→60.13%，全栈自研与零部件自产支撑。"),
 ("2025 扣非净利率 34.8%","扣非加权 ROE 28.70%，经常性盈利能力强。"),
 ("归母低于扣非 3.13 亿","非经常性净损失 -31,254.23 万元，主要为股份支付。"),
 ("口径提示","2025 基本 EPS 0.76 元；评估盈利看扣非。"),
],gap=1.05)
footer(s,"来源：上市保荐书/落实函回复（底稿 S2/S3）；非经常性损益=归母-扣非现算",9)

# ============================================================ P10 2026H1 E vs A
s=slide()
title_block(s,"1H2026: FORECAST vs ACTUAL","2026H1 收入略超业绩预告上限，扣非落在区间内但同比 -19.34%",10)
# 原生表格
rows=[["指标（万元）","预测下限(E)","预测上限(E)","实际(A)","对照"],
      ["营业收入","105,200.00","112,800.00","115,224.56","略超上限"],
      ["归母净利润","25,800.00","30,600.00","27,399.99","区间内"],
      ["扣非归母净利润","23,600.00","28,300.00","24,393.03","区间内"]]
tbl_x, tbl_y = ML, Inches(2.05)
gtbl=s.shapes.add_table(4,5,tbl_x,tbl_y,Inches(7.25),Inches(2.5)).table
gtbl.columns[0].width=Inches(1.95)
for c in range(1,4): gtbl.columns[c].width=Inches(1.4)
gtbl.columns[4].width=Inches(1.1)
for r in range(4):
    for c in range(5):
        cell=gtbl.cell(r,c); cell.text=rows[r][c]
        p=cell.text_frame.paragraphs[0]; run=p.runs[0]
        run.font.name=EN; _ea(run)
        run.font.size=Pt(10.5 if r else 10)
        if r==0:
            run.font.bold=True; run.font.color.rgb=WHITE; cell.fill.solid(); cell.fill.fore_color.rgb=INK
        else:
            run.font.color.rgb=TEXT; cell.fill.solid(); cell.fill.fore_color.rgb=WHITE if r%2 else LIGHT
            run.font.bold = (c==0)
        p.alignment=PP_ALIGN.LEFT if c==0 else PP_ALIGN.CENTER
        cell.vertical_anchor=MSO_ANCHOR.MIDDLE
        cell.margin_top=Pt(3); cell.margin_bottom=Pt(3)
_,tf=box(s,ML,Inches(4.75),Inches(7.3),Inches(0.3)); para(tf,"表1  2026H1 业绩预告（2026-05 上会稿，预测）与上市公告书实际对照",size=9,color=AUX,first=True)
insight(s,Inches(8.35),Inches(2.3),Inches(4.4),[
 ("收入端超预期","实际 11.52 亿元，高于预测上限 11.28 亿。"),
 ("利润端同比承压","扣非 2.44 亿、同比 -19.34%（2026Q1 曾 -52.55%）。"),
 ("费用是主因","上半年研发费用同比 +0.82 亿；销售费用 1.64 亿（品牌推广+扩编）。"),
 ("归母扭亏含低基数","上年同期 -3,202.45 万，含约 3.49 亿股份支付。"),
],gap=1.02)
footer(s,"来源：上会稿业绩预告（E）与 2026-08-17 上市公告书（A，未经审计）；预测不作为已实现事实",10)

# ============================================================ P11 现金流与资产负债
s=slide()
title_block(s,"CASH FLOW & BALANCE SHEET","经营现金流三年抬升至 6.70 亿、低杠杆；2026H1 末负债率回升至 25.11%",11)
add_combo(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,
          [("经营现金流净额（亿元）",[0.05,1.92,6.70])],[INK],
          [("合并资产负债率",[0.2357,0.1619,0.1882])],[P60],
          bar_fmt='0.00',line_fmt='0.0%')
_,tf=box(s,ML,Inches(6.55),Inches(7.2),Inches(0.3)); para(tf,"图6  经营现金流净额（柱）与合并资产负债率（线）",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("现金含金量高","2025 CFO/营收约 39.4%，现金对利润覆盖充分。"),
 ("整体低杠杆","2023–2025 资产负债率 23.57%/16.19%/18.82%。"),
 ("2026H1 末变化","总资产 384,546.94 万、较年初 +19.85%；负债率 25.11%。"),
 ("需跟踪","H1 CFO 2.32 亿、同比 -32.53%，合同/应付/租赁负债增加。"),
],gap=1.05)
footer(s,"来源：上市保荐书/上市公告书（底稿 S2/S5）；2026H1 未经审计",11)

# ============================================================ P12 研发
s=slide()
title_block(s,"R&D","研发绝对额三年升至 1.45 亿，费率因规模放大降至 8.53%——是摊薄非收缩",12)
add_combo(s,ML,Inches(2.0),Inches(7.0),Inches(4.55),cats,
          [("研发费用（亿元）",[0.50,0.70,1.45])],[INK],
          [("研发费用率",[0.3139,0.1783,0.0853])],[P60],
          bar_fmt='0.00',line_fmt='0.0%')
_,tf=box(s,ML,Inches(6.55),Inches(7.2),Inches(0.3)); para(tf,"图7  研发费用（柱）与研发费用率（线）；三年累计 2.65 亿元",size=9,color=AUX,first=True)
insight(s,Inches(7.95),Inches(2.15),Inches(4.8),[
 ("投入持续加大","4,995.18→7,001.70→14,496.56 万元。"),
 ("费率下降是规模效应","31.39%→17.83%→8.53%。"),
 ("人员结构","2025 年末 516 人，研发 184 人、占 35.66%。"),
 ("募投倾斜研发","原拟募资约 42.02 亿，模型/本体/新产品约 35.77 亿、占约 85%。"),
],gap=1.05)
footer(s,"来源：上市保荐书（底稿 S2）、募投项目（底稿 S1，分项为约数、精确额待核）",12)

# ============================================================ P13 竞争优势
s=slide()
title_block(s,"COMPETITIVE EDGE","五项竞争优势：技术垂直整合 × 出货规模 × 财务弹性",13)
adv=[("01","全栈自研支撑高毛利","主营毛利率 60.13%，电机/控制器/感知算法/整机/具身模型垂直自研，为降价与再投入留出空间。"),
     ("02","出货规模全球领先","2025 人形确认收入 5,215 台、公司称纯人形出货超 5,500 台全球第一；四足三年超 3.3 万台。"),
     ("03","产销衔接顺畅","2025 年前三季度人形产销率超 95%，基本满产满销，需求支撑现有产能。"),
     ("04","价格带下探拓宽市场","人形单价降至 16.64 万元、G1 进入 10 万元级，扩大装机与开发者生态。"),
     ("05","报表稳健、弹药充足","2025 负债率 18.82%、CFO 6.70 亿；IPO 募资净额 59.17 亿元，支撑研发与制造投入。")]
y=Inches(1.98)
for i,(n,h,b) in enumerate(adv):
    yy=y+Inches(i*0.98)
    _,tf=box(s,ML,yy,Inches(0.8),Inches(0.6)); para(tf,n,size=20,bold=True,color=P30,first=True,en=EN)
    _,tf=box(s,ML+Inches(0.95),yy,Inches(11.2),Inches(0.9))
    para(tf,h,size=14,bold=True,color=INK,first=True,space_after=2)
    para(tf,b,size=11,color=TEXT,line=1.12,space_after=0)
    if i<4: line_h(s,ML+Inches(0.95),yy+Inches(0.82),Inches(11.2),HAIR)
footer(s,"来源：上市保荐书/招股说明书/发行公告（底稿 S1/S2/S6）；同业量化对比数据不足，不作扩展结论",13)

# ============================================================ P14 增长变量
s=slide()
title_block(s,"GROWTH DRIVERS","增长变量：已兑现的事实与待验证的计划分列",14)
# 左 事实
lx=ML; lw=Inches(6.0)
rect(s,lx,Inches(2.0),lw,Inches(0.5),fill=INK)
_,tf=box(s,lx+Inches(0.2),Inches(2.07),lw,Inches(0.4)); para(tf,"已兑现的事实（A）",size=13,bold=True,color=WHITE,first=True)
facts2=[("人形放量","2025 占主营 51.78%、销量 5,215 台。"),
        ("境内市场反超","2025 境内占比升至 56.35%，境外绝对额仍增至 7.32 亿。"),
        ("场景结构","四足场景较均衡；人形 2025 1-9M 科研教育占 73.6%。"),
        ("资金到位","IPO 募资净额 59.17 亿元，相对原拟投项目超募。")]
yy=Inches(2.7)
for h,b in facts2:
    _,tf=box(s,lx,yy,lw,Inches(0.9))
    para(tf,h,size=12.5,bold=True,color=INK,first=True,space_after=2)
    para(tf,b,size=11,color=TEXT,line=1.12,space_after=0); yy=yy+Inches(0.92)
# 右 计划
rx=Inches(6.85); rw=Inches(5.93)
rect(s,rx,Inches(2.0),rw,Inches(0.5),fill=P60)
_,tf=box(s,rx+Inches(0.2),Inches(2.07),rw,Inches(0.4)); para(tf,"待验证的计划 / 变量（E）",size=13,bold=True,color=WHITE,first=True)
plans=[("场景拓宽","人形由科研教育向行业应用（当前仅约 9.01%）渗透的速度。"),
       ("募投研发转化","模型/本体/新产品约 35.77 亿投入能否转化为产品力。"),
       ("制造基地产能","达产规划人形 7.5 万、四足 11.5 万台/年——为规划，非已实现产能或产量。"),
       ("海外扩张","渠道与本地化进展，及关税/汇率影响。")]
yy=Inches(2.7)
for h,b in plans:
    _,tf=box(s,rx,yy,rw,Inches(0.9))
    para(tf,h,size=12.5,bold=True,color=P60,first=True,space_after=2)
    para(tf,b,size=11,color=TEXT,line=1.12,space_after=0); yy=yy+Inches(0.92)
footer(s,"来源：招股说明书/上市保荐书（底稿 S1/S2/S7）；规划与预测均不作为已实现事实",14)

# ============================================================ P15 风险
s=slide()
title_block(s,"KEY RISKS","六项主要风险：场景集中、价格下行与费用扩张最值得盯紧",15)
risks=[("商业化场景集中","人形 2025 1-9M 约 73.6% 收入来自科研教育，行业应用仅约 9.01%。",True),
       ("价格下行 / 竞争加剧","两类产品单价逐年下行，价格战或进一步压缩单价与毛利。",True),
       ("股份支付扰动表观利润","2025 非经常性净损失 -3.13 亿，后续股权激励或继续扰动归母。",False),
       ("费用扩张压制扣非","2026H1 扣非同比 -19.34%、CFO 同比 -32.53%，费用刚性下利润率承压。",False),
       ("高估值波动","发行市值 609.93 亿、媒体口径 PE 219.23 倍（待核），对业绩兑现高度敏感。",False),
       ("外包/供应链与外销","劳务外包费用升至 6,802.65 万；境外占比 43.65%，汇率与供应链风险并存。",False)]
x0=ML; y0=Inches(2.0); cw=Inches(3.95); chh=Inches(2.15)
for i,(h,b,hot) in enumerate(risks):
    col=i%3; row=i//3
    x=x0+col*Inches(4.07); y=y0+row*Inches(2.4)
    line_h(s,x,y,cw,INK if hot else HAIR, 1.5 if hot else 0.75)
    _,tf=box(s,x,y+Inches(0.12),cw,chh)
    para(tf,f"{i+1:02d}  {h}",size=13,bold=True,color=ACC if hot else INK,first=True,space_after=5,line=1.1)
    para(tf,b,size=10.5,color=TEXT,line=1.2,space_after=0)
footer(s,"来源：招股说明书/上市保荐书/上市公告书（底稿 S1/S2/S5）；暖赤为当前最需盯紧的两项",15)

# ============================================================ P16 结论 + 来源
s=slide()
s.shapes.add_picture("ppt_assets/closing_hero.png",0,0,EMU_W,EMU_H)
ov=rect(s,0,0,EMU_W,EMU_H,fill=RGBColor(0x0A,0x1B,0x30))
sp=ov.fill._xPr.find(qn('a:solidFill')).find(qn('a:srgbClr')); sp.append(sp.makeelement(qn('a:alpha'),{'val':'42000'}))
rect(s,Inches(0.7),Inches(0.7),Inches(0.5),Inches(0.06),fill=RGBColor(0x7F,0xB0,0xE0))
_,tf=box(s,Inches(0.7),Inches(0.9),Inches(12),Inches(0.6)); para(tf,"结论：成长仍在，重心从“增速”转向“盈利质量兑现”",size=23,bold=True,color=WHITE,first=True)
concl=["产品：完成四足→人形的结构切换，人形是下一阶段核心弹性；",
       "盈利：扣非盈利能力强（2025 扣非净利率 34.8%、毛利率 60.13%），但费用扩张使 2026 扣非承压；",
       "跟踪：人形行业场景渗透、募投与制造基地达产进度（规划非已实现）、扣非利润率能否企稳。"]
_,tf=box(s,Inches(0.7),Inches(1.75),Inches(12),Inches(1.7))
for i,c in enumerate(concl): para(tf,c,size=13.5,color=RGBColor(0xDD,0xE6,0xF0),first=(i==0),space_after=6,line=1.2)
# 来源清单
_,tf=box(s,Inches(0.7),Inches(3.7),Inches(12),Inches(0.35)); para(tf,"资料来源与口径",size=13,bold=True,color=WHITE,first=True)
src=("S1 招股说明书（注册稿，上交所 auditId=2178）；S2 上市保荐书（注册稿）；S3 审核落实函回复；S4 招股意向书；S5 上市公告书；S6 发行/投资风险公告；"
     "S7 浦银国际、S8 兴业证券、S9 国信证券研报转引；S10 东方财富/证券时报数据中心（交叉核对）；S11 公司官网。\n"
     "口径：金额除注明外为万元（图表换算亿元）；A=已实现（2023–2025 经审计、2026Q1 经审阅、2026H1 上市公告书披露且未经审计），E=预测；年度采用注册稿口径；资料截止 2026-08-30，其后行情不纳入。本页及全文不构成投资建议。")
_,tf=box(s,Inches(0.7),Inches(4.15),Inches(12),Inches(2.6)); para(tf,src,size=9.5,color=RGBColor(0xC2,0xCF,0xDF),first=True,line=1.3,space_after=0)
_,tf=box(s,Inches(0.7),Inches(7.05),Inches(12),Inches(0.3)); para(tf,"宇树科技 688836.SH  |  内部汇报  |  16",size=8.5,color=RGBColor(0x9F,0xB0,0xC4),first=True)

OUT="/Users/guoqingtao/Desktop/AI办公评测/豆包办公/宇树科技内部汇报_截至20260830.pptx"
prs.save(OUT); print("SAVED",OUT,"slides=",len(prs.slides._sldIdLst))
