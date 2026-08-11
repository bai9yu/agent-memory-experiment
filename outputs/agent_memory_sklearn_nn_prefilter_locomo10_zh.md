# Sklearn NearestNeighbors Candidate Prefilter Experiment

本实验使用 BGE-M3 embedding + sklearn NearestNeighbors 先做向量 top-N 候选召回，再在候选集合上执行重排。
当前 sklearn 配置是 exact nearest-neighbor index baseline，不是 FAISS/HNSW 近似索引；它用于建立可复现的向量索引效率对照。

## Index Setting

- Backend: `sentence-transformer`
- Embedding model: `BAAI/bge-m3`
- sklearn algorithm: `brute`
- Metric: `euclidean`
- Note: vectors are L2-normalized before indexing; euclidean ranking is therefore equivalent to cosine ranking.
- Memories: `2517`
- Queries: `1838`

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| scorer_init_and_query_cache | 3.8181 | 2.08 |
| build_nearest_neighbors_index | 0.0011 | - |
| query_nearest_neighbors | 0.1602 | 0.09 |

## Runtime

| Candidate Limit | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|
| 50 | 50.0 | 3.7325 | 3.8927 | 9.26x |
| 100 | 100.0 | 5.7946 | 5.9548 | 6.05x |
| 200 | 200.0 | 10.2757 | 10.4359 | 3.45x |
| 500 | 500.0 | 23.4473 | 23.6075 | 1.53x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.482 | 0.639 | 0.695 | 0.579 |
| 100 | 0.498 | 0.667 | 0.724 | 0.600 |
| 200 | 0.509 | 0.682 | 0.734 | 0.613 |
| 500 | 0.507 | 0.675 | 0.737 | 0.612 |

## 结论

- sklearn NearestNeighbors 给出了 BGE-M3 向量索引版候选召回的可复现基线。
- 与直接 batched exact top-N 相比，它使用标准索引接口，更接近论文中的 retrieval system 设置。
- 下一步应加入 FAISS/HNSW，把 exact NN 与 ANN 在召回率、构建时间、查询时间和端到端 MRR 上并列表达。
