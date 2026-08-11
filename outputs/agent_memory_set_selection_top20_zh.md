# 集合级选择基线

本实验在 candidate reranker 的 Top-20 候选上做无监督 set-level selection：保留原 Top-1，然后用文本 Jaccard 去重和 memory type 多样性选择后续候选。
固定参数：alpha=1.0, beta=0.25, gamma=0.05。该方法不使用 gold evidence 调参。所有指标仅基于已缓存 Top-20 候选计算。

## Overall

| Method | Rows | MRR | R@1 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 2760 | 0.660 | 0.556 | 0.796 | 0.653 | 0.527 | 0.786 | 0.658 |
| set_selector_all | 2760 | 0.658 | 0.556 | 0.780 | 0.637 | 0.512 | 0.786 | 0.658 |
| set_selector_type3 | 2760 | 0.660 | 0.556 | 0.794 | 0.651 | 0.526 | 0.786 | 0.658 |

## Type 3

| Method | Rows | MRR | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 0.418 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| set_selector_all | 126 | 0.412 | 0.452 | 0.340 | 0.238 | 0.597 | 0.444 |
| set_selector_type3 | 126 | 0.412 | 0.452 | 0.340 | 0.238 | 0.597 | 0.444 |

## 解释

- `set_selector_type3` 没有提升 Type 3 coverage，说明仅在当前 Top-20 内做文本去重和 memory type 多样性不足以解决多证据覆盖。
- Coverage@20 反映输入候选池的总体证据空间；Coverage@5 下降说明简单多样性可能把相关证据推到更后。
- 下一步应做 query decomposition、扩大候选召回，或训练真正的 set-level selector，而不是只在 Top-20 内做启发式重排。
