# RC-079 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078
- 修改文件：`backend/rabbit_code/public_output.py`、`backend/rabbit_code/prototype_app.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc079_public_output.py`
- 用户可见行为：Provider/事件公开输出递归过滤隐藏 reasoning/thinking/chain-of-thought 字段；日志只包含固定状态、预定义进度、允许的 Token/费用/延迟和最多 240 字符依据；SSE 原型事件也经过同一过滤器。
- 风险与假设：过滤器按字段名隔离隐藏推理，不判断普通文本语义；原始 Provider 响应不应绕过公开输出边界直接写日志/导出，新增输出路径必须调用 `safe_json_dumps` 或 `sanitize_public_payload`。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc079_public_output.py` | PASS：3 passed | `backend/tests/test_rc079_public_output.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py` | PASS：56 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/public_output.py backend/rabbit_code/prototype_app.py backend/rabbit_code/__init__.py backend/tests/test_rc079_public_output.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：62 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：165 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 165 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-079/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-079 测试，并恢复本项对 `public_output.py`、`prototype_app.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-078 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。语义级隐藏内容检测、第三方 Provider 原始响应审计和全量导出路径检查留给后续安全/隐私 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
