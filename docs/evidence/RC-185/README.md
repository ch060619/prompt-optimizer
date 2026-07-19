# RC-185 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-184
- 目标：提供 Windows PowerShell、Linux Shell 包装脚本，并由 CLI/GUI 共享可重入的本地模型安装事件和状态核心。

## 实现范围

- `LocalInstallCore` 持久化 `install-state.json`，以 `download -> verify -> install -> ready` 状态推进；分片写入使用 fsync，安装使用临时文件原子替换。
- 支持许可证确认、暂停/恢复、取消、SHA-256 校验、runner 状态、重复启动/重复安装幂等和结构化 JSON 事件。
- `scripts/local_model_install.py` 是 JSON CLI；`scripts/install-local-model.ps1` 与 `scripts/install-local-model.sh` 只负责解释器、路径和参数包装。
- GUI 本地安装向导消费与核心一致的 `event/message/state` 事件字段，状态映射覆盖下载、暂停、恢复、校验、取消和健康检查流程。
- 模型 ID 限制为安全文件名，校验完成后禁止继续向分片文件追加下载内容。

## 验证

- RC-185 后端专项：`4 passed`。
- RC-149 + RC-185 本地模型关联回归：`15 passed`。
- 前端 RC-185 专项：`5 passed`；前端全量：21 个测试文件、`98 passed`。
- Windows PowerShell 包装脚本启动/查询状态实测通过；Python CLI 在未显式设置 `PYTHONPATH` 时也能返回 JSON 状态。
- ESLint、TypeScript、Vite production build、定向 Ruff、严格 Mypy、Python `compileall` 和 `git diff --check` 通过。

## 限制

- 当前环境没有 `sh`/`bash`，Linux Shell 包装脚本未在 Linux 实机执行；脚本保持 POSIX `sh` 语法，并选择 `python3` 或 `python`。
- 验证使用小型模拟源文件，未下载或提交 Gemma/Qwen 权重，也未发送网络请求；真实下载源、重试和镜像策略留给 RC-191。
- GUI 测试运行在浏览器 jsdom，验证共享 JSON 事件协议和状态行为；桌面壳到本地 sidecar 的真实进程绑定留给后续桌面集成门禁。
- 既有前端 jsdom navigation stderr 和路径迁移 warning 保留，不影响本项通过。
