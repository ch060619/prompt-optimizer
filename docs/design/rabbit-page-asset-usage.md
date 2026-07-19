# Rabbit 页面级素材用法矩阵

- RC ID: RC-124
- 状态：规划完成；实际源素材授权与派生物生成由 RC-122/RC-123 解除后执行
- 设计原则：Rabbit Code 是高效编码工具，素材用于品牌识别和状态提示，不覆盖代码、diff、终端、对话输入或关键操作。

## 页面矩阵

| 页面/路由 | 变体 | 位置 | Desktop 基准 | 小窗口行为 | 主题 | 替代文本 |
| --- | --- | --- | --- | --- | --- | --- |
| Public home `/` | `full` | 首屏主视觉右侧 | 643x684，保留 8% 安全区 | 缩至 320px 高，保持主体可见 | light/dark | `Rabbit Code 兔兔品牌插画` |
| Login/Register | `full` | 认证页左侧视觉区 | 最大 325px 高 | 移到表单上方，最小 220px 高 | light/dark | `Rabbit Code 兔兔品牌插画` |
| Onboarding `/onboarding` | `full` | 首次启动 hero artwork | 643x684，标签不压图 | 小窗口使用 220-260px 高 | light/dark | `Rabbit Code 兔兔品牌插画` |
| Workspace `/workspace` | `avatar`/`mark` | 左侧品牌栏 | mark 64px，完整形象仅在宽栏 | 小窗口隐藏大图，保留 32px mark | light/dark | `Rabbit Code 品牌标记` |
| Workspace home `/workspace/home` | `empty` | 空项目/空任务状态 | 最大 240x160 | 随内容列宽收缩 | light/dark | `暂无项目的兔兔插画` |
| Task `/workspace/task` | `mark` | 页面角落/非 composer 区 | 48-64px | 32px，不进入输入区 | light/dark | `Rabbit Code 品牌标记` |
| Review/Terminal | `mark`/`mono` | 标题栏或空状态 | 32-64px | 24-32px | light/dark/high contrast | `Rabbit Code 品牌标记` |
| Providers/Models/Assets/Settings/Diagnostics | `mark`/`empty` | section heading 或空状态 | 32-160px | 24-96px | light/dark | 说明实际状态，不只读装饰 alt |

## 禁入区

- 代码、diff 和 terminal 输出区域不得出现覆盖内容的 watermark；素材与文本边界至少保留 16px。
- Task composer、prompt textarea、provider/API key 输入、权限/安装弹窗的按钮和焦点环不得被素材覆盖。
- 任何素材不能覆盖发送、优化、接受/拒绝、停止、重试、保存和删除操作的点击区域。
- 在 200% 缩放、高对比和 `prefers-reduced-motion` 下，素材不能改变内容阅读顺序、焦点顺序或可点击面积。
- `mono` 变体必须有清晰对比度；无法辨识时使用文字品牌标记，不强行显示装饰图。

## 验收清单

1. 每个独立路由在矩阵中只有一个主素材槽位，弹窗和面板不机械重复。
2. 每个槽位记录变体、尺寸、主题、响应式行为和替代文本；不依赖桌面外部路径。
3. Desktop、小窗口、light/dark、200% zoom 和 high-contrast 逐页检查无重叠、无溢出、无裁切主体。
4. 代码、diff、terminal、composer 和关键按钮区域人工确认内容对比度与可操作性不下降。
5. RC-122 源素材注册、RC-123 派生导出和 RC-133 视觉回归通过后，才把当前规划状态升级为发布资产验收。

## 当前实现对照

现有代码已在 public home、认证、onboarding 和主 workspace 使用仓库内 `rabbit-artwork.png`；
其余工作页的页面级 RabbitMark 由 RC-125 接入。本文件是使用边界和验收矩阵，不宣称当前
外部源素材授权或所有路由的视觉回归已经完成。
