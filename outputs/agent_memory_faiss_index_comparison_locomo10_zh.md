# FAISS 向量索引对比实验

本报告比较 LoCoMo10 answerable slice 上的 BGE-M3 + FAISS 候选召回配置。所有配置都先用 FAISS 取 top-N 候选，再执行相同的 `type_aware` 重排。

## 关键设置

- 数据：DeepSeek extracted fact memory，2517 条 memories，1838 条 answerable queries。
- Embedding：`BAAI/bge-m3`，使用本地缓存。
- 检索：L2-normalized vectors 上的 inner product。
- Full-ranking baseline：36.0491 秒，MRR 0.609，Recall@5 0.733。
- 稳定性：在当前 macOS/arm64 环境中，FAISS 与 sentence-transformers 同进程运行需要设置 `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`，否则 IVF 实验可能触发原生库段错误。

## Top-200 主结果

| Index | nlist | nprobe | Candidate Gold Recall | Query Index Seconds | End-to-End Seconds | Speedup | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FAISS Flat | - | - | 0.977 | 0.1008 | 10.6574 | 3.38x | 0.508 | 0.734 | 0.612 |
| FAISS IVF | 64 | 8 | 0.901 | 0.0739 | 12.0575 | 2.99x | 0.477 | 0.680 | 0.571 |
| FAISS IVF | 64 | 32 | 0.966 | 0.2049 | 10.8834 | 3.31x | 0.502 | 0.725 | 0.605 |

## 多候选规模结果

| Index | Candidate Limit | Candidate Gold Recall | End-to-End Seconds | Speedup | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flat | 50 | 0.875 | 3.8876 | 9.27x | 0.482 | 0.695 | 0.579 |
| Flat | 100 | 0.935 | 6.0480 | 5.96x | 0.497 | 0.723 | 0.600 |
| Flat | 200 | 0.977 | 10.6574 | 3.38x | 0.508 | 0.734 | 0.612 |
| Flat | 500 | 0.993 | 24.7472 | 1.46x | 0.506 | 0.737 | 0.611 |
| IVF nprobe=8 | 50 | 0.841 | 4.2416 | 8.50x | 0.458 | 0.662 | 0.552 |
| IVF nprobe=8 | 100 | 0.879 | 6.8235 | 5.28x | 0.467 | 0.674 | 0.562 |
| IVF nprobe=8 | 200 | 0.901 | 12.0575 | 2.99x | 0.477 | 0.680 | 0.571 |
| IVF nprobe=8 | 500 | 0.905 | 19.0996 | 1.89x | 0.475 | 0.679 | 0.571 |
| IVF nprobe=32 | 50 | 0.873 | 4.0197 | 8.97x | 0.480 | 0.693 | 0.577 |
| IVF nprobe=32 | 100 | 0.929 | 6.1962 | 5.82x | 0.495 | 0.717 | 0.596 |
| IVF nprobe=32 | 200 | 0.966 | 10.8834 | 3.31x | 0.502 | 0.725 | 0.605 |
| IVF nprobe=32 | 500 | 0.980 | 24.9764 | 1.44x | 0.505 | 0.725 | 0.606 |

## 结论

- FAISS Flat top-200 基本复现 sklearn exact NN / batched top-N 的准确率，是当前 exact vector index upper-bound。
- IVF nprobe=8 查询阶段最快，但 candidate gold recall 从 0.977 降到 0.901，导致 MRR 从 0.612 降到 0.571。
- IVF nprobe=32 接近 exact recall，MRR 回升到 0.605，但在 LoCoMo10 当前规模下查询阶段并不比 Flat 更快。
- 论文中可以将 FAISS Flat 作为可复现 exact index baseline，将 IVF8/IVF32 作为 ANN 速度-召回折中实验，并说明当前数据规模较小，ANN 优势需要在更大 memory bank 上进一步验证。
