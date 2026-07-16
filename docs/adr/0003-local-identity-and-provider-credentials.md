# ADR-0003：本地用户身份与 Provider 凭据分离

- RC ID: RC-052
- Status: Accepted
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Context

现有 V2 使用本地 JWT 令牌将用户与历史版本、项目空间和后台任务关联；离线优化本身可以在未登录状态运行。Provider 配置则由进程环境读取，包含可能需要保密的 API Key。把这两类信息混在“登录”概念或同一持久化记录中，会让用户误以为 Rabbit Code 账户等于第三方 Provider 账户，也会扩大令牌泄露后的影响面。

仓库事实由 `backend/src/prompt_optimizer/auth/service.py`、`backend/src/prompt_optimizer/providers/registry.py`、`backend/src/prompt_optimizer/storage/service.py` 和 `backend/tests/test_auth_boundary.py` 固定：JWT 只编码本地用户身份和过期时间；`users` 表只保存密码哈希；Provider Key 当前只在进程配置中存在。

## Decision

保留 JWT，但将其定义为可选的本地应用身份层，而不是 Rabbit Code 云账户或 Provider 登录：

- 未登录用户可以使用离线分析和优化；需要保存历史、项目或后台任务时必须登录。
- JWT 只包含 `sub`、`username`、`exp`，不包含 API Key、Provider 配置、提示词、源码、路径或模型内容。
- 本地用户资料、密码哈希和资源归属继续由 SQLite 管理；API Key 不进入 `users`、Prompt 版本、任务结果或 JWT。
- Provider 凭据与本地身份独立建模。当前仅允许进程环境或显式传入的临时配置；后续持久化凭据必须使用操作系统密钥库，遵守 RC-179，在此之前不得写 SQLite 或普通配置文件。
- UI 文案区分“本地登录/历史归属”和“配置 Provider/API”，不把第三方 API Key 称为 Rabbit Code 密码。

## Threat Model

| 威胁 | 当前控制 | 残余风险/后续 |
| --- | --- | --- |
| JWT 被窃取后读取本地资源 | HMAC 签名、12 小时过期、路由按 `owner_id` 隔离 | 本地服务生产认证、Origin、随机令牌和撤销由 RC-207/后续安全 RC 加固 |
| API Key 进入 JWT 或用户表 | JWT 载荷固定字段；用户表仅有密码哈希；边界测试阻止混入 | 环境变量可能被宿主进程或诊断工具读取；密钥库由 RC-179 负责 |
| 用户密码泄露 | PBKDF2-HMAC-SHA256 加盐哈希，不返回哈希 | 生产密钥策略、登录限流和升级哈希由后续安全 RC 评估 |
| 无 API 用户被迫登录或被误标为云模型 | 离线路线允许 guest；`OfflineRuleProvider` 明确为本地规则 | 本地模型安装/密钥库与产品文案由后续 RC 完善 |
| 取消 JWT 时历史归属丢失 | 本项不移除 JWT、不迁移 owner ID，保留 SQLite 记录 | 将来移除必须先做显式用户映射和可回滚迁移，不得静默合并 |

## Alternatives

| 方案 | 结论 |
| --- | --- |
| 立即移除 JWT，按操作系统用户归属 | 拒绝：会破坏现有历史/项目/任务隔离，且 RC-053 尚未提供迁移和回滚演练 |
| 把 Provider Key 放进 JWT 或 `users` 表 | 拒绝：身份令牌和第三方秘密生命周期不同，扩大泄露面 |
| 保留 JWT 并与 Provider 凭据分离 | 采用：兼容现有客户端，支持 guest 离线路径，并为后续 OS Keychain 迁移保留边界 |

## Migration and Review Triggers

本项不修改数据库 Schema、不迁移现有用户、不改变 JWT 字段。若未来改为移除或替换 JWT，必须先完成：导出用户/资源归属映射、双读验证、失败回滚、旧 Token 过期窗口和用户可见迁移说明。若 App Server 不再是单机本地服务、需要多设备同步，或 OS 密钥库无法满足 Provider 凭据生命周期，应新建 ADR 重新审议本决策。

## Consequences

- 现有登录、历史、项目和任务能力继续可复用；离线 guest 路径不需要凭据。
- Provider Adapter 可以独立演进，不需要把 API Key 传给本地用户认证服务。
- 本决策不声称当前本地服务已达到生产级认证门槛；相关安全门禁仍按计划执行。
