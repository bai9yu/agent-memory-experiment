# FAISS Candidate Prefilter Experiment

本实验使用 BGE-M3 embedding + FAISS 先做向量候选召回，再在候选集合上执行 type-aware 重排。
`flat` 是 exact inner-product index；`ivf` 是 ANN inverted-file index，可通过 `nlist/nprobe` 控制速度与召回折中。

## Index Setting

- Backend: `sentence-transformer`
- Embedding model: `BAAI/bge-m3`
- FAISS index: `flat`
- Metric: `inner_product_on_l2_normalized_vectors`
- nlist: `64`
- nprobe: `8`
- Memories: `2517`
- Queries: `1838`

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| scorer_init_and_query_cache | 4.2215 | 2.30 |
| train_index | 0.0000 | - |
| add_vectors | 0.0006 | - |
| query_index | 0.1008 | 0.05 |

## Runtime And Candidate Recall

| Candidate Limit | Candidate Gold Recall | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.875 | 50.0 | 3.7868 | 3.8876 | 9.27x |
| 100 | 0.935 | 100.0 | 5.9472 | 6.0480 | 5.96x |
| 200 | 0.977 | 200.0 | 10.5566 | 10.6574 | 3.38x |
| 500 | 0.993 | 500.0 | 24.6463 | 24.7472 | 1.46x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.482 | 0.639 | 0.695 | 0.579 |
| 100 | 0.497 | 0.667 | 0.723 | 0.600 |
| 200 | 0.508 | 0.681 | 0.734 | 0.612 |
| 500 | 0.506 | 0.674 | 0.737 | 0.611 |

## 结论

- FAISS 使候选召回具备标准向量索引实现，适合写入论文效率实验。
- `flat` 可作为 exact upper-bound；`ivf` 用于报告 ANN 速度-召回折中。
- 如果 IVF 的 candidate gold recall 明显下降，需要提高 `nprobe` 或增大候选池。
