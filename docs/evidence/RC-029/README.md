# RC-029 执行证据

- RC ID: RC-029
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`0180f13`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-028（已完成并有 restricted 来源）
- 修改文件：Anthropic 授权监控登记、复核日志、监控脚本和季度 workflow
- 用户可见行为：官方仓库元数据按季度复核；变化会触发失败和新 ADR，不会自动扩大复用权限。
- 风险与假设：GitHub API 元数据不等于法律授权；terms/docs URL 只登记待确认状态。

## 交付

- 监控 `anthropics/claude-code` 和 `anthropics/claude-agent-sdk-python` 的默认分支、HEAD SHA、license、归档和禁用状态。
- 建立 2026-10-01 下一次季度复核日期和变化处理日志。
- GitHub Actions 使用季度 cron 与手动触发，变化时要求创建 ADR 并维持原有限制。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_anthropic_authorization_monitor.py` | PASS：季度监控登记和复核日志结构通过 | `docs/research/anthropic-authorization-monitor.yml` |
| `python scripts/check_anthropic_authorization_monitor.py --live` | PASS：两个官方仓库 live metadata 与固定基线一致 | `scripts/check_anthropic_authorization_monitor.py` |
| `python -m ruff check scripts/check_anthropic_authorization_monitor.py` | PASS：All checks passed | `scripts/check_anthropic_authorization_monitor.py` |
| workflow 静态检查 | PASS：schedule 为季度，支持 workflow_dispatch，无写入权限或秘密依赖 | `.github/workflows/anthropic-authorization-monitor.yml` |

## 未解决项

- terms/docs URL 的内容状态仍待独立法律/文档复核，不据此形成授权结论。
- 上游元数据变化时必须记录旧/新值、影响范围、ADR 编号和批准人；新 ADR 合并前保持 `behavior-only`/`restricted`/禁止复用。

## 回滚

- 需要回滚的本项文件/迁移：删除监控登记、日志、脚本、workflow 和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
