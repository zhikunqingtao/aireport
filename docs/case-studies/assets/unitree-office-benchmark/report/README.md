# v4.5.1 报告与复算材料

本目录仅保留当前活动版 v4.5.1。为保持公开 URL 稳定，下列兼容文件名继续沿用 `v4.5`，其内容版本为 v4.5.1：

- [自包含原报告](source-self-contained-v4.5.html)
- [活动数据](activity-report-data-v4.5.json)
- [GitHub发布适配数据](portable-report-data-v4.5.json)
- `release-v4.5/`：统一规则复算脚本、v4.5.1一致性修订/盖章脚本、构建源文件、最终数据、最终QA与发布清单

GitHub Pages 的阅读入口位于案例根目录。旧版报告、旧版PDF、候选稿、预加固副本及重复HTML不在本案例包内。原始参评文件和原生应用复核证据位于`../source-tree/`，不属于“报告版本”。

`release-v4.5/` 中以 `v451` 命名的脚本和 QA 才是当前发布流水线。`adjudicate_v45.py`、`stamp_v45.py`、`qa_v45.py`、`qa_interaction_affordance.json`、`qa_report_postpublication_hardened.json` 与 `recompute_summary.json` 仅保留为 v4.5 历史参考；其中的旧 HTML 哈希或浏览器 QA 不代表 v4.5.1 当前构建。

## v4.5.1 复现顺序

从仓库根目录依次运行：

```bash
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/revise_v451.py
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/qa_v451.py --phase candidate --out docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/qa_v451_candidate.json
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/stamp_v451.py
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/qa_v451.py --phase final --out docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/qa_v451.json
```

使用最终数据分别构建 GitHub Pages 版和全媒体自包含版：

```bash
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/build_report_v4.py --data docs/case-studies/assets/unitree-office-benchmark/report/portable-report-data-v4.5.json --out docs/case-studies/AI办公工具对比测评_宇树科技_截至2026-08-30.html --compress-report-data
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/build_report_v4.py --data docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/report_v4.5_final.json --out docs/case-studies/assets/unitree-office-benchmark/report/source-self-contained-v4.5.html --compress-report-data --allow-over-40mb
```

构建后运行 `release-v4.5/finalize_v451.py --write` 刷新构建摘要、发布清单、文件清单与全包 SHA-256，最后从仓库根目录运行总验收脚本：

```bash
node scripts/verify-unitree-office-benchmark.mjs --repo .
```

候选与最终 QA 使用固定时间和仓库相对路径；最终盖章绑定规范化 QA 摘要，避免因执行机器或运行时刻不同而改变冻结数据哈希。
