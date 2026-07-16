# RC-027 黑盒兼容差异报告

RC IDs: RC-027

## 运行范围

- Fixture：`docs/research/black-box-fixtures/rc027-claude-cli-help.yml`
- 官方命令：`claude --help`
- 官方版本：`2.1.202`
- 本轮 `claude --help` 输出 SHA-256：`e3fba9bfce4c126545eaa70c839fe2fbfe3abf02e1243aa846592d2a97dbb3bb`
- 原始 stdout：不保留；只保留 SHA-256 和自建抽象断言。
- 输入来源：官方公开 README 链接和本地官方可执行程序的无副作用帮助命令。

## 已观察断言

| 断言 | 结果 | 中立含义 |
| --- | --- | --- |
| `-p, --print` 存在 | PASS | 提供非交互输出模式 |
| `--output-format <format>` 存在 | PASS | 提供可选择的输出格式入口 |
| `--permission-mode <mode>` 存在 | PASS | 提供显式权限模式入口 |
| `--fork-session` 存在 | PASS | 恢复时提供会话分叉入口 |
| `--include-hook-events` 存在 | PASS | 可选择包含 Hook 生命周期事件 |

## 差异状态

本轮没有发送模型请求，也没有运行 Rabbit Code 对等实现，因此“官方行为 vs Rabbit Code 行为”的差异矩阵仍为 `pending-confirmation`。后续运行必须使用自建输入、明确授权、脱敏工作目录和可重复命令；不得复制官方测试夹具或保存完整官方输出。
