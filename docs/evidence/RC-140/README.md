# RC-140 执行证据

- RC ID: RC-140
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-139
- 修改文件：`frontend/src/components/PromptOptimizationDiff.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/PromptOptimizationDiff.test.tsx`、`frontend/tests/App.test.tsx`、`docs/evidence/RC-140/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 新增结构化逐行 diff 视图，支持 inline 与 side-by-side 模式，并对相同、变更、删除、增加行使用独立状态。
- 长文本视图只挂载带 overscan 的可视窗口；专项测试覆盖 1000 行输入不会一次挂载全部行。
- 优化结果保持可编辑，支持复制、整段替换、选区替换、重试、撤销和恢复原文；选区替换会将未选行保留为原文、选中行采用优化结果并写回当前输入。
- 复制动作使用浏览器剪贴板 API，成功后提供状态播报；既有发送动作仍由用户显式触发。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizationDiff.test.tsx tests/App.test.tsx` | PASS：2 test files、16 tests passed；覆盖 inline/side-by-side、选区替换回调、复制、整段替换、撤销、恢复、重试、长文本窗口和优化预览写回 | `frontend/tests/PromptOptimizationDiff.test.tsx`、`frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/components/PromptOptimizationDiff.tsx`、`frontend/src/App.tsx` |
| `npm --prefix frontend run build` | PASS：TypeScript 编译和 Vite production build 通过 | `frontend/src/components/PromptOptimizationDiff.tsx` |
| `python scripts/workspace.py verify` | PASS：追踪、依赖边界、route coverage、设计 token、交付计划和生成 drift 校验通过；后端 281 passed、5 skipped、31 warnings；前端 17 test files、74 passed；Ruff/Mypy、Lint、Build 均通过 | `docs/evidence/RC-140/README.md` |

## 未解决项与后续

- 当前 diff 以行号对齐，长行使用可换行的行视图；更精细的词级 diff 和结构化输入保护留给 RC-142。
- 仓库未配置 Storybook，未伪造其结果；交互由 Vitest 真实挂载测试覆盖。
- 既有前端 jsdom navigation warning、迁移 DeprecationWarning 和 5 个环境相关 skip 如实保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-140 完成后自动读取并继续 RC-141。

## 回滚

- 需要回滚的本项文件：删除 `PromptOptimizationDiff`、选区合并回调、专项断言和 RC-140 计划/追踪/证据登记；恢复 RC-139 的单一可编辑预览。不回滚 RC-135 至 RC-139 的优化请求、取消保护和发送隔离。
