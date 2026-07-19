# RC-131 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-130；RC-127 的实际位图导出仍 pending，不阻塞图标语言
- 修改文件：`frontend/src/App.tsx`、`frontend/src/promptAssets.tsx`、`frontend/src/providerModels.tsx`、`frontend/src/taskWorkspace.tsx`、`frontend/src/terminalProcess.tsx`、`frontend/tests/App.test.tsx`、`frontend/tests/__snapshots__/UiStates.test.tsx.snap`、`scripts/check_rabbit_icon_language.py`、`scripts/workspace.py`、`docs/design/rabbit-icon-language.md`、`docs/evidence/RC-131/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 在 Workspace 的分析、优化、流式优化、后台优化和导出动作中使用熟悉的 Lucide 图标；`Sparkles` 仅用于提示词优化动作。
- 将 API onboarding 的入口保留为 `Cloud`，品牌入口保留为 `RabbitMark`；收藏使用 `Heart`，Provider 默认项使用 `Pin`，消除无关 `Star` 语义。
- 为 icon-only 的菜单、分页、收藏、关闭、添加、面板、终端发送和最近项目删除控件保留 `aria-label` 与 `title`；图标作为装饰时统一 `aria-hidden="true"`。
- 建立图标语言清单和 `workspace.py check` 门禁，防止后续将 `Sparkles` 或无关星形图标复用于其他操作。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_icon_language.py` | PASS：`Sparkles` 仅由 Workspace 优化入口持有；无未归属 `Star`；品牌/API 图标边界通过 | `scripts/check_rabbit_icon_language.py` |
| `npm --prefix frontend test -- --run tests/App.test.tsx` | PASS：10 passed；优化按钮使用 `lucide-sparkles`，分析按钮使用 `lucide-search`，Tooltip 检查通过 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、61 passed；图标门禁、Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-131/README.md` |

## 未解决项与后续

- 本项只锁定图标语义、Tooltip 和可访问名称，不宣称 RC-132 的完整键盘/对比度/200% 缩放验收。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-131 完成后自动读取并继续 RC-132。

## 回滚

- 需要回滚的本项文件：删除图标语言文档、门禁、证据和测试增量，恢复 Workspace 优化按钮、Prompt assets 收藏图标、Provider 默认图标及相关 Tooltip 修改；不回滚 RC-128 的 mark/mono SVG、RC-129 层级逻辑或 RC-130 token 系统。
