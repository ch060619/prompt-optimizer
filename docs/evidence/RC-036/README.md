# RC-036 执行证据

- RC ID: RC-036
- 状态：已提交（PENDING CONFIRMATION；M0 评审未批准）
- 负责人：Codex
- 基线 Commit：`2376aed`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-035（已提交；素材授权仍待确认）
- 修改文件：调研汇总、机器登记、校验器、CI 步骤和本证据
- 用户可见行为：后续架构工作只能引用已登记的决策和来源边界；没有批准决策的 Issue 保持 blocked。
- 风险与假设：本轮汇总已验证的来源事实和已有记录，不替代法律意见、M0 签署、商标/素材授权或模型条款确认。

## 交付

- 汇总 Codex、OpenCode、Claude Code、Claude Agent SDK、本地模型/运行器和兔兔素材的事实、决策与复用边界。
- 建立功能问题域对比、ADR/法律决策索引、许可证矩阵和明确的不复用清单。
- 把重复 `ADR-0003` 编号记录为待修正风险，按文件路径区分，未伪造 canonical ADR 编号。
- 建立跨模块评审登记：研究、工程、合规/Provenance、法律/素材均待签收；M0 保持 blocked。
- 建立后续架构 Issue 门禁字段：批准决策 ID、证据路径、Provenance/许可证范围、审查人和日期；当前映射为空。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_rc036_research_summary.py` | PASS：六组来源、七项不复用边界、ADR 索引和 M0/Issue 门禁完整 | `scripts/check_rc036_research_summary.py` |
| `python -m ruff check scripts/check_rc036_research_summary.py` | PASS：All checks passed | `scripts/check_rc036_research_summary.py` |
| M0 跨模块签收 | PENDING CONFIRMATION：`m0_approved=false`；RC-025、RC-030、RC-034、RC-035、RC-031 仍有阻塞 | `docs/research/rc036-research-delivery-summary.yml` |
| 后续架构 Issue 决策映射 | PENDING CONFIRMATION：门禁已定义，当前没有已批准 Issue 映射 | `docs/research/rc036-research-delivery-summary.md` |
| 来源/许可证/不复用材料 | PASS：均指向现有固定登记和边界文档；不新增外部实现或专有资产 | `docs/research/rc036-research-delivery-summary.md` |

## 未解决项

- 组织 M0 评审并由研究、工程、合规和法律/素材责任人逐份签收。
- 为正式架构 Issue 绑定批准 ADR/决策 ID、证据、Provenance、许可证范围、审查人和日期。
- 重新编号或命名空间化两个 `ADR-0003` 文件后，再生成最终 canonical ADR 索引。
- RC-031 Gemma 条款、RC-034 名称/渠道法律审查、RC-035 兔兔授权和 RC-030 source-map M0 仍按各自门禁处理。

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-036 汇总、登记、校验器、CI 步骤和本证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
