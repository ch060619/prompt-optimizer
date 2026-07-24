# Rabbit Code 动效与资源预算

<!-- RC ID: RC-259. Animation is a state/space affordance, not decoration. -->

## 允许的动效

| 场景 | 用途 | 预算 | reduced-motion |
| --- | --- | --- | --- |
| Marketing reveal | 页面空间进入 | 一次性 700ms reveal | 完全跳过 |
| FAQ | 展开/收起答案 | 500ms 高度/箭头过渡 | 1ms 等效，无动画理解依赖 |
| Local model progress | 下载状态变化 | 200ms 宽度变化 | 1ms 等效 |
| Agents route transition | 禁用跨文档自动转场，避免与 SPA history 冲突 | 0ms | 禁用 |
| Rabbit route slot | 品牌识别 | 静态透明度和尺寸，无循环动画 | 不变 |

## 生命周期

```text
页面挂载
  -> prefers-reduced-motion? 是 -> 不创建 GSAP/Lenis/RAF
  -> 无 .reveal-on-scroll? 是 -> 不创建 GSAP/Lenis/RAF
  -> 有 reveal -> 创建一次 ScrollTrigger + Lenis
       -> visible 运行 RAF
       -> hidden 取消 RAF
       -> visible 恢复 RAF
       -> 卸载取消 RAF、销毁 Lenis、回滚 context
```

工作区、Provider、模型、设置、诊断、Task、Review 和 Terminal 没有
`reveal-on-scroll`，因此不会为一个静态工作页启动持续 RAF。所有状态反馈仍使用明确文本/状态色，动画不是信息的唯一载体。

## 验收规则

- 禁止兔兔、背景、装饰线或空闲状态无限循环动画。
- 后台 tab 不保留 Lenis RAF；页面重新可见时只恢复必要的滚动转场。
- reduced-motion 同时关闭 JS 动效和 CSS transition，并将 reveal 恢复为可见静态内容。
- 动效预算只能引用 `packages/ui/tokens.json` 的 motion token；新动效必须有状态或空间语义。
