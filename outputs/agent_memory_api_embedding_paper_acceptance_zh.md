# API Embedding Paper Acceptance Gate

本文件是外部 API embedding baseline 的严格论文引用门禁。它不联网、不调用 provider、也不读取 API key；只检查真实运行后落到本地的结果是否覆盖完整 LoCoMo10 answerable slice，并且是否已生成与 BGE-M3 的完整 delta 表。

## 总览

- Provider profile source: `outputs/agent_memory_embedding_provider_profiles.csv`
- Query source: `work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl`
- Expected rank_output_k: 20
- Providers checked: 2
- Accepted for paper: 0
- Partial/failed local results: 0
- Ready to cite external embedding baseline: False

## 明细

| Label | Status | Summary Queries | Metrics OK | Per-Query Rows | Ranking Rows | Comparison | Missing Files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI text-embedding-3-small | pending_api_run | 0/1838 | False | 0/1838 | 0/36760 | False | summary.csv;summary_by_type.csv;per_query_metrics.csv;rankings.csv |
| Generic OpenAI-compatible embedding | pending_api_run | 0/1838 | False | 0/1838 | 0/36760 | False | summary.csv;summary_by_type.csv;per_query_metrics.csv;rankings.csv |

## Acceptance Rules

- `summary.csv` 必须包含目标 method，且 `num_queries` 等于当前 answerable query 数。
- `recall@1/3/5` 和 `mrr` 必须能解析为 `[0, 1]` 区间内的数值。
- `per_query_metrics.csv` 中目标 method 的行数必须等于 query 数。
- `rankings.csv` 中目标 method 的行数必须等于 `query 数 * rank_output_k`。
- `summary_by_type.csv` 必须覆盖 LoCoMo query type 1-5。
- `summary.csv` 必须保留 vector/keyword/hybrid/time_aware/type_aware 方法，防止只跑单一不完整配置。
- comparison 表必须包含 4 个核心指标且状态为 completed。

## 论文使用边界

- 当前没有 provider 通过严格论文引用门禁；只能写接入协议、费用估计和跑后验收流程已经准备好。
