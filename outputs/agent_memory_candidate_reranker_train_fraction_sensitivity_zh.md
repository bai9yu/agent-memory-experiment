# Candidate Reranker 训练比例敏感性

本实验复用已缓存的 LoCoMo10 BGE-M3 ranking 候选池，不重新计算 embedding，也不调用外部 API。它检查 intrinsic candidate reranker 是否依赖固定的 70% train fraction。

## 设置

- Train fractions: 0.5, 0.6, 0.7, 0.8
- Seeds per fraction: 101, 103, 107, 109, 113, 127, 131, 137, 139, 149
- Baseline: fixed `type_aware`
- Compared methods: `ablation_intrinsic_only`, `ablation_full`

## 跨训练比例平均指标

| Train Fraction | Method | Seeds | MRR | MRR Std | Recall@5 | Recall@5 Std |
|---:|---|---:|---:|---:|---:|---:|
| 0.5 | ablation_full | 10 | 0.662 | 0.0077 | 0.783 | 0.0081 |
| 0.5 | ablation_intrinsic_only | 10 | 0.671 | 0.0064 | 0.795 | 0.0061 |
| 0.5 | type_aware | 10 | 0.612 | 0.0060 | 0.733 | 0.0063 |
| 0.6 | ablation_full | 10 | 0.665 | 0.0115 | 0.788 | 0.0081 |
| 0.6 | ablation_intrinsic_only | 10 | 0.674 | 0.0063 | 0.795 | 0.0079 |
| 0.6 | type_aware | 10 | 0.614 | 0.0077 | 0.734 | 0.0088 |
| 0.7 | ablation_full | 10 | 0.669 | 0.0145 | 0.789 | 0.0062 |
| 0.7 | ablation_intrinsic_only | 10 | 0.673 | 0.0120 | 0.797 | 0.0086 |
| 0.7 | type_aware | 10 | 0.614 | 0.0134 | 0.733 | 0.0119 |
| 0.8 | ablation_full | 10 | 0.668 | 0.0157 | 0.792 | 0.0166 |
| 0.8 | ablation_intrinsic_only | 10 | 0.675 | 0.0152 | 0.798 | 0.0164 |
| 0.8 | type_aware | 10 | 0.610 | 0.0159 | 0.728 | 0.0191 |

## 相对 Type-Aware 的敏感性

| Train Fraction | Method | Mean ΔMRR | Min ΔMRR | Win Rate | Mean ΔR@5 | Min ΔR@5 |
|---:|---|---:|---:|---:|---:|---:|
| 0.5 | ablation_full | 0.0508 | 0.0400 | 1.00 | 0.0503 | 0.0305 |
| 0.5 | ablation_intrinsic_only | 0.0598 | 0.0501 | 1.00 | 0.0622 | 0.0435 |
| 0.6 | ablation_full | 0.0518 | 0.0427 | 1.00 | 0.0535 | 0.0394 |
| 0.6 | ablation_intrinsic_only | 0.0604 | 0.0501 | 1.00 | 0.0609 | 0.0435 |
| 0.7 | ablation_full | 0.0547 | 0.0373 | 1.00 | 0.0558 | 0.0417 |
| 0.7 | ablation_intrinsic_only | 0.0584 | 0.0414 | 1.00 | 0.0645 | 0.0471 |
| 0.8 | ablation_full | 0.0574 | 0.0394 | 1.00 | 0.0639 | 0.0380 |
| 0.8 | ablation_intrinsic_only | 0.0644 | 0.0513 | 1.00 | 0.0704 | 0.0435 |

## 主要结论

- `intrinsic_only` 在所有测试训练比例上的 MRR win rate 最低为 1.00，最小 seed-level ΔMRR 为 0.0414，平均 fraction-level ΔMRR 为 0.0608。
- `full` reranker 也保持正向，但 intrinsic-only 更简洁，仍适合作为主方法。
- 该结果说明当前方法不是只在 70% train fraction 下成立；但它仍属于 LoCoMo10 内部稳定性证据，不能替代跨数据集泛化。
