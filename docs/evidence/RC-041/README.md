# RC-041 执行证据

- RC ID: RC-041
- 状态：已提交（MVP、首个稳定版和后续增强版边界已定义；发布验收待后续 RC）
- 负责人：Codex
- 基线 Commit：`e9f70c3`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-040（已提交；三表面实现对账待后续 RC）
- 修改文件：`docs/product/release-scope.yml`、`docs/product/release-scope.md`、`scripts/check_release_scope.py`、本证据和主计划/追踪记录
- 用户可见行为：版本范围明确区分 MVP、首个稳定版和增强项；R1-R6 与当前 `RC-001..RC-310` 全部进入稳定版路线，增强项有理由、复审触发和进入条件。
- 风险与假设：登记的是范围与门槛，不伪造实现、真实 Provider、真实本地模型、跨平台实机、签名制品或发布验收结果。

## 交付

- MVP 定义工作区、Agent、权限、工具、终端、诊断、星星优化和离线规则的最小纵向闭环。
- 首个稳定版显式包含 R1-R6、原初 12 类计划和 `RC-001..RC-310`，避免将原始要求标成无限期后续。
- 延后项仅包含稳定版之外的新范围：macOS/Apple GPU、ARM64/额外 Linux、签名制品/商店渠道；每项均有理由、复审触发和进入条件。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_release_scope.py` | PASS：MVP、首个稳定版、R1-R6、12 类计划、RC-001..RC-310 和延期进入条件完整 | `scripts/check_release_scope.py` |
| `python -m ruff check scripts/check_release_scope.py` | PASS：All checks passed | `scripts/check_release_scope.py` |
| R1-R6、12 类计划和 RC-001..RC-310 覆盖审查 | PASS：六项原始要求和 310 项当前计划均进入稳定版路线；增强项不挪走原始要求 | `docs/product/release-scope.yml` |
| `python scripts/check_rc_traceability.py --rc RC-041` + `--check` | PASS：RC-041 为 GREEN；版本文档、校验器和证据已登记，反向索引当前 | `docs/traceability/rc-index.md` |
| 进度不变量与 `git diff --check` | PASS：Done 37、Pending 273、Total 310、UniqueIds 310；本轮文件无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| RC-015 至 RC-040 跨 RC 门禁批次 | PASS：Persona、核心场景、三表面能力、来源基线、source-map denylist、专有内容、clean-room、模型、第三方、名称/素材和 RC-036 汇总检查全部通过 | `.github/workflows/ci.yml` |
| 真实实现、实机、真实 API、本地模型和发布验收 | PENDING CONFIRMATION：由后续实现、平台、模型、测试和发布 RC 执行 | `docs/product/release-scope.md` |

## 未解决项

- MVP 退出标准和首个稳定版发布门槛需要由后续 Agent、GUI、Provider、本地模型、整合测试和发布 RC 提供执行证据。
- 增强项不能反向缩小 R1-R6、Windows/Linux 首发范围或当前稳定版的 310 项计划；新增范围必须创建新的 RC。

## 回滚

- 需要回滚的本项文件/迁移：删除版本范围登记、文档、校验器、本证据和 RC-041 主计划/追踪记录，恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
