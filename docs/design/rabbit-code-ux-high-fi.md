# Rabbit Code 多尺寸高保真规格

<!-- RC ID: RC-255. Geometry is explicit so implementation does not guess. -->

## 基线与约束

| 基线 | 视口 | 关键布局 | 适用页面 |
| --- | --- | --- | --- |
| Desktop | 1440 x 1100 CSS px | 工作区侧栏 230px；主区 `minmax(0, 1fr)`；输入区最大 1190px | 首页、工作区、Review、Terminal、Provider、模型、设置、诊断 |
| Compact | 390 x 844 CSS px | 侧栏转为顶部；四项导航四等分；首页快捷卡片两列；Composer 元信息纵向堆叠 | 所有工作页和入口页 |
| Screenshot 2x | 640 x 844 CSS px @2 | 等效 320 CSS px 内容宽度检查，保持同一折行规则 | 视觉回归与高密度文本 |

页面使用 `box-sizing: border-box`、`min-width: 0` 和稳定的 `min-height`。不可压缩的操作只允许增长高度或换行，不允许挤出视口。

## 工作区高保真规格

```text
Desktop 1440
+-----------230-----------+---------------------- main ----------------------+
| brand / new task         | hero / quick actions                         |
| primary navigation       |                                               |
| settings                 | composer max 1190: metadata / textarea / CTA |
+--------------------------+-----------------------------------------------+

Compact 390
+-------------------------------+
| brand                          |
| new task                       |
| skill | plugin | project | task|
| hero / quick actions (2 cols)  |
| composer                       |
| metadata rows                 |
| textarea                      |
| controls   star       SEND     |
+-------------------------------+
```

### Composer 状态

| 状态 | 文本区 | 星星动作 | 发送动作 | 结果区 |
| --- | --- | --- | --- | --- |
| Empty | 占位文案，不截断 | 禁用 | 禁用 | 不显示 |
| Ready | 164px 稳定高度 | 42px 图标按钮 | 48px 主按钮 | 不显示 |
| Optimizing | 保留快照文本 | 显示 busy/cancel | 禁用 | 单一 live region |
| Ready to compare | 保留当前新文本 | 可查看/重新优化 | 仍按当前输入判断 | 显示 revision 对比 |
| Success | 不自动写回 | success 状态 | 不自动触发 | 显示可编辑预览 |
| Error/fallback | 原文保留 | 可恢复 | 可恢复 | 错误码/降级原因/恢复动作 |

星星是独立次级图标动作，透明背景、42 x 42；发送是唯一显式主提交，金色背景、最小高度 48px，带图标和文字。两者之间固定 13px 间距，焦点环不改变布局尺寸。

## 长文案和中英文规则

- Provider 名、模型 ID、错误摘要和路径使用 `min-width: 0` 与 `overflow-wrap: anywhere`；列表行可以增高，不能产生横向滚动。
- 状态标签可换行；仅导航的短 uppercase 标签保留 `white-space: nowrap`。
- 中英文混排正文按 1.4 至 1.5 行高；代码、模型 ID、错误码使用 mono 字体和 1.2 至 1.35 行高。
- 深色主题只切换 `--paper`、`--ink`、`--line`、`--gold`、状态色等 token，不复制组件布局规则。
- 错误必须同时有可读描述和恢复动作，错误面板的边界/颜色来自 `--danger-*` token，不以颜色作为唯一信号。

## Token 对齐

规格引用 `packages/ui/tokens.json` 的 `--space-*`、`--radius-control`、`--icon-*`、`--focus-ring`、`--motion-duration` 和 Rabbit 尺寸/透明度 token。页面实现中已有的固定几何（Composer 164px、星星 42px、发送 48px、触控目标 44px）在截图和 DOM 检查中作为不漂移约束。

## 交付状态

本稿覆盖 Desktop/Compact、light/dark、Provider/模型长名、中文/英文、empty/loading/success/error/fallback/compare 状态。真实运行时的重叠、溢出、裁切和动态布局偏移由 RC-256 的 Playwright 证据验收，不在本稿中预先宣称通过。
