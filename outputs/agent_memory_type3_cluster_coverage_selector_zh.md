# Type 3 集合级覆盖簇选择实验

本实验验证一个更接近多证据检索目标的选择策略：在扩展候选池上进行 Top-5 选择时，不只看单条候选分数，还奖励覆盖新的文本关键词簇，并惩罚与已选证据高度相似的候选。排序阶段不使用 gold evidence。

## 参数

- cluster_terms：`4`
- cluster_bonus：`0.035`
- near_duplicate_penalty：`0.04`
- keep_top1：`True`

## 结果

| 方法 | Rows | Pool | Top5 Clusters | MRR | R@5 | Coverage@5 | Full@5 | Coverage@100 | Full@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate20_then_expansion | 126 | 80.2 | 4.81 | 0.421 | 0.492 | 0.372 | 0.262 | 0.720 | 0.563 |
| cluster_coverage_selector | 126 | 80.2 | 4.87 | 0.422 | 0.484 | 0.343 | 0.206 | 0.720 | 0.563 |
| expanded_pool_oracle_top5 | 126 | 80.2 | 4.87 | 0.865 | 0.865 | 0.718 | 0.563 | 0.718 | 0.563 |

## 相比 Candidate20 Then Expansion 的变化

- `cluster_coverage_selector`：MRR `+0.0014`，R@5 `-0.0079`，Coverage@5 `-0.0290`，Full@5 `-0.0556`，Top5 cluster count `+0.0635`。
- `expanded_pool_oracle_top5`：MRR `+0.4441`，R@5 `+0.3730`，Coverage@5 `+0.3455`，Full@5 `+0.3016`，Top5 cluster count `+0.0556`。

## 解释

- 如果 Top5 cluster count 上升但 Coverage@5 不升，说明表面多样性没有对齐 gold evidence。
- 如果 Coverage@5/Full@5 上升，说明集合级覆盖信号可以把扩展候选池收益转化为最终证据选择收益。
- 如果仍低于 oracle，下一步应从无监督簇覆盖转向监督式 setwise/listwise 选择。
