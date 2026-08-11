# 集合级选择基线

本实验在 candidate reranker 的 Top-10 候选上做无监督 set-level selection：保留原 Top-1，然后用文本 Jaccard 去重和 memory type 多样性选择后续候选。
固定参数：alpha=1.0, beta=0.25, gamma=0.05。该方法不使用 gold evidence 调参。所有指标仅基于已缓存 Top-10 候选计算。

## Overall

| Method | Rows | MRR | R@1 | R@5 | Coverage@5 | Full@5 | Coverage@10 | Full@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 2760 | 0.657 | 0.556 | 0.796 | 0.653 | 0.527 | 0.724 | 0.592 |
| set_selector_all | 2760 | 0.656 | 0.556 | 0.782 | 0.638 | 0.513 | 0.724 | 0.592 |
| set_selector_type3 | 2760 | 0.657 | 0.556 | 0.795 | 0.652 | 0.526 | 0.724 | 0.592 |

## Type 3

| Method | Rows | MRR | R@5 | Coverage@5 | Full@5 | Coverage@10 | Full@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 0.410 | 0.492 | 0.372 | 0.262 | 0.462 | 0.325 |
| set_selector_all | 126 | 0.407 | 0.468 | 0.351 | 0.238 | 0.462 | 0.325 |
| set_selector_type3 | 126 | 0.407 | 0.468 | 0.351 | 0.238 | 0.462 | 0.325 |

## 解释

- `set_selector_type3` 没有提升 Type 3 coverage，说明仅在当前 Top-10 内做文本去重和 memory type 多样性不足以解决多证据覆盖。
- Top-10 coverage 不变表示候选集合本身没有扩大；Top-5 下降说明简单多样性可能把相关证据推到更后。
- 下一步应做 query decomposition、扩大候选召回，或训练真正的 set-level selector，而不是只在 Top-10 内做启发式重排。
