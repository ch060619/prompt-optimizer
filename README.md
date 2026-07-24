# Rabbit Code

Rabbit Code 是离线优先的提示词工程工作台：分析和优化提示词、管理模板、保存版本、查看 diff，并通过 CLI、Web 工作台或 Tauri 桌面壳使用。离线规则路径不需要云端 API；OpenAI 兼容、Gemini、Anthropic、Azure、Vertex 和 Bedrock 路径按需配置。

![Rabbit Code 桌面工作台](桌面端参考图.png)

![Rabbit Code 终端工作流](终端参考图.png)

## 当前支持范围

- 正式发布目标：Windows 11 x64、Ubuntu 24.04 x64。
- CPU-only 离线规则路径是最低可用基线。
- macOS 不在首发构建、测试和支持范围内。
- 本地模型和云端 Provider 都不随安装包携带；用户选择模型、许可证和数据发送边界。
- 当前包版本是 `3.0.0`；`prompt_optimizer` Python 模块路径和 `prompt-opt` 命令为兼容入口。

完整矩阵见 [支持矩阵](docs/support-matrix.md)。

## 功能

- 对清晰度、具体性、上下文、输出格式、约束、角色、示例和可执行性评分。
- 通过离线规则生成改进建议，也可路由到已配置的模型 Provider。
- 管理技术、创意、商务、教育和通用模板。
- 将优化结果保存到本地 SQLite，支持历史、版本 diff 和 Markdown/JSON/TXT/CSV 导出。
- 使用 SSE 流式优化或后台任务；取消、失败、Provider 降级和本地模型恢复状态会保留在结果元数据中。
- Web 工作台提供项目、任务、变更审查、终端、Provider/模型、提示词资产、设置和诊断入口。

## 安装与快速开始

### 依赖

- Python 3.12+
- Node.js 20.19+，仅在开发或构建前端时需要
- Git
- Docker Desktop，可选，仅用于本地开发/测试

克隆后安装后端：

```bash
git clone <repository-url>
cd prompt-optimizer
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux
# . .venv/bin/activate
python -m pip install -e "backend[dev]"
```

构建并启动 Web 工作台：

```bash
npm --prefix frontend install
npm --prefix frontend run build
rabbit serve --host 127.0.0.1 --port 8000
```

浏览器访问 <http://127.0.0.1:8000>。Windows 也可以运行 `start.bat local`；Docker 模式是 `start.bat docker`。

### CLI 最短路径

```bash
rabbit version
rabbit analyze "解释机器学习，并用三条要点回答。"
rabbit optimize "帮我写一封商务邮件" --provider offline
rabbit templates list --category tech
rabbit history list
rabbit doctor --json
```

<!-- docs-check:run -->
```python
python scripts/check_docs.py
```

使用 `rabbit prompt ...` 仍然有效。完整命令和 GUI 工作流见 [使用手册](docs/user-guide.md)。

## Provider 与本地模型

默认 `offline` 不发送提示词。云端 Provider 必须明确设置 API Key、模型和端点，密钥保存在操作系统凭据边界或进程环境中，不写入 README、日志、Issue 或截图。配置细节见 [Provider 接入指南](docs/providers/provider-integration.md)。

本地模型需要用户自行安装运行器、确认模型许可证并留出磁盘/RAM；安装包不暗带权重。见 [本地模型指南](docs/providers/local-models.md)。

## 数据、隐私和删除

默认数据目录是 Windows `%APPDATA%\rabbit-code`，Linux `$XDG_DATA_HOME/rabbit-code` 或 `~/.local/share/rabbit-code`。可用 `RABBIT_CODE_HOME` 和 `RABBIT_CODE_DB` 覆盖。旧的 `PROMPT_OPTIMIZER_*` 变量仅用于迁移兼容，并会提示弃用。

提示词历史、任务、缓存、日志和 Provider 元数据可能包含用户输入派生内容；不要把敏感数据发送到未审查的 Provider。遥测默认关闭，启用时只允许匿名技术元数据，不包含提示词、文件、凭据、请求体或响应。删除预览和保留策略见 [安全、隐私与删除](docs/security/privacy-and-data.md) 与应用设置页。

## 开发与质量检查

```bash
python scripts/check_docs.py
pytest backend/tests
ruff check backend
mypy backend/src
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```

性能数字只能引用 [基准 JSON](docs/performance/baseline.json) 和对应生成命令的实际输出；不能手填到 README 或发布说明。

架构、开发、测试、发布和协作入口：

- [架构说明](docs/architecture/rabbit-code.md)
- [开发与发布指南](docs/development-guide.md)
- [贡献指南](docs/contribution.md)
- [安全策略](SECURITY.md)
- [第三方许可](THIRD_PARTY_NOTICES.md)
- [RC 追踪索引](docs/traceability/rc-index.md)

## 许可证

源代码使用 [MIT License](LICENSE)。第三方依赖、模型和图片有各自的许可证与使用条件；发布或导入前请阅读 [第三方声明](THIRD_PARTY_NOTICES.md) 和本地模型许可证记录。
