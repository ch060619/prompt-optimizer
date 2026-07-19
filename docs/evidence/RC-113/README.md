# RC-113 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-094、RC-111
- 修改文件：`frontend/src/terminalProcess.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/TerminalProcess.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/terminal`；支持多终端标签、选中终端的命令输入和输出、终端尺寸字段与同步状态、后台进程列表及停止/重启、终端退出恢复和关闭确认；确认关闭后所有 UI 运行项转为 stopped，页面报告无运行进程残留。
- 边界：RC-094 已提供真实进程生命周期和显式 PTY 不可用契约；本项实现的是前端终端/进程消费边界，使用稳定的本地状态夹具。真实 PTY service、真实 shell I/O、窗口 resize 接线和跨平台关闭无残留实测留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/TerminalProcess.test.tsx` | PASS：3 passed；覆盖多标签、日志、命令输入、尺寸同步、终端停止/恢复、后台进程停止/重启和关闭清理 | `frontend/tests/TerminalProcess.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：6 test files、24 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `python -m pytest backend/tests/test_rc094_process_tools.py -q` | PASS：5 passed；复核进程注册、游标日志、超时/停止、端口探测、PTY 边界和生命周期清理 | `backend/tests/test_rc094_process_tools.py` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：追踪索引生成并保持 current | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 24 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-113/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `TerminalProcess.test.tsx`，并恢复本项对 `terminalProcess.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-112 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 真实 PTY service、真实 shell I/O、窗口 resize 接线、终端与后端 process registry 的实时订阅、关闭应用时的跨平台无残留实测尚未接线，留给后续 RC。
- RC-057/060 外部确认仍 pending；既有迁移/脚本环境与前端 jsdom navigation 警告不阻塞本项。
