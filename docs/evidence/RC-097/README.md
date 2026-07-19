# RC-097 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-070、RC-076、RC-096
- 修改文件：`backend/rabbit_code/tool_registry.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc097_tool_registry.py`、`docs/traceability/rc-index.md`
- 用户可见行为：工具注册必须声明名称、描述、对象型 JSON Schema、权限模式、读写/网络/进程影响、幂等、取消和审计动作；重复、缺字段、非法 Schema 和缺 handler 工具不能进入 startup/model catalog；调用前校验输入与共享权限策略，并记录允许/拒绝/失败/成功审计。
- 风险与假设：当前 JSON Schema 校验覆盖工具输入所需的对象、字段、基础类型和额外字段边界，不替代完整 JSON Schema 引擎；工具 handler 仍由后续 RC 接入真实 Shell/File/Git 适配。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc097_tool_registry.py -q` | PASS：5 passed | `backend/tests/test_rc097_tool_registry.py` |
| `python -m pytest backend/tests/test_rc091_shell_tools.py backend/tests/test_rc094_process_tools.py backend/tests/test_rc095_patch_tools.py backend/tests/test_rc096_tool_results.py backend/tests/test_rc097_tool_registry.py -q` | PASS：26 passed、2 skipped | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/tool_registry.py backend/tests/test_rc097_tool_registry.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：80 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 233 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-097/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-097 测试，并恢复本项对 `tool_registry.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-096 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。完整 JSON Schema 语义、现有所有工具的统一注册接线和 CLI/GUI/API 内容块消费留给后续 RC；RC-057/060 外部确认仍 pending。
