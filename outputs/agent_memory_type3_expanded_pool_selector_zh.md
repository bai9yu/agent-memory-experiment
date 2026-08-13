# Type 3 扩展候选池证据选择实验

本实验把上一轮召回增强的候选池接入实际 Top-5 证据选择：候选池由 candidate Top-20、offline Top-K 和 intent-facet Top-K 合并得到，然后用无监督多信号打分与冗余惩罚选择证据。排序阶段不使用 gold evidence。

## 参数

- offline_k：`50`
- facet_k：`50`
- select_k：`5`
- keep_top1：`True`
- redundancy_weight：`0.02`

## 结果

| 方法 | Rows | Pool | MRR | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 | Coverage@100 | Full@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 20.0 | 0.418 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 | 0.597 | 0.444 |
| candidate20_then_expansion | 126 | 80.2 | 0.421 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 | 0.720 | 0.563 |
| expanded_pool_selector | 126 | 80.2 | 0.422 | 0.500 | 0.348 | 0.206 | 0.462 | 0.286 | 0.720 | 0.563 |
| expanded_pool_oracle_top5 | 126 | 80.2 | 0.865 | 0.865 | 0.718 | 0.563 | 0.718 | 0.563 | 0.718 | 0.563 |

## 相比 Candidate Reranker 的变化

- `candidate20_then_expansion`：MRR `+0.0027`，R@5 `+0.0000`，Coverage@5 `+0.0000`，Full@5 `+0.0000`，Coverage@100 `+0.1232`，Full@100 `+0.1190`。
- `expanded_pool_oracle_top5`：MRR `+0.4468`，R@5 `+0.3730`，Coverage@5 `+0.3455`，Full@5 `+0.3016`，Coverage@100 `+0.1208`，Full@100 `+0.1190`。
- `expanded_pool_selector`：MRR `+0.0040`，R@5 `+0.0079`，Coverage@5 `-0.0241`，Full@5 `-0.0556`，Coverage@100 `+0.1232`，Full@100 `+0.1190`。

## 解释

- 如果 Coverage@5/Full@5 提升，说明召回增强已经能转化为端到端证据选择收益。
- `candidate20_then_expansion` 不改变原始 Top-20，只把扩展证据追加到后面，用来检验候选池收益是否可保守保留。
- `expanded_pool_oracle_top5` 使用 gold evidence 构造上限，只用于诊断，不是可部署方法。
- 如果 oracle 明显提升但 selector 不提升，说明候选池变好了，但 Top-5 selector 还不够强。
- 如果 MRR 下降明显，说明扩展候选带来噪声，需要学习式 listwise/setwise 目标控制排序。
