# RC-081 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080
- 修改文件：`backend/rabbit_code/instructions.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc081_instructions.py`
- 用户可见行为：用户全局、项目根、目录级 `AGENTS.md`/`RABBIT.md`/`.rabbit-code/instructions.md` 按稳定优先级合并并返回来源；项目外工作目录被拒绝，项目级符号链接越界文件不读取，指令内容从不自动执行。
- 风险与假设：全局指令文件由调用方显式提供；项目指令仅沿项目根到工作目录路径加载；具体内容解析、冲突策略和执行授权留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc081_instructions.py` | PASS：2 passed | `backend/tests/test_rc081_instructions.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py backend/tests/test_rc080_project_context.py backend/tests/test_rc081_instructions.py` | PASS：60 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/instructions.py backend/rabbit_code/__init__.py backend/tests/test_rc081_instructions.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：64 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：169 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 169 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-081/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-081 测试，并恢复本项对 `instructions.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-080 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。指令内容解析、项目配置优先级、冲突解释和执行授权留给后续 RC-082/权限 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
