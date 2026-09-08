#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_unitree_interactive.py
对《宇树科技_交互式数据报告.html》做两项检查：
1) 数字比对：提取 HTML 中 const DATA = {...} 的全部数字（含字符串内数字），
   与底稿（unitree_excel_spec.md）数字白名单逐一比对，输出"底稿外数字"清单（目标为 0）。
   例外：年份/日期成分（0-31、2016-2031）、坐标刻度与 CSS 像素值（本检查只解析 DATA 块，
   天然不含 CSS/刻度；页面 JS/CSS 中的数字不参与比对）。
2) Playwright(chromium) 自检：加载页面 → console 错误计数 → 检测 window.echarts
   （jsdelivr 失败时页面自动回退 unpkg）→ 全页截图 + 4 个分段截图。
"""
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "宇树科技_交互式数据报告.html")
SCRATCH = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a"
SHOT_DIR = os.path.join(SCRATCH, "interactive_shots")

# ---------------------------------------------------------------- 数字白名单
# 日期成分（年月日）与小序号：0-31；年份：2016-2031（底稿中出现的全部年份）
DATE_PARTS = {str(i) for i in range(0, 32)}
YEARS = {str(y) for y in range(2016, 2032)}

# 底稿数字集合（unitree_excel_spec.md 中核验过的全部数字；含任务书明确给出的推算值）
SPEC_NUMBERS = {
    # 代码 / 文号
    "688836", "1612",
    # 数据块A：利润表
    "12300", "12100", "15913.44", "39276.6", "39237.06", "169926.93", "115200", "11.52",
    "2210.05", "1114.51", "9547.47", "9450.18", "27821.05", "27400", "2.74", "3202.45",
    "807", "1801.91", "7847.65", "7750", "59075.28", "24400", "2.44", "19.34",
    "44.18", "44.22", "56.74", "56.41", "60.13", "60.27", "56.01",
    "2998.48", "4995.18", "7001.7", "14500", "1.45", "107", "13600", "1.36", "8203.74", "11.8",
    "24.39", "31.39", "17.84", "8.53",
    "3019.73", "494.25", "19200", "1.92", "67000", "6.7", "248.24", "3439.96",
    "116700", "10500", "43100", "42800",
    "42284.05", "68.49", "4025.36", "52.55", "8483.65",
    "31254", "34906.55", "3.49",
    "29.95", "145.83", "335.31", "332.64", "226.8", "226.78", "34.8", "62.9", "152", "250",
    "48.54", "73", "104",
    # 数据块B：分产品 / 下游
    "11900", "75.78", "23100", "59.47", "69800", "41.62",
    "296.71", "1.88", "10700", "27.68", "86800", "51.78",
    "3500", "22.3", "5000", "12.9", "11100", "6.6", "15700", "38800", "167700",
    "59500", "51.53", "48800", "42.25", "6700", "5.8",
    "73.6", "43800", "17.39", "9.01", "1570", "2.64", "31.58", "42.3", "26.12",
    # 数据块C：分地区
    "6935.28", "57.21", "8764.24", "55.63", "21600", "55.7",
    "45300", "179.88", "39.2", "70200", "445.69", "60.8",
    "73200", "43.65", "109.91", "13.3", "20500", "12.09", "4887",
    # 数据块D：销量 / 单价 / 份额
    "2403", "3121", "7136", "17946", "25500", "3.3",
    "410", "3551", "5215", "5500",
    "59.34", "26.07", "16.76", "3.86", "2.72",
    "69.75", "32.4", "4200", "26.4",
    # 数据块E：资产负债
    "321500", "110.55", "60200", "143.36", "261300", "104.21",
    "6200", "40.5", "13700", "24500", "30000",
    # 数据块F：员工 / 专利
    "480", "175", "36.46", "142", "29.6", "516", "184", "154", "123", "264", "262",
    # 数据块G：IPO / 股东 / 募投 / 融资 / 机构观点
    "150.8", "4044.6434", "40446.434", "609932.22", "591714.92", "18217.31",
    "420171.12", "171500", "219.23", "38.56", "35.89", "0.01809759", "3008.772", "7.44",
    "1100", "629.44", "800.08", "845", "460.34", "3417.72", "231.6",
    "687", "603.08", "591.53", "564.9", "2285", "2439",
    "23.8216", "9.5367", "33.3583", "21.4395", "65.31",
    "9.6488", "7.1149", "5.4528", "4.4245", "4.49", "3.83", "2.6",
    "36", "12",
    "202245.93", "110973.8", "44540", "62411.39", "48", "85", "7.5", "11.5",
    "18.92", "120", "127", "1500", "1.5",
    "506", "559", "370", "269",
    # 数据块H：经营要点 / 产能 / 行业预测
    "9997", "1600", "9.9", "8.5", "13500", "3.99", "2.99", "65",
    "18000", "11000", "60.57", "150", "900",
    # 任务书明确给出的推算值 / 表态值（页面已标注性质）
    "609.93",   # 发行市值（=219.23倍×2025归母，底稿G亦载）
    "2779",     # 08-20 收盘 687 元 × 总股本 40446.434 万股推算（任务书给定约值）
    "2393",     # 08-26 收盘 591.53 元 × 总股本推算（任务书给定约值）
    "821",      # 8月底市值对应 2025 归母 PE（底稿结论要点8）
    "40", "50",  # 出口占比约 40–50%（任务书给定，管理层表态口径）
    "27.92",    # 可比公司研发费用率均值（底稿结论要点7）
    "60", "70",  # 四足份额 60–70%（管理层表态）
}

WHITELIST = DATE_PARTS | YEARS | SPEC_NUMBERS


def canon(token):
    """规范化数字 token：去负号；整数去前导零；小数另给出去尾零变体。返回候选集合。"""
    t = token.lstrip("-")
    cands = {t}
    if "." in t:
        t2 = t.rstrip("0").rstrip(".")
        cands.add(t2)
    else:
        cands.add(t.lstrip("0") or "0")
    return cands


def extract_data_block(html):
    """从 HTML 中提取 const DATA = {...}; 的 JSON 文本（括号配平）。"""
    idx = html.find("const DATA = ")
    if idx < 0:
        raise RuntimeError("未找到 const DATA 块")
    start = html.find("{", idx)
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(html)):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return html[start:i + 1]
    raise RuntimeError("DATA 块括号未闭合")


def check_numbers():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    raw = extract_data_block(html)
    data = json.loads(raw)  # 验证 DATA 是合法 JSON
    tokens = re.findall(r"-?\d+(?:\.\d+)?", raw)
    uniq = sorted(set(tokens), key=lambda x: (len(x), x))
    violations = []
    for tok in uniq:
        cands = canon(tok)
        if not any(c in WHITELIST for c in cands):
            violations.append(tok)
    print("=" * 64)
    print("【数字比对】DATA 块数字 token 总数: %d（去重 %d）" % (len(tokens), len(uniq)))
    print("【数字比对】底稿外数字: %d" % len(violations))
    for v in violations:
        print("  - 底稿外: %s" % v)
    # DATA 可被 json.loads 解析说明结构合法
    print("【数字比对】DATA JSON 结构合法: 是（顶层键 %d 个）" % len(data))
    return len(violations) == 0


# ---------------------------------------------------------------- Playwright 自检
def check_playwright():
    from playwright.sync_api import sync_playwright

    os.makedirs(SHOT_DIR, exist_ok=True)
    console_errors = []
    page_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto("file://" + HTML_PATH)
        # 等待 CDN（jsdelivr，失败页面自动回退 unpkg）与首屏渲染
        try:
            page.wait_for_function("window.echarts !== undefined", timeout=15000)
            echarts_ok = True
        except Exception:
            echarts_ok = False
        page.wait_for_timeout(2500)
        banner_shown = page.evaluate(
            "document.getElementById('cdnBanner').classList.contains('show')")
        # 滚动触发全部渐入与图表
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)
        # 全页截图
        page.screenshot(path=os.path.join(SHOT_DIR, "00_full.png"), full_page=True)
        # 4 个分段截图
        sections = ["history", "business", "finance", "ipo"]
        for i, sid in enumerate(sections):
            page.evaluate("document.getElementById('%s').scrollIntoView()" % sid)
            page.wait_for_timeout(1600)
            page.screenshot(path=os.path.join(SHOT_DIR, "%02d_%s.png" % (i + 1, sid)))
        # 图表画布数量
        canvas_count = page.evaluate("document.querySelectorAll('.echart canvas').length")
        browser.close()
    total_errors = len(console_errors) + len(page_errors)
    print("=" * 64)
    print("【Playwright】window.echarts 加载: %s" % ("成功" if echarts_ok else "失败"))
    print("【Playwright】CDN 失败提示条显示: %s" % ("是" if banner_shown else "否"))
    print("【Playwright】console 错误: %d，pageerror: %d（合计 %d）"
          % (len(console_errors), len(page_errors), total_errors))
    for e in console_errors[:10]:
        print("  console.error: %s" % e)
    for e in page_errors[:10]:
        print("  pageerror: %s" % e)
    print("【Playwright】已渲染 ECharts 画布数: %d（页面共 9 个图表容器）" % canvas_count)
    print("【Playwright】截图目录: %s" % SHOT_DIR)
    return total_errors == 0 and echarts_ok and canvas_count >= 6


if __name__ == "__main__":
    ok1 = check_numbers()
    ok2 = True
    if "--numbers-only" not in sys.argv:
        ok2 = check_playwright()
    print("=" * 64)
    print("总结: 数字比对 %s；Playwright 自检 %s"
          % ("通过" if ok1 else "未通过", "通过" if ok2 else "未通过"))
    sys.exit(0 if (ok1 and ok2) else 1)
