# RC-039 执行证据

- RC ID: RC-039
- 状态：已提交（核心场景与测试卡已定义；实现和 E2E 验证待后续 RC）
- 负责人：Codex
- 基线 Commit：`f141caf`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-038（已提交；平台正式格实测待后续 RC）
- 修改文件：`docs/product/core-scenarios.yml`、`docs/product/core-scenarios.md`、`scripts/check_core_scenarios.py`、本证据和主计划进度记录
- 用户可见行为：打开仓库到离线对话的十二个核心旅程均有前置、主流程、失败/恢复分支、功能依赖、R1-R6 映射和人工测试卡。
- 风险与假设：本轮冻结验收口径，不伪造 Agent、GUI、Provider、真实 API、真实本地模型或跨平台 E2E 已完成。

## 交付

- 定义打开仓库、编码任务、阅读代码、规划、编辑、命令、测试、diff、会话恢复、模型切换、星星优化和离线对话十二个 P0 场景。
- 每个场景至少有三步主流程、两个失败/恢复分支、RC 功能依赖和可执行人工测试卡。
- R1 至 R6 均有场景覆盖；Mock、Loopback 和离线规则作为本轮默认验证边界。
- 统一拒绝、失败、取消、降级和恢复语义，避免失败被静默跳过或离线规则冒充模型。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_core_scenarios.py` | PASS：十二个场景、R1-R6 覆盖、失败分支、依赖和人工测试卡完整 | `scripts/check_core_scenarios.py` |
| `python -m ruff check scripts/check_core_scenarios.py` | PASS：All checks passed | `scripts/check_core_scenarios.py` |
| 场景与 R1-R6 覆盖审查 | PASS：R1 至 R6 均有登记映射；所有场景保持 `planned`，未伪造实现通过 | `docs/product/core-scenarios.yml` |
| `python scripts/check_rc_traceability.py --write` + `--check` | PASS：需求总数 310、已关联证据 35、RC-039 查询为 GREEN，反向索引已更新 | `docs/traceability/rc-index.md` |
| RC-015 至 RC-038 跨 RC 门禁批次 | PASS：Persona、RC-036 汇总、名称/素材、第三方登记、source baseline/denylist、专有内容、clean-room、模型登记和 RC-038 追踪检查通过；source-map 扫描 150 个输入零命中 | `.github/workflows/ci.yml` |
| 进度不变量与 `git diff --check` | PASS：Done 35、Pending 275、Total 310、UniqueIds 310；差异无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| 实现/E2E/真实 Provider/本地模型验证 | PENDING CONFIRMATION：由后续 Agent、GUI、Provider、模型和整合测试 RC 执行 | `docs/product/core-scenarios.md` |

## 未解决项

- RC-039 场景需要在 RC-068 至 RC-158、RC-174 至 RC-200 和整合测试 RC 实现后逐卡执行并记录环境证据。
- 真实用户验证、Persona 优先级和产品范围签收仍按 RC-037 保持待确认。
- RC-040 将这些场景进一步拆为 CLI、GUI 和无头能力矩阵；RC-042 将失败/取消/降级字段转成参数集。

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-039 场景登记、人工测试卡、校验器、本证据和主计划 RC-039 进度记录，恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
