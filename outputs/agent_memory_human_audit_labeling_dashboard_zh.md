# Human Audit Labeling Dashboard

本文件把 priority20/full80 盲审表的人工填写进度展开成可执行面板。它只读取 human_* 字段是否填写，不替代人工判断，也不使用 LLM-assisted 标签作为人工结果。

## 总览

- Priority CSV: `outputs/agent_memory_human_audit_priority20_blind_review.csv`
- Full CSV: `outputs/agent_memory_human_audit_full80_blind_review.csv`
- priority20 complete required: 0/20
- full80 complete required: 0/80
- Next item preview limit: 30

## Progress Summary

| Scope | Value | Count | Total | Share | Evidence |
| --- | --- | --- | --- | --- | --- |
| priority20 | samples | 20 | 20 | 1.000 | blind review rows |
| priority20 | complete_required | 0 | 20 | 0.000 | all required human_* fields filled |
| priority20 | partial_required | 0 | 20 | 0.000 | some required human_* fields filled |
| priority20 | not_started | 20 | 20 | 1.000 | no required human_* fields filled |
| priority20 | missing_required_fields | 60 | 60 | 1.000 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | samples | 80 | 80 | 1.000 | blind review rows |
| full80 | complete_required | 0 | 80 | 0.000 | all required human_* fields filled |
| full80 | partial_required | 0 | 80 | 0.000 | some required human_* fields filled |
| full80 | not_started | 80 | 80 | 1.000 | no required human_* fields filled |
| full80 | missing_required_fields | 240 | 240 | 1.000 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |

## Next Items To Label

| Scope | Review Order | Audit ID | Query Type | Auto Reason | Rank Bucket | Missing Required | Missing Fields |
| --- | --- | --- | --- | --- | --- | --- | --- |
| priority20 | 1 | audit_050 | 5 | other | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 2 | audit_076 | 2 | temporal_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 3 | audit_020 | 5 | gold_below_top20 | rank_gt_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 4 | audit_031 | 5 | memory_type_mismatch | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 5 | audit_002 | 1 | activity_neighbor | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 6 | audit_007 | 4 | career_education_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 7 | audit_051 | 5 | other | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 8 | audit_056 | 1 | other | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 9 | audit_055 | 5 | other | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 10 | audit_069 | 5 | relationship_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 11 | audit_025 | 5 | identity_neighbor | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 12 | audit_077 | 2 | temporal_neighbor | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 13 | audit_075 | 4 | temporal_neighbor | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 14 | audit_010 | 5 | gold_below_top20 | rank_gt_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 15 | audit_045 | 5 | memory_type_mismatch | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 16 | audit_034 | 4 | memory_type_mismatch | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 17 | audit_019 | 2 | gold_below_top20 | rank_gt_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 18 | audit_040 | 3 | memory_type_mismatch | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 19 | audit_009 | 4 | career_education_neighbor | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| priority20 | 20 | audit_006 | 3 | career_education_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 1 | audit_039 | 5 | memory_type_mismatch | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 2 | audit_009 | 4 | career_education_neighbor | rank_11_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 3 | audit_069 | 5 | relationship_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 4 | audit_010 | 5 | gold_below_top20 | rank_gt_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 5 | audit_052 | 4 | other | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 6 | audit_047 | 4 | memory_type_mismatch | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 7 | audit_014 | 4 | gold_below_top20 | rank_gt_20 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 8 | audit_064 | 4 | preference_neighbor | rank_6_10 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 9 | audit_080 | 2 | temporal_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |
| full80 | 10 | audit_076 | 2 | temporal_neighbor | rank_2_5 | 3 | human_auto_reason_correct;human_top_memory_relevant;human_gold_memory_sufficient |

## 使用方式

1. 标注者打开 priority20 或 full80 blind review CSV。
2. 优先从 `Next Items To Label` 中的 review_order 开始填写。
3. 每条至少填写 `human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`。
4. 建议同时填写 `human_manual_reason` 和 `human_auditor_notes`，便于后续错误分析复盘。

## 论文使用边界

- 可以写：人工标注进度有独立 dashboard，可复现记录每轮完成度。
- 不能写：dashboard 通过就等于人工审计完成；真正完成仍以 agreement/readiness gate 为准。
