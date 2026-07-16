# RC-034 执行证据

- RC ID: RC-034
- 状态：已提交（PENDING CONFIRMATION）
- 负责人：Codex
- 基线 Commit：`cb7994a`
- 完成 Commit：`3b85662`
- 前置 RC：RC-033（已提交；正式实现 PR 和角色签署仍待确认）
- 修改文件：名称/渠道审计登记册、说明、校验器和 CI 步骤
- 用户可见行为：发布前对产品名、发行标识、域名、组织、包仓库和应用商店入口保留可追溯的冲突审计记录。
- 风险与假设：HTTP 200/404/403 只记录入口响应，不证明控制权、可注册性、商标无冲突或应用商店批准；法务和负责人签署仍是发布门槛。

## 交付

- `Rabbit Code` / `rabbit-code`、兼容旧标识、候选域名、GitHub、PyPI、npm、Microsoft Store、Apple Store 和 Flathub 入口均已登记。
- USPTO、EUIPO 和 CNIPA 入口已登记，但具体文字、类别和法域检索保持 `not-run`。
- 既有 `prompt-optimizer` 在 PyPI/npm 返回 200，保留为兼容标识和名称混淆风险；不把它宣称为新品牌可用性证明。
- `Rabbit Prompt`、`Prompt Rabbit` 和 `Local Prompt Studio` 作为备用名记录，未在完成法律与渠道审查前切换。
- 校验器对必需渠道、商标数据库、404 的非可用性风险和未运行的商标检索施加保守门禁。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_name_channel_audit.py` | PASS：公开检查已记录，法律清权仍待确认 | `scripts/check_name_channel_audit.py` |
| `python -m ruff check scripts/check_name_channel_audit.py` | PASS：All checks passed | `scripts/check_name_channel_audit.py` |
| 目标市场商标检索和负责人/法务签署 | PENDING CONFIRMATION：三类商标入口可访问，但本轮没有执行具体检索；签署字段为空 | `docs/legal/product-name-channel-audit.yml` |
| 域名、组织、包名和商店控制权 | PENDING CONFIRMATION：公开响应不替代注册人、控制权或渠道批准核验 | `docs/legal/product-name-channel-audit.md` |

## 未解决项

- 负责人和合资格法务需要补充检索日期、法域/类别、结果摘要、冲突风险、决定和决策编号。
- `rabbitcode.dev`、`rabbitcode.app` 等域名以及组织、包名和应用商店状态需要人工控制权/注册核验。
- 在签署和控制权核验完成前，不得对外宣称 `Rabbit Code` 已清权、可注册或可发布。

## 回滚

- 需要回滚的本项文件/迁移：删除名称/渠道登记册、说明、校验器、CI 步骤和本证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
