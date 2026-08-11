# FAISS Candidate Prefilter Experiment

本实验使用 BGE-M3 embedding + FAISS 先做向量候选召回，再在候选集合上执行 type-aware 重排。
`flat` 是 exact inner-product index；`ivf` 是 ANN inverted-file index，可通过 `nlist/nprobe` 控制速度与召回折中。

## Index Setting

- Backend: `sentence-transformer`
- Embedding model: `BAAI/bge-m3`
- FAISS index: `ivf`
- Metric: `inner_product_on_l2_normalized_vectors`
- nlist: `64`
- nprobe: `32`
- Memories: `2517`
- Queries: `1838`

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| scorer_init_and_query_cache | 4.2128 | 2.29 |
| train_index | 0.0116 | - |
| add_vectors | 0.0017 | - |
| query_index | 0.2049 | 0.11 |

## Runtime And Candidate Recall

| Candidate Limit | Candidate Gold Recall | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.873 | 50.0 | 3.8148 | 4.0197 | 8.97x |
| 100 | 0.929 | 100.0 | 5.9913 | 6.1962 | 5.82x |
| 200 | 0.966 | 200.0 | 10.6785 | 10.8834 | 3.31x |
| 500 | 0.980 | 500.0 | 24.7715 | 24.9764 | 1.44x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.480 | 0.637 | 0.693 | 0.577 |
| 100 | 0.495 | 0.662 | 0.717 | 0.596 |
| 200 | 0.502 | 0.672 | 0.725 | 0.605 |
| 500 | 0.505 | 0.664 | 0.725 | 0.606 |

## 结论

- FAISS 使候选召回具备标准向量索引实现，适合写入论文效率实验。
- `flat` 可作为 exact upper-bound；`ivf` 用于报告 ANN 速度-召回折中。
- 如果 IVF 的 candidate gold recall 明显下降，需要提高 `nprobe` 或增大候选池。
