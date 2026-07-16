# RC-054 执行证据

- RC ID: RC-054
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`a40afb7`
- 完成 Commit：`107df2c`
- 前置 RC：RC-053（已完成并有证据）
- 修改范围：发行包/CLI、兼容环境和路径、API/UI 标识、前端包、启动脚本、README、OpenAPI 和迁移文档；完整列表见 `107df2c`。
- 用户可见行为：产品/API/UI 新名称为 Rabbit Code；旧 `prompt-opt`、旧 `prompt_optimizer` 模块路径、旧环境变量和旧数据目录在兼容期继续可用并发出迁移警告。

## 决策

- 发行包名从 `prompt-optimizer` 更新为 `rabbit-code`；Python import 路径保持 `prompt_optimizer`，避免大规模移动。
- 新 CLI 为 `rabbit`，`prompt-opt` 指向同一 Typer 应用并提示迁移，兼容截止版本为 Rabbit Code `3.0.0`。
- 新环境变量使用 `RABBIT_CODE_*`；`PROMPT_OPTIMIZER_*` 仅回退使用，新值优先。
- 新安装默认数据目录/文件为 `rabbit-code/rabbit-code.sqlite3`；检测旧 `prompt-optimizer/prompt_optimizer.sqlite3` 时原地兼容读取，不创建第二份或覆盖旧数据。
- FastAPI OpenAPI 标题、前端站点标题和前端私有包名更新为 Rabbit Code；`/api/*` 接口兼容层不删除。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 7、Pending 303、Total 310、UniqueIds 310；W0 顺序下一项为 RC-054 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_identity_migration.py`（实现前） | FAIL（预期）：身份兼容模块不存在 | 本轮测试先行记录 |
| OpenAPI 标题测试（实现前） | FAIL（预期）：标题仍为 `Prompt Optimizer` | `backend/tests/test_api_contract.py` |
| 身份/OpenAPI/sidecar 契约测试 | PASS：相关测试通过 | `backend/tests/test_identity_migration.py`、`backend/tests/test_api_contract.py` |
| `python -m pytest backend/tests` | PASS：62 passed；存在预期的旧目录/旧环境弃用警告 | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：36 个源码文件无问题 | 本文件“完整回归”记录 |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| OpenAPI 重复生成与 SHA-256 比较 | PASS：两次均为 `5035F758C784DB0BDBE22AAAC090346247C09484AAEB76238FF61625F8EC2F34`；标题 `Rabbit Code`；36 条路径 | `docs/api/openapi-v1.json` |
| CLI/启动脚本检查 | PASS：pyproject 同时声明 `rabbit`/`prompt-opt`；旧别名兼容提示；sidecar 使用新目录；旧 Docker 标签保留 | `backend/pyproject.toml`、`start.bat` |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 现有数据、限制与回滚

本机检测到旧 `prompt-optimizer` 数据目录，应用会自动发现并给出弃用警告，没有创建新旧双写目录。历史评测报告和 `prompt_optimizer` 模块路径保留作为 V2 兼容内容，不静默改写 RC-047 黄金行为。安装包升级/卸载、旧发行包在线迁移和兼容期结束后的删除留给 RC-055/发布波次。

- 时间：2026-07-17 02:49:55 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 回滚本项使用完成 Commit `107df2c` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。
