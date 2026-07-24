# RC-121 执行证据

- 状态：PASS WITH DOCUMENTED ACCESSIBILITY LIMITS
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-060 desktop shell boundary、RC-120 window/system strategy
- 修改文件：`docs/adr/0012-title-bar-strategy.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 结论：采用 Tauri 原生标题栏（`decorations: true`），不引入自绘拖拽区；Windows/Linux 原生窗口创建、调整、最大化和关闭均已验证。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_desktop_boundary.py` | PASS：desktop shell boundary and command allowlist valid；仅证明业务边界，不证明标题栏交互 | `apps/desktop/command-allowlist.toml`、`scripts/check_desktop_boundary.py` |
| Windows Tauri window probe | PASS：标题 `Rabbit Code`；初始 1551x1061；最大化 1721x1033；恢复 1551x1061；关闭退出码 0 | `apps/desktop/src-tauri/tauri.conf.json` |
| Linux Xvfb/Openbox probe | PASS：初始 1534x999；调整 1200x800；EWMH 最大化 1536x1005；关闭退出码 0 | `scripts/prototypes/rc121_linux_window_probe.sh` |
| Windows/Linux `cargo build --locked` | PASS：Windows MSVC 可执行文件和 Linux ELF64 x86-64 PIE 均链接完成 | `apps/desktop/src-tauri/` |

## 验收边界

- 原生标题栏把拖拽、双击最大化、系统菜单、键盘窗口命令、缩放和高对比交给操作系统，不维护自绘标题栏的命中区域或辅助技术名称。
- 自动验证覆盖窗口创建、调整、最大化、恢复（Windows）和关闭；未把 Narrator/Orca 人工朗读结果伪造成自动测试通过。
- Linux 结果来自 Docker/Xvfb/Openbox；发行版、桌面环境和真实辅助技术矩阵继续作为发布级人工验收，而非阻断架构选择。

## 回滚

- 需要回滚的本项文件：删除本证据、`0012-title-bar-strategy.md`，并恢复执行计划和追踪索引对 RC-121 的登记；不得覆盖 RC-060、RC-120 或其他既有变更。
