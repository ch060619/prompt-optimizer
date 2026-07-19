# RC-076 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075
- 修改文件：`backend/rabbit_code/mcp.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc076_mcp.py`
- 用户可见行为：支持 stdio 与 Streamable HTTP MCP 传输抽象、用户/项目配置合并、初始化和工具发现、统一工具 Schema、认证校验、断连重试、取消和关闭；未授权服务器的写工具不会自动执行。
- 风险与假设：stdio 通过 `shell=False` 启动并在关闭时 terminate/kill；HTTP 使用注入的 `httpx.Client`；MCP 协议版本和完整 Streamable HTTP 会话扩展留在当前 v1 边界内，真实官方服务器矩阵留给后续测试 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc076_mcp.py` | PASS：5 passed | `backend/tests/test_rc076_mcp.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py` | PASS：43 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/mcp.py backend/rabbit_code/__init__.py backend/tests/test_rc076_mcp.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：59 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：152 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 152 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-076/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-076 测试，并恢复本项对 `mcp.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-075 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。真实官方 MCP 服务器矩阵、跨进程故障演练、认证刷新和 UI/MCP 配置留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
