# LSH Candidate Prefilter Experiment

本实验使用 dependency-free hash embedding + random-hyperplane LSH 先做近似候选召回，再在候选集合上执行重排。
它是一个可复现的 ANN-style 索引基线，用于补充效率实验；由于 embedding 不是 BGE-M3，不能直接替代 BGE 主结果。

## Index Setting

- Tables: `12`
- Bits per table: `8`
- Probe radius: `1`
- Memories: `2517`
- Queries: `1838`

## Index / Recall Stage

| Stage | Seconds | ms / Query |
|---|---:|---:|
| vectorize_memories | 0.0405 | - |
| build_lsh_index | 1.2675 | - |
| query_lsh_and_rank_pool | 5.3439 | 2.91 |

## Runtime

| Candidate Limit | Avg LSH Pool | Avg Candidates | Empty Queries | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 1137.6 | 50.0 | 0 | 2.8071 | 8.1510 | 4.42x |
| 100 | 1137.6 | 100.0 | 0 | 5.7221 | 11.0660 | 3.26x |
| 200 | 1137.6 | 200.0 | 0 | 11.3810 | 16.7249 | 2.16x |
| 500 | 1137.6 | 500.0 | 0 | 28.1194 | 33.4633 | 1.08x |

## Type-Aware Accuracy

| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|
| 50 | 0.385 | 0.507 | 0.553 | 0.458 |
| 100 | 0.393 | 0.519 | 0.561 | 0.470 |
| 200 | 0.389 | 0.522 | 0.572 | 0.471 |
| 500 | 0.388 | 0.520 | 0.568 | 0.472 |

## 结论

- LSH 给出了一个无需安装 FAISS/sklearn 的近似索引实验入口。
- 如果 LSH 准确率低于 BGE exact top-N，说明当前主要瓶颈不是索引结构，而是近似召回 embedding 的表达能力。
- 论文版建议继续加入 BGE-M3 + FAISS/HNSW，并报告 ANN recall、构建时间、查询时间和端到端 MRR。
