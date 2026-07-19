# Rabbit Code 图标语言清单

<!-- RC ID: RC-131. Keep tool icons familiar, labeled, and semantically scoped. -->

## 规则

- 工具动作优先使用 `lucide-react` 中的熟悉图标，不绘制新的近似图标。
- 只有图标的按钮必须同时提供 `aria-label` 和 `title`；带有可见动作文字的按钮以该文字作为可访问名称，并保留图标的 `aria-hidden="true"`。
- `Sparkles` 只表示提示词优化：优化、流式优化和后台优化。品牌使用 `RabbitMark`，API 入口使用 `Cloud`。
- `Star` 不用于收藏或 Provider 默认项。收藏使用 `Heart`，默认项使用 `Pin`。
- 状态、文件、导航和外部链接图标只补充文字，不承担唯一语义。

## 动作清单

| 表面 | 动作 | 图标 | Tooltip / 可访问名称 | 语义边界 |
| --- | --- | --- | --- | --- |
| Workspace | 分析 | `Search` | `分析提示词` / visible `分析` | 读取并评估当前提示词 |
| Workspace | 优化、流式优化、后台优化 | `Sparkles` | 分别说明优化方式 / visible action text | 唯一的 Sparkles 语义 |
| Workspace | 导出 | `Download` | `导出 md/json/txt/csv` / format text | 输出已保存版本 |
| Navigation | 打开/关闭菜单 | `Menu` / `X` | `Open navigation` / `Close navigation` | 只负责导航显示 |
| Prompt assets | 导入、导出、收藏、翻页、关闭对比 | `Upload`, `Download`, `Heart`, `ChevronLeft`, `ChevronRight`, `X` | icon-only controls have `aria-label` + `title`; text actions keep visible labels | 不使用 Sparkles |
| Providers | 添加、发现、编辑、启用、删除、设为默认 | `Plus`, `RefreshCw`, `Pencil`, `Power`, `Trash2`, `Pin` | visible action text; icon-only add controls have `aria-label` + `title` | 默认项使用 Pin |
| Models | 安装、暂停、继续、验证、修复、运行、停止、卸载 | `Download`, `Pause`, `Play`, `ShieldCheck`, `RotateCcw`, `CheckCircle2`, `X`, `Trash2` | visible action text | 不使用 Sparkles |
| Task / Terminal | 会话、面板、发送命令、终端控制 | `Plus`, `PanelRight*`, `Send`, `SquareTerminal`, `Maximize2`, `CircleStop` | icon-only controls have `aria-label` + `title`; text actions keep visible labels | 不使用 Sparkles |
| Review / Diagnostics | 接受、拒绝、验证、回滚、复制、重启、更新 | `Check`, `X`, `ShieldCheck`, `RotateCcw`, `Clipboard`, `RefreshCw` | visible action text; decorative icons are hidden | 不使用 Sparkles |

## 审查记录

- 品牌和 API 入口的旧 `Sparkles` 误用已移除。
- 前端源码中 `Sparkles` 仅保留在 `frontend/src/App.tsx` 的三个提示词优化动作。
- 无关的 `Star` 已替换为 `Heart` 和 `Pin`。
- icon-only 的菜单、分页、收藏、关闭、添加、面板、终端发送和最近项目删除控件均有可访问名称及 Tooltip。

