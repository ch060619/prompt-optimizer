# Clean-room 重写记录

RC IDs: RC-033

## 状态

`pending-implementation-pr`

本记录定义不明来源能力的独立重写流程；本轮没有从任何受限仓库读取代码，也没有声称已有核心模块完成重写。

## 输入规格

- 只接收 `docs/research/clean-room-specs/` 中的行为规格：输入、输出、状态、约束和不确定性。
- 规格模板：`docs/templates/clean-room-behavior-spec.md`。
- 不接收源文件名、原文、代码片段、内部 Prompt、测试夹具、私有常量或专有资产。
- 设计依据记录在 `docs/adr/0005-independent-agent-event-design.md`，并只使用 clean-room 规格、官方文档、合法 SDK 和许可清晰来源的抽象事实。

## 独立候选方案

- 方案 A：不可变类型化事件和集中状态转换，已在 ADR-0005 选择。
- 方案 B：动态字典直通，作为独立对照保留但不进入生产实现。
- 两种方案由 Rabbit Code 独立编写，不复用外部字段名、协议常量或测试。

## 实现与测试门禁

- 实现者：待 RC-025 角色签署和正式实现 PR 分配。
- 实现 PR：必须填写 `.github/pull_request_template.md` Provenance 段，声明来源、许可证、原创性、扫描和人工相似性审查。
- 测试：先使用自建输入和断言；不得使用泄露源码测试、source-map 还原工程或外部 golden fixture。
- 提交历史：实现 PR 合并前必须保存实现者记录、原创提交历史、测试命令和审查日期。
- 相似性审计：人工检查当前 diff；字符串扫描为阻断信号，但零命中不等于法律清除。

## 当前结果

- 受限材料访问：`false`。
- 生产实现：`not-started`。
- 自建中立规格与双方案设计：已具备。
- 正式实现 PR、实现者记录和原创提交历史：待确认。
