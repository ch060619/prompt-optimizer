# RC-082 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081
- 修改文件：`backend/rabbit_code/context_items.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc082_context_items.py`
- 用户可见行为：文件、目录、代码选择、图片/附件、终端输出、diff 和诊断统一进入有界 ContextItem；路径限制在工作区内，依赖目录忽略，文本按 UTF-8 字节上限截断，二进制只记录安全元数据。
- 风险与假设：当前图片/附件只进入类型、MIME 和大小元数据，不自动读取二进制内容；更高层 Agent 上下文预算合并和实际多模态上传留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc082_context_items.py` | PASS：2 passed | `backend/tests/test_rc082_context_items.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py backend/tests/test_rc080_project_context.py backend/tests/test_rc081_instructions.py backend/tests/test_rc082_context_items.py` | PASS：62 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/context_items.py backend/rabbit_code/__init__.py backend/tests/test_rc082_context_items.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：65 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：171 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 171 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-082/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-082 测试，并恢复本项对 `context_items.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-081 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。真实多模态上传、附件解析、上下文压缩和跨模块预算协调留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
