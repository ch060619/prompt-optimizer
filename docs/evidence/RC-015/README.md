# RC-015 执行证据

- RC ID: RC-015
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`a1edec5`
- 完成 Commit：`5fc9361`
- 前置 RC：RC-055（已完成并有证据）

## 交付

- `docs/research/source-baselines.yml` 固定了 9 个 GitHub 来源的仓库 URL、默认分支、HEAD commit SHA、不可变 commit URL、调研日期、更新时间、许可证元数据、归档状态和禁用状态。
- `scripts/check_source_baselines.py` 校验 YAML schema、来源唯一性、GitHub canonical URL、40 位 SHA、commit URL 一致性、时间格式、许可证字段和来源分类。
- `.github/workflows/ci.yml` 增加 RC-015 source baseline 检查。
- 未克隆、读取或提交任何来源仓库源码；无许可证或 source-map 相关来源只标为 `research-only`/`behavior-only`，不视为可复用代码。

## 来源摘要

| 类别 | 数量 | 处理 |
| --- | ---: | --- |
| `open-source` | 3 | 后续 RC 可按各自许可证单独审核 |
| `behavior-only` | 1 | 只研究公开行为和文档，不复制核心实现 |
| `research-only` | 5 | 只保存元数据和研究索引；无许可证时默认禁止复用 |
| 无 SPDX 许可证 | 4 | 不得据此推断授权 |
| 已归档 | 1 | 记录状态，不能当作活跃上游 |

## 验证

| 命令 | 结果 |
| --- | --- |
| `gh api repos/{owner}/{repo}` 与默认分支 commit API | PASS：9 个来源均返回元数据和 40 位 commit SHA |
| `python scripts/check_source_baselines.py --check` | PASS：Validated 9 source baselines captured on 2026-07-17 |
| `python -m ruff check scripts/check_source_baselines.py` | PASS |
| RC-055 完成后的后端/前端回归 | PASS：后端 65 passed、Ruff/Mypy；前端 9 passed、Lint/Build |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和反向索引同步 |

## 事实边界

GitHub API 的 `license` 字段为空只表示本次 API 元数据未识别许可证，不构成法律意见；source-map 相关仓库的公开可见性也不构成 Anthropic 源码授权。RC-021 至 RC-030 负责更深入的来源事实、法律和 clean-room 审核。
