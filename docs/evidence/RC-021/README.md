# RC-021 执行证据

- RC ID: RC-021
- 状态：已提交（含待确认项）
- 负责人：Codex
- 基线 Commit：`ee19518`
- 完成 Commit：`46f5cec`
- 前置 RC：RC-020（已提交并有证据）
- 修改文件：source-map 元数据证据、复用边界、校验器
- 用户可见行为：source-map 仓库被登记为高风险、禁止复用；Rabbit Code 不把当前 GitHub 可见性当成授权。
- 风险与假设：本项严格没有访问、运行或保存 source-map 还原源码正文。

## 交付

- 固定 5 个仓库的 URL、默认分支、HEAD SHA、不可变 commit URL、API 状态、README 状态、license 字段、归档/禁用状态和调研日期。
- 保存 README 的中立摘要，不保存 README 正文或 source-map 内容。
- 明确 GitHub API 不提供 DMCA/删除字段，使用 `not-observed`，不推导“没有 DMCA/删除请求”。
- 所有来源默认 `high` 风险、`prohibited` 复用；未进入工作树、依赖、CI、Docker、安装包或发布物。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 5 个 GitHub repository API 查询 | PASS：均 HTTP 200；归档、禁用和 license 字段已保存 | `docs/research/source-map-evidence.yml` |
| 5 个固定 commit URL HEAD 查询 | PASS：均 HTTP 200 | `docs/research/source-map-evidence.yml` |
| 5 个固定 SHA README API 查询 | PASS：均 HTTP 200；未保存正文 | `docs/research/source-map-evidence.yml` |
| `python scripts/check_source_map_evidence.py` | PASS：5 个 source-map 元数据条目通过 | `scripts/check_source_map_evidence.py` |
| `python -m ruff check scripts/check_source_map_evidence.py` | PASS：All checks passed | `scripts/check_source_map_evidence.py` |
| source body 访问/运行审计 | PASS：均为 false | `docs/research/source-map-evidence.yml` |

## 待确认

- GitHub API 没有 DMCA/删除状态字段；`not-observed` 需由后续法律/平台渠道复核。
- 当前可见性、README 自述或 license badge 都不构成源代码授权、版权清除或再分发许可。

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-021 登记、边界、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
