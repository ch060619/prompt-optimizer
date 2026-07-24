# Grok Build CLI 对标分析

## 来源与方法

审计对象是官方开源仓库 [xai-org/grok-build](https://github.com/xai-org/grok-build)，许可证 Apache-2.0，默认分支 `main`，审计提交 `7cfcb20d2b50b0d18801a6c0af2e401c0e060894`，仓库同步的上游 `SOURCE_REV` 为 `f9736c7b86f8e1c0e99e20ebbbd1195cd0c147e3`。仓库 API 元数据在 2026-07-19 获取；只读取公开源码、README、Cargo manifest、模块树和测试路径，不复制源码、提示词、测试 fixture、品牌或模型权重。

审计覆盖 `xai-grok-agent`、`xai-grok-shell`、`xai-grok-pager`、`xai-grok-workspace`、`xai-grok-tools`、`xai-tool-runtime`、`xai-tool-protocol`、`xai-chat-state`、`xai-codebase-graph`、`xai-fast-worktree`、`xai-grok-memory`、`xai-grok-mcp`、`xai-grok-hooks`、`xai-grok-compaction` 和 TUI/PTY 性能测试路径。

## 架构要点

1. **组合根与窄 crate 边界**：`xai-grok-pager-bin` 只组装 TUI；Agent、Shell、Tools、Workspace、协议和渲染各自独立，生成的根 workspace 被当作只读输入。
2. **事件/协议优先**：工具运行时和 ACP 传输以结构化 envelope、能力和错误类型连接 UI、headless、编辑器与远程入口；未知事件可降级，事件有顺序和生命周期。
3. **会话 actor 与持久化**：`xai-chat-state`、`xai-grok-shell` 将 turn、prompt queue、interjection、compaction、session fork/load/merge、JSONL durable storage 分开；取消不会遗留唤醒或孤儿 tool-call 更新。
4. **Workspace 安全边界**：权限 manager、规则、auto mode、sandbox、敏感 edit target、Git 参数防护、checkpoint/rewind 和 worktree 操作位于 workspace 层，不散落在 UI。
5. **工具和扩展治理**：MCP、OAuth、Hooks、插件 manifest/marketplace/trust、LSP 和 Web fetch 有独立能力声明、重试、截断和 SSRF/信任门禁。
6. **长期任务与可观测性**：goal planner/strategist/verifier、todo、memory dream/search、dashboard 和 session metrics 支持 run-until-done；PTY、Markdown、Mermaid、代码图和索引具有独立基准与 soak 测试。

## Rabbit Code 差异

| 能力 | Rabbit Code 当前状态 | 可借鉴做法 | 本轮决策 |
| --- | --- | --- | --- |
| Agent 循环/工具 | Python `AgentCore`、ToolRegistry、取消、预算、压缩、checkpoint 已覆盖 RC-230 | 事件 envelope、actor 生命周期、孤儿事件清理 | 保持现有 Python 边界；用统一导航/共享事件契约接近该模式，不复制 Rust 实现 |
| Provider/优化 | 原生 OpenAI/Responses/Gemini/Anthropic、离线规则、本地模型和 SSE | capability negotiation、错误分类、取消向下传播 | 已有 RC-167/170/226 继续作为契约源 |
| Workspace/变更 | 文件工具、Git/diff、checkpoint、权限矩阵、共享 revision | worktree 隔离、checkpoint store、敏感目标门禁 | 维持 Python 安全边界；发布阶段再加入真实 worktree/平台矩阵 |
| 会话/任务 | SQLite、共享 surface、CLI/GUI 事件恢复、后台任务 | JSONL durable event log、fork/merge、prompt queue | 把会话导航与任务路由集中到 Agents route catalog；不扩张持久化 schema |
| 索引/性能 | SafeSearchIndexer、固定性能 baseline | tree-sitter code graph、增量 actor、cache/query version、soak | 当前先修前端 chunk 与 Docker；代码图属于后续明确 RC，不在本轮臆造实现 |
| 扩展 | MCP/plugin/hooks 有 trust/permission 契约 | manifest + trust + capability + liveness | 复用已有扩展契约和审计，不引入上游实现/文案 |
| UI | React workspace + Tauri 壳，14 路由视觉基线 | TUI/ACP 多表面共用事件与权限 | 本轮补齐浏览器 SPA 导航；原生 Tauri bundling 仍由 RC-272+ |
| 可靠性 | 有限重试、恢复、取消、日志和 metrics | circuit breaker、cancel suppression、session load perf | 已有 RC-225~229 覆盖离线/Mock；真实长时 soak 留发布矩阵 |

## 采用与拒绝

**采用**：窄模块边界、结构化导航/事件、能力与权限集中管理、增量索引/缓存方向、独立性能门禁、扩展信任声明。  
**拒绝**：复制上游源码、加密 prompt、专有品牌/资产、默认上传整个仓库、把真实订阅 token 当 API key、把 Grok 特定服务端协议塞入 Rabbit Provider。

## 性能观察

Grok 的性能工程不是单一 benchmark：仓库提供 session load、PTY paste latency、Markdown render/search、code graph index、memory soak 和 dhat steady-state 检查。Rabbit Code 的 `rc222-v1` 保持 CLI/离线首 token/search/diff/GUI HTTP/RSS/wheel 预算；本轮 Vite 分包把最大 JS chunk 从约 500 KB 降到约 202 KB，删除未引用的 public 资源后总 dist 为 829,010 bytes。25 次 RC-271 基线和趋势自比较均通过，迁移原因与旧值保留在 `docs/performance/baseline.md`。

## 法律与来源边界

该分析是公开仓库的架构研究，不是代码复用许可。Rabbit Code 只实现独立的 Python/TypeScript 方案，继续遵守 source-map denylist、第三方 NOTICE、Apache/MIT 许可登记和 clean-room 规则。任何未来逐文件借鉴都必须先建立 provenance、许可证和人工审查记录。
