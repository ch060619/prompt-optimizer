# RC-088 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086、RC-087
- 修改文件：`backend/rabbit_code/workspace_isolation.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc088_workspace_isolation.py`、`docs/traceability/rc-index.md`
- 用户可见行为：会话绑定规范化工作区 ID；可选创建独立目录 worktree；读写、缓存、进程和终端都检查会话归属；清理只删除管理器新建的 worktree/缓存并注销本会话资源，不删除项目用户分支或既有项目缓存。
- 风险与假设：本项提供进程内文件/资源隔离边界；真实 Git worktree 创建、进程树终止、跨进程资源注册和生产 GUI 工作区管理留给后续 RC，不把目录 worktree 原型描述为完整 Git 生命周期。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc088_workspace_isolation.py -q` | PASS：5 passed | `backend/tests/test_rc088_workspace_isolation.py` |
| `python -m ruff check backend/rabbit_code/workspace_isolation.py backend/tests/test_rc088_workspace_isolation.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/workspace_isolation.py` | PASS | `backend/rabbit_code/workspace_isolation.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 191 passed/1 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-088/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-088 测试，并恢复本项对 `workspace_isolation.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-087 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。真实 Git worktree、进程终止、跨进程资源服务和生产 GUI 工作区管理留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
