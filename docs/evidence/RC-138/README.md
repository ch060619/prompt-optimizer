# RC-138 执行证据

- RC ID: RC-138
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-137
- 修改文件：`scripts/generate_api.py`、`frontend/src/generated/client.ts`、`frontend/src/api.ts`、`frontend/src/components/PromptOptimizeButton.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx`、`docs/evidence/RC-138/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 生成 API client 的 optimize/optimizeStream 调用支持可选 `AbortSignal`；优化按钮取消时，信号传递到 `fetch`，并在响应异常路径忽略已取消请求。
- 用 `promptRevisionRef` 保存最新输入 revision；请求回包仅在快照 revision 未变时直接应用。
- revision 已变化时保留结果快照，不写入当前结果区，展示“输入已改变，优化结果待比较”，提供“查看比较”和“重新优化”。
- 重新优化通过同一优化按钮 ref 触发，不复制请求逻辑；查看比较只应用返回结果，不修改用户当前输入。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizeButton.test.tsx tests/App.test.tsx` | PASS：2 test files、19 tests passed；组件 7 passed，App 12 passed；覆盖 signal abort、延迟回包、revision 变化、待比较和重试 | `frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx` |
| `python scripts/generate_api.py --check` | PASS：生成的 schema/client 与 OpenAPI current，optimize/optimizeStream 的 signal 改动可复现 | `scripts/generate_api.py`、`frontend/src/generated/client.ts` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题；保留 TypeScript 5.9 与 typescript-estree 支持范围提示 | `frontend/src/`、`frontend/tests/` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 16 test files、70 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-138/README.md` |

## 未解决项与后续

- 当前“查看比较”复用现有结果展示，尚未提供 RC-140 要求的结构化行内/并排 diff、选区替换、撤销和长文本虚拟化。
- 当前取消已向 fetch 传播；后端若已完成不可撤销计算，前端仍会丢弃其迟到结果，不把旧结果写回当前输入。
- 仓库未配置 Storybook，未伪造其结果；并发和回包行为由 Vitest 真实挂载测试覆盖。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-138 完成后自动读取并继续 RC-139。

## 回滚

- 需要回滚的本项文件：删除生成 client 的 AbortSignal 扩展、revision ref、待比较面板、重试 ref、专项测试和计划/追踪/证据登记；恢复优化回包无条件应用行为。不回滚 RC-135 至 RC-137 的状态、Tooltip 和快照边界。
