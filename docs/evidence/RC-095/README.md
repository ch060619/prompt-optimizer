# RC-095 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-090、RC-094
- 修改文件：`backend/rabbit_code/patch_tools.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc095_patch_tools.py`、`docs/traceability/rc-index.md`
- 用户可见行为：结构化 JSON/Mapping/PatchEdit 补丁支持单文件和多文件应用；应用前校验 workspace、symlink、权限、SHA-256 基线和唯一上下文；临时副本写入同目录并 fsync，替换中途失败时逆序恢复；保留 UTF-8/UTF-16 BOM、编码和主导换行。
- 风险与假设：补丁目标必须是可解码文本，二进制和未知编码明确拒绝；跨设备文件系统不在本项范围；多文件替换通过同目录备份和回滚实现，最终恢复仍受底层文件系统权限/故障影响。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc095_patch_tools.py -q` | PASS：6 passed | `backend/tests/test_rc095_patch_tools.py` |
| `python -m ruff check backend/rabbit_code/patch_tools.py backend/tests/test_rc095_patch_tools.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：78 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 223 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-095/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-095 测试，并恢复本项对 `patch_tools.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-094 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。复杂二进制/未知编码拒绝属于明确边界；工具输出上限、截断、可重试条件和部分成功状态留给 RC-096；RC-057/060 外部确认仍 pending。
