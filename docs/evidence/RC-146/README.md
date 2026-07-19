# RC-146 执行证据

- RC ID: RC-146
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-145
- 修改文件：`backend/src/prompt_optimizer/core/models.py`、`backend/src/prompt_optimizer/storage/service.py`、`backend/src/prompt_optimizer/storage/version_service.py`、`backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/src/prompt_optimizer/contracts.py`、`frontend/src/App.tsx`、`frontend/src/api.ts`、`frontend/src/settings.tsx`、`frontend/src/generated/client.ts`、`frontend/src/generated/schema.ts`、`frontend/src/components/PromptOptimizationDiff.tsx`、`frontend/src/styles.css`、`backend/tests/test_rc146_persistence.py`、`frontend/tests/PromptHistory.test.tsx`

## 已交付

- `prompt_versions` 持久化原文、优化结果、采用状态、采用时间、Provider、模型和创建时间，并通过兼容迁移补齐旧数据库字段。
- `OptimizeRequest.save_prompt_history` 贯穿非流式、SSE 流式和后台任务；关闭时仍返回分析/优化结果和 Provider metadata，但不写入版本历史。
- 新增历史版本采用和删除 API，删除与采用均按当前用户隔离。
- Settings 的 workspace-scoped `Save prompt history` 开关控制三条优化入口；结果的整段采用和选区采用都会持久化采用状态。
- 历史列表显示采用状态、Provider、模型并支持删除；删除后刷新列表并清理当前 diff/版本状态。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc146_persistence.py -q` | PASS：4 passed、1 warning；覆盖保存开关、非流式/流式/后台内存结果、采用、删除、元数据时间戳和用户隔离 | `backend/tests/test_rc146_persistence.py` |
| `npm --prefix frontend test -- --run tests/PromptHistory.test.tsx` | PASS：2 passed；覆盖 workspace 保存开关贯穿三条请求、整段/选区采用调用、Provider/模型展示和删除 | `frontend/tests/PromptHistory.test.tsx` |
| `python scripts/generate_api.py --check` | PASS：OpenAPI、生成客户端和 schema 无 drift | `docs/api/openapi-v1.json`、`frontend/src/generated/` |
| `python scripts/generate_v2_regression_baseline.py --approve-rc RC-146 --reason "Persist accepted/provider/model fields in PromptVersion JSON exports as part of RC-146 history persistence." --migration-note docs/evidence/RC-146/README.md` | PASS：approved baseline 显式记录 RC-146 的 PromptVersion 导出字段变化 | `backend/tests/golden/v2_regression.json` |
| `python scripts/workspace.py verify` | PASS：后端 301 passed、5 skipped、39 warnings；前端 19 test files、81 passed；根级生成、追踪、依赖边界、Ruff、Mypy、Lint 和 Build 均通过 | 根级工作区门禁 |

## 未解决项与后续

- 关闭历史保存只影响优化版本历史；当前请求的内存结果仍会在当前页面显示，跨刷新不恢复。
- Provider 原生 token/cost 遥测、历史保留期和全量清理留给后续数据治理任务。
- 既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-146 完成后自动进入 RC-147。

## 回滚

- 回退 RC-146 的 schema/API、版本存储字段、前端设置与历史动作、专项测试和证据登记；恢复 approved v2 baseline 前需保留迁移说明并由对应 RC 明确批准。
