# 贡献指南

项目采用 GitHub Flow：`main` 保存通过检查的版本，每项改动从新分支发起 PR。无需维护长期 `develop` 分支。

## 一次改动的流程

1. 先查已有 Issue；新增接口、跨模块改动先在 Issue 说明目的、输入输出和验收方法。
2. 同步 `main` 后创建 `feat/<topic>`、`fix/<topic>`、`docs/<topic>` 或 `chore/<topic>`。
3. 一条 PR 解决一个问题，避免混入重命名、数据导出或无关格式化。
4. 运行对应离线测试和提交检查，PR 中写清命令、结果、跳过项和未做的现场验证。
5. 等待 CI 通过、讨论解决；优先 squash merge，合并后删除功能分支。

```powershell
git switch main
git pull --ff-only
git switch -c feat/rgbd-stream
# 修改后只暂存明确需要的路径
git add ue5/tools/example.py
python scripts/check_repository.py --staged-only
git diff --cached --check
git diff --cached
git commit -m "feat(slam): add RGB-D stream adapter"
git push -u origin feat/rgbd-stream
```

示例路径用于演示暂存方式，请替换为实际改动文件。不要用 `git add -f` 绕过忽略规则；先修改规则并在 PR 解释必要性。

## 提交与审查

提交采用 `type(scope): summary`，如 `fix(capture): correct depth scale`；摘要可中文或英文。类型使用 `feat`、`fix`、`docs`、`test`、`refactor`、`chore`、`ci`。不强制签名或复杂提交钩子。

默认代码责任人为仓库维护者。团队有第二位维护者后，启用至少 1 人批准并扩展 CODEOWNERS；个人维护阶段仍通过 PR 和 CI 合并，避免要求自己批准自己的 PR。

不要对 `main` 强推或改写已共享历史；自己尚未共享的功能分支可整理提交，已共享分支应先与协作者协调，必要时使用 `--force-with-lease`。

## 工程约定

- 先复核当前设备、系统、用户和路径；两台电脑的环境互不推定。
- 新配置不得写入用户名、服务器地址或凭据；秘密放环境变量或本地忽略文件。现有控制器路径依赖见开发指南。
- 保留现有代码风格；新 Python 代码用 4 空格，C++ 遵循 Unreal 习惯。
- 行为变化补充有意义的测试；低风险文档变更不必制造测试。
- 真值与估计输入隔离；禁止按评测成绩选择数据、手填指标或把 oracle 结果当算法表现。
- Windows 输入控制只在明确授权、有人观察并完成急停验收后测试；CI 不操作游戏、不启动收费云资源。
- 改动坐标系、单位、时间戳、深度或动作协议时，同时更新文档并提供兼容说明。

## 协作权限

公开访问无需写权限。外部伙伴可 Fork 后提 PR；熟悉项目后由所有者按需邀请协作者。不要共享账户、SSH 私钥、模型访问令牌或云机器登录信息。授权和第三方材料规则见 [NOTICE](NOTICE.md) 与 [上传规则](docs/repository-policy.md)。
