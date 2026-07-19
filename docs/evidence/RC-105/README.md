# RC-105 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-097、RC-104
- 修改文件：`backend/rabbit_code/dry_run.py`、`backend/rabbit_code/cli.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc105_dry_run.py`、`docs/traceability/rc-index.md`
- 用户可见行为：`--dry-run` 只生成 command/cwd/permission/would_execute=false 计划，不创建 Agent runtime；MachineEventStream 产生连续 seq 的 JSON/JSONL 事件；支持 read-only 策略冲突校验和 quiet/error/info/debug log-level。
- 风险与假设：dry-run 当前预览 Rabbit CLI run 动作，不执行真实工具或模型请求；更细工具动作预览和跨消费者事件回放留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc105_dry_run.py -q` | PASS：3 passed | `backend/tests/test_rc105_dry_run.py` |
| `python -m ruff check backend/rabbit_code/dry_run.py backend/rabbit_code/cli.py backend/tests/test_rc105_dry_run.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：87 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 262 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-105/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-105 测试，并恢复本项对 `dry_run.py`、`cli.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-104 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实工具动作预览、复杂计划事件和更多 event consumers 留给后续 RC；RC-057/060 外部确认仍 pending。
