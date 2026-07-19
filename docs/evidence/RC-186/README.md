# RC-186 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`（未提交工作树）
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-185
- 目标：生成包含 OS、架构、CPU、RAM、磁盘、GPU/显存/驱动、网络、代理和本地运行器的稳定 JSON 硬件报告。

## 实现范围

- 新增 `HardwareDetector` 和 `HardwareReport`；每个字段都包含 `value`、`source` 和 `confidence`，输出不含时间戳并通过排序键保持稳定。
- 使用平台 API、`/proc`、磁盘 API、GPU CLI、PATH 和受控 DNS 探针进行 best-effort 检测；权限不足、命令不可用和读取失败降级为 `null`/空集合/低置信度。
- 代理只报告脱敏 scheme/host/port 和 `NO_PROXY`，不输出代理用户名或密码；运行器覆盖 Ollama 和 llama.cpp 的 `llama-server` 探测。
- `scripts/hardware_report.py` 支持 `--override-json`，用户可纠正不可检测字段，非法 JSON 以参数错误退出。

## 验证

- RC-186 专项：`3 passed`。
- RC-149 + RC-185 + RC-186 关联回归：`18 passed`，保留 11 个既有路径迁移 warning。
- 夹具覆盖稳定 JSON、GPU 显存/驱动解析、Ollama 发现、代理凭据脱敏、用户覆盖、网络失败、文件权限失败和 PATH 权限失败。
- 定向 Ruff、严格 Mypy、Python `compileall` 通过；CLI 实测输出结构化 JSON，非法 override JSON 以 argparse 错误退出。
- 前端全量：21 个测试文件、`98 passed`；RC-185 已验证的 ESLint、TypeScript 和 Vite build 基线保持通过。

## 限制

- 当前为 Windows 环境，未在 Linux 实机执行 `/proc`、GPU 驱动和 runner 命令矩阵；权限和不可用分支使用注入探针验证。
- 网络字段只做 DNS 可达性探测，不发送 Provider 请求；真实硬件推荐和 runner 选择留给 RC-187/RC-188。
- 报告不持久化用户纠正值；当前 `--override-json` 是单次修正入口，持久化设置留给后续配置/GUI 接线。
