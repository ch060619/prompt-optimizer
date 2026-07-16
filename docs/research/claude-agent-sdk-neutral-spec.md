# Claude Agent SDK 中立接口与权利边界

RC IDs: RC-020

本记录只提炼固定提交 README、`pyproject.toml`、公开示例路径和目录元数据。SDK 的 MIT 声明不被扩展解释为 Claude Code CLI 的授权；Rabbit Code 不捆绑、下载或分发 Claude Code CLI。

## 已验证接口事实

| 事实编号 | 中立描述 | 来源 | 置信度 |
| --- | --- | --- | --- |
| SDK-001 | `query()` 返回异步消息迭代器，调用方逐条消费响应消息。 | [固定 README](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/README.md) | 已验证文档事实 |
| SDK-002 | `ClaudeSDKClient` 支持双向、交互式会话；README 将 custom tools 和 hooks 列为该客户端能力。 | [固定 README](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/README.md) | 已验证文档事实 |
| SDK-003 | custom tool 可通过 Python 函数和进程内 SDK MCP server 提供；README 也描述进程外 MCP server 的混用。 | [固定 README](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/README.md) | 已验证文档事实 |
| SDK-004 | 权限材料区分 `allowed_tools`、`disallowed_tools`、`permission_mode` 和 `can_use_tool`；`allowed_tools` 是自动批准清单，不等同于移除工具。 | [固定 README](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/README.md) | 已验证文档事实 |
| SDK-005 | README 将 Hook 描述为由 Claude Code application 在 Agent loop 的特定时点调用的 Python 函数；固定树包含 Hook 示例。 | [固定 README](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/README.md)、[Hook 示例](https://github.com/anthropics/claude-agent-sdk-python/blob/02782876a00afbcab584d501e8851b5109907077/examples/hooks.py) | 已验证文档/结构事实 |
| SDK-006 | 固定树包含 session resume、session mutations、session store 和 subprocess CLI transport 路径；README 的变更记录提到 session forking，但本轮未据此推断具体接口签名。 | [固定提交树](https://github.com/anthropics/claude-agent-sdk-python/tree/02782876a00afbcab584d501e8851b5109907077) | 结构事实；接口待确认 |

## 权利矩阵

| 组件 | 可验证声明 | Rabbit Code 处理 |
| --- | --- | --- |
| Python SDK 仓库/包 | `pyproject.toml` 声明 MIT，仓库有 `LICENSE` | 仅可在逐文件 NOTICE/版权审查后参考或复用 |
| bundled Claude Code CLI | README 声明 CLI 随 SDK 自动打包，并支持自定义 CLI 路径 | 不把 CLI 当作 SDK MIT 代码；默认不下载、捆绑、分发或复刻 |
| 官方文档 | README 链接到平台文档，但本轮已知入口返回 HTTP 404 | 待确认；不从失效链接推断商业条款或 API 细节 |
| 商业服务/条款 | 本轮未导入任何商业条款文本 | 维持默认禁止，需单独合规审查 |

## Rabbit Code 中立采用范围

- 可参考异步消息迭代、交互会话、工具/MCP、Hook、权限回调和会话存储这些问题域。
- Rabbit Code 必须定义自己的事件类型、权限决策顺序、MCP 适配器、会话模型和 CLI 生命周期。
- 不复制 SDK 源码、测试、示例代码、CLI 二进制、内部提示词、私有协议常量或商业条款内容。
