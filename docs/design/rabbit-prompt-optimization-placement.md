# Rabbit Code 菱形星星布局评审

- RC ID: RC-134
- 状态：已完成布局决策；交互状态和优化请求留给 RC-135 至 RC-146
- 评审基线：Rabbit Code 当前 `TaskWorkspace` composer；桌面 `1280x1000`、小窗 `640x844` 和移动窄屏规则
- 参考假设：用户提到的 Trae 截图未随当前工作树提供，因此本记录只采用执行卡中的“模型选择、语音、附件、发送”关系和 Rabbit Code 已有 token/图标/无障碍规则，不复制外部品牌布局或资产

## 方案比较

| 方案 | 位置 | 优点 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| A：发送旁并列 | `Sparkles` 紧贴主发送按钮，位于 composer footer 右侧 | 路径短，优化与发送属于同一操作组 | 两个相邻动作都很强；星星容易被误认为发送或被误点 | 不采用 |
| B：上下文左、动作右 | 模型选择、附件、语音在 footer 左侧；`Sparkles` 与发送同在右侧，但以次级描边按钮和主色发送按钮分级 | 保留现有发送锚点；模型/附件/语音保持上下文关系；星星靠近发送但不抢主层级 | 小窗需要把上下文组和动作组分行 | **采用** |
| C：输入框内尾部 | `Sparkles` 放在 textarea 右下角，与附件/语音叠放 | 桌面占用空间小 | 长文本、调整大小、屏幕阅读器和触控命中区容易互相影响 | 不采用 |

## 锁定布局

```text
composer
  textarea
  footer
    context-group: [model selector] [attachment] [voice]
    action-group:  [prompt optimization / Sparkles] [send]
```

- `footer` 是 composer 的稳定边界；不能把星星放进可编辑文本区域，也不能让装饰 Rabbit 槽位承担交互。
- context group 使用 `minmax(0, 1fr)`，模型名允许换行或省略，不得把 action group 推出视口。
- action group 的发送按钮保留唯一主色填充；星星使用描边/次级层级，固定 `40px` 高度和 `40px` 宽度，避免加载状态造成布局跳动。
- desktop 的主操作顺序是“模型/附件/语音 → 星星 → 发送”；星星始终位于发送左侧，不与发送重叠。
- 星星在后续实现中必须是独立 `button`，不能隐式提交 composer；发送按钮仍是唯一 `type="submit"`。

## 响应式规则

| 视口 | 规则 |
| --- | --- |
| `>= 901px` | footer 单行；context group 靠左，action group 靠右；两组之间使用 `justify-content: space-between` 和至少 `12px` 间距。 |
| `641px - 900px` | footer 允许换行；context group 保持完整一组，action group 不拆分；模型选择可占满 context group 的剩余宽度。 |
| `<= 640px` | footer 分为 context 行和 action 行；模型选择占 context 行剩余宽度，附件/语音保持固定命中区；星星与发送保持同一 action 行。 |
| 所有视口 | 不使用基于 viewport 的字体缩放；按钮最小命中区 `40px`；长模型名 `overflow-wrap:anywhere`，不得产生横向溢出。 |

## 键盘与点击路径审查

1. 从 textarea 继续 Tab，顺序为模型选择、附件、语音、星星、发送；DOM 顺序与视觉分组一致。
2. 打开模型选择、附件或语音浮层后，Escape 关闭并把焦点还给触发按钮；浮层不覆盖星星或发送。
3. 触发星星只进入优化状态，不提交表单；触发发送才提交当前草稿。
4. 触控检查按左侧上下文组、右侧动作组分别命中；星星与发送之间保留可辨识间隔，不使用仅颜色区分。

## 评审结论

- 方案 B 通过设计评审：它把“选择上下文”和“执行动作”分成两个清晰组，同时满足星星靠近发送但不冒充发送的要求。
- 在当前桌面 Task 截图上，composer 的发送按钮已有稳定右下锚点；本决策只在其左侧预留次级动作槽位，不改变对话、会话栏或 inspector 的布局轨道。
- 后续 RC-135 负责状态机和固定尺寸；RC-136 负责 Tooltip/可访问命名；RC-137 以后负责请求、取消、结果和历史行为。本项不提前实现这些行为。

