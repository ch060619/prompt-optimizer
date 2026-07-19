# RC-153 执行证据

- RC ID: RC-153
- 状态：实现完成，运行验证受环境阻塞
- 负责人：Codex
- 基线 Commit：未提交工作树（HEAD `5610c00`）
- 前置 RC：RC-152

## 已交付

- 新增可打包的版本化资源 `rc153.v1.txt` 和资源加载器；Provider 代码不再硬编码专用 System Prompt。
- `ModelRequest` 明确携带 `system_prompt` 与 `system_prompt_version`；OpenAI-compatible payload 将资源放入 `system` role，将受保护用户文本、模板和语言要求保留在 `user` role。
- 优化结果 metadata 增加 `system_prompt_version`，并同步 OpenAPI 与 TypeScript 生成契约。
- 新增 RC-153 测试，覆盖资源版本、注入文本 role 分离、结构标记和 metadata 追溯。

## 已执行验证

| 命令或检查 | 结果 |
| --- | --- |
| Bundled Python `compileall` | PASS：后端源代码和 RC-153 测试无语法错误 |
| `python -m prompt_optimizer.prompts.system` | PASS：版本化资源可导入并读取 |
| `python -m pytest backend/tests/test_rc153_system_prompt.py -q` | BLOCKED：当前可用 Python 未安装 `pytest` |
| 安装仓库依赖后运行测试 | BLOCKED：pip 访问包索引被系统网络策略拒绝（WinError 10013） |

## 未解决项与后续

- RC-153 专项测试、相邻回归、Ruff、Mypy、根级 verify 仍需在具备仓库 Python 依赖的环境重跑；本证据不将其伪造为 PASS。
- 按用户指令自动进入 RC-154；RC-153 保持待复核状态，不阻塞当前可独立实施的目标参数契约。
