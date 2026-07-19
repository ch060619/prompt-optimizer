# RC-129 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-124/125/126/128；RC-127 的实际位图导出仍 pending，不阻塞工作页层级门禁
- 修改文件：`frontend/src/components/SiteShell.tsx`、`frontend/src/styles.css`、`frontend/tests/RabbitRoutes.test.tsx`、`docs/design/rabbit-content-hierarchy.md`、`docs/evidence/RC-129/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 定义交互、代码/diff/终端、状态和 Rabbit 装饰的四级优先级。
- 将工作页 mark/mono/empty 的尺寸、透明度、移动端预算和不可交互边界写入 CSS 变量与设计文档。
- 固定槽位增加 `aria-hidden`、`data-rabbit-layer="decorative"` 和无按钮结构门禁。
- 定义 Review、Terminal、Task 的真实密集内容视觉夹具，要求长代码、长日志、diff、错误和关键按钮优先。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/RabbitRoutes.test.tsx` | PASS：9 passed；固定槽位均为 decorative/aria-hidden、无按钮后代，empty 使用 PNG，mark/mono 使用独立 SVG | `frontend/tests/RabbitRoutes.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| Playwright Review/Terminal/Task 密集内容检查 | PASS：1280x1000 Desktop 与 390x844 窄窗口检查；mark/mono 按 56/32px 和 0.16/0.12 预算渲染，`pointer-events=none`，与标题、按钮、输入、textarea、pre、状态的交集为空 | `output/playwright/rc-129-review-desktop.png`、`output/playwright/rc-129-review-mobile.png`、`output/playwright/rc-129-terminal-desktop.png`、`output/playwright/rc-129-terminal-mobile.png`、`output/playwright/rc-129-task-mobile.png` |
| Playwright 视觉人工复核 | PASS：真实 diff、长终端日志、命令输入、验证/回滚按钮和 Task composer 可扫描；装饰没有覆盖内容；现有 Review 390px 三栏拥挤保留给 RC-255/256 | `docs/design/rabbit-content-hierarchy.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、API drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-129/README.md` |

## 未解决项与后续

- 本项控制页面层级和装饰预算，不宣称 RC-133 的全路由视觉回归已完成。
- RC-127 的 PNG/WebP/应用图标实际导出仍等待 RC-122 源文件和授权。
- 390px Review 的既有三栏布局存在横向拥挤和文字截断风险，未由本项新增；交给 RC-255/256，不能用装饰层级门禁替代页面响应式修复。
- 按用户指令，RC-129 完成后自动读取并继续 RC-130。

## 回滚

- 需要回滚的本项文件：删除本设计和证据，恢复 `SiteShell.tsx`、`styles.css`、`RabbitRoutes.test.tsx` 的 RC-129 修改，并恢复执行计划/追踪索引；不删除 RC-128 的 SVG 标识。
