# RC-193 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-192
- 目标：安装后执行脱敏健康检查，只有全部必选检查通过才允许进入 `ready`。

## 实现范围

- 新增 `run_health_check()`，按固定顺序检查 runner 版本、模型加载、最小生成、流式增量、取消、上下文探针、停止后重载和资源峰值。
- `HealthReport` 以原子替换方式保存 JSON；报告只包含模型 ID、runner 版本、检查结果和资源数值，不保存健康探针或用户提示词。
- `LocalInstallCore` 支持 `health_check_required`：安装后进入 `health_check`，报告全部通过才转为 `ready`；任一检查失败或资源探针不可用时转为 `failed`，阻止运行。
- In-memory runner 实现版本查询和取消检查，继续作为当前无网络环境的确定性测试替身。

## 验证

- `backend/tests/test_rc193_health.py`、RC-185、RC-187 联合专项：`8 passed`。
- RC-149 至 RC-193 关联后端回归：`190 passed, 2 skipped, 50 warnings`；warning 为既有路径迁移提示。
- 定向 Ruff、严格 Mypy 和 Python 编译通过。

## 限制

- 当前健康检查使用 in-memory runner；真实 Ollama/llama.cpp 版本、权重加载、流式取消和多平台资源峰值未在当前 Windows 环境执行。
- 上下文检查使用内部探针字符串，不代表每个真实模型 tokenizer 的完整极限容量；真实 runner 适配器接入时需复用同一报告契约并提供实际上下文边界。
