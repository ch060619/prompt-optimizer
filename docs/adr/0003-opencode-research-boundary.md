# ADR-0003：OpenCode 调研的抽象复用边界

RC IDs: RC-018

## 状态

Accepted for research; no upstream code is approved for Rabbit Code.

## 决策

Rabbit Code 只吸收 OpenCode 固定提交中可独立表达的架构抽象：模块边界、状态生命周期、协议分层、Provider 能力边界、扩展边界和客户端契约。所有实现代码、测试、文案、资源、协议常量和 UI 资产均不复制。

研究原型使用原创的合成事件名验证边界转换，不导入 OpenCode 依赖，不改变 Rabbit Code 运行时，也不作为生产功能。

## 采用项

- 用明确的 Agent、服务、协议、Provider 和呈现层边界指导后续 Rabbit Code 设计。
- 保留 schema-first 和能力声明的研究方向，但协议字段必须由 Rabbit Code 自行定义并测试。
- 用隔离的客户端契约思路评估 CLI、GUI 和服务之间的接口，不复制 SDK 实现。

## 放弃项

- 不复制 `anomalyco/opencode` 的源码、测试、内部提示词、文案、资源或 UI 设计。
- 不把 OpenCode 的目录布局当成 Rabbit Code 的目标目录；现有 Python/FastAPI、React/TypeScript 和 CLI 边界继续独立演进。
- 不把 MIT 许可证理解为允许忽略 NOTICE、版权声明或修改声明；如果将来需要逐文件复用，必须另开来源登记和许可证审查。

## 验证

- 固定 SHA、MIT 许可证和路径证据：`docs/research/opencode-research-register.yml`。
- 模块对照：`docs/research/opencode-module-map.md`。
- 原创隔离原型：`scripts/opencode_boundary_prototype.py`。
