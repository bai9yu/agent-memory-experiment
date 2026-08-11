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
