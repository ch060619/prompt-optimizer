# RC-103 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-097、RC-102
- 修改文件：`backend/rabbit_code/slash_commands.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc103_slash_commands.py`、`docs/traceability/rc-index.md`
- 用户可见行为：SlashCommandRegistry 定义并校验命令参数、描述、session 影响和 handler；默认提供 help/model/provider/permission/plan/context/session/clear/compact/mcp/plugin/doctor/exit；自动生成帮助和补全，未知命令给近似建议，引用参数按 shell 规则解析，exit 返回结构化终止标记。
- 风险与假设：本项冻结命令协议和注册表，不伪造真实 Agent/Provider/MCP/Plugin 业务执行；各命令的业务 handler 接线留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc103_slash_commands.py -q` | PASS：4 passed | `backend/tests/test_rc103_slash_commands.py` |
| `python -m ruff check backend/rabbit_code/slash_commands.py backend/tests/test_rc103_slash_commands.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：85 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 256 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-103/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-103 测试，并恢复本项对 `slash_commands.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-102 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实 slash command 业务 handler、TUI 交互接线和更广命令参数验证留给后续 RC；RC-057/060 外部确认仍 pending。
