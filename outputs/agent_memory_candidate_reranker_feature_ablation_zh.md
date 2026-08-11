# Candidate Reranker 特征组消融

本实验复用已落盘的 `rankings.csv` 候选池，不重新计算 embedding。它检查 candidate-level reranker 的提升是否依赖某一类特征，或是否来自多检索器候选信号融合。

## 消融设置

| Variant | Meaning |
|---|---|
| `full` | 原始 candidate reranker 全特征。 |
| `retrieval_rank_only` | 只保留各检索器的 score/rank/present 特征。 |
| `intrinsic_only` | 去掉各检索器 method-level 特征，只保留 candidate 自身分数、query type、memory type 和交互项。 |
| `no_time_features` | 去掉 time decay / recency / time-aware method 特征。 |
| `no_type_persona_features` | 去掉 query type、memory type、persona 和 type-aware method 特征。 |
| `no_keyword_features` | 去掉 keyword score、keyword method 和 semantic-keyword 交互。 |
| `no_semantic_features` | 去掉 semantic score、vector method 和 semantic-keyword 交互。 |
| `type_aware_score_only` | 只保留 fixed type-aware score/rank/present。 |

## 多划分结果

| Method | Splits | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|---:|---:|
| candidate_oracle | 5 | 0.909 | 0.909 | 0.909 | 0.909 |
| ablation_intrinsic_only | 5 | 0.672 | 0.568 | 0.746 | 0.801 |
| ablation_no_keyword_features | 5 | 0.666 | 0.563 | 0.734 | 0.799 |
| ablation_full | 5 | 0.661 | 0.556 | 0.732 | 0.796 |
| ablation_no_semantic_features | 5 | 0.644 | 0.542 | 0.707 | 0.766 |
| ablation_no_type_persona_features | 5 | 0.640 | 0.540 | 0.704 | 0.766 |
| ablation_no_time_features | 5 | 0.632 | 0.526 | 0.699 | 0.766 |
| ablation_retrieval_rank_only | 5 | 0.615 | 0.516 | 0.671 | 0.732 |
| type_aware | 5 | 0.607 | 0.499 | 0.670 | 0.733 |
| ablation_type_aware_score_only | 5 | 0.547 | 0.451 | 0.597 | 0.663 |

## 相对变化

| Method | MRR | ΔMRR vs Type-Aware | ΔMRR vs Full | R@5 | ΔR@5 vs Type-Aware | ΔR@5 vs Full |
|---|---:|---:|---:|---:|---:|---:|
| ablation_intrinsic_only | 0.672 | 0.0652 | 0.0113 | 0.801 | 0.0681 | 0.0058 |
| ablation_no_keyword_features | 0.666 | 0.0589 | 0.0051 | 0.799 | 0.0656 | 0.0033 |
| ablation_full | 0.661 | 0.0539 | 0.0000 | 0.796 | 0.0623 | 0.0000 |
| ablation_no_semantic_features | 0.644 | 0.0371 | -0.0168 | 0.766 | 0.0330 | -0.0293 |
| ablation_no_type_persona_features | 0.640 | 0.0336 | -0.0202 | 0.766 | 0.0330 | -0.0293 |
| ablation_no_time_features | 0.632 | 0.0251 | -0.0287 | 0.766 | 0.0322 | -0.0301 |
| ablation_retrieval_rank_only | 0.615 | 0.0080 | -0.0458 | 0.732 | -0.0018 | -0.0641 |
| type_aware | 0.607 | 0.0000 | -0.0539 | 0.733 | 0.0000 | -0.0623 |
| ablation_type_aware_score_only | 0.547 | -0.0600 | -0.1139 | 0.663 | -0.0707 | -0.1330 |

## 主要结论

- Full reranker 相比 fixed `type_aware` 的 MRR 提升为 `0.0539`，Recall@5 提升为 `0.0623`。
- Candidate oracle 相比 full reranker 仍有 MRR `0.2488` 的空间，说明候选池内仍存在未充分利用的相关证据。
- 如果某个去除特征组后的结果接近 full，说明该特征组不是主要增益来源；如果明显下降，说明该特征组对学习重排必要。
- 本实验与主 reranker 共享同一 train/test seed 和候选池，因此适合作为论文中的 ablation table。
