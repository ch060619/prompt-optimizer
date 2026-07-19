# RC-184 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-183
- 目标：提供 Provider credential 删除、配置迁移、全部本地数据清理和明确的删除/保留确认流程。

## 实现范围

- `LocalDataCleanupService.preview()` 读取将删除的 SQLite、backup、FileStore、config 路径和 opaque credential 数量，并明确保留应用安装文件。
- `clear_all(confirm=False)` 只返回 cancelled，不触碰文件或 SecretStore；确认后先校验 process guard，再删除 SecretStore references，并对文件进行覆盖、fsync、unlink。
- `migrate_opaque_config()` 只迁移 opaque `env:`/`keychain:` 或已有 SecretStore references，检测到敏感字段明文时拒绝。
- `/api/v1/data/cleanup/preview` 与 `/api/v1/data/cleanup` 接入生成 API；Settings Data 页提供预览、取消和危险确认对话框，确认后清理本地浏览器状态并退出 token。
- `delete_provider_credential()` 提供单 credential 删除边界；既有 Provider UI 的迁移删除流程继续保留引用完整性。

## 验证

RC-184 清理/API 合约专项：`10 passed`，其中清理专项 `4 passed`。

联合后端回归：`139 passed, 1 skipped`，覆盖 RC-064、RC-160 至 RC-173、RC-179 至 RC-184。

前端全量：21 个测试文件、`98 passed`；覆盖 Settings 预览、取消不变更和确认清理；ESLint、TypeScript/Vite build、OpenAPI generated drift、定向 Ruff、定向 Mypy、Python `compileall` 通过。

## 限制

- 未发送真实 Provider 或同步请求，未产生费用。
- 当前 process guard 是清理服务注入边界；生产桌面集成必须在停止相关 worker/sidecar 后调用确认清理。
- Windows/Linux 两个平台的原生文件擦除和 Keychain 实机矩阵仍需各平台运行环境；现有 Windows SecretStore round-trip 已在 RC-179 记录。
