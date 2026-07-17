# RC-060 执行证据

- RC ID: RC-060
- 状态：实现完成、验证受阻（不勾选完成）
- 负责人：Codex
- 基线 Commit：`94c6920`
- 实现 Commit：`590d4d9`
- 前置 RC：RC-059 已完成；RC-057 外部平台确认仍 pending
- 修改范围：`apps/desktop/command-allowlist.toml`、`scripts/check_desktop_boundary.py`、`backend/tests/test_rc060_desktop_boundary.py`、`docs/adr/0007-desktop-shell-boundary.md`

## 已交付

- 建立 desktop shell command allowlist，限定 window、file picker、notification、update、secret-store 和 sidecar lifecycle 六类 OS 能力。
- 明确 `business_logic=false`，静态检查拒绝 desktop 代码直接出现 `prompt_optimizer`、`Provider` 或 `AgentCore` 实现引用。
- ADR 记录 Agent/Provider/Prompt/Session 逻辑必须留在 App Server/Agent Core，桌面壳只承载协议和 OS 桥接。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc060_desktop_boundary.py -q` | FAIL（预期）：desktop boundary checker 尚不存在 |
| `python -m pytest backend/tests/test_rc060_desktop_boundary.py -q` | PASS：1 passed |
| `python scripts/check_desktop_boundary.py` | PASS |
| `python -m ruff check scripts/check_desktop_boundary.py backend/tests/test_rc060_desktop_boundary.py` | PASS |
| `python -m mypy scripts/check_desktop_boundary.py` | PASS |
| `cargo` / `rustc` availability | BLOCKED：当前环境未安装 Rust 工具链，未伪造 Tauri build、Keychain 或 sidecar lifecycle 结果 |

## 阻塞与自动继续

- Tauri/Rust 工程、Windows/Linux 打包、OS Keychain 实测和参数级 Rust 测试尚未执行；ADR 保持 Proposed。
- RC-060 保持 `[ ]`，完成数不增加；阻塞已记录，按用户要求自动进入 RC-061 协议层准备。

## 环境

- 时间：2026-07-17 15:52:43 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
