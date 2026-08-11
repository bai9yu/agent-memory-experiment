# 人工错误复核统计

本文件汇总人工复核表中的标注结果，用于判断自动错误分析是否足以写入论文。未完成标注时，本文件会明确显示 pending 状态。

## 总览

- 状态：`pending_labels`
- 样本数：80
- 至少填写一个人工字段的样本数：0
- 三个人工字段均已填写的样本数：0
- 非法标签数：0

## 字段分布

暂无人工标注。

## 按自动错误类型统计

| Auto Reason | Labeled | Yes | Partial | No | Unlabeled | Weighted Correct |
| --- | --- | --- | --- | --- | --- | --- |
| activity_neighbor | 0 | 0 | 0 | 0 | 5 | 0.000 |
| career_education_neighbor | 0 | 0 | 0 | 0 | 4 | 0.000 |
| gold_below_top20 | 0 | 0 | 0 | 0 | 13 | 0.000 |
| identity_neighbor | 0 | 0 | 0 | 0 | 3 | 0.000 |
| memory_type_mismatch | 0 | 0 | 0 | 0 | 23 | 0.000 |
| other | 0 | 0 | 0 | 0 | 8 | 0.000 |
| persona_confusion | 0 | 0 | 0 | 0 | 5 | 0.000 |
| preference_neighbor | 0 | 0 | 0 | 0 | 4 | 0.000 |
| relationship_neighbor | 0 | 0 | 0 | 0 | 4 | 0.000 |
| semantic_neighbor | 0 | 0 | 0 | 0 | 5 | 0.000 |
| temporal_neighbor | 0 | 0 | 0 | 0 | 6 | 0.000 |

## 论文使用判断

- 当前只能说明人工复核流程已经准备好，不能宣称自动错误分类已被人工验证。
- 需要填写 `manual_reason`、`auto_reason_correct`、`top_memory_relevant`、`gold_memory_sufficient` 后重新运行本脚本。
