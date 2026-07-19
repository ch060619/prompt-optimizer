# RC-125 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-124
- 修改文件：`frontend/src/components/RabbitMark.tsx`、`frontend/src/components/SiteShell.tsx`、`frontend/src/App.tsx`、`frontend/src/marketing.tsx`、`frontend/src/onboarding.tsx`、`frontend/src/styles.css`、`frontend/tests/RabbitMark.test.tsx`、`frontend/tests/RabbitRoutes.test.tsx`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 用户可见行为：`RabbitMark` 只接受受控 `variant`，固定引用仓库内 `/rabbit-artwork.png`，不接受任意外部图片路径；workspace home/task/review/terminal/providers/models/assets/settings/diagnostics 通过 `SiteShell` 显式声明槽位，public/auth/onboarding/main workspace 保留明确的 full/mark 组件；装饰槽位不进入屏幕阅读器。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `npm --prefix frontend test -- --run tests/RabbitMark.test.tsx tests/RabbitRoutes.test.tsx` | PASS：RabbitMark 2 passed；9 路由槽位 9 passed；固定内部 src、变体和 decorative aria 行为通过 | `frontend/tests/RabbitMark.test.tsx`、`frontend/tests/RabbitRoutes.test.tsx` |
| `npm --prefix frontend test -- --run` | PASS：15 test files、58 passed；保留既有 jsdom navigation warning | `frontend/tests/` |
| `npm --prefix frontend run lint` | PASS：无 ESLint 问题 | `frontend/src/`、`frontend/tests/` |
| `npm --prefix frontend run build` | PASS：TypeScript 与 Vite production build 完成 | `frontend/dist/` |
| `python scripts/workspace.py verify` | PASS：后端 281 passed、5 skipped、31 warnings；前端 58 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、desktop boundary 和交付计划校验通过 | `docs/evidence/RC-125/README.md` |

## 未解决项

- `RabbitMark` 当前所有变体仍消费已存在的仓库 PNG；RC-122/123 的用户源素材、许可证和真实派生物仍 pending。
- 页面级视觉回归、主题/缩放/高对比截图矩阵留给 RC-133；RC-121 原生标题栏实测和 RC-057/060 外部确认不在本项伪造。

## 回滚

- 需要回滚的本项文件：删除 `RabbitMark.tsx`、两份测试和本证据，并恢复 Shell、App、marketing、onboarding、styles、执行计划和追踪索引的本项修改；不得删除或覆盖 RC-122/124 已记录的素材和设计文档。
