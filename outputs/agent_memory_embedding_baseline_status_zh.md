# 外部 Embedding Baseline 状态

本文件记录外部 embedding baseline 的接入与运行状态。它只检查环境变量是否存在，不读取、不打印 API key。

| Label | Provider | Model | Key Env | Key Available | Status | Method | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI text-embedding-3-small | OpenAI-compatible embeddings API | text-embedding-3-small | OPENAI_API_KEY | False | pending_api_key | type_aware | OPENAI_API_KEY is not set; summary.csv not found |

## 跑前规模预估

- `outputs/agent_memory_api_embedding_run_estimate_zh.md` 记录当前 LoCoMo10 外部 embedding baseline 的文本数量、近似 token、批次数和缓存状态。

## 推荐运行命令

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004 \
  --semantic-backend api \
  --api-embedding-model text-embedding-3-small \
  --api-embedding-base-url https://api.openai.com/v1 \
  --api-key-env OPENAI_API_KEY \
  --api-embedding-batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --half-life-days 30 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3 \
  --importance-weight 0.06 \
  --type-awareness-weight 0.04 \
  --rank-output-k 20
```

## 论文使用判断

- 当前只能说明外部 embedding baseline 已具备接入和缓存框架；在实际跑完前，不能作为实验结果写入主表。
