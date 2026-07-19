# RC-109 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-054、RC-058、RC-106、RC-107
- 修改文件：`frontend/src/onboarding.tsx`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/tests/Onboarding.test.tsx`、`docs/traceability/rc-index.md`
- 用户可见行为：新增独立 `/onboarding` 首次启动页；探测 `/api/v1/health`，读取浏览器中的非敏感配置状态标记，展示 Configuration、App Server、Key vault、Local runner 状态；新装、已有配置、服务异常分别显示对应状态；页面只有两条主要入口“USE API”和“NO API / LOCAL MODEL”，均为可聚焦链接，服务异常额外提供重试。
- 视觉与可访问性：首次视口展示 Rabbit Code 名称、现有兔兔品牌 PNG 和明确状态；主入口使用图标+文本，保留 `:focus-visible` 焦点样式和语义 heading/status/link/button；桌面与 700px 以下窗口使用稳定网格/单列布局。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/Onboarding.test.tsx` | PASS：3 passed；覆盖新装、已有配置/键盘焦点、服务异常/重试 | `frontend/tests/Onboarding.test.tsx` |
| `npm --prefix frontend test -- --run tests/App.test.tsx` | PASS：9 passed；既有首页、工作区、登录、注册和优化流程回归通过；保留 jsdom navigation warning | `frontend/tests/App.test.tsx` |
| `npm --prefix frontend run lint` | PASS | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 12 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-109/README.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除本证据文件和 `Onboarding.test.tsx`，并恢复本项对 `onboarding.tsx`、`App.tsx`、`styles.css` 和生成追踪索引的修改；不得覆盖 RC-066 至 RC-108 的既有变更。
- 不得触碰的用户数据：Provider 凭据、共享状态 JSON、会话数据库、Agent 检查点、后台进程日志和未提交用户修改。

## 未解决项

- 无实现阻塞项。真实 App Server 配置服务、Credential Manager/Secret Service、本地模型健康检查和完成选择后的生产路由接线留给后续 RC；当前 health 404 是未配置状态，网络异常是不可用状态；RC-057/060 外部确认仍 pending。
