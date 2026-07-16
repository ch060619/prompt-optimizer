# V2 回归基线更新规则

- RC ID: RC-047
- Status: Accepted

`backend/tests/golden/v2_regression.json` 是 Prompt Optimizer V2 的黄金输出，覆盖评分、建议、规则、模板、优化、diff、历史、导出和评测。普通测试只读取并比较该文件，不自动改写它。

更新基线必须同时满足：

1. 有意行为变化已有对应 RC 和仓库内迁移说明。
2. 迁移说明包含 `RC ID: RC-xxx`、变化原因、兼容影响和审批结论。
3. 使用下列命令显式传入审批 RC、理由和迁移说明。
4. 评审生成差异；禁止看到测试失败后无审查地接受全部新输出。

```powershell
& .\.venv\Scripts\python.exe scripts\generate_v2_regression_baseline.py `
  --approve-rc RC-xxx `
  --reason "说明有意行为变化" `
  --migration-note docs\migrations\RC-xxx-description.md
```

若变化并非有意，应修复实现而不是更新黄金文件。动态时间、耗时和临时路径由生成器规范化，不得降低断言来绕过差异。
