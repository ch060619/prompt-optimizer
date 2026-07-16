# RC-053 执行证据

- RC ID: RC-053
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`0444544`
- 完成 Commit：`994983f`
- 前置 RC：RC-052（已完成并有证据）
- 修改文件：`backend/src/prompt_optimizer/storage/backup.py`、`backend/src/prompt_optimizer/storage/service.py`、`backend/tests/test_storage_backup.py`、`scripts/backup_db.py`、`scripts/restore_db.py`、`docs/migrations/RC-053-sqlite-backup-recovery.md`、`docs/traceability/rc-index.md`
- 用户可见行为：已有 SQLite 打开时自动执行版本化升级前备份；新增显式备份、只读完整性检查和恢复工具。

## 交付

- `PRAGMA user_version` 从现有 V2 的版本 0 升级到 Schema 版本 1；版本 1 重开幂等，高版本数据库拒绝打开。
- 迁移前使用 SQLite backup API 生成热备和 JSON manifest；`PROMPT_OPTIMIZER_CONFIG` 指向的配置文件可随批次复制。
- Schema 创建、兼容列补齐和版本更新在同一事务中；注入异常时回滚，原库哈希、版本号和完整性不变。
- `scripts/restore_db.py --check-only` 通过只读连接检查备份；显式恢复先写临时文件、校验后原子替换，覆盖已有目标必须给 `--overwrite`。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 6、Pending 304、Total 310、UniqueIds 310；W0 顺序下一项为 RC-053 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_storage_backup.py -q`（实现前） | FAIL（预期）：收集阶段因 `prompt_optimizer.storage.backup` 不存在而失败 | 本轮测试先行记录 |
| `python -m pytest backend/tests/test_storage_backup.py -q` | PASS：4 passed | `backend/tests/test_storage_backup.py` |
| 真实 V2 副本迁移演练 | PASS：users、prompt_versions、tasks 数量保持一致；版本 0 -> 1；manifest 和配置副本存在 | `backend/tests/test_storage_backup.py` |
| 迁移故障注入 | PASS：原数据库 SHA-256、`user_version=0` 和 `integrity_check=ok` 保持不变；迁移前备份存在 | `backend/tests/test_storage_backup.py` |
| 只读备份检查与恢复 | PASS：备份和恢复目标完整性为 `ok`，恢复后数据计数与源库一致 | `backend/tests/test_storage_backup.py` |
| `python -m pytest backend/tests` | PASS：58 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：35 个源码文件无问题 | 本文件“完整回归”记录 |
| `python scripts/backup_db.py --help`、`python scripts/restore_db.py --help` | PASS：命令参数可加载 | 本文件“工具检查”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 回滚与限制

回滚本项使用完成 Commit `994983f` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。备份文件和配置副本可能包含敏感数据，本项未实现加密、保留周期、跨设备同步或并发写入协调；这些由 RC-214、发布治理和后续数据库 RC 加固。

## 环境

- 时间：2026-07-17 02:30:54 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
