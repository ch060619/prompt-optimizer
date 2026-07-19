# RC-086 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085
- 修改文件：`backend/rabbit_code/sessions.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc086_sessions.py`、`docs/traceability/rc-index.md`
- 用户可见行为：按所有者隔离会话；支持新建、读取、命名、搜索、分页、置顶、归档、软删除/恢复、继续、分叉和确定性 JSON 导出；分叉复制原消息并保留父会话关系；每个成功操作追加顺序审计事件，审计支持分页。
- 风险与假设：本项提供 Agent Core 进程内最小服务边界；持久化会话库、跨进程恢复、API/CLI/GUI 接入和生产保留策略留给后续 RC，不把进程内存储描述为崩溃可恢复数据库。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc086_sessions.py -q` | PASS：4 passed | `backend/tests/test_rc086_sessions.py` |
| `python -m ruff check backend/rabbit_code/sessions.py backend/tests/test_rc086_sessions.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/sessions.py` | PASS | `backend/rabbit_code/sessions.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 182 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-086/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-086 测试，并恢复本项对 `sessions.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-085 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。持久化会话数据库、跨进程恢复、API/CLI/GUI 接入和生产保留策略留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
