# Candidate Reranker 多 Seed 稳定性

本实验复用已缓存的 LoCoMo10 BGE-M3 ranking 候选池，不重新计算 embedding，也不调用外部 API。目的不是提出新方法，而是回答审稿人可能追问的随机划分稳定性问题：intrinsic candidate reranker 的提升是否只来自少数幸运 seed。

## 设置

- Seeds: 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197
- Train fraction: 0.7
- Baseline: fixed `type_aware`
- Compared methods: `ablation_intrinsic_only`, `ablation_full`
- Candidate pool: `keyword/vector/hybrid/time_aware/type_aware` Top-K 并集

## 跨 Seed 平均指标

| Method | Seeds | MRR | MRR Std | Recall@5 | Recall@5 Std |
|---|---:|---:|---:|---:|---:|
| ablation_intrinsic_only | 20 | 0.675 | 0.0126 | 0.803 | 0.0118 |
| ablation_full | 20 | 0.670 | 0.0127 | 0.791 | 0.0095 |
| type_aware | 20 | 0.615 | 0.0122 | 0.738 | 0.0154 |

## 相对 Type-Aware 的 Seed-wise 稳定性

| Method | Mean ΔMRR | Std ΔMRR | Min ΔMRR | Max ΔMRR | Positive Seeds | Win Rate | Mean ΔR@5 | Min ΔR@5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ablation_intrinsic_only | 0.0602 | 0.0098 | 0.0414 | 0.0775 | 20/20 | 1.00 | 0.0657 | 0.0471 |
| ablation_full | 0.0551 | 0.0077 | 0.0373 | 0.0711 | 20/20 | 1.00 | 0.0530 | 0.0181 |

## 主要结论

- `intrinsic_only` 在 20/20 个 seed 上 MRR 高于 `type_aware`，平均 ΔMRR=0.0602，最小 ΔMRR=0.0414。
- `full` reranker 在 20/20 个 seed 上 MRR 高于 `type_aware`，平均 ΔMRR=0.0551。
- 跨 seed 平均看，`intrinsic_only` MRR=0.675，`full` MRR=0.670，`type_aware` MRR=0.615。
- 该结果支持把 `intrinsic_only` 作为论文主方法：它不是单一划分上的偶然提升，同时比 full reranker 更简洁。

## 写作边界

- 可以写：在扩展 seed stability 检查中，intrinsic candidate reranker 的 MRR 提升在全部随机划分上保持为正。
- 仍需谨慎：这不是外部数据集泛化证据，不能替代真实外部 embedding baseline 或人工复核。
