# AI Report

宇树科技 AI 办公工具对比测评的静态报告与审计材料。

> 本仓库保留完整原始证据，未对其中的账户信息、本机路径、文档元数据或第三方快照作脱敏删减。报告基于固定样本、固定时间窗口与特定测试环境，不应被解读为对任一产品长期能力的普遍结论。

## 查看报告

- [交互式 HTML 报告](docs/case-studies/AI办公工具对比测评_宇树科技_截至2026-08-30.html)
- [证据包浏览说明](docs/evidence.html)
- [证据包原始 README](docs/case-studies/assets/unitree-office-benchmark/README.md)

如果后续启用 GitHub Pages，仓库入口预计为：

<https://zhikunqingtao.github.io/aireport/>

当前 GitHub Pages 尚未启用；以上地址仅用于说明预期发布方式。

## 目录结构

```text
.
├── docs/
│   ├── index.html
│   ├── evidence.html
│   └── case-studies/
│       ├── AI办公工具对比测评_宇树科技_截至2026-08-30.html
│       └── assets/unitree-office-benchmark/
├── scripts/
│   └── verify-unitree-office-benchmark.mjs
├── LICENSE
└── NOTICE.md
```

`docs/` 可直接作为 GitHub Pages 的发布目录。主报告通过相对路径引用证据包，因此在本地 HTTP 服务和 GitHub Pages 子路径下均可打开。

## 完整性校验

在仓库根目录运行：

```bash
node scripts/verify-unitree-office-benchmark.mjs --repo .
```

校验器会检查报告摘要、清单记录、路径映射和证据文件的完整性。已发布内容若有任何有意的脱敏或删减，应同步重建清单与报告，不能直接修改受校验文件后忽略失败。

## 发布边界

证据包包含第三方网页快照、软件界面截图、办公文档与测试过程材料。它们可能带有第三方著作权、商标、账户信息、设备路径或其他隐私数据。发布者选择按完整原始证据范围保留这些材料；访问、下载、引用或再发布者应自行评估隐私、凭据、保密与版权风险。仓库的 MIT License 不自动授予这些第三方材料的权利。

详见 [NOTICE.md](NOTICE.md)。
