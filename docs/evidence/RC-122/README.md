# RC-122 执行证据

- 状态：PASS（技术源登记与 Rabbit Code 发布授权完成）
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-121（pending 不阻塞本次只读素材核对）
- 修改文件：`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`、`docs/evidence/RC-122/README.md`

## 核对结果

用户随后在本轮对话中明确提供兔兔素材并要求加入项目。仓库根目录 `兔兔素材.png` 作为品牌母版登记；桌面和终端扣图分别保存为 `桌面端兔兔素材.png`、`终端兔兔素材.png`，运行时不依赖桌面外部路径。

| 项目 | 当前仓库素材结果 |
| --- | --- |
| 路径 | `兔兔素材.png` |
| SHA-256 | `2C7EDC4488B81533F116B2A908415FCF2063C2F6A51DCDF76E0C59014A057A38` |
| 文件大小 | 1191609 bytes |
| 尺寸/格式 | 1254 × 1254、RGB PNG |
| 外部来源/许可证 | 用户声明 AI 生成并明确允许 Rabbit Code 发布 |

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `Get-FileHash 兔兔素材.png -Algorithm SHA256` | PASS：哈希固定如上 | `兔兔素材.png` |
| Pillow 元数据读取 | PASS：尺寸、像素格式和 PNG 格式已记录 | `兔兔素材.png` |
| `python scripts/check_rabbit_asset_spec.py --require-source --require-outputs` | PASS：源图与 6 个实际输出均存在、哈希和预算有效 | `docs/design/rabbit-asset-manifest.json` |
| `python scripts/check_rabbit_art_license.py` | PASS：用户授权证据存在，Rabbit Code 发布允许 | `docs/legal/rabbit-art-license.yml` |

## 边界

- RC-122 登记技术源文件和运行时依赖边界；用户已允许 Rabbit Code 项目包含、修改、派生和再分发素材。
- 通用商业许可和脱离 Rabbit Code 项目的素材单独销售不在本次授权范围内。

## 回滚

- 本项没有复制或修改二进制素材；仅需删除本证据文件并恢复执行计划/追踪索引登记即可，不触碰现有仓库素材和用户数据。
