# RC-183 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-182
- 目标：本地会话、模型和配置不依赖 Rabbit Code 云账户；未来同步必须是独立可选边界。

## 实现范围

- 既有 `/api/v1/optimize` offline 路由保留 optional account 逻辑，无 `Authorization` 也可执行本地规则优化。
- 新增 `OptionalSyncService`，默认 `enabled=False`，本地状态标记为 `local_only=True`；只有显式启用、显式账户 token 和注入 transport 同时存在时才允许同步。
- Provider 凭据仍通过 RC-179 的 SecretStore/opaque reference 管理，账户 token 由 `AuthService`/账户存储管理，本地配置与模型路由保持 workspace/app-data 边界；同步模块不读取 Provider SecretStore。
- 前端 onboarding 与 workspace home 保留 API/local 两个入口，guest/local 路线不先决登录；本地路线显示和测试不依赖账户 token。

## 验证

RC-183 专项：`3 passed`。

- 匿名 offline API 优化成功，响应 Provider 为 `offline`。
- 默认关闭同步拒绝 push，且不要求账户授权。
- 启用同步时无显式账户授权会拒绝。
- 联合后端回归：`129 passed, 1 skipped`。
- 前端 onboarding/workspace 本地入口回归：`7 passed`；ESLint、TypeScript/Vite build、定向 Ruff、定向 Mypy、Python `compileall` 通过。

## 限制

- 未发送真实 Provider 或同步请求，未产生费用。
- 跨设备同步 transport、账户服务和具体云端 API 仍未实现，必须在未来保持独立授权边界。
- 既有数据目录迁移 warning 保留，不影响本地路径验证。
