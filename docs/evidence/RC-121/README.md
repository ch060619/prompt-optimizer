# RC-121 执行证据

- 状态：SUBMITTED WITH PENDING CONFIRMATION
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-060 desktop shell boundary、RC-120 window/system strategy
- 修改文件：`docs/adr/0012-title-bar-strategy.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 结论：未勾选 RC-121。当前仓库没有可运行 Tauri/Rust 桌面壳，也没有 Linux 桌面原型，不能验证原生/自绘标题栏的拖拽、最大化、双击、系统菜单、缩放、高对比和屏幕阅读器行为。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_desktop_boundary.py` | PASS：desktop shell boundary and command allowlist valid；仅证明业务边界，不证明标题栏交互 | `apps/desktop/command-allowlist.toml`、`scripts/check_desktop_boundary.py` |
| `Get-ChildItem apps/desktop -Recurse -File` | PENDING：只有 `README.md` 和 `command-allowlist.toml`，无 Rust/Tauri 工程或标题栏原型 | `apps/desktop/` |
| `docs/adr/0007-desktop-shell-boundary.md` | PENDING：明确 Tauri/Rust implementation and OS integration pending | `docs/adr/0007-desktop-shell-boundary.md` |

## 受阻条件与后续

- 需要 Windows/Linux 可运行桌面壳、标题栏原型、DPI/高对比/屏幕阅读器测试环境和可重复的拖拽/窗口控制夹具。
- 本项保持未完成，不把 boundary gate 的 PASS 写成标题栏验收 PASS。
- 按用户指令，已自动将下一待执行项推进到 RC-122；RC-057/060 外部确认仍 pending。

## 回滚

- 需要回滚的本项文件：删除本证据、`0012-title-bar-strategy.md`，并恢复执行计划和追踪索引对 RC-121 的登记；不得覆盖 RC-060、RC-120 或其他既有变更。
