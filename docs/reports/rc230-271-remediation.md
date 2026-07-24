# RC-230 至 RC-271 遗留问题修复报告

更新时间：2026-07-19（Asia/Shanghai）  
审计对象：Rabbit Code 3.0.0，当前工作树（未提交）

## 结论

RC-230 至 RC-271 的离线、Mock、静态门禁和前端工作流在本机可复现通过；本轮接管验收补上了此前没有闭环的容器构建、前端依赖安全、导航状态和 Rust 工具链验证。修复后基线为：后端 `718 passed, 9 skipped`，前端 `33 files / 150 tests passed`，前端 lint/build、生产依赖审计、OpenAPI/data-model drift、文档门禁、Tauri `cargo test --locked` 和 Docker 镜像构建均通过。

“完整运行”不能被夸大为真实云 Provider、模型权重、物理 GPU、Linux 实机或原生安装包已经通过。相关 RC 证据仍明确标为受控手动矩阵；本报告把这些限制保留为发布门槛，而不是把 Mock 结果伪装成平台结果。

## 问题清单、根因与方案

| 优先级 | 问题 | 根因 | 修复 | 验证 |
| --- | --- | --- | --- | --- |
| P0 | Docker 前端阶段构建失败，找不到 `packages/ui/tokens.css` | `Dockerfile` 只把 `frontend/` 复制到构建阶段，而 `frontend/src/styles.css` 通过相对路径引用共享令牌 | 前端阶段改为 `/app` 工作目录，复制 `frontend/` 与 `packages/ui/`，用 `npm ci --prefix frontend` 和 `npm run build --prefix frontend` | `docker build -t rabbit-code:rc271-audit .` 通过，镜像运行时用户为 `rabbit` |
| P1 | Agents 导航偶发跳到历史提示词网站/路由 | 没有统一路由状态；裸 `<a>` 加两处 `replaceState` 与旧公开路径混用，`/prompt-management` 等路径没有 Agents 分支 | 新增 `frontend/src/navigation.tsx`：统一 location 状态、`popstate`、SPA 内部链接、同源校验、旧路径一次性别名收敛；所有 Agents 内链改用 `AppLink` | `Navigation.test.tsx`、原有全量测试；别名收敛到 `/workspace/assets`，无循环跳转 |
| P1 | 前端依赖审计不可用且开发依赖存在漏洞 | 本机 npm 全局 registry 指向不提供 advisory API 的镜像；Vite 5/Vitest 2 锁定旧 `esbuild` | 用官方 registry 执行 `npm audit fix`，升级 Vite 8.1.5、Vitest 4.1.10、`@vitejs/plugin-react` 6.0.3；增加固定 `audit:production` 脚本 | 生产审计 `found 0 vulnerabilities`，完整审计 `found 0 vulnerabilities` |
| P1 | Tauri “未验证”误判为 Rust 缺失 | `cargo/rustc` 已安装在用户 Rustup 目录，但 Codex 进程 PATH 未继承 `%USERPROFILE%\\.cargo\\bin` | 验证 Rustup stable 1.97.1，使用显式工具链路径完成构建测试；文档继续要求新环境将该目录加入 PATH | `cargo test --locked` 通过；未声称生成原生安装包（`bundle.active=false`） |
| P2 | 前端单一主包触发 500 KB 告警 | App、图标、GSAP/Lenis 与 React 供应商全部进入同一 Rollup chunk | Vite 8 `manualChunks` 函数分离 `react`、`icons`、`motion`，保留可复现构建 | 最大 JS chunk 从约 500 KB 降至约 202 KB；总 dist 仍低于 2 MB 门槛 |
| P2 | 前端 dist 包含 3 个未使用的图片副本 | Vite 会原样复制 `public/`，但 desktop WebP 与 terminal PNG/WebP 没有任何运行时、测试或文档引用 | 删除这 3 个 public 副本，保留实际使用的 desktop PNG、品牌 PNG 与根级来源素材 | dist 从 1,097,522 降至 829,010 bytes，并低于旧趋势允许值 1,008,598.8 bytes |
| P2 | 性能趋势把同一 Git HEAD 下不同未提交实现当成同一制品 | 报告环境只记录 Commit，无法区分本轮大规模脏工作树；旧基线早于 RC-230~271 实现 | 先保留失败 comparison 诊断，再完成资源优化；在不放宽绝对预算的前提下生成 RC-271 25 次基线，并在性能文档记录旧值、增量和迁移理由 | 9 项绝对预算与新基线趋势比较全部 PASS；CLI p95 917.953 ms、GUI 冷启动 p95 1,794.780 ms、RSS 64,110,592 bytes |
| P2 | jsdom 测试输出 `scrollTo`/下载导航噪声 | jsdom 未实现浏览器滚动与 Blob 下载的默认行为；产品代码在真实浏览器中需要这些行为 | 测试 setup 只 mock `window.scrollTo` 和 `HTMLAnchorElement.click`，不改变生产代码 | 全量 150 tests 通过，测试输出不再包含动画/下载噪声 |
| P2 | RC-238 门禁没有检查共享令牌输入 | 只检查 `npm ci`/build 标记，未检查 Docker 构建上下文 | `check_rc238_installation.py` 与专项测试增加 `COPY packages/ui/` 断言 | RC-238 脚本与 2 个测试通过 |

## RC-230 至 RC-271 证据分级

- **本机自动化通过**：Agent Core、Provider Mock、FastAPI、CLI、GUI Mock 旅程、离线模型状态机、权限/安全矩阵、质量 gate、文档和治理门禁。
- **本机真实运行通过**：Vite 浏览器工作流、Docker 镜像构建、Windows Rust/Tauri 单元测试、Python 依赖安装与导入。
- **受控外部矩阵**：真实云 Provider、模型下载/权重、Ollama/llama.cpp 进程、Linux shell/Tauri、物理 GPU/低内存、NVDA/VoiceOver、干净 VM 安装升级、真实高频用户和人工盲评。

这些分级与 `docs/evidence/RC-230/` 至 `docs/evidence/RC-271/` 的 Limits 段一致。任何发布候选版本都必须在对应平台矩阵中完成第三类验证后再把限制改为 PASS。

## 验证矩阵

| 检查 | 结果 |
| --- | --- |
| `python -m pytest backend/tests -q` | 718 passed, 9 skipped |
| `npm.cmd test -- --run` | 33 test files, 150 passed |
| `npm.cmd run lint` | PASS |
| `npm.cmd run build` | PASS，Vite 8 分包 |
| `npm.cmd run audit:production` | PASS，0 vulnerabilities |
| `python scripts/performance_baseline.py --iterations 25 --check` | PASS，9 项绝对预算通过 |
| `python benchmarks/performance_gate.py ... --check` | PASS，RC-271 基线无趋势回归 |
| `python scripts/check_docs.py --run` | PASS |
| `python scripts/workspace.py check` | PASS |
| `cargo test --locked` | PASS，Windows Tauri shell 无业务测试 |
| `docker build --progress=plain -t rabbit-code:rc271-audit .` | PASS |
| UTF-8 `pip-audit` | No known vulnerabilities；两个本地未发布包按政策跳过 |

## 未混入的清理

本轮只删除可证明的生成缓存，保留被证据、设计或脚本引用的截图/素材、模型 manifest、测试 fixture 和文档。清单见 [project-cleanup.md](project-cleanup.md)。
