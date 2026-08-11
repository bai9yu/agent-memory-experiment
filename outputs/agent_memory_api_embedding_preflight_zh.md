# API Embedding Baseline Preflight

本文件是外部 embedding baseline 的跑前门禁。它不联网、不调用 provider、不打印 API key，只检查本地输入、环境变量、缓存和目标结果是否处于可运行状态。

## 总览

- Provider label: `OpenAI text-embedding-3-small`
- Model: `text-embedding-3-small`
- Base URL: `https://api.openai.com/v1`
- Required checks: 4/5
- Ready to run paid/API baseline: False
- Input items: 4355
- Approx tokens: 71882
- API batches still needed if cache is unchanged: 35
- Existing result summary satisfies method: False

## 环境

- Env file: `.env`
- Env file exists: True
- Loaded key names: DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
- Required key name: `OPENAI_API_KEY`

## 检查明细

| Check | Pass | Severity | Evidence |
| --- | --- | --- | --- |
| memories file exists | True | required | work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl |
| queries file exists | True | required | work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl |
| memory rows available | True | required | 2517 |
| query rows available | True | required | 1838 |
| api key available | False | required | OPENAI_API_KEY set=False |
| embedding cache dir parent exists | True | optional | work/agent_memory_experiment/cache/embeddings |
| memory cache exists | False | optional | work/agent_memory_experiment/cache/embeddings/api/text-embedding-3-small/memories_c34fdc2deb14403f24e1c232339215988d75a771e362b02264503b2bf98501bf.npz |
| query cache exists | False | optional | work/agent_memory_experiment/cache/embeddings/api/text-embedding-3-small/queries_4fbbb2a49a5a46e96bbf61c51d82f0e68830c1a3e3f49c889c60c38b99d7792c.npz |
| result summary exists | False | optional | work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004/summary.csv |
| result summary has method | False | optional | type_aware |

## 下一步

- 先修复未通过的 required check；当前不建议启动付费/API baseline。
- 首次运行后会写入 embedding cache；之后重复实验应优先命中缓存。
