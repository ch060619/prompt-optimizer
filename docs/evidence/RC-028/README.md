# RC-028 执行证据

- RC ID: RC-028
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`ed210b1`
- 完成 Commit：`b14a498`
- 前置 RC：RC-027（已提交并有待确认差异项）
- 修改文件：MIT 分析资料审计登记、审计报告、校验器和 CI 步骤
- 用户可见行为：分析资料来源必须先按 `approved/restricted/rejected` 处理，未批准内容不能成为实现 Provenance。
- 风险与假设：本轮只读固定 LICENSE/README 元数据与统计，不读取源码正文或代码片段。

## 交付

- 两个自称 MIT 的分析资料均有固定 SHA、LICENSE/README URL 和 HTTP 200 证据。
- 记录 README 代码围栏数量、外链数量、逆向分析/Anthropic 上游自述，区分结构统计与授权结论。
- 两个来源均标为 `restricted`；仅允许独立重新推导的高层问题域，不批准源码、测试、Prompt、常量、fixture 或机械实现复用。
- CI 接入 RC-028 审计校验；相关审计器列为 evidence-only，不进入产品输入扫描。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_mit_analysis_source_audit.py` | PASS：2 sources restricted, zero implementation approvals | `scripts/check_mit_analysis_source_audit.py` |
| `python -m ruff check scripts/check_mit_analysis_source_audit.py` | PASS：All checks passed | `scripts/check_mit_analysis_source_audit.py` |
| 固定 LICENSE/README API 查询 | PASS：两份 LICENSE/README 均 HTTP 200，MIT 文本可见 | `docs/research/mit-analysis-source-audit.yml` |
| README 结构统计 | PASS：代码围栏/外链为 `2/7` 和 `0/9`；不作为引用比例或授权证明 | `docs/research/mit-analysis-source-audit.md` |
| source body/code snippet 访问 | PASS：未访问、保存或运行 | `docs/research/mit-analysis-source-audit.yml` |
| `python scripts/check_source_map_denylist.py` | PASS：审计器列为 evidence-only 后零命中 | `docs/research/source-map-denylist.yml` |

## 未解决项

- 代码相似度、衍生关系和法律授权需要后续合资格审查；当前默认禁止复用。
- 许可证或上游声明变化时需要重新固定和审计。

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-028 登记、报告、校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
