# RC-180 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-179
- 目标：UI、导出、错误、诊断、公共 JSON/metadata 和运行时已知密钥均不得泄漏 Provider secret。

## 实现范围

- 前端 `publicOutput.ts` 维护运行时 secret fingerprint，识别多种 Provider key 格式，并提供固定 `********` 掩码与末尾四位显示。
- API 错误格式化、导出文本、Provider 编辑器/API 向导和诊断复制均经过公共脱敏边界；诊断不包含 prompt/source 正文。
- 后端 `prompt_optimizer.public` 对 Provider 错误、错误摘要、request metadata 和运行时注册 secret 脱敏；`rabbit_code.public_output` 对公共 JSON 递归移除隐藏推理字段并替换敏感字段。
- SecretStore 配置解析在读取 opaque reference 后只登记运行时指纹，不写回明文配置。

## 验证

从仓库根目录执行：

```powershell
$env:PYTHONPATH = 'backend/src;backend;packages/protocol'
& '.venv\Scripts\python.exe' -m pytest backend/tests/test_rc064_storage_boundary.py backend/tests/test_rc160_openai_chat.py backend/tests/test_rc161_openai_responses.py backend/tests/test_rc162_gemini.py backend/tests/test_rc163_anthropic.py backend/tests/test_rc164_claude_boundary.py backend/tests/test_rc165_hosted_providers.py backend/tests/test_rc166_provider_presets.py backend/tests/test_rc167_capabilities.py backend/tests/test_rc168_model_discovery.py backend/tests/test_rc169_connection_test.py backend/tests/test_rc170_error_classification.py backend/tests/test_rc171_network_resilience.py backend/tests/test_rc172_model_selection_budget.py backend/tests/test_rc173_provider_contracts.py backend/tests/test_rc179_secret_store.py backend/tests/test_rc180_redaction.py -q
```

结果：`118 passed, 1 skipped`。

补充检查：

- RC-180 专项：`2 passed`。
- 前端：`21` 个测试文件、`96 passed`；ESLint、TypeScript/Vite build 通过。
- 定向 Ruff、定向 Mypy、`compileall` 通过。
- `check_rc_traceability.py --write`、`workspace.py check` 在本次计划更新后执行并通过。

## 限制

- 未发送真实 Provider 请求，未产生费用；Provider secret 仅使用测试夹具。
- 当前环境为 Windows，Linux Secret Service 未做实机验证；该限制沿用 RC-179 记录。
- 前端测试保留既有 jsdom navigation stderr，不影响测试退出码。
