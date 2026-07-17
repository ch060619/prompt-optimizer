# ADR-0006：版本、兼容与迁移策略

- Status: Accepted
- Date: 2026-07-17
- RC ID: RC-044
- Deciders: Rabbit Code engineering

## Context

Rabbit Code 同时维护本地 SQLite 数据、CLI/GUI/无头客户端、FastAPI 兼容入口和分层配置。版本升级必须允许用户前向迁移，失败时可以回到迁移前备份；旧客户端不能因新版本发布而静默改变语义。当前发布边界是 Windows/Linux、未签名制品和本地免费工具链，不能把云账户、签名证书或远程数据库作为迁移前置条件。

## Decision

采用 SemVer。MAJOR 允许删除已完成弃用窗口的 API、配置或数据兼容；MINOR 只增加向后兼容能力；PATCH 只修复错误或安全问题，不改变已登记契约。发布前必须记录版本、迁移说明、兼容矩阵和回滚入口。

API 继续保留现有 `/api/*` 兼容入口，新客户端使用 `/api/v1/*`；同一 major 内不删除旧入口。配置采用新键优先、旧键只读回退和明确来源提示，禁止双写。数据库用 SQLite `PRAGMA user_version` 表示 schema 版本：打开旧版本时先做同目录热备，再在单事务中执行前向迁移；高于当前版本直接拒绝，不猜测降级。降级不做原地逆向迁移，只能从完整备份恢复到匹配版本。

## Compatibility windows

- API：同一 MAJOR 的旧入口至少保留到下一 MAJOR；弃用公告、替代入口和迁移示例必须先进入文档与测试。
- 配置：新键立即生效，旧键在兼容窗口内只读回退；窗口结束前给出诊断，结束后由新的 RC 批准删除。
- 数据库：当前 schema 为 v1，支持 v0 -> v1 前向迁移；任何 v1 -> 更高版本必须新增迁移记录、备份和恢复测试。
- CLI：旧 `prompt-opt` 入口按 RC-051 的 3.0.0 迁移提示保留；删除或更改退出码必须另开 RC。

## Migration and rollback

迁移流程固定为：预检版本/磁盘/权限 -> SQLite 热备和 manifest -> 临时事务迁移 -> 完整性检查和关键记录计数 -> 原子提交 -> 记录迁移事件。任何步骤失败都回滚事务；若数据库已经提交但验收失败，关闭应用并从带 SHA-256 的迁移前备份恢复到独立目标，再由用户明确替换，禁止覆盖未知数据库。

RC-053 的 `backend/tests/test_storage_backup.py` 已提供 v0/v1 SQLite 数据、备份、前向迁移、注入失败回滚、完整性检查和恢复路径；本 ADR 将其作为当前数据库迁移演练基线。机器登记和两版测试数据见 [`version-migration-policy.yml`](../migrations/version-migration-policy.yml)。

## Consequences

- 新客户端、配置和数据库变更必须先更新兼容矩阵与迁移测试，不能直接改现有字段语义。
- 用户数据不会因为降级尝试而被静默覆盖；恢复需要额外目标和明确确认。
- 维护成本增加了版本窗口、弃用公告、manifest 和迁移回滚演练，但这换来可验证的升级失败边界。
- 远程数据库、付费服务和数字签名不是当前迁移成功条件；真实平台发布验证仍由后续 RC 负责。

## Acceptance evidence

- `scripts/check_version_migration_policy.py` 校验 SemVer、兼容矩阵、v0/v1 测试数据和回滚步骤。
- `python -m pytest backend/tests/test_storage_backup.py -q` 验证现有 SQLite 前向迁移、备份、异常回滚和恢复。
