# Rabbit Code 名称与渠道冲突审计

RC IDs: RC-034

## 当前结论

状态：`pending-human-legal-review`。本轮是公开入口和名称占用风险登记，不是商标检索意见、域名注册证明、包名可用性证明或应用商店批准。

- `Rabbit Code` / `rabbit-code` 是当前产品和发行标识。
- GitHub/PyPI/npm 的 `rabbit-code` 候选本轮返回 404；这不等于可注册、可使用或没有未公开权利冲突。
- 既有 `prompt-optimizer` 在 PyPI/npm 返回 200，作为兼容标识存在名称占用/混淆风险；兼容期内不把它宣称为新发行品牌。
- `rabbitcode.dev` 和 `rabbitcode.app` 返回 200，不能据此认定项目控制或可用；域名注册人和内容需人工核验。
- USPTO、EUIPO、CNIPA 入口可访问，但本轮没有完成具体文字/类别/法域检索；商标结论待法务和负责人签署。
- Microsoft Store 返回 403、Apple 搜索返回 404、Flathub 搜索返回 200；这些响应不构成应用商店可发布性结论。

## 备用名称

`Rabbit Prompt`、`Prompt Rabbit`、`Local Prompt Studio` 仅是待检索候选，不得在完成商标、域名、包仓库和渠道审计前切换品牌。

## 发布前要求

- 负责人和法务分别填写责任人、检索日期、法域/类别、结果摘要、冲突风险、决定和决策编号。
- 取得域名/组织/包名控制权或明确备用方案后，更新 README、包元数据、安装包、应用商店标识和迁移文案。
- 任何“可用/无冲突/可注册”结论必须有具体检索记录和签署，不由 HTTP 404/200 推导。
