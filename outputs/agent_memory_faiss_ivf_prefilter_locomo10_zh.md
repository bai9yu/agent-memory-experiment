# FAISS Candidate Prefilter Experiment

本实验使用 BGE-M3 embedding + FAISS 先做向量候选召回，再在候选集合上执行 type-aware 重排。
`flat` 是 exact inner-product index；`ivf` 是 ANN inverted-file index，可通过 `nlist/nprobe` 控制速度与召回折中。

## Index Setting

- Backend: `sentence-transformer`
- Embedding model: `BAAI/bge-m3`
- FAISS index: `ivf`
- Metric: `inner_product_on_l2_normalized_vectors`
- nlist: `64`
- nprobe: `8`
- Memories: `2517`
- Queries: `1838`

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| scorer_init_and_query_cache | 4.3323 | 2.36 |
| train_index | 0.0092 | - |
| add_vectors | 0.0018 | - |
| query_index | 0.0739 | 0.04 |

## Runtime And Candidate Recall

| Candidate Limit | Candidate Gold Recall | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.841 | 50.0 | 4.1677 | 4.2416 | 8.50x |
| 100 | 0.879 | 100.0 | 6.7496 | 6.8235 | 5.28x |
| 200 | 0.901 | 200.0 | 11.9836 | 12.0575 | 2.99x |
| 500 | 0.905 | 349.9 | 19.0257 | 19.0996 | 1.89x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.458 | 0.610 | 0.662 | 0.552 |
| 100 | 0.467 | 0.621 | 0.674 | 0.562 |
| 200 | 0.477 | 0.629 | 0.680 | 0.571 |
| 500 | 0.475 | 0.628 | 0.679 | 0.571 |

## 结论

- FAISS 使候选召回具备标准向量索引实现，适合写入论文效率实验。
- `flat` 可作为 exact upper-bound；`ivf` 用于报告 ANN 速度-召回折中。
- 如果 IVF 的 candidate gold recall 明显下降，需要提高 `nprobe` 或增大候选池。
