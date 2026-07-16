# ADR-0004：Claude Agent SDK 与捆绑 CLI 的权利边界

RC IDs: RC-020

## 状态

Accepted for research; SDK and bundled CLI remain separate rights surfaces.

## 决策

将 `anthropics/claude-agent-sdk-python` 的 Python SDK 作为 MIT 声明的独立研究来源。README 明确表示 Claude Code CLI 会随 SDK 包自动捆绑，但这不证明 CLI 代码、二进制、品牌或商业条款受 SDK 的 MIT 声明覆盖。

Rabbit Code 默认不下载、捆绑、分发或复刻 Claude Code CLI。Rabbit Code 可在不复制实现的前提下参考公开 SDK 文档事实所描述的问题域：消息流、交互会话、custom tools、MCP、Hooks、权限回调和会话持久化。

## 采用

- 采用异步消息流和交互会话作为中立接口研究方向。
- 采用权限决策需要区分自动批准、拒绝和回调判断的研究方向。
- 采用 SDK MCP 与外部 MCP 的边界作为适配器设计输入，但重新定义 Rabbit Code 协议。

## 不采用

- 不把 SDK 的 MIT 许可证扩展到捆绑的 Claude Code CLI。
- 不在默认构建、安装、测试或发布产物中下载或分发 Claude Code CLI。
- 不复制 SDK 源码、示例、测试、商业条款、内部 Prompt、私有协议或 CLI 二进制。
- 不把 session fork 的目录证据当成已验证的 API 签名；该接口留待合法公开文档或黑盒验证。

## 证据

- 固定来源和组件登记：`docs/research/claude-agent-sdk-research.yml`。
- 中立规格：`docs/research/claude-agent-sdk-neutral-spec.md`。
