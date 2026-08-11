# 论文表格汇总

该文件由 `generate_paper_tables.py` 从缓存实验结果生成，用于写论文时复制主结果表、消融表和 Type 3 失败分析表。

## LoCoMo10 主检索结果

| Method | Queries | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- | --- |
| keyword | 1838 | 0.428 | 0.581 | 0.634 | 0.526 |
| vector | 1838 | 0.419 | 0.585 | 0.643 | 0.527 |
| hybrid | 1838 | 0.477 | 0.647 | 0.705 | 0.583 |
| time_aware | 1838 | 0.499 | 0.668 | 0.727 | 0.605 |
| type_aware | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |

## 记忆形态对比

| Memory | Queries | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- | --- |
| llm_extracted_fact | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| locomo_observation | 1638 | 0.483 | 0.639 | 0.703 | 0.583 |

## 候选级学习重排

| Method | Splits | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- | --- |
| type_aware | 5 | 0.499 | 0.670 | 0.733 | 0.607 |
| candidate_reranker | 5 | 0.556 | 0.732 | 0.796 | 0.661 |
| candidate_oracle | 5 | 0.909 | 0.909 | 0.909 | 0.909 |

## 候选级重排显著性

| Metric | Delta | 95% CI | p-value |
| --- | --- | --- | --- |
| mrr | +0.0539 | [0.0462, 0.0619] | 0.0002 |
| recall@5 | +0.0623 | [0.0500, 0.0746] | 0.0002 |

## 候选级重排 LOCO 验证

| Method | Splits | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- | --- |
| type_aware | 10 | 0.503 | 0.669 | 0.732 | 0.608 |
| candidate_reranker_loco | 10 | 0.557 | 0.720 | 0.782 | 0.657 |
| candidate_oracle | 10 | 0.911 | 0.911 | 0.911 | 0.911 |

## 候选级重排 LOCO 显著性

| Metric | Delta | 95% CI | p-value |
| --- | --- | --- | --- |
| mrr | +0.0504 | [0.0411, 0.0601] | 0.0002 |
| recall@5 | +0.0522 | [0.0375, 0.0675] | 0.0002 |

## 候选级重排特征组消融

| Method | MRR | ΔMRR vs Type-Aware | ΔMRR vs Full | R@5 | ΔR@5 vs Type-Aware |
| --- | --- | --- | --- | --- | --- |
| ablation_intrinsic_only | 0.672 | +0.0652 | +0.0113 | 0.801 | +0.0681 |
| ablation_full | 0.661 | +0.0539 | +0.0000 | 0.796 | +0.0623 |
| ablation_no_time_features | 0.632 | +0.0251 | -0.0287 | 0.766 | +0.0322 |
| ablation_retrieval_rank_only | 0.615 | +0.0080 | -0.0458 | 0.732 | -0.0018 |
| type_aware | 0.607 | +0.0000 | -0.0539 | 0.733 | +0.0000 |
| ablation_type_aware_score_only | 0.547 | -0.0600 | -0.1139 | 0.663 | -0.0707 |

## Type 3 方法边界

| Method | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- |
| type_aware | 0.344 | 0.507 | 0.546 | 0.434 |
| type3_specific_reranker | 0.312 | 0.417 | 0.475 | 0.399 |
| supervised_set_selector | 0.312 | 0.393 | 0.490 | 0.389 |
| query_decomposition | 0.128 | 0.221 | 0.279 | 0.214 |
| type_aware_plus_decomposition | 0.198 | 0.442 | 0.512 | 0.342 |
| candidate_oracle | 0.778 | 0.778 | 0.778 | 0.778 |

## Type 3 覆盖显著性

| Experiment | Candidate | Base Cov@5 | Cand Cov@5 | Delta | p-value |
| --- | --- | --- | --- | --- | --- |
| type3_specific_reranker | type3_specific_reranker | 0.377 | 0.331 | -0.0467 | 0.0474 |
| supervised_set_selector | supervised_set_selector | 0.377 | 0.320 | -0.0572 | 0.0286 |
| query_decomposition_fusion | type_aware_plus_decomposition | 0.370 | 0.337 | -0.0325 | 0.0198 |

## 向量候选预筛选

| Candidate K | R@1 | R@3 | R@5 | MRR |
| --- | --- | --- | --- | --- |
| 50 | 0.482 | 0.639 | 0.695 | 0.579 |
| 100 | 0.498 | 0.667 | 0.724 | 0.600 |
| 200 | 0.509 | 0.682 | 0.734 | 0.613 |
| 500 | 0.507 | 0.675 | 0.737 | 0.612 |
