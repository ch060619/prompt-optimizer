# RC-022 执行证据

- RC ID: RC-022
- 状态：已提交（待人工法律复核）
- 负责人：Codex
- 基线 Commit：`87421ae`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-021（已提交并有证据）
- 修改文件：`docs/legal/claude-source-map-legal-review.md`、`scripts/check_source_map_legal_review.py`
- 用户可见行为：法律意见缺失时，source-map 还原源码及衍生内容保持禁止访问、运行、复制和分发。
- 风险与假设：本项不构成法律意见；待人工顾问提供法域、资质、决策编号和允许/禁止范围。

## 交付

- 提供 5 个 source-map 仓库的来源包、计划用途、法律问题清单和所需书面决策字段。
- 明确版权、合同、商业秘密、再分发、clean-room 和供应链进入范围等待回答问题。
- 在书面结论前冻结 source-map 正文访问和使用，默认禁止复用。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_source_map_legal_review.py` | PASS：待人工法律复核与临时禁止规则存在 | `docs/legal/claude-source-map-legal-review.md` |
| `python -m ruff check scripts/check_source_map_legal_review.py` | PASS：All checks passed | `scripts/check_source_map_legal_review.py` |
| 合资格法律顾问书面意见 | PENDING CONFIRMATION：当前会话未提供，未伪造结论 | 本证据的“待确认”部分 |

## 待确认

- 法域、法律顾问/机构、意见日期和决策编号待填写。
- 允许范围、禁止范围和复核触发条件待法律顾问书面确认。
- 在确认前不访问、运行、复制、机械改写或分发 source-map 还原源码。

## 回滚

- 需要回滚的本项文件/迁移：删除法律复核请求、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
