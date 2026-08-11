# API Embedding Post-Run Gate

本文件检查外部 API embedding baseline 跑完之后，结果是否足够进入论文对照表。它不联网、不调用 provider，也不读取 API key；只检查本地结果文件和 comparison 表。

## 总览

- Provider profile source: `outputs/agent_memory_embedding_provider_profiles.csv`
- Provider profiles checked: 2
- Completed for paper: 0
- Partial results: 0
- Ready to cite external embedding baseline: False

## 明细

| Label | Model | Dimensions | Status | Summary Metrics OK | Result Files OK | Comparison Completed | Missing Files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI text-embedding-3-small | text-embedding-3-small | 0 | pending_api_run | False | False | False | summary.csv;summary_by_type.csv;per_query_metrics.csv;rankings.csv |
| Generic OpenAI-compatible embedding | provider_embedding_model | 0 | pending_api_run | False | False | False | summary.csv;summary_by_type.csv;per_query_metrics.csv;rankings.csv |

## 判定规则

- `summary.csv` 中必须存在目标 method，并且 `recall@1/3/5`、`mrr` 可以解析为数值。
- `summary.csv`、`summary_by_type.csv`、`per_query_metrics.csv`、`rankings.csv` 必须同时存在。
- 必须已经生成相对 BGE-M3 的 completed comparison 表。

## 论文使用边界

- 当前还不能把外部 embedding baseline 写成已完成结果；只能写接入链路和跑后验收门禁已经准备好。
