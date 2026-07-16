# RC-046 执行证据

- RC ID: RC-046
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`1f31f54`
- 完成 Commit：`4429c82`
- 前置 RC：RC-043（已完成，证据：`docs/evidence/RC-043/README.md`）
- 修改文件：`backend/tests/test_sidecar_prototype.py`、`docs/adr/0002-technology-stack-retention.md`、`docs/benchmarks/rc-046-windows.json`、`scripts/benchmark_tech_stack.py`、`scripts/prototypes/sidecar_probe.py`、`docs/traceability/rc-index.md`
- 用户可见行为：无产品 UI 变更；工程侧冻结现有八项技术职责，并提供可运行的 FastAPI sidecar 生命周期原型与基准采集命令。
- 风险与假设：本轮只在 Windows 11 实测；生产级认证、优雅退出、崩溃拉起和跨平台打包不属于本项，分别由 RC-057、RC-067、RC-207 和发布波次验证。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 1、Pending 309、Total 310、UniqueIds 310 | 本文件“基线”记录 |
| `python -m pytest backend/tests/test_sidecar_prototype.py -q`（实现前） | FAIL（预期）：sidecar 原型不存在 | 本文件“测试先行”记录 |
| `python -m pytest backend/tests/test_sidecar_prototype.py -q` | PASS：3 passed | `backend/tests/test_sidecar_prototype.py` |
| `python scripts/benchmark_tech_stack.py --output docs/benchmarks/rc-046-windows.json` | PASS：生成版本、sidecar、SQLite、Typer、前端资源与 Docker 状态 | `docs/benchmarks/rc-046-windows.json` |
| Sidecar 生命周期 | PASS：1,323 ms 就绪；2 ms 终止；无残留进程 | `docs/benchmarks/rc-046-windows.json` |
| SQLite 5,000 行单事务 | PASS：写入 2 ms，计数读取 < 1 ms | `docs/benchmarks/rc-046-windows.json` |
| Docker 状态 | LIMITATION：CLI 29.5.3 可用，Engine 未运行；未执行镜像构建 | `docs/benchmarks/rc-046-windows.json` |
| `python -m pytest backend/tests` | PASS：39 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts/benchmark_tech_stack.py scripts/prototypes/sidecar_probe.py` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `npm --prefix frontend test` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | 本文件“完整回归”记录 |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和索引同步 | `docs/traceability/rc-index.md` |

## 基线

- 时间：2026-07-17（Asia/Shanghai）
- 基线 Commit：`1f31f54`
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 后端：36 passed；Ruff、Mypy 通过。
- 前端：9 passed；Lint、Build 通过；Vitest 的 jsdom navigation stderr 警告在修改前已存在。
- 工作树仅有用户已有未跟踪 `.runtime/` 与 `frontend/.openapi.json`。

## 测试先行

- 首次目标测试退出码为 1，收集阶段因 `scripts/prototypes/sidecar_probe.py` 不存在而失败。
- 实现生命周期原型、基准采集器和 ADR 后，同一目标测试为 3 passed。

## 完整回归

- sidecar 使用随机 `127.0.0.1` 端口和临时 `PROMPT_OPTIMIZER_HOME`，不读写用户现有数据库。
- 新增 3 个验收测试后，后端共 39 passed。
- 前端无源码修改，测试、Lint 和生产构建继续通过。
- ADR 逐项评估 Python、FastAPI、React、Vite、TypeScript、SQLite、Typer 与 Docker，并记录替代方案和替换触发条件。

## 回滚

- 需要回滚的本项文件/迁移：完成 Commit `4429c82` 及记录 RC-046 进度的后续文档提交；本项无数据库迁移。
- 不得触碰的用户数据：`.runtime/`、`frontend/.openapi.json`、V2 用户数据库及其他未跟踪文件。

## 未解决项

- Windows 原型通过 `TerminateProcess` 路径回收 Uvicorn，退出码为 1；生产级优雅关闭、版本协商和崩溃监督由 RC-067 验证。
- Docker Engine 未运行，未执行镜像构建；Docker 已明确限定为开发/测试补充，不是本项桌面 sidecar 验收条件。
- macOS/Linux sidecar 与 Tauri/Electron 对比由 RC-057/M1 跨平台原型执行，本项不伪造三平台结果。
