# RC-084 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083
- 修改文件：`backend/rabbit_code/context_budget.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc084_context_budget.py`
- 用户可见行为：上下文块按必需指令、当前任务、相关文件、历史分层分配 Token；重复内容去重，超限块生成带来源的结构化摘要，保留估算 Token、压缩状态、去重数和警告。
- 风险与假设：Token 估算采用 UTF-8 字节/4 的保守近似，结构化摘要为本地确定性预览，不声称等同 Provider tokenizer；真实模型 tokenizer、质量基准和持久缓存留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc084_context_budget.py` | PASS：2 passed | `backend/tests/test_rc084_context_budget.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py backend/tests/test_rc080_project_context.py backend/tests/test_rc081_instructions.py backend/tests/test_rc082_context_items.py backend/tests/test_rc083_search_index.py backend/tests/test_rc084_context_budget.py` | PASS：65 passed，1 skipped | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/context_budget.py backend/rabbit_code/__init__.py backend/tests/test_rc084_context_budget.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：67 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：174 passed，1 skipped，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 174 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-084/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-084 测试，并恢复本项对 `context_budget.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-083 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。真实 tokenizer、压缩质量基准、持久上下文缓存和跨 Provider 预算协调留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
