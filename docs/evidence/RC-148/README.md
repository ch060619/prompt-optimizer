# RC-148 执行证据

- RC ID: RC-148
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-147
- 修改文件：`backend/src/prompt_optimizer/core/models.py`、`backend/src/prompt_optimizer/providers/registry.py`、`backend/src/prompt_optimizer/providers/__init__.py`、`backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/storage/service.py`、`backend/src/prompt_optimizer/storage/version_service.py`、`backend/src/prompt_optimizer/contracts.py`、`backend/src/prompt_optimizer/api/app.py`、`frontend/src/api.ts`、`frontend/src/App.tsx`、`frontend/src/providerModels.tsx`、`frontend/src/generated/client.ts`、`frontend/src/generated/schema.ts`、`backend/tests/test_rc148_provider_selection.py`、`frontend/tests/ProviderModels.test.tsx`、`frontend/tests/PromptHistory.test.tsx`

## 已交付

- OptimizeRequest 支持会话 model 和独立 optimizer provider/model；`ProviderRegistry.resolve` 按 session/default → optimizer 覆盖优先级解析。
- 独立优化器先做可用性检查；覆盖不可用时回到健康的会话/default 路由，并标记 `provider_health=fallback`，不静默选择未授权云 Provider。
- metadata 与 PromptVersion/VersionSummary 保存 `selection_scope` 和 `provider_health`，模型切换立即反映到优化结果和历史。
- Provider 页面把受支持的 workspace provider/model 选择保存到 workspace-scoped localStorage；GUI 三条优化入口读取并传递该 session route。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc148_provider_selection.py backend/tests/test_rc146_persistence.py backend/tests/test_api.py backend/tests/test_storage_export.py -q` | PASS：25 passed、15 warnings；覆盖健康 optimizer 覆盖、不可用回退、API metadata 和版本持久化 | `backend/tests/test_rc148_provider_selection.py` |
| `npm --prefix frontend test -- --run tests/PromptHistory.test.tsx tests/ProviderModels.test.tsx` | PASS：5 passed；覆盖 workspace route 持久化和三条优化请求的 provider/model 传递 | `frontend/tests/PromptHistory.test.tsx`、`frontend/tests/ProviderModels.test.tsx` |
| `python -m ruff check backend/src/prompt_optimizer backend/tests/test_rc148_provider_selection.py` | PASS：无 Ruff 问题 | 对应后端源文件和测试 |
| `python -m mypy backend/src/prompt_optimizer/core/models.py backend/src/prompt_optimizer/storage/service.py backend/src/prompt_optimizer/storage/version_service.py backend/src/prompt_optimizer/providers/registry.py backend/src/prompt_optimizer/services.py backend/src/prompt_optimizer/api/app.py backend/tests/test_rc148_provider_selection.py` | PASS：无类型问题 | 对应后端源文件和测试 |
| `python scripts/generate_v2_regression_baseline.py --approve-rc RC-148 --reason "Persist provider selection scope and health in PromptVersion exports as part of RC-148 routing." --migration-note docs/evidence/RC-148/README.md` | PASS：approved baseline 显式记录 RC-148 的历史导出字段变化 | `backend/tests/golden/v2_regression.json` |
| `python scripts/workspace.py verify` | PASS：后端 307 passed、5 skipped、39 warnings；前端 19 test files、82 passed；根级所有生成、追踪、依赖、类型、Lint、测试和 Build 门禁通过 | 根级工作区门禁 |

## 未解决项与后续

- 当前可用性检查验证配置完整性和注入 Provider 健康标记，不执行真实云端连接；真实连接健康探测留给 Provider 契约任务。
- Provider 自定义名称的统一协议注册、独立优化器持久化编辑器和选择询问 UI 留给后续 Provider 管理任务。
- 本地模型 Adapter 和离线降级细化留给 RC-149/RC-150。
- 既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-148 完成后自动进入 RC-149。

## 回滚

- 删除 request model/optimizer 字段、ProviderRegistry selection、selection metadata/storage 列、前端 route persistence、专项测试和证据登记；恢复上一版 RC-146 approved baseline 前保留迁移说明。
