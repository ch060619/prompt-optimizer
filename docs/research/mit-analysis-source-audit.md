# MIT 分析资料来源审计

RC IDs: RC-028

## 审计范围

本轮只检查两个 README 自称 MIT 的分析资料：固定 SHA 的 LICENSE 可见性与前 15 行、README 可见性、外链/代码围栏计数、逆向分析/Anthropic 上游自述。没有读取、保存或运行源码、代码片段、测试、Prompt、source-map 或还原工程。

## 结论

| 来源 | LICENSE | README 统计 | 内容自述 | 决策 |
| --- | --- | --- | --- | --- |
| `ComeOnOliver/claude-code-analysis` | HTTP 200；MIT 文本 | 2 个代码围栏，7 个外链 | 包含逆向分析和 Anthropic 上游相关自述 | `restricted` |
| `dadiaomengmeimei/claude-code-sourcemap-learning-notebook` | HTTP 200；MIT 文本 | 0 个代码围栏，9 个外链 | 包含逆向分析和 Anthropic 上游相关自述 | `restricted` |

MIT 文本只证明对应仓库声明了 MIT 许可，不自动解决其中第三方还原/分析内容的版权、合同、商业秘密或再分发问题。由于 source body 未审阅，本项目不批准任何代码、测试、文案、Prompt、常量、fixture 或机械衍生实现进入 Issue、代码、依赖、CI 或制品。

## 允许的抽象

仅允许实现人员独立重新推导高层问题域，例如“需要事件流”“需要权限边界”“需要会话恢复”；这些抽象必须再由 clean-room 规格、官方公开文档、许可清晰的 Codex/OpenCode/SDK 资料或自建黑盒观察独立证明。具体来源标记为 `restricted`，不能直接作为实现 Provenance。

## 审计限制

- 外链数量和代码围栏数量是 README 结构统计，不是引用比例、原创比例或授权证明。
- 未读取代码片段，因此没有对代码相似度或衍生关系作更强结论。
- 许可证和上游声明变化时必须重新审计；在 RC-022 书面法律意见前维持禁止复用。
