# RC 追踪约定

<!-- RC ID: RC-043 -->

每个实现、测试、设计决策和发布说明都必须引用主控计划中的需求。单项写作 `RC ID: RC-xxx`，多项写作 `RC IDs: RC-xxx, RC-yyy`；只有这种显式字段会被索引。通用模板位于 `docs/templates/` 和 `.github/`。

生成反向索引：

```powershell
python scripts/check_rc_traceability.py --write
```

检查模板与索引是否同步：

```powershell
python scripts/check_rc_traceability.py --check
```

查询单个需求的全部仓库证据：

```powershell
python scripts/check_rc_traceability.py --rc RC-043
```

报告中的 `RED` 是待处理状态：孤立需求尚无主控计划外引用，孤立代码文件尚无有效 RC 引用。该状态用于暴露迁移基线，不代表脚本执行失败；模板缺失、ID 集合错误或索引过期才会使检查失败。
