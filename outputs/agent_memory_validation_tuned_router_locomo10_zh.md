# 验证集调参 Text-Intent Router 实验

本实验保留 text-intent router 的 query 文本规则，只在训练集上为每个 predicted intent 自动选择平均 MRR 最好的检索方法。
测试集仅使用 query 文本得到 intent，再套用训练集学到的 intent-to-method route；不使用测试集 query type 或答案选择 route。

## Held-Out 多划分结果

| 方法 | 划分数 | MRR 均值 | MRR 标准差 | Recall@1 均值 | Recall@5 均值 |
|---|---:|---:|---:|---:|---:|
| oracle_best_method | 5 | 0.693 | 0.022 | 0.600 | 0.799 |
| type_aware | 5 | 0.607 | 0.024 | 0.499 | 0.733 |
| validation_tuned_intent_router | 5 | 0.606 | 0.023 | 0.497 | 0.733 |

## 相比固定 Type-Aware 的变化

- MRR 变化：`-0.0012`
- Recall@1 变化：`-0.0014`
- Recall@5 变化：`-0.0007`

## 距离 Oracle Best 的差距

- Oracle MRR 差距：`0.0877`
- Oracle Recall@5 差距：`0.0659`

## 学到的 Route 分布

| Predicted Intent | Selected Method | Splits |
|---|---|---:|
| causal_type_aware | time_aware | 2 |
| causal_type_aware | type_aware | 3 |
| default_type_aware | type_aware | 5 |
| identity_profile_vector | type_aware | 5 |
| keyword_heavy | time_aware | 2 |
| keyword_heavy | type_aware | 3 |
| temporal_type_aware | type_aware | 5 |

## 解释

- 该实验比固定手写 route 更稳健，因为 intent 到检索器的映射来自训练集表现。
- 如果它仍低于 fixed `type_aware`，说明当前 intent 颗粒度不足，无法稳定区分检索策略。
- 如果它接近或超过 fixed `type_aware`，可以继续把 intent detector 从规则替换为 LLM 或小模型分类器。
