# RC-040 CLI/GUI/无头一致性矩阵

RC IDs: RC-040

## 状态与范围

状态：`defined-not-implementation-validated`。本文件冻结三种表面的产品能力边界，不声明 Rabbit Code Agent Core、最终 GUI、Provider 或会话 Schema 已实现。机器可校验登记见 `docs/product/capability-matrix.yml`，校验器见 `scripts/check_capability_matrix.py`。

三种表面定义为：CLI/TUI 负责交互终端和 JSON/JSONL；GUI 负责桌面渲染和系统集成；无头模式负责无 TTY 的脚本/CI。三者必须调用同一核心服务和事件/存储契约。

## 一致性规则

- Agent、Provider、权限、工具、会话、任务和 PromptOptimizationService 只有一份核心边界。
- 事件只能从 `agent-event-v1`、`content-block-v1` 和 `optimization-event-v1` 产生；表面不能创建私有业务事件。
- 存储只能从 `workspace-v1`、`session-v1`、`provider-v1`、`prompt-optimization-v1` 和 `settings-v1` 选择；表面不能复制一套数据库或 Schema。
- CLI、GUI 和无头的差异限于输入/输出传输、渲染和取消方式。窗口、拖放、系统通知是 GUI 专属，并且必须由共享事件/内容块派生。
- 无头模式没有可交互提示；需要批准时返回机器可读状态/退出码，不能静默放行或跳过。

## 能力矩阵

| 能力 | 共享契约 | 存储 | CLI/TUI | GUI | 无头 | 差异理由 |
| --- | --- | --- | --- | --- | --- | --- |
| 工作区发现 | `workspace-runtime-v1`/`agent-event-v1` | `workspace-v1` | 终端状态 | 工作区首页 | JSON 状态 | 同一发现服务，不同渲染 |
| 上下文搜索/内容块 | `context-runtime-v1`/`content-block-v1` | `session-v1` | 路径、搜索、stdin | 选择、预览、拖放 | JSON 引用 | 拖放只改变 GUI 输入方式 |
| Agent 循环 | `agent-runtime-v1`/`agent-event-v1` | `session-v1` | 进度和工具卡 | 时间线和任务卡 | JSONL 事件 | 状态和终态唯一 |
| Plan/Edit/高权限 | `permission-runtime-v1`/`agent-event-v1` | `workspace-v1` | 批准命令 | 审批面板 | 策略参数/退出码 | 交互载体不同，能力集合相同 |
| 工具与审批 | `tool-runtime-v1`/`agent-event-v1` | `session-v1` | 终端批准 | 弹窗批准 | 策略决策 | Schema 和审计唯一 |
| 终端命令/进程 | `process-runtime-v1`/`content-block-v1` | `session-v1` | PTY/子进程 | 终端面板 | 非 TTY 捕获 | 仅传输方式不同 |
| Git/diff/检查点 | `change-review-v1`/`content-block-v1` | `session-v1` | 文本 diff | 可视 diff | JSON diff | 变更归属唯一 |
| 会话/历史/恢复 | `session-runtime-v1`/`agent-event-v1` | `session-v1` | 命令恢复 | 恢复向导 | session ID | 同一检查点和审计链 |
| 任务/进度/取消 | `task-runtime-v1`/`agent-event-v1` | `session-v1` | Ctrl+C | 取消按钮 | 信号/退出码 | 取消令牌唯一 |
| Provider/模型 | `provider-runtime-v1`/`agent-event-v1` | `provider-v1` | 参数/配置 | 模型选择器 | 配置引用 | 同一能力和错误分类 |
| 菱形星星优化 | `prompt-optimization-v1`/`optimization-event-v1` | `prompt-optimization-v1` | 子命令/JSON | 星星、比较、采用 | JSON 事件 | revision/fallback 唯一 |
| 本地模型/离线规则 | `local-model-runtime-v1`/`optimization-event-v1` | `provider-v1` | 选择/状态 | 安装/健康 UI | 离线结果/错误 | 运行器和降级语义唯一 |
| 测试/诊断 | `diagnostics-v1`/`content-block-v1` | `session-v1` | 稳定行/退出码 | 文件行号组件 | 诊断 JSON | 字段相同，布局不同 |
| 导出/隐私/审计 | `export-runtime-v1`/`content-block-v1` | `settings-v1` | 显式导出 | 预览/确认 | 格式参数 | 脱敏和审计规则唯一 |
| 窗口管理 | GUI 专属 | 无 | 不适用 | 窗口/焦点/菜单 | 不适用 | 桌面壳系统集成 |
| 拖放/桌面附件 | `content-block-v1` | `session-v1` | 路径/stdin 替代 | 拖入后统一内容块 | JSON 引用替代 | 只改变 GUI 手势 |
| 系统通知 | `agent-event-v1` | `settings-v1` | 终端/退出码替代 | 共享事件派生通知 | JSON/日志替代 | 不产生独立业务状态 |

完整字段、状态枚举、依赖 RC 和唯一 Schema 登记以 YAML 为准；表格不另定义协议。

## 验证卡

| 卡片 | 检查 | 通过条件 | 当前状态 |
| --- | --- | --- | --- |
| RC040-01 | 同一请求走 CLI、GUI、无头 | 输入、Provider、权限、事件序列、结果和错误语义一致，仅渲染/传输不同 | planned |
| RC040-02 | 事件夹具重放 | 三种表面消费同一事件夹具，不能产生私有业务字段或不同终态 | planned |
| RC040-03 | 存储 Schema 对账 | 会话、任务、Provider、优化和设置只对应登记的唯一 Schema | planned |
| RC040-04 | GUI 专属边界 | 窗口、拖放、通知不出现在 CLI/无头业务契约；其派生内容仍使用共享 Schema | planned |
| RC040-05 | 无头无交互 | 无 TTY 缺少批准时返回机器可读状态和稳定退出码，不等待或静默放行 | planned |

## 现有仓库迁移说明

当前 V2 FastAPI 已有 `/api/v1`、SSE 优化、任务、历史、diff 和导出契约；这些是 RC-046/048/050/051/053 的既有资产，不等同于最终 Agent Core 事件。后续实现必须把兼容 API 适配到本登记的共享服务，不能为 GUI、CLI、无头分别复制业务逻辑。
