# RC-020 执行证据

- RC ID: RC-020
- 状态：已提交（含待确认项）
- 负责人：Codex
- 基线 Commit：`ced7b45`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-019（已提交并有证据）
- 修改文件：Claude Agent SDK 研究登记、中立规格、权利边界 ADR 和校验器
- 用户可见行为：SDK 能力与捆绑 CLI 的权利边界被单独记录；默认构建不下载或分发 Claude Code CLI。
- 风险与假设：SDK README/pyproject 的 MIT 声明只用于 SDK 研究边界，不作为捆绑 CLI 的授权结论。

## 交付

- 固定 `anthropics/claude-agent-sdk-python` `main` 分支基线 SHA `02782876a00afbcab584d501e8851b5109907077`，SDK 元数据声明 MIT。
- 覆盖消息流、交互客户端、custom tools/MCP、Hooks、权限、会话/分叉路径和 CLI transport。
- ADR 明确 SDK 代码与随包捆绑 CLI 是不同权利面；Rabbit Code 默认不下载、捆绑或分发 CLI。
- 未导入 SDK 源码、测试、示例实现、CLI 二进制或商业条款文本。

## 外部核对

| 查询或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| GitHub API `repos/anthropics/claude-agent-sdk-python` | PASS：默认分支 `main`、许可证元数据 MIT、未归档、未禁用 | `docs/research/source-baselines.yml` |
| GitHub API 固定提交树 | PASS：SDK、session、MCP、Hook、permission 和 CLI transport 路径存在 | `docs/research/claude-agent-sdk-research.yml` |
| 固定 README 与 `pyproject.toml` | PASS：README 声明消息/交互/MCP/Hook/权限和 bundled CLI；pyproject 声明 MIT | `docs/research/claude-agent-sdk-neutral-spec.md` |
| 官方 SDK 文档入口 | PENDING CONFIRMATION：本轮已知入口返回 HTTP 404；未推断文档内容 | `docs/research/claude-agent-sdk-research.yml` |

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_claude_agent_sdk_research.py` | PASS：8 个 SDK 组件与 CLI 权利边界校验通过 | `docs/research/claude-agent-sdk-research.yml` |
| `python -m ruff check scripts/check_claude_agent_sdk_research.py` | PASS：All checks passed | `scripts/check_claude_agent_sdk_research.py` |
| session fork 具体 API 签名 | PENDING CONFIRMATION：本轮仅确认固定树路径和 README 变更记录，未写入签名结论 | `docs/research/claude-agent-sdk-neutral-spec.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-020 登记、中立规格、ADR、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。

## 未解决项

- 官方 SDK 文档入口 404 待确认。
- session fork 的具体公开接口待确认；当前不把目录结构或 README 变更记录当成 API 签名。
- 上述待确认项不阻塞 RC-021 自动开始。
