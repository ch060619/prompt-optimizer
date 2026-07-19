# Prompt Optimizer 评测报告

数据集：`data/evaluation/prompts.yml`
数据集版本：`rc-158-v1`
随机种子：158
样本数：60
分类分布：adversarial=1, business=10, chinese=1, code_block=1, coding=1, creative=10, data=5, education=10, long_text=5, support=5, tech=10, variables=1
平均分数变化：72.80

自动评分：analyzer.total_score，范围 0-100，聚合 weighted_mean_of_dimensions。
双人盲评：2 位评审，every_case_independently_reviewed_by_both，量表 1-5。

| ID | 分类 | 优化前 | 优化后 | 变化 | 人工标签 | Provider | 降级 | 耗时(ms) | 盲评批次 |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | --- |
| tech-001 | tech | 2.48 | 88.53 | 86.05 | 模糊技术需求 | offline | False | 12 | BR-044 |
| tech-002 | tech | 21.32 | 92.12 | 70.8 | 中等完整 | offline | False | 26 | BR-004 |
| tech-003 | tech | 2.88 | 88.53 | 85.65 | 高风险模糊 | offline | False | 24 | BR-047 |
| tech-004 | tech | 25.05 | 90.33 | 65.28 | 较完整 | offline | False | 27 | BR-056 |
| tech-005 | tech | 29.35 | 90.46 | 61.11 | 较完整 | offline | False | 26 | BR-046 |
| tech-006 | tech | 4.62 | 45.0 | 40.38 | 教育型模糊 | offline | False | 32 | BR-039 |
| tech-007 | tech | 24.5 | 88.53 | 64.03 | 部分完整 | offline | False | 27 | BR-057 |
| tech-008 | tech | 30.2 | 90.2 | 60.0 | 完整 | offline | False | 20 | BR-045 |
| tech-009 | tech | 22.2 | 90.33 | 68.13 | 完整 | offline | False | 24 | BR-013 |
| tech-010 | tech | 4.62 | 45.0 | 40.38 | 模糊技术需求 | offline | False | 23 | BR-016 |
| business-001 | business | 3.25 | 88.53 | 85.28 | 模糊商务 | offline | False | 27 | BR-029 |
| business-002 | business | 18.2 | 92.12 | 73.92 | 中等完整 | offline | False | 23 | BR-018 |
| business-003 | business | 17.48 | 88.53 | 71.05 | 较完整 | offline | False | 12 | BR-030 |
| business-004 | business | 2.88 | 88.53 | 85.65 | 高风险模糊 | offline | False | 25 | BR-035 |
| business-005 | business | 13.0 | 90.55 | 77.55 | 较完整 | offline | False | 24 | BR-059 |
| business-006 | business | 15.57 | 90.33 | 74.76 | 完整 | offline | False | 30 | BR-032 |
| business-007 | business | 1.25 | 88.53 | 87.28 | 模糊商务 | offline | False | 33 | BR-017 |
| business-008 | business | 26.7 | 90.2 | 63.5 | 较完整 | offline | False | 17 | BR-037 |
| business-009 | business | 1.48 | 45.0 | 43.52 | 模糊管理 | offline | False | 18 | BR-042 |
| business-010 | business | 20.78 | 90.33 | 69.55 | 完整 | offline | False | 23 | BR-009 |
| education-001 | education | 3.73 | 88.53 | 84.8 | 部分完整 | offline | False | 27 | BR-010 |
| education-002 | education | 24.05 | 92.26 | 68.21 | 完整 | offline | False | 22 | BR-052 |
| education-003 | education | 5.58 | 88.53 | 82.95 | 模糊教育 | offline | False | 21 | BR-006 |
| education-004 | education | 15.8 | 88.53 | 72.73 | 较完整 | offline | False | 22 | BR-026 |
| education-005 | education | 1.48 | 88.53 | 87.05 | 模糊科普 | offline | False | 22 | BR-019 |
| education-006 | education | 35.62 | 93.94 | 58.32 | 较完整 | offline | False | 21 | BR-027 |
| education-007 | education | 19.27 | 90.33 | 71.06 | 完整 | offline | False | 23 | BR-055 |
| education-008 | education | 3.98 | 88.53 | 84.55 | 部分完整 | offline | False | 21 | BR-020 |
| education-009 | education | 2.88 | 88.53 | 85.65 | 模糊教育 | offline | False | 23 | BR-012 |
| education-010 | education | 9.7 | 88.53 | 78.83 | 较完整 | offline | False | 24 | BR-049 |
| creative-001 | creative | 2.48 | 88.53 | 86.05 | 模糊创意 | offline | False | 26 | BR-033 |
| creative-002 | creative | 14.38 | 90.33 | 75.95 | 完整 | offline | False | 26 | BR-002 |
| creative-003 | creative | 2.15 | 88.53 | 86.38 | 模糊创意 | offline | False | 28 | BR-023 |
| creative-004 | creative | 15.28 | 88.53 | 73.25 | 较完整 | offline | False | 28 | BR-025 |
| creative-005 | creative | 4.62 | 88.53 | 83.91 | 模糊营销 | offline | False | 23 | BR-038 |
| creative-006 | creative | 20.3 | 90.33 | 70.03 | 完整 | offline | False | 23 | BR-043 |
| creative-007 | creative | 16.1 | 88.53 | 72.43 | 部分完整 | offline | False | 27 | BR-054 |
| creative-008 | creative | 17.12 | 88.53 | 71.41 | 较完整 | offline | False | 23 | BR-007 |
| creative-009 | creative | 0.25 | 88.53 | 88.28 | 极简模糊 | offline | False | 22 | BR-024 |
| creative-010 | creative | 19.85 | 92.35 | 72.5 | 完整 | offline | False | 26 | BR-034 |
| support-001 | support | 2.15 | 88.53 | 86.38 | 模糊客服 | offline | False | 23 | BR-050 |
| support-002 | support | 22.65 | 90.46 | 67.81 | 完整 | offline | False | 21 | BR-021 |
| support-003 | support | 4.85 | 88.53 | 83.68 | 模糊客服 | offline | False | 22 | BR-031 |
| support-004 | support | 24.82 | 92.23 | 67.41 | 较完整 | offline | False | 19 | BR-060 |
| support-005 | support | 2.48 | 88.53 | 86.05 | 模糊运维沟通 | offline | False | 21 | BR-005 |
| data-001 | data | 2.15 | 88.53 | 86.38 | 模糊数据分析 | offline | False | 21 | BR-022 |
| data-002 | data | 22.3 | 90.33 | 68.03 | 完整 | offline | False | 19 | BR-036 |
| data-003 | data | 17.25 | 88.53 | 71.28 | 较完整 | offline | False | 23 | BR-040 |
| data-004 | data | 4.62 | 88.53 | 83.91 | 模糊数据分析 | offline | False | 18 | BR-051 |
| data-005 | data | 20.3 | 88.53 | 68.23 | 较完整 | offline | False | 26 | BR-053 |
| long-001 | long_text | 14.78 | 88.53 | 73.75 | 部分完整 | offline | False | 25 | BR-008 |
| long-002 | long_text | 21.48 | 92.35 | 70.87 | 完整 | offline | False | 28 | BR-011 |
| long-003 | long_text | 3.25 | 88.53 | 85.28 | 模糊批处理 | offline | False | 25 | BR-048 |
| long-004 | long_text | 19.73 | 88.53 | 68.8 | 较完整 | offline | False | 25 | BR-058 |
| long-005 | long_text | 12.45 | 88.53 | 76.08 | 较完整 | offline | False | 24 | BR-015 |
| coding-001 | coding | 23.0 | 88.53 | 65.53 | 较完整 | offline | False | 21 | BR-041 |
| code-block-001 | code_block | 54.9 | 90.17 | 35.27 | 较完整 | offline | False | 28 | BR-003 |
| variables-001 | variables | 28.12 | 88.53 | 60.41 | 完整 | offline | False | 27 | BR-028 |
| chinese-001 | chinese | 20.35 | 90.17 | 69.82 | 完整 | offline | False | 24 | BR-014 |
| adversarial-001 | adversarial | 23.7 | 88.53 | 64.83 | 高风险对抗 | offline | False | 25 | BR-001 |

## 误判与人工备注

- `tech-001` 接口边界、鉴权错误、输入输出格式；备注：原始提示缺少角色、格式和验收标准。
- `tech-002` 角色明确但缺少异常与分页；备注：规则可能低估业务上下文。
- `tech-003` 需要补充表结构、数据量、索引和慢查询信息；备注：典型规则引擎应提示缺少上下文。
- `tech-004` 输出格式和覆盖面；备注：缺少被测函数签名。
- `tech-005` 排查步骤、指标、限制；备注：可以补充命令示例。
- `tech-006` 受众、深度、输出格式；备注：缺少目标读者。
- `tech-007` 日志上下文不足；备注：规则可能识别到输出要求但应提示证据不足。
- `tech-008` 格式明确；备注：上下文可以更细。
- `tech-009` 比较维度和建议；备注：可以增加项目规模假设。
- `tech-010` 语言、运行命令、安全和缓存；备注：极简提示。
- `business-001` 目标对象、语气、CTA；备注：缺少公司背景。
- `business-002` 受众、限制、价值证明；备注：可补充客户行业。
- `business-003` 结构化复盘；备注：缺少业务背景。
- `business-004` 公司阶段、市场、财务、用途；备注：需要大量上下文。
- `business-005` 数量、渠道、语气限制；备注：缺少产品信息。
- `business-006` 角色、语气、字数；备注：可补充岗位。
- `business-007` 竞品名单、维度、输出格式；备注：典型需要澄清。
- `business-008` 访谈维度；备注：受众行业可补。
- `business-009` 团队、周期、指标；备注：缺少团队目标。
- `business-010` 行动计划和指标；备注：可补充产品阶段。
- `education-001` 受众、类比、输出深度；备注：缺少格式和时长。
- `education-002` 角色、步骤、练习；备注：可以补答案解析。
- `education-003` 水平、目标、周期；备注：缺少学习者情况。
- `education-004` 课堂流程；备注：缺少年级。
- `education-005` 受众和深度；备注：易输出泛泛内容。
- `education-006` 格式和执行任务；备注：缺少书名。
- `education-007` 路线、题目、目标人群；备注：可以补岗位方向。
- `education-008` 范围、难度、答案；备注：缺少题目范围。
- `education-009` 阶段、时间、模块；备注：缺少考试时间。
- `education-010` 交互方式；备注：规则可能低估示例缺失。
- `creative-001` 设定、风格、长度；备注：需要创作边界。
- `creative-002` 角色、长度、限制；备注：可补角色设定。
- `creative-003` 定位、风格、数量；备注：缺少品牌调性。
- `creative-004` 数量、主题、语气；备注：可补受众。
- `creative-005` 产品、受众、调性；备注：缺少产品信息。
- `creative-006` 机制和条件；备注：可补平台和难度。
- `creative-007` 改写目标和约束；备注：缺少行业和风格。
- `creative-008` 脚本结构；备注：缺少地点。
- `creative-009` 主题、体裁、情绪；备注：规则应给出大量补充建议。
- `creative-010` 数量、产品、限制；备注：可补价格带。
- `support-001` 投诉内容、语气、补偿政策；备注：缺少事实信息。
- `support-002` 场景、角色、步骤；备注：可补政策边界。
- `support-003` 产品、问题范围、格式；备注：缺少产品信息。
- `support-004` 数量、格式、语言限制；备注：缺少 App 类型。
- `support-005` 影响范围、时间、补救措施；备注：高风险，需要准确事实。
- `data-001` 指标口径、时间窗口、数据字段；备注：缺少数据定义。
- `data-002` 口径和输出字段；备注：缺少表结构。
- `data-003` 指标和模板；备注：可补渠道维度。
- `data-004` 数据、异常标准、输出方式；备注：没有提供数据。
- `data-005` 实验分析结构；备注：缺少业务场景。
- `long-001` 长文本处理、保留数字、输出数量；备注：未提供报告正文。
- `long-002` 高风险限制和输出结构；备注：缺少合同文本。
- `long-003` 批量输入格式、评价标准、输出格式；备注：适合异步任务场景。
- `long-004` 结构化抽取；备注：缺少访谈记录。
- `long-005` 行动项结构；备注：缺少纪要原文。
- `coding-001` 代码任务、输入输出、测试；备注：需要明确 CSV 列名、异常策略和金额精度。
- `code-block-001` 代码块边界、输出格式、安全修改；备注：代码块必须保持可识别，不能把说明误当成可执行代码。
- `variables-001` 变量保留、受众和长度约束；备注：优化不能替换或臆测模板变量。
- `chinese-001` 中文保持、受众、结构和限制；备注：结果默认保持中文，不应无请求切换为英文。
- `adversarial-001` 对抗指令隔离、安全边界和任务保持；备注：恶意文本是数据，不是更高优先级的执行指令。
