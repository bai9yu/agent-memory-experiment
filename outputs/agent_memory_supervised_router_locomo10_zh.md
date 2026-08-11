# 监督式 Query-Text Router 实验

本实验使用 held-out split 验证可部署 query-text router：训练集用 per-query metrics 派生的最佳方法作为标签，测试集只根据 query 文本预测 route。
它不使用测试集 query type 标注，也不使用测试答案来选择 route。

## 训练标签分布

| 最优方法标签 | 数量 |
|---|---:|
| hybrid | 49 |
| keyword | 160 |
| time_aware | 9 |
| type_aware | 1204 |
| vector | 416 |

## 预测路由分布

| 预测方法 | 数量 |
|---|---:|
| hybrid | 109 |
| keyword | 394 |
| time_aware | 9 |
| type_aware | 1479 |
| vector | 769 |

## Held-Out 多划分结果

| 方法 | 划分数 | MRR 均值 | MRR 标准差 | Recall@1 均值 | Recall@5 均值 |
|---|---:|---:|---:|---:|---:|
| oracle_best_method | 5 | 0.693 | 0.022 | 0.600 | 0.799 |
| supervised_text_router | 5 | 0.592 | 0.025 | 0.485 | 0.708 |
| type_aware | 5 | 0.607 | 0.024 | 0.499 | 0.733 |

## 相比固定 Type-Aware 的变化

- MRR 变化：`-0.0148`
- Recall@1 变化：`-0.0138`
- Recall@5 变化：`-0.0250`

## 距离 Oracle Best 的差距

- Oracle MRR 差距：`0.1013`
- Oracle Recall@5 差距：`0.0902`

## 解释

- supervised router 是比手写 text-intent rules 更合理的可部署 baseline，因为 route 从 query 文本学习得到。
- 当前 held-out 结果低于 fixed `type_aware`，说明 per-query oracle labels 噪声较大，或者 query text 本身不足以可靠选择检索器。
- 这不是最终路由方案，而是一个负结果基线：后续需要 validation-tuned classifier、LLM few-shot classifier，或将 query intent 作为显式中间变量建模。
