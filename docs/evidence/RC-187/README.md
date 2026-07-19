# RC-187 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-186
- 目标：选择默认本地运行器并建立不绑定 Ollama/llama.cpp 特有命令的生命周期 Adapter。

## 实现范围

- 新增 `LocalRunnerAdapter`，统一 `pull`、`load`、`generate`、`stream`、`stop`、`list`、`remove` 和 `health`。
- `RunnerRegistry` 暴露 `ollama` 默认 runner 与 `llama-cpp` 替代 runner；确定性内存适配器用于免费契约测试，不发网络请求、不加载权重。
- `RUNNER_COMPARISON` 记录许可证、安装、GPU、API 和维护取舍；ADR-0014 选择 Ollama 默认，并明确真实进程适配器的后续边界。
- 旧 `LocalModelRunner` 的生成协议保持兼容，Agent Core 未加入 runner-specific command。

## 验证

- RC-187 专项：`2 passed`。
- RC-149 local Provider + RC-187 runner 回归：`13 passed`，保留 11 个既有路径迁移 warning。
- 定向 Ruff、严格 Mypy、Python `compileall` 通过。
- 两个 runner 均覆盖未安装拒绝、pull、load、health、生成、流式、stop、list 和 remove 全生命周期。

## 限制

- 本项验证使用内存适配器；真实 Ollama HTTP 和 llama.cpp 进程/二进制调用留给模型清单、健康检查和资源控制完成后的后续 RC。
- 两个 runner 的许可证和固定来源记录沿用 `docs/research/local-model-license-manifest.yml`，未下载或打包 runner/model 权重。
