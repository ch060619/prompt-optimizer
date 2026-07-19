# RC-134 执行证据

- RC ID: RC-134
- 状态：已完成布局决策
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-133
- 设计文件：`docs/design/rabbit-prompt-optimization-placement.md`

## 已交付

- 对“发送旁并列”“上下文左、动作右”“输入框内尾部”三种布局进行比较，选择“上下文左、动作右”。
- 锁定星星按钮位于发送按钮左侧的次级动作组；模型选择、附件、语音属于左侧上下文组，发送保持唯一主色主操作。
- 锁定桌面、小窗和窄屏三档响应式规则，保证长模型名不会把星星或发送推出视口；按钮命中区固定为至少 `40px`。
- 锁定 DOM/键盘顺序：模型选择 → 附件 → 语音 → 星星 → 发送；星星不隐式提交 composer，发送仍是唯一 submit 动作。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 设计评审 | PASS：三方案的主次、误触风险、长模型名和窄屏行为均有记录；方案 B 通过 | `docs/design/rabbit-prompt-optimization-placement.md` |
| 当前 Task composer 视觉基线人工检查 | PASS：现有发送按钮右下锚点稳定；方案 B 只在其左侧预留次级动作槽位，不改变会话栏、对话区和 inspector 轨道 | `output/playwright/rc-133-workspace-task-dark-1x.png` |
| 交互路径审查 | PASS：模型/附件/语音属于上下文组，星星/发送属于动作组；Escape 返回触发控件、星星不提交、发送提交等后续实现边界已锁定 | `docs/design/rabbit-prompt-optimization-placement.md` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 15 test files、62 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-134/README.md` |

## 未解决项与后续

- Trae 参考图未在当前工作树提供，未伪造图像来源或像素级复刻；本项按执行卡文字约束和 Rabbit Code 自有视觉系统完成布局决策。
- 本项只锁定位置、层级、点击路径和响应式规则；RC-135 实现 idle/loading/success/error 等状态，RC-136 实现 Tooltip 和可访问命名，RC-137 以后实现优化请求、取消、结果和历史。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-134 完成后自动读取并继续 RC-135。

## 回滚

- 需要回滚的本项文件：删除布局评审、证据和计划/追踪登记；不回滚 RC-133 视觉回归契约和页面截图。
