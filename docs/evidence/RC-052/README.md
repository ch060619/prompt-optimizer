# RC-052 执行证据

- RC ID: RC-052
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`ae6ce17`
- 完成 Commit：`eea66e9`
- 前置 RC：RC-050（已完成并有证据）
- 修改文件：`docs/adr/0003-local-identity-and-provider-credentials.md`、`backend/tests/test_auth_boundary.py`、`docs/traceability/rc-index.md`
- 用户可见行为：无破坏性行为变更；固定本地 JWT 可选身份边界，明确 Provider/API Key 不等于本地登录密码。

## 决策

- 保留 JWT 作为可选的本地应用身份层，用于用户、历史、项目和任务归属；离线分析/优化仍支持 guest。
- JWT 只包含 `sub`、`username`、`exp`，不包含 API Key、Provider 配置、提示词、源码或模型内容。
- `users` 表只保存用户名、PBKDF2 密码哈希和创建时间；Provider Key 当前仅作为进程运行时配置读取，不写入 SQLite。
- 后续持久化 Provider 凭据必须走 OS Keychain/系统密钥库；RC-179 完成前禁止写普通配置或 SQLite。
- 若未来移除 JWT，必须先做 owner 映射、双读验证、可回滚迁移和旧 Token 过期窗口，不能静默合并历史。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 5、Pending 305、Total 310、UniqueIds 310；W0 顺序下一项为 RC-052 | 本文件对应完成日志 |
| `python -m pytest backend/tests/test_auth_boundary.py -q` | PASS：2 passed；JWT 字段集合和 SQLite/Provider 配置边界均符合 ADR | `backend/tests/test_auth_boundary.py` |
| `python -m pytest backend/tests` | PASS：54 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend scripts` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 | `docs/traceability/rc-index.md` |
| `npm --prefix frontend test -- --run` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| 用户未跟踪文件检查 | PASS：`.runtime/`、`frontend/.openapi.json` 未暂存、未修改 | `git status --short --branch` |

## 威胁模型与遗留问题

ADR 记录 JWT 窃取、API Key 混入、密码哈希、guest 离线和未来移除 JWT 的控制与残余风险。生产级本地服务认证、Origin、随机令牌、撤销、登录限流和 OS 密钥库仍由后续安全 RC 负责，不在本项伪造完成。

## 环境与回滚

- 时间：2026-07-17 02:20:55 +08:00（Asia/Shanghai）
- Python：3.12.10；Node.js：24.15.0；npm：11.12.1；Git：2.54.0.windows.1。
- 回滚本项使用完成 Commit `eea66e9` 的反向提交；不得触碰 `.runtime/`、`frontend/.openapi.json`、V2 用户数据库或其他用户数据。
