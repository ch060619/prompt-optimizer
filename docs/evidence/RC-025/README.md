# RC-025 执行证据

- RC ID: RC-025
- 状态：已提交（待人工签署）
- 负责人：Codex
- 基线 Commit：`0170116`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-024（已完成并有证据）
- 修改文件：clean-room 角色登记、信息边界、规格模板、中立示例和校验器
- 用户可见行为：研究材料只能通过中立规格进入实现流程；原始受限材料不得进入实现工作树、CI、依赖或制品。
- 风险与假设：当前没有真实多人员权限系统或签署主体，本项只提交制度和可执行检查，不伪造签署记录。
- 范围校准：联合门禁发现 RC-023 的 `evidence_only_files` 元数据被误当作阻断 token，已在本项中修正 token 展开逻辑并重新验证零命中。

## 交付

- `researcher` 只输出输入、输出、状态、约束和不确定性；`implementer` 只接收已审查中立规格；`reviewer` 负责抽查和留痕。
- 角色登记明确 source-map 还原源码、原文、私有 Prompt、内部测试、源文件名和代码结构均不得流入 clean-room 规格。
- 提供 `docs/templates/clean-room-behavior-spec.md` 和一个无外部来源的中立 Agent 事件规格示例。
- 角色签署状态均为 `pending-human-assignment`。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_clean_room_boundary.py` | PASS：角色待签署，neutral specs 无受限标记 | `scripts/check_clean_room_boundary.py` |
| `python -m ruff check scripts/check_clean_room_boundary.py` | PASS：All checks passed | `scripts/check_clean_room_boundary.py` |
| `python scripts/check_source_map_denylist.py` | PASS：132 个供应链输入，zero hits | `scripts/check_source_map_denylist.py` |
| `python scripts/test_source_map_denylist.py` | PASS：注入禁用 URL 产生失败命中 | `scripts/test_source_map_denylist.py` |
| 角色身份/权限/签署 | PENDING CONFIRMATION：当前会话没有真实人员分配或签署记录 | `docs/legal/clean-room-role-register.yml` |
| 中立规格抽查 | PASS：示例只描述输入、输出、状态和约束，不含源文件名、原文或代码结构 | `docs/research/clean-room-specs/example-agent-event.md` |

## 未解决项

- 需要项目负责人分配研究者、实现者和审查者，配置最小权限并补充签署日期/记录。
- 在签署前维持临时默认规则：实现人员不得访问 source-map 还原仓库或正文。

## 回滚

- 需要回滚的本项文件/迁移：删除角色登记、信息边界、模板、示例、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
