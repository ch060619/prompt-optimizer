# RC-100 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-069、RC-097、RC-099
- 修改文件：`backend/rabbit_code/cli.py`、`backend/tests/test_rc100_cli_surface.py`、`docs/traceability/rc-index.md`
- 用户可见行为：`rabbit` 支持 run、continue、resume、model、mode、output 命令；支持 `--session`、`--model`、`--mode`、`--output`、runtime 参数；旧的单次 prompt、stdin、TTY 和 JSON/JSONL 事件流保持；控制命令提供稳定机器输出和 usage 退出码。
- 风险与假设：本项冻结 CLI 命令/参数面；continue/resume 的持久会话加载、model/mode 的真实配置写入和 TUI 交互留给后续 RC，不伪造为已接线。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc100_cli_surface.py backend/tests/test_rc069_cli_modes.py backend/tests/test_cli_compatibility.py -q` | PASS：12 passed、2 warnings | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/cli.py backend/tests/test_rc100_cli_surface.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：82 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 245 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-100/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-100 测试，并恢复本项对 `cli.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-099 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。持久会话恢复、实际 model/mode 配置消费、TUI、跨平台终端实测留给后续 RC；RC-057/060 外部确认仍 pending。
