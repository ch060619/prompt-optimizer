# Rabbit Code 视觉无障碍基线

<!-- RC ID: RC-132. Define keyboard, focus, semantic, contrast, zoom, and motion rules. -->

## 规则

- 所有可操作元素按 DOM 顺序进入键盘流程；对话框和全屏导航循环焦点，Escape 关闭并恢复触发元素焦点。
- icon-only 控件同时提供可访问名称和 Tooltip；装饰图标与 Rabbit 素材从读屏树隐藏。
- Tab、tabpanel、dialog、alertdialog、main、region 和 complementary 均使用唯一且有意义的名称；动态状态使用 `role="status"` 或 `aria-live`。
- light/dark 主题的正文、状态色、表单控件和焦点环采用主题 token；焦点环在普通和 forced-colors 模式均可见。
- `prefers-reduced-motion: reduce` 时关闭平滑滚动、view transition、reveal 和 CSS 动画；不依赖动画才能理解页面。
- 页面在窄视口及 640px CSS 视口（桌面 200% 缩放的等效检查）保持可读且无横向溢出。

## 交付

- `Task` 和 `Review` 移除嵌套 main landmark；Task inspector tabs 关联唯一 `tabpanel`，计划折叠按钮暴露 `aria-expanded`。
- Workspace 增加唯一 h1、命名模板库/版本历史 landmark 和提示词输入名称；统一 UI error heading 层级。
- 主题 token 增加 `focus-ring`、`accent-ink`、`surface-*` 和暗色状态/错误表面，避免暗色主题反转导致对比度失败。
- 全屏导航增加 Tab 循环；CSS 增加 reduced-motion 与 forced-colors 规则。

## 验收记录

- Playwright accessibility snapshot：Task 的 `region`、`tabpanel`、`tablist`、输入名称及导航 dialog 均可读；菜单 Tab/Escape 焦点路径人工复核通过。
- axe-core 4.10.2：14 条 route coverage 路由分别在 light/dark 主题运行，共 28 组检查，`violations: []`。
- 原生 axe CLI 因本机 Chrome `150.0.7871.125` 与自动 ChromeDriver `151` 不匹配而无法启动；改用同一 axe-core 版本注入 Playwright 页面完成等价审计，并保留该环境限制。
- `prefers-reduced-motion`：`scroll-behavior=auto`、reveal `opacity=1`、`transform=none`。
- 640px CSS 视口：`clientWidth=640`、`scrollWidth=640`；窄窗口 Task 截图无横向溢出。

