# RC-089 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086、RC-087、RC-088
- 修改文件：`backend/rabbit_code/session_database.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc089_session_database.py`、`docs/traceability/rc-index.md`
- 用户可见行为：独立会话数据库使用迁移表、WAL、NORMAL 同步、外键和完整性检查；启动时将遗留 started 事务标记为 recovered；保存会话检查点；支持验证备份、恢复副本、按用户/会话/全库导出和隐私清理；损坏数据库提供只读救援连接入口。
- 风险与假设：本项提供会话数据库的最小可恢复边界；更广的磁盘错误/kill 故障注入、跨进程会话服务、生产保留和加密策略留给后续 RC，不声称覆盖所有 SQLite/文件系统故障组合。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc089_session_database.py -q` | PASS：5 passed | `backend/tests/test_rc089_session_database.py` |
| `python -m ruff check backend/rabbit_code/session_database.py backend/tests/test_rc089_session_database.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/session_database.py` | PASS | `backend/rabbit_code/session_database.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 196 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-089/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-089 测试，并恢复本项对 `session_database.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-088 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。更广数据库故障注入、跨进程会话服务、生产保留和加密策略留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
