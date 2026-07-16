# RC-050 执行证据

- RC ID: RC-050
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`fd09654`
- 完成 Commit：`46485ac`
- 前置 RC：RC-048（已完成并有证据）；RC-049 按 W0 固定顺序留到 Provider Adapter 波次
- 修改文件：`backend/src/prompt_optimizer/providers/offline.py`、`backend/tests/test_offline_fallback_contract.py`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/App.test.tsx`、`docs/providers/offline-rule-fallback.md`、`docs/traceability/rc-index.md`
- 用户可见行为：工作台把 `offline` 显示为“离线规则”；远程 Provider 失败时显示离线规则和降级原因。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 4、Pending 306、Total 310、UniqueIds 310；W0 顺序下一项为 RC-050 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_offline_fallback_contract.py -q`（实现前） | FAIL（预期）：3 项中 Provider 本地元数据缺失，远程测试 Provider 名称不在现有请求枚举中 | 本轮测试先行记录 |
| `npm --prefix frontend test -- --run tests/App.test.tsx`（实现前） | FAIL（预期）：9 项中流式工作台没有“离线规则”标识 | 本轮测试先行记录 |
| `python -m pytest backend/tests/test_offline_fallback_contract.py -q` | PASS：3 passed | `backend/tests/test_offline_fallback_contract.py` |
| `python -m pytest backend/tests` | PASS：52 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| OpenAPI 重复生成与 SHA-256 比较 | PASS：两次均为 `5B7EFA64D31685DECE12179B907DCB0BFD103F3DB72538A274BC255B2FE6C17F`；RC-048 Schema 无漂移 | `docs/api/openapi-v1.json` |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 交付与决策

- `OfflineRuleProvider` 在 `ProviderRegistry` 初始化时注册，`display_name=离线规则`、`is_model=false`、`network_access=false`，不创建 HTTP 客户端或访问网络。
- 远程错误、超时、限流和 Provider 不可用是降级触发条件；同步响应和 SSE `fallback` 事件保留 `provider_used=offline`、`fallback_used=true` 和 `error_summary`。
- 用户主动选择离线规则时 `fallback_used=false`，避免把正常本地路线误标为故障回退。
- 新增 UI 状态和回退原因展示，未改变 RC-048 冻结的 OpenAPI 响应结构。

## 回滚与遗留问题

回滚本项使用完成 Commit `46485ac` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。Provider Adapter 拆分、真实本地模型和模型安装不属于本项，分别留给 RC-049 及后续 RC。

## 环境

- 时间：2026-07-17 02:15:33 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
