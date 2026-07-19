# RC-137 执行证据

- RC ID: RC-137
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-136
- 修改文件：`frontend/src/components/PromptOptimizeButton.tsx`、`frontend/src/App.tsx`、`frontend/tests/PromptOptimizeButton.test.tsx`、`docs/evidence/RC-137/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 点击前复制不可变语义快照：原文、revision、光标起止位置和附件引用数组；实际优化 API 使用快照文本，而不是异步执行期间重新读取当前输入。
- 空文本在无附件时直接禁用按钮；只有附件时给出明确提示，不发起请求。
- 超过 `12000` 字符拒绝请求并保留原文，不静默截断；提示包含预算值，后续可在产品层增加用户选择。
- 已有活动请求继续使用 RC-135 的单请求/取消/请求 ID 保护；快照不写回输入框，原文可由调用方直接恢复。
- 记录 textarea 修改 revision 和 selection 范围；切换模板也会生成新的 revision 和光标位置。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizeButton.test.tsx tests/App.test.tsx` | PASS：2 test files、18 tests passed；覆盖空输入禁用、快照字段、只有附件、超长不截断、取消/重复点击、Tooltip 和现有 App 行为；保留既有 jsdom navigation warning | `frontend/tests/PromptOptimizeButton.test.tsx`、`frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题；保留 TypeScript 5.9 与 typescript-estree 支持范围提示 | `frontend/src/`、`frontend/tests/` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 16 test files、69 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-137/README.md` |

## 未解决项与后续

- 当前附件引用只有组件契约和测试夹具，真正附件控件与附件上传流程不在本项范围；已有任务的等待/取消仍由 RC-135 按钮状态承载。
- 并发编辑期间禁止旧快照覆盖新输入、结果比较/采用/撤销留给 RC-138 至 RC-140。
- 仓库未配置 Storybook，未伪造其结果；状态和边界由 Vitest 真实挂载测试覆盖。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-137 完成后自动读取并继续 RC-138。

## 回滚

- 需要回滚的本项文件：删除 snapshot 类型/边界校验、App revision/cursor 追踪、专项测试和计划/追踪/证据登记；恢复优化 API 读取组件外层 prompt 的行为。不回滚 RC-135 状态机和 RC-136 Tooltip/命名。
