# RC-115 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-049、RC-094、RC-114
- 修改文件：`frontend/src/localModels.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/LocalModels.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增 `/workspace/models`；显示硬件/磁盘/runner readiness，提供 Gemma 3 4B 与 Qwen2.5-Coder 7B 推荐；许可证确认后可开始、暂停、恢复、完成下载、取消、校验、修复、加载、停止和卸载模型。
- 边界：本项实现本地模型安装生命周期的前端消费边界；下载、哈希校验、App Server 进度订阅、真实模型文件和 runner 进程未接线，不伪造为实机验证。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/LocalModels.test.tsx` | PASS：3 passed；覆盖硬件 readiness、许可证、Gemma 成功生命周期、Qwen 暂停/恢复/取消、校验失败和修复 | `frontend/tests/LocalModels.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：8 test files、29 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/check_rc_traceability.py --write` | PASS：追踪索引生成并保持 current | `docs/traceability/rc-index.md` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 29 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-115/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `LocalModels.test.tsx`，并恢复本项对 `localModels.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-114 的既有变更。
- 不得触碰的用户数据：工作区文件、Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 真实下载/校验文件、App Server 进度订阅、真实模型 runner、断网/磁盘不足实机故障注入和状态与实际文件/进程一致性尚未接线，留给后续 RC。
- RC-057/060 外部确认仍 pending；既有迁移/脚本环境与前端 jsdom navigation 警告不阻塞本项。
