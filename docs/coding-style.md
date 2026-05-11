# 代码规范

## Python

- 使用 Python 3.12+。
- 使用 `src` 布局和类型标注。
- 使用 Pydantic 定义接口数据模型。
- 业务逻辑放在核心服务层，CLI 和 API 不重复实现。
- 使用 `pytest` 编写测试，使用 `ruff` 和 `mypy` 做质量检查。

## TypeScript

- 使用 React 函数组件和 Hooks。
- API 类型集中放在 `src/types.ts`。
- 组件状态保持简单，复杂业务逻辑留在后端核心服务。
- 样式使用普通 CSS，保持本地工具界面简洁、可扫描。

## 提交信息

推荐格式：

```text
feat: add prompt scoring engine
fix: handle empty prompt validation
docs: update installation guide
test: cover export service
```

## 测试要求

- 新增评分规则时补充核心测试。
- 新增 API 时补充集成测试。
- 新增前端交互时补充组件测试。

