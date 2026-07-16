# ADR-0002：Rabbit Code 技术栈保留范围

- RC ID: RC-046
- Status: Accepted
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Context

V2 已使用 Python、FastAPI、React、Vite、TypeScript、SQLite、Typer 和 Docker。W0 的目标是先证明这些资产能支撑本地 App Server 与桌面 sidecar 边界，再决定是否重写。此决策不批准 Tauri 产品壳、最终协议、数据库迁移或 Rabbit Code 业务实现；这些仍由后续 RC 验证。

## Decision

保留现有八项技术及其当前职责。Rabbit Code 新核心继续使用 Python 3.12 与 FastAPI；React、Vite 和 TypeScript 继续承担 GUI；SQLite 继续承担本地结构化数据；Typer 保留为 CLI 命令层；Docker 仅保留为开发、测试和可选服务部署工具，不作为桌面安装或 sidecar 运行时。

最小 sidecar 原型通过独立 Python 进程启动现有 FastAPI App、随机选择 Loopback 端口、轮询 OpenAPI 就绪端点、使用隔离数据目录，并在宿主结束时清理进程。原型只验证进程和打包边界，不提前实现 RC-067 的生产级令牌、版本协商、崩溃拉起和优雅退出协议。

## 基准数据

原始机器可读结果保存于 `docs/benchmarks/rc-046-windows.json`。本次环境为 Windows 11 `10.0.26200`，基线 Commit `1f31f54`；Python 3.12.10、FastAPI 0.136.1、Uvicorn 0.46.0、React 18.3.1、Vite 5.4.21、TypeScript 5.9.3、Typer 0.25.1、SQLite 3.49.1。采集命令为：

```powershell
& .\.venv\Scripts\python.exe scripts\benchmark_tech_stack.py --output docs\benchmarks\rc-046-windows.json
```

| 指标 | 实测结果 | 用途 |
| --- | --- | --- |
| FastAPI sidecar 就绪 | 1,323 ms，随机端口 `63117` | 验证桌面宿主启动边界 |
| Sidecar 终止 | 2 ms；Windows 强制终止退出码 1；无残留进程 | 验证宿主能回收进程；优雅协议留给 RC-067 |
| SQLite 5,000 行单事务写入 | 写入 2 ms，计数读取 < 1 ms | 验证本地元数据量级 |
| Typer `--help` 冷调用 | 1,335 ms，退出码 0 | 验证 CLI 命令层启动成本 |
| Vite 生产资源 | 5 个文件，共 895,633 bytes | 验证现有 GUI 静态资源规模 |
| Docker 可用性 | CLI 29.5.3 可用；Engine 未运行（exit 1） | 区分开发容器与桌面运行时，不把未执行构建写成通过 |

## 技术评估

| 技术 | 成熟度与现有证据 | 打包 | 性能证据 | 维护成本 | 结论 |
| --- | --- | --- | --- | --- | --- |
| Python | V2 后端 36 项基线测试通过，生态覆盖 Agent、Provider 与本地工具 | 可由后续 sidecar 打包方案冻结解释器和依赖 | 进程启动数据见 sidecar 基准 | 团队只维护一套现有后端语言 | 保留 3.12；不升级或改写 |
| FastAPI | 现有 REST、SSE 和 OpenAPI 已运行 | 可随 Python sidecar 打包 | 就绪时间由真实子进程测量 | 路由与服务层已有测试资产 | 保留；生产加固留给 RC-058/207 |
| React | 现有 GUI 与 9 项组件测试通过 | 构建为静态资源供桌面壳加载 | 现有页面构建成功 | 组件和生态成熟，避免 UI 重写 | 保留 18；不在本项升级 |
| Vite | 当前生产构建成功 | 输出静态 `dist`，适合 Tauri WebView | 资源大小见基准 JSON | 配置小且已有锁文件 | 保留 5；桌面集成由 M1 验证 |
| TypeScript | 当前严格模式与生产类型检查通过 | 编译期依赖，不增加独立运行时 | 构建已纳入前端门禁 | 防止 GUI/API 契约漂移 | 保留；协议类型后续改为生成 |
| SQLite | V2 已保存用户、项目、版本和任务 | Python 标准库自带，无独立服务 | 5,000 行事务基准见 JSON | 单机运维成本低 | 保留；迁移/WAL 留给 RC-053/214 |
| Typer | 当前 CLI 命令面可运行 | 与 Python sidecar/CLI 一同分发 | `--help` 冷调用见 JSON | 声明式参数减少重复解析代码 | 保留；TUI 另行评估 prompt_toolkit |
| Docker | Dockerfile 与本地启动模式已存在 | 适合 CI/服务镜像，不适合桌面安装 | CLI/Engine 状态见 JSON | 多维护一条镜像链但可复用 CI | 限定保留，不作为桌面成功证据 |

## 备选方案

| 方案 | 优点 | 代价与本次结论 |
| --- | --- | --- |
| 全 TypeScript/Node Agent Core | GUI 与核心同语言，单运行时 | 重写 V2 Python 规则、Provider、CLI 和测试；在 M1 出现阻断证据前拒绝 |
| Electron + Node 主进程 | Node sidecar 集成直接，生态成熟 | 包体与双运行时成本更高；Tauri/Electron 实测比较留给 RC-057 |
| PostgreSQL 或独立数据库服务 | 高并发与远程协作更强 | 违背离线单机和零服务目标；首发拒绝 |
| Click/argparse 直接实现 CLI | 依赖更少、控制更底层 | 重写现有命令和帮助系统无收益；拒绝 |
| 仅用 Docker 分发 | 服务环境一致 | 不能覆盖桌面窗口、系统密钥库、更新和普通用户安装；拒绝 |

## 替换触发条件

- Python/FastAPI：M1 原型无法满足启动、流式取消、打包或跨平台进程治理，并有可复现实测替代方案。
- React/Vite/TypeScript：Tauri WebView 出现无法修复的兼容或性能阻断，且替代前端在同一用户旅程中实测更优。
- SQLite：单机 WAL、索引和迁移优化后仍无法满足会话并发或恢复门槛；不得因此引入远程必需服务。
- Typer：交互 TUI 原型证明输入、PTY 或事件渲染无法通过 CLI 验收；命令解析层与 TUI 渲染层应分别决策。
- Docker：若维护成本超过服务端/CI收益，可移除该补充渠道，但不得用容器结果替代桌面验收。

## Consequences

- W0 后续工作可以先回归和保护 V2，无需进行栈迁移。
- 新 Rabbit Code 模块进入 `backend/src/rabbit_code`，现有 `prompt_optimizer` 在兼容期内不整体改名。
- sidecar 原型暴露的是技术可行性，不是生产安全承诺；随机令牌、严格 Origin、版本协商和崩溃监督仍是后续门禁。
