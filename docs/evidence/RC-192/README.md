# RC-192 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-191
- 目标：禁止未经许可的模型权重进入安装包，并在按需下载前展示和记录许可证确认版本。

## 实现范围

- 受控 manifest 为每个模型标记 `bundled`、`ondemand` 或 `manual` 分发策略；当前 Gemma 与 Qwen 条目均为 `ondemand`，且保留许可证摘要、原文 HTTPS URL 和确认版本。
- `license_prompt()` 提供 UI/CLI 所需的非敏感许可证摘要；`validate_license_confirmation()` 对拒绝、过期版本和正确版本 fail-closed。
- 下载状态持久化许可证确认版本、摘要和 URL；CLI、PowerShell/Shell 包装可以传递这些字段。
- `scripts/check_model_distribution.py` 对源树/包树执行权重后缀 denylist，并接入 `scripts/workspace.py check`；当前仓库扫描未发现模型权重文件。

## 验证

- `backend/tests/test_rc192_distribution.py`：`3 passed`；覆盖 manifest 分发策略、许可证确认版本、下载状态记录、未确认拒绝和权重 denylist。
- RC-188/RC-191/RC-192 联合专项：`14 passed`；定向 Ruff、严格 Mypy、Python 编译和 workspace 追踪/分发门禁通过。

## 限制

- 当前仓库没有生成真实安装包或 SBOM；denylist 已作为源码/构建前门禁执行，实际发布产物审计仍需在打包流水线中运行。
- manifest 的确认版本是仓库审计标识，不替代用户阅读许可证原文；Gemma 条款仍要求下载前明确确认。
