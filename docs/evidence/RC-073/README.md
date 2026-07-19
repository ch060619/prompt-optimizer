# RC-073 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072
- 修改文件：`backend/rabbit_code/run_control.py`、`backend/rabbit_code/agent.py`、`backend/tests/test_rc073_run_control.py`
- 用户可见行为：运行可暂停/恢复/取消/重试/重新生成；模型请求按幂等键复用或递增重试，写操作失败后拒绝安全性未知的重放；运行控制和尝试链支持 JSON 持久化。
- 风险与假设：模型流采用事件序列缓存以支持同一请求恢复；写操作没有可证明的提交确认时保持 `UnsafeRetry`，不自动再次提交；Tauri/Rust、跨平台打包和真实 Provider 仍不属于本项。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc073_run_control.py` | PASS：5 passed | `backend/tests/test_rc073_run_control.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py` | PASS：29 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/run_control.py backend/rabbit_code/agent.py backend/tests/test_rc073_run_control.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：56 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：138 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 138 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-073/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-073 测试，并恢复本项对 `run_control.py` 与 `agent.py` 的修改；不得覆盖 RC-068 至 RC-072 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录，不阻塞下一项 RC-074。
