# LoCoMo10 成本与延迟分析

## API Token 成本

- API sessions：`269`
- Prompt tokens：`361103`
- Completion tokens：`198471`
- Total tokens：`559574`
- 货币成本：未计算货币成本；如需估算，请传入 input/output 每百万 token 单价。

## Memory Storage

| Variant | Memories | Memory Tokens | Avg Tokens / Memory |
|---|---:|---:|---:|
| llm_extracted_fact | 2517 | 31148 | 12.38 |
| locomo_observation | 2507 | 40241 | 16.05 |

DeepSeek extracted fact 的 memory token 是 LoCoMo observation 的 `0.774`，约节省 `22.6%` memory storage tokens。

## Runtime

| Variant | Runtime Seconds | Queries | Memories | Methods | ms / Query | ms / Query-Method |
|---|---:|---:|---:|---:|---:|---:|
| llm_extracted_fact | 44.6335 | 1838 | 2517 | 5 | 24.28 | 4.86 |
| locomo_observation | 40.8617 | 1638 | 2507 | 5 | 24.95 | 4.99 |

说明：runtime 是 `memory_eval.py` 的端到端离线评测时间，包含本地模型/缓存读取、编码、排序和写出结果，不等同于线上服务单 query latency。

## Latency Breakdown

| Variant | Main Bottleneck | Ranking Share | Scorer Init Seconds | Query Encoding Seconds |
|---|---|---:|---:|---:|
| llm_extracted_fact | ranking_and_metrics | 0.879 | 4.2435 | 0.0167 |
| locomo_observation | ranking_and_metrics | 0.870 | 4.2494 | 0.0151 |

细粒度结果见 `outputs/agent_memory_latency_breakdown_locomo10_zh.md`。当前瓶颈主要是 full-memory ranking，而不是 BGE-M3 query encoding。

## Candidate Prefiltering

| Candidate Limit | Runtime Seconds | Speedup vs Full Ranking | Recall@1 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|---:|
| full | 36.0491 | 1.00x | 0.503 | 0.733 | 0.609 |
| 50 | 6.2673 | 5.75x | 0.482 | 0.694 | 0.579 |
| 100 | 8.3394 | 4.32x | 0.497 | 0.724 | 0.600 |
| 200 | 13.4028 | 2.69x | 0.509 | 0.733 | 0.613 |
| 500 | 28.6656 | 1.26x | 0.507 | 0.736 | 0.611 |

top-200 在当前离线实验中取得较好的效率-准确率折中：相比 full ranking 快约 2.69x，MRR 略高。后续如果接入向量索引，可把 semantic top-N 的全量打分进一步替换为近似检索。

## Indexed Candidate Prefiltering

进一步使用 batched dense similarity matrix 进行 exact top-N 候选召回：

| Candidate Limit | End-to-End Seconds | Speedup vs Full Ranking | Recall@1 | Recall@5 | MRR |
|---:|---:|---:|---:|---:|---:|
| 50 | 4.0470 | 8.91x | 0.482 | 0.695 | 0.579 |
| 100 | 7.2054 | 5.00x | 0.497 | 0.724 | 0.600 |
| 200 | 11.3399 | 3.18x | 0.509 | 0.733 | 0.613 |
| 500 | 24.4946 | 1.47x | 0.507 | 0.737 | 0.612 |

batched top-N 的候选召回阶段耗时为 0.2920 秒，约 0.16 ms/query。top-200 仍是当前最佳效率-准确率折中点。

## Vector Index Baselines

进一步加入两个索引基线：

- `sklearn NearestNeighbors`：BGE-M3 dense embedding + exact NN index，作为可复现的标准向量索引对照。
- `LSH`：hash embedding + random-hyperplane LSH，作为无需额外依赖的 ANN-style 弱基线。

| Index | Candidate Limit | End-to-End Seconds | Speedup vs Full Ranking | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| sklearn NN | 50 | 3.8927 | 9.26x | 0.482 | 0.695 | 0.579 |
| sklearn NN | 100 | 5.9548 | 6.05x | 0.498 | 0.724 | 0.600 |
| sklearn NN | 200 | 10.4359 | 3.45x | 0.509 | 0.734 | 0.613 |
| sklearn NN | 500 | 23.6075 | 1.53x | 0.507 | 0.737 | 0.612 |
| LSH | 50 | 8.1510 | 4.42x | 0.385 | 0.553 | 0.458 |
| LSH | 100 | 11.0660 | 3.26x | 0.393 | 0.561 | 0.470 |
| LSH | 200 | 16.7249 | 2.16x | 0.389 | 0.572 | 0.471 |
| LSH | 500 | 33.4633 | 1.08x | 0.388 | 0.568 | 0.472 |

sklearn NN top-200 是当前最合适的效率-准确率折中：MRR 0.613，Recall@5 0.734，端到端加速 3.45x。LSH 的召回质量明显较低，说明近似索引实验必须和强 embedding 结合，后续应加入 BGE-M3 + FAISS/HNSW。

## Accuracy-Cost Tradeoff

| Variant | Method | Recall@1 | Recall@5 | MRR |
|---|---|---:|---:|---:|
| llm_extracted_fact | keyword | 0.428 | 0.634 | 0.526 |
| llm_extracted_fact | vector | 0.419 | 0.643 | 0.527 |
| llm_extracted_fact | hybrid | 0.477 | 0.705 | 0.583 |
| llm_extracted_fact | time_aware | 0.499 | 0.727 | 0.605 |
| llm_extracted_fact | type_aware | 0.503 | 0.733 | 0.609 |
| locomo_observation | keyword | 0.402 | 0.605 | 0.497 |
| locomo_observation | vector | 0.471 | 0.679 | 0.567 |
| locomo_observation | hybrid | 0.465 | 0.675 | 0.565 |
| locomo_observation | time_aware | 0.483 | 0.703 | 0.583 |
| locomo_observation | type_aware | 0.483 | 0.703 | 0.583 |

## 结论

- DeepSeek 抽取带来一次性 API 成本，但生成的 fact-level memory 比 observation 更短。
- type-aware 的准确率最高，但 runtime 与 time-aware 基本同阶，因为只增加轻量规则匹配。
- keyword/vector 单独使用成本低但准确率明显弱于 hybrid/time-aware/type-aware。
- 若面向在线系统，应进一步拆分 embedding 编码时间、候选召回时间和重排时间。
- 细粒度 latency breakdown 显示，下一步效率优化应优先做候选预筛选或向量索引，减少全量 memory 排序成本。
- indexed candidate prefiltering 显示，top-200 可在 MRR 不降的情况下取得约 3.18x 端到端加速。
