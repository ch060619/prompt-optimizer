# RC-027 执行证据

- RC ID: RC-027
- 状态：已提交（含待确认差异）
- 负责人：Codex
- 基线 Commit：`6743ade`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-026（已完成并有证据）
- 修改文件：自建黑盒 fixture、差异报告、CLI 断言运行器和 CI fixture 校验步骤
- 用户可见行为：测试只保存中立断言和输出哈希，不保存官方完整输出或泄露测试夹具。
- 风险与假设：真实模型请求可能需要账户授权、网络和费用，本轮未执行；Rabbit Code 对照差异保持待确认。

## 交付

- Fixture 由项目自行创建，记录创建日期、命令、官方版本、公开材料依据、输出 SHA-256 和 5 项抽象断言。
- 运行器支持自建 fixture 校验和合法本地官方 CLI `--help` 黑盒检查，使用 UTF-8 容错读取 Windows 输出。
- 差异报告区分已观察断言与尚未执行的官方 vs Rabbit Code 对照，不把推测写成事实。
- CI 运行 fixture 契约检查；官方 CLI 运行作为受控本地步骤，不在 CI 中隐式触发外部请求。

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_claude_black_box_fixtures.py` | PASS：5 项自建抽象断言 fixture 校验通过 | `docs/research/black-box-fixtures/rc027-claude-cli-help.yml` |
| `python scripts/check_claude_black_box_fixtures.py --run-official` | PASS：Claude Code 2.1.202，5 项 help 断言通过；输出 SHA-256 已记录 | `docs/research/rc027-black-box-difference-report.md` |
| `python -m ruff check scripts/check_claude_black_box_fixtures.py` | PASS：All checks passed | `scripts/check_claude_black_box_fixtures.py` |
| 完整模型请求/对照差异 | PENDING CONFIRMATION：未授权发送请求，Rabbit Code 对照未运行 | `docs/research/rc027-black-box-difference-report.md` |

## 未解决项

- Rabbit Code 与官方 CLI 的真实任务差异矩阵待合法授权和受控工作目录后补充。
- 不得保存完整官方 stdout、官方测试夹具、私有 Prompt、项目源码或未脱敏路径。

## 回滚

- 需要回滚的本项文件/迁移：删除 fixture、差异报告、运行器、CI 步骤和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。
