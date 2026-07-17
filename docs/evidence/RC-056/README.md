# RC-056 执行证据

- RC ID: RC-056
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`c9394b1`
- 实现 Commit：`04de5ae`
- 前置 RC：RC-049（实现 `78f2f19`，证据 `c9394b1`）；RC-050 至 RC-055 已完成
- 修改范围：`workspace.toml`、`scripts/check_monorepo.py`、`scripts/workspace.py`、`backend/tests/test_monorepo.py`、工作区边界 README、`docs/architecture/monorepo-boundary.md`

## 交付

- 建立根级 `workspace.toml`，统一工作区名称和 `3.0.0` 版本，登记 desktop、CLI、backend/Agent Core、frontend、protocol、UI、scripts、tests、docs 和 data 成员边界。
- 增加根级 `install`、`check`、`test`、`build`、`verify` 任务入口；当前已验证 Python editable 安装、frontend 依赖安装、检查、测试和构建链路。
- 保留已验证的 `backend/src/prompt_optimizer` 和 `frontend/src` 路径，新增 `apps/*`、`backend/rabbit_code`、`packages/*` 和根 `tests` 的迁移边界说明，不进行破坏性搬迁。
- 校验器检查成员目录、backend/frontend/lockfile 版本一致性、任务入口和当前 Python 跨层私有导入；未来协议和 UI 包在对应 RC 稳定后再承载代码。

## 验证

| 命令或检查 | 结果 |
| --- | --- |
| 实现前 `python -m pytest backend/tests/test_monorepo.py -q` | FAIL（预期）：`scripts.check_monorepo` 尚不存在 |
| `python -m pytest backend/tests/test_monorepo.py -q` | PASS：1 passed |
| `python scripts/check_monorepo.py` | PASS：workspace manifest and boundaries are valid |
| `python scripts/workspace.py install` | PASS：backend editable 安装成功；frontend 依赖安装成功；未改变 frontend lockfile 内容哈希 |
| `python scripts/workspace.py verify` | PASS：根级 check、Ruff、Mypy、后端 70 passed、前端 9 passed、Lint、Build 全部通过 |
| `python scripts/check_rc_traceability.py --check` | PASS |
| `python scripts/check_delivery_plan.py` | PASS：RC-001..RC-310 工作包字段和日期依赖有效 |
| `git diff --check` | PASS |

## 范围与决策

- 本 RC 完成的是可验证的 Monorepo 边界和根任务编排，不提前搬迁已完成 RC 依赖的源码；每次后续迁移必须保持构建和兼容测试通过。
- 未引入新的构建框架或付费服务。安装复用了现有 Python/npm 依赖和锁文件；没有真实 API、模型下载或外部账户操作。
- 当前边界检查拒绝 backend/scripts 导入 frontend、apps 或 packages；版本化协议、共享 Agent Core、Tauri 壳和真正的 UI 包装分别留给 RC-057 至 RC-061 及后续任务。

## 回滚与遗留问题

回滚本项使用 `04de5ae` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。`apps/*`、`packages/*` 和 `backend/rabbit_code` 目前是受约束的迁移边界，尚非生产实现目录。

## 环境

- 时间：2026-07-17 15:23:05 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1
