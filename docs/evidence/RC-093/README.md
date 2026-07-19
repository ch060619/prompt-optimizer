# RC-093 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076、RC-077、RC-078、RC-079、RC-080、RC-081、RC-082、RC-083、RC-084、RC-085、RC-086、RC-087、RC-088、RC-089、RC-090、RC-091、RC-092
- 修改文件：`backend/rabbit_code/diagnostics.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc093_diagnostics.py`、`docs/traceability/rc-index.md`
- 用户可见行为：统一输出 command、exit_code、file、line、column、severity、message、source、raw；解析 Ruff/Mypy/TypeScript/Pytest 常见诊断；解析失败时保留完整 stdout/stderr 和原始诊断，CLI/GUI 可消费同一 `to_dict()` 结构。
- 风险与假设：本项覆盖当前项目常见文本输出格式；完整 LSP 协议、更多编译器格式和跨平台诊断矩阵留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc093_diagnostics.py -q` | PASS：3 passed | `backend/tests/test_rc093_diagnostics.py` |
| `python -m ruff check backend/rabbit_code/diagnostics.py backend/tests/test_rc093_diagnostics.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/rabbit_code/diagnostics.py` | PASS | `backend/rabbit_code/diagnostics.py` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 212 passed/4 skipped、前端 9 passed、Lint、Build | `docs/evidence/RC-093/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-093 测试，并恢复本项对 `diagnostics.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-068 至 RC-092 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无阻塞项。完整 LSP 协议、更多编译器格式和跨平台诊断矩阵留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
