# Codex 来源与桌面观察边界

RC IDs: RC-017

本记录把 Codex CLI/App Server 的开源事实、公开文档事实和桌面产品行为观察分开。来源登记位于 `docs/research/codex-source-register.yml`，由 `scripts/check_codex_source_register.py` 校验。

## 分类规则

| 分类 | 允许记录 | 禁止推导或复用 |
| --- | --- | --- |
| `open-source` | 固定 SHA 的 `openai/codex` 仓库、许可证和可审计的源代码来源 | 未经许可证/NOTICE 审核直接复制；将 CLI/App Server 来源当成桌面 GUI 来源 |
| `public-doc` | 固定文档 URL 的公开文字事实 | 把无法访问的页面、推测或二手描述写成已验证事实；复制文案或代码片段 |
| `behavior-only` | 公开可观察的产品行为、自制观察说明和抽象交互约束 | 未知桌面源码、品牌资产、图标、截图资产、像素级布局或专有实现 |

## 当前边界

- `openai/codex` 的固定提交 `78ba047bdae3db0342dee11d8d9ef5582fe8ce49` 作为 CLI/App Server 开源来源登记；其 Apache-2.0 义务仍需在具体复用前逐项审核。
- 该提交的 GitHub 仓库页和 README 可访问，可作为公开文档事实来源；来源登记只保留 URL、SHA 和用途边界，不把文档事实扩展成桌面源码结论。
- 官方 Codex manual URL 本轮重新检查返回 HTTP 200；登记为 `public-doc / verified / facts-only`。它仍然只是公开文档来源，不构成桌面 GUI 源码或专有实现的授权来源。
- 桌面 GUI 只允许以 `behavior-only` 记录公开行为或自制观察说明。本轮不保存官方桌面源码、专有资源或截图二进制；自制截图若以后产生，必须只保留脱敏的行为说明和来源元数据。

## Rabbit Code 代码审计边界

- 本轮没有把 `openai/codex` 仓库克隆进 Rabbit Code 工作树，也没有新增 Codex GUI 源码、品牌资产或截图二进制。
- Rabbit Code 现有 `openai` Provider 文本属于既有 Provider 标识，不构成 Codex 来源声明；任何未来借鉴必须在变更中填写来源、固定 SHA、许可证、NOTICE 和修改说明。
- GUI 的信息架构只能由 Rabbit Code 自己的组件、文案和素材实现；本记录不授权复制 Codex 桌面产品的专有实现。
