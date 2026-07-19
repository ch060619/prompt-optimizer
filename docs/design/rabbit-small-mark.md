# Rabbit 小尺寸标识规范

- RC ID: RC-128
- 状态：代码原生 mark/mono 版本、尺寸回归和浏览器设计评审已通过

## 设计决策

`mark` 和 `mono` 不再把整张 `rabbit-artwork.png` 缩小到小尺寸。它们使用独立的 64 x 64 viewBox，只保留在低分辨率仍有辨识度的耳朵、帽檐、脸部轮廓和眼睛；`mark` 使用品牌强调色帽檐，`mono` 只使用继承的当前文字色。完整兔兔、头像和空状态仍由 RC-123 的 raster 变体负责。

这两个版本是组件内的代码原生 SVG，不复制、重编码或裁切来源不明的 PNG。SVG 不作为 RC-122 的源图或 RC-127 的 PNG/WebP 导出物，后续如需平台位图图标，仍必须从已登记母版或已批准的独立矢量源导出并记录哈希。

## 尺寸与背景矩阵

| CSS 尺寸 | 浅色背景 | 深色背景 | 验收重点 |
| ---: | --- | --- | --- |
| 16px | `var(--paper)` / inherited text color | `var(--paper)` / inherited text color | 耳朵、帽檐和脸部轮廓不能糊成一团 |
| 20px | `var(--paper)` / inherited text color | `var(--paper)` / inherited text color | 眼睛和帽檐仍可定位 |
| 24px | `var(--paper)` / inherited text color | `var(--paper)` / inherited text color | 轮廓连续，无透明边缘光晕 |
| 32px | `var(--paper)` / inherited text color | `var(--paper)` / inherited text color | 可作为侧栏和状态行的小标，不挤压邻近文字 |

`mono` 使用与背景有足够对比的继承色；深色主题通过已有 `:root[data-theme="dark"]` 的 `--ink` 变量切换，不在组件中硬编码第二套主题路径。小标在按钮、状态行和侧栏中必须保持固定宽高和 `aspect-ratio: 1`，不能因加载、悬停或标签变化而跳动。

## 可访问性与使用边界

- 非装饰标识使用 SVG `role="img"` 和明确的 `aria-label`；装饰槽位使用 `role="presentation"`、`aria-hidden="true"`，不重复朗读页面标题。
- `mark` 与 `mono` 不是工具操作图标，不放入需要 Lucide 图标表达的按钮命令中；命令按钮继续使用既有图标系统。
- 浏览器设计评审覆盖 16/20/24/32px、浅色/深色和固定尺寸；RC-133 继续覆盖完整页面截图、高对比和 200% 缩放回归。
- 禁止把整张 `full` raster 通过 CSS 缩小后作为 `mark` 或 `mono` 的替代实现。
