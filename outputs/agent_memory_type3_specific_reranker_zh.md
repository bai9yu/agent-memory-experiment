# Type 3 专用监督重排实验

本实验只在 LoCoMo Type 3 多证据/推理类问题上评估候选级学习重排。训练时使用相同随机 query-level 划分，避免同一 query 的候选同时进入训练和测试。

对比方法：

- `type_aware`：固定公式检索基线。
- `global_candidate_reranker`：使用所有 query type 的训练候选学习，然后只在 Type 3 测试集评估。
- `type3_specific_reranker`：只使用训练集中的 Type 3 候选学习，再在 Type 3 测试集评估。
- `candidate_oracle`：候选池上限，用于判断瓶颈在候选召回还是重排。

## Type 3 Held-Out 排序指标

| 方法 | 划分数 | 平均 Query 数 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 5 | 25.2 | 0.434 | 0.344 | 0.507 | 0.546 |
| global_candidate_reranker | 5 | 25.2 | 0.421 | 0.351 | 0.432 | 0.496 |
| type3_specific_reranker | 5 | 25.2 | 0.399 | 0.312 | 0.417 | 0.475 |
| candidate_oracle | 5 | 25.2 | 0.778 | 0.778 | 0.778 | 0.778 |

## 相比 Type-Aware 的变化

- `global_candidate_reranker`：MRR `-0.0127`，Recall@5 `-0.0505`。
- `type3_specific_reranker`：MRR `-0.0346`，Recall@5 `-0.0716`。

配对显著性检验显示，`type3_specific_reranker` 相比 `type_aware` 的 MRR delta 为 `-0.0362`，95% CI `[-0.0705, -0.0002]`，permutation p-value `0.0460`；Recall@5 delta 为 `-0.0794`，95% CI `[-0.1429, -0.0238]`，p-value `0.0260`。因此该方向应作为负结果记录，而不是继续作为主要优化路线。

## Type 3 多证据覆盖 @5

| 方法 | Rows | Mean Gold | Multi-Evidence Share | Any | Full | Coverage Ratio |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 126 | 2.65 | 0.675 | 0.548 | 0.230 | 0.377 |
| global_candidate_reranker | 126 | 2.65 | 0.675 | 0.492 | 0.262 | 0.372 |
| type3_specific_reranker | 126 | 2.65 | 0.675 | 0.468 | 0.206 | 0.331 |
| candidate_oracle | 126 | 2.65 | 0.675 | 0.778 | 0.524 | 0.658 |

## Type3-Specific Top Feature Importance

| Feature | Importance Mean | Importance Std |
|---|---:|---:|
| semantic_score | 0.1365 | 0.0150 |
| vector_score | 0.0888 | 0.0076 |
| time_aware_score | 0.0858 | 0.0096 |
| type_aware_score | 0.0802 | 0.0084 |
| type_aware_rr | 0.0621 | 0.0094 |
| hybrid_score | 0.0613 | 0.0028 |
| time_aware_rr | 0.0612 | 0.0072 |
| vector_rr | 0.0573 | 0.0091 |
| hybrid_rr | 0.0466 | 0.0048 |
| time_decay | 0.0449 | 0.0063 |
| entity_score | 0.0317 | 0.0034 |
| importance_score | 0.0284 | 0.0043 |

## 结论

- 如果 Type3 专用模型没有超过 global reranker，说明目前 Type3 训练样本规模或特征表达不足，单独建模会过拟合。
- 如果 candidate oracle 明显高于学习器，后续应优先做 query decomposition 或 supervised set selector，而不是继续只优化 Top1 排名。
