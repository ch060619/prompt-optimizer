# RC-107 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-091、RC-101、RC-102、RC-106
- 修改文件：`backend/rabbit_code/terminal_compatibility.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc107_terminal_compatibility.py`、`docs/traceability/rc-index.md`
- 用户可见行为：提供 Windows Terminal/PowerShell/cmd/WSL/Linux 能力矩阵；终端测试验证 Unicode/空格输入、ANSI 输出保留、TUI 宽高约束、Unicode cwd、取消信号和 WSL Linux shell 输出；不可用的交互终端/剪贴板能力显式返回 skip 原因，不伪装成功。
- 环境快照：Windows 11 host；Windows Terminal executable `7.6.3`；PowerShell `7.6.3`；cmd 可用；WSL `sh` 输出探针通过；当前进程没有 `WT_SESSION`；宿主不是原生 Linux。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc107_terminal_compatibility.py -q` | PASS：6 passed、1 skipped；skip 为无交互 Windows Terminal 剪贴板会话 | `backend/tests/test_rc107_terminal_compatibility.py` |
| `python -m ruff check backend/rabbit_code/terminal_compatibility.py backend/tests/test_rc107_terminal_compatibility.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：89 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 272 passed、5 skipped、29 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-107/README.md` |
| `wt --version` | PASS：7.6.3 executable detected；当前无 `WT_SESSION`，交互尺寸/剪贴板标为未实测 | `backend/rabbit_code/terminal_compatibility.py` |
| `pwsh -NoProfile -NonInteractive -Command '$PSVersionTable.PSVersion.ToString()'` | PASS：7.6.3 | `backend/tests/test_rc107_terminal_compatibility.py` |
| `wsl -e sh -lc "printf ..."` | PASS：WSL Linux shell 输出 `linux-input:中文 path` | `backend/tests/test_rc107_terminal_compatibility.py` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-107 测试，并恢复本项对 `terminal_compatibility.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-106 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。Windows Terminal 交互尺寸/剪贴板需要在真实 `WT_SESSION` 下补测；宿主为 Windows，原生 Linux 终端矩阵留待 Linux CI/实机；RC-057/060 外部确认仍 pending。
