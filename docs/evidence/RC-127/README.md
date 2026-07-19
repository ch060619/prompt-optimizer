# RC-127 执行证据

- 状态：SUBMITTED WITH PENDING CONFIRMATION
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-122/123 的源素材、授权和实际派生物仍 pending
- 修改文件：`docs/design/rabbit-asset-delivery.md`、`docs/evidence/RC-127/README.md`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`

## 已交付

- 定义无损母版、派生发布物和构建输出的隔离边界，禁止构建脚本覆盖母版。
- 定义 `full`、`empty`、`avatar`、`mark`、`mono` 和 `app-icon` 的 PNG/WebP/图标单文件预算及总包体目标。
- 定义裁切无效透明留白、固定归一化焦点、1x/2x 同焦点、透明边缘、色偏和最小尺寸清晰度检查。
- 定义源图登记、临时目录导出、哈希记录、预算检查和发布目录写入流程。
- 记录当前只读基线；没有复制、裁切、重编码或生成未经授权的位图。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `Test-Path C:\Users\10735\Desktop\提示词\兔兔素材.png` | EXPECTED PENDING：返回 `False`；指定源图和目录不存在 | `docs/design/rabbit-asset-delivery.md` |
| `Get-FileHash frontend/public/rabbit-artwork.png -Algorithm SHA256` | PASS：`1DDE71742091C82D85EDB403449AF8DE843D5F61DCA8CBF65B59AEBD9B90E599` | `frontend/public/rabbit-artwork.png` |
| 现有 PNG 元数据读取 | PASS：643 x 684、550885 bytes、`Format32bppArgb` | `frontend/public/rabbit-artwork.png` |
| `python scripts/check_rabbit_asset_spec.py` | PASS：6 个变体规范有效，source status=pending | `docs/design/rabbit-asset-manifest.json` |
| `python scripts/check_rabbit_asset_spec.py --require-source` | EXPECTED PENDING：因 `source is not registered` 失败 | `docs/evidence/RC-122/README.md` |
| 实际 PNG/WebP/应用图标导出、预算和视觉对比 | NOT RUN：缺少可核验源图和授权 | `docs/design/rabbit-asset-delivery.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 15 test files、58 passed；Ruff/Mypy、Lint/Build、API drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-127/README.md` |

## 受阻条件与后续

- RC-122 指定源文件不存在，仓库现有 PNG 的来源和许可证也未确认；不能据此完成 RC-127 的实际裁切和导出验收。
- RC-127 保持执行计划中的 `[ ]`，不把规范检查通过写成素材交付通过。
- 按用户指令自动读取并继续 RC-128；源图和授权补齐后，RC-127 需要重新执行实际导出与清晰度/包体检查。

## 回滚

- 需要回滚的本项文件：删除本证据和 `docs/design/rabbit-asset-delivery.md`，恢复执行计划和追踪索引的 RC-127 引用；不触碰 `frontend/public/rabbit-artwork.png` 或 RC-123 manifest。
