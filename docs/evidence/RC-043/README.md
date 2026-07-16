# RC-043 执行证据

- RC ID: RC-043
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`ab7b65b`
- 完成 Commit：`ed0e098`
- 前置 RC：无（W0 首项）
- 修改文件：`.github/ISSUE_TEMPLATE/rabbit-code.yml`、`.github/pull_request_template.md`、`.github/workflows/ci.yml`、`backend/tests/test_rc_traceability.py`、`docs/templates/`、`docs/traceability/`、`scripts/check_rc_traceability.py`
- 用户可见行为：贡献者可在 ADR、Issue、PR、测试、文档和 Release Note 模板中填写 RC ID，并生成、校验或查询反向索引。
- 风险与假设：现有 V2 代码在 RC 迁移前保留为 `RED`，不为通过检查而伪造关联；`RED` 是待处理追踪状态，模板缺失、ID 不完整或索引过期才阻断 CI。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| 主控进度核对命令（修改前） | PASS：Done 0、Pending 310、Total 310、UniqueIds 310 | 本文件“基线”记录 |
| `python -m pytest backend/tests/test_rc_traceability.py -q`（实现前） | FAIL（预期）：追踪脚本不存在 | 本文件“测试先行”记录 |
| `python -m pytest backend/tests/test_rc_traceability.py -q` | PASS：4 passed | `backend/tests/test_rc_traceability.py` |
| `python scripts/check_rc_traceability.py --check` | PASS：模板和索引同步 | `docs/traceability/rc-index.md` |
| `python scripts/check_rc_traceability.py --rc RC-043` | PASS：返回 RC-043 全部仓库证据 | `docs/traceability/rc-index.md` |
| `python -m pytest backend/tests` | PASS：36 passed | 本文件“完整回归”记录 |
| `python -m ruff check backend` | PASS | 本文件“完整回归”记录 |
| `python -m mypy backend/src` | PASS：34 个源码文件无问题 | 本文件“完整回归”记录 |
| `npm --prefix frontend test` | PASS：9 passed；保留既有 jsdom navigation stderr 警告 | 本文件“完整回归”记录 |
| `npm --prefix frontend run lint` | PASS | 本文件“完整回归”记录 |
| `npm --prefix frontend run build` | PASS：Vite 构建成功 | 本文件“完整回归”记录 |
| `git diff --cached --check` | PASS | 完成 Commit `ed0e098` |

## 基线

- 时间：2026-07-17（Asia/Shanghai）
- Python：3.12.10
- Node.js：24.15.0
- npm：11.12.1
- Git：2.54.0.windows.1
- 后端：32 passed；Ruff、Mypy 通过。
- 前端：9 passed；Lint、Build 通过；Vitest 存在修改前已出现的 jsdom navigation stderr 警告。

## 测试先行

- 首次目标测试退出码为 1，收集阶段因 `scripts/check_rc_traceability.py` 不存在而失败。
- 实现脚本、模板和索引后，同一目标测试为 4 passed。

## 完整回归

- 后端新增 4 个追踪契约测试后共 36 passed。
- 前端未修改，测试、Lint 和生产构建仍通过。
- 反向索引仅识别显式 `RC ID:` / `RC IDs:` 字段，避免说明文字或夹具误报证据。

## 回滚

- 需要回滚的本项文件/迁移：完成 Commit `ed0e098` 及记录 RC-043 进度的后续文档提交。
- 不得触碰的用户数据：`.runtime/`、`frontend/.openapi.json` 及任何 V2 本地数据。

## 未解决项

- 309 个 RC 需求尚待后续波次实施，报告保持 `RED`。
- 48 个现有代码文件尚无显式 RC 关联，应在对应迁移或维护 RC 中逐项处理；不阻塞 RC-043 的追踪基础设施验收。
