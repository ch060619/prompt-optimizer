# RC-057 执行证据

- RC ID: RC-057
- 状态：PASS（Windows/Linux 原型与 Tauri 构建已验证）
- 负责人：Codex
- 基线 Commit：`c4f13ad`
- 实现 Commits：`1d29f8e`、`fc7fe44`
- 前置 RC：RC-056 已完成；当前清单完成数保持 42
- 修改范围：`backend/rabbit_code/` Agent Core、prototype App Server、CLI、`backend/tests/test_rc057_agent_prototype.py`、`scripts/prototypes/rc057_agent_probe.py`、候选 ADR 和 Windows benchmark

## 已交付

- `AgentCore` 复用 RC-049 `ProviderEvent`，输出统一 `AgentEvent`，覆盖 started、delta、completed 和 cancelled。
- 独立 prototype App Server 提供 `/health` 与 `/agent/stream`；CLI 复用同一 Agent Core 并输出 JSON lines。
- Windows probe 实际启动 prototype App Server、读取 SSE、结束进程并确认无残留；取消语义由确定性单元测试验证。
- 候选架构 ADR 和机器可读 benchmark 明确保留 Python/FastAPI + React/TypeScript 路线，同时不伪造 TypeScript 替代实现数据。
- 新增最小 Tauri 2 桌面壳，复用 React `frontend/dist`，Windows/Linux 均完成原生构建。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc057_agent_prototype.py -q` | FAIL（预期）：Agent Core 模块不存在 |
| `python -m pytest backend/tests/test_rc057_agent_prototype.py -q` | PASS：4 passed；Agent 事件、取消、prototype SSE、CLI 共享序列和 ADR 边界通过 |
| `python scripts/prototypes/rc057_agent_probe.py` | PASS（Windows）：ready=true；startup 1343 ms；SSE 为 `started, delta, delta, delta, completed`；无残留进程；终止退出码 1 为宿主 terminate 语义 |
| `python scripts/workspace.py verify` | PASS：RC traceability/delivery check、Ruff、Mypy（42 源文件）、后端 74 passed、前端 9 passed、Lint、Build |
| `python -m mypy backend/src backend/rabbit_code scripts/prototypes/rc057_agent_probe.py` | PASS |
| `python -m ruff check backend/rabbit_code scripts backend/tests/test_rc057_agent_prototype.py` | PASS |
| Linux Docker `pytest`（RC-057/060/100/101） | PASS：14 passed；Linux Agent 事件、取消、CLI/TUI 与桌面边界通过 |
| Linux `python scripts/prototypes/rc057_agent_probe.py` | PASS：ready=true；startup 25195 ms；SSE 为 `started, delta, delta, delta, completed`；SIGTERM `-15`；无残留进程 |
| Linux wheel build | PASS：`rabbit_code-3.0.0-py3-none-any.whl`，283 KiB |
| Windows Tauri `cargo build --locked` | PASS：MSVC/Windows SDK 实际链接完成 |
| Linux Tauri `cargo build --locked` | PASS：生成 ELF64 x86-64 PIE；`scripts/prototypes/rc121_linux_window_probe.sh` 创建/调整/最大化/关闭窗口，退出码 0 |

## 结论与边界

- 采用共享 Python Agent Core、FastAPI App Server、CLI/TUI、React GUI 与薄 Tauri 壳；不再要求实现第二套 TypeScript Agent Core 才能完成候选基线。
- Linux 验证运行于 Docker Desktop 的 Debian/Xvfb/Openbox 环境；不等同于发行版安装包或物理 Linux GPU/桌面矩阵。
- 可复用本地镜像：`rabbit-code-tauri-linux:20260719-build`（含 Rust/Tauri 编译缓存）和 `rabbit-code-tauri-linux:20260719-xvfb`（含窗口测试依赖）。

## 环境

- 复核时间：2026-07-19（Asia/Shanghai）
- Windows：Rust 1.97.1、Visual Studio Build Tools 17.14.36、Windows SDK 10.0.26100
- Linux：Docker Engine 29.5.3、Debian trixie、Python 3.12、Rust 1.97.1、WebKitGTK 4.1
