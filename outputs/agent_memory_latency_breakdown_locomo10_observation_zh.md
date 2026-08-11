# Retrieval Latency Breakdown

## Run Meta

| Variant | Memories | Queries | Methods | Total Seconds | ms / Query | ms / Query-Method |
|---|---:|---:|---:|---:|---:|---:|
| locomo_observation | 2507 | 1638 | 5 | 33.5125 | 20.46 | 4.09 |

## Stage Breakdown

| Variant | Stage | Seconds | Share | ms / Query |
|---|---|---:|---:|---:|
| locomo_observation | load_data | 0.0268 | 0.001 | 0.02 |
| locomo_observation | feature_prep | 0.0586 | 0.002 | 0.04 |
| locomo_observation | semantic_scorer_init | 4.2494 | 0.127 | 2.59 |
| locomo_observation | query_encoding | 0.0151 | 0.000 | 0.01 |
| locomo_observation | ranking_and_metrics | 29.1626 | 0.870 | 17.80 |
| locomo_observation | total | 33.5125 | 1.000 | 20.46 |

## Metrics Sanity Check

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.465 | 0.625 | 0.675 | 0.565 |
| keyword | 0.402 | 0.550 | 0.605 | 0.497 |
| time_aware | 0.483 | 0.639 | 0.703 | 0.583 |
| type_aware | 0.483 | 0.639 | 0.703 | 0.583 |
| vector | 0.471 | 0.625 | 0.679 | 0.567 |

说明：该报告测量离线评测链路的粗粒度耗时，包括本地 embedding cache 读取、query 编码、全量 memory 排序与指标计算。
它不是线上服务的严格单请求 latency，但可用于论文中的可复现实验效率分析。
