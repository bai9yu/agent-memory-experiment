# Type 3 监督式集合选择实验

本实验针对 LoCoMo Type 3 多证据问题，训练一个 greedy set-level selector。模型在每一步选择候选时，不只看单条 memory 的相关性，还加入已选集合带来的文本冗余、memory type 覆盖等上下文特征。

当前 redundancy weight 为 `0.0`。训练和测试仍使用 query-level held-out split，避免同一 query 的候选泄漏。

## Type 3 Held-Out 排序指标

| 方法 | 划分数 | 平均 Query 数 | MRR | R@1 | R@3 | R@5 |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 5 | 25.2 | 0.434 | 0.344 | 0.507 | 0.546 |
| global_candidate_reranker | 5 | 25.2 | 0.421 | 0.351 | 0.432 | 0.496 |
| type3_specific_reranker | 5 | 25.2 | 0.399 | 0.312 | 0.417 | 0.475 |
| supervised_set_selector | 5 | 25.2 | 0.389 | 0.312 | 0.393 | 0.490 |
| candidate_oracle | 5 | 25.2 | 0.778 | 0.778 | 0.778 | 0.778 |

## Type 3 多证据覆盖 @5

| 方法 | Rows | Mean Gold | Multi-Evidence Share | Any | Full | Coverage Ratio |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 126 | 2.65 | 0.675 | 0.548 | 0.230 | 0.377 |
| global_candidate_reranker | 126 | 2.65 | 0.675 | 0.492 | 0.262 | 0.372 |
| type3_specific_reranker | 126 | 2.65 | 0.675 | 0.468 | 0.206 | 0.331 |
| supervised_set_selector | 126 | 2.65 | 0.675 | 0.484 | 0.175 | 0.320 |
| candidate_oracle | 126 | 2.65 | 0.675 | 0.778 | 0.524 | 0.658 |

## 相比 Type-Aware 的变化

- MRR delta：`-0.0443`
- Recall@5 delta：`-0.0567`
- Coverage@5 delta：`-0.0572`
- Full@5 delta：`-0.0556`

## 解释

- 如果该方法提升 Coverage@5 但降低 MRR，说明集合覆盖目标有效，但会牺牲第一个证据的排序。
- 如果仍未超过 `type_aware`，说明仅用候选上下文特征还不足，需要显式 query decomposition 或更强的 listwise/setwise 学习目标。
- Candidate oracle 是候选池上限，用于判断剩余空间是否来自候选召回还是集合选择。
