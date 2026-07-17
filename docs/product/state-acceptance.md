# RC-042 功能状态验收矩阵

RC IDs: RC-042

## 范围

本矩阵以 RC-040 的 17 项能力为功能闭集。每项功能都必须记录成功、失败、取消、重试、降级、离线、拒绝和恢复八种状态；状态描述是验收口径，不代表当前实现已经通过。

统一状态、错误码和 UI 文案登记在 [`state-acceptance.yml`](state-acceptance.yml)。每项能力至少有一个非成功测试参数，测试参数默认使用本地夹具、Mock、Loopback 或离线规则，不需要付费资源或真实 API Key。

## 统一状态契约

| 状态 | 终态 | 错误码 | UI 文案 |
| --- | --- | --- | --- |
| 成功 | 是 | 无 | 已完成 |
| 失败 | 是 | `RC42-FEATURE-FAILED` | 执行失败 |
| 取消 | 是 | `RC42-TASK-CANCELLED` | 已取消，已保留已完成内容 |
| 重试 | 否 | `RC42-RETRY-AVAILABLE` | 可以重试 |
| 降级 | 是 | `RC42-DEGRADED` | 已降级，来源和限制已标明 |
| 离线 | 是 | `RC42-OFFLINE` | 离线模式 |
| 拒绝 | 是 | `RC42-PERMISSION-DENIED` | 操作已拒绝 |
| 恢复 | 是 | `RC42-RECOVERED` | 已从检查点恢复 |

错误码的 `class`、是否可重试和消息模板必须从 YAML 目录读取；界面可以换布局，但不能改变状态语义或隐藏来源、权限和限制。

## 功能覆盖

| 能力 | R 映射 | 核心场景 | 非成功参数 |
| --- | --- | --- | --- |
| 工作区发现 | R1/R5 | 打开仓库 | `RC042-workspace-discovery-failure` |
| 上下文搜索与内容块 | R1/R5 | 阅读代码、编码任务 | `RC042-context-assembly-denied` |
| Agent 状态与模型循环 | R1/R5 | 编码任务、规划任务 | `RC042-agent-loop-cancel` |
| Plan/Edit/高权限 | R1/R5 | 规划任务、编辑文件 | `RC042-permission-denied` |
| 工具调用与审批 | R1/R5 | 编码任务、运行命令 | `RC042-tool-approval-denied` |
| 终端命令与进程 | R1/R5 | 运行命令 | `RC042-terminal-process-cancel` |
| Git、diff、检查点和回滚 | R1/R2/R5 | 编辑文件、审查 diff | `RC042-git-diff-failure` |
| 会话、历史和恢复 | R1/R3/R5 | 恢复会话 | `RC042-session-recovery-failure` |
| 任务、进度和取消 | R1/R3/R5 | 编码任务、运行测试 | `RC042-task-cancel` |
| Provider、模型和能力协商 | R3/R4/R6 | 切换模型、编码任务 | `RC042-provider-denied` |
| 菱形星星提示词优化 | R2/R3/R5/R6 | 优化提示词 | `RC042-optimization-revision` |
| 本地模型与离线规则 | R3/R4/R5 | 离线对话 | `RC042-local-model-offline` |
| 测试、Lint、类型和诊断 | R1/R5 | 运行测试、审查 diff | `RC042-diagnostics-failure` |
| 导出、隐私和审计 | R1/R3/R5 | 审查 diff、恢复会话 | `RC042-export-denied` |
| 桌面窗口管理 | R2 | 打开仓库、编码任务 | `RC042-window-recovery` |
| 文件拖放与桌面附件 | R2/R3 | 阅读代码、优化提示词 | `RC042-drag-drop-denied` |
| 系统通知与桌面集成 | R2/R5 | 编码任务、恢复会话 | `RC042-notification-degraded` |

每项能力的八种具体期望、统一错误码和可执行参数集以 YAML 为唯一机器源；不在 Markdown 表格重复定义第二套状态枚举。

## 验收规则

- 成功之外的任何状态都必须保留原因、来源、权限或恢复线索；不能用成功文案覆盖降级、离线、拒绝和取消。
- 取消和失败不得丢失原输入、已完成安全结果或检查点；重试不得重复未经确认的副作用。
- 无头模式没有交互批准时返回机器可读拒绝/等待状态；GUI 专属窗口、拖放和通知只能从共享事件/内容块派生。
- 每个关键能力至少执行一个非成功参数；真实 Provider、真实本地模型、Windows/Linux 实机和完整 E2E 由后续实现/测试 RC 记录。

机器校验器见 [`check_state_acceptance.py`](../../scripts/check_state_acceptance.py)。
