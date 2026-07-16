# RC-048 执行证据

- RC ID: RC-048
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`fad8d45`
- 完成 Commit：`424b135`
- 前置 RC：RC-043、RC-046、RC-047（均已完成并有证据）
- 修改文件：`backend/src/prompt_optimizer/api/app.py`、`backend/tests/test_api_contract.py`、`docs/api/RC-048-compatibility.md`、`docs/api/openapi-v1.json`、`scripts/generate_openapi.py`、`docs/traceability/rc-index.md`
- 用户可见行为：保留既有 `/api/*` 客户端入口，并增加共享实现的 `/api/v1/*` 版本化入口；请求、响应、认证和 SSE 行为不分叉。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 3、Pending 307、Total 310、UniqueIds 310；W0 顺序下一项为 RC-048 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_api_contract.py backend/tests/test_api.py -q`（实现前） | FAIL（预期）：6 项契约测试中 5 项因缺少 `/api/v1`、版本化 Schema 或导出文件失败；旧 API 鉴权测试通过 | 本轮测试先行记录 |
| `python scripts/generate_openapi.py` | PASS：导出 OpenAPI 3.1.0；版本 `2.0.0`；36 条路径；22 个 Schema | `docs/api/openapi-v1.json` |
| OpenAPI 重复生成与 SHA-256 比较 | PASS：两次均为 `5B7EFA64D31685DECE12179B907DCB0BFD103F3DB72538A274BC255B2FE6C17F` | `docs/api/openapi-v1.json` |
| `python -m pytest backend/tests` | PASS：49 passed | `backend/tests/test_api_contract.py`、既有 `backend/tests/test_api.py` |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 契约决策

- `/api/analyze`、`/api/optimize`、`/api/optimize/stream`、任务、认证、项目、模板、历史/版本、diff 和导出均保留为旧客户端入口。
- 同一组能力通过 `/api/v1` 前缀提供版本化入口；新客户端只依赖导出的 v1 Schema。
- OpenAPI 使用 `x-api-version: v1`、`x-legacy-prefix: /api` 和 `x-rc-reference: RC IDs: RC-048` 标识版本与追踪边界。
- 旧入口不在本项删除或静默变更；未来废弃必须另立 RC 并提供兼容期公告和旧客户端测试。
- 前端生成客户端目录和 CI 生成差异门禁留给 RC-062；本项先冻结可生成的服务端契约。

## 测试先行与回滚

目标契约测试先在未实现版本运行，确认版本化路径、OpenAPI 元数据和导出文件缺口；实现路由别名、响应模型和导出脚本后，目标测试与既有 API 测试全部通过。

回滚本项使用完成 Commit `424b135` 的反向提交；不得触碰用户未跟踪的 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。

## 环境与遗留问题

- 时间：2026-07-17 02:04:39 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 既有前端 jsdom navigation stderr 警告在本项之前已存在，不影响 9 项测试通过。
- `/api/*` 的最终废弃窗口、生成客户端和 CI 差异门禁尚未完成，分别留给后续版本治理/RC-062；不阻塞 RC-048。
