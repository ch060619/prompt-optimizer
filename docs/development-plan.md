# 开发计划

## Phase 1：项目初始化

- 创建 GitHub 仓库结构。
- 配置 Python 包、React 前端、测试和 CI。
- 编写 README、许可证和基础文档。

## Phase 2：核心算法

- 实现评分维度和规则加载。
- 实现提示词分析、建议生成和优化提示词构造。
- 建立技术、创意、商务、教育、通用模板库。

## Phase 3：存储与导出

- SQLite 保存版本历史。
- 实现版本列表、详情和 diff。
- 支持 Markdown、JSON、TXT、CSV 导出。

## Phase 4：CLI 与 API

- Typer CLI 覆盖分析、优化、模板、历史、对比、导出、服务启动。
- FastAPI 提供 Web 所需接口。
- 保持 CLI 和 API 复用核心服务。

## Phase 5：Web UI

- 实现模板浏览、提示词输入、分析优化、评分展示、历史和导出。
- 使用 Vite 开发代理，生产构建后由 FastAPI 静态托管。

## Phase 6：测试与发布准备

- 后端单元测试和 API 集成测试。
- 前端组件测试和生产构建检查。
- GitHub Actions 自动运行测试、lint 和类型检查。

