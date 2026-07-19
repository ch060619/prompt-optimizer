# RC-083 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082
- 修改文件：`backend/rabbit_code/search_index.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc083_search_index.py`
- 用户可见行为：安全索引合并 `.gitignore`、`.rabbitignore` 和用户排除；敏感文件、二进制、大文件和符号链接不进入索引；未变化文件复用缓存，扫描支持取消，文本搜索只访问已索引内容。
- 风险与假设：当前忽略匹配覆盖常见 glob/目录规则；Windows 无创建符号链接权限时对应夹具跳过，代码仍在运行时显式拒绝 symlink；完整 Git ignore 语义和文件监视器留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc083_search_index.py` | PASS：1 passed；1 skipped（Windows symlink 创建不可用） | `backend/tests/test_rc083_search_index.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py backend/tests/test_rc079_public_output.py backend/tests/test_rc080_project_context.py backend/tests/test_rc081_instructions.py backend/tests/test_rc082_context_items.py backend/tests/test_rc083_search_index.py` | PASS：63 passed，1 skipped | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/search_index.py backend/rabbit_code/__init__.py backend/tests/test_rc083_search_index.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：66 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：172 passed，1 skipped，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 172 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-083/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-083 测试，并恢复本项对 `search_index.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-082 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。完整 gitignore 语义、文件监视器、磁盘活动基准和 Linux/Windows symlink 矩阵留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
