# Source Map 法律复核请求

RC IDs: RC-022

## 状态

`pending-human-legal-review`

本文件不是法律意见，也没有批准任何 source-map 仓库、还原源码、npm 包内容或衍生实现的访问、运行、复制或分发。当前只有元数据/README 证据，见 `docs/research/source-map-evidence.yml`。

## 提供给法律顾问的来源包

- 5 个仓库的固定 URL、默认分支、Commit SHA、README 状态、许可证字段、归档/禁用状态和风险登记：`docs/research/source-map-evidence.yml`。
- 研究用途和复用禁止边界：`docs/research/source-map-reuse-boundary.md`。
- Rabbit Code 计划用途：独立实现共享 Agent、CLI、GUI、Provider、工具、权限、会话和协议，不把 source-map 内容放入工作树、依赖、构建或发布链路。
- 当前访问策略：在书面结论前不访问、克隆、运行、复制或分发 source-map 还原源码正文。

## 需要书面回答的问题

1. source-map 暴露的 `sourcesContent`、还原源码、测试、Prompt、资源和协议常量的版权归属与可复制范围是什么？
2. 公开 npm 包、source map、GitHub 仓库 README、仓库许可证和贡献声明之间是否存在合同或再分发限制？
3. 还原内容是否可能涉及商业秘密、未公开实现、访问控制绕过或其他非版权权利？
4. Rabbit Code 的研究、行为分析、独立 clean-room 实现和兼容性测试分别有哪些允许/禁止边界？
5. 哪些材料可以进入研究人员环境、实现人员环境、CI 缓存、依赖树、Docker 镜像、安装包和公开发布物？
6. 对 MIT badge、公开可见性、作者自述“research/cleanroom”和 GitHub 当前状态，项目可以作出哪些、不能作出哪些授权推断？

## 需要的决策输出

书面意见应包含法域、出具人资质、日期、决策编号、事实范围、允许清单、禁止清单、保留条件和复核触发条件。没有该决策编号前，Rabbit Code 采用以下临时规则：

- 禁止访问、运行、复制、机械改写或分发 source-map 还原源码及其衍生内容。
- 只允许使用已固定的仓库元数据和 README 可见性记录，不把它们当成法律授权。
- 只允许依据独立设计、官方明确授权材料、许可证清晰的其他来源和自建黑盒测试继续实现。

## 待补字段

- 法域：待法律顾问填写
- 法律顾问/机构：待法律顾问填写
- 书面意见日期：待法律顾问填写
- 决策编号：待法律顾问填写
- 允许范围：待法律顾问填写
- 禁止范围：临时默认禁止，待法律顾问确认
