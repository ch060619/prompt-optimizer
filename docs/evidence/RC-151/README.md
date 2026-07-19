# RC-151 执行证据

- RC ID: RC-151
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-150
- 修改文件：`backend/src/prompt_optimizer/providers/base.py`、`backend/src/prompt_optimizer/providers/__init__.py`、`backend/src/prompt_optimizer/providers/registry.py`、`backend/src/prompt_optimizer/providers/openai.py`、`backend/src/prompt_optimizer/public.py`、`backend/src/prompt_optimizer/services.py`、`backend/tests/test_rc151_routing_resilience.py`

## 已交付

- 环境 Provider 配置保持 `RABBIT_CODE_*` 优先于旧兼容名称；云 Provider 必须显式设置对应 `RABBIT_CODE_<PROVIDER>_AUTHORIZED=true`，否则路由健康为 unavailable，Adapter 在 HTTP 前置检查拒绝请求。
- Provider 配置支持超时、重试、限流和熔断参数；OpenAI-compatible Adapter 实现 closed/open/half-open 状态，熔断打开时不发 HTTP 请求，恢复窗口后成功请求关闭熔断。
- 统一服务为每次普通优化生成 request ID，流式优化沿用流 ID；Adapter 重试复用同一 `Idempotency-Key`，取消事件在请求和流式读取过程中传播且不会被当成可回退 Provider 错误。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc151_routing_resilience.py backend/tests/test_providers.py backend/tests/test_rc149_local_model.py -q` | PASS：26 passed；覆盖未授权零 HTTP、同 ID 重试、熔断 open/half-open/closed、熔断窗口阻断、取消和环境授权 | `backend/tests/test_rc151_routing_resilience.py` |
| `python -m ruff check ...` | PASS：无 Ruff 问题 | RC-151 修改的后端源文件和测试 |
| `python -m mypy ...` | PASS：7 个目标文件无类型问题 | RC-151 修改的后端源文件和测试 |
| `python scripts/workspace.py verify` | PASS：后端 324 passed、5 skipped、39 warnings；前端 19 test files、82 passed；生成、追踪、依赖、Lint、Mypy、Build 和全部工作区门禁通过 | 根级工作区门禁 |

## 未解决项与后续

- 当前云 Provider 仍使用 OpenAI-compatible 单请求协议；更细粒度的 Provider 原生限流/cost 遥测、持久熔断账本和真实跨进程取消留给后续任务。
- RC-152 继续处理 started/analysis/delta/saved/completed/cancelled/error 事件契约和 SSE 重连去重。
- RC-127/RC-121/RC-057/RC-060 外部条件仍 pending；既有迁移 DeprecationWarning 和前端 jsdom navigation warning 不阻塞本项。

## 回滚

- 删除授权字段、熔断状态、Provider 取消/幂等字段、服务 request ID 接线和 RC-151 测试；恢复 RC-150 的现有 Provider 重试与限流行为。
