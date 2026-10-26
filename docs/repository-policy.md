# 上传范围与 Git 规则

仓库发布采用 `.gitignore` 白名单，意外新增的根目录默认不入库。新增共享目录需在 PR 同时修改忽略规则和检查脚本，说明用途、大小及授权来源。

| 材料 | 决定 | 原因 |
|---|---|---|
| controller、tests、ue5/tools | 上传 | 可复用逻辑、实验实现和回归验证 |
| UE Source、uproject、三个 Default 配置 | 上传 | 源代码与必要项目描述；保留版权头 |
| 精简工程文档、协作模板、依赖清单 | 上传 | 支持新人理解、复现和审查 |
| output、tmp、inputs | 仅本地 | 原始数据、截图、私人材料、运行状态及临时导出混杂 |
| docs 历史日期文档、tutorials、superpowers | 仅本地 | 含机器路径、云端连接过程及私人交接；有价值结论另行脱敏整理 |
| research 及其论文全文/翻译/插图 | 仅本地 | 版权边界和人员信息未逐项确认；公开版使用原创摘要或来源入口 |
| UE Content、Media、编辑器模板配置 | 仅本地 | 蓝图、地图和模板资产分发来源未审定；默认启动资源需开发者补齐 |
| UE Binaries/Intermediate/Saved/DerivedDataCache | 不入库 | 可生成、体积大且可能记录个人路径 |
| 密钥、令牌、.env、私钥、云端账户/连接记录 | 禁止上传 | 凭据、隐私与账户安全 |
| 模型权重、数据库、点云、批量帧 | 不入 Git | 大体积或可再生成；需要发布时单独审查数据集与许可 |

“仅本地”不表示没有价值，也不会删除文件。GitHub 仓库不构成这些材料的备份。将来可分享的数据应有独立的许可、来源、内容审查、清单与校验和，再选择数据集存储；当前没有启用 Git LFS。

## 提交前

先显式 `git add <paths>`，运行 `python scripts/check_repository.py --staged-only`，再查看 `git diff --cached --check` 与 `git diff --cached`。检查脚本扫描暂存区实际内容；默认扫描全部跟踪文件，检查路径、大小和常见令牌/私钥模式，不回显匹配内容。它不是完整的数据泄漏检测器，仍需人工审查。

## 远程规则

目标配置：`main` 需 PR，CI 的 `controller-offline`、`slam-offline`、`repository-policy` 三项通过，分支需保持更新，讨论需解决，禁止强推和删除，只用 squash merge。仓库所有者保留管理恢复能力；普通协作者按规则合并。单维护者阶段不强制人工批准；出现第二位维护者后提高到 1 人批准。

GitHub 的保护分支是服务端配置，单靠提交本文件不会生效；实际应用结果以 GitHub 设置与交付记录为准。[GitHub 保护分支说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)。
