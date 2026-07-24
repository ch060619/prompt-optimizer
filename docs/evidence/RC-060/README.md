# RC-060 执行证据

- RC ID: RC-060
- 状态：PASS（Tauri/Rust 桌面壳与双平台构建已验证）
- 负责人：Codex
- 基线 Commit：`94c6920`
- 实现 Commit：`590d4d9`
- 前置 RC：RC-059 已完成；RC-057 外部平台确认仍 pending
- 修改范围：`apps/desktop/command-allowlist.toml`、`scripts/check_desktop_boundary.py`、`backend/tests/test_rc060_desktop_boundary.py`、`docs/adr/0007-desktop-shell-boundary.md`

## 已交付

- 建立 desktop shell command allowlist，限定 window、file picker、notification、update、secret-store 和 sidecar lifecycle 六类 OS 能力。
- 明确 `business_logic=false`，静态检查拒绝 desktop 代码直接出现 `prompt_optimizer`、`Provider` 或 `AgentCore` 实现引用。
- ADR 记录 Agent/Provider/Prompt/Session 逻辑必须留在 App Server/Agent Core，桌面壳只承载协议和 OS 桥接。
- `apps/desktop/src-tauri` 提供最小 Tauri 2 工程、窗口配置、默认 capability、Windows ICO 和跨平台 PNG；桌面壳未引入 Agent/Provider 业务逻辑。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc060_desktop_boundary.py -q` | FAIL（预期）：desktop boundary checker 尚不存在 |
| `python -m pytest backend/tests/test_rc060_desktop_boundary.py -q` | PASS：2 passed |
| `python scripts/check_desktop_boundary.py` | PASS |
| `python -m ruff check scripts/check_desktop_boundary.py backend/tests/test_rc060_desktop_boundary.py` | PASS |
| `python -m mypy scripts/check_desktop_boundary.py` | PASS |
| Windows `cargo check/build --locked` | PASS：Rust 1.97.1 + MSVC/Windows SDK；生成并启动 `rabbit-code-desktop.exe` |
| Linux `cargo check/build --locked` | PASS：Debian/WebKitGTK；生成 ELF64 x86-64 PIE |
| Windows 原生窗口 probe | PASS：初始 1551x1061；最大化 1721x1033；恢复 1551x1061；关闭退出码 0、无残留进程 |
| Linux Xvfb/Openbox probe | PASS：初始 1534x999；调整 1200x800；EWMH 最大化 1536x1005；关闭退出码 0 |

## 结论与边界

- RC-060 的薄壳职责、命令白名单、Tauri 工程和 Windows/Linux 构建已完成，可勾选。
- `start_sidecar`、`store_secret`、`pick_file` 仍以明确错误表示需要打包宿主桥接；完整安装包、OS Keychain round-trip 和 sidecar 制品绑定属于后续发布/安全集成，不作为薄壳边界验收的伪通过项。
- Linux 测试为 Docker/Xvfb/Openbox，不等同于各发行版安装器验收。

## 环境

- 复核时间：2026-07-19（Asia/Shanghai）
- Docker Engine 29.5.3；Rust 1.97.1；Visual Studio Build Tools 17.14.36；Debian trixie/WebKitGTK 4.1
