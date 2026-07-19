# Rabbit Code Design Token 规范

- RC ID: RC-130
- 状态：token 源文件、CSS 变量、TypeScript 类型、light/dark 快照和前端消费门禁已完成

## 单一来源与生成物

| 文件 | 角色 |
| --- | --- |
| `packages/ui/tokens.json` | 唯一编辑源，包含主题色、语义状态色、字体、间距、圆角、阴影、图标尺寸、动效和 Rabbit 工作页预算 |
| `packages/ui/tokens.css` | 生成的 `:root` 与 `:root[data-theme="dark"]` CSS 变量 |
| `packages/ui/tokens.ts` | 生成的只读 TypeScript token 值、分类类型和 `token()` CSS var helper |
| `packages/ui/token-snapshot.md` | 生成的 light/dark 对照和静态/尺寸 token 快照 |
| `scripts/generate_design_tokens.py` | `--write` 生成、`--check` 漂移检查；已接入 `workspace.py check` |

`frontend/src/styles.css` 通过 `@import "../../packages/ui/tokens.css"` 消费变量。页面 CSS 不再直接写主界面颜色；主题切换只改根节点变量，不复制页面规则。

## Token 分类

| 分类 | 示例 | 使用边界 |
| --- | --- | --- |
| 主题 | `--paper`、`--ink`、`--line`、`--gold` | light/dark 主题基础表面、文本、边框和强调色 |
| 状态 | `--success-text`、`--warning-text`、`--danger-surface` | 成功、运行中、警告、错误和降级状态；状态语义不能借给装饰 |
| 字体 | `--font-sans`、`--serif`、`--mono` | 页面正文、展示标题、代码/日志和控制标签 |
| 空间/形状 | `--space-*`、`--gutter`、`--radius-control` | 页面间距和稳定控件几何；按钮圆角保持现有 2px 约束 |
| 影和动效 | `--shadow-*`、`--motion-duration`、`--motion-ease` | Dialog、产品 mockup 和空间转场；不用于持续装饰动画 |
| 图标/品牌 | `--icon-*`、`--rabbit-*` | Lucide 尺寸和 Rabbit 工作页装饰预算；工具动作仍使用 Lucide |

## 门禁

- 修改 token 只能编辑 `tokens.json`，然后运行 `python scripts/generate_design_tokens.py --write`。
- `python scripts/generate_design_tokens.py --check` 检查 CSS、TS 和 Markdown 快照漂移；根 `workspace.py check` 强制执行。
- `frontend/src/styles.css` 的原始颜色扫描必须为空；原始颜色只允许存在于 token 源和生成 CSS 中。
- 主题快照必须同时包含 light/dark；状态色、代码字体、图标尺寸、间距、阴影和动效 token 必须可定位。
- 页面级内联值只允许来自数据或运行时尺寸（例如 diff 宽度、进度百分比），不能绕过 token 写主题值。
