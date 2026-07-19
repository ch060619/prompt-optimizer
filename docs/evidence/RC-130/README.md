# RC-130 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-129；RC-127 的实际位图导出仍 pending，不阻塞 token 系统
- 修改文件：`packages/ui/tokens.json`、`packages/ui/tokens.css`、`packages/ui/tokens.ts`、`packages/ui/token-snapshot.md`、`packages/ui/README.md`、`scripts/generate_design_tokens.py`、`scripts/workspace.py`、`frontend/src/styles.css`、`docs/design/rabbit-design-tokens.md`、`docs/evidence/RC-130/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 建立 light/dark 主题色、语义状态色、字体、间距、圆角、阴影、图标尺寸、动效和 Rabbit 装饰预算的 JSON 源。
- 生成 CSS 变量、TypeScript token 类型/helper 和 light/dark Markdown 快照。
- 前端样式改为消费 `packages/ui/tokens.css`，删除页面 CSS 中的直接颜色字面量。
- 将 token 生成漂移检查接入 `python scripts/workspace.py check`。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/generate_design_tokens.py --write` | PASS：生成 `tokens.css`、`tokens.ts` 和 `token-snapshot.md` | `packages/ui/` |
| `python scripts/generate_design_tokens.py --check` | PASS：三个生成物 current | `scripts/generate_design_tokens.py` |
| `frontend/src/styles.css` 原始颜色扫描 | PASS：无 `#...`、`rgb(...)` 或 `rgba(...)` 字面量 | `frontend/src/styles.css` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、API drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-130/README.md` |

## 未解决项与后续

- 当前 token 系统覆盖 Rabbit Code 前端样式；`packages/ui` 的 React primitives 仍按既有迁移边界留给后续 UI RC。
- 现有 390px Review 三栏响应式问题由 RC-255/256 处理，不用 token 迁移掩盖布局缺陷。
- 按用户指令，RC-130 完成后自动读取并继续 RC-131。

## 回滚

- 需要回滚的本项文件：删除 token 源/生成物、生成器、token 文档和证据，恢复 `workspace.py`、`styles.css`、执行计划和追踪索引；不回滚 RC-129 的层级 CSS 逻辑，只恢复其变量定义来源。
