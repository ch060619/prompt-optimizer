# RC-035 执行证据

- RC ID: RC-035
- 状态：已提交（PENDING CONFIRMATION；发布阻断）
- 负责人：Codex
- 基线 Commit：`bbed667`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-034（已提交；名称/渠道法务确认仍待人工完成）
- 修改文件：兔兔素材授权登记、授权说明、校验器、CI 步骤和本证据
- 用户可见行为：未经授权的兔兔素材不获得发布批准；新发布流程必须保持素材发布阻断。
- 风险与假设：仓库中已有素材的存在和视觉内容不等于取得版权或再分发许可；本轮不推断权利人或许可证。

## 交付

- 登记任务要求的外部源路径 `C:\Users\10735\Desktop\提示词\兔兔素材.png`，并记录本轮检查为缺失。
- 固定仓库候选 `frontend/public/rabbit-artwork.png` 的大小和 SHA-256，作为内容证据而不是权利证据。
- 将商业使用、开源使用、修改、派生、再分发和署名全部设为 `pending`。
- `release.allowed: false` 与 `release.status: blocked` 形成临时发布门禁；没有授权证据时不得加入新的发布包。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_art_license.py` | PASS：缺少授权被明确记录，发布保持 blocked | `scripts/check_rabbit_art_license.py` |
| `python -m ruff check scripts/check_rabbit_art_license.py` | PASS：All checks passed | `scripts/check_rabbit_art_license.py` |
| 外部源文件检查 | PENDING CONFIRMATION：`C:\Users\10735\Desktop\提示词\兔兔素材.png` 不存在 | `docs/legal/rabbit-art-license.yml` |
| 权利人声明/许可证/署名条款 | PENDING CONFIRMATION：未提供或未发现可核验授权证据 | `docs/legal/rabbit-art-license.md` |

## 未解决项

- 提供源文件或可核验原始来源，以及创作者/权利人的书面授权。
- 明确商业使用、开源分发、修改、派生、再分发和署名要求，并将原始证据入库。
- 授权完成前维持发布阻断；当前仓库中已有静态引用不应被解释为已获批准。

## 回滚

- 需要回滚的本项文件/迁移：删除兔兔素材授权登记、说明、校验器、CI 步骤和本证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
