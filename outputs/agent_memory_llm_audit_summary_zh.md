# LLM-assisted 错误复核统计

本文件汇总 LLM-assisted 预标注结果，用于加速人工复核和检查自动错误分析。它不是人工标注结果，不能直接替代 human audit。

## 总览

- 状态：`llm_assisted_ready_for_human_review`
- 样本数：80
- 至少填写一个人工字段的样本数：80
- 三个人工字段均已填写的样本数：80
- 非法标签数：0

## 字段分布

| Field | Value | Count | Share |
| --- | --- | --- | --- |
| auto_reason_correct | yes | 28 | 0.350 |
| auto_reason_correct | partial | 29 | 0.362 |
| auto_reason_correct | no | 23 | 0.287 |
| top_memory_relevant | yes | 1 | 0.013 |
| top_memory_relevant | partial | 55 | 0.688 |
| top_memory_relevant | no | 24 | 0.300 |
| gold_memory_sufficient | yes | 63 | 0.787 |
| gold_memory_sufficient | no | 12 | 0.150 |
| gold_memory_sufficient | unclear | 5 | 0.062 |

## 按自动错误类型统计

| Auto Reason | Labeled | Yes | Partial | No | Unlabeled | Weighted Correct |
| --- | --- | --- | --- | --- | --- | --- |
| activity_neighbor | 5 | 0 | 4 | 1 | 0 | 0.400 |
| career_education_neighbor | 4 | 0 | 2 | 2 | 0 | 0.250 |
| gold_below_top20 | 13 | 12 | 0 | 1 | 0 | 0.923 |
| identity_neighbor | 3 | 3 | 0 | 0 | 0 | 1.000 |
| memory_type_mismatch | 23 | 8 | 9 | 6 | 0 | 0.543 |
| other | 8 | 0 | 3 | 5 | 0 | 0.188 |
| persona_confusion | 5 | 5 | 0 | 0 | 0 | 1.000 |
| preference_neighbor | 4 | 0 | 4 | 0 | 0 | 0.500 |
| relationship_neighbor | 4 | 0 | 0 | 4 | 0 | 0.000 |
| semantic_neighbor | 5 | 0 | 3 | 2 | 0 | 0.300 |
| temporal_neighbor | 6 | 0 | 4 | 2 | 0 | 0.333 |

## 论文使用判断

- 可以作为人工复核前的预标注材料，帮助快速定位自动错误分类是否合理。
- 不应直接写成 human audit；论文中最多表述为 LLM-assisted audit draft，最终仍需人工确认。
