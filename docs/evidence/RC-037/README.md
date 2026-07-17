# RC-037 执行证据

- RC ID: RC-037
- 状态：已提交（PENDING CONFIRMATION；访谈和产品范围评审待完成）
- 负责人：Codex
- 基线 Commit：`03974d2`
- 完成 Commit：`4d75ca9`
- 前置 RC：RC-036（已提交；M0 评审待确认）
- 修改文件：Persona 登记、Persona 文档、校验器、CI 步骤和本证据
- 用户可见行为：产品范围按五类目标用户、可测任务和约束组织；没有访谈证据的结论明确标为假设。
- 风险与假设：本轮使用仓库现有计划/架构/许可证材料校准，未进行真实用户访谈；优先级和冲突需要产品评审确认。

## 交付

- 为个人开发者、无 API 用户、多 Provider 用户、开源贡献者和团队维护者建立 Persona。
- 每类 Persona 记录目标、约束、至少三个高频任务、P0/P1 优先级和可验证结果。
- 记录隐私/Provider、速度/治理、个人/团队、范围/验证成本和视觉/扫描效率冲突，并给出解决方向。
- 将仓库/Agent、离线优化、Provider/模型、会话归属、Provenance/发布门禁映射到 Persona，覆盖当前核心能力。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_personas.py` | PASS：五类 Persona、可测任务、冲突和核心能力覆盖完整 | `scripts/check_personas.py` |
| `python -m ruff check scripts/check_personas.py` | PASS：All checks passed | `scripts/check_personas.py` |
| 访谈/问卷 | PENDING CONFIRMATION：本轮未执行，Persona 保持证据校准假设 | `docs/product/personas.yml` |
| 产品范围评审 | PENDING CONFIRMATION：P0 优先级、样本、目标时限和最终范围待评审 | `docs/product/personas.md` |

## 未解决项

- 通过真实访谈、任务观察或问卷验证五类 Persona，并记录样本、日期和偏差。
- 产品评审确认 P0/P1 优先级、目标时限、额外角色和核心能力覆盖。
- 将确认后的 Persona 与 RC-038 至 RC-041 的平台、场景、一致性和版本范围决策关联。

## 回滚

- 需要回滚的本项文件/迁移：删除 Persona 登记、文档、校验器、CI 步骤和本证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
