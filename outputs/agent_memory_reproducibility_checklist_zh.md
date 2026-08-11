# 论文实验复现清单

本清单用于检查当前仓库是否具备复现实验和写论文的关键 artifact。它不重新运行重型实验，只核对数据、结果文件、核心指标和复现命令入口。

## 总览

- Artifact 存在性：87/87
- 关键指标阈值：5/5

## 环境快照

| Key | Value |
|---|---|
| git_commit | `ccf6f87` |
| git_branch_status | `## main...origin/main` |
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
| Bootstrap metric CI report | True | 4250 | `outputs/agent_memory_bootstrap_metric_ci_zh.md` |
| Bootstrap metric CI CSV | True | 7562 | `outputs/agent_memory_bootstrap_metric_ci.csv` |
| Validation-tuned router comparison | True | 850159 | `outputs/agent_memory_validation_tuned_router_locomo10_comparison_per_query.csv` |
| Candidate reranker LOCO report | True | 3506 | `outputs/agent_memory_candidate_reranker_loco_zh.md` |
| Candidate reranker LOCO summary | True | 684 | `outputs/agent_memory_candidate_reranker_loco_summary.csv` |
| Candidate reranker LOCO significance | True | 627 | `outputs/agent_memory_candidate_reranker_loco_significance_zh.md` |
| Candidate reranker LOCO comparison | True | 316655 | `outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv` |
| Type3 coverage significance | True | 2545 | `outputs/agent_memory_type3_coverage_significance_zh.md` |
| Type3 query decomposition fusion4 report | True | 5473 | `outputs/agent_memory_type3_query_decomposition_fusion4_zh.md` |
| Type3 query decomposition fusion4 summary | True | 1604 | `outputs/agent_memory_type3_query_decomposition_fusion4_summary.csv` |
| Type3 query decomposition fusion4 per-query | True | 48687 | `outputs/agent_memory_type3_query_decomposition_fusion4_per_query.csv` |
| Type3 query decomposition fusion4 facets | True | 43337 | `outputs/agent_memory_type3_query_decomposition_fusion4_facets.csv` |
| Type3 query decomposition fusion4 ranked top20 | True | 529533 | `outputs/agent_memory_type3_query_decomposition_fusion4_ranked_top20.csv` |
| Type3 supervised selector rw0 report | True | 1936 | `outputs/agent_memory_type3_supervised_set_selector_rw0_zh.md` |
| Type3 supervised selector rw0 split summary | True | 2563 | `outputs/agent_memory_type3_supervised_set_selector_rw0_split_summary.csv` |
| Type3 supervised selector rw0 summary | True | 1074 | `outputs/agent_memory_type3_supervised_set_selector_rw0_summary.csv` |
| Type3 supervised selector rw0 coverage summary | True | 2033 | `outputs/agent_memory_type3_supervised_set_selector_rw0_coverage_summary.csv` |
| Type3 supervised selector rw0 per-query | True | 39665 | `outputs/agent_memory_type3_supervised_set_selector_rw0_per_query.csv` |
| Type3 supervised selector rw0 coverage | True | 66756 | `outputs/agent_memory_type3_supervised_set_selector_rw0_coverage.csv` |
| Type3 supervised selector rw0 comparison | True | 41035 | `outputs/agent_memory_type3_supervised_set_selector_rw0_comparison_per_query.csv` |
| Type3 supervised selector rw0 ranked top20 | True | 727551 | `outputs/agent_memory_type3_supervised_set_selector_rw0_ranked_top20.csv` |
| Type3 supervised selector rwn002 report | True | 1938 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_zh.md` |
| Type3 supervised selector rwn002 split summary | True | 2547 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_split_summary.csv` |
| Type3 supervised selector rwn002 summary | True | 1073 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_summary.csv` |
| Type3 supervised selector rwn002 coverage summary | True | 2031 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_coverage_summary.csv` |
| Type3 supervised selector rwn002 per-query | True | 39667 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_per_query.csv` |
| Type3 supervised selector rwn002 coverage | True | 66755 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_coverage.csv` |
| Type3 supervised selector rwn002 comparison | True | 41037 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_comparison_per_query.csv` |
| Type3 supervised selector rwn002 ranked top20 | True | 725694 | `outputs/agent_memory_type3_supervised_set_selector_rwn002_ranked_top20.csv` |
| Paper tables Markdown | True | 2832 | `outputs/agent_memory_paper_tables_zh.md` |
| Paper tables LaTeX | True | 3994 | `outputs/agent_memory_paper_tables.tex` |
| Paper evidence matrix | True | 6662 | `outputs/agent_memory_paper_evidence_matrix_zh.md` |
| Paper draft outline | True | 6827 | `outputs/agent_memory_paper_draft_outline_zh.md` |
| Paper manuscript draft | True | 9893 | `outputs/agent_memory_manuscript_draft_zh.md` |
| Paper manuscript claim check | True | 1827 | `outputs/agent_memory_manuscript_claim_check_zh.md` |
| Paper manuscript claim check CSV | True | 1395 | `outputs/agent_memory_manuscript_claim_check.csv` |
| Submission readiness gate | True | 2319 | `outputs/agent_memory_submission_readiness_gate_zh.md` |
| Submission readiness gate CSV | True | 1877 | `outputs/agent_memory_submission_readiness_gate.csv` |
| Public release readiness gate | True | 1436 | `outputs/agent_memory_public_release_readiness_zh.md` |
| Public release readiness gate CSV | True | 968 | `outputs/agent_memory_public_release_readiness.csv` |
| Artifact integrity manifest | True | 3770 | `outputs/agent_memory_artifact_integrity_manifest_zh.md` |
| Artifact integrity manifest CSV | True | 14865 | `outputs/agent_memory_artifact_integrity_manifest.csv` |
| Submission gap analysis | True | 9070 | `outputs/agent_memory_submission_gap_analysis_zh.md` |
| Submission gap analysis CSV | True | 4904 | `outputs/agent_memory_submission_gap_analysis.csv` |
| Experiment protocol | True | 4247 | `outputs/agent_memory_experiment_protocol_zh.md` |
| Embedding baseline status | True | 2683 | `outputs/agent_memory_embedding_baseline_status_zh.md` |
| Embedding baseline status CSV | True | 400 | `outputs/agent_memory_embedding_baseline_status.csv` |
| API embedding preflight | True | 2189 | `outputs/agent_memory_api_embedding_preflight_zh.md` |
| API embedding preflight CSV | True | 1109 | `outputs/agent_memory_api_embedding_preflight.csv` |
| Mock API embedding smoke test | True | 977 | `outputs/agent_memory_mock_api_embedding_smoke_test_zh.md` |
| Mock API embedding smoke test CSV | True | 102 | `outputs/agent_memory_mock_api_embedding_smoke_test.csv` |
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
| Human/LLM priority20 audit ids | True | 3777 | `outputs/agent_memory_human_llm_audit_priority20_ids.csv` |
| Human/LLM priority20 audit guide | True | 5330 | `outputs/agent_memory_human_llm_audit_priority20_guide_zh.md` |
| Human/LLM priority20 audit confirmation | True | 11290 | `outputs/agent_memory_human_llm_audit_priority20_confirmation.csv` |
| Human/LLM priority20 audit agreement | True | 1804 | `outputs/agent_memory_human_llm_audit_priority20_agreement_zh.md` |
| Human/LLM priority20 audit agreement CSV | True | 980 | `outputs/agent_memory_human_llm_audit_priority20_agreement.csv` |
| Human audit priority20 blind review | True | 1220 | `outputs/agent_memory_human_audit_priority20_blind_review_zh.md` |
| Human audit priority20 blind review CSV | True | 6882 | `outputs/agent_memory_human_audit_priority20_blind_review.csv` |
| Human audit full80 blind review | True | 1201 | `outputs/agent_memory_human_audit_full80_blind_review_zh.md` |
| Human audit full80 blind review CSV | True | 28745 | `outputs/agent_memory_human_audit_full80_blind_review.csv` |
| Human audit readiness gate | True | 4943 | `outputs/agent_memory_human_audit_readiness_gate_zh.md` |
| Human audit readiness gate CSV | True | 4116 | `outputs/agent_memory_human_audit_readiness_gate.csv` |
| Paper experiment status | True | 25867 | `outputs/agent_memory_paper_experiment_status_zh.md` |
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
| Bootstrap metric CI | `work/agent_memory_experiment/bootstrap_metric_ci.py` | Computes query-level bootstrap confidence intervals for main, LOCO, router, and Type3 paired results. |
| Type3 diagnostics | `work/agent_memory_experiment/type3_coverage_significance_analysis.py` | Aggregates Type3 coverage significance tests. |
| Type3 query decomposition fusion4 | `work/agent_memory_experiment/type3_query_decomposition_experiment.py` | Records the stronger keyword-facet decomposition fusion variant and its negative result. |
| Type3 supervised set selector variants | `work/agent_memory_experiment/type3_supervised_set_selector_experiment.py` | Records rw=0 and rw=-0.02 greedy set-selector variants for Type3 negative-result analysis. |
| Embedding baseline status | `work/agent_memory_experiment/generate_embedding_baseline_status.py` | Tracks API embedding baseline readiness without reading or printing keys. |
| API embedding preflight | `work/agent_memory_experiment/preflight_api_embedding_baseline.py` | Checks inputs, key availability, cache paths, and result summary before paid/API embedding runs. |
| Mock API embedding smoke test | `work/agent_memory_experiment/mock_api_embedding_smoke_test.py` | Runs the API embedding backend against a localhost OpenAI-compatible mock and verifies cache hits. |
| API embedding run estimate | `work/agent_memory_experiment/estimate_api_embedding_run.py` | Estimates API embedding item count, approximate tokens, batches, and cache status without network. |
| Embedding baseline comparison | `work/agent_memory_experiment/compare_embedding_baselines.py` | Compares API embedding summary against BGE-M3 when the API run exists. |
| Human audit sample | `work/agent_memory_experiment/generate_human_audit_sample.py` | Creates stratified manual-review sample for error-analysis reliability. |
| Human audit summary | `work/agent_memory_experiment/summarize_human_audit.py` | Summarizes manual labels once the audit CSV is filled. |
| LLM-assisted audit | `work/agent_memory_experiment/llm_audit_retrieval_errors.py` | Uses DeepSeek to draft audit labels for human review; does not replace human audit. |
| Human/LLM audit confirmation | `work/agent_memory_experiment/confirm_llm_audit_labels.py` | Creates a human-confirmation sheet and summarizes agreement after manual labels are filled. |
| Human/LLM priority20 audit | `work/agent_memory_experiment/generate_priority_audit_subset.py` | Selects a 20-sample quick-review subset and reuses the agreement workflow. |
| Blinded human audit sheets | `work/agent_memory_experiment/blind_human_audit_labels.py` | Exports blind review sheets that hide LLM-assisted labels and can merge human labels back. |
| Human audit readiness gate | `work/agent_memory_experiment/validate_human_audit_readiness.py` | Checks whether priority20/full80 human confirmations can support paper claims. |
| Evidence matrix | `work/agent_memory_experiment/generate_evidence_matrix.py` | Summarizes paper claims, evidence strength, and remaining gaps. |
| Paper draft outline | `work/agent_memory_experiment/generate_paper_draft_outline.py` | Builds a Chinese paper skeleton from current evidence, formulas, and result tables. |
| Paper manuscript draft | `work/agent_memory_experiment/generate_paper_manuscript.py` | Generates an editable Chinese manuscript draft from cached experiment outputs. |
| Paper manuscript claim check | `work/agent_memory_experiment/validate_manuscript_claims.py` | Checks that the draft does not overclaim pending embedding or human-audit results. |
| Submission readiness gate | `work/agent_memory_experiment/validate_submission_readiness.py` | Aggregates reproducibility, baseline, human-audit, and reviewer-risk gates before final submission. |
| Public release readiness gate | `work/agent_memory_experiment/validate_public_release_readiness.py` | Scans tracked files for secret-like strings, .env hygiene, release metadata, and artifact links. |
| Artifact integrity manifest | `work/agent_memory_experiment/generate_artifact_integrity_manifest.py` | Writes sha256, size, and line-count metadata for all reproducibility artifacts. |
| Submission gap analysis | `work/agent_memory_experiment/generate_submission_gap_analysis.py` | Ranks reviewer-facing risks and minimum actions before submission. |
| Experiment protocol | `work/agent_memory_experiment/generate_experiment_protocol.py` | Builds a paper appendix-style protocol from cached metrics and artifacts. |
| Environment snapshot | `work/agent_memory_experiment/generate_environment_snapshot.py` | Records Python/package/cache/Git environment; does not read .env. |
| Paper tables | `work/agent_memory_experiment/generate_paper_tables.py` | Generates Markdown and LaTeX tables from cached CSVs. |

## 仍需补强

- DeepSeek 抽取重复实验已具备 3 个 completed run；后续可在额外数据集或更大 slice 上复验稳定性。
- 跨智能体/KV cache 仍需要真实或半真实 multi-agent trace。
- Type 3 需要更强 LLM 子问题生成或 listwise/setwise objective；当前浅层方法均为负结果。
- 如果投稿，需要把实验环境写成固定版本，包括 Python、sentence-transformers、FAISS/sklearn 版本和 BGE-M3 缓存来源。
