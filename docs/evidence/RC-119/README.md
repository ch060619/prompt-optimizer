# RC-119 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-118
- 修改文件：`frontend/src/components/UiStates.tsx`、`frontend/src/styles.css`、`frontend/src/App.tsx`、`frontend/src/workspaceHome.tsx`、`frontend/src/providerModels.tsx`、`frontend/src/localModels.tsx`、`frontend/src/settings.tsx`、`frontend/src/terminalProcess.tsx`、`frontend/src/promptAssets.tsx`、`frontend/tests/UiStates.test.tsx`、`frontend/tests/LocalModels.test.tsx`、`frontend/tests/__snapshots__/UiStates.test.tsx.snap`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 用户可见行为：共享 UI 库提供 `EmptyState`、`ErrorState`、`OfflineState`，以及通用 `UiDialog`、`PermissionDialog`、`InstallDialog`；工作区首页、主工作区、Provider 模型空列表、离线规则、本地模型安装、设置重置、终端关闭、Provider 编辑和 Prompt 导入均走共享状态/弹窗结构。
- 无障碍行为：弹窗使用 `dialog`/`alertdialog`、`aria-modal`、标题/描述关联；打开时聚焦第一个可聚焦控件，Tab 在弹窗内循环，Escape 关闭，关闭后恢复触发控件焦点。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/UiStates.test.tsx tests/ProviderModels.test.tsx tests/PromptAssets.test.tsx` | PASS：3 test files、11 passed；覆盖三类状态、两类 Dialog 快照和焦点/语义行为，并确认 Provider 编辑和 Prompt 导入迁移到共享 Dialog | `frontend/tests/UiStates.test.tsx`、`frontend/tests/__snapshots__/UiStates.test.tsx.snap` |
| `npm --prefix frontend test -- --run` | PASS：12 test files、44 passed；本地模型安装回归包含确认弹窗；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：重新生成反向追踪索引；RC-119 为 GREEN | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 44 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-119/README.md` |

## 现场记录

- 登记前的第一次根 verify 按预期在追踪门禁停止，报错为 `reverse index is stale; run with --write`；随后执行上述 `--write`，再次运行根 verify 通过。
- 仓库没有 Storybook 配置。本项没有引入未使用的 Storybook 依赖，而是使用 Vitest 的组件快照覆盖 Empty/Error/Offline/Permission/Install 五个变体，并用行为测试验证交互门禁。
- 测试中保留的 skip 为既有 Windows symlink 创建权限、WSL bash 运行时不可用和 RC-107 无交互剪贴板会话；既有 Python 迁移/环境 DeprecationWarning 与前端 jsdom navigation warning 不阻塞本项。

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、`UiStates.tsx`、`UiStates.test.tsx`、快照文件，并恢复本项对各页面、`styles.css`、执行计划和追踪索引的修改；不得覆盖 RC-066 至 RC-118 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 系统级原生权限弹窗、安装器和 Tauri 窗口层语义未接线，留给后续平台/桌面 RC。
- RC-057/060 外部确认仍 pending；既有环境警告和前端 jsdom navigation warning 不阻塞本项。
