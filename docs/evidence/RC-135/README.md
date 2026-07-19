# RC-135 执行证据

- RC ID: RC-135
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-134
- 修改文件：`frontend/src/components/PromptOptimizeButton.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/PromptOptimizeButton.test.tsx`、`docs/evidence/RC-135/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 新增固定尺寸的 `PromptOptimizeButton`，状态集合为 `idle`、`hover`、`pressed`、`loading`、`success`、`error`、`disabled`、`cancelling`。
- 使用请求 ID 和活动请求引用，旧请求完成或失败时不会回写当前按钮；重复点击只保留一个有效活动请求。
- 取消动作调用 `AbortController`，立即进入 `cancelling`，并在取消后的微任务中回到 `idle`；迟到的结果被请求 ID 丢弃。
- 将现有 Workspace 的主要优化入口接入该状态机；API 失败会同时保留页面错误信息并进入按钮 `error` 状态。
- 为 loading/cancelling、success、error 和 disabled 增加固定容器与主题状态样式，避免状态文本导致尺寸跳动。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizeButton.test.tsx tests/App.test.tsx` | PASS：2 test files、15 tests passed；组件 4 passed，App 11 passed；既有 jsdom navigation warning 保留 | `frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题；保留 TypeScript 5.9 与 typescript-estree 支持范围提示 | `frontend/src/`、`frontend/tests/` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 16 test files、66 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-135/README.md` |

## 未解决项与后续

- 仓库没有 Storybook 配置；本项没有伪造 Storybook 结果，使用 Vitest 真实挂载组件覆盖全部状态和转换。若建立 Storybook 环境，状态矩阵可直接复用该组件的 `data-state` 契约。
- Tooltip 与最终“优化输入内容”读屏文案、模型/附件/语音语义区分留给 RC-136；当前按钮保留基础 `aria-label` 和 `title` 以避免无名控件。
- 输入快照、空输入/附件/超长和已有任务边界留给 RC-137；并发编辑旧结果保护留给 RC-138。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-135 完成后自动读取并继续 RC-136。

## 回滚

- 需要回滚的本项文件：删除 `PromptOptimizeButton` 组件、专项测试、状态样式和计划/追踪/证据登记；恢复 App 优化按钮的直接 `withLoading` 调用。不回滚 RC-134 布局决策文档或 RC-133 视觉回归契约。
