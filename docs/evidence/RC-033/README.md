# RC-033 执行证据

- RC ID: RC-033
- 状态：已提交（待实现 PR）
- 负责人：Codex
- 基线 Commit：`7d8d455`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-032（已提交；部分依赖许可证待确认）
- 修改文件：clean-room 重写记录、校验器和 CI 步骤
- 用户可见行为：来源不明内容只能通过中立行为规格和独立设计进入实现流程，不能直接复制或机械改写。
- 风险与假设：当前没有需要重写的核心实现 PR；本项建立流程，不伪造实现者、原创提交历史或相似性批准。

## 交付

- 行为输入限定为输入、输出、状态、约束和不确定性；禁止源文件名、原文、代码片段、Prompt、测试夹具、常量和专有资产。
- 复用 RC-026 的方案 A/B 独立设计决策，要求未来实现者先比较候选方案再编码。
- PR 必须包含 Provenance、实现者记录、原创提交历史、自建测试和人工相似性审查。
- `pending-implementation-pr` 状态确保没有把空缺实现误报为完成。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_clean_room_rewrite.py` | PASS：pending implementation、restricted access false、独立输入齐全 | `scripts/check_clean_room_rewrite.py` |
| `python -m ruff check scripts/check_clean_room_rewrite.py` | PASS：All checks passed | `scripts/check_clean_room_rewrite.py` |
| `python scripts/check_third_party_register.py --check` | PASS：32 entries, no unregistered direct dependencies | `scripts/check_third_party_register.py` |
| `python scripts/check_source_map_denylist.py` | PASS：142 个供应链输入零命中 | `scripts/check_source_map_denylist.py` |
| `python scripts/check_proprietary_content_policy.py` | PASS：68 个产品输入零禁用字面量 | `scripts/check_proprietary_content_policy.py` |
| 正式实现 PR/实现者历史 | PENDING CONFIRMATION：当前没有待重写核心 PR，角色签署待人工确认 | `docs/research/clean-room-rewrite-record.md` |

## 未解决项

- 分配正式实现者和审查者后，补充真实实现 PR、测试报告、原创提交历史和相似性审查记录。
- 在此之前不得访问 source-map 还原正文或将 restricted 材料导入实现工作树。

## 回滚

- 需要回滚的本项文件/迁移：删除 clean-room 重写记录、校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
