# RC-136 执行证据

- RC ID: RC-136
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-135
- 修改文件：`frontend/src/components/PromptOptimizeButton.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx`、`docs/evidence/RC-136/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 优化按钮固定使用 `aria-label="优化输入内容"`，并设置 `data-action="prompt-optimize"`，不与发送等其他动作共用语义。
- 使用自定义延迟 Tooltip，鼠标悬停和键盘焦点均在 500ms 后显示；Tooltip 有 `role="tooltip"`，仅在可见时通过 `aria-describedby` 关联触发按钮。
- Tooltip 使用主题表面和固定层级，桌面 toolbar 从按钮上方显示，避免覆盖下方提示词输入；短标签保持单行，长文本受视口宽度限制。
- 保留发送按钮的独立提交语义；本项未把语音、附件或模型选择伪装成优化动作，后续 composer 控件沿用 RC-134 的分组契约。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizeButton.test.tsx tests/App.test.tsx` | PASS：2 test files、16 tests passed；Tooltip 专项 5 passed，App 专项 11 passed；保留既有 jsdom navigation warning | `frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题；保留 TypeScript 5.9 与 typescript-estree 支持范围提示 | `frontend/src/`、`frontend/tests/` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 16 test files、67 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-136/README.md` |

## 未解决项与后续

- 原生 axe CLI 仍受本机 Chrome/ChromeDriver 版本限制；RC-132 已完成同版本 axe-core 的 14 路由 × light/dark 审计，本项用组件可访问名称和 Tooltip 关联测试覆盖新增语义。
- 仓库未配置 Storybook，本项未伪造 Storybook 结果；Vitest 组件测试覆盖了 Tooltip 的延迟、鼠标、键盘、关联和隐藏行为。
- 输入快照、空输入/只有附件/超长/已有任务的边界处理留给 RC-137；并发编辑旧结果保护留给 RC-138。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-136 完成后自动读取并继续 RC-137。

## 回滚

- 需要回滚的本项文件：删除自定义 Tooltip、`aria-describedby`/`data-action` 语义、专项断言和计划/追踪/证据登记，恢复 RC-135 的基础名称/`title` 行为。不回滚 RC-135 状态机、RC-134 布局决策或 RC-133 视觉回归契约。
