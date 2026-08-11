# 外部 Embedding Provider Profiles

本文件把外部 embedding baseline 的 provider 配置、跑前检查、真实运行和结果对比命令集中到一处。它不联网、不读取 API key 内容，只根据环境变量是否存在给出可执行状态。

## Provider 概览

| Label | Model | Base URL | Dimensions | Key Env | Key Available | Status | Result Dir |
|---|---|---|---:|---|---:|---|---|
| OpenAI text-embedding-3-small | `text-embedding-3-small` | `https://api.openai.com/v1` | 0 | `OPENAI_API_KEY` | False | pending_api_key | `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004` |
| Generic OpenAI-compatible embedding | `provider_embedding_model` | `https://provider.example/v1` | 0 | `EXTERNAL_EMBEDDING_API_KEY` | False | pending_api_key | `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_provider_embedding_model_type_004` |

## 使用顺序

1. 在 `.env` 中配置其中一个 provider 的 key/model/base URL；如 provider 支持指定维度，可配置 `OPENAI_EMBEDDING_DIMENSIONS` 或 `EXTERNAL_EMBEDDING_DIMENSIONS`。
2. 先运行该 provider 的 preflight，确认 required checks 全部通过。
3. 运行真实 API embedding baseline；首次运行会产生外部 API 调用和费用，之后应命中 embedding cache。
4. 运行 compare 命令，生成相对 BGE-M3 的 delta 表，再重跑 evidence/readiness gate。

## 1. OpenAI text-embedding-3-small

### Preflight

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/preflight_api_embedding_baseline.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --result-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004 \
  --method type_aware \
  --provider-label "OpenAI text-embedding-3-small" \
  --model "text-embedding-3-small" \
  --base-url "https://api.openai.com/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --api-key-env OPENAI_API_KEY \
  --env-file .env \
  --output-csv outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_preflight.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_preflight_zh.md
```

### Estimate

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --model "text-embedding-3-small" \
  --base-url "https://api.openai.com/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --output-csv outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_run_estimate.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_run_estimate_zh.md
```

### Run

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004 \
  --semantic-backend api \
  --api-embedding-model "text-embedding-3-small" \
  --api-embedding-base-url "https://api.openai.com/v1" \
  --api-key-env OPENAI_API_KEY \
  --env-file .env \
  --api-embedding-batch-size 128 \
  --api-embedding-dimensions 0 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --half-life-days 30 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3 \
  --importance-weight 0.06 \
  --type-awareness-weight 0.04 \
  --rank-output-k 20
```

### Compare With BGE-M3

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py \
  --bge-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv \
  --api-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004/summary.csv \
  --method type_aware \
  --api-label "OpenAI text-embedding-3-small" \
  --output-csv outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_comparison.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text-embedding-3-small_comparison_zh.md
```

## 2. Generic OpenAI-compatible embedding

### Preflight

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/preflight_api_embedding_baseline.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --result-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_provider_embedding_model_type_004 \
  --method type_aware \
  --provider-label "Generic OpenAI-compatible embedding" \
  --model "provider_embedding_model" \
  --base-url "https://provider.example/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --api-key-env EXTERNAL_EMBEDDING_API_KEY \
  --env-file .env \
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_preflight.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_preflight_zh.md
```

### Estimate

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --model "provider_embedding_model" \
  --base-url "https://provider.example/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_run_estimate.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_run_estimate_zh.md
```

### Run

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_provider_embedding_model_type_004 \
  --semantic-backend api \
  --api-embedding-model "provider_embedding_model" \
  --api-embedding-base-url "https://provider.example/v1" \
  --api-key-env EXTERNAL_EMBEDDING_API_KEY \
  --env-file .env \
  --api-embedding-batch-size 128 \
  --api-embedding-dimensions 0 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --half-life-days 30 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3 \
  --importance-weight 0.06 \
  --type-awareness-weight 0.04 \
  --rank-output-k 20
```

### Compare With BGE-M3

```bash
PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py \
  --bge-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv \
  --api-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_provider_embedding_model_type_004/summary.csv \
  --method type_aware \
  --api-label "Generic OpenAI-compatible embedding" \
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_comparison.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai-compatible_embedding_comparison_zh.md
```

## 论文使用判断

- 只要任一 provider 生成 `summary.csv` 并完成 compare，就可以作为外部 embedding baseline 写入对照实验。
- 在 summary 生成前，本文件只能证明 provider 接入路径清楚，不能替代真实 baseline 结果。
