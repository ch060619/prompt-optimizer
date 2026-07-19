# RC-117 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-106、RC-111、RC-116
- 修改文件：`frontend/src/settings.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/Settings.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/settings`；按外观、语言、终端、权限、沙箱、数据、隐私、更新、快捷键、MCP、插件和高级配置分区；显示 `WORKSPACE / LOCAL` 作用域和来源，设置变更即时写入 workspace-specific localStorage；危险重置需确认。
- 隔离边界：设置 key 使用 `rabbit_code_settings_<workspace>`，测试确认 workspace `alpha` 的主题不会出现在 `beta`，重置只影响当前 workspace。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/Settings.test.tsx` | PASS：3 passed；覆盖分区导航、即时持久化、终端/隐私/MCP/插件设置、workspace 隔离和危险重置确认 | `frontend/tests/Settings.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：10 test files、34 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：追踪索引生成并保持 current | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 34 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-117/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `Settings.test.tsx`，并恢复本项对 `settings.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-116 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 真实 OS/Tauri 设置存储、系统主题/语言/终端即时接线、系统快捷键/MCP/插件服务和跨设备同步尚未接线，留给后续平台 RC。
- RC-057/060 外部确认仍 pending；既有迁移/脚本环境与前端 jsdom navigation 警告不阻塞本项。
