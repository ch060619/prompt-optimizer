# RC-051 CLI 兼容迁移

- RC ID: RC-051
- 状态：已完成
- 新命令：`rabbit prompt`
- 旧命令：`prompt-opt`
- 兼容截止：Rabbit Code `3.0.0`

## 命令盘点与映射

| 旧命令 | 新命令 | 参数/输出/退出码 |
| --- | --- | --- |
| `prompt-opt analyze <prompt>` | `rabbit prompt analyze <prompt>` | 参数和评分/建议输出相同；成功 0，参数错误 2 |
| `prompt-opt optimize <prompt> [-t ID] [-p PROVIDER]` | `rabbit prompt optimize <prompt> [--template-id ID] [--provider PROVIDER]` | Provider、版本保存和降级输出相同 |
| `prompt-opt templates list [--category CATEGORY]` | `rabbit prompt templates list [--category CATEGORY]` | 表格输出和过滤参数相同 |
| `prompt-opt templates show <template-id>` | `rabbit prompt templates show <template-id>` | 模板详情和错误行为相同 |
| `prompt-opt history list` | `rabbit prompt history list` | 历史排序和字段相同 |
| `prompt-opt history diff <old-id> <new-id>` | `rabbit prompt history diff <old-id> <new-id>` | diff 和分数变化相同 |
| `prompt-opt export <version-id> [-f FORMAT] [-o PATH]` | `rabbit prompt export <version-id> [--format FORMAT] [--output PATH]` | 导出格式、文件写入和错误行为相同 |
| `prompt-opt evaluate -d DATASET -o OUTPUT [-p PROVIDER]` | `rabbit prompt evaluate --dataset DATASET --output OUTPUT [--provider PROVIDER]` | 评测报告和退出码相同 |
| `prompt-opt serve [--host HOST] [--port PORT]` | `rabbit prompt serve [--host HOST] [--port PORT]` | 运行同一个 FastAPI App Server |

`rabbit analyze`、`rabbit optimize` 等平面命令也保留，方便从旧命令逐步迁移；新文档统一使用 `rabbit prompt`，所有入口挂载同一函数和服务对象，不维护第二套业务实现。

## 兼容行为

- `prompt-opt` 仍是 `rabbit-code` 发行包提供的入口别名，启动时向 stderr 输出弃用提示、`rabbit` 迁移目标和 `3.0.0` 截止版本。
- 旧命令参数解析和退出码不通过静默重写改变；未知命令/参数仍由 Typer 返回 2，业务错误保持既有命令行为。
- 配置和数据目录遵循 RC-054：优先 `RABBIT_CODE_*`，回退 `PROMPT_OPTIMIZER_*`；旧目录自动发现但不双写。
- CLI 仍复用 `prompt_optimizer` 模块路径和现有 SQLite 历史；RC-053 负责数据库版本、备份和恢复。

## 验收

`backend/tests/test_cli_compatibility.py` 比较 `rabbit prompt analyze/templates` 与旧平面命令的逐字输出和退出码，并直接验证旧 `prompt-opt` 入口提示。命令盘点、参数映射和迁移截止版本记录在本文件；真实安装包渠道、升级卸载和兼容期结束后的入口删除留给 RC-055/发布门禁。
