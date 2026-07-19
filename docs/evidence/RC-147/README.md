# RC-147 执行证据

- RC ID: RC-147
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-146
- 修改文件：`backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/src/prompt_optimizer/cli/app.py`、`backend/src/prompt_optimizer/evaluation/service.py`、`backend/tests/test_rc147_optimization_service.py`

## 已交付

- 在服务层建立唯一 `PromptOptimizationService.optimize/stream/cancel`，统一结构保护、语言校验、Provider 路由、fallback、metadata、结果分析和版本保存。
- API 普通优化、SSE 流式优化、后台任务、CLI 和评测均通过 `AppServices.optimization` 调用；AppServices 保留旧 wrapper 仅用于兼容既有调用，不再包含独立路由逻辑。
- API 流式入口只把服务事件编码为 SSE，移除 API 内重复的 Provider 拼接、降级和保存实现。
- `cancel(request_id)` 使用服务内 request id cancellation registry，在流生成进入终态前停止后续输出和保存。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc147_optimization_service.py -q` | PASS：3 passed、1 warning；覆盖普通/流式输出一致、取消、API 和后台任务复用统一契约 | `backend/tests/test_rc147_optimization_service.py` |
| `python -m ruff check backend/src/prompt_optimizer/services.py backend/src/prompt_optimizer/api/app.py backend/src/prompt_optimizer/cli/app.py backend/src/prompt_optimizer/evaluation/service.py backend/tests/test_rc147_optimization_service.py` | PASS：无 Ruff 问题 | 对应源文件和测试 |
| `python -m mypy backend/src/prompt_optimizer/services.py backend/src/prompt_optimizer/api/app.py` | PASS：2 source files 无类型问题 | 对应服务和 API |
| 生产代码搜索 `optimize_and_save` / `_stream_provider_result` | PASS：API、CLI、评测和任务入口均改为 `services.optimization`；旧 wrapper 只保留兼容接口 | `backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/api/app.py` |
| `python scripts/workspace.py verify` | PASS：后端 304 passed、5 skipped、39 warnings；前端 19 test files、81 passed；根级生成、追踪、依赖边界、Ruff、Mypy、Lint 和 Build 均通过 | 根级工作区门禁 |

## 未解决项与后续

- 当前取消服务方法已覆盖核心流生成；外部取消路由、SSE cancelled/reconnect 游标和客户端断线续传留给 RC-152。
- Provider 选择优先级、独立优化模型和本地模型 Adapter 留给 RC-148/RC-149。
- 既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-147 完成后自动进入 RC-148。

## 回滚

- 删除 `PromptOptimizationService`、服务事件和取消 registry，恢复 API 流式 helper 及各入口旧调用；保留 RC-146 的历史持久化和保存开关。
