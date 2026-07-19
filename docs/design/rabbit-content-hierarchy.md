# Rabbit 内容层级与密度门禁

- RC ID: RC-129
- 状态：工作页层级约束、装饰预算和 Review/Terminal 视觉检查已建立

## 内容优先级

| 层级 | 内容 | 视觉规则 |
| --- | --- | --- |
| 1 | 输入框、发送/停止/接受/拒绝/重试/保存/删除和错误操作 | 100% 对比度和可点击面积；不得被素材遮挡或降透明度 |
| 2 | 用户输入、代码、diff、终端输出、长文件名和长日志 | 100% 对比度；允许滚动和换行；优先保证扫描宽度和行高 |
| 3 | 连接、任务、测试、进程和离线状态 | 使用状态色和明确文本；不与装饰共享语义 |
| 4 | Rabbit 品牌标识和空状态插图 | 仅用于识别和空间提示；工作页标识不抢焦点、不接收点击、不进入读屏顺序 |

## 工作页装饰预算

| 场景 | Desktop | 小窗口 | 不透明度 | 约束 |
| --- | ---: | ---: | ---: | --- |
| task/review/providers/models/assets/settings/diagnostics mark | 56 x 56px | 32 x 32px | 0.16 | 固定右下角、`pointer-events: none`、`aria-hidden` |
| terminal mono | 56 x 56px | 32 x 32px | 0.12 | 深色终端中只作弱识别，不覆盖日志或命令输入 |
| workspace home empty | 192 x 128px | 内容列内收缩 | 0.20 | 只在空状态区域出现，不作为固定水印 |
| public/auth/onboarding full | 由页面矩阵控制 | 由页面矩阵控制 | 1.0 | 这些是页面主视觉，不套用工作页装饰预算 |

工作页固定标识的宽度不超过视口宽度的安全边界，移动端直接降到 32px；装饰图层不包含按钮、链接、表单或错误正文。素材的存在不能改变 composer、diff pane、terminal log 或 validation actions 的布局轨道。

## 密集内容检查夹具

视觉检查必须使用真实代码、长日志和 diff，而不是只有短占位文本：

- Review：包含 `backend/rabbit_code/agent.py`、测试 hunk、接受/拒绝操作和 validation sidebar。
- Terminal：包含长命令、进程状态、列/行控制、滚动日志、命令输入和停止/关闭操作。
- Task：包含长 prompt、长文件名、Plan/Diff/Context inspector 和 composer 发送按钮。

每个夹具检查 Desktop、窄窗口、浅色和深色主题：关键文本没有被遮挡，错误/状态可读，按钮仍可点击，Rabbit 标识不进入内容滚动区。移动端优先保留内容列宽，装饰只保留 32px mark 或 mono。

## 实现门禁

- `SiteShell` 给固定槽位标记 `data-rabbit-layer="decorative"` 和 `aria-hidden="true"`。
- CSS 只允许通过已登记的透明度和尺寸变量调整工作页装饰；禁止页面局部把装饰 opacity 提高到内容级别。
- `pointer-events: none` 是固定槽位的硬约束；任何需要交互的品牌入口必须使用独立按钮或链接，不复用装饰槽位。
- `RabbitMark` 的 `mark`/`mono` 使用独立 SVG；完整素材不进入代码、diff、终端和 composer 的内容层。
