# Prompt Optimizer 提示词优化工具

Prompt Optimizer 是一个离线优先的提示词分析、优化、模板管理、版本对比与导出工具。项目包含 Python 后端核心库、命令行界面、本地 FastAPI 服务和 React Web 工作台，并可选接入远程模型 Provider。

## V3.0 版本状态

V3.0 聚焦 AI 工程化能力补强：模型 Provider 抽象、SSE 流式优化、多用户归属、后台任务、评测集、结构化日志、Docker 构建和 CI 检查。

本次发布保留旧版本在 `main` 分支，V2.0 使用 `release/v2.0` 分支保存发布线，并用 `v2.0` Git tag 标记可复现的版本快照。GitHub Release 基于 `v2.0` tag 创建，而不是只依赖分支。

已在本机完成的真实验证：

- 后端测试覆盖率：`81%`，来自 `pytest --cov=prompt_optimizer --cov-report=term-missing`。
- 评测集：`55` 条样本，报告由 CLI 生成在 [docs/evaluation-report.md](docs/evaluation-report.md)。
- Docker：已通过 `docker build -t prompt-optimizer:local .` 构建，并完成容器内 `/docs`、`/openapi.json`、`/api/templates`、`/api/analyze`、`/api/auth/register`、`/api/auth/login`、`/api/optimize` 冒烟验证。

## 核心功能

- 提示词分析与评分：按清晰度、具体性、上下文、输出格式、约束、角色、示例、可执行性评分。
- 智能优化建议：基于规则和启发式算法生成具体改进建议。
- 模板库管理：内置技术、创意、商务、教育、通用场景模板。
- 版本控制与对比：SQLite 保存优化历史，支持版本 diff 和分数变化。
- 模型接入抽象：支持离线规则 Provider，并预留 OpenAI、通义、智谱 HTTP Provider。
- 流式与异步：提供 SSE 流式优化接口，以及后台优化、导出、评测任务。
- 多用户归属：JWT 登录后按用户隔离历史版本、项目空间和任务。
- 多格式导出：支持 Markdown、JSON、TXT、CSV。
- 双入口使用：CLI 覆盖全部能力，Web UI 提供本地工作台。

## 环境要求

- Python 3.12+
- Node.js 18+（仅开发或构建前端时需要）
- Git
- Docker Desktop（可选，仅 Docker 启动或镜像构建时需要）

## 一键启动

Windows 用户可以直接双击 `start.bat`。脚本默认使用本地 Python/Node.js 模式：检查 Python、Node.js 18+ 和 npm，创建 `.venv`，安装后端依赖，安装/构建前端，并启动本地 Web 服务。

启动后访问：

```text
http://127.0.0.1:8000
```

也可以显式选择启动模式：

```bat
start.bat local
start.bat docker
```

`start.bat docker` 会检查 Docker Desktop 是否运行，构建 `prompt-optimizer:v2.0` 和 `prompt-optimizer:local` 镜像，并以前台容器方式启动服务。Docker 启动前必须设置随机的、至少 32 字节的 JWT 密钥；数据库保存在 Docker 命名卷 `prompt-optimizer-data` 中。

```bat
set PROMPT_OPTIMIZER_JWT_SECRET=<use-a-random-secret-of-at-least-32-bytes>
start.bat docker
```

## 安装步骤

```bash
git clone <your-repo-url>
cd prompt-optimizer

python -m venv .venv
.venv\Scripts\activate
pip install -e backend[dev]
```

前端开发依赖：

```bash
cd frontend
npm install
```

## 命令行使用

```bash
prompt-opt analyze "你是一名老师，请解释机器学习，输出格式为列表。"
prompt-opt optimize "帮我写一封商务邮件"
prompt-opt optimize "帮我写一封商务邮件" --provider offline
prompt-opt evaluate --dataset data/evaluation/prompts.yml --output docs/evaluation-report.md
prompt-opt templates list --category tech
prompt-opt templates show tech-code-generation
prompt-opt history list
prompt-opt history diff 1 2
prompt-opt export 1 --format md --output result.md
```

启动本地 Web 服务：

```bash
prompt-opt serve --host 127.0.0.1 --port 8000
```

开发模式前端：

```bash
cd frontend
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`，API 请求会代理到 `http://127.0.0.1:8000`。

## 项目结构

```text
backend/                  Python 核心库、CLI、API、测试
frontend/                 React + Vite Web 工作台
data/rules/               内置评分规则
data/templates/           内置提示词模板
data/evaluation/          提示词评测集
docs/                     架构、计划、规范和贡献文档
.github/workflows/ci.yml  自动化测试与质量检查
Dockerfile                多阶段 Docker 构建
.dockerignore             Docker 构建上下文排除规则
```

## 评测集

项目内置 50+ 条多场景提示词评测样本，覆盖技术、商务、教育、创意、客服、数据分析和长文本场景。运行以下命令可生成本地评测报告：

```bash
prompt-opt evaluate --dataset data/evaluation/prompts.yml --output docs/evaluation-report.md
```

报告记录优化前后得分、人工标签、规则误判备注、Provider、降级状态和本地耗时。仓库中的 [评测报告](docs/evaluation-report.md) 由上述命令生成，简历中的 QPS、耗时、覆盖率等数字应只引用实际运行结果。

## 工程化亮点

- 规则引擎链路：评分维度、建议生成、优化结果和版本保存可独立测试。
- 模型降级链路：远程 Provider 超时、限流或失败时自动回退离线规则，并返回 metadata。
- 验证方法链路：内置评测集、报告生成、测试覆盖率命令和 [压测方法](docs/performance.md)，所有性能数字以实际运行为准。

## 本地数据

默认 SQLite 数据库保存到系统应用数据目录。可通过环境变量覆盖：

```bash
set PROMPT_OPTIMIZER_HOME=<your-data-dir>
set PROMPT_OPTIMIZER_DB=<your-data-dir>\prompt_optimizer.sqlite3
```

## 测试与质量检查

```bash
cd backend
pytest --cov=prompt_optimizer --cov-report=term-missing
ruff check .
mypy src

cd ../frontend
npm test
npm run lint
npm run build
```

Docker 验证：

```bash
docker build -t prompt-optimizer:local .
docker run --name prompt-optimizer-smoke -p 127.0.0.1:8000:8000 -v prompt-optimizer-data:/data -e PROMPT_OPTIMIZER_JWT_SECRET prompt-optimizer:local
```

数据库备份与恢复：

```powershell
$env:PROMPT_OPTIMIZER_DB = "C:\data\prompt_optimizer.sqlite3"
pwsh -File scripts/backup_db.ps1 -Output C:\backup\prompt-optimizer.sqlite3
pwsh -File scripts/restore_db.ps1 -Backup C:\backup\prompt-optimizer.sqlite3

# Online SQLite backup, safe while WAL is active:
python scripts/backup_db.py --database C:\data\prompt_optimizer.sqlite3 --output C:\backup\prompt-optimizer.sqlite3
python scripts/restore_db.py --backup C:\backup\prompt-optimizer.sqlite3 --database C:\data\prompt_optimizer.sqlite3
```

## 贡献指南

欢迎提交 Issue 和 Pull Request。请阅读 [贡献指南](docs/contribution.md) 和 [代码规范](docs/coding-style.md)。提交前请运行测试和静态检查，确保新增模板、规则或功能有相应测试覆盖。

## 许可证

本项目基于 MIT License 开源。
