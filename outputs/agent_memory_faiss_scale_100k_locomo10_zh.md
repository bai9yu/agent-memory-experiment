# FAISS Scale Stress Test

本实验是 index-only stress test：在 LoCoMo10 的真实 BGE-M3 memory/query embedding 基础上，加入轻微扰动的 synthetic distractor vectors 扩展 memory bank，比较 FAISS Flat 与 IVF 的候选召回速度和 gold recall。
该实验不重新执行 type-aware reranking，因此用于支持论文中的索引扩展性分析，不替代主检索准确率实验。

## Setting

- Base memories: `2517`
- Queries: `1838`
- Embedding model: `BAAI/bge-m3`
- Target memory sizes: `100000`
- Top-k: `200`
- Distractor noise std: `0.03`

## Results

| Memory Bank | Index | nlist | nprobe | Query Seconds | ms / Query | Candidate Gold Recall | Train Seconds | Add Seconds |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 100000 | flat | 0 | 0 | 0.3602 | 0.196 | 0.952 | 0.0000 | 0.0897 |
| 100000 | ivf | 512 | 4 | 0.1990 | 0.108 | 0.737 | 0.9946 | 0.2004 |
| 100000 | ivf | 512 | 16 | 0.5551 | 0.302 | 0.845 | 1.0267 | 0.1443 |
| 100000 | ivf | 512 | 64 | 2.0774 | 1.130 | 0.941 | 1.0369 | 0.1405 |

## Interpretation

- Flat index 是 exact upper-bound，candidate gold recall 通常最高，但查询成本随 memory bank 线性增长。
- IVF 是真正 ANN；在更大 memory bank 中应优先观察 query seconds 是否低于 Flat，以及 candidate gold recall 是否保持在可接受范围。
- 如果 IVF recall 明显下降，应提高 `nprobe`、增大 candidate top-k，或换 HNSW/IVF-PQ 等索引配置。
