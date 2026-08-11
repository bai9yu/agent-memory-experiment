# Query-Type Router Experiment

本实验不重新运行检索，而是基于已有 per-query metrics 做离线 routing：不同 LoCoMo query type 选择不同检索方法。

## Routing Rule

| Query Type | Selected Method |
|---|---|
| Type 1 | vector |
| Type 2 | type_aware |
| Type 3 | type_aware |
| Type 4 | type_aware |
| Type 5 | keyword |

## Overall Result

| Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|
| type_aware | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| query_type_router | 1838 | 0.505 | 0.674 | 0.731 | 0.611 |

## Router Gain Over Fixed Type-Aware

- Delta Recall@1: `0.0016`
- Delta Recall@5: `-0.0022`
- Delta MRR: `0.0020`

## By-Type Router Result

| Query Type | Queries | Selected Method | Recall@1 | Recall@5 | MRR |
|---|---:|---|---:|---:|---:|
| Type 1 | 278 | vector | 0.371 | 0.658 | 0.513 |
| Type 2 | 310 | type_aware | 0.632 | 0.826 | 0.723 |
| Type 3 | 86 | type_aware | 0.326 | 0.547 | 0.429 |
| Type 4 | 752 | type_aware | 0.557 | 0.794 | 0.663 |
| Type 5 | 412 | keyword | 0.442 | 0.633 | 0.537 |

## Interpretation

- 该 router 是 oracle-light 版本：它使用 LoCoMo 已知 query type，不使用测试标签答案，因此适合作为后续 query-intent router 的上界启发。
- router 的 MRR 比固定 `type_aware` 高 0.0020，但 Recall@5 低 0.0022；paired significance test 显示该差异尚不显著。
- 结果说明统一打分公式仍可能有改进空间，但当前 router 只能作为后续方法方向，不能作为已经稳定提升的主结论。
- 真正可部署版本需要用规则或小模型从 query 文本预测 route，而不能依赖数据集标注的 type。
