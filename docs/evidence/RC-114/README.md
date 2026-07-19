# RC-114 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-049、RC-052、RC-109、RC-110
- 修改文件：`frontend/src/providerModels.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/ProviderModels.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/providers`；显示 Provider 列表、配置/连接状态、能力标签、费用/未知费用、模型发现与手动模型 ID、模型选择和默认路由；支持新增、编辑、启用/禁用、删除和连接测试。
- 安全边界：API Key 输入受控为空值，仅更新“已收到 keychain 值”的状态提示；密钥不写入 DOM、localStorage 或日志。当前页面为 Provider 管理前端消费边界，真实 OS keychain、Provider 管理 API 和连接服务留给后续 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/ProviderModels.test.tsx` | PASS：2 passed；覆盖 Provider CRUD、连接测试、模型发现、手动 ID、选择、禁用、默认切换和密钥 DOM 红线 | `frontend/tests/ProviderModels.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：7 test files、26 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：追踪索引生成并保持 current | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 26 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-114/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `ProviderModels.test.tsx`，并恢复本项对 `providerModels.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-113 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 真实 Provider 管理 API、OS keychain 写入、真实连接测试、原生模型 discovery、token/cost 遥测和跨设备配置同步尚未接线，留给后续 Provider/平台 RC。
- RC-057/060 外部确认仍 pending；既有迁移/脚本环境与前端 jsdom navigation 警告不阻塞本项。
