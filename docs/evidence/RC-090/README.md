# RC-090 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086、RC-087、RC-088、RC-089
- 修改文件：`backend/rabbit_code/file_tools.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc090_file_tools.py`、`docs/traceability/rc-index.md`
- 用户可见行为：提供 read/list/search/edit/patch/create/move/delete；路径、工作区、symlink、文件大小、UTF-8/二进制和共享权限策略统一校验；现有文件变更需期望 SHA-256 防并发覆盖；写操作返回 before/after SHA-256 和 unified diff。
- 风险与假设：本项提供进程内文件工具边界；Windows symlink 创建权限不可用时对应夹具跳过；并发文件监视器、跨平台权限矩阵和更广工具编排留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc090_file_tools.py -q` | PASS：3 passed，1 skipped（Windows symlink 创建不可用） | `backend/tests/test_rc090_file_tools.py` |
| `python -m ruff check backend/rabbit_code/file_tools.py backend/tests/test_rc090_file_tools.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/file_tools.py` | PASS | `backend/rabbit_code/file_tools.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 199 passed/2 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-090/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-090 测试，并恢复本项对 `file_tools.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-089 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。Windows symlink 创建权限导致的测试 skip、并发监听、跨平台权限矩阵和更广工具编排留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
