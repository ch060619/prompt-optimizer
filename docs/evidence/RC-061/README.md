# RC-061 执行证据

- RC ID: RC-061
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`451e1ef`
- 实现 Commit：`1adc320`
- 前置 RC：RC-060 边界已提交；Rust/Tauri 外部确认仍 pending，不影响协议包本地实现
- 修改范围：`packages/protocol/pyproject.toml`、`packages/protocol/rabbit_code_protocol/`、`scripts/check_monorepo.py`、`scripts/workspace.py`、`backend/tests/test_rc061_protocol.py`

## 交付

- 建立独立 `rabbit-code-protocol` Pydantic 包，统一 workspace 版本 `3.0.0`。
- Schema 覆盖 Agent request、session、message/content block、tool call、approval、stream event、diff、task status、error 和 Provider capabilities。
- 所有跨表面模型携带 `protocol_version="v1"`；流事件携带 `request_id`、非负 `seq`、type、payload 和 timestamp。
- workspace 版本校验、安装入口和 Mypy 范围纳入 protocol 包；TypeScript 客户端生成留给 RC-062。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc061_protocol.py -q` | FAIL（预期）：protocol 包不存在；随后修正一次 Pydantic 前向引用导入错误 |
| `python -m pytest backend/tests/test_rc061_protocol.py -q` | PASS：2 passed；round-trip、版本拒绝、序号约束通过 |
| `python scripts/workspace.py install` | PASS：backend 和 `rabbit-code-protocol` editable 安装成功；frontend 依赖已安装 |
| `python scripts/workspace.py verify` | PASS：root check、Ruff、Mypy、后端 81 passed、前端 9 passed、Lint、Build 全部通过 |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS：44 个源码文件无问题 |
| `python -m ruff check backend scripts packages/protocol` | PASS |

## 范围与遗留

- Schema 是独立的 v1 基线，不复制现有 FastAPI DTO；生成 TypeScript 类型/客户端、兼容窗口和 CI drift 门禁留给 RC-062。
- 未发起真实 API、模型、Tauri 或付费资源操作；RC-057/060 外部平台 pending 状态继续保留并在清单中显示。

## 环境

- 时间：2026-07-17 16:02:31 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
