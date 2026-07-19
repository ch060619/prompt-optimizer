# RC-085 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084
- 修改文件：`backend/rabbit_code/memory.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc085_memory.py`、`docs/traceability/rc-index.md`
- 用户可见行为：临时、会话、项目和用户记忆使用独立表与 `scope_id` 隔离；新建/编辑必须明确来源、用途并显式确认；支持查看、编辑、逐项删除、作用域清理和全清理；禁用作用域后所有读写、编辑、删除和清理操作均拒绝。
- 风险与假设：本项提供 Agent Core 进程内的最小隔离边界；持久化存储、API/CLI/GUI 接入、审计和记忆界面留给后续生命周期与 UI RC，不把进程内实现描述为崩溃可恢复存储。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc085_memory.py -q` | PASS：4 passed | `backend/tests/test_rc085_memory.py` |
| `python -m ruff check backend/rabbit_code/memory.py backend/tests/test_rc085_memory.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/memory.py` | PASS | `backend/rabbit_code/memory.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 178 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-085/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-085 测试，并恢复本项对 `memory.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-084 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。持久化后端、API/CLI/GUI 接入、审计和记忆展示留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
