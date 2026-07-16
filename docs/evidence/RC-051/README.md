# RC-051 执行证据

- RC ID: RC-051
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`6479c20`
- 完成 Commit：`bfe7e47`
- 前置 RC：RC-054（已完成并有证据）
- 修改文件：`backend/src/prompt_optimizer/cli/app.py`、`backend/tests/test_cli_compatibility.py`、`docs/migrations/RC-051-cli-compatibility.md`、`README.md`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `rabbit prompt` 命令组；保留平面 `rabbit` 命令和 `prompt-opt` 旧入口，旧入口发出迁移警告。

## 交付与兼容决策

- `rabbit prompt analyze/optimize/templates/history/export/evaluate/serve` 复用既有函数和服务，保持旧参数、输出和退出码。
- `rabbit analyze/...` 平面入口继续可用，避免从旧命令迁移时产生额外断点。
- `prompt-opt` 继续作为发行包入口别名，提示迁移到 `rabbit`，兼容截止 Rabbit Code `3.0.0`。
- 旧环境变量、数据目录和 SQLite 归属按 RC-054/RC-053 处理；CLI 不复制或重写用户数据。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 8、Pending 302、Total 310、UniqueIds 310；W0 顺序下一项为 RC-051 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_cli_compatibility.py -q`（实现前） | FAIL（预期）：`rabbit prompt` 子组未注册，2 项分组命令退出码 2；旧入口提示测试通过 | 本轮测试先行记录 |
| `python -m pytest backend/tests/test_cli_compatibility.py -q` | PASS：3 passed | `backend/tests/test_cli_compatibility.py` |
| `python -m pytest backend/tests` | PASS：65 passed；保留旧目录/旧环境弃用警告 | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：36 个源码文件无问题 | 本文件“完整回归”记录 |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| OpenAPI 重复生成与 SHA-256 比较 | PASS：标题 `Rabbit Code`；两次 SHA-256 均为 `5035F758C784DB0BDBE22AAAC090346247C09484AAEB76238FF61625F8EC2F34` | `docs/api/openapi-v1.json` |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 环境与回滚

- 时间：2026-07-17 02:56:28 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 回滚本项使用完成 Commit `bfe7e47` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。
- 安装包升级/卸载、CLI 独立二进制和兼容期结束后的旧入口删除留给 RC-055/发布波次；既有前端 jsdom 警告保留。
