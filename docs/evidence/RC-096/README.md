# RC-096 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-091、RC-094
- 修改文件：`backend/rabbit_code/tool_results.py`、`backend/rabbit_code/shell_tools.py`、`backend/rabbit_code/process_tools.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc096_tool_results.py`、`docs/traceability/rc-index.md`
- 用户可见行为：同步 Shell 和后台日志使用有界采集；保留上限内文本并记录总字节、SHA-256、二进制和截断状态；返回成功、失败、部分成功、超时、取消五类结果；重试仅按显式 outcome 条件执行；后台 reader 继续排空输出，避免巨量日志阻塞进程。
- 风险与假设：默认输出/日志上限为 1 MiB/10 MiB，调用方可显式降低；二进制只提供受限文本预览和元数据，不把原始二进制伪装成 UTF-8；当前跨平台实测仍以 Windows 为主。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc096_tool_results.py -q` | PASS：5 passed | `backend/tests/test_rc096_tool_results.py` |
| `python -m pytest backend/tests/test_rc091_shell_tools.py backend/tests/test_rc094_process_tools.py backend/tests/test_rc096_tool_results.py -q` | PASS：15 passed、2 skipped | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/tool_results.py backend/rabbit_code/shell_tools.py backend/rabbit_code/process_tools.py backend/tests/test_rc096_tool_results.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：79 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 228 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-096/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-096 测试，并恢复本项对 `tool_results.py`、`shell_tools.py`、`process_tools.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-095 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。跨平台实机矩阵、统一工具异常协议和更广部分成功编排留给后续 RC；RC-057/060 外部确认仍 pending。
