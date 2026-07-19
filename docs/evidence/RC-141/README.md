# RC-141 执行证据

- RC ID: RC-141
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-140
- 修改文件：`backend/src/prompt_optimizer/core/models.py`、`backend/src/prompt_optimizer/public.py`、`backend/src/prompt_optimizer/services.py`、`backend/src/prompt_optimizer/api/app.py`、`backend/src/prompt_optimizer/providers/offline.py`、`backend/src/prompt_optimizer/providers/openai.py`、`backend/tests/test_rc141_metadata.py`、`frontend/src/App.tsx`、`frontend/src/publicOutput.ts`、`frontend/src/styles.css`、`frontend/src/generated/schema.ts`、`frontend/src/generated/client.ts`、`frontend/tests/App.test.tsx`、`docs/evidence/RC-141/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- Optimize metadata 现在包含 Provider 显示名、模型、`local/cloud`、fallback、耗时、错误码和密钥引用；密钥引用只表达配置引用名，不返回密钥值。
- 非流式、流式和后台任务共用同一组 metadata 字段；离线规则显示为本地规则 Provider，不伪装成模型。
- Provider 异常先映射为稳定错误码并通过脱敏器；API key、Bearer token、`system_prompt`/内部提示词和源码内容不会进入 public metadata。
- 前端 metadata 区域清晰显示 Provider、模型、运行位置、降级状态、耗时、错误码和安全的错误摘要；前端再做一次防御性脱敏。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc141_metadata.py backend/tests/test_offline_fallback_contract.py -q` | PASS：5 tests passed；覆盖本地 Provider metadata、fallback、错误码和含 API key/System Prompt 的恶意异常 | `backend/tests/test_rc141_metadata.py`、`backend/tests/test_offline_fallback_contract.py` |
| `npm --prefix frontend test -- --run tests/App.test.tsx` | PASS：14 tests passed；覆盖 metadata 展示和 secret-bearing error 不进入页面 | `frontend/tests/App.test.tsx` |
| `python -m ruff check backend/src/prompt_optimizer backend/tests/test_rc141_metadata.py` | PASS：无 Ruff 问题 | `backend/src/prompt_optimizer/public.py`、`backend/src/prompt_optimizer/services.py` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：91 source files 无类型问题 | `backend/src/prompt_optimizer/public.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、route coverage、设计 token 和交付计划校验通过；后端 283 passed、5 skipped、33 warnings；前端 17 test files、75 passed；Lint、Build 通过 | `docs/evidence/RC-141/README.md` |

## 未解决项与后续

- 当前错误脱敏覆盖 Provider 错误、credential assignment、Bearer token、常见 API key 和内部提示词标记；更广泛的结构化输入保护留给 RC-142。
- 仓库未配置 Storybook，未伪造其结果；metadata 和脱敏由 Vitest/API 专项测试覆盖。
- 既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 如实保留，不阻塞本项。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-141 完成后自动读取并继续 RC-142。

## 回滚

- 需要回滚的本项文件：删除 metadata 扩展字段、Provider 公开身份 helper、错误脱敏、前端 metadata 区域、专项测试和 RC-141 计划/追踪/证据登记；保留 RC-140 diff 交互。不回滚既有 Provider fallback 契约。
