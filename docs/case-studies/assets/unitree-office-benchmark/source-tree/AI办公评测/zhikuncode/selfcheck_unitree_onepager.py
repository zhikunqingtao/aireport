#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selfcheck_unitree_onepager.py — 数字零误差自检
抽取 宇树科技_投资人一页纸.html 可见文本中的全部数字 token，
与 unitree_excel_spec.md（底稿）数字集合逐一比对。
SVG 坐标轴刻度（class="tick"，版式标尺非数据）单列不参与比对。
白名单：2016（成立年份，任务约定豁免的结构性数字，见 unitree_business.md）。
"""
import re, sys
from html.parser import HTMLParser

HTML = "/Users/guoqingtao/Desktop/AI办公评测/zhikuncode/宇树科技_投资人一页纸.html"
SPEC = "/Users/guoqingtao/Desktop/dev/code/zhikuncode/backend/.zhikun/scratchpad/6992084c-5998-4b16-be17-8d993359853a/unitree_excel_spec.md"
WHITELIST = {
    "2016": "成立年份（结构性数字，任务约定豁免）",
    "2026-08-31": "底稿“08-31 收564.90元（市值约2,285亿）”补全年份；任务文案指定",
}

TOK = re.compile(r"\d{4}-\d{2}(?:-\d{2})?|\d[\d,]*(?:\.\d+)?%?")
FULLDATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def variants(tok):
    v = {tok, tok.replace(",", "")}
    out = set()
    for x in v:
        out.add(x)
        out.add(x.rstrip("%"))
        out.add(x.lstrip("-"))
        out.add(x.lstrip("-").rstrip("%"))
        if FULLDATE.match(x):          # 全日期 → 年月前缀（如 2025-09-30 ⊃ 2025-09）
            out.add(x[:7])
    return out

class TextGrab(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.buf = []
    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("style", "script") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

def tokens(text):
    s = set()
    for m in TOK.finditer(text):
        s.add(m.group(0))
    return s

def main():
    raw = open(HTML, encoding="utf-8").read()
    # 1) 单独提取坐标轴刻度（版式标尺）
    ticks = set(re.findall(r'<text[^>]*class="tick"[^>]*>([^<]+)</text>', raw))
    raw_wo_ticks = re.sub(r'<text[^>]*class="tick"[^>]*>[^<]+</text>', "", raw)
    # 2) 可见文本
    g = TextGrab(); g.feed(raw_wo_ticks)
    vis = " ".join(g.buf)
    spec = open(SPEC, encoding="utf-8").read()
    spec_set = set()
    for t in tokens(spec):
        spec_set |= variants(t)
    html_toks = tokens(vis)
    ok, miss, wl = [], [], []
    for t in sorted(html_toks):
        if variants(t) & spec_set:
            ok.append(t)
        elif t.replace(",", "").rstrip("%") in WHITELIST:
            wl.append(t)
        else:
            miss.append(t)
    print("=== 可见文本数字 token 总数: %d ===" % len(html_toks))
    print("命中底稿: %d ｜ 白名单豁免: %d ｜ 底稿外: %d" % (len(ok), len(wl), len(miss)))
    print("\n--- 白名单豁免 ---")
    for t in wl:
        print(" ", t, "→", WHITELIST[t.replace(",", "").rstrip("%")])
    print("\n--- 底稿外数字（目标=0） ---")
    for t in miss:
        print("  !!", t)
    if not miss:
        print("  （无）")
    print("\n--- 坐标轴刻度（版式标尺，不参与比对） ---")
    print(" ", ", ".join(sorted(ticks)))
    print("\n--- 命中底稿的数字清单 ---")
    print(" ", ", ".join(ok))
    return 1 if miss else 0

if __name__ == "__main__":
    sys.exit(main())
