# RC-190 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-189
- 目标：审核并锁定首发 Gemma 版本、模板、EOS 和许可证约束。

## 实现范围

- 受控 Gemma 条目固定为 `google/gemma-3-1b-it`，revision 和 SHA-256 沿用 RC-031 固定登记。
- Manifest 增加 `gemma-3` chat template、`<end_of_turn>` EOS、model-card 状态、template 审核状态和许可证约束；Gemma Terms 继续要求下载前用户确认。
- `gemma_model()` fail-closed 选择器和生成 smoke 绑定 manifest 的完整 model ID；GUI 对齐为 Gemma 3 1B IT 并显示完整源 ID。
- ADR-0015 记录选择理由：首发使用受控清单中资源最小的 reviewed Gemma 候选，较大版本需要新的审核条目。

## 验证

- RC-188 + RC-189 + RC-190 backend 回归：`5 passed`；RC-186 至 RC-190 联合专项：`10 passed`。
- Gemma 专项覆盖固定 ID、family、chat template、EOS、许可证 gate、runner health 和生成 smoke。
- 前端 local model 专项：`5 passed`；前端全量：21 个测试文件、`98 passed`。
- ESLint、TypeScript、Vite production build、定向 Ruff、严格 Mypy、compileall 通过。

## 限制

- 真实 Gemma 权重、真实 runner 模板/EOS 生成和模型卡全文审查未在当前环境执行；当前 smoke 使用无网络内存 runner。
- Gemma gated 条款仍是下载前用户确认项，manifest 不包含权重或再分发授权。
