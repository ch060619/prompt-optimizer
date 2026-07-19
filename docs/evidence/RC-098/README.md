# RC-098 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-061、RC-071、RC-093、RC-097
- 修改文件：`backend/rabbit_code/content_blocks.py`、`packages/protocol/rabbit_code_protocol/models.py`、`packages/protocol/rabbit_code_protocol/__init__.py`、`backend/tests/test_rc098_content_blocks.py`、`docs/traceability/rc-index.md`
- 用户可见行为：工具结果统一为 text、diagnostic、diff、file、image、progress、error 内容块；后端验证并输出 canonical 字段；API protocol 接受同一联合块；CLI/GUI 使用相同 renderer snapshot；未知块保留来源类型并安全降级为 text。
- 风险与假设：图片块当前传递受协议约束的 MIME/data 字段，不负责实际渲染；未知块不执行其 payload；真实 CLI/GUI 组件接线和更多内容块类型留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python -m pytest backend/tests/test_rc098_content_blocks.py -q` | PASS：5 passed | `backend/tests/test_rc098_content_blocks.py` |
| `python -m ruff check backend/rabbit_code/content_blocks.py backend/tests/test_rc098_content_blocks.py backend/rabbit_code/__init__.py packages/protocol/rabbit_code_protocol/models.py packages/protocol/rabbit_code_protocol/__init__.py` | PASS | `backend/rabbit_code/`、`packages/protocol/` |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：81 source files | `backend/rabbit_code/`、`backend/src/`、`packages/protocol/` |
| `python scripts/workspace.py verify` | PASS：后端 238 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-098/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 RC-098 测试，并恢复本项对 `content_blocks.py`、protocol models、protocol exports 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-097 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、运行控制 JSON、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。图片实际渲染、真实 CLI/GUI 组件接线、跨表面 E2E 和扩展工具结果适配留给后续 RC；RC-057/060 外部确认仍 pending。
