# RC-038 首发平台支持矩阵

RC IDs: RC-038

## 范围与状态

首个稳定版只承诺 Windows 和 Linux。macOS 不在首发平台、CI、安装包、密钥库或端到端验收范围内；后续若增加 macOS，必须新增 RC 项和独立的平台/许可证/发布验证。

矩阵中的状态含义固定如下：

- **正式支持**：首发发布门槛必须覆盖该格；至少有一个固定 CI 环境或真实机器验收，失败会阻断对应发布。
- **尽力支持**：允许用户尝试，但不作为首发稳定版兼容承诺；必须记录实际验证环境和已知限制，不得写成通过。
- **不在首发范围**：不构建、不测试，也不对用户承诺；需要后续需求重新定义。

矩阵的“验证方式”是验收路径，不代表本文件创建时已经完成实测。未标记为 `verified` 的格只能保持计划状态。

## 操作系统与 CPU 架构

| 单元 | 操作系统版本 | CPU 架构 | 首发状态 | 验证环境与方式 | 负责人 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- |
| WIN-11-X64 | Windows 11 24H2 | x86_64 | 正式支持 | 真实 Windows 11 x64 机器；安装、首次启动、CLI、PowerShell/cmd、升级阻断、卸载和 SHA-256 校验 | Codex 执行；项目维护者发布签收 | planned |
| UBUNTU-24-X64 | Ubuntu 24.04 LTS | x86_64 | 正式支持 | 固定 `ubuntu-24.04` CI；另用 Ubuntu 24.04 x64 真实机器验证 AppImage、deb、CLI 和卸载 | Codex 执行；项目维护者发布签收 | planned |
| WIN-10-X64 | Windows 10 22H2 | x86_64 | 尽力支持 | 独立 Windows 10 x64 真实机器；运行 CLI/安装包冒烟，不阻断 Windows 11 发布 | 项目维护者 | planned |
| WIN-ARM64 | Windows 11 24H2 | arm64 | 尽力支持 | Windows on ARM64 真实机器；只在有可用设备时执行安装和 CLI 冒烟，不伪造 CI 结果 | 项目维护者 | blocked-no-fixed-runner |
| LINUX-ARM64 | Ubuntu 24.04 LTS | arm64 | 尽力支持 | 固定 arm64 CI 或真实 arm64 机器；验证 CLI 和 AppImage，未建立环境前不作稳定版承诺 | 项目维护者 | blocked-no-fixed-runner |
| OTHER-LINUX | 其他发行版/版本 | x86_64 或 arm64 | 不在首发范围 | 不纳入首发发布门槛；新增发行版需单独登记版本、镜像和验收负责人 | 项目维护者 | out-of-scope |

首发正式支持的 CPU 基线是 `x86_64`。arm64 保留为尽力支持，不能因为构建成功就提升为正式支持。

## 终端与 Shell

| 单元 | 终端 | Shell/版本 | 适用范围 | 首发状态 | 验证环境与方式 | 负责人 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-TERM-PS | Windows Terminal 1.21+ | PowerShell 7.4+ | CLI、启动脚本、日志和退出码 | 正式支持 | WIN-11-X64 真实机器；执行交互、无头、JSON、管道输入和非零退出码测试 | Codex 执行；项目维护者签收 | planned |
| WIN-CMD | Windows console/cmd.exe | cmd.exe 10.x | CLI、`start.bat` 和诊断命令 | 正式支持 | WIN-11-X64 真实机器；执行安装后 PATH、启动、诊断和卸载命令 | Codex 执行；项目维护者签收 | planned |
| WSL2-BASH | Windows Terminal + WSL2 | Ubuntu 24.04 / Bash 5.2+ | Linux CLI；不代表 Windows GUI 安装包 | 正式支持 | Windows 11 WSL2 实例；验证 CLI、管道、TTY/非 TTY 和工作区路径边界 | 项目维护者 | planned |
| LINUX-GNOME-BASH | GNOME Terminal 46+ | Bash 5.2+ | Ubuntu 24.04 CLI | 正式支持 | Ubuntu 24.04 x64 真实机器；验证交互、无头、JSON、信号取消和退出码 | Codex 执行；项目维护者签收 | planned |
| LINUX-KONSOLE-ZSH | Konsole 24.02+ | zsh 5.9+ | Linux CLI | 尽力支持 | 有对应 Linux 桌面机器时执行 CLI 冒烟；不阻断 Ubuntu 正式发布 | 项目维护者 | planned |
| WIN-PS51 | Windows console | Windows PowerShell 5.1 | CLI 兼容尝试 | 尽力支持 | WIN-11-X64 真实机器；仅验证无特殊编码依赖的 CLI 命令 | 项目维护者 | planned |

终端矩阵覆盖计划中要求的 Windows Terminal、PowerShell、cmd、WSL 和主流 Linux 终端。GUI 窗口行为由独立的桌面/视觉 RC 验证，不把终端通过等同于 GUI 通过。

## GPU 与运行模式

| 单元 | GPU/运行模式 | 首发状态 | 验证环境与方式 | 负责人 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| CPU-ONLY | 无 GPU，CPU-only | 正式支持 | WIN-11-X64 与 UBUNTU-24-X64；验证启动、离线规则路径、资源提示和基本 CLI/API 工作流 | Codex 执行；项目维护者签收 | planned |
| NVIDIA-CUDA | NVIDIA GPU，CUDA 12.x | 尽力支持 | 具备固定驱动和 CUDA 12.x 的 Windows/Linux 真实机器；记录 GPU、驱动、显存、模型和量化后再判定 | 项目维护者 | blocked-no-fixed-runner |
| AMD-INTEL | AMD 或 Intel GPU 加速 | 尽力支持 | 只有在对应运行器 Adapter 和固定真实设备可用时验证；没有设备时保持未验证 | 项目维护者 | blocked-no-fixed-runner |
| APPLE-GPU | Apple GPU | 不在首发范围 | macOS 不在首发平台范围；不构建、不测试、不承诺 | 项目维护者 | out-of-scope |

CPU-only 是首发最低可用基线。GPU 加速不是首发稳定版的必要条件；本矩阵不提前承诺某一 GPU、驱动、显存或模型规模的性能。

## 未签名安装包与校验

| 制品 | 目标环境 | 首发状态 | 验证环境与方式 | 负责人 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| Windows unsigned NSIS EXE | WIN-11-X64 | 正式支持 | 固定 Windows 11 x64 真实机器；全新安装、首次启动、升级/降级阻断、卸载和篡改文件后的 SHA-256 失败路径 | Codex 执行；项目维护者发布签收 | planned |
| Linux AppImage | UBUNTU-24-X64 | 正式支持 | Ubuntu 24.04 x64 真实机器和 `ubuntu-24.04` CI；下载、执行权限、首次启动、卸载/删除和 SHA-256 | Codex 执行；项目维护者发布签收 | planned |
| Linux deb | Ubuntu 24.04 x64 | 正式支持 | Ubuntu 24.04 x64 真实机器；安装、升级、降级阻断、卸载、残留数据选择和 SHA-256 | 项目维护者 | planned |
| Linux rpm | Fedora 41 x64 | 尽力支持 | Fedora 41 x64 真实机器或固定 CI；安装、卸载和 SHA-256；不阻断 Ubuntu 正式支持 | 项目维护者 | planned |

所有首发制品均为未签名制品。每个制品必须发布独立的 SHA-256 校验文件，安装器不得暗带本地模型权重。代码签名、公证和应用商店账户不属于当前发布前置条件；更新/下载只执行 HTTPS 来源、许可证和哈希校验。

## 验收责任与发布规则

| 验证环境 ID | 固定环境 | 用途 | 责任角色 |
| --- | --- | --- | --- |
| WIN-LOCAL-X64 | Windows 11 24H2 x64 真实机器 | Windows 正式格、Windows 终端和 Windows 未签名安装包 | Codex 执行；项目维护者发布签收 |
| CI-UBUNTU-X64 | GitHub Actions `ubuntu-24.04` x64 | Linux 构建、后端/前端质量门禁和 Linux CLI | Codex 执行；CI/项目维护者维护 |
| UBUNTU-LOCAL-X64 | Ubuntu 24.04 LTS x64 真实机器 | Linux 安装包、桌面终端、首次启动和卸载 | 项目维护者发布签收 |
| OPTIONAL-ARM-GPU | 明确记录型号、驱动、运行器和模型的 ARM/GPU 设备 | 尽力支持实验，不作为默认发布门槛 | 项目维护者 |

RC-038 完成的是范围和验证责任冻结；`planned` 与 `blocked-no-fixed-runner` 必须在后续平台、安装包、模型和测试 RC 中转换为可复现的验证证据后，才能写成 `verified`。任何正式支持格缺少固定环境、测试结果或发布签收时，stable 发布保持阻断。
