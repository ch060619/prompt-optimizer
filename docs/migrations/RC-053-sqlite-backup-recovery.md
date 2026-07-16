# RC-053 SQLite 备份、迁移与恢复

- RC ID: RC-053
- 状态：已完成
- 当前 Schema：`PRAGMA user_version = 1`
- 适用数据库：现有 V2 `prompt_optimizer.sqlite3` 及其临时/测试副本

## 迁移策略

`StorageService` 在打开已有数据库时先读取 `PRAGMA user_version`。版本 0 视为现有 V2 数据，升级到版本 1 前自动创建同目录 `backups/` 下的 SQLite 热备和 JSON manifest；如果设置 `PROMPT_OPTIMIZER_CONFIG` 且文件存在，同时复制一份配置文件到同一备份批次。版本 1 重复打开是幂等的，不会再次创建迁移备份；高于当前版本的数据库直接拒绝打开。

Schema 建表、兼容列补齐和 `user_version` 更新位于同一 SQLite 事务。迁移异常时事务回滚，原数据库仍保持原字节内容，迁移前备份仍可用于恢复。manifest 记录来源路径、前后版本、数据库 SHA-256、配置副本和创建时间；备份目录包含用户数据和可能的配置秘密，必须按敏感数据保护。

## 运维命令

手工备份：

```powershell
& .\.venv\Scripts\python.exe scripts\backup_db.py `
  --database "$env:PROMPT_OPTIMIZER_DB" `
  --config "$env:PROMPT_OPTIMIZER_CONFIG"
```

只读检查备份，不创建或修改恢复目标：

```powershell
& .\.venv\Scripts\python.exe scripts\restore_db.py `
  --backup .\backups\prompt_optimizer-pre-v0-to-v1-<stamp>.sqlite3 `
  --database .\recovery\prompt_optimizer.sqlite3 `
  --check-only
```

显式恢复到不存在的目标；覆盖已有目标必须额外给出 `--overwrite`：

```powershell
& .\.venv\Scripts\python.exe scripts\restore_db.py `
  --backup .\backups\prompt_optimizer-pre-v0-to-v1-<stamp>.sqlite3 `
  --database .\recovery\prompt_optimizer.sqlite3
```

恢复工具先用只读连接执行 `PRAGMA integrity_check`，再恢复到同目录临时文件，校验成功后原子替换目标。配置副本只有同时显式传入 `--config-backup` 和 `--config` 才会复制。

## 验收

`backend/tests/test_storage_backup.py` 使用真实 V2 形状的副本，验证版本升级后 users、prompt_versions、tasks 数量一致；注入迁移异常后验证原数据库哈希、版本号和完整性不变，并验证备份可只读检查和恢复。该测试不读写用户 `.runtime/` 或默认应用数据库。

## 限制

本项完成单机 SQLite 备份和恢复，不声称解决并发写入协调、跨设备同步、加密备份、自动保留策略或云端灾备。WAL/并发、发布备份策略和更高版本迁移由 RC-214、发布治理和后续数据库 RC 继续加固。
