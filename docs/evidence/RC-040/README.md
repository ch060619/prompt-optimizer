# RC-040 执行证据

- RC ID: RC-040
- 状态：已提交（CLI/GUI/无头一致性边界已定义；实现对账待后续 RC）
- 负责人：Codex
- 基线 Commit：`848477c`
- 完成 Commit：`16f773c`
- 前置 RC：RC-039（已提交；场景实现和 E2E 待后续 RC）
- 修改文件：`docs/product/capability-matrix.yml`、`docs/product/capability-matrix.md`、`scripts/check_capability_matrix.py`、本证据和主计划进度记录
- 用户可见行为：CLI、GUI、无头模式的共享能力、唯一事件/存储 Schema 和 GUI 专属差异均有明确登记；无头缺少交互批准时必须返回机器可读状态。
- 风险与假设：本轮冻结契约边界，不伪造三表面实现、事件重放、数据库对账或完整 E2E 结果；现有 V2 API 只作为迁移依赖记录。

## 交付

- 登记 17 项能力，覆盖工作区、上下文、Agent、权限、工具、终端、Git/diff、会话、任务、Provider、优化、离线、诊断、导出和 GUI 专属能力。
- 登记三种共享事件 Schema、五种共享存储 Schema和五条一致性规则；表面只改变输入/输出/渲染。
- 明确窗口管理、拖放和系统通知是 GUI 专属，并要求拖放/通知从共享内容块或事件派生。
- 记录现有 V2 `/api/v1`、SSE、任务、历史、diff、导出作为迁移依赖，不把它们冒充最终 Agent Core。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_capability_matrix.py` | PASS：17 项能力、CLI/GUI/无头表面、共享事件/存储 Schema 和 GUI-only 约束完整 | `scripts/check_capability_matrix.py` |
| `python -m ruff check scripts/check_capability_matrix.py` | PASS：All checks passed | `scripts/check_capability_matrix.py` |
| 一致性规则审查 | PASS：每项能力只有一份 event/storage Schema；差异理由齐全；没有 CLI/无头 GUI-only 业务副本 | `docs/product/capability-matrix.yml` |
| `python scripts/check_rc_traceability.py --write` + `--check` | PASS：需求总数 310、已关联证据 36、RC-040 查询为 GREEN，反向索引已更新 | `docs/traceability/rc-index.md` |
| RC-015 至 RC-039 跨 RC 门禁批次 | PASS：既有来源、素材、第三方、source-map、专有内容、clean-room、模型、Persona、场景和追踪检查通过 | `.github/workflows/ci.yml` |
| 进度不变量与 `git diff --check` | PASS：Done 36、Pending 274、Total 310、UniqueIds 310；差异无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| 三表面实现/事件重放/存储对账 | PENDING CONFIRMATION：由 Agent Core、协议、GUI/CLI、数据模型和整合测试 RC 执行 | `docs/product/capability-matrix.md` |

## 未解决项

- RC-040 矩阵需要在 RC-056 至 RC-099、RC-213/214、RC-230 至 RC-234 和 RC-244/245 实现后执行五张验证卡。
- 现有 V2 API、React 工作台和 CLI 仍有历史入口；迁移时必须通过共享服务和事件契约消除业务分叉。
- RC-041 需要把 R1-R6 和矩阵能力排入 MVP/稳定版，RC-042 需要把矩阵状态扩展为完整状态验收。

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-040 能力登记、矩阵文档、校验器、本证据和主计划 RC-040 进度记录，恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
