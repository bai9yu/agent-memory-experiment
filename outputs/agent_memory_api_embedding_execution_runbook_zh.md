# API Embedding Execution Runbook

本文件把外部 API embedding baseline 的真实运行路径整理成可执行 runbook。它不联网、不读取 API key 内容，也不会自动启动付费调用；目标是在拿到 key 后按同一顺序关闭 external embedding blocker。

## 总览

- Providers: 2
- Paid/network steps listed: 2
- Providers completed for paper: 0
- Offline refresh starts paid run: False

## Step Matrix

| Provider | Step | Phase | Current Pass | Evidence | Acceptance |
| --- | --- | --- | --- | --- | --- |
| OpenAI text-embedding-3-small | 1_configure_key | manual | False | OPENAI_API_KEY available=False | Store the provider key in .env or shell; never commit the key. |
| OpenAI text-embedding-3-small | 2_preflight | offline_check | False | default preflight required=4/5; provider key available=False | All required preflight checks pass before any paid/network API call. |
| OpenAI text-embedding-3-small | 3_cost_and_cache_estimate | offline_check | True | memories: items=2517, tokens=45429, batches=20, cache_exists=False; queries: items=1838, tokens=26453, batches=15, cache_exists=False | Review item count, approximate tokens, uncached batches, and expected cache reuse. |
| OpenAI text-embedding-3-small | 4_real_api_run | network_paid_run | False | intentionally not run by offline refresh | Run only after preflight passes and expected cost/cache behavior is acceptable. |
| OpenAI text-embedding-3-small | 5_compare_with_bge_m3 | offline_after_run | False | requires provider summary.csv from real API run | Generate numeric delta table versus BGE-M3 after summary.csv exists. |
| OpenAI text-embedding-3-small | 6_postrun_gate | offline_after_run | False | completed_for_paper=0 | Post-run gate and paper acceptance gate must report at least one provider completed/accepted for paper. |
| OpenAI text-embedding-3-small | 7_final_refresh | offline_after_run | False | run after external baseline and comparison are complete | Refresh evidence matrix, manuscript, claim checks, reproducibility, freshness, and submission readiness. |
| Generic OpenAI-compatible embedding | 1_configure_key | manual | False | EXTERNAL_EMBEDDING_API_KEY available=False | Store the provider key in .env or shell; never commit the key. |
| Generic OpenAI-compatible embedding | 2_preflight | offline_check | False | default preflight required=4/5; provider key available=False | All required preflight checks pass before any paid/network API call. |
| Generic OpenAI-compatible embedding | 3_cost_and_cache_estimate | offline_check | True | memories: items=2517, tokens=45429, batches=20, cache_exists=False; queries: items=1838, tokens=26453, batches=15, cache_exists=False | Review item count, approximate tokens, uncached batches, and expected cache reuse. |
| Generic OpenAI-compatible embedding | 4_real_api_run | network_paid_run | False | intentionally not run by offline refresh | Run only after preflight passes and expected cost/cache behavior is acceptable. |
| Generic OpenAI-compatible embedding | 5_compare_with_bge_m3 | offline_after_run | False | requires provider summary.csv from real API run | Generate numeric delta table versus BGE-M3 after summary.csv exists. |
| Generic OpenAI-compatible embedding | 6_postrun_gate | offline_after_run | False | completed_for_paper=0 | Post-run gate and paper acceptance gate must report at least one provider completed/accepted for paper. |
| Generic OpenAI-compatible embedding | 7_final_refresh | offline_after_run | False | run after external baseline and comparison are complete | Refresh evidence matrix, manuscript, claim checks, reproducibility, freshness, and submission readiness. |

## 使用方式

1. 选择一个 provider。
2. 完成 `1_configure_key`，确保 key 只在 `.env` 或 shell 中，不进入 Git。
3. 运行 `2_preflight` 和 `3_cost_and_cache_estimate`。
4. 只有 preflight 全部通过、费用/缓存可接受时，才运行 `4_real_api_run`。
5. 跑完后依次运行 compare、postrun gate、paper acceptance gate 和 final refresh。

## 命令附录

以下命令来自 runbook CSV 的 `command` 字段；复制前先确认 provider、模型、费用和缓存目录。`4_real_api_run` 是唯一会触发真实网络/付费 embedding 调用的步骤。

### OpenAI text-embedding-3-small

#### 1_configure_key (manual)

```bash
Set the OPENAI_API_KEY environment variable in .env or shell.
```

#### 2_preflight (offline_check)

```bash
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
  --output-csv outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_preflight.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_preflight_zh.md
```

#### 3_cost_and_cache_estimate (offline_check)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --model "text-embedding-3-small" \
  --base-url "https://api.openai.com/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --output-csv outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_run_estimate.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_run_estimate_zh.md
```

#### 4_real_api_run (network_paid_run)

```bash
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

#### 5_compare_with_bge_m3 (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py \
  --bge-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv \
  --api-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004/summary.csv \
  --method type_aware \
  --api-label "OpenAI text-embedding-3-small" \
  --output-csv outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_comparison.csv \
  --output-report outputs/agent_memory_api_embedding_1_openai_text_embedding_3_small_comparison_zh.md
```

#### 6_postrun_gate (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_api_embedding_postrun.py \
  --profile-csv outputs/agent_memory_embedding_provider_profiles.csv \
  --outputs-dir outputs \
  --output-csv outputs/agent_memory_api_embedding_postrun_gate.csv \
  --output-report outputs/agent_memory_api_embedding_postrun_gate_zh.md

work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_api_embedding_paper_acceptance.py \
  --profile-csv outputs/agent_memory_embedding_provider_profiles.csv \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --outputs-dir outputs \
  --rank-output-k 20 \
  --output-csv outputs/agent_memory_api_embedding_paper_acceptance.csv \
  --output-report outputs/agent_memory_api_embedding_paper_acceptance_zh.md
```

#### 7_final_refresh (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/refresh_paper_artifacts.py \
  --project-root . \
  --output-csv outputs/agent_memory_paper_artifact_refresh_run.csv \
  --output-report outputs/agent_memory_paper_artifact_refresh_run_zh.md
```

### Generic OpenAI-compatible embedding

#### 1_configure_key (manual)

```bash
Set the EXTERNAL_EMBEDDING_API_KEY environment variable in .env or shell.
```

#### 2_preflight (offline_check)

```bash
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
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_preflight.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_preflight_zh.md
```

#### 3_cost_and_cache_estimate (offline_check)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --model "provider_embedding_model" \
  --base-url "https://provider.example/v1" \
  --dimensions 0 \
  --batch-size 128 \
  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_run_estimate.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_run_estimate_zh.md
```

#### 4_real_api_run (network_paid_run)

```bash
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

#### 5_compare_with_bge_m3 (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py \
  --bge-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv \
  --api-summary work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_provider_embedding_model_type_004/summary.csv \
  --method type_aware \
  --api-label "Generic OpenAI-compatible embedding" \
  --output-csv outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_comparison.csv \
  --output-report outputs/agent_memory_api_embedding_2_generic_openai_compatible_embedding_comparison_zh.md
```

#### 6_postrun_gate (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_api_embedding_postrun.py \
  --profile-csv outputs/agent_memory_embedding_provider_profiles.csv \
  --outputs-dir outputs \
  --output-csv outputs/agent_memory_api_embedding_postrun_gate.csv \
  --output-report outputs/agent_memory_api_embedding_postrun_gate_zh.md

work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_api_embedding_paper_acceptance.py \
  --profile-csv outputs/agent_memory_embedding_provider_profiles.csv \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --outputs-dir outputs \
  --rank-output-k 20 \
  --output-csv outputs/agent_memory_api_embedding_paper_acceptance.csv \
  --output-report outputs/agent_memory_api_embedding_paper_acceptance_zh.md
```

#### 7_final_refresh (offline_after_run)

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/refresh_paper_artifacts.py \
  --project-root . \
  --output-csv outputs/agent_memory_paper_artifact_refresh_run.csv \
  --output-report outputs/agent_memory_paper_artifact_refresh_run_zh.md
```

## 论文使用边界

- 可以写：外部 embedding baseline 的真实运行和验收路径已经固定，且离线刷新不会误触发付费 API。
- 不能写：runbook 生成完成就等于外部 embedding baseline 已完成；最终仍以 postrun gate completed_for_paper 和 paper acceptance accepted_for_paper 为准。
