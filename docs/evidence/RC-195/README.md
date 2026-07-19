# RC-195 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-194
- 目标：支持全局默认本地模型和按会话覆盖，并保证选择、请求 metadata 与历史版本一致。

## 实现范围

- 新增 `localModelSelection.ts`，固定 Gemma 3 1B IT 与 Qwen2.5-Coder 1.5B 的内部 ID、完整源 ID 和 context length。
- 本地模型加载成功及 Workspace Home 本地选择会写入全局默认；`workspace` + `session`/`task` 参数形成会话覆盖键，不会污染默认值或其他会话。
- Workspace 主编辑页增加 Session Model 控件；仅 `ready`/`busy` 模型可切换，提示词超过模型 context length 或当前生成进行中时拒绝/禁用切换。
- 优化、流式和后台请求统一使用最终会话选择；已有 Provider metadata、version history 保存实际 `model` 与 `selection_scope`，后端专项验证 Gemma/Qwen 两次版本记录不串值。

## 验证

- `backend/tests/test_rc195_local_model_selection.py`：1 passed。
- RC-148/RC-172/RC-195 后端关联专项：10 passed，8 warnings。
- `frontend/tests/LocalModelSelection.test.tsx`：3 passed；App/Workspace/Task/LocalModels 关联测试：28 passed。
- 前端 ESLint、TypeScript/Vite build 通过。

## 限制

- 未执行真实 Ollama/llama.cpp 权重加载；当前切换门控依赖持久 GUI 状态和后端已有 Provider/model 选择契约，真实 runner 多模型装载由后续运行时 RC 覆盖。
