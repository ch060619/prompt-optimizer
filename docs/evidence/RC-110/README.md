# RC-110 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-054、RC-058、RC-086、RC-109
- 修改文件：`frontend/src/workspaceHome.tsx`、`frontend/src/App.tsx`、`frontend/src/api.ts`、`frontend/src/styles.css`、`frontend/tests/WorkspaceHome.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/home` 工作区首页；认证用户从生成 API client 加载项目，guest 从本地最近记录加载项目；显示最近任务、当前模型、模型状态、账户/guest 路由；支持打开项目目录选择器、快速新建任务、项目链接、移除最近项目、空状态和项目服务错误重试。
- 持久化与边界：项目移除写入本地隐藏 ID，远程服务重载不会立即恢复；默认不提供删除服务器项目操作；目录选择仅更新本地最近记录，不上传用户文件；现有 `/workspace` 提示词编辑器路由保持不变。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/WorkspaceHome.test.tsx` | PASS：3 passed；覆盖 guest 空状态、API 项目/模型状态/移除、服务错误/重试 | `frontend/tests/WorkspaceHome.test.tsx` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-110/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `WorkspaceHome.test.tsx`，并恢复本项对 `workspaceHome.tsx`、`App.tsx`、`api.ts`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-109 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实目录权限探测、服务器项目删除/历史服务、任务列表统一 API、Provider 模型目录和完整项目上下文恢复留给后续 RC；RC-057/060 外部确认仍 pending。
