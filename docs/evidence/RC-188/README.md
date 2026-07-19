# RC-188 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-187
- 目标：建立不包含权重的版本化模型 manifest，并按硬件安全余量生成受控推荐。

## 实现范围

- `data/models/manifest.yml` 固定 Gemma 3 1B IT 与 Qwen2.5-Coder 1.5B Instruct 的完整 model ID、HTTPS 来源、revision、文件 SHA-256、参数量、量化、上下文、磁盘/RAM/VRAM、聊天模板和许可证状态。
- `load_manifest()` 校验 schema、HTTPS、固定 hash、正资源需求、许可证字段和布尔门控；未知模型默认不在受控清单内，只有显式 advanced 路径允许手动导入。
- `recommend_models()` 以默认 80% RAM/磁盘/VRAM 安全余量筛选，超限模型返回明确原因；许可证确认作为安装前原因保留，不改变资源安全判断。
- `scripts/check_model_manifest.py` 提供无权重 manifest 门禁和可复现推荐摘要。

## 验证

- RC-188 专项：`3 passed`。
- RC-186 + RC-187 + RC-188 联合专项：`8 passed`。
- Manifest CLI 输出：`Validated RC-188 model manifest: 2 models, 2 recommended.`
- 定向 Ruff、严格 Mypy、Python `compileall` 和 `git diff --check` 通过。

## 限制

- manifest 只登记来源和元数据，未下载、提交或打包模型权重；Gemma 许可证仍需用户在下载前确认。
- 推荐使用调用方提供的硬件容量，不持久化自动检测结果；真实模型家族/聊天模板生成冒烟留给 RC-189/190/193。
