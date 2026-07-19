# RC-142 执行证据

- RC ID: RC-142
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-141
- 修改文件：`backend/src/prompt_optimizer/core/structure.py`、`backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/src/prompt_optimizer/providers/openai.py`、`backend/tests/test_rc142_structured_input.py`

## 已交付

- 新增 `StructuredPrompt` 解析器，识别并保护代码围栏、内联代码、文件提及、附件 token、命令、`{{variable}}` 占位符和用户指定输出格式行。
- 非流式优化在发送 Provider 前将结构化片段替换为不可变标记，返回后验证标记数量、唯一性和原始值，再恢复原文；失败时抛出可恢复错误且不创建版本。
- 流式优化复用同一保护与校验边界，结构化结果通过校验后才向客户端发送可见 chunks，失败时只发送错误事件，不发送完成事件。
- OpenAI-compatible Provider 的系统提示明确要求逐个原样保留保护标记；前端复用现有错误状态显示“结果未采用，请重试”。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc142_structured_input.py -q` | PASS：6 passed；覆盖结构识别、保护/恢复、未闭合代码围栏、非流式拒绝和流式成功/失败 | `backend/tests/test_rc142_structured_input.py` |
| `python -m pytest backend/tests/test_api.py::test_api_optimize_stream_can_use_provider_chunks backend/tests/test_rc142_structured_input.py -q` | PASS：7 passed；确认既有无结构化流式 chunk 边界不回归 | `backend/tests/test_api.py`、`backend/tests/test_rc142_structured_input.py` |
| `python -m pytest backend/tests/test_core.py backend/tests/test_api.py backend/tests/test_providers.py backend/tests/test_offline_fallback_contract.py backend/tests/test_rc141_metadata.py backend/tests/test_rc142_structured_input.py -q` | PASS：38 passed、23 warnings；核心/API/Provider/fallback/RC-141/RC-142 回归通过 | 对应 backend tests |
| `python -m ruff check backend/src/prompt_optimizer/core/structure.py backend/src/prompt_optimizer/services.py backend/src/prompt_optimizer/api/app.py backend/src/prompt_optimizer/providers/openai.py backend/tests/test_rc142_structured_input.py` | PASS：无 Ruff 问题 | 对应源文件和测试 |
| `python -m mypy backend/src/prompt_optimizer/core/structure.py backend/src/prompt_optimizer/services.py backend/src/prompt_optimizer/api/app.py backend/src/prompt_optimizer/providers/openai.py backend/tests/test_rc142_structured_input.py` | PASS：5 source files 无类型问题 | 对应源文件和测试 |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、视觉/Token/路由覆盖、交付计划、Ruff、前端 lint、Mypy、后端 289 passed/5 skipped/37 warnings、前端 17 test files/75 passed、build 全部通过 | 根级工作区门禁 |

## 未解决项与后续

- Provider 仍可能返回无法保留保护标记的结果；系统会拒绝该结果并要求重试，不自动采用或保存。
- 真实云 Provider、附件上传协议和跨平台实机矩阵不属于本项；附件 token 以提示词中的稳定 token 形式保护。
- 既有迁移 `DeprecationWarning`、前端 jsdom navigation warning 和环境相关 skip 按原计划保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出以及 RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-142 完成后自动读取并继续 RC-143。

## 回滚

- 删除 `StructuredPrompt` 保护/校验模块、服务层和流式路径的结构门禁、Provider 标记说明、专项测试及本证据和计划登记；保留 RC-141 的 Provider metadata 与脱敏实现。
