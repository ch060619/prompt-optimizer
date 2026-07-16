# RC-018 执行证据

- RC ID: RC-018
- 状态：已完成
- 负责人：Codex
- 基线 Commit：`b8dcceb`
- 完成 Commit：`bbcd3c1`
- 前置 RC：RC-017（已完成并有证据）
- 修改文件：OpenCode 来源登记、模块对照、ADR、隔离原型和校验器
- 用户可见行为：OpenCode 的可借鉴范围被限制为抽象边界；Rabbit Code 不引入 OpenCode 上游代码或资产。
- 风险与假设：固定提交的目录树是结构证据，不等同于对每个实现细节的源码审阅；后续逐文件复用必须重新审核。

## 交付

- 固定 `anomalyco/opencode` `dev` 分支基线 SHA `453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d`，许可证元数据为 MIT。
- `docs/research/opencode-module-map.md` 覆盖 agent、cli、tui、desktop、app、server、protocol、llm、plugin、sdk、ui。
- `docs/adr/0003-opencode-research-boundary.md` 记录采用抽象、放弃实现和 MIT 义务边界。
- `scripts/opencode_boundary_prototype.py` 是原创、无上游依赖的合成事件边界原型。

## 外部核对

| 查询或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| GitHub API `repos/anomalyco/opencode` | PASS：默认分支 `dev`、许可证 MIT、未归档、未禁用 | `docs/research/source-baselines.yml` |
| GitHub API 固定提交树 | PASS：SHA `453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d` 可解析，未截断；11 个模块路径存在 | `docs/research/opencode-research-register.yml` |
| 固定 SHA 仓库页、LICENSE、README HEAD 请求 | PASS：均返回 HTTP 200 | `docs/research/opencode-module-map.md` |

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_opencode_research_register.py` | PASS：Validated OpenCode research register: 11 modules at pinned SHA | `docs/research/opencode-research-register.yml` |
| `python scripts/opencode_boundary_prototype.py` | PASS：3 synthetic events translated without upstream imports | `scripts/opencode_boundary_prototype.py` |
| `python -m ruff check scripts/check_opencode_research_register.py scripts/opencode_boundary_prototype.py` | PASS：All checks passed | `scripts/` |
| Git diff/source audit | PASS：本轮未引入 OpenCode 依赖、源码、测试、文案或 UI 资产 | 本证据与 ADR |

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-018 登记、模块图、ADR、原型、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。

## 未解决项

- 无。逐文件代码复用若在后续任务提出，必须重新完成许可证、NOTICE 和修改声明审查。
