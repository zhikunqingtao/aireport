# -*- coding: utf-8 -*-
"""宇树科技经营与财务分析底稿 生成脚本（openpyxl 直写）"""
try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import CellIsRule

def xl_color(css_hex: str) -> str:
    value = css_hex.removeprefix("#").upper()
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, got: {css_hex}")
    return "FF" + value

XL_PRIMARY = xl_color("#4472C4")
XL_HEADER_TXT = xl_color("#FFFFFF")
XL_LIGHT = xl_color("#D9E2F3")
XL_SUM = xl_color("#2F5597")
XL_BORDER = xl_color("#BFBFBF")
XL_WARN = xl_color("#FFC7CE")
XL_WARN_TXT = xl_color("#9C0006")

thin_side = Side(style="thin", color=XL_BORDER)
BORDER_ALL = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

F_TITLE = Font(name="微软雅黑", size=14, bold=True, color=XL_SUM)
F_SECTION = Font(name="微软雅黑", size=11, bold=True, color=XL_SUM)
F_HEADER = Font(name="微软雅黑", size=10, bold=True, color=XL_HEADER_TXT)
F_BODY = Font(name="微软雅黑", size=10)
F_BOLD = Font(name="微软雅黑", size=10, bold=True)
F_NOTE = Font(name="微软雅黑", size=9, color="595959")

FILL_HEADER = PatternFill("solid", fgColor=XL_PRIMARY)
FILL_LIGHT = PatternFill("solid", fgColor=XL_LIGHT)
FILL_SECTION = PatternFill("solid", fgColor=XL_LIGHT)
FILL_SUM = PatternFill("solid", fgColor=XL_SUM)
FILL_WHITE = PatternFill("solid", fgColor="FFFFFFFF")

AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
AL_R = Alignment(horizontal="right", vertical="center")

FMT_AMT = '#,##0.00;[Red]-#,##0.00'
FMT_PCT = '0.00%;[Red]-0.00%'
FMT_NUM = '#,##0'
FMT_PCT1 = '0.0'

OUT = "/Users/guoqingtao/Desktop/AI办公评测/workbuddy/宇树科技经营与财务分析底稿.xlsx"

wb = Workbook()
wb.properties.title = "宇树科技经营与财务分析底稿"


def style_range(ws, rng, font=None, fill=None, align=None, border=True, fmt=None):
    for row in ws[rng]:
        for c in row:
            if font: c.font = font
            if fill: c.fill = fill
            if align: c.alignment = align
            if border: c.border = BORDER_ALL
            if fmt: c.number_format = fmt


def put_title(ws, cell_range, text):
    ws[cell_range.split(":")[0]] = text
    ws.merge_cells(cell_range)
    first = cell_range.split(":")[0]
    ws[first].font = F_TITLE
    ws[first].alignment = AL_C


def put_section(ws, cell_range, text):
    ws[cell_range.split(":")[0]] = text
    ws.merge_cells(cell_range)
    first = cell_range.split(":")[0]
    ws[first].font = F_SECTION
    ws[first].fill = FILL_SECTION
    ws[first].alignment = AL_L


# ============================================================
# Sheet 1: 说明与口径
# ============================================================
ws1 = wb.active
ws1.title = "说明与口径"
put_title(ws1, "A1:B1", "宇树科技经营与财务分析底稿——编制说明与口径")
rows1 = [
    ("分析对象", "宇树科技股份有限公司（证券代码：688836.SH，证券简称：宇树科技-W），高性能通用人形机器人、四足机器人、机器人组件及具身智能模型的研发、生产和销售。"),
    ("资料截止时间", "2026年8月30日（上市后二级市场数据仅采用截至该日的公开信息）。"),
    ("编制时间", "2026年9月4日。"),
    ("金额单位", "人民币万元（另标注除外；图表中为亿元）。百分比均以百分数列示。"),
    ("报告期口径", "年度：2022/2023/2024/2025年度；期间：2025H1（上半年）、2025Q1-3（前三季度）、2026Q1（一季度）、2026H1（上半年）。同比比较一律采用相同报告期口径（如2026H1对2025H1）。"),
    ("资料优先级", "A级：上交所披露文件（招股说明书申报稿、科创板上市公告书、定期报告）；B级：公司官方公开资料（官网等）；C级：权威财经媒体报道（证券时报、21世纪经济报道、中新经纬、中国经济网等，用于交叉验证）；D级：据披露增速反推的推算值（均已在表中标注）。"),
    ("数据性质标注", "原始数据表中每行均标注数据性质；推算值、约数均写入备注，未将任何预测数据当作已发生事实（机构预测单独存放于“预测参考(非事实)”表）。"),
    ("重要口径差异提示1", "2025年度营业收入：招股说明书申报稿（2026-03-20受理稿）披露为17.08亿元；科创板上市公告书/年报口径为16.99亿元（169,926.93万元）。本底稿以16.99亿元（上市公告书/年报口径）为准，差异原因待核对原文。"),
    ("重要口径差异提示2", "毛利率存在“主营业务毛利率”（招股书口径）与“销售毛利率”（整体报表口径）两套数据，且招股书不同版本（申报稿/上会稿）数字略有差异，本底稿分两行分别列示并在备注中说明。"),
    ("重要口径差异提示3", "2025年归母净利润约2.78亿元、净利润（含少数股东）约2.88亿元，媒体转引存在2.78/2.88亿元两种表述，疑为归母与含少数股东口径之别，精确值需以2025年年度报告为准。"),
    ("编辑说明", "本工作簿为可编辑底稿：黄色浅底区域为计算区（含公式，请勿直接覆盖）；修改原始数据后，核心计算与图表数据将联动更新。"),
    ("免责声明", "本底稿基于公开信息整理，仅供研究参考，不构成投资建议。所引媒体与券商数据未经审计，使用前请按“待人工核验清单”逐项核对交易所披露原文。"),
]
r = 3
ws1["A2"] = "项目"; ws1["B2"] = "内容"
style_range(ws1, "A2:B2", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
for k, v in rows1:
    ws1[f"A{r}"] = k; ws1[f"B{r}"] = v
    r += 1
r += 1
put_section(ws1, f"A{r}:B{r}", "待人工核验清单（使用前请逐项核对披露原文）")
r += 1
checks = [
    "1. 2025年度归母净利润精确值（媒体口径2.78亿/2.88亿元并存，需以2025年年报利润表为准）。",
    "2. 2025年度营收申报稿17.08亿元与年报16.99亿元差异原因（是否审计调整），需核对年报原文。",
    "3. 2024年研发费用精确值：本文按“研发费用率17.8%×营收”推算约6,983万元，需以年报为准。",
    "4. 2022年扣非归母净利润-807万元为媒体转引招股书数据，精确到元的数值待核。",
    "5. 各期毛利率“主营/整体”口径及申报稿与上会稿版本差异，需对照招股书原文核对。",
    "6. 经营活动现金流净额为约数（2025年“超6.7亿元”、2024年约1.9亿元为按“增加4.8亿元”反推），需以现金流量表为准。",
    "7. 2025H1营收77,560万元、扣非30,250万元系按2026H1披露同比增速反推，需与2025年半年度报告核对。",
    "8. 历史收入结构占比（人形1.88%/27.6%等）的分母为主营业务收入口径，需核对招股书分部数据表。",
    "9. 资产总额/流动资产2025年末数为按2026H1披露增幅反推，需与2025年报资产负债表核对。",
    "10. 券商盈利预测（野村、招商证券）来自媒体转引，未经研报原文核验，仅供方向性参考。",
]
for c in checks:
    ws1[f"A{r}"] = c
    ws1.merge_cells(f"A{r}:B{r}")
    ws1[f"A{r}"].font = F_BODY
    ws1[f"A{r}"].alignment = AL_L
    r += 1
ws1.column_dimensions["A"].width = 22
ws1.column_dimensions["B"].width = 95
style_range(ws1, f"A3:B{3+len(rows1)-1}", font=F_BODY, align=AL_L)
for row in ws1[f"A3:B{3+len(rows1)-1}"]:
    row[0].font = F_BOLD

# ============================================================
# Sheet 2: 资料来源
# ============================================================
ws2 = wb.create_sheet("资料来源")
put_title(ws2, "A1:I1", "资料来源清单（按优先级排序，资料截止2026-08-30）")
headers2 = ["序号", "资料名称", "资料类型", "披露/发布方", "披露/发布日期", "涉及报告期", "主要引用数据", "链接", "备注"]
for i, h in enumerate(headers2, start=1):
    ws2.cell(row=2, column=i, value=h)
style_range(ws2, "A2:I2", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
src_rows = [
    (1, "宇树科技首次公开发行股票并在科创板上市招股说明书（申报稿）", "交易所披露文件（A级）", "上海证券交易所/宇树科技", "2026-03-20（受理日披露）", "2022-2025年度、2025Q1-3", "营收、归母净利、扣非净利、主营业务毛利率、收入结构、销量、募投计划、2026H1业绩预告", "www.sse.com.cn（发行上市审核项目页面）", "IPO受理稿，申报口径财务数据"),
    (2, "首次公开发行股票科创板上市公告书（含2026年上半年业绩更新）", "交易所披露文件（A级）", "上海证券交易所/宇树科技", "2026-08-17", "2026H1、2025H1（对比数）、2025年度", "2026H1营收11.52亿元/归母2.74亿元/扣非2.44亿元、总资产38.45亿元、增速与费用变动说明", "www.sse.com.cn", "2026-08-19上市前披露，上市后首份经审阅半年数据"),
    (3, "宇树科技2025年年度报告（688836）", "定期报告（A级）", "宇树科技", "2026年上半年披露", "2025年度", "2025年度收入构成（产品/地域）、研发费用14,496.56万元、销售毛利率60.44%、净利润数据", "www.sse.com.cn", "A股财务数据库转引年报数据，建议核对年报原文"),
    (4, "宇树科技2026年第一季度报告（688836）", "定期报告（A级）", "宇树科技", "2026年4月", "2026Q1、2025Q1", "2026Q1营收42,284.05万元（+68.49%）、扣非4,025.36万元（-52.55%）、毛利率58.42%、研发费用6,319.31万元", "www.sse.com.cn", "媒体及行情数据库转引，建议核对原文"),
    (5, "宇树科技官方网站及官方公开信息", "官方公开资料（B级）", "宇树科技", "持续更新", "——", "公司业务描述、产品矩阵（H1/G1/G2/H2/B2/Go2等）、组织与招聘信息", "www.unitree.com", "非财务数据来源"),
    (6, "证券时报、21世纪经济报道、中新经纬、中国经济网、广州日报等报道", "权威财经媒体（C级）", "各媒体", "2026-03至2026-09", "全期间", "IPO进展、上市首日行情、2026H1业绩解读、股东结构（王兴兴持股23.8216%）等交叉验证信息", "egs.stcn.com/news/detail/2255406.html 等多篇文章", "用于交叉验证与背景信息，关键数据已与A级来源比对"),
    (7, "华源证券等券商研究报告（媒体/知识库转引）", "券商研究（C级）", "华源证券等", "2026年", "2023-2025、2026Q1", "费用率拆分（销售/管理/研发/财务）、扣非净利率、分产品毛利率、2026Q2盈利预测", "第三方知识库转引", "未经原文核验，仅作交叉参考；预测内容已归入“预测参考(非事实)”表"),
]
r = 3
for row in src_rows:
    for i, v in enumerate(row, start=1):
        ws2.cell(row=r, column=i, value=v)
    r += 1
style_range(ws2, f"A3:I{r-1}", font=F_BODY, align=AL_L)
for row in ws2[f"A3:A{r-1}"]:
    row[0].alignment = AL_C
widths2 = [6, 38, 16, 16, 14, 16, 42, 30, 28]
for i, w in enumerate(widths2, start=1):
    ws2.column_dimensions[get_column_letter(i)].width = w
ws2.freeze_panes = "A3"

# ============================================================
# Sheet 3: 原始数据-财务
# ============================================================
ws3 = wb.create_sheet("原始数据-财务")
FIN = "原始数据-财务"
put_title(ws3, "A1:L1", "原始财务数据（单位：人民币万元；百分比为小数格式）")
headers3 = ["指标", "单位", "2022年度", "2023年度", "2024年度", "2025年度", "2025H1", "2025Q1-3", "2026Q1", "2026H1", "数据性质", "备注（口径与来源）"]
for i, h in enumerate(headers3, start=1):
    ws3.cell(row=2, column=i, value=h)
style_range(ws3, "A2:L2", font=F_HEADER, fill=FILL_HEADER, align=AL_C)

fin_rows = [
    # (指标, 单位, vals dict col->value, 数据性质, 备注)
    ("营业收入", "万元", {"C": 12291.95, "D": 15913.44, "E": 39237.06, "F": 169926.93, "G": 77560, "H": 116700, "I": 42284.05, "J": 115224.56},
     "披露为主", "2022-2024及2026H1为交易所/数据库精确值；2025年度为上市公告书口径169,926.93万元（申报稿口径17.08亿元，见说明表）；2025Q1-3为招股书约数11.67亿元；2025H1为按2026H1同比+48.54%反推的推算值；2026Q1为一季报精确值42,284.05万元。"),
    ("归母净利润", "万元", {"C": -2210.05, "D": -1114.51, "E": 9450.18, "F": 27800, "G": -3202.45, "H": 10500, "J": 27400.00},
     "披露为主", "2022-2024及2025H1、2026H1（273,999,911.92元）为披露值；2025年度约2.78亿元为媒体转引（另有含少数股东口径约2.88亿元），精确值待核年报；2025Q1-3约1.05亿元。"),
    ("净利润（含少数股东）", "万元", {"E": 9547.47, "F": 28800},
     "媒体报道", "2024年9,547.47万元、2025年约2.88亿元（媒体转引招股书/上会稿），与归母口径差异为少数股东损益。"),
    ("扣非归母净利润", "万元", {"C": -807, "D": -1801.91, "E": 7750, "F": 59075.28, "G": 30250, "H": 43100, "I": 4025.36, "J": 24400},
     "披露为主", "2025年度59,075.28万元为上市公告书口径；2024年7,750万元为申报稿披露（按2025年+652.78%推算约7,845万元，存在小幅版本差异）；2025H1为按2026H1同比-19.34%反推的推算值；2026Q1为4,025.36万元。"),
    ("主营业务毛利率", "%", {"C": 0.4418, "D": 0.4422, "E": 0.5641, "F": 0.6027, "H": 0.5945},
     "披露（招股书）", "招股书申报稿口径：2022/2023/2024/2025Q1-3分别为44.18%/44.22%/56.41%/59.45%；2025年度60.27%（申报稿），上会稿口径为60.13%，存在版本差异。"),
    ("销售毛利率（整体）", "%", {"D": 0.4475, "E": 0.5698, "F": 0.6044, "I": 0.5842, "J": 0.5601},
     "披露（报表口径）", "整体报表口径（含其他业务）：2023年44.75%、2024年56.98%、2025年60.44%、2026Q1为58.42%、2026H1为56.01%。"),
    ("研发费用", "万元", {"D": 4995.18, "E": 6983, "F": 14496.56, "G": 5387, "H": 9021, "I": 6319.31, "J": 13590.65},
     "披露/推算混合", "2023年4,995.18万元、2025年14,496.56万元、2026Q1为6,319.31万元、2026H1为13,590.65万元（披露值）；2024年约6,983万元为按研发费用率17.8%推算；2025H1为5,387万元（据2026H1同比+152%披露值）。"),
    ("销售费用", "万元", {"F": 14100, "J": 16400},
     "披露（约数）", "2025年约1.41亿元（费用率8.31%）；2026H1约1.64亿元，已超过2025年全年水平。"),
    ("经营活动现金流净额", "万元", {"E": 19000, "F": 67000},
     "约数/推算", "2025年净流入超6.7亿元（约数）；2024年约1.9亿元为按“2025年较2024年增加4.8亿元”反推，需以现金流量表为准。"),
    ("资产总额", "万元", {"F": 320800, "J": 384500},
     "披露/推算混合", "2026-06-30为38.45亿元（披露，较上年末+19.85%）；2025年末32.08亿元为反推值。"),
    ("流动资产", "万元", {"F": 221900, "J": 288800},
     "披露/推算混合", "2026-06-30为28.88亿元（披露，较上年末+30.13%）；2025年末22.19亿元为反推值。"),
    ("股份支付费用（非经常性）", "万元", {"F": 34906.55, "G": 34900},
     "披露", "2025年确认34,906.55万元（股权激励平台上海宇翼增资），主要在2025H1确认，导致2025H1归母净利润为负而扣非为正。"),
]
r = 3
for name, unit, vals, nature, note in fin_rows:
    ws3[f"A{r}"] = name; ws3[f"B{r}"] = unit
    for col, v in vals.items():
        ws3[f"{col}{r}"] = v
        if unit == "%":
            ws3[f"{col}{r}"].number_format = FMT_PCT
        else:
            ws3[f"{col}{r}"].number_format = FMT_AMT
    ws3[f"K{r}"] = nature; ws3[f"L{r}"] = note
    r += 1
last3 = r - 1
style_range(ws3, f"A3:L{last3}", font=F_BODY, align=AL_L)
for row in ws3[f"A3:L{last3}"]:
    for c in row[1:10]:
        c.alignment = AL_R
    row[0].font = F_BOLD
    row[10].alignment = AL_C
# 负值红字（净利/扣非行）
ws3.conditional_formatting.add(f"C4:J6",
    CellIsRule(operator="lessThan", formula=["0"], font=Font(color=XL_WARN_TXT, name="微软雅黑", size=10)))
widths3 = [22, 8, 13, 13, 13, 14, 12, 12, 12, 13, 14, 60]
for i, w in enumerate(widths3, start=1):
    ws3.column_dimensions[get_column_letter(i)].width = w
ws3.freeze_panes = "C3"

# ============================================================
# Sheet 4: 原始数据-业务
# ============================================================
ws4 = wb.create_sheet("原始数据-业务")
BIZ = "原始数据-业务"
put_title(ws4, "A1:F1", "业务与经营数据（单位：人民币万元；资料截止2026-08-30）")

# 一、2025年度收入结构（按产品）
put_section(ws4, "A3:F3", "一、2025年度主营业务收入结构（按产品，年报口径）")
for i, h in enumerate(["产品", "收入（万元）", "占比", "备注"], start=1):
    ws4.cell(row=4, column=i, value=h)
style_range(ws4, "A4:D4", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
prod_rows = [
    ("人形机器人", 86783.19, "2025年占比51.07%，第一大收入来源；全年出货超5,500台（纯人形，不含轮式双臂），出货量全球第一"),
    ("四足机器人", 69762.56, "占比41.05%；B系列行业级+Go系列消费级，2022-2025Q3累计销量超3万台"),
    ("机器人组件", 10373.67, "占比6.10%；关节模组、灵巧手、协作机械臂、感知传感器等"),
    ("其他业务", 2315.84, "占比1.36%"),
    ("其他", 691.67, "占比0.41%"),
]
r = 5
for name, v, note in prod_rows:
    ws4[f"A{r}"] = name; ws4[f"B{r}"] = v; ws4[f"D{r}"] = note
    ws4[f"C{r}"] = f'=IF(OR($B$10="",$B$10=0),"",B{r}/$B$10)'
    ws4[f"B{r}"].number_format = FMT_AMT; ws4[f"C{r}"].number_format = FMT_PCT
    r += 1
ws4["A10"] = "合计"; ws4["B10"] = "=SUM(B5:B9)"
ws4["C10"] = '=IF(OR(B10="",B10=0),"",1)'
ws4["B10"].number_format = FMT_AMT; ws4["C10"].number_format = FMT_PCT
style_range(ws4, "A5:D10", font=F_BODY, align=AL_L)
for row in ws4["B5:C10"]:
    for c in row: c.alignment = AL_R
style_range(ws4, "A10:D10", font=F_BOLD, fill=FILL_LIGHT, align=AL_L)
ws4["B10"].alignment = AL_R; ws4["C10"].alignment = AL_R

# 二、2025年度收入结构（按地域）
put_section(ws4, "A12:F12", "二、2025年度收入结构（按地域，年报口径）")
for i, h in enumerate(["地域", "收入（万元）", "占比", "备注"], start=1):
    ws4.cell(row=13, column=i, value=h)
style_range(ws4, "A13:D13", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
geo_rows = [
    ("境内", 94445.56, "占比55.58%；2025年春晚演出后境内需求显著放量，为2022年以来境内占比首次过半"),
    ("境外", 73165.53, "占比43.06%；2022-2024年境外收入占比均超50%，2025年结构反转"),
    ("其他业务", 2315.84, "占比1.36%"),
]
r = 14
for name, v, note in geo_rows:
    ws4[f"A{r}"] = name; ws4[f"B{r}"] = v; ws4[f"D{r}"] = note
    ws4[f"C{r}"] = f'=IF(OR($B$17="",$B$17=0),"",B{r}/$B$17)'
    ws4[f"B{r}"].number_format = FMT_AMT; ws4[f"C{r}"].number_format = FMT_PCT
    r += 1
ws4["A17"] = "合计"; ws4["B17"] = "=SUM(B14:B16)"
ws4["C17"] = '=IF(OR(B17="",B17=0),"",1)'
ws4["B17"].number_format = FMT_AMT; ws4["C17"].number_format = FMT_PCT
style_range(ws4, "A14:D17", font=F_BODY, align=AL_L)
for row in ws4["B14:C17"]:
    for c in row: c.alignment = AL_R
style_range(ws4, "A17:D17", font=F_BOLD, fill=FILL_LIGHT, align=AL_L)
ws4["B17"].alignment = AL_R; ws4["C17"].alignment = AL_R

# 三、收入结构历史趋势
put_section(ws4, "A19:F19", "三、收入结构历史趋势（占主营业务收入比例）")
for i, h in enumerate(["年度", "人形机器人占比", "四足机器人占比", "境外收入占比", "备注"], start=1):
    ws4.cell(row=20, column=i, value=h)
style_range(ws4, "A20:E20", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
trend_rows = [
    ("2022年度", None, 0.7657, None, "四足机器人占总营收76.57%；境外收入占比超50%（精确值待核）"),
    ("2023年度", 0.0188, None, None, "首款人形H1上市当年，人形收入占比1.88%；境外占比超50%"),
    ("2024年度", 0.276, None, None, "中型人形G1放量，人形占比提升至27.6%；境外占比超50%"),
    ("2025Q1-3", 0.5153, None, 0.392, "人形收入5.95亿元（+642.38%）首次反超四足；境内占比60.8%"),
    ("2025年度", 0.5107, 0.4105, 0.4306, "人形51.07%/四足41.05%/境外43.06%（年报口径）"),
]
r = 21
for vals in trend_rows:
    for i, v in enumerate(vals, start=1):
        if v is not None:
            ws4.cell(row=r, column=i, value=v)
            if i in (2, 3, 4):
                ws4.cell(row=r, column=i).number_format = FMT_PCT
    r += 1
style_range(ws4, "A21:E25", font=F_BODY, align=AL_L)
for row in ws4["B21:D25"]:
    for c in row: c.alignment = AL_R

# 四、销量与产品动态
put_section(ws4, "A27:F27", "四、销量与产品动态（招股书/官方口径）")
for i, h in enumerate(["指标", "数值", "单位", "备注"], start=1):
    ws4.cell(row=28, column=i, value=h)
style_range(ws4, "A28:D28", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
vol_rows = [
    ("四足机器人累计销量（2022-2025Q3）", 30000, "台", "超3万台，全球四足机器人市场第一梯队"),
    ("2025年度人形机器人出货量", 5500, "台", "超5,500台（纯人形，不含轮式双臂），出货量全球第一（约数）"),
    ("2025Q1-3人形机器人销量", 3551, "台", "同比增长1054.8%"),
    ("2025Q1-3人形机器人收入", 59500, "万元", "同比增长642.38%"),
    ("2025Q1-3四足机器人收入", 48800, "万元", "同比增长182.22%"),
    ("2025Q1-3人形收入中科研教育领域占比", 0.736, "%", "科研教育为当前最主要下游场景；海外收入占比超40%"),
]
r = 29
for name, v, unit, note in vol_rows:
    ws4[f"A{r}"] = name; ws4[f"B{r}"] = v; ws4[f"C{r}"] = unit; ws4[f"D{r}"] = note
    if unit == "%":
        ws4[f"B{r}"].number_format = FMT_PCT
    else:
        ws4[f"B{r}"].number_format = FMT_NUM
    r += 1
style_range(ws4, "A29:D34", font=F_BODY, align=AL_L)
for row in ws4["B29:B34"]:
    for c in row: c.alignment = AL_R

# 五、分产品毛利率
put_section(ws4, "A36:F36", "五、分产品毛利率（招股书披露口径）")
for i, h in enumerate(["产品", "2023年度", "2024年度", "2025Q1-3", "备注"], start=1):
    ws4.cell(row=37, column=i, value=h)
style_range(ws4, "A37:E37", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
ws4["A38"] = "人形机器人"; ws4["B38"] = 0.877; ws4["C38"] = 0.684; ws4["D38"] = 0.629
ws4["E38"] = "毛利率随G1放量与主动降价而收窄，但仍显著高于整体水平"
ws4["A39"] = "机器人组件"; ws4["B39"] = 0.488; ws4["C39"] = 0.569; ws4["D39"] = 0.604
ws4["E39"] = "组件毛利率稳步提升"
for rr in (38, 39):
    for cc in "BCD":
        ws4[f"{cc}{rr}"].number_format = FMT_PCT
style_range(ws4, "A38:E39", font=F_BODY, align=AL_L)
for row in ws4["B38:D39"]:
    for c in row: c.alignment = AL_R

# 六、IPO与上市信息
put_section(ws4, "A41:F41", "六、IPO与上市信息（截至2026-08-30）")
for i, h in enumerate(["项目", "内容", "备注"], start=1):
    ws4.cell(row=42, column=i, value=h)
style_range(ws4, "A42:C42", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
ipo_rows = [
    ("IPO受理日期", "2026-03-20", "上交所科创板受理，适用“预先审阅”机制"),
    ("上市委会议通过", "2026-06-01", "受理至过会约70余天"),
    ("上市日期", "2026-08-19", "科创板，A股“人形机器人整机第一股”"),
    ("证券代码/简称", "688836.SH 宇树科技-W", "上市后未盈利?否——已实现盈利；-W为特殊标识（加权表决权/类似安排，以公告为准）"),
    ("发行价格", "150.80元/股", "发行市盈率约219倍"),
    ("拟募集资金", "420,200万元（42.02亿元）", "投向智能机器人模型研发、机器人本体研发、新型智能机器人产品开发、智能机器人制造基地建设四大项目"),
    ("拟公开发行新股", "不低于4,044.64万股", "招股书披露"),
    ("上市首日表现", "开盘1,100元/股（+629.44%），收盘845元/股，成交额231.60亿元", "首日换手率85.28%；上市后股价波动较大，截至8月底较首日高点明显回落"),
    ("控股股东/实控人", "王兴兴，直接持股23.8216%", "控制近七成表决权（据媒体披露）"),
    ("主要机构股东", "含美团、蚂蚁集团、红杉中国、腾讯、阿里等（媒体披露）", "股东阵容详见招股书"),
]
r = 43
for name, v, note in ipo_rows:
    ws4[f"A{r}"] = name; ws4[f"B{r}"] = v; ws4[f"C{r}"] = note
    r += 1
style_range(ws4, "A43:C52", font=F_BODY, align=AL_L)
widths4 = [30, 16, 16, 16, 55, 10]
for i, w in enumerate(widths4, start=1):
    ws4.column_dimensions[get_column_letter(i)].width = w
ws4.column_dimensions["B"].width = 24
ws4.column_dimensions["C"].width = 30
ws4.column_dimensions["D"].width = 55

# ============================================================
# Sheet 5: 核心计算
# ============================================================
ws5 = wb.create_sheet("核心计算")
CAL = "核心计算"
put_title(ws5, "A1:H1", "核心计算（公式联动“原始数据-财务”，修改原始数据后自动更新）")
for i, h in enumerate(["指标", "单位", "2022年度", "2023年度", "2024年度", "2025年度", "2026H1", "计算口径说明"], start=1):
    ws5.cell(row=2, column=i, value=h)
style_range(ws5, "A2:H2", font=F_HEADER, fill=FILL_HEADER, align=AL_C)

def fin(col, row):
    return f"'{FIN}'!{col}{row}"

# 行3: 营业收入同比增速
ws5["A3"] = "营业收入同比增速"; ws5["B3"] = "%"
ws5["D3"] = f'=IF(OR({fin("C",3)}="",{fin("C",3)}=0),"",{fin("D",3)}/{fin("C",3)}-1)'
ws5["E3"] = f'=IF(OR({fin("D",3)}="",{fin("D",3)}=0),"",{fin("E",3)}/{fin("D",3)}-1)'
ws5["F3"] = f'=IF(OR({fin("E",3)}="",{fin("E",3)}=0),"",{fin("F",3)}/{fin("E",3)}-1)'
ws5["G3"] = f'=IF(OR({fin("G",3)}="",{fin("G",3)}=0),"",{fin("J",3)}/{fin("G",3)}-1)'
ws5["H3"] = "2026H1为对2025H1（推算值）的同比；2025年度同比对应招股书披露+332.64%~335.36%（版本差异）"
# 行4: 归母净利率
ws5["A4"] = "归母净利率"; ws5["B4"] = "%"
for cc, pc in (("C", "C"), ("D", "D"), ("E", "E"), ("F", "F")):
    ws5[f"{cc}4"] = f'=IF(OR({fin(pc,3)}="",{fin(pc,3)}=0),"",{fin(cc,4)}/{fin(pc,3)})'
ws5["G4"] = f'=IF(OR({fin("J",3)}="",{fin("J",3)}=0),"",{fin("J",4)}/{fin("J",3)})'
ws5["H4"] = "归母净利润/营业收入"
# 行5: 扣非净利率
ws5["A5"] = "扣非归母净利率"; ws5["B5"] = "%"
for cc in ("C", "D", "E", "F"):
    ws5[f"{cc}5"] = f'=IF(OR({fin(cc,3)}="",{fin(cc,3)}=0),"",{fin(cc,6)}/{fin(cc,3)})'
ws5["G5"] = f'=IF(OR({fin("J",3)}="",{fin("J",3)}=0),"",{fin("J",6)}/{fin("J",3)})'
ws5["H5"] = "扣非归母净利润/营业收入；2025年度约34.77%（券商口径34.8%一致）"
# 行6: 研发费用率
ws5["A6"] = "研发费用率"; ws5["B6"] = "%"
for cc in ("D", "E", "F"):
    ws5[f"{cc}6"] = f'=IF(OR({fin(cc,3)}="",{fin(cc,3)}=0),"",{fin(cc,9)}/{fin(cc,3)})'
ws5["G6"] = f'=IF(OR({fin("J",3)}="",{fin("J",3)}=0),"",{fin("J",9)}/{fin("J",3)})'
ws5["H6"] = "研发费用/营业收入；2024年研发费用为推算值，结果仅供参考"
# 行7: 扣非归母净利润同比
ws5["A7"] = "扣非归母净利润同比增速"; ws5["B7"] = "%"
ws5["E7"] = f'=IF(OR({fin("D",6)}="",{fin("D",6)}=0),"",{fin("E",6)}/{fin("D",6)}-1)'
ws5["F7"] = f'=IF(OR({fin("E",6)}="",{fin("E",6)}=0),"",{fin("F",6)}/{fin("E",6)}-1)'
ws5["G7"] = f'=IF(OR({fin("G",6)}="",{fin("G",6)}=0),"",{fin("J",6)}/{fin("G",6)}-1)'
ws5["H7"] = "2026H1为对2025H1（推算值）的同比，与披露值-19.34%一致；2025年度同比披露口径为+652.78%~674.29%"
for rr in (3, 4, 5, 6, 7):
    for cc in ("C", "D", "E", "F", "G"):
        if ws5[f"{cc}{rr}"].value is not None:
            ws5[f"{cc}{rr}"].number_format = FMT_PCT
style_range(ws5, "A3:H7", font=F_BODY, align=AL_L)
for row in ws5["C3:G7"]:
    for c in row: c.alignment = AL_R
for rr in range(3, 8):
    ws5[f"A{rr}"].font = F_BOLD

# 关键综合指标
put_section(ws5, "A9:H9", "关键综合指标")
for i, h in enumerate(["指标", "数值", "单位", "计算说明"], start=1):
    ws5.cell(row=10, column=i, value=h)
style_range(ws5, "A10:D10", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
key_rows = [
    ("2022-2025营业收入CAGR", f'=IF(OR({fin("C",3)}="",{fin("C",3)}=0,{fin("F",3)}="",{fin("F",3)}=0),"",({fin("F",3)}/{fin("C",3)})^(1/3)-1)', "%", "2022→2025三年复合增速；招股书按2025Q1-3年化口径披露为133.09%（口径不同）"),
    ("2023-2025营业收入CAGR", f'=IF(OR({fin("D",3)}="",{fin("D",3)}=0,{fin("F",3)}="",{fin("F",3)}=0),"",({fin("F",3)}/{fin("D",3)})^(1/2)-1)', "%", "2023→2025两年复合增速"),
    ("2025年营收相对2022年倍数", f'=IF(OR({fin("C",3)}="",{fin("C",3)}=0),"",{fin("F",3)}/{fin("C",3)})', "倍", "三年约13.8倍"),
    ("2025年度扣非归母净利率", "=IF(OR(F5=\"\",F5=0),\"\",F5)", "%", "引用上行计算结果"),
    ("2026H1扣非归母净利率", "=IF(OR(G5=\"\",G5=0),\"\",G5)", "%", "2026H1扣非2.44亿元/营收11.52亿元"),
    ("2026Q1扣非归母净利率", f'=IF(OR({fin("I",3)}="",{fin("I",3)}=0),"",{fin("I",6)}/{fin("I",3)})', "%", "2026Q1扣非净利率约9.52%，受研发与销售费用前置影响偏低"),
    ("2026Q1营业收入同比增速", 0.6849, "%", "公司一季报披露值（+68.49%），非本表推算"),
    ("2026H1研发费用同比增速", f'=IF(OR({fin("G",9)}="",{fin("G",9)}=0),"",{fin("J",9)}/{fin("G",9)}-1)', "%", "与披露口径+152%（约1.52倍）一致"),
    ("2026H1销售费用相对2025全年", f'=IF(OR({fin("F",10)}="",{fin("F",10)}=0),"",{fin("J",10)}/{fin("F",10)})', "倍", "2026H1销售费用已超2025年全年"),
    ("2025年度销售费用率", f'=IF(OR({fin("F",3)}="",{fin("F",3)}=0),"",{fin("F",10)}/{fin("F",3)})', "%", "约8.31%（券商口径一致）"),
    ("2025年人形机器人收入占比", f'=IF(OR(\'{BIZ}\'!B10="",\'{BIZ}\'!B10=0),"",\'{BIZ}\'!B5/\'{BIZ}\'!B10)', "%", "引用业务表计算结果"),
    ("2026H1资产总额较2025年末增幅", f'=IF(OR({fin("F",12)}="",{fin("F",12)}=0),"",{fin("J",12)}/{fin("F",12)}-1)', "%", "与披露值+19.85%一致（2025年末数为反推值）"),
]
r = 11
for name, v, unit, note in key_rows:
    ws5[f"A{r}"] = name; ws5[f"B{r}"] = v; ws5[f"C{r}"] = unit; ws5[f"D{r}"] = note
    if unit == "%":
        ws5[f"B{r}"].number_format = FMT_PCT
    else:
        ws5[f"B{r}"].number_format = '0.00'
    r += 1
style_range(ws5, "A11:D22", font=F_BODY, align=AL_L)
for row in ws5["B11:B22"]:
    for c in row: c.alignment = AL_R
widths5 = [26, 14, 8, 14, 14, 14, 14, 55]
for i, w in enumerate(widths5, start=1):
    ws5.column_dimensions[get_column_letter(i)].width = w
ws5.column_dimensions["D"].width = 60

# ============================================================
# Sheet 6: 趋势图表
# ============================================================
ws6 = wb.create_sheet("趋势图表")
put_title(ws6, "A1:E1", "趋势图表（数据块引用原始数据与核心计算，图表随数据联动）")

# 数据块A：营收与增速
put_section(ws6, "A3:C3", "图1数据：营业收入与增速（年度）")
for i, h in enumerate(["年度", "营业收入（亿元）", "同比增速（%）"], start=1):
    ws6.cell(row=4, column=i, value=h)
style_range(ws6, "A4:C4", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
rev_years = [("2022", "C", None), ("2023", "D", "D"), ("2024", "E", "E"), ("2025", "F", "F")]
r = 5
for label, col, calcol in rev_years:
    ws6[f"A{r}"] = label
    ws6[f"B{r}"] = f'={fin(col,3)}/10000'
    ws6[f"B{r}"].number_format = '0.00'
    if calcol:
        ws6[f"C{r}"] = f"='{CAL}'!{calcol}3*100"
        ws6[f"C{r}"].number_format = FMT_PCT1
    r += 1
style_range(ws6, "A5:C8", font=F_BODY, align=AL_C)
for row in ws6["B5:C8"]:
    for c in row: c.alignment = AL_R

# 数据块B：净利润
put_section(ws6, "A11:C11", "图2数据：归母净利润与扣非归母净利润（年度）")
for i, h in enumerate(["年度", "归母净利润（亿元）", "扣非归母净利润（亿元）"], start=1):
    ws6.cell(row=12, column=i, value=h)
style_range(ws6, "A12:C12", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
r = 13
for label, col in (("2022", "C"), ("2023", "D"), ("2024", "E"), ("2025", "F")):
    ws6[f"A{r}"] = label
    ws6[f"B{r}"] = f'={fin(col,4)}/10000'
    ws6[f"C{r}"] = f'={fin(col,6)}/10000'
    ws6[f"B{r}"].number_format = '0.00'; ws6[f"C{r}"].number_format = '0.00'
    r += 1
style_range(ws6, "A13:C16", font=F_BODY, align=AL_C)
for row in ws6["B13:C16"]:
    for c in row: c.alignment = AL_R

# 数据块C：利润率
put_section(ws6, "A19:C19", "图3数据：利润率趋势（年度）")
for i, h in enumerate(["年度", "主营业务毛利率（%）", "扣非归母净利率（%）"], start=1):
    ws6.cell(row=20, column=i, value=h)
style_range(ws6, "A20:C20", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
r = 21
for label, col, calcol in (("2022", "C", "C"), ("2023", "D", "D"), ("2024", "E", "E"), ("2025", "F", "F")):
    ws6[f"A{r}"] = label
    ws6[f"B{r}"] = f'=IF({fin(col,7)}="","",{fin(col,7)}*100)'
    ws6[f"C{r}"] = f"=IF('{CAL}'!{calcol}5=\"\",\"\",'{CAL}'!{calcol}5*100)"
    ws6[f"B{r}"].number_format = FMT_PCT1; ws6[f"C{r}"].number_format = FMT_PCT1
    r += 1
style_range(ws6, "A21:C24", font=F_BODY, align=AL_C)
for row in ws6["B21:C24"]:
    for c in row: c.alignment = AL_R

# 数据块D：2025收入结构
put_section(ws6, "A27:C27", "图4数据：2025年度收入结构（产品）")
for i, h in enumerate(["产品", "收入（万元）"], start=1):
    ws6.cell(row=28, column=i, value=h)
style_range(ws6, "A28:B28", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
pie_rows = [("人形机器人", f"='{BIZ}'!B5"), ("四足机器人", f"='{BIZ}'!B6"), ("机器人组件", f"='{BIZ}'!B7"), ("其他", f"=SUM('{BIZ}'!B8:B9)")]
r = 29
for name, formula in pie_rows:
    ws6[f"A{r}"] = name; ws6[f"B{r}"] = formula
    ws6[f"B{r}"].number_format = FMT_AMT
    r += 1
style_range(ws6, "A29:B32", font=F_BODY, align=AL_C)
for row in ws6["B29:B32"]:
    for c in row: c.alignment = AL_R

# 数据块E：人形占比
put_section(ws6, "A35:C35", "图5数据：人形机器人收入占比（年度）")
for i, h in enumerate(["年度", "人形机器人收入占比（%）"], start=1):
    ws6.cell(row=36, column=i, value=h)
style_range(ws6, "A36:B36", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
h_rows = [("2023", f"'{BIZ}'!B22"), ("2024", f"'{BIZ}'!B23"), ("2025", f"'{BIZ}'!B25")]
r = 37
for label, ref in h_rows:
    ws6[f"A{r}"] = label; ws6[f"B{r}"] = f'=IF({ref}="","",{ref}*100)'
    ws6[f"B{r}"].number_format = FMT_PCT1
    r += 1
style_range(ws6, "A37:B39", font=F_BODY, align=AL_C)
for row in ws6["B37:B39"]:
    for c in row: c.alignment = AL_R

# 图1：营收柱状+增速折线（次坐标轴）
c1 = BarChart(); c1.type = "col"; c1.style = 10
c1.title = "营业收入及同比增速（2022-2025）"
d1 = Reference(ws6, min_col=2, min_row=4, max_row=8)
cats1 = Reference(ws6, min_col=1, min_row=5, max_row=8)
c1.add_data(d1, titles_from_data=True); c1.set_categories(cats1)
c1.y_axis.title = "营业收入（亿元）"; c1.x_axis.title = "年度"
c1.y_axis.majorGridlines = None
l1 = LineChart()
d1b = Reference(ws6, min_col=3, min_row=4, max_row=8)
l1.add_data(d1b, titles_from_data=True)
l1.y_axis.axId = 200; l1.y_axis.title = "同比增速（%）"
l1.y_axis.majorGridlines = None
c1.y_axis.crosses = "max"
c1 += l1
c1.width = 16; c1.height = 8.5
ws6.add_chart(c1, "F3")

# 图2：净利润柱状
c2 = BarChart(); c2.type = "col"; c2.style = 12
c2.title = "归母净利润与扣非归母净利润（2022-2025）"
d2 = Reference(ws6, min_col=2, max_col=3, min_row=12, max_row=16)
cats2 = Reference(ws6, min_col=1, min_row=13, max_row=16)
c2.add_data(d2, titles_from_data=True); c2.set_categories(cats2)
c2.y_axis.title = "亿元"; c2.x_axis.title = "年度"
c2.width = 16; c2.height = 8.5
ws6.add_chart(c2, "F20")

# 图3：利润率折线
c3 = LineChart(); c3.style = 12
c3.title = "主营业务毛利率与扣非归母净利率（2022-2025）"
d3 = Reference(ws6, min_col=2, max_col=3, min_row=20, max_row=24)
cats3 = Reference(ws6, min_col=1, min_row=21, max_row=24)
c3.add_data(d3, titles_from_data=True); c3.set_categories(cats3)
c3.y_axis.title = "%"; c3.x_axis.title = "年度"
c3.width = 16; c3.height = 8.5
ws6.add_chart(c3, "F37")

# 图4：2025收入结构饼图
c4 = PieChart(); c4.title = "2025年度收入结构（按产品）"
d4 = Reference(ws6, min_col=2, min_row=28, max_row=32)
cats4 = Reference(ws6, min_col=1, min_row=29, max_row=32)
c4.add_data(d4, titles_from_data=True); c4.set_categories(cats4)
c4.dataLabels = DataLabelList(); c4.dataLabels.showPercent = True
c4.width = 16; c4.height = 8.5
ws6.add_chart(c4, "F54")

# 图5：人形占比折线
c5 = LineChart(); c5.style = 13
c5.title = "人形机器人收入占比（2023-2025）"
d5 = Reference(ws6, min_col=2, min_row=36, max_row=39)
cats5 = Reference(ws6, min_col=1, min_row=37, max_row=39)
c5.add_data(d5, titles_from_data=True); c5.set_categories(cats5)
c5.y_axis.title = "%"; c5.x_axis.title = "年度"
c5.width = 16; c5.height = 8.5
ws6.add_chart(c5, "F71")

widths6 = [14, 18, 18, 10, 10]
for i, w in enumerate(widths6, start=1):
    ws6.column_dimensions[get_column_letter(i)].width = w

# ============================================================
# Sheet 7: 分析结论
# ============================================================
ws7 = wb.create_sheet("分析结论")
put_title(ws7, "A1:D1", "分析结论（区分事实、计算结果与分析判断）")
for i, h in enumerate(["序号", "结论要点", "类型", "依据（数据/来源）"], start=1):
    ws7.cell(row=2, column=i, value=h)
style_range(ws7, "A2:D2", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
conclusions = [
    (1, "营收三年约13.8倍高速扩张：营业收入由2022年1.23亿元增至2025年16.99亿元，2022-2025年CAGR约140%，2025年同比+333%（招股书披露区间+332.64%~335.36%）。", "计算结果", "原始数据-财务、核心计算；招股书/年报"),
    (2, "2024年起扭亏为盈并快速放大：归母净利润由2023年-1,114.51万元升至2024年9,450.18万元、2025年约2.78亿元；扣非归母净利润由-1,801.91万元升至2025年59,075.28万元。", "事实（含约数）", "招股书、上市公告书"),
    (3, "盈利质量持续改善：主营业务毛利率由2022年44.18%升至2025年约60.27%（整体口径60.44%），扣非净利率2025年达约34.8%，在全球人形机器人公司中属少数实现规模化盈利的样本。", "计算结果+判断", "招股书、年报、核心计算"),
    (4, "收入结构完成切换：人形机器人收入占比由2023年1.88%→2024年27.6%→2025年51.07%，2025年首次超过四足机器人成为第一大收入来源；2025年人形出货超5,500台，居全球第一。", "事实", "招股书、年报"),
    (5, "市场结构反转：2022-2024年境外收入占比均超50%，2025年境内占比升至55.58%（春晚等品牌事件带动），境外降至43.06%，内需成为主要增量。", "事实+判断", "招股书、年报"),
    (6, "2026年增速换挡：2026Q1营收同比+68.49%、2026H1同比+48.54%，较2025年+333%明显回落；公司归因于营收基数大幅提升、行业热度缓和及竞争加剧。", "事实", "一季报、上市公告书"),
    (7, "阶段性的“增收不增利”信号：2026Q1扣非同比-52.55%、2026H1扣非同比-19.34%；2026H1研发费用1.36亿元（+152%）、销售费用1.64亿元（已超2025年全年），费用前置是主因，2026Q2扣非净利率已回升（招股书预告区间31.11%-34.42%）。", "事实+判断", "一季报、上市公告书、券商拆分"),
    (8, "归母与扣非差异主要来自股份支付：2025年确认非经常性股份支付34,906.55万元（主要在2025H1），导致2025H1归母-3,202.45万元而扣非为正，阅读利润数据时须区分口径。", "事实", "上市公告书、招股书"),
    (9, "盈利有现金流支撑：2025年经营活动现金净流入超6.7亿元，较2024年增加约4.8亿元；2026-06-30总资产38.45亿元（较上年末+19.85%）、流动资产28.88亿元，资金面稳健。", "事实（含约数）", "招股书、上市公告书"),
    (10, "下游场景仍以科研教育为主：2025Q1-3人形收入中科研教育领域占比73.6%，工业与商业场景的规模化落地仍是未来增长的关键变量。", "事实+判断", "招股书（媒体转引）"),
    (11, "竞争与估值风险：国内整车/消费电子企业入局人形机器人，产品定价、份额与利润率面临潜在压力；发行市盈率约219倍，上市首日开盘1,100元/股后股价大幅回落，估值消化依赖业绩持续兑现。", "事实+判断", "招股书风险提示、上市公告书、公开行情"),
    (12, "总体判断：公司处于“高速成长+盈利兑现+结构切换”阶段，2026年上半年呈现增速换挡与费用前置的组合特征；后续重点跟踪人形机器人工业场景订单、毛利率走势及费用率回归水平。", "分析判断", "本底稿综合"),
]
r = 3
for no, text, typ, basis in conclusions:
    ws7[f"A{r}"] = no; ws7[f"B{r}"] = text; ws7[f"C{r}"] = typ; ws7[f"D{r}"] = basis
    r += 1
style_range(ws7, f"A3:D{r-1}", font=F_BODY, align=AL_L)
for row in ws7[f"A3:A{r-1}"]:
    row[0].alignment = AL_C
for row in ws7[f"C3:C{r-1}"]:
    row[0].alignment = AL_C
r += 1
put_section(ws7, f"A{r}:D{r}", "声明")
r += 1
ws7[f"A{r}"] = "以上结论基于截至2026-08-30的公开资料；标注“约数/推算”的数据请先按“说明与口径”表中的待核验清单核对披露原文后再对外使用；券商预测数据见“预测参考(非事实)”表，均非已发生事实。"
ws7.merge_cells(f"A{r}:D{r}")
ws7[f"A{r}"].font = F_NOTE; ws7[f"A{r}"].alignment = AL_L
widths7 = [6, 80, 14, 30]
for i, w in enumerate(widths7, start=1):
    ws7.column_dimensions[get_column_letter(i)].width = w

# ============================================================
# Sheet 8: 预测参考(非事实)
# ============================================================
ws8 = wb.create_sheet("预测参考(非事实)")
put_title(ws8, "A1:F1", "机构预测参考——以下均为预测/前瞻陈述，不是已发生的事实")
ws8["A2"] = "⚠ 特别提示：本表全部数据为机构预测或公司业绩预告，截至2026-08-30均未经审计、未实际发生，仅作方向性参考，不得作为历史事实引用。"
ws8.merge_cells("A2:F2")
ws8["A2"].font = Font(name="微软雅黑", size=10, bold=True, color=XL_WARN_TXT)
ws8["A2"].fill = PatternFill("solid", fgColor=XL_WARN)
ws8["A2"].alignment = AL_L
for i, h in enumerate(["机构", "指标", "2026E", "2027E", "2028E", "数据性质"], start=1):
    ws8.cell(row=4, column=i, value=h)
style_range(ws8, "A4:F4", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
forecast_rows = [
    ("野村证券（媒体报道转引）", "营业收入（亿元）", 26.87, 53.96, 131.84, "机构预测，非事实"),
    ("招商证券（媒体报道转引）", "营业收入（亿元）", 30.97, 49.60, 76.83, "机构预测，非事实"),
]
r = 5
for row in forecast_rows:
    for i, v in enumerate(row, start=1):
        ws8.cell(row=r, column=i, value=v)
        if isinstance(v, float):
            ws8.cell(row=r, column=i).number_format = '0.00'
    r += 1
style_range(ws8, "A5:F6", font=F_BODY, align=AL_L)
for row in ws8["C5:E6"]:
    for c in row: c.alignment = AL_R
r += 1
put_section(ws8, f"A{r}:F{r}", "业绩预告与实际披露对照（招股书预告 vs 上市公告书实际）")
r += 1
for i, h in enumerate(["项目", "招股书预告区间（未经审计）", "实际披露（上市公告书）", "差异说明"], start=1):
    ws8.cell(row=r, column=i, value=h)
style_range(ws8, f"A{r}:D{r}", font=F_HEADER, fill=FILL_HEADER, align=AL_C)
r += 1
cmp_rows = [
    ("2026H1营业收入（亿元）", "10.52 - 11.28", "11.52", "实际超出预告区间上限，收入端强于预告"),
    ("2026H1扣非归母净利润（亿元）", "2.36 - 2.83", "2.44", "实际落于预告区间内"),
    ("2026Q2扣非净利率（推算）", "31.11% - 34.42%（预告推算）", "2026H1整体扣非净利率约21.2%", "Q1受费用前置拖累，Q2回升（据券商拆分）"),
]
for row in cmp_rows:
    for i, v in enumerate(row, start=1):
        ws8.cell(row=r, column=i, value=v)
    r += 1
style_range(ws8, f"A{r-3}:D{r-1}", font=F_BODY, align=AL_L)
r += 1
ws8[f"A{r}"] = "注：野村/招商证券预测来自媒体转引，未经研报原文核验；上表“实际披露”列才是已发生事实。"
ws8.merge_cells(f"A{r}:F{r}")
ws8[f"A{r}"].font = F_NOTE; ws8[f"A{r}"].alignment = AL_L
widths8 = [26, 26, 24, 24, 16, 16]
for i, w in enumerate(widths8, start=1):
    ws8.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT)
print("SAVED:", OUT)
