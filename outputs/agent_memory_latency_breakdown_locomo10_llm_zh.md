# Retrieval Latency Breakdown

## Run Meta

| Variant | Memories | Queries | Methods | Total Seconds | ms / Query | ms / Query-Method |
|---|---:|---:|---:|---:|---:|---:|
| llm_extracted_fact | 2517 | 1838 | 5 | 36.0491 | 19.61 | 3.92 |

## Stage Breakdown

| Variant | Stage | Seconds | Share | ms / Query |
|---|---|---:|---:|---:|
| llm_extracted_fact | load_data | 0.0301 | 0.001 | 0.02 |
| llm_extracted_fact | feature_prep | 0.0576 | 0.002 | 0.03 |
| llm_extracted_fact | semantic_scorer_init | 4.2435 | 0.118 | 2.31 |
| llm_extracted_fact | query_encoding | 0.0167 | 0.000 | 0.01 |
| llm_extracted_fact | ranking_and_metrics | 31.7012 | 0.879 | 17.25 |
| llm_extracted_fact | total | 36.0491 | 1.000 | 19.61 |

## Metrics Sanity Check

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.477 | 0.647 | 0.705 | 0.583 |
| keyword | 0.428 | 0.581 | 0.634 | 0.526 |
| time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| vector | 0.419 | 0.585 | 0.643 | 0.527 |

说明：该报告测量离线评测链路的粗粒度耗时，包括本地 embedding cache 读取、query 编码、全量 memory 排序与指标计算。
它不是线上服务的严格单请求 latency，但可用于论文中的可复现实验效率分析。
