# 中立 Agent 事件规格示例

RC IDs: RC-025

## Inputs

- 用户提交一段待处理文本。
- 当前任务具有唯一标识，工作区状态可被读取为摘要。

## Outputs

- 系统发送有序状态事件：开始、增量结果、工具状态、完成或失败。
- 用户可以看到失败类别和可重试提示，原始输入保持不变。

## State Transitions

```text
idle -> running -> streaming -> completed
idle -> running -> failed
running -> cancelled
```

## Constraints

- 未经允许不得扩大数据发送范围或自动执行高风险动作。
- 取消后不得继续提交新的外部副作用。
- 事件顺序和任务标识必须可追踪；未知事件不应破坏已提交状态。
- 本规格不描述任何实现文件、源代码、私有文案或专有协议常量。
