# Agent Memory Stage 1 Summary

Created a first-stage local experiment under `work/agent_memory_experiment`.

It now includes:

- 10 hand-checkable memory records and 10 queries
- 100 synthetic memories and 80 generated queries
- 300 synthetic memories and 240 generated queries
- 500 synthetic memories and 400 generated queries
- three retrieval baselines: `vector`, `hybrid`, and `time_aware`
- overall metrics, per-query metrics, per-type metrics, rankings, and Markdown reports
- one-command pipeline script: `work/agent_memory_experiment/run_experiments.py`
- full pipeline script: `work/agent_memory_experiment/run_full_pipeline.py`
- offline HTML visualization: `outputs/agent_memory_experiment_visualization.html`
- pluggable semantic backend support: default `hash`, optional `sentence-transformer`
- LoCoMo-like long-conversation converter: `work/agent_memory_experiment/convert_long_conversation.py`
- validated conversion sample: `work/agent_memory_experiment/results/locomo_like_sample`
- real LoCoMo pipeline: `work/agent_memory_experiment/run_locomo_real.py`
- real LoCoMo converted data: 5882 memories and 1986 queries
- real LoCoMo analysis output: `outputs/agent_memory_locomo_real_report_zh.md`
- memory compression experiment: `work/agent_memory_experiment/compression_experiment.py`
- compression analysis outputs: `outputs/agent_memory_compression_analysis.md` and `outputs/agent_memory_compression_results.csv`
- cross-agent memory reuse experiment: `work/agent_memory_experiment/cross_agent_experiment.py`
- cross-agent analysis outputs: `outputs/agent_memory_cross_agent_analysis.md` and `outputs/agent_memory_cross_agent_results.csv`
- consolidated full-pipeline report: `outputs/agent_memory_full_pipeline_report.md`
- real-dataset adoption plan: `outputs/agent_memory_dataset_plan.md`
- Chinese current design / formulas / flow document: `outputs/agent_memory_current_design_zh.md`
- Chinese open-source research analysis: `outputs/agent_memory_open_source_research_zh.md`
- Chinese experiment retrospective: `outputs/agent_memory_experiment_retro_zh.md`
- Chinese GPU/model/API adoption plan: `outputs/agent_memory_model_gpu_api_plan_zh.md`
- DeepSeek official API setup guide: `outputs/deepseek_api_setup_zh.md`
- Chinese embedding model selection: `outputs/agent_memory_embedding_selection_zh.md`

Main analysis report:

`outputs/agent_memory_experiment_analysis.md`

Trend CSV:

`outputs/agent_memory_experiment_trends.csv`

Visualization:

`outputs/agent_memory_experiment_visualization.html`

Compression analysis:

`outputs/agent_memory_compression_analysis.md`

Cross-agent analysis:

`outputs/agent_memory_cross_agent_analysis.md`

Full-pipeline report:

`outputs/agent_memory_full_pipeline_report.md`

Dataset plan:

`outputs/agent_memory_dataset_plan.md`

Real LoCoMo report:

`outputs/agent_memory_locomo_real_report_zh.md`

Chinese current design, formulas, and flow:

`outputs/agent_memory_current_design_zh.md`

Chinese open-source research analysis:

`outputs/agent_memory_open_source_research_zh.md`

Chinese experiment retrospective:

`outputs/agent_memory_experiment_retro_zh.md`

Chinese GPU, model, and API adoption plan:

`outputs/agent_memory_model_gpu_api_plan_zh.md`

DeepSeek official API setup guide:

`outputs/deepseek_api_setup_zh.md`

Chinese embedding model selection:

`outputs/agent_memory_embedding_selection_zh.md`

## Current Results

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| sample_10 / hybrid | 0.800 | 0.900 | 1.000 | 0.875 |
| sample_10 / time_aware | 0.800 | 0.900 | 1.000 | 0.875 |
| sample_10 / vector | 0.800 | 0.900 | 1.000 | 0.870 |
| synthetic_100 / hybrid | 0.400 | 0.825 | 0.988 | 0.637 |
| synthetic_100 / time_aware | 0.575 | 0.887 | 0.988 | 0.740 |
| synthetic_100 / vector | 0.400 | 0.825 | 0.988 | 0.637 |
| synthetic_300 / hybrid | 0.200 | 0.546 | 0.721 | 0.438 |
| synthetic_300 / time_aware | 0.338 | 0.646 | 0.750 | 0.529 |
| synthetic_300 / vector | 0.175 | 0.525 | 0.700 | 0.416 |
| synthetic_500 / hybrid | 0.138 | 0.417 | 0.573 | 0.345 |
| synthetic_500 / time_aware | 0.240 | 0.522 | 0.642 | 0.424 |
| synthetic_500 / vector | 0.120 | 0.383 | 0.542 | 0.324 |

Key finding: as memory count grows, plain retrieval increasingly confuses old and new facts. The `time_aware` method improves temporal-update Recall@1 from 0.030 to 0.440 in the 500-memory run.

Compression finding: fact-level compression reduces token cost to about 43% of raw memory while mostly preserving time-aware retrieval. In the 500-memory run, raw time-aware Recall@1 is 0.240 and fact-compressed time-aware Recall@1 is 0.235; grouped summary compression drops to 0.110.

Cross-agent finding: when agent B can only see private memory, Recall@1 is 0 across 100/300/500 queries because the answer memories from agent A are unavailable. With authorized shared memory, time-aware Recall@1 reaches 0.910 / 0.757 / 0.704 for 100 / 300 / 500 memories. In the unfiltered private-first risk control, time-aware Recall@1 drops to 0, showing that permission filtering must happen before ranking, deduplication, or KV-cache reuse.

Real LoCoMo finding: the real `locomo10.json` dataset was converted into 5882 memories and 1986 queries. With the current offline hash baseline, `hybrid` performs best overall with Recall@1 0.186, Recall@3 0.299, Recall@5 0.342, and MRR 0.263. This confirms the real-data pipeline works, and also shows that the next improvement should be real embeddings plus LoCoMo-specific filtering/reranking.

To reproduce all current retrieval results:

```bash
python3 work/agent_memory_experiment/run_experiments.py
```

To reproduce the full first-stage evidence package, including retrieval, compression, cross-agent reuse, aggregation, and the final consolidated report:

```bash
python3 work/agent_memory_experiment/run_full_pipeline.py
```

To run the same pipeline with real embeddings after installing optional dependencies:

```bash
python3 work/agent_memory_experiment/run_experiments.py \
  --semantic-backend sentence-transformer \
  --embedding-model sentence-transformers/all-MiniLM-L6-v2
```

To include a real LoCoMo-like file after download:

```bash
python3 work/agent_memory_experiment/run_experiments.py \
  --long-conversation-input path/to/locomo.json \
  --long-conversation-name locomo_first_10 \
  --max-long-records 10
```

To reproduce the real LoCoMo run:

```bash
python3 work/agent_memory_experiment/run_locomo_real.py
```

To reproduce cross-agent reuse results:

```bash
python3 work/agent_memory_experiment/cross_agent_experiment.py \
  --memories work/agent_memory_experiment/data/synthetic_100_memories.jsonl \
  --output-dir work/agent_memory_experiment/results/cross_agent_100
```

Next useful step: download a real LoCoMo or LongMemEval file, convert the first 10 records, then scale to 100+ records with the same pipeline.
