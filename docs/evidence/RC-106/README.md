# RC-106 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-100、RC-101、RC-104、RC-105
- 修改文件：`backend/rabbit_code/shared_surface.py`、`backend/rabbit_code/permissions.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc106_shared_surface.py`、`docs/traceability/rc-index.md`
- 用户可见行为：CLI 与 GUI 可通过独立 context 读取同一 Provider 引用、模型目录、当前模型、会话、权限模式和 Prompt optimizer；共享状态写入 JSON 时只保存 `api_key_ref`，不保存 API Key；原子替换、跨进程文件锁和进程内路径锁保护并发写入。
- 风险与假设：本项提供共享状态服务边界和持久化并发保护，真实 CLI/GUI 进程接线、Credential Manager/Secret Service 密钥存储和完整会话服务留给后续配置与 GUI RC；当前锁矩阵在 Windows 实机验证，Unix 分支由实现和静态检查覆盖。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc106_shared_surface.py -q` | PASS：4 passed | `backend/tests/test_rc106_shared_surface.py` |
| `python -m ruff check backend/rabbit_code/shared_surface.py backend/rabbit_code/permissions.py backend/tests/test_rc106_shared_surface.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：88 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 266 passed、4 skipped、29 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-106/README.md` |
| 并发状态人工/自动检查 | PASS：两个独立 context 同时更新 session 后 JSON 仍可解析，最终状态为任一完整提交值，无临时文件残留 | `backend/tests/test_rc106_shared_surface.py` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-106 测试，并恢复本项对 `shared_surface.py`、`permissions.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-105 的既有变更。
- 不得触碰的用户数据：Provider 凭据、共享状态 JSON、会话数据、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实 Credential Manager/Secret Service、跨进程会话服务和 CLI/GUI 生产接线留给后续 RC；当前 Windows 环境保留 WSL bash 与 symlink 权限 skip；RC-057/060 外部确认仍 pending。
