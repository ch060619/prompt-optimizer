# RC-094 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-088、RC-091
- 修改文件：`backend/rabbit_code/process_tools.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc094_process_tools.py`、`docs/traceability/rc-index.md`
- 用户可见行为：后台进程进入注册表并保留 PID、命令、cwd、PTY 模式、状态、超时和日志路径；stdout/stderr 合并到按字节游标读取的日志；支持等待、停止、超时树级终止、独立 TCP 端口探测；Windows 使用进程组、`taskkill /T /F` 和 Job Object；不支持原生 PTY 的平台显式报告 `PtyUnavailable`。
- 风险与假设：当前验证环境是 Windows；Linux/非 Windows PTY、Job Object 等平台实机矩阵留待对应平台条件；日志游标以 UTF-8 原始字节偏移计数，读取块可能在多字节字符或换行序列中间结束，但不会伪造或重排原始输出。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc094_process_tools.py -q` | PASS：5 passed | `backend/tests/test_rc094_process_tools.py` |
| `python -m ruff check backend/rabbit_code/process_tools.py backend/tests/test_rc094_process_tools.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python scripts/workspace.py verify` | PASS：后端 217 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-094/README.md` |
| Windows Job Object 创建检查 | PASS：`ProcessManager` 创建有效 Job Object handle | `backend/rabbit_code/process_tools.py` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-094 测试，并恢复本项对 `process_tools.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-093 的既有变更。
- 不得触碰的用户数据：后台进程、进程日志、Provider 凭据、运行控制 JSON、Agent 检查点、工作区文件和未提交用户修改。

## 未解决项

- 无实现阻塞项。当前 Windows 环境未执行 Linux/非 Windows PTY 与进程树实机矩阵，已明确记录，不将未执行平台结果标为通过；RC-057/060 外部确认仍 pending。
