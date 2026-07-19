# RC-133 执行证据

- RC ID: RC-133
- 状态：已完成
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-132；RC-127 的实际位图导出仍 pending，不阻塞本项的页面视觉回归
- 修改文件：`docs/design/rabbit-visual-regression.json`、`scripts/check_rabbit_visual_regression.py`、`scripts/workspace.py`、`frontend/src/components/SiteShell.tsx`、`docs/evidence/RC-133/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 建立 14 条独立路由的视觉回归 manifest，与 Rabbit 路由覆盖矩阵逐项对齐。
- 为每条路由定义 `light/dark × 1x/2x` 四组基线：桌面 `1280x1000@1` 和小窗等效 `640x844@2`。
- 将最大像素差比例、横向溢出、裁切元素和兔兔与内容重叠阈值写入 manifest，并把契约检查接入 `python scripts/workspace.py check`。
- 为动态模板与历史接口使用稳定夹具；工作页路由使用专属兔兔槽位，避免装饰层覆盖 Compare 等功能控件。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_visual_regression.py --check` | PASS：14 routes x 4 baselines，diff、overflow、clipping、overlap 阈值均已定义 | `scripts/check_rabbit_visual_regression.py`、`docs/design/rabbit-visual-regression.json` |
| Playwright 真实页面截图 | PASS：14 条路由 × 4 组基线，共 56 张截图；`failed=[]`，`themes=["light", "dark"]`，所有样本 `diff_ratio=0`、`rabbit_present=true`、`horizontal_overflow_px=0`、`clipped_elements=0`、`rabbit_content_overlaps=0` | `output/playwright/rc-133-*.png` |
| 深色主题人工抽查 | PASS：`/workspace/assets` 的 `dark-1x` 页面使用深色表面与浅色文字，Rabbit 标记存在且未遮挡 Compare 控件 | `output/playwright/rc-133-workspace-assets-dark-1x.png` |
| `python scripts/workspace.py verify` | PASS：登记后根验证通过；后端 281 passed、5 skipped、31 warnings；前端 15 test files、62 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过；保留既有迁移/环境与 jsdom navigation warnings | `docs/evidence/RC-133/README.md` |

## 未解决项与后续

- 本项已验证当前稳定夹具下的四组视觉基线、主题字段和 DOM 边界阈值；跨版本黄金图审批不在本轮新增范围内，后续视觉回归扩展留给 RC-235/RC-256。
- 原生 axe CLI 受本机 Chrome/ChromeDriver 版本限制；RC-132 已用相同 axe-core 版本注入 Playwright 页面完成无障碍审计，不在本项重复执行。
- RC-127 实际 PNG/WebP/应用图标导出仍等待 RC-122 源文件和授权；RC-121/057/060 外部条件仍 pending。
- 按用户指令，RC-133 完成后自动读取并继续 RC-134。

## 回滚

- 需要回滚的本项文件：删除视觉回归 manifest、校验脚本、`workspace.py` 门禁、RC-133 证据和计划/追踪登记；恢复工作页路由兔兔槽位为变更前状态。不回滚 RC-128 至 RC-132 的既有素材、层级、token、图标和无障碍改动。
