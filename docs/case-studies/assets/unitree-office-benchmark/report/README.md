# v4.5.2 报告、冻结数据与复算材料

当前活动展示版本为 v4.5.2，评分数据版本为 v4.5.1。v4.5.2 仅升级视觉、导航、交互、打印与无障碍呈现，不改变 30 件终稿的评分、排名、交付闸门、事实、证据或来源。为保持公开 URL 与证据引用稳定，下列兼容文件名继续沿用 `v4.5`：

- [自包含原报告](source-self-contained-v4.5.html)
- [活动数据](activity-report-data-v4.5.json)
- [GitHub发布适配数据](portable-report-data-v4.5.json)
- `release-v4.5/`：v4.5.1 冻结数据及语义 QA、v4.5.2 视觉源文件、双版本构建器、展示层验证脚本与发布清单

GitHub Pages 的阅读入口位于案例根目录。旧版报告、旧版PDF、候选稿、预加固副本及重复HTML不在本案例包内。原始参评文件和原生应用复核证据位于`../source-tree/`，不属于“报告版本”。

`release-v4.5/` 中以 `v451` 命名的修订、盖章脚本和 QA 是当前冻结评分数据的复算依据，不是 v4.5.2 的展示层构建器。`adjudicate_v45.py`、`stamp_v45.py`、`qa_v45.py`、`qa_interaction_affordance.json`、`qa_report_postpublication_hardened.json` 与 `recompute_summary.json` 仅保留为 v4.5 历史参考；其中的旧 HTML 哈希或浏览器 QA 不代表 v4.5.2 当前构建。

## v4.5.2 展示层构建

展示层改动使用同一份 `report.ui.json` 和原子双版本构建器，不进入评分修订或盖章流程。默认命令只在临时目录完成双构建、确定性、语义一致性、媒体解析和 40 MiB 上限检查；加 `--write` 才会同时替换本地 Pages HTML 与自包含 HTML，仍不会提交或发布：

```bash
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/build_release_variants.py
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/build_release_variants.py --write
```

人工验收通过后，运行展示层校验和定版脚本；它们不会执行评分修订或数据盖章：

```bash
node scripts/verify-report-v452-preview.mjs --repo .
python3 docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/finalize_v452.py --write
node scripts/verify-unitree-office-benchmark.mjs --repo .
```

## v4.5.1 冻结评分数据复现顺序

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

候选与最终 QA 使用固定时间和仓库相对路径；最终盖章绑定规范化 QA 摘要，避免因执行机器或运行时刻不同而改变冻结数据哈希。
