# External Embedding Baseline Blocker Audit

本文件把外部 embedding baseline 的投稿 blocker 拆成可执行检查项。它不读取、不打印 API key，也不发起网络请求；只汇总当前本地证据，说明为什么还不能把外部 embedding 写进论文主结果。

## 总览

- Blocker count: 3
- Status source: `outputs/agent_memory_embedding_baseline_status.csv`
- Preflight source: `outputs/agent_memory_api_embedding_preflight.csv`
- Estimate source: `outputs/agent_memory_api_embedding_run_estimate.csv`
- Readiness source: `outputs/agent_memory_submission_readiness.csv`
- Post-run source: `outputs/agent_memory_api_embedding_postrun_gate.csv`
- Paper acceptance source: `outputs/agent_memory_api_embedding_paper_acceptance.csv`

| Item | Status | Evidence | Required Action | Unblocks |
| --- | --- | --- | --- | --- |
| default_openai_key | blocker | OPENAI_API_KEY is not set; summary.csv not found | Set OPENAI_API_KEY in .env or shell, then rerun preflight. | api_embedding_preflight |
| generic_provider_key | alternative_missing | EXTERNAL_EMBEDDING_API_KEY is not set; summary.csv not found | Alternatively set EXTERNAL_EMBEDDING_API_KEY, EXTERNAL_EMBEDDING_MODEL, and EXTERNAL_EMBEDDING_BASE_URL. | api_embedding_preflight |
| preflight_required_checks | blocker | 4/5 required checks pass | Run preflight_api_embedding_baseline.py after configuring an embedding provider key. | safe paid/API run |
| run_scale_known | pass | items=4355, approx_tokens=71882, uncached_batches=35 | Rerun estimate_api_embedding_run.py if memories or queries change. | cost/risk planning |
| external_summary_completed | blocker | completed external embedding baselines=0, postrun_pass=0 | Run memory_eval.py with semantic-backend api and generate summary.csv. | external_embedding_completed |
| api_embedding_postrun_gate | pending_summary | no provider has complete summary, result files, and comparison table | Run validate_api_embedding_postrun.py after the API baseline and comparison finish. | paper-safe external embedding baseline |
| api_embedding_paper_acceptance | pending_summary | no provider has complete query-scale, per-query, ranking, by-type, and comparison evidence | Run validate_api_embedding_paper_acceptance.py after the API baseline, comparison, and post-run gate finish. | paper-citable external embedding baseline |
| comparison_table_completed | pending_summary | API summary not available; comparison remains pending | Run compare_embedding_baselines.py after API summary.csv exists. | paper embedding baseline table |

## 结论

- 当前不能启动真实外部 embedding baseline，也不能把外部 embedding 对照写成已完成实验。
- 当前 `.env` 中的 DeepSeek key 可用于 LLM memory writer / LLM-assisted audit，但不能解除 embedding baseline blocker。
- 最小解除路径：配置 `OPENAI_API_KEY`，或配置 `EXTERNAL_EMBEDDING_API_KEY` + `EXTERNAL_EMBEDDING_MODEL` + `EXTERNAL_EMBEDDING_BASE_URL`，然后按 README 的 preflight -> memory_eval -> compare 顺序运行。

## 复现实验命令顺序

1. `generate_embedding_baseline_status.py`：确认 key 是否存在以及 summary 是否已完成。
2. `preflight_api_embedding_baseline.py`：确认输入、key、缓存和输出路径。
3. `estimate_api_embedding_run.py`：确认文本数量、近似 token 和未缓存批次数。
4. `memory_eval.py --semantic-backend api`：执行真实外部 embedding baseline。
5. `compare_embedding_baselines.py`：生成相对 BGE-M3 的 delta 表。
6. `validate_api_embedding_postrun.py`：确认 summary、rankings、per-query metrics、summary_by_type 和 comparison 都完整。
7. `validate_api_embedding_paper_acceptance.py`：确认 query 数、per-query、Top-20 ranking、type coverage 和 comparison delta 均完整。
8. `validate_submission_readiness.py`：确认 `api_embedding_preflight` 与 `external_embedding_completed` 门禁是否解除。
