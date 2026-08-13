# Type 3 学习式扩展池证据选择实验

本实验在扩展候选池上训练无依赖的轻量选择器：用训练 query 的相关/不相关候选特征均值差学习权重，在 validation seed 上选择 mix/redundancy/keep_top1，再在 held-out seed 上评估。

优化目标：`coverage`。测试 query 的 gold evidence 不参与训练或调参。

## Held-Out 结果

| 方法 | Rows | Pool | MRR | R@5 | Coverage@5 | Full@5 | Coverage@100 | Full@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate20_then_expansion | 126 | 80.2 | 0.421 | 0.492 | 0.372 | 0.262 | 0.720 | 0.563 |
| learned_expanded_selector | 126 | 80.2 | 0.421 | 0.492 | 0.372 | 0.262 | 0.720 | 0.563 |
| expanded_pool_oracle_top5 | 126 | 80.2 | 0.865 | 0.865 | 0.718 | 0.563 | 0.718 | 0.563 |

## 相比 Candidate20 Then Expansion 的变化

- `expanded_pool_oracle_top5`：MRR `+0.4441`，R@5 `+0.3730`，Coverage@5 `+0.3455`，Full@5 `+0.3016`。
- `learned_expanded_selector`：MRR `-0.0001`，R@5 `+0.0000`，Coverage@5 `+0.0000`，Full@5 `+0.0000`。

## Validation 选择参数

| Seed | Mix | Redundancy | Keep Top1 | Validation Coverage@5 | Validation Full@5 |
|---:|---:|---:|---:|---:|---:|
| 13 | 0.0 | 0.0 | True | 0.461 | 0.348 |
| 17 | 0.0 | 0.0 | True | 0.351 | 0.208 |
| 23 | 0.0 | 0.0 | True | 0.351 | 0.208 |
| 29 | 0.0 | 0.0 | True | 0.351 | 0.208 |
| 31 | 0.0 | 0.0 | True | 0.351 | 0.208 |

## Top Learned Weights

| Feature | Mean Abs Weight | Mean Weight | Std |
|---|---:|---:|---:|
| candidate_norm | 1.7441 | 1.7441 | 0.1211 |
| candidate_rank_inv | 1.6918 | 1.6918 | 0.1315 |
| source_candidate | 1.1997 | 1.1997 | 0.0712 |
| bm25_norm | 0.7549 | 0.7549 | 0.0572 |
| facet_hits | 0.5587 | 0.5587 | 0.0860 |
| persona_score | 0.3633 | 0.3633 | 0.0158 |
| importance_score | 0.3109 | 0.3109 | 0.0719 |
| memory_type=hobby | 0.2957 | -0.2957 | 0.0440 |
| source_facet | 0.2890 | 0.2890 | 0.0144 |
| semantic_norm | 0.2442 | 0.2442 | 0.0705 |
| source_offline | 0.2146 | 0.2146 | 0.0414 |
| memory_type=work | 0.1891 | -0.1891 | 0.0040 |

## 解释

- 如果学习式选择器提升 Coverage@5/Full@5，说明扩展池收益已能转成最终证据选择收益。
- 如果仍低于 oracle，说明需要更强的 listwise/setwise 模型或 LLM 子问题标签。
- 如果与保守追加基线持平，说明当前无依赖特征学习不足，但扩展池本身仍有价值。
