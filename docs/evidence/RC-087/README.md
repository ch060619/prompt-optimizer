# RC-087 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086
- 修改文件：`backend/rabbit_code/checkpoints.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc087_checkpoints.py`、`docs/traceability/rc-index.md`
- 用户可见行为：创建检查点时保存工作树基线；每组变更记录 before/after 文件内容、工具和验证结果；回滚仅恢复当前仍等于 Agent after 的文件；并发用户改动报告冲突且不覆盖；全量回滚按变更组逆序，部分回滚返回明确范围、恢复、跳过和冲突列表。
- 风险与假设：本项提供进程内、文件级的可证明回滚边界；持久化检查点、跨进程恢复、完整工具编排和生产 GUI 展示留给后续 RC，不声称覆盖未纳入基线的路径。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc087_checkpoints.py -q` | PASS：4 passed | `backend/tests/test_rc087_checkpoints.py` |
| `python -m ruff check backend/rabbit_code/checkpoints.py backend/tests/test_rc087_checkpoints.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/checkpoints.py` | PASS | `backend/rabbit_code/checkpoints.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 186 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-087/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-087 测试，并恢复本项对 `checkpoints.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-086 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。持久化检查点、跨进程恢复、完整工具编排和生产 GUI 展示留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
