# RC-078 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077
- 修改文件：`backend/rabbit_code/capabilities.py`、`backend/src/prompt_optimizer/providers/base.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc078_capabilities.py`
- 用户可见行为：请求发送前按文本/视觉/工具/结构化输出/推理/上下文能力生成协商计划；可选工具在 Provider 不支持时明确降级并移除工具 Schema，必需能力缺失时拒绝请求并提供替代建议。
- 风险与假设：能力协商是 Provider 请求前的独立边界，当前 `PreparedModelRequest` 承载工具列表；真实 Provider 原生能力遥测和 UI 展示留给后续 Provider/UI RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc078_capabilities.py` | PASS：3 passed | `backend/tests/test_rc078_capabilities.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc078_capabilities.py` | PASS：53 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/capabilities.py backend/src/prompt_optimizer/providers/base.py backend/rabbit_code/__init__.py backend/tests/test_rc078_capabilities.py` | PASS | `backend/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：61 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：162 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 162 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-078/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-078 测试，并恢复本项对 `capabilities.py`、Provider 能力字段和 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-077 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。真实 Provider 能力遥测、能力 UI、跨协议映射和完整视觉/音频能力留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
