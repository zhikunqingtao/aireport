# AI Report

宇树科技 AI 办公工具对比测评的静态报告与审计材料。

> 本仓库发布固定样本报告、可复算数据与已纳入范围的冻结证据；适用边界、未公开材料及第三方内容说明见下文“发布边界”。

## 查看报告

- [打开在线交互式报告](https://zhikunqingtao.github.io/aireport/case-studies/AI%E5%8A%9E%E5%85%AC%E5%B7%A5%E5%85%B7%E5%AF%B9%E6%AF%94%E6%B5%8B%E8%AF%84_%E5%AE%87%E6%A0%91%E7%A7%91%E6%8A%80_%E6%88%AA%E8%87%B32026-08-30.html)
- [报告发布入口](https://zhikunqingtao.github.io/aireport/)
- [证据包浏览说明](https://zhikunqingtao.github.io/aireport/evidence.html)
- [打开离线自包含报告](https://zhikunqingtao.github.io/aireport/case-studies/assets/unitree-office-benchmark/report/source-self-contained-v4.5.html)
- [证据包原始 README](docs/case-studies/assets/unitree-office-benchmark/README.md)
- [完整过程录屏哈希索引](docs/case-studies/assets/unitree-office-benchmark/manifests/process-video-index.json)

GitHub Pages 已从 `main` 分支的 `/docs` 目录发布：

<https://zhikunqingtao.github.io/aireport/>

## 参评工具入口

- [千问办公](https://qwenwork.cn/)
- [Qoder](https://qoder.cn/)
- [豆包办公](https://www.doubao.com/work/group)
- [WorkBuddy](https://www.workbuddy.cn/)
- [ZhikunCode](https://github.com/zhikunqingtao/zhikuncode/)

以上链接用于定位本次参评工具，不构成厂商认可、合作或推荐声明。

## 本地预览

克隆仓库后，在仓库根目录启动本地静态服务：

```bash
python3 -m http.server 8765 --directory docs
```

随后访问 <http://127.0.0.1:8765/>。建议通过本地 HTTP 服务查看，不直接依赖 `file://`，以避免浏览器对相对资源、下载和本地文件访问的额外限制。

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

在线 Pages 版通过仓库相对路径加载 710 个媒体对象；离线自包含版将同一批媒体嵌入单个 HTML。两者使用同一份报告数据和界面配置，评分、排名、交付闸门与证据标识一致。

## 完整性校验

在仓库根目录运行：

```bash
node scripts/verify-unitree-office-benchmark.mjs --repo .
```

校验器会检查报告摘要、清单记录、路径映射、录屏哈希边界和证据文件的完整性。已发布内容若有任何有意的脱敏或删减，应同步重建清单与报告，不能直接修改受校验文件后忽略失败。

可直接查看发布记录：

- [v4.5.2 Release Manifest](docs/case-studies/assets/unitree-office-benchmark/report/release-v4.5/release_manifest_v4.5.json)
- [SHA-256 校验和](docs/case-studies/assets/unitree-office-benchmark/manifests/SHA256SUMS.txt)
- [文件清单](docs/case-studies/assets/unitree-office-benchmark/manifests/files.json)

## 发布边界

证据包包含第三方网页快照、软件界面截图、办公文档与测试过程材料。它们可能带有第三方著作权、商标、账户信息、设备路径或其他隐私数据。发布者选择原样保留已纳入发布范围的材料；访问、下载、引用或再发布者应自行评估隐私、凭据、保密与版权风险。仓库的 MIT License 不自动授予这些第三方材料的权利。

当前活动展示版本为 `v4.5.2`，评分数据版本为 `v4.5.1`。v4.5.2 只升级版式、字体、导航、可读性与交互，不改变 30 件终稿的评分、排名、G0/G1/G2、证据或事实。两张“终稿独立使用”排名是正式固定样本结果；两张“首次归责”结果仅作为探索性非因果诊断，不用于采购名次。评测由单一评审者完成，未测量评审者间一致性；现有公开材料未具体列明评测者与参评工具之间是否存在开发、雇佣、投资、代理或委托关系。读者应结合冻结原件与可复算数据独立判断。

8 段视频合计完整记录本次 5 款工具 × 6 项任务的执行过程，但暂不上传 GitHub。需要核验原视频时，请通过 [GitHub Issues](https://github.com/zhikunqingtao/aireport/issues) 联系提供。

详见 [NOTICE.md](NOTICE.md)。
