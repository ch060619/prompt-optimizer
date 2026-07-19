# RC-104 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-069、RC-100
- 修改文件：`backend/rabbit_code/ci_execution.py`、`backend/rabbit_code/cli.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc104_noninteractive.py`、`docs/traceability/rc-index.md`
- 用户可见行为：显式 `--non-interactive` 没有 `--permission-policy` 时快速返回 usage 错误；支持 deny/read-only/approve 策略；非交互路径不显示 prompt 或等待 stdin；历史无 TTY 管道默认按 read-only 兼容；权限拒绝返回独立退出码 3，机器输出保持 text/json/jsonl 稳定。
- 风险与假设：本项验证 CLI 策略边界和运行时异常映射，真实危险工具 approval 传递由后续工具接线 RC 完成；旧管道兼容默认是 read-only，不代表永久授权。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc104_noninteractive.py backend/tests/test_rc100_cli_surface.py backend/tests/test_rc069_cli_modes.py -q` | PASS：12 passed、2 warnings | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/ci_execution.py backend/rabbit_code/cli.py backend/tests/test_rc104_noninteractive.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：86 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 259 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-104/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-104 测试，并恢复本项对 `ci_execution.py`、`cli.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-103 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实危险工具审批传递、Windows/Linux CI 实机和更多退出码场景留给后续 RC；RC-057/060 外部确认仍 pending。
