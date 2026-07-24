# Rabbit 素材派生资产规范

- RC ID: RC-123
- 状态：规范、技术源登记和 Rabbit Code 发布授权已完成
- 目标色彩空间：sRGB
- 导出格式：PNG；需要透明度的变体必须保留 alpha
- 命名：`rabbit-{variant}-{theme}-{size}.png`；`size` 是 CSS 像素基准，2x 文件使用同一基准尺寸的两倍像素

## 变体清单

| 变体 | 主题 | 1x CSS 尺寸 | 2x 像素尺寸 | 最小显示 | 安全区 | 用途 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `full` | light/dark | 643x684 | 1286x1368 | 180px 高 | 四边至少 8% 留白；主体不得贴边 | 首页和 onboarding 主视觉 |
| `avatar` | light/dark | 256x256 | 512x512 | 32px | 主体占画布 72%-88%；脸部中心位于画布中心 | 账户、会话和小型品牌槽位 |
| `mark` | light/dark | 64x64 | 128x128 | 16px | 主体占画布 68%-88%；不得依赖细于 1px 的线 | 侧栏、状态行和应用标识 |
| `empty` | light/dark | 480x320 | 960x640 | 160px 宽 | 内容安全区为画布 10%-90%；文本禁入图像安全区 | 空状态插图 |
| `mono` | light/dark | 64x64 | 128x128 | 16px | 仅保留可辨识轮廓；对比度至少 4.5:1 | 单色小标和高对比模式 |
| `app-icon` | light/dark | 32/64/128/256/512 方形 | 各自 2x | 16px | 8% 内缩安全区；不可用完整形象硬缩出不可识别细节 | 应用图标和桌面快捷方式 |

## 导出规则

1. 导出工具读取仓库根目录 `兔兔素材.png` 的固定 SHA-256，不能从桌面路径运行时加载。
2. 每个变体必须同时记录源 SHA-256、导出脚本版本、尺寸、主题、色彩空间和生成时间。
3. 1x/2x 使用同一裁切焦点；2x 只提高像素密度，不改变安全区或视觉比例。
4. 深色变体只调整背景/轮廓对比，不改变兔兔主体的识别焦点；浅色和深色预览都要检查透明边缘。
5. 最小显示尺寸下必须人工检查主体可辨识性；`mono` 和 `app-icon` 不允许简单缩小 `full` 变体。

## 当前门禁

`docs/design/rabbit-asset-manifest.json` 是机器可检验的唯一变体清单。
`scripts/check_rabbit_asset_spec.py` 检查变体 ID、主题、1x/2x、最小显示尺寸和安全区字段。
当前 `source.status=registered`；`scripts/check_rabbit_asset_spec.py --require-source --require-outputs`
会检查源图和实际 PNG/WebP/ICO 的路径、SHA-256、尺寸字段及文件预算。用户发布授权
记录在 `docs/legal/rabbit-art-license.yml`。
