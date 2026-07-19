# RC-149 执行证据

- RC ID: RC-149
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-148
- 修改文件：`backend/src/prompt_optimizer/core/models.py`、`backend/src/prompt_optimizer/providers/local.py`、`backend/src/prompt_optimizer/providers/registry.py`、`backend/src/prompt_optimizer/providers/__init__.py`、`backend/src/prompt_optimizer/services.py`、`frontend/src/localModels.tsx`、`frontend/src/App.tsx`、`frontend/src/generated/client.ts`、`frontend/src/generated/schema.ts`、`backend/tests/test_rc149_local_model.py`、`frontend/tests/LocalModels.test.tsx`

## 已交付

- 新增无网络 `LocalModelProvider` 和 `LocalModelRunner` 协议，runner health、单次生成和流式 chunk 均通过 Adapter 注入，默认未配置 runner 明确报告 unavailable。
- `ProviderRegistry` 注册 local Provider；PromptOptimizationService 读取 local route 并通过现有 Loopback FastAPI 优化入口生成结果，取消仍由统一服务传播。
- 本地模型加载后写入 workspace-scoped local route、模型 ID 和 runner health；GUI 优化请求因此可传递 `provider=local` 与 Gemma/Qwen 模型 ID。
- local Provider 不创建云端 HTTP client；未就绪时返回受控 Provider 错误，交由既有 fallback 路径处理，细化的 RC-150 降级文案留待下一项。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc149_local_model.py backend/tests/test_rc148_provider_selection.py backend/tests/test_rc146_persistence.py backend/tests/test_api.py -q` | PASS：23 passed、15 warnings；覆盖本地 runner 生成、流式 chunk、local metadata、RC-148 选择和现有 API 回归 | `backend/tests/test_rc149_local_model.py` |
| `npm --prefix frontend test -- --run tests/LocalModels.test.tsx tests/PromptHistory.test.tsx tests/ProviderModels.test.tsx` | PASS：8 passed；覆盖本地 runner 生命周期、route persistence、provider/model 请求传递 | `frontend/tests/LocalModels.test.tsx`、`frontend/tests/PromptHistory.test.tsx`、`frontend/tests/ProviderModels.test.tsx` |
| `python -m ruff check backend/src/prompt_optimizer/providers backend/src/prompt_optimizer/services.py backend/tests/test_rc149_local_model.py` | PASS：无 Ruff 问题 | 对应后端源文件和测试 |
| `python -m mypy backend/src/prompt_optimizer/providers/local.py backend/src/prompt_optimizer/providers/registry.py backend/src/prompt_optimizer/services.py backend/tests/test_rc149_local_model.py` | PASS：无类型问题 | 对应后端源文件和测试 |
| `python scripts/generate_api.py --check` | PASS：`local` Provider 枚举和生成客户端/schema 无 drift | `docs/api/openapi-v1.json`、`frontend/src/generated/` |
| `python scripts/workspace.py verify` | PASS：后端 309 passed、5 skipped、39 warnings；前端 19 test files、82 passed；生成、追踪、依赖、类型、Lint 和 Build 门禁通过 | 根级工作区门禁 |

## 未解决项与后续

- 默认安装不携带模型权重，也不启动真实 Gemma/Qwen runtime；真实 runner 进程、模型目录和硬件 Adapter 留给本地模型安装任务。
- runner 未安装、未就绪、OOM、超时和修复入口的用户可见降级细节留给 RC-150。
- 既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-149 完成后自动进入 RC-150。

## 回滚

- 删除 local Provider/runner 协议、ProviderRegistry 注册、local route 持久化、API 枚举生成改动、专项测试和证据登记；保留 RC-148 云端选择与健康回退。
