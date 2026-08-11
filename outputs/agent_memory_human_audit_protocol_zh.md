# 人工错误复核抽样包

本文件用于对自动错误分析结果做人工抽样复核。目标不是重新跑实验，而是检查自动错误类别是否可信，并为论文中的错误分析提供人工可靠性证据。

## 抽样设置

- 来源错误样本数：913
- 人工复核样本数：80
- 随机种子：20260811
- 每个自动错误类型最低抽样数：4

## 样本分布：自动错误类型

| Auto Reason | Sample Count | 判定说明 |
| --- | --- | --- |
| activity_neighbor | 5 | Top-1 与活动/经历相近，但不是问题要问的活动。 |
| career_education_neighbor | 4 | Top-1 与职业/教育相关，但不是目标事实。 |
| gold_below_top20 | 13 | 正确 gold evidence 没有进入 Top-20，主要是候选召回失败。 |
| identity_neighbor | 3 | Top-1 与人物身份相关，但身份属性或目标人物不对。 |
| memory_type_mismatch | 23 | Top-1 记忆主题相关但 memory type 与问题所需类型不匹配。 |
| other | 8 | 以上类别都不准确，或需要人工补充新的错误原因。 |
| persona_confusion | 5 | Top-1 混淆了说话人、人物身份或关系主体。 |
| preference_neighbor | 4 | Top-1 与偏好相近，但不是问题要问的偏好。 |
| relationship_neighbor | 4 | Top-1 与关系相关，但关系类型、对象或状态不对。 |
| semantic_neighbor | 5 | Top-1 与问题语义相近，但回答的是相邻事实而非目标事实。 |
| temporal_neighbor | 6 | Top-1 涉及相近事件或人物，但时间点不对。 |

## 样本分布：Query Type

| Query Type | Sample Count |
| --- | --- |
| 1 | 18 |
| 2 | 10 |
| 3 | 6 |
| 4 | 23 |
| 5 | 23 |

## 标注字段说明

- `manual_reason`：人工认为最合适的错误类型；可以沿用自动 reason，也可以填写新的类别。
- `auto_reason_correct`：填写 `yes` / `no` / `partial`，表示自动 reason 是否正确。
- `top_memory_relevant`：填写 `yes` / `no` / `partial`，表示 Top-1 memory 是否与问题有关。
- `gold_memory_sufficient`：填写 `yes` / `no` / `unclear`，表示 gold memory 是否足以回答问题。
- `auditor_notes`：记录判断依据、歧义点或新增错误类型。

## 论文使用方式

完成标注后，可以统计 `auto_reason_correct` 的 yes / partial / no 比例，作为自动错误分析可靠性的补充证据。如果 `gold_memory_sufficient=no` 的比例较高，需要在论文中说明该数据集标注本身存在证据不充分问题。
