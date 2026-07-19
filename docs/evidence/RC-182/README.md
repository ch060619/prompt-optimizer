# RC-182 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-181
- 目标：仅为有明确第三方客户端政策许可的 Provider 提供官方 OAuth；包含 PKCE、state、刷新、撤销和回调清理。

## 实现范围

- `OAuthProviderPolicy` 与 `OAuthPolicyRegistry` 是强制 allowlist；默认 `APPROVED_OAUTH_POLICIES` 为空，未确认政策的 Provider 不可开始 OAuth。
- `OAuthClient.start()` 生成高熵 state 与 verifier，使用 S256 PKCE，构造授权 URL，并通过注入的系统浏览器 opener 打开。
- 回调要求原始 state、Provider 和 ephemeral loopback redirect 完全匹配；state 在处理前后都有防重放/生命周期保护，失败或取消会清理 callback 状态。
- access/refresh token 只写入 SecretStore，返回 `OAuthCredential` 只包含 opaque references；refresh 会轮换引用，revoke 会调用 transport 并清除本地引用。
- 当前前端 Provider 页没有 OAuth 入口，因为默认批准列表为空；未把订阅 Cookie、内部 token 或逆向登录接入 OAuth。

## 验证

RC-182 专项：`4 passed`。

测试覆盖：未批准 Provider 拒绝、PKCE/state 参数、系统浏览器 hook、CSRF/state 重放、回调重定向劫持、loopback 清理、opaque token 存储、refresh token 轮换和 revoke 清理。

联合回归结果：`126 passed, 1 skipped`，覆盖 RC-064、RC-160 至 RC-173、RC-179、RC-180、RC-181 和 RC-182；定向 Ruff、定向 Mypy、Python `compileall` 通过。

## 限制

- 当前没有可核实的 Provider 第三方客户端政策许可，因此默认批准列表为空；没有伪造 Anthropic、OpenAI 或其他 Provider 的 OAuth 许可。
- 未执行真实浏览器回调、真实 token endpoint、真实刷新/撤销或真实 Provider 请求，未产生费用。
- 下游分发只有在完成官方政策审查、注入真实 token transport 和系统回调 listener 后，才能添加具体 allowlist 项。
