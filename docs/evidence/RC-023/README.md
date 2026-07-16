# RC-023 执行证据

- RC ID: RC-023
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`71d5d1a`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-022（已提交并有待人工法律复核项）
- 修改文件：denylist、扫描器、注入失败测试、pre-commit 配置、CI
- 用户可见行为：source-map 仓库 URL、仓库名、artifact 名称和固定哈希进入统一阻断门禁。
- 风险与假设：研究证据目录只用于审计，不作为产品、依赖、Docker、SBOM 或发布输入。

## 交付

- `docs/research/source-map-denylist.yml` 固定 5 个 source-map 来源的 URL、仓库名、artifact 名称和 Commit SHA。
- `scripts/check_source_map_denylist.py` 扫描已跟踪的代码、依赖、锁文件、Docker、`.gitmodules`、CI 和其他供应链输入。
- `.pre-commit-config.yaml` 和 `.github/workflows/ci.yml` 接入 denylist 检查。
- `scripts/test_source_map_denylist.py` 使用临时注入文件证明命中禁用 URL 时测试失败。

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_source_map_denylist.py` | PASS：128 个供应链输入扫描，zero hits | `scripts/check_source_map_denylist.py` |
| `python scripts/test_source_map_denylist.py` | PASS：注入禁用 URL 产生失败命中 | `scripts/test_source_map_denylist.py` |
| `python -m ruff check scripts/check_source_map_denylist.py scripts/test_source_map_denylist.py` | PASS：All checks passed | `scripts/` |
| pre-commit 配置检查 | PASS：local hook 调用 RC-023 scanner，且不依赖文件名参数 | `.pre-commit-config.yaml` |
| CI 配置检查 | PASS：backend job 在 Ruff 前执行 scanner 和注入测试 | `.github/workflows/ci.yml` |

## 范围校准

初次扫描命中了研究审计脚本中的仓库标识；该脚本不是供应链输入，已按 `evidence_only_files` 显式排除。校准后扫描结果为零命中，研究证据仍保留且可追溯。

## 回滚

- 需要回滚的本项文件/迁移：删除 denylist、scanner、测试、pre-commit 配置、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
