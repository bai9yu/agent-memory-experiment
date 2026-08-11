# 候选级学习重排实验

本实验使用 `rankings.csv` 中各检索器 Top-K 候选的并集作为候选池，在训练 query 上学习 candidate-level relevance classifier，并在 held-out query 上重排候选记忆。
当前学习器为轻量随机森林分类器。它不重新计算 embedding，也不使用测试 query 的答案来训练；候选池受原始 Top-K 落盘范围限制。

## 候选标签分布

| Label | Count |
|---|---:|
| non_relevant | 72547 |
| relevant | 2581 |

## Held-Out 多划分结果

| 方法 | 划分数 | MRR 均值 | MRR 标准差 | Recall@1 均值 | Recall@5 均值 |
|---|---:|---:|---:|---:|---:|
| candidate_oracle | 5 | 0.909 | 0.014 | 0.909 | 0.909 |
| candidate_reranker | 5 | 0.661 | 0.028 | 0.556 | 0.796 |
| type_aware | 5 | 0.607 | 0.024 | 0.499 | 0.733 |

## 相比固定 Type-Aware 的变化

- MRR 变化：`0.0539`
- Recall@1 变化：`0.0569`
- Recall@5 变化：`0.0623`

## 候选池 Oracle 差距

- Candidate Oracle MRR 差距：`0.2488`
- Candidate Oracle Recall@5 差距：`0.1138`

## Top Feature Importance

| Feature | Importance Mean | Importance Std |
|---|---:|---:|
| type_aware_score | 0.0784 | 0.0041 |
| time_aware_rr | 0.0776 | 0.0083 |
| semantic_score | 0.0771 | 0.0014 |
| time_aware_score | 0.0762 | 0.0040 |
| hybrid_score | 0.0750 | 0.0037 |
| type_aware_rr | 0.0704 | 0.0045 |
| hybrid_rr | 0.0648 | 0.0033 |
| vector_rr | 0.0610 | 0.0011 |
| vector_score | 0.0565 | 0.0015 |
| time_decay | 0.0518 | 0.0020 |
| semantic_x_keyword | 0.0395 | 0.0017 |
| query_type=1 | 0.0302 | 0.0016 |

## 解释

- 该实验检验的是：给定多个检索器已经召回的候选并集，轻量学习器能否学到比固定公式更好的排序。
- candidate reranker 明显高于 fixed `type_aware`，说明固定加权公式不足以利用多检索器候选中的互补排序信号。
- candidate oracle 仍明显更高，说明候选池里还有大量未被重排器充分利用的空间。
- 按 query type 的细粒度结果见 `outputs/agent_memory_candidate_reranker_by_type_zh.md`；当前 Type 5 收益最大，Type 3 反而下降，是下一步重点优化对象。
