# RC-118 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-108、RC-111、RC-117
- 修改文件：`frontend/src/diagnostics.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/Diagnostics.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/diagnostics`；聚合 App/sidecar/runner 版本和健康、日志目录、MIT/NOTICE、更新状态、关于信息；sidecar/runner 故障提供具体重启或模型安装修复；复制诊断时使用 `[REDACTED]` 和 `[NOT INCLUDED]`，不显示 Key 或源码正文。
- 边界：组件健康、更新和日志信息当前为前端消费夹具；真实 sidecar/runner 探测、日志目录服务、版本源和系统更新通道留给后续平台 RC。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/Diagnostics.test.tsx` | PASS：3 passed；覆盖版本/健康/日志/许可证、故障修复、更新检查和脱敏诊断红线 | `frontend/tests/Diagnostics.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：11 test files、37 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：追踪索引生成并保持 current | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 37 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-118/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `Diagnostics.test.tsx`，并恢复本项对 `diagnostics.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-117 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 真实 sidecar/runner 健康探测、日志目录服务、版本源、更新通道、系统许可证聚合和剪贴板权限策略尚未接线，留给后续平台 RC。
- RC-057/060 外部确认仍 pending；既有迁移/脚本环境与前端 jsdom navigation 警告不阻塞本项。
