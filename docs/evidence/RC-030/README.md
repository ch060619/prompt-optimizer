# RC-030 执行证据

- RC ID: RC-030
- 状态：已提交（待技术/合规/法律批准）
- 负责人：Codex
- 基线 Commit：`6483383`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-029（已完成并有季度监控）
- 修改文件：`docs/legal/claude-source-map-clean-room.md`、`scripts/check_m0_clean_room_decision.py`、CI
- 用户可见行为：M0 未批准时 source-map 内容保持禁止，允许范围不会因文档存在而扩大。
- 风险与假设：本项是治理决策记录草案，不是法律意见，不伪造任何签字、资质或决策编号。

## 交付

- 汇总 RC-021 至 RC-029 的事实来源、风险、临时允许/禁止范围、角色隔离、Provenance、denylist 和季度监控。
- 明确技术负责人、合规负责人和合资格法律顾问签署字段，以及 M0 从 blocked 到 approved 的触发条件。
- 明确 source-map 正文不得进入工作树、依赖、CI、Docker、SBOM、安装包、测试夹具或发布物。
- CI 增加 M0 决策记录结构校验；未批准状态可审计但不能被误报为批准。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_m0_clean_room_decision.py` | PASS：记录完整，pending approval，M0 blocked | `docs/legal/claude-source-map-clean-room.md` |
| `python -m ruff check scripts/check_m0_clean_room_decision.py` | PASS：All checks passed | `scripts/check_m0_clean_room_decision.py` |
| `python scripts/check_source_map_denylist.py` | PASS：138 个供应链输入零命中 | `scripts/check_source_map_denylist.py` |
| `python scripts/check_proprietary_content_policy.py` | PASS：65 个产品输入零禁用字面量 | `scripts/check_proprietary_content_policy.py` |
| 技术/合规/法律签署 | PENDING CONFIRMATION：当前会话没有签署主体或决策编号 | `docs/legal/claude-source-map-clean-room.md` |

## 未解决项

- 技术负责人、合规负责人和合资格法律顾问/法域/书面意见/决策编号待人工填写。
- M0 保持 blocked；在批准前默认禁止 source-map 正文访问、运行、复制、机械改写和分发。

## 回滚

- 需要回滚的本项文件/迁移：删除 clean-room 决策记录、M0 校验器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
