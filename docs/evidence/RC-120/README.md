# RC-120 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-119、RC-060 desktop shell boundary
- 修改文件：`frontend/src/windowPreferences.ts`、`frontend/src/components/SiteShell.tsx`、`frontend/src/taskWorkspace.tsx`、`frontend/src/settings.tsx`、`frontend/src/styles.css`、`frontend/tests/WindowPreferences.test.ts`、`frontend/tests/TaskWorkspace.test.tsx`、`frontend/tests/Settings.test.tsx`、`docs/adr/0011-window-and-system-integration-strategy.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 用户可见行为：单原生窗口承载内部多工作区；窗口 bounds、面板状态、light/dark 主题、通知和可选托盘偏好使用共享键 `rabbit_code_window_preferences`；Task inspector 重新打开时恢复面板/展开状态；设置页立即应用主题；已获权限时可发送系统通知，否则使用本地事件边界。
- 恢复边界：保存的 logical-pixel bounds 在工作区变化后钳制到至少保留 80 像素可见；原生壳读取该记录完成真实窗口恢复，当前 webview 不自行移动宿主窗口。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/WindowPreferences.test.ts tests/TaskWorkspace.test.tsx tests/Settings.test.tsx` | PASS：3 test files、9 passed；覆盖 bounds 钳制、偏好持久化、通知禁用、面板恢复和主题应用 | `frontend/tests/WindowPreferences.test.ts`、`frontend/tests/TaskWorkspace.test.tsx`、`frontend/tests/Settings.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_desktop_boundary.py` | PASS：desktop shell boundary and command allowlist valid | `apps/desktop/command-allowlist.toml`、`scripts/check_desktop_boundary.py` |
| `python scripts/check_rc_traceability.py --write` | PASS：重新生成反向追踪索引；RC-120 为 GREEN | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 47 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-120/README.md` |

## 现场记录

- 当前 `apps/desktop` 只有 allowlist 和 Proposed ADR，没有可执行 Tauri/Rust 工程；因此 native resize/move、tray lifecycle、OS notification permission、DPI 和 Windows/Linux multi-monitor 实机没有伪造成通过。
- webview 能力通过 `windowPreferences.ts` 提供可测试的持久化/恢复边界；ADR-0011 记录了单窗、内部多工作区、逻辑像素和原生壳接管范围。
- 完整根验证保留既有 Windows symlink、WSL bash、RC-107 剪贴板 skip，以及 Python 迁移/环境和前端 jsdom navigation warning。

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、`0011-window-and-system-integration-strategy.md`、`windowPreferences.ts`、`WindowPreferences.test.ts`，并恢复本项对 Shell、Task workspace、Settings、CSS、执行计划和追踪索引的修改；不得覆盖 RC-066 至 RC-119 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。
