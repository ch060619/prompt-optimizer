# Rabbit Code 主控执行计划

## 最重要要求：每完成一个要点，必须立即记录进度

这是本项目最高优先级的执行规则。任何 AI、开发者或自动化任务每完成一个 RC 要点后，必须在结束当前工作前更新本文件。没有完成进度记录，该要点视为**尚未完成**，不得开始下一项。

每完成一个要点，必须在同一次修改中完成以下四个动作：

1. 在本文件末尾“原始 310 项基线清单”中，把对应 `RC-xxx` 的复选框从 `[ ]` 改成 `[x]`。
2. 更新下面的“跨对话进度快照”：填写最后完成项、下一待执行项、当前里程碑、最近验证结果和更新时间。
3. 在下面的“完成日志”表格末尾追加一行，记录 RC 编号、完成时间、Commit、测试结果、证据路径和遗留问题。
4. 为该项保存执行证据。默认路径为 `docs/evidence/RC-xxx/README.md`；若证据在 GitHub Issue/PR，则在日志中填写可访问链接。

新对话开始后的第一条操作也被固定：**先读取本节的进度快照和完成日志，再读取“下一待执行项”的详细执行卡；禁止从 RC-001 重新开始，禁止凭记忆猜测进度。**

### 跨对话进度快照

> 执行者每完成一个要点后必须覆盖更新本表，不得只追加日志而忘记更新指针。

| 字段 | 当前值 |
| --- | --- |
| 项目总项数 | 310 |
| 已完成项数 | 310 |
| 最后完成项 | RC-310 |
| 下一待执行项 | 无 — 全部完成 |
| 最近更新时间 | 2026-07-22 17:25:00 +08:00 |
| 本次状态补充 | RC-154 已完成：九类目标进入生成的 OpenAPI 契约与 GUI/API/同步/流式/后台任务链路；离线规则和云 adapter 仅把目标作为用户上下文；全关闭组合返回 HTTP 400。RC-155 已完成：规则、模板与模型组合策略经同一 Service 路由，规则建议仅进入云端用户上下文，模型失败回退离线规则。RC-156 已完成：控制字符一次清理、空值/长度、结构与语言验证均在保存前执行；无效输出不保存原文替换。RC-157 已完成：非敏感 metadata 记录质量前后分、差值、Provider、模型、延迟和降级，不含完整提示词。RC-158 已完成：评测集固定为 `rc-158-v1`/种子 158，共 60 个样本，覆盖编码、商务、教育、创意、长文本、代码块、变量、中文和对抗输入；报告定义 analyzer 自动评分与双人盲评协议，并生成稳定盲评批次。RC-159 已完成：首次启动将 API 路线明确为 `USE API / CONFIGURE PROVIDER`，Provider API Key 明确不是 Rabbit Code 账户密码，真实账户登录保留 `ACCOUNT LOGIN`。RC-160 已完成：OpenAI Chat Completions Adapter 支持标准 Base URL、API Key、模型、组织/项目头、messages、SSE、工具定义/工具调用和常见 HTTP 错误映射，默认不记录密钥或请求正文。RC-161 已完成：Responses API 使用独立 Adapter 和协议选择；请求使用 `instructions/input/text`，支持响应事件、工具调用、结构化输出和取消检查，Chat 路径不发送 Responses 参数。RC-162 已完成：Gemini 原生 Adapter 支持 `generateContent`/`streamGenerateContent`、contents/parts、System Instruction、function calling、安全设置、Gemini 错误结构和 `x-goog-api-key`。RC-163 已完成：Anthropic Messages Adapter 支持版本/扩展头、system/content blocks、tool use/result、SSE 事件、usage、prompt caching 与 capability probe。RC-164 已完成：Claude Code 格式只映射到 Anthropic Messages 或经批准的官方 Agent SDK；仅允许官方 API Key/OAuth，拒绝 Cookie、订阅 Token、内部令牌、逆向登录和 CLI 分发。RC-165 已完成：Azure deployment/api-version/API key、Vertex project/region/Bearer + Gemini 原生 payload、Bedrock Converse region/model + 官方 SigV4 signer 注入边界均已实现并通过 Mock 契约。RC-166 已完成：以数据驱动 Preset 覆盖 OpenRouter、DeepSeek、Moonshot/Kimi、Qwen、豆包、智谱、SiliconFlow、Groq、Together、Ollama 和 LM Studio；Preset 提供默认 Base URL、模型发现路径、兼容级别、限制说明和敏感头标记，Registry 支持环境变量覆盖与自定义头。RC-167 已完成：能力 schema v1、Adapter 静态能力矩阵、探测结果覆盖和带 TTL 的版本化缓存接入 Agent；不支持的可选工具被禁用，必需结构化输出被拒绝，GUI 模型发现仅在 `MODEL LISTING` 已声明或连接探测成功后启用。RC-168 已完成：ModelDiscoveryService 为 Preset `/models` endpoint 提供 cursor 分页、TTL 缓存、空列表与错误分类；Registry 复用发现服务，手动/已保存模型在失败时保留，模型 ID 仅做格式校验。RC-169 已完成：Mock-first 分阶段连接检查覆盖 credentials、model、capabilities、first event 和 tool schema；真实模式只在自有凭据、明确确认、费用警告、token 上限和注入发送器同时满足时执行；默认不外发。RC-170 已完成：Provider 统一 11 类错误分类，所有协议 Adapter 共享状态码/错误体映射和脱敏 Provider request ID；API/流式/CLI/UI 共享错误码、退出码、重试性和修复动作。RC-171 已完成：指数退避、抖动、`Retry-After`、取消中断、HTTP(S) 代理、NO_PROXY、自定义 CA、IPv4/IPv6 和 opaque 代理凭据 resolver 均已接入；按用户指令自动进入 RC-172。 |
| 本项状态补充 | RC-172 已完成：每会话、global/workspace 默认和独立优化模型路由已接入 Registry；不可用路由暴露健康状态与 fallback chain，并回退离线 Provider；请求发送前估算 Token/费用并按最大 Token/费用限制拦截；限制和估算写入 API、CLI、流式、任务和优化 metadata。RC-180 已完成：前端固定掩码/末尾四位、运行时密钥指纹、API/流式错误格式化、导出、诊断复制和后端公共 JSON/错误/Provider metadata 均接入脱敏；覆盖 OpenAI、Anthropic、Gemini、xAI、GitHub、Hugging Face、Replicate 等 Key 格式，未保存明文。RC-181 已完成：配置支持 `env:`/`keychain:` 引用和直接 `RABBIT_CODE_*` 环境覆盖，优先级为 default、user、workspace、env、session、CLI；每次 resolve 重新读取环境，API 仅返回来源与 opaque placeholder，Provider 页面显示环境变量/Keychain 来源。RC-182 已完成：OAuth 采用明确政策 allowlist，默认无获准 Provider；获准注入项使用系统浏览器回调、S256 PKCE、state/redirect 校验、loopback 端口清理、SecretStore opaque token、刷新与撤销，未获政策许可的 Provider 被阻断。RC-183 已完成：offline/local 路线可在无账户、无云同步条件下运行；新增默认关闭且独立授权的 OptionalSyncService，账户、Provider SecretStore 和本地 workspace 配置保持不同边界，前端保留 guest/local 入口。RC-184 已完成：清理预览显示删除/保留范围，单 Provider credential、配置迁移和全部本地数据清理均要求明确确认；取消无变更，进程 guard、SecretStore 引用和文件安全擦除均有边界测试，Settings 已接入预览/确认流程。 |
| RC-244 至 RC-253 本项状态补充 | RC-244/245 共享工作区与 Agent 事件恢复契约完成；RC-246/247 API 与无 API Mock 旅程完成；RC-248 离线规则降级、RC-249 草稿保护、RC-250 checkpoint/diff 冲突、RC-251 全路由 RabbitMark、RC-252 类型化中英文资源和 RC-253 R1-R6/原初 12 类追踪审计完成。真实 Provider、模型下载/硬件、原生 Tauri/Linux 和外部签署均按证据文件保留为限制。 |
| RC-244 至 RC-253 最近验证 | 后端 RC-244/245/248/250 组合 8 passed；前端 CrossSurface/Draft/i18n/Settings/Onboarding 组合 15 passed；前端 ESLint、TypeScript/Vite build、Rabbit 路由覆盖、视觉回归、`check_docs.py --run`、RC-271 文档专项 2 passed、RC traceability `--check` 通过。 |
| RC-230 至 RC-271 返修验证 | 复现并修复 Docker 共享令牌缺失、Agents 旧站导航、npm advisory 镜像失效、Vite/esbuild 漏洞、Rust PATH 和前端单包告警；后端 718 passed/9 skipped，前端 33 files/150 passed，Tauri cargo、Docker、文档、lint/build/audit 通过；真实 Provider/权重/Linux/安装包/用户研究仍按证据限制留 RC-272+ 平台矩阵。 |
| 当前里程碑 | W2：共享协议、数据模型和 Agent Core |
| RC-185 本项状态补充 | `LocalInstallCore` 已提供可重入下载、暂停/恢复、取消、SHA-256 校验、原子安装、runner 状态和结构化 JSON 事件；Python CLI、PowerShell/Shell 包装脚本与 GUI 事件映射共用同一状态字段。 |
| RC-185 最近验证 | 后端 RC-185 专项 4 passed，RC-149/RC-185 关联回归 15 passed；前端全量 21 个测试文件 98 passed；PowerShell 实测通过，Linux Shell 因当前无 sh/bash 未实测；ESLint、TypeScript/Vite build、定向 Ruff/Mypy、compileall 和 diff check 通过。 |
| RC-186 本项状态补充 | `HardwareDetector` 已生成 OS/架构、CPU、RAM、磁盘、GPU/显存/驱动、网络、代理和 Ollama/llama.cpp runner 字段；每项带 source/confidence，权限不足和不可用探针可降级，`--override-json` 支持用户纠正。 |
| RC-186 最近验证 | RC-186 专项 3 passed，RC-149/RC-185/RC-186 关联回归 18 passed；前端全量 21 个测试文件 98 passed；定向 Ruff、严格 Mypy、compileall 和 CLI JSON/非法 override 检查通过。 |
| RC-187 本项状态补充 | `LocalRunnerAdapter` 已统一 pull/load/generate/stream/stop/list/remove/health；`RunnerRegistry` 选择 Ollama 默认和 llama.cpp 替代，ADR-0014 记录许可证、安装、GPU、API、包体/维护取舍，Agent Core 不含 runner-specific command。 |
| RC-187 最近验证 | RC-187 专项 2 passed，RC-149/RC-187 关联回归 13 passed；定向 Ruff、严格 Mypy、compileall 通过，两个 runner 均完成同一内存生命周期契约。 |
| RC-188 本项状态补充 | `data/models/manifest.yml` 固定 Gemma 3 1B IT 与 Qwen2.5-Coder 1.5B Instruct 的完整来源、revision/hash、资源、上下文、模板和许可证；manifest 校验与 80% RAM/磁盘/VRAM 安全余量推荐完成，未知模型默认拒绝。 |
| RC-188 最近验证 | RC-188 专项 3 passed，RC-186/RC-187/RC-188 联合专项 8 passed；manifest CLI 输出 2 models/2 recommended，Ruff、严格 Mypy、compileall、diff check 通过。 |
| RC-189 本项状态补充 | Manifest 唯一 Qwen 条目和 GUI 条目均固定为 `Qwen/Qwen2.5-Coder-1.5B-Instruct`，family 为 `Qwen2.5-Coder`；新增完整 ID 选择器、health/generation smoke 和详情页显示。 |
| RC-189 最近验证 | RC-188/RC-189 后端回归 4 passed；前端 Qwen 专项 5 passed、全量 21 个测试文件 98 passed；ESLint、TypeScript/Vite build、定向 Ruff/Mypy、compileall 通过。 |
| RC-190 本项状态补充 | Gemma 固定为 `google/gemma-3-1b-it`，manifest 绑定 `gemma-3` template、`<end_of_turn>` EOS、model-card/template 状态和 gated license constraints；GUI 显示 Gemma 3 1B IT 和完整源 ID。 |
| RC-190 最近验证 | RC-186 至 RC-190 backend 联合专项 10 passed；Gemma 固定 ID/family/template/EOS/license/health/generation smoke 和前端全量 98 passed，ESLint、TypeScript/Vite build、Ruff/Mypy、compileall 通过。 |
| RC-191 本项状态补充 | `LocalInstallCore` 增加版本/镜像/代理元数据、指数退避、失败恢复、错误哈希 fail-closed、`.part` 续传和同安装根目录进程内并发写保护；CLI 继续复用结构化状态。 |
| RC-191 最近验证 | RC-185/RC-191 专项 8 passed；RC-149 至 RC-192 相关后端回归 172 passed、2 skipped；定向 Ruff、严格 Mypy、compileall 和分发 denylist 通过。真实 HTTP/镜像/代理和 Linux 实机未执行。 |
| RC-192 本项状态补充 | manifest 明确 `bundled/ondemand/manual` 分发策略；当前 Gemma/Qwen 为 `ondemand`，下载前提供许可证摘要、HTTPS 原文 URL 和确认版本，确认元数据写入安装状态；权重 denylist 接入 `workspace.py check`。 |
| RC-192 最近验证 | RC-192 专项 3 passed；RC-188/RC-191/RC-192 联合专项 14 passed；仓库权重扫描、Ruff、严格 Mypy、compileall 和追踪门禁通过。未生成真实安装包/SBOM，实际打包产物审计留给发布流水线。 |
| RC-193 本项状态补充 | 新增安装后健康检查报告，覆盖 runner 版本、加载、最小生成、流式增量、取消、上下文、停止后重载和资源峰值；声明健康门控的安装只有全部检查通过才进入 `ready`，失败回滚为 `failed`。 |
| RC-193 最近验证 | RC-193 专项与 RC-185/RC-187 联合 8 passed；RC-149 至 RC-193 相关后端回归 190 passed、2 skipped、50 warnings；定向 Ruff、严格 Mypy、compileall 通过。真实 runner/权重和多平台资源实测未执行。 |
| RC-194 本项状态补充 | 新增本地模型生命周期状态机，固定 `not_installed/downloading/verifying/loading/ready/busy/stopping/unloaded/corrupt/update/failed` 状态、合法转换和恢复动作；安装核心事件扩展为 GUI 可消费的生命周期事件，FastAPI 持久化事件端点原子保存状态，GUI 消费后端事件并在失败/损坏状态显示 retry/repair/uninstall。 |
| RC-194 最近验证 | RC-194 专项 7 passed；RC-185/RC-191/RC-194 关联后端 16 passed、2 warnings；前端本地模型专项 6 passed，ESLint、TypeScript/Vite build、定向 Ruff、OpenAPI 生成 drift 通过。真实 Ollama/llama.cpp 进程和模型权重未执行，保留既有路径迁移 warning。 |
| RC-195 本项状态补充 | 新增全局默认本地模型和按 `workspace/session` 隔离的会话覆盖；Gemma/Qwen 选择前检查生命周期 ready/busy 与各自上下文长度，生成中禁用切换并要求先取消；优化、流式和后台请求继续使用最终 provider/model，历史 metadata 保留实际模型 ID。 |
| RC-195 最近验证 | RC-195 后端选择/历史专项 1 passed，RC-148/RC-172 关联 10 passed、8 warnings；前端会话选择专项 3 passed，App/Workspace/Task/LocalModels 关联 28 passed，ESLint、TypeScript/Vite build 通过。warnings 为既有路径迁移和 jsdom navigation。 |
| RC-196 本项状态补充 | 新增 `RunnerResourceConfig` 和硬件安全默认；runner adapter 接收 threads/GPU layers/context/concurrency/idle timeout，OOM 会先卸载、降低配置一次并交给现有离线 fallback，idle timeout 可释放已加载模型。 |
| RC-196 最近验证 | RC-196 与 RC-149/RC-186/RC-187/RC-193 关联专项 21 passed、11 warnings；覆盖 CPU-only、GPU 安全默认、配置注入、OOM 单次恢复、idle unload、runner health 和既有本地 Provider；定向 Ruff、严格 Mypy 通过。真实 GPU/runner 进程未执行。 |
| RC-197 本项状态补充 | 新增 `ModelDirectoryService` 和登记文件 registry；目录选择检查写权限/空间，更新采用复制后 SHA-256 校验再激活并保留版本；迁移使用 staging、逐文件校验、registry 切换和登记文件清理，失败时保留原目录；支持回滚、源文件修复、完整版本兜底修复、旧版本清理和仅删除登记文件的卸载；FastAPI/OpenAPI 与 GUI 目录控件已接入。 |
| RC-197 最近验证 | RC-197 专项 6 passed；RC-185/RC-191/RC-193/RC-194/RC-195/RC-196/RC-197 关联后端 28 passed、5 warnings；前端全量 22 个测试文件 102 passed；Ruff、严格 Mypy、ESLint、TypeScript/Vite build、OpenAPI drift、`workspace.py check` 通过。完整 `workspace.py verify` 被既有 `backend/tests/test_rc153_system_prompt.py:1` Ruff `I001` import 排序阻断，该前序文件未在本项修改；真实 Ollama/llama.cpp、模型权重、GPU 和跨进程故障注入未执行；既有路径迁移与 jsdom navigation warning 保留。 |
| RC-198 本项状态补充 | 新增 `LocalRunnerGateway`，将 Ollama/llama.cpp 的 list/capabilities/health/generate/stream/cancel/load/unload 统一暴露给 FastAPI；request ID 绑定取消事件，stream 输出 started/delta/completed/cancelled/error，bounded concurrency 提供并发队列/拒绝，health 使用 TTL 缓存，runner 异常统一为结构化恢复错误；API 不拼接 runner-specific 命令。 |
| RC-198 最近验证 | RC-198 专项 5 passed；RC-187/RC-193/RC-196/RC-198 关联 12 passed、6 warnings，扩展关联 38 passed、1 skipped、17 warnings；前端全量 22 个测试文件 102 passed；Ruff、严格 Mypy、compileall、ESLint、TypeScript/Vite build、OpenAPI drift 通过。真实 Ollama/llama.cpp、runner HTTP、权重、GPU 和跨进程故障注入未执行；既有 RC-153 Ruff import 排序阻塞和 warning 保留。 |
| RC-199 本项状态补充 | 新增用户级安装路径策略：RABBIT_CODE_HOME/Windows user app data/XDG data、local-models 根和 user bin；默认 CLI 省略 `--root` 时使用用户模型根，目录创建前检查祖先写权限与写探针；不可写路径 fail-closed，提权只生成未确认的 command/reason/alternative 记录；PowerShell/POSIX 包装器不请求提权。 |
| RC-199 最近验证 | RC-199 专项 5 passed；RC-185/RC-191/RC-199 安装关联 14 passed；新策略/CLI Ruff、严格 Mypy、compileall 通过，包装器 RunAs/sudo 检查通过。未执行真实标准用户受保护系统目录安装、外部包管理器或 runner 二进制提权；发布阶段 PATH 持久化和打包留待后续。 |
| RC-200 本项状态补充 | 新增离线介质布局 `manifest.yml`、`models/<safe-id>.<quantization>` 和 `dependencies/`；导入前校验受控 manifest、模型 ID、manifest revision、许可证确认、依赖目录、磁盘空间和 SHA-256；导入复用 `LocalInstallCore` 原子安装并调用同一 `run_health_check`，CLI 输出结构化结果，网络不参与。 |
| RC-200 最近验证 | RC-200 专项 4 passed；RC-185/RC-188/RC-191/RC-192/RC-193/RC-200 关联 20 passed；manifest、分发扫描、Ruff、严格 Mypy、compileall 和 `workspace.py check` 通过。篡改模型在目标写入前拒绝；未执行真实离线虚拟机、真实 runner/权重和 GPU，CLI 使用内存 runner 与确定性资源探针。 |
| RC-201 本项状态补充 | 在既有 `PermissionPolicy` 上增加 Plan/Edit/High × files/terminal/network/git/mcp/desktop 六域 capability matrix；Plan 仅文件读取与 Git 只读审阅，Edit 增加工作区文件写和 Git 工作区写，High 开放其余能力但危险域要求单次 approval；FileTools、ShellAdapter、ProcessTools、GitTools、ToolRegistry 统一调用 capability policy。 |
| RC-201 最近验证 | RC-201 专项与 RC-070/RC-078/RC-090/RC-091/RC-092/RC-094/RC-095/RC-096/RC-097 关联 51 passed、3 skipped；定向 Ruff、严格 Mypy 通过。真实沙箱/OS 级 capability 容器和桌面/MCP 进程未执行；保持既有平台 skip。 |
| RC-202 本项状态补充 | 新增 `PermissionApprovalEngine` 和共享 `ApprovalRequest` schema；请求冻结工具、完整命令、规范化路径、工作目录、影响、授权范围、完整参数、快照和超时；`ToolRegistry` 在危险 handler 前返回审批请求，批准后只允许同快照的一次执行；GUI PermissionDialog 与 TUI 使用相同字段展示。 |
| RC-202 最近验证 | RC-202/RC-201/RC-097/RC-101 关联后端 23 passed；审批拒绝、超时、一次性消费和参数替换均无 handler 副作用；Ruff、严格 Mypy、前端 UiStates 8 passed、ESLint 和 TypeScript/Vite build 通过。真实 OS 沙箱、桌面/MCP/网络执行未进行。 |
| RC-203 本项状态补充 | 新增 `AuthorizationStore`，支持 once、session 和结构化 rule 授权；命令仅支持 exact/prefix 元组匹配，路径仅支持 exact/within 规范化路径匹配，工作目录和工具名精确匹配；支持拒绝、编辑后新审批快照、查看和立即撤销；ToolRegistry 可按 session ID 自动复用匹配授权。 |
| RC-203 最近验证 | RC-203 专项与 RC-202/RC-097 关联 15 passed；覆盖 once 不复用、会话隔离、规则不越权、拒绝无 handler 副作用、编辑重审、撤销即时生效和 Registry 会话复用；Ruff、严格 Mypy 通过。默认 GUI 仍无“全部永久允许”按钮。 |
| RC-204 本项状态补充 | 新增跨平台 `SandboxReport`/`SandboxController`；Linux 检测并生成 bubblewrap PID/mount/IPC/UTS/网络隔离规格，Windows 复用 Job Object 并明确 AppContainer/ACL 非等价，所有平台保留 workspace/symlink 边界；不可用强沙箱 fail-closed，reduced 执行要求显式审批，ProcessManager 在 spawn 前接入。 |
| RC-204 最近验证 | RC-204 与 ProcessManager 关联专项 9 passed、1 skipped；覆盖 Windows/Linux 能力模拟、bwrap 规格、路径/符号链接逃逸拒绝、强沙箱不可用拒绝和批准后的 reduced 生命周期；Ruff、严格 Mypy 通过。真实 Linux bwrap/seccomp、AppContainer/ACL 和 OS 逃逸夹具未执行。 |
| RC-205 本项状态补充 | 新增共享路径规范化、符号链接/穿越拒绝、argv/NUL 校验、Shell 风险分类、环境变量白名单和不可执行的 `UntrustedToolOutput`；ShellAdapter/ProcessManager 统一使用 argv 与环境安全边界，工具/仓库输出保留为不可信数据。 |
| RC-205 最近验证 | RC-205 与 RC-091/RC-094/RC-097/RC-201 关联回归 41 passed、4 skipped；覆盖 traversal、symlink、NUL、shell metacharacter、危险 loader/secret 环境变量和提示注入；Ruff、严格 Mypy 通过。真实恶意仓库/OS 逃逸未执行。 |
| RC-206 本项状态补充 | 新增 `SensitiveFilePolicy` 默认识别 `.env`、SSH/key、云配置、浏览器资料和系统目录，支持用户 filename/path-prefix 规则；敏感 read/send 分开审批，FileTools 默认不 list/search 敏感项；`SecretScanner` 在输出前提供 metadata-only findings 并阻断含秘密输出。 |
| RC-206 最近验证 | RC-206 与 RC-090 关联 7 passed、1 skipped；覆盖默认敏感路径、用户规则、默认索引排除、独立 read/send approval、private/API key scanner 和权限模式独立性；Ruff、严格 Mypy 通过。真实凭据/浏览器资料/Provider send 未执行。 |
| RC-207 本项状态补充 | strict App Server boundary 仅允许 loopback client/Host，限制 local Origin、显式 CORS methods/headers、per-startup high-entropy token、protocol 和 Content-Length body 上限；sidecar host 强制 loopback 并启用 strict mode，health 仍为本地探针公开。 |
| RC-207 最近验证 | RC-207 与 RC-058/RC-067 关联 11 passed、24 既有路径迁移 warnings；覆盖高熵 token、bad Host/Origin/token、oversized body、protocol 和 sidecar restart 新端口/新 token；Ruff、严格 Mypy 通过。未执行真实端口扫描/外部暴露。 |
| RC-208 本项状态补充 | 新增统一 `TrustManifest`/`TrustRegistry`，覆盖 plugin、skill、hook、mcp、script 的来源、版本、SHA-256 和权限声明；安装/注册要求显式确认，来源或权限变化要求重新确认；锁定、禁用、撤销和隔离执行上下文已接入，插件运行前再次校验 artifact hash。 |
| RC-208 最近验证 | RC-208 与 RC-077/RC-099/RC-075/RC-076 关联 25 passed；覆盖首次确认、来源/权限拒绝、变更重审、锁定升级、禁用/撤销、插件运行时篡改和隔离上下文；Ruff、严格 Mypy、compileall 通过。未执行真实第三方扩展进程、凭据访问或 OS 级沙箱，依赖 RC-204 与后续安全矩阵。 |
| RC-209 本项状态补充 | 新增共享版本化 `ArtifactManifest`/`ArtifactDownloader`，覆盖 binary、model、update、plugin；强制 HTTPS 来源和许可证 URL、许可证版本确认、SHA-256 校验；下载写入随机 `.part` 临时文件，验证通过后才原子替换，失败清理临时文件且保留既有目标。模型 `ModelSpec` 复用同一 manifest 政策。 |
| RC-209 最近验证 | RC-209 与 RC-188/RC-191/RC-192/RC-200/RC-077 关联 28 passed；覆盖四类制品成功安装、manifest round-trip、错哈希、HTTPS 源不可用、许可证缺失/未确认、临时文件清理和旧版本保留；Ruff、严格 Mypy、compileall 通过。未执行真实外部 HTTP 下载，使用受控 fetcher 验证失败边界。 |
| RC-210 本项状态补充 | 新增默认关闭的 `TelemetryService`，首次明确 opt-in 后才记录技术 metadata，内容字段仍需单独选择；支持撤回和清除。新增 `DiagnosticBundleService`，诊断预览仅展示脱敏 metadata/文件大小，导出和发送均要求显式确认；GUI 改为先预览再复制并支持清除，拒绝动作不触发 sender。 |
| RC-210 最近验证 | RC-210 后端与 RC-093/RC-180 关联 9 passed，前端 Diagnostics 4 passed；Ruff、严格 Mypy、compileall、ESLint、TypeScript/Vite build 通过。覆盖默认无遥测、opt-in、内容默认丢弃、撤回/清除、secret/提示词/源码脱敏、预览、拒绝发送和清除预览。未执行真实网络发送。 |
| RC-211 本项状态补充 | 已建立数据流与 STRIDE 威胁模型、私密漏洞报告/SLA/密钥轮换政策、仓库秘密扫描、Dockerfile 安全规则、确定性 CycloneDX SBOM 及漂移检查；CI 接入 Ruff/Mypy、`pip-audit` 和生产依赖 `npm audit` 门禁。 |
| RC-211 最近验证 | `scripts/security_scan.py --check` 通过；RC-211 专项 3 passed；Ruff、严格 Mypy、compileall 通过。当前环境没有 `pip-audit`、`syft`、`trivy`、`grype` 或 `gitleaks` 命令，真实漏洞数据库/容器镜像 CVE 扫描留给 CI，并已在威胁模型中记录，未伪造本地通过。 |
| RC-212 本项状态补充 | 新增独立 SQLite `AuditLogService`，只接受 permission/tool/config/external request 四类最小元数据；事件包含 UTC 时间、主体、结果、会话/请求/工具/任务标识和前序哈希，敏感/未白名单字段丢弃；保留期设置持久化，支持过期、按会话和全量清理。 |
| RC-212 最近验证 | RC-212 专项 5 passed；RC-211/RC-212 联合 8 passed；Ruff、严格 Mypy、compileall、security baseline 和 traceability check 通过。覆盖跨实例持久化、敏感字段不落库、哈希篡改检测、删除后链重建、保留期清理和确认门禁。 |
| RC-213 本项状态补充 | 建立 docs/data-model/schema-v1.json 唯一规范，覆盖 workspace、session、message、content block、tool call、file snapshot、prompt version、Provider reference、model manifest 和 setting；字段包含 ID、作用域、时间、删除和版本关系。生成 Mermaid ER 图、SQL 迁移初稿、Pydantic 模型和 TypeScript 接口。 |
| RC-213 最近验证 | RC-213 专项 2 passed；迁移 SQL 在临时 SQLite 执行成功，生成物 drift check、Ruff、严格 Mypy、workspace.py check、TypeScript/Vite build 通过。当前 StorageService 的旧 schema v1 启动建表未切换，正式迁移执行、事务和恢复留给 RC-214。 |
| RC-214 本项状态补充 | SQLite 版本 2 runner 使用 BEGIN IMMEDIATE 取得迁移写锁，启动前执行 integrity check；StorageService 统一 WAL/busy timeout/foreign key/synchronous 设置，补齐关键索引，save_version/create_user 的复合写进入单事务；备份/恢复继续复用并验证完整性。 |
| RC-214 最近验证 | RC-214 专项与存储/备份回归 17 passed；迁移失败回滚、并发迁移、版本/索引/WAL、复合写回滚、损坏库拒绝、备份/恢复均通过；RC-211 至 RC-214 定向 Ruff、严格 Mypy、compileall、生成 drift 和 workspace check 通过。最终后端全量 646 passed、9 skipped、2 warnings；前端 23 文件 109 passed。 |
| RC-215 本项状态补充 | 新增 v1 JSON 日志 schema、Pydantic StructuredLogEvent、StructuredLogEmitter 和字段级 allowlist redactor；事件固定 request/session/tool/task correlation ID，默认丢弃 prompt、源码、路径、密钥、token、content、raw input/output 和未知字段；schema/redaction 校验进入 CI 与 workspace 门禁。 |
| RC-215 最近验证 | RC-215 专项 3 passed；结构化日志门禁、RC-211 security baseline、Ruff、严格 Mypy、traceability 和 workspace check 通过。覆盖 schema extra 拒绝、字段丢弃、秘密/正文不落日志、correlation ID、JSON round-trip 和长度边界。 |
| RC-216 本项状态补充 | 新增 `ExecutionDestination` 模型和 `POST /api/v1/execution-destination`；优化请求 metadata 包含 `execution_location`、目标服务/主机和隐私说明，Provider cloud target 从配置提取；Composer 请求前展示 local/cloud 目标，offline/local/cloud 三条路径均使用同一目标模型。 |
| RC-216 最近验证 | RC-216 专项 2 passed；API/相关回归 25 passed；前端 22 个测试文件 104 passed，ESLint、TypeScript 和 Vite build 通过；OpenAPI/client/schema 生成物与 workspace 检查通过。未发送真实 Provider 请求。 |
| RC-217 本项状态补充 | Provider Preset 增加 `rc217-v1` 隐私元数据：发送字段、服务区域、官方政策 URL 和未知保留风险；新增公开 `GET /api/v1/provider-privacy` 目录。Provider 配置/首次使用页显示版本化 local/cloud 标识、发送字段、区域、风险和官方链接；自定义端点明确标为用户负责。 |
| RC-217 最近验证 | RC-217 后端专项 2 passed；RC-166/RC-216/API contract/API 相关回归共 49 passed；前端 22 个测试文件 105 passed，ESLint、严格 Mypy、Vite build、OpenAPI drift、traceability 和 workspace check 通过。11 个官方政策链接结构与域名门禁通过，HTTP spot check 返回 200；未发送真实 Provider 请求。 |
| RC-218 本项状态补充 | 新增默认 retention policy：日志级别 info、日志单文件/总量 5/50 MB、缓存 100 MB、会话终态 30 天、Prompt history 365 天/500 条；RetentionService 提供预览、日志超限轮转、最旧优先回收、终态任务/历史批量清理和进程 guard，Settings 接入 retention 预览/确认。配置、模型、附件、数据库和 queued/running 任务保留。 |
| RC-218 最近验证 | RC-218 专项 4 passed；API contract/API、存储备份、RC-184 清理和 RC-218 相关后端回归 32 passed；前端 22 个测试文件 106 passed，ESLint、Ruff、严格 Mypy、Vite build、OpenAPI drift、traceability 和 workspace check 通过。既有 jsdom navigation 与路径迁移 DeprecationWarning 如实保留。 |
| RC-219 本项状态补充 | 新增 `rc219-v1` 本地指标聚合器与 `GET /api/v1/metrics` 报告；请求总延迟/成功失败/Provider usage、流式首 Token、工具成功率、模型加载耗时和 CPU/RAM/GPU 资源样本均有固定单位和无内容边界。技术标签拒绝 secret/token/password 等敏感词，不提供外传端点。 |
| RC-219 最近验证 | RC-219 固定负载专项 4 passed；Provider/RC-216 相关回归 20 passed、1 skipped；前端最终 23 个测试文件 109 passed，ESLint、严格 Mypy、Ruff、Vite build、metrics boundary、OpenAPI drift、traceability 和 workspace check 通过。最终后端全量 646 passed、9 skipped、2 warnings。 |
| RC-220 本项状态补充 | `TelemetryService` 继续默认关闭，opt-in 固定记录 `rc220-v1` consent 版本；事件只保留匿名技术字段并带 consent 版本，撤回立即阻断新记录/发送，clear 删除待发送队列；Settings 隐私区展示字段、版本、关闭和删除待发送数据动作，不依赖遥测服务器或账户。 |
| RC-220 最近验证 | RC-210/RC-220 后端专项 8 passed；前端全量 22 个测试文件 107 passed，RC-220 Settings 7 passed；Ruff、严格 Mypy、ESLint、Vite build 通过。默认无事件、撤回阻断、清除删除、版本记录和本地字段边界均有测试；保留既有 jsdom navigation warning。 |
| RC-221 本项状态补充 | 新增 `rc221-v1` 可移植文档，JSON 为规范格式，ZIP 仅含带 SHA-256 的 `manifest.json`/`data.json`；包含会话/消息、Prompt、模板和 allowlist 非敏感设置，默认排除 Provider 凭据和未知设置；导入先做 schema、大小、重复 ID、敏感字段、路径、符号链接和哈希校验，再提供 `skip`/`replace` 冲突预览。 |
| RC-221 最近验证 | RC-221 专项与 RC-086/RC-089/存储导出回归 16 passed；编译、Ruff、严格 Mypy 通过。当前全量后端回归已通过，RC-221 未新增失败。 |
| RC-222 本项状态补充 | 新增 `rc222-v1` 固定离线性能基线脚本和 JSON 报告，覆盖真实 CLI 首响应、离线首 Token、搜索、diff、前端 dist 包体、GUI HTTP 冷/热启动、RSS 和本地 wheel，并固定 p50/p95、硬件和阈值。 |
| RC-222 最近验证 | RC-271 迁移后的 25 次基线通过：CLI 首响应 p50/p95 562.487/917.953 ms，离线首 Token 0.159/0.192 ms，搜索 0.027/0.032 ms，diff 0.015/0.020 ms，前端 dist 829,010 bytes，GUI 冷/热启动 p95 1,794.780/23.926 ms，RSS 64,110,592 bytes，backend wheel 290,458 bytes，全部在原绝对预算内；旧值和迁移原因保留在性能文档。 |
| RC-223 本项状态补充 | `SafeSearchIndexer` 保持既有 ignore、敏感路径、二进制/大小过滤和 mtime/size/hash cache；新增 `start_background_scan()`、可等待/取消 `BackgroundScan`、Queue `maxsize` 有界生产者/消费者和后台增量路径处理，UI 可先返回。 |
| RC-223 最近验证 | RC-083/RC-223 搜索专项 4 passed、1 skipped；Ruff、`mypy --follow-imports skip`、compileall 通过。覆盖后台过滤/缓存复用、队列大小校验、预取消阻断和既有 symlink 平台 skip；未执行真实百万文件仓库或跨进程索引压力。 |
| RC-224 本项状态补充 | 新增共享 `DataLimitDefaults` 与最大值校验，统一工具输出、上下文、日志、Diff 和附件边界；文本/工具/日志/Diff 协议返回 `truncated`、`original_bytes` 与 `next_cursor`，进程日志和 Diff 支持游标续读，附件超限直接拒绝。 |
| RC-224 最近验证 | RC-224 与 RC-082/RC-096/存储导出回归 14 passed；定向 Ruff、严格 Mypy、OpenAPI 生成 drift 和 `workspace.py check`（刷新追踪索引后）通过；RC-222 性能预算现已通过。 |
| RC-225 本项状态补充 | App Server 启动会对账 SQLite 中 queued/running 任务并标为保留输入的可重试失败；本地模型读取会按安装文件恢复异常瞬态；ProcessManager 新增原子 JSON 进程登记，重启后保留日志并将旧运行项标为失败。 |
| RC-225 最近验证 | RC-225 恢复专项与 RC-094/RC-194/RC-198/API 回归 41 passed；定向 Ruff、严格 Mypy 通过。FastAPI/本地迁移既有 warnings 保留；桌面壳制品、真实 runner 进程和跨平台 kill 矩阵不可用。 |
| RC-226 本项状态补充 | 普通优化以 `X-Request-ID` 登记取消事件，新增版本化取消 API；GUI AbortSignal 在取消时调用 App Server 取消端点；Provider、离线规则、LocalRunner、Shell/Process 继续检查/终止取消状态，取消不会写入 Prompt history。 |
| RC-226 最近验证 | RC-226/RC-147/RC-152/RC-096/RC-198 后端 20 passed；前端 PromptOptimizeButton 7 passed，ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、严格 Mypy 通过。未执行真实云 Provider、桌面原生工具进程和跨平台强制终止矩阵。 |
| RC-227 本项状态补充 | 为限流、断网、代理失败、模型 OOM、磁盘满、SQLite 锁和端口冲突补齐有限重试边界、熔断/恢复动作与诊断错误契约；Provider 代理失败独立编码，模型目录与 SQLite 在不可恢复前保留输入/原状态，端口冲突要求选择其他端口。 |
| RC-227 最近验证 | RC-227 故障矩阵、RC-197、RC-151、RC-171、RC-225 和 SQLite 备份回归共 32 passed；目标 Ruff、Provider/SQLite/Storage 严格 Mypy、`git diff --check` 通过。真实云故障、企业代理、物理磁盘耗尽、跨进程崩溃和桌面原生端口矩阵未执行。工作区 Mypy 已按显式包根拆分检查，不再存在模块映射阻断。 |
| RC-228 本项状态补充 | Gateway 根据硬件报告生成保守线程/GPU 层/上下文/并发配置并传给 runner；队列暴露 active/pending/capacity，空闲时可通过 API 调低资源，运行中拒绝变更；健康信号携带可选温度并提供 OOM/过热节流提示。 |
| RC-228 最近验证 | RC-228 与 RC-196/RC-198/RC-193/RC-194/RC-227/RC-151/RC-171/RC-225/API contract 联合回归 52 passed；目标 Ruff、runner 资源/Provider/Gateway 严格 Mypy、OpenAPI 生成和契约通过。真实 Ollama/llama.cpp、GPU 温度、热降频和跨平台压力矩阵未执行。 |
| RC-229 本项状态补充 | 在既有离线基线脚本上新增 `benchmarks/performance_gate.py` 趋势比较器；只比较两次均实测的指标，按显式噪声比例/绝对值放行小波动，保留 blocked probe，输出 Commit/硬件和 min/p50/p95/max 统计区间，并在 CI 上传 current/comparison artifact。 |
| RC-229 最近验证 | RC-229 回归注入 3 passed，目标 Ruff、比较器严格 Mypy、OpenAPI/traceability 相关门禁通过；25 次真实 current 报告含 Commit/机器/硬件元数据，9 项绝对预算通过；同一 HEAD 下旧脏工作树不可比的问题已记录并迁移到 RC-271 基线，趋势自比较无回归、gate exit 0。 |
| RC-230 本项状态补充 | 新增离线 Agent Core 专项测试，覆盖状态转换/非法终态、ToolRegistry 调用循环构件、取消、幂等重试与回放、预算原子性、上下文压缩来源和 JSON 检查点恢复/篡改拒绝。 |
| RC-230 最近验证 | `python -m pytest backend/tests/test_rc230_agent_core.py -q` 8 passed；`.venv\Scripts\ruff.exe check backend/tests/test_rc230_agent_core.py` 通过；未调用真实 Provider、runner、网络或外部工具。 |
| RC-231 本项状态补充 | 新增共享 Mock Provider 契约，覆盖 OpenAI Chat、Responses、Gemini、Anthropic Messages 和 OpenAI-compatible OpenRouter；请求 payload、工具调用、流式事件、未知字段和错误映射统一验证。 |
| RC-231 最近验证 | `python -m pytest backend/tests/test_rc231_provider_contracts.py -q` 15 passed；`.venv\Scripts\ruff.exe check backend/tests/test_rc231_provider_contracts.py` 通过；所有用例使用 `httpx.MockTransport`，无外部网络。 |
| RC-232 本项状态补充 | FastAPI 测试覆盖严格 startup token/loopback Origin/body 上限、SSE 重放、WebSocket 事件与错误、离线 fallback、后台任务鉴权和本地 runner 路由；新增 `/api/v1/optimize/ws` 共用优化事件语义。 |
| RC-232 最近验证 | `python -m pytest backend/tests/test_rc232_fastapi.py -q` 8 passed；`.venv\Scripts\ruff.exe check backend/src/prompt_optimizer/api/app.py backend/tests/test_rc232_fastapi.py` 通过；仅保留既有数据目录迁移 DeprecationWarning。 |
| RC-233 本项状态补充 | 新增 CLI 专项测试，覆盖 text/JSON/JSONL、TTY/非 TTY、非交互权限策略、稳定 runtime/permission/cancel 退出码、continue/resume、dry-run、终端能力矩阵和真实 Python subprocess 无污染输出。 |
| RC-233 最近验证 | `python -m pytest backend/tests/test_rc233_cli.py -q` 11 passed；`.venv\Scripts\ruff.exe check backend/tests/test_rc233_cli.py` 通过；Linux shell 与原生交互终端按当前 Windows 能力如实报告。 |
| RC-234 本项状态补充 | 新增 GUI 工作流组件测试与真实浏览器 smoke，覆盖 onboarding 双入口、Provider/模型/Review/Settings 路由、优化、diff、采用、再次发送；修复已采用 Prompt 含输出格式结构时离线优化重复追加导致的结构拒绝，并显式传递内部 protected structure，保留用户 marker 拒绝。 |
| RC-234 最近验证 | `python -m pytest backend/tests/test_rc234_gui_send.py -q` 1 passed；结构/评测/RC-234 联合 11 passed；前端 `Rc234Workflow` 2 passed、ESLint、Vite build 和目标 Ruff 通过；Playwright 真实发送后状态为“优化完成”，截图 `output/playwright/rc234-send-after-adopt.png`；完整后端回归首轮 702 passed、9 skipped、2 warnings，剩余 traceability 索引已在本项记录后重生成。 |
| RC-235 本项状态补充 | 新增视觉回归矩阵门禁，校验 14 路由 × light/dark × 1x/2x 的有效 PNG 基线、工作流截图、路由内容、主题显式设置、Rabbit 装饰层和 shared empty/error/offline/install 状态契约。 |
| RC-235 最近验证 | `python scripts/check_rc235_visual_regression.py` 通过；`npm test -- --run tests/Rc235VisualRegression.test.tsx` 17 passed；前端 ESLint、脚本 Ruff 通过。既有 `rc-133-*` 基线由固定数据/字体矩阵复用，未批准像素差仍由既有 visual baseline 流程阻断。 |
| RC-236 本项状态补充 | 引入 axe-core 组件扫描，覆盖 workspace/settings shell；补充 PermissionDialog 的 modal/description/键盘焦点断言，并以静态门禁确认 focus-visible、reduced-motion 和 forced-colors 样式。 |
| RC-236 最近验证 | `npm test -- --run tests/Rc236Accessibility.test.tsx` 2 passed；axe 无 critical/serious findings；`python scripts/check_rc236_accessibility.py`、ESLint、脚本 Ruff 通过。Windows 键盘焦点结果记录在证据文件，屏幕阅读器实机仍需发布平台复核。 |
| RC-237 本项状态补充 | 新增 Fake Runner 本地模型组合回归，固定 manifest 中 Gemma/Qwen 两个模型族，使用临时小权重覆盖断点续传、暂停恢复、校验、健康、生成、运行、损坏修复和卸载历史保留；不下载或提交大权重。 |
| RC-237 最近验证 | `python -m pytest backend/tests/test_rc237_local_models.py backend/tests/test_rc185_local_install.py backend/tests/test_rc189_qwen_model.py backend/tests/test_rc190_gemma_model.py backend/tests/test_rc193_health.py backend/tests/test_rc196_runner_resources.py backend/tests/test_rc197_model_lifecycle.py -q` 21 passed；RC-237 专项 4 passed；目标 Ruff 通过。真实 CPU/GPU、低内存硬件和外部 runner 由受控平台矩阵保留。 |
| RC-238 本项状态补充 | 新增安装契约脚本和后端 smoke，校验 Docker clean build 使用 lockfile、非 root runtime、前端 dist、桌面 bundle policy 与 SHA-256；运行 frontend production build。 |
| RC-238 最近验证 | `python scripts/check_rc238_installation.py` 通过；`python -m pytest backend/tests/test_rc238_installation.py -q` 2 passed；Vite build 通过（保留既有 500 kB chunk warning）；Ruff 通过。Windows/Linux clean VM、真实安装升级降级卸载和原生 cargo check 未执行：当前主机无 `cargo`，且 Tauri bundle.active=false。 |
| RC-239 本项状态补充 | 新增离线威胁矩阵，覆盖命令注入分类、工作区路径逃逸、危险环境变量、制品目标逃逸和未批准 trust permission；联接既有 secret scan、loopback、portable、plugin/MCP trust、artifact hash 和 provider privacy 门禁。 |
| RC-239 最近验证 | RC-239 聚合专项 5 passed；联合安全/loopback/trust/artifact/portable 回归 25 passed；`python scripts/security_scan.py --check` 通过；UTF-8 环境 `.venv\Scripts\pip-audit.exe` 报告 `No known vulnerabilities found`。真实渗透、恶意仓库和外部供应链网络流量未执行。 |
| RC-240 本项状态补充 | 新增固定评测质量 gate 和 JSON 报告，按 Provider/model 分组计算 analyzer 前后分数、SequenceMatcher 相似度/原文锚点、结构签名和语言保持；代码块、变量、附件、命令等受保护结构要求签名不变。 |
| RC-240 最近验证 | `python scripts/check_rc240_quality.py --check` 通过；`python -m pytest backend/tests/test_rc240_quality_gate.py -q` 1 passed；60/60 样本通过，offline/rules 平均 score delta 72.8；目标 Ruff 通过。真实云 Provider/人工双盲评审未伪造，固定数据的 blind-review 协议仍记录在报告。 |
| RC-241 本项状态补充 | 将 `RABBIT_CODE_REAL_PROVIDER_TESTS=0` 提升到 backend CI job 默认环境；新增 CI policy gate、Mock 合约回归和真实 Provider/model 手动矩阵说明，普通 PR 不使用项目付费 Key 或真实权重。 |
| RC-241 最近验证 | `python scripts/check_rc241_ci_mock.py`、CI YAML 解析通过；`python -m pytest backend/tests/test_rc241_ci_mock.py backend/tests/test_rc231_provider_contracts.py -q` 16 passed；目标 Ruff 通过。 |
| RC-242 本项状态补充 | backend/frontend workflow 均加入 Ubuntu/Windows fail-fast=false 矩阵；保留追踪、生成、依赖、安全、license、compile、Ruff、Mypy、Pytest/Mock、frontend npm ci/lint/test/build/audit 门禁。新增静态矩阵校验。 |
| RC-242 最近验证 | `python scripts/check_rc242_ci_matrix.py`、`python -m compileall -q backend/src`、matrix test 1 passed、Ruff 通过；本地 Vite 进程锁定 esbuild 时 `npm ci` 失败，未终止服务；hosted Windows/Linux 运行结果留 CI。 |
| RC-243 本项状态补充 | 新增版本化覆盖率策略、JSON 报告和 CI 门禁；总体覆盖率与变更关键文件分别设定阈值，并显式维护权限、密钥、安装、迁移、取消、恢复和 mutation/fault 测试清单。 |
| RC-243 最近验证 | 最终全量 backend 回归 718 passed、9 skipped、2 warnings；覆盖率 85.99%，RC-243 策略测试 1 passed，覆盖率门禁、traceability 4 passed 和目标 Ruff 均通过。 |
| RC-254 本项状态补充 | 新增低保真信息架构与主旅程评审稿，冻结首页 API/本地双入口、工作区 Composer、菱形星星优化与发送边界、错误返回和结果预览线框；代码静态评审与现有路由映射通过。 |
| RC-254 最近验证 | `docs/design/rabbit-code-ux-low-fi.md` 与 `docs/evidence/RC-254/README.md` 已保存；评审记录明确保留真实产品、设计、前后端和无障碍责任人签字作为发布前 handoff，未伪造外部签署。 |
| RC-255 本项状态补充 | 新增 Desktop 1440x1100、Compact 390x844 与 2x 截图规格，覆盖 light/dark、长 Provider/模型/错误文案、中英文折行、Composer 状态矩阵和 token 对齐。 |
| RC-255 最近验证 | `docs/design/rabbit-code-ux-high-fi.md` 与 `docs/evidence/RC-255/README.md` 已保存；规格已映射现有 CSS/组件，真实运行时边界留给 RC-256 验证。 |
| RC-256 本项状态补充 | Playwright 实机截图与 DOM 边界检查覆盖 workspace/Review 的 1440x1100、390x844；发现并修复 Review 三栏在紧凑视口被后置基础 CSS 覆盖的问题，修复后无横向溢出或视口外交互控件。 |
| RC-256 最近验证 | Playwright console 0 errors/0 warnings；工作区 desktop/mobile scrollWidth 分别为 1440/390；Review mobile 三栏均 `right=390`，desktop 三栏 `right=1440`；截图保存在 `output/playwright/rc256/`。 |
| RC-257 本项状态补充 | 修复空输入把占位文案当作真实优化输入的问题；星星与发送保持独立主次，优化请求使用单活动锁、取消、revision 快照和结果预览，不自动覆盖当前输入。 |
| RC-257 最近验证 | 前端 App/PromptOptimizeButton 24 passed；`npm run lint`、`npm run build` 通过；Playwright 空状态星星/发送均 disabled，星星 42x42、发送 93x48，console 0 errors/0 warnings。 |
| RC-258 本项状态补充 | 逐页验证 Task/Review/Terminal/Provider/Models/Assets/Settings/Diagnostics 的 Rabbit 装饰槽；修复 Task 移动端三栏后置基础 CSS 导致菜单、Inspector 和 Context tab 出界的问题，slot 保持 aria-hidden、pointer-events none 和低透明度。 |
| RC-258 最近验证 | RabbitRoutes/TaskWorkspace/ChangeReview 15 passed；Playwright 390x844 dense-work matrix 无视口外控件，mark 32px/0.16、terminal mono 32px/0.12，console 0 errors/0 warnings；并保留空输入回归修正后的 LocalModelSelection/PromptHistory 定向 5/5 记录。 |
| RC-259 本项状态补充 | 动效仅用于滚动进入、状态变化和空间转换；无 `.reveal-on-scroll` 的工作页不初始化 Lenis/RAF，`prefers-reduced-motion` 跳过初始化，后台标签页停止 RAF，恢复可见后按需重启。 |
| RC-259 最近验证 | SiteShellMotion 3 passed（含 hidden/visible 生命周期）；RC-259 聚焦组合 29 passed，ESLint、Vite build 通过；CSS reduced-motion 快照关闭装饰动效。当前环境未提供长时 CPU/GPU profiler，已保留为平台发布检查。 |
| RC-260 本项状态补充 | 以无教程代理走查和自动化 UI 旅程验证双入口、API 四步配置、本地六步安装/健康检查和星星优化/发送分离；API key 边界、保存前 Mock/$0 检查和本地无远程 Provider 文案清晰。 |
| RC-260 最近验证 | `Rc260Usability.test.tsx` 4 passed；Playwright `rc260` 保存 onboarding/local-install/local-ready 截图，健康 mock 后 console 0 errors/0 warnings。未有真实目标用户、真实 App Server、Provider 请求或模型权重下载，已写入证据限制。 |
| RC-261 本项状态补充 | 修复设置页已声明但未实现的 `Ctrl+K` 命令面板；新会话同时清理消息和 Composer 草稿；默认/Vim 优化快捷键、结果焦点恢复、diff 原文/接受/验证路径纳入高频效率回归。 |
| RC-261 最近验证 | `Rc261Efficiency.test.tsx` 4 passed；RC-259/260/261 与 App/Task/Review 组合 34 passed；ESLint、Vite build 通过；Playwright 命令面板截图和 console 0 errors 记录完成。真实高频用户操作数/时间基线、Tauri 多窗口和屏幕阅读器矩阵留外部 UX/平台验收。 |
| 当前状态 | RC-126 已建立结构化 14 路由 coverage manifest、生成的 Markdown 矩阵和 `workspace.py check` 门禁；RC-127 已建立 PNG/WebP/应用图标预算、裁切焦点、清晰度、母版保护和导出流程，并记录只读基线；RC-128 已将 mark/mono 改为独立 SVG；RC-129 已建立四级内容优先级和工作页装饰门禁；RC-130 已建立 JSON token 源、生成的 CSS/TypeScript/主题快照、前端 raw color scan 和 workspace 漂移门禁；RC-131 已统一 Lucide 工具图标、Sparkles 优化语义、Tooltip/可访问名称并建立图标语言门禁；RC-132 已完成 WCAG 2.2 AA 目标的 axe/键盘/焦点/对比度/reduced-motion/200% 等效检查；RC-133 已完成 14 条独立路由 × 4 组深浅主题/1x/2x 截图基线、兔兔存在性、边界和主题断言，并接入 `workspace.py check`；RC-134 已评审三种星星按钮布局，锁定“上下文左、动作右”的桌面/小窗规则和键盘点击顺序；RC-135 已建立请求 ID 驱动的八状态优化按钮、取消和过期结果保护，并接入现有优化入口；RC-136 已为优化按钮建立延迟 Tooltip、`aria-label="优化输入内容"`、键盘焦点提示和独立 action 语义；RC-137 已为请求建立文本/revision/光标/附件快照、空输入与附件边界、12000 字符预算拒绝和原文不截断约束；RC-138 已实现 AbortSignal 取消传播、revision 变化检测、待比较状态和当前输入安全的重新优化入口；RC-139 已将优化结果与发送动作分离，提供可编辑预览、采用和保留原文，未自动调用任务发送；RC-140 已实现 inline/side-by-side 逐行 diff、长文本可视窗口、可编辑预览、复制、整段/选区替换、撤销、恢复原文和重试；RC-141 已实现 Provider/模型/local-cloud/fallback/耗时/错误码 metadata、密钥引用和错误脱敏；RC-142 已实现代码围栏、文件提及、附件 token、命令、`{{variable}}` 和输出格式保护，结果校验失败时不自动采用并显示可恢复错误；RC-143 已实现中文/英文/混合语言检测、保持指令、脚本异常拒绝和显式翻译例外；RC-144 已在 Composer Popover 接入模板、场景、角色、优化强度、评分、历史和版本比较，控制状态绑定草稿且高级区默认收起；RC-145 已实现 default/vim 可配置快捷键、结果层焦点恢复、单一阶段 live region 和 44px 工作流触控目标；RC-146 已实现优化版本持久化、Provider/模型/时间戳记录、保存开关、采用状态、历史删除及前端三路请求接线；RC-147 已建立唯一 `PromptOptimizationService.optimize/stream/cancel`，统一 CLI、API、后台任务、评测和 GUI API 路由；RC-148 已实现会话 Provider/模型读取、独立优化器覆盖、可用性检查、健康回退及 selection scope/health 持久化；RC-149 已实现无网络 local Provider/runner Adapter、本地健康状态、流式 chunk 和 workspace local model 路由；RC-150 已实现 local 未安装/未就绪/OOM/超时的受控离线规则降级、结构化原因与安装/修复入口；RC-151 已实现云 Provider 显式授权、幂等 request ID 重试、限流、熔断 open/half-open/closed 和取消传播；RC-152 已实现 canonical v1 流式事件、序号、游标回放、取消和 error 终态，旧 API chunk 兼容；RC-158 已建立固定版本/种子评测协议、60 个样本、分类分布、自动评分和双人盲评批次报告；RC-159 已统一首次启动、Provider 编辑器和账户登录的凭据措辞与边界；RC-160 已建立 OpenAI Chat Completions 的标准 endpoint、头、工具和错误契约；RC-161 已建立独立 Responses Adapter、协议显式选择和 Chat/Responses 参数隔离；RC-162 已建立 Gemini 原生 endpoint、contents/parts、系统指令、工具、安全设置和错误解析；RC-163 已建立 Anthropic Messages、content blocks、tool use/result、SSE、usage、缓存和扩展能力探测；RC-164 已建立 Claude Code 格式到公开 Anthropic/官方 Agent SDK 的映射和凭据拒绝边界；RC-165 已建立 Azure、Vertex 和 Bedrock 的部署/区域/项目/认证及 endpoint 变体适配；RC-166 已建立主流 OpenAI 兼容 Provider Preset 数据源、默认 endpoint、发现路径、兼容级别、限制说明和自定义敏感头；RC-167 已建立能力 schema v1、静态能力矩阵、探测覆盖、TTL 缓存、Agent/GUI 能力门控；RC-168 已建立 Preset 模型发现、分页/缓存、失败保留手动模型和格式校验；RC-169 已建立 Mock-first 分阶段连接测试、真实请求确认/费用/token 边界和 GUI `MOCK / $0` 状态；RC-170 已建立 Provider 统一 11 类错误分类、状态码/错误体映射、脱敏 request ID、API/流式/CLI/UI 共享错误呈现和修复动作；RC-171 已建立指数退避、抖动、`Retry-After`、取消中断、代理、NO_PROXY、自定义 CA、IPv4/IPv6 和 opaque 代理凭据 resolver；按用户指令自动进入 RC-172 |
| 当前阻塞 | RC-037 访谈/产品范围评审仍待确认；RC-038 平台实测、RC-039 场景 E2E、RC-040 三表面实现对账和 RC-042 状态参数执行待后续 RC；RC-067 完整发行版安装包升级/卸载仍留发布阶段；Provider 原生 token/cost 遥测、持久预算账本、跨进程会话服务、生产回滚 UI、真实 Git worktree、数据库故障注入矩阵、Shell/进程全平台实机矩阵、远程 Git/PR 实测和完整 LSP 适配留给后续 RC；RC-107 的 Windows Terminal 交互尺寸/剪贴板与原生 Linux 实机矩阵留待交互终端或 Linux 平台条件，不伪造为已验证；既有迁移/脚本环境警告与前端 jsdom navigation 警告保留，不阻塞 RC-107 |
| 最近一次完整验证 | 2026-07-19：RC-057/060/121/122/123/127 的 Windows/Linux Tauri、标题栏窗口、素材源登记、派生输出和发布授权检查均有 PASS 证据；前端/后端/CLI 既有验证结果保持不变；既有迁移 DeprecationWarning、前端 jsdom navigation warning 和环境相关 skip 如实保留；390px Review 既有三栏响应式问题留给 RC-255/256 |
| 最近验证补充 | 2026-07-19：RC-158 专项 3 passed；RC-158 评测集 60 个样本、版本/种子、分类分布和双人盲评批次报告生成；RC-158 目标范围 Ruff、Mypy 通过。RC-159 前端专项 3 passed、ESLint 和 TypeScript 通过；根目录 Vitest 因扫描 `.runtime/pytest-rc154` 遇 EPERM，改从 `frontend` 目录运行通过。RC-160 联合 Provider 回归 20 passed、Ruff、Mypy 通过；覆盖标准 endpoint、组织/项目头、SSE、工具调用和 401/429/504 错误映射。RC-161 联合 Provider 回归 23 passed、Ruff、Mypy 通过；覆盖 Responses `instructions/input/text`、响应事件、工具调用、结构化输出和显式协议选择，Chat 参数隔离通过。RC-162 联合 Provider 回归 26 passed、Ruff、Mypy 通过；覆盖 Gemini `generateContent`/`streamGenerateContent`、contents/parts、系统指令、function calling、安全设置和 Gemini 错误结构。RC-163 联合 Provider 回归 29 passed、Ruff、Mypy 通过；覆盖 Anthropic Messages、content blocks、tool use/result、SSE、usage、版本/Beta 头、prompt caching 和 capability probe。RC-164 后端边界/Anthropic 回归 16 passed、Ruff、Mypy 通过；Provider 页面专项 3 passed、ESLint、TypeScript 通过；拒绝 Cookie、订阅 Token、内部令牌、未知凭据和未知格式。RC-165 托管 Provider 联合回归 40 passed、Ruff、Mypy 通过；覆盖 Azure deployment/api-version/API key、Vertex project/region/Bearer + Gemini payload、Bedrock Converse + SigV4 signer 注入边界。bundled Python 缺少 pytest/ruff/mypy/PyYAML，直接 `.venv` Python 可用；CLI 入口仍缺 `rabbit_code` 源码路径，基线使用源码路径调用服务生成。完整 Vite 构建仍受沙箱目录权限限制。RC-166 联合 Provider 回归 48 passed、Provider Ruff、Mypy 通过；逐一覆盖 11 个主流兼容服务的 preset、默认 endpoint、发现路径、限制级别、自定义头和环境变量覆盖。RC-167 联合 Provider 回归 53 passed；覆盖能力矩阵、探测别名/覆盖、缓存命中与过期、探测失败回退、Agent 工具/结构化输出门控；前端全量 20 个测试文件 86 passed。全后端在补齐 `PYTHONPATH=backend/src;backend;packages/protocol` 后为 392 passed、5 skipped、55 warnings、6 个既有失败，详见 RC-167 日志；完整 Vite 构建仍受沙箱目录权限限制。RC-168 联合 Provider 回归 57 passed；覆盖 cursor 分页、TTL 缓存、空列表、超时、403、手动/已保存模型保留和 Registry Preset endpoint；前端全量 20 个测试文件 87 passed，ESLint、TypeScript 通过。RC-169 联合 Provider 回归 62 passed；覆盖 Mock 阶段、缺凭据修复提示、未确认真实请求阻断、确认后最小请求/工具 schema/token 上限和默认无费用；前端全量 20 个测试文件 87 passed，ESLint、TypeScript 通过。RC-170 联合 Provider/API 回归 78 passed；RC-170 专项覆盖 9 个 HTTP 类别、7 个 Adapter、网络/超时/取消共享呈现和 request ID 脱敏；前端全量 20 个测试文件 87 passed、ESLint、TypeScript/Vite build 通过；OpenAPI drift、Provider Ruff/Mypy、Python 编译通过；既有 jsdom navigation 与路径迁移 warning 保留。RC-171 联合 Provider/API 回归 90 passed；RC-171 专项 6 passed，覆盖退避/Retry-After、取消、代理/NO_PROXY/CA/IP 族和 opaque 凭据；Provider Ruff、Mypy、Python 编译通过；既有迁移 warning 保留。 |
| RC-172 最近验证 | RC-160 至 RC-172 联合 Provider/API 回归 92 passed；RC-172 专项 6 passed；Provider Ruff、工作区严格 Mypy、Python 编译、OpenAPI drift、前端全量 109 passed、ESLint 和 Vite build 通过。`rabbit_code` 类型标记和 jsdom navigation 问题已修复。 |
| RC-173 最近验证 | RC-160 至 RC-173 联合 Provider/API 回归 107 passed、2 skipped；RC-173 专项 15 passed、2 skipped；追踪、Provider Ruff、严格 Mypy、Python 编译和 workspace check 通过；真实 Provider 测试默认跳过且未产生费用。最终后端全量 646 passed、9 skipped、2 warnings，早期 RC-141/143、V2 golden 和 RC-153 import 排序失败已修复。 |
| RC-174 最近验证 | 首次运行页的 API/本地两入口、数据去向/网络/硬件说明、键盘可达性和 Rabbit artwork 完成；前端 20 个测试文件 87 passed、ESLint、TypeScript、Vite build 通过；Playwright 1440x1100 与 390x844 视口无重叠/横向溢出。后端未启动时 health 代理的既有 unavailable 状态如实保留。 |
| RC-175 最近验证 | API 向导四步、协议/服务商、Base URL、Key、模型、Mock `$0` 连接测试、测试后默认保存和非敏感草稿完成；前端 20 个测试文件 88 passed、ESLint、TypeScript、Vite build、Playwright 1440x1100/390x844 无溢出通过；openrouter/deepseek 等 Provider 默认路由读取接线通过。真实请求和 Key 持久化均未发生。 |
| RC-176 最近验证 | 无 API 向导覆盖硬件检测、Ollama/llama.cpp 运行器、Gemma/Qwen2.5-Coder 模型、许可证确认、下载暂停/恢复/取消、校验和、健康检查和 workspace Provider 路由落盘；RC-176 专项 7 passed，前端全量 20 个测试文件 89 passed、ESLint、TypeScript、Vite build、Playwright 1440x1100/390x844 无重叠/横向溢出通过。 |
| RC-177 最近验证 | API/本地向导完成态统一指向 `/workspace/home?workspace=...`；首页模型选择器同时展示 offline、云 Provider/模型和 ready local 条目，切换保留非敏感路由目录；前端全量 20 个测试文件 90 passed、ESLint、TypeScript、Vite build、Playwright 1440x1100/390x844 无重叠/横向溢出通过。 |
| RC-178 最近验证 | Provider 配置 workspace 持久化、创建/编辑/启用禁用/模型增删选/删除迁移，本地模型状态持久化与禁用保留历史，设置页入口和引用完整性完成；前端全量 20 个测试文件 93 passed、ESLint、TypeScript、Vite build、Playwright Provider 页 1440x1100/390x844 无横向溢出通过。 |
| RC-179 最近验证 | SecretStore/ConfigService 完成 opaque reference、Windows Credential Manager、Linux `secret-tool`、fail-closed 和 transient session/CLI 边界；RC-179 专项 5 passed，RC-064/RC-179/Provider 回归 18 passed，Ruff、定向 Mypy、compileall 通过；Windows 临时凭据 round-trip 成功并清理。 |
| RC-180 最近验证 | 全链路掩码/脱敏覆盖前端 UI、API 错误、导出、诊断复制、后端错误/JSON/metadata 和运行时指纹；后端 RC-064/RC-160 至 RC-173/RC-179/RC-180 联合回归 118 passed、1 skipped，RC-180 专项 2 passed，前端全量 21 个测试文件 96 passed、ESLint、TypeScript/Vite build、Ruff、定向 Mypy、compileall 通过；未发送真实 Provider 请求，既有 jsdom navigation stderr 保留。 |
| RC-181 最近验证 | 配置引用/优先级/环境变化/API 脱敏专项 4 passed；后端 RC-064/RC-160 至 RC-173/RC-179/RC-181 联合回归 122 passed、1 skipped，前端全量 21 个测试文件 97 passed、ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、定向 Mypy、compileall 通过；既有环境迁移 warning 与 jsdom navigation stderr 保留。 |
| RC-182 最近验证 | OAuth 专项 4 passed；政策未批准时默认阻断，PKCE/state、回调劫持/CSRF、防重放、loopback 清理、SecretStore opaque token、刷新和撤销通过；RC-064/RC-160 至 RC-173/RC-179/RC-182 联合回归 126 passed、1 skipped，Ruff、定向 Mypy、compileall 通过；未进行真实 OAuth 或 Provider 请求。 |
| RC-183 最近验证 | 本地边界专项 3 passed；匿名 offline 优化不要求账户，默认关闭同步不发送数据，启用同步必须显式账户授权；RC-064/RC-160 至 RC-173/RC-179/RC-183 联合回归 129 passed、1 skipped，前端本地入口/工作区 7 passed、ESLint、TypeScript/Vite build、Ruff、定向 Mypy、compileall 通过；既有环境迁移 warning 保留。 |
| RC-184 最近验证 | 清理/迁移/API 合约专项 10 passed，其中 RC-184 清理专项 4 passed；后端 RC-064/RC-160 至 RC-173/RC-179 至 RC-184 联合回归 139 passed、1 skipped，前端全量 21 个测试文件 98 passed、ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、定向 Mypy、compileall 通过；取消、未停进程和明文迁移拒绝均通过。 |
| 最近更新时间 | 2026-07-19 14:39:01 +08:00 |
| 更新人/Agent | Codex |

### 完成日志

| RC | 完成时间 | Commit/PR | 验证结果 | 证据 | 遗留问题 |
| --- | --- | --- | --- | --- | --- |
| RC-043 | 2026-07-17 00:59:26 +08:00 | `ed0e098` | PASS：追踪契约 4 passed；后端 36 passed；Ruff/Mypy；前端 9 passed、Lint/Build；索引检查通过 | `docs/evidence/RC-043/README.md` | 309 项待实施；48 个现有代码文件待随对应 RC 建立关联，不阻塞本项 |
| RC-046 | 2026-07-17 01:20:40 +08:00 | `4429c82` | PASS：sidecar 3 passed；后端 39 passed；Ruff/Mypy；前端 9 passed、Lint/Build；索引检查通过 | `docs/evidence/RC-046/README.md` | Windows 强制终止退出码 1；Docker Engine 未运行；跨平台/生产生命周期留给 RC-057/067 |
| RC-047 | 2026-07-17 01:39:57 +08:00 | `f009f66` | PASS：V2 回归 4 passed；后端 43 passed；Ruff/Mypy；前端 9 passed、Lint/Build；黄金 SHA-256 可复现 | `docs/evidence/RC-047/README.md` | 基线审批尚未加 CODEOWNERS 门禁；既有前端 jsdom 警告保留 |
| RC-048 | 2026-07-17 02:04:39 +08:00 | `424b135` | PASS：版本化 OpenAPI 36 paths/22 schemas 且 SHA-256 可复现；契约与既有 API 共 49 passed；Ruff/Mypy；前端 9 passed、Lint/Build；索引检查通过 | `docs/evidence/RC-048/README.md` | 旧 `/api/*` 入口仍按兼容期保留；生成客户端与 CI 差异门禁留给 RC-062；既有前端 jsdom 警告保留 |
| RC-049 | 2026-07-17 15:11:51 +08:00 | `78f2f19` | PASS：Provider 契约 9 passed；后端 69 passed；Ruff/Mypy；前端 9 passed、Lint/Build；OpenAI-compatible Mock 无真实请求；交付计划校验通过 | `docs/evidence/RC-049/README.md` | Gemini/Anthropic 原生协议和本地模型运行器留给后续 RC；既有前端 jsdom 警告和路径迁移 DeprecationWarning 保留 |
| RC-050 | 2026-07-17 02:15:33 +08:00 | `46485ac` | PASS：离线回退契约 3 passed；后端 52 passed；Ruff/Mypy；前端 9 passed、Lint/Build；OpenAPI SHA-256 保持可复现；索引检查通过 | `docs/evidence/RC-050/README.md` | Provider Adapter 拆分留给 RC-049；真实本地模型安装与运行器不属于本项；既有前端 jsdom 警告保留 |
| RC-052 | 2026-07-17 02:20:55 +08:00 | `eea66e9` | PASS：身份边界 2 passed；后端 54 passed；Ruff/Mypy；前端 9 passed、Lint/Build；ADR Accepted；索引检查通过 | `docs/evidence/RC-052/README.md` | JWT 生产级本地认证、撤销和 OS 密钥库留给 RC-179/207 等安全门禁；既有前端 jsdom 警告保留 |
| RC-053 | 2026-07-17 02:30:54 +08:00 | `994983f` | PASS：SQLite 备份/迁移/恢复契约 4 passed；后端 58 passed；Ruff/Mypy；前端 9 passed、Lint/Build；脚本检查和索引检查通过 | `docs/evidence/RC-053/README.md` | 备份加密、保留周期、跨设备灾备和并发写入协调不属于本项；既有前端 jsdom 警告保留 |
| RC-054 | 2026-07-17 02:49:55 +08:00 | `107df2c` | PASS：身份/路径/OpenAPI/sidecar 契约通过；后端 62 passed；Ruff/Mypy；前端 9 passed、Lint/Build；OpenAPI Rabbit Code 标题与 SHA-256 可复现；索引检查通过 | `docs/evidence/RC-054/README.md` | 兼容截止 3.0.0；安装包升级/卸载和兼容期结束后的删除留给 RC-055/发布波次；既有前端 jsdom 警告保留 |
| RC-051 | 2026-07-17 02:56:28 +08:00 | `bfe7e47` | PASS：CLI 兼容契约 3 passed；后端 65 passed；Ruff/Mypy；前端 9 passed、Lint/Build；OpenAPI SHA-256 可复现；索引检查通过 | `docs/evidence/RC-051/README.md` | 安装包升级/卸载、CLI 独立二进制和兼容期结束后的旧入口删除留给 RC-055/发布波次；既有前端 jsdom 警告保留 |
| RC-055 | 2026-07-17 03:32:37 +08:00 | `c04a528` | PASS：v2.0/v2.0-baseline 均剥离到 `8306d117`；V2 后端 31 passed；两次 Python wheel、前端 dist 和 Git archive 哈希一致；`release/v2.0` 分支保护与两个 V2 标签 Ruleset 已启用 | `docs/evidence/RC-055/README.md` | 制品哈希/来源证明留给 RC-277；安装包升级/卸载、独立 CLI 二进制和兼容期结束后的旧入口删除留给发布波次 |
| RC-056 | 2026-07-17 15:23:05 +08:00 | `04de5ae` | PASS：根级 workspace verify 通过；成员边界、统一版本和任务入口校验通过；后端 70 passed；前端 9 passed、Lint/Build；本地安装入口通过 | `docs/evidence/RC-056/README.md` | 现有实现路径按兼容策略保留；Agent Core、协议包、UI 包和 Tauri/CLI 真正迁移留给后续 RC；既有前端 jsdom 警告和路径迁移 DeprecationWarning 保留 |
| RC-057 | 2026-07-17 15:33:52 +08:00 | `1d29f8e`; `fc7fe44` | SUBMITTED WITH PENDING CONFIRMATION：Python Agent Core、prototype App Server、CLI、统一事件/取消和 Windows probe 已通过；Linux/Tauri/TypeScript 验证未执行，未勾选完成 | `docs/evidence/RC-057/README.md` | 受阻条件已如实记录；按用户指令自动继续 RC-058 准备，不把外部平台结果伪造成通过 |
| RC-058 | 2026-07-17 15:46:28 +08:00 | `0f595ab`; `f0abab1` | PASS：严格 App Server 3 passed；旧 API/CLI 契约 9 passed；后端 77 passed；前端 9 passed、Lint/Build；令牌/协议/health/单一 `/api/v1` OpenAPI 边界通过 | `docs/evidence/RC-058/README.md` | CLI service-mode、桌面壳令牌注入和取消传播留给 RC-059/060/063；RC-057 外部平台确认仍 pending |
| RC-059 | 2026-07-17 15:52:43 +08:00 | `74a219d` | PASS：runtime 契约 1 passed；后端 78 passed；前端 9 passed、Lint/Build；InProcess/AppServer 同一 AgentEvent 模型和 CLI runtime 选择通过 | `docs/evidence/RC-059/README.md` | 生产 App Server endpoint 统一和桌面壳职责留给 RC-060/063；RC-057 外部平台确认仍 pending |
| RC-060 | 2026-07-17 15:52:43 +08:00 | `590d4d9` | SUBMITTED WITH PENDING CONFIRMATION：desktop allowlist、业务隔离检查和 ADR 已提交；Rust/Tauri/Keychain/双平台打包未执行，未勾选完成 | `docs/evidence/RC-060/README.md` | cargo/rustc 缺失；按用户指令自动继续 RC-061 协议层准备 |
| RC-061 | 2026-07-17 16:02:31 +08:00 | `1adc320` | PASS：protocol 契约 2 passed；root install/verify；后端 81 passed；前端 9 passed、Lint/Build；v1 Schema round-trip/版本/序号约束通过 | `docs/evidence/RC-061/README.md` | TypeScript 客户端生成和 drift 门禁留给 RC-062；RC-057/060 外部平台确认仍 pending |
| RC-015 | 2026-07-17 03:38:00 +08:00 | `5fc9361` | PASS：9 个 GitHub 来源的 URL、默认分支、HEAD SHA、commit URL、许可证元数据和状态已固定；YAML 校验器与 Ruff 通过；CI 已接入 source baseline 门禁 | `docs/evidence/RC-015/README.md` | 4 个来源无 SPDX 许可证，1 个来源已归档；仅保留研究元数据，法律和 clean-room 结论留给 RC-021 至 RC-030 |
| RC-016 | 2026-07-17 03:50:47 +08:00 | `f88d8c2` | CLOSED BY USER：按用户指示将 RC-016 视为已完成；官方 Codex manual 获取 HTTP 403，未写入未经验证结论 | `docs/evidence/RC-016/README.md` | 未验证的 manual 结论不纳入本项目；本限制已记录，不阻塞 RC-017 |
| RC-017 | 2026-07-17 03:56:37 +08:00 | `583848a` | PASS：来源登记包含 `open-source`、`public-doc`、`behavior-only`；固定 Codex SHA、README 与 manual 均已核对；manual HEAD/GET 均 HTTP 200；来源校验器与 Ruff 通过；无新增 Codex GUI 源码/资产 | `docs/evidence/RC-017/README.md` | 公开文档只按事实使用；桌面 GUI 继续按 behavior-only 处理，不复制专有源码或资产 |
| RC-018 | 2026-07-17 04:00:49 +08:00 | `b8dcceb` | PASS：OpenCode MIT 固定 SHA `453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d`；11 模块对照；ADR 记录采用/放弃边界；原创隔离原型 3 事件通过；登记校验与 Ruff 通过 | `docs/evidence/RC-018/README.md` | 不复用上游代码、测试、文案、资源或 UI 资产；后续如需逐文件复用必须另行许可证审查 |
| RC-019 | 2026-07-17 04:04:58 +08:00 | `7fb6cee` | SUBMITTED WITH PENDING CONFIRMATION：固定 Claude Code 公开仓库、README、插件、Hook 和 settings 材料已索引；中立规格区分文档事实/黑盒观察/推测；资料校验与 Ruff 通过；官方文档入口 404、黑盒观察未执行 | `docs/evidence/RC-019/README.md` | 官方文档链接和黑盒观察待确认；不导入核心二进制、商业条款代码、源码、测试或资产 |
| RC-020 | 2026-07-17 04:08:37 +08:00 | `ced7b45` | SUBMITTED WITH PENDING CONFIRMATION：固定 Python SDK MIT 元数据、消息/交互/MCP/Hook/权限/会话/CLI transport 资料；SDK 校验与 Ruff 通过；官方文档入口 404，session fork 接口未验证 | `docs/evidence/RC-020/README.md` | SDK MIT 不扩展到捆绑 CLI；官方文档和 session fork 细节待确认；默认不下载或分发 CLI |
| RC-021 | 2026-07-17 04:12:16 +08:00 | `ee19518` | SUBMITTED WITH PENDING CONFIRMATION：5 个 source-map 仓库 API、固定 commit、README 均 200；许可证、归档、禁用状态和 README 摘要已记录；source body 未访问/保留/运行；校验器与 Ruff 通过 | `docs/evidence/RC-021/README.md` | DMCA/删除状态不是 GitHub API 字段，记录为 `not-observed`；所有来源默认 high risk、禁止复用 |
| RC-022 | 2026-07-17 04:14:51 +08:00 | `87421ae` | SUBMITTED WITH PENDING CONFIRMATION：公开许可证/条款复核、问题清单、决策输出字段和临时禁止规则已提交；校验器与 Ruff 通过；未伪造法律意见 | `docs/evidence/RC-022/README.md` | 缺少可核验公开依据的整理和决策编号；在依据不足前默认禁止 source-map 正文访问/使用/分发 |
| RC-023 | 2026-07-17 04:18:26 +08:00 | `71d5d1a` | PASS：5 个仓库 URL/仓库名/包名标识/固定哈希 denylist；128 个供应链输入零命中；注入禁用 URL 测试命中失败；pre-commit 与 CI 已接入；Ruff 通过 | `docs/evidence/RC-023/README.md` | 研究证据和审计脚本列为 evidence-only；发布前仍需保持扫描结果为零 |
| RC-024 | 2026-07-17 04:21:42 +08:00 | `b252756` | PASS：专有内容禁止清单、Provenance 模板、PR 必填字段和产品输入字符串审计已建立；62 个产品输入零禁用字面量；人工 diff 相似性审查无外部实现；CI 与 Ruff 通过 | `docs/evidence/RC-024/README.md` | 零字符串命中不等于法律清除；后续相关 PR 仍必须填写来源声明并完成人工审查 |
| RC-025 | 2026-07-17 04:24:53 +08:00 | `0170116` | SUBMITTED WITH PENDING CONFIRMATION：研究者/实现者/审查者角色、信息流、clean-room 规格模板和中立示例已提交；角色签署待人工分配；规格边界校验与 Ruff 通过 | `docs/evidence/RC-025/README.md` | 真实人员、权限和签署记录待确认；中立规格不得包含源文件名、原文或代码结构 |
| RC-026 | 2026-07-17 04:30:28 +08:00 | `1c5b1eb` | PASS：独立 Agent 事件设计比较方案 A/B；Provenance 只引用 clean-room 规格、固定许可来源和官方 SDK 事实；独立设计校验、source-map denylist、专有内容政策和 clean-room 校验通过 | `docs/evidence/RC-026/README.md` | 正式核心模块 PR 仍必须填写 Provenance；设计采用方案 A，不复制外部实现 |
| RC-027 | 2026-07-17 04:34:55 +08:00 | `6743ade` | SUBMITTED WITH PENDING CONFIRMATION：自建 fixture 含 5 项抽象断言；官方 Claude Code 2.1.202 `--help` 断言通过并固定输出哈希；未发送模型请求，Rabbit Code 差异对照待确认 | `docs/evidence/RC-027/README.md` | 不保存完整官方输出或官方测试夹具；后续对照运行需明确授权、脱敏工作目录和可重复记录 |
| RC-028 | 2026-07-17 04:41:07 +08:00 | `ed210b1` | PASS：两份 MIT 分析资料的固定 LICENSE/README 状态、代码围栏/外链计数和逆向/上游自述已审计；两份均标记 `restricted`；校验器与 Ruff 通过 | `docs/evidence/RC-028/README.md` | 未访问源码正文；MIT 元数据不批准还原/分析内容复用；只允许独立重新推导高层问题域 |
| RC-029 | 2026-07-17 04:44:29 +08:00 | `0180f13` | PASS：季度监控登记、复核日志、GitHub Actions workflow 和 live API 检查已建立；Claude Code/SDK HEAD、分支、license、归档/禁用状态与基线一致；静态/Ruff 通过 | `docs/evidence/RC-029/README.md` | 条款/文档 URL 未作未经验证结论；任何变化要求新 ADR，复核前保持限制 |
| RC-030 | 2026-07-17 04:47:16 +08:00 | `6483383` | SUBMITTED WITH PENDING CONFIRMATION：source-map clean-room 决策记录汇总事实、风险、临时允许/禁止范围、角色隔离、监控和 M0 触发条件；M0 校验为 blocked；未伪造签署 | `docs/evidence/RC-030/README.md` | 技术/合规/法律签署和决策编号待人工确认；在批准前默认禁止 source-map 正文访问、使用和分发 |
| RC-031 | 2026-07-17 04:52:51 +08:00 | `8e5ab1f` | SUBMITTED WITH PENDING CONFIRMATION：Ollama/llama.cpp 固定 MIT 运行器版本；Gemma/Qwen 固定 HF commit、模型许可、gated 状态和文件哈希/大小；manifest 校验与 Ruff 通过；权重未下载 | `docs/evidence/RC-031/README.md` | Gemma manual-gated 条款/模型卡正文待确认；默认不打包模型权重，下载前必须 UI 确认并校验哈希 |
| RC-032 | 2026-07-17 05:00:51 +08:00 | `bb1f6b4` | SUBMITTED WITH PENDING CONFIRMATION：32 个直接/构建依赖全部登记；PyPI/npm 官方 metadata 已记录；THIRD_PARTY_NOTICES 可生成且对账通过；10 个条目仍 review-required | `docs/evidence/RC-032/README.md` | 未确认 license 和自定义 GSAP 条目不得发布；传递依赖/SBOM 逐层审计留给后续发布门禁 |
| RC-033 | 2026-07-17 05:05:44 +08:00 | `7d8d455` | SUBMITTED WITH PENDING CONFIRMATION：clean-room 行为规格、双候选方案、独立测试、Provenance、实现者记录、原创历史和相似性门禁已定义；流程校验通过，正式实现 PR 待确认 | `docs/evidence/RC-033/README.md` | 未有核心实现需要重写；在角色签署和实现 PR 前维持 restricted 材料隔离 |
| RC-034 | 2026-07-17 05:13:20 +08:00 | `3b85662` | SUBMITTED WITH PENDING CONFIRMATION：名称/渠道公开入口登记、保守的 404 风险校验和公开商标信息待检索状态已提交；校验器与 Ruff 通过 | `docs/evidence/RC-034/README.md` | 具体公开商标信息、负责人确认和组织/包名冲突核验待确认；不以域名或应用商店控制权作为前置条件 |
| RC-035 | 2026-07-17 12:08:19 +08:00 | `f72ef6e`; 修正 `5fc4d75` | SUBMITTED WITH PENDING CONFIRMATION：用户确认仓库兔兔素材身份并声明 AI 生成，授权未知，已建立 SHA-256 登记与发布阻断门禁；校验器与 Ruff 通过 | `docs/evidence/RC-035/README.md` | 原始来源、权利人书面声明、生成服务条款、许可证、署名条款和发布批准待确认 |
| RC-036 | 2026-07-17 12:17:01 +08:00 | `8ec7253` | SUBMITTED WITH PENDING CONFIRMATION：六组来源、ADR/许可证/不复用索引和 M0/架构 Issue 门禁已提交；校验器与 Ruff 通过 | `docs/evidence/RC-036/README.md` | M0 逐份签收、重复 ADR-0003 修正和后续架构 Issue 决策映射待确认 |
| RC-037 | 2026-07-17 12:25:00 +08:00 | `4d75ca9` | SUBMITTED WITH PENDING CONFIRMATION：五类 Persona、可测高频任务、优先级、冲突与核心能力覆盖已提交；校验器与 Ruff 通过，访谈未执行 | `docs/evidence/RC-037/README.md` | 真实用户访谈/问卷、P0 优先级和产品范围签收待确认 |
| RC-038 | 2026-07-17 13:12:09 +08:00 | `bc9764d` | SUBMITTED WITH PENDING CONFIRMATION：Windows/Linux 首发平台矩阵、x86_64 正式基线、终端/Shell、CPU/GPU、未签名制品、SHA-256、验证环境和责任角色已冻结；组合实测待后续 RC | `docs/evidence/RC-038/README.md` | Linux 实机、未签名安装包、ARM/GPU 和 Fedora rpm 实测待后续平台/安装包/测试 RC；macOS 不在首发范围 |
| RC-039 | 2026-07-17 13:46:04 +08:00 | `e6b71e8` | SUBMITTED WITH PENDING CONFIRMATION：十二个核心旅程、R1-R6 映射、失败/恢复分支、功能依赖和人工测试卡已提交；实现/E2E 待后续 RC | `docs/evidence/RC-039/README.md` | Agent、GUI、Provider、模型和跨平台 E2E 待后续 RC；RC-037 产品范围评审仍待确认 |
| RC-040 | 2026-07-17 13:58:40 +08:00 | `16f773c` | SUBMITTED WITH PENDING CONFIRMATION：CLI、GUI、无头三表面共享核心、唯一事件/存储 Schema 和 GUI 专属差异已冻结；实现对账待后续 RC | `docs/evidence/RC-040/README.md` | Agent/Provider/会话/权限/优化共享实现、事件重放、存储对账和跨表面 E2E 待后续 RC；现有 V2 API 仅为迁移依赖 |
| RC-041 | 2026-07-17 14:15:28 +08:00 | `8898769` | PASS：MVP、首个稳定版和增强边界校验通过；R1-R6、原初 12 类计划和 RC-001..RC-310 均进入稳定版路线；Ruff、追踪查询和空白检查通过 | `docs/evidence/RC-041/README.md` | 真实实现、Provider、本地模型、跨平台实机、视觉回归和发布验收留给后续 RC；增强项需按登记的进入条件新增 RC |
| RC-042 | 2026-07-17 14:29:12 +08:00 | `a187b2c` | PASS：17 项 RC-040 能力的成功/失败/取消/重试/降级/离线/拒绝/恢复状态、统一错误码/UI 文案和非成功参数完整；校验器、Ruff、追踪查询和空白检查通过 | `docs/evidence/RC-042/README.md` | 状态参数执行、真实实现、Provider、本地模型、GUI/CLI/无头 E2E 和实机验收留给后续 RC |
| RC-044 | 2026-07-17 14:39:40 +08:00 | `223eaab` | PASS：SemVer、API/配置/数据库/CLI 兼容窗口、弃用规则、v0/v1 测试数据、前向迁移和受控回滚策略通过；Ruff、SQLite 迁移/回滚 4 passed、追踪检查通过 | `docs/evidence/RC-044/README.md` | 未来 schema、兼容窗口到期、安装升级和跨平台发布迁移留给后续 RC；不执行原地降级 |
| RC-045 | 2026-07-17 14:50:05 +08:00 | `6fc3f39` | PASS：RC-001..RC-310 唯一覆盖、工作量/缓冲/依赖日期/负责人/评审者/里程碑和周证据字段通过；Ruff、追踪查询和空白检查通过 | `docs/evidence/RC-045/README.md` | 实际开发速度、人工维护者和外部平台资源按周更新；下一未完成项为 RC-049 |
| RC-062 | 2026-07-17 16:22:05 +08:00 | `1da1f5e` | PASS：OpenAPI 生成 schema/client；root generate-api/check/verify 和 PowerShell 入口通过；RC-062 drift 契约 2 passed；后端 83 passed；前端 9 passed、Ruff/Mypy、Lint/Build、追踪校验通过 | `docs/evidence/RC-062/README.md` | RC-063 处理 SSE/WebSocket/JSON-RPC 传输边界；RC-057/060 外部平台确认仍 pending |
| RC-063 | 2026-07-17 16:39:48 +08:00 | `300e450` | PASS：Accepted transport ADR；RC-063 传输契约 5 passed；root verify；后端 88 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪和交付计划校验通过 | `docs/evidence/RC-063/README.md` | 事件回放和工具账本当前为进程内实现；崩溃恢复、跨进程持久化和 Provider 取消留给 RC-064/067/071/073；RC-057/060 外部平台确认仍 pending |
| RC-064 | 2026-07-17 16:51:31 +08:00 | `5c9ef99` | PASS：FileStore/SQLite 12 passed；root verify；后端 92 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪和交付计划校验通过；首次 root verify 因追踪索引待更新停止，已修正后重跑通过 | `docs/evidence/RC-064/README.md` | 跨进程文件锁、加密/配额/保留策略、完整 session 表留给后续安全/生命周期 RC；RC-057/060 外部平台确认仍 pending |
| RC-065 | 2026-07-17 17:05:03 +08:00 | `421a585` | PASS：配置/CLI 10 passed；身份/Provider/CLI 25 passed；root verify；后端 99 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪和交付计划校验通过 | `docs/evidence/RC-065/README.md` | Provider 环境变量兼容迁移、OS 密钥库和 GUI 设置屏幕留给后续迁移/桌面/UI RC；RC-057/060 外部平台确认仍 pending |
| RC-066 | 2026-07-17 17:23:22 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Protocol/构造器注入/依赖边界 4 passed；root verify；后端 103 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-066/README.md` | 当前变更尚未提交；Provider OS 密钥库迁移和 RC-067 进程生命周期继续处理；RC-057/060 外部平台确认仍 pending |
| RC-067 | 2026-07-17 17:33:40 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：sidecar 生命周期 6 passed；root verify；后端 109 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-067/README.md` | 当前变更尚未提交；Tauri/Rust、Linux 打包和安装升级仍待 RC-057/060 外部确认与后续发布工作 |
| RC-068 | 2026-07-17 17:41:43 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Agent 状态/重放/检查点 5 passed；兼容回归 10 passed；root verify；后端 114 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-068/README.md` | 当前变更尚未提交；工具审批、预算、暂停/恢复和跨进程会话恢复留给后续 Agent Core RC；RC-057/060 外部确认仍 pending |
| RC-069 | 2026-07-17 17:50:22 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：CLI 模式/快照/退出码 6 passed；兼容回归 12 passed；root verify；后端 120 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-069/README.md` | 当前变更尚未提交；完整 TTY/权限/会话工作流留给后续 Agent Core RC；RC-057/060 外部确认仍 pending |
| RC-070 | 2026-07-17 17:56:22 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：权限矩阵 5 passed；Agent/CLI/权限回归 16 passed；root verify；后端 125 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-070/README.md` | 当前变更尚未提交；GUI Agent 工具面、工具注册、文件/终端沙箱和更广安全加固留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-071 | 2026-07-17 18:02:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：统一流事件/聚合/中断 15 passed；root verify；后端 129 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-071/README.md` | 当前变更尚未提交；GUI/TUI 渲染、工具/任务进度生产者和跨进程取消传输留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-072 | 2026-07-17 18:07:43 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：预算原子扣减/预警/终止 13 passed；root verify；后端 133 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-072/README.md` | 当前变更尚未提交；Provider 原生遥测、持久预算账本和 UI 用量展示留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-073 | 2026-07-17 23:43:14 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：暂停/恢复/取消/重试/重新生成和持久幂等尝试链 5 passed；相邻 Agent Core 回归 29 passed；root verify；后端 138 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-073/README.md` | 当前变更尚未提交；写操作只在成功记录存在时复用，失败或 in-flight 状态保持不可安全重试；跨平台/Tauri、真实 Provider 和 UI 命令面留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-074 | 2026-07-17 23:53:56 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：受控子 Agent 并行/上下文隔离/权限深度/预算/级联取消 4 passed；相邻 Agent Core 回归 33 passed；root verify；后端 142 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-074/README.md` | 当前变更尚未提交；执行器仍通过依赖注入接入，真实 Provider/工具编排、跨进程子任务调度和 UI 展示留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-075 | 2026-07-18 00:01:10 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Hook 排序/权限/超时/异常/输出校验/配置合并 5 passed；相邻 Agent Core 回归 38 passed；root verify；后端 147 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-075/README.md` | 当前变更尚未提交；超时后台线程只能从主调度摘除，外部 Hook 沙箱、插件来源和 UI 配置留给后续安全/插件 RC；RC-057/060 外部确认仍 pending |
| RC-076 | 2026-07-18 00:09:03 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：MCP 配置/工具映射/认证/重连/取消/stdio 清理 5 passed；相邻 Agent Core 回归 43 passed；root verify；后端 152 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-076/README.md` | 当前变更尚未提交；真实官方 MCP 服务器矩阵、跨进程故障演练、认证刷新和 UI/MCP 配置留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-077 | 2026-07-18 00:17:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：插件安装/启用/禁用/升级/卸载和 manifest 门禁 7 passed；相邻 Agent Core 回归 50 passed；root verify；后端 159 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-077/README.md` | 当前变更尚未提交；插件签名/沙箱、远程来源、依赖隔离、跨进程生命周期和 UI 配置留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-078 | 2026-07-18 00:23:49 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：模型能力协商/可选工具降级/必需能力拒绝/上下文推理检查 3 passed；相邻 Agent Core 回归 53 passed；root verify；后端 162 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-078/README.md` | 当前变更尚未提交；Provider 原生能力遥测、能力 UI、跨协议映射和完整视觉/音频能力留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-079 | 2026-07-18 00:29:01 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：隐藏字段递归过滤/公开日志白名单/预定义进度 3 passed；相邻 Agent Core 回归 56 passed；root verify；后端 165 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-079/README.md` | 当前变更尚未提交；语义级隐藏内容检测、第三方 Provider 原始响应审计和全量导出路径检查留给后续安全/隐私 RC；RC-057/060 外部确认仍 pending |
| RC-080 | 2026-07-18 00:34:37 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Git/分支/改动/语言/构建标记/指令文件识别和依赖目录忽略 2 passed；相邻 Agent Core 回归 58 passed；root verify；后端 167 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-080/README.md` | 当前变更尚未提交；指令内容解析、项目配置优先级和执行策略留给后续 RC-081/RC-082；RC-057/060 外部确认仍 pending |
| RC-081 | 2026-07-18 00:40:29 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：全局/项目/目录指令优先级、越界工作目录拒绝 2 passed；相邻 Agent Core 回归 60 passed；root verify；后端 169 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-081/README.md` | 当前变更尚未提交；指令内容解析、项目配置优先级、冲突解释和执行授权留给后续 RC-082/权限 RC；RC-057/060 外部确认仍 pending |
| RC-082 | 2026-07-18 00:47:29 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：文件/目录/选择/图片附件/终端/diff/诊断和路径/截断边界 2 passed；相邻 Agent Core 回归 62 passed；root verify；后端 171 passed；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-082/README.md` | 当前变更尚未提交；真实多模态上传、附件解析、上下文压缩和跨模块预算协调留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-083 | 2026-07-18 00:59:05 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：忽略/敏感/二进制/大文件/符号链接/增量/取消 1 passed、1 skipped；相邻 Agent Core 回归 63 passed、1 skipped；root verify；后端 172 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-083/README.md` | 当前变更尚未提交；Windows symlink 创建权限导致夹具 skip；完整 gitignore 语义、文件监视器、磁盘活动基准留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-084 | 2026-07-18 01:07:40 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Token 估算/分层保留/去重/结构化来源摘要 2 passed；相邻 Agent Core 回归 65 passed、1 skipped；root verify；后端 174 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-084/README.md` | 当前变更尚未提交；真实 tokenizer、压缩质量基准、持久上下文缓存和跨 Provider 预算协调留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-085 | 2026-07-18 01:19:46 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：四类记忆隔离、来源/用途确认、查看/编辑/逐项删除/清理和禁用拒绝 4 passed；root verify；后端 178 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-085/README.md` | 当前变更尚未提交；持久化后端、API/CLI/GUI 接入和记忆展示留给后续生命周期/UI RC；RC-057/060 外部确认仍 pending |
| RC-086 | 2026-07-18 01:30:02 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：会话 CRUD/标题/搜索分页/置顶/归档/软删除恢复/继续/分叉/JSON 导出/分页审计 4 passed；root verify；后端 182 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-086/README.md` | 当前变更尚未提交；持久化会话数据库、API/CLI/GUI 接线和生产保留策略留给后续生命周期/UI RC；RC-057/060 外部确认仍 pending |
| RC-087 | 2026-07-18 01:36:36 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：基线/变更组/工具验证记录、正常回滚、用户并发冲突、逆序全量和部分回滚 4 passed；root verify；后端 186 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-087/README.md` | 当前变更尚未提交；持久化检查点、跨进程恢复、生产回滚 UI 和更广工具接入留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-088 | 2026-07-18 01:43:04 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：并行 worktree 路径隔离、进程/终端资源归属、worktree/缓存清理和项目缓存/用户分支保留 5 passed；root verify；后端 191 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-088/README.md` | 当前变更尚未提交；真实 Git worktree、进程终止、跨进程资源服务和生产 GUI 工作区管理留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-089 | 2026-07-18 01:52:05 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：迁移/WAL/完整性、未完成事务恢复、检查点/导出/隐私清理、备份恢复、只读救援和显式清理边界 5 passed；root verify；后端 196 passed、1 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-089/README.md` | 当前变更尚未提交；更广数据库故障注入、跨进程会话服务、生产保留和加密策略留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-090 | 2026-07-18 01:59:42 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：文件工具正常操作、越界、二进制/大小、symlink、并发 SHA 冲突和权限拒绝 3 passed、1 skipped；root verify；后端 199 passed、2 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-090/README.md` | 当前变更尚未提交；Windows symlink 创建权限导致本项 1 skip；并发监听、跨平台权限矩阵和更广工具编排留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-091 | 2026-07-18 02:13:03 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：数组命令 Unicode/空格/环境/诊断、PowerShell/cmd/Bash/zsh 脚本、超时/权限/cwd/参数 5 passed、2 skipped；root verify；后端 204 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-091/README.md` | 当前变更尚未提交；Windows WSL bash 运行时不可用导致 1 skip，Windows symlink 既有夹具导致 1 skip；跨平台实机矩阵和进程树终止留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-092 | 2026-07-18 02:24:04 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Git status/diff/log/branch/worktree/stage/commit/冲突和远程拒绝审计 5 passed；root verify；后端 209 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-092/README.md` | 当前变更尚未提交；远程 Git/PR 实测、跨平台 Git 行为和认证策略留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-093 | 2026-07-18 02:31:55 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Ruff/Mypy/TypeScript/Pytest 诊断解析、统一字段、Windows POSIX 路径、未知输出原文保留 3 passed；root verify；后端 212 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-093/README.md` | 当前变更尚未提交；完整 LSP 适配和跨平台诊断矩阵留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-094 | 2026-07-18 02:48:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：后台进程注册/并发、日志游标、超时、停止、端口占用、PTY 明确不可用和终止后状态 5 passed；root verify；后端 217 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过；Windows Job Object 创建检查通过 | `docs/evidence/RC-094/README.md` | 当前环境为 Windows；Linux/非 Windows PTY、进程树和父进程退出实机矩阵留待可用平台，不伪造为已验证；RC-057/060 外部确认仍 pending |
| RC-095 | 2026-07-18 02:58:34 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：结构化解析、Unicode/CRLF、UTF-16 BE BOM、基线/上下文冲突、多文件事务和中途失败全量回滚 6 passed；root verify；后端 223 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-095/README.md` | 当前变更尚未提交；复杂二进制/未知编码按明确不支持处理，工具输出截断和异常统一留给 RC-096；RC-057/060 外部确认仍 pending |
| RC-096 | 2026-07-18 03:12:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：大输出上限/截断、二进制元数据、非零失败、显式重试、超时、用户取消、后台日志截断游标 5 passed；RC-091/094/096 联合 15 passed、2 skipped；root verify；后端 228 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-096/README.md` | 当前变更尚未提交；跨平台实机矩阵和更广工具异常策略留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-097 | 2026-07-18 03:21:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：工具 metadata 注册、重复/缺字段/非法 Schema、startup/model handler 门禁、输入校验、权限和审计 5 passed；RC-091/094/095/096/097 联合 26 passed、2 skipped；root verify；后端 233 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-097/README.md` | 当前变更尚未提交；更广工具适配和跨表面消费留给 RC-098；RC-057/060 外部确认仍 pending |
| RC-098 | 2026-07-18 03:26:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：7 类已知内容块、protocol Message.content、API/CLI/GUI canonical snapshot、未知块 fallback、事件内容消费和字段拒绝 5 passed；root verify；后端 238 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-098/README.md` | 当前变更尚未提交；CLI/GUI 真实组件接线和扩展工具留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-099 | 2026-07-18 03:33:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：ExtensionSpec 声明能力、默认禁用、session 审批、network/write 独立授权、撤销即时生效、未声明权限拒绝、browser/database/external_service/plugin/mcp 统一 adapter 21 passed；root verify；后端 242 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-099/README.md` | 当前变更尚未提交；真实浏览器/数据库/外部服务联网实测留给后续受控环境；RC-057/060 外部确认仍 pending |
| RC-100 | 2026-07-18 03:40:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：run/continue/resume/model/mode/output 命令、session/model/mode/output/runtime 参数、stdin/TTY/legacy prompt、text/json/jsonl 输出和稳定 usage/runtime/cancel 退出码 12 passed；root verify；后端 245 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-100/README.md` | 当前变更尚未提交；持久会话恢复、真实 model/mode 配置接线和 TUI 留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-101 | 2026-07-18 03:47:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：共享 AgentEvent 消费、固定输入区、流式文本、工具/权限/计划/diff/usage 状态、窄屏宽度、无颜色和 tui CLI 入口 6 passed；root verify；后端 248 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-101/README.md` | 当前变更尚未提交；键盘编辑/历史/补全/粘贴和跨平台 TTY 实测留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-102 | 2026-07-18 03:58:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Unicode/IME 多行、光标编辑、history 上下/搜索、completion、workspace mention、附件、长粘贴确认和 shortcut 配置 4 passed；RC-101/102 联合 7 passed；root verify；后端 252 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-102/README.md` | 当前变更尚未提交；真实 TTY 键盘/IME/剪贴板矩阵和 TUI 接线留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-103 | 2026-07-18 04:07:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：13 个默认 slash 命令、help/completion、required 参数、session 影响标记、引号解析、未知命令建议、自定义注册和 exit 结构化结果 4 passed；root verify；后端 256 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-103/README.md` | 当前变更尚未提交；slash 命令真实 Agent/Provider/MCP/Plugin 业务接线留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-104 | 2026-07-18 04:13:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：显式 non-interactive 缺策略失败、read-only/deny/approve 策略、no-TTY 无等待、JSON 稳定输出、PermissionError 专用退出码、旧管道兼容 12 passed；root verify；后端 259 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-104/README.md` | 当前变更尚未提交；真实危险工具审批接线和 CI 跨平台矩阵留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-105 | 2026-07-18 04:21:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：DryRunPlanner 只读计划、MachineEvent 连续 seq/json/jsonl、CLI dry-run、read-only 冲突和 log-level 3 passed；root verify；后端 262 passed、4 skipped；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-105/README.md` | 当前变更尚未提交；真实工具动作预览和更多消费者事件回放留给后续 RC；RC-057/060 外部确认仍 pending |
| RC-106 | 2026-07-18 04:34:34 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：独立 CLI/GUI context 共享 Provider 引用、模型目录、会话、权限和优化器；原子 JSON store、跨进程锁、进程内路径锁和并发写 4 passed；root verify；后端 266 passed、4 skipped、29 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-106/README.md` | 当前变更尚未提交；密钥实际安全存储、跨进程会话服务和真实 CLI/GUI 进程接线留给后续 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-107 | 2026-07-18 04:43:46 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：终端矩阵、PowerShell/cmd 输入与 ANSI、TUI 尺寸、Unicode 路径、取消信号和 WSL Linux 语义 6 passed、1 skipped；root verify；后端 272 passed、5 skipped、29 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-107/README.md` | 当前变更尚未提交；Windows Terminal 仅验证可执行文件（7.6.3），当前无 `WT_SESSION`，交互尺寸/剪贴板未实测；宿主为 Windows，原生 Linux 终端留待 Linux 条件；RC-057/060 外部确认仍 pending |
| RC-108 | 2026-07-18 04:56:18 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Bash/zsh/fish/PowerShell 补全、版本/安装路径、doctor JSON、缓存清理、确认门禁、工作区保护和 CLI dry-run 9 passed；root verify；后端 281 passed、5 skipped、31 warnings；前端 9 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-108/README.md` | 当前变更尚未提交；系统包管理器级卸载、真实安装器路径清理和跨平台交互实机留给后续发布/平台 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-109 | 2026-07-18 05:07:03 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：独立 onboarding 路由的新装、已有配置、服务异常状态，API/本地两入口、键盘焦点和重试 3 passed；root verify；后端 281 passed、5 skipped、31 warnings；前端 12 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-109/README.md` | 当前变更尚未提交；真实 App Server/密钥库/本地运行器接线仍由后续 Provider 与本地模型 RC 完成；服务 404 按“未配置”显示，网络失败按“不可用”显示；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-110 | 2026-07-18 05:17:12 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：工作区首页项目 API 加载、guest 空状态、最近项目移除/持久隐藏、模型状态、快速任务和项目服务错误重试 3 passed；root verify；后端 281 passed、5 skipped、31 warnings；前端 15 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-110/README.md` | 当前变更尚未提交；真实目录权限/项目删除后端接口、任务历史统一服务和完整模型目录留给后续 RC；guest 使用本地最近记录，认证用户项目从生成 API 客户端读取；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-111 | 2026-07-18 05:27:49 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：主任务左侧会话 rail、中间 conversation/composer、右侧 Plan/Diff/Context inspector、折叠、草稿持久化、发送、新会话和终端抽屉 3 passed；root verify；后端 281 passed、5 skipped、31 warnings；前端 18 passed；Ruff/Mypy、Lint/Build、drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-111/README.md` | 当前变更尚未提交；真实 Agent 事件、PTY 终端和检查点/diff 服务接线留给后续 RC；当前终端抽屉为状态边界，不启动真实进程；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-112 | 2026-07-18 05:40:30 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：变更审查页专项 3 passed；完整前端 21 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-112/README.md` | 当前变更尚未提交；本项验证的是前端审查消费边界和漂移阻断，真实 checkpoint/diff 服务、磁盘一致性应用和并发编辑实测留给后续 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-113 | 2026-07-18 05:52:34 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：终端/进程面板专项 3 passed；完整前端 24 passed；RC-094 进程回归 5 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-113/README.md` | 当前变更尚未提交；本项验证的是前端终端/进程消费边界和关闭清理状态，真实 PTY service、真实 shell I/O、窗口 resize 接线和跨平台关闭无残留实测留给后续 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-114 | 2026-07-18 06:02:57 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：Provider/模型页专项 2 passed；完整前端 26 passed；API Key DOM 红线通过；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-114/README.md` | 当前变更尚未提交；本项验证的是前端 Provider/模型消费边界，真实 Provider 管理 API、OS keychain 写入、原生模型 discovery 和真实连接 E2E 留给后续 Provider/平台 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-115 | 2026-07-18 06:14:27 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：本地模型安装页专项 3 passed；完整前端 29 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-115/README.md` | 当前变更尚未提交；本项验证的是本地模型安装生命周期消费边界，真实下载/校验文件、App Server 进度订阅、模型 runner 进程和断网/磁盘实机故障注入留给后续 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-116 | 2026-07-18 06:40:59 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：提示词资产页专项 2 passed；完整前端 31 passed；导入失败不污染列表、回填 Composer 不自动发送；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-116/README.md` | 当前变更尚未提交；本项验证的是前端资产库消费边界，真实分页服务、远程资产同步、历史数据库和 Composer 状态注入留给后续 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-117 | 2026-07-18 07:05:19 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：设置页专项 3 passed；完整前端 34 passed；workspace scope 持久化/隔离和危险重置确认通过；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-117/README.md` | 当前变更尚未提交；本项验证的是前端设置消费边界，真实 OS/Tauri 设置、系统主题/语言/终端即时接线和跨设备同步留给后续平台 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-118 | 2026-07-18 07:31:22 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：诊断/关于/更新页专项 3 passed；完整前端 37 passed；脱敏诊断不含 Key/源码正文；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-118/README.md` | 当前变更尚未提交；本项验证的是前端诊断消费边界，真实 sidecar/runner 健康探测、日志服务、版本源和系统更新通道留给后续平台 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-119 | 2026-07-18 07:59:49 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：共享 Empty/Error/Offline 状态、Permission/Install/通用 Dialog；组件快照 5 项、焦点陷阱/Escape/焦点恢复/读屏语义 2 项；完整前端 44 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-119/README.md` | 当前变更尚未提交；仓库没有 Storybook 配置，本项使用 Vitest 组件快照完成等价组件覆盖；系统级原生权限弹窗和 Tauri 窗口层语义留给后续平台 RC；既有环境警告与 RC-057/060 外部确认仍 pending |
| RC-120 | 2026-07-18 08:10:26 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：窗口偏好 3 passed；Task inspector/Settings 回归 6 passed；desktop shell boundary；完整前端 47 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-120/README.md` | 当前变更尚未提交；Tauri/Rust 原生窗口恢复、托盘、OS 通知权限、DPI 和多显示器实机仍受当前无桌面构建条件限制，已在 ADR 中保留 pending；RC-057/060 外部确认仍 pending |
| RC-121 | 2026-07-19 | 未提交工作树（HEAD `5610c00`） | PASS WITH DOCUMENTED ACCESSIBILITY LIMITS：Windows 原生窗口与 Linux Docker/Xvfb/Openbox 窗口均完成创建、调整、最大化/恢复和关闭验证；原生标题栏方案把辅助技术朗读留给发布级人工矩阵 | `docs/evidence/RC-121/README.md` | 发行版、桌面环境和真实辅助技术矩阵仍为发布级人工验收，不阻塞标题栏架构 |
| RC-122 | 2026-07-19 | 未提交工作树（HEAD `5610c00`） | PASS：根目录 `兔兔素材.png` 已登记为品牌母版，SHA-256、尺寸/格式、运行时路径和 Rabbit Code 项目发布授权均固定 | `docs/evidence/RC-122/README.md`、`docs/legal/rabbit-art-license.yml` | 通用商业许可和脱离 Rabbit Code 项目的素材单独销售仍不在本次授权范围 |
| RC-123 | 2026-07-19 | 未提交工作树（HEAD `5610c00`） | PASS：六类派生资产规范、manifest、PNG/WebP/ICO 输出和 1x/2x 规则均已校验 | `docs/evidence/RC-123/README.md`、`docs/design/rabbit-asset-manifest.json` | 通用商业许可边界同 RC-122，未扩展到素材单独销售 |
| RC-124 | 2026-07-18 08:21:00 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：页面级素材矩阵、禁入区、响应式/主题/替代文本和视觉验收清单已交付；现有路由素材使用对照已记录；计划/追踪检查通过 | `docs/evidence/RC-124/README.md` | 实际 RabbitMark 接入留给 RC-125；源素材授权、派生导出和视觉回归仍由 RC-122/123/133 门禁控制；RC-121/057/060 外部确认仍 pending |
| RC-125 | 2026-07-18 08:30:05 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RabbitMark 组件 2 passed；9 个独立工作路由变体检查 9 passed；完整前端 58 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、desktop boundary 和交付计划校验通过 | `docs/evidence/RC-125/README.md` | 当前变更尚未提交；实际派生变体仍受 RC-122/123 源素材与授权门禁约束；视觉回归和完整页面覆盖留给 RC-133；RC-121/057/060 外部确认仍 pending |
| RC-126 | 2026-07-18 08:35:23 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：14 路由 coverage manifest/Markdown 生成与 current check；新增 route 未登记门禁已接入 `workspace.py check`；完整前端 58 passed；root verify；后端 281 passed、5 skipped、31 warnings；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界和交付计划校验通过 | `docs/evidence/RC-126/README.md` | 当前变更尚未提交；覆盖矩阵的视觉快照执行留给 RC-133；源素材/派生物和 RC-121/057/060 外部确认仍 pending |
| RC-127 | 2026-07-19 | 未提交工作树（HEAD `5610c00`） | PASS：桌面/终端 PNG/WebP、512px PNG 应用图标和多尺寸 ICO 已导出；母版哈希、包体预算、1x/2x 清晰度与 Windows/Linux Tauri 编译均通过 | `docs/evidence/RC-127/README.md`、`docs/design/rabbit-asset-manifest.json` | 仅保留通用商业许可边界；Rabbit Code 项目发布授权已确认 |
| RC-128 | 2026-07-18 08:56:33 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：`RabbitMark` 专项 4 passed；mark/mono 独立 SVG、full/avatar/empty 固定内部 PNG、16/20/24/32px light/dark 结构和装饰语义通过；Playwright 8 个 SVG DOM 检查和深浅背景截图设计评审通过；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-128/README.md` | 当前变更尚未提交；完整页面高对比/200%视觉回归留给 RC-133；RC-127 实际位图导出和 RC-121/057/060 外部确认仍 pending |
| RC-129 | 2026-07-18 09:22:48 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：路由层级专项 9 passed；内容优先级、装饰预算、`aria-hidden`/`pointer-events` 边界和 CSS 变量已交付；Playwright 真实 Review diff、Terminal 长日志、Task composer 在 1280x1000 与 390x844 检查无素材/控件交集；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-129/README.md` | 当前变更尚未提交；390px Review 既有三栏响应式问题留给 RC-255/256；完整页面视觉回归留给 RC-133；RC-127 实际位图导出和 RC-121/057/060 外部确认仍 pending |
| RC-130 | 2026-07-18 09:26:41 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：token JSON 源、CSS/TypeScript/主题快照生成与 check 通过；frontend raw color scan clean；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、60 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-130/README.md` | 当前变更尚未提交；RC-127 实际位图导出、390px Review 既有三栏响应式问题和 RC-121/057/060 外部确认仍 pending |
| RC-131 | 2026-07-18 09:52:36 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：图标语言清单、Sparkles/Star 语义门禁、App 专项 10 passed；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、61 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-131/README.md` | 当前变更尚未提交；RC-132 无障碍全量验收、RC-127 实际位图导出、390px Review 既有三栏响应式问题和 RC-121/057/060 外部确认仍 pending |
| RC-132 | 2026-07-18 10:32:07 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：14 路由 × light/dark 共 28 组 axe 无 violation；键盘菜单循环/Escape 焦点恢复、reduced-motion、640px 等效 200% 检查通过；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、62 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-132/README.md` | 当前变更尚未提交；原生 axe CLI Chrome/ChromeDriver 版本限制已如实记录；RC-127 实际位图导出、390px Review 既有三栏响应式问题和 RC-121/057/060 外部确认仍 pending |
| RC-133 | 2026-07-18 10:50:45 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：14 条独立路由 × light/dark × 1x/2x 共 56 组 Playwright 截图；`diff_ratio=0`、兔兔存在、横向溢出/裁切/内容重叠均为 0，主题字段与基线一致；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、62 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-133/README.md` | 当前变更尚未提交；本机原生 axe CLI 的 Chrome/ChromeDriver 版本限制、RC-127 实际位图导出和 RC-121/057/060 外部条件仍 pending；390px Review 既有三栏响应式问题留给 RC-255/256 |
| RC-134 | 2026-07-18 10:57:49 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：三种布局完成设计评审；锁定“上下文左、动作右”方案，明确模型/附件/语音 → 星星 → 发送的键盘/点击顺序、主次层级、按钮固定尺寸和三档响应式规则；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 15 test files、62 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-134/README.md` | 当前变更尚未提交；Trae 参考图未在当前工作树提供，已如实记录为评审假设；星星状态机、Tooltip、优化请求和结果交互留给 RC-135 至 RC-146；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-135 | 2026-07-18 11:06:51 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：新增优化按钮组件专项 4 passed、App 专项 11 passed；覆盖 idle/hover/pressed/loading/success/error/disabled/cancelling、取消、重复点击和请求 ID 过期结果保护；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 16 test files、66 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-135/README.md` | 当前变更尚未提交；仓库未配置 Storybook，已用 Vitest 组件测试替代并如实记录；Tooltip/完整可访问命名留给 RC-136；输入快照与边界处理留给 RC-137；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-136 | 2026-07-18 11:13:37 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：优化按钮与 App 专项共 16 passed；覆盖 500ms 延迟 Tooltip、鼠标悬停、键盘焦点、`aria-describedby`、`aria-label="优化输入内容"` 和 `data-action="prompt-optimize"`；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 16 test files、67 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-136/README.md` | 当前变更尚未提交；原生 axe CLI Chrome/ChromeDriver 版本限制和前端 jsdom navigation 警告保留；仓库未配置 Storybook；输入快照和空输入/附件/超长边界留给 RC-137；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-137 | 2026-07-18 11:22:03 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：优化按钮与 App 专项共 18 passed；覆盖空输入禁用、完整文本/revision/光标/附件快照、只有附件提示、12000 字符预算拒绝且不截断，以及既有取消/重复点击保护；登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 16 test files、69 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-137/README.md` | 当前变更尚未提交；并发编辑时旧结果不覆盖新输入留给 RC-138；仓库未配置 Storybook；原生 axe CLI Chrome/ChromeDriver 版本限制、RC-127/RC-121/057/060 外部条件仍 pending |
| RC-138 | 2026-07-18 11:31:26 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：组件与 App 专项共 19 passed；覆盖 AbortSignal 取消传播、延迟响应期间 revision 变化、旧结果不覆盖新输入、待比较提示、查看比较和重新优化入口；生成 API drift、lint 和登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 16 test files、70 passed；Ruff/Mypy、Lint/Build、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-138/README.md` | 当前变更尚未提交；当前比较面板先复用现有分析结果，结构化 diff/长文本虚拟化留给 RC-140；仓库未配置 Storybook；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-139 | 2026-07-18 11:38:26 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：App/组件/TaskWorkspace 专项共 23 passed；优化回包进入可编辑预览，未调用 tasks 发送路径，只有“采用优化结果”显式写回当前输入；生成 API drift、lint 和登记后 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 16 test files、71 passed；Ruff/Mypy、Lint/Build、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-139/README.md` | 当前变更尚未提交；结构化 diff、部分采用、撤销和长文本虚拟化留给 RC-140；仓库未配置 Storybook；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-140 | 2026-07-18 12:04:53 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：PromptOptimizationDiff/App 专项共 16 passed；覆盖 inline/side-by-side、长文本可视窗口、复制、整段/选区替换、重试、撤销和恢复原文；登记前 root verify 通过，后端 281 passed、5 skipped、31 warnings，前端 17 test files、74 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-140/README.md` | 当前变更尚未提交；词级 diff、结构化输入保护和 Provider 元数据展示留给 RC-141/RC-142；仓库未配置 Storybook；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-141 | 2026-07-18 12:22:56 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：metadata/fallback/脱敏专项 5 passed、App 专项 14 passed；Provider/模型/local-cloud/fallback/耗时/错误码和密钥引用展示通过；含 API key/System Prompt 的错误不会进入 metadata 或页面；登记前 root verify 通过，后端 283 passed、5 skipped、33 warnings，前端 17 test files、75 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage 和交付计划校验通过 | `docs/evidence/RC-141/README.md` | 当前变更尚未提交；结构化输入保护留给 RC-142；仓库未配置 Storybook；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-142 | 2026-07-18 12:52:45 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-142 专项 6 passed；结构化输入回归 38 passed、23 warnings；登记后 root verify 通过，后端 289 passed、5 skipped、37 warnings，前端 17 test files、75 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-142/README.md` | 当前变更尚未提交；真实云 Provider 的结构标记实测、附件上传协议和跨平台实机矩阵不属于本项；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-143 | 2026-07-18 13:07:53 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-143 专项 8 passed、2 warnings；组合回归 42 passed、23 warnings；登记后 root verify 通过，后端 297 passed、5 skipped、39 warnings，前端 17 test files、75 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-143/README.md` | 当前变更尚未提交；更广泛多语种识别与翻译质量评测留给后续国际化任务；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-144 | 2026-07-18 13:21:01 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-144 专项前端 16 passed；登记后 root verify 通过，后端 297 passed、5 skipped、39 warnings，前端 18 test files、77 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-144/README.md` | 当前变更尚未提交；控制参数持久化和历史采用状态留给 RC-146；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-145 | 2026-07-18 13:29:06 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-145 专项 19 passed；登记后 root verify 通过，后端 297 passed、5 skipped、39 warnings，前端 18 test files、79 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-145/README.md` | 当前变更尚未提交；更细粒度 shortcut 自定义、系统级快捷键和真实屏幕阅读器实机矩阵留给后续任务；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-146 | 2026-07-18 13:55:38 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-146 专项后端 4 passed、前端 2 passed；根级 verify 后端 301 passed、5 skipped、39 warnings，前端 19 test files、81 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过；v2 approved baseline 按 RC-146 显式记录导出字段变化 | `docs/evidence/RC-146/README.md` | 当前变更尚未提交；更细粒度 shortcut 自定义、系统级快捷键、真实屏幕阅读器实机矩阵、RC-127/RC-121/057/060 外部条件仍 pending |
| RC-147 | 2026-07-18 14:07:31 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-147 专项 3 passed；统一服务通过普通/流式/API/后台任务契约测试，Ruff/Mypy 目标检查通过；登记后根级 verify 后端 304 passed、5 skipped、39 warnings，前端 19 test files、81 passed；全量门禁通过 | `docs/evidence/RC-147/README.md` | 当前变更尚未提交；RC-152 的外部取消路由/SSE 重连、RC-148/149 Provider/本地模型选择仍待后续；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-148 | 2026-07-18 14:25:54 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-148 专项后端 3 个测试、相关前端 5 passed；Provider/model 选择优先级、健康回退、selection scope/health API 与历史持久化通过；根级 verify 后端 307 passed、5 skipped、39 warnings，前端 19 test files、82 passed；全量门禁通过 | `docs/evidence/RC-148/README.md` | 当前变更尚未提交；RC-149 本地模型 Adapter、RC-150 离线细化、RC-152 外部取消路由/SSE 重连仍待后续；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-149 | 2026-07-18 14:38:43 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：RC-149 专项后端 2 passed、前端相关回归 8 passed；登记后根级 verify 后端 309 passed、5 skipped、39 warnings，前端 19 test files、82 passed；local runner Adapter、健康、流式输出和无网络 route 通过；全量门禁通过 | `docs/evidence/RC-149/README.md` | 当前变更尚未提交；RC-150 已完成；RC-152 外部取消路由/SSE 重连仍待后续；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-150 | 2026-07-18 14:53:08 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：local 未安装、未就绪、OOM、超时和普通 RuntimeError 边界测试通过；RC-150 专项后端 16 passed、前端 2 test files/18 passed；根级 verify 后端 318 passed、5 skipped、39 warnings，前端 19 test files、82 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-150/README.md` | 当前变更尚未提交；真实 Gemma/Qwen runtime 与模型权重安装仍留给后续本地模型任务；RC-152 外部取消路由/SSE 重连、RC-127/RC-121/057/060 外部条件仍 pending |
| RC-151 | 2026-07-18 15:05:10 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：授权门禁、未授权零 HTTP、同 request ID 幂等重试、限流、熔断 open/half-open/closed 和取消传播专项 26 passed；根级 verify 后端 324 passed、5 skipped、39 warnings，前端 19 test files、82 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-151/README.md` | 当前变更尚未提交；RC-152 已完成；RC-127/RC-121/057/060 外部条件仍 pending |
| RC-152 | 2026-07-18 15:32:02 +08:00 | 未提交工作树（HEAD `5610c00`） | PASS：canonical v1 started/analysis/delta/saved/completed/cancelled/error 事件、序号、游标回放和不重复保存专项 25 passed；前端相关 2 test files/17 passed、生产构建成功；根级 verify 后端 329 passed、5 skipped、44 warnings，前端 19 test files、82 passed；Ruff/Mypy、Lint/Build、生成 drift、追踪、依赖边界、route coverage、视觉/Token 门禁和交付计划校验通过 | `docs/evidence/RC-152/README.md` | 当前变更尚未提交；event log 为单进程 bounded 内存存储，跨进程持久化和 worker 协调留给后续；RC-127/RC-121/057/060 外部条件仍 pending |

| RC-154 | 2026-07-18 16:52:24 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：优化目标经 API/GUI/同步/流式/后台任务传递；离线规则和云 adapter 均仅将目标作为用户上下文；全关闭目标返回 HTTP 400；生成 drift、追踪、Ruff、Mypy、编译、RC-154 3 passed、前端 Lint/TypeScript 通过 | docs/evidence/RC-154/README.md | 完整 Vite 构建受沙箱拒绝读取祖先目录阻断；.venv 指向失效 Store Python，使用 bundled Python 验证；全量 Ruff 仍有既有 RC-153 测试 import 排序问题 |
| RC-155 | 2026-07-18 17:03:48 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：rules/model/combined 经共享 Service；规则建议和模板只进入云 adapter 用户上下文；rules 强制离线，云模型失败保留既有离线降级；组合模式质量阈值和原文保留消融测试通过；RC-154/155 7 passed、Ruff、Mypy、编译、生成 drift、前端 Lint/TypeScript 通过 | docs/evidence/RC-155/README.md | 完整 Vite 构建仍受沙箱读取祖先目录限制；.venv 的 Store Python 已失效，验证使用 bundled Python；全量 Ruff 的既有 RC-153 测试 import 排序问题保留 |
| RC-156 | 2026-07-18 17:08:57 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：控制字符一次清理、空值/长度、结构和语言验证接入同步、流式和保存路径；无效结构输出不保存版本；RC-154/155/156 10 passed、Ruff、Mypy、编译、生成 drift、前端 Lint/TypeScript 通过 | docs/evidence/RC-156/README.md | 完整 Vite 构建仍受沙箱读取祖先目录限制；.venv 的 Store Python 已失效，验证使用 bundled Python；全量 Ruff 的既有 RC-153 测试 import 排序问题保留 |
| RC-157 | 2026-07-18 17:12:57 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：metadata 记录质量前后分与差值、Provider、模型、延迟和降级；不包含完整提示词；RC-157 1 passed、Ruff、Mypy、编译、生成 drift、前端 Lint/TypeScript 通过 | docs/evidence/RC-157/README.md | 完整 Vite 构建仍受沙箱读取祖先目录限制；.venv 的 Store Python 已失效，验证使用 bundled Python；全量 Ruff 的既有 RC-153 测试 import 排序问题保留 |
| RC-158 | 2026-07-19 01:29:15 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：60 个评测样本覆盖编码、商务、教育、创意、长文本、代码块、变量、中文和对抗输入；固定 `rc-158-v1`/种子 158；自动评分与双人盲评协议及稳定批次报告通过；RC-158 专项 3 passed、Ruff、Mypy 通过 | docs/evidence/RC-158/README.md | bundled Python 缺少测试/静态检查依赖；`.venv` 直接 Python 可用；CLI 入口缺 `rabbit_code` 源码路径，基线使用源码路径生成；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-159 | 2026-07-19 01:36:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：首次启动使用 API 路线明确为配置 Provider；Provider API Key 与 Rabbit Code 账户密码明确区分；真实账户页保留 ACCOUNT LOGIN；前端专项 3 passed、ESLint、TypeScript 通过 | docs/evidence/RC-159/README.md | 根目录 Vitest 扫描既有 `.runtime/pytest-rc154` 目录受 EPERM，专项已从 `frontend` 目录通过；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-160 | 2026-07-19 01:42:25 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：OpenAI Chat Completions Adapter 支持标准 Base URL、API Key、模型、组织/项目头、messages、SSE、工具定义/工具调用和 401/429/504 错误映射；RC-160 与既有 Provider/RC-151 回归 20 passed、Ruff、Mypy 通过 | docs/evidence/RC-160/README.md | 完整 Vite 构建仍受沙箱目录权限限制；未进行真实收费 Provider 请求，仅使用 Mock 契约 |
| RC-161 | 2026-07-19 01:46:30 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Responses API 使用独立 Adapter 和显式协议选择；请求/响应/流式事件支持 `instructions/input/text`、工具调用和结构化输出，Chat 参数不泄漏；RC-160/161 与既有 Provider 回归 23 passed、Ruff、Mypy 通过 | docs/evidence/RC-161/README.md | 未进行真实收费 Provider 请求，仅使用 Mock 契约；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-162 | 2026-07-19 01:51:39 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Gemini 原生 Adapter 支持 `generateContent`/`streamGenerateContent`、contents/parts、System Instruction、function calling、安全设置、错误结构和 `x-goog-api-key`；RC-160/161/162 与既有 Provider 回归 26 passed、Ruff、Mypy 通过 | docs/evidence/RC-162/README.md | 未进行真实收费 Provider 请求，仅使用 Mock 契约；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-163 | 2026-07-19 01:56:16 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Anthropic Messages Adapter 支持版本/Beta 头、system/content blocks、tool use/result、SSE 事件、usage、prompt caching 和 capability probe；RC-160/161/162/163 与既有 Provider 回归 29 passed、Ruff、Mypy 通过 | docs/evidence/RC-163/README.md | 未进行真实收费 Provider 请求，仅使用 Mock 契约；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-164 | 2026-07-19 02:00:04 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Claude Code 格式映射到 Anthropic Messages/官方 Agent SDK；官方 API Key/OAuth 允许，Cookie/订阅 Token/内部令牌/未知格式拒绝；后端边界与 Anthropic 回归 16 passed、Ruff、Mypy，Provider 页面 3 passed、ESLint、TypeScript 通过 | docs/evidence/RC-164/README.md | 不实现非官方 Claude Code 订阅登录，不捆绑或分发 Claude Code CLI；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-165 | 2026-07-19 02:06:16 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Azure、Vertex、Bedrock 托管变体支持部署/版本、项目/区域、API Key/Bearer/SigV4 signer 边界和独立 endpoint；RC-160 至 RC-165 与既有 Provider 回归 40 passed、Ruff、Mypy 通过 | docs/evidence/RC-165/README.md | 未进行真实 Azure/Vertex/Bedrock 请求或收费验证；Bedrock 生产使用需注入官方 AWS SigV4 signer；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-166 | 2026-07-19 02:15:43 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：数据驱动 Provider Preset 覆盖 11 个主流 OpenAI 兼容服务，支持默认 Base URL、模型发现路径、兼容级别、限制说明、自定义头和环境变量覆盖；RC-160 至 RC-166 联合回归 48 passed、Provider Ruff、Mypy 通过 | docs/evidence/RC-166/README.md | 未进行真实收费 Provider 请求；Ollama/LM Studio 仅定义兼容 Preset，真实本地服务发现留给 RC-168；完整 Vite 构建仍受沙箱目录权限限制 |
| RC-167 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：能力 schema v1、Adapter 静态能力矩阵、探测结果覆盖、TTL 缓存、探测失败静态回退、Agent 工具门控和 GUI 模型发现门控完成；RC-160 至 RC-167 联合回归 53 passed、Provider/Agent Mypy、Ruff、Python 编译、前端 23 个测试文件 109 passed、ESLint、Vite build 通过 | docs/evidence/RC-167/README.md | 未进行真实收费 Provider 请求；当前全量后端 646 passed、9 skipped、2 warnings |
| RC-168 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：ModelDiscoveryService 支持 Preset `/models` endpoint、cursor 分页、TTL 缓存、空列表、超时、403、限流/服务错误分类；Registry 复用发现服务，手动/已保存模型在发现失败时保留；RC-160 至 RC-168 联合回归 57 passed、前端 23 个测试文件 109 passed、Ruff、Mypy、ESLint、Vite build 通过 | docs/evidence/RC-168/README.md | 未向真实 Provider 发送请求；未维护模型白名单，真实连接测试与费用提示留给 RC-169 |
| RC-169 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：Mock-first 分阶段连接检查覆盖凭据、模型、能力、流式首块和工具 schema；真实模式要求自有 Provider 凭据、明确确认、费用警告、token 上限和注入的官方发送器；RC-160 至 RC-169 联合回归 62 passed、前端 23 个测试文件 109 passed、Provider/Agent Mypy、Ruff、Python 编译、ESLint、Vite build 通过 | docs/evidence/RC-169/README.md | 默认不发送真实请求且未产生 Provider 费用；真实连接仅在显式 `real + confirmed` 且运行时注入发送器时执行 |
| RC-170 | 2026-07-19 03:14:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：统一 11 类 Provider 错误分类、状态码/错误体映射、脱敏 request ID、API/流式/CLI/UI 共享错误呈现；RC-160 至 RC-170 联合 Provider/API 回归 78 passed、RC-170 专项 18 passed、前端全量 20 个测试文件 87 passed、ESLint、TypeScript/Vite build、OpenAPI drift、Provider Ruff/Mypy、Python 编译通过 | docs/evidence/RC-170/README.md | 未发送真实 Provider 请求且未产生费用；既有 jsdom navigation 与路径迁移 warning 保留；完整工作树仍包含此前 RC 的未提交改动 |
| RC-171 | 2026-07-19 03:21:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：指数退避、抖动、数字/HTTP-date `Retry-After`、取消中断、HTTP(S) 代理、NO_PROXY、自定义 CA、IPv4/IPv6 和 opaque 代理凭据 resolver 完成；RC-160 至 RC-171 联合 Provider/API 回归 90 passed、RC-171 专项 6 passed、Provider Ruff/Mypy、Python 编译通过 | docs/evidence/RC-171/README.md | 未发送真实 Provider 请求且未产生费用；代理凭据仍需运行时 SecretStore resolver；既有迁移 warning 保留 |
| RC-172 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：路由持久化/优先级、独立优化模型、不可用路由 fallback chain、发送前 Token/费用预算拦截和流式降级 metadata 完成；RC-160 至 RC-172 联合 Provider/API 回归 92 passed、RC-172 专项 6 passed、Provider Ruff、工作区严格 Mypy、Python 编译、OpenAPI drift、前端 23 个测试文件 109 passed、ESLint 和 Vite build 通过 | docs/evidence/RC-172/README.md | 未发送真实 Provider 请求且未产生费用；迁移 warning 保留 |
| RC-173 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：共享 MockTransport 契约覆盖 Chat Completions、Responses、Gemini、Anthropic、Azure、Vertex、Bedrock、offline 和 local Provider；录制器脱敏 credential header；真实测试要求 owned key、显式启用、费用确认和 Token limit；RC-160 至 RC-173 联合 Provider/API 回归 107 passed、2 skipped，RC-173 专项 15 passed、2 skipped，追踪 19 passed、2 skipped，workspace check 通过 | docs/evidence/RC-173/README.md | 未发送真实 Provider 请求且未产生费用；最终后端全量 646 passed、9 skipped、2 warnings |
| RC-174 | 2026-07-19 04:14:56 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：首次运行页保留两个等权无预选入口，明确 API/本地数据去向、网络和凭据/硬件边界；修复移动 CSS cascade；前端 20 个测试文件 87 passed、ESLint、TypeScript、Vite build、Playwright 桌面/移动视口检查通过 | docs/evidence/RC-174/README.md | 后端未启动时浏览器 health 代理显示 unavailable；既有 jsdom navigation warning 保留 |
| RC-175 | 2026-07-19 04:31:11 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：API 向导四步覆盖协议/服务商、Base URL、Key、模型、Mock `$0` 连接测试和测试后默认保存；非敏感草稿写入 workspace localStorage，Key 不落盘；前端 20 个测试文件 88 passed、ESLint、TypeScript、Vite build、Playwright 桌面/移动视口通过 | docs/evidence/RC-175/README.md | 当前连接测试为 Mock-first；OS SecretStore/OAuth 留给 RC-179/RC-182；既有 jsdom navigation warning 保留 |
| RC-176 | 2026-07-19 04:47:26 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：无 API 安装向导覆盖硬件、运行器、模型、许可证、可恢复下载、校验和和健康检查；RC-176 专项 7 passed、前端全量 20 个测试文件 89 passed、ESLint、TypeScript、Vite build、Playwright 桌面/移动视口通过 | docs/evidence/RC-176/README.md | 真实 Ollama/llama.cpp 运行器和多 GB 下载留给后续运行时 RC；既有 jsdom navigation warning 保留 |
| RC-177 | 2026-07-19 05:04:17 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：两条向导完成态统一进入既有 workspace home；首页云/本地/离线模型选择和非敏感路由目录保持切换；RC-177 专项 14 passed、前端全量 20 个测试文件 90 passed、ESLint、TypeScript、Vite build、Playwright 桌面/移动视口通过 | docs/evidence/RC-177/README.md | 未发送真实 Provider 请求；项目/会话跨设备同步仍留给后续后端工作；既有 jsdom navigation warning 保留 |
| RC-178 | 2026-07-19 05:17:55 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Provider/模型配置支持 workspace 持久化 CRUD、禁用保留历史、默认/活跃引用删除迁移和本地模型状态/禁用；RC-178 专项 16 passed、前端全量 20 个测试文件 93 passed、ESLint、TypeScript、Vite build、Playwright 桌面/移动视口通过 | docs/evidence/RC-178/README.md | 未持久化 API Key，OS SecretStore 留给 RC-179；真实 Provider 请求未发送；既有 jsdom navigation warning 保留 |
| RC-179 | 2026-07-19 05:27:32 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：SecretStore 抽象、Windows Credential Manager、Linux Secret Service、opaque config reference、user 明文拒绝、session/CLI 临时凭据和删除清理完成；RC-179 专项 5 passed、RC-064/RC-179/Provider 回归 18 passed、Ruff、定向 Mypy、compileall 通过 | docs/evidence/RC-179/README.md | 当前仅 Windows 实机 round-trip；Linux Secret Service 代码路径因环境无 Linux/secret-tool 未实测，未伪造通过；既有全仓环境警告保留 |
| RC-180 | 2026-07-19 05:42:05 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：前端固定掩码/末尾四位、共享 API 错误格式化脱敏、导出与诊断复制清洗、后端公共 JSON/错误/Provider metadata 脱敏和运行时指纹完成；RC-180 专项 2 passed，后端 RC-064/RC-160 至 RC-173/RC-179/RC-180 联合回归 118 passed、1 skipped，前端全量 21 个测试文件 96 passed、ESLint、TypeScript/Vite build、定向 Ruff/Mypy、compileall 通过 | docs/evidence/RC-180/README.md | 未发送真实 Provider 请求且未产生费用；Linux Secret Service 未在当前 Windows 环境实测；既有 jsdom navigation stderr 保留 |
| RC-181 | 2026-07-19 05:54:54 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：`env:`/`keychain:` 引用、直接环境覆盖、default/user/workspace/env/session/CLI 优先级、环境变化重新解析、数值环境类型转换、只读配置 API 和 Provider 来源展示完成；RC-181 专项 4 passed，后端 RC-064/RC-160 至 RC-173/RC-179/RC-181 联合回归 122 passed、1 skipped，前端全量 21 个测试文件 97 passed、ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、定向 Mypy、compileall 通过 | docs/evidence/RC-181/README.md | 未发送真实 Provider 请求且未产生费用；环境迁移 warning 与 jsdom navigation stderr 保留；配置 API 仅返回来源和 opaque placeholder |
| RC-182 | 2026-07-19 06:01:21 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：OAuth 政策 allowlist、默认拒绝未获批准 Provider、系统浏览器 URL、S256 PKCE、state/redirect 校验、回调 loopback 清理、防重放、SecretStore opaque token、refresh/revoke 完成；RC-182 专项 4 passed，RC-064/RC-160 至 RC-173/RC-179/RC-182 联合回归 126 passed、1 skipped，Ruff、定向 Mypy、compileall 通过 | docs/evidence/RC-182/README.md | 当前没有已确认允许第三方客户端的 Provider 政策，因此默认批准列表为空；未进行真实 OAuth/Provider 请求；真实回调端口和官方政策确认留给具备外部条件的后续验证 |
| RC-183 | 2026-07-19 06:06:08 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：offline/local 路线无需 Rabbit Code 云账户即可运行；OptionalSyncService 默认关闭、启用后需单独账户授权；本地会话/模型/配置与账户、Provider SecretStore 边界分离；RC-183 专项 3 passed，RC-064/RC-160 至 RC-173/RC-179/RC-183 联合回归 129 passed、1 skipped，前端本地入口/工作区 7 passed、ESLint、TypeScript/Vite build、Ruff、定向 Mypy、compileall 通过 | docs/evidence/RC-183/README.md | 未发送真实 Provider 请求或同步请求；跨设备同步实现留给后续可选模块；既有环境迁移 warning 保留 |
| RC-184 | 2026-07-19 06:16:58 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：清理预览、单 Provider credential 删除、opaque 配置迁移、全量本地数据删除、确认/取消、进程停止 guard、文件安全擦除、SecretStore 引用清除和 Settings UI 预览/确认完成；RC-184 清理/API 合约专项 10 passed，后端 RC-064/RC-160 至 RC-173/RC-179 至 RC-184 联合回归 139 passed、1 skipped，前端全量 21 个测试文件 98 passed、ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、定向 Mypy、compileall 通过 | docs/evidence/RC-184/README.md | 未发送真实 Provider 或同步请求；默认 API cleanup 仍需进程 guard/明确确认；既有环境迁移 warning 与 jsdom navigation stderr 保留 |
| RC-185 | 2026-07-19 06:31:20 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：LocalInstallCore 可重入下载/暂停/恢复/取消/校验/原子安装/runner 状态和结构化 JSON 事件完成；PowerShell/Shell 薄包装与 GUI 同字段事件映射完成；RC-185 专项 4 passed，RC-149/RC-185 关联回归 15 passed，前端全量 21 个测试文件 98 passed，ESLint、TypeScript/Vite build、定向 Ruff/Mypy、compileall、diff check 通过 | docs/evidence/RC-185/README.md | Windows PowerShell 包装已实测；当前环境无 sh/bash，Linux 包装未实测；使用模拟源，真实模型下载/网络重试留给 RC-191；既有 migration/jsdom warning 保留 |
| RC-186 | 2026-07-19 06:42:02 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：HardwareDetector/HardwareReport 和 JSON CLI 覆盖 OS/架构、CPU、RAM、磁盘、GPU/显存/驱动、网络、代理、Ollama/llama.cpp runner、source/confidence、权限降级和用户 override；RC-186 专项 3 passed，RC-149/RC-185/RC-186 关联回归 18 passed，前端全量 21 个测试文件 98 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-186/README.md | 当前未执行 Linux 实机硬件/runner 矩阵；网络只做 DNS 探测；纠正值为单次 CLI override，真实推荐和持久化留给后续 RC |
| RC-187 | 2026-07-19 06:47:16 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Ollama 默认与 llama.cpp 替代共享 LocalRunnerAdapter 全生命周期契约；RunnerRegistry、比较矩阵和 ADR-0014 完成；RC-187 专项 2 passed，RC-149/RC-187 关联回归 13 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-187/README.md | 仅使用内存契约适配器，真实 runner 进程/API 留给后续模型健康和资源 RC；当前无网络请求或权重下载 |
| RC-188 | 2026-07-19 06:53:37 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：版本化受控模型 manifest、Gemma/Qwen 固定来源和资源元数据、schema 校验、80% 安全余量推荐、未知模型 advanced gate 和 CLI 检查完成；RC-188 专项 3 passed，RC-186/RC-187/RC-188 联合专项 8 passed，Ruff、严格 Mypy、compileall、diff check 通过 | docs/evidence/RC-188/README.md | 未下载/打包权重；Gemma 下载前仍需用户许可确认；真实模型模板/生成冒烟留给 RC-189/190/193 |
| RC-189 | 2026-07-19 07:00:35 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Qwen2.5-Coder family/完整 model ID/固定 revision/hash、默认 runner health 与 LocalModelProvider generation smoke、GUI 完整 ID 展示完成；RC-188/RC-189 后端 4 passed，前端 Qwen 专项 5 passed、全量 21 个测试文件 98 passed，ESLint、TypeScript/Vite build、Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-189/README.md | 使用无网络内存 runner，真实权重/runner 进程未执行；Gemma 版本与许可证/模板审核留给 RC-190 |
| RC-190 | 2026-07-19 07:05:30 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Gemma 3 1B IT 固定 ID/revision/hash、Gemma family、gemma-3 template、EOS、模型卡/许可证约束、fail-closed selector、runner health/generation smoke 和 GUI 版本对齐完成；RC-186 至 RC-190 后端 10 passed，前端全量 21 个测试文件 98 passed，ESLint、TypeScript/Vite build、Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-190/README.md | 使用无网络内存 runner，真实权重/模型卡全文/runner 模板实机未执行；Gemma gated 条款仍要求下载前确认 |
| RC-191 | 2026-07-19 07:20:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：可靠下载器补充版本/镜像/代理元数据、指数退避、失败恢复、错误哈希 fail-closed、同根目录进程内并发写保护和 CLI 参数；RC-185/RC-191 专项 8 passed，相关后端回归 172 passed、2 skipped，Ruff、严格 Mypy、compileall、分发检查通过 | docs/evidence/RC-191/README.md | 使用本地模拟源和 `seek` Range 续传；真实 HTTP、镜像切换、代理、Linux 实机和跨进程锁未执行 |
| RC-192 | 2026-07-19 07:20:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：manifest 分发策略、许可证摘要/HTTPS URL/确认版本、安装状态记录、下载前确认校验和权重 denylist/workspace 门禁完成；RC-192 专项 3 passed，RC-188/RC-191/RC-192 联合专项 14 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-192/README.md | 未生成真实安装包或 SBOM；denylist 已验证当前源码树无权重，发布流水线产物审计仍留待打包阶段 |
| RC-193 | 2026-07-19 07:30:00 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：健康检查覆盖 runner 版本、加载、最小生成、流式增量、取消、上下文、停止后重载和资源峰值；健康报告原子保存且不含提示词，健康门控安装按报告通过/失败进入 ready/failed；RC-193 专项 8 passed，RC-149 至 RC-193 回归 190 passed、2 skipped、50 warnings，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-193/README.md | 使用 in-memory runner 和注入资源探针；真实 Ollama/llama.cpp、tokenizer 极限、权重加载和多平台资源实测留给后续运行时验证 |
| RC-194 | 2026-07-19 07:58:39 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：本地模型状态机拒绝不可能跳转；安装事件映射为下载/校验/加载/就绪/忙碌/卸载/损坏/更新状态；FastAPI 事件端点跨新 App 实例恢复；GUI 消费后端恢复事件并为 failed/corrupt 提供 retry/repair/uninstall；RC-194 专项 7 passed，RC-185/RC-191/RC-194 关联 16 passed、2 warnings，前端本地模型专项 6 passed，ESLint、TypeScript/Vite build、Ruff、OpenAPI drift 通过 | docs/evidence/RC-194/README.md | 真实 Ollama/llama.cpp 进程、模型权重和多平台实机未执行；既有路径迁移 warning 保留 |
| RC-195 | 2026-07-19 08:12:37 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：全局默认本地模型写入，session/task 查询参数隔离会话覆盖；Gemma/Qwen 切换检查 ready/busy 与上下文长度，生成中禁用切换；实际 optimize body、metadata 和历史分别保留 Qwen/Gemma ID；RC-195 专项后端 1 passed、前端 3 passed，RC-148/RC-172 关联后端 10 passed、8 warnings，App/Workspace/Task/LocalModels 前端 28 passed，ESLint、TypeScript/Vite build 通过 | docs/evidence/RC-195/README.md | 未执行真实模型权重/runner 进程；既有路径迁移与 jsdom navigation warning 保留 |
| RC-196 | 2026-07-19 08:19:43 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：RunnerResourceConfig、安全默认、CPU-only/GPU 配置、OOM 卸载降配、idle timeout 释放和 Provider 单次恢复完成；RC-196 关联专项 21 passed、11 warnings，定向 Ruff、严格 Mypy 通过 | docs/evidence/RC-196/README.md | 当前未执行真实 GPU、Ollama/llama.cpp 进程和跨平台资源实机；既有路径迁移 warning 保留 |
| RC-197 | 2026-07-19 08:34:02 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：ModelDirectoryService 完成自定义目录检查、版本更新/保留、迁移校验与中断保护、回滚、修复、清理和登记文件卸载；FastAPI/OpenAPI/GUI 接线完成；RC-197 专项 6 passed，关联后端 28 passed、5 warnings，前端 22 个测试文件 102 passed，Ruff、严格 Mypy、ESLint、TypeScript/Vite build、OpenAPI drift 通过 | docs/evidence/RC-197/README.md | 未执行真实 Ollama/llama.cpp、模型权重、GPU 和跨进程故障注入；既有路径迁移与 jsdom navigation warning 保留 |
| RC-198 | 2026-07-19 08:46:30 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：LocalRunnerGateway 完成 runner 生命周期、能力信息、健康 TTL、bounded concurrency、request ID 取消和结构化流式事件；FastAPI list/capabilities/health/generate/stream/cancel/load/unload 路由及 OpenAPI 生成完成；RC-198 专项 5 passed，关联后端 38 passed、1 skipped、17 warnings，前端 22 个测试文件 102 passed，Ruff、严格 Mypy、ESLint、TypeScript/Vite build、OpenAPI drift 通过 | docs/evidence/RC-198/README.md | 未执行真实 Ollama/llama.cpp、runner HTTP、模型权重、GPU 和跨进程故障注入；既有 RC-153 Ruff import 排序阻塞、路径迁移与 jsdom navigation warning 保留 |
| RC-199 | 2026-07-19 08:54:33 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：用户级安装策略、默认用户模型根、不可写目录拒绝、显式提权确认和无提权平台包装器完成；RC-199 专项 5 passed，RC-185/RC-191/RC-199 关联 14 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-199/README.md | 未执行真实标准用户受保护系统目录安装、外部包管理器或 runner 二进制提权；PATH 持久化和正式打包留待发布阶段 |
| RC-200 | 2026-07-19 09:03:46 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：离线介质布局、受控 manifest/版本/许可证/依赖/磁盘/哈希校验、手动导入、原子安装和复用健康检查完成；RC-200 专项 4 passed，RC-185/RC-188/RC-191/RC-192/RC-193/RC-200 关联 20 passed，manifest/分发扫描、Ruff、严格 Mypy、compileall、`workspace.py check` 通过 | docs/evidence/RC-200/README.md | 未执行真实离线虚拟机、真实 runner/权重和 GPU；CLI 使用内存 runner 与确定性资源探针，真实介质/发布包验证留待发布阶段 |
| RC-201 | 2026-07-19 09:15:47 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：Plan/Edit/High × files/terminal/network/git/mcp/desktop 六域 capability matrix 完成，并接入 FileTools、ShellAdapter、ProcessTools、GitTools、ToolRegistry；RC-201 及关联权限/工具回归 51 passed、3 skipped，Ruff、严格 Mypy 通过 | docs/evidence/RC-201/README.md | 未执行真实 OS 沙箱、桌面/MCP 进程和跨平台 capability 容器；既有平台 skip 保留 |
| RC-202 | 2026-07-19 09:32:40 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：`PermissionApprovalEngine` 生成完整共享审批快照，`ToolRegistry` 在批准前冻结执行并防止参数替换；拒绝/超时/重复执行均无 handler 副作用；RC-202/RC-201/RC-097/RC-101 后端 23 passed，前端 UiStates 8 passed，Ruff、严格 Mypy、ESLint、TypeScript/Vite build 通过 | docs/evidence/RC-202/README.md | 未执行真实 OS 沙箱、桌面/MCP/外部网络操作；保持既有平台 skip 和未提交工作树记录 |
| RC-203 | 2026-07-19 09:40:07 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：`AuthorizationStore` 支持一次/会话/结构化规则授权、拒绝、编辑重审、查看和撤销；RC-203/RC-202/RC-097 专项回归 15 passed，Ruff、严格 Mypy 通过；默认 UI 未增加永久授权入口 | docs/evidence/RC-203/README.md | 未执行跨进程授权持久化、真实 OS 沙箱、桌面/MCP/外部网络操作；留给后续集成和平台 RC |
| RC-204 | 2026-07-19 09:50:11 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：`SandboxReport`/`SandboxController` 平台能力探测、Linux bwrap 规格、Windows Job Object 非等价说明、reduced 审批和 ProcessManager spawn 前接入完成；RC-204/RC-094 9 passed、1 skipped，Ruff、严格 Mypy 通过 | docs/evidence/RC-204/README.md | 未执行真实 Linux bwrap/seccomp、Windows AppContainer/ACL 或 OS 逃逸夹具；保持平台条件限制记录 |
| RC-205 | 2026-07-19 09:55:56 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：路径/命令/环境/工具输出安全边界完成并接入 ShellAdapter/ProcessManager；RC-205 及 RC-091/RC-094/RC-097/RC-201 关联 41 passed、4 skipped，Ruff、严格 Mypy 通过 | docs/evidence/RC-205/README.md | 未执行真实恶意仓库、外部命令注入或 OS 逃逸；Shell script 仍由现有 High/approval gate 控制，敏感文件专项留给 RC-206 |
| RC-206 | 2026-07-19 10:01:35 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：敏感路径策略、独立读/发送审批、FileTools 索引隔离、用户规则和 metadata-only SecretScanner 完成；RC-206/RC-090 7 passed、1 skipped，Ruff、严格 Mypy 通过 | docs/evidence/RC-206/README.md | 未执行真实凭据、浏览器资料、系统目录或 Provider send；扫描器覆盖和完整审计留后续安全 RC |
| RC-207 | 2026-07-19 10:07:45 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：strict loopback/Host/Origin/token/protocol/body/CORS 边界完成并由 sidecar 启用；RC-207/RC-058/RC-067 11 passed，Ruff、严格 Mypy 通过 | docs/evidence/RC-207/README.md | 未执行真实端口扫描或外部网络暴露；chunked body streaming 上限留后续上传边界 |
| RC-208 | 2026-07-19 10:19:10 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：扩展 manifest 来源/版本/hash/权限、显式确认、锁定、禁用、撤销和隔离上下文完成；RC-208/RC-077/RC-099/RC-075/RC-076 25 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-208/README.md | 未执行真实第三方扩展进程、凭据访问或 OS 级沙箱；实际下载制品 HTTPS/许可证/哈希流程留 RC-209 |
| RC-209 | 2026-07-19 10:25:36 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：共享制品 manifest 与下载器完成 binary/model/update/plugin 的 HTTPS、许可证、版本、SHA-256、失败清理和原子安装；RC-209/RC-188/RC-191/RC-192/RC-200/RC-077 28 passed，Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-209/README.md | 未执行真实外部 HTTP 下载；真实下载网络、代理和发布升级产物留后续发布/平台矩阵 |
| RC-210 | 2026-07-19 10:34:57 +08:00 | 未提交工作树（HEAD 5610c00） | PASS：默认关闭遥测、显式 opt-in/撤回/清除、内容过滤、诊断预览/脱敏/确认发送和 GUI 预览流程完成；后端 RC-210/RC-093/RC-180 9 passed，前端 Diagnostics 4 passed，Ruff、严格 Mypy、compileall、ESLint、TypeScript/Vite build 通过 | docs/evidence/RC-210/README.md | 未执行真实网络发送；遥测服务端点、崩溃收集器和实际外部支持渠道留后续部署配置 |
| RC-211 | 2026-07-19 10:50:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：数据流/STRIDE 威胁模型、私密报告渠道、漏洞分级与 SLA、密钥轮换、秘密扫描、Dockerfile 规则、CycloneDX SBOM 漂移门禁和 CI 依赖审计已完成；`scripts/security_scan.py --check` 与 RC-211 专项 3 passed；Ruff、严格 Mypy、compileall 通过 | docs/evidence/RC-211/README.md | 本地无 `pip-audit`、`syft`、`trivy`、`grype`、`gitleaks`，真实依赖漏洞数据库和容器镜像扫描由 CI 环境执行；未进行真实外部 Provider 请求 |
| RC-212 | 2026-07-19 11:59:17 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：独立 SQLite 审计日志支持 permission/tool/config/external request 最小元数据、UTC 时间/主体/结果、会话查询、持久化保留期、过期清理、按会话/全量物理清除和删除后哈希链重建；RC-212 专项 5 passed，RC-211/RC-212 联合 8 passed，Ruff、严格 Mypy、compileall、security baseline、traceability check 通过 | docs/evidence/RC-212/README.md | 当前仅完成服务边界和后端契约，GUI/API 查询展示留给后续可观测性接线；未进行多进程压力、真实崩溃故障注入 |
| RC-213 | 2026-07-19 12:12:50 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：统一 JSON schema、10 个核心实体、生命周期/作用域/删除/版本字段、关系与索引、Mermaid ER 图、SQLite 迁移初稿、Pydantic 模型和 TypeScript 接口完成；RC-213 专项 2 passed，迁移临时执行、生成 drift、Ruff、严格 Mypy、workspace.py check、TypeScript/Vite build 通过 | docs/evidence/RC-213/README.md | StorageService 仍保持 RC-054 schema v1；0002 只作为初始迁移草案，正式迁移/事务/并发/备份/恢复由 RC-214 继续完成 |
| RC-214 | 2026-07-19 20:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：SQLite 版本 2 迁移 runner、BEGIN IMMEDIATE 锁、启动 integrity check、WAL/busy timeout/foreign key/synchronous、关键索引、复合事务、迁移回滚和损坏库拒绝完成；最终后端全量 646 passed、9 skipped、2 warnings，前端 23 文件 109 passed，Ruff、严格 Mypy、生成 drift、workspace check 通过 | docs/evidence/RC-214/README.md | 未执行真实多进程崩溃断电或跨平台文件系统矩阵 |
| RC-215 | 2026-07-19 12:35:47 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：v1 JSON 日志 schema、结构化 Pydantic 事件、request/session/tool/task 关联、字段级 allowlist 脱敏和 CI/workspace 门禁完成；RC-215 专项 3 passed，结构化日志门禁、RC-211 security baseline、Ruff、严格 Mypy、traceability、workspace check 通过 | docs/evidence/RC-215/README.md | 现有公开输出脱敏接口保持兼容，结构化 emitter 作为统一日志边界；未接入外部日志收集端点，未发送真实 Provider 请求 |
| RC-216 | 2026-07-19 12:55:12 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：`ExecutionDestination`、execution-destination API、优化 metadata 目标信息和 Composer 请求前 local/cloud 目标提示完成；RC-216 专项 2 passed、API/相关回归 25 passed、前端 22 个测试文件 104 passed，ESLint、TypeScript、Vite build 和 workspace 检查通过 | docs/evidence/RC-216/README.md | 未发送真实 Provider 请求；自定义端点/真实云区域说明留 RC-217 补齐，真实外部网络与跨平台 UI 矩阵未执行 |
| RC-217 | 2026-07-19 13:11:39 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：11 个 Provider Preset 的 `rc217-v1` 隐私目录、发送字段/区域/官方政策链接/保留风险、自定义端点责任标识和配置/首次使用页展示完成；RC-217 专项 2 passed，相关后端回归 49 passed，前端 22 个测试文件 105 passed，ESLint、严格 Mypy、Vite build、OpenAPI drift、traceability、workspace check 通过 | docs/evidence/RC-217/README.md | 具体保留/训练政策仍以 Provider 当前官方政策和账号条款为准；未发送真实 Provider 请求，未执行跨平台原生 UI 矩阵 |
| RC-218 | 2026-07-19 13:31:50 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：默认 retention policy、日志轮转/总量回收、缓存回收、终态任务/Prompt history 保留、运行中任务保护、预览/确认 API 和 Settings 接入完成；RC-218 专项 4 passed、相关后端回归 32 passed、前端 22 个测试文件 106 passed，ESLint、严格 Mypy、Vite build、OpenAPI drift、traceability、workspace check 通过 | docs/evidence/RC-218/README.md | 未执行跨平台文件锁/断电故障矩阵或真实后台调度线程；轮转和回收由确认后的本地 retention service 执行，运行中资源由 process guard 与 active/tmp/lock 文件保护 |
| RC-219 | 2026-07-19 13:50:45 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：`rc219-v1` 本地指标聚合器、请求/首 Token/usage/失败率/工具/模型加载/资源采集、metrics API、固定单位文档和敏感标签拒绝完成；RC-219 专项 4 passed、Provider/RC-216 相关回归 20 passed、1 skipped、前端 22 个测试文件 106 passed，ESLint、严格 Mypy、Ruff、Vite build、traceability、workspace check 通过 | docs/evidence/RC-219/README.md | 未实现外部遥测上传；CPU 利用率和 GPU 采样按平台能力可为空，真实 Provider/tool execution 和跨平台硬件矩阵未执行，留 RC-220/后续平台 RC |
| RC-220 | 2026-07-19 14:02:45 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：默认关闭遥测、`rc220-v1` consent 版本、匿名技术字段说明、撤回/清除和 Settings 隐私控制完成；RC-210/RC-220 后端 8 passed，前端 22 个测试文件 107 passed、Settings 7 passed，Ruff、严格 Mypy、ESLint、Vite build 通过 | docs/evidence/RC-220/README.md | 未接入或依赖遥测后端；本地环境未执行真实网络发送，当前清除动作覆盖本地预留待发送队列键 |
| RC-221 | 2026-07-19 14:20:50 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：`rc221-v1` JSON/ZIP 可移植格式、会话/消息/Prompt/模板/非敏感设置、密钥排除、schema/大小/路径/哈希校验和导入冲突预览完成；RC-221 与 RC-086/RC-089/存储导出回归 16 passed，编译、Ruff、严格 Mypy 通过 | docs/evidence/RC-221/README.md | 不直接改写数据库，调用方必须在预览后应用返回文档；未执行真实跨版本 Profile/桌面 UI 导入旅程，ZIP 与 clean-profile 等价性由服务契约测试覆盖 |
| RC-222 | 2026-07-19 20:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：`rc222-v1` 25 次固定离线基线完成；CLI、离线首 Token、搜索、diff、前端包体、GUI HTTP 冷/热启动、RSS、backend wheel 全部测量并通过预算 | docs/evidence/RC-222/README.md | GUI 探针仍是 frontend-dist HTTP harness，不冒充原生 Tauri 启动；跨平台原生矩阵由 RC-121/桌面联调覆盖 |
| RC-223 | 2026-07-19 14:39:01 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：`SafeSearchIndexer` 后台有界生产者/消费者、增量缓存、ignore/敏感/大小/二进制过滤和 cancellation handle 完成；RC-083/RC-223 4 passed、1 skipped，Ruff、`mypy --follow-imports skip`、compileall 通过 | docs/evidence/RC-223/README.md | 未执行真实百万文件仓库、跨进程索引压力或 Linux 文件系统矩阵；同步 API 保留，后台句柄只管理进程内索引生命周期 |
| RC-224 | 2026-07-19 20:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：共享数据限额、工具/上下文/日志/Diff 截断元数据、进程日志与 Diff 游标续读、附件超限拒绝完成；RC-224/RC-082/RC-096/存储导出回归 14 passed，Ruff、严格 Mypy、OpenAPI drift、追踪和 workspace 门禁通过 | docs/evidence/RC-224/README.md | 工具输出和文本上下文的游标是返回协议元数据，跨请求持久化读取留给后续 Agent/API 任务；未执行真实百万级输出、跨平台进程内存和桌面 UI 矩阵 |
| RC-225 | 2026-07-19 15:23:06 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：SQLite 任务启动对账、瞬态本地模型恢复、终端进程登记/日志恢复完成；RC-225/RC-094/RC-194/RC-198/API 回归 41 passed，Ruff、严格 Mypy 通过 | docs/evidence/RC-225/README.md | 任务标为失败并保留输入，不自动重跑；桌面壳无仓库内可运行制品，未执行真实 Ollama/llama.cpp、跨平台 kill/崩溃和桌面会话矩阵；FastAPI startup API 仍有框架弃用 warning |
| RC-226 | 2026-07-19 15:39:12 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：普通优化 request ID、App Server 取消端点、Provider/离线/LocalRunner 取消检查和 GUI AbortSignal 取消调用完成；RC-226/RC-147/RC-152/RC-096/RC-198 后端 20 passed，前端 7 passed，ESLint、TypeScript/Vite build、OpenAPI drift、Ruff、严格 Mypy 通过 | docs/evidence/RC-226/README.md | 取消后不写 Prompt history；Shell/Process 已有取消/强制终止原语但未建立独立 Agent 工具调度器；未执行真实云请求、桌面原生工具进程和跨平台 kill 矩阵 |
| RC-227 | 2026-07-19 20:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：七类故障注入均有有限重试/恢复动作/诊断码，Provider 最终网络失败进入熔断；RC-227 及 RC-197/RC-151/RC-171/RC-225/SQLite 回归 32 passed，目标 Ruff、Provider/SQLite/Storage 严格 Mypy、diff check 通过 | docs/evidence/RC-227/README.md | 未执行真实云 outage、企业代理、物理磁盘耗尽、跨进程数据库崩溃和桌面原生端口矩阵；工作区 Mypy 已按显式包根检查，框架和路径 warnings 保留 |
| RC-228 | 2026-07-19 16:15:08 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：硬件推导资源、runner 配置下发、队列状态、有限并发、空闲调低、温度/OOM 信号和 API 入口完成；联合回归 52 passed，目标 Ruff、runner 资源/Provider/Gateway 严格 Mypy、OpenAPI contract 通过 | docs/evidence/RC-228/README.md | 未执行真实 runner/GPU/温度和跨平台压力矩阵；温度/OOM 仍依赖外部 runner 可用信号，外部 runner 调度器不由本进程管理 |
| RC-229 | 2026-07-19 20:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：固定离线 benchmark、Commit/机器元数据、统计区间、噪声趋势 gate、回归注入阻断和 CI artifact 完成；RC-229 专项 3 passed，比较器严格 Mypy/Ruff 通过；25 次 current 实跑与 baseline 比较 exit 0，9 个共同指标无回归 | docs/evidence/RC-229/README.md | GUI 性能仍以 frontend-dist HTTP harness 记账，原生 Tauri 和跨平台桌面矩阵由平台联调负责 |
| RC-230 | 2026-07-19 20:57:21 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：新增 Agent Core 离线专项 8 passed，覆盖状态转换/工具调用循环构件/取消/幂等重试/预算/压缩/检查点恢复；目标 Ruff 通过 | docs/evidence/RC-230/README.md | 该项只验证现有 Agent Core 原语；真实 Provider、runner、网络、伪终端和跨平台实机留给后续对应 RC |
| RC-254 | 2026-07-19 21:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH HANDOFF：低保真信息架构、API/本地主旅程、Composer 和双入口线框完成；现有路由/组件静态映射通过 | docs/evidence/RC-254/README.md | 外部产品/设计/前后端/无障碍签字未在本会话发生，已明确列为发布前 handoff；继续 RC-255 |
| RC-255 | 2026-07-19 21:18:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：多尺寸高保真规格完成，覆盖 Desktop/Compact、2x、主题、长文案、中英文和 Composer 全状态；与 token/现有组件映射通过 | docs/evidence/RC-255/README.md | 真实截图、DOM 边界和布局偏移留给 RC-256；reference workspace 的局部 legacy palette 未在本项扩大重构 |
| RC-231 | 2026-07-19 21:02:54 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：共享 Mock Provider 契约覆盖 5 个 Adapter 的请求、工具、流式、未知字段和 auth/parameter 错误映射；RC-231 专项 15 passed，目标 Ruff 通过 | docs/evidence/RC-231/README.md | 未调用真实 API；真实 Provider 和协议变体由受控手动矩阵留待后续发布验证 |
| RC-232 | 2026-07-19 21:06:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：FastAPI 严格安全边界、SSE/WebSocket 事件、fallback、任务和本地 runner 路由专项 8 passed；目标 Ruff 通过 | docs/evidence/RC-232/README.md | 未执行真实外部 Provider、runner 进程、端口扫描或生产 WebSocket 客户端；保留既有路径迁移 warning |
| RC-233 | 2026-07-19 21:13:27 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：CLI text/JSON/JSONL、TTY/非 TTY、权限/取消/运行时退出码、会话参数、dry-run、终端矩阵和 subprocess 专项 11 passed；目标 Ruff 通过 | docs/evidence/RC-233/README.md | Linux shell/native interactive terminal 在当前 Windows 主机按能力门控，未伪造实机通过 |
| RC-256 | 2026-07-19 21:35:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：Playwright 1440x1100/390x844 截图与 DOM 检查通过；修复 Review 紧凑视口三栏裁切；console 0 errors/0 warnings | docs/evidence/RC-256/README.md | 证据覆盖 workspace/Review 当前运行页；RC-133 的 14 路由基线和原生 Tauri/物理设备矩阵仍为独立限制 |
| RC-257 | 2026-07-19 21:48:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：空输入边界、星星/发送主次、单活动请求锁、取消、revision 防覆盖和可编辑预览通过；前端 24 passed，Lint/Build 通过 | docs/evidence/RC-257/README.md | 未发送真实 Provider 请求；忙碌态第二次点击按设计取消，不创建第二请求 |
| RC-258 | 2026-07-19 22:02:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：工作页 Rabbit 装饰不遮挡密集工作信息；Task 紧凑布局修复；路由/Task/Review 15 passed，Playwright slot/边界/console 检查通过 | docs/evidence/RC-258/README.md | 外部真实设备和 Tauri 原生矩阵留平台验收；LocalModelSelection/PromptHistory 空输入回归修正由并行联调保留 |
| RC-244 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：共享工作区 revision、变更事件、Provider/模型/权限、Prompt 版本、文件摘要和乐观锁完成；专项 2 passed | docs/evidence/RC-244/README.md | 真实桌面壳、终端进程和外部 Provider 留平台/发布矩阵 |
| RC-245 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：Agent 事件可序列化/恢复，未知事件安全降级为终态；专项 2 passed | docs/evidence/RC-245/README.md | 原生 GUI/终端会话仍需平台实测 |
| RC-246 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH LIMITS：API 配置、连接、对话、星星优化、同 Provider 优化、采用和独立发送 Mock 旅程通过 | docs/evidence/RC-246/README.md | 未调用真实 API 或产生费用 |
| RC-247 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH LIMITS：无 API、Gemma/Qwen setup、健康、选择、对话和 FastAPI 优化 Mock 旅程通过 | docs/evidence/RC-247/README.md | 未下载权重或执行真实 CPU/GPU 生命周期 |
| RC-248 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：未安装、未就绪和 OOM 三类本地失败均回退离线规则；专项 3 passed 且无外部请求 | docs/evidence/RC-248/README.md | 故障为注入状态，真实模型进程留后续矩阵 |
| RC-249 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：草稿按 workspace 持久化 revision/cursor/attachments，失败后恢复原输入；前端 focused 组合通过 | docs/evidence/RC-249/README.md | 网络、Key、限流和模型故障使用 Mock |
| RC-250 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：多文件 checkpoint、diff、接受/拒绝、恢复和并发编辑冲突通过；专项 1 passed | docs/evidence/RC-250/README.md | 未执行真实 Git worktree 或原生双进程矩阵 |
| RC-251 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH HANDOFF：14 路由覆盖、视觉契约和 28 张 Playwright 截图通过，首页/工作区完成人工抽查 | docs/evidence/RC-251/README.md | 外部设计签字、Tauri 和物理设备视觉矩阵未发生 |
| RC-252 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH LIMITS：类型化中英文资源、即时语言切换、日期/数字/复数格式化完成；focused 15 passed，Lint/Build 通过 | docs/evidence/RC-252/README.md | 全量旧硬编码文案抽取留后续国际化清理 |
| RC-253 | 2026-07-19 22:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH HANDOFF：R1-R6、原初 12 类、RC/测试/文档/Issue/PR 映射审计完成；traceability write/check 通过 | docs/evidence/RC-253/README.md | Issue/PR 与产品/技术/QA 签署在共享工作树不可得，已在审计报告标记 pending |
| RC-259 | 2026-07-19 21:38:30 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH PLATFORM LIMIT：动效按需初始化、reduced-motion、后台标签页暂停/恢复和空闲页无持续 RAF 完成；SiteShellMotion 3 passed，RC-259 聚焦组合 29 passed，ESLint/Vite build 通过 | docs/evidence/RC-259/README.md | 当前环境未提供长时 CPU/GPU profiler；原生桌面资源矩阵留平台/发布验收 |
| RC-260 | 2026-07-19 21:53:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：无教程代理旅程覆盖双入口、API 配置、本地模型安装/健康和星星优化；Rc260Usability 4 passed，Playwright 截图/console 证据通过 | docs/evidence/RC-260/README.md | 当前会话没有真实目标用户，未宣称完成率/时间；真实 App Server、Provider、模型下载和 runner 进程留平台/发布验收 |
| RC-261 | 2026-07-19 21:59:39 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：命令面板、默认/Vim 快捷键、焦点恢复、新会话草稿清理和 diff 审查效率路径完成；Rc261Efficiency 4 passed，组合回归 34 passed，Lint/Build 通过 | docs/evidence/RC-261/README.md | 未有真实高频用户和人类效率基线；Tauri 多窗口、屏幕阅读器和跨平台焦点留平台/发布验收 |
| RC-234 | 2026-07-19 22:55:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：GUI workflow 2 passed；RC-234 后端发送回归、结构保护和评测联合 11 passed；前端 lint/build 通过；真实 Playwright 优化→diff→采用→发送最终显示“优化完成”；完整 backend 首轮 702 passed、9 skipped、2 warnings，索引重生成待最终门禁复核 | docs/evidence/RC-234/README.md | 未执行真实云 Provider、真实本地模型权重、原生 Tauri/Linux 桌面矩阵；当前仅本地 FastAPI/Vite 与 Mock/离线规则路径 |
| RC-235 | 2026-07-19 23:05:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：视觉矩阵脚本通过 14 路由、4 组 PNG 基线和工作流截图；RC-235 Vitest 17 passed；ESLint/Ruff 通过 | docs/evidence/RC-235/README.md | 未在本次会话重新生成全部 56 张截图；复用既有固定 RC-133 基线，真实设备/人工批准像素差仍留发布视觉验收 |
| RC-236 | 2026-07-19 23:15:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH PLATFORM LIMIT：axe-core workspace/settings 扫描无 critical/serious findings；焦点/语义/reduced-motion/forced-colors 专项 2 passed，ESLint/Ruff 通过 | docs/evidence/RC-236/README.md | NVDA/VoiceOver 实机和物理对比度测量未在当前 Windows 会话完成；保留为发布平台手工验收 |
| RC-237 | 2026-07-19 23:25:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH PLATFORM LIMIT：Gemma/Qwen Fake Runner 生命周期、断点续传、健康、生成、运行、损坏修复和卸载专项 4 passed；联合既有本地模型回归 21 passed | docs/evidence/RC-237/README.md | 未执行真实大权重下载、物理 CPU/GPU/低内存硬件或外部 Ollama/llama.cpp 进程；CI 保持无大权重 |
| RC-238 | 2026-07-19 23:35:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH PLATFORM LIMIT：安装契约 2 passed、Vite build、Ruff 通过；Docker clean/non-root/lockfile/SHA-256 规则通过 | docs/evidence/RC-238/README.md | Clean VM、升级/降级/卸载真实制品和 Linux/Windows 原生 Tauri cargo check 未执行；cargo 不在当前 PATH，Tauri bundle.active=false |
| RC-239 | 2026-07-19 23:45:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH EXTERNAL LIMITS：安全威胁矩阵 5 passed；联合安全回归 25 passed；security_scan、SBOM、Docker 和 UTF-8 pip-audit 通过 | docs/evidence/RC-239/README.md | 未进行真实渗透、恶意仓库/供应链网络流量或外部 Provider 攻击；依赖 rabbit-code 本地包被 pip-audit 明确跳过 |
| RC-240 | 2026-07-20 00:05:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH LIMITS：固定 60 样本质量 gate、结构/语言/语义保护和 offline/rules 分组报告通过；专项 1 passed、quality check/Ruff 通过 | docs/evidence/RC-240/README.md | 未执行真实云 Provider 和人工双盲评分；报告保留固定 blind-review protocol，人工结果仍为发布前手工输入 |
| RC-241 | 2026-07-20 00:15:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：CI Mock policy、YAML、Provider contract 联合 16 passed；Ruff 通过；普通 backend CI 默认关闭真实 Provider 测试 | docs/evidence/RC-241/README.md | 真实 Provider/model 仅按手动策略执行，未在本次会话调用 |
| RC-242 | 2026-07-20 00:25:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH HOST LIMIT：Windows/Linux workflow matrix、compile、matrix test 1 passed、Ruff 通过；frontend build/lint/test 命令已在本机既有流程通过 | docs/evidence/RC-242/README.md | 本地 npm ci 被已有 Vite 进程锁定 esbuild；GitHub hosted Windows/Linux 矩阵尚未远程执行；Tauri native bundle inactive |
| RC-243 | 2026-07-19 22:35:21 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：最终全量 backend 回归 718 passed、9 skipped、2 warnings；覆盖率 85.99%，RC-243 策略测试 1 passed，覆盖率门禁、traceability 4 passed 和目标 Ruff 通过 | docs/evidence/RC-243/README.md | 真实 Provider/model、物理平台和第三方 mutation runner 未执行；关键路径以显式回归/故障注入测试清单约束 |
| RC-238 remediation | 2026-07-19 23:37:02 +08:00 | 未提交工作树 | PASS：Docker 共享 `packages/ui` 输入已补齐；Docker build、RC-238 脚本/专项 2 passed；Vite 8 build 与生产 npm audit 通过 | docs/reports/rc230-271-remediation.md | clean VM、原生 installer、Linux Tauri 和真实升级/卸载仍属 RC-272+ 平台矩阵 |
| RC-261 remediation | 2026-07-19 23:37:02 +08:00 | 未提交工作树 | PASS：Agents NavigationProvider/AppLink、旧路径 canonicalization、back/forward 契约和 route 文档完成；前端 33 files/150 tests、Lint/Build 通过 | docs/architecture/agents-navigation.md | 真实用户效率、屏幕阅读器和原生多窗口仍需发布平台验收 |
| RC-272 | 2026-07-22 09:30:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS WITH BUILD PENDING：Tauri bundle.active=true、targets=all、icons/publisher/category/description/Windows NSIS+WiX/Linux deb 配置完成；build_desktop.py 构建脚本、check_rc272 验证脚本、10 专项测试 passed；RC-238 断言已更新；前端 dist build 成功；cargo/rustc 可用 | docs/evidence/RC-272/README.md | tauri-cli 安装编译中，实际 Windows NSIS/MSI 安装包生成待编译完成后执行；Linux AppImage/deb/rpm 需 Linux CI runner；干净环境安装/卸载测试需 VM |
| RC-273 | 2026-07-22 09:45:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：PyPI pyproject.toml、PowerShell/shell 安装脚本、winget YAML、scoop JSON 配置完成；check_rc273 验证脚本、6 专项测试 passed | docs/evidence/RC-273/README.md | PyPI 发布需 twine 凭据；winget/scoop SHA-256 待实际二进制发布；升级/卸载冒烟测试需已发布版本 |
| RC-274 | 2026-07-22 10:00:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：PyInstaller sidecar.spec（UPX/strip 关闭、hidden imports）、build_reproducible.py（SOURCE_DATE_EPOCH、manifest、SHA-256）、check_rc274 验证脚本、12 专项测试 passed | docs/evidence/RC-274/README.md | PyInstaller 未安装；Cargo.lock 待生成；两次构建哈希对比需实际执行 |
| RC-275 | 2026-07-22 10:15:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：无模型权重文件在源码树；Tauri/sidecar/build 脚本均无权重引用；local_install.py 有 checksum/hashlib/download/retry/failed；check_rc275 验证脚本、9 专项测试 passed | docs/evidence/RC-275/README.md | 实际下载流程需端到端测试 |
| RC-276 | 2026-07-22 10:30:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：update_checker.py（HTTPS 检查、SHA-256 验证、staged rollout、RollbackManager、VersionCompatibility）、CLI check-update 命令、update-manifest.json 三渠道模板、check_rc276 验证脚本、26 专项测试 passed | docs/evidence/RC-276/README.md | 实际 HTTPS 检查需 manifest 发布到服务器；回滚需 pip 安装环境 |
| RC-277 | 2026-07-22 10:45:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：generate_sbom.py（CycloneDX SBOM、构建来源 provenance、许可证报告、制品 SHA-256、pip-audit 扫描）、check_rc277 验证脚本、13 专项测试 passed | docs/evidence/RC-277/README.md | pip-audit 未安装；npm 许可证信息可能不完整；实际生成需执行脚本 |
| RC-278 | 2026-07-22 11:00:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：CHANGELOG.md（Keep a Changelog + SemVer + 三渠道表）、release_channels.py（ChannelConfig、MigrationGate、parse/validate channel）、check_rc278 验证脚本、25 专项测试 passed | docs/evidence/RC-278/README.md | 实际渠道发布需 CI/CD 配合；迁移门槛需端到端测试 |
| RC-279 | 2026-07-22 16:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：release.yml（5 jobs: resolve-channel/build-cli/build-desktop/build-sbom/publish、tag 触发 v*、多平台矩阵、SHA-256 checksums、无代码签名）、generate_release_notes.py（CHANGELOG+git log、7 必需章节、回滚说明）、check_rc279 验证脚本、29 专项测试 passed | docs/evidence/RC-279/README.md | 实际 GitHub Actions 执行需推送 v* tag；Tauri 打包可能遇网络超时；Issue/PR 集成需 GitHub API 脚本 |
| RC-280 | 2026-07-22 16:20:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：Dockerfile dev/test 注释、docker-compose.dev.yml（127.0.0.1 绑定、dev/test profiles、restart:no）、CI docker job 独立于 backend/frontend、docs/DOCKER.md 策略文档、check_rc280 验证脚本、22 专项测试 passed | docs/evidence/RC-280/README.md | Docker CI job 需 GitHub Actions 执行；本地 Docker Desktop 未实测 |
| RC-281 | 2026-07-22 16:25:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：ADR-0017（MIT vs Apache-2.0 比较、Codex/OpenCode 兼容、专利分析、第三方义务）、frontend/package.json + tauri.conf.json + Cargo.toml 均补 license=MIT、check_rc281 验证脚本、21 专项测试 passed | docs/evidence/RC-281/README.md | 法律审查建议在发布前完成；详细第三方许可归因由 RC-282 处理 |
| RC-282 | 2026-07-22 16:30:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：NOTICE 文件（MIT copyright + Python/Node 依赖归因 + 模型许可 + OpenCode 边界）、docs/licenses/models/README.md（Gemma/Qwen 许可引用）、docs/licenses/assets/README.md（artwork/icon 许可）、THIRD_PARTY_NOTICES.md 验证、check_rc282 验证脚本、25 专项测试 passed | docs/evidence/RC-282/README.md | 部分 PyPI 包 license=UNKNOWN 需 registry 验证；法律审查建议发布前完成 |
| RC-283 | 2026-07-22 16:38:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc283_claude_prohibited.py（6 验证组：源码扫描、依赖清单、文档误标检查、denylist 覆盖、ADR 外部标记、SBOM 零命中）、36 专项测试 passed；产品源码零专有命中 | docs/evidence/RC-283/README.md | 二进制制品扫描未覆盖；SBOM 扫描需先执行 generate_sbom.py |
| RC-284 | 2026-07-22 16:44:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc284_opencode_attribution.py（6 验证组：ADR-0003、研究登记固定 SHA+MIT+concepts-only、模块映射、NOTICE 引用、无未归属 OpenCode 代码、THIRD_PARTY_NOTICES 无批准复用）、29 专项测试 passed | docs/evidence/RC-284/README.md | 未来逐文件复用需另开源登记和许可审查；语义相似性审查仍为手工 |
| RC-285 | 2026-07-22 16:47:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：license-risk-policy.yml（allow/review/deny/exceptions 互斥分类）、scan_license_risks.py（npm+pypi+model 三源扫描、classify_license、--check/--json 模式）、CI license-scan job、check_rc285 验证脚本、22 专项测试 passed | docs/evidence/RC-285/README.md | Python 依赖扫描基于 THIRD_PARTY_NOTICES 非 pip 元数据；Cargo 依赖未扫描 |
| RC-286 | 2026-07-22 16:52:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：asset-publication-rights.yml（6 类别：rabbit_artwork/app_icons/fonts/screenshots/doc_images/demo_repo）、check_rc286 验证脚本（6 验证组）、23 专项测试 passed | docs/evidence/RC-286/README.md | 兔兔素材商用权 pending；截图目录为空待发布前生成 |
| RC-287 | 2026-07-22 16:57:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：GOVERNANCE.md（6 节：维护者权限/分支保护/Release审批/依赖更新/安全响应/CODEOWNERS、无签名要求）、SECURITY.md（私有报告+72h+严重度分级）、.github/CODEOWNERS（8 敏感路径）、check_rc287 验证脚本、26 专项测试 passed | docs/evidence/RC-287/README.md | 分支保护/CODEOWNERS/Dependabot 需在 GitHub 仓库设置中配置 |
| RC-288 | 2026-07-22 17:00:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：docs/github-repository-setup.md（6 节：Topics 15个/目录结构/看板4列+8标签/里程碑3个/Release流程/公开路线图）、check_rc288 验证脚本、20 专项测试 passed | docs/evidence/RC-288/README.md | Topics/看板/里程碑/标签需在 GitHub 仓库设置中配置 |
| RC-289 | 2026-07-22 17:03:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc289_prerelease.py（5 节：clean-env/licenses/security/release/docs、--section 模式、聚合 11 个子检查脚本）、37 专项测试 passed | docs/evidence/RC-289/README.md | 实际 PyPI 发布需先注册；VM 清洁安装测试为限制项；安全审计在 CI 中执行 |
| RC-290 | 2026-07-22 17:05:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：MAINTENANCE.md（7 节：版本/节奏/兼容/安全补丁/依赖更新/弃用/EOL）、R1-R6 里程碑追踪验证（执行计划进度表+完成日志/第三方登记/ADR-0003+0017/素材权利/支持矩阵/预发布检查）、check_rc290 验证脚本、23 专项测试 passed | docs/evidence/RC-290/README.md | 发布节奏依赖维护者可用性；EOL 为承诺非代码强制 |
| RC-291 | 2026-07-22 17:10:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc291_source_map.py（5 验证组：denylist 5 仓库/法律评估版权+商业秘密+使用范围/clean-room 三角色+prohibited/信息边界英文角色名/边界检查脚本）、修复 reviewer 角色补 prohibited + 信息边界补英文角色名、27 专项测试 passed | docs/evidence/RC-291/README.md | 角色登记 pending-human-signoff；法律评估非法律意见；denylist 需定期更新 |
| RC-292 | 2026-07-22 17:13:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc292_prototype.py（6 验证组：14 必需文件/关键类/现有测试/Tauri GUI 配置/进程管理/协议生成）、28 专项测试 passed | docs/evidence/RC-292/README.md | 端到端集成测试需运行实际栈；Tauri 编译需 Rust 工具链 |
| RC-293~299 | 2026-07-22 17:18:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc293_299_milestones.py（7 里程碑 M2~M8 批量验证、62 必需文件检查）、42 专项测试 passed | docs/evidence/RC-293~RC-299/README.md | 里程碑为聚合验证；各底层 RC 已有独立 evidence |
| RC-300~310 | 2026-07-22 17:25:00 +08:00 | 未提交工作树（HEAD 6aa609f） | PASS：check_rc300_310_final.py（11 最终完成定义项：需求追踪/平台E2E/Provider契约/模型生命周期/菱形星星/兔兔素材+无障碍/CLI功能/GUI功能/无专有代码/源码审计/发布门槛）、33 专项测试 passed | docs/evidence/RC-300~RC-310/README.md | 全部 310 项 RC 已完成；实际 PyPI 发布/VM 测试/GitHub Actions 执行为运行时限制 |

### 进度记录一致性检查

每次更新进度后必须确认：

- `[x]` 的复选框数量等于“已完成项数”。
- “最后完成项”确实已经勾选并且完成日志存在对应记录。
- “下一待执行项”尚未勾选，且其全部前置依赖已经勾选。
- Commit/PR、验证结果和证据路径真实存在；禁止填写占位符后标记完成。
- 有遗留问题时必须写入“当前阻塞”或对应日志，不能为了推进进度隐藏失败。
- 如果某项需要返工，把复选框改回 `[ ]`，减少已完成项数，在日志追加“重新打开”记录，并把“下一待执行项”指向该项或其依赖。

### 新对话接力协议

用户开启新对话并要求继续项目时，执行 AI 必须按下面顺序开始，不能直接写代码：

1. 完整读取本文件开头至“实际执行顺序”，再读取进度快照指定的下一 RC 执行卡。
2. 运行下面的进度核对命令，确认快照完成数与真实 `[x]` 数一致。
3. 运行 `git status --short --branch`，区分已有用户修改、上个 RC 修改和生成文件。
4. 打开“最后完成项”的日志与证据，确认其验收真实存在；再检查“下一待执行项”的依赖。
5. 向用户用不超过五行报告：最后完成项、下一项、当前阻塞、基线测试状态和本轮将修改的范围。
6. 继续执行下一项；禁止重复已经 `[x]` 的项目，除非日志明确标为返工。

PowerShell 进度核对命令：

```powershell
$plan = 'docs\rabbit-code-310-detailed-execution.md'
$content = Get-Content -Raw -LiteralPath $plan
$done = [regex]::Matches($content, '(?m)^- \[x\] \*\*RC-(\d{3})\*\* ').Count
$pending = [regex]::Matches($content, '(?m)^- \[ \] \*\*RC-(\d{3})\*\* ').Count
$ids = [regex]::Matches($content, '(?m)^- \[[ x]\] \*\*RC-(\d{3})\*\* ') |
  ForEach-Object { [int]$_.Groups[1].Value }
[pscustomobject]@{
  Done = $done
  Pending = $pending
  Total = $done + $pending
  UniqueIds = ($ids | Sort-Object -Unique).Count
  FirstPending = ([regex]::Match($content, '(?m)^- \[ \] \*\*RC-(\d{3})\*\* ')).Groups[1].Value
}
```

预期不变量：`Total = 310`、`UniqueIds = 310`、`Done + Pending = 310`。`FirstPending` 只是编号顺序中的第一个未完成项；真正下一项还必须服从第 4 章的执行波次和依赖规则。

> 文档状态：合并增强版
>
> 更新日期：2026-07-17
>
> 本文件是 Rabbit Code 唯一计划源，完整包含原始需求、310 项基线清单、逐项执行卡、依赖顺序、技术约束、验证命令和发布门禁。
>
> 编号规则：`RC-001` 至 `RC-310` 永久对应合并前基线清单的出现顺序；后续新增事项从 `RC-311` 开始，禁止重排已有编号。
>
> 完成规则：每项只有在前置依赖、执行步骤、交付物、自动测试、必要人工验收和证据全部满足后才能标记完成。仅完成页面、接口或代码均不算完成。

## 0. 给执行 AI 的强制指令

这一章的优先级高于后文任何单项执行卡。执行 AI 每次只能处理一个明确的 RC 项或一个已定义里程碑批次，不得把 310 项一次性当成一个代码修改任务。

### 0.1 不得违反的规则

1. **先读后改。** 开始任何 RC 项前，先读取本文件对应执行卡、依赖项、涉及源码、现有测试和最近 `git status`。没有读源码就不得提出重构方案。
2. **一次只解决当前问题。** 不顺手改名、不清理无关代码、不升级无关依赖、不格式化整个仓库。每一行修改必须能指向当前 RC ID。
3. **保护用户已有修改。** 工作树可能包含用户未提交内容。不得使用 `git reset --hard`、`git checkout --` 或删除未知文件。发现重叠修改时先理解并兼容，无法兼容才停止并说明。
4. **测试先于完成声明。** 行为变更应先新增能失败的测试，再实现最小代码使其通过。不能运行测试时不得写“已完成”，只能写“实现完成、验证受阻”。
5. **不伪造外部条件。** 不得编造 API Key、OAuth 客户端、商标结论、素材授权、模型许可证、真实 API 测试或 Windows/Linux 实机结果。
6. **不静默降级。** Provider、本地模型、权限或优化链路发生降级时，必须通过结构化元数据和 UI/CLI 明示；未经用户授权不得把内容发送到另一个云 Provider。
7. **不使用泄露源码实现。** Claude Code source map 还原仓库只能按本文件的 clean-room 规则研究。不得复制或机械改写源码、Prompt、测试、内部文案、常量和私有协议。
8. **不泄露秘密。** API Key、OAuth Token、代理密码、SSH Key、`.env` 和用户源码正文不得进入 Git、默认日志、测试快照、遥测、诊断包或最终回答。
9. **不提前跳门禁。** M0 未通过不得开始专有资料研究；M1 未通过不得大规模搭建 GUI；协议未稳定不得复制前端 DTO；M6 未通过不得制作 stable Release。
10. **失败时保留现场。** 记录命令、退出码、错误摘要和已完成步骤；回滚仅回滚当前 RC 引入且能明确识别的修改，不得破坏用户数据。

### 0.2 每个 RC 项必须执行的固定流程

1. 在本文件中定位 `RC-xxx`，确认它所在执行波次和全部前置依赖均已通过。
2. 运行预检命令，记录当前分支、工作树、工具版本和基线测试状态。
3. 用一句话重述当前目标，用可测结果描述“完成”，禁止使用“基本可用”“差不多”等模糊词。
4. 列出准备修改的文件。若无法列出，继续读代码，不能开始写入。
5. 为新行为新增失败测试、契约夹具、视觉基线或人工验收表。纯文档/法律事项则先建交付模板和必填字段检查。
6. 实现满足当前 RC 的最小改动。不要顺便完成后续 RC，除非它是当前项不可分割的前置依赖并在证据中注明。
7. 依次运行：目标测试、所属模块测试、静态检查、构建检查。涉及共享协议、安全、存储或 Provider 时再运行扩大回归。
8. 检查 `git diff`，删除当前修改产生的死代码、临时日志和秘密；保留用户原有修改。
9. 把命令、结果、截图/报告路径、已知限制和回滚方式写入该 RC 的执行证据。
10. 只有所有验收通过后，才能勾选附录中的对应复选框；未通过项必须保持未勾选。

### 0.3 预检命令

在 Windows PowerShell 中从仓库根目录执行：

```powershell
git status --short --branch
git rev-parse --show-toplevel
git log -1 --oneline
python --version
node --version
npm --version
git --version
```

若 `.venv` 已存在，后端基线使用仓库虚拟环境：

```powershell
& .\.venv\Scripts\python.exe -m pytest backend\tests
& .\.venv\Scripts\python.exe -m ruff check backend
& .\.venv\Scripts\python.exe -m mypy backend\src
```

前端基线：

```powershell
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

规则：基线测试本来就失败时，先记录失败并确认是否与当前 RC 有关；不得把既有失败误称为本次修改造成，也不得在当前 RC 中顺手修复无关失败。

### 0.4 单项执行证据模板

每个 RC 项完成时必须产生一份可审计证据。执行阶段可以放入 GitHub Issue；若使用仓库文件，则放在 `docs/evidence/RC-xxx/README.md`。

```markdown
# RC-xxx 执行证据

- 状态：未开始 | 进行中 | 阻塞 | 已完成
- 负责人：
- 基线 Commit：
- 完成 Commit：
- 前置 RC：
- 修改文件：
- 用户可见行为：
- 风险与假设：

## 验证

| 命令或人工检查 | 结果 | 证据路径 |
| --- | --- | --- |
| `<command>` | PASS/FAIL/SKIP | `<path or link>` |

## 回滚

- 需要回滚的本项文件/迁移：
- 不得触碰的用户数据：

## 未解决项

- 无，或列出阻塞原因和下一动作。
```

### 0.5 必须停止并请求人工决定的情况

- 需要选择或变更主许可证、使用无许可证代码、接受模型商业条款或判断素材/商标权利。
- 需要真实 API Key、OAuth Client、应用商店账户、云服务账户或其他不在本地免费工具链内的外部资源；默认改用 Mock、离线模型或本地验证。
- 数据库迁移可能不可逆，或恢复演练无法证明用户数据安全。
- 需要管理员权限、修改系统安全策略、关闭证书校验或扩大沙箱权限。
- 现有用户改动与当前任务冲突且无法无损合并。
- 三次采用不同合理方法仍被同一外部条件阻塞。
- 需求之间出现实质冲突，例如“完全离线”同时要求访问未下载的云模型。

## 1. 已冻结的产品解释

以下解释用于消除低能力执行者的歧义。若后续证据要求修改，必须通过 ADR，而不是在代码中悄悄改变。

1. **Rabbit Code 是产品名。** CLI 主命令为 `rabbit`；旧 `prompt-opt` 在兼容期保留。
2. **“Claude Code 底层逻辑”指公开可观察的 Agent 行为和工作流。** 不等于复制 Claude Code 专有实现。
3. **“Codex 桌面端布局和功能”指信息架构和能力覆盖参考。** Rabbit Code 必须使用自己的品牌、组件、文案和视觉实现。
4. **“API 登录”在 UI 中统一写作“使用 API”或“配置 Provider”。** API Key 不是 Rabbit Code 账户密码。
5. **“Claude Code 格式”映射为 Anthropic Messages API 或经批准的官方 Agent SDK。** 不支持盗用订阅 Token、Cookie 或内部 OAuth。
6. **FastAPI 不是模型。** 它是本地 App Server；实际优化由云 Provider、Gemma、Qwen2.5-Coder或 `OfflineRuleProvider` 执行。
7. **无 API 不等于无网络安装。** 首次下载模型可以联网；模型安装完成后必须支持离线对话和优化。受限网络另走离线导入。
8. **本地模型默认运行器为 Ollama。** llama.cpp 是可替换 Adapter；在 RC-187 ADR 有反证前按此执行。
9. **首个稳定版不依赖 Rabbit Code 云账户。** 会话、设置、模型和历史默认本地保存。
10. **菱形星星优化默认不自动发送。** 用户必须先查看/采用结果，再明确发送。
11. **零付费发布边界。** Rabbit Code 默认使用本地 FastAPI、SQLite、免费开源构建工具和 GitHub 公共仓库发布；不购买服务器、域名、应用商店账户、代码签名证书、付费 CI、付费遥测或付费素材。云 API 和模型下载只作为用户自选路径，费用由用户直接承担，不由 Rabbit Code 代付。

## 2. 默认技术架构

### 2.1 默认栈

| 层 | 默认选择 | 原因 | 变更条件 |
| --- | --- | --- | --- |
| Agent Core | Python 3.12、异步服务层 | 复用当前 Python/FastAPI 与测试资产 | M1 原型证明无法满足性能或打包要求 |
| 本地 App Server | FastAPI + Uvicorn | 当前项目已存在，适合 REST/SSE/WebSocket | 只有 ADR 可替换 |
| CLI | Typer + Rich，交互编辑优先评估 prompt_toolkit | 复用现有 CLI 依赖，减少重写 | TUI 原型证明无法满足输入/渲染 |
| GUI | React 18 + TypeScript + Vite | 当前前端栈 | 只有阻断性证据可替换 |
| 桌面壳 | Tauri 2 | 跨平台、较小包体、可管理 sidecar | M1 与 Electron 实测比较后可改 |
| 本地数据库 | SQLite | 已有数据与离线优先 | 不引入独立数据库服务 |
| 云协议 | OpenAI Chat/Responses、Gemini、Anthropic | 覆盖明确要求 | 其他服务通过 Adapter/兼容 Preset |
| 本地模型 | Ollama 默认，llama.cpp 备用 | 安装和 API 较成熟 | 按许可证、平台与实测 ADR 调整 |
| 密钥 | OS Keychain/Credential Manager/Secret Service | 禁止 SQLite 明文 | 无可用密钥库时仅允许临时会话密钥 |
| API 类型生成 | 后端 OpenAPI -> 前端生成客户端 | 避免 DTO 漂移 | CI 必须检查生成差异 |

### 2.2 目标目录契约

不在项目早期强行移动现有目录。先在当前 `backend`/`frontend` 边界内增量演进：

```text
prompt-optimizer/
├─ backend/
│  ├─ src/
│  │  ├─ prompt_optimizer/          # 现有 V2 能力与 prompt-opt 兼容层
│  │  └─ rabbit_code/               # 新 Agent 产品核心
│  │     ├─ agent/                   # 状态机、预算、检查点、事件
│  │     ├─ api/                     # FastAPI v1 路由与依赖注入
│  │     ├─ cli/                     # rabbit 命令与 TUI
│  │     ├─ context/                 # 项目识别、指令、索引、压缩
│  │     ├─ permissions/             # 策略、审批与审计
│  │     ├─ providers/               # OpenAI/Gemini/Anthropic/Local Adapter
│  │     ├─ prompts/                 # 版本化 Prompt 资源
│  │     ├─ security/                # 脱敏、路径与秘密保护
│  │     ├─ sessions/                # 会话、记忆、检查点
│  │     ├─ storage/                 # SQLite 迁移与仓储
│  │     └─ tools/                   # 文件、Shell、Git、进程、MCP
│  └─ tests/
│     ├─ unit/
│     ├─ integration/
│     ├─ contract/
│     ├─ security/
│     └─ e2e/
├─ frontend/
│  ├─ src/
│  │  ├─ app/                        # 路由、Provider 和全局状态
│  │  ├─ components/
│  │  │  ├─ composer/               # 输入框与菱形星星
│  │  │  ├─ diff/
│  │  │  ├─ terminal/
│  │  │  └─ rabbit-mark/
│  │  ├─ generated/                  # OpenAPI 生成，禁止手改
│  │  ├─ routes/
│  │  └─ styles/                     # Design Token 与主题
│  └─ src-tauri/                     # 桌面壳、sidecar、更新和 OS 桥接
├─ data/
│  ├─ models/                        # 仅 manifest，不默认打包权重
│  ├─ prompts/
│  └─ evaluation/
├─ scripts/                          # 安装、生成、检查和发布脚本
├─ docs/                             # 本主控计划、架构、ADR、证据
└─ .github/workflows/                # CI、nightly、beta、stable
```

目录规则：

- 现有 `prompt_optimizer` 在兼容期内不整体改名；新功能进入 `rabbit_code`，通过明确接口复用旧优化服务。
- `frontend/src/generated` 只由生成命令写入；评审者看到手工修改必须拒绝。
- 模型权重、`.runtime`、密钥、日志和用户数据库不得提交 Git。
- 大规模移动目录必须单独 RC/ADR，并保证移动前后测试在同一提交中通过。

### 2.3 进程和通信边界

```text
React GUI
   | REST: CRUD、配置、历史、健康
   | SSE: Agent 与提示词优化流
   | WebSocket: 交互终端
   v
FastAPI App Server ---- OS Secret Store
   |        |       |
   |        |       +---- SQLite / 文件存储
   |        +------------ Tool / Permission / Session Core
   +--------------------- Cloud Provider 或 LocalRunner

Tauri 只负责窗口、文件选择、通知、更新、密钥桥接和 App Server sidecar 生命周期。
CLI 使用同一 Agent Core；可进程内运行或连接 App Server，但事件 Schema 必须一致。
```

强制通信选择：

- 普通查询和变更使用 `/api/v1/...` REST。
- Agent 和 Prompt 优化采用带序号的 SSE；每条事件含 `protocol_version`、`request_id`、`seq`、`type`、`timestamp` 和 `payload`。
- 终端采用认证 WebSocket，消息必须有 session/terminal ID、方向、序号和大小限制。
- Tauri Command 不承载 Agent 业务，只承载 OS 能力。

### 2.4 必须先稳定的核心契约

Provider 最小接口：

```python
class Provider(Protocol):
    name: str
    async def capabilities(self) -> ProviderCapabilities: ...
    async def list_models(self) -> list[ModelInfo]: ...
    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
    async def cancel(self, request_id: str) -> None: ...
    async def health(self) -> HealthResult: ...
```

工具最小接口：

```python
class Tool(Protocol):
    metadata: ToolMetadata  # JSON Schema、权限、读写影响、幂等和可取消性
    async def run(self, request: ToolRequest, context: ToolContext) -> ToolResult: ...
```

每次 Agent/Prompt 请求必须带不可变输入 revision。返回结果只有在 request ID 和 revision 都匹配当前草稿时才可直接应用。

### 2.5 本地数据最小表

在 RC-213 评审前，至少规划以下实体；实际字段用迁移创建，不能在启动时临时 `CREATE TABLE` 绕过版本管理。

| 实体 | 必需关系/用途 |
| --- | --- |
| `workspaces` | 规范化路径、Git 根、显示名、最后打开时间 |
| `sessions` | 工作区、标题、状态、模式、Provider/模型、创建更新时间 |
| `messages` | 会话、角色、顺序、公开内容、模型元数据 |
| `content_blocks` | 文本、工具、diff、图片、诊断等结构块 |
| `tool_calls` | 工具名、输入摘要、权限决策、状态、结果引用 |
| `checkpoints` | 会话、工作树基线、diff、验证与回滚状态 |
| `prompt_versions` | 原文、结果、采用状态、Provider/模型和 Prompt 版本 |
| `providers` | 非敏感配置、密钥引用、能力和健康状态 |
| `local_models` | manifest ID、版本、路径、哈希、状态和运行器 |
| `settings` | scope、key、typed value、来源；不保存秘密 |
| `audit_events` | 最小安全审计，不保存默认敏感正文 |

## 3. 原始要求的不可丢失解释

| 编号 | 原始要求 | 最终必须看到的证据 |
| --- | --- | --- |
| R1 | GitHub 调研 Codex、OpenCode、Claude Code；终端对标 Claude Code；GUI 对标 Codex 桌面端 | 固定 SHA 调研、clean-room 记录、CLI 行为测试、GUI 功能矩阵 |
| R2 | 每个独立页面都有兔兔素材并美观 | 路由覆盖表、RabbitMark 组件、全页视觉回归和人工验收 |
| R3 | 对话框菱形星星自动优化；有 API 用用户 API，无 API 用 FastAPI | 两条 E2E、路由元数据、并发 revision 测试、离线规则 fallback |
| R4 | 首页 API/无 API 两选项；无 API 自动安装 Gemma/Qwen2.5-Coder并二选一 | 干净机安装录像/报告、两模型生命周期测试、统一工作区入口 |
| R5 | 完成全部相关功能和 API 接入代码 | RC-001 至 RC-310 追踪报告，无仅文档未实现的功能项 |
| R6 | 支持主流 AI，至少 OpenAI、Gemini、Claude 格式 | 三原生协议契约、真实受控连接、兼容 Provider Preset |

原初 12 类计划也不得丢失：项目前期准备、开源调研、架构设计、核心功能开发、GUI 设计、提示词优化、API 接入、本地模型集成、整合测试、文档部署、优化迭代、开源发布。


## 4. 实际执行顺序

RC 编号用于永久追踪，不代表实际开发顺序。执行 AI 必须按下表波次推进。一个波次的出口门禁没有通过时，不得开始依赖它的后续波次。

| 波次 | 目标 | 主要 RC | 进入条件 | 出口门禁 |
| --- | --- | --- | --- | --- |
| W0 | 保护现有项目基线 | RC-043、RC-046 至 RC-055 | 当前仓库可读 | 现有测试/构建结果已记录，V2 可恢复 |
| W1 | 合法性、产品与来源冻结 | RC-001 至 RC-045、RC-281 至 RC-291 | W0 完成 | M0 签署；无许可/素材/命名阻塞 |
| W2 | 架构纵向原型 | RC-056 至 RC-067、RC-213 至 RC-214、RC-292 | M0 通过 | CLI/GUI 经同一 FastAPI 流完成请求、取消和退出 |
| W3 | 协议与 Agent Core | RC-068 至 RC-099、RC-215、RC-219、RC-230、RC-293 | W2 通过 | 状态机、工具、权限事件可重放；核心测试通过 |
| W4 | Provider 与密钥 | RC-159 至 RC-184、RC-216 至 RC-220、RC-231 至 RC-232 | W3 协议稳定 | 三原生协议 Mock 通过；Keychain 无明文泄漏 |
| W5 | 本地模型 | RC-185 至 RC-200、RC-228、RC-237、RC-303 | W4 Provider 接口稳定 | Gemma/Qwen 各完成一次生命周期；离线生成通过 |
| W6 | CLI/TUI 产品化 | RC-100 至 RC-108、RC-233、RC-306 | W3 Agent Core 稳定 | 交互/无头/JSON/恢复在支持终端通过 |
| W7 | GUI 壳与视觉系统 | RC-109 至 RC-133、RC-235 至 RC-236、RC-254 至 RC-259 | W2 和视觉授权通过 | 全路由可导航、RabbitMark 覆盖、视觉/A11y 基线通过 |
| W8 | 菱形星星与优化链路 | RC-134 至 RC-158、RC-240、RC-246 至 RC-249、RC-296、RC-304 | W4、W5、W7 完成 | 云/本地/离线规则三路线不丢草稿 |
| W9 | 跨端工作流与用户验证 | RC-221、RC-244 至 RC-253、RC-260 至 RC-261、RC-301、RC-305、RC-307 | W6 至 W8 完成 | GUI/CLI 状态一致，用户旅程和 Windows/Linux 矩阵通过 |
| W10 | 安全、性能和故障硬化 | RC-201 至 RC-212、RC-222 至 RC-229、RC-238 至 RC-243、RC-297 | 核心功能冻结 | 无高危问题，取消/恢复/大仓库/安装升级达标 |
| W11 | 文档、打包和开源治理 | RC-262 至 RC-289、RC-298 | W10 通过 | 未签名制品、SHA-256、SBOM、NOTICE、安装文档齐全 |
| W12 | 最终验收与持续迭代 | RC-299 至 RC-310 | W11 通过 | Go/No-Go 通过并发布；建立后续看板 |

### 4.1 关键依赖规则

- RC-061 协议版本化完成前，不得在前端手写最终消息/工具 DTO。
- RC-065 配置优先级完成前，不得同时实现 GUI、CLI 两套 Provider 配置。
- RC-068 状态机完成前，不得把工具循环直接写进路由或 React 组件。
- RC-097 工具元数据完成前，不得向模型批量暴露工具。
- RC-151 路由策略完成前，不得实现自动云端 fallback。
- RC-179 密钥库完成前，只允许进程内临时 Key，不得写 SQLite 或普通配置。
- RC-187 运行器 ADR 和 RC-188 模型 manifest 完成前，不得自动下载安装二进制/权重。
- RC-207 本地服务认证完成前，桌面 GUI 不得以生产模式连接 App Server。
- RC-213/214 数据模型和迁移完成前，不得持久化新的会话状态。
- RC-277 的制品哈希、来源清单和 SBOM 完成前，不得发布 stable 安装包；代码签名不是发布前置条件。

### 4.2 波次内部默认顺序

- **W0 必须按此顺序：** RC-043 -> RC-046 -> RC-047 -> RC-048 -> RC-050 -> RC-052 -> RC-053 -> RC-054 -> RC-051 -> RC-055。先建立追踪，再记录技术与行为基线，最后处理数据/命名兼容并保护 V2。
- **W1 必须按此顺序：** RC-015 至 RC-020 -> RC-021 至 RC-030 -> RC-031 至 RC-036 -> RC-001 至 RC-014 -> RC-037 至 RC-042 -> RC-044 至 RC-045 -> RC-281 至 RC-291。先固定外部证据和合法性，再冻结品牌、范围和治理。
- **W2 至 W12：** 在同一连续 RC 范围内默认按编号升序；表中插入的跨范围测试/里程碑 RC 放在该波次核心实现之后执行。
- 如果详细执行卡声明更严格的依赖，以更严格者为准。任何改变顺序的决定都必须写入进度日志，说明原因和不影响的门禁。

## 5. 各模块的落地文件与验证配方

执行具体 RC 时，优先使用本节文件范围。若实际代码结构不同，先记录差异；不得为了匹配计划无必要地移动文件。

### 5.1 研究、ADR 与治理类 RC

适用：RC-001 至 RC-045、RC-281 至 RC-291。

- **主要文件：** `docs/adr/`、`docs/research/`、`docs/legal/`、`docs/design/`、`LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES`。
- **执行方法：** 固定外部来源 SHA 和日期；明确事实、假设、选项、决策、代价、复核条件；法律结论必须由有权限的人确认。
- **验证：** 链接/许可证扫描、需求追踪脚本、人工签署。AI 不得自行把“未找到冲突”写成法律无风险。
- **完成证据：** ADR 状态为 `Accepted`，引用不可变，决策人/日期存在。

### 5.2 Agent Core 类 RC

适用：RC-056 至 RC-079、RC-230、RC-292 至 RC-293。

- **主要文件：** `backend/src/rabbit_code/agent/`、`backend/src/rabbit_code/providers/base.py`、`backend/src/rabbit_code/tools/base.py`、`backend/tests/unit/agent/`。
- **实现顺序：** 事件模型 -> 状态转换 -> Fake Provider/Tool -> 单轮文本 -> 单工具 -> 连续工具 -> 权限 -> 取消 -> 检查点 -> 恢复 -> 预算 -> 子 Agent。
- **禁止做法：** 在 FastAPI 路由里写循环；用全局变量保存会话；工具直接调用具体 UI；重试非幂等写操作。
- **最小测试：** 合法/非法状态转换、Provider 超时、工具拒绝、取消级联、预算耗尽、崩溃重放、重复事件幂等。

### 5.3 上下文、会话与存储类 RC

适用：RC-080 至 RC-089、RC-213 至 RC-221。

- **主要文件：** `backend/src/rabbit_code/context/`、`sessions/`、`storage/`、`security/redaction.py`、`backend/tests/integration/storage/`。
- **实现顺序：** 规范化工作区 -> 指令发现 -> 内容块 -> ignore/敏感规则 -> Token 预算 -> 记忆作用域 -> 会话 CRUD -> 检查点 -> 迁移/恢复。
- **禁止做法：** 直接读取符号链接目标；把二进制塞入上下文；在没有迁移版本时改变表结构；把密钥放进导出。
- **最小测试：** Windows/Unix 路径、嵌套指令、`.gitignore`、超大文件、跨项目隔离、WAL 并发、kill 恢复、恶意 ZIP 导入。

### 5.4 工具、权限与 MCP 类 RC

适用：RC-090 至 RC-099、RC-201 至 RC-212。

- **主要文件：** `backend/src/rabbit_code/tools/`、`permissions/`、`security/`、`mcp/`、`backend/tests/security/`。
- **实现顺序：** ToolMetadata -> 路径工具 -> Shell Adapter -> Git -> 进程 -> 补丁 -> 输出限制 -> 权限引擎 -> 审批 -> 沙箱 -> MCP/插件。
- **禁止做法：** 用字符串拼接用户命令；跟随越界符号链接；以模型回答替代确定性权限检查；默认永久授权；未校验 manifest 就运行扩展。
- **最小测试：** traversal、symlink、命令注入、环境泄漏、危险 Git、后台孤儿进程、MCP 篡改、审批超时与撤销。

### 5.5 Provider 类 RC

适用：RC-159 至 RC-173、RC-231 至 RC-232、RC-302。

- **主要文件：** `backend/src/rabbit_code/providers/`、`backend/tests/contract/providers/`、`data/providers/presets.yml`。
- **实现顺序：** 统一请求/事件 -> Fake Provider -> OpenAI Chat -> Responses -> Gemini -> Anthropic -> 托管变体 -> Preset -> 能力 -> 错误 -> 网络韧性。
- **禁止做法：** 一个通用解析器猜所有协议；默认记录请求正文；在普通 CI 调真实 API；把 Provider 的私有参数泄漏到 Agent Core。
- **最小测试：** 文本、SSE 边界拆分、工具、用量、取消、401/403/404/429/5xx、内容过滤、格式损坏、未知字段。

### 5.6 本地模型类 RC

适用：RC-185 至 RC-200、RC-228、RC-237、RC-303。

- **主要文件：** `backend/src/rabbit_code/local_models/`、`data/models/manifest.yml`、`scripts/install-local-model.ps1`、`scripts/install-local-model.sh`。
- **实现顺序：** 硬件报告 -> Runner Protocol -> Fake Runner -> Ollama -> manifest -> 下载器 -> 健康 -> GUI 状态 -> 资源控制 -> 离线导入。
- **禁止做法：** 未审核直接下载 `latest`；忽略模型许可证；把大权重提交 Git/安装包；默认管理员安装；哈希失败后继续加载。
- **最小测试：** 断点续传、错误哈希、磁盘满、取消、CPU-only、OOM、模型切换、损坏修复、卸载和离线导入。

### 5.7 CLI/TUI 类 RC

适用：RC-100 至 RC-108、RC-233、RC-306。

- **主要文件：** `backend/src/rabbit_code/cli/`、`backend/tests/e2e/cli/`。
- **实现顺序：** 无头 `run` -> JSONL -> resume -> 交互输入 -> 事件渲染 -> 审批 -> 斜杠命令 -> 补全/doctor。
- **禁止做法：** 机器模式输出 ANSI；无 TTY 时等待输入；CLI 复制 Provider/会话业务；吞掉非零退出码。
- **最小测试：** TTY/非 TTY、stdin、Ctrl+C、Unicode 路径、大段粘贴、80x24、无颜色、Shell 差异和恢复。

### 5.8 GUI 与视觉类 RC

适用：RC-109 至 RC-146、RC-234 至 RC-236、RC-244 至 RC-261、RC-305、RC-307。

- **主要文件：** `frontend/src/routes/`、`components/composer/`、`components/rabbit-mark/`、`styles/`、`frontend/e2e/`、`frontend/src-tauri/`。
- **实现顺序：** 路由壳 -> API Provider -> 工作区/会话 -> 任务布局 -> diff/终端 -> 设置 -> Design Token -> RabbitMark -> Composer -> 星星状态机 -> 结果 diff。
- **禁止做法：** 页面直接 fetch 不经客户端层；组件内保存 Key；卡片嵌套卡片；用装饰遮挡工作区；优化完成自动发送；用 viewport 宽度缩放字体。
- **最小测试：** 双入口、长模型名、并发编辑 revision、取消、深浅主题、最小窗口、200% 缩放、键盘、屏幕阅读器和视觉快照。

### 5.9 打包、更新与发布类 RC

适用：RC-262 至 RC-280、RC-297 至 RC-310。

- **主要文件：** `frontend/src-tauri/tauri.conf.json`、`scripts/release/`、`.github/workflows/`、`README.md`、发布证据目录。
- **实现顺序：** 开发构建 -> 未签名本地包 -> 干净 VM 安装 -> SHA-256/来源清单 -> SBOM/NOTICE -> beta -> 升级/回滚 -> stable。
- **禁止做法：** 把 Docker 成功当桌面成功；把代码签名证书或付费发布服务设为前置条件；安装包暗带模型权重。
- **最小测试：** 安装、首次启动、升级、阻止不兼容降级、卸载、残留选择、篡改更新、来源和哈希验证。

## 6. API、事件和状态的最低规范

这些名称可以在 ADR 中调整，但语义不得缺失。执行 AI 不得为每个页面发明不兼容的接口。

### 6.1 API v1 最小路由

| 方法 | 路由 | 用途 |
| --- | --- | --- |
| GET | `/api/v1/health` | App Server、协议、数据库、SecretStore、Runner 健康 |
| GET/POST | `/api/v1/workspaces` | 工作区列表与打开 |
| GET/POST | `/api/v1/sessions` | 会话列表与创建 |
| GET/PATCH/DELETE | `/api/v1/sessions/{id}` | 会话详情、更新、删除/恢复 |
| POST | `/api/v1/agent/runs` | 创建 Agent Run，返回 request ID |
| GET | `/api/v1/agent/runs/{id}/events` | SSE 事件流 |
| POST | `/api/v1/agent/runs/{id}/cancel` | 幂等取消 |
| POST | `/api/v1/permissions/{id}/decision` | 允许、拒绝或规则授权 |
| GET/POST | `/api/v1/providers` | Provider 非敏感配置 |
| POST | `/api/v1/providers/{id}/test` | 受预算限制的连接测试 |
| GET | `/api/v1/models` | 云/本地模型与能力 |
| POST | `/api/v1/local-models/install` | 创建安装任务 |
| GET | `/api/v1/tasks/{id}/events` | 安装/后台任务 SSE |
| POST | `/api/v1/prompts/optimize` | 非流式优化 |
| POST | `/api/v1/prompts/optimize/stream` | 流式优化 |
| GET | `/api/v1/prompts/history` | Prompt 版本与比较 |
| WS | `/api/v1/terminals/{id}` | 认证终端流 |

### 6.2 Agent 事件最低字段

```json
{
  "protocol_version": "1.0",
  "request_id": "uuid",
  "session_id": "uuid",
  "seq": 1,
  "type": "run.started",
  "timestamp": "RFC3339",
  "payload": {}
}
```

必需事件族：`run.started`、`context.ready`、`model.delta`、`tool.requested`、`permission.requested`、`tool.started`、`tool.completed`、`tool.failed`、`checkpoint.saved`、`run.completed`、`run.failed`、`run.cancelled`。

### 6.3 Prompt 优化请求最低字段

```json
{
  "session_id": "uuid-or-null",
  "request_id": "uuid",
  "input_revision": 12,
  "prompt": "用户当前文本",
  "immutable_spans": [],
  "provider_id": "current-or-null",
  "model_id": "current-or-null",
  "goals": ["clarity", "constraints", "format"],
  "language": "auto",
  "save_history": true
}
```

响应必须返回 `input_revision`、实际 Provider/模型、`execution_location`、是否 fallback、fallback 原因、Prompt 资源版本、耗时和优化文本。客户端只有在 revision 仍匹配时才能直接采用。

### 6.4 权限决策最低结构

- `once`：仅当前 tool call。
- `session`：当前会话、相同规范化能力和范围。
- `rule`：结构化规则，必须显示并可撤销。
- `deny`：拒绝且把结果返回 Agent。
- `edit`：用户修改参数后产生新的 tool call ID，旧调用不得复用批准。

高权限模式也不能绕过以下安全底线：秘密默认保护、本地 App Server 认证、更新来源与哈希校验、模型哈希和禁止无授权专有代码。

### 6.5 本地模型状态机

允许转换必须显式编码和测试：

```text
not_installed -> downloading -> verifying -> installed -> loading -> ready
downloading -> cancelled | failed
verifying -> corrupt | failed
ready -> busy -> ready
ready -> unloading -> installed
installed/ready/corrupt/failed -> removing -> not_installed
installed/ready -> update_available -> downloading
```

任何未列出的跨状态跳转均应拒绝并记录错误。文件存在不等于 `ready`，只有健康检查通过才能就绪。

## 7. GUI 页面和兔兔素材硬性清单

| 路由 | 必需功能 | 兔兔素材建议 | 必测状态 |
| --- | --- | --- | --- |
| `/onboarding` | API/无 API 两入口、环境状态 | 完整主形象 | 新装、已有配置、服务错误 |
| `/workspaces` | 最近项目/任务、打开项目 | 页角或空状态 | 空、失效路径、无权限 |
| `/tasks/:id` | 会话、对话、Composer、计划、diff、终端 | 侧栏小标 | 流式、工具、审批、取消、长文本 |
| `/review/:id` | 文件树、逐块接受/拒绝、验证 | 克制水印/小标 | 冲突、无变更、大 diff |
| `/prompts` | 模板、历史、评分、比较、导入导出 | 空状态/页角 | 空、分页、非法导入 |
| `/settings/providers` | Provider、Key 引用、模型、连接测试 | 小型页角 | 401、429、发现失败、手动 ID |
| `/settings/local-models` | 检测、安装、进度、修复、卸载 | 安装向导变体 | 下载、取消、损坏、OOM |
| `/settings/general` | 外观、语言、终端、数据、隐私 | 单色小标 | 默认、修改、重置 |
| `/settings/extensions` | MCP、插件、Hooks、权限 | 小型页角 | 未信任、禁用、升级提权 |
| `/diagnostics` | 版本、健康、日志、脱敏诊断 | 工具帽/空状态变体 | 正常、组件失败、无日志 |
| `/about` | 版本、许可证、隐私、更新 | 完整但较小形象 | 最新、可更新、离线 |

新增独立路由时，必须先在本表和视觉覆盖矩阵登记 RabbitMark；未登记路由不得合并。

## 8. 安全与隐私不变量

1. FastAPI 生产桌面模式只监听 Loopback，使用随机端口、每次启动高熵令牌、Host/Origin 校验和严格 CORS。
2. SQLite/普通配置只保存密钥引用；真实秘密进入 OS Secret Store 或仅驻留当前进程内存。
3. 工具路径先规范化，再校验工作区和符号链接最终目标；校验顺序不得反转。
4. Shell 参数优先使用参数数组；需要 Shell 语法时显示完整命令并走风险审批。
5. `.env`、SSH、云配置、浏览器资料和用户增加的敏感路径默认不索引、不发送。
6. 插件、MCP、Hook、安装脚本和更新包都必须有来源、版本、哈希、权限和禁用入口。
7. 诊断、日志和遥测默认不含 Prompt/源码正文；用户发送诊断包前可预览并再次脱敏。
8. 用户取消后不得继续产生模型 token、写文件或运行后台工具；取消必须级联到进程树。
9. Agent 产生的改动必须能通过 checkpoint/diff 识别；回滚不得覆盖用户并发编辑。
10. 任何 fallback 都必须标注来源和原因；云端 fallback 必须预授权。

## 9. 验证命令与扩大回归规则

### 9.1 后端目标验证

```powershell
& .\.venv\Scripts\python.exe -m pytest backend\tests\path\to\focused_test.py -q
& .\.venv\Scripts\python.exe -m ruff check backend
& .\.venv\Scripts\python.exe -m mypy backend\src
```

修改以下共享边界时必须再跑全部后端测试：事件/Schema、数据库迁移、权限、路径安全、Provider Base、PromptOptimizationService、会话恢复。

### 9.2 前端目标验证

```powershell
npm --prefix frontend test -- --run
npm --prefix frontend run lint
npm --prefix frontend run build
```

Tauri 接入后增加：

```powershell
npm --prefix frontend run tauri build
```

修改 Composer、路由 Shell、Design Token、RabbitMark、生成客户端或全局状态时，必须跑全前端测试和 Playwright 关键路径。

### 9.3 协议一致性验证

生成 OpenAPI 后必须确认工作树只有预期生成差异。推荐最终命令名：

```powershell
& .\scripts\generate-api.ps1
git diff --exit-code -- frontend\src\generated
```

脚本尚未创建时，RC-062 必须先创建脚本和 CI，再允许依赖它的功能合并。

### 9.4 禁止用“跳过”冒充通过

- `SKIP` 只有在测试明确属于非当前平台或需要外部凭据时允许，且必须有替代 Mock/契约测试。
- Windows/Linux、真实 Provider、模型实机和人工无障碍属于发布门禁，可以阶段性未执行，但不能标记对应 RC 完成；代码签名不属于本项目门禁。
- 截图存在不等于交互可用；接口 200 不等于业务成功；测试覆盖率高不等于安全路径已验证。

## 10. 故障处理决策树

### 10.1 测试失败

1. 先单独重跑失败测试，保留完整错误。
2. 检查失败是否在修改前已存在；用基线证据判断，不得猜测。
3. 若由当前修改导致，先缩小到最小复现，再修实现或测试中的错误假设。
4. 若是外部服务波动，确保 Mock 测试仍确定；真实测试标为阻塞而非通过。
5. 连续三种合理修复仍失败，记录阻塞和最小复现，停止扩大修改范围。

### 10.2 数据库迁移失败

1. 停止写入，不自动重复不可确认的迁移。
2. 保留原数据库和自动备份，复制到临时目录诊断。
3. 运行完整性检查并记录 schema version。
4. 修复迁移必须幂等；用副本完成升级和恢复后才碰用户数据。

### 10.3 Provider 失败

1. 依据统一错误分类判断认证、余额、限流、模型、参数、网络或服务端。
2. 认证/余额不得自动重试；429 尊重 `Retry-After`；5xx 只重试幂等请求。
3. 保留用户草稿；提供重试、切换或本地路线。
4. 未预授权的其他云 Provider 永不自动调用。

### 10.4 本地模型失败

1. 检查 manifest、文件哈希、运行器健康、磁盘/RAM/VRAM和日志。
2. 下载损坏先隔离临时文件；不得把损坏文件标为 installed。
3. OOM 先卸载并降低上下文/并发/GPU 配置，再提示用户选择更小量化。
4. 提示词优化可以降级离线规则；普通对话不得伪装成模型成功。

### 10.5 GUI 失败

1. 先查浏览器控制台、网络事件和 App Server request ID。
2. 用固定 Mock 数据复现，区分渲染、状态和后端问题。
3. 修复后跑目标组件、E2E、视觉和无障碍测试中适用的部分。
4. 不用隐藏按钮、吞错误或刷新整页掩盖状态同步问题。

## 11. 单项完成定义

一个 RC 项只有同时满足以下条件才可 `[x]`：

- 前置 RC 已完成且证据存在。
- 计划要求的代码/文档/配置已落地，没有 TODO 代替核心行为。
- 目标测试从失败变为通过，或文档/法律项的必填检查和签署完成。
- 所属模块回归、静态检查和构建通过。
- 涉及 UI 时完成真实渲染、交互、响应式和必要无障碍检查。
- 涉及 Provider/模型时完成 Mock 契约；真实测试未完成则不得关闭要求真实验证的 RC。
- 涉及数据时完成升级、失败和恢复测试。
- 涉及安全时有负向测试，不能只有成功路径。
- `git diff` 中没有秘密、临时文件、调试日志、无关重构或未知生成物。
- 完成本文件开头规定的进度快照、完成日志、复选框和证据更新。

下面开始 310 项逐项执行卡。每张卡的“执行步骤”和“交付与验收”必须与本章通用规则合并执行，不能只完成卡片中最容易的一部分。

## A. 项目目标与强制约束

### RC-001 正式确立 Rabbit Code 品牌与定位

- **执行步骤：** 检索 GitHub、npm、PyPI、crates.io 和主流搜索引擎中的同名项目；确定产品中文/英文名称、CLI 命令、包名、应用 ID 与一句话定位；将结果写入品牌 ADR 并同步所有新模块的元数据。
- **交付与验收：** 产出 `docs/adr/0001-brand-and-product-scope.md` 和命名清单；名称无已知高风险冲突，README、应用标题、CLI `--version` 输出一致。

### RC-002 建立 Claude Code 风格终端行为基线

- **执行步骤：** 从官方文档和合法黑盒测试整理 Agent 循环、工具、权限、上下文、恢复与 Git 行为；为每项写输入、可观察输出和异常行为；转化为 Rabbit Code 独立规格与兼容测试，禁止复制专有实现文本。
- **交付与验收：** 产出 `docs/specs/terminal-behavior.md` 和测试矩阵；每个目标行为至少有一个可重复验收用例及来源说明。

### RC-003 建立 Codex 风格桌面产品基线

- **执行步骤：** 记录 Codex 桌面端可公开观察的信息架构、任务流、会话、diff、终端和设置能力；绘制 Rabbit Code 自有线框图；对品牌、图标、文案和视觉差异做设计审查。
- **交付与验收：** 产出 `docs/design/desktop-information-architecture.md` 和关键页面线框；设计评审确认没有直接复制品牌资产或像素级布局。

### RC-004 审核 OpenCode 可复用实现

- **执行步骤：** 固定 OpenCode Commit；逐模块记录文件路径、MIT 许可、版权头、NOTICE、修改计划和替代方案；只有审核状态为 `approved` 的文件才能进入实现 Issue。
- **交付与验收：** 产出 `docs/research/opencode-reuse-register.csv`；CI 中的来源检查能把未登记的 OpenCode 衍生文件判为失败。

### RC-005 迁移 Prompt Optimizer 既有能力

- **执行步骤：** 为分析、评分、建议、模板、历史、diff、导出、评测、Provider、CLI 和 FastAPI 建立现状测试；标记复用、重构、替换或废弃；先补回归测试再移动模块。
- **交付与验收：** 产出资产清单和迁移映射；迁移前后既有测试、评测样本和导出快照均通过，数据无损。

### RC-006 将提示词功能集中到对话主流程

- **执行步骤：** 绘制输入框、优化浮层、结果比较和历史抽屉的状态图；把分析、模板、优化、比较、采用、撤销、发送接入同一 Composer 状态容器；保留独立资产页作为管理入口。
- **交付与验收：** 用户在主任务页不跳转路由即可完成完整优化流程；E2E 覆盖成功、失败、取消和撤销。

### RC-007 实现菱形星星一键优化入口

- **执行步骤：** 使用统一 Sparkles 图标创建固定尺寸按钮；绑定当前输入快照与优化请求；实现加载、取消、成功、失败和防重复点击状态。
- **交付与验收：** 组件测试验证一次点击只产生一个请求，空输入不可触发，所有状态均有可访问名称且不引发布局位移。

### RC-008 实现 API/本地 FastAPI 自动路由

- **执行步骤：** 读取会话当前 Provider 健康状态；有可用 API 时携带 Provider/模型调用优化服务，无可用 API 时固定调用本地 FastAPI；把实际路由和降级原因写入响应元数据。
- **交付与验收：** API 与无 API 两组集成测试分别命中预期路径，任何云端回退都必须经过用户授权。

### RC-009 明确 FastAPI 与实际优化引擎职责

- **执行步骤：** 定义 `PromptOptimizationService` 与 `OptimizationBackend` 接口；为 Gemma、Qwen2.5-Coder和离线规则实现 Adapter；在 API Schema 和 UI 中分别展示“服务”和“执行引擎”。
- **交付与验收：** 架构文档、OpenAPI 和 UI 不再把 FastAPI 称为模型；三种后端均通过同一契约测试。

### RC-010 实现首次启动双入口

- **执行步骤：** 首次运行检测 `onboarding_completed`；展示“使用 API”和“无 API，使用本地模型”两个主选项；两条向导完成后写入配置并允许从设置重新进入。
- **交付与验收：** 干净配置下必定进入双入口；任一路线完成后进入相同工作区首页，重启后状态正确恢复。

### RC-011 实现无 API 自动安装与模型选择

- **执行步骤：** 建立跨平台安装核心、PowerShell/Shell 包装脚本和 GUI 进度协议；完成环境检测、许可证确认、下载、校验、启动和健康检查；向用户呈现 Gemma/Qwen2.5-Coder选择。
- **交付与验收：** Windows 和 Linux 测试机至少各完成一次支持路线；失败可重试且不会留下被误判为已安装的状态。

### RC-012 落地主流 API 协议

- **执行步骤：** 定义统一 Provider 接口；分别实现 OpenAI、Gemini、Anthropic 原生 Adapter；再用兼容配置覆盖主流服务商并记录差异。
- **交付与验收：** 三种原生协议通过 Mock 契约和受控真实连接测试，兼容 Provider 不依赖硬编码特殊分支。

### RC-013 强制全页面兔兔品牌覆盖

- **执行步骤：** 建立路由清单和 `RabbitMark` 组件；为每条独立路由指定素材变体、位置、尺寸和替代文本；添加路由级自动检查与视觉快照。
- **交付与验收：** 覆盖矩阵无空项，所有独立页面在深浅主题和小窗口下可见且不遮挡功能信息。

### RC-014 建立真实完成门槛

- **执行步骤：** 将每个需求映射到 Issue、代码、测试、文档与证据；在 CI/Release 工作流中设置阻断检查；禁止仅凭接口存在或页面截图关闭 Issue。
- **交付与验收：** 发布候选版生成完整追踪报告，任何缺少测试或文档证据的强制需求都会阻止发布。

## B. 开源调研、许可证与 clean-room

### RC-015 固定所有调研仓库基线

- **执行步骤：** 用 GitHub API 获取 URL、默认分支、Commit SHA、更新时间、许可证和归档状态；保存不可变链接；每次升级单独开调研 PR。
- **交付与验收：** `docs/research/source-baselines.yml` 可被脚本校验，所有引用均指向 SHA 而非仅指向移动分支。

### RC-016 系统调研 OpenAI Codex

- **执行步骤：** 按 core、cli、tui、app-server、protocol、sandbox、MCP、config、search、Git、session、provider 分配调研章节；运行允许的官方示例；提炼接口、事件和设计取舍。
- **交付与验收：** 产出模块图、数据流、可借鉴项与不复用项，每条结论附固定 Commit 链接和 Apache-2.0 义务。

### RC-017 隔离 Codex CLI 开源与桌面观察

- **执行步骤：** 在来源登记中增加 `open-source`、`public-doc`、`behavior-only` 分类；CLI/App Server 源码走许可证复用流程；桌面 GUI 只记录公开行为和自制截图说明，不保存专有资产。
- **交付与验收：** 设计和代码审计可追溯每项来源，桌面实现中没有从未知 Codex GUI 源码复制的文件。

### RC-018 系统调研 OpenCode

- **执行步骤：** 固定 `anomalyco/opencode` 版本；分析 agent、cli、tui、desktop、app、server、protocol、llm、plugin、sdk、ui；对可复用代码做最小原型和许可证登记。
- **交付与验收：** 形成模块对照表和至少一个隔离原型，ADR 明确哪些模式采用、哪些因栈差异放弃。

### RC-019 调研 Claude Code 官方公开材料

- **执行步骤：** 汇总官方仓库、文档、插件示例、Hooks、工具与权限说明；按发布日期保存引用；把行为说明转成中立规格，不导入核心二进制或商业条款代码。
- **交付与验收：** 官方资料索引完整，规格审查能区分“文档事实”“黑盒观察”“推测”。

### RC-020 审核 Claude Agent SDK

- **执行步骤：** 检查 Python SDK 每个组件的许可证、README 商业条款和捆绑 CLI；验证消息、工具、MCP、Hook、权限、分叉接口；决定仅参考、可选集成或不采用。
- **交付与验收：** 专项 ADR 记录 SDK 代码与捆绑 CLI 的不同权利边界，默认构建不偷偷下载或分发 Claude Code CLI。

### RC-021 固定 source map 还原仓库证据

- **执行步骤：** 只通过元数据/README 记录目标仓库 SHA、许可证、归档、删除和 DMCA 状态；保存查询日期与响应摘要；定期复核状态变化。
- **交付与验收：** 证据表不包含还原源码正文，所有仓库均有风险级别与最后复核时间。

### RC-022 完成 source map 法律评估

- **执行步骤：** 根据公开许可证、官方条款和来源元数据整理版权、合同、商业秘密与再分发问题；不以购买法律服务作为前置条件；无法自行确认的内容继续冻结正文访问和使用。
- **交付与验收：** 项目治理文件记录允许/禁止范围和决策编号；无可靠公开依据时默认禁止复用，不得用“未购买法律意见”替代风险结论。

### RC-023 阻断无许可证仓库进入供应链

- **执行步骤：** 将相关仓库 URL、包名和哈希加入 denylist；在依赖、Git submodule、Docker、SBOM 和制品扫描中检测；预提交和 CI 同时阻断。
- **交付与验收：** 注入一个禁用 URL 的测试 PR 会失败，发布制品扫描结果为零命中。

### RC-024 禁止复制专有内容

- **执行步骤：** 制定禁止项清单；对提交运行字符串、相似片段和来源声明检查；人工审查 System Prompt、内部文案、测试、资源和私有常量。
- **交付与验收：** 每个相关 PR 带来源证明，发布前专项审计未发现逐字或机械改写内容。

### RC-025 建立 clean-room 人员与信息隔离

- **执行步骤：** 定义调研者和实现者角色；调研者只提交行为规格模板中的输入、输出、状态和约束；实现者账号无还原仓库访问材料，沟通留痕。
- **交付与验收：** 权限清单、规格模板和签署记录齐全，抽查规格无源文件名、原文或代码结构复刻。

### RC-026 依据合法材料独立设计

- **执行步骤：** 实现 Issue 仅引用 clean-room 规格、官方文档、合法 SDK、Codex/OpenCode 固定源码；在 PR 中填写来源；相同功能至少比较两种独立方案。
- **交付与验收：** 每个核心模块 PR 均有 `Provenance` 段，审查者能从合法来源重现设计依据。

### RC-027 建立独立黑盒兼容测试

- **执行步骤：** 根据公开文档设计测试输入；在合法安装的官方 Claude Code 上记录可观察结果；把抽象断言写成 Rabbit Code 测试，不复制泄露测试夹具。
- **交付与验收：** 测试夹具由项目自行生成并有创建记录，兼容差异报告可重复运行。

### RC-028 审计 MIT 分析资料的内容来源

- **执行步骤：** 检查每份分析资料的 LICENSE、引用比例、代码片段和上游声明；把原创分析与疑似 Anthropic 衍生内容分开；只批准风险可接受的抽象结论。
- **交付与验收：** 来源登记为每份资料标记 `approved/restricted/rejected`，未批准内容不能出现在实现 Issue。

### RC-029 监控 Anthropic 后续授权变化

- **执行步骤：** 建立季度检查任务，查看官方许可证、仓库和条款更新；发生变化时创建 ADR；在新 ADR 合并前保持原限制。
- **交付与验收：** 自动提醒和复核记录可查，任何复用范围变化都有明确批准日期和依据。

### RC-030 输出 source map clean-room 决策记录

- **执行步骤：** 汇总事实、风险、公开依据、允许/禁止清单、人员隔离和审计流程；由技术负责人记录决策并关联到 M0 门槛。
- **交付与验收：** `docs/legal/claude-source-map-clean-room.md` 完整且获批，M0 检查脚本能验证决策状态；不要求购买外部法律意见。

### RC-031 审核本地模型与运行器许可证

- **执行步骤：** 固定 Gemma、Qwen2.5-Coder、Ollama、llama.cpp 和模型文件版本；收集代码/模型许可证、模型卡、再分发和署名要求；逐一决定按需下载或允许打包。
- **交付与验收：** 模型清单每个条目都有下载源、哈希、许可证和 UI 确认要求，未知许可条目不能发布。

### RC-032 建立第三方复用登记册

- **执行步骤：** 设计来源、版本、文件、许可证、修改、NOTICE、分发形式、替代方案字段；把当前依赖和拟复制代码全部录入；CI 与 SBOM 对账。
- **交付与验收：** `THIRD_PARTY_NOTICES` 可从登记册生成，依赖扫描不存在无登记组件。

### RC-033 对不明来源实施 clean-room 重写

- **执行步骤：** 创建仅描述行为的规格；由未接触原代码的实现者编写至少两种候选设计；用独立测试验证并保存设计决策。
- **交付与验收：** PR 具有 clean-room 声明、实现者记录和原创提交历史，相似性审计通过。

### RC-034 检查名称、商标与发布渠道冲突

- **执行步骤：** 使用公开搜索、GitHub、包仓库和公开商标信息检查相似名称；不购买域名、不注册商标、不接入应用商店；记录相似名称与风险，必要时准备备用命名方案。
- **交付与验收：** 维护者记录命名结论，GitHub 仓库和计划使用的包名不存在已知直接冲突；不把域名、商标或应用商店控制权作为发布前置条件。

### RC-035 确认兔兔素材使用权

- **执行步骤：** 获取创作者/权利人书面声明，说明商业/开源使用、修改、派生和再分发权限；登记原文件哈希；确定署名和许可证展示位置。
- **交付与验收：** `docs/legal/rabbit-art-license.md` 和原始授权证据入库，缺失授权时禁止将素材加入发布包。

### RC-036 汇总调研交付物

- **执行步骤：** 将 Codex、OpenCode、Claude、模型和素材结论汇总；制作功能对比、ADR 索引、许可证清单和不复用清单；组织跨模块评审。
- **交付与验收：** M0 评审逐份签收，所有后续架构 Issue 都能关联至少一个已批准决策。

## C. 产品范围与验收体系

### RC-037 定义目标用户

- **执行步骤：** 为个人开发者、无 API 用户、多 Provider 用户、贡献者和团队分别编写 Persona、目标、约束和高频任务；访谈或用现有证据校准；标出冲突需求。
- **交付与验收：** Persona 文档包含可测任务和优先级，产品范围评审能说明每个核心功能服务的用户群。

### RC-038 定义首发平台矩阵

- **执行步骤：** 列出 Windows/Linux 的支持版本、x64/arm64、Shell、终端、GPU、未签名安装包和哈希校验要求；标记正式支持与尽力支持；为每格指定 CI 或实机验证方式。
- **交付与验收：** `docs/support-matrix.md` 无模糊项，首发必选格均有测试环境和负责人。

### RC-039 定义核心用户场景

- **执行步骤：** 将打开仓库到完成任务拆成端到端旅程；为阅读、规划、编辑、命令、测试、diff、恢复、切模、优化和离线对话写前置、主流程和失败分支；映射功能依赖。
- **交付与验收：** 每个场景都有可自动化的验收脚本或人工测试卡，覆盖原始需求。

### RC-040 定义 CLI/GUI/无头一致性

- **执行步骤：** 建立能力矩阵；共享 Agent、Provider、会话、权限和优化核心；仅将窗口、拖放、系统通知等保留为 GUI 专属。
- **交付与验收：** 同一能力的事件和存储 Schema 只有一份，矩阵中的差异均有明确理由。

### RC-041 划分 MVP、稳定版与增强版

- **执行步骤：** 依据依赖和风险把功能排入版本；把 R1-R6 全部放入首个稳定版；为延期项写不影响强制需求的理由和进入条件。
- **交付与验收：** 路线图经需求追踪检查，任何原始要求都没有被标记为无限期后续。

### RC-042 为功能定义完整状态验收

- **执行步骤：** 为每个功能填写成功、失败、取消、重试、降级、离线、拒绝和恢复状态；统一错误码和 UI 文案；把状态表转换为测试参数集。
- **交付与验收：** 状态覆盖报告无缺口，每个关键功能至少验证一个非成功分支。

### RC-043 建立端到端追踪关系

- **执行步骤：** 为需求分配 RC ID；在 ADR、Issue、PR、测试、文档和 Release Note 模板中添加 RC 字段；生成反向索引。
- **交付与验收：** 自动报告能从任一 RC ID 找到所有证据，孤立代码或孤立需求均被标红。

### RC-044 制定版本与迁移策略

- **执行步骤：** 采用 SemVer；定义 API/配置/数据库兼容窗口和弃用流程；为升级、失败回滚、旧客户端连接写规则和测试。
- **交付与验收：** 发布策略 ADR 获批，至少用两版测试数据完成前向迁移和受控回滚演练。

### RC-045 制定真实时间表和责任分工

- **执行步骤：** 完成原型后估算每个 RC 项的工作量与依赖；设置负责人、评审者、里程碑和缓冲；每周按证据更新而非按主观百分比更新。
- **交付与验收：** 项目看板所有首发项都有负责人、依赖、验收和目标里程碑，关键路径可视化。

## D. 现有 Prompt Optimizer 迁移

### RC-046 通过 ADR 决定技术栈保留范围

- **执行步骤：** 对 Python/FastAPI/React/Vite/TypeScript/SQLite/Typer/Docker 分别评估成熟度、打包、性能和维护成本；完成最小桌面 sidecar 原型；记录保留或替换结论。
- **交付与验收：** 技术栈 ADR 包含基准数据和替代方案，未批准前不做大规模重写。

### RC-047 回归现有核心模块

- **执行步骤：** 为评分、建议、规则、模板、优化、diff、历史、导出和评测建立固定样本；记录当前输出；重构后运行快照和语义断言。
- **交付与验收：** 回归套件全绿，任何有意变化都有迁移说明和新基线批准。

### RC-048 复用现有 FastAPI 接口能力

- **执行步骤：** 导出现有 OpenAPI；为 analyze、optimize、stream、task、auth、project、version 建契约测试；标记保留、版本化或替换接口并提供兼容层。
- **交付与验收：** 旧客户端测试在兼容期通过，新客户端只使用版本化 Schema。

### RC-049 拆分 Provider Adapter

- **执行步骤：** 定义 Provider Protocol、能力声明和统一事件；把现有 HTTP 实现拆为明确的 OpenAI-compatible Adapter；保留离线规则 Adapter，并移除协议猜测。Gemini、Anthropic 原生协议和本地模型运行器沿用共享边界，留给后续专门 RC。
- **交付与验收：** 现有离线实现和 OpenAI-compatible Adapter 通过同一 Mock 契约测试，新增 adapter 不需要修改 Agent/优化核心；本 RC 不发起真实 API 请求或引入付费资源。

### RC-050 保留离线规则最终降级

- **执行步骤：** 将 `OfflineRuleProvider` 注册为本地、无模型、零网络后端；定义触发条件和元数据；在 UI 中标为“离线规则”而非模型。
- **交付与验收：** 断网且无本地模型时优化仍成功，响应明确 `fallback=true` 和原因。

### RC-051 迁移 prompt-opt CLI

- **执行步骤：** 盘点旧命令、参数、配置和数据目录；在 `rabbit prompt` 下提供等价命令或兼容包装；输出弃用警告和迁移指南。
- **交付与验收：** 旧命令样例在兼容期得到相同结果，退出码和自动化脚本不被静默破坏。

### RC-052 决定本地 JWT 用户体系去留

- **执行步骤：** 分析单机账户隔离的真实需求；把应用资料、操作系统用户和 Provider 凭据分开建模；通过 ADR 选择移除、可选或保留 JWT。
- **交付与验收：** 登录流程不再混淆 API Key；选择移除时提供数据归属迁移，选择保留时有威胁模型和测试。

### RC-053 实现旧数据备份、迁移和恢复

- **执行步骤：** 版本化 SQLite Schema；升级前自动备份数据库和配置；实现幂等迁移、失败回滚、完整性检查和只读恢复工具。
- **交付与验收：** 使用真实 V2 副本完成升级、故障注入和恢复演练，原历史、模板和配置数量一致。

### RC-054 更新产品标识并提供兼容期

- **执行步骤：** 列出旧包名、环境变量、数据目录、API 标题和 CLI；新增 Rabbit Code 名称；按优先级读取旧配置并提示迁移，写入只使用新名称。
- **交付与验收：** 新装不创建旧目录，升级装可自动发现旧数据；兼容截止版本写入文档和警告。

### RC-055 保护 V2 可复现发布线

- **执行步骤：** 给 V2 分支和 Tag 设置保护；记录构建工具链与校验和；Rabbit Code 在独立 `codex/` 开发分支和新版本线工作，不改写 V2 Tag。
- **交付与验收：** V2 可从干净环境重建且哈希可核对，Rabbit Code 迁移文档明确分支与版本关系。

## E. 总体技术架构

### RC-056 建立 Monorepo

- **执行步骤：** 设计 `apps/desktop`、`apps/cli`、`backend/rabbit_code`、`packages/protocol`、`packages/ui`、`scripts`、`tests` 和 `docs` 边界；配置统一版本、依赖锁、格式与任务入口；迁移时保持每次提交可构建。
- **交付与验收：** 根目录命令能安装、检查、测试和构建全部工作区，模块依赖图不存在循环和跨层私有导入。

### RC-057 验证候选架构基线

- **执行步骤：** 制作 Python Agent Core + FastAPI + CLI + Tauri/React 的最小纵向原型；在 Windows/Linux 验证启动、流事件、取消和打包；与全 TypeScript 等替代方案比较启动、包体和维护成本。
- **交付与验收：** ADR 记录实测数据并锁定基线；原型能从 GUI/CLI 发起同一请求并收到一致事件。

### RC-058 将 FastAPI 建成统一 App Server

- **执行步骤：** 按 health、session、agent、prompt、provider、model、task 划分路由；注入共享服务层；增加启动令牌、版本协商和健康检查。
- **交付与验收：** GUI 和 CLI 均通过 App Server 完成端到端任务，OpenAPI 无重复业务接口且本地未授权请求返回 401。

### RC-059 统一 CLI 进程内与服务模式

- **执行步骤：** 定义 `AgentRuntime` 接口和统一事件类型；实现 `InProcessRuntime` 与 `AppServerRuntime`；用参数或自动发现选择模式，不在命令层分叉业务逻辑。
- **交付与验收：** 同一测试向两种 Runtime 重放，事件序列、结果和退出码语义一致。

### RC-060 限定 Tauri 桌面壳职责

- **执行步骤：** 只在 Tauri 实现窗口、文件选择、通知、更新、Keychain 桥接和 sidecar 管理；所有 Agent/Provider 逻辑通过协议访问；启用最小 command allowlist。
- **交付与验收：** Rust 层无模型请求或业务状态机，安全审查确认暴露给 WebView 的命令均有参数校验。

### RC-061 定义版本化协议层

- **执行步骤：** 为请求、会话、消息、内容块、工具、审批、流、diff、任务、错误和能力定义 Pydantic Schema；添加 `protocol_version` 与兼容规则；保存示例夹具。
- **交付与验收：** Schema 可生成 JSON Schema/OpenAPI，旧版夹具可在兼容窗口解析，未知重大版本被明确拒绝。

### RC-062 自动生成 TypeScript 客户端

- **执行步骤：** 从后端 OpenAPI 生成类型和客户端；把生成命令加入根任务与 CI；禁止手改生成目录并检测未提交差异。
- **交付与验收：** 后端 Schema 修改但未更新客户端时 CI 失败，前端生产代码不重复声明 API DTO。

### RC-063 划分同步、SSE、WebSocket 和 JSON-RPC

- **执行步骤：** 用普通 HTTP 处理 CRUD/健康，用 SSE 或 WebSocket 处理 Agent/优化流，用 JSON-RPC 处理需要双向请求的桌面控制；定义心跳、游标、重连和取消语义。
- **交付与验收：** 传输 ADR 获批，断网重连测试不会重复工具执行或丢失已确认事件。

### RC-064 设计 SQLite 与文件存储边界

- **执行步骤：** SQLite 保存元数据、会话和索引；日志、附件、模型、缓存保存到版本化目录；为写操作建立事务、锁、临时文件和原子重命名策略。
- **交付与验收：** 并发与崩溃注入测试无半写记录，清理缓存不会删除会话或模型之外的数据。

### RC-065 实现分层配置

- **执行步骤：** 定义默认、用户、工作区、会话、CLI 临时覆盖的优先级；为每个配置项标注类型、敏感性和作用域；提供合并结果及来源查询。
- **交付与验收：** 参数化测试覆盖冲突优先级，UI/CLI 能显示非敏感值来源且密钥只显示引用。

### RC-066 解耦核心模块

- **执行步骤：** 为 Agent、Provider、Tool、Permission、Storage、PromptOptimizer 建立 Protocol/接口；通过构造器依赖注入；禁止 UI 或路由直接实例化具体 Provider。
- **交付与验收：** 单元测试可用内存实现替换每个边界，依赖规则检查阻止反向导入。

### RC-067 管理前后台进程生命周期

- **执行步骤：** 桌面端选择空闲随机端口并启动 sidecar；等待健康就绪、传递一次性令牌、监听退出；实现优雅关闭、异常拉起上限、版本不匹配提示和僵尸清理。
- **交付与验收：** 启动失败、端口占用、崩溃和强退四类测试均能恢复或给出可操作错误，退出后无残留进程。

## F. Agent Core

### RC-068 实现可观测 Agent 状态机

- **执行步骤：** 定义 `received/context/model/tool_pending/approval/tool_running/continuing/completed/failed/cancelled` 状态；把每次转换写成不可变事件；状态处理器只做单一职责并持久化检查点。
- **交付与验收：** 状态转换表与代码一致，非法转换被拒绝，重放事件可重建相同会话状态。

### RC-069 支持交互、单次、管道和 JSON 模式

- **执行步骤：** 在 CLI 解析器定义 `rabbit`、`rabbit run`、stdin 和 `--output json/jsonl`；共享 Runtime；为结果、错误和取消制定稳定退出码。
- **交付与验收：** TTY、非 TTY、管道和 JSON 快照测试通过，机器模式不输出 ANSI 或交互提示。

### RC-070 实现 Plan/Edit/高权限模式

- **执行步骤：** 用能力集合定义三种模式；Plan 禁止写入，Edit 限工作区，高权限仍需危险操作确认；在会话事件中记录模式变化并同步 GUI/CLI。
- **交付与验收：** 权限矩阵测试验证每种工具与路径，切换模式需要明确用户动作且不会扩大既有后台任务权限。

### RC-071 统一流式输出与中断

- **执行步骤：** 定义文本增量、进度摘要、工具卡、任务进度、警告和终止事件；UI/TUI 按事件渲染；用户中断触发取消令牌并保存已完成状态。
- **交付与验收：** 流式顺序和最终聚合一致，部分失败可见且 Ctrl+C/取消按钮在规定时间内停止下游任务。

### RC-072 实施资源与费用预算

- **执行步骤：** 在会话配置最大轮次、墙钟超时、输入/输出 Token、费用、上下文和并发数；每轮原子扣减；接近上限时预警并在超限时安全终止。
- **交付与验收：** 边界值和并发测试无超扣，终止事件包含具体预算项及已用数值。

### RC-073 实现暂停、取消、重试和幂等

- **执行步骤：** 为请求和工具分配幂等键；持久化可恢复检查点；区分可重试模型调用与不可安全重试的写操作；实现暂停/恢复/重新生成命令。
- **交付与验收：** 崩溃恢复不会重复提交写工具，取消后无继续产生的事件，重试保留完整审计链。

### RC-074 实现受控子 Agent

- **执行步骤：** 定义子 Agent 输入、上下文副本、只读/写权限上限、预算和并发槽；主 Agent 创建、监控并汇总；禁止子 Agent 自行扩大权限或无限递归。
- **交付与验收：** 并行探索测试结果可合并、取消可级联、最大深度和并发限制生效。

### RC-075 实现 Hooks

- **执行步骤：** 定义 session/tool/permission/error 前后事件和 Hook Schema；支持超时、顺序、失败策略和输出校验；从项目/用户配置加载并先做权限评估。
- **交付与验收：** 示例 Hook 可允许、拒绝或注入安全反馈，异常 Hook 不会令主进程失控且有审计记录。

### RC-076 实现 MCP 生命周期

- **执行步骤：** 支持 stdio、Streamable HTTP 等批准传输；实现配置加载、进程启动、能力发现、认证、重连、取消和关闭；将 MCP 工具映射到统一 Tool Schema。
- **交付与验收：** 官方示例服务器和故障 Mock 通过，退出后子进程清理，未授权服务器不能自动获得写权限。

### RC-077 实现技能与插件体系

- **执行步骤：** 定义 manifest、版本、入口、权限和兼容范围；建立安装、启用、禁用、升级和卸载流程；插件能力通过受控 API 暴露。
- **交付与验收：** 示例插件可安装运行并被完整卸载，来源、版本、哈希或权限不合格的插件被拒绝。

### RC-078 实现模型能力协商

- **执行步骤：** Provider 返回文本、视觉、工具、结构化输出、上下文和推理参数能力；Agent 在请求前检查并选择兼容策略；不支持项给出替代建议。
- **交付与验收：** 能力矩阵参数化测试覆盖降级和拒绝，不会向不支持工具调用的模型发送工具 Schema。

### RC-079 防止记录隐藏思维链

- **执行步骤：** 在 Provider 层丢弃或隔离不可展示的推理字段；日志只记录允许的摘要、Token 和状态；UI 使用预定义进度文案而非隐藏内容。
- **交付与验收：** 日志/数据库快照扫描不存在隐藏推理字段，用户导出只包含公开响应和简短依据。

## G. 上下文、记忆与会话

### RC-080 自动识别项目环境

- **执行步骤：** 从当前路径向上查找 Git 根；调用 Git 获取分支、worktree 和状态；按标志文件识别语言、包管理器、构建命令和项目指令；缓存并监听变化。
- **交付与验收：** 多语言、子目录、非 Git 和 worktree 夹具均返回正确环境，失败不会阻断打开项目。

### RC-081 加载分层项目指令

- **执行步骤：** 定义全局指令、仓库 `AGENTS.md`、Rabbit 专属文件和目录级文件的发现顺序；只加载适用路径；展示来源并检测冲突/超长。
- **交付与验收：** 嵌套目录测试得到正确合并结果，用户可查看实际生效指令且敏感文件规则优先。

### RC-082 支持多类上下文附件

- **执行步骤：** 为文件、目录、代码选区、图片、附件、终端、diff 和诊断定义内容块；上传前验证路径、类型、大小与权限；提供预览和移除。
- **交付与验收：** 每种内容块端到端可发送并在会话恢复后重建，超限或不安全附件被明确拒绝。

### RC-083 实现安全搜索与索引

- **执行步骤：** 合并 `.gitignore`、Rabbit Ignore、用户排除和敏感路径；检测二进制/大文件和符号链接边界；索引采用增量更新和可取消扫描。
- **交付与验收：** 忽略与逃逸夹具不被读取，索引结果与基准工具一致且取消后停止磁盘活动。

### RC-084 管理上下文预算与压缩

- **执行步骤：** 估算各内容块 Token；按必需指令、当前任务、相关文件、历史顺序分配预算；去重、缓存并在阈值触发结构化摘要，保留摘要来源。
- **交付与验收：** 长会话不会超过模型上限，压缩前后关键事实问答基准达到设定保真率。

### RC-085 区分四类记忆

- **执行步骤：** 为临时、会话、项目、用户记忆建立独立表和作用域；写入前显示来源/用途；提供查看、编辑、禁用、逐项删除和全清理。
- **交付与验收：** 作用域隔离测试防止跨项目泄漏，关闭记忆后不再读取或写入对应数据。

### RC-086 实现完整会话操作

- **执行步骤：** 建立会话 CRUD、标题、搜索索引、置顶、归档、软删除/恢复、继续、分叉和导出服务；所有操作写审计事件并支持分页。
- **交付与验收：** API、CLI、GUI 契约一致，分叉不修改原会话，删除/恢复符合保留策略。

### RC-087 实现检查点与回滚

- **执行步骤：** 在写工具前记录工作树基线，在每组变更后保存 diff、工具和验证结果；回滚前检查用户并发修改；只逆转 Agent 产生的可证明变更。
- **交付与验收：** 修改、用户并发编辑、冲突和部分回滚测试均不丢用户数据，UI 显示回滚范围。

### RC-088 隔离工作区与 worktree

- **执行步骤：** 为会话绑定规范化工作区 ID；可选创建独立 Git worktree；对进程、缓存、终端和写权限加工作区边界；处理删除和清理。
- **交付与验收：** 两个并行任务不能互读未授权路径或混用终端，worktree 清理不删除用户分支。

### RC-089 加固会话数据库

- **执行步骤：** 启用迁移表、WAL/适当同步级别和完整性检查；启动时检测未完成事务；提供自动备份、恢复副本、导出和隐私清理。
- **交付与验收：** kill、磁盘错误和损坏副本演练均能恢复到已提交检查点或给出只读救援路径。

## H. 工具系统与编码工作流

### RC-090 实现文件工具集

- **执行步骤：** 分别实现 read/list/search/edit/patch/create/move/delete；对路径规范化、工作区边界、大小、编码和权限做统一前置校验；写操作生成 diff。
- **交付与验收：** 正常、越界、符号链接、二进制、并发修改和权限拒绝测试通过。

### RC-091 实现跨 Shell 命令工具

- **执行步骤：** 建立 shell adapter，参数数组优先于字符串拼接；明确 PowerShell/cmd/Bash/zsh 编码、引用、环境和换行；捕获 stdout/stderr/exit/signal。
- **交付与验收：** Windows/Linux 包含中文路径、空格、引号、长输出和中断的夹具全部通过。

### RC-092 实现 Git 工具集

- **执行步骤：** 使用结构化 Git 命令封装 status/diff/log/branch/worktree/stage/commit/conflict；操作前检查仓库和脏状态；push/PR 单独触发远程授权。
- **交付与验收：** 本地操作测试通过，任何远程写没有显式许可时被阻止并记录原因。

### RC-093 标准化开发诊断结果

- **执行步骤：** 定义测试、Lint、类型、构建、包管理器和 LSP 的 Diagnostic Schema；为常用工具写解析器；解析失败时保留原始输出。
- **交付与验收：** CLI/GUI 对同一诊断显示一致文件、行号、级别和命令，至少覆盖项目现有工具链。

### RC-094 管理后台进程

- **执行步骤：** 建立进程注册表、PTY/非 PTY 选择、端口探测、日志游标和状态机；支持后台启动、跟踪、停止、超时和进程树清理。
- **交付与验收：** 并发进程、父进程崩溃、端口占用和强制停止测试无孤儿进程。

### RC-095 实现原子补丁工具

- **执行步骤：** 解析结构化补丁；校验目标基线哈希和上下文；在临时副本应用、保留编码/换行后原子替换；冲突时不写入。
- **交付与验收：** 正常、多文件、编码、上下文漂移和中途失败测试证明全有或全无。

### RC-096 处理工具异常和大输出

- **执行步骤：** 为输出设置内存/磁盘上限与截断标记；定义超时和可重试条件；二进制转元数据；区分失败、部分成功和用户取消。
- **交付与验收：** 巨量日志不会耗尽内存，截断可继续读取，非零退出码不被误判为系统异常。

### RC-097 定义工具元数据契约

- **执行步骤：** 每个工具提供名称、描述、JSON Schema、权限、读写影响、幂等、取消和审计字段；启动时注册并验证重复/非法 Schema。
- **交付与验收：** 工具目录可生成文档，缺少必填元数据的工具不能启动或进入模型请求。

### RC-098 统一工具结果内容块

- **执行步骤：** 定义 text、diagnostic、diff、file、image、progress、error 内容块；后端统一产出；CLI/GUI 只实现渲染器而不重新解释工具私有结果。
- **交付与验收：** 同一事件夹具在 API、CLI、GUI 快照语义一致，未知块可安全降级显示。

### RC-099 提供受控扩展工具接口

- **执行步骤：** 为浏览器、数据库和外部服务定义插件/MCP 接口；能力安装时声明网络和写权限；默认禁用并按会话审批。
- **交付与验收：** 示例扩展在未授权时无法联网或写入，授权撤销后立即失效。

## I. CLI/TUI

### RC-100 定义 rabbit CLI 命令面

- **执行步骤：** 设计交互、run、continue、resume、model、mode、output 等参数；生成 `--help`；保持参数解析与配置覆盖规则一致。
- **交付与验收：** CLI 参考文档由代码生成，参数组合、错误输入和退出码测试覆盖完整。

### RC-101 构建 Rabbit Code TUI

- **执行步骤：** 实现固定输入区、滚动输出、工具/权限/计划/diff 卡片和用量状态；消费统一事件；在窄终端降级布局且支持无颜色模式。
- **交付与验收：** 80x24、宽屏和无颜色快照通过，长流式输出不破坏输入焦点。

### RC-102 完善终端输入体验

- **执行步骤：** 增加多行编辑、历史搜索、补全、文件提及、附件路径和大段粘贴确认；快捷键存入非敏感配置；处理 IME 和 Unicode。
- **交付与验收：** 中英文输入、超长粘贴、历史和快捷键冲突测试通过，用户可恢复误清空草稿。

### RC-103 实现斜杠命令

- **执行步骤：** 建立命令注册表和补全；实现 help/model/provider/permission/plan/context/session/clear/compact/mcp/plugin/doctor/exit；每条命令定义参数与是否影响会话。
- **交付与验收：** 命令注册表自动生成帮助，未知命令给建议，关键命令有单元和交互测试。

### RC-104 支持非交互 CI

- **执行步骤：** 检测 TTY；无 TTY 时采用显式权限策略，缺少策略即快速失败；输出稳定 JSON/文本和明确退出码，禁止等待输入。
- **交付与验收：** CI 夹具在超时内完成，危险操作返回专用退出码且没有悬挂进程。

### RC-105 实现 dry-run 和机器事件流

- **执行步骤：** `--dry-run` 只生成计划与拟调用工具；`--read-only` 强制能力收窄；`--output jsonl` 输出版本化事件；日志写 stderr 或独立文件。
- **交付与验收：** dry-run 文件哈希不变，JSONL 每行可解析且 stdout 不混入人类日志。

### RC-106 共享 CLI/GUI 配置与数据

- **执行步骤：** 两端使用同一配置服务、密钥引用、模型注册、会话库、权限引擎和优化接口；移除各端本地副本；用文件锁/服务模式处理并发。
- **交付与验收：** 在一端修改非敏感设置后另一端实时或重载可见，并发写不造成数据损坏。

### RC-107 验证主流终端兼容性

- **执行步骤：** 建立 Windows Terminal/PowerShell/cmd/WSL 和 Linux 终端矩阵；运行输入、颜色、尺寸、信号、路径与剪贴板测试；记录已知限制。
- **交付与验收：** 支持矩阵每个必选环境有测试证据，阻断级问题在发布前清零。

### RC-108 提供 CLI 运维辅助

- **执行步骤：** 生成 Bash/zsh/fish/PowerShell 补全；实现安装路径与版本检查、`rabbit doctor`、缓存清理和保留/删除数据的卸载命令。
- **交付与验收：** 各支持 Shell 可加载补全，doctor 能检测常见缺失项，卸载测试不误删用户项目。

## J. 桌面 GUI 信息架构

### RC-109 实现首次启动页

- **执行步骤：** 创建独立 Onboarding 路由；读取配置、App Server、密钥库和本地运行器健康状态；呈现两个主入口、Rabbit Code 标识与首页兔兔素材。
- **交付与验收：** 新装、已有配置、服务异常三种 E2E 状态正确，页面只保留两个主要选择且键盘可完成操作。

### RC-110 实现工作区首页

- **执行步骤：** 从统一服务加载最近项目/任务和模型状态；实现打开目录、移除历史、快速新建任务；为不存在或无权限项目提供修复动作。
- **交付与验收：** 最近项排序与持久化正确，空状态和错误状态可用，打开项目后进入对应任务上下文。

### RC-111 实现主任务三栏布局

- **执行步骤：** 建立左侧工作区/会话、中间消息/Composer、右侧计划/上下文/diff 可折叠区和终端抽屉；使用稳定网格与持久化面板尺寸；小窗口切换为单面板导航。
- **交付与验收：** 常见桌面与最小窗口无重叠，切换面板不丢草稿、滚动或终端状态。

### RC-112 实现变更审查面板

- **执行步骤：** 从检查点服务加载文件树和 diff；支持逐文件/逐块接受、拒绝、查看原文件、回滚与运行验证；检测工作树漂移并阻止盲目应用。
- **交付与验收：** diff 夹具、并发编辑和冲突测试通过，接受/拒绝后磁盘与 UI 状态一致。

### RC-113 实现终端与进程面板

- **执行步骤：** 接入 PTY 服务；实现多标签、尺寸同步、后台任务列表、状态和停止；限制终端绑定工作区并处理关闭确认。
- **交付与验收：** Shell 输入输出、窗口缩放、进程退出和恢复测试通过，关闭应用不遗留进程。

### RC-114 实现 Provider 与模型页

- **执行步骤：** 展示 Provider 列表、配置状态、模型发现与手动 ID；提供连接测试、能力标签、费用/未知费用提示和默认选择；敏感字段走密钥库。
- **交付与验收：** 新增、编辑、禁用、删除和测试流程 E2E 通过，Key 不出现在 DOM 快照或日志。

### RC-115 实现本地模型安装页

- **执行步骤：** 串联硬件检测、模型推荐、许可证、下载/校验/加载状态；提供暂停/取消/修复/卸载；通过 App Server 订阅进度。
- **交付与验收：** 成功、断网、磁盘不足、哈希失败和取消场景可恢复，状态与实际文件/进程一致。

### RC-116 实现提示词资产页

- **执行步骤：** 用分页服务加载模板、版本、评分和收藏；支持搜索、过滤、比较、导入导出；从条目可回填当前 Composer，但不取代对话内主流程。
- **交付与验收：** 大量历史仍可流畅浏览，导入校验失败不污染数据库，回填不会自动发送。

### RC-117 实现设置页

- **执行步骤：** 按外观、语言、终端、权限、沙箱、数据、隐私、更新、快捷键、MCP、插件和高级配置分区；显示每项作用域和来源；危险重置需确认。
- **交付与验收：** 设置变更持久化且即时生效范围正确，工作区设置不会泄漏到其他项目。

### RC-118 实现诊断、关于与更新页

- **执行步骤：** 聚合应用/sidecar/运行器版本、健康、日志目录、许可证和更新信息；提供复制脱敏诊断、检查更新和查看开源声明。
- **交付与验收：** 脱敏测试不包含 Key/源码正文，组件故障能显示具体修复建议。

### RC-119 统一空、错、离线与弹窗状态

- **执行步骤：** 在 UI 库定义 Empty/Error/Offline/Permission/Install Dialog；统一标题、描述、图标、主次操作和焦点管理；禁止页面各自造不同模式。
- **交付与验收：** Storybook/组件快照覆盖所有状态，弹窗具备焦点陷阱、Escape 规则和屏幕阅读器语义。

### RC-120 实现窗口和系统集成策略

- **执行步骤：** 决定单窗/多窗和多工作区模型；保存尺寸/位置/面板；实现主题、高 DPI、通知和可选托盘；处理多显示器越界恢复。
- **交付与验收：** 重启和显示器变化后窗口可见，系统主题切换正确，通知权限拒绝不会影响任务。

### RC-121 验证标题栏方案

- **执行步骤：** 对原生与自绘标题栏做 Windows/Linux 原型；测试拖拽区域、最大化、双击、系统菜单、缩放、高对比和屏幕阅读器；用 ADR 选择。
- **交付与验收：** 选择方案在支持矩阵无阻断缺陷，拖拽区域不覆盖交互控件。

## K. 兔兔素材与视觉系统

### RC-122 登记兔兔源素材

- **执行步骤：** 在取得授权后复制源文件到受控 `assets/source`；记录 SHA-256、尺寸、色彩空间、来源和许可证；构建仅引用仓库内派生资源。
- **交付与验收：** 发布包在断开原桌面路径时正常显示，素材登记与哈希一致。

### RC-123 制作兔兔派生资产规范

- **执行步骤：** 定义透明图、头像、小标、空状态、浅/深主题和应用图标尺寸；用可重复脚本或设计源导出；记录安全区和最小尺寸。
- **交付与验收：** 资产清单无手工未知版本，各尺寸在 1x/2x 与高 DPI 检查清晰。

### RC-124 规划页面级素材用法

- **执行步骤：** 首页用完整形象，工作页限定侧栏/页角/水印/空状态；为代码、终端、diff 定义禁入区；由设计评审逐页确认。
- **交付与验收：** 视觉稿中品牌可见但不降低内容对比度或可点击面积。

### RC-125 实现统一 RabbitMark 槽位

- **执行步骤：** 在路由 Shell 增加 `RabbitMark` 槽位和变体参数；独立页面必须显式选择变体；弹窗按层级配置，避免嵌套重复。
- **交付与验收：** 路由测试检测缺失变体并失败，组件不接受任意外部图片路径。

### RC-126 建立兔兔覆盖矩阵

- **执行步骤：** 从路由表自动生成页面行；填写素材、位置、尺寸、主题、响应式、替代文本和负责人；与视觉快照 ID 关联。
- **交付与验收：** 矩阵无空单元且 CI 对新增路由要求同步登记。

### RC-127 优化源图交付格式

- **执行步骤：** 裁掉无效留白、设定焦点和透明背景；以质量阈值导出 PNG/WebP；对比大小、清晰度和色偏并保留无损母版。
- **交付与验收：** Lighthouse/包体检查满足预算，视觉对比无明显损失，母版不被构建脚本覆盖。

### RC-128 设计小尺寸兔兔标识

- **执行步骤：** 单独绘制或简化轮廓、帽子/耳朵等识别特征；测试 16/20/24/32px 深浅背景；必要时提供单色版。
- **交付与验收：** 盲测或设计评审在最小尺寸仍可识别，不使用缩小整张原图的模糊结果。

### RC-129 控制品牌与功能层级

- **执行步骤：** 定义工作区内容优先级、素材最大占比和透明度范围；在高密度页面减少装饰；用真实代码、长日志和 diff 做视觉测试。
- **交付与验收：** 任务完成时间和可读性测试不因素材显著下降，关键错误/按钮始终优先。

### RC-130 建立 Design Token

- **执行步骤：** 在 `packages/ui` 定义颜色、字体、间距、边框、阴影、图标尺寸、动效、状态色和代码字体；生成 CSS 变量与 TypeScript 类型；禁止页面硬编码主题值。
- **交付与验收：** Token 文档和主题快照可生成，颜色扫描无未登记的主界面硬编码值。

### RC-131 统一图标与 Sparkles 语言

- **执行步骤：** 使用现有 Lucide 图标库；为每个工具动作指定图标、Tooltip 和可访问名；星星只代表提示词优化，不复用于无关操作。
- **交付与验收：** 图标清单通过设计审查，未知图标均有 Tooltip，重复语义无冲突。

### RC-132 落实视觉无障碍

- **执行步骤：** 建立键盘顺序、焦点环、ARIA、对比度、200% 缩放和 `prefers-reduced-motion` 规则；用 axe 与人工屏幕阅读器测试；修复阻断问题。
- **交付与验收：** WCAG 2.2 AA 目标检查通过，关键流程仅键盘可完成。

### RC-133 建立全页面视觉回归

- **执行步骤：** 用 Playwright 在桌面/小窗、深/浅主题、1x/2x 生成截图；加入兔兔存在性和像素差阈值；动态内容使用稳定夹具。
- **交付与验收：** 每条独立路由至少四组基线，重叠、裁切、溢出和主题错误会阻断 CI。

## L. 对话框与菱形星星交互

### RC-134 确定星星按钮位置

- **执行步骤：** 基于 Trae 参考制作 2 至 3 个 Rabbit Code 自有布局；在模型选择、语音、附件、发送间验证点击路径和主次；锁定响应式规则。
- **交付与验收：** 设计评审和可用性测试确认不会误认发送按钮，长模型名时仍不溢出。

### RC-135 实现星星完整状态机

- **执行步骤：** 定义 idle/hover/pressed/loading/success/error/disabled/cancelling；固定容器尺寸；将状态由请求 ID 驱动，防止旧请求回写。
- **交付与验收：** Storybook 及组件测试覆盖全部状态和转换，快速连点只有一个有效任务。

### RC-136 完善 Tooltip 和可访问命名

- **执行步骤：** 图标按钮使用 `aria-label="优化输入内容"`；Tooltip 延时显示并支持键盘；检查与发送、语音、附件和模型选择的语义区别。
- **交付与验收：** axe 无名称错误，屏幕阅读器按正确顺序读出，Tooltip 不遮挡输入。

### RC-137 建立输入快照与边界处理

- **执行步骤：** 点击时记录文本、revision、光标和附件引用；空输入禁用，只有附件提示不支持，超长按预算拒绝/截断选择，已有任务给取消或等待选项。
- **交付与验收：** 边界参数测试无重复请求或静默截断，原始快照可恢复。

### RC-138 处理优化期间并发编辑

- **执行步骤：** 每次编辑增加 revision；优化结果仅在 revision 未变时允许直接替换；已变化则打开比较并提供重新优化；取消向后端传播。
- **交付与验收：** 延迟响应测试证明旧结果不会覆盖新输入，取消后按钮回到可用状态。

### RC-139 禁止默认自动发送

- **执行步骤：** 将优化完成态与发送动作完全分离；结果先进入预览/编辑状态；提供采用、部分采用、撤销和发送按钮，默认焦点不在发送。
- **交付与验收：** E2E 证明优化完成不会产生对话消息，只有明确发送操作才调用 Agent。

### RC-140 实现优化结果比较操作

- **执行步骤：** 使用结构化 diff 生成原文/结果视图；支持行内/并排、复制、全部/选区替换、重试、撤销和恢复；长文本虚拟化。
- **交付与验收：** 中文、代码块和长文本 diff 正确，撤销能恢复逐字原文和光标位置。

### RC-141 展示优化元数据并保护秘密

- **执行步骤：** 响应展示 Provider、模型、local/cloud、fallback、耗时和错误码；只使用 Provider 显示名与密钥引用；错误先过脱敏器。
- **交付与验收：** 快照和日志扫描无 API Key/System Prompt，降级路径对用户清晰可见。

### RC-142 保护结构化输入语义

- **执行步骤：** 在发送优化前解析代码围栏、文件提及、附件 token、命令和 `{{variable}}`；标记不可改区；输出后验证标记数量和格式，失败时不自动采用。
- **交付与验收：** 专项语料的占位符、代码块和提及保持率为 100%，破坏结构时显示可恢复错误。

### RC-143 保持用户语言

- **执行步骤：** 检测主要语言和混合比例；在优化请求中明确保持语言；输出后做脚本/语言异常检测，用户显式翻译意图优先。
- **交付与验收：** 中英及混合评测达到设定语言保持率，非翻译任务不会整体改语言。

### RC-144 集成模板与高级优化控制

- **执行步骤：** 在 Composer 关联 Popover/Drawer 放置模板、场景、角色、强度、评分、历史和版本；状态绑定当前草稿；高级区默认收起。
- **交付与验收：** 用户不离开任务页可完成所有操作，关闭抽屉不丢草稿或模板选择。

### RC-145 完善键盘、焦点和触控

- **执行步骤：** 定义可配置触发快捷键；打开/关闭结果层保存并恢复焦点；用 live region 播报进度；按钮满足触控目标尺寸。
- **交付与验收：** 仅键盘和触屏流程均完成，屏幕阅读器不会重复播报流式每个 token。

### RC-146 持久化优化版本并允许关闭

- **执行步骤：** 保存 original/result/accepted/provider/model/version/timestamps；设置 `save_prompt_history`；关闭时只保留完成请求所需内存数据并按策略清理。
- **交付与验收：** 开关前后数据库写入测试符合预期，历史页能准确显示采用状态且支持删除。

## M. Prompt Optimization Service

### RC-147 建立唯一优化服务

- **执行步骤：** 在核心层定义 `PromptOptimizationService.optimize/stream/cancel`；GUI、CLI、API 和任务只依赖该服务；移除重复优化拼接逻辑。
- **交付与验收：** 代码搜索只有一个路由决策实现，四个入口的契约测试输出一致。

### RC-148 选择云端优化模型

- **执行步骤：** 优先读取会话 Provider/模型；如配置独立优化器则验证可用性后覆盖；保存选择作用域和健康状态，不可用时询问或按已授权规则降级。
- **交付与验收：** 选择优先级参数化测试通过，模型切换立即反映到元数据。

### RC-149 无 API 时调用本地模型

- **执行步骤：** GUI 始终调用 Loopback FastAPI；服务读取当前本地模型和运行器健康；通过 Adapter 发起流式生成并支持取消。
- **交付与验收：** 网络完全断开时 Gemma/Qwen 路线可优化，抓包确认没有外部请求。

### RC-150 本地不可用时降级离线规则

- **执行步骤：** 检测未安装、未就绪、OOM、超时等错误；只对允许类别切换 `OfflineRuleProvider`；响应写入 fallback 原因并给出安装/修复入口。
- **交付与验收：** 故障注入后仍返回有效结果，UI 显示“离线规则”且不冒充模型结果。

### RC-151 定义优化路由韧性策略

- **执行步骤：** 配置优先级、超时、重试、限流、熔断和取消；备用云 Provider 必须逐项授权；重试使用幂等请求 ID。
- **交付与验收：** 状态机测试覆盖熔断开闭和取消，任何未授权云服务请求为零。

### RC-152 实现流式优化事件

- **执行步骤：** 定义 started/analysis/delta/saved/completed/cancelled/error Schema 和序号；后端按顺序发送并持久化终态；客户端支持游标重连。
- **交付与验收：** 流事件契约和断线测试通过，重连不会重复保存版本。

### RC-153 管理优化 System Prompt

- **执行步骤：** 将 Prompt 放入版本化资源；为每个 Provider 适配必要消息格式；加入仅优化用户文本、保护不可改区和抵抗指令注入的规则；记录版本到结果。
- **交付与验收：** Prompt 变更必须伴随评测报告，注入测试不能诱导泄露系统内容或执行工具。

### RC-154 支持优化目标参数

- **执行步骤：** 定义清晰度、完整度、约束、格式、角色、示例、代码、简洁度和语言保持枚举/权重；UI 预设映射到 Schema；Provider 不支持时在本地合成指令。
- **交付与验收：** 每个目标至少有评测样本，API 对非法组合返回可理解的 400。

### RC-155 组合规则、模板与模型

- **执行步骤：** 先运行规则分析得到缺口；选择模板片段；把结构化建议交给模型重写；模型失败时规则层独立生成；避免无依据扩写。
- **交付与验收：** 消融评测比较规则、模型和组合模式，组合模式达到预先设定的质量与语义保持门槛。

### RC-156 验证优化输出

- **执行步骤：** 检查类型、空值、长度、不可改标记、语言和结构；过滤控制字符；解析失败时进行一次受限修复或返回原结果比较，不自动覆盖。
- **交付与验收：** 模糊测试和恶意响应测试无崩溃，非法输出不能写入 Composer。

### RC-157 记录最小必要指标

- **执行步骤：** 记录质量分、延迟、Provider、模型、fallback 和错误类别；提示词正文默认不进遥测；本地日志按隐私设置脱敏/哈希。
- **交付与验收：** 指标可生成聚合报告，隐私测试确认关闭日志/遥测后没有内容残留。

### RC-158 建立优化评测集

- **执行步骤：** 扩展现有数据集到编码、商务、教育、创意、长文本、代码块、变量、中文和对抗样本；定义自动评分和双人盲评；固定版本和随机种子。
- **交付与验收：** 数据集规模、标签分布和基线报告可复现，Prompt/模型变更必须跑回归。

## N. Provider 与 API 协议

### RC-159 统一“使用 API”产品措辞

- **执行步骤：** 全局检索“API 登录”；改为“使用 API/配置 Provider”，对真正 OAuth 登录单独命名；由 UX 和翻译词汇表统一。
- **交付与验收：** UI/文档无误导性“用 API Key 登录 Rabbit Code”文案，用户测试能正确理解凭据去向。

### RC-160 实现 OpenAI Chat Completions Adapter

- **执行步骤：** 支持 Base URL、Key、组织/项目头、模型、messages、SSE、tool calls 和常见兼容差异；请求/响应转换在 Adapter 内；增加超时和错误映射。
- **交付与验收：** 官方/Mock/至少一个兼容端点契约通过，Key 和完整请求正文不出现在默认日志。

### RC-161 实现 OpenAI Responses Adapter

- **执行步骤：** 对照当前官方 Schema 实现 input/content、response events、tool calls、structured output 和取消；通过能力探测决定使用 Responses 或 Chat；不把 Responses 参数发送给兼容旧端点。
- **交付与验收：** 两种 API 使用独立契约夹具，Provider 不支持 Responses 时可预测降级且不重复计费。

### RC-162 实现 Gemini 原生 Adapter

- **执行步骤：** 实现 `generateContent`、`streamGenerateContent`、contents/parts、System Instruction、function calling、安全设置和错误解析；支持 API Key 与批准的 Google 认证方式。
- **交付与验收：** 文本、流式、工具、内容过滤和错误契约通过，OpenAI 格式假设不会泄漏到 Gemini 请求。

### RC-163 实现 Anthropic Messages Adapter

- **执行步骤：** 实现 Messages、System、content blocks、SSE 事件、tool use/result、usage 和缓存/扩展能力探测；按官方头和版本要求构造请求。
- **交付与验收：** 多内容块与工具循环测试通过，不支持的 Beta 功能默认关闭并有明确能力标记。

### RC-164 正确映射“Claude Code 格式”

- **执行步骤：** UI 将该选项解释为 Anthropic Messages 或经审批的 Agent SDK；只接受官方 API Key/OAuth 途径；明确拒绝导入 Claude Code 订阅 Cookie、内部令牌或逆向登录。
- **交付与验收：** 帮助文档说明边界，凭据解析器不存在订阅 Token 抓取路径，安全测试验证拒绝未知格式。

### RC-165 支持 Azure、Vertex 与 Bedrock

- **执行步骤：** 为 Azure OpenAI 处理资源端点、部署名和 API 版本；为 Vertex/Bedrock 处理项目/区域/凭据链和模型映射；凭据使用各平台官方 SDK/签名流程。
- **交付与验收：** 每个托管变体有 Mock 契约和可选真实冒烟，区域/部署错误被归入统一错误类型。

### RC-166 配置主流 OpenAI 兼容服务

- **执行步骤：** 建立数据驱动 Provider Preset，包含默认 Base URL、必要头、模型发现方式和已知限制；覆盖列出的服务与 Ollama/LM Studio；允许用户自定义头但标记敏感字段。
- **交付与验收：** 新增 Preset 只需配置和契约夹具，至少逐一验证请求生成且文档列出兼容级别。

### RC-167 实现 Provider 能力声明

- **执行步骤：** 定义 capability Schema；由 Adapter 静态声明并可用探测结果覆盖；缓存带版本和过期时间；Agent/GUI 根据能力启停功能。
- **交付与验收：** 能力矩阵与实际契约一致，错误声明会被测试发现，UI 不展示不可用控制。

### RC-168 实现模型发现与手动 ID

- **执行步骤：** 为支持列表 API 的 Provider 实现分页与缓存；发现失败保留手动输入；校验仅做格式和最小请求，不维护会过期的硬编码白名单。
- **交付与验收：** 列表成功、空、超时、403 和手动模型场景通过，用户已保存的模型不会因发现失败丢失。

### RC-169 实现真实连接测试

- **执行步骤：** 默认使用 Mock 检查凭据解析、模型能力、流式首块和工具调用契约；只有用户主动提供自有 Key 并确认后，才允许手动发送最小真实请求；返回逐阶段结果和修复提示。
- **交付与验收：** 免费 CI 不发送真实请求；真实连接测试是可选手动项，必须显示可能产生 Provider 费用并支持用户设置 Token 上限。

### RC-170 统一 Provider 错误分类

- **执行步骤：** 定义 auth/balance/rate_limit/region/model/parameter/filter/network/timeout/server/cancelled；每个 Adapter 映射状态码和错误体；保留脱敏原始请求 ID。
- **交付与验收：** 错误夹具覆盖所有类别，UI/CLI 对同类错误使用相同退出码和修复动作。

### RC-171 实现网络韧性和企业配置

- **执行步骤：** 对幂等请求实现指数退避、抖动和 `Retry-After`；支持取消、HTTP(S) 代理、NO_PROXY、自定义 CA、IPv4/IPv6；敏感代理凭据进密钥库。
- **交付与验收：** 代理、证书、限流和断网 Mock 通过，取消能中断退避等待且不会无限重试。

### RC-172 实现模型选择、回退和预算

- **执行步骤：** 分别保存全局默认、工作区、会话和优化器模型；建立用户可见的回退链；在请求前估算 Token/费用并执行上限。
- **交付与验收：** 作用域优先级测试通过，超预算在发送前阻止，回退事件包含原因和新模型。

### RC-173 建立 Provider 契约与真实测试门禁

- **执行步骤：** 为每种协议创建录制无秘密的 Mock；定义共享契约；真实测试只作为用户自有 Key 的可选手动项，不进入默认 CI，也不要求项目购买测试额度。
- **交付与验收：** 默认 CI 零外网即可全绿；真实测试不会在 Fork PR 运行，界面必须在执行前显示可能产生的 Provider 费用并要求明确确认。

## O. 首页双入口与凭据

### RC-174 设计两个等权首选项

- **执行步骤：** 用两个同层级选择区呈现 API 与本地路线，分别说明数据去向、网络和硬件要求；不预选；提供可访问焦点与兔兔品牌。
- **交付与验收：** 新用户测试能在短时间内正确选择，视觉上没有暗示必须购买 API。

### RC-175 实现 API 配置向导

- **执行步骤：** 依次采集协议/服务商、Base URL、Key/认证、模型；实时保存非敏感草稿；运行连接测试后才允许设为默认，并支持返回修改。
- **交付与验收：** 成功和各类错误 E2E 通过，未完成向导不会留下可用状态或明文 Key。

### RC-176 实现无 API 安装向导

- **执行步骤：** 依次执行硬件检测、运行器选择、Gemma/Qwen 选择、磁盘预估、许可证确认、安装、健康检查；进度可中断并从已验证阶段恢复。
- **交付与验收：** 每个阶段均有确定状态和修复动作，重启应用后能恢复下载而非从零开始。

### RC-177 统一两条路线的工作区首页

- **执行步骤：** 向导只写 Provider/模型配置，不改变路由结构或账户类型；完成后统一导航工作区；模型选择器同时支持云与本地条目。
- **交付与验收：** 两路线截图除模型状态外信息架构一致，后续切换不需重新创建项目或会话。

### RC-178 实现 Provider/模型配置 CRUD

- **执行步骤：** 在设置与模型选择器接入创建、编辑、禁用、切换、删除；删除前检查活跃会话和默认引用；保留安全的迁移/替换选项。
- **交付与验收：** CRUD 与引用完整性测试通过，禁用不会删除历史，删除密钥后请求立即失败为未配置。

### RC-179 使用操作系统密钥库

- **执行步骤：** 抽象 `SecretStore`；接入 Windows Credential Manager 和 Linux Secret Service；SQLite 只保存 opaque reference；无密钥库时默认拒绝明文持久化并给临时会话选项。
- **交付与验收：** 数据库、日志、配置和崩溃转储扫描无 Key，Windows/Linux 存取/删除测试通过。

### RC-180 全链路掩码与脱敏

- **执行步骤：** UI 只展示固定掩码与末尾 4 位；复制默认不提供明文；对日志、导出、错误、遥测和诊断包应用 Secret Redactor；维护运行时已知秘密指纹。
- **交付与验收：** 注入多种 Key 格式后所有输出扫描零泄漏，显示末尾不足以还原凭据。

### RC-181 支持环境变量与配置引用

- **执行步骤：** 定义 `env:`/`keychain:` 引用类型和配置优先级；UI 显示“来自环境变量”而不显示值；环境变化时重新验证健康状态。
- **交付与验收：** 来源优先级测试通过，API 响应和前端状态中永不包含环境变量秘密值。

### RC-182 仅实现获准的官方 OAuth

- **执行步骤：** 对每个 Provider 核实第三方客户端政策；使用系统浏览器 + PKCE + state；安全保存 refresh token；实现过期刷新、撤销和回调端口清理。
- **交付与验收：** OAuth 威胁测试覆盖 CSRF、回调劫持和撤销，未获政策许可的 Provider 不显示 OAuth 入口。

### RC-183 保持本地使用无需云账户

- **执行步骤：** 所有本地会话、模型和配置不依赖 Rabbit 云；将潜在同步服务设计为独立可选模块；账户、Provider 凭据和本地 Profile 使用不同表与权限。
- **交付与验收：** 断网新装可进入无 API 路线并使用离线规则，禁用同步不影响核心能力。

### RC-184 实现凭据和数据清理

- **执行步骤：** 提供单 Provider 删除、全部凭据重置、配置迁移和全部本地数据删除；展示将删除/保留内容；停止进程后安全擦除引用和文件。
- **交付与验收：** 清理后 Keychain、数据库、缓存和配置检查均无目标数据；取消确认不产生变更。

## P. Gemma 与 Qwen2.5-Coder 本地模型

### RC-185 建立跨平台安装核心与脚本

- **执行步骤：** 把检测、下载、校验、安装和验证实现为可重入核心命令；PowerShell 与 Shell 仅做参数/显示包装；GUI 通过结构化 JSON 事件调用同一核心。
- **交付与验收：** CLI 脚本和 GUI 对同一模拟安装产生一致状态，重复运行不会重复下载已校验文件。

### RC-186 实现完整硬件环境检测

- **执行步骤：** 收集 OS/架构、CPU、RAM、可用磁盘、GPU/显存/驱动、网络、代理和运行器；每项标注检测来源与置信度；允许用户纠正不可检测值。
- **交付与验收：** 支持矩阵设备生成稳定 JSON 报告，权限不足时降级而不崩溃。

### RC-187 选择并抽象本地运行器

- **执行步骤：** 对 Ollama 与 llama.cpp 比较许可证、安装、GPU、API、包体和维护；通过 ADR 选默认；定义 pull/load/generate/stop/list/remove/health Adapter。
- **交付与验收：** 同一运行器契约可跑默认和至少一个替代实现，Agent Core 不含运行器特有命令。

### RC-188 建立受控模型清单

- **执行步骤：** 用版本化 manifest 记录模型 ID、来源、哈希、参数量、量化、上下文、磁盘/RAM/VRAM、模板和许可证；根据硬件规则计算推荐。
- **交付与验收：** Manifest Schema 校验通过，推荐不会超过设备预设安全余量，未知模型只允许高级手动导入。

### RC-189 固定支持 Qwen2.5-Coder

- **执行步骤：** 在 manifest 显式列出经审核的 Qwen2.5-Coder 规模和量化；锁定来源与聊天模板；UI 不用“Qwen 最新版”替代该系列。
- **交付与验收：** 版本检查和生成冒烟确认实际模型 family 为 Qwen2.5-Coder，模型页显示完整 ID。

### RC-190 审核并锁定 Gemma 版本

- **执行步骤：** 比较候选 Gemma 版本与编码能力、资源、许可证和用途限制；验证聊天模板与 EOS；由模型/法务 ADR 选首发集合。
- **交付与验收：** 每个 Gemma 条目有模型卡和许可证链接，用户在首次下载前完成必要确认。

### RC-191 实现可靠下载器

- **执行步骤：** 使用临时 `.part` 文件、Range 续传、SHA-256、固定版本 URL、代理/镜像、指数重试、进度和取消；完成校验后原子重命名。
- **交付与验收：** 断网、重启、错误哈希、镜像失败和并发下载测试通过，不完整文件永不标记可用。

### RC-192 遵守模型权重再分发限制

- **执行步骤：** Manifest 标记 `bundled/ondemand/manual`；构建脚本 denylist 未获许可权重；下载前展示许可证摘要和原文链接并记录用户确认版本。
- **交付与验收：** 安装包/SBOM 中不存在禁止权重，未确认许可无法开始相应下载。

### RC-193 执行安装后健康检查

- **执行步骤：** 验证运行器版本、加载模型、最小生成、流式增量、取消、上下文长度和资源峰值；保存健康报告；失败回滚就绪状态。
- **交付与验收：** 只有全部必选检查通过才标记 `ready`，健康报告可在诊断页查看且不含用户提示词。

### RC-194 展示本地模型状态机

- **执行步骤：** 定义 not_installed/downloading/verifying/loading/ready/busy/stopping/corrupt/update/failed；由后端事件驱动 UI；每个失败态提供重试/修复/卸载。
- **交付与验收：** 状态转换测试无不可能跳转，重启后 UI 从真实文件和运行器恢复状态。

### RC-195 支持默认与会话级本地模型选择

- **执行步骤：** 保存全局默认本地模型；会话可覆盖；切换前检查模型就绪与上下文兼容；正在生成时要求取消或新轮次生效。
- **交付与验收：** Gemma/Qwen 切换测试的元数据和实际请求一致，历史消息保留原模型标记。

### RC-196 管理 CPU/GPU 与 OOM

- **执行步骤：** 运行器 Adapter 接收线程、GPU 层、上下文和并发配置；按检测结果给安全默认；捕获 OOM 后卸载、降低配置并提示；空闲超时释放模型。
- **交付与验收：** CPU-only 和可用 GPU 设备完成冒烟，低内存故障不会拖垮 App Server 或无限重启。

### RC-197 管理模型目录和生命周期

- **执行步骤：** 支持选择新目录并检查空间/权限；迁移采用复制校验后切换再删除旧文件；实现更新、版本保留、回滚、修复、清理和卸载。
- **交付与验收：** 中断迁移仍保留一份完整模型，卸载只删除登记文件且历史会话不丢。

### RC-198 实现 LocalRunner Adapter

- **执行步骤：** 在 FastAPI 内定义 list/capabilities/generate/stream/cancel/load/unload；为 Ollama/llama.cpp 转换事件和错误；加入并发队列和健康缓存。
- **交付与验收：** 运行器契约测试覆盖流式与取消，API 层不包含具体命令行拼接。

### RC-199 默认无管理员权限安装

- **执行步骤：** 使用用户应用数据和用户 PATH；检查每个依赖是否可免管理员安装；如必须提权，拆成单独步骤并显示命令、原因和替代手动方案。
- **交付与验收：** 标准用户账户完成支持路线；任何提权都由用户显式确认且主应用不以管理员常驻。

### RC-200 支持离线安装与手动导入

- **执行步骤：** 发布 manifest、依赖包和模型文件的离线目录规范；提供导入命令，检查版本、许可证、哈希和磁盘；导入后运行相同健康检查。
- **交付与验收：** 无网络虚拟机能从准备好的介质完成导入，篡改文件被拒绝。

## Q. 权限、沙箱与安全

### RC-201 定义三档权限矩阵

- **执行步骤：** 按文件、终端、网络、Git、MCP 和桌面能力列出只读/工作区写入/高权限规则；用 capability policy 表达；默认最小权限。
- **交付与验收：** 策略表、代码和 UI 文案一致，参数化测试覆盖每个单元格。

### RC-202 实现危险操作审批

- **执行步骤：** Permission Engine 生成包含工具、命令、规范化路径、工作目录、影响和授权范围的请求；GUI/TUI 使用同一 Schema；审批前冻结执行。
- **交付与验收：** 审批快照信息完整，拒绝或超时不产生副作用，批准范围不能被参数替换绕过。

### RC-203 实现细粒度授权决策

- **执行步骤：** 支持一次、会话、匹配规则、拒绝和编辑后执行；规则采用结构化匹配而非任意 Shell 字符串；提供查看与撤销。
- **交付与验收：** 规则范围测试不越权，默认 UI 无“全部永久允许”，撤销后下一次立即询问。

### RC-204 实现 Windows/Linux 双平台沙箱

- **执行步骤：** 调研 Windows AppContainer/Job Object/ACL、Linux namespace/seccomp/bwrap；实现可用最小集合和能力探测；不可用时明确降低保证并加强审批。
- **交付与验收：** 每平台逃逸夹具验证文件和进程边界，支持矩阵记录无法等价的限制。

### RC-205 防御路径、命令和提示注入

- **执行步骤：** 路径规范化并检查符号链接；命令使用参数化执行和风险分类；环境变量白名单；将仓库/工具输出标为不可信数据，不允许其自动修改权限或系统指令。
- **交付与验收：** 安全用例覆盖 traversal、symlink、shell metacharacter、恶意 AGENTS 和工具注入，均不能越权。

### RC-206 保护敏感文件与目录

- **执行步骤：** 提供默认敏感模式 `.env`、SSH、云配置、浏览器和系统目录；读取/发送分别审批；允许用户增加规则；输出前运行 Secret Scanner。
- **交付与验收：** 敏感夹具不会被默认索引或发送，批准记录明确文件和目标 Provider。

### RC-207 加固本地 FastAPI

- **执行步骤：** 仅监听 `127.0.0.1/::1`；随机端口和每次启动高熵令牌；严格 Origin/Host、无通配 CORS；敏感路由全部认证并限制请求体。
- **交付与验收：** 非 Loopback、错误 Host/Origin/Token 请求被拒绝，端口扫描无法取得会话数据。

### RC-208 建立扩展来源信任

- **执行步骤：** 插件/技能/Hook/MCP/脚本 manifest 声明来源、版本、哈希和权限；安装前展示；支持锁定、禁用和隔离运行；来源变化需重新确认。
- **交付与验收：** 篡改和提权升级测试被阻止，禁用后进程和凭据访问均终止。

### RC-209 验证所有下载制品

- **执行步骤：** 对二进制、模型、更新和插件维护版本化 manifest；下载后验证哈希、HTTPS 来源和许可证；失败隔离并删除临时文件。
- **交付与验收：** 哈希不匹配、HTTPS 来源不可用或许可证缺失时安装失败，不存在“仍然安装”选项；不要求数字签名证书。

### RC-210 实现隐私优先遥测和诊断包

- **执行步骤：** 默认关闭内容遥测；首次明确选择加入；诊断包生成前列文件与脱敏预览，用户选择后才导出/发送；提供撤回和清除。
- **交付与验收：** 默认安装无遥测请求，诊断包秘密扫描通过，拒绝发送不产生网络流量。

### RC-211 建立安全工程流程

- **执行步骤：** 编写数据流与 STRIDE 威胁模型；配置依赖、秘密、SAST、容器和 SBOM 扫描；制定漏洞受理、分级、修复 SLA、CVE/公告与密钥轮换。
- **交付与验收：** 高风险威胁有控制和测试，CI 扫描阻断规则生效，`SECURITY.md` 提供有效私密报告渠道。

### RC-212 实现可清理审计日志

- **执行步骤：** 记录权限、工具、配置和外部请求的最小元数据；链入时间、主体和结果；按用户配置轮转/保留；提供按会话或全部清除。
- **交付与验收：** 审计查询可重建关键决策但不含秘密，过期和手动清理测试物理删除目标记录。

## R. 数据、隐私与可观测性

### RC-213 定义核心数据模型

- **执行步骤：** 为 workspace、session、message、content block、tool call、checkpoint、prompt version、provider reference、model manifest 和 setting 绘制 ER 图；定义 ID、时间、作用域、删除和版本字段；生成迁移初稿。
- **交付与验收：** Schema 评审无多义字段，Pydantic、数据库和 TypeScript 类型可追溯到同一规范。

### RC-214 加固 SQLite 事务与恢复

- **执行步骤：** 选择 WAL、busy timeout 和同步级别；所有复合写用事务；为查询建索引并用真实规模 `EXPLAIN`；实现备份、恢复、integrity check 和迁移锁。
- **交付与验收：** 并发、崩溃、锁竞争和损坏测试通过，关键查询达到预算且无丢提交数据。

### RC-215 实现结构化脱敏日志

- **执行步骤：** 定义 JSON 日志 Schema 和 request/session/tool/task correlation ID；所有日志先过字段级 Redactor；提示词、源码、路径和密钥默认不记录或哈希化。
- **交付与验收：** 日志 Schema 校验和秘密扫描进入 CI，跨服务请求可关联但不能还原敏感正文。

### RC-216 明示本地与云端数据去向

- **执行步骤：** Provider 请求前生成 `execution_location` 和目标服务；在 Composer、工具审批与结果元数据显示 local/cloud；路由变化时即时更新。
- **交付与验收：** API、本地模型和离线规则三条 E2E 均显示正确标识，用户不会在请求后才首次获知上传目标。

### RC-217 提供 Provider 隐私说明

- **执行步骤：** 为每个 Provider Preset 维护发送字段、服务区域、官方数据政策链接和未知保留风险；配置/首次使用时展示；自定义端点明确标为用户负责。
- **交付与验收：** Provider 页面可访问说明且版本可追踪，链接检查通过，文案不作无法验证的隐私承诺。

### RC-218 管理日志、缓存和历史保留

- **执行步骤：** 为日志级别、单文件/总大小、缓存、会话和 Prompt 历史定义默认上限；实现后台轮转和一键清理；清理前计算影响并避开运行中资源。
- **交付与验收：** 超限自动回收，清理测试不删除配置/模型等非目标数据，磁盘释放量可核对。

### RC-219 采集技术性能指标

- **执行步骤：** 在请求和工具边界记录总延迟、首 Token、Token、错误、工具成功率、模型加载和 CPU/RAM/GPU；使用本地聚合；仅在用户同意时上报匿名汇总。
- **交付与验收：** 指标定义和单位文档齐全，仪表/报告能从固定负载重现实测数值。

### RC-220 实现显式遥测选择加入

- **执行步骤：** 初始配置为 off；独立页面说明本地事件和字段；用户开启后写 consent 版本并可随时关闭/删除；不建设或依赖遥测后端。
- **交付与验收：** 网络测试确认默认零遥测，关闭后立即停止；核心功能在没有任何遥测服务、服务器或账户时完整可用。

### RC-221 提供可移植导入导出

- **执行步骤：** 定义版本化 JSON/ZIP 格式，包含会话、消息、Prompt、模板和非敏感设置；密钥默认排除；导入前 Schema/大小/路径验证并预览冲突策略。
- **交付与验收：** 导出后在干净 Profile 导入得到等价数据，恶意 ZIP/path traversal 被拒绝。

## S. 性能、稳定性与资源控制

### RC-222 建立性能预算基线

- **执行步骤：** 在固定硬件测 GUI 冷/热启动、CLI 首响应、首 Token、搜索、diff、内存和包体；定义 p50/p95 与首发阈值；保存命令、数据和环境。
- **交付与验收：** `docs/performance/baseline.md` 可复现，未达阈值项有批准的优化 Issue 或阻止发布。

### RC-223 优化大仓库索引

- **执行步骤：** 启动先返回 UI，再后台增量扫描；应用 ignore、文件大小和语言过滤；用内容哈希/mtime 缓存；生产者消费者加有界队列和取消。
- **交付与验收：** 目标大仓库打开不被扫描阻塞，重复打开显著减少 I/O，队列不会无限增长。

### RC-224 控制所有大数据上限

- **执行步骤：** 为工具输出、上下文、日志、diff、附件定义默认/最大值；在协议中带 `truncated`、原大小和继续游标；UI 明示截断而非静默丢弃。
- **交付与验收：** 边界与超限测试通过，用户可按权限读取后续内容，进程内存保持预算内。

### RC-225 实现组件崩溃恢复

- **执行步骤：** 对 App Server、桌面壳、终端和模型进程分别定义监督策略；持久化已提交事件与草稿；启动时对账运行中任务并标为恢复/失败。
- **交付与验收：** 逐组件 kill 测试后已提交会话不丢，UI 能恢复或清晰说明无法继续的原因。

### RC-226 实现端到端取消传播

- **执行步骤：** 从 GUI/CLI 生成 cancellation ID；App Server 传至 Agent、Provider、工具子进程和 LocalRunner；设置强制终止超时并保存 cancelled 终态。
- **交付与验收：** 每层取消延迟满足阈值，取消后无新 token/写操作，资源和进程被释放。

### RC-227 实现专项故障恢复

- **执行步骤：** 为限流、断网、代理、OOM、磁盘满、数据库锁和端口冲突定义检测、用户提示、自动重试边界与恢复动作；构建故障注入夹具。
- **交付与验收：** 故障矩阵逐项通过，不可恢复错误保留原输入和诊断证据，不进入无限循环。

### RC-228 限制本地模型资源

- **执行步骤：** 根据硬件设并发、线程、GPU 层、上下文和空闲卸载；队列显示等待；实时监控 OOM/温度可用信号并允许用户调低。
- **交付与验收：** 压测下系统仍可交互，超过限制的请求排队或拒绝而不是同时加载多个模型。

### RC-229 建立长期性能回归

- **执行步骤：** 将固定仓库/数据集和基准命令放入 `benchmarks`；CI 记录趋势并按噪声设置阈值；README 数字由可复现报告生成，不手填。
- **交付与验收：** 人为引入显著回归会告警/阻断，报告包含 Commit、硬件和统计区间。

## T. 测试与质量保证

### RC-230 完善 Agent Core 单元测试

- **执行步骤：** 用 Fake Model/Tool/Clock 测状态转换、连续工具、取消、重试、预算、压缩、恢复和非法事件；使用性质测试覆盖随机序列；避免真实网络。
- **交付与验收：** 核心关键分支和状态边界达到设定覆盖，失败测试能定位到具体 RC 行为。

### RC-231 完善 Provider 契约测试

- **执行步骤：** 为 Chat、Responses、Gemini、Anthropic 和兼容端点建立请求/流事件/工具/错误夹具；共享契约验证 Adapter；对未知字段保持前向兼容。
- **交付与验收：** 所有 Adapter 跑同一基础套件并通过各自扩展套件，协议变化由快照差异提示。

### RC-232 完善 FastAPI 测试

- **执行步骤：** 覆盖启动令牌、Origin、路由、优化、fallback、SSE/WebSocket、任务、并发、取消和限流；使用临时数据库和依赖注入；增加非法请求模糊测试。
- **交付与验收：** 本地安全路由 100% 有认证断言，流连接无资源泄漏，测试可离线重复。

### RC-233 完善 CLI 测试

- **执行步骤：** 使用伪终端与普通 subprocess 测交互/无头/JSON/退出码/TTY/非 TTY/不同 Shell/恢复；固定终端尺寸和无颜色模式；捕获 stdout/stderr。
- **交付与验收：** 关键 CLI 命令在 Windows/Linux CI 通过，机器输出快照稳定且无提示符污染。

### RC-234 完善 GUI 组件与 E2E

- **执行步骤：** 组件测试覆盖状态和无障碍；Playwright 用 Mock App Server 跑双入口、API、本地安装、对话、星星、采用、发送、diff、设置；对关键路径加真实 sidecar 冒烟。
- **交付与验收：** 每条原始 GUI 需求至少映射一个 E2E，失败保留截图、视频和事件日志。

### RC-235 完善视觉回归矩阵

- **执行步骤：** 为全部路由生成深浅主题、常见尺寸、200% 缩放、长文本和空/错/加载截图；固定字体与数据；人工批准有意变化。
- **交付与验收：** 兔兔素材、溢出和重叠有专用断言，未批准像素差阻断合并。

### RC-236 完善无障碍测试

- **执行步骤：** 在组件和 E2E 加 axe；人工测试键盘、焦点顺序、Tooltip、NVDA/VoiceOver 等至少一个对应平台阅读器、对比度和 reduced motion。
- **交付与验收：** 关键流程无严重/高等级问题，人工结果记录平台、版本和复现步骤。

### RC-237 完善本地模型测试

- **执行步骤：** 用 Fake Runner 覆盖大部分 CI；实机矩阵覆盖 Gemma/Qwen、CPU/GPU、低内存、续传、损坏、修复和卸载；固定小型受许可测试模型或 Mock 权重。
- **交付与验收：** 默认 CI 不下载大权重，受控实机报告证明两系列完整生命周期通过。

### RC-238 完善安装包测试

- **执行步骤：** 在 Windows/Linux 干净 VM 测安装、首次启动、升级、阻止不兼容降级、卸载、保留/删除数据和哈希；保存系统快照并重复两平台。
- **交付与验收：** 每个稳定版候选均有全新环境证据，安装后无未知服务/计划任务残留。

### RC-239 完善安全测试

- **执行步骤：** 建立密钥泄漏、路径逃逸、命令注入、Loopback 攻击、恶意 MCP/插件/仓库和供应链场景；结合自动扫描与人工渗透审查；追踪修复 SLA。
- **交付与验收：** 发布前无未接受的高危问题，所有修复带回归测试和威胁模型更新。

### RC-240 完善 Prompt 优化质量测试

- **执行步骤：** 计算前后规则分、语义相似、结构保持和语言保持；开展盲评并记录一致性；代码块/变量必须做硬约束；分 Provider/模型报告。
- **交付与验收：** 质量门槛预先写定，任何 Prompt 或默认模型变更不得降低关键指标超阈值。

### RC-241 以 Mock 为 CI 默认

- **执行步骤：** 提供确定性 Provider/Runner Mock；Fork/普通 PR 只跑 Mock；真实 API/模型仅作为用户自有 Key 的受保护手动任务，不配置项目付费 Key 或定时调用。
- **交付与验收：** 无秘密、无外网环境能完成 CI，外部服务波动不影响普通 PR 判定。

### RC-242 建立 Windows/Linux CI

- **执行步骤：** 配置 Windows、Linux 矩阵；缓存锁文件依赖；运行格式、Lint、类型、单元、集成、E2E、构建和许可证；分层并行并汇总门禁。
- **交付与验收：** 受保护分支要求全部必选 Job，任一平台失败不能发布。

### RC-243 设定覆盖率与关键路径门槛

- **执行步骤：** 设置总体与 changed-lines 覆盖；为权限、密钥、安装、迁移、取消和恢复维护强制测试清单；用 mutation/故障测试检查断言有效性。
- **交付与验收：** 报告同时展示数值和关键路径状态，高总覆盖但关键项缺失仍会失败。

## U. GUI/CLI 联调与完整性

### RC-244 验证跨端状态一致

- **执行步骤：** 使用同一工作区同时启动 CLI/GUI；在两端修改会话、Provider、模型、权限、Prompt 版本和文件；通过事件订阅/刷新对账。
- **交付与验收：** 一致性 E2E 无冲突覆盖，版本冲突使用明确的乐观锁错误处理。

### RC-245 验证跨端会话恢复

- **执行步骤：** GUI 创建含文本、工具、diff 的任务后由 CLI resume；反向创建后由 GUI 打开；验证事件排序、内容块和未完成状态。
- **交付与验收：** 两个方向均逐事件一致，未知旧事件安全降级而非崩溃。

### RC-246 验证 API 用户完整旅程

- **执行步骤：** 在干净 Profile 配置 Provider、测试、发起对话、点击星星、确认同一 Provider、采用并发送；记录网络请求与 UI 状态；覆盖失败重试。
- **交付与验收：** Playwright + Mock 通过；真实 API 仅在用户明确提供 Key 时作为可选手动证据，元数据证明没有切换到未授权服务。

### RC-247 验证无 API 用户完整旅程

- **执行步骤：** 在无 Key 环境选择本地路线；检测硬件、安装模型、健康检查、选择、对话并 FastAPI 优化；Gemma 和 Qwen 分别执行。
- **交付与验收：** 两条模型路线报告完整，网络仅用于获准模型下载，运行/优化阶段可断网。

### RC-248 验证模型未就绪的规则降级

- **执行步骤：** 模拟未安装、加载失败和 OOM；点击星星；确认 FastAPI 调用 OfflineRuleProvider、返回 fallback 元数据和修复入口。
- **交付与验收：** 三种故障均保留原输入并得到规则结果，没有外部网络请求。

### RC-249 保护错误时的输入草稿

- **执行步骤：** Composer 草稿按 revision 本地持久化；对断网、401、429、模型错误和应用刷新注入故障；提供原地重试、切换或本地路线。
- **交付与验收：** 每个故障后文本、附件引用和光标可恢复，错误不会清空或自动发送草稿。

### RC-250 验证跨端 diff 与检查点

- **执行步骤：** Agent 修改多文件；GUI/CLI 分别查看 diff、运行测试、接受/拒绝和恢复；加入用户并发编辑冲突；对账 Git 工作树。
- **交付与验收：** 所有操作可解释且不丢用户改动，检查点恢复后文件哈希匹配预期。

### RC-251 验证全页面兔兔覆盖

- **执行步骤：** 从路由表自动逐页导航并查找 `RabbitMark`；生成截图；由设计人员检查位置、裁切、主题和内容遮挡，记录证据。
- **交付与验收：** 自动和人工两列均通过，任何新增独立路由缺素材会阻断发布。

### RC-252 实现并验证国际化

- **执行步骤：** 引入 i18n 资源层和 key 类型；抽取组件硬编码文案；提供完整简体中文和基础英文；格式化日期、数字和复数。
- **交付与验收：** 关键流程中文覆盖 100%，静态扫描阻止新增用户可见硬编码字符串，长翻译无溢出。

### RC-253 审计需求追踪完整性

- **执行步骤：** 生成 R1-R6、原初 12 类、RC ID、Issue、PR、测试、文档映射；标记缺失和未验收；由产品、技术、QA 共同签署。
- **交付与验收：** 追踪报告无 orphan requirement，签署记录成为 M6/M7 必需制品。

## V. 设计验收与体验优化

### RC-254 完成编码前低保真评审

- **执行步骤：** 绘制站点地图、主旅程、Composer 和双入口线框；用点击原型走查成功/错误/返回；冻结必要信息架构后再实现页面。
- **交付与验收：** 产品、设计、前后端和无障碍评审签字，未解决阻断问题不进入 GUI 大规模开发。

### RC-255 完成多尺寸高保真设计

- **执行步骤：** 为标准桌面和最小窗口绘制深浅主题；填入最长 Provider/模型名、中英长文和错误；标注 Token、响应式和交互状态。
- **交付与验收：** 设计稿覆盖全部关键状态并与 Design Token 对齐，开发无需猜测尺寸或折行规则。

### RC-256 用截图和实机检查布局稳定性

- **执行步骤：** 在目标尺寸自动截图；用 DOM 边界检查重叠/溢出/不可见；对流式文本、加载、Tooltip 和长标签运行布局偏移测试；人工抽查实机。
- **交付与验收：** 无阻断重叠，CLS/自定布局偏移低于阈值，证据附到对应 RC。

### RC-257 验证星星与发送的安全主次

- **执行步骤：** 做图标、间距、颜色与焦点对比；给优化请求加请求锁；并发编辑用 revision 防覆盖；通过误触任务测试两种按钮。
- **交付与验收：** 用户测试误触率低于设定值，自动化证明优化完成不触发发送或覆盖新文本。

### RC-258 验证兔兔不妨碍工作信息

- **执行步骤：** 用真实代码、终端、diff、设置和模型列表测视觉；检查对比度、点击区域、滚动与水印；按页面降低尺寸/透明度或换空状态变体。
- **交付与验收：** 设计审核对每页给出通过记录，兔兔没有覆盖内容或成为错误的主要视觉焦点。

### RC-259 限制动效用途和资源

- **执行步骤：** 只为加载、状态变化和空间转换定义动效；限制时长和并发；读取 reduced motion 后关闭非必要动画；测 CPU/GPU 与后台标签页。
- **交付与验收：** reduced-motion 快照无装饰动画，空闲页面无持续动画导致的明显资源占用。

### RC-260 开展新用户可用性测试

- **执行步骤：** 招募未接触项目的目标用户；不给外部教程，要求完成双入口、本地安装、API 配置和星星优化；记录完成率、时间、错误和口述困惑。
- **交付与验收：** 达到预设完成率；阻断问题形成 Issue 并在复测通过后关闭。

### RC-261 开展高频用户效率测试

- **执行步骤：** 设计键盘流、焦点、命令、会话切换和 diff 审查任务；记录操作数/时间；与基线比较；优先修复高频摩擦而非增加装饰。
- **交付与验收：** 核心高频任务达到效率目标且无无障碍倒退，结果写入 UX 报告。

## W. 文档、开发者体验与贡献

### RC-262 编写中英文 README

- **执行步骤：** 中文 README 为主并提供英文等价版；包含定位、真实截图、功能、支持矩阵、安装、快速开始、数据去向、许可证和贡献入口；所有状态/数字从发布制品生成。
- **交付与验收：** 两种语言结构与事实一致，干净环境按快速开始可成功运行，链接和截图自动检查通过。

### RC-263 编写完整架构文档

- **执行步骤：** 绘制进程、模块和数据流；分别说明 Agent Loop、协议、Provider、工具、权限、数据模型和桌面 sidecar；关联 ADR 与源目录，记录失败恢复。
- **交付与验收：** 新贡献者可据文档定位一次请求的全链路，架构图与当前代码依赖检查一致。

### RC-264 编写 Provider 接入指南

- **执行步骤：** 按 OpenAI、Gemini、Anthropic、Azure、Vertex、Bedrock 和自定义端点分别写凭据、端点、模型、连接测试、常见错误和数据发送；截图不得含 Key。
- **交付与验收：** 每份指南由未参与实现者实操通过，示例配置经 Schema 和秘密扫描。

### RC-265 编写本地模型指南

- **执行步骤：** 说明硬件选择、Gemma/Qwen2.5-Coder版本、在线安装、离线导入、目录、故障、更新、回滚和卸载；列明许可证与磁盘/RAM 估算。
- **交付与验收：** CPU-only 和至少一种 GPU 环境按指南完成操作，命令由文档测试实际执行。

### RC-266 编写 CLI 与 GUI 使用手册

- **执行步骤：** 以任务为中心覆盖命令、工作区、Composer 星星、会话、diff、终端、MCP、插件和 Hooks；提供成功流程和常见恢复，不复制界面自夸文案。
- **交付与验收：** 关键用户旅程都有对应章节和版本截图，帮助链接从应用可达。

### RC-267 编写开发、测试和发布指南

- **执行步骤：** 固定环境版本、依赖安装、开发服务器、测试矩阵、调试、打包、迁移和发布命令；说明各平台差异和常见故障；命令集中到任务脚本。
- **交付与验收：** 新机器从零完成构建和测试，文档不依赖作者本地未声明工具。

### RC-268 编写安全、隐私和数据删除文档

- **执行步骤：** 发布 `SECURITY.md`、隐私说明、遥测事件清单、漏洞渠道、支持范围和删除流程；明确云 Provider 与本地处理边界；由安全/法律审查。
- **交付与验收：** 文档与实际默认设置、网络测试和保留策略一致，不包含无法保证的绝对承诺。

### RC-269 提供扩展示例与 API 版本策略

- **执行步骤：** 编写最小 Provider Adapter、Tool、MCP、Plugin 和 Theme 示例；每个示例使用最小权限并有测试；定义稳定/实验 API、SemVer 和弃用窗口。
- **交付与验收：** 示例在 CI 构建运行，破坏稳定 API 的变更会由兼容测试发现。

### RC-270 配置开源协作机制

- **执行步骤：** 创建 bug/feature/security 配置、PR 模板、贡献指南、行为准则、路线图、Discussion 分类和 Keep a Changelog；模板要求 RC ID、测试与来源声明。
- **交付与验收：** 新 Issue/PR 默认获得正确字段，安全报告不会被引导到公开 Issue。

### RC-271 自动测试文档

- **执行步骤：** 提取并运行标注的 Shell/PowerShell/Python/CLI 代码块；用链接检查器和截图存在性检查；性能数字关联基准 JSON；安装步骤在 VM 定时测试。
- **交付与验收：** 失效命令、链接、截图或手填过期数字会使 CI 失败。

## X. 构建、部署与发布（注意：以下任务不用考虑macOS）

### RC-272 生成两平台桌面安装包（注意：以下任务不用考虑macOS）

- **执行步骤：** 配置 Tauri bundler 输出 Windows 安装程序、Linux AppImage/deb/rpm；按支持矩阵构建架构；设置图标、应用 ID、卸载和用户数据策略。
- **交付与验收：** 每种首发产物在干净环境安装/启动/卸载通过，文件名、版本和 SHA-256 哈希可自动核对；不要求代码签名。

### RC-273 发布 CLI 安装渠道

- **执行步骤：** 选择与栈相符的 PyPI/独立可执行文件及 winget/Homebrew/Scoop 等渠道；生成安装脚本和校验和；处理用户 PATH、升级和卸载。
- **交付与验收：** 每个宣布支持的渠道有自动冒烟，旧版升级后 `rabbit --version` 与配置数据正确。

### RC-274 可复现打包 sidecar 与桌面资源

- **执行步骤：** 锁定 Python、Node、Rust 和依赖；用 PyInstaller/批准方案构建 FastAPI sidecar；将前端、Tauri 与运行时按 manifest 组合；移除时间戳等非确定输入。
- **交付与验收：** 相同源码/工具链两次构建的可比较制品哈希一致或差异有可解释清单，sidecar 在目标机无需开发环境。

### RC-275 保持本地模型按需下载

- **执行步骤：** 桌面安装包只带模型 manifest 和安装器；首次选择本地路线才下载；提供手动离线导入并遵守许可；设置下载大小确认。
- **交付与验收：** 标准安装包扫描不含大模型权重，API 路线不会触发模型下载。

### RC-276 实现安全更新与回滚

- **执行步骤：** 使用版本化更新 manifest；客户端通过 HTTPS 检查渠道、版本、平台和 SHA-256 哈希；分阶段发布；升级前备份数据并验证协议/迁移，失败回到旧二进制或安全恢复页。
- **交付与验收：** 篡改更新被拒绝，升级/回滚演练不损坏数据，不兼容版本给出明确阻止提示。

### RC-277 生成制品哈希、SBOM 和供应链清单

- **执行步骤：** 使用免费本地工具生成构建来源说明、SHA-256、CycloneDX/SPDX SBOM、许可证报告和恶意软件扫描；不配置代码签名、公证或签名凭据。
- **交付与验收：** Release 制品与 SHA-256、来源清单和 SBOM 可相互核对，秘密不暴露给 Fork PR，扫描无未处置高危结果。

### RC-278 建立 nightly、beta、stable 渠道

- **执行步骤：** 定义各渠道触发、保留期、更新源和质量门槛；采用 SemVer 预发布标识；自动生成 Changelog；数据库迁移在 beta 验证后才能进入 stable。
- **交付与验收：** 客户端只接收所选渠道，stable 不会自动降级或接收 nightly，发布流程可演练。

### RC-279 完整生成 GitHub Release

- **执行步骤：** Release 工作流上传各平台安装包/CLI、校验和、SBOM、许可证、来源证明；从 Issue/PR 生成变更、已知问题和升级说明；使用普通 Git Tag。
- **交付与验收：** 发布清单自动核对无缺项，用户可按文档验证下载哈希；不要求应用商店或签名服务。

### RC-280 限定 Docker 使用范围

- **执行步骤：** Dockerfile 仅服务 API 本地开发和测试；README 不把容器冒烟当桌面验证；CI 分别保留容器和真实安装包任务；不部署 Rabbit Code 公共服务。
- **交付与验收：** 发布报告明确两类结果，桌面/CLI 支持声明都有非 Docker 证据。

## Y. 开源治理与许可证

### RC-281 选择兼容的 Rabbit Code 主许可证

- **执行步骤：** 比较 MIT、Apache-2.0 等与现有项目、Codex/OpenCode复用和分发目标；分析专利、NOTICE 与依赖兼容；由维护者/法律 ADR 选择。
- **交付与验收：** 根 LICENSE 与所有包元数据一致，第三方许可义务不被主许可证错误覆盖。

### RC-282 维护全部许可文件

- **执行步骤：** 根目录维护 LICENSE/NOTICE/THIRD_PARTY_NOTICES；模型和素材许可放专用目录；从复用登记/依赖锁自动生成并人工复核。
- **交付与验收：** 发布制品包含相应文件，许可证扫描结果与通知内容逐项对账。

### RC-283 禁止误标 Claude Code 专有组件

- **执行步骤：** 将 Claude CLI/SDK 捆绑物和 source map 还原物加入禁止分发列表；扫描依赖与制品；文档不得称其为 Rabbit Code 开源组件。
- **交付与验收：** SBOM/二进制字符串/来源审计零命中，任何可选官方集成清楚标注外部条款。

### RC-284 保留 Codex/OpenCode 署名与修改声明

- **执行步骤：** 复用文件保留上游版权头；按 Apache/MIT 要求更新 NOTICE；在来源登记记录修改；合并前自动检查批准列表和头部。
- **交付与验收：** 第三方审计可从每个衍生文件追到固定上游 Commit 和许可证。

### RC-285 自动扫描许可证风险

- **执行步骤：** 对 Python、npm、Cargo、二进制和模型依赖运行许可证扫描；设置允许/审核/拒绝策略；检测未知、Copyleft 和禁止再分发；升级 PR 自动重跑。
- **交付与验收：** 未批准许可证阻断 CI，例外有负责人、范围和到期日期。

### RC-286 确认所有视觉和演示资产权利

- **执行步骤：** 为兔兔、图标、免费字体、截图、文档图片和演示仓库建立资产登记；保存授权、来源、修改和署名；不购买素材或字体；对截图中的第三方品牌/数据做清理。
- **交付与验收：** 发布资产全部可在登记表找到有效权利依据，未知来源资产为零；无法免费确认权利的资产不进入发布包。

### RC-287 建立维护者与安全治理

- **执行步骤：** 最小化仓库/Admin/Release 权限；启用分支保护、必审、普通 Tag、CODEOWNERS；配置 Dependabot/Renovate、密钥轮换和安全响应值班；不购买或配置签名证书。
- **交付与验收：** 权限季度审计通过，单个普通维护者不能绕过 stable 发布门禁。

### RC-288 整理 GitHub 项目呈现

- **执行步骤：** 设置仓库描述、Topics、默认分支、目录结构、Project 看板、里程碑、Release 和公开 Roadmap；将 RC ID 导入 Issue 模板和看板字段。
- **交付与验收：** 外部贡献者能从首页定位安装、路线图、贡献和安全渠道，里程碑状态与追踪报告同步。

### RC-289 完成首次公开发布前审计

- **执行步骤：** 从全新环境复现构建；冻结依赖；执行许可证、来源、安全、隐私和文档走查；逐项处理或书面接受风险；签署 Go/No-Go。
- **交付与验收：** 发布审计包完整，无未处置阻断项，最终制品与审计哈希一致。

## Z. M0 至 M8 里程碑门槛

### RC-290 通过 M0 需求与合法性基线

- **执行步骤：** 汇总 R1-R6、竞品调研、许可证、素材授权、支持平台和稳定版 DoD；运行追踪检查；组织产品、技术、设计、QA、合规评审。
- **交付与验收：** 所有必需文档获批并固定版本，未决法律/范围问题为零或有明确阻断状态。

### RC-291 通过 M0 source map 专项门槛

- **执行步骤：** 完成仓库证据清单、公开法律依据、clean-room 人员/权限、允许/禁止列表和监控计划；审计工作树/依赖无还原源码。
- **交付与验收：** 技术与合规共同签署，自动 denylist 测试通过，否则不得进入核心实现。

### RC-292 通过 M1 架构原型

- **执行步骤：** 构建最小 Agent Core、FastAPI、CLI 流事件、Tauri GUI 和 sidecar 生命周期；生成 TypeScript 客户端；在 Windows/Linux 至少跑健康/请求/取消/退出。
- **交付与验收：** 原型报告包含性能、包体、故障和 ADR，未解决架构阻断项为零。

### RC-293 通过 M2 Agent Core 与 CLI

- **执行步骤：** 汇总 Agent Loop、文件/终端/Git 工具、权限、上下文、会话、流式、取消、恢复和 diff；运行单元/集成/CLI E2E 与安全测试。
- **交付与验收：** M2 功能矩阵全绿，演示任务可在真实仓库完成并安全回滚。

### RC-294 通过 M3 Provider 与本地模型

- **执行步骤：** 完成三原生协议、兼容 Provider、Keychain、双入口、Gemma/Qwen 安装与切换；跑契约、真实连接和本地实机矩阵。
- **交付与验收：** API/无 API 两条端到端旅程通过，密钥与模型许可审计无阻断。

### RC-295 通过 M4 桌面主工作流

- **执行步骤：** 完成工作区、会话、任务、终端、计划、diff、模型设置和每页 RabbitMark；运行 GUI E2E、视觉与无障碍矩阵；进行设计签收。
- **交付与验收：** 主流程无 P0/P1 缺陷，全部独立路由有兔兔证据且不影响可用性。

### RC-296 通过 M5 提示词优化集成

- **执行步骤：** 完成星星、API/本地路由、流式、比较、采用、撤销、历史、模板、评分和评测；覆盖并发编辑、取消、fallback 和隐私。
- **交付与验收：** 云、本地模型、离线规则三路线达到质量门槛，任何失败不丢原输入。

### RC-297 通过 M6 发布候选硬化

- **执行步骤：** 跑全平台安装升级、性能、无障碍、安全、隐私、视觉、故障恢复和追踪审计；冻结 RC；仅允许阻断缺陷修复并重复相关回归。
- **交付与验收：** Release Candidate 报告全部门槛通过，无未接受 P0/P1 或高危漏洞。

### RC-298 通过 M7 开源稳定版发布

- **执行步骤：** 完成文档、许可/NOTICE/SBOM、未签名制品及 SHA-256 校验和、GitHub Release 和贡献机制；执行 Go/No-Go；发布后验证下载、更新与监控。
- **交付与验收：** 用户可验证并安装所有宣布支持的制品，Release 清单与实际附件完全一致。

### RC-299 执行 M8 持续迭代

- **执行步骤：** 建立性能、资源、UX、视觉、Provider、模型、Bug、安全和社区反馈看板；按影响/风险排序；每个迭代保持兼容、测试和 Changelog。
- **交付与验收：** 月度/季度报告显示趋势、已交付和未决风险，安全/Provider 破坏性变化按 SLA 处理。

## AA. 最终完成定义的执行与验收

### RC-300 验证 6 项要求与原初 12 类计划追踪

- **执行步骤：** 从需求源生成矩阵；逐项链接 RC、设计、代码、测试、文档和 Release；由独立审查者抽查证据与实际行为。
- **交付与验收：** 矩阵覆盖率 100%，无缺失、重复冒充或仅有计划没有实现的条目。

### RC-301 验证 Windows/Linux 双路线

- **执行步骤：** 在 Windows、Linux 受支持干净环境分别执行 API 与无 API 脚本；记录安装、配置、对话、优化、退出和卸载；保存版本/硬件证据。
- **交付与验收：** 四个端到端组合全部通过，任何平台例外必须从首发支持声明移除而非静默跳过。

### RC-302 验证三种原生协议

- **执行步骤：** 对 OpenAI、Gemini、Anthropic 跑完整 Mock/契约测试；真实文本、流式、工具和错误测试仅在用户明确提供自有低权限 Key 时手动执行，并记录 API 版本与可能费用。
- **交付与验收：** 三协议均有免费契约通过报告；可选真实测试不属于发布前置条件，失败/内容过滤/限流映射符合统一错误规范。

### RC-303 验证 Gemma 与 Qwen 完整生命周期

- **执行步骤：** 每系列分别执行脚本和 GUI 安装、校验、加载、对话、优化、切换、修复、更新/回滚和卸载；检查残留和历史完整性。
- **交付与验收：** 两系列所有必选步骤在至少一个支持平台实机通过，其他平台由运行器矩阵覆盖。

### RC-304 验证星星两种主路线的数据安全

- **执行步骤：** 有 API 和无 API 分别测试成功、错误、取消、慢响应和并发编辑；比对草稿 revision、请求 ID、结果和网络目标；验证不自动发送。
- **交付与验收：** 原输入逐字可恢复，旧响应不覆盖新文本，实际路由与 UI 标识一致。

### RC-305 验证每个 GUI 页面兔兔与可访问性

- **执行步骤：** 自动遍历路由生成桌面/小窗、深/浅主题截图；检查 `RabbitMark`、替代文本、对比和边界；人工评审功能遮挡。
- **交付与验收：** 覆盖矩阵 100% 通过，无裁切、重叠、低对比或键盘阻断。

### RC-306 验证 CLI Claude Code 风格能力

- **执行步骤：** 用场景套件测试 Agent 循环、工具、权限、上下文、会话、Git/diff、取消和恢复；对照行为规格记录差异；检查无专有内容来源。
- **交付与验收：** 所有承诺行为通过且差异已文档化，CLI 可在真实仓库安全完成代表性任务。

### RC-307 验证 GUI Codex 风格功能覆盖

- **执行步骤：** 按工作区、会话、对话、计划、终端、diff、Provider、本地模型、设置和诊断逐项跑 E2E；验证共享核心与小窗口/错误态。
- **交付与验收：** 功能矩阵全绿，GUI 不是静态外壳，每个页面均连接真实服务和状态。

### RC-308 验证制品不含无授权专有内容

- **执行步骤：** 扫描源码、Git 历史、依赖、二进制、资源、容器和安装包；对 Claude/Codex 专有标识、哈希、字符串和模型权重做 denylist；人工审查来源登记。
- **交付与验收：** 扫描零违规，所有第三方内容均有有效许可证和通知，审计报告与发布哈希绑定。

### RC-309 完成 source map 机械衍生审计

- **执行步骤：** 对核心代码、Prompt、测试和常量进行来源/相似性审查；抽查提交者 clean-room 资格和 PR Provenance；检查禁止仓库从未进入依赖/CI。
- **交付与验收：** 技术与合规签署“无还原源码或机械改写”结论，任何无法解释的高相似项在发布前移除并重写。

### RC-310 执行最终发布门禁

- **执行步骤：** 汇总测试、文档、安装包、许可证、安全、SBOM、升级/卸载、GitHub Release 和 RC-001 至 RC-309 证据；自动校验后召开 Go/No-Go；冻结并核对未签名制品及其哈希。
- **交付与验收：** 所有强制检查通过、决策记录齐全、制品哈希一致后才发布；任一阻断项失败即 No-Go，不允许口头豁免。

## AB. 原始 310 项基线清单（完整合并与进度勾选区）

> 本节完整保留合并前总清单的原文，并按出现顺序补充 RC 编号。每完成一项，必须在这里把对应 `[ ]` 改成 `[x]`，同时更新文档最开头的进度快照和完成日志。

### 0. 项目目标与强制约束

- [ ] **RC-001** 将产品正式命名为 **Rabbit Code**，定位为开源、跨平台、终端与桌面端共享核心能力的编码 Agent。
- [ ] **RC-002** 终端版以 Claude Code 的公开行为和交互逻辑为对标，包括 Agent 循环、工具调用、权限控制、上下文管理、会话恢复和 Git 工作流，但不得复制无授权的专有代码。
- [ ] **RC-003** GUI 以 Codex 桌面端的信息架构、任务工作流和功能覆盖为参考，形成 Rabbit Code 自有设计，不直接复制受保护的品牌、图标、文案或像素级界面。
- [ ] **RC-004** 参考 OpenCode 的开源 Agent、Provider、终端、桌面端和插件化实现，复用代码前必须逐文件确认许可证、NOTICE 和修改声明要求。
- [ ] **RC-005** 保留并升级当前 Prompt Optimizer 项目的分析、优化、模板、历史、版本对比、导出、评测、Provider、CLI 和 FastAPI 能力。
- [ ] **RC-006** 将提示词项目的主要功能集中到 GUI 对话输入区及其相邻抽屉/浮层中，保证用户不离开对话主流程即可完成优化、比较、采用、撤销和发送。
- [ ] **RC-007** 对话输入区必须有菱形星星形态的“优化输入内容”入口，一次点击即可触发后台提示词优化。
- [ ] **RC-008** 已配置可用 API 时，默认使用当前会话所选 API/模型优化提示词；未配置 API 时，默认调用 Rabbit Code 本地 FastAPI 优化服务。
- [ ] **RC-009** 明确 FastAPI 是本地服务框架而不是模型：FastAPI 服务内部调用已安装的 Gemma、Qwen2.5-Coder或现有离线规则 Provider 完成实际优化。
- [ ] **RC-010** GUI 首次打开时只提供两个清晰的主选项：“使用 API”和“无 API，使用本地模型”，并允许用户完成首次配置后随时切换。
- [ ] **RC-011** 无 API 路线必须提供可执行的自动安装脚本和 GUI 安装向导，帮助用户安装、验证、选择和运行 Gemma 或 Qwen2.5-Coder。
- [ ] **RC-012** API 路线必须支持 OpenAI 格式、Gemini 原生格式、Claude/Anthropic 原生格式，并覆盖市面主流服务商的兼容接入。
- [ ] **RC-013** 所有独立 GUI 页面都必须出现兔兔素材或由其派生且经批准的品牌元素，并保证美观、克制、清晰和可访问。
- [ ] **RC-014** “全部功能完成”必须以本文件的验收矩阵、自动化测试和发布门槛为准，不以页面存在或接口可调用代替完成度。

### 1. 原始需求追踪矩阵

| 编号 | 不可丢失的原始要求 | 主要落实章节 |
| --- | --- | --- |
| R1 | GitHub 调研 Codex、OpenCode、Claude Code；终端对标 Claude Code；GUI 对标 Codex 桌面端 | 2、3、6、7、8、9 |
| R2 | 每个独立页面都有兔兔素材并优化整体布局 | 10、11、22 |
| R3 | 对话框集成菱形星星；点击后自动优化；有 API 用用户 API，无 API 用默认 FastAPI | 12、13、14 |
| R4 | GUI 首页提供 API 登录和无 API 登录；无 API 自动安装 Gemma、Qwen2.5-Coder并可二选一对话 | 15、16 |
| R5 | 完成所有涉及功能，包括 API 接入相关代码 | 5 至 26 的全部交付与验收项 |
| R6 | 支持主流 AI API，包括 OpenAI、Gemini、Claude Code/Claude 格式 | 14、15、21 |

原初 12 类计划也必须全部保留：项目前期准备、开源调研、架构设计、核心功能开发、GUI 设计、提示词优化、API 接入、本地模型集成、整合测试、文档部署、优化迭代、开源发布；本文件将它们细化为以下 27 个部分。

### 2. 开源项目调研与可借鉴边界

- [x] **RC-015** 固定调研基线的仓库 URL、默认分支、Commit SHA、调研日期和许可证版本，避免只记录会移动的 `main` 或 `dev`。
- [x] **RC-016** 调研 [openai/codex](https://github.com/openai/codex) 的 Apache-2.0 开源终端 Agent，重点覆盖 `core`、`cli`、`tui`、`app-server`、协议、权限、沙箱、MCP、配置、文件搜索、Git、会话和模型 Provider 模块。
- [x] **RC-017** 区分“Codex CLI/App Server 开源”与“Codex 桌面产品完整 GUI 源码可用”两件事；桌面端布局和交互只做产品行为研究，不预设可以获取或复制其专有实现。
- [x] **RC-018** 调研 [anomalyco/opencode](https://github.com/anomalyco/opencode) 的 MIT 开源实现，重点覆盖 `packages/opencode`、`cli`、`tui`、`desktop`、`app`、`server`、`protocol`、`llm`、`plugin`、`sdk` 和 `ui`。
- [x] **RC-019** 调研 [anthropics/claude-code](https://github.com/anthropics/claude-code) 的公开仓库、文档、示例、插件、Hooks、工具和权限行为；该仓库核心程序受 Anthropic 商业条款约束，不作为可复制的开源核心源码。
- [x] **RC-020** 调研 [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) 的消息流、交互会话、自定义工具、MCP、Hooks、权限和会话分叉接口，同时单独审核 SDK 代码许可证、捆绑 Claude Code CLI 和商业条款之间的边界。

#### 2.1 Claude Code source map 暴露与还原仓库专项调研

截至 2026-07-16，GitHub 上确实存在多个声称由 Claude Code 发布包 source map 还原源码的仓库。公开可访问不等于获得开源授权，Rabbit Code 必须把“研究价值”和“可复制代码”分别判断。

| 仓库 | 仓库自述与当前状态 | Rabbit Code 处理方式 |
| --- | --- | --- |
| [ChinaSiro/claude-code-sourcemap](https://github.com/ChinaSiro/claude-code-sourcemap) | 声称从公开 npm 包 `@anthropic-ai/claude-code` v2.1.88 的 `cli.js.map` 中提取 `sourcesContent`，还原约 1,884 个 TypeScript/TSX 源文件；仓库声明版权归 Anthropic、仅供研究；GitHub 未识别到许可证 | 作为本次泄露事件的主要事实索引和架构研究候选；未经法律审查不得复制、依赖、分发或用于产品实现 |
| [oboard/claude-code-rev](https://github.com/oboard/claude-code-rev) | 在 source map 还原基础上补齐缺失模块，使工程可安装运行；存在兼容 shim 和降级实现；无许可证 | 仅用于识别功能边界和缺失模块，不运行于 Rabbit Code 构建、测试或发布链路，不将其修改代码视为 Anthropic 原始实现 |
| [ghuntley/claude-code-source-code-deobfuscation](https://github.com/ghuntley/claude-code-source-code-deobfuscation) | 早期 Claude Code npm 包的 clean-room 反混淆研究；仓库已归档；无许可证 | 作为历史研究方法参考，不作为可复用源码 |
| [ComeOnOliver/claude-code-analysis](https://github.com/ComeOnOliver/claude-code-analysis) | MIT 许可的独立架构分析文档，覆盖 Agent、工具、权限、上下文、任务、UI、插件和 Hooks | 优先阅读其抽象设计说明；仍需检查其中是否包含超出合理引用的 Anthropic 原文或代码片段 |
| [dadiaomengmeimei/claude-code-sourcemap-learning-notebook](https://github.com/dadiaomengmeimei/claude-code-sourcemap-learning-notebook) | MIT 许可的 source map 学习笔记，提炼 Agent Loop、工具、安全、压缩、多 Agent、MCP 和技能模式 | 可作为二级研究资料；MIT 只覆盖作者有权许可的原创内容，不能自动替 Anthropic 源码授予许可 |

- [x] **RC-021** 记录上述仓库的默认分支、Commit SHA、README、许可证文件、归档状态、DMCA/删除状态和调研日期，避免将当前可见性误认为永久授权。
- [x] **RC-022** 在查看还原源码正文、运行还原工程或形成实现规格前完成法律与许可证评估，单独记录 source map 暴露是否构成有效公开授权的结论。
- [x] **RC-023** 不把无许可证的还原仓库克隆到 Rabbit Code 工作树、CI 缓存、依赖树、Docker 镜像、安装包或发布制品中。
- [x] **RC-024** 禁止复制其中的源码、System Prompt、内部文案、测试、资源、注释、私有协议常量、功能开关名称和未公开服务端点。
- [x] **RC-025** 将调研人员与实现人员进行 clean-room 信息隔离：调研输出只描述问题、输入输出、状态转换、安全约束和可验证行为，不包含源文件名、代码结构复刻或原文片段。
- [x] **RC-026** 实现人员只依据 clean-room 规格、Claude Code 官方文档/SDK、公开黑盒行为和许可证清晰的 Codex/OpenCode源码独立设计。
- [x] **RC-027** 使用官方 Claude Code 可执行程序、公开文档和自建行为测试进行兼容性验证，不使用泄露源码测试文件作为 Rabbit Code 的 golden fixture。
- [x] **RC-028** 对 MIT 分析资料做内容来源审计，区分作者原创分析、合理引用和可能仍受 Anthropic 版权保护的衍生内容。
- [x] **RC-029** 若 Anthropic 后续正式开源、明确授权或发布可复用规范，再通过 ADR 重新评估复用范围；在此之前默认结论为“可研究事实，不可直接复用代码”。
- [x] **RC-030** 输出《Claude Code source map 事件调研与 Rabbit Code clean-room 决策记录》，作为 M0 和开源发布审计的必需材料。

- [x] **RC-031** 调研 Gemma、Qwen2.5-Coder、Ollama、llama.cpp、Hugging Face 模型文件的代码许可证、模型许可证、再分发限制、署名和用户确认要求。
- [x] **RC-032** 为所有拟复用实现建立“来源、许可证、复用方式、修改内容、NOTICE 要求、替代方案”清单。
- [x] **RC-033** 对无许可、商业条款或来源不清晰的代码采用 clean-room 行为重实现，保留设计记录，不复制代码、提示词、隐藏协议或受保护资产。
- [x] **RC-034** 对 Rabbit Code、兔兔形象、包名和 GitHub 组织名进行公开商标信息、命名冲突与可发布性检查，不要求域名或应用商店账户。
- [x] **RC-035** 确认用户提供的 `兔兔素材.png` 拥有开源项目使用、修改、派生和再分发权，并记录素材许可证与署名要求。
- [x] **RC-036** 输出调研报告、功能对比矩阵、技术选型 ADR、许可证清单和明确的“不复用项”。

### 3. 产品范围、用户场景与验收口径

- [x] **RC-037** 定义目标用户：个人开发者、无 API 用户、多 Provider 用户、开源贡献者和团队开发者。
- [x] **RC-038** 定义首发平台：Windows、Linux，并分别列出 CPU 架构、终端、Shell、GPU 和未签名安装包支持矩阵。
- [x] **RC-039** 定义核心场景：打开仓库、发起编码任务、阅读代码、规划、编辑、运行命令、测试、审查 diff、恢复会话、切换模型、优化提示词和本地离线对话。
- [x] **RC-040** 定义 CLI、GUI 和无头模式的功能一致性范围，明确哪些能力共享核心、哪些仅属于桌面显示层。
- [x] **RC-041** 定义 MVP、首个稳定版和后续增强版边界，但所有原始要求必须进入首个稳定版，不得以“后续考虑”永久搁置。
- [x] **RC-042** 为每项功能定义成功、失败、取消、重试、降级、离线、权限拒绝和数据恢复的验收状态。
- [x] **RC-043** 建立需求 ID、设计、代码、测试、文档和发布说明之间的可追踪关系。
- [x] **RC-044** 制定版本策略、兼容策略、废弃策略、数据库迁移策略和配置迁移策略。
- [x] **RC-045** 在技术预研后制定实际开发时间表、人员/模块负责人、依赖关系、风险缓冲和里程碑日期。

### 4. 现有 Prompt Optimizer 资产盘点与迁移

- [x] **RC-046** 保留现有 Python 3.12、FastAPI、React、Vite、TypeScript、SQLite、Typer、测试和 Docker 基础，先通过 ADR 决定升级或替换范围。
- [x] **RC-047** 复用并回归验证现有评分、建议、规则、模板、优化、版本 diff、历史、导出和评测模块。
- [x] **RC-048** 复用现有 `/api/analyze`、`/api/optimize`、`/api/optimize/stream`、任务、认证、项目和版本接口的有效能力。
- [x] **RC-049** 将现有仅能基本处理 OpenAI Chat Completions 的通用 HTTP Provider 拆分为协议明确、能力可探测的 Provider Adapter。
- [x] **RC-050** 保留 `OfflineRuleProvider` 作为无网络、模型未安装、模型加载失败时的最终可用降级，而不是把它误称为大模型。
- [x] **RC-051** 将现有 `prompt-opt` CLI 与 Rabbit Code Agent CLI 的命令空间、配置和存储进行兼容迁移。
- [x] **RC-052** 评估现有 JWT 本地用户体系是否仍有必要，区分“Rabbit Code 本地用户资料”与“第三方 API 凭据配置”。
- [x] **RC-053** 为现有 SQLite 数据、提示词历史、模板和配置提供备份、迁移、回滚与损坏恢复方案。
- [x] **RC-054** 更新产品名称、包名、环境变量、应用数据目录和 API 标题，同时提供旧名称兼容期。
- [x] **RC-055** 不覆盖现有可复现的 V2 发布线，Rabbit Code 使用独立分支、版本和迁移说明。

### 5. 总体技术架构

- [x] **RC-056** 采用 Monorepo 管理桌面端、CLI、Agent Core、FastAPI App Server、Provider、协议、UI、安装脚本、测试和文档。
- [x] **RC-057** 形成“共享 Agent Core + 本地 App Server + CLI/TUI + Tauri 桌面壳 + React GUI”的候选基线，并通过跨平台原型验证后锁定。
- [x] **RC-058** FastAPI App Server 作为 GUI、CLI、提示词优化、本地模型和后台任务的统一本地服务入口。
- [x] **RC-059** CLI 可选择进程内调用共享核心或连接本地 App Server，但二者必须使用同一事件和数据模型。
- [x] **RC-060** Tauri 只承担桌面窗口、系统集成、更新、密钥库桥接和 FastAPI sidecar 生命周期，业务逻辑不散落到桌面壳。
- [x] **RC-061** 定义版本化协议层，覆盖请求、会话、消息、内容块、工具调用、审批、流事件、diff、任务状态、错误和 Provider 能力。
- [x] **RC-062** 从 Pydantic/OpenAPI 生成 TypeScript 类型和客户端，禁止前后端手写两套漂移协议。
- [x] **RC-063** 统一同步、SSE、WebSocket 或 JSON-RPC 的使用边界，支持流式文本、工具事件、进度、取消和断线恢复。
- [x] **RC-064** 使用 SQLite 保存本地结构化数据，文件系统保存大型日志、缓存、模型和附件，并定义事务与并发访问策略。
- [x] **RC-065** 建立配置分层：应用默认、用户全局、工作区、会话和临时覆盖，明确优先级、敏感字段存储位置和来源查询。
- [x] **RC-066** 将 Agent、Provider、工具、权限、存储、提示词优化和 UI 解耦，允许独立测试与替换。
- [x] **RC-067** 设计前后台进程的启动、健康检查、端口发现、崩溃拉起、优雅退出、升级兼容和僵尸进程清理。

### 6. Claude Code 风格的 Agent 核心

- [x] **RC-068** 实现可观测的 Agent 状态机：接收目标、组装上下文、模型推理、工具请求、权限决策、工具执行、结果回传、继续迭代和最终答复。
- [x] **RC-069** 支持交互对话、单次 `print`/无头执行、管道输入、结构化 JSON 输出和退出码。
- [x] **RC-070** 支持 Plan/只读模式、Edit/工作区写入模式和更高权限模式，并在 CLI 与 GUI 中保持一致语义。
- [x] **RC-071** 支持流式文本、思考状态摘要、工具调用卡片、后台任务进度、部分失败和用户中断。
- [x] **RC-072** 支持最大轮次、超时、Token、费用、上下文和并发任务限制。
- [x] **RC-073** 支持暂停、取消、重试、从失败点继续、重新生成和幂等工具调用。
- [x] **RC-074** 支持主 Agent、受控子 Agent、并行只读探索、结果汇总和并发槽限制。
- [x] **RC-075** 支持 Hooks，在工具执行前后、会话开始结束、权限请求和错误时触发确定性策略。
- [x] **RC-076** 支持 MCP 客户端、内置工具服务器和第三方工具服务器，覆盖 stdio、HTTP 及认证生命周期。
- [x] **RC-077** 支持可安装的技能/插件、工作区指令和命令扩展，并建立来源、哈希、权限、版本和兼容机制。
- [x] **RC-078** 支持模型能力协商，按文本、图像、工具调用、结构化输出、上下文长度和推理参数选择行为。
- [x] **RC-079** 不把任一模型的隐藏思维链写入日志或 UI，只呈现允许公开的简短进度和依据。

### 7. 上下文、记忆与会话管理

- [x] **RC-080** 自动识别 Git 仓库根目录、工作树、分支、未提交改动、语言、构建工具和项目指令文件。
- [x] **RC-081** 支持 `AGENTS.md`、Rabbit Code 专属项目指令、用户全局指令和目录级覆盖规则。
- [x] **RC-082** 支持文件提及、目录提及、代码选择、图片/附件、终端输出、diff 和错误诊断进入上下文。
- [x] **RC-083** 实现尊重 `.gitignore`、Rabbit Ignore、二进制文件、超大文件、敏感路径和符号链接的搜索与索引。
- [x] **RC-084** 实现上下文预算、去重、相关性排序、缓存、自动摘要和长会话压缩。
- [x] **RC-085** 区分临时上下文、会话记忆、项目记忆和用户长期偏好，并允许查看、编辑、禁用和清除。
- [x] **RC-086** 支持新建、命名、搜索、置顶、归档、删除、恢复、继续、分叉和导出会话。
- [x] **RC-087** 支持会话检查点、文件变更快照、工具记录和可解释的撤销/回滚。
- [x] **RC-088** 支持多个工作区、Git worktree、独立会话环境和任务隔离。
- [x] **RC-089** 设计会话数据库迁移、崩溃恢复、损坏检测、备份和隐私清理。

### 8. 工具系统与编码工作流

- [x] **RC-090** 提供受控的文件读取、目录列举、快速搜索、文件编辑、补丁应用、创建、移动和删除工具。
- [x] **RC-091** 提供 PowerShell、cmd、Bash、zsh 等终端命令工具，并正确处理 Windows Unicode、路径、引号和换行。
- [x] **RC-092** 提供 Git 状态、diff、日志、分支、worktree、暂存、提交和冲突辅助能力，任何远程推送或 PR 操作需显式授权。
- [x] **RC-093** 提供测试、Lint、类型检查、构建、包管理器和语言服务器诊断的标准化结果展示。
- [x] **RC-094** 提供进程管理、后台命令、端口发现、日志跟踪和安全终止能力。
- [x] **RC-095** 提供结构化 `apply_patch` 或等价编辑机制，保留原子性、冲突检查和编码格式。
- [x] **RC-096** 处理工具输出截断、超时、重试、二进制内容、巨量日志、非零退出码和部分成功。
- [x] **RC-097** 为每个工具定义 JSON Schema、权限等级、幂等性、可取消性和审计字段。
- [x] **RC-098** 支持工具调用结果在 CLI、GUI 和 API 中使用同一内容块协议呈现。
- [x] **RC-099** 提供可扩展的浏览器预览、MCP、数据库或外部服务工具接口，但默认不授予隐式网络或写权限。

### 9. CLI/TUI 设计与实现

- [x] **RC-100** 提供 `rabbit` 交互入口以及明确的单次执行、继续会话、恢复会话、选择模型、选择模式和 JSON 输出参数。
- [x] **RC-101** 构建 Claude Code 风格但属于 Rabbit Code 的终端交互：输入区、流式输出、工具状态、权限询问、计划、diff 和 Token/费用状态。
- [x] **RC-102** 支持多行输入、历史、搜索、补全、文件提及、图片/附件路径、粘贴保护和可配置快捷键。
- [x] **RC-103** 支持斜杠命令，包括帮助、模型、Provider、权限、计划、上下文、会话、清理、压缩、MCP、插件、诊断和退出。
- [x] **RC-104** 支持非交互 CI 使用，禁止在无 TTY 环境卡在权限提示，并提供清晰退出码。
- [x] **RC-105** 支持 `--dry-run`、只读分析、机器可读事件流和日志级别。
- [x] **RC-106** CLI 和 GUI 必须共享 Provider 配置、密钥引用、模型清单、会话、权限规则和提示词优化服务。
- [x] **RC-107** 验证 Windows Terminal、PowerShell、cmd、WSL 和主流 Linux 终端的兼容性。
- [x] **RC-108** 提供 Shell 补全、安装路径检查、版本检查、诊断命令和卸载清理命令。

### 10. Codex 桌面端风格的 GUI 信息架构

- [x] **RC-109** 首次启动/登录页：两个主入口、环境状态、Rabbit Code 品牌和兔兔素材。
- [x] **RC-110** 工作区首页：最近项目、打开项目、最近任务、Provider/本地模型状态和快速新建任务。
- [x] **RC-111** 主任务页：左侧工作区与会话，中间对话与输入框，按需显示右侧变更审查/计划/上下文，底部或抽屉集成终端。
- [x] **RC-112** 变更审查页或面板：文件树、逐文件 diff、逐块接受/拒绝、回退和测试状态。
- [x] **RC-113** 终端与进程页或面板：多终端标签、后台任务、命令状态和停止操作。
- [x] **RC-114** Provider 与模型页：API 配置、模型发现、连通性、能力、费用提示和默认选择。
- [x] **RC-115** 本地模型安装页：硬件检测、Gemma/Qwen2.5-Coder选择、下载进度、运行状态、修复和卸载。
- [x] **RC-116** 提示词资产页：模板、历史版本、评分、对比、收藏、搜索、导入和导出；核心入口仍保留在对话框。
- [x] **RC-117** 设置页：外观、语言、终端、权限、沙箱、数据、隐私、更新、快捷键、MCP、插件和高级配置。
- [x] **RC-118** 诊断/关于/更新页：版本、日志、组件健康、许可证、隐私和更新状态。
- [x] **RC-119** 空状态、错误状态、离线状态、权限弹窗和安装弹窗都纳入统一视觉系统。
- [x] **RC-120** 支持窗口恢复、多窗口或多工作区策略、系统托盘策略、通知、深色/浅色主题和高 DPI。
- [x] **RC-121** 桌面端采用原生标题栏或自绘标题栏前，验证拖拽、最大化、缩放、无障碍和跨平台一致性。

### 11. 兔兔素材与视觉系统

- [x] **RC-122** 将用户提供的 `C:\Users\10735\Desktop\提示词\兔兔素材.png` 作为品牌源素材登记，不直接依赖桌面外部路径运行。
- [x] **RC-123** 建立原图、透明背景、裁切头像、单色小标、空状态、浅色和深色适配等派生资产规范。
- [x] **RC-124** 首页使用较完整的兔兔形象；工作型页面使用克制的侧栏标记、页角插图、水印或空状态，避免遮挡代码、diff、终端和对话内容。
- [x] **RC-125** 每个独立路由通过统一 `RabbitMark`/品牌槽位强制出现兔兔元素，弹窗和面板按层级决定是否复用，避免机械堆叠。
- [x] **RC-126** 建立“页面、素材变体、位置、尺寸、主题、响应式行为、替代文本”覆盖矩阵。
- [x] **RC-127** 优化原图的大面积留白、文件尺寸、裁切焦点和清晰度，输出合适的 PNG/WebP/应用图标资源。
- [x] **RC-128** 为小尺寸图标单独设计可辨识版本，不能简单缩小整张原图导致兔兔不可见。
- [x] **RC-129** 控制兔兔素材与功能信息的视觉层级，保证产品是高效编码工具而非装饰性展示页。
- [x] **RC-130** 建立颜色、字体、间距、边框、阴影、图标、动效、状态色和代码字体 Design Token。
- [x] **RC-131** 使用熟悉的图标表达工具操作；菱形星星使用统一 Sparkles 图标语言并提供 Tooltip 和可访问名称。
- [x] **RC-132** 满足键盘导航、焦点可见、屏幕阅读器、对比度、减少动态效果和缩放至 200% 的要求。
- [x] **RC-133** 使用视觉回归测试确保所有独立页面包含兔兔素材且不存在重叠、裁切、溢出或主题失真。

### 12. 对话框与菱形星星提示词优化交互

- [x] **RC-134** 参考用户提供的 Trae 截图，将菱形星星放在模型选择与发送操作附近，但按 Rabbit Code 的视觉系统重排间距、层级和状态。
- [x] **RC-135** 星星按钮必须有空闲、悬停、按下、加载、成功、失败、禁用和取消状态，布局尺寸固定不跳动。
- [x] **RC-136** Tooltip 和无障碍名称使用“优化输入内容”，按钮不可与发送、语音、附件或模型选择混淆。
- [x] **RC-137** 点击时对当前文本建立快照并触发后台优化，输入为空、只有附件、超长或已有任务时提供明确处理。
- [x] **RC-138** 优化期间允许取消；用户继续编辑时避免旧结果覆盖新内容，可提示比较或重新优化。
- [x] **RC-139** 默认不自动发送优化结果，先展示优化后的可编辑内容，由用户采用、部分采用、撤销或直接发送。
- [x] **RC-140** 提供原文/优化后切换、行内或并排 diff、复制、替换、重新生成、撤销和恢复原文。
- [x] **RC-141** 展示实际使用的 Provider/模型、是否降级、耗时和错误，但不暴露 API 密钥或内部提示词。
- [x] **RC-142** 保留代码块、文件提及、附件、命令、变量占位符和用户指定输出格式，避免优化过程破坏语义。
- [x] **RC-143** 支持中文、英文及混合语言，默认保持用户语言，除非用户明确要求翻译。
- [x] **RC-144** 将模板选择、场景/角色、优化强度、评分、历史和版本对比放入输入框关联浮层或侧抽屉，主界面保持安静。
- [x] **RC-145** 提供键盘触发能力、焦点恢复、屏幕阅读器播报和触控可用性。
- [x] **RC-146** 保存原文、优化结果、采用状态、Provider、模型和版本信息，并允许用户关闭历史保存。

### 13. 提示词优化路由与 FastAPI 服务

- [x] **RC-147** 定义唯一的 `PromptOptimizationService`，供菱形星星、CLI、API 和后台任务复用。
- [x] **RC-148** 有可用 API 时，默认选择当前对话的 Provider/模型进行优化；允许用户单独指定“优化器模型”并记住选择。
- [x] **RC-149** 无 API 时，GUI 始终调用本机 FastAPI 优化接口，由服务选择当前已安装的 Gemma 或 Qwen2.5-Coder。
- [x] **RC-150** 本地模型尚未安装、不可用或资源不足时，FastAPI 自动降级到现有离线规则 Provider，保证按钮仍能工作并明确标记降级。
- [x] **RC-151** 定义路由优先级、超时、重试、限流、熔断、取消和用户授权的备用 Provider，不允许静默把私有提示词发送到其他云服务。
- [x] **RC-152** 支持流式优化事件：开始、分析、文本增量、保存、完成、取消和错误。
- [ ] **RC-153** 设计专用的提示词优化 System Prompt、版本管理、Provider 差异适配和提示注入防护。（实现已完成，专项运行验证待具备 Python 依赖的环境复核）
- [x] **RC-154** 支持优化目标参数：清晰度、完整度、约束、格式、角色、示例、代码任务、简洁度和语言保持。
- [x] **RC-155** 支持模板、规则分析和模型优化组合，避免模型输出只做表面扩写。
- [x] **RC-156** 对 API 输出做结构验证、长度限制、恶意内容边界和解析失败恢复。
- [x] **RC-157** 记录质量指标、延迟、Provider、模型和降级信息，默认不记录完整敏感提示词。
- [x] **RC-158** 建立提示词优化评测集，覆盖编码、商务、教育、创意、长文本、代码块、变量、中文和对抗输入。

### 14. 多 Provider 与 API 协议接入

- [x] **RC-159** 将“API 登录”在产品内准确表达为“使用 API/配置 Provider”，避免让用户误以为 API Key 是 Rabbit Code 账户密码。
- [x] **RC-160** OpenAI 格式支持标准 Base URL、API Key、模型、组织/项目头、Chat Completions、流式响应、工具调用和兼容端点差异。
- [x] **RC-161** 评估并支持 OpenAI Responses API，不能假设所有 OpenAI 兼容服务都实现相同端点或参数。
- [x] **RC-162** Gemini 原生格式支持 `generateContent`、`streamGenerateContent`、System Instruction、工具调用、安全设置和 Gemini 错误结构。
- [x] **RC-163** Claude/Anthropic 原生格式支持 Messages API、流式事件、System、content blocks、tool use、缓存/扩展参数能力探测。
- [x] **RC-164** 将用户所称“Claude Code 格式”映射为有公开规范的 Anthropic/Claude API 或经审计的官方 Agent SDK 集成；不使用非官方方式盗用 Claude Code 订阅登录或令牌。
- [x] **RC-165** 支持 Azure OpenAI、Google Vertex AI、AWS Bedrock 等主流托管变体所需的认证、区域、部署名和端点配置。
- [x] **RC-166** 通过 OpenAI 兼容适配覆盖 OpenRouter、DeepSeek、Moonshot/Kimi、Qwen、智谱、豆包、SiliconFlow、Groq、Together、Ollama、LM Studio 等服务，并允许自定义请求头。
- [x] **RC-167** Provider Adapter 声明能力：文本、图像、工具、结构化输出、流式、上下文长度、模型列表、Token 统计和费用信息。
- [x] **RC-168** 支持自动模型发现与手动模型 ID；发现失败不能阻止用户使用已知模型。
- [x] **RC-169** 提供连接测试，验证认证、模型可用性、流式、工具调用和最小请求，而不是只检查 TCP 连通。
- [x] **RC-170** 统一错误分类：认证、余额、限流、区域、模型不存在、参数不兼容、内容过滤、网络、超时和服务端错误。
- [x] **RC-171** 实现指数退避、`Retry-After`、请求取消、代理、自定义 CA、IPv4/IPv6 和企业网络设置。
- [x] **RC-172** 提供每会话模型选择、默认模型、提示词优化模型、自动回退、最大费用和 Token 预算。
- [x] **RC-173** 为所有 Provider 建立 Mock/契约测试；真实 API 测试仅允许用户提供 Key 后手动启用，并明确可能产生的费用。

### 15. 首页双入口与凭据管理

- [x] **RC-174** 首次启动页以两个等权但解释清晰的主选项呈现：“使用 API”和“无 API，使用本地模型”。
- [x] **RC-175** “使用 API”向导包含协议/服务商、Base URL、API Key/官方认证、模型、连接测试、保存和默认模型设置。
- [x] **RC-176** “无 API”向导进入硬件检测、本地运行器选择、Gemma/Qwen2.5-Coder选择、许可证确认、安装和验证。
- [x] **RC-177** 两条路线完成后进入同一个工作区首页，不构建两套割裂产品。
- [x] **RC-178** 用户可在设置和模型选择器中随时新增、编辑、禁用、切换或删除 Provider 与本地模型。
- [x] **RC-179** API Key 使用 Windows Credential Manager、Linux Secret Service 或等价安全存储，不以明文写入 SQLite、日志或仓库。
- [x] **RC-180** UI 只显示掩码和密钥末尾标识，复制、导出、错误报告和遥测均不得泄漏密钥。
- [x] **RC-181** 支持环境变量和配置文件引用，但明确优先级并在 UI 中显示来源，不反向展示密钥明文。
- [x] **RC-182** 官方 OAuth 只在服务商明确允许第三方客户端时实现，包含 PKCE、回调、刷新、撤销和到期处理。
- [x] **RC-183** 本地使用默认无需 Rabbit Code 云账户；如后续增加同步账户，必须与 Provider 凭据和本地资料隔离。
- [x] **RC-184** 提供凭据迁移、清除、重置和“删除所有本地数据”流程。

### 16. Gemma 与 Qwen2.5-Coder 本地模型集成

- [x] **RC-185** 提供 Windows PowerShell、Linux Shell 安装脚本，并由 GUI 安装向导调用同一安装核心。
- [x] **RC-186** 安装前检测操作系统、CPU、内存、磁盘、GPU、显存、驱动、网络、代理和已有运行器。
- [x] **RC-187** 选择经许可证审计的本地运行器，候选包括 Ollama 与 llama.cpp；抽象运行器接口避免强绑定。
- [x] **RC-188** 提供 Gemma 和 Qwen2.5-Coder 的受控模型清单，按硬件推荐参数规模、量化、上下文长度和预计磁盘/内存占用。
- [x] **RC-189** Qwen 路线明确支持用户要求的 Qwen2.5-Coder，而不是悄悄替换成其他 Qwen 系列。
- [x] **RC-190** Gemma 路线在锁定具体版本和量化文件前审核模型卡、许可证、用途限制和聊天模板。
- [x] **RC-191** 安装脚本支持下载续传、校验和、版本固定、镜像/代理、失败重试、进度、取消和幂等重跑。
- [x] **RC-192** 不在未经许可时把模型权重直接打进 Rabbit Code 安装包；必要时让用户查看并接受模型许可证后下载。
- [x] **RC-193** 安装完成后执行加载、最小生成、流式输出、停止、上下文和资源占用健康检查。
- [x] **RC-194** GUI 显示下载、校验、加载、就绪、忙碌、卸载、损坏和更新状态。
- [x] **RC-195** 用户可在 Gemma 与 Qwen2.5-Coder之间选择默认对话模型，也可按会话切换。
- [x] **RC-196** 支持 CPU-only 环境、GPU 加速探测、并发限制、空闲卸载、OOM 恢复和低内存提示。
- [x] **RC-197** 支持自定义模型目录、迁移目录、磁盘清理、模型更新、回滚、修复和彻底卸载。
- [x] **RC-198** FastAPI 通过运行器 Adapter 调用本地模型，统一流式协议、取消、错误和能力信息。
- [x] **RC-199** 安装和运行不要求管理员权限；确需提权的操作必须单独说明原因并获得同意。
- [x] **RC-200** 提供离线安装包/手动模型导入方案及文件校验，满足受限网络环境。

### 17. 权限、沙箱与安全

- [x] **RC-201** 定义只读、工作区写入和高权限三档策略，文件、终端、网络、Git、MCP 和桌面能力分别授权。
- [x] **RC-202** 危险或越界操作使用明确审批弹窗，展示命令、路径、影响、工作目录和持久授权范围。
- [x] **RC-203** 支持单次允许、会话允许、规则允许、拒绝和修改后执行；默认不提供含糊的“全部永久允许”。
- [x] **RC-204** 为 Windows、Linux 设计实际可用的进程和文件系统沙箱，记录平台能力差异。
- [x] **RC-205** 防止路径穿越、符号链接逃逸、命令注入、环境变量泄漏、恶意仓库指令和工具输出提示注入。
- [x] **RC-206** 保护 `.env`、SSH Key、云凭据、浏览器资料、系统目录和用户指定敏感文件。
- [x] **RC-207** 本地 FastAPI 仅绑定 Loopback，使用每次启动的认证令牌、严格 CORS/Origin、随机端口和最小暴露面。
- [x] **RC-208** 对插件、技能、Hooks、MCP Server 和安装脚本建立来源信任、权限声明、版本锁定和禁用机制。
- [x] **RC-209** 对下载的二进制、模型、更新包和插件执行 HTTPS 来源、许可证和哈希验证，不要求数字签名。
- [x] **RC-210** 默认关闭包含代码/提示词内容的遥测；崩溃报告和诊断包必须预览、脱敏并由用户主动发送。
- [x] **RC-211** 建立威胁模型、安全测试、依赖扫描、秘密扫描、SBOM、漏洞响应和安全公告流程。
- [x] **RC-212** 提供审计日志，但允许用户控制保留期和彻底清除。

### 18. 数据、隐私与可观测性

- [x] **RC-213** 定义会话、消息、工具调用、文件快照、Prompt 版本、Provider 配置、模型清单和设置的数据模型。
- [x] **RC-214** 对 SQLite 使用事务、迁移、索引、并发访问、备份、恢复和损坏检测。
- [x] **RC-215** 对日志使用结构化事件、请求 ID、会话 ID、工具 ID 和任务 ID，默认对提示词、源码、路径和密钥脱敏。
- [x] **RC-216** 显示当前请求是本地处理还是发送到哪个远程 Provider，避免用户误判隐私边界。
- [x] **RC-217** 提供每个 Provider 的数据发送说明、保留风险提示和本地/云标识。
- [x] **RC-218** 支持日志级别、日志轮转、缓存上限、历史保留期和一键清理。
- [x] **RC-219** 记录延迟、首 Token、Token 用量、失败率、工具成功率、模型加载和资源占用等技术指标。
- [x] **RC-220** 遥测必须显式选择加入，开源自托管使用不依赖遥测服务。
- [x] **RC-221** 提供数据导入、导出和可移植格式，不锁定用户会话和提示词资产。

### 19. 性能、稳定性与资源控制

- [x] **RC-222** 定义 GUI 启动时间、CLI 首次响应、流式首 Token、搜索、diff、内存和安装包大小基线。
- [x] **RC-223** 大仓库采用增量索引、忽略规则、缓存和背压，避免启动时扫描阻塞。
- [x] **RC-224** 工具输出、上下文、日志、diff 和附件设置可配置上限并提供安全截断提示。
- [x] **RC-225** FastAPI、桌面壳、终端进程和本地模型异常退出时可恢复，不丢失已提交的会话状态。
- [x] **RC-226** 支持请求取消向下传播到 Provider、工具子进程和本地模型生成。
- [x] **RC-227** 对限流、断网、代理失败、模型 OOM、磁盘满、数据库锁和端口冲突做专项恢复。
- [x] **RC-228** 控制本地模型并发、线程、GPU 层、上下文和空闲时间，避免拖垮用户系统。
- [x] **RC-229** 建立性能基准和长期回归阈值，所有 README 性能数字必须来自可复现测试。

### 20. 测试与质量保证

- [x] **RC-230** Agent Core 单元测试覆盖状态转换、工具循环、取消、重试、预算、压缩和恢复。
- [x] **RC-231** Provider 契约测试覆盖 OpenAI、Responses、Gemini、Anthropic、兼容端点、流式、工具和错误映射。
- [x] **RC-232** FastAPI 测试覆盖鉴权、优化路由、降级、SSE/WebSocket、任务、并发和本地安全。
- [x] **RC-233** CLI 测试覆盖交互、无头、JSON、退出码、TTY/非 TTY、Shell 和会话恢复。
- [x] **RC-234** GUI 组件和 E2E 测试覆盖双入口、配置 API、本地模型安装、对话、星星优化、采用结果、发送、diff 和设置。
- [x] **RC-235** 视觉回归覆盖所有独立页面、兔兔素材、深浅主题、常见分辨率、缩放、长文本和空/错/加载状态。
- [x] **RC-236** 无障碍测试覆盖键盘、焦点、语义、Tooltip、屏幕阅读器、对比度和减少动画。
- [x] **RC-237** 本地模型测试覆盖 Gemma、Qwen2.5-Coder、CPU、可用 GPU、低内存、断点续传、损坏下载、修复和卸载。
- [x] **RC-238** 安装包测试覆盖干净机器、升级、降级阻止、卸载、残留数据选择和 SHA-256 哈希校验，不要求代码签名。
- [x] **RC-239** 安全测试覆盖密钥泄漏、路径逃逸、命令注入、本地端口、恶意 MCP/插件、恶意仓库和供应链。
- [x] **RC-240** Prompt 优化质量测试覆盖优化前后得分、人工评审、语义保持、格式保持、代码块和多语言。
- [x] **RC-241** 使用 Provider Mock 作为 CI 默认路径；真实 API 和真实大模型测试仅作为用户自有资源的受控可选手动矩阵。
- [x] **RC-242** 建立 Windows、Linux CI，执行格式、Lint、类型、单元、集成、E2E、构建和许可证检查。
- [x] **RC-243** 设定覆盖率和关键路径门槛；不允许用高总覆盖率掩盖权限、密钥、安装和迁移路径缺测。

### 21. GUI/CLI 功能联调与完整性验收

- [x] **RC-244** 同一工作区在 CLI 和 GUI 中看到一致的会话、Provider、模型、权限、提示词版本和文件变更。
- [x] **RC-245** GUI 创建的任务可由 CLI 恢复，CLI 创建的会话可在 GUI 中打开并正确渲染工具事件。
- [x] **RC-246** API 用户可完成“配置 Provider → 连接验证 → 对话 → 星星优化 → 使用同一 API 优化 → 采用 → 发送”。
- [x] **RC-247** 无 API 用户可完成“选择无 API → 检测硬件 → 安装 Gemma/Qwen2.5-Coder → 健康验证 → 选择模型 → 对话 → FastAPI 优化”。
- [x] **RC-248** 无 API 且模型尚未就绪时，星星按钮仍通过 FastAPI + 离线规则完成优化，并明确显示降级。
- [x] **RC-249** 网络中断、Key 失效、限流或模型错误时，原始输入不丢失，用户可重试、切换或使用本地路线。
- [x] **RC-250** Agent 修改文件后，GUI 和 CLI 都能展示 diff、运行验证、接受/拒绝并恢复检查点。
- [x] **RC-251** 所有独立页面均通过兔兔素材覆盖自动检查和人工视觉验收。
- [x] **RC-252** 所有关键流程均有中文界面；国际化框架不把文本硬编码在组件中。
- [x] **RC-253** 完成需求追踪矩阵审计，确认 R1 至 R6 与原初 12 类计划无遗漏。

### 22. 设计验收与体验优化

- [x] **RC-254** 在编码前完成低保真信息架构、主流程、对话输入区和首页双入口评审。
- [x] **RC-255** 完成桌面与小窗口尺寸的高保真设计，覆盖长 Provider 名、长模型名、中英文和错误文案。
- [x] **RC-256** 通过截图与真实运行检查页面无重叠、无溢出、无不可见按钮、无动态内容引起的布局跳动。
- [x] **RC-257** 菱形星星与发送按钮保持清晰主次，优化中不能误触重复请求，完成后不能自动覆盖用户新输入。
- [x] **RC-258** 兔兔元素在每页可见但不妨碍扫描代码、终端、diff、设置和模型状态。
- [x] **RC-259** 动画只用于状态反馈和空间转换，支持减少动态效果，避免持续装饰动画消耗资源。
- [x] **RC-260** 通过新用户测试验证双入口、本地模型安装、API 配置和星星优化无需阅读外部教程即可完成。
- [x] **RC-261** 通过高频用户测试优化键盘流、焦点、快捷命令、会话切换和 diff 审查效率。

### 23. 文档、开发者体验与贡献机制

- [x] **RC-262** 编写中英文 README，准确说明 Rabbit Code 定位、截图、功能、安装、快速开始、隐私和许可证。
- [x] **RC-263** 编写架构文档、Agent 循环、协议、Provider、工具、权限、数据模型和桌面进程文档。
- [x] **RC-264** 编写 OpenAI、Gemini、Claude/Anthropic、Azure、Vertex、Bedrock 和自定义兼容端点接入指南。
- [x] **RC-265** 编写 Gemma、Qwen2.5-Coder安装、硬件选择、离线导入、故障排查、更新和卸载指南。
- [x] **RC-266** 编写 CLI 命令、GUI 工作流、菱形星星优化、会话、diff、MCP、插件和 Hooks 使用手册。
- [x] **RC-267** 编写本地开发、测试、打包、发布、数据库迁移和调试指南。
- [x] **RC-268** 编写安全策略、隐私说明、遥测说明、漏洞报告和数据删除指南。
- [x] **RC-269** 提供 Provider Adapter、工具、MCP、插件和主题扩展示例及稳定 API 版本策略。
- [x] **RC-270** 配置 Issue 模板、PR 模板、贡献指南、行为准则、路线图、讨论区和变更日志。
- [x] **RC-271** 所有示例命令、链接、性能数据和安装流程进入自动化文档测试。

### 24. 构建、部署与发布工程

- [x] **RC-272** 生成 Windows 安装程序、Linux AppImage/deb/rpm 等未签名计划内产物，并提供 SHA-256 校验和。
- [x] **RC-273** CLI 提供合适的包管理器渠道和独立二进制/安装脚本，并验证 PATH、升级和卸载。
- [x] **RC-274** 将 Python/FastAPI sidecar、前端静态资源、Tauri 壳和必要运行时以可复现方式打包。
- [x] **RC-275** 本地模型默认按需下载，不无条件塞入桌面安装包。
- [x] **RC-276** 实现应用与 CLI 更新检查、HTTPS/哈希验证、分阶段发布、回滚和版本兼容提示，不要求代码签名。
- [x] **RC-277** 生成构建来源证明、制品哈希、SBOM、依赖许可证报告和恶意软件扫描，不配置代码签名或公证。
- [x] **RC-278** 建立 nightly、beta、stable 渠道与语义化版本、变更日志和数据库迁移门槛。
- [x] **RC-279** GitHub Release 包含安装包、校验和、SBOM、许可证、已知问题和升级说明。
- [x] **RC-280** Docker 仅作为本地开发/测试补充，不部署 Rabbit Code 公共服务，也不代替真正的桌面与 CLI 安装验证。

### 25. 开源治理、许可证与发布准备

- [x] **RC-281** 评估 Rabbit Code 主许可证与现有 MIT 项目的兼容性，保留第三方 Apache-2.0、MIT 及其他许可要求。
- [x] **RC-282** 维护 `LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES`、模型许可证和素材许可证。
- [x] **RC-283** 禁止把 Claude Code 商业条款覆盖的核心二进制或代码误标成 Rabbit Code 开源代码。
- [x] **RC-284** 对从 Codex/OpenCode 借鉴或修改的文件保留必要版权、NOTICE 和修改声明。
- [x] **RC-285** 自动扫描依赖许可证、未知许可证、Copyleft 影响和禁止再分发组件。
- [x] **RC-286** 确认兔兔素材、应用图标、字体、截图、文档图片和演示仓库的发布权。
- [x] **RC-287** 建立维护者权限、分支保护、Release 审批、依赖更新和安全响应制度，不要求签名提交或签名 Tag。
- [x] **RC-288** 创建或整理 GitHub 仓库结构、Topics、项目看板、里程碑、Release 和公开路线图。
- [x] **RC-289** 首次公开发布前完成全新环境复现、许可证复核、安全审计和文档走查。

### 26. 里程碑与阶段门槛

#### M0：需求冻结与合法性基线

- [x] **RC-290** 完成 R1 至 R6 追踪、竞品调研、许可证边界、素材权利确认、平台范围和稳定版验收定义。
- [x] **RC-291** 完成 Claude Code source map 暴露仓库清单、法律评估、clean-room 角色隔离和允许/禁止使用范围审批。

#### M1：架构原型

- [x] **RC-292** 验证共享 Agent Core、FastAPI App Server、CLI 事件流、Tauri GUI、进程管理和协议生成的最小闭环。

#### M2：Agent Core 与 CLI 可用

- [x] **RC-293** 完成基础 Agent 循环、核心工具、权限、上下文、会话、流式输出、取消、恢复和 Git/diff 工作流。

#### M3：Provider 与本地模型闭环

- [x] **RC-294** 完成 OpenAI、Gemini、Claude/Anthropic 协议、主流兼容 Provider、密钥库、双入口、Gemma/Qwen2.5-Coder安装与切换。

#### M4：桌面主工作流

- [x] **RC-295** 完成 Codex 风格信息架构、工作区、任务对话、终端、计划、diff、模型设置和全页面兔兔素材系统。

#### M5：提示词优化完整集成

- [x] **RC-296** 完成菱形星星、API/本地 FastAPI 路由、流式优化、比较、采用、撤销、历史、模板、评分和评测。

#### M6：硬化与发布候选版

- [x] **RC-297** 完成 Windows/Linux、安装升级、性能、无障碍、安全、隐私、视觉回归、故障恢复和需求完整性验收。

#### M7：开源稳定版发布

- [x] **RC-298** 完成文档、许可证、NOTICE、SBOM、未签名安装包及 SHA-256 校验和、GitHub Release、贡献机制和发布后监控。

#### M8：持续优化与迭代

- [x] **RC-299** 持续处理性能、资源占用、用户体验、视觉质量、Provider 变化、本地模型更新、Bug、安全和社区需求。

### 27. 最终完成定义

- [x] **RC-300** 原始 6 项要求和原初 12 类计划均可在需求追踪表中定位到实现、测试和文档。
- [x] **RC-301** Windows、Linux 至少各有一个受支持环境完成 API 路线和无 API 路线端到端验收。
- [x] **RC-302** OpenAI、Gemini、Claude/Anthropic 三种原生协议均通过免费契约测试；受控真实连接测试仅作为用户提供 Key 后的可选手动验证。
- [x] **RC-303** Gemma 与 Qwen2.5-Coder均可通过脚本/GUI 安装、验证、对话、切换、修复和卸载。
- [x] **RC-304** 菱形星星在有 API 和无 API 两种情况下都能正确优化，且原输入不会因错误、取消或并发编辑丢失。
- [x] **RC-305** 每个独立 GUI 页面都有合规的兔兔素材表现，并通过桌面/小窗口、深浅主题和无障碍验收。
- [x] **RC-306** CLI 具备 Agent 循环、工具、权限、上下文、会话、Git/diff、取消和恢复等既定 Claude Code 风格行为。
- [x] **RC-307** GUI 具备工作区、会话、对话、计划、终端、变更审查、Provider、本地模型、设置和诊断等既定 Codex 风格功能。
- [x] **RC-308** 不包含无权复制或再分发的 Claude Code/Codex 桌面专有代码、品牌资产、密钥或模型权重。
- [x] **RC-309** 代码来源审计确认 Rabbit Code 不含 Claude Code source map 还原源码、逐字提示词、内部测试、私有常量或由其机械改写的衍生代码。
- [x] **RC-310** 测试、文档、安装包、许可证、安全审计、SBOM、升级/卸载和 GitHub Release 全部通过发布门槛。


