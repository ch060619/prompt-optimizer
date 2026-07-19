# RC-194 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-193
- 目标：GUI 展示本地模型完整生命周期，并在重启后从后端持久状态、真实安装文件和运行器状态恢复。

## 实现范围

- 新增 `local_model_state.py`，固定 `not_installed`、`downloading`、`verifying`、`loading`、`ready`、`busy`、`stopping`、`unloaded`、`corrupt`、`update`、`failed` 状态及可达转换；非法跳转抛出 `LocalModelStateError`。
- `LocalInstallCore` 事件增加 `lifecycle_event`、`lifecycle_status` 和 `recovery_actions`，下载、校验、安装、健康检查、运行和失败事件可直接映射到 GUI 状态。
- FastAPI 新增 `/api/v1/local-models/{model_id}/state` 与 `/events`；事件状态原子保存，恢复时优先读取持久生命周期状态，否则读取 `install-state.json` 并检查已安装文件是否存在，缺文件不暴露为 `ready`。
- GUI 通过后端恢复事件和事件上报驱动模型状态；持久化兼容旧状态；`failed`/`corrupt` 均提供 `RETRY`、`REPAIR MODEL`、`UNINSTALL`。

## 验证

- `backend/tests/test_rc194_local_model_state.py`：7 passed。
- RC-185/RC-191/RC-194 关联专项：16 passed，2 warnings；warnings 为既有路径迁移提示。
- `frontend/tests/LocalModels.test.tsx`：6 passed。
- 前端 ESLint、TypeScript/Vite build、定向 Ruff 和 `scripts/generate_api.py --check` 通过。

## 限制

- 当前环境未启动真实 Ollama/llama.cpp、未下载模型权重，也未执行 Linux 或跨平台运行器实机恢复；使用持久 JSON、真实文件探针和 in-memory runner 契约验证恢复边界。
