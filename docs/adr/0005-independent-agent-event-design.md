# ADR-0005：合法材料驱动的独立 Agent 事件设计

RC IDs: RC-026

## 状态

Submitted; formal clean-room role sign-off remains pending under RC-025.

## 目标

为中立规格中的“有序状态事件”选择一个 Rabbit Code 自己实现的边界，不复制任何外部实现、字段名、协议常量或测试夹具。

## 方案 A：不可变类型化事件

- Agent Core 产生带任务 ID、事件类型和受限 payload 的不可变内部事件。
- 状态机负责合法转换；CLI、GUI 和 App Server 各自把中立事件映射到自己的显示/传输格式。
- 未知事件进入显式兼容分支，不覆盖已经提交的状态。

## 方案 B：动态字典直通

- Agent Core 产生任意字典，CLI、GUI 和 App Server 自行判断键名和状态。
- 新事件可以直接透传，但每个消费者都需要重复处理缺失字段、未知类型和错误恢复。
- 该方案降低初始类型成本，但使事件契约、权限边界和回放一致性分散。

## 决策

采用方案 A。它与当前 Python/FastAPI 共享核心方向一致，能把状态转换、取消和恢复约束放在单一边界内；方案 B 作为隔离对照保留，不进入生产实现。

## Provenance

- Clean-room 行为输入：`docs/research/clean-room-specs/example-agent-event.md`，由 Rabbit Code 自行编写，只描述输入、输出、状态和约束。
- 合法公开抽象参考：`docs/research/codex-source-register.yml` 固定 Apache-2.0 来源、`docs/research/opencode-research-register.yml` 固定 MIT 来源、`docs/research/claude-agent-sdk-neutral-spec.md` 的 SDK 文档事实；只使用模块/问题域抽象，不复制源码、测试、文案或常量。
- 许可证/NOTICE：本 ADR 不引入第三方代码；未来逐文件复用必须另开许可证和 NOTICE 审查。
- 原创性：事件类型、状态名、payload 约束、方案比较和决策均为 Rabbit Code 独立设计。
- 字符串与相似性检查：RC-023 denylist、RC-024 专有内容政策和人工 diff 审查通过。

## 后续门禁

- 实现 PR 必须包含 `.github/pull_request_template.md` 的 Provenance 段。
- 实现者只能接收已审查的 clean-room 规格，不能访问 source-map 还原源码。
- 真实核心模块实现前，补充正式审查人、日期、来源链接和测试证据。
