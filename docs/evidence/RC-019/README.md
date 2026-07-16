# RC-019 执行证据

- RC ID: RC-019
- 状态：已提交（含待确认项）
- 负责人：Codex
- 基线 Commit：`7fb6cee`
- 完成 Commit：待本项记录提交后固定
- 前置 RC：RC-018（已完成并有证据）
- 修改文件：Claude Code 公开材料登记、中立行为规格和资料校验器
- 用户可见行为：官方公开材料按固定 SHA 归档；规格明确区分文档事实、黑盒观察和推测。
- 风险与假设：GitHub API 未识别该仓库 SPDX 许可证；这不是法律意见，默认不复制核心代码或商业条款材料。

## 交付

- 固定 `anthropics/claude-code` `main` 分支基线 SHA `c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab`。
- 索引固定提交中的 README、插件 README、Hook 示例、settings 示例、插件目录和 `LICENSE.md` 路径。
- 中立规格只记录已读取的公开文档事实；黑盒观察保留为 `not-run`，推测保留为 `not-approved`。
- 未导入核心二进制、商业条款代码、源代码、测试夹具、内部 Prompt 或资源。

## 外部核对

| 查询或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| GitHub API `repos/anthropics/claude-code` | PASS：默认分支 `main`、未归档、未禁用；许可证字段为空 | `docs/research/source-baselines.yml` |
| GitHub API 固定提交树 | PASS：SHA `c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab` 可解析，未截断；examples/plugins/hooks/settings 路径存在 | `docs/research/claude-code-public-materials.yml` |
| 固定 SHA README、plugins README、settings README、Hook 示例和 LICENSE 页面 | PASS：固定 GitHub 页面可访问；只记录公开材料事实 | `docs/research/claude-code-neutral-spec.md` |
| `https://code.claude.com/docs/en/overview` 与 `/hooks` | PENDING CONFIRMATION：本轮 HEAD 返回 HTTP 404；未推断页面内容 | `docs/research/claude-code-public-materials.yml` |

## 验证

| 命令 | 结果 | 证据路径 |
| --- | --- | --- |
| `python scripts/check_claude_public_materials.py` | PASS：文档事实、待确认链接和观察边界校验通过 | `docs/research/claude-code-public-materials.yml` |
| `python -m ruff check scripts/check_claude_public_materials.py` | PASS：All checks passed | `scripts/check_claude_public_materials.py` |
| 黑盒 CLI/GUI 观察 | PENDING CONFIRMATION：本轮未执行，不写入行为事实 | `docs/research/claude-code-neutral-spec.md` |

## 回滚

- 需要回滚的本项文件/迁移：删除 RC-019 材料登记、中立规格、校验器和证据，并恢复主计划指针。
- 不得触碰的用户数据：`.runtime/` 和 `frontend/.openapi.json` 未跟踪文件。

## 未解决项

- 官方文档 URL 404 待确认。
- 黑盒 CLI/GUI 观察未执行，后续只能在合法可用的官方程序和公开行为范围内补充。
- 根据当前会话规则，上述待确认项不阻塞 RC-020 自动开始。
