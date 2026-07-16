# RC-054 Rabbit Code 产品标识迁移

- RC ID: RC-054
- 状态：已完成
- 兼容截止：Rabbit Code `3.0.0`

## 新旧映射

| 范围 | Rabbit Code 新名称 | Prompt Optimizer 旧名称 | 兼容策略 |
| --- | --- | --- | --- |
| 产品/API 标题 | `Rabbit Code` | `Prompt Optimizer` | 新安装和 OpenAPI 使用新名称；旧接口路径继续由 RC-048 兼容层提供 |
| Python 发行包 | `rabbit-code` | `prompt-optimizer` | `prompt_optimizer` import 路径不变；本地模块是兼容边界，不做大规模移动 |
| CLI | `rabbit` | `prompt-opt` | 两个入口指向同一 Typer 应用；旧入口输出弃用警告 |
| 前端包 | `rabbit-code-web` | `prompt-optimizer-web` | 私有前端包只更新新装标识，运行时 API 路径不变 |
| Windows/macOS/Linux 数据目录 | `rabbit-code` | `prompt-optimizer` | 新装只创建新目录；发现旧目录时自动读取并发出弃用警告 |
| SQLite 默认文件 | `rabbit-code.sqlite3` | `prompt_optimizer.sqlite3` | 旧目录沿用旧文件名，避免升级时复制或覆盖用户数据 |
| 环境变量 | `RABBIT_CODE_*` | `PROMPT_OPTIMIZER_*` | 新变量优先；旧变量回退并发 `DeprecationWarning` |

## 环境变量优先级

以下变量已经支持新旧并行：`HOME`、`DB`、`CONFIG`、`JWT_SECRET`，以及 Provider 的 `<PROVIDER>_<FIELD>` 配置。优先读取 `RABBIT_CODE_<SUFFIX>`，缺失时读取 `PROMPT_OPTIMIZER_<SUFFIX>`。两者同时存在时新变量胜出，旧变量不会覆盖新配置。

兼容期结束后，旧变量和旧 CLI 将不再写入新配置；截止版本前的弃用警告包含迁移目标和截止版本。API Key、JWT Secret 和数据库文件不会因为改名自动复制到普通文本配置。

## 数据目录迁移

新安装调用 `app_data_dir()` 时只创建 `rabbit-code`。如果新目录不存在而旧 `prompt-optimizer` 已存在，应用直接使用旧目录，避免用户历史、模板和项目丢失；RC-053 的 Schema 版本化逻辑随后负责升级前备份和事务迁移。应用不会自动创建新旧两份数据库，也不会静默合并两个目录。

显式设置 `RABBIT_CODE_HOME` 或 `RABBIT_CODE_DB` 可以覆盖自动发现。旧 `PROMPT_OPTIMIZER_HOME`/`PROMPT_OPTIMIZER_DB` 仍可用于回退，迁移完成后应改为新变量。需要跨目录复制时必须使用 RC-053 的备份/恢复工具和用户确认。

## 验收

`backend/tests/test_identity_migration.py` 覆盖新变量优先、旧变量警告、旧目录发现和新装目录；`backend/tests/test_api_contract.py` 锁定 OpenAPI 标题；前端 `App.test.tsx` 锁定 Rabbit Code 页面标识。`pyproject.toml` 同时提供 `rabbit` 与 `prompt-opt` 入口，模块路径保持稳定。

## 非目标

本项不重命名 `prompt_optimizer` 源码目录、不改写 RC-047 黄金评测报告中的历史产品标题、不删除 `/api/*` 旧路由、不迁移用户数据副本，也不实现跨平台安装包升级；这些边界分别由兼容期、RC-048、RC-053 和发布波次负责。
