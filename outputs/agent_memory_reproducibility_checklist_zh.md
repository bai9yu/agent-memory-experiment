# 论文实验复现清单

本清单用于检查当前仓库是否具备复现实验和写论文的关键 artifact。它不重新运行重型实验，只核对数据、结果文件、核心指标和复现命令入口。

## 总览

- Artifact 存在性：38/38
- 关键指标阈值：5/5

## 环境快照

| Key | Value |
|---|---|
| git_commit | `d5f25d9` |
| git_branch_status | `## main...origin/main [ahead 39]` |
| python | `3.9.6` |

## 数据文件

| Label | Path | Count/Status |
|---|---|---:|
| LLM fact memories | `work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl` | 2517 |
| Answerable queries | `work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl` | 1838 |

## 关键 Artifact

| Label | Exists | Size | Path |
|---|---:|---:|---|
| Main baseline CSV | True | 1146 | `outputs/agent_memory_baseline_comparison_locomo10.csv` |
| LLM extraction report | True | 3431 | `outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md` |
| Writer stability report | True | 1780 | `outputs/agent_memory_writer_stability_zh.md` |
| Writer stability aggregate | True | 967 | `outputs/agent_memory_writer_stability_aggregate.csv` |
| Writer stability runs | True | 924 | `outputs/agent_memory_writer_stability_runs.csv` |
| Candidate reranker report | True | 2019 | `outputs/agent_memory_candidate_reranker_locomo10_zh.md` |
| Candidate reranker significance | True | 607 | `outputs/agent_memory_candidate_reranker_significance_zh.md` |
| Candidate reranker LOCO report | True | 3506 | `outputs/agent_memory_candidate_reranker_loco_zh.md` |
| Candidate reranker LOCO summary | True | 684 | `outputs/agent_memory_candidate_reranker_loco_summary.csv` |
| Candidate reranker LOCO significance | True | 627 | `outputs/agent_memory_candidate_reranker_loco_significance_zh.md` |
| Candidate reranker LOCO comparison | True | 316655 | `outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv` |
| Type3 coverage significance | True | 2545 | `outputs/agent_memory_type3_coverage_significance_zh.md` |
| Paper tables Markdown | True | 2832 | `outputs/agent_memory_paper_tables_zh.md` |
| Paper tables LaTeX | True | 3994 | `outputs/agent_memory_paper_tables.tex` |
| Paper evidence matrix | True | 6590 | `outputs/agent_memory_paper_evidence_matrix_zh.md` |
| Paper draft outline | True | 6755 | `outputs/agent_memory_paper_draft_outline_zh.md` |
| Submission gap analysis | True | 8194 | `outputs/agent_memory_submission_gap_analysis_zh.md` |
| Submission gap analysis CSV | True | 4434 | `outputs/agent_memory_submission_gap_analysis.csv` |
| Embedding baseline status | True | 2017 | `outputs/agent_memory_embedding_baseline_status_zh.md` |
| Embedding baseline status CSV | True | 400 | `outputs/agent_memory_embedding_baseline_status.csv` |
| API embedding run estimate | True | 1048 | `outputs/agent_memory_api_embedding_run_estimate_zh.md` |
| API embedding run estimate CSV | True | 502 | `outputs/agent_memory_api_embedding_run_estimate.csv` |
| Embedding baseline comparison | True | 998 | `outputs/agent_memory_embedding_baseline_comparison_zh.md` |
| Embedding baseline comparison CSV | True | 381 | `outputs/agent_memory_embedding_baseline_comparison.csv` |
| Human audit protocol | True | 2479 | `outputs/agent_memory_human_audit_protocol_zh.md` |
| Human audit sample | True | 28471 | `outputs/agent_memory_human_audit_sample_type_aware.csv` |
| Human audit summary | True | 1394 | `outputs/agent_memory_human_audit_summary_zh.md` |
| Human audit summary CSV | True | 777 | `outputs/agent_memory_human_audit_summary.csv` |
| LLM-assisted audit report | True | 620 | `outputs/agent_memory_llm_audit_report_zh.md` |
| LLM-assisted audit summary | True | 1834 | `outputs/agent_memory_llm_audit_summary_zh.md` |
| LLM-assisted audit summary CSV | True | 1241 | `outputs/agent_memory_llm_audit_summary.csv` |
| LLM-assisted audit usage | True | 357 | `outputs/agent_memory_llm_audit_usage.csv` |
| Human/LLM audit confirmation | True | 44890 | `outputs/agent_memory_human_llm_audit_confirmation.csv` |
| Human/LLM audit agreement | True | 1804 | `outputs/agent_memory_human_llm_audit_agreement_zh.md` |
| Human/LLM audit agreement CSV | True | 980 | `outputs/agent_memory_human_llm_audit_agreement.csv` |
| Paper experiment status | True | 22067 | `outputs/agent_memory_paper_experiment_status_zh.md` |
| Experiment retro | True | 33114 | `outputs/agent_memory_experiment_retro_zh.md` |
| Environment snapshot | True | 1421 | `outputs/agent_memory_environment_snapshot_zh.md` |

## 核心指标检查

| Metric | Observed | Expected Min | Pass |
|---|---:|---:|---:|
| LoCoMo10 type_aware MRR | 0.6094 | 0.6000 | True |
| LoCoMo10 type_aware Recall@5 | 0.7334 | 0.7300 | True |
| Candidate reranker MRR | 0.6606 | 0.6500 | True |
| Candidate reranker Recall@5 | 0.7957 | 0.7900 | True |
| Type3 supervised selector Coverage@5 delta is negative | 0.0572 | 0.0500 | True |

## 复现命令入口

| Stage | Command / Document | Notes |
|---|---|---|
| Main LoCoMo retrieval | `work/agent_memory_experiment/README.md#recommended-locomo-run` | Requires local BGE-M3 cache; no online embedding API. |
| Writer stability | `work/agent_memory_experiment/summarize_writer_stability.py` | Summarizes repeated DeepSeek memory-writer runs from a local manifest. |
| Candidate reranker | `work/agent_memory_experiment/candidate_reranker_experiment.py` | Uses cached rankings.csv; held-out query split. |
| Candidate reranker LOCO | `work/agent_memory_experiment/candidate_reranker_loco_experiment.py` | Uses cached rankings.csv; leave-one-conversation-out split. |
| Type3 diagnostics | `work/agent_memory_experiment/type3_coverage_significance_analysis.py` | Aggregates Type3 coverage significance tests. |
| Embedding baseline status | `work/agent_memory_experiment/generate_embedding_baseline_status.py` | Tracks API embedding baseline readiness without reading or printing keys. |
| API embedding run estimate | `work/agent_memory_experiment/estimate_api_embedding_run.py` | Estimates API embedding item count, approximate tokens, batches, and cache status without network. |
| Embedding baseline comparison | `work/agent_memory_experiment/compare_embedding_baselines.py` | Compares API embedding summary against BGE-M3 when the API run exists. |
| Human audit sample | `work/agent_memory_experiment/generate_human_audit_sample.py` | Creates stratified manual-review sample for error-analysis reliability. |
| Human audit summary | `work/agent_memory_experiment/summarize_human_audit.py` | Summarizes manual labels once the audit CSV is filled. |
| LLM-assisted audit | `work/agent_memory_experiment/llm_audit_retrieval_errors.py` | Uses DeepSeek to draft audit labels for human review; does not replace human audit. |
| Human/LLM audit confirmation | `work/agent_memory_experiment/confirm_llm_audit_labels.py` | Creates a human-confirmation sheet and summarizes agreement after manual labels are filled. |
| Evidence matrix | `work/agent_memory_experiment/generate_evidence_matrix.py` | Summarizes paper claims, evidence strength, and remaining gaps. |
| Paper draft outline | `work/agent_memory_experiment/generate_paper_draft_outline.py` | Builds a Chinese paper skeleton from current evidence, formulas, and result tables. |
| Submission gap analysis | `work/agent_memory_experiment/generate_submission_gap_analysis.py` | Ranks reviewer-facing risks and minimum actions before submission. |
| Environment snapshot | `work/agent_memory_experiment/generate_environment_snapshot.py` | Records Python/package/cache/Git environment; does not read .env. |
| Paper tables | `work/agent_memory_experiment/generate_paper_tables.py` | Generates Markdown and LaTeX tables from cached CSVs. |

## 仍需补强

- DeepSeek 抽取重复实验已具备 3 个 completed run；后续可在额外数据集或更大 slice 上复验稳定性。
- 跨智能体/KV cache 仍需要真实或半真实 multi-agent trace。
- Type 3 需要更强 LLM 子问题生成或 listwise/setwise objective；当前浅层方法均为负结果。
- 如果投稿，需要把实验环境写成固定版本，包括 Python、sentence-transformers、FAISS/sklearn 版本和 BGE-M3 缓存来源。
