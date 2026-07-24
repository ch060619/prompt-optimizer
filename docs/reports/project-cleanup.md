# 项目清理与结构说明

## 保留的源码边界

```
backend/                 Python Agent、FastAPI、Provider、存储与测试
frontend/                React Agents 页面、导航、API client 与测试
apps/desktop/src-tauri/  仅 Tauri/OS 壳，不放业务逻辑
packages/protocol/       跨表面 Python 协议
packages/ui/             共享生成设计令牌
scripts/                 生成、门禁、安装和性能脚本
docs/                    ADR、架构、用户/开发/安全/RC 证据
benchmarks/              可复现性能比较器
data/                    受控模型与应用数据 manifest，不含权重
examples/                本地、无网络扩展示例
```

## 本轮删除/忽略的生成物

| 路径 | 处理 | 原因 |
| --- | --- | --- |
| `.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.coverage` | 本机验证后删除 | 测试/类型/静态检查缓存，不是源码或证据 |
| `scripts/**/__pycache__/`、`packages/**/__pycache__/` | 本机验证后删除 | Python 编译缓存 |
| `apps/desktop/src-tauri/target/` | 本机 Cargo 验证后删除 | Rust 构建产物，可由 Cargo 复现 |
| `.runtime/`、`.playwright-cli/` | 本轮会话结束后删除并加入 `.gitignore` | 临时服务、浏览器会话和 pytest 临时目录；不应进入仓库 |
| `output/imagegen/`、`output/reference/` | 删除并加入 `.gitignore` | 生成中间物未被产品、文档或测试引用；发布素材位于 `frontend/public/` 和根级授权素材 |
| `frontend/public/rabbit-desktop.webp`、`frontend/public/rabbit-terminal.png`、`frontend/public/rabbit-terminal.webp` | 删除 | 构建会原样复制这些资源，但当前组件、测试和文档均未引用；保留实际使用的 `rabbit-desktop.png` 与 `rabbit-artwork.png` |

`output/playwright/` 不删除：RC-128/129/133/234/251/256/257/258/260/261 证据显式引用它。`frontend/node_modules/` 不删除：是可复现 `npm ci` 的本地安装，而不是提交内容。模型权重、fixture、manifest、授权素材和文档截图不删除。

## 依赖清理

- 生产依赖没有发现高危漏洞；npm 完整审计在升级 Vite 8/Vitest 4 后为 0 vulnerabilities。
- 未删除 `gsap`、`lenis`、`lucide-react` 或 `axe-core`：它们分别被动效、图标和无障碍测试实际引用。
- `rabbit-code` 与 `rabbit-code-protocol` 是本地分发包，pip-audit 按项目政策跳过；这不是漏洞豁免，发布前仍需生成 SBOM 并审计传递依赖。
