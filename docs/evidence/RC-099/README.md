# RC-099 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-076、RC-077、RC-098
- 修改文件：`backend/rabbit_code/extensions.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc099_extensions.py`、`docs/traceability/rc-index.md`
- 用户可见行为：浏览器、数据库、外部服务、Plugin、MCP 使用统一 ExtensionSpec/Adapter/Manager；能力必须声明 network/workspace_write；安装后没有隐式启用；每个 session 通过显式确认获得独立 grant；未授权无法调用，撤销后立即失效；所有审批、拒绝、成功和失败写入审计。
- 风险与假设：本项验证能力边界和 fake adapter，不执行真实浏览器、数据库或外部网络请求；真实适配器连接和凭据处理留给受控环境与后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc099_extensions.py -q` | PASS：4 passed | `backend/tests/test_rc099_extensions.py` |
| `python -m pytest backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py backend/tests/test_rc098_content_blocks.py backend/tests/test_rc099_extensions.py -q` | PASS：21 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/extensions.py backend/tests/test_rc099_extensions.py backend/rabbit_code/__init__.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：82 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 242 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-099/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-099 测试，并恢复本项对 `extensions.py`、`__init__.py` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-098 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实联网/数据库/浏览器适配、生产凭据、插件/MCP 进程沙箱和跨表面 UI 审批留给后续 RC；RC-057/060 外部确认仍 pending。
