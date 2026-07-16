# RC-026 执行证据

- RC ID: RC-026
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`1c5b1eb`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-025（已提交；正式角色签署待人工确认）
- 修改文件：独立设计 ADR、设计校验器和 CI 步骤
- 用户可见行为：设计决策必须有合法来源、许可证/NOTICE 说明、原创性声明、方案比较和人工审查范围。
- 风险与假设：本项建立设计门禁，不声称已经完成所有未来核心模块 PR 的 Provenance。

## 交付

- `docs/adr/0005-independent-agent-event-design.md` 比较类型化不可变事件与动态字典直通两种独立方案，选择方案 A。
- Provenance 只引用 RC-025 clean-room 规格、固定 Codex/OpenCode 许可来源和 Claude Agent SDK 文档事实；不引用 source-map 内容。
- `scripts/check_independent_design.py` 检查双方案、决策、来源记录和禁止复制标记。
- CI 在专有内容政策后执行独立设计 Provenance 检查。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_independent_design.py` | PASS：two alternatives, provenance, and no copied-material markers | `scripts/check_independent_design.py` |
| `python scripts/check_clean_room_boundary.py` | PASS：neutral specs 无受限标记 | `scripts/check_clean_room_boundary.py` |
| `python scripts/check_proprietary_content_policy.py` | PASS：62 个产品输入零禁用字面量 | `scripts/check_proprietary_content_policy.py` |
| `python scripts/check_source_map_denylist.py` | PASS：134 个供应链输入零命中 | `scripts/check_source_map_denylist.py` |
| `python -m ruff check scripts/check_independent_design.py` | PASS：All checks passed | `scripts/check_independent_design.py` |
| 当前设计人工 Provenance 审查 | PASS：无外部源码、测试、Prompt、资产或私有常量进入 ADR | `docs/adr/0005-independent-agent-event-design.md` |

## 未解决项

- 未来每个核心模块实现 PR 仍需单独填写 Provenance，并由正式审查者确认。
- RC-025 的研究者/实现者/审查者身份与签署仍待人工确认。

## 回滚

- 需要回滚的本项文件/迁移：删除独立设计 ADR、校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
