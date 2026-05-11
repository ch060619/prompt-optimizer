# Prompt Optimizer 提示词优化工具

Prompt Optimizer 是一个离线优先的提示词分析、优化、模板管理、版本对比与导出工具。项目包含 Python 后端核心库、命令行界面、本地 FastAPI 服务和 React Web 工作台，不依赖外部 AI API，适合本地使用和开源二次开发。

## 核心功能

- 提示词分析与评分：按清晰度、具体性、上下文、输出格式、约束、角色、示例、可执行性评分。
- 智能优化建议：基于规则和启发式算法生成具体改进建议。
- 模板库管理：内置技术、创意、商务、教育、通用场景模板。
- 版本控制与对比：SQLite 保存优化历史，支持版本 diff 和分数变化。
- 多格式导出：支持 Markdown、JSON、TXT、CSV。
- 双入口使用：CLI 覆盖全部能力，Web UI 提供本地工作台。

## 环境要求

- Python 3.12+
- Node.js 18+（仅开发或构建前端时需要）
- Git

## 一键启动

Windows 用户可以直接双击 `start.bat`。脚本会自动检查 Python、Node.js 18+ 和 npm，创建 `.venv`，安装后端依赖，安装/构建前端，并启动本地 Web 服务。

启动后访问：

```text
http://127.0.0.1:8000
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
docs/                     架构、计划、规范和贡献文档
.github/workflows/ci.yml  自动化测试与质量检查
```

## 本地数据

默认 SQLite 数据库保存到系统应用数据目录。可通过环境变量覆盖：

```bash
set PROMPT_OPTIMIZER_HOME=<your-data-dir>
set PROMPT_OPTIMIZER_DB=<your-data-dir>\prompt_optimizer.sqlite3
```

## 测试与质量检查

```bash
cd backend
pytest
ruff check .
mypy src

cd ../frontend
npm test
npm run lint
npm run build
```

## 贡献指南

欢迎提交 Issue 和 Pull Request。请阅读 [贡献指南](docs/contribution.md) 和 [代码规范](docs/coding-style.md)。提交前请运行测试和静态检查，确保新增模板、规则或功能有相应测试覆盖。

## 许可证

本项目基于 MIT License 开源。
