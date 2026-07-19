# RC-128 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-125；RC-122/127 的源素材和位图派生门禁保持 pending，不阻塞本项独立 SVG 标识实现
- 修改文件：`frontend/src/components/RabbitMark.tsx`、`frontend/src/styles.css`、`frontend/tests/RabbitMark.test.tsx`、`frontend/tests/RabbitRoutes.test.tsx`、`frontend/tests/App.test.tsx`、`docs/design/rabbit-small-mark.md`、`docs/evidence/RC-128/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- `mark` 和 `mono` 变体使用独立 64 x 64 SVG 轮廓，不再缩小整张 `/rabbit-artwork.png`。
- `mark` 保留帽檐强调色；`mono` 只使用当前文字色，可随浅色/深色主题变量切换。
- 组件保留 full/avatar/empty 的现有内部 PNG 边界，新增 `size` 仅用于固定尺寸的小标回归和受控调用。
- 装饰 SVG 使用 presentation/aria-hidden；非装饰 SVG 使用 img role 和 accessible label。
- 设计文档记录 16/20/24/32px 浅色/深色背景矩阵，并完成浏览器设计评审。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/RabbitMark.test.tsx` | PASS：4 tests；full/avatar/empty 保持内部 PNG，mark/mono 为独立 SVG，16/20/24/32px 和 light/dark 结构尺寸通过，装饰语义通过 | `frontend/tests/RabbitMark.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| Playwright 浏览器 DOM 检查 | PASS：8 个 SVG 覆盖浅/深背景各 16/20/24/32px；每个有 `viewBox=0 0 64 64`、正确 width/height 和 7 条轮廓路径 | `output/playwright/rc-128-small-mark-review.png` |
| Playwright 截图设计评审 | PASS：深浅背景均可辨识，无空白、溢出或整图缩小模糊；深色主题对比问题已修复后复核 | `output/playwright/rc-128-small-mark-review.png` |
| `npm --prefix frontend test -- --run` | PASS：15 test files、60 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、API drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-128/README.md` |

## 未解决项与后续

- 当前变更没有生成新的 PNG/WebP 或应用图标二进制；RC-122 源图/许可证确认后，RC-127 再执行位图预算和导出。
- 完整页面截图、高对比和 200% 缩放视觉回归留给 RC-133。
- 按用户指令，RC-128 完成后自动读取并继续 RC-129。

## 回滚

- 需要回滚的本项文件：恢复 `RabbitMark.tsx`、`styles.css` 和 `RabbitMark.test.tsx` 的 RC-128 修改，删除本设计和证据文件，并恢复执行计划/追踪索引；不删除 RC-125 的路由槽位或 RC-127 的交付规范。
