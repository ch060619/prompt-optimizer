# RC-044 执行证据

- RC ID: RC-044
- 状态：已提交（版本、兼容与迁移策略 ADR 已接受；实际发布迁移由后续 RC 持续执行）
- 负责人：Codex
- 基线 Commit：`24aa31d`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-043（已完成；追踪基础设施和反向索引可用）
- 修改文件：`docs/adr/0006-version-and-migration-policy.md`、`docs/migrations/version-migration-policy.yml`、`scripts/check_version_migration_policy.py`、本证据和主计划/追踪记录
- 用户可见行为：SemVer、API/配置/数据库/CLI 兼容窗口、弃用规则、前向迁移、备份、恢复和受控回滚边界均有明确登记。
- 风险与假设：本项不删除旧 API、不执行不可逆降级、不修改用户数据库；真实安装升级和跨平台发布仍留给后续 RC。

## 交付

- 接受 ADR-0006，规定 MAJOR/MINOR/PATCH 变更边界、兼容窗口和弃用流程。
- 固定 API `/api` 与 `/api/v1`、配置命名空间、SQLite v0/v1 和 CLI 迁移规则。
- 登记两版无秘密测试数据、事务前向迁移和独立目标受控回滚步骤；复用 RC-053 的真实 SQLite 演练作为当前基线。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_version_migration_policy.py` | PASS：SemVer、API/config/database/CLI 窗口、v0/v1 数据和受控回滚标准完整 | `scripts/check_version_migration_policy.py` |
| `python -m ruff check scripts/check_version_migration_policy.py` | PASS：All checks passed | `scripts/check_version_migration_policy.py` |
| `python -m pytest backend/tests/test_storage_backup.py -q` | PASS：4 passed；包含 v0 -> v1 前向迁移、备份、异常回滚、完整性检查和恢复 | `backend/tests/test_storage_backup.py` |
| SemVer/兼容窗口/弃用/两版数据/回滚审查 | PASS：API、配置、数据库和 CLI 窗口均有替代入口、弃用和新增 RC 条件 | `docs/migrations/version-migration-policy.yml` |
| `python scripts/check_rc_traceability.py --rc RC-044` + `--check` | PASS：RC-044 为 GREEN；ADR、策略、校验器和证据已登记，反向索引当前 | `docs/traceability/rc-index.md` |
| 进度不变量与 `git diff --check` | PASS：Done 39、Pending 271、Total 310、UniqueIds 310；本轮文件无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| RC-015 至 RC-043 跨 RC 门禁批次 | PASS：RC-041/042、Persona、核心场景、三表面能力、来源基线、source-map denylist、专有内容、clean-room、模型、第三方、名称/素材和 RC-036 汇总检查全部通过 | `.github/workflows/ci.yml` |

## 未解决项

- 当前真实 SQLite 实现和安装升级验证由 RC-053、RC-055 及后续发布 RC 继续执行；本项不宣称完成跨版本安装包演练。
- 兼容窗口到期后的 API/配置删除、数据库高版本迁移和发布回滚必须新增 RC 并保留旧客户端测试。

## 回滚

- 需要回滚的本项文件/迁移：删除 ADR、版本策略登记、校验器、本证据和 RC-044 主计划/追踪记录；不执行数据逆向迁移。
- 不得触碰的用户数据：`.runtime/`、`frontend/.openapi.json` 和任何默认应用数据库。
