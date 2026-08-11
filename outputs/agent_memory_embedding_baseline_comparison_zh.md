# Embedding Baseline 对比报告

本文件用于比较本地 BGE-M3 主结果与外部 API embedding baseline。它只读取本地 summary.csv，不发起网络请求。

## 输入

- BGE-M3 summary: `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv`
- API embedding summary: `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004/summary.csv`
- Method: `type_aware`

## 指标对比

| Metric | BGE-M3 | API Embedding | Delta | Status |
| --- | --- | --- | --- | --- |
| recall@1 | 0.5033 | pending | pending | pending_api_result |
| recall@3 | 0.6703 | pending | pending | pending_api_result |
| recall@5 | 0.7334 | pending | pending | pending_api_result |
| mrr | 0.6094 | pending | pending | pending_api_result |

## 论文使用判断

- API embedding baseline 尚未生成 summary.csv；当前只能说明对比框架已准备好，不能写入主结果。
