# RC-122 执行证据

- 状态：SUBMITTED WITH PENDING CONFIRMATION
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-121（pending 不阻塞本次只读素材核对）
- 修改文件：`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`、`docs/evidence/RC-122/README.md`

## 核对结果

用户计划指定的源文件 `C:\Users\10735\Desktop\提示词\兔兔素材.png` 在当前环境不存在，且 `C:\Users\10735\Desktop\提示词` 目录不存在。对桌面递归搜索仅发现仓库内的 `frontend/public/rabbit-artwork.png` 和生成的 `frontend/dist/rabbit-artwork.png`，两者相同，不能据此证明外部源素材的来源或许可证。

| 项目 | 当前仓库素材结果 |
| --- | --- |
| 路径 | `frontend/public/rabbit-artwork.png` |
| SHA-256 | `1DDE71742091C82D85EDB403449AF8DE843D5F61DCA8CBF65B59AEBD9B90E599` |
| 文件大小 | 550885 bytes |
| 尺寸 | 643 × 684 |
| 像素格式 | `Format32bppArgb` |
| PNG 原始格式 GUID | `b96b3caf-0728-11d3-9d7b-0000f81ef32e` |
| 外部来源/许可证 | 未确认 |

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `Get-FileHash frontend/public/rabbit-artwork.png -Algorithm SHA256` | PASS：哈希固定如上 | `frontend/public/rabbit-artwork.png` |
| `System.Drawing.Image` 元数据读取 | PASS：尺寸、像素格式和 PNG GUID 已记录 | `frontend/public/rabbit-artwork.png` |
| `Get-ChildItem C:\Users\10735\Desktop -Recurse -Filter *.png` | PASS：未找到指定源文件；仅发现仓库 public/dist 副本 | 当前工作区外部路径检查 |

## 受阻条件与后续

- 需要用户提供 `C:\Users\10735\Desktop\提示词\兔兔素材.png`，或提供可核验的源 URL、版权/授权说明和允许复制到仓库的范围。
- 在来源和许可证确认前，不复制、裁切、重编码或登记仓库 `rabbit-artwork.png` 为源素材，不勾选 RC-122。
- 按用户指令，下一待执行项已推进到 RC-123。

## 回滚

- 本项没有复制或修改二进制素材；仅需删除本证据文件并恢复执行计划/追踪索引登记即可，不触碰现有仓库素材和用户数据。
