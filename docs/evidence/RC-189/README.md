# RC-189 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-188
- 目标：固定受控的 Qwen2.5-Coder 路线，避免以模糊的“Qwen 最新版”替代用户要求。

## 实现范围

- Manifest 唯一 Qwen 条目固定为 `Qwen/Qwen2.5-Coder-1.5B-Instruct`，family 固定为 `Qwen2.5-Coder`，并绑定 revision、SHA-256、上下文、资源和 `qwen2` chat template。
- 新增 `qwen_coder_model()` fail-closed 选择器；Qwen 生成冒烟从该 manifest 取完整 ID，加载默认 runner 后通过 `LocalModelProvider` 生成。
- GUI 本地模型目录改为受控的 `qwen2.5-coder-1.5b-instruct` 内部 ID，详情页和安装向导显示完整源 model ID。

## 验证

- RC-189 后端 family/health/generation smoke：`1 passed`。
- RC-188 manifest + RC-189 Qwen 回归：`4 passed`。
- 前端 local model/Qwen identity 专项：`5 passed`；前端全量：21 个测试文件、`98 passed`。
- ESLint、TypeScript、Vite production build、定向 Ruff、严格 Mypy、compileall 通过。

## 限制

- 生成冒烟使用无网络内存 runner，不加载真实权重；真实模型文件和 runner 进程验证留给后续安装/健康 RC。
- Gemma 条目和许可证/模板审核由 RC-190 继续处理；未将 Qwen 条目替换为其他 family。
