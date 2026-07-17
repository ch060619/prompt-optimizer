# RC-049 执行证据

- RC ID: RC-049
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`267f3f0`
- 实现 Commit：`78f2f19`
- 前置 RC：RC-045（证据完成提交 `6fc3f39`，收尾提交 `267f3f0`）；RC-046 至 RC-048 已完成
- 修改文件：`backend/src/prompt_optimizer/providers/base.py`、`backend/src/prompt_optimizer/providers/openai.py`、`backend/src/prompt_optimizer/providers/http.py`、`backend/src/prompt_optimizer/providers/offline.py`、`backend/src/prompt_optimizer/providers/registry.py`、`backend/src/prompt_optimizer/providers/__init__.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/tests/test_providers.py`、`backend/tests/test_api.py`

## 交付

- 定义可运行时检查的 `ModelProvider` Protocol、`ProviderCapabilities` 和统一 `ProviderEvent` 生命周期（`started`、`delta`、`completed`）。
- 将现有 HTTP 实现拆为明确的 `OpenAICompatibleAdapter`；旧 `HttpChatProvider` 导入路径保留为兼容别名。
- OpenAI-compatible 解析器只接受 Chat Completions 的 `choices[0].message.content` 和流式 `choices[0].delta.content`，不再猜测 `output` 等其他协议。
- `OfflineRuleProvider` 保留原有规则优化结果、无网络属性和最终降级行为，流式输出改用统一 Provider 事件；API 继续生成原有 SSE `chunk` 事件。
- Provider Registry 对兼容端点明确创建 `OpenAICompatibleAdapter`；新增 adapter 的契约验证不修改 `core/optimizer.py` 或其他优化核心文件。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_providers.py -q` | FAIL（预期）：新契约测试在收集阶段发现 `ProviderEventType` 和 `providers.openai` 尚未实现 |
| `python -m pytest backend/tests/test_providers.py -q` | PASS：9 passed；离线与 OpenAI-compatible Mock 契约、旧别名、Registry 和协议拒绝行为通过 |
| `python -m pytest backend/tests/test_api.py backend/tests/test_offline_fallback_contract.py -q` | PASS：17 passed；SSE、离线降级和统一事件边界通过 |
| `python -m pytest backend/tests -q` | PASS：69 passed；保留既有数据目录迁移 DeprecationWarning |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src` | PASS：37 个源码文件无问题 |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 |
| `npm --prefix frontend run lint` | PASS |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 |
| `python scripts/check_delivery_plan.py` | PASS：RC-001..RC-310 工作包字段和日期依赖有效 |
| `git diff --check` | PASS |

## 范围与决策

- 本 RC 只建立共享 Provider 边界并交付 OpenAI-compatible HTTP adapter；没有真实 API 请求、API Key、付费资源或外部服务依赖，所有 HTTP 行为使用 `httpx.MockTransport`。
- Gemini、Anthropic 原生协议和本地模型运行器不通过通用解析器猜测；它们沿用共享协议，分别留给清单中后续原生协议/本地运行器 RC。
- `ModelRequest`、`ModelResponse`、现有优化器和 API 响应 DTO 保持兼容；事件只在 Provider 到 SSE 的内部边界转换。

## 回滚与遗留问题

回滚本项使用 `78f2f19` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。原生 Gemini、Anthropic 和本地 Adapter 尚未实现，不伪造真实连接验收，按后续 RC 继续。

## 环境

- 时间：2026-07-17 15:11:51 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
