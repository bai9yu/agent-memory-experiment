# Indexed Candidate Prefilter Experiment

本实验使用 batched dense similarity matrix 先计算 query-memory 相似度并取 top-N，再在候选集合上执行重排。
它模拟向量索引候选召回的批量上限，但仍是 exact top-N，不是 ANN 近似索引。

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| scorer_init_and_query_cache | 4.9046 | 2.67 |
| batched_similarity_topn | 0.2920 | 0.16 |

## Runtime

| Candidate Limit | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|
| 50 | 50.0 | 3.7550 | 4.0470 | 8.91x |
| 100 | 100.0 | 6.9133 | 7.2054 | 5.00x |
| 200 | 200.0 | 11.0479 | 11.3399 | 3.18x |
| 500 | 500.0 | 24.2026 | 24.4946 | 1.47x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.482 | 0.639 | 0.695 | 0.579 |
| 100 | 0.497 | 0.667 | 0.724 | 0.600 |
| 200 | 0.509 | 0.681 | 0.733 | 0.613 |
| 500 | 0.507 | 0.675 | 0.737 | 0.612 |

## 结论

- batched top-N 把候选召回阶段压缩到很小的固定成本。
- top-200 仍然是当前较好的效率-准确率折中点。
- 若后续换成 FAISS/HNSW 等 ANN 索引，应进一步报告召回率、构建时间和查询时间。
