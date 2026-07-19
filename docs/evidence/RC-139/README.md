# RC-139 执行证据

- RC ID: RC-139
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-138
- 修改文件：`frontend/src/App.tsx`、`frontend/src/taskWorkspace.tsx`、`frontend/src/styles.css`、`frontend/tests/App.test.tsx`、`frontend/tests/TaskWorkspace.test.tsx`、`docs/evidence/RC-139/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 优化完成后先显示 `Optimization preview` 可编辑文本框，不自动写回原输入，不自动提交任务或对话消息。
- 提供“采用优化结果”和“保留原文”两个显式动作；只有采用动作才把预览内容写回提示词输入并生成新的 revision。
- TaskWorkspace 发送按钮保留独立 `type="submit"` 和 `data-action="send-task"`；优化按钮是 `type="button"`，不会触发表单提交。
- 预览区域使用固定边界、可调整高度和独立操作行，为 RC-140 的结构化 diff/部分采用/撤销留出明确状态边界。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/App.test.tsx tests/PromptOptimizeButton.test.tsx tests/TaskWorkspace.test.tsx` | PASS：3 test files、23 tests passed；覆盖预览编辑、采用/保留原文、tasks 发送路径为 0、优化按钮不提交和 TaskWorkspace 发送行为 | `frontend/tests/App.test.tsx`、`frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/TaskWorkspace.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题；保留 TypeScript 5.9 与 typescript-estree 支持范围提示 | `frontend/src/`、`frontend/tests/` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 16 test files、71 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-139/README.md` |

## 未解决项与后续

- 本项已完成单一预览、整段采用和保留原文；部分采用、结构化行内/并排 diff、复制、撤销/恢复和长文本虚拟化留给 RC-140。
- 当前“发送”验证的是现有 TaskWorkspace 发送路径未被优化入口触发；完整 Agent 发送语义和优化结果进入任务对话留给后续工作流 RC。
- 仓库未配置 Storybook，未伪造其结果；预览与发送隔离由 Vitest 真实挂载测试覆盖。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-139 完成后自动读取并继续 RC-140。

## 回滚

- 需要回滚的本项文件：删除优化预览状态、采用/保留动作、发送 action 标记、专项测试和计划/追踪/证据登记；恢复只读 `pre` 结果展示。不回滚 RC-138 的 revision/取消保护。
