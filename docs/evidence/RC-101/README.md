# RC-101 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-071、RC-098、RC-100
- 修改文件：`backend/rabbit_code/tui.py`、`backend/rabbit_code/cli.py`、`backend/tests/test_rc101_tui.py`、`docs/traceability/rc-index.md`
- 用户可见行为：TUI 从共享 AgentEvent 生成固定 header、输入区、流式文本、工具状态、权限提示、计划、diff 和 usage/费用状态；窄屏只压缩正文不丢状态栏/输入区；无颜色输出无 ANSI；`rabbit tui` 复用同一 runtime。
- 风险与假设：本项实现事件状态和静态渲染边界；多行编辑、历史、补全、IME、粘贴保护和真实 Windows/Linux TTY 矩阵留给 RC-102/107。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc101_tui.py backend/tests/test_rc100_cli_surface.py -q` | PASS：6 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/tui.py backend/rabbit_code/cli.py backend/tests/test_rc101_tui.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：83 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 248 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-101/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-101 测试，并恢复本项对 `tui.py`、`cli.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-100 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。键盘编辑/历史/补全/IME/粘贴保护、真实 TTY 矩阵和更丰富内容块渲染留给后续 RC；RC-057/060 外部确认仍 pending。
