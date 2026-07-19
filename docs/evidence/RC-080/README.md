# RC-080 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079
- 修改文件：`backend/rabbit_code/project_context.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc080_project_context.py`
- 用户可见行为：只读识别 Git 根目录、当前分支、未提交路径、语言、构建标记和明确的项目指令文件；Windows Git 输出使用 UTF-8 replacement 解码；依赖目录不参与语言/指令扫描，不自动执行任何项目命令。
- 风险与假设：Git 不可用或目录不是仓库时返回空 Git 信息但保留文件扫描；指令文件只登记路径，不读取或执行内容；构建工具按文件标记识别而非运行构建。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc080_project_context.py` | PASS：2 passed | `backend/tests/test_rc080_project_context.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py backend/tests/test_rc080_project_context.py` | PASS：58 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/project_context.py backend/rabbit_code/__init__.py backend/tests/test_rc080_project_context.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：63 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：167 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 167 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-080/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-080 测试，并恢复本项对 `project_context.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-079 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。指令内容解析、项目配置优先级和执行策略留给后续 RC-081/RC-082；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
