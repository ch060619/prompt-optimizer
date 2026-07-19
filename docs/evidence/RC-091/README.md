# RC-091 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086、RC-087、RC-088、RC-089、RC-090
- 修改文件：`backend/rabbit_code/shell_tools.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc091_shell_tools.py`、`docs/traceability/rc-index.md`
- 用户可见行为：数组命令始终不经过 shell 拼接；显式支持 PowerShell/cmd/Bash/zsh 脚本；cwd 限定工作区；支持环境变量覆盖、输入、指定编码、stdout/stderr、退出码、信号和超时；Shell 执行受共享权限策略控制。
- 风险与假设：Windows 当前没有可用 WSL bash 运行时，bash 脚本夹具跳过；本项提供适配器和诊断契约，跨平台实机矩阵、完整进程树终止和 shell 特殊行为留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc091_shell_tools.py -q` | PASS：5 passed，2 skipped（WSL bash 运行时与平台条件） | `backend/tests/test_rc091_shell_tools.py` |
| `python -m ruff check backend/rabbit_code/shell_tools.py backend/tests/test_rc091_shell_tools.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/shell_tools.py` | PASS | `backend/rabbit_code/shell_tools.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 204 passed/4 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-091/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-091 测试，并恢复本项对 `shell_tools.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-090 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。WSL bash 运行时不可用与 Windows symlink 创建权限导致测试 skip；跨平台实机矩阵、完整进程树终止和 shell 特殊行为留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
