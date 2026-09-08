# -*- coding: utf-8 -*-
"""
宇树科技(688836) 经营与财务表现分析底稿生成脚本
资料截止日: 2026-08-30
数据来源: 上交所披露(招股说明书注册稿/上市保荐书/落实函回复/招股意向书/上市公告书)、公司公开资料、券商研报转引
口径: 金额除特别注明外均为人民币万元; 比率为百分数(存储为小数); 已实现=A, 预测=E(单独标识)
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter

OUT = "/Users/guoqingtao/Desktop/AI办公评测/豆包办公/宇树科技经营财务分析底稿_截至20260830.xlsx"

# ---------- 样式常量(商务蓝) ----------
FONT_CN = "微软雅黑"
C_HEAD, C_SEC, C_LIGHT = "0F3B5D", "3288B9", "CFE3F1"
C_WARN = "FFF2CC"
thin = Side(style="thin", color="B8C7D9")
bd_top = Border(top=thin)
bd_final = Border(top=thin, bottom=Side(style="double", color="0F3B5D"))

f_title = Font(name=FONT_CN, size=13, bold=True, color="FFFFFF")
f_sec   = Font(name=FONT_CN, size=10, bold=True, color="FFFFFF")
f_light = Font(name=FONT_CN, size=10, bold=True, color="0F3B5D")
f_bold  = Font(name=FONT_CN, size=10, bold=True, color="000000")
f_norm  = Font(name=FONT_CN, size=10, color="000000")
f_green = Font(name=FONT_CN, size=10, color="008000")          # 跨表引用
f_aux   = Font(name=FONT_CN, size=9, italic=True, color="808080")
f_warn  = Font(name=FONT_CN, size=10, color="9C6500")
fill_head  = PatternFill("solid", fgColor=C_HEAD)
fill_sec   = PatternFill("solid", fgColor=C_SEC)
fill_light = PatternFill("solid", fgColor=C_LIGHT)
fill_warn  = PatternFill("solid", fgColor=C_WARN)
al_l = Alignment(horizontal="left", vertical="center", wrap_text=True)
al_c = Alignment(horizontal="center", vertical="center", wrap_text=True)
al_r = Alignment(horizontal="right", vertical="center")

NUM2 = '#,##0.00;(#,##0.00);"-"'
NUM0 = '#,##0;(#,##0);"-"'
PCT1 = '0.0%'
PCT2 = '0.00%'

def title_row(ws, row, c1, c2, text):
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    for c in range(c1, c2+1):
        cell = ws.cell(row=row, column=c); cell.fill = fill_head; cell.font = f_title
        cell.alignment = al_l
    ws.cell(row=row, column=c1).value = text
    ws.row_dimensions[row].height = 24

def sec_row(ws, row, c1, c2, text, fill=fill_sec, font=f_sec):
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    for c in range(c1, c2+1):
        cell = ws.cell(row=row, column=c); cell.fill = fill; cell.font = font
        cell.alignment = al_l
    ws.cell(row=row, column=c1).value = text

def put(ws, coord, val, font=f_norm, fmt=None, align=None, fill=None, border=None):
    c = ws[coord]; c.value = val; c.font = font
    if fmt: c.number_format = fmt
    if align: c.alignment = align
    if fill: c.fill = fill
    if border: c.border = border
    return c

wb = Workbook()

# =========================================================
# 00 封面与口径
# =========================================================
ws = wb.active; ws.title = "00_封面与口径"; ws.sheet_view.showGridLines = False
for col,w in {"A":2,"B":26,"C":70,"D":16}.items(): ws.column_dimensions[col].width = w
title_row(ws,1,2,4,"宇树科技股份有限公司(688836.SH) 经营与财务表现分析底稿")
put(ws,"B2","资料截止日",f_bold); put(ws,"C2","2026-08-30（该日之后发生的二级市场数据不纳入本底稿）")
put(ws,"B3","生成日期",f_bold); put(ws,"C3","2026-09-04")
put(ws,"B4","分析对象",f_bold); put(ws,"C4","宇树科技股份有限公司，高性能通用人形/四足机器人、机器人组件及具身智能模型研发、生产、销售；2026-08-19 上交所科创板上市")
rows = [
 ("一、工作簿结构",""),
 ("01_资料来源","引用文件清单、披露主体、日期、链接与对应数据范围（来源编号 S1~S10）"),
 ("02_原始数据_年度","2023A/2024A/2025A 经审计年度原始数据（注册稿口径），逐行标注来源编号"),
 ("03_原始数据_期间","2025 分季度/2026Q1/2026H1 实际数；2026H1 业绩预告（预测，单独标识）"),
 ("04_业务经营数据","分产品收入/销量/单价、分地区收入、应用场景、人员、出货地位"),
 ("05_核心计算","同比、CAGR、利润率、费用率、现金流质量等，全部以 Excel 公式跨表引用，可联动重算"),
 ("06_IPO与募投","发行方案、估值历程、原拟募投项目、产能规划（规划≠已实现）"),
 ("07_趋势图表","6 张原生 Excel 图表（数据源以公式链接原始表，可编辑、随数据更新）"),
 ("08_分析结论","分主题结论及对应数据支撑位置"),
 ("09_待人工核验","需人工以招股书原文/年报进一步核验的事项清单"),
 ("二、统一口径",""),
 ("货币与单位","除特别注明外，金额单位均为人民币【万元】；股数为【万股】；单价为【万元/台】；人数为【人】"),
 ("报告期口径","年度=自然年(2023/2024/2025，经审计)；Q1=一季度、H1=上半年、1-9M=前三季度；2023→2025 的 CAGR 按 2 年计算"),
 ("已实现 vs 预测","列标题后缀 A=Actual 已实现(经审计/经审阅/上市公告书披露)；E=Estimate 预测。2026H1 业绩预告区间为公司 2026-05 披露的【预测数】，已在 03 表单独列示，不得当作已实现事实；实际数取自 2026-08-17 上市公告书"),
 ("口径差异提示","招股书申报稿(2026-03-20) 与注册稿(2026-06-02) 对 2025 年数据有修订，本底稿一律采用注册稿/上市保荐书最终数；差异在备注列说明"),
 ("主营 vs 营业收入","主营业务收入不含其他业务；占比分产品/分地区结构均以主营业务收入为分母，营业收入口径占比另注"),
 ("颜色约定","黑色=本表数据；绿色=跨工作表公式引用；浅黄底=待人工核验/约数或反推数；灰色斜体=注释与来源"),
 ("三、重要声明","本底稿为分析工作稿，不构成投资建议；数据以上交所披露文件原文为准，转引数据已标注；预测不代表实际结果。"),
]
r = 6
for k,v in rows:
    if v=="":
        sec_row(ws,r,2,4,k,fill_light,f_light)
    else:
        put(ws,f"B{r}",k,f_bold,align=al_l); put(ws,f"C{r}",v,align=al_l)
        ws.row_dimensions[r].height = 30
    r+=1

# =========================================================
# 01 资料来源
# =========================================================
ws = wb.create_sheet("01_资料来源"); ws.sheet_view.showGridLines=False
widths={"A":2,"B":8,"C":34,"D":16,"E":12,"F":15,"G":62,"H":26}
for col,w in widths.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,8,"资料来源清单（优先级：上交所披露 > 公司官方 > 券商/媒体转引）")
heads=["编号","文件/资料名称","披露主体","类型","日期","链接 / 出处","用于数据"]
for i,h in enumerate(heads):
    put(ws,f"{get_column_letter(2+i)}3",h,f_sec,align=al_c,fill=fill_sec)
srcs=[
 ("S1","招股说明书（注册稿），项目编号 auditId=2178（申报稿2026-03-20/上会稿2026-05-25/注册稿2026-06-02）","上海证券交易所/发行人","一手·交易所","2026-06-02","https://star.sse.com.cn/listing/renewal/ipo/index_listing_detail.shtml?auditId=2178","年度三表、产品/地区/销量/费用/募投的最终口径"),
 ("S2","《上市保荐书》（注册稿）002178_20260602_VI1W.pdf","中信证券/上交所","一手·交易所","2026-06-02","http://static.sse.com.cn/stock/disclosure/announcement/c/202606/002178_20260602_VI1W.pdf","主要财务数据及指标表、研发费用、科创属性、劳务外包、市值标准"),
 ("S3","《审核中心意见落实函的回复》002178_20260525_V4H0.pdf","发行人/上交所","一手·交易所","2026-05-25","http://static.sse.com.cn/stock/disclosure/announcement/c/202605/002178_20260525_V4H0.pdf","综合毛利率、2026Q1 经审阅数据、同业对比"),
 ("S4","《招股意向书》全文","发行人（新浪财经公告库转引）","一手·转引","2026-07-31","https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?CompanyCode=82494861&gather=1&id=12470775","境外主营收入及占比、汇兑、审计截止日后财务信息"),
 ("S5","《首次公开发行股票科创板上市公告书》","发行人/上海证券报","一手·交易所","2026-08-17","http://paper.cnstock.com/html/2026-08/18/content_2255912.htm（提示性公告）；全文数据见新浪/澎湃转引","2026H1 实际业绩、资产负债、发行上市概况"),
 ("S6","《发行公告》《投资风险特别公告》《发行结果公告》","发行人/巨潮·上证报","一手·转引","2026-08-07","https://static.cninfo.com.cn/finalpage/2026-08-07/1225462415.PDF","发行价、发行数量、募资总额/净额、发行市盈率"),
 ("S7","浦银国际《宇树招股书解读：六大维度看全球机器人龙头商业落地》","浦银国际","二手·研报转引","2026-03-24","https://www.spdbi.com（研报PDF）","2022-2024 及 2025 1-9M 分产品/分地区/应用场景明细（申报稿口径）"),
 ("S8","兴业证券《全球通用机器人领军企业》研报","兴业证券","二手·研报转引","2026-08-11","慧博投研资讯 hibor.com.cn","2025 四足销量 23,037 台、收入 69,762.56 万元、单价（注册稿口径）"),
 ("S9","国信证券《人形机器人本体系列之宇树科技招股书梳理》","国信证券","二手·研报转引","2026-08-22","慧博投研资讯 hibor.com.cn","2025 产品结构（营业收入口径）交叉核对"),
 ("S10","东方财富/证券时报·数据中心 688836 财务指标","数据商","二手·数据聚合","2026-08-29起","https://data.eastmoney.com/stockdata/688836.html；https://stcn.com/quotes/index/sh688836.html","季度数据、2026H1 指标交叉核对"),
 ("S11","公司官方网站与官方公开资料","宇树科技","公司官方","持续","https://www.unitree.com；ir@unitree.com","产品线、技术与业务介绍（H1/G1/Go2/B2 等）"),
]
r=4
for row in srcs:
    for i,v in enumerate(row):
        cell=put(ws,f"{get_column_letter(2+i)}{r}",v,align=al_l)
        if i==0: cell.font=f_bold; cell.alignment=al_c
    ws.row_dimensions[r].height=42
    r+=1
put(ws,f"B{r+1}","注：S7~S10 为二手转引/数据聚合，仅用于交叉核对与补充明细；如与 S1~S5 一手披露不一致，以一手披露为准。",f_aux,align=al_l)

# =========================================================
# 02 原始数据_年度 (B科目 C=2023A D=2024A E=2025A F来源 G备注)
# =========================================================
ws = wb.create_sheet("02_原始数据_年度"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":34,"C":14,"D":14,"E":14,"F":9,"G":40}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,7,"年度原始数据（单位：万元；比率除外；注册稿最终口径）")
put(ws,"B2","（金额万元，比率为%；A=已实现并经审计）",f_aux,align=al_l)
for i,h in enumerate(["项目","2023A","2024A","2025A","来源","备注"]):
    put(ws,f"{get_column_letter(2+i)}3",h,f_sec,align=al_c,fill=fill_sec)

# (label, 2023, 2024, 2025, fmt, src, note, kind) kind: sec/num/pct/formula
ann = [
 ("一、经营规模", None,None,None,None,"","","sec"),
 ("营业收入", 15913.44, 39277.07, 169926.93, NUM2, "S2", "注册稿；申报稿曾为170,820.87，以注册稿为准","num"),
 ("主营业务收入", 15753.65, 38727.28, 167611.09, NUM2, "S1/S7", "2025=境内94,445.56+境外73,165.53","num"),
 ("其他业务收入", "=C5-C6","=D5-D6","=E5-E6", NUM2, "计算", "=营业收入-主营业务收入","formula"),
 ("二、盈利能力", None,None,None,None,"","","sec"),
 ("归母净利润", -1114.51, 9547.47, 27821.05, NUM2, "S2", "2023亏损，2024扭亏","num"),
 ("扣非后归母净利润", -1801.91, 7847.65, 59075.28, NUM2, "S2", "2025扣非高于归母，因非经常性项目为净损失(主要为股份支付)","num"),
 ("非经常性损益", "=C9-C10","=D9-D10","=E9-E10", NUM2, "计算", "=归母-扣非；2025为-31,254.23","formula"),
 ("主营业务毛利率", 0.4422, 0.5674, 0.6013, PCT1, "S2", "披露值","pct"),
 ("综合毛利率", 0.4475, 0.5722, 0.6044, PCT1, "S3", "披露值，与主营毛利率口径略异","pct"),
 ("扣非后加权平均ROE", -0.0592, 0.0860, 0.2870, PCT1, "S2", "披露值","pct"),
 ("基本每股收益(元/股)", None, None, 0.76, '0.00', "S2", "2023/2024股改前口径不可比，留空","num"),
 ("三、期间费用与外包", None,None,None,None,"","","sec"),
 ("研发费用", 4995.18, 7001.70, 14496.56, NUM2, "S2", "三年累计26,493.44万元","num"),
 ("销售费用", 3771.83, 5915.85, 14120.93, NUM2, "S1/媒体", "2025约1.41亿、按披露销售费用率8.31%反推=14,120.93，精确值待核","warn"),
 ("劳务外包费用", 1161.69, 1922.26, 6802.65, NUM2, "S2", "装配环节外包","num"),
 ("四、资产、权益与现金流（期末/当期）", None,None,None,None,"","","sec"),
 ("资产总额", 39127.15, 152786.94, 320853.83, NUM2, "S2", "期末数","num"),
 ("归母所有者权益", 29904.49, 128054.90, 260465.85, NUM2, "S2", "期末数","num"),
 ("资产负债率(合并)", 0.2357, 0.1619, 0.1882, PCT1, "S2", "披露值","pct"),
 ("经营活动现金流量净额", 494.25, 19239.13, 66998.18, NUM2, "S2", "当期数","num"),
 ("五、人员（期末，人）", None,None,None,None,"","","sec"),
 ("员工总数", None, None, 516, NUM0, "S2", "仅取得2025年末数","num"),
 ("研发人员", None, None, 184, NUM0, "S2", "占员工35.66%","num"),
 ("研发人员占比", None, None, "=E27/E26", PCT1, "计算", "=研发人员/员工总数","formula"),
]
r=4
rowmap={}
for item in ann:
    label=item[0]; rowmap[label]=r
    kind=item[7]
    if kind=="sec":
        sec_row(ws,r,2,7,label,fill_light,f_light)
    else:
        put(ws,f"B{r}",label,f_norm,align=al_l)
        for ci,col in zip(item[1:4],["C","D","E"]):
            cell=put(ws,f"{col}{r}",ci,align=al_r)
            cell.number_format=item[4]
            if kind=="formula": cell.font=f_norm
            if kind=="pct": cell.number_format=item[4]
            if kind=="warn": cell.fill=fill_warn; cell.font=f_warn
        put(ws,f"F{r}",item[5],f_aux,align=al_c); put(ws,f"G{r}",item[6],f_aux,align=al_l)
    r+=1
ws.freeze_panes="C4"
ANN="02_原始数据_年度"

# =========================================================
# 03 原始数据_期间
# =========================================================
ws=wb.create_sheet("03_原始数据_期间"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":30,"C":12,"D":12,"E":12,"F":12,"G":12,"H":12,"I":36}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,9,"期间数据：实际(A) 与 2026H1 业绩预告预测(E) 分列（万元）")
# block A actuals
sec_row(ws,3,2,9,"一、已实现数据（A：2025 年分期间为账面/披露数；2026Q1 经审阅；2026H1 取自上市公告书）",fill_light,f_light)
colsA=["2025Q1A","2025H1A","2025 1-9MA","2025FYA","2026Q1A","2026H1A"]
for i,h in enumerate(colsA): put(ws,f"{get_column_letter(3+i)}4",h,f_sec,align=al_c,fill=fill_sec)
put(ws,"B4","项目",f_sec,align=al_c,fill=fill_sec); put(ws,"I4","备注/来源",f_sec,align=al_c,fill=fill_sec)
per=[
 ("营业收入",25095.9,77571.4,116749.01,169926.93,42284.05,115224.56,NUM2,"S3/S5/S10；2025Q1、H1由同比与1-9M数反推(约)，1-9M及以后为披露精确值","warnrow"),
 ("归母净利润",9560.0,-3202.45,10530.0,27821.05,5001.38,27399.99,NUM2,"S5/S10；2025Q1约0.956亿、1-9M约1.053亿","warnrow"),
 ("扣非归母净利润",8483.65,30243.35,43061.23,59075.28,4025.36,24393.03,NUM2,"S3/S5/S10","num"),
 ("经营活动现金流量净额",None,34300.0,42800.0,66998.18,3439.96,23154.53,NUM2,"S5/S10；2025H1约3.43亿、1-9M约4.28亿(约数)","warnrow"),
 ("营业收入同比",None,None,None,3.3264,0.6849,0.4854,PCT1,"S2/S3/S5 披露值","pctrow"),
 ("扣非归母同比",None,None,None,None,-0.5255,-0.1934,PCT1,"S3/S5 披露值","pctrow"),
]
r=5
per_rowmap={}
for label,*vals in per:
    fmt=vals[6]; note=vals[7]; kind=vals[8]
    per_rowmap[label]=r
    put(ws,f"B{r}",label,align=al_l)
    for i,v in enumerate(vals[:6]):
        cell=put(ws,f"{get_column_letter(3+i)}{r}",v if v is not None else None,align=al_r)
        cell.number_format=fmt
        if kind in("warnrow",) and i in(0,1,3): cell.fill=fill_warn
        if kind=="pctrow": cell.number_format=PCT1
    put(ws,f"I{r}",note,f_aux,align=al_l)
    r+=1
put(ws,f"B{r}","审计/审阅状态",f_bold,align=al_l)
put(ws,f"I{r}","2025年度经审计；2026Q1经审阅；2026H1为上市公告书披露(未经审计)；浅黄=约数/反推，精确值以定期报告为准",f_aux,align=al_l)
r+=2

# block B forecast
fb=r
sec_row(ws,r,2,9,"二、2026 年上半年业绩预告（E=预测，公司 2026-05 上会稿披露；【非已实现事实】，仅作对照）",fill_warn,f_warn); r+=1
put(ws,f"B{r}","预测指标",f_sec,align=al_c,fill=fill_sec)
put(ws,f"C{r}","下限",f_sec,align=al_c,fill=fill_sec); put(ws,f"D{r}","上限",f_sec,align=al_c,fill=fill_sec)
put(ws,f"E{r}","同比下限",f_sec,align=al_c,fill=fill_sec); put(ws,f"F{r}","同比上限",f_sec,align=al_c,fill=fill_sec)
ws.merge_cells(start_row=r,start_column=7,end_row=r,end_column=9)
put(ws,f"G{r}","说明",f_sec,align=al_c,fill=fill_sec); r+=1
fc=[
 ("2026H1 营业收入(E)",105200,112800,0.3562,0.4541,NUM2,"预测区间10.52亿~11.28亿"),
 ("2026H1 归母净利润(E)",25800,30600,None,None,NUM2,"预测2.58亿~3.06亿，上年同期-3,202.45万(扭亏)"),
 ("2026H1 扣非归母(E)",23600,28300,-0.2197,-0.0643,NUM2,"预测2.36亿~2.83亿，同比-21.97%~-6.43%"),
]
fc_row={}
for label,lo,hi,y1,y2,fmt,note in fc:
    fc_row[label]=r
    put(ws,f"B{r}",label,align=al_l)
    for col,v in (("C",lo),("D",hi)):
        c=put(ws,f"{col}{r}",v,align=al_r,fill=fill_warn); c.number_format=fmt
    for col,v in (("E",y1),("F",y2)):
        c=put(ws,f"{col}{r}",v,align=al_r,fill=fill_warn); c.number_format=PCT1
    ws.merge_cells(start_row=r,start_column=7,end_row=r,end_column=9)
    put(ws,f"G{r}",note,f_aux,align=al_l)
    r+=1
r+=1
sec_row(ws,r,2,9,"三、预测 vs 实际对照（公式；实际取自上市公告书）",fill_light,f_light); r+=1
put(ws,f"B{r}","对照项",f_bold,align=al_l); put(ws,f"C{r}","实际值",f_bold,align=al_c); put(ws,f"D{r}","预测下限",f_bold,align=al_c); put(ws,f"E{r}","预测上限",f_bold,align=al_c); put(ws,f"F{r}","结论",f_bold,align=al_c)
ws.merge_cells(start_row=r,start_column=6,end_row=r,end_column=9); r+=1
cmp_start=r
put(ws,f"B{r}","2026H1 营业收入",align=al_l)
put(ws,f"C{r}",f"=H{per_rowmap['营业收入']}",f_green,align=al_r).number_format=NUM2
put(ws,f"D{r}",f"=C{fc_row['2026H1 营业收入(E)']}",align=al_r).number_format=NUM2
put(ws,f"E{r}",f"=D{fc_row['2026H1 营业收入(E)']}",align=al_r).number_format=NUM2
put(ws,f"F{r}",f'=IF(C{r}>E{r},"实际高于预测上限",IF(C{r}<D{r},"实际低于预测下限","落在预测区间内"))',align=al_c)
ws.merge_cells(start_row=r,start_column=6,end_row=r,end_column=9)
PER="03_原始数据_期间"

# =========================================================
# 04 业务经营数据
# =========================================================
ws=wb.create_sheet("04_业务经营数据"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":30,"C":13,"D":13,"E":13,"F":11,"G":42}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,7,"业务经营数据（主营口径，金额万元；销量台；单价万元/台）")
# A 分产品
sec_row(ws,3,2,7,"一、主营业务收入分产品（万元 / 占比）",fill_light,f_light)
for i,h in enumerate(["产品","2023A","2024A","2025A","来源","备注"]): put(ws,f"{get_column_letter(2+i)}4",h,f_sec,align=al_c,fill=fill_sec)
prod=[
 ("人形机器人收入",296.71,10689.76,86783.19,NUM2,"S1/S8","2025占主营51.78%，成第一大产品"),
 ("四足机器人收入",11938.09,23054.37,69762.56,NUM2,"S1/S8","2025注册稿69,762.56"),
 ("机器人组件收入",2692.34,4453.82,None,NUM2,"S7","2025与其他合并轧差，见下"),
 ("其他主营收入",826.51,529.33,None,NUM2,"S7",""),
 ("主营业务收入合计","=SUM(C5:C8)","=SUM(D5:D8)","=SUM(E5:E8)",NUM2,"计算","分产品合计，应与02表主营一致"),
 ("人形占比","=C5/C9","=D5/D9","=E5/E9",PCT1,"计算",""),
 ("四足占比","=C6/C9","=D6/D9","=E6/E9",PCT1,"计算",""),
 ("组件+其他占比","=(C7+C8)/C9","=(D7+D8)/D9","=(E9-E5-E6)/E9",PCT1,"计算","2025=轧差数11,065.34(约6.6%)，其中组件约1.04亿待核"),
]
r=5; prod_row={}
for label,a,b,c,fmt,src,note in prod:
    prod_row[label]=r
    put(ws,f"B{r}",label,align=al_l,font=f_bold if "合计" in label else f_norm)
    for col,v in zip(["C","D","E"],[a,b,c]):
        cell=put(ws,f"{col}{r}",v,align=al_r); cell.number_format=fmt
        if str(v).startswith("="): cell.font=f_norm
    put(ws,f"F{r}",src,f_aux,align=al_c); put(ws,f"G{r}",note,f_aux,align=al_l)
    if "合计" in label:
        for cc in "BCDE": ws[f"{cc}{r}"].border=bd_top
    r+=1
r+=1
# B 销量单价
sec_row(ws,r,2,7,"二、销量（台）与平均单价（万元/台，=收入/销量）",fill_light,f_light); r+=1
for i,h in enumerate(["指标","2023A","2024A","2025A","来源","备注"]): put(ws,f"{get_column_letter(2+i)}{r}",h,f_sec,align=al_c,fill=fill_sec)
r+=1
vol_h=r
vol=[
 ("人形机器人销量(台)",5,412,5215,NUM0,"S1/上证报","2024最终412台(申报稿曾为410)"),
 ("四足机器人销量(台)",3121,7136,23037,NUM0,"S7/S8","三年合计33,294台(超3.3万台)"),
 ("人形平均单价","=C5/C{}".format(vol_h),"=D5/D{}".format(vol_h),"=E5/E{}".format(vol_h),'0.00',"计算","披露59.34→26.04→16.64；2024按注册稿销量412台机械相除得25.95，与披露26.04差于版本修订，以披露为准"),
 ("四足平均单价","=C6/C{}".format(vol_h+1),"=D6/D{}".format(vol_h+1),"=E6/E{}".format(vol_h+1),'0.00',"计算","3.83→3.23→3.03"),
]
for label,a,b,c,fmt,src,note in vol:
    put(ws,f"B{r}",label,align=al_l)
    for col,v in zip(["C","D","E"],[a,b,c]):
        cell=put(ws,f"{col}{r}",v,align=al_r); cell.number_format=fmt
    put(ws,f"F{r}",src,f_aux,align=al_c); put(ws,f"G{r}",note,f_aux,align=al_l)
    r+=1
r+=1
# C 地区
sec_row(ws,r,2,7,"三、主营业务收入分地区（万元 / 占比）",fill_light,f_light); r+=1
for i,h in enumerate(["地区","2023A","2024A","2025A","来源","备注"]): put(ws,f"{get_column_letter(2+i)}{r}",h,f_sec,align=al_c,fill=fill_sec)
r+=1; reg_h=r
reg=[
 ("境内收入",6989.41,17116.54,94445.56,NUM2,"S4/S1","2024=主营-境外轧差(申报稿17,156.55略有修订)"),
 ("境外收入",8764.24,21610.74,73165.53,NUM2,"S4","占比55.63%→55.74%→43.65%"),
 ("主营合计","=SUM(C{}:C{})".format(reg_h,reg_h+1),"=SUM(D{}:D{})".format(reg_h,reg_h+1),"=SUM(E{}:E{})".format(reg_h,reg_h+1),NUM2,"计算",""),
 ("境外占比","=C{}/C{}".format(reg_h+1,reg_h+2),"=D{}/D{}".format(reg_h+1,reg_h+2),"=E{}/E{}".format(reg_h+1,reg_h+2),PCT1,"计算",""),
]
for label,a,b,c,fmt,src,note in reg:
    put(ws,f"B{r}",label,align=al_l,font=f_bold if label=="主营合计" else f_norm)
    for col,v in zip(["C","D","E"],[a,b,c]):
        cell=put(ws,f"{col}{r}",v,align=al_r); cell.number_format=fmt
    put(ws,f"F{r}",src,f_aux,align=al_c); put(ws,f"G{r}",note,f_aux,align=al_l)
    r+=1
r+=1
# D 应用场景 2025 1-9M
sec_row(ws,r,2,7,"四、下游应用场景结构（2025年1-9月，占该产品收入比，申报稿口径）",fill_light,f_light); r+=1
for i,h in enumerate(["产品/场景","科研教育","商业消费","行业应用","来源","备注"]): put(ws,f"{get_column_letter(2+i)}{r}",h,f_sec,align=al_c,fill=fill_sec)
r+=1
app=[("人形机器人",0.7360,0.1739,0.0901,"S7","人形仍高度依赖科研教育(73.6%)"),
     ("四足机器人",0.3158,0.4230,0.2612,"S7","场景相对均衡")]
for label,a,b,c,src,note in app:
    put(ws,f"B{r}",label,align=al_l)
    for col,v in zip(["C","D","E"],[a,b,c]):
        put(ws,f"{col}{r}",v,align=al_r).number_format=PCT1
    put(ws,f"F{r}",src,f_aux,align=al_c); put(ws,f"G{r}",note,f_aux,align=al_l); r+=1
r+=1
sec_row(ws,r,2,7,"五、出货地位与人员",fill_light,f_light); r+=1
facts=[("2025年人形机器人出货","超5,500台（纯人形，不含轮式双臂），公司称出货量全球第一；确认收入口径销量5,215台（S1/S2）"),
       ("四足机器人","报告期(2023-2025)销量合计超3.3万台，全球份额领先（S2）"),
       ("员工","2025年末516人，其中研发184人、占35.66%（S2）"),
       ("产能现状","2025年前三季度人形产销率超95%，基本满产满销（S7）")]
for k,v in facts:
    put(ws,f"B{r}",k,f_bold,align=al_l); ws.merge_cells(start_row=r,start_column=3,end_row=r,end_column=7)
    put(ws,f"C{r}",v,align=al_l); ws.row_dimensions[r].height=28; r+=1
BIZ="04_业务经营数据"

# =========================================================
# 05 核心计算 (formula driven)
# =========================================================
ws=wb.create_sheet("05_核心计算"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":36,"C":13,"D":13,"E":13,"F":13,"G":44}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,7,"核心计算（全部为 Excel 公式，绿色=跨表引用；修改原始数据后自动重算）")
for i,h in enumerate(["指标","2023A","2024A","2025A","2026H1A","口径/公式说明"]): put(ws,f"{get_column_letter(2+i)}3",h,f_sec,align=al_c,fill=fill_sec)
def ar(label): return rowmap[label]
F="02_原始数据_年度"
calc=[
 ("营业收入同比增速",None,
   f"='{F}'!D{ar('营业收入')}/'{F}'!C{ar('营业收入')}-1",
   f"='{F}'!E{ar('营业收入')}/'{F}'!D{ar('营业收入')}-1",
   f"='{PER}'!H{per_rowmap['营业收入']}/'{PER}'!D{per_rowmap['营业收入']}-1",
   PCT1,"本期/上年同期-1；2026H1对比2025H1"),
 ("营业收入2年CAGR(23→25)",None,
   None,
   f"=('{F}'!E{ar('营业收入')}/'{F}'!C{ar('营业收入')})^(1/2)-1",None,
   PCT1,"(末值/起值)^(1/年数)-1，披露值226.78%"),
 ("归母净利润同比",None,
   f"='{F}'!D{ar('归母净利润')}/ABS('{F}'!C{ar('归母净利润')})*SIGN('{F}'!D{ar('归母净利润')})",
   f"='{F}'!E{ar('归母净利润')}/'{F}'!D{ar('归母净利润')}-1",
   f"='{PER}'!H{per_rowmap['归母净利润']}/'{PER}'!D{per_rowmap['归母净利润']}-1",
   PCT1,"2023为负，2024同比按扭亏口径展示"),
 ("扣非归母同比",None,None,
   f"='{F}'!E{ar('扣非后归母净利润')}/'{F}'!D{ar('扣非后归母净利润')}-1",
   f"='{PER}'!H{per_rowmap['扣非归母净利润']}/'{PER}'!D{per_rowmap['扣非归母净利润']}-1",
   PCT1,"2026H1扣非同比-19.34%"),
 ("销售净利率(归母/营收)",
   f"='{F}'!C{ar('归母净利润')}/'{F}'!C{ar('营业收入')}",
   f"='{F}'!D{ar('归母净利润')}/'{F}'!D{ar('营业收入')}",
   f"='{F}'!E{ar('归母净利润')}/'{F}'!E{ar('营业收入')}",
   f"='{PER}'!H{per_rowmap['归母净利润']}/'{PER}'!H{per_rowmap['营业收入']}",
   PCT1,"归母净利润/营业收入"),
 ("扣非净利率(扣非/营收)",
   f"='{F}'!C{ar('扣非后归母净利润')}/'{F}'!C{ar('营业收入')}",
   f"='{F}'!D{ar('扣非后归母净利润')}/'{F}'!D{ar('营业收入')}",
   f"='{F}'!E{ar('扣非后归母净利润')}/'{F}'!E{ar('营业收入')}",
   f"='{PER}'!H{per_rowmap['扣非归母净利润']}/'{PER}'!H{per_rowmap['营业收入']}",
   PCT1,"扣非归母/营业收入，2025达34.8%"),
 ("研发费用率",
   f"='{F}'!C{ar('研发费用')}/'{F}'!C{ar('营业收入')}",
   f"='{F}'!D{ar('研发费用')}/'{F}'!D{ar('营业收入')}",
   f"='{F}'!E{ar('研发费用')}/'{F}'!E{ar('营业收入')}",None,
   PCT1,"研发费用/营业收入，核对披露31.39/17.83/8.53%"),
 ("销售费用率",
   f"='{F}'!C{ar('销售费用')}/'{F}'!C{ar('营业收入')}",
   f"='{F}'!D{ar('销售费用')}/'{F}'!D{ar('营业收入')}",
   f"='{F}'!E{ar('销售费用')}/'{F}'!E{ar('营业收入')}",None,
   PCT1,"销售费用/营业收入；2025销售费用为约数(浅黄)"),
 ("研发+销售费用合计",
   f"='{F}'!C{ar('研发费用')}+'{F}'!C{ar('销售费用')}",
   f"='{F}'!D{ar('研发费用')}+'{F}'!D{ar('销售费用')}",
   f"='{F}'!E{ar('研发费用')}+'{F}'!E{ar('销售费用')}",None,
   NUM2,"万元"),
 ("非经常性损益(归母-扣非)",
   f"='{F}'!C{ar('非经常性损益')}",f"='{F}'!D{ar('非经常性损益')}",f"='{F}'!E{ar('非经常性损益')}",None,
   NUM2,"2025为-3.13亿，主要系股份支付费用"),
 ("经营现金流/营收(CFO含金量)",
   f"='{F}'!C{ar('经营活动现金流量净额')}/'{F}'!C{ar('营业收入')}",
   f"='{F}'!D{ar('经营活动现金流量净额')}/'{F}'!D{ar('营业收入')}",
   f"='{F}'!E{ar('经营活动现金流量净额')}/'{F}'!E{ar('营业收入')}",
   f"='{PER}'!H{per_rowmap['经营活动现金流量净额']}/'{PER}'!H{per_rowmap['营业收入']}",
   PCT1,"CFO/营业收入"),
 ("经营现金流/归母净利润",
   f"=IF('{F}'!C{ar('归母净利润')}=0,\"\",'{F}'!C{ar('经营活动现金流量净额')}/'{F}'!C{ar('归母净利润')})",
   f"='{F}'!D{ar('经营活动现金流量净额')}/'{F}'!D{ar('归母净利润')}",
   f"='{F}'!E{ar('经营活动现金流量净额')}/'{F}'!E{ar('归母净利润')}",
   f"='{PER}'!H{per_rowmap['经营活动现金流量净额']}/'{PER}'!H{per_rowmap['归母净利润']}",
   '0.00',"盈利现金保障倍数"),
 ("资产总额同比",None,
   f"='{F}'!D{ar('资产总额')}/'{F}'!C{ar('资产总额')}-1",
   f"='{F}'!E{ar('资产总额')}/'{F}'!D{ar('资产总额')}-1",None,PCT1,"期末口径"),
 ("2025人均营业收入(万元/人)",None,None,
   f"='{F}'!E{ar('营业收入')}/'{F}'!E{ar('员工总数')}",None,NUM2,"仅2025有年末员工数"),
 ("2026H1营收/2025全年",None,None,None,
   f"='{PER}'!H{per_rowmap['营业收入']}/'{F}'!E{ar('营业收入')}",PCT1,"半年完成去年全年比重"),
]
r=4
for label,a,b,c,d,fmt,note in calc:
    put(ws,f"B{r}",label,align=al_l)
    for col,v in zip(["C","D","E","F"],[a,b,c,d]):
        cell=put(ws,f"{col}{r}",v if v is not None else None,align=al_r)
        cell.number_format=fmt
        if isinstance(v,str) and v.startswith("=") and "!" in v: cell.font=f_green
    put(ws,f"G{r}",note,f_aux,align=al_l); r+=1
# 单季测算
r+=1
sec_row(ws,r,2,7,"单季度拆分（由期间累计数相减得到，万元）",fill_light,f_light); r+=1
put(ws,f"B{r}","单季",f_bold,align=al_c)
for i,q in enumerate(["2025Q2","2025Q3","2025Q4","2026Q2"]): put(ws,f"{get_column_letter(3+i)}{r}",q,f_bold,align=al_c)
put(ws,f"G{r}","说明",f_bold,align=al_c); r+=1
P=PER
q_rows=[
 ("单季营业收入",
  f"='{P}'!D{per_rowmap['营业收入']}-'{P}'!C{per_rowmap['营业收入']}",
  f"='{P}'!E{per_rowmap['营业收入']}-'{P}'!D{per_rowmap['营业收入']}",
  f"='{P}'!F{per_rowmap['营业收入']}-'{P}'!E{per_rowmap['营业收入']}",
  f"='{P}'!H{per_rowmap['营业收入']}-'{P}'!G{per_rowmap['营业收入']}",NUM2,"累计值相减"),
 ("单季归母净利润",
  f"='{P}'!D{per_rowmap['归母净利润']}-'{P}'!C{per_rowmap['归母净利润']}",
  f"='{P}'!E{per_rowmap['归母净利润']}-'{P}'!D{per_rowmap['归母净利润']}",
  f"='{P}'!F{per_rowmap['归母净利润']}-'{P}'!E{per_rowmap['归母净利润']}",
  f"='{P}'!H{per_rowmap['归母净利润']}-'{P}'!G{per_rowmap['归母净利润']}",NUM2,"2025Q2亏损主因股份支付"),
 ("单季扣非归母",
  f"='{P}'!D{per_rowmap['扣非归母净利润']}-'{P}'!C{per_rowmap['扣非归母净利润']}",
  f"='{P}'!E{per_rowmap['扣非归母净利润']}-'{P}'!D{per_rowmap['扣非归母净利润']}",
  f"='{P}'!F{per_rowmap['扣非归母净利润']}-'{P}'!E{per_rowmap['扣非归母净利润']}",
  f"='{P}'!H{per_rowmap['扣非归母净利润']}-'{P}'!G{per_rowmap['扣非归母净利润']}",NUM2,""),
]
for label,a,b,c,d,fmt,note in q_rows:
    put(ws,f"B{r}",label,align=al_l)
    for col,v in zip(["C","D","E","F"],[a,b,c,d]):
        put(ws,f"{col}{r}",v,f_green,align=al_r).number_format=fmt
    put(ws,f"G{r}",note,f_aux,align=al_l); r+=1
CALC="05_核心计算"

# =========================================================
# 06 IPO与募投
# =========================================================
ws=wb.create_sheet("06_IPO与募投"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":34,"C":20,"D":14,"E":48}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,5,"IPO 发行方案、估值历程与募投项目")
sec_row(ws,3,2,5,"一、发行上市方案",fill_light,f_light)
ipo=[("股票简称/代码","宇树科技 / 688836.SH","S5/S6","科创板，扩位简称同"),
 ("上市日期","2026-08-19","S5",""),
 ("发行价格(元/股)",150.80,"S6",""),
 ("本次公开发行数量(万股)",4044.6434,"S6","占发行后总股本10.00%"),
 ("发行后总股本(万股)",40446.4340,"S5",""),
 ("发行募资总额(亿元)",60.99,"S6","按150.80元×4,044.6434万股"),
 ("发行募资净额(亿元)",59.17,"S6","扣除发行费用"),
 ("发行时市值(亿元)",609.93,"S5/S6","发行价×发行后总股本"),
 ("发行市盈率(倍)",219.23,"媒体(待核)","按2025归母口径，数据见媒体，需以发行公告原文核验"),
 ("上市标准","预计市值≥100亿元(科创板规则2.1.4条第一款)","S2","具有表决权差异安排"),
 ("实际控制人","王兴兴，发行后持股21.44%；上市前直接持股23.82%、合计控制68.78%表决权","S5/S7","同股不同权"),
]
r=4
for k,v,src,note in ipo:
    put(ws,f"B{r}",k,f_bold,align=al_l)
    c=put(ws,f"C{r}",v,align=al_l); ws.merge_cells(start_row=r,start_column=3,end_row=r,end_column=3)
    if "待核" in src: c.fill=fill_warn
    put(ws,f"D{r}",src,f_aux,align=al_c); put(ws,f"E{r}",note,f_aux,align=al_l); r+=1
r+=1
sec_row(ws,r,2,5,"二、估值历程（亿元）",fill_light,f_light); r+=1
for i,h in enumerate(["时点","投前估值","投后/发行市值","说明"]): put(ws,f"{get_column_letter(2+i)}{r}",h,f_sec,align=al_c,fill=fill_sec)
r+=1
val=[("2025-06 Pre-IPO轮",120.00,127.00,"最近一次市场化股权融资(S2)"),
     ("2026-08 IPO发行",None,609.93,"发行价对应市值(S6)")]
for a,b,c,d in val:
    put(ws,f"B{r}",a,align=al_l); put(ws,f"C{r}",b,align=al_r).number_format='0.00'
    put(ws,f"D{r}",c,align=al_r).number_format='0.00'; put(ws,f"E{r}",d,f_aux,align=al_l); r+=1
r+=1
sec_row(ws,r,2,5,"三、原拟募投项目（招股书披露，万元；实际募资60.99亿元为超募）",fill_light,f_light); r+=1
for i,h in enumerate(["项目","拟投入(万元)","占比","性质"]): put(ws,f"{get_column_letter(2+i)}{r}",h,f_sec,align=al_c,fill=fill_sec)
r+=1; mp_h=r
mps=[("智能机器人模型研发项目",202200,"研发","具身大模型(大脑/小脑)"),
     ("机器人本体研发项目",111000,"研发","本体与结构"),
     ("新型智能机器人产品开发项目",44500,"研发","新产品开发"),
     ("智能机器人制造基地建设项目",62400,"产能","达产规划年产能：人形7.5万台、四足11.5万台（规划，非已实现）")]
for a,b,c,d in mps:
    put(ws,f"B{r}",a,align=al_l); put(ws,f"C{r}",b,align=al_r).number_format=NUM0
    put(ws,f"D{r}",f"=C{r}/C{mp_h+4}",align=al_r).number_format=PCT1
    put(ws,f"E{r}",d,f_aux,align=al_l); r+=1
put(ws,f"B{r}","合计",f_bold,align=al_l)
put(ws,f"C{r}",f"=SUM(C{mp_h}:C{mp_h+3})",f_bold,align=al_r).number_format=NUM0
put(ws,f"D{r}",f"=C{r}/C{r}",f_bold,align=al_r).number_format=PCT1
put(ws,f"E{r}","原拟募资420,171.12万元(约42.02亿)；表内为约数，精确分项目金额以招股书为准(待核)",f_aux,align=al_l)
for cc in "BCD": ws[f"{cc}{r}"].border=bd_final
IPO="06_IPO与募投"

# =========================================================
# 07 趋势图表 (原生图表; 辅助数据区以公式链接原始表)
# =========================================================
ws=wb.create_sheet("07_趋势图表"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":16,"C":13,"D":13,"E":13,"F":13,"G":3}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,6,"趋势图表（原生 Excel 图表，数据源为下方公式链接区，可编辑、随原始数据更新）")

def block(ws,r,title,headers,rows,fmt=NUM2):
    sec_row(ws,r,2,2+len(headers)-1,title,fill_light,f_light); r+=1
    for i,h in enumerate(headers): put(ws,f"{get_column_letter(2+i)}{r}",h,f_bold,align=al_c,fill=fill_light)
    r+=1
    r0=r
    for row in rows:
        put(ws,f"B{r}",row[0],align=al_c)
        for i,v in enumerate(row[1:]):
            cell=put(ws,f"{get_column_letter(3+i)}{r}",v,f_green if isinstance(v,str) and v.startswith("=") else f_norm,align=al_r)
            cell.number_format=fmt
        r+=1
    return r0,r-1

# T1 年度 营收/扣非
t1_h=3
t1a,t1b=block(ws,t1_h,"图1数据源：年度营收与扣非归母（万元）",["年份","营业收入","扣非归母净利润"],[
 ["2023A",f"='{ANN}'!C{rowmap['营业收入']}",f"='{ANN}'!C{rowmap['扣非后归母净利润']}"],
 ["2024A",f"='{ANN}'!D{rowmap['营业收入']}",f"='{ANN}'!D{rowmap['扣非后归母净利润']}"],
 ["2025A",f"='{ANN}'!E{rowmap['营业收入']}",f"='{ANN}'!E{rowmap['扣非后归母净利润']}"]])
# T2 年度比率 (引用05核心计算行)
calc_row={lab:4+i for i,(lab,*_ ) in enumerate(calc)}
t2a,t2b=block(ws,t1b+2,"图2数据源：年度盈利能力与费用率（%）",["年份","主营毛利率","销售净利率","扣非净利率","研发费用率"],[
 ["2023A",f"='{ANN}'!C{rowmap['主营业务毛利率']}",f"='{CALC}'!C{calc_row['销售净利率(归母/营收)']}",f"='{CALC}'!C{calc_row['扣非净利率(扣非/营收)']}",f"='{CALC}'!C{calc_row['研发费用率']}"],
 ["2024A",f"='{ANN}'!D{rowmap['主营业务毛利率']}",f"='{CALC}'!D{calc_row['销售净利率(归母/营收)']}",f"='{CALC}'!D{calc_row['扣非净利率(扣非/营收)']}",f"='{CALC}'!D{calc_row['研发费用率']}"],
 ["2025A",f"='{ANN}'!E{rowmap['主营业务毛利率']}",f"='{CALC}'!E{calc_row['销售净利率(归母/营收)']}",f"='{CALC}'!E{calc_row['扣非净利率(扣非/营收)']}",f"='{CALC}'!E{calc_row['研发费用率']}"]],fmt=PCT1)
# T3 产品结构
t3a,t3b=block(ws,t2b+2,"图3数据源：分产品收入（万元）",["年份","人形机器人","四足机器人","组件及其他"],[
 ["2023A",f"='{BIZ}'!C{prod_row['人形机器人收入']}",f"='{BIZ}'!C{prod_row['四足机器人收入']}",f"='{BIZ}'!C{prod_row['人形机器人收入']}*0+'{BIZ}'!C{prod_row['机器人组件收入']}+'{BIZ}'!C{prod_row['其他主营收入']}"],
 ["2024A",f"='{BIZ}'!D{prod_row['人形机器人收入']}",f"='{BIZ}'!D{prod_row['四足机器人收入']}",f"='{BIZ}'!D{prod_row['机器人组件收入']}+'{BIZ}'!D{prod_row['其他主营收入']}"],
 ["2025A",f"='{BIZ}'!E{prod_row['人形机器人收入']}",f"='{BIZ}'!E{prod_row['四足机器人收入']}",f"='{BIZ}'!E{prod_row['组件+其他占比']}*'{BIZ}'!E{prod_row['主营业务收入合计']}"]])
# T4 地区
reg_rows={lab:reg_h+i for i,lab in enumerate(["境内收入","境外收入","主营合计","境外占比"])}
t4a,t4b=block(ws,t3b+2,"图4数据源：分地区收入（万元）",["年份","境内","境外"],[
 ["2023A",f"='{BIZ}'!C{reg_rows['境内收入']}",f"='{BIZ}'!C{reg_rows['境外收入']}"],
 ["2024A",f"='{BIZ}'!D{reg_rows['境内收入']}",f"='{BIZ}'!D{reg_rows['境外收入']}"],
 ["2025A",f"='{BIZ}'!E{reg_rows['境内收入']}",f"='{BIZ}'!E{reg_rows['境外收入']}"]])
# T5 单季营收
t5a,t5b=block(ws,t4b+2,"图5数据源：单季营业收入（万元，累计相减）",["季度","营业收入"],[
 ["2025Q1",f"='{PER}'!C{per_rowmap['营业收入']}"],
 ["2025Q2",f"='{PER}'!D{per_rowmap['营业收入']}-'{PER}'!C{per_rowmap['营业收入']}"],
 ["2025Q3",f"='{PER}'!E{per_rowmap['营业收入']}-'{PER}'!D{per_rowmap['营业收入']}"],
 ["2025Q4",f"='{PER}'!F{per_rowmap['营业收入']}-'{PER}'!E{per_rowmap['营业收入']}"],
 ["2026Q1",f"='{PER}'!G{per_rowmap['营业收入']}"],
 ["2026Q2",f"='{PER}'!H{per_rowmap['营业收入']}-'{PER}'!G{per_rowmap['营业收入']}"]])
# T6 人形量价
vp_h=vol_h
t6a,t6b=block(ws,t5b+2,"图6数据源：人形机器人销量(台)与单价(万元/台)",["年份","销量(台)","平均单价"],[
 ["2023A",f"='{BIZ}'!C{vp_h}",f"='{BIZ}'!C{vp_h+2}"],
 ["2024A",f"='{BIZ}'!D{vp_h}",f"='{BIZ}'!D{vp_h+2}"],
 ["2025A",f"='{BIZ}'!E{vp_h}",f"='{BIZ}'!E{vp_h+2}"]],fmt=NUM0)
# fix 单价格式
for rr in range(t6a,t6b+1): ws[f"E{rr}"].number_format='0.00'

def cats(r0,r1): return Reference(ws,min_col=2,min_row=r0,max_row=r1)
def dat(c0,c1,r0,r1): return Reference(ws,min_col=c0,max_col=c1,min_row=r0-1,max_row=r1)

# C1 柱线组合
c1=BarChart(); c1.type="col"; c1.title="图1 营业收入与扣非归母净利润（2023-2025，万元）"
c1.add_data(dat(3,3,t1a,t1b),titles_from_data=True); c1.set_categories(cats(t1a,t1b))
c1.y_axis.title="万元"; c1.x_axis.title="年度"; c1.height=7.2; c1.width=11.5
ln=LineChart(); ln.add_data(dat(4,4,t1a,t1b),titles_from_data=True); ln.y_axis.axId=200
ln.y_axis.crosses="max"; c1.y_axis.crosses="autoZero"; c1+=ln
c1.legend.position="b"
# C2 折线
c2=LineChart(); c2.title="图2 毛利率/净利率/研发费用率趋势（%）"
c2.add_data(dat(3,6,t2a,t2b),titles_from_data=True); c2.set_categories(cats(t2a,t2b))
c2.y_axis.title="%"; c2.x_axis.title="年度"; c2.height=7.2; c2.width=11.5; c2.legend.position="b"
for s in c2.series: s.smooth=False
# C3 堆叠柱
c3=BarChart(); c3.type="col"; c3.grouping="stacked"; c3.overlap=100
c3.title="图3 主营业务收入产品结构（万元，堆叠）"
c3.add_data(dat(3,5,t3a,t3b),titles_from_data=True); c3.set_categories(cats(t3a,t3b))
c3.y_axis.title="万元"; c3.x_axis.title="年度"; c3.height=7.2; c3.width=11.5; c3.legend.position="b"
# C4 堆叠柱地区
c4=BarChart(); c4.type="col"; c4.grouping="stacked"; c4.overlap=100
c4.title="图4 主营业务收入地区结构（万元，堆叠）"
c4.add_data(dat(3,4,t4a,t4b),titles_from_data=True); c4.set_categories(cats(t4a,t4b))
c4.y_axis.title="万元"; c4.x_axis.title="年度"; c4.height=7.2; c4.width=11.5; c4.legend.position="b"
# C5 单季柱
c5=BarChart(); c5.type="col"; c5.title="图5 单季营业收入（万元）"
c5.add_data(dat(3,3,t5a,t5b),titles_from_data=True); c5.set_categories(cats(t5a,t5b))
c5.y_axis.title="万元"; c5.x_axis.title="季度"; c5.height=7.2; c5.width=11.5; c5.legend=None
# C6 量价组合
c6=BarChart(); c6.type="col"; c6.title="图6 人形机器人销量(台)与平均单价(万元/台)"
c6.add_data(dat(3,3,t6a,t6b),titles_from_data=True); c6.set_categories(cats(t6a,t6b))
c6.y_axis.title="销量(台)"; c6.x_axis.title="年度"; c6.height=7.2; c6.width=11.5
ln6=LineChart(); ln6.add_data(dat(4,4,t6a,t6b),titles_from_data=True); ln6.y_axis.axId=210
ln6.y_axis.crosses="max"; c6.y_axis.crosses="autoZero"; c6+=ln6; c6.legend.position="b"
for ch,anc in [(c1,"H3"),(c2,"S3"),(c3,"H19"),(c4,"S19"),(c5,"H35"),(c6,"S35")]:
    ws.add_chart(ch,anc)

# =========================================================
# 08 分析结论
# =========================================================
ws=wb.create_sheet("08_分析结论"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":18,"C":78,"D":30}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,4,"经营与财务分析结论（结论后附数据支撑位置；截至2026-08-30）")
for i,h in enumerate(["主题","分析结论","数据支撑"]): put(ws,f"{get_column_letter(2+i)}3",h,f_sec,align=al_c,fill=fill_sec)
concl=[
 ("1 高增长但增速换挡","2023-2025营收1.59→3.93→16.99亿元，2年CAGR约226.8%；但增速逐期回落：2025全年+332.6%→2026Q1+68.5%→2026H1+48.5%，公司明确归因于基数抬高、行业热度缓和与竞争加剧，高增速阶段正在过去。","02表营业收入；05表CAGR/同比；03表期间同比"),
 ("2 盈利：扣非强、归母受股份支付扰动","2024扭亏，2025扣非归母5.91亿、扣非净利率约34.8%、主营毛利率60.1%（全栈自研、核心零部件自产支撑高毛利）；但2025归母仅2.78亿，差额-3.13亿为非经常性损失（主要是股权激励股份支付）。分析盈利质量应以扣非口径为主。","02表归母/扣非/非经常性损益/毛利率；05表扣非净利率"),
 ("3 2026利润端承压","2026H1营收11.52亿(+48.5%)、归母2.74亿(同比扭亏，因上年同期含3.49亿股份支付低基数)，但扣非2.44亿、同比-19.3%；2026Q1扣非-52.6%。主因研发费用(上半年同比+0.82亿)与销售费用(春晚品牌推广、销售扩编，H1销售费用1.64亿)快速扩张。","03表实际数；05表单季拆分；04表费用"),
 ("4 产品结构切换、量增价减","人形机器人收入由2023年296.71万(占1.88%)升至2025年8.68亿(占主营51.78%)，超过四足成为第一大产品；销量5→412→5,215台，单价59.34→26.04→16.64万元/台(G1下探至10万级)。四足仍是基本盘(6.98亿、23,037台、单价降至3.03万)。","04表分产品/销量/单价；07图3、图6"),
 ("5 地区：境内放量、境外占比回落","境外收入0.88→2.16→7.32亿元，占主营55.63%→55.74%→43.65%；2025境内9.44亿(56.35%)反超，主要系国内人形需求与春晚效应；海外仍为重要市场，需关注汇率与外销结算风险。","04表分地区；07图4"),
 ("6 现金流与资产负债表","经营现金流净额0.05→1.92→6.70亿元，2025 CFO/营收约39.4%、现金对利润覆盖充分；合并资产负债率仅18.82%、低杠杆。2026H1末总资产38.45亿(较年初+19.85%)、负债率回升至25.11%(合同负债、应付及租赁负债增加)，CFO 2.32亿同比-32.5%需跟踪。","02表资产/权益/负债/CFO；05表现金含量；03表2026H1"),
 ("7 研发：强度下降、绝对额上升","研发费用0.50→0.70→1.45亿元，费用率31.39%→17.83%→8.53%（规模摊薄而非缩减）；研发人员184人、占35.66%；IPO原拟募资42.02亿中约85%(35.77亿)投向模型/本体/新产品研发，战略向具身大模型倾斜。","02表研发；06表募投；05表研发费率"),
 ("8 主要风险","①人形机器人2025 1-9M约73.6%收入来自科研教育、行业应用仅约9%，规模化工业商业化尚早；②价格战与降价趋势压制单价/毛利；③股份支付等非经常项持续扰动表观利润；④2026费用扩张可能继续压制扣非利润；⑤发行市盈率高、估值波动大；⑥装配依赖劳务外包。","04表应用场景；06表发行方案；02表外包费用"),
 ("9 预测与实际严格区分","公司2026-05曾预测2026H1营收10.52-11.28亿、扣非2.36-2.83亿(预测E)；上市公告书披露实际营收11.52亿、扣非2.44亿——营收略超预测上限，扣非落在区间内。预测仅作参照，不应当作既成事实。","03表第二、三区块"),
]
r=4
for a,b,c in concl:
    put(ws,f"B{r}",a,f_bold,align=al_l); put(ws,f"C{r}",b,align=al_l); put(ws,f"D{r}",c,f_aux,align=al_l)
    ws.row_dimensions[r].height=78; r+=1

# =========================================================
# 09 待人工核验
# =========================================================
ws=wb.create_sheet("09_待人工核验"); ws.sheet_view.showGridLines=False
for col,w in {"A":2,"B":6,"C":40,"D":50,"E":22}.items(): ws.column_dimensions[col].width=w
title_row(ws,1,2,5,"仍需人工核验事项（底稿中以浅黄底标注者同属此类）")
for i,h in enumerate(["序号","待核验事项","原因 / 建议核对位置","当前底稿处理"]): put(ws,f"{get_column_letter(2+i)}3",h,f_sec,align=al_c,fill=fill_sec)
todo=[
 ("以S1招股说明书注册稿PDF原文复核全部年度数字","本底稿年度数主要取自S2上市保荐书摘要表，应与招股书『财务会计信息』章节逐字核对","已采用注册稿口径，差异处已备注"),
 ("2025年销售费用精确值","媒体称约1.41亿、按披露费率8.31%反推为14,120.93万","浅黄标注为约数"),
 ("2025年管理费用、财务费用及期间费用明细","仅取得管理费用约3.64亿(含股份支付)的媒体口径，未取得三年完整序列","未填列，避免编造"),
 ("2025年分产品中'机器人组件'与'其他主营'精确拆分","仅取得组件约1.04亿，精确值需查招股书收入附注","以轧差合并列示并备注"),
 ("2025Q1、2025H1部分数据为反推/约数","由后续累计数与同比反推(浅黄格)，需以2025半年报/三季报原文替换","已浅黄标注"),
 ("2026H1数据的审计状态与精确金额","取自上市公告书转引(营收115,224.56、归母27,399.99、扣非24,393.03、CFO23,154.53)，正式半年报披露后应替换核对","已标注未经审计"),
 ("发行市盈率219.23倍、初始流通比例7.44%","来自媒体，需以S6发行公告/发行结果公告原文核验","浅黄标注待核"),
 ("原拟募投四项目精确到万元的金额","本表按20.22/11.10/4.45/6.24亿元约数填列(合计约42.02亿)","已标注为约数"),
 ("应用场景结构为2025年1-9月(申报稿)口径","非全年口径，且后续注册稿可能修订","已明确标注期间与口径"),
 ("境外收入分国别/币种、汇兑损益、客户与供应商集中度","本次未取得完整明细","未纳入，建议补充"),
 ("二级市场股价/市值","属资料截止日(8-30)后波动数据，本底稿仅保留发行时市值609.93亿，不纳入后续行情","按截止日剔除"),
 ("研报转引数据(S7-S10)","均为二手，需回溯招股书对应表格原文","已标注来源级别"),
]
r=4
for i,(a,b,c) in enumerate(todo,1):
    put(ws,f"B{r}",i,align=al_c); put(ws,f"C{r}",a,align=al_l); put(ws,f"D{r}",b,f_aux,align=al_l); put(ws,f"E{r}",c,align=al_l)
    ws.row_dimensions[r].height=44; r+=1

# 全局：标签页顺序与活动表
wb.active=0
# 打开时强制全量重算，保证公式与图表在 Excel/WPS 打开即刷新
try:
    wb.calculation.fullCalcOnLoad = True
except Exception:
    pass
wb.save(OUT)
print("ALL SHEETS SAVED:", wb.sheetnames)
