# RC-058 执行证据

- RC ID: RC-058
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`3e5daec`
- 实现 Commits：`0f595ab`、`f0abab1`
- 前置 RC：RC-056 已完成；RC-057 的外部 Linux/Tauri/TypeScript 确认保留为 pending，不阻塞本项严格 App Server 边界交付
- 修改范围：`backend/src/prompt_optimizer/api/app.py`、`backend/src/prompt_optimizer/api/__init__.py`、`backend/src/prompt_optimizer/cli/app.py`、`backend/tests/test_rc058_app_server.py`、`frontend/src/api.ts`、`frontend/src/marketing.tsx`、`frontend/tests/App.test.tsx`

## 交付

- 增加严格 `create_app_server()` 工厂：只挂载 `/api/v1`，不在新 OpenAPI 中重复 `/api` 业务路径。
- 增加公开 `/api/v1/health`，返回状态、协议版本和是否要求启动令牌。
- App Server 业务请求要求 `X-Rabbit-Code-Startup-Token`；不匹配返回 401；`X-Rabbit-Code-Protocol` 不支持时返回 426，并返回支持版本。
- CLI `serve --startup-token` 可启动严格模式；无参数仍保留旧兼容模式，RC-059 再统一 CLI 的进程内/服务调用模式。
- GUI API client 和用户可见接口说明已切换到 `/api/v1`；后端 `/api` 兼容层和 RC-048 OpenAPI 保持不变。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_rc058_app_server.py -q` | FAIL（预期）：严格 App Server 工厂不存在 |
| `python -m pytest backend/tests/test_rc058_app_server.py -q` | PASS：3 passed；health、启动令牌、协议协商和无重复路径通过 |
| `python -m pytest backend/tests/test_api_contract.py backend/tests/test_cli_compatibility.py -q` | PASS：9 passed；旧 API/OpenAPI/CLI 兼容保持 |
| `python -m pytest backend/tests -q` | PASS：77 passed；保留既有路径迁移和 jsdom 警告 |
| `npm --prefix frontend test -- --run` | PASS：9 passed；Mock 请求已使用 `/api/v1` |
| `npm --prefix frontend run lint` | PASS |
| `npm --prefix frontend run build` | PASS |
| `python scripts/workspace.py verify` | PASS：根级 check、Ruff、Mypy、后端/前端测试和构建全部通过 |

## 范围与遗留

- 默认 `create_app()` 不改变 RC-048 兼容行为；严格启动令牌模式是新的 App Server boundary，避免旧客户端静默破坏。
- 真实桌面壳启动令牌注入、CLI service-mode 和取消向下传播留给 RC-059/060/063；真实 API/外部服务未调用。
- RC-057 的 Linux、Tauri 打包和 TypeScript 替代方案仍是 pending，不被本项的严格 App Server 测试掩盖；按用户要求继续自动执行 RC-059。

## 环境

- 时间：2026-07-17 15:46:28 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
