# RC-047 执行证据

- RC ID: RC-047
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`493b352`
- 完成 Commit：`f009f66`
- 前置 RC：RC-043、RC-046（均已完成并有证据）
- 修改文件：`backend/tests/fixtures/v2_evaluation.yml`、`backend/tests/golden/v2_regression.json`、`backend/tests/test_v2_regression.py`、`docs/migrations/RC-047-v2-regression-baseline.md`、`docs/regression/v2-baseline-policy.md`、`scripts/generate_v2_regression_baseline.py`、`docs/traceability/rc-index.md`
- 用户可见行为：无产品行为变更；新增 V2 迁移保护网，固定评分、建议、规则、模板、优化、diff、历史、导出和评测输出。
- 风险与假设：黄金快照记录当前可观察行为，不代表现有行为全部正确；有意修复必须通过新的 RC、迁移说明和基线审批，不能静默改写快照。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 2、Pending 308、Total 310、UniqueIds 310 | 本文件“基线”记录 |
| `python -m pytest backend/tests/test_v2_regression.py -q`（实现前） | FAIL（预期）：回归生成器不存在 | 本文件“测试先行”记录 |
| `python scripts/generate_v2_regression_baseline.py --approve-rc RC-047 ...` | PASS：生成 33,689 bytes、671 行黄金 JSON | `backend/tests/golden/v2_regression.json` |
| 重复生成与 SHA-256 比较 | PASS：两次均为 `4D0FD32CC4AC071EC0E01BC0ABB2DFBB95C7A8DBBF9F1DE30B51380127C8ABD7` | 本文件“可复现性”记录 |
| `python -m pytest backend/tests/test_v2_regression.py -q` | PASS：4 passed | `backend/tests/test_v2_regression.py` |
| `python -m pytest backend/tests` | PASS：43 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts/check_rc_traceability.py scripts/benchmark_tech_stack.py scripts/generate_v2_regression_baseline.py scripts/prototypes/sidecar_probe.py` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `npm --prefix frontend test` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | 本文件“完整回归”记录 |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和索引同步 | `docs/traceability/rc-index.md` |
| 新增行凭据与绝对用户路径扫描 | PASS：0 命中 | 完成 Commit `f009f66` |

## 基线

- 时间：2026-07-17（Asia/Shanghai）
- 基线 Commit：`493b352`
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 后端：39 passed；Ruff、Mypy 通过。
- 前端：9 passed；Lint、Build 通过；Vitest 的 jsdom navigation stderr 警告在修改前已存在。
- 工作树仅有用户已有未跟踪 `.runtime/` 与 `frontend/.openapi.json`。

## 测试先行

- 首次目标测试退出码为 1，收集阶段因 `scripts/generate_v2_regression_baseline.py` 不存在而失败。
- 生成器、固定评测夹具、审批策略、迁移说明和黄金文件完成后，同一目标套件为 4 passed。
- 负向测试证明迁移说明中的 RC ID 与审批 RC 不一致时，生成器拒绝更新基线。

## 可复现性

- 黄金文件中的动态 `created_at` 统一为 `<generated-at>`，评测耗时统一为 `<latency-ms>`。
- 临时数据库和绝对路径不进入快照；两次生成得到相同 SHA-256。
- Windows 首次生成发现 SQLite 文件依赖垃圾回收释放，生成器在退出临时目录前显式释放服务对象；业务存储实现未在本项修改。

## 完整回归

- 新增 4 个 V2 回归/审批测试后，后端共 43 passed。
- 快照同时包含精确输出和语义断言，覆盖九类 RC-047 要求。
- 前端无源码修改，测试、Lint 和生产构建继续通过。

## 回滚

- 需要回滚的本项文件/迁移：完成 Commit `f009f66` 及记录 RC-047 进度的后续文档提交；本项无业务代码或数据库迁移。
- 不得触碰的用户数据：`.runtime/`、`frontend/.openapi.json`、V2 用户数据库及其他未跟踪文件。

## 未解决项

- 黄金基线审批依赖仓库评审流程，尚未加入签名或 CODEOWNERS 强制门禁；发布治理波次再加固。
- 既有前端 jsdom navigation stderr 警告不属于 RC-047，保持原状并记录。
