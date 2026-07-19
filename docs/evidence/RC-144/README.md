# RC-144 执行证据

- RC ID: RC-144
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-143
- 修改文件：`frontend/src/components/PromptOptimizationControls.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/PromptOptimizationControls.test.tsx`

## 已交付

- 在 Composer 工具栏加入优化控制 Popover，模板选择与现有草稿/模板状态绑定，选择模板会写回当前输入并更新 revision/光标。
- 高级区使用原生 `details` 默认收起，提供场景、角色、优化强度和评分开关；关闭 Popover 不清除父页状态，控制语义在优化、流式和后台任务请求中复用。
- 在同一高级区提供历史版本列表和版本比较入口，调用现有 diff 服务，用户不离开任务页即可比较版本。
- 使用稳定宽度、移动端回流和图标按钮/Tooltip 样式，避免工具栏布局跳动；现有侧栏模板和右侧历史入口保持兼容。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/PromptOptimizationControls.test.tsx tests/App.test.tsx` | PASS：16 passed；覆盖 Popover 打开/关闭、高级区状态、模板选择、版本比较和既有 App 优化流程 | `frontend/tests/PromptOptimizationControls.test.tsx`、`frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/components/PromptOptimizationControls.tsx`、`frontend/src/App.tsx` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite build 通过 | `frontend/src/components/PromptOptimizationControls.tsx`、`frontend/src/App.tsx` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、视觉/Token/路由覆盖、交付计划、Ruff、前端 lint、Mypy、后端 297 passed/5 skipped/39 warnings、前端 18 test files/77 passed、build 全部通过 | 根级工作区门禁 |

## 未解决项与后续

- 控制值以优化请求中的控制语义参与当前 Provider；持久化优化参数、采用状态和历史删除留给 RC-146。
- 当前 Composer 保留既有三栏工作区；390px Review 三栏响应式问题仍留给 RC-255/256。
- 既有前端 jsdom navigation warning 和后端迁移/环境警告按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-144 完成后自动读取并继续 RC-145。

## 回滚

- 删除 `PromptOptimizationControls`、App 中的控制状态/请求语义、对应 CSS、专项测试及本证据和计划登记；保留 RC-143 语言保持和 RC-142 结构保护。
