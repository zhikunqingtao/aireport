# -*- coding: utf-8 -*-
"""宇树科技公司研究报告生成脚本。数据仅来自已核验 Excel 底稿，派生比率由原值现算。"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import numbers

OUT = "/Users/guoqingtao/Desktop/AI办公评测/豆包办公/宇树科技公司研究报告_截至20260830.docx"
CN, CN_H, EN = "宋体", "黑体", "Arial"
BLACK = RGBColor(0, 0, 0)
HDR_FILL = "D9D9D9"

# ============ 底层数据（唯一来源：已核验底稿；万元） ============
rev = {2023: 15913.44, 2024: 39277.07, 2025: 169926.93}
main_rev = {2023: 15753.65, 2024: 38727.28, 2025: 167611.09}
ni = {2023: -1114.51, 2024: 9547.47, 2025: 27821.05}
nd = {2023: -1801.91, 2024: 7847.65, 2025: 59075.28}
gm = {2023: 0.4422, 2024: 0.5674, 2025: 0.6013}
roe = {2023: -0.0592, 2024: 0.086, 2025: 0.287}
rd = {2023: 4995.18, 2024: 7001.70, 2025: 14496.56}
sell = {2023: 3771.83, 2024: 5915.85, 2025: 14120.93}  # 2025 为反推约数(待核)
cfo = {2023: 494.25, 2024: 19239.13, 2025: 66998.18}
asset = {2023: 39127.15, 2024: 152786.94, 2025: 320853.83}
debt_ratio = {2023: 0.2357, 2024: 0.1619, 2025: 0.1882}
prod = {"人形": {2023: 296.71, 2024: 10689.76, 2025: 86783.19},
        "四足": {2023: 11938.09, 2024: 23054.37, 2025: 69762.56},
        "组件及其他": {2023: 2692.34 + 826.51, 2024: 4453.82 + 529.33, 2025: 167611.09 - 86783.19 - 69762.56}}
vol = {"人形": {2023: 5, 2024: 412, 2025: 5215}, "四足": {2023: 3121, 2024: 7136, 2025: 23037}}
price_disc = {"人形": {2023: 59.34, 2024: 26.04, 2025: 16.64}, "四足": {2023: 3.83, 2024: 3.23, 2025: 3.03}}
region = {"境内": {2023: 6989.41, 2024: 17116.54, 2025: 94445.56},
          "境外": {2023: 8764.24, 2024: 21610.74, 2025: 73165.53}}
YEARS = [2023, 2024, 2025]

def pct(x, d=1):
    return f"{x*100:.{d}f}%"
def wan_yi(v):  # 万元 -> 亿元字符串（2位）
    return f"{v/10000:.2f}"
def num(v, d=2):
    return f"{v:,.{d}f}"

# 派生比率（由原值现算）
yoy = {2024: rev[2024]/rev[2023]-1, 2025: rev[2025]/rev[2024]-1}
cagr = (rev[2025]/rev[2023])**0.5-1
nd_margin = {y: nd[y]/rev[y] for y in YEARS}
ni_margin = {y: ni[y]/rev[y] for y in YEARS}
rd_rate = {y: rd[y]/rev[y] for y in YEARS}
cfo_rate = {y: cfo[y]/rev[y] for y in YEARS}
# 与披露值核对（断言）
assert abs(cagr-2.2678) < 0.001
assert abs(yoy[2025]-3.3264) < 0.001
for y in YEARS:
    assert abs(sum(prod[k][y] for k in prod)-main_rev[y]) < 0.01, (y,)
    assert abs(sum(region[k][y] for k in region)-main_rev[y]) < 0.01, (y,)

# ============ docx 基础工具 ============
doc = Document()

def set_fonts(style, cn=CN, en=EN, size=12, bold=False, color=BLACK):
    style.font.name = en; style.font.size = Pt(size); style.font.bold = bold; style.font.color.rgb = color
    rpr = style.element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.append(rf)
    rf.set(qn('w:eastAsia'), cn); rf.set(qn('w:ascii'), en); rf.set(qn('w:hAnsi'), en)

def run_font(run, cn=CN, en=EN, size=12, bold=False, color=BLACK, italic=False):
    run.font.name = en; run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.append(rf)
    rf.set(qn('w:eastAsia'), cn); rf.set(qn('w:ascii'), en); rf.set(qn('w:hAnsi'), en)

# 页面 A4 + 2.5cm
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Cm(2.5)

# 样式
set_fonts(doc.styles['Normal'], size=12)
normal = doc.styles['Normal']
normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
normal.paragraph_format.space_before = Pt(0); normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
# 首行缩进2字符（firstLineChars=200）
npPr = normal.element.get_or_add_pPr(); ind = npPr.find(qn('w:ind'))
if ind is None:
    ind = OxmlElement('w:ind'); npPr.append(ind)
ind.set(qn('w:firstLineChars'), '200'); ind.set(qn('w:firstLine'), '480')
for nm, sz in [('Title', 18), ('Heading 1', 16), ('Heading 2', 14), ('Heading 3', 12)]:
    set_fonts(doc.styles[nm], cn=CN_H, size=sz, bold=True, color=BLACK)
    doc.styles[nm].paragraph_format.first_line_indent = Pt(0)
for nm in ['Title', 'Heading 1', 'Heading 2', 'Heading 3']:
    pf = doc.styles[nm].paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE

def para(text="", size=12, bold=False, align=None, indent=True, cn=CN, color=BLACK, italic=False, after=0, before=0):
    p = doc.add_paragraph()
    if not indent:
        p.paragraph_format.first_line_indent = Pt(0)
        pPr = p._p.get_or_add_pPr(); ii = pPr.find(qn('w:ind'))
        if ii is None:
            ii = OxmlElement('w:ind'); pPr.append(ii)
        ii.set(qn('w:firstLineChars'), '0'); ii.set(qn('w:firstLine'), '0')
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
    if text:
        r = p.add_run(text); run_font(r, cn=cn, size=size, bold=bold, color=color, italic=italic)
    return p

def h1(t): 
    p = doc.add_heading(level=1); r = p.add_run(t); run_font(r, cn=CN_H, size=16, bold=True)
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(6); return p
def h2(t):
    p = doc.add_heading(level=2); r = p.add_run(t); run_font(r, cn=CN_H, size=14, bold=True)
    p.paragraph_format.space_before = Pt(11); p.paragraph_format.space_after = Pt(5); return p

def shade(cell, fill=HDR_FILL):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def set_cell(cell, text, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5, fill=None):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]; p.text = ""
    p.alignment = align; p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pPr = p._p.get_or_add_pPr(); ii = pPr.find(qn('w:ind'))
    if ii is None:
        ii = OxmlElement('w:ind'); pPr.append(ii)
    ii.set(qn('w:firstLineChars'), '0'); ii.set(qn('w:firstLine'), '0')
    r = p.add_run(str(text)); run_font(r, size=size, bold=bold)
    if fill: shade(cell, fill)

def caption(t):
    para(t, size=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=4, before=6)

def source_note(t):
    para(t, size=9, align=WD_ALIGN_PARAGRAPH.LEFT, indent=False, color=RGBColor(0x76,0x76,0x76), after=6)

def make_table(headers, rows, widths, num_cols=()):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    t.allow_autofit = False
    # 表头跨页重复、行内不分页
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
    # 表格宽度=版心16cm
    tblPr = t._tbl.tblPr; tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), str(int(16*567))); tblW.set(qn('w:type'), 'dxa'); tblPr.append(tblW)
    layout = OxmlElement('w:tblLayout'); layout.set(qn('w:type'), 'fixed'); tblPr.append(layout)
    for j, htxt in enumerate(headers):
        set_cell(t.rows[0].cells[j], htxt, bold=True, fill=HDR_FILL)
    for row in rows:
        cells = t.add_row().cells
        for j, val in enumerate(row):
            al = WD_ALIGN_PARAGRAPH.RIGHT if j in num_cols else (WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            set_cell(cells[j], val, align=al)
    for r_ in t.rows:
        cs = r_._tr.get_or_add_trPr(); cs2 = OxmlElement('w:cantSplit'); cs2.set(qn('w:val'),'true'); cs.append(cs2)
    for j, w in enumerate(widths):
        for r_ in t.rows:
            r_.cells[j].width = Cm(w)
    return t

def add_hyperlink(paragraph, url, text):
    part = paragraph.part; r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement('w:hyperlink'); h.set(qn('r:id'), r_id)
    new_run = OxmlElement('w:r'); rPr = OxmlElement('w:rPr')
    rf = OxmlElement('w:rFonts'); rf.set(qn('w:ascii'), EN); rf.set(qn('w:hAnsi'), EN); rf.set(qn('w:eastAsia'), CN); rPr.append(rf)
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '21'); rPr.append(sz)
    color = OxmlElement('w:color'); color.set(qn('w:val'), '1155CC'); rPr.append(color)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rPr.append(u)
    new_run.append(rPr); t = OxmlElement('w:t'); t.text = text; new_run.append(t); h.append(new_run)
    paragraph._p.append(h); return h

# 页脚居中页码
def add_page_number(section):
    fp = section.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run(); fld1 = OxmlElement('w:fldChar'); fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = ' PAGE '
    fld2 = OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'), 'end')
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2); run_font(run, size=10.5)
add_page_number(sec)

# ============ 封面标题区 ============
tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = tp.add_run("宇树科技（688836.SH）公司研究报告"); run_font(tr, cn=CN_H, size=18, bold=True)
tp.paragraph_format.space_after = Pt(4); tp.paragraph_format.space_before = Pt(24)
sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sp.add_run("经营与财务表现分析"); run_font(sr, cn=CN_H, size=14, bold=True)
sp.paragraph_format.space_after = Pt(10)
para("资料截止日：2026年8月30日（该日之后二级市场行情不纳入）｜生成日期：2026年9月4日",
     size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, color=RGBColor(0x76,0x76,0x76))
para("金额单位除注明外均为人民币万元；A＝已实现（经审计/经审阅/上市公告书披露），E＝预测；年度数据采用招股说明书注册稿口径。",
     size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, color=RGBColor(0x76,0x76,0x76), after=10)

# 目录
toc_h = doc.add_paragraph(); toc_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = toc_h.add_run("目  录"); run_font(r, cn=CN_H, size=14, bold=True)
toc_p = doc.add_paragraph(); run = toc_p.add_run()
b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin')
it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = 'TOC \\o "1-2" \\h \\z \\u'
sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate')
tt = OxmlElement('w:t'); tt.text = '（打开后右键“更新域”即可生成目录）'
e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end')
for o in (b, it, sep, tt, e): run._r.append(o)
run_font(run, size=10.5, color=RGBColor(0x76,0x76,0x76))
doc.add_page_break()

# ============ 执行摘要 ============
h1("执行摘要")
para("核心判断：宇树科技处于“收入高速扩张、产品结构快速切换、盈利质量以扣非口径更真实”的阶段。2023—2025年营业收入由1.59亿元增至16.99亿元，两年复合增速约226.8%，但同比增速已由2025年全年的332.6%回落至2026年上半年的48.5%，高增速阶段正在过去；2025年人形机器人收入占比过半、取代四足成为第一大产品，同时研发与销售费用扩张使2026年上半年扣非利润同比下降，规模增长与盈利承压并存。")
para("关键依据：①2025年营业收入169,926.93万元、扣非后归母净利润59,075.28万元、扣非净利率约34.8%、主营业务毛利率60.13%；②归母净利润27,821.05万元低于扣非数，差额-31,254.23万元为非经常性净损失（主要为股份支付），分析盈利应以扣非为主；③人形机器人收入占主营比重由1.88%升至51.78%，销量由5台增至5,215台、平均单价由59.34万元降至16.64万元；④2025年经营活动现金流净额66,998.18万元、合并资产负债率18.82%，报表稳健；⑤2026年上半年营收115,224.56万元（同比+48.5%）、扣非24,393.03万元（同比-19.3%）。")
para("主要约束：人形下游仍以科研教育为主（2025年1—9月占人形收入73.6%）、行业规模化商业落地尚早；产品降价与费用扩张可能继续压制利润率；2026年上半年数据取自上市公告书、未经审计；发行估值偏高（发行市盈率219.23倍为媒体口径、待核）。")
para("关注动作：跟踪扣非利润率与费用率拐点、人形在行业应用场景的订单占比、募投项目（模型/本体/制造基地）实际投入与达产进度，以及正式半年报对上市公告书数据的审计确认。")

# ============ 1 公司与主营、产品结构 ============
h1("1  公司概况、主营业务与产品结构")
h2("1.1  公司概况与发行上市")
para("宇树科技股份有限公司（简称宇树科技，科创板代码688836.SH）主营高性能通用人形机器人、四足机器人、机器人组件及具身智能模型的研发、生产与销售，于2026年8月19日在上海证券交易所科创板上市。本次公开发行4,044.6434万股、占发行后总股本10.00%，发行价150.80元/股，发行募资总额60.99亿元、净额59.17亿元，发行价对应市值609.93亿元；公司设置表决权差异安排，按“预计市值不低于100亿元”的科创板标准上市，实际控制人王兴兴发行后持股21.44%。")
para("需要说明：发行市盈率219.23倍来自媒体口径，尚需以发行公告原文核验；2025年6月Pre-IPO轮投前估值120亿元、投后127亿元，是IPO前最近一次市场化股权定价。")

h2("1.2  产品结构：人形跃升为第一大产品")
para("按主营业务口径，公司收入由人形机器人、四足机器人、机器人组件及其他构成。2023—2025年结构发生根本性切换：人形机器人收入由296.71万元增至86,783.19万元，占主营比重由1.88%升至51.78%；四足机器人由11,938.09万元增至69,762.56万元，占比由75.78%降至41.62%，由绝对主力转为基本盘；组件及其他占比降至约6.6%（2025年组件与其他未单列，按主营轧差，其中组件约1.04亿元、精确拆分待核）。")
caption("表1  主营业务收入分产品结构（万元，主营口径）")
rows = []
for k in ["人形", "四足", "组件及其他"]:
    rows.append([k+"机器人" if k!="组件及其他" else "组件及其他",
                 num(prod[k][2023]), pct(prod[k][2023]/main_rev[2023],2),
                 num(prod[k][2024]), pct(prod[k][2024]/main_rev[2024],2),
                 num(prod[k][2025]), pct(prod[k][2025]/main_rev[2025],2)])
rows.append(["主营业务合计", num(main_rev[2023]), "100.00%", num(main_rev[2024]), "100.00%", num(main_rev[2025]), "100.00%"])
make_table(["产品", "2023A", "占比", "2024A", "占比", "2025A", "占比"], rows,
           [3.1,2.35,1.95,2.35,1.95,2.35,1.95], num_cols=(1,2,3,4,5,6))
source_note("数据来源：招股说明书（注册稿）及券商研报转引（底稿S1/S7/S8）；占比由本表收入除以主营合计现算；2025年组件及其他为轧差数。")

h2("1.3  销量与单价：量增价减")
para("人形机器人销量由2023年的5台增至2024年412台、2025年5,215台，同期披露平均单价由59.34万元/台降至26.04万元、再降至16.64万元/台，价格带随G1等产品下探至10万元级；四足机器人销量由3,121台增至23,037台，单价由3.83万元降至3.03万元。出货放量伴随单位价格下行，是“以价换量、扩大装机基数”的典型路径。公司称2025年纯人形机器人出货超5,500台、出货量全球第一（与确认收入口径5,215台存在统计差异）；报告期四足累计销量超3.3万台。")
caption("表2  主要产品销量与平均单价（销量：台；单价：万元/台）")
rows = []
for k in ["人形", "四足"]:
    rows.append([k+"销量"]+[f"{vol[k][y]:,}" for y in YEARS])
    rows.append([k+"平均单价(披露)"]+[f"{price_disc[k][y]:.2f}" for y in YEARS])
make_table(["指标", "2023A", "2024A", "2025A"], rows, [4.6,3.8,3.8,3.8], num_cols=(1,2,3))
source_note("数据来源：底稿S1/S7/S8。注：人形2024年按注册稿销量412台机械相除得约25.95万元，与披露单价26.04万元的差异源于申报稿与注册稿版本修订，本报告采用披露值。")

h2("1.4  地区结构：境内放量、境外占比回落")
para("2023—2024年境外收入约占主营55.6%—55.7%，2025年境内收入94,445.56万元（占56.35%）反超境外73,165.53万元（占43.65%），主要来自国内人形机器人需求放量。海外仍是重要市场，外销结算与汇率波动需持续关注。")
caption("表3  主营业务收入分地区（万元）")
rows = []
for k in ["境内", "境外"]:
    rows.append([k, num(region[k][2023]), pct(region[k][2023]/main_rev[2023],2),
                 num(region[k][2024]), pct(region[k][2024]/main_rev[2024],2),
                 num(region[k][2025]), pct(region[k][2025]/main_rev[2025],2)])
make_table(["地区", "2023A", "占比", "2024A", "占比", "2025A", "占比"], rows,
           [2.8,2.4,2.0,2.4,2.0,2.4,2.0], num_cols=(1,2,3,4,5,6))
source_note("数据来源：招股意向书、招股说明书（底稿S4/S1）；2024年境内为主营减境外轧差数。")

h2("1.5  下游应用场景")
para("按2025年1—9月（申报稿口径，非全年）结构，人形机器人收入中科研教育占73.60%、商业消费占17.39%、行业应用仅占9.01%，需求仍高度依赖科研教育；四足机器人场景相对均衡，科研教育、商业消费、行业应用分别占31.58%、42.30%、26.12%。人形机器人向工业等行业场景的规模化渗透尚处早期。")

# ============ 2 收入与盈利变化 ============
h1("2  收入与盈利变化")
h2("2.1  高增长与增速换挡")
para("2023—2025年营业收入分别为15,913.44万元、39,277.07万元、169,926.93万元，2024、2025年同比分别增长146.82%、332.64%，两年复合增长率约226.78%。进入2026年后增速明显回落：2026年一季度营收同比+68.49%，上半年同比+48.54%。增速下行主要源于基数抬高，公司亦提及行业热度缓和与竞争加剧，高斜率增长阶段正在向中高速过渡。")
caption("表4  核心经营与财务指标（万元，比率除外）")
rows = [
 ["营业收入", num(rev[2023]), num(rev[2024]), num(rev[2025]), "115,224.56"],
 ["营业收入同比", "—", pct(yoy[2024],2), pct(yoy[2025],2), "48.54%"],
 ["归母净利润", num(ni[2023]), num(ni[2024]), num(ni[2025]), "27,399.99"],
 ["扣非后归母净利润", num(nd[2023]), num(nd[2024]), num(nd[2025]), "24,393.03"],
 ["主营业务毛利率", pct(gm[2023],2), pct(gm[2024],2), pct(gm[2025],2), "56.01%"],
 ["销售净利率(归母)", pct(ni_margin[2023],2), pct(ni_margin[2024],2), pct(ni_margin[2025],2), "—"],
 ["扣非净利率", pct(nd_margin[2023],2), pct(nd_margin[2024],2), pct(nd_margin[2025],2), "—"],
 ["扣非加权ROE", pct(roe[2023],2), pct(roe[2024],2), pct(roe[2025],2), "9.99%"],
 ["经营现金流净额", num(cfo[2023]), num(cfo[2024]), num(cfo[2025]), "23,154.53"],
 ["资产总额(期末)", num(asset[2023]), num(asset[2024]), num(asset[2025]), "384,546.94"],
 ["合并资产负债率", pct(debt_ratio[2023],2), pct(debt_ratio[2024],2), pct(debt_ratio[2025],2), "25.11%"],
]
make_table(["指标", "2023A", "2024A", "2025A", "2026H1A"], rows,
           [4.0,3.0,3.0,3.0,3.0], num_cols=(1,2,3,4))
source_note("数据来源：上市保荐书（注册稿）、落实函回复、上市公告书（底稿S2/S3/S5）；比率由原值现算并与披露值核对。2026H1为上市公告书披露、未经审计；2025年基本每股收益0.76元。")

h2("2.2  盈利质量：扣非强、归母受股份支付扰动")
para("盈利能力快速改善：主营业务毛利率由44.22%升至56.74%、再到60.13%，主要依托全栈自研与核心零部件自产；2024年实现扭亏，2025年扣非后归母净利润59,075.28万元、扣非净利率约34.77%，扣非加权平均净资产收益率28.70%。但2025年归母净利润仅27,821.05万元，低于扣非数31,254.23万元，差额为非经常性净损失，主要系股权激励形成的股份支付费用。因此，评估公司经常性盈利能力应以扣非口径为主，归母口径会被一次性/非经常项目扰动。")

h2("2.3  2026年上半年：收入增长、扣非承压，预测与实际分列")
para("2026年上半年公司实现营业收入115,224.56万元、归母净利润27,399.99万元（上年同期为-3,202.45万元、同比扭亏，低基数中包含上年同期约3.49亿元股份支付费用）；扣非后归母净利润24,393.03万元、同比下降19.34%（2026年一季度扣非同比-52.55%）。扣非下滑主要源于研发费用（上半年同比增加约8,203.74万元）与销售费用（上半年16,407.27万元，含品牌推广与销售扩编）快速扩张。")
para("公司曾于2026年5月（上会稿）披露2026年上半年业绩预告（预测，E）：营业收入105,200万—112,800万元、归母净利润25,800万—30,600万元、扣非23,600万—28,300万元。对照上市公告书实际数（A）：实际营收略高于预测上限，归母、扣非均落在预测区间内。预测仅作参照，不应当作既成事实。")
caption("表5  2026年上半年业绩预告（E，预测）与实际（A）对照（万元）")
make_table(["指标", "预测下限(E)", "预测上限(E)", "实际(A)", "对照结论"],
           [["营业收入", "105,200.00", "112,800.00", "115,224.56", "略超上限"],
            ["归母净利润", "25,800.00", "30,600.00", "27,399.99", "落在区间内"],
            ["扣非归母净利润", "23,600.00", "28,300.00", "24,393.03", "落在区间内"]],
           [3.6,3.0,3.0,3.0,3.4], num_cols=(1,2,3))
source_note("数据来源：业绩预告取自2026-05上会稿（预测）；实际取自2026-08-17上市公告书（未经审计）。")

h2("2.4  现金流与资产负债表")
para("经营活动现金流净额由494.25万元增至19,239.13万元、再到66,998.18万元，2025年经营现金流/营业收入约39.4%，现金对利润覆盖较充分；2023—2025年合并资产负债率为23.57%、16.19%、18.82%，整体低杠杆。截至2026年6月末，公司总资产384,546.94万元、较年初增长19.85%，资产负债率回升至25.11%（合同负债、应付款项及租赁负债增加），上半年经营现金流净额23,154.53万元、同比下降32.53%，需持续跟踪回款与负债结构变化。")

# ============ 3 研发投入 ============
h1("3  研发投入")
para("研发费用绝对额持续上升、费用率因收入快速放大而下降：2023—2025年研发费用分别为4,995.18万元、7,001.70万元、14,496.56万元，三年累计26,493.44万元；研发费用率由31.39%降至17.83%、再到8.53%，属于规模摊薄而非投入收缩。截至2025年末公司员工516人，其中研发人员184人、占35.66%。")
caption("表6  研发投入与人员（万元、人、%）")
make_table(["指标", "2023A", "2024A", "2025A"],
           [["研发费用", num(rd[2023]), num(rd[2024]), num(rd[2025])],
            ["研发费用率", pct(rd_rate[2023],2), pct(rd_rate[2024],2), pct(rd_rate[2025],2)],
            ["员工总数(期末)", "—", "—", "516"],
            ["研发人员(期末)", "—", "—", "184"],
            ["研发人员占比", "—", "—", "35.66%"]],
           [4.6,3.8,3.8,3.8], num_cols=(1,2,3))
source_note("数据来源：上市保荐书（底稿S2）；研发费用率由研发费用/营业收入现算；人员仅取得2025年末数。")
para("从募投方向看，原拟募资约42.02亿元中，智能机器人模型研发（20.22亿元）、机器人本体研发（11.10亿元）、新型智能机器人产品开发（4.45亿元）三项合计约35.77亿元、占比约85%，战略资源明显向具身智能“大脑/小脑”模型与本体技术倾斜（分项金额为约数、精确值以招股书为准）。")

# ============ 4 竞争优势 ============
h1("4  竞争优势")
para("（1）全栈自研支撑高毛利。主营业务毛利率三年提升至60.13%，与公司在电机、控制器、感知算法、整机及具身智能模型上的垂直自研、核心零部件自产直接相关，高毛利为研发再投入和价格下探留出空间。")
para("（2）出货规模与产品矩阵领先。人形机器人2025年确认收入口径销量5,215台、公司称纯人形出货超5,500台居全球第一；四足报告期累计销量超3.3万台、全球份额领先，规模效应有助于摊薄单位成本并巩固供应链议价能力。")
para("（3）产销衔接顺畅。2025年前三季度人形机器人产销率超过95%，基本满产满销，显示需求侧对现有产能形成较强支撑。")
para("（4）产品价格带持续下探、拓宽可及市场。人形平均单价由59.34万元降至16.64万元、四足降至3.03万元，通过G1等产品把价格带下探至10万元级，有利于扩大装机与开发者生态。")
para("（5）报表稳健、具备融资能力。2025年末资产负债率仅18.82%、经营现金流66,998.18万元；2026年8月IPO募资净额59.17亿元（相对原拟投项目形成超募），为模型、本体研发与制造基地建设提供资金。上述优势均以披露数据为依据，技术领先性的同业量化对比本报告未取得充分一手数据，不作扩展结论。")

# ============ 5 增长变量 ============
h1("5  增长变量")
para("（1）人形机器人放量与结构升级。人形已成为第一大收入来源（2025年占主营51.78%），其销量增长、产品迭代与单价策略是收入弹性的首要变量；能否把需求从科研教育拓展到行业应用，决定增长的持续性。")
para("（2）下游场景拓宽。当前人形收入约73.6%来自科研教育（2025年1—9月口径），商业消费、行业应用占比提升将打开新增量；四足在商业消费与行业应用的占比已相对均衡，可作为场景拓展的参照。")
para("（3）境内需求与品牌外溢。2025年境内收入占比升至56.35%并反超境外，国内人形需求与重大活动品牌曝光带来拉动；境外收入绝对额仍增至73,165.53万元，海外渠道扩张构成第二增长曲线。")
para("（4）募投与产能建设（计划，非已实现）。原拟投建智能机器人制造基地，达产规划年产能为人形7.5万台、四足11.5万台——该数字为招股书披露的达产规划，并非当前已实现产能或产量；募投项目的实际投入、建设进度与达产节奏是后续供给端的关键变量，需以定期报告和公告持续验证。")
para("（5）资金与研发转化。IPO超募资金与约85%投向研发的募投结构，若能有效转化为模型与产品竞争力，将支撑中长期增长；反之则可能形成费用与折旧压力。")

# ============ 6 主要风险 ============
h1("6  主要风险")
para("（1）商业化场景集中风险。人形机器人收入约73.6%来自科研教育、行业应用仅约9.01%（2025年1—9月口径），规模化工业与消费级落地尚早，若科研采购节奏放缓，需求波动会被放大。")
para("（2）价格下行与竞争加剧风险。两类产品平均单价均逐年下行，行业价格战可能进一步压缩单价与毛利率；公司亦将竞争加剧列为增速回落的原因之一。")
para("（3）利润口径扰动风险。股份支付等非经常性项目使归母净利润显著低于扣非（2025年差额-31,254.23万元），后续股权激励仍可能持续扰动表观利润。")
para("（4）费用扩张与扣非承压风险。2026年上半年研发、销售费用快速增加，扣非归母同比下降19.34%、经营现金流同比下降32.53%，若收入增速继续换挡而费用刚性，利润率仍有下行压力。")
para("（5）高估值波动风险。发行价对应市值609.93亿元、媒体口径发行市盈率219.23倍（待核），估值对业绩兑现高度敏感，二级市场波动风险较大。")
para("（6）供应链与外包风险。装配环节存在劳务外包，2023—2025年劳务外包费用由1,161.69万元增至6,802.65万元，产能扩张下对外包与供应链稳定性的依赖上升。")
para("（7）外销与汇率风险。2025年境外收入73,165.53万元、占主营43.65%，海外结算、关税与汇率波动可能影响盈利；此外，2026年上半年数据未经审计、部分2025年分季度及分产品明细为反推或轧差约数，正式定期报告披露后可能修订。")

# ============ 7 结论 ============
h1("7  结论")
para("宇树科技在报告期内完成了从四足为主到人形主导的产品切换，并以全栈自研维持了60%左右的主营毛利率和强劲现金流，属于高成长、高研发强度、低杠杆的硬科技企业。但增长斜率正在放缓，2026年进入“收入仍快、扣非承压”的阶段：竞争加剧、价格下行与费用扩张同时出现，人形需求仍集中于科研教育。后续判断的关键，在于人形能否向行业应用规模化渗透、募投研发与制造基地能否按计划转化为产品与产能，以及扣非利润率能否在费用扩张后重新企稳。本报告所有数据均来自上交所披露文件与公司公开资料（详见资料来源），预测与规划已与已实现数据明确区分，不构成投资建议。")

# ============ 口径说明 ============
h1("8  口径与数据说明")
for t in [
 "1. 金额除注明外均为人民币万元，比率以小数存储、百分比显示；亿元为万元除以10,000换算。",
 "2. 后缀A表示已实现（2023—2025年经审计、2026年一季度经审阅、2026年上半年为上市公告书披露且未经审计）；后缀E表示预测（2026年5月业绩预告），预测不作为已发生事实。",
 "3. 年度数据统一采用招股说明书注册稿/上市保荐书最终口径；申报稿2025年营业收入170,820.87万元等已被修订的数据未采用。",
 "4. 分产品、分地区占比以主营业务收入为分母；2025年“组件及其他”、2024年境内收入为轧差数；2025年销售费用14,120.93万元为按披露费率反推的约数，发行市盈率219.23倍为媒体口径，均待以原文核验。",
 "5. 制造基地7.5万台/11.5万台为达产规划，非已实现产能或产量；资料截止日2026年8月30日之后的二级市场行情不纳入。",
]:
    para(t, size=10.5, indent=False)

# ============ 资料来源 ============
h1("9  资料来源")
sources = [
 ("S1  招股说明书（注册稿），上交所科创板项目 auditId=2178（申报稿2026-03-20/上会稿2026-05-25/注册稿2026-06-02）", "https://star.sse.com.cn/listing/renewal/ipo/index_listing_detail.shtml?auditId=2178"),
 ("S2  《上市保荐书》（注册稿）002178_20260602_VI1W.pdf，中信证券/上交所", "http://static.sse.com.cn/stock/disclosure/announcement/c/202606/002178_20260602_VI1W.pdf"),
 ("S3  《审核中心意见落实函的回复》002178_20260525_V4H0.pdf，发行人/上交所", "http://static.sse.com.cn/stock/disclosure/announcement/c/202605/002178_20260525_V4H0.pdf"),
 ("S4  《招股意向书》全文（新浪财经公告库转引），2026-07-31", "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?CompanyCode=82494861&gather=1&id=12470775"),
 ("S5  《首次公开发行股票科创板上市公告书》，2026-08-17（上海证券报提示性公告）", "http://paper.cnstock.com/html/2026-08/18/content_2255912.htm"),
 ("S6  《发行公告》《投资风险特别公告》（巨潮资讯），2026-08-07", "https://static.cninfo.com.cn/finalpage/2026-08-07/1225462415.PDF"),
 ("S7  浦银国际《宇树招股书解读：六大维度看全球机器人龙头商业落地》（二手·研报转引）", "https://www.spdbi.com"),
 ("S8  兴业证券《全球通用机器人领军企业》研报（二手·研报转引，慧博投研）", "https://www.hibor.com.cn"),
 ("S9  国信证券《人形机器人本体系列之宇树科技招股书梳理》（二手·研报转引，慧博投研）", "https://www.hibor.com.cn"),
 ("S10 东方财富/证券时报·数据中心 688836 财务指标（二手·数据聚合，交叉核对）", "https://data.eastmoney.com/stockdata/688836.html"),
 ("S11 宇树科技官方网站与官方公开资料", "https://www.unitree.com"),
]
for label, url in sources:
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Pt(0)
    pPr = p._p.get_or_add_pPr(); ii = OxmlElement('w:ind'); ii.set(qn('w:firstLineChars'),'0'); ii.set(qn('w:firstLine'),'0'); pPr.append(ii)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(label + "  "); run_font(r, size=10.5)
    add_hyperlink(p, url, url)
para("说明：S7—S10为二手转引/数据聚合，仅用于交叉核对与补充明细；如与S1—S5一手披露不一致，以一手披露为准。配套数据底稿见《宇树科技经营财务分析底稿_截至20260830.xlsx》。",
     size=10.5, indent=False, before=4)

doc.save(OUT)
print("SAVED", OUT)
