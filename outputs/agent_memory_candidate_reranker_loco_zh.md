# Candidate Reranker Leave-One-Conversation-Out 验证

本实验把 LoCoMo10 的每个 conversation 轮流作为测试集，其余 conversation 作为训练集。它比随机 query-level split 更严格，用于检查 candidate-level reranker 是否跨 conversation 保持收益。

## 总览

- Splits: 10
- Type-aware MRR: 0.608
- LOCO candidate reranker MRR: 0.657
- MRR delta: 0.049
- Recall@5 delta: 0.050

## 方法汇总

| Method | Splits | Mean Queries | MRR | MRR Stdev | R@1 | R@3 | R@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate_oracle | 10 | 183.800 | 0.911 | 0.022 | 0.911 | 0.911 | 0.911 |
| candidate_reranker_loco | 10 | 183.800 | 0.657 | 0.035 | 0.557 | 0.720 | 0.782 |
| type_aware | 10 | 183.800 | 0.608 | 0.031 | 0.503 | 0.669 | 0.732 |

## Delta

| Metric | Baseline | LOCO Reranker | Delta |
|---|---:|---:|---:|
| mrr | 0.608 | 0.657 | 0.049 |
| recall@1 | 0.503 | 0.557 | 0.054 |
| recall@3 | 0.669 | 0.720 | 0.051 |
| recall@5 | 0.732 | 0.782 | 0.050 |

## Split 明细

| Split | Method | Queries | MRR | R@1 | R@3 | R@5 |
|---|---|---:|---:|---:|---:|---:|
| record_01 | type_aware | 176 | 0.591 | 0.483 | 0.659 | 0.722 |
| record_01 | candidate_reranker_loco | 176 | 0.642 | 0.540 | 0.705 | 0.801 |
| record_01 | candidate_oracle | 176 | 0.909 | 0.909 | 0.909 | 0.909 |
| record_02 | type_aware | 94 | 0.577 | 0.489 | 0.628 | 0.670 |
| record_02 | candidate_reranker_loco | 94 | 0.601 | 0.511 | 0.660 | 0.713 |
| record_02 | candidate_oracle | 94 | 0.883 | 0.883 | 0.883 | 0.883 |
| record_03 | type_aware | 173 | 0.633 | 0.520 | 0.711 | 0.769 |
| record_03 | candidate_reranker_loco | 173 | 0.688 | 0.590 | 0.751 | 0.803 |
| record_03 | candidate_oracle | 173 | 0.931 | 0.931 | 0.931 | 0.931 |
| record_04 | type_aware | 239 | 0.587 | 0.477 | 0.644 | 0.699 |
| record_04 | candidate_reranker_loco | 239 | 0.643 | 0.540 | 0.707 | 0.762 |
| record_04 | candidate_oracle | 239 | 0.921 | 0.921 | 0.921 | 0.921 |
| record_05 | type_aware | 227 | 0.635 | 0.546 | 0.683 | 0.736 |
| record_05 | candidate_reranker_loco | 227 | 0.696 | 0.604 | 0.762 | 0.806 |
| record_05 | candidate_oracle | 227 | 0.912 | 0.912 | 0.912 | 0.912 |
| record_06 | type_aware | 148 | 0.583 | 0.473 | 0.642 | 0.723 |
| record_06 | candidate_reranker_loco | 148 | 0.626 | 0.527 | 0.682 | 0.716 |
| record_06 | candidate_oracle | 148 | 0.892 | 0.892 | 0.892 | 0.892 |
| record_07 | type_aware | 175 | 0.668 | 0.549 | 0.731 | 0.800 |
| record_07 | candidate_reranker_loco | 175 | 0.712 | 0.600 | 0.783 | 0.846 |
| record_07 | candidate_oracle | 175 | 0.954 | 0.954 | 0.954 | 0.954 |
| record_08 | type_aware | 228 | 0.592 | 0.491 | 0.645 | 0.711 |
| record_08 | candidate_reranker_loco | 228 | 0.640 | 0.539 | 0.702 | 0.772 |
| record_08 | candidate_oracle | 228 | 0.912 | 0.912 | 0.912 | 0.912 |
| record_09 | type_aware | 183 | 0.630 | 0.530 | 0.683 | 0.749 |
| record_09 | candidate_reranker_loco | 183 | 0.677 | 0.585 | 0.738 | 0.787 |
| record_09 | candidate_oracle | 183 | 0.913 | 0.913 | 0.913 | 0.913 |
| record_10 | type_aware | 195 | 0.587 | 0.467 | 0.667 | 0.744 |
| record_10 | candidate_reranker_loco | 195 | 0.643 | 0.533 | 0.713 | 0.810 |
| record_10 | candidate_oracle | 195 | 0.882 | 0.882 | 0.882 | 0.882 |

## 论文使用判断

- 如果 LOCO reranker 仍显著高于 type-aware，可把它写成跨 conversation 的泛化证据。
- 如果提升变小，应如实说明 candidate-level reranker 在更严格 split 下仍有收益，但泛化幅度弱于随机 query split。
