# RC-108 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-054、RC-065、RC-103、RC-107
- 修改文件：`backend/rabbit_code/maintenance.py`、`backend/rabbit_code/__init__.py`、`backend/src/prompt_optimizer/cli/app.py`、`backend/tests/test_rc108_cli_maintenance.py`、`docs/traceability/rc-index.md`
- 用户可见行为：`rabbit completion bash|zsh|fish|powershell` 输出可加载补全；`rabbit version` 和 `rabbit path` 检查版本/安装/数据/数据库路径；`rabbit doctor [--json]` 输出 Python、包版本、可执行文件、数据目录和数据库父目录检查；`rabbit uninstall` 默认 dry-run 清理缓存，`--purge-data` 删除全部应用数据必须再带 `--yes`。
- 安全边界：卸载只允许名称为 `rabbit-code` 或 `prompt-optimizer` 的应用数据目录；拒绝包含项目工作区的路径和文件系统根目录；默认不删除数据库，任何未确认命令不删除文件；测试确认用户项目保持不变。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc108_cli_maintenance.py -q` | PASS：9 passed、4 warnings | `backend/tests/test_rc108_cli_maintenance.py` |
| `python -m ruff check backend/rabbit_code/maintenance.py backend/rabbit_code/__init__.py backend/src/prompt_optimizer/cli/app.py backend/tests/test_rc108_cli_maintenance.py` | PASS | `backend/rabbit_code/`、`backend/src/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：90 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-108/README.md` |
| CLI maintenance smoke tests | PASS：`version`、`path --json`、`doctor --json`、`completion bash` 和 `uninstall --purge-data` dry-run 均通过 | `backend/tests/test_rc108_cli_maintenance.py` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-108 测试，并恢复本项对 `maintenance.py`、`__init__.py`、`app.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-107 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。当前命令清理应用缓存/数据，不代替操作系统包管理器移除 Python 包或安装器文件；真实安装器卸载、跨平台包路径和升级回滚留给后续发布 RC；RC-057/060 外部确认仍 pending。
