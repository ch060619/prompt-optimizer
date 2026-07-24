# RC-123 执行证据

- 状态：PASS
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-122 技术源登记与项目发布授权完成
- 修改文件：`docs/design/rabbit-asset-derivatives.md`、`docs/design/rabbit-asset-manifest.json`、`scripts/check_rabbit_asset_spec.py`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 已交付：`full`、`avatar`、`mark`、`empty`、`mono`、`app-icon` 六个变体的 light/dark、1x/2x、最小显示尺寸、安全区、sRGB、PNG、命名和来源哈希规则。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_asset_spec.py` | PASS：6 variants；source status=registered；字段和尺寸规则有效 | `docs/design/rabbit-asset-manifest.json` |
| `python scripts/check_rabbit_asset_spec.py --require-source --require-outputs` | PASS：源图与 PNG/WebP/ICO 实际输出哈希、尺寸字段和预算有效 | `docs/evidence/RC-122/README.md` |
| `python -m json.tool docs/design/rabbit-asset-manifest.json` | PASS：manifest JSON 有效 | `docs/design/rabbit-asset-manifest.json` |
| `\.venv\Scripts\python.exe -m ruff check scripts\check_rabbit_asset_spec.py` | PASS | `scripts/check_rabbit_asset_spec.py` |

## 结论与边界

- 六类派生规范、源登记和实际输出 manifest 均已完成，可勾选 RC-123。
- 桌面/终端扣图及应用图标使用用户提供构图；技术生成只做无损/调色板压缩和格式封装。
- Rabbit Code 发布授权已记录在 `docs/legal/rabbit-art-license.yml`；通用商业许可未扩展。

## 回滚

- 需要回滚的本项文件：删除本证据、资产规范、manifest 和校验脚本，并恢复执行计划/追踪索引登记；不触碰现有 `frontend/public/rabbit-artwork.png`。
