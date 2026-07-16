# RC-032 执行证据

- RC ID: RC-032
- 状态：已提交（含待确认许可证）
- 负责人：Codex
- 基线 Commit：`bb1f6b4`
- 完成 Commit：`eff60d6`
- 前置 RC：RC-031（已提交；Gemma 条款待确认）
- 修改文件：第三方登记册、登记册政策、THIRD_PARTY_NOTICES 生成器/产物、CI 步骤
- 用户可见行为：第三方依赖和来源在发布前可追溯到版本、许可证、NOTICE、分发状态和替代方案。
- 风险与假设：PyPI 部分 license 字段为空、GSAP 为自定义 Standard license；这些条目明确 review-required，不视为批准。

## 交付

- 32 个当前直接/构建依赖全部录入 `docs/research/third-party-register.yml`，`reused_sources` 显式为空。
- 登记字段覆盖生态、名称、声明版本、观察版本、来源、许可证、NOTICE、修改、分发状态和替代方案。
- `THIRD_PARTY_NOTICES.md` 由脚本生成，禁止手工改写；未确认条目保留 UNKNOWN/review-required。
- CI 对账 backend `pyproject.toml`、frontend `package.json` 和生成 notices，阻止未登记依赖。

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_third_party_register.py --write` | PASS：生成 `THIRD_PARTY_NOTICES.md` | `scripts/check_third_party_register.py` |
| `python scripts/check_third_party_register.py --check` | PASS：32 entries, no unregistered direct dependencies | `docs/research/third-party-register.yml` |
| `python -m ruff check scripts/check_third_party_register.py` | PASS：All checks passed | `scripts/check_third_party_register.py` |
| 许可证状态审计 | PENDING CONFIRMATION：10 个条目为 metadata-null/custom/pending，全部 review-required | `THIRD_PARTY_NOTICES.md` |
| CI 配置 | PASS：RC-032 check 在 backend job 中执行 | `.github/workflows/ci.yml` |

## 未解决项

- 10 个许可证条目在补充官方 LICENSE/NOTICE 前不得进入发布放行。
- 传递依赖、锁文件、运行器第三方组件和 SBOM 对账需要后续发布门禁继续执行。

## 回滚

- 需要回滚的本项文件/迁移：删除登记册、政策、生成 notices、校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
