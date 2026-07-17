# RC-059 执行证据

- RC ID: RC-059
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`7e748e3`
- 实现 Commit：`74a219d`
- 前置 RC：RC-058 已完成；RC-057 外部平台确认仍 pending，但不阻塞本地 runtime 抽象
- 修改范围：`backend/rabbit_code/runtime.py`、`backend/rabbit_code/cli.py`、`backend/rabbit_code/__init__.py`、`backend/tests/test_rc059_runtime.py`

## 交付

- 定义 `AgentRuntime` Protocol，并提供 `InProcessRuntime` 与 `AppServerRuntime` 两个实现。
- App Server runtime 使用 `X-Rabbit-Code-Startup-Token` 和 `X-Rabbit-Code-Protocol` 请求头，解析 SSE 为同一 `AgentEvent` 类型。
- CLI prototype 增加 `--runtime in-process|app-server`、`--base-url` 和 `--startup-token`；默认仍走离线进程内 runtime。
- 进程内和 App Server runtime 的 started/delta/completed 事件序列由同一 Mock 契约测试对比，未发送真实网络请求。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc059_runtime.py -q` | FAIL（预期）：runtime 模块不存在 |
| `python -m pytest backend/tests/test_rc059_runtime.py -q` | PASS：1 passed；请求头、SSE 解析和两 runtime 事件模型一致 |
| `python -m pytest backend/tests -q` | PASS：78 passed；保留既有路径迁移、数据目录和 jsdom 警告 |
| `python -m mypy backend/src backend/rabbit_code` | PASS：42 个源码文件无问题 |
| `python -m ruff check backend scripts` | PASS |
| `python scripts/workspace.py verify` | PASS：根级 check、Ruff、Mypy、后端/前端测试和构建全部通过 |
| `python -m backend.rabbit_code.cli --help` | PASS：runtime/base-url/startup-token 选项可见 |

## 范围与遗留

- App Server 请求使用独立 prototype `/agent/stream` SSE 边界；生产 CLI service-mode 与主 App Server endpoint 统一留给后续 RC-060/063，避免复制业务逻辑。
- 真实 App Server、真实 API、外部服务和付费资源均未调用；MockTransport 是本项唯一远程边界验证。
- RC-057 的 Linux/Tauri/TypeScript 外部确认仍 pending，已记录在其证据，不在本项隐藏。

## 环境

- 时间：2026-07-17 15:52:43 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
