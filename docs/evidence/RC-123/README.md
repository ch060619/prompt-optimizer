# RC-123 执行证据

- 状态：SUBMITTED WITH PENDING CONFIRMATION
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-122（源素材/授权 pending）
- 修改文件：`docs/design/rabbit-asset-derivatives.md`、`docs/design/rabbit-asset-manifest.json`、`scripts/check_rabbit_asset_spec.py`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 已交付：`full`、`avatar`、`mark`、`empty`、`mono`、`app-icon` 六个变体的 light/dark、1x/2x、最小显示尺寸、安全区、sRGB、PNG、命名和来源哈希规则。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_asset_spec.py` | PASS：6 variants；source status=pending；字段和尺寸规则有效 | `docs/design/rabbit-asset-manifest.json` |
| `python scripts/check_rabbit_asset_spec.py --require-source` | EXPECTED PENDING：失败 `ERROR: source is not registered`；防止无授权导出被误认为完成 | `docs/evidence/RC-122/README.md` |
| `python -m json.tool docs/design/rabbit-asset-manifest.json` | PASS：manifest JSON 有效 | `docs/design/rabbit-asset-manifest.json` |
| `\.venv\Scripts\python.exe -m ruff check scripts\check_rabbit_asset_spec.py` | PASS | `scripts/check_rabbit_asset_spec.py` |

## 受阻条件与后续

- RC-122 指定源文件不存在且来源/许可证未确认，因此本项没有生成透明图、头像、小标、空状态、浅/深主题或应用图标二进制。
- 未宣称 1x/2x、高 DPI 清晰度或安全区的视觉检查已通过；这些检查必须在源素材注册和派生物生成后执行。
- 按用户指令，下一待执行项已推进到 RC-124。

## 回滚

- 需要回滚的本项文件：删除本证据、资产规范、manifest 和校验脚本，并恢复执行计划/追踪索引登记；不触碰现有 `frontend/public/rabbit-artwork.png`。
