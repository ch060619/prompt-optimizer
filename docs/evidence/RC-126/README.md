# RC-126 执行证据

- 状态：已完成
- 负责人：Codex
- 基线 Commit：`5610c00`
- 完成 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-125
- 修改文件：`docs/design/rabbit-coverage-matrix.json`、`docs/design/rabbit-coverage-matrix.md`、`scripts/check_rabbit_coverage_matrix.py`、`scripts/workspace.py`、`docs/rabbit-code-310-detailed-execution.md`、`docs/traceability/rc-index.md`
- 交付：结构化 14 路由 manifest；自动生成 Markdown 矩阵；字段包含素材变体、位置、Desktop 尺寸、响应式行为、主题、替代文本和视觉快照 ID；`workspace.py check` 强制检查 matrix current，并从 `App.tsx` 路由比较未登记新增路径。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rabbit_coverage_matrix.py --write` | PASS：生成 `docs/design/rabbit-coverage-matrix.md`，共 14 routes | `docs/design/rabbit-coverage-matrix.json`、`docs/design/rabbit-coverage-matrix.md` |
| `python scripts/check_rabbit_coverage_matrix.py --check` | PASS：route coverage matrix current | `scripts/check_rabbit_coverage_matrix.py` |
| `\.venv\Scripts\python.exe -m ruff check scripts\check_rabbit_coverage_matrix.py` | PASS | `scripts/check_rabbit_coverage_matrix.py` |
| `python scripts/workspace.py verify` | PASS：route matrix 门禁、后端 281 passed、5 skipped、31 warnings；前端 58 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-126/README.md` |

## 设计边界

- 生成器使用 `App.tsx` 的显式 pathname 路由作为新增路由门禁，根 `/` 由固定入口补入；通用 marketing route 仍由 `SiteRoute`/`SharedRabbit` 统一承载。
- RC-122/123 的源素材和派生文件仍 pending；矩阵登记 intended variants，不把未经授权素材写进发布物。

## 回滚

- 需要回滚的本项文件：删除 coverage manifest、生成 Markdown、校验脚本，并恢复 `workspace.py`、执行计划和追踪索引的本项修改；不得覆盖 RC-124/125 设计和组件实现。
