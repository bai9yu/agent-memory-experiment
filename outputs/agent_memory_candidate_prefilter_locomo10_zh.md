# LoCoMo10 候选预筛选实验

本实验先用 semantic top-N 取候选，再在候选集合上执行 keyword / hybrid / time-aware / type-aware 重排。

Full ranking 的 type-aware 基线为：

| Setting | Recall@1 | Recall@3 | Recall@5 | MRR | Runtime |
|---|---:|---:|---:|---:|---:|
| Full ranking | 0.503 | 0.670 | 0.733 | 0.609 | 36.0491s |

## Runtime

| Candidate Limit | Avg Candidates | Seconds | ms / Query | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|
| 50 | 50.0 | 6.2673 | 3.41 | 5.75x |
| 100 | 100.0 | 8.3394 | 4.54 | 4.32x |
| 200 | 200.0 | 13.4028 | 7.29 | 2.69x |
| 500 | 500.0 | 28.6656 | 15.60 | 1.26x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.482 | 0.639 | 0.694 | 0.579 |
| 100 | 0.497 | 0.668 | 0.724 | 0.600 |
| 200 | 0.509 | 0.681 | 0.733 | 0.613 |
| 500 | 0.507 | 0.674 | 0.736 | 0.611 |

## 结论

- top-50 速度最快，约 5.75x speedup，但 Recall@5 从 0.733 降到 0.694，候选召回损失明显。
- top-100 取得 4.32x speedup，MRR 从 0.609 降到 0.600，适合低延迟但允许小幅精度损失的设置。
- top-200 取得 2.69x speedup，并且 MRR 为 0.613，略高于 full ranking 的 0.609；这说明语义预筛选可能有降噪效果。
- top-500 只带来 1.26x speedup，准确率接近 top-200，但效率收益较小。

当前推荐：

```text
online setting: semantic top-200 prefilter + type-aware reranking
```

需要注意：本实验使用 semantic top-N 作为候选召回，仍然需要对全部 memory 计算一次 semantic score；真正线上部署还应使用向量索引近似 top-N，以进一步降低召回时间。
