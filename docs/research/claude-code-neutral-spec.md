# Claude Code 中立行为规格

RC IDs: RC-019

本规格只把固定提交中的公开文档事实转换成中立行为描述。它不包含 Claude Code 核心二进制、商业条款代码、源码片段、内部 Prompt、测试或资源。

## 文档事实

| 事实编号 | 中立描述 | 来源 | 置信度 |
| --- | --- | --- | --- |
| DOC-001 | 产品公开 README 将其描述为终端中的编码 Agent，可通过自然语言处理日常编码任务、解释复杂代码并处理 Git 工作流。 | [固定 README](https://github.com/anthropics/claude-code/blob/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab/README.md) | 已验证文档事实 |
| DOC-002 | 官方插件材料把扩展点分为命令、Agent、Hook 和 MCP Server 等类别。 | [固定 plugins README](https://github.com/anthropics/claude-code/blob/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab/plugins/README.md) | 已验证文档事实 |
| DOC-003 | 官方 settings 示例表达了层级化配置、allow/ask/deny 权限规则、托管 Hook、marketplace 控制和 Bash 专属 sandbox 范围。 | [固定 settings README](https://github.com/anthropics/claude-code/blob/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab/examples/settings/README.md) | 已验证文档事实 |
| DOC-004 | 固定提交包含 Hook 示例、插件目录和设置示例；这些路径只证明公开材料存在，不授权复制其中实现。 | [固定提交树](https://github.com/anthropics/claude-code/tree/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab) | 已验证结构事实 |

## 黑盒观察

本轮没有运行 Claude Code 官方可执行程序，也没有进行 GUI 或 CLI 黑盒测试。因此不记录响应顺序、权限弹窗、工具事件、会话恢复或具体错误行为为已验证事实。后续若进行观察，必须保存自建输入、输出摘要、日期和版本，禁止复制官方测试夹具。

## 推测隔离

以下内容当前不批准写入 Rabbit Code 的实现规格：

- 根据 README、目录名或二手资料推断核心程序内部模块、状态机、私有协议或 Prompt。
- 将公开仓库的目录结构或插件示例等同于完整核心源码授权。
- 将文档链接当前返回 404 推断页面内容、产品行为或商业条款含义。

## Rabbit Code 处理边界

- 只参考中立的用户可观察能力类别：自然语言任务入口、Git 工作流、扩展点分类和分层权限概念。
- Rabbit Code 重新定义自己的事件、权限、Hook、MCP、文案和 UI，不复制 Claude Code 的实现、品牌、资产或文本。
- `docs/research/source-baselines.yml` 将该来源标为 `behavior-only` 且 GitHub API 未识别 SPDX；这不是法律意见，具体复用仍默认禁止。
