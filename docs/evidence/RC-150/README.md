# RC-150 执行证据

- RC ID: RC-150
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-149
- 修改文件：`backend/src/prompt_optimizer/providers/local.py`、`backend/src/prompt_optimizer/providers/__init__.py`、`backend/src/prompt_optimizer/public.py`、`backend/src/prompt_optimizer/core/models.py`、`backend/src/prompt_optimizer/services.py`、`backend/tests/test_rc149_local_model.py`、`frontend/src/App.tsx`、`frontend/src/generated/schema.ts`、`frontend/src/generated/client.ts`、`docs/evidence/RC-150/README.md`

## 已交付

- local runner health 增加未安装、未就绪、资源不足和超时状态；runner 的 `MemoryError`、超时、文件缺失和显式 health 状态均转换为可审计的本地故障类别。
- 只有上述 `LocalModelFailure` 类别允许切换 `OfflineRuleProvider`；普通 local `RuntimeError` 不再静默降级。
- 优化响应和流式 fallback 事件写入 `fallback_reason`、`recovery_action` 与专用错误码；离线结果明确标识为 `离线规则`，不伪装成模型输出。
- UI 读取持久化的 `local` route，并在离线降级 metadata 中显示原因和本地模型安装/修复入口。

## 专项验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc149_local_model.py backend/tests/test_rc141_metadata.py backend/tests/test_rc148_provider_selection.py -q` | PASS：16 passed、3 warnings；覆盖四类 health 故障、OOM/超时注入、流式 timeout fallback、普通 RuntimeError 不降级 | `backend/tests/test_rc149_local_model.py` |
| `npm --prefix frontend test -- --run tests/App.test.tsx tests/LocalModels.test.tsx` | PASS：2 test files、18 passed；覆盖离线规则身份、降级原因和安装/修复入口 | `frontend/tests/App.test.tsx`、`frontend/tests/LocalModels.test.tsx` |
| `python -m ruff check ...` | PASS：无 Ruff 问题 | RC-150 修改的后端源文件和测试 |
| `python -m mypy ...` | PASS：6 个目标文件无类型问题 | RC-150 修改的后端源文件和测试 |
| `python scripts/generate_api.py --check` | PASS：OpenAPI 与生成客户端/schema 无 drift | `docs/api/openapi-v1.json`、`frontend/src/generated/` |

## 根级验证

`python scripts/workspace.py verify`：PASS。后端 318 passed、5 skipped、39 warnings；前端 19 test files、82 passed；生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁、Ruff、Mypy、Lint 和 Vite Build 全部通过。既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 如实保留。

## 未解决项与后续

- 默认安装不携带模型权重，也不启动真实 Gemma/Qwen runtime；真实 runner 进程、模型目录和硬件 Adapter 仍留给本地模型安装任务。
- RC-151 继续定义 Provider 路由韧性策略；RC-152 继续处理外部取消路由和 SSE 重连。
- RC-127/RC-121/RC-057/RC-060 外部条件仍 pending；既有迁移 DeprecationWarning 和前端 jsdom navigation warning 不阻塞本项。

## 回滚

- 删除 local runner 故障分类、fallback metadata 字段、local route 读取和对应专项测试；恢复 RC-149 的单一本地 unavailable fallback 行为。
