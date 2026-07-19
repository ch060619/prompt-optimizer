# RC-181 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-180
- 目标：支持环境变量和配置文件引用，明确优先级，并在 API/UI 中只显示来源而不显示环境变量秘密值。

## 实现范围

- `ConfigService` 支持 `env:VARIABLE`、`keychain:secret://rabbit-code/...` 和兼容旧格式的 opaque keychain reference。
- 配置优先级固定为 `default < user < workspace < env < session < cli`；直接环境覆盖使用 `RABBIT_CODE_*`，并保留 `PROMPT_OPTIMIZER_*` 兼容读取。
- 每次 `resolve()` 重新读取环境变量，环境变化会得到新值并重新登记运行时 secret fingerprint；数值字段按声明类型转换。
- `/api/v1/config` 只返回配置展示状态：敏感字段使用 `secret://config/...` placeholder，并提供 `source_kind`/`source_label`，不返回环境变量值。
- Provider 页面读取来源状态并显示 `ENVIRONMENT`、`KEYCHAIN` 等来源标签；不把 API key 放入前端状态持久化或页面文本。

## 验证

RC-181 专项与相关 API/SecretStore 测试：`15 passed`（其中 RC-181 专项 4 passed）。

从仓库根目录执行联合回归：

```powershell
$env:PYTHONPATH = 'backend/src;backend;packages/protocol'
& '.venv\Scripts\python.exe' -m pytest backend/tests/test_rc064_storage_boundary.py backend/tests/test_rc160_openai_chat.py backend/tests/test_rc161_openai_responses.py backend/tests/test_rc162_gemini.py backend/tests/test_rc163_anthropic.py backend/tests/test_rc164_claude_boundary.py backend/tests/test_rc165_hosted_providers.py backend/tests/test_rc166_provider_presets.py backend/tests/test_rc167_capabilities.py backend/tests/test_rc168_model_discovery.py backend/tests/test_rc169_connection_test.py backend/tests/test_rc170_error_classification.py backend/tests/test_rc171_network_resilience.py backend/tests/test_rc172_model_selection_budget.py backend/tests/test_rc173_provider_contracts.py backend/tests/test_rc179_secret_store.py backend/tests/test_rc180_redaction.py backend/tests/test_rc181_config_references.py -q
```

结果：`122 passed, 1 skipped`。

补充检查：

- 前端全量：21 个测试文件、`97 passed`；ESLint、TypeScript/Vite build 通过。
- OpenAPI generated drift、定向 Ruff、定向 Mypy、Python `compileall` 通过。
- 本次更新后执行 `check_rc_traceability.py --write` 和 `workspace.py check`。

## 限制

- 未发送真实 Provider 请求，未产生费用；Provider secret 仅使用测试夹具。
- 当前为 Windows 环境，Linux Secret Service 未做实机验证；沿用 RC-179 限制。
- 配置 API 返回的是来源与 opaque placeholder，未返回任何环境变量秘密值。
