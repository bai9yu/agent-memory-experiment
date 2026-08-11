# LoCoMo10 细粒度延迟分解

## 实验设置

- 数据：LoCoMo10 answerable slice
- Embedding：本地 `BAAI/bge-m3`
- 方法数：5，包含 `keyword`、`vector`、`hybrid`、`time_aware`、`type_aware`
- 说明：该实验测量离线评测链路耗时，不等同于线上服务单请求 latency。

## Run Meta

| Variant | Memories | Queries | Methods | Total Seconds | ms / Query | ms / Query-Method |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact | 2517 | 1838 | 5 | 36.0491 | 19.61 | 3.92 |
| LoCoMo observation | 2507 | 1638 | 5 | 33.5125 | 20.46 | 4.09 |

## Stage Breakdown

| Variant | Stage | Seconds | Share | ms / Query |
|---|---|---:|---:|---:|
| DeepSeek extracted fact | load_data | 0.0301 | 0.001 | 0.02 |
| DeepSeek extracted fact | feature_prep | 0.0576 | 0.002 | 0.03 |
| DeepSeek extracted fact | semantic_scorer_init | 4.2435 | 0.118 | 2.31 |
| DeepSeek extracted fact | query_encoding | 0.0167 | 0.000 | 0.01 |
| DeepSeek extracted fact | ranking_and_metrics | 31.7012 | 0.879 | 17.25 |
| LoCoMo observation | load_data | 0.0268 | 0.001 | 0.02 |
| LoCoMo observation | feature_prep | 0.0586 | 0.002 | 0.04 |
| LoCoMo observation | semantic_scorer_init | 4.2494 | 0.127 | 2.59 |
| LoCoMo observation | query_encoding | 0.0151 | 0.000 | 0.01 |
| LoCoMo observation | ranking_and_metrics | 29.1626 | 0.870 | 17.80 |

## 结论

- 离线评测的主要耗时来自 full-memory ranking 与 metrics，占总耗时约 87%-88%。
- BGE-M3 scorer 初始化与 embedding cache 读取约 4.25 秒，占 12%左右。
- query encoding 几乎不构成瓶颈，因为当前运行复用了本地 embedding cache。
- DeepSeek extracted fact 的 memory 更多、query 更多，但 ms/query 略低于 observation，说明 memory 文本更短可能抵消了部分候选规模成本。
- 如果面向线上系统，下一步应实现候选预筛选或向量索引，避免每个 query 对全部 memory 做全量排序。
