# RC-132 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-131；RC-127 的实际位图导出仍 pending，不阻塞无障碍系统
- 修改文件：`packages/ui/tokens.json`、`packages/ui/tokens.css`、`packages/ui/tokens.ts`、`packages/ui/token-snapshot.md`、`frontend/src/styles.css`、`frontend/src/App.tsx`、`frontend/src/components/SiteShell.tsx`、`frontend/src/components/UiStates.tsx`、`frontend/src/taskWorkspace.tsx`、`frontend/src/changeReview.tsx`、`frontend/tests/App.test.tsx`、`frontend/tests/TaskWorkspace.test.tsx`、`frontend/tests/ChangeReview.test.tsx`、`frontend/tests/__snapshots__/UiStates.test.tsx.snap`、`docs/design/rabbit-accessibility.md`、`docs/evidence/RC-132/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 建立可见 focus ring、forced-colors、ARIA landmark/tab/dialog 语义、表单名称、焦点循环/恢复、reduced-motion 和 200% 等效缩放规则。
- 修复 light/dark 主题颜色对比度，避免暗色主题把深色表面 token 当作浅色文字，确保状态、表单、错误面板和主按钮可读。
- `Task`/`Review` 不再产生嵌套 main；Task inspector tabs 与 panel 语义关联；Workspace 主页面有唯一 h1 和命名 complementary landmarks。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| Playwright + axe-core 4.10.2 | PASS：14 条覆盖路由分别在 light/dark 主题运行，共 28 组，全部 `violations: []` | `docs/design/rabbit-accessibility.md` |
| Playwright keyboard flow | PASS：全屏导航最后一个控件 Tab 回到第一个链接；Escape 关闭并恢复 `Open navigation` 焦点 | `frontend/tests/App.test.tsx`、`.playwright-cli/page-*.yml` |
| Playwright reduced-motion / 640px | PASS：scroll auto、reveal opacity 1/transform none；640px CSS 视口 clientWidth 与 scrollWidth 均为 640 | `output/playwright/rc-132-home-640-reduced-motion.png` |
| `npm --prefix frontend test -- --run` | PASS：15 test files、62 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、62 passed；图标语言门禁、Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-132/README.md` |

## 未解决项与后续

- 原生 axe CLI 受本机 Chrome/ChromeDriver 版本不匹配阻塞；已用相同 axe-core 版本注入 Playwright 页面完成 28 组审计，不伪造原生 CLI 结果。
- 本项完成目标是 WCAG 2.2 AA 的自动化和关键键盘流程；Windows/Linux 原生桌面读屏、标题栏与安装包级验收仍留给平台 RC。
- 390px Review 既有三栏拥挤问题仍由 RC-255/256 处理；本项只确认没有横向溢出和无障碍阻断。
- RC-127 实际 PNG/WebP/应用图标导出及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-132 完成后自动读取并继续 RC-133。

## 回滚

- 需要回滚的本项文件：删除无障碍设计/证据、token 增量和 h2 快照，恢复 focus/reduced-motion/forced-colors CSS、主题表面与状态 token、Task/Review landmark/tab 语义、菜单焦点循环和 Workspace 标签修改；不回滚 RC-131 图标语言门禁。
