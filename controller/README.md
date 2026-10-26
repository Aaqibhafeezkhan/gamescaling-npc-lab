# Windows 游戏控制实验

该模块将游戏画面送给 GameScaling 策略客户端，过滤模型建议并记录实际执行反馈。它是既有实验基础设施；当前尚未与 UE 的 SLAM 地图接成完整 NPC 决策闭环。

## 离线开发

在仓库根目录安装 `requirements/controller.txt` 后运行：

```powershell
python -m unittest discover -s tests -v
```

这些测试不启动模型或操作游戏。依赖官方 `gamescaling` 包的测试未满足依赖时明确跳过。

## 跨电脑配置

控制器不再假设固定的 WSL 发行版、用户目录或虚拟环境。启动本地 WSL 后端前，在当前 shell 配置以下变量：

| 变量 | 用途 | 示例 |
|---|---|---|
| `GAMESCALING_WSL_DISTRO` | 已安装的 WSL 发行版名称 | `Ubuntu-22.04` |
| `GAMESCALING_WSL_CLIENT_REPO` | WSL 内官方 GameScaling 客户端仓库的绝对路径 | `/home/alice/src/GameScaling` |
| `GAMESCALING_WSL_PYTHON` | WSL 内含客户端依赖的 Python 解释器绝对路径 | `/home/alice/venvs/game/bin/python` |
| `GAMESCALING_WINDOWS_CLIENT_REPO` | Windows 侧可访问的客户端仓库路径，供 cloud worker 导入 | `D:\\dev\\GameScaling` |

示例 PowerShell 配置（请替换为本机实际路径）：

```powershell
$env:GAMESCALING_WSL_DISTRO = "Ubuntu-22.04"
$env:GAMESCALING_WSL_CLIENT_REPO = "/home/alice/src/GameScaling"
$env:GAMESCALING_WSL_PYTHON = "/home/alice/venvs/game/bin/python"
$env:GAMESCALING_WINDOWS_CLIENT_REPO = "D:\\dev\\GameScaling"
```

WSL 后端所需配置缺失时会在启动子进程前报告缺少的变量。cloud worker 只使用显式配置的 Windows 客户端仓库路径。推理端点仍固定为回环地址，模型 ID 与模型根目录仍需精确匹配；这些配置不会开放任意 URL 或绕过模型身份检查。路径配置不包含凭据。

## 组件

| 文件 | 作用 |
|---|---|
| `automatic.py` | 自动启动编排与有限会话入口 |
| `bounded_session.py` | 参数校验、限时、停止与会话记录 |
| `run_agent.py` | 检查、截图、影子、校准与探索模式 |
| `control_core.py` | 动作校验、WASD 过滤、分段执行与释放 |
| `windows_adapter.py` | 客户区截图、窗口与权限检查、输入和急停 |
| `supervisor.py` | 独立线程监督失焦、急停和时限 |
| `wsl_bridge.py` | 有超时的 JSONL 桥接和进程清理 |
| `policy_worker.py` | 策略推理，建议动作与实际执行历史分离 |
| `backends.py` | 受限本地/云端回环端点与模型身份检查 |
| `evaluate_saved.py` | 已保存画面的受控评估 |
| `telemetry.py` | GPU 采样记录 |
| `cloud/` | 特定云平台的下载、预检和服务辅助脚本 |

## 接入前的限制

GPU 推理运行时、官方客户端、权重、云机器、隧道与凭据需要独立配置，仓库不包含这些资源。

现有端点固定为本地回环地址，不应为接入方便直接去掉校验或开放公网服务。云端服务脚本含 `--trust-remote-code`，正式运行前应审查所选上游版本及远程代码。

完成环境适配后，先进行无输入检查与影子模式。任何真实输入实验都需要独立授权，并在现场验证权限兼容、实体急停、失焦停止、超时和按键释放。不要把本次仓库初始化当成运行游戏输入的授权。

## 结果解释

程序状态成功只代表对应流程结束。已发送输入数不代表游戏接受动作或任务完成；模型建议不等于已执行历史。真实历史仅应提交确认完成的动作，过期或部分执行必须独立记录。

本地输出默认位于忽略的 `output/local-control` 下，可能包括截图、原始模型输出、窗口信息和运行日志。分享时先脱敏并审查内容，不直接上传整包。
