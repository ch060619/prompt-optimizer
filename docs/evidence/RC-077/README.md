# RC-077 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-068、RC-069、RC-070、RC-071、RC-072、RC-073、RC-074、RC-075、RC-076
- 修改文件：`backend/rabbit_code/plugins.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc077_plugins.py`
- 用户可见行为：插件 manifest 固定名称/版本/入口/权限/兼容范围/来源/产物哈希；安装、启用、禁用、升级、卸载均受注册表控制并审计；插件只能调用宿主显式注册的 handler，未知入口不会被导入或执行。
- 风险与假设：当前插件包为本地目录复制并使用 SHA-256 校验；来源 allowlist、权限 allowlist 和 handler registry 是安装/启用前置门禁；签名、沙箱、远程下载和 UI 管理留给后续安全/发布 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest -q backend/tests/test_rc077_plugins.py` | PASS：7 passed | `backend/tests/test_rc077_plugins.py` |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py backend/tests/test_rc070_permissions.py backend/tests/test_rc071_streaming.py backend/tests/test_rc072_budget.py backend/tests/test_rc073_run_control.py backend/tests/test_rc074_subagents.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py backend/tests/test_rc077_plugins.py` | PASS：50 passed | `backend/tests/` |
| `python -m ruff check backend/rabbit_code/plugins.py backend/rabbit_code/__init__.py backend/tests/test_rc077_plugins.py` | PASS | `backend/rabbit_code/`、`backend/tests/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：60 source files | `backend/`、`packages/protocol/` |
| `python -m pytest -q backend/tests` | PASS：159 passed，29 warnings | `backend/tests/` |
| `python scripts/workspace.py verify` | PASS：生成 drift、追踪、依赖边界、交付计划、Ruff、Mypy、后端 159 passed、前端 9 passed、Lint、Build | `docs/evidence/RC-077/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件、新增 RC-077 测试，并恢复本项对 `plugins.py` 与 `__init__.py` 的修改；不得覆盖 RC-068 至 RC-076 的既有变更。
- 不得触碰的用户数据：本地运行控制 JSON、Agent 检查点、Provider 凭据、工作区文件和未提交用户修改。

## 未解决项

- 无。插件签名/沙箱、远程来源、依赖隔离、跨进程生命周期和 UI 配置留给后续 RC；既有路径迁移 DeprecationWarning 与前端 jsdom navigation 警告已保留并记录。
