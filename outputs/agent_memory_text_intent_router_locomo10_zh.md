# Text-Intent Router Experiment

本实验只使用 query 文本规则预测 route，不使用 LoCoMo 标注 type，因此比 query-type router 更接近可部署设置。

## Overall Result

| Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|
| type_aware | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| text_intent_router | 1838 | 0.489 | 0.661 | 0.715 | 0.595 |

## Router Gain Over Fixed Type-Aware

- Delta Recall@1: `-0.0147`
- Delta Recall@5: `-0.0180`
- Delta MRR: `-0.0146`

## Route Distribution

| Selected Method | Predicted Intent | Queries | Share |
|---|---|---:|---:|
| keyword | keyword_heavy | 181 | 0.098 |
| type_aware | causal_type_aware | 171 | 0.093 |
| type_aware | default_type_aware | 953 | 0.518 |
| type_aware | temporal_type_aware | 342 | 0.186 |
| vector | identity_profile_vector | 191 | 0.104 |

## By Predicted Intent

| Predicted Intent | Selected Method | Queries | Recall@1 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|
| causal_type_aware | type_aware | 171 | 0.497 | 0.754 | 0.614 |
| default_type_aware | type_aware | 953 | 0.470 | 0.695 | 0.576 |
| identity_profile_vector | vector | 191 | 0.387 | 0.628 | 0.503 |
| keyword_heavy | keyword | 181 | 0.409 | 0.619 | 0.510 |
| temporal_type_aware | type_aware | 342 | 0.635 | 0.854 | 0.734 |

## Interpretation

- 该规则版 router 是可部署 baseline，但仍然很粗糙，可能把大量问题路由到不合适的方法。
- 结果显著弱于 fixed `type_aware`，说明简单关键词规则不足以替代 LoCoMo query type 标注。
- 与 oracle-light query-type router 形成对照：有标注 type 时 routing 略有潜力；只靠粗规则预测 route 时会稳定退化。
- 下一步需要更强的 query intent classifier，例如基于 validation split 训练的小模型、LLM few-shot classifier，或更细的手写规则并配合验证集调参。
