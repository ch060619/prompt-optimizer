# 提示词规则说明

## 评分维度

- 清晰度：任务目标是否明确。
- 具体性：是否有范围、数量、边界和细节。
- 上下文完整度：是否给出背景、受众和场景。
- 输出格式：是否指定 Markdown、JSON、表格或字段。
- 约束条件：是否说明限制、禁用项、字数和语气。
- 角色设定：是否给出专业角色和工作视角。
- 示例质量：是否提供输入输出样例。
- 可执行性：是否能直接拆解为步骤和验收标准。

## 规则文件

规则位于 `data/rules/scoring.yml`。每个维度包含：

- `id`
- `label`
- `weight`
- `keywords`
- `min_length`
- `suggestion`

## 模板文件

模板位于 `data/templates/*.yml`。每个模板包含：

- `id`
- `name`
- `category`
- `description`
- `tags`
- `template`
- `variables`
- `best_practices`

