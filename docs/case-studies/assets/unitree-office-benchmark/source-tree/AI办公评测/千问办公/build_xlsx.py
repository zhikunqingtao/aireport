# -*- coding: utf-8 -*-
"""宇树科技(688836)经营与财务分析底稿构建脚本
数据截止: 2026-08-30
主源: 上交所披露的上市公告书(2026-08-18)与招股说明书(上会稿, 2026-05)
"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference

OUT = "/Users/guoqingtao/.qwenworkcn/workspace/mtlqdnun26b6cmrm/outputs/宇树科技经营与财务分析底稿.xlsx"

wb = openpyxl.Workbook()

FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF", size=10)
BLACK = Font(name=FONT, color="000000", size=10)
GREEN = Font(name=FONT, color="008000", size=10)
TITLE_F = Font(name=FONT, size=14, bold=True)
H_F = Font(name=FONT, size=10, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", start_color="1F4E78")
SEC_F = Font(name=FONT, size=11, bold=True)
SEC_FILL = PatternFill("solid", start_color="D9E1F2")
NOTE_F = Font(name=FONT, size=9, italic=True, color="808080")
B_F = Font(name=FONT, size=10, bold=True)
YEL_FILL = PatternFill("solid", start_color="FFFF00")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

PCT = "0.00%"
NUM = "#,##0.00"
INT = "#,##0"
X2 = "0.00"

A = "'原始数据-年度'"
P = "'原始数据-期间与IPO'"

def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = H_F
        cell.fill = H_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER

def put(ws, r, c, v, kind="in", fmt=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = {"in": BLUE, "f": BLACK, "x": GREEN}[kind]
    cell.border = BORDER
    if fmt:
        cell.number_format = fmt
    return cell

def label(ws, r, c, v, bold=False):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = B_F if bold else Font(name=FONT, size=10)
    cell.border = BORDER
    return cell

# ================= Sheet 1 说明与来源 =================
ws = wb.active
ws.title = "说明与来源"
ws.sheet_view.showGridLines = False
ws["A1"] = "宇树科技股份有限公司（688836.SH）经营与财务表现分析底稿"
ws["A1"].font = TITLE_F
ws["A2"] = "资料截止时间：2026-08-30　|　编制日期：2026-09-04　|　单位：除特别说明外为人民币万元"
ws["A2"].font = NOTE_F
ws["A4"] = "一、口径说明"
ws["A4"].font = SEC_F
rows = [
    ["报告期", "2023年度、2024年度、2025年度（经审计，容诚审字[2026]230Z1692号，标准无保留意见）"],
    ["审阅期间", "2026年1-3月（经审阅，容诚阅字[2026]230Z0038号）"],
    ["未审计期间", "2026年1-6月（未经审计，经第一届董事会第二十二次会议审议，见上市公告书附件二）"],
    ["预测数据", "招股说明书所载2026年1-6月预计数据为管理层估计，未经审计或审阅，不构成盈利预测或业绩承诺；本底稿以黄底单独列示并与实际数对照，绝不混同于已发生事实"],
    ["金额单位", "统一为人民币万元；每股/单价数据为元；销量为台；比率以%列示（单元格存储为小数）"],
    ["颜色图例", "蓝字=披露原文硬编码输入；黑字=本表公式；绿字=跨表引用公式；黄底=预测数据"],
    ["可编辑性", "修改蓝字输入后，全部公式与图表自动重算"],
]
r = 5
for a, b in rows:
    ws.cell(row=r, column=1, value=a).font = B_F
    ws.cell(row=r, column=2, value=b).font = BLACK
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
r += 1
ws.cell(row=r, column=1, value="二、资料来源清单").font = SEC_F
r += 1
for i, h in enumerate(["编号", "资料名称", "披露/批复日期", "出具方", "用途", "获取方式"]):
    ws.cell(row=r, column=i + 1, value=h)
style_header(ws, r, 6)
r += 1
sources = [
    ["S1", "首次公开发行股票科创板上市公告书", "2026-08-18", "宇树科技/中信证券", "IPO要素、2026H1未审计报表、2025年末比较数据", "上交所网站披露;PDF镜像 stockmc.xueqiu.com/202608/688836_20260818_ROD1.pdf"],
    ["S2", "首次公开发行股票并在科创板上市招股说明书(上会稿)", "2026-05", "宇树科技", "报告期2023-2025财务与业务数据、产品结构、募投", "上交所披露;镜像 pdf.dfcfw.com/pdf/H2_AN202605251822861710_1.pdf"],
    ["S3", "招股说明书(注册稿)及注册批复 证监许可〔2026〕1612号", "2026-07-01", "中国证监会", "法定生效版本;关键数字已与S1/S2核对一致", "上交所网站,建议人工复核"],
    ["S4", "审计报告 容诚审字[2026]230Z1692号", "2026", "容诚会计师事务所", "2023-2025审计", "招股意向书附录"],
    ["S5", "审阅报告 容诚阅字[2026]230Z0038号", "2026", "容诚会计师事务所", "2026年1-3月审阅", "招股意向书附录"],
    ["S6", "上市公告书附件二:2026年1-6月财务会计报表", "2026-08-18", "宇树科技(未经审计)", "2026H1三大报表", "同S1"],
]
for row in sources:
    for i, v in enumerate(row):
        cell = ws.cell(row=r, column=i + 1, value=v)
        cell.font = BLUE if i in (1, 2, 3) else BLACK
        cell.border = BORDER
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
r += 1
ws.cell(row=r, column=1, value="三、边界与需人工核验事项").font = SEC_F
r += 1
for t in [
    "1) 2022年度营收1.23亿元等仅见于媒体报道,未纳入正式表(招股书报告期为2023-2025)。",
    "2) 上市首日(2026-08-19)及后续二级市场涨跌幅属行情数据,非披露财务口径,本底稿不纳入;如需要请以上交所行情为准。",
    "3) 本底稿招股书数据取自上会稿镜像;注册稿为法定文本,关键数字(2025营收169,926.93万元、扣非归母59,075.28万元、主营毛利率60.13%、研发费用14,496.56万元)已与上市公告书交叉验证一致,仍建议以注册稿原文页码复核。",
    "4) 2026H1数据未经审计;2026Q1为审阅数。",
]:
    ws.cell(row=r, column=1, value=t).font = NOTE_F
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
    r += 1
for col, w in zip("ABCDEFGHI", [16, 34, 16, 24, 36, 44, 12, 12, 12]):
    ws.column_dimensions[col].width = w

# ================= Sheet 2 原始数据-年度 =================
ws = wb.create_sheet("原始数据-年度")
ws["A1"] = "原始数据·年度（2023-2025，经审计）"
ws["A1"].font = TITLE_F
ws["A2"] = "单位：万元（每股/单价除外）　来源：S2招股说明书(上会稿)/S1上市公告书"
ws["A2"].font = NOTE_F
for i, h in enumerate(["项目", "单位", "2023", "2024", "2025", "来源/备注"]):
    ws.cell(row=3, column=i + 1, value=h)
style_header(ws, 3, 6)
annual = [
    ("营业收入", "万元", 15913.44, 39277.07, 169926.93, "S2/S1", NUM),          # r4
    ("主营业务收入", "万元", 15753.65, 38767.28, 167611.09, "S2", NUM),        # r5
    ("－四足机器人收入", "万元", 11938.09, 23054.37, 69762.56, "S2", NUM),     # r6
    ("－人形机器人收入", "万元", 296.71, 10729.76, 86783.19, "S2", NUM),       # r7
    ("－机器人组件收入", "万元", 2692.34, 4453.82, 10373.67, "S2", NUM),       # r8
    ("－其他收入", "万元", 826.51, 529.33, 691.67, "S2", NUM),                 # r9
    ("主营业务毛利率", "%", 0.4422, 0.5674, 0.6013, "S2", PCT),                # r10
    ("－四足机器人毛利率", "%", 0.4371, 0.5165, 0.5672, "S2", PCT),            # r11
    ("－人形机器人毛利率", "%", 0.8767, 0.6926, 0.6318, "S2", PCT),            # r12
    ("－组件毛利率", "%", 0.4876, 0.5694, 0.5936, "S2", PCT),                  # r13
    ("－其他毛利率", "%", 0.2111, 0.2323, 0.3353, "S2", PCT),                  # r14
    ("综合毛利率", "%", 0.4475, 0.5722, 0.6044, "S2同业比较表", PCT),          # r15
    ("主营业务毛利", "万元", 6965.75, 21996.62, 100785.07, "S2", NUM),         # r16
    ("－四足机器人毛利", "万元", 5218.21, 11906.88, 39569.16, "S2", NUM),      # r17
    ("－人形机器人毛利", "万元", 260.12, 7430.99, 54826.61, "S2", NUM),        # r18
    ("－组件毛利", "万元", 1312.90, 2535.79, 6157.41, "S2", NUM),              # r19
    ("－其他毛利", "万元", 174.52, 122.96, 231.89, "S2", NUM),                 # r20
    ("归母净利润", "万元", -1114.51, 9547.47, 27821.05, "S2/S1", NUM),         # r21
    ("扣非归母净利润", "万元", -1801.91, 7847.65, 59075.28, "S2/S1", NUM),     # r22
    ("其中:股份支付费用", "万元", 0, 0, 34906.55, "S2 非经常性,计入管理费用", NUM),  # r23
    ("销售费用", "万元", 3771.83, 5915.85, 14120.32, "S2", NUM),               # r24
    ("管理费用", "万元", 1332.80, 2500.52, 39959.61, "S2", NUM),               # r25
    ("研发费用", "万元", 4995.18, 7001.70, 14496.56, "S2/S1", NUM),            # r26
    ("财务费用", "万元", -732.47, -1718.64, 98.61, "S2", NUM),                 # r27
    ("经营活动现金流量净额", "万元", 494.25, 19239.13, 66998.18, "S2", NUM),   # r28
    ("资产总额", "万元", 39127.15, 152786.94, 320853.83, "S2", NUM),           # r29
    ("归属于母公司所有者权益", "万元", 29904.49, 128054.90, 260465.85, "S2", NUM),  # r30
    ("资产负债率(合并)", "%", 0.2357, 0.1619, 0.1882, "S2", PCT),              # r31
    ("加权平均ROE", "%", -0.0366, 0.1046, 0.1352, "S2", PCT),                  # r32
    ("扣非加权平均ROE", "%", -0.0592, 0.0860, 0.2870, "S2", PCT),              # r33
    ("基本每股收益", "元", None, None, 0.76, "S2", X2),                        # r34
    ("四足机器人销量", "台", 3121, 7136, 23037, "S2", INT),                    # r35
    ("四足机器人单价", "万元/台", 3.83, 3.23, 3.03, "S2", X2),                 # r36
    ("人形机器人销量", "台", 5, 412, 5215, "S2", INT),                         # r37
    ("人形机器人单价", "万元/台", 59.34, 26.04, 16.64, "S2", X2),              # r38
    ("人形机器人出货量", "台", None, None, 5511, "S2 全球第一", INT),          # r39
    ("员工总数(年末)", "人", None, None, 516, "S2", INT),                      # r40
    ("研发人员(年末)", "人", None, None, 184, "S2 占比35.66%", INT),           # r41
    ("美国市场收入占比", "%", 0.1839, 0.1954, 0.1330, "S1风险因素", PCT),       # r42
    ("前五大客户收入占比", "%", 0.1269, 0.1245, 0.1208, "S2", PCT),            # r43
    ("线上销售收入占比", "%", 0.1314, 0.1039, 0.1072, "S2", PCT),              # r44
]
r = 4
for name, unit, v23, v24, v25, note, fmt in annual:
    label(ws, r, 1, name)
    ws.cell(row=r, column=2, value=unit).font = NOTE_F
    ws.cell(row=r, column=2).border = BORDER
    for c, v in ((3, v23), (4, v24), (5, v25)):
        if v is not None:
            put(ws, r, c, v, "in", fmt)
        else:
            ws.cell(row=r, column=c).border = BORDER
    ws.cell(row=r, column=6, value=note).font = NOTE_F
    ws.cell(row=r, column=6).border = BORDER
    r += 1
for col, w in zip("ABCDEF", [26, 10, 14, 14, 14, 42]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A4"

# ================= Sheet 3 原始数据-期间与IPO =================
ws = wb.create_sheet("原始数据-期间与IPO")
ws["A1"] = "原始数据·期间（审阅/未审计）与IPO要素"
ws["A1"].font = TITLE_F
for i, h in enumerate(["项目", "单位", "2025Q1", "2025H1", "2026Q1", "2026H1", "审计属性", "来源"]):
    ws.cell(row=3, column=i + 1, value=h)
style_header(ws, 3, 8)
interim = [
    ("营业收入", "万元", 25095.87, 77571.92, 42284.05, 115224.56, "25Q1审阅;25H1/26H1未审计", "S2/S1", NUM),   # r4
    ("营业成本", "万元", None, 30907.39, None, 50688.51, "未审计", "S1附件二", NUM),                            # r5
    ("归母净利润", "万元", 9560.25, -3202.45, 5001.38, 27399.99, "同上", "S2/S1", NUM),                          # r6
    ("扣非归母净利润", "万元", 8483.65, 30243.35, 4025.36, 24393.03, "同上", "S2/S1", NUM),                      # r7
    ("经营活动现金流量净额", "万元", None, 34319.36, 3439.96, 23154.53, "同上", "S2/S1", NUM),                   # r8
    ("研发费用", "万元", None, 5386.90, None, 13590.65, "未审计", "S1附件二", NUM),                              # r9
    ("销售费用", "万元", None, 4685.11, None, 16407.27, "未审计", "S1附件二", NUM),                              # r10
    ("管理费用", "万元", None, 36399.38, None, 4208.48, "25H1含股份支付34,906.55", "S1附件二", NUM),             # r11
    ("资产总额", "万元", None, None, 345907.18, 384546.94, "同上", "S2/S1", NUM),                                # r12
    ("归母所有者权益", "万元", None, None, 265533.55, 287998.48, "同上", "S2/S1", NUM),                          # r13
    ("基本每股收益", "元", None, -0.09, None, 0.75, "未审计", "S1", X2),                                         # r14
]
r = 4
for name, unit, a, b, c, d, attr, src, fmt in interim:
    label(ws, r, 1, name)
    ws.cell(row=r, column=2, value=unit).font = NOTE_F
    ws.cell(row=r, column=2).border = BORDER
    for cc, v in ((3, a), (4, b), (5, c), (6, d)):
        if v is not None:
            put(ws, r, cc, v, "in", fmt)
        else:
            ws.cell(row=r, column=cc).border = BORDER
    ws.cell(row=r, column=7, value=attr).font = NOTE_F
    ws.cell(row=r, column=7).border = BORDER
    ws.cell(row=r, column=8, value=src).font = NOTE_F
    ws.cell(row=r, column=8).border = BORDER
    r += 1
# r=15
r = 16
ws.cell(row=r, column=1, value="2026年1-6月预计数据（招股书·预测·未经审计或审阅·不构成盈利预测）").font = SEC_F
ws.cell(row=r, column=1).fill = YEL_FILL
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
r = 17
for i, h in enumerate(["项目", "单位", "预计下限", "预计上限", "上年同期", "同比区间", "属性", "来源"]):
    ws.cell(row=r, column=i + 1, value=h)
style_header(ws, r, 8)
forecast = [
    ("营业收入", "万元", 105200, 112800, 77571.92, "+35.62%至+45.41%", "预测", "S2"),      # r18
    ("归母净利润", "万元", 25800, 30600, -3202.45, "扭亏", "预测", "S2"),                  # r19
    ("扣非归母净利润", "万元", 23600, 28300, 30243.35, "-21.97%至-6.43%", "预测", "S2"),   # r20
]
r = 18
for name, unit, lo, hi, base, yoy, attr, src in forecast:
    label(ws, r, 1, name)
    ws.cell(row=r, column=2, value=unit).font = NOTE_F
    for cc, v in ((3, lo), (4, hi), (5, base)):
        cell = put(ws, r, cc, v, "in", NUM)
        cell.fill = YEL_FILL
    ws.cell(row=r, column=6, value=yoy).font = NOTE_F
    ws.cell(row=r, column=7, value=attr).font = NOTE_F
    ws.cell(row=r, column=8, value=src).font = NOTE_F
    r += 1
# r=21
r = 22
ws.cell(row=r, column=1, value="IPO与发行要素（S1上市公告书, 2026-08-18）").font = SEC_F
r = 23
ipo_num = [
    ("发行价格", 150.80, "元/股"),                 # r23
    ("发行后总股本", 40446.4340, "万股"),          # r24
    ("募集资金总额", 609932.22, "万元"),           # r25
    ("募集资金净额", 591714.92, "万元"),           # r26
    ("发行费用(不含税)", 18217.31, "万元"),        # r27
    ("发行市盈率(扣非孰低)", 219.23, "倍"),        # r28
    ("发行市净率", 7.16, "倍"),                    # r29
    ("发行后每股收益", 0.69, "元"),                # r30
    ("发行后每股净资产", 21.07, "元"),             # r31
    ("行业平均静态市盈率(T-3,C34)", 38.56, "倍"),  # r32
    ("拟使用募集资金(募投合计)", 420171.12, "万元"),  # r33
    ("发行前最后一轮投后估值(2025-06)", 1270000, "万元"),  # r34
]
for name, v, unit in ipo_num:
    label(ws, r, 1, name)
    put(ws, r, 2, v, "in", NUM if v >= 100 else X2)
    ws.cell(row=r, column=3, value=unit).font = NOTE_F
    r += 1
# r=35
ipo_txt = [
    ("证券代码/上市板块/上市日期", "688836.SH / 科创板 / 2026-08-19"),
    ("本次发行新股数量", "4,044.6434万股（占发行后总股本10%）"),
    ("特别表决权: 王兴兴表决权", "发行前68.7816%; 发行后≤65.3090%"),
    ("战略配售", "占20%; 社保基金/深度求索/昆仑资本/南网产融/天翼资本/启善投资(腾讯关联)/中证投资/员工资管计划, 限售12-36个月"),
]
r += 1
for name, val in ipo_txt:
    label(ws, r, 1, name)
    ws.cell(row=r, column=2, value=val).font = BLUE
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    r += 1
for col, w in zip("ABCDEFGH", [28, 14, 14, 14, 16, 18, 30, 12]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A4"

# ================= Sheet 4 核心计算 =================
ws = wb.create_sheet("核心计算")
ws["A1"] = "核心计算（全部为公式，修改原始数据自动重算）"
ws["A1"].font = TITLE_F
r = 3
for i, h in enumerate(["项目", "2024", "2025", "2026H1", "公式/口径"]):
    ws.cell(row=r, column=i + 1, value=h)
style_header(ws, r, 5)
calc_rows = [
    ("营业收入同比增速", f"={A}!D4/{A}!C4-1", f"={A}!E4/{A}!D4-1", f"={P}!F4/{P}!D4-1", "收入YoY", PCT),                      # r4
    ("扣非归母净利润同比增速", f'=IF({A}!C22<0,"基期为负",{A}!D22/{A}!C22-1)', f'=IF({A}!D22<0,"基期为负",{A}!E22/{A}!D22-1)', f'=IF({P}!D7<0,"基期为负",{P}!F7/{P}!D7-1)', "扣非YoY", PCT),              # r5
    ("归母净利润同比增速", f'=IF({A}!C21<0,"基期为负",{A}!D21/{A}!C21-1)', f'=IF({A}!D21<0,"基期为负",{A}!E21/{A}!D21-1)', f'=IF({P}!D6<0,"基期为负",{P}!F6/{P}!D6-1)', "归母YoY", PCT),  # r6
    ("人形机器人收入占主营比重", f"={A}!D7/{A}!D5", f"={A}!E7/{A}!E5", None, "人形/主营", PCT),                                  # r7
    ("四足机器人收入占主营比重", f"={A}!D6/{A}!D5", f"={A}!E6/{A}!E5", None, "四足/主营", PCT),                                  # r8
    ("四足机器人销量同比", f"={A}!D35/{A}!C35-1", f"={A}!E35/{A}!D35-1", None, "销量YoY", PCT),                                 # r9
    ("人形机器人销量同比", f"={A}!D37/{A}!C37-1", f"={A}!E37/{A}!D37-1", None, "销量YoY", PCT),                                 # r10
    ("综合毛利率", f"={A}!C15", f"={A}!E15", f"=1-{P}!F5/{P}!F4", "26H1按未审计成本推算", PCT),                                  # r11
    ("主营业务毛利率", f"={A}!C10", f"={A}!E10", None, "披露值", PCT),                                                          # r12
    ("扣非净利率", f"={A}!C22/{A}!C4", f"={A}!E22/{A}!E4", f"={P}!F7/{P}!F4", "扣非/收入", PCT),                                # r13
    ("归母净利率", f"={A}!C21/{A}!C4", f"={A}!E21/{A}!E4", f"={P}!F6/{P}!F4", "归母/收入", PCT),                                # r14
    ("研发费用率", f"={A}!C26/{A}!C4", f"={A}!E26/{A}!E4", f"={P}!F9/{P}!F4", "研发/收入", PCT),                                # r15
    ("销售费用率", f"={A}!C24/{A}!C4", f"={A}!E24/{A}!E4", f"={P}!F10/{P}!F4", "销售/收入", PCT),                               # r16
    ("管理费用率", f"={A}!C25/{A}!C4", f"={A}!E25/{A}!E4", f"={P}!F11/{P}!F4", "25含股份支付", PCT),                            # r17
    ("经营现金流/扣非净利润", f'=IF({A}!C22<=0,"基期为负",{A}!C28/{A}!C22)', f"={A}!E28/{A}!E22", f"={P}!F8/{P}!F7", "盈利现金含量", X2),  # r18
]
r = 4
for name, f24, f25, f26h, note, fmt in calc_rows:
    label(ws, r, 1, name)
    put(ws, r, 2, f24, "x", fmt)
    put(ws, r, 3, f25, "x", fmt)
    if f26h:
        put(ws, r, 4, f26h, "x", fmt)
    else:
        ws.cell(row=r, column=4).border = BORDER
    ws.cell(row=r, column=5, value=note).font = NOTE_F
    r += 1
# r=19
ws.cell(row=19, column=1, value="营业收入CAGR(2023-2025)").font = B_F
put(ws, 19, 3, f"=({A}!E4/{A}!C4)^(1/2)-1", "x", PCT)
ws.cell(row=19, column=5, value="(末/初)^(1/2)-1").font = NOTE_F
# r=21 标题
ws.cell(row=21, column=1, value="单价交叉验证（计算值 vs 披露值）").font = SEC_F
ws.cell(row=21, column=1).fill = SEC_FILL
ws.merge_cells(start_row=21, start_column=1, end_row=21, end_column=5)
r = 22
for i, h in enumerate(["项目", "2023", "2024", "2025", "口径"]):
    ws.cell(row=r, column=i + 1, value=h)
style_header(ws, r, 5)
asp_rows = [
    ("四足计算单价(万元/台)", f"={A}!C6/{A}!C35", f"={A}!D6/{A}!D35", f"={A}!E6/{A}!E35", "收入/销量", X2),   # r23
    ("四足披露单价(万元/台)", f"={A}!C36", f"={A}!D36", f"={A}!E36", "S2披露", X2),                           # r24
    ("差异", "=B23-B24", "=C23-C24", "=D23-D24", "四舍五入差异", X2),                                          # r25
    ("人形计算单价(万元/台)", f"={A}!C7/{A}!C37", f"={A}!D7/{A}!D37", f"={A}!E7/{A}!E37", "收入/销量", X2),   # r26
    ("人形披露单价(万元/台)", f"={A}!C38", f"={A}!D38", f"={A}!E38", "S2披露", X2),                           # r27
    ("差异", "=B26-B27", "=C26-C27", "=D26-D27", "四舍五入差异", X2),                                          # r28
]
r = 23
for name, a, b, c, note, fmt in asp_rows:
    label(ws, r, 1, name)
    for cc, v in ((2, a), (3, b), (4, c)):
        put(ws, r, cc, v, "x", fmt)
    ws.cell(row=r, column=5, value=note).font = NOTE_F
    r += 1
# r=29; 标题 r30
ws.cell(row=30, column=1, value="发行估值测算").font = SEC_F
ws.cell(row=30, column=1).fill = SEC_FILL
ws.merge_cells(start_row=30, start_column=1, end_row=30, end_column=5)
val_rows = [
    ("发行市值(万元)", f"={P}!B23*{P}!B24", "发行价×发行后总股本", NUM),          # r31
    ("发行市值/募资总额(倍)", "=B31/B25".replace("B25", f"{P}!B25"), "应≈10(新股占10%)", X2),  # r32
    ("P/S(2025,发行市值口径,倍)", f"=B31/{A}!E4", "市值/2025收入", X2),           # r33
    ("P/E交叉验证(倍)", f"={P}!B23/{P}!B30", "发行价/发行后EPS,披露219.23", X2),  # r34
    ("EPS交叉验证(元)", f"={A}!E21/{P}!B24", "2025孰低归母/总股本,披露0.69", X2), # r35
    ("募资净额勾稽(万元)", f"={P}!B25-{P}!B27-{P}!B26", "总额-费用-净额=0", NUM), # r36
]
r = 31
for name, f, note, fmt in val_rows:
    label(ws, r, 1, name)
    put(ws, r, 2, f, "x", fmt)
    ws.cell(row=r, column=3, value=note).font = NOTE_F
    r += 1
# r=37; 标题 r38
ws.cell(row=38, column=1, value="预测 vs 实际（2026H1：招股书预计区间 vs 上市公告书实际·未审计）").font = SEC_F
ws.cell(row=38, column=1).fill = SEC_FILL
ws.merge_cells(start_row=38, start_column=1, end_row=38, end_column=5)
r = 39
for i, h in enumerate(["项目", "预计下限", "预计上限", "实际", "对照结论"]):
    ws.cell(row=r, column=i + 1, value=h)
style_header(ws, r, 5)
fc_rows = [
    ("营业收入", f"={P}!C18", f"={P}!D18", f"={P}!F4", f'=IF({P}!F4>{P}!D18,"实际高于预计上限",IF({P}!F4<{P}!C18,"低于下限","区间内"))'),  # r40
    ("归母净利润", f"={P}!C19", f"={P}!D19", f"={P}!F6", f'=IF({P}!F6>{P}!D19,"实际高于预计上限",IF({P}!F6<{P}!C19,"低于下限","区间内"))'),  # r41
    ("扣非归母净利润", f"={P}!C20", f"={P}!D20", f"={P}!F7", f'=IF({P}!F7>{P}!D20,"实际高于预计上限",IF({P}!F7<{P}!C20,"低于下限","区间内"))'),  # r42
]
r = 40
for name, lo, hi, act, concl in fc_rows:
    label(ws, r, 1, name)
    put(ws, r, 2, lo, "x", NUM)
    put(ws, r, 3, hi, "x", NUM)
    put(ws, r, 4, act, "x", NUM)
    put(ws, r, 5, concl, "x")
    r += 1
# r=43; 标题 r44
ws.cell(row=44, column=1, value="数据勾稽校验（结果应≈0）").font = SEC_F
ws.cell(row=44, column=1).fill = SEC_FILL
ws.merge_cells(start_row=44, start_column=1, end_row=44, end_column=5)
chk = [
    ("2023 分产品收入合计-主营", f"=SUM({A}!C6:C9)-{A}!C5", NUM),     # r45
    ("2024 分产品收入合计-主营", f"=SUM({A}!D6:D9)-{A}!D5", NUM),     # r46
    ("2025 分产品收入合计-主营", f"=SUM({A}!E6:E9)-{A}!E5", NUM),     # r47
    ("2023 分产品毛利合计-主营毛利", f"=SUM({A}!C17:C20)-{A}!C16", NUM),  # r48
    ("2024 分产品毛利合计-主营毛利", f"=SUM({A}!D17:D20)-{A}!D16", NUM),  # r49
    ("2025 分产品毛利合计-主营毛利", f"=SUM({A}!E17:E20)-{A}!E16", NUM),  # r50
    ("2025 四足毛利交叉(收入×毛利率-毛利)", f"={A}!E6*{A}!E11-{A}!E17", NUM),  # r51
    ("2025 人形毛利交叉(收入×毛利率-毛利)", f"={A}!E7*{A}!E12-{A}!E18", NUM),  # r52
    ("CAGR与披露226.78%之差", f"=({A}!E4/{A}!C4)^(1/2)-1-2.2678", PCT),  # r53
    ("2026H1收入YoY与披露48.54%之差", f"={P}!F4/{P}!D4-1-0.4854", PCT),  # r54
]
r = 45
for name, f, fmt in chk:
    label(ws, r, 1, name)
    put(ws, r, 2, f, "f", fmt)
    r += 1
# r=55; 图表数据区 标题 r56, header r57, data r58-69
ws.cell(row=56, column=1, value="图表数据区（供“趋势图表”引用）").font = SEC_F
ws.cell(row=56, column=1).fill = SEC_FILL
ws.merge_cells(start_row=56, start_column=1, end_row=56, end_column=4)
CH_HDR = 57
CH0 = 58
for i, h in enumerate(["项目", "2023", "2024", "2025"]):
    ws.cell(row=CH_HDR, column=i + 1, value=h)
style_header(ws, CH_HDR, 4)
chart_rows = [
    ("营业收入(亿元)", f"={A}!C4/10000", f"={A}!D4/10000", f"={A}!E4/10000", NUM),          # 58
    ("营业收入YoY", None, f"={A}!D4/{A}!C4-1", f"={A}!E4/{A}!D4-1", PCT),                   # 59
    ("归母净利润(亿元)", f"={A}!C21/10000", f"={A}!D21/10000", f"={A}!E21/10000", NUM),     # 60
    ("扣非归母净利润(亿元)", f"={A}!C22/10000", f"={A}!D22/10000", f"={A}!E22/10000", NUM), # 61
    ("主营业务毛利率", f"={A}!C10", f"={A}!D10", f"={A}!E10", PCT),                          # 62
    ("四足机器人毛利率", f"={A}!C11", f"={A}!D11", f"={A}!E11", PCT),                        # 63
    ("人形机器人毛利率", f"={A}!C12", f"={A}!D12", f"={A}!E12", PCT),                        # 64
    ("人形机器人收入(亿元)", f"={A}!C7/10000", f"={A}!D7/10000", f"={A}!E7/10000", NUM),     # 65
    ("四足机器人收入(亿元)", f"={A}!C6/10000", f"={A}!D6/10000", f"={A}!E6/10000", NUM),     # 66
    ("组件及其他收入(亿元)", f"=({A}!C8+{A}!C9)/10000", f"=({A}!D8+{A}!D9)/10000", f"=({A}!E8+{A}!E9)/10000", NUM),  # 67
    ("四足销量(台)", f"={A}!C35", f"={A}!D35", f"={A}!E35", INT),                            # 68
    ("人形销量(台)", f"={A}!C37", f"={A}!D37", f"={A}!E37", INT),                            # 69
]
r = CH0
for name, a, b, c, fmt in chart_rows:
    label(ws, r, 1, name)
    for cc, v in ((2, a), (3, b), (4, c)):
        if v is None:
            ws.cell(row=r, column=cc).border = BORDER
        else:
            put(ws, r, cc, v, "x", fmt)
    r += 1
for col, w in zip("ABCDE", [32, 14, 14, 14, 42]):
    ws.column_dimensions[col].width = w

# ================= Sheet 5 趋势图表 =================
ws = wb.create_sheet("趋势图表")
ws["A1"] = "趋势图表（引用“核心计算”图表数据区，随数据自动更新）"
ws["A1"].font = TITLE_F
src = wb["核心计算"]
cats = Reference(src, min_col=2, max_col=4, min_row=CH_HDR)

bar = BarChart(); bar.type = "col"; bar.title = "营业收入(亿元)与同比增速"
bar.y_axis.title = "亿元"
bar.add_data(Reference(src, min_col=2, max_col=4, min_row=CH0), titles_from_data=True)
bar.set_categories(cats)
line = LineChart()
line.add_data(Reference(src, min_col=3, max_col=4, min_row=CH0 + 1), titles_from_data=True)
line.y_axis.axId = 200
line.y_axis.title = "YoY"
line.y_axis.number_format = '0%'
bar += line
bar.height = 9; bar.width = 18
ws.add_chart(bar, "A3")

b2 = BarChart(); b2.type = "col"; b2.title = "归母净利润 vs 扣非归母净利润(亿元)"
b2.add_data(Reference(src, min_col=2, max_col=4, min_row=CH0 + 2, max_row=CH0 + 3), titles_from_data=True)
b2.set_categories(cats)
b2.height = 9; b2.width = 18
ws.add_chart(b2, "A20")

l3 = LineChart(); l3.title = "毛利率趋势(主营/四足/人形)"
l3.y_axis.number_format = '0%'
l3.add_data(Reference(src, min_col=2, max_col=4, min_row=CH0 + 4, max_row=CH0 + 6), titles_from_data=True)
l3.set_categories(cats)
l3.height = 9; l3.width = 18
ws.add_chart(l3, "A37")

b4 = BarChart(); b4.type = "col"; b4.grouping = "stacked"; b4.title = "主营业务收入结构(亿元)"
b4.add_data(Reference(src, min_col=2, max_col=4, min_row=CH0 + 7, max_row=CH0 + 9), titles_from_data=True)
b4.set_categories(cats)
b4.height = 9; b4.width = 18
ws.add_chart(b4, "A54")

b5 = BarChart(); b5.type = "col"; b5.title = "机器人销量(台)"
b5.add_data(Reference(src, min_col=2, max_col=4, min_row=CH0 + 10, max_row=CH0 + 11), titles_from_data=True)
b5.set_categories(cats)
b5.height = 9; b5.width = 18
ws.add_chart(b5, "A71")

# ================= Sheet 6 分析结论 =================
ws = wb.create_sheet("分析结论")
ws.sheet_view.showGridLines = False
ws["A1"] = "分析结论（基于上交所披露文件，资料截止2026-08-30）"
ws["A1"].font = TITLE_F
concl = [
    ("一、成长性", "2023-2025年营业收入由15,913.44万元增至169,926.93万元，CAGR 226.78%（公式校验与披露一致）；扣非归母净利润由-1,801.91万元增至59,075.28万元，2024年起扭亏并快速放大。2026H1实现营业收入115,224.56万元（+48.54%，未审计），增速较报告期年度复合水平明显放缓，与招股书风险提示一致。"),
    ("二、收入结构", "人形机器人2025年收入86,783.19万元、占主营51.78%，首次超过四足机器人（41.62%）成为第一收入来源；2025年人形销量5,215台、出货5,511台（披露为全球第一），四足销量23,037台。产品结构切换是毛利率与估值叙事的核心驱动。"),
    ("三、盈利能力", "主营业务毛利率44.22%→56.74%→60.13%，2025年综合毛利率60.44%高于同行业可比公司均值44.44%。其中人形毛利率87.67%→69.26%→63.18%逐年回落（G1占比提升叠加主动降价），四足毛利率43.71%→56.72%持续改善。2025年归母净利率仅约16.4%，主因股份支付34,906.55万元计入管理费用；扣非净利率34.8%更能反映经营层面盈利。"),
    ("四、费用与投入", "研发费用4,995.18→7,001.70→14,496.56万元，费用率31.39%→8.53%（规模效应）；2026H1研发13,590.65万元、同比增加8,203.74万元，叠加春晚等品牌推广使销售费用大增，导致2026H1扣非净利同比-19.34%、2026Q1扣非-52.55%——高投入期利润承压是现阶段主要特征。"),
    ("五、现金流与资产负债表", "2025年经营现金流净额66,998.18万元，约为扣非净利的1.13倍，盈利现金含量高；2026H1为23,154.53万元（-32.53%），系备货与费用付现增加。2026-06-30总资产384,546.94万元、归母权益287,998.48万元、合并资产负债率约25.1%，货币资金约14.92亿元，叠加募资净额591,714.92万元，资金储备充裕。"),
    ("六、估值与发行", "发行价150.80元/股，对应发行后市值约609.93亿元；发行市盈率219.23倍（扣非孰低口径）、P/S(2025)约35.9倍，估值锚定高成长预期，显著高于C34行业平均静态市盈率38.56倍所隐含水平。战略配售引入社保基金、深度求索、腾讯关联方等，锁定期12-36个月。"),
    ("七、治理与风险", "特别表决权安排下王兴兴发行后表决权≤65.3090%；美国市场收入占比13.30%-19.54%，FCC 2026-07-28新规对新型号认证构成潜在限制；人形毛利率下行、行业竞争加剧（含特斯拉Optimus等）、股份支付后续授予将再增费用，均为招股书列示的核心风险。"),
    ("八、预测对照", "招股书预计2026H1营收105,200-112,800万元，实际（未审计）115,224.56万元，高于预计上限；扣非实际24,393.03万元，落于预计区间23,600-28,300万元内。预测数据在本底稿中均以黄底单独列示，未与已发生数据混同。"),
]
r = 3
for t, body in concl:
    ws.cell(row=r, column=1, value=t).font = Font(name=FONT, size=11, bold=True)
    ws.cell(row=r + 1, column=1, value=body).font = Font(name=FONT, size=10)
    ws.cell(row=r + 1, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r + 1, start_column=1, end_row=r + 1, end_column=10)
    ws.row_dimensions[r + 1].height = 80
    r += 3
ws.column_dimensions["A"].width = 115

os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print("saved:", OUT)
