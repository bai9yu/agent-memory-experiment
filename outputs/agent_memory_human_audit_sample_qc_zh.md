# Human Audit Sample QC

本文件检查 priority20/full80 人工复核样本的结构质量：样本数、重复、错误类型覆盖、query type 覆盖、rank 区间覆盖和标注完成进度。它不自动填写人工标签，也不把空白标注当作已完成结果。

## 总览

- Priority CSV: `outputs/agent_memory_human_audit_priority20_blind_review.csv`
- Full CSV: `outputs/agent_memory_human_audit_full80_blind_review.csv`
- Blocking QC failures: 0
- Coverage warnings: 0
- Pending human-label progress rows: 4
- Sample QC pass: True

## QC 明细

| Scope | Group | Value | Count | Total | Share | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| priority20 | overview | sample_count | 20 | 20 | 1.000 | pass | expected=20 |
| priority20 | overview | duplicate_audit_ids | 0 | 20 | 0.000 | pass | audit_id should be unique within scope |
| priority20 | overview | confirmed_samples | 0 | 20 | 0.000 | pending_human_labels | not required for sample QC; tracked for labeling progress |
| priority20 | overview | missing_required_human_fields | 60 | 60 | 1.000 | pending_human_labels | human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient |
| priority20 | coverage | auto_reason_types | 8 | 8 | 1.000 | pass | sample should cover multiple automatic error categories |
| priority20 | coverage | query_types | 5 | 5 | 1.000 | pass | sample should cover multiple LoCoMo query types |
| priority20 | coverage | rank_buckets | 4 | 4 | 1.000 | pass | rank_11_20=6;rank_2_5=7;rank_6_10=4;rank_gt_20=3 |
| full80 | overview | sample_count | 80 | 80 | 1.000 | pass | expected=80 |
| full80 | overview | duplicate_audit_ids | 0 | 80 | 0.000 | pass | audit_id should be unique within scope |
| full80 | overview | confirmed_samples | 0 | 80 | 0.000 | pending_human_labels | not required for sample QC; tracked for labeling progress |
| full80 | overview | missing_required_human_fields | 240 | 240 | 1.000 | pending_human_labels | human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient |
| full80 | coverage | auto_reason_types | 11 | 11 | 1.000 | pass | sample should cover multiple automatic error categories |
| full80 | coverage | query_types | 5 | 5 | 1.000 | pass | sample should cover multiple LoCoMo query types |
| full80 | coverage | rank_buckets | 4 | 4 | 1.000 | pass | rank_11_20=10;rank_2_5=41;rank_6_10=16;rank_gt_20=13 |
| priority20_vs_full80 | overlap | priority_queries_in_full80 | 20 | 20 | 1.000 | pass | priority20 is expected to be a focused subset or compatible slice of full80 |

## 分布明细

| Scope | Group | Value | Count | Share |
| --- | --- | --- | --- | --- |
| priority20 | auto_reason_distribution | memory_type_mismatch | 4 | 0.200 |
| priority20 | auto_reason_distribution | other | 4 | 0.200 |
| priority20 | auto_reason_distribution | career_education_neighbor | 3 | 0.150 |
| priority20 | auto_reason_distribution | gold_below_top20 | 3 | 0.150 |
| priority20 | auto_reason_distribution | temporal_neighbor | 3 | 0.150 |
| priority20 | auto_reason_distribution | activity_neighbor | 1 | 0.050 |
| priority20 | auto_reason_distribution | identity_neighbor | 1 | 0.050 |
| priority20 | auto_reason_distribution | relationship_neighbor | 1 | 0.050 |
| priority20 | query_type_distribution | 5 | 9 | 0.450 |
| priority20 | query_type_distribution | 4 | 4 | 0.200 |
| priority20 | query_type_distribution | 2 | 3 | 0.150 |
| priority20 | query_type_distribution | 1 | 2 | 0.100 |
| priority20 | query_type_distribution | 3 | 2 | 0.100 |
| priority20 | first_rank_bucket_distribution | rank_2_5 | 7 | 0.350 |
| priority20 | first_rank_bucket_distribution | rank_11_20 | 6 | 0.300 |
| priority20 | first_rank_bucket_distribution | rank_6_10 | 4 | 0.200 |
| priority20 | first_rank_bucket_distribution | rank_gt_20 | 3 | 0.150 |
| priority20 | top_memory_type_distribution | event | 4 | 0.200 |
| priority20 | top_memory_type_distribution | hobby | 4 | 0.200 |
| priority20 | top_memory_type_distribution | plan | 3 | 0.150 |
| priority20 | top_memory_type_distribution | preference | 3 | 0.150 |
| priority20 | top_memory_type_distribution | family | 2 | 0.100 |
| priority20 | top_memory_type_distribution | emotion | 1 | 0.050 |
| priority20 | top_memory_type_distribution | goal | 1 | 0.050 |
| priority20 | top_memory_type_distribution | relationship | 1 | 0.050 |
| priority20 | top_memory_type_distribution | work | 1 | 0.050 |
| full80 | auto_reason_distribution | memory_type_mismatch | 23 | 0.287 |
| full80 | auto_reason_distribution | gold_below_top20 | 13 | 0.163 |
| full80 | auto_reason_distribution | other | 8 | 0.100 |
| full80 | auto_reason_distribution | temporal_neighbor | 6 | 0.075 |
| full80 | auto_reason_distribution | activity_neighbor | 5 | 0.062 |
| full80 | auto_reason_distribution | persona_confusion | 5 | 0.062 |
| full80 | auto_reason_distribution | semantic_neighbor | 5 | 0.062 |
| full80 | auto_reason_distribution | career_education_neighbor | 4 | 0.050 |
| full80 | auto_reason_distribution | preference_neighbor | 4 | 0.050 |
| full80 | auto_reason_distribution | relationship_neighbor | 4 | 0.050 |
| full80 | auto_reason_distribution | identity_neighbor | 3 | 0.037 |
| full80 | query_type_distribution | 4 | 23 | 0.287 |
| full80 | query_type_distribution | 5 | 23 | 0.287 |
| full80 | query_type_distribution | 1 | 18 | 0.225 |
| full80 | query_type_distribution | 2 | 10 | 0.125 |
| full80 | query_type_distribution | 3 | 6 | 0.075 |
| full80 | first_rank_bucket_distribution | rank_2_5 | 41 | 0.512 |
| full80 | first_rank_bucket_distribution | rank_6_10 | 16 | 0.200 |
| full80 | first_rank_bucket_distribution | rank_gt_20 | 13 | 0.163 |
| full80 | first_rank_bucket_distribution | rank_11_20 | 10 | 0.125 |
| full80 | top_memory_type_distribution | event | 21 | 0.263 |
| full80 | top_memory_type_distribution | hobby | 12 | 0.150 |
| full80 | top_memory_type_distribution | preference | 12 | 0.150 |
| full80 | top_memory_type_distribution | plan | 10 | 0.125 |
| full80 | top_memory_type_distribution | family | 7 | 0.087 |
| full80 | top_memory_type_distribution | goal | 3 | 0.037 |
| full80 | top_memory_type_distribution | health | 3 | 0.037 |
| full80 | top_memory_type_distribution | identity | 3 | 0.037 |
| full80 | top_memory_type_distribution | work | 3 | 0.037 |
| full80 | top_memory_type_distribution | education | 2 | 0.025 |
| full80 | top_memory_type_distribution | emotion | 2 | 0.025 |
| full80 | top_memory_type_distribution | relationship | 2 | 0.025 |

## 论文使用边界

- 可以写：人工复核样本已经通过样本数、去重和覆盖性 QC，适合进入人工标注。
- 可以写：priority20/full80 的错误类型、query type 和 first-rank 区间分布可复现记录。
- 不能写：人工标注已经完成或错误分析已经 human-verified；这仍取决于 human_* 字段是否填写并通过 agreement/readiness gate。
