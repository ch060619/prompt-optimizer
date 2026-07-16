# Claude Code Source Map Clean-room 决策记录

RC IDs: RC-030

## 决策状态

`pending-human-approval`

M0 状态：`blocked`

本记录汇总已完成的事实登记、风险、临时允许/禁止范围、角色隔离、审计和监控，但不是法律意见，也没有在缺少合资格顾问/技术负责人/合规负责人签字时批准任何 source-map 内容。

## 事实依据

- 5 个 source-map 仓库的 URL、固定 SHA、README 状态、license 字段、归档/禁用状态和风险：`docs/research/source-map-evidence.yml`。
- Source-map 内容在 RC-021/022/023/025/028 的当前流程中未进入工作树、依赖、CI、Docker、安装包或发布物。
- GitHub API license 字段、README 自述、MIT badge 和公开可见性不构成版权、合同、商业秘密、DMCA 或再分发结论。
- Claude Code 官方公开材料、SDK、Codex/OpenCode 许可来源和自建黑盒断言分别记录在 RC-019、RC-020、RC-015、RC-016/018 和 RC-027。

## 风险

| 风险 | 当前判断 | 临时处理 |
| --- | --- | --- |
| 版权/衍生作品 | source-map 可能暴露第三方源码正文、测试、Prompt、资源和常量 | 禁止访问、运行、复制、机械改写和分发 |
| 合同/服务条款 | 公开 npm 包、CLI、source map 和 GitHub 仓库可能受不同条款约束 | 等待书面法律复核；不把公开可见性当授权 |
| 商业秘密/未公开实现 | 还原内容可能包含未公开实现或私有协议 | 不进入研究者/实现者/CI/制品环境 |
| 供应链/再分发 | 无许可证或来源不清内容可能被误带入依赖、镜像或发布包 | RC-023 denylist、Provenance 和发布前扫描阻断 |

## 临时允许范围

- 记录固定仓库元数据、README HTTP 状态和中立摘要，不保存正文。
- 使用官方公开文档的已验证事实、合法 SDK/许可清晰来源和自建黑盒观察，独立编写 Rabbit Code 设计。
- 记录行为问题域和输入/输出/状态/约束，不复制源文件名、代码结构、原文、Prompt、测试或资源。

## 明确禁止范围

- 访问、克隆、运行、导入、复制、分发 source-map 还原源码及其衍生工程。
- 把 MIT badge、README、作者自述、公开 URL 或 GitHub license 字段当成第三方还原内容授权。
- 将 source-map 内容放入实现 Issue、clean-room 规格、工作树、依赖、缓存、Docker、SBOM、安装包、测试夹具或发布制品。
- 在新的法律意见和 ADR 批准前扩大任何复用范围。

## 角色与审计

- 研究者、实现者和审查者角色登记与信息边界：`docs/legal/clean-room-role-register.yml`、`docs/legal/clean-room-information-boundary.md`。
- 相关 PR 必须填写 Provenance；RC-024 专有内容策略、RC-023 denylist 和 RC-029 授权变化监控继续有效。
- 发现越界材料时停止合并，隔离材料，记录事件，重新进入法律复核流程。

## 待签署与批准字段

- 技术负责人：待人工填写
- 合规负责人：待人工填写
- 合资格法律顾问/法域：待人工填写
- 决策编号：待人工填写
- 批准日期：待人工填写
- 允许范围：临时默认禁止，待书面意见
- 禁止范围：以上明确禁止清单，待书面意见确认

## M0 触发条件

只有在事实来源、法律意见、角色权限、允许/禁止清单、监控计划和工作树/依赖扫描均有签署证据后，才能把 M0 从 `blocked` 改为 `approved`。状态变化必须通过新的 ADR 记录，不得直接编辑为批准。
