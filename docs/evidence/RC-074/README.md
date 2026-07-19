# RC-074 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073
- 修改文件：`backend/rabbit_code/subagents.py`、`backend/rabbit_code/budget.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc074_subagents.py`
- 用户可见行为：主 Agent 可并行创建受控子任务；每个子任务获得深拷贝上下文、父级权限以内的模式、独立预算和共享取消信号；管理器限制深度/并发，按输入顺序汇总结果并报告失败/取消任务。
- 风险与假设：执行器通过依赖注入接入，子任务不直接暴露创建子任务的管理器，因此递归深度由规格和管理器边界共同限制；真实 Provider/工具执行器接入留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc074_subagents.py` | PASS：4 passed | `backend/tests/test_rc074_subagents.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py` | PASS：33 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/subagents.py backend/rabbit_code/budget.py backend/rabbit_code/__init__.py backend/tests/test_rc074_subagents.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：57 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：142 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 142 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-074/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-074 测试，并恢复本项对 `subagents.py`、`budget.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-073 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。真实子 Agent Provider/工具编排、跨进程调度和 UI 展示留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
