# Agent Memory Experiment

This folder contains the core code for an agent memory experiment framework. It supports long-conversation memory conversion, semantic retrieval, time-aware reranking, persona-aware reranking, importance-aware reranking, memory compression analysis, and cross-agent memory reuse evaluation.

## What It Implements

The retrieval module compares and combines three scoring families:

1. `vector`: semantic similarity, using either deterministic hash vectors or local sentence-transformer embeddings.
2. `hybrid`: semantic similarity + BM25 keyword matching + entity overlap.
3. `time_aware`: hybrid retrieval with adaptive recency gating, persona-aware reranking, and importance-aware reranking.

The main LoCoMo configuration uses local `BAAI/bge-m3` embeddings with:

- BGE-M3 embedding cache
- adaptive time-aware reranking
- persona gate for speaker/person disambiguation
- importance proxy for long-term preferences, relationships, identity, goals, plans, and emotional memories

The project also includes:

- a permissive long-conversation converter for LoCoMo-like JSON/JSONL files
- LoCoMo `observation` and `session_summary` compression builders
- DeepSeek-based fact-level memory extraction from raw dialogue sessions
- synthetic data generation for controlled retrieval, compression, and cross-agent tests
- aggregation scripts for Chinese experiment reports

## Run

```bash
python3 work/agent_memory_experiment/memory_eval.py
```

Outputs are written to:

- `work/agent_memory_experiment/results/sample_10/summary.csv`
- `work/agent_memory_experiment/results/sample_10/rankings.csv`
- `work/agent_memory_experiment/results/sample_10/report.md`
- `work/agent_memory_experiment/results/sample_10/summary_by_type.csv`
- `work/agent_memory_experiment/results/sample_10/per_query_metrics.csv`

## One-Command Pipeline

Run the retrieval pipeline:

```bash
python3 work/agent_memory_experiment/run_experiments.py
```

Run the full pipeline, including retrieval, compression, cross-agent reuse, aggregation, and the consolidated report:

```bash
python3 work/agent_memory_experiment/run_full_pipeline.py
```

The default semantic backend is dependency-free:

```bash
python3 work/agent_memory_experiment/run_experiments.py --semantic-backend hash
```

If `sentence-transformers` is installed, run the same pipeline with local BGE embeddings:

```bash
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/run_experiments.py \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-small-en-v1.5 \
  --embedding-batch-size 16 \
  --local-files-only
```

The default route does not require an online embedding API. Use BGE-small for a fast local check, then switch to BGE-M3 for the main LoCoMo run:

```bash
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_1_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_1_bge_small \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-small-en-v1.5 \
  --embedding-batch-size 16 \
  --local-files-only

HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_1_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_1_bge_m3 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only
```

Recommended LoCoMo run with BGE-M3 cache, persona-gated time-aware scoring, and importance proxy:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_all_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_all_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_all_bge_m3_importance_006 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 20 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4 \
  --importance-weight 0.06
```

Sentence-transformer embeddings are cached under `work/agent_memory_experiment/cache/embeddings/`, keyed by model name, ids, and text content.

Feature weights can be tuned from a candidate-level `rankings.csv` without re-encoding BGE-M3:

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/tune_memory_features_from_rankings.py \
  --rankings work/agent_memory_experiment/results/locomo_real_all_bge_m3_importance_006/rankings.csv \
  --output-csv outputs/agent_memory_feature_tuning_results.csv \
  --output-report outputs/agent_memory_feature_tuning_zh.md
```

By default this evaluates:

- `sample_10`
- `synthetic_100`
- `synthetic_300`
- `synthetic_500`

It also writes:

- `outputs/agent_memory_experiment_analysis.md`
- `outputs/agent_memory_experiment_trends.csv`
- `outputs/agent_memory_experiment_visualization.html`

The full pipeline additionally writes:

- `outputs/agent_memory_compression_analysis.md`
- `outputs/agent_memory_compression_results.csv`
- `outputs/agent_memory_cross_agent_analysis.md`
- `outputs/agent_memory_cross_agent_results.csv`
- `outputs/agent_memory_full_pipeline_report.md`

Chinese project notes:

- `outputs/agent_memory_current_design_zh.md`
- `outputs/agent_memory_open_source_research_zh.md`
- `outputs/agent_memory_experiment_retro_zh.md`
- `outputs/agent_memory_dataset_plan.md`

To include a LoCoMo-like input file in the same pipeline:

```bash
python3 work/agent_memory_experiment/run_experiments.py \
  --long-conversation-input path/to/locomo_or_long_conversation.json \
  --long-conversation-name locomo_first_10 \
  --max-long-records 10
```

## Generate Larger Synthetic Runs

```bash
python3 work/agent_memory_experiment/generate_synthetic_data.py --num-memories 100 --seed 7
python3 work/agent_memory_experiment/generate_synthetic_data.py --num-memories 300 --seed 11
```

Run evaluation on generated data:

```bash
python3 work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/synthetic_100_memories.jsonl \
  --queries work/agent_memory_experiment/data/synthetic_100_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/synthetic_100

python3 work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/synthetic_300_memories.jsonl \
  --queries work/agent_memory_experiment/data/synthetic_300_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/synthetic_300
```

Create a consolidated analysis report:

```bash
python3 work/agent_memory_experiment/compare_results.py \
  work/agent_memory_experiment/results/sample_10 \
  work/agent_memory_experiment/results/synthetic_100 \
  work/agent_memory_experiment/results/synthetic_300 \
  --output outputs/agent_memory_experiment_analysis.md
```

Create the offline visualization separately:

```bash
python3 work/agent_memory_experiment/visualize_results.py \
  --trend-csv outputs/agent_memory_experiment_trends.csv \
  --result-dirs \
  work/agent_memory_experiment/results/sample_10 \
  work/agent_memory_experiment/results/synthetic_100 \
  work/agent_memory_experiment/results/synthetic_300 \
  work/agent_memory_experiment/results/synthetic_500 \
  --output outputs/agent_memory_experiment_visualization.html
```

## Convert LoCoMo-Like Long Conversation Data

The converter accepts JSON or JSONL input and tries common field names such as:

- conversation containers: `sessions`, `conversation`, `dialogue`, `messages`, `turns`
- message text: `content`, `text`, `message`, `utterance`
- speaker fields: `speaker`, `role`, `agent_id`, `name`
- question containers: `qa`, `qas`, `questions`, `qa_pairs`
- evidence fields: `evidence`, `evidence_turns`, `supporting_turns`, `answer_memory_ids`

After downloading LoCoMo `data/locomo10.json` to `work/agent_memory_experiment/data/locomo10.json`, run the real-data pipeline:

```bash
python3 work/agent_memory_experiment/run_locomo_real.py
```

This writes:

- `work/agent_memory_experiment/data/locomo_real_all_memories.jsonl`
- `work/agent_memory_experiment/data/locomo_real_all_queries.jsonl`
- `work/agent_memory_experiment/results/locomo_real_all/`
- `outputs/agent_memory_locomo_real_report_zh.md`

To start with a smaller subset:

```bash
python3 work/agent_memory_experiment/run_locomo_real.py \
  --name locomo_real_1 \
  --max-records 1
```

Run the included sample:

```bash
python3 work/agent_memory_experiment/convert_long_conversation.py \
  --input work/agent_memory_experiment/data/locomo_like_sample.json \
  --output-prefix work/agent_memory_experiment/data/locomo_like_converted

python3 work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_like_converted_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_like_converted_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_like_sample
```

For a real dataset, start small:

```bash
python3 work/agent_memory_experiment/convert_long_conversation.py \
  --input path/to/locomo.json \
  --output-prefix work/agent_memory_experiment/data/locomo_first_10 \
  --max-records 10
```

## Memory Compression Experiments

Run raw/fact/summary compression experiments for one dataset:

```bash
python3 work/agent_memory_experiment/compression_experiment.py \
  --memories work/agent_memory_experiment/data/synthetic_100_memories.jsonl \
  --queries work/agent_memory_experiment/data/synthetic_100_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/compression_100
```

Aggregate multiple compression runs:

```bash
python3 work/agent_memory_experiment/compare_compression_results.py \
  work/agent_memory_experiment/results/compression_100 \
  work/agent_memory_experiment/results/compression_300 \
  work/agent_memory_experiment/results/compression_500 \
  --output outputs/agent_memory_compression_analysis.md \
  --csv-output outputs/agent_memory_compression_results.csv
```

Compression variants:

- `raw`: original memory records.
- `fact`: shorter fact-style records, preserving one record per source memory.
- `summary`: grouped records, five source memories per summary block by default.

Build LoCoMo official compression variants from `observation` and `session_summary`:

```bash
python3 work/agent_memory_experiment/build_locomo_compression_variants.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --raw-memories work/agent_memory_experiment/data/locomo_real_all_memories.jsonl \
  --output-dir work/agent_memory_experiment/data/locomo_compression_variants
```

Evaluate each LoCoMo compression variant with the recommended BGE-M3 configuration:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_compression_variants/observation/memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_compression_variants/observation/queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_compression_observation_bge_m3_importance_006 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 20 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4 \
  --importance-weight 0.06
```

Repeat the same command for `session_summary`, then aggregate:

```bash
python3 work/agent_memory_experiment/compare_locomo_compression_variants.py \
  --build-dir work/agent_memory_experiment/data/locomo_compression_variants \
  --raw-summary work/agent_memory_experiment/results/locomo_real_all_bge_m3_importance_006/summary.csv \
  --observation-summary work/agent_memory_experiment/results/locomo_compression_observation_bge_m3_importance_006/summary.csv \
  --session-summary work/agent_memory_experiment/results/locomo_compression_session_summary_bge_m3_importance_006/summary.csv \
  --output outputs/agent_memory_locomo_compression_real_zh.md \
  --csv-output outputs/agent_memory_locomo_compression_real_results.csv
```

## LLM Memory Extraction

Create a local `.env` file in the repository root:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

Run a small DeepSeek extraction job:

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3 \
  --max-records 1 \
  --max-sessions 1 \
  --temperature 0.1
```

Run the first full LoCoMo conversation with DeepSeek extraction:

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3 \
  --max-records 1 \
  --max-sessions 30 \
  --temperature 0.1
```

Run LoCoMo10 with resumable extraction:

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3 \
  --max-records 10 \
  --max-sessions 30 \
  --temperature 0.1 \
  --sleep-seconds 0.2 \
  --resume
```

Slice the result to the extracted LoCoMo session:

```bash
python3 work/agent_memory_experiment/filter_memory_eval_slice.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3/memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3/queries.jsonl \
  --output-prefix work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1 \
  --sessions D1 \
  --require-answer
```

Evaluate the extracted memory:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo_1s_v3_d1_bge_m3 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 10 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4 \
  --importance-weight 0.06
```

Create a comparison report against LoCoMo official observation memory:

```bash
python3 work/agent_memory_experiment/summarize_llm_extraction_comparison.py \
  --llm-memories work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3_d1_d30_memories.jsonl \
  --llm-summary work/agent_memory_experiment/results/llm_extracted_locomo_1c_all_v3_d1_d30_bge_m3/summary.csv \
  --llm-rankings work/agent_memory_experiment/results/llm_extracted_locomo_1c_all_v3_d1_d30_bge_m3/rankings.csv \
  --llm-usage work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3/usage.csv \
  --observation-memories work/agent_memory_experiment/data/locomo_observation_record1_d1_d30_memories.jsonl \
  --observation-summary work/agent_memory_experiment/results/locomo_observation_record1_d1_d30_bge_m3/summary.csv \
  --observation-rankings work/agent_memory_experiment/results/locomo_observation_record1_d1_d30_bge_m3/rankings.csv \
  --output outputs/agent_memory_llm_extraction_1conversation_comparison_zh.md \
  --csv-output outputs/agent_memory_llm_extraction_1conversation_comparison.csv
```

Current first-conversation DeepSeek result with local BGE-M3:

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact | 187 | 2443 | 175 | 0.474 | 0.726 | 0.590 |
| LoCoMo observation | 184 | 3002 | 155 | 0.497 | 0.690 | 0.578 |

Current LoCoMo10 DeepSeek result with local BGE-M3 and type-aware reranking:

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact + type-aware | 2517 | 31148 | 1838 | 0.503 | 0.733 | 0.609 |
| LoCoMo observation | 2507 | 40241 | 1638 | 0.483 | 0.703 | 0.583 |

Run type-aware reranking on the same slice:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3_d1_d30_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3_d1_d30_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo_1c_all_v3_d1_d30_bge_m3_type_008 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 20 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4 \
  --importance-weight 0.06 \
  --type-awareness-weight 0.08
```

The same run now also writes a pure BM25 `keyword` method alongside `vector`, `hybrid`, `time_aware`, and `type_aware`.

Run paired significance testing:

```bash
python3 work/agent_memory_experiment/paired_significance_test.py \
  --per-query work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004/per_query_metrics.csv \
  --baseline time_aware \
  --candidate type_aware \
  --output-csv outputs/agent_memory_type_aware_significance_results.csv \
  --output-report outputs/agent_memory_type_aware_significance_zh.md
```

Run top-1 error analysis:

```bash
python3 work/agent_memory_experiment/error_analysis.py \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --rankings work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004/rankings.csv \
  --per-query work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004/per_query_metrics.csv \
  --method type_aware \
  --output-csv outputs/agent_memory_error_analysis_locomo10_type_aware.csv \
  --summary-csv outputs/agent_memory_error_analysis_locomo10_type_aware_summary.csv \
  --output-report outputs/agent_memory_error_analysis_locomo10_type_aware_zh.md
```

Run cost and latency analysis:

```bash
python3 work/agent_memory_experiment/cost_latency_analysis.py \
  --llm-memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \
  --observation-memories work/agent_memory_experiment/data/locomo_observation_all_answerable_memories.jsonl \
  --usage work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3/usage.csv \
  --llm-report work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/report.md \
  --observation-report work/agent_memory_experiment/results/locomo_observation_all_answerable_bge_m3_type_008_with_keyword/report.md \
  --baseline-csv outputs/agent_memory_baseline_comparison_locomo10.csv \
  --output-csv outputs/agent_memory_cost_storage_locomo10.csv \
  --runtime-csv outputs/agent_memory_latency_locomo10.csv \
  --output-report outputs/agent_memory_cost_latency_locomo10_zh.md
```

## Cross-Agent Memory Reuse Experiments

Run one cross-agent reuse experiment:

```bash
python3 work/agent_memory_experiment/cross_agent_experiment.py \
  --memories work/agent_memory_experiment/data/synthetic_100_memories.jsonl \
  --output-dir work/agent_memory_experiment/results/cross_agent_100
```

Aggregate multiple scale runs:

```bash
python3 work/agent_memory_experiment/compare_cross_agent_results.py \
  work/agent_memory_experiment/results/cross_agent_100 \
  work/agent_memory_experiment/results/cross_agent_300 \
  work/agent_memory_experiment/results/cross_agent_500 \
  --output outputs/agent_memory_cross_agent_analysis.md \
  --csv-output outputs/agent_memory_cross_agent_results.csv
```

Cross-agent strategies:

- `private_only`: agent B sees only its private pool, so answer memories from agent A are unavailable.
- `shared_allowed`: agent B can retrieve authorized shared memories from agent A.
- `shared_plus_private_noise`: shared memories remain visible while same-topic private distractors are also present.
- `unfiltered_private_first`: a risk control where unauthorized private copies appear before shared copies, showing why permission filtering must happen before ranking or KV-cache reuse.

## Data Format

Memories are JSONL rows with fields:

- `id`
- `session_id`
- `turn`
- `date`
- `agent_id`
- `user_id`
- `text`
- `entities`

Queries are JSONL rows with fields:

- `id`
- `query`
- `answer_memory_ids`
- `query_date`
- `type`

## Scale-Up Path

Use the same script with larger files:

```bash
python3 work/agent_memory_experiment/memory_eval.py \
  --memories path/to/memories.jsonl \
  --queries path/to/queries.jsonl \
  --output-dir work/agent_memory_experiment/results/my_run
```

Recommended next steps:

1. Convert a real LoCoMo subset into the same JSONL format.
2. Run the converted subset with the default hash backend.
3. Replace the offline hashed-vector scorer with `mem0` or sentence-transformer embeddings.
4. Replace heuristic fact compression with LLM-based fact extraction.
5. Replace synthetic cross-agent records with real multi-agent traces and add source-agent trust / KV-cache reuse cost as a reranking feature.
