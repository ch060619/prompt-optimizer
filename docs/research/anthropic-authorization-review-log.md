# Anthropic 授权变化监控记录

RC IDs: RC-029

## 当前规则

- 每季度复核 `docs/research/anthropic-authorization-monitor.yml` 中的官方仓库元数据和登记 URL。
- 仓库默认分支、HEAD SHA、license 字段、归档/禁用状态或官方 URL 状态变化时，监控任务失败并要求新增 ADR。
- 新 ADR 合并前维持当前 `behavior-only`、`restricted` 和禁止复用规则，不自动扩大来源权限。
- 监控不代替法律意见；GitHub license 字段和页面可见性不能证明版权、合同、商业秘密、DMCA 或再分发权利。

## 复核记录

| 日期 | 范围 | 结果 | 后续 |
| --- | --- | --- | --- |
| 2026-07-17 | `anthropics/claude-code`、`anthropics/claude-agent-sdk-python` 的 GitHub API 元数据；terms/docs URL 登记 | 初始基线已固定；GitHub 仓库可查询；条款/文档 URL 不作未经验证结论 | 下一次 2026-10-01；变化时创建 ADR 并保持限制 |

## 变更处理模板

发现变化时必须记录：旧/新 URL、默认分支、HEAD SHA、license、归档/禁用状态、页面响应摘要、检测日期、影响范围、是否需要法律意见、ADR 编号和批准人。未完成复核前，不得把变化解释成“已授权”。
