# 贡献指南

## 提交流程

1. Fork 仓库并创建功能分支。
2. 修改代码、模板或文档。
3. 运行测试和质量检查。
4. 提交 Pull Request，并说明变更动机、测试结果和兼容性影响。

## 本地检查

```bash
cd backend
pytest
ruff check .
mypy src

cd ../frontend
npm test
npm run lint
npm run build
```

## 模板贡献

新增模板请放到 `data/templates/` 中对应分类文件，确保：

- ID 唯一且语义清楚。
- 包含变量说明和最佳实践。
- 模板文本可以直接复制使用。

## 规则贡献

新增或修改评分规则时，请同步更新 `docs/prompt-rules.md`，并补充测试说明规则行为。

