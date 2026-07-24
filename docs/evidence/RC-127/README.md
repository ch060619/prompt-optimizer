# RC-127 执行证据

- 状态：PASS
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-122/123 技术源、规范与项目发布授权已完成
- 修改文件：`docs/design/rabbit-asset-delivery.md`、`docs/evidence/RC-127/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 定义无损母版、派生发布物和构建输出的隔离边界，禁止构建脚本覆盖母版。
- 定义 `full`、`empty`、`avatar`、`mark`、`mono` 和 `app-icon` 的 PNG/WebP/图标单文件预算及总包体目标。
- 定义裁切无效透明留白、固定归一化焦点、1x/2x 同焦点、透明边缘、色偏和最小尺寸清晰度检查。
- 定义源图登记、临时目录导出、哈希记录、预算检查和发布目录写入流程。
- 交付桌面/终端 PNG 与 lossless WebP、512px PNG 应用图标和标准多尺寸 ICO；保持用户提供兔兔构图不变。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 母版哈希 | PASS：`2C7EDC4488B81533F116B2A908415FCF2063C2F6A51DCDF76E0C59014A057A38` | `兔兔素材.png` |
| 桌面 PNG/WebP | PASS：942x959；121667/109690 bytes；兔兔完整显示 | `frontend/public/rabbit-desktop.*` |
| 终端 PNG/WebP | PASS：614x655；84280/74542 bytes；兔兔完整显示 | `frontend/public/rabbit-terminal.*` |
| 应用图标 | PASS：512x512 RGBA PNG 140780 bytes；16-256 多尺寸 ICO 74975 bytes | `apps/desktop/src-tauri/icons/` |
| `python scripts/check_rabbit_asset_spec.py --require-source --require-outputs` | PASS：6 个变体规范与 6 个实际输出有效 | `docs/design/rabbit-asset-manifest.json` |
| Windows/Linux Tauri build | PASS：ICO/PNG 均被平台资源编译接受 | `docs/evidence/RC-060/README.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、58 passed；Ruff/Mypy、Lint/Build、API drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-127/README.md` |

## 结论与边界

- 实际导出、包体预算、应用图标资源编译和完整显示检查已完成，可勾选 RC-127。
- 用户已允许 Rabbit Code 发布；通用商业许可未扩展，不需要重新改变兔兔素材。

## 回滚

- 需要回滚的本项文件：删除本证据和 `docs/design/rabbit-asset-delivery.md`，恢复执行计划和追踪索引的 RC-127 引用；不触碰 `frontend/public/rabbit-artwork.png` 或 RC-123 manifest。
