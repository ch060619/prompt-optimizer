# RC-035 执行证据

- RC ID: RC-035
- 状态：PASS（用户已明确允许 Rabbit Code 发布）
- 负责人：Codex
- 基线 Commit：`bbed667`
- 完成 Commit：`f72ef6e`
- 状态修正 Commit：`5fc4d75`
- 前置 RC：RC-034（已提交；名称/渠道法务确认仍待人工完成）
- 修改文件：兔兔素材授权登记、授权说明、校验器、CI 步骤和本证据
- 用户可见行为：当前登记素材已获 Rabbit Code 项目发布批准；新发布流程仍必须通过授权校验。
- 风险与假设：用户已确认素材身份、声明其由 AI 生成，并明确允许 Rabbit Code 发布；通用商业许可和生成服务条款仍未扩展推断。

## 交付

- 记录用户确认并加入项目的素材身份：`兔兔素材.png`。
- 固定该文件的大小和 SHA-256，作为内容证据而不是权利证据；原执行卡外部路径未作为运行时依赖。
- 记录用户的“AI 生成”来源声明，但保留生成服务条款、人类创作贡献、适用法域和明确许可证待核验。
- 记录用户原文“我允许发布了”，允许 Rabbit Code 仓库和项目制品包含、修改、派生与再分发素材。
- `release.allowed: true` 与 `release.status: approved-by-user` 确认 Rabbit Code 项目发布允许；通用商业使用仍保持 pending。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_art_license.py` | PASS：用户授权证据存在，Rabbit Code 发布允许 | `scripts/check_rabbit_art_license.py` |
| `python -m ruff check scripts/check_rabbit_art_license.py` | PASS：All checks passed | `scripts/check_rabbit_art_license.py` |
| 素材身份确认 | PASS：用户确认 `兔兔素材.png` 是品牌源素材，SHA-256 为 `2C7EDC4488B81533F116B2A908415FCF2063C2F6A51DCDF76E0C59014A057A38` | `docs/legal/rabbit-art-license.yml` |
| AI 生成来源声明 | PENDING CONFIRMATION：用户已声明 AI 生成，但 provider/条款/人类创作贡献未核验 | `docs/legal/rabbit-art-license.yml` |
| 发布授权 | PASS：用户原文“我允许发布了”已入库；无需署名 | `docs/legal/rabbit-art-release-authorization.md` |

## 边界

- Rabbit Code 项目发布已获允许。
- 通用商业许可、生成服务条款和素材脱离本项目的单独销售仍未获授权。

## 回滚

- 需要回滚的本项文件/迁移：删除兔兔素材授权登记、说明、校验器、CI 步骤和本证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
