# RC-075 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074
- 修改文件：`backend/rabbit_code/hooks.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc075_hooks.py`
- 用户可见行为：Hooks 覆盖 session/tool/permission/error 前后阶段，按优先级确定性执行；权限在执行前评估，Hook 可允许、拒绝或注入反馈；超时、异常和非法输出按失败策略记录审计，不令主 Agent 崩溃；用户级/项目级 JSON 配置按项目覆盖用户同名 Hook。
- 风险与假设：Hook handler 是进程内依赖注入函数；超时后后台线程无法被强制终止，只会从主调度路径摘除；外部 Hook 沙箱、插件来源和 UI 配置留给后续安全/插件 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc075_hooks.py` | PASS：5 passed | `backend/tests/test_rc075_hooks.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py` | PASS：38 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/hooks.py backend/rabbit_code/__init__.py backend/tests/test_rc075_hooks.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：58 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：147 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 147 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-075/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-075 测试，并恢复本项对 `hooks.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-074 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。外部 Hook 沙箱、插件来源/权限、跨进程执行和 UI 配置留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
