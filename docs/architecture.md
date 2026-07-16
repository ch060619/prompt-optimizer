# 项目架构

## 总览

Prompt Optimizer 使用前后端分离架构，但所有能力都面向本地运行。

- 后端：Python 包，提供核心服务、CLI 和 FastAPI。
- 前端：React + Vite + TypeScript，本地工作台。
- 数据：内置 YAML 规则和模板，用户历史存入 SQLite。

## 后端分层

- `core`：评分、建议、分析、优化和 diff，不依赖 API 或 CLI。
- `templates`：加载、筛选和渲染 YAML 模板。
- `storage`：SQLite 初始化、版本保存和查询。
- `export`：将版本导出为 Markdown、JSON、TXT、CSV。
- `api`：FastAPI 路由，复用核心服务。
- `cli`：Typer 命令行，复用核心服务。

## 数据流

1. 用户通过 CLI 或 Web 输入提示词。
2. `Analyzer` 调用 `ScoringEngine` 得到维度分数。
3. `SuggestionEngine` 根据低分维度生成建议。
4. `Optimizer` 组合原始提示词、模板和建议生成优化版本。
5. `VersionService` 将结果保存到 SQLite。
6. 用户可查询历史、对比版本或导出结果。

## 运行与安全边界

离线 Provider 始终可用；远程 Provider 通过环境变量配置，并要求已认证用户。生产环境必须设置 `PROMPT_OPTIMIZER_ENV=production` 和随机的 `PROMPT_OPTIMIZER_JWT_SECRET`（至少 32 字节）。

Docker 将 SQLite 数据保存到 `/data/prompt_optimizer.sqlite3`，宿主机应挂载命名卷并定期备份。跨实例部署需要在网关或共享 Redis 中提供限流与配额计量；单个应用进程的内存计数不作为分布式限流。
