# RC-038 执行证据

- RC ID: RC-038
- 状态：已提交（平台范围与验证责任已冻结；实测留给后续平台/安装包/测试 RC）
- 负责人：Codex
- 基线 Commit：`79b8a0f`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-037（已提交；访谈和产品范围评审待确认，不阻塞本项）
- 修改文件：`docs/support-matrix.md`、本证据和主计划进度记录
- 用户可见行为：首发平台明确为 Windows/Linux；正式支持、尽力支持和不在首发范围的组合有固定版本、架构、终端、Shell、GPU、安装包、验证环境和负责人。
- 风险与假设：本轮冻结的是验收边界，不伪造 Linux 真实机器、ARM/GPU 设备或未签名安装包实测结果；macOS 明确不在首发范围。

## 交付

- Windows 11 24H2 x64 和 Ubuntu 24.04 LTS x64 定义为首发正式支持基线。
- Windows 10、Windows/Linux arm64、NVIDIA/AMD/Intel GPU、Konsole/zsh 和 Fedora rpm 明确为尽力支持或等待固定环境。
- 终端覆盖 Windows Terminal、PowerShell、cmd、WSL 和 Ubuntu Linux Bash；GUI 验收与 CLI 验收分开。
- Windows unsigned NSIS EXE、Linux AppImage/deb 定义为正式制品格，Linux rpm 定义为尽力支持；所有制品要求 SHA-256，不要求签名或公证。
- 为正式格指定真实机器/固定 CI、验收范围和项目维护者发布签收责任。

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `Get-Content docs/support-matrix.md` 人工矩阵审查 | PASS：操作系统/架构、终端、Shell、GPU、安装包均逐格包含状态、验证环境、负责人和当前状态 | `docs/support-matrix.md` |
| RC-038 矩阵结构断言 | PASS：四个维度表的每一行均有正式支持/尽力支持/不在首发范围状态，必选环境、负责人、制品和哈希规则齐全 | `docs/support-matrix.md` |
| 首发范围审查 | PASS：仅 Windows/Linux；macOS 明确为 `out-of-scope`，未留下首发必选的 macOS 格 | `docs/support-matrix.md` |
| `python scripts/check_rc_traceability.py --write` + `--check` | PASS：需求总数 310、已关联证据 34、RC-038 查询为 GREEN，反向索引已更新 | `docs/traceability/rc-index.md` |
| RC-015 至 RC-037 跨 RC 门禁批次 | PASS：Persona、RC-036 汇总、名称/素材、第三方登记、source baseline/denylist、专有内容、clean-room、模型登记等检查通过；Ruff 通过 | `.github/workflows/ci.yml` |
| 进度不变量与 `git diff --check` | PASS：Done 34、Pending 276、Total 310、UniqueIds 310；差异无空白错误 | `docs/rabbit-code-310-detailed-execution.md` |
| 实机/CI 全组合测试 | PENDING CONFIRMATION：正式格的安装包、Linux 真实机、ARM 和 GPU 实测由后续 RC 执行；文档未伪造 PASS | `docs/support-matrix.md` |

## 未解决项

- 为 `WIN-LOCAL-X64`、`UBUNTU-LOCAL-X64` 和 `CI-UBUNTU-X64` 运行后续正式格测试，并把 `planned` 更新为可复现验证结果。
- 由后续安装包、模型、测试和发布 RC 验证 NSIS/AppImage/deb 的安装、升级、卸载、哈希和回滚路径。
- ARM/GPU/ Fedora rpm 只有在固定设备或 CI、版本和负责人可用时才执行；没有固定环境则保持尽力支持或 blocked。
- 将 RC-038 平台边界关联到 RC-039 至 RC-045 的场景、模式、版本、状态和责任分工决策。

## 回滚

- 需要回滚的本项文件/迁移：删除 `docs/support-matrix.md`、本证据和主计划 RC-038 进度记录，恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
