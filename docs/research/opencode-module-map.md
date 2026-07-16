# OpenCode 模块对照与复用边界

RC IDs: RC-018

固定来源：[`anomalyco/opencode@453b61e`](https://github.com/anomalyco/opencode/commit/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d)，MIT。以下路径只来自该固定提交的 Git tree 元数据；本项目没有克隆或复制上游源码。

## 模块对照

| 模块 | 固定提交中的路径 | 可借鉴的抽象 | Rabbit Code 决策 |
| --- | --- | --- | --- |
| agent | [`packages/opencode/src/agent`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/opencode/src/agent) | 生命周期和状态边界 | 采用抽象，不复用代码 |
| cli | [`packages/cli`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/cli) | 命令层边界 | 采用抽象，不复用代码 |
| tui | [`packages/opencode/src/cli/tui`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/opencode/src/cli/tui)、[`packages/tui`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/tui) | 终端渲染与业务边界 | 采用抽象，不复用代码 |
| desktop | [`packages/desktop`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/desktop) | 桌面交付边界 | 跳过实现和资产 |
| app | [`packages/app`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/app) | 工作流分层 | 采用抽象，不复用代码 |
| server | [`packages/server`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/server)、[`packages/opencode/src/server`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/opencode/src/server) | 服务边界 | 采用抽象，不复用代码 |
| protocol | [`packages/protocol`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/protocol) | schema-first 契约边界 | 采用抽象，不复用代码 |
| llm | [`packages/llm`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/llm) | Provider 能力边界 | 采用抽象，不复用代码 |
| plugin | [`packages/plugin`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/plugin) | 扩展边界 | 采用抽象，不复用代码 |
| sdk | [`packages/sdk`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/sdk)、[`packages/sdk-next`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/sdk-next)、[`sdks/vscode`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/sdks/vscode) | 客户端契约边界 | 采用抽象，不复用代码 |
| ui | [`packages/ui`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/ui)、[`packages/app/src/components/ui`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/app/src/components/ui)、[`packages/tui/src/ui`](https://github.com/anomalyco/opencode/tree/453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d/packages/tui/src/ui) | UI 分层 | 使用 Rabbit Code 自有设计系统 |

## 数据流抽象

```text
输入/CLI/GUI -> 中立任务边界 -> Agent 状态 -> Provider/工具边界
                                      -> 协议事件 -> CLI/TUI/GUI 渲染层
```

该数据流是本项目基于公开目录结构的原创抽象，不是 OpenCode 源码、协议常量或文案的复制。
