# RC-036 调研交付汇总

RC IDs: RC-036

## 当前结论

状态：`submitted-pending-m0-review`。本文件汇总已固定的来源事实、功能问题域、ADR、许可证和不复用边界；它不把研究登记、工程 Accepted 状态或用户声明升级为完整 M0 法律/产品批准。

机器可读登记位于 `docs/research/rc036-research-delivery-summary.yml`，由 `scripts/check_rc036_research_summary.py` 校验。

## 功能对比

| 来源 | 已验证问题域 | Rabbit Code 决策 | 复用边界 |
| --- | --- | --- | --- |
| Codex CLI/App Server | 固定 SHA、Apache-2.0、CLI/App Server；官方 manual 当前 HTTP 200；桌面端仅行为观察 | 采用公开事实和独立边界 | 源码逐文件审查许可证/NOTICE；不复制桌面源码、资产或品牌 |
| OpenCode | 固定 SHA、MIT、Agent/CLI/TUI/App/Server/Protocol/LLM/Plugin/SDK 模块元数据 | 采用模块和状态边界的抽象 | 不复制上游代码、测试、文案、资源、协议常量或 UI；桌面实现跳过 |
| Claude Code | 固定公开仓库材料、README/插件/Hook/settings 文档事实 | 只采用中立能力类别 | license 未核验；不复制核心代码、商业材料、Prompt、测试、品牌和资产；黑盒观察未运行 |
| Claude Agent SDK | MIT 声明的 SDK 接口事实：消息、交互会话、工具/MCP、Hook、权限、会话 | 仅作接口问题域参考 | SDK MIT 不覆盖捆绑 CLI；不下载、捆绑、分发或复刻 CLI |
| 本地模型/运行器 | Ollama/llama.cpp MIT 元数据；Gemma gated/manual；Qwen Apache-2.0；权重未下载 | 运行器 Adapter 和用户确认后的按需模型安装 | 权重不进安装包；Gemma 条款未确认；Qwen 显示许可后按需下载并校验哈希 |
| 兔兔素材 | 用户确认 `frontend/public/rabbit-artwork.png` 为素材并声明 AI 生成；SHA-256 已固定 | 身份登记，等待权利/条款确认 | `release.allowed=false`；授权前不新增发布分发 |

## ADR 与决策索引

| 记录 | 状态 | 范围 | 当前限制 |
| --- | --- | --- | --- |
| ADR-0002 技术栈保留 | Accepted | Python/FastAPI/React/Vite/TypeScript/SQLite/Typer/Docker 职责 | 不是 Tauri、生产安全或最终协议批准 |
| ADR-0003 OpenCode 边界 | Accepted for research | 只采用抽象，不复用上游实现 | 逐文件复用需另开审查 |
| ADR-0003 本地身份与 Provider 凭据 | Accepted | 本地 JWT 与 Provider Key 分离 | 生产密钥库/撤销等留给后续安全 RC；编号与上项冲突 |
| ADR-0004 SDK 权利边界 | Accepted for research | SDK 与捆绑 CLI 分开 | CLI 默认不下载/捆绑/分发 |
| ADR-0005 独立 Agent 事件设计 | Submitted | 方案 A 类型化事件；方案 B 仅作对照 | RC-025 角色签署和实现 PR 待确认 |
| Claude source-map 决策 | Pending human approval / M0 blocked | 事实、隔离、临时禁止范围 | 技术/合规/法律签署待确认 |
| 名称与渠道审计 | Pending human legal review | 产品名、组织、包、域名、商店入口 | 商标检索与控制权核验待确认 |
| 兔兔素材授权 | Pending human confirmation | 素材身份、哈希、授权和发布阻断 | 权利人、生成服务条款和许可证待确认 |

编号注意：当前仓库有两个文件使用 `ADR-0003`，机器登记将其按文件路径区分；在发布 canonical ADR index 前必须重新编号或明确命名空间。

## 许可证清单结论

- 许可证清晰来源：Codex Apache-2.0、OpenCode MIT、Claude Agent SDK 仓库声明 MIT、Ollama/llama.cpp 固定 LICENSE 元数据 MIT、Qwen 模型元数据 Apache-2.0。
- 受限或未完成来源：Claude Code license 未识别且按 behavior-only；Gemma 使用专用条款并 gated/manual；兔兔素材许可证未知；第三方登记册 32 项中 10 项仍 review-required。
- `docs/research/third-party-register.yml` 和生成的 `THIRD_PARTY_NOTICES.md` 是依赖/NOTICE 的单独门禁，不被本汇总替代。

## 不复用清单

- 不复制 Codex 桌面源码、品牌、图标、截图或专有资产。
- 不复制 OpenCode 源码、测试、文案、内部 Prompt、协议常量、资源或 UI；只使用独立表达的抽象。
- 不复制 Claude Code 核心二进制、商业条款材料、内部 Prompt、测试、品牌或资产。
- 不把 Claude Agent SDK 的 MIT 声明扩展到捆绑 CLI；不下载、捆绑、分发或复刻 CLI。
- 不访问、运行、复制、机械改写或分发 source-map 还原内容。
- 不把模型权重放入安装包；Gemma 未经条款确认不下载，Qwen 只能按需下载并重新校验哈希。
- 兔兔素材授权未确认前不进入新的发布包、安装包、Release 附件或演示仓库。

## 跨模块评审

当前状态：`pending-human-m0-review`，`M0 approved=false`。

待签收模块为研究与来源、工程架构、合规与 Provenance、法律与素材权利。RC-025 角色签署、RC-030 source-map M0、RC-034 名称/渠道审查、RC-035 素材授权和 RC-031 Gemma 条款确认均未完成，因此本汇总只提交评审，不声明已批准。

后续架构 Issue 必须关联至少一个已批准的决策 ID，并填写证据路径、Provenance/许可证范围、审查人和日期；当前映射为空，未满足条件的 Issue 应保持 blocked。
