# Type 3 监督式窗口重排实验

本实验针对 rescue-space 分析中发现的 Top-20 可救回空间，训练一个轻量监督模型预测候选记忆相关性，并只在 Top-K 窗口内做保守重排。参数 `alpha/window_k/keep_top1` 只在训练 query 上选择，测试 query 不参与调参。

优化目标：`balanced`。该实验不调用外部大模型，也不使用测试 query 的 gold evidence 进行排序。

## Held-Out 结果

| 方法 | Rows | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 0.418 | 0.349 | 0.429 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| supervised_window_reranker | 126 | 0.417 | 0.349 | 0.413 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |

## 相比 Candidate Reranker 的变化

- `supervised_window_reranker`：MRR `-0.0009`，R@5 `+0.0000`，Coverage@5 `+0.0000`，Full@5 `+0.0000`。

## 训练集选择的参数

| Seed | Alpha | Window K | Keep Top1 | Train Coverage@5 | Train Full@5 |
|---:|---:|---:|---:|---:|---:|
| 13 | 0.0 | 5 | True | 0.579 | 0.467 |
| 17 | 0.8 | 5 | True | 0.391 | 0.250 |
| 23 | 0.0 | 5 | True | 0.443 | 0.250 |
| 29 | 0.8 | 5 | True | 0.375 | 0.222 |
| 31 | 0.0 | 5 | True | 0.356 | 0.222 |

## Top Feature Importance

| Feature | Importance Mean | Importance Std |
|---|---:|---:|
| candidate_rr | 1.1622 | 0.2110 |
| candidate_norm | 1.0732 | 0.1749 |
| candidate_rrf | 0.8604 | 0.1742 |
| bm25_norm | 0.5981 | 0.1548 |
| text_len_log | 0.5887 | 0.0760 |
| query_token_coverage | 0.4591 | 0.0360 |
| semantic_norm | 0.2772 | 0.0685 |
| importance_score | 0.2437 | 0.1215 |
| memory_type=work | 0.2214 | 0.0454 |
| memory_type=hobby | 0.2164 | 0.0885 |
| memory_type=event | 0.2133 | 0.1135 |
| memory_type=plan | 0.1980 | 0.1653 |

## 解释

- 如果该方法提升 MRR 且不降低 Coverage@5/Full@5，说明保守窗口重排能利用 Top-20 可救回空间。
- 如果 Coverage@5 仍没有提升，说明需要真正的 set/listwise 覆盖目标，而非单候选相关性模型。
- 如果指标下降，说明当前 Type 3 训练样本或特征不足，应优先增强召回或引入 LLM 子问题标签。
