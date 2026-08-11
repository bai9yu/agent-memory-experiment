# FAISS Scale Stress Test

本实验是 index-only stress test：在 LoCoMo10 的真实 BGE-M3 memory/query embedding 基础上，加入轻微扰动的 synthetic distractor vectors 扩展 memory bank，比较 FAISS Flat 与 IVF 的候选召回速度和 gold recall。
该实验不重新执行 type-aware reranking，因此用于支持论文中的索引扩展性分析，不替代主检索准确率实验。

## Setting

- Base memories: `2517`
- Queries: `1838`
- Embedding model: `BAAI/bge-m3`
- Target memory sizes: `2517,10000,25000,50000`
- Top-k: `200`
- Distractor noise std: `0.03`

## Results

| Memory Bank | Index | nlist | nprobe | Query Seconds | ms / Query | Candidate Gold Recall | Train Seconds | Add Seconds |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2517 | flat | 0 | 0 | 0.0595 | 0.032 | 0.977 | 0.0000 | 0.0012 |
| 2517 | ivf | 128 | 8 | 0.0341 | 0.019 | 0.862 | 0.0105 | 0.0018 |
| 2517 | ivf | 128 | 32 | 0.1006 | 0.055 | 0.950 | 0.0104 | 0.0016 |
| 10000 | flat | 0 | 0 | 0.0792 | 0.043 | 0.973 | 0.0000 | 0.0038 |
| 10000 | ivf | 128 | 8 | 0.1564 | 0.085 | 0.881 | 0.0430 | 0.0088 |
| 10000 | ivf | 128 | 32 | 0.6455 | 0.351 | 0.964 | 0.0432 | 0.0074 |
| 25000 | flat | 0 | 0 | 0.1290 | 0.070 | 0.964 | 0.0000 | 0.0099 |
| 25000 | ivf | 128 | 8 | 0.2852 | 0.155 | 0.872 | 0.1084 | 0.0236 |
| 25000 | ivf | 128 | 32 | 1.1317 | 0.616 | 0.950 | 0.1223 | 0.0203 |
| 50000 | flat | 0 | 0 | 0.1993 | 0.108 | 0.958 | 0.0000 | 0.0464 |
| 50000 | ivf | 128 | 8 | 0.4901 | 0.267 | 0.862 | 0.1544 | 0.0438 |
| 50000 | ivf | 128 | 32 | 1.9144 | 1.042 | 0.941 | 0.1548 | 0.0387 |

## Interpretation

- Flat index 是 exact upper-bound，candidate gold recall 通常最高，但查询成本随 memory bank 线性增长。
- IVF 是真正 ANN；在更大 memory bank 中应优先观察 query seconds 是否低于 Flat，以及 candidate gold recall 是否保持在可接受范围。
- 如果 IVF recall 明显下降，应提高 `nprobe`、增大 candidate top-k，或换 HNSW/IVF-PQ 等索引配置。

## 100k Additional Probe

进一步使用 100k memory bank 和 `nlist=512` 测试 IVF 参数：

| Memory Bank | Index | nlist | nprobe | Query Seconds | ms / Query | Candidate Gold Recall | Train Seconds | Add Seconds |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 100000 | flat | 0 | 0 | 0.3602 | 0.196 | 0.952 | 0.0000 | 0.0897 |
| 100000 | ivf | 512 | 4 | 0.1990 | 0.108 | 0.737 | 0.9946 | 0.2004 |
| 100000 | ivf | 512 | 16 | 0.5551 | 0.302 | 0.845 | 1.0267 | 0.1443 |
| 100000 | ivf | 512 | 64 | 2.0774 | 1.130 | 0.941 | 1.0369 | 0.1405 |

100k 规模下，IVF nprobe=4 开始显示查询速度优势，但 candidate gold recall 下降明显；nprobe=64 接近 Flat recall，但查询慢于 Flat。因此当前结论是：FAISS IVF 已形成可报告的 ANN 折中曲线，但若要在论文中展示“高召回且明显快于 Flat”，还需要更大 memory bank、HNSW，或 IVF-PQ/压缩索引。
