# RC-042 执行证据

- RC ID: RC-042
- 状态：已提交（17 项功能的八状态验收、统一错误码/UI 文案和非成功参数集已定义；实现验证待后续 RC）
- 负责人：Codex
- 基线 Commit：`ab09158`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-041（已提交；版本范围和稳定版门槛已冻结）
- 修改文件：`docs/product/state-acceptance.yml`、`docs/product/state-acceptance.md`、`scripts/check_state_acceptance.py`、本证据和主计划/追踪记录
- 用户可见行为：每项 CLI/GUI/无头共享或 GUI 专属能力均有成功、失败、取消、重试、降级、离线、拒绝和恢复口径；错误码、UI 文案和至少一个非成功测试参数统一登记。
- 风险与假设：本轮定义验收契约，不伪造实现、真实 Provider、本地模型、实机、完整 E2E 或发布结果。

## 交付

- 以 RC-040 的 17 项能力为闭集，任何能力缺少八种状态时校验失败。
- 统一 `RC42-*` 错误码和 `state.*` 文案，状态必须保留原因、来源、权限或恢复线索。
- 为每项关键能力登记一个非成功参数，覆盖失败、取消、拒绝、离线、恢复和降级等分支。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_state_acceptance.py` | PASS：17 项能力、八种状态、统一错误码/UI 文案和非成功参数完整 | `scripts/check_state_acceptance.py` |
| `python -m ruff check scripts/check_state_acceptance.py` | PASS：All checks passed | `scripts/check_state_acceptance.py` |
| 八状态/错误码/UI 文案/参数覆盖审查 | PASS：每项 RC-040 能力均有完整状态期望和至少一个非成功参数 | `docs/product/state-acceptance.yml` |
| `python scripts/check_rc_traceability.py --rc RC-042` + `--check` | PASS：RC-042 为 GREEN；状态文档、校验器和证据已登记，反向索引当前 | `docs/traceability/rc-index.md` |
| 进度不变量与 `git diff --check` | PASS：Done 38、Pending 272、Total 310、UniqueIds 310；本轮文件无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| RC-015 至 RC-041 跨 RC 门禁批次 | PASS：RC-041 版本范围、Persona、核心场景、三表面能力、来源基线、source-map denylist、专有内容、clean-room、模型、第三方、名称/素材和 RC-036 汇总检查全部通过 | `.github/workflows/ci.yml` |
| 真实实现、实机、真实 API、本地模型和完整 E2E | PENDING CONFIRMATION：由后续 Agent、Provider、GUI、模型、平台和整合测试 RC 执行 | `docs/product/state-acceptance.md` |

## 未解决项

- 八状态需要在 Agent Core、Provider、GUI、CLI、模型和整合测试实现后逐参数执行并记录实际环境。
- 统一错误码和 UI 文案是验收契约，不替代后续 API 错误 Schema、终端退出码和 GUI 无障碍文案验收。

## 回滚

- 需要回滚的本项文件/迁移：删除状态验收登记、文档、校验器、本证据和 RC-042 主计划/追踪记录，恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
