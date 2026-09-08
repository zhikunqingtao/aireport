# -*- coding: utf-8 -*-
"""自检脚本：重新加载生成的xlsx，核对sheet、关键数字、公式、图表。"""
import sys
from openpyxl import load_workbook

PATH = "/Users/guoqingtao/Desktop/AI办公评测/zhikuncode/宇树科技_经营与财务分析底稿.xlsx"
wb = load_workbook(PATH)  # data_only=False，保留公式

ok, fail = [], []

def check(name, cond, detail=""):
    (ok if cond else fail).append(f"{'PASS' if cond else 'FAIL'} | {name} | {detail}")

# 1) sheet存在且顺序正确
expected = ["说明", "资料来源", "原始数据_财务", "原始数据_IPO与股东", "原始数据_经营",
            "核心计算", "趋势图表", "分析结论", "待核验事项"]
check("sheet数量=9", len(wb.sheetnames) == 9, str(wb.sheetnames))
check("sheet顺序正确", wb.sheetnames == expected)

fin = wb["原始数据_财务"]
ipo = wb["原始数据_IPO与股东"]
calc = wb["核心计算"]
cht = wb["趋势图表"]

# 2) 抽查10个关键数字
def approx(a, b, tol=1e-6):
    return isinstance(a, (int, float)) and abs(a - b) <= tol

key_checks = [
    ("营业收入2025=169,926.93", fin["E5"].value, 169926.93),
    ("归母净利润2025=27,821.05", fin["E6"].value, 27821.05),
    ("扣非归母2025=59,075.28", fin["E7"].value, 59075.28),
    ("营业收入2023=15,913.44", fin["C5"].value, 15913.44),
    ("营业收入2024=39,276.6(倒算)", fin["D5"].value, 39276.6),
    ("归母净利润2024=9,547.47", fin["D6"].value, 9547.47),
    ("主营毛利率2025=60.13%(0.6013)", fin["E8"].value, 0.6013),
    ("股份支付=34,906.55", fin["B21"].value, 34906.55),
    ("发行价=150.80元", ipo["B6"].value, 150.80),
    ("发行市盈率=219.23倍", ipo["B14"].value, 219.23),
    ("首日收盘市值=3,417.72亿", ipo["C53"].value, 3417.72),
    ("人形2023收入=296.71", fin["B29"].value, 296.71),
]
for name, got, want in key_checks:
    check(f"关键数字:{name}", approx(got, want), f"got={got!r}")

# 3) 核心计算含公式（跨表引用）
formula_cells = []
for row in calc.iter_rows():
    for c in row:
        if isinstance(c.value, str) and c.value.startswith("="):
            formula_cells.append(c.coordinate)
check("核心计算公式单元格数量>=35", len(formula_cells) >= 35, f"共{len(formula_cells)}个")
sample = ["B5", "D5", "B10", "B20", "B24", "B32", "B36", "B40", "B41", "B45", "D45", "B52", "B56", "D56"]
all_formula = all(isinstance(calc[s].value, str) and calc[s].value.startswith("=") for s in sample)
check("核心计算抽查14个计算单元格均为公式", all_formula,
      "; ".join(f"{s}={calc[s].value}" for s in sample[:4]))
cross = all("'原始数据_" in str(calc[s].value) for s in ["B5", "B20", "B32", "B45", "B52", "B56"])
check("公式为跨表引用原始数据sheet", cross)

# 4) 趋势图表：数据区公式 + 7个图表
cht_formulas = sum(1 for row in cht.iter_rows(max_row=51) for c in row
                   if isinstance(c.value, str) and c.value.startswith("="))
check("趋势图表数据区公式数量>=25", cht_formulas >= 25, f"共{cht_formulas}个")
n_charts = len(cht._charts)
check("原生图表数量=7", n_charts == 7, f"实际{n_charts}个")
titles = []
for ch in cht._charts:
    try:
        t = ch.title
        # 提取标题文本
        txt = ""
        for p in t.tx.rich.p:
            for r_ in (p.r or []):
                txt += r_.t or ""
        titles.append(txt)
    except Exception:
        titles.append("(无法解析)")
check("图表标题含口径说明(万元/二级市场)", any("万元" in t for t in titles) and any("二级市场" in t for t in titles),
      " | ".join(titles))

# 5) 其他sheet完整性
src = wb["资料来源"]
check("资料来源行数在25-30之间", 25 <= src.max_row - 2 <= 30, f"{src.max_row - 2}条")
check("资料来源首条为上交所688836公告列表",
      "sse.com.cn" in str(src["F3"].value) and "688836" in str(src["C3"].value),
      f"{src['C3'].value} | {src['F3'].value}")
check("资料来源首条含2026-08-30核验说明", "2026-08-30" in str(src["D3"].value) + str(src["E3"].value))
todo = wb["待核验事项"]
check("待核验事项>=12条", todo.max_row - 2 >= 12, f"{todo.max_row - 2}条")
concl = wb["分析结论"]
texts = [str(concl.cell(row=r, column=1).value) for r in range(1, concl.max_row + 1)]
check("分析结论含9节", all(any(f"{s}、" in t for t in texts) for s in "一二三四五六七八九"))
check("分析结论含局限说明", any("局限" in t for t in texts))

print("=" * 70)
for line in ok:
    print(line)
print("-" * 70)
for line in fail:
    print(line)
print("=" * 70)
print(f"总计: PASS={len(ok)} FAIL={len(fail)}")
sys.exit(1 if fail else 0)
