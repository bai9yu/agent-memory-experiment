# 论文实验复现清单

本清单用于检查当前仓库是否具备复现实验和写论文的关键 artifact。它不重新运行重型实验，只核对数据、结果文件、核心指标和复现命令入口。

## 总览

- Artifact 存在性：194/194
- 关键指标阈值：22/22

## 环境快照

| Key | Value |
|---|---|
| git_commit | `a307719` |
| git_branch_status | `## main...origin/main [ahead 2]` |
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
| Dataset slice profile report | True | 4014 | `outputs/agent_memory_dataset_slice_profile_zh.md` |
| Dataset slice profile summary | True | 1545 | `outputs/agent_memory_dataset_slice_profile_summary.csv` |
| Dataset slice profile distribution | True | 15966 | `outputs/agent_memory_dataset_slice_profile_distribution.csv` |
| LLM extraction report | True | 3431 | `outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md` |
| Writer stability report | True | 1780 | `outputs/agent_memory_writer_stability_zh.md` |
| Writer stability aggregate | True | 967 | `outputs/agent_memory_writer_stability_aggregate.csv` |
| Writer stability runs | True | 924 | `outputs/agent_memory_writer_stability_runs.csv` |
| Time-aware error analysis report | True | 2493 | `outputs/agent_memory_error_analysis_locomo10_time_aware_zh.md` |
| Time-aware error analysis CSV | True | 308368 | `outputs/agent_memory_error_analysis_locomo10_time_aware.csv` |
| Time-aware error analysis summary | True | 14604 | `outputs/agent_memory_error_analysis_locomo10_time_aware_summary.csv` |
| Type-aware error analysis report | True | 4359 | `outputs/agent_memory_error_analysis_locomo10_type_aware_zh.md` |
| Type-aware error analysis CSV | True | 305669 | `outputs/agent_memory_error_analysis_locomo10_type_aware.csv` |
| Type-aware error analysis summary | True | 14594 | `outputs/agent_memory_error_analysis_locomo10_type_aware_summary.csv` |
| Candidate reranker report | True | 2019 | `outputs/agent_memory_candidate_reranker_locomo10_zh.md` |
| Candidate reranker significance | True | 607 | `outputs/agent_memory_candidate_reranker_significance_zh.md` |
| Candidate reranker feature ablation report | True | 3225 | `outputs/agent_memory_candidate_reranker_feature_ablation_zh.md` |
| Candidate reranker feature ablation summary | True | 2034 | `outputs/agent_memory_candidate_reranker_feature_ablation_summary.csv` |
| Candidate reranker feature ablation split summary | True | 5458 | `outputs/agent_memory_candidate_reranker_feature_ablation_split_summary.csv` |
| Candidate reranker feature ablation deltas | True | 1407 | `outputs/agent_memory_candidate_reranker_feature_ablation_deltas.csv` |
| Candidate reranker feature ablation comparison | True | 1724236 | `outputs/agent_memory_candidate_reranker_feature_ablation_comparison_per_query.csv` |
| Candidate reranker paired effect-size report | True | 1912 | `outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md` |
| Candidate reranker paired effect-size CSV | True | 6383 | `outputs/agent_memory_candidate_reranker_paired_effect_size.csv` |
| Candidate reranker statistical power report | True | 3581 | `outputs/agent_memory_candidate_reranker_statistical_power_zh.md` |
| Candidate reranker statistical power CSV | True | 4128 | `outputs/agent_memory_candidate_reranker_statistical_power.csv` |
| Paper case study pack | True | 8632 | `outputs/agent_memory_paper_case_study_pack_zh.md` |
| Paper case study pack CSV | True | 5466 | `outputs/agent_memory_paper_case_study_pack.csv` |
| Candidate reranker seed stability report | True | 2058 | `outputs/agent_memory_candidate_reranker_seed_stability_zh.md` |
| Candidate reranker seed stability summary | True | 682 | `outputs/agent_memory_candidate_reranker_seed_stability_summary.csv` |
| Candidate reranker seed stability deltas | True | 612 | `outputs/agent_memory_candidate_reranker_seed_stability.csv` |
| Candidate reranker seed stability split summary | True | 6086 | `outputs/agent_memory_candidate_reranker_seed_stability_split_summary.csv` |
| Candidate reranker train-fraction sensitivity report | True | 2558 | `outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md` |
| Candidate reranker train-fraction sensitivity summary | True | 2399 | `outputs/agent_memory_candidate_reranker_train_fraction_summary.csv` |
| Candidate reranker train-fraction sensitivity deltas | True | 1835 | `outputs/agent_memory_candidate_reranker_train_fraction_sensitivity.csv` |
| Candidate reranker train-fraction sensitivity split summary | True | 12588 | `outputs/agent_memory_candidate_reranker_train_fraction_split_summary.csv` |
| Candidate oracle gap analysis report | True | 2509 | `outputs/agent_memory_candidate_oracle_gap_analysis_zh.md` |
| Candidate oracle gap analysis CSV | True | 3129 | `outputs/agent_memory_candidate_oracle_gap_analysis.csv` |
| Bootstrap metric CI report | True | 6438 | `outputs/agent_memory_bootstrap_metric_ci_zh.md` |
| Bootstrap metric CI CSV | True | 12250 | `outputs/agent_memory_bootstrap_metric_ci.csv` |
| Validation-tuned router comparison | True | 850159 | `outputs/agent_memory_validation_tuned_router_locomo10_comparison_per_query.csv` |
| Candidate reranker LOCO report | True | 3506 | `outputs/agent_memory_candidate_reranker_loco_zh.md` |
| Candidate reranker LOCO summary | True | 684 | `outputs/agent_memory_candidate_reranker_loco_summary.csv` |
| Candidate reranker LOCO significance | True | 627 | `outputs/agent_memory_candidate_reranker_loco_significance_zh.md` |
| Candidate reranker LOCO comparison | True | 316655 | `outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv` |
| Intrinsic candidate reranker LOCO report | True | 3683 | `outputs/agent_memory_candidate_reranker_intrinsic_loco_zh.md` |
| Intrinsic candidate reranker LOCO summary | True | 685 | `outputs/agent_memory_candidate_reranker_intrinsic_loco_summary.csv` |
| Intrinsic candidate reranker LOCO split summary | True | 3266 | `outputs/agent_memory_candidate_reranker_intrinsic_loco_split_summary.csv` |
| Intrinsic candidate reranker LOCO deltas | True | 306 | `outputs/agent_memory_candidate_reranker_intrinsic_loco_deltas.csv` |
| Intrinsic candidate reranker LOCO comparison | True | 316457 | `outputs/agent_memory_candidate_reranker_intrinsic_loco_comparison_per_query.csv` |
| Intrinsic reranker method appendix | True | 6999 | `outputs/agent_memory_intrinsic_reranker_method_appendix_zh.md` |
| Intrinsic reranker feature groups | True | 924 | `outputs/agent_memory_intrinsic_reranker_feature_groups.csv` |
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
| Paper tables Markdown | True | 3724 | `outputs/agent_memory_paper_tables_zh.md` |
| Paper tables LaTeX | True | 5197 | `outputs/agent_memory_paper_tables.tex` |
| Paper table consistency audit | True | 3343 | `outputs/agent_memory_paper_table_consistency_zh.md` |
| Paper table consistency audit CSV | True | 3737 | `outputs/agent_memory_paper_table_consistency.csv` |
| Paper evidence matrix | True | 7856 | `outputs/agent_memory_paper_evidence_matrix_zh.md` |
| Paper draft outline | True | 7485 | `outputs/agent_memory_paper_draft_outline_zh.md` |
| Paper manuscript draft | True | 12592 | `outputs/agent_memory_manuscript_draft_zh.md` |
| Paper manuscript claim check | True | 1827 | `outputs/agent_memory_manuscript_claim_check_zh.md` |
| Paper manuscript claim check CSV | True | 1395 | `outputs/agent_memory_manuscript_claim_check.csv` |
| Paper manuscript numeric claim check | True | 3116 | `outputs/agent_memory_manuscript_numeric_claim_check_zh.md` |
| Paper manuscript numeric claim check CSV | True | 11685 | `outputs/agent_memory_manuscript_numeric_claim_check.csv` |
| Paper scope claim audit | True | 11366 | `outputs/agent_memory_paper_scope_claim_audit_zh.md` |
| Paper scope claim audit CSV | True | 10190 | `outputs/agent_memory_paper_scope_claim_audit.csv` |
| Threats to validity appendix | True | 5872 | `outputs/agent_memory_threats_to_validity_zh.md` |
| Threats to validity CSV | True | 3236 | `outputs/agent_memory_threats_to_validity.csv` |
| Reviewer response preparation matrix | True | 4396 | `outputs/agent_memory_reviewer_response_prep_zh.md` |
| Reviewer response preparation matrix CSV | True | 4244 | `outputs/agent_memory_reviewer_response_prep.csv` |
| Submission package index | True | 8532 | `outputs/agent_memory_submission_package_index_zh.md` |
| Submission package index CSV | True | 9694 | `outputs/agent_memory_submission_package_index.csv` |
| Submission entrypoint consistency audit | True | 2106 | `outputs/agent_memory_submission_entrypoint_consistency_zh.md` |
| Submission entrypoint consistency audit CSV | True | 1487 | `outputs/agent_memory_submission_entrypoint_consistency.csv` |
| Submission readiness gate | True | 2550 | `outputs/agent_memory_submission_readiness_zh.md` |
| Submission readiness gate CSV | True | 2230 | `outputs/agent_memory_submission_readiness.csv` |
| Public release readiness gate | True | 1688 | `outputs/agent_memory_public_release_readiness_zh.md` |
| Public release readiness gate CSV | True | 1424 | `outputs/agent_memory_public_release_readiness.csv` |
| Untracked artifact audit | True | 4747 | `outputs/agent_memory_untracked_artifact_audit_zh.md` |
| Untracked artifact audit CSV | True | 3637 | `outputs/agent_memory_untracked_artifact_audit.csv` |
| Large intermediate provenance audit | True | 2048 | `outputs/agent_memory_large_intermediate_provenance_zh.md` |
| Large intermediate provenance audit CSV | True | 2824 | `outputs/agent_memory_large_intermediate_provenance.csv` |
| Artifact path portability audit | True | 734 | `outputs/agent_memory_artifact_path_portability_zh.md` |
| Artifact path portability audit CSV | True | 214 | `outputs/agent_memory_artifact_path_portability.csv` |
| Artifact integrity manifest | True | 3795 | `outputs/agent_memory_artifact_integrity_manifest_zh.md` |
| Artifact integrity manifest CSV | True | 33742 | `outputs/agent_memory_artifact_integrity_manifest.csv` |
| Submission gap analysis | True | 9993 | `outputs/agent_memory_submission_gap_analysis_zh.md` |
| Submission gap analysis CSV | True | 5825 | `outputs/agent_memory_submission_gap_analysis.csv` |
| Submission blocker closure plan | True | 3600 | `outputs/agent_memory_submission_blocker_closure_plan_zh.md` |
| Submission blocker closure plan CSV | True | 2813 | `outputs/agent_memory_submission_blocker_closure_plan.csv` |
| Paper artifact refresh run | True | 5602 | `outputs/agent_memory_paper_artifact_refresh_run_zh.md` |
| Paper artifact refresh run CSV | True | 19706 | `outputs/agent_memory_paper_artifact_refresh_run.csv` |
| Paper refresh coverage audit | True | 8159 | `outputs/agent_memory_paper_refresh_coverage_audit_zh.md` |
| Paper refresh coverage audit CSV | True | 7101 | `outputs/agent_memory_paper_refresh_coverage_audit.csv` |
| Evidence freshness audit | True | 808 | `outputs/agent_memory_evidence_freshness_audit_zh.md` |
| Evidence freshness audit CSV | True | 98 | `outputs/agent_memory_evidence_freshness_audit.csv` |
| Experiment protocol | True | 4247 | `outputs/agent_memory_experiment_protocol_zh.md` |
| Embedding baseline status | True | 3276 | `outputs/agent_memory_embedding_baseline_status_zh.md` |
| Embedding baseline status CSV | True | 734 | `outputs/agent_memory_embedding_baseline_status.csv` |
| Embedding provider profiles | True | 9136 | `outputs/agent_memory_embedding_provider_profiles_zh.md` |
| Embedding provider profiles CSV | True | 919 | `outputs/agent_memory_embedding_provider_profiles.csv` |
| API embedding preflight | True | 2189 | `outputs/agent_memory_api_embedding_preflight_zh.md` |
| API embedding preflight CSV | True | 1109 | `outputs/agent_memory_api_embedding_preflight.csv` |
| Mock API embedding smoke test | True | 896 | `outputs/agent_memory_mock_api_embedding_smoke_test_zh.md` |
| Mock API embedding smoke test CSV | True | 102 | `outputs/agent_memory_mock_api_embedding_smoke_test.csv` |
| API embedding run estimate | True | 1048 | `outputs/agent_memory_api_embedding_run_estimate_zh.md` |
| API embedding run estimate CSV | True | 502 | `outputs/agent_memory_api_embedding_run_estimate.csv` |
| API embedding execution runbook | True | 4254 | `outputs/agent_memory_api_embedding_execution_runbook_zh.md` |
| API embedding execution runbook CSV | True | 13688 | `outputs/agent_memory_api_embedding_execution_runbook.csv` |
| Embedding baseline comparison | True | 998 | `outputs/agent_memory_embedding_baseline_comparison_zh.md` |
| Embedding baseline comparison CSV | True | 381 | `outputs/agent_memory_embedding_baseline_comparison.csv` |
| API embedding post-run gate | True | 1445 | `outputs/agent_memory_api_embedding_postrun_gate_zh.md` |
| API embedding post-run gate CSV | True | 898 | `outputs/agent_memory_api_embedding_postrun_gate.csv` |
| Offline embedding sensitivity | True | 2669 | `outputs/agent_memory_offline_embedding_sensitivity_zh.md` |
| Offline embedding sensitivity CSV | True | 1993 | `outputs/agent_memory_offline_embedding_sensitivity.csv` |
| External embedding blocker audit | True | 3406 | `outputs/agent_memory_external_embedding_blocker_audit_zh.md` |
| External embedding blocker audit CSV | True | 1396 | `outputs/agent_memory_external_embedding_blocker_audit.csv` |
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
| Human audit priority20 review packet | True | 15963 | `outputs/agent_memory_human_audit_priority20_review_packet_zh.md` |
| Human audit priority20 dual review CSV | True | 7390 | `outputs/agent_memory_human_audit_priority20_dual_review.csv` |
| Human audit priority20 dual agreement | True | 6254 | `outputs/agent_memory_human_audit_priority20_dual_agreement_zh.md` |
| Human audit priority20 dual agreement CSV | True | 750 | `outputs/agent_memory_human_audit_priority20_dual_agreement.csv` |
| Human audit full80 blind review | True | 1201 | `outputs/agent_memory_human_audit_full80_blind_review_zh.md` |
| Human audit full80 blind review CSV | True | 28745 | `outputs/agent_memory_human_audit_full80_blind_review.csv` |
| Human audit full80 review packet | True | 62903 | `outputs/agent_memory_human_audit_full80_review_packet_zh.md` |
| Human audit priority20 annotation HTML | True | 26223 | `outputs/agent_memory_human_audit_priority20_annotation.html` |
| Human audit full80 annotation HTML | True | 71948 | `outputs/agent_memory_human_audit_full80_annotation.html` |
| Human audit annotation interface | True | 907 | `outputs/agent_memory_human_audit_annotation_interface_zh.md` |
| Human audit annotation interface CSV | True | 319 | `outputs/agent_memory_human_audit_annotation_interface.csv` |
| Human audit annotation interface validation | True | 2856 | `outputs/agent_memory_human_audit_annotation_interface_validation_zh.md` |
| Human audit annotation interface validation CSV | True | 2178 | `outputs/agent_memory_human_audit_annotation_interface_validation.csv` |
| Human audit annotation import readiness | True | 2681 | `outputs/agent_memory_human_audit_annotation_import_readiness_zh.md` |
| Human audit annotation import readiness CSV | True | 734 | `outputs/agent_memory_human_audit_annotation_import_readiness.csv` |
| Human audit paper-claim upgrade gate | True | 2510 | `outputs/agent_memory_human_audit_paper_claim_upgrade_zh.md` |
| Human audit paper-claim upgrade gate CSV | True | 2624 | `outputs/agent_memory_human_audit_paper_claim_upgrade.csv` |
| Human audit full80 dual review CSV | True | 29853 | `outputs/agent_memory_human_audit_full80_dual_review.csv` |
| Human audit full80 dual agreement | True | 6250 | `outputs/agent_memory_human_audit_full80_dual_agreement_zh.md` |
| Human audit full80 dual agreement CSV | True | 750 | `outputs/agent_memory_human_audit_full80_dual_agreement.csv` |
| Human audit readiness gate | True | 4943 | `outputs/agent_memory_human_audit_readiness_gate_zh.md` |
| Human audit readiness gate CSV | True | 4116 | `outputs/agent_memory_human_audit_readiness_gate.csv` |
| Human audit annotation codebook | True | 8167 | `outputs/agent_memory_human_audit_annotation_codebook_zh.md` |
| Human audit annotation schema | True | 1883 | `outputs/agent_memory_human_audit_annotation_schema.csv` |
| Human audit execution plan | True | 3788 | `outputs/agent_memory_human_audit_execution_plan_zh.md` |
| Human audit execution plan CSV | True | 2165 | `outputs/agent_memory_human_audit_execution_plan.csv` |
| Human audit sample QC | True | 6936 | `outputs/agent_memory_human_audit_sample_qc_zh.md` |
| Human audit sample QC CSV | True | 7512 | `outputs/agent_memory_human_audit_sample_qc.csv` |
| Human audit labeling dashboard | True | 6904 | `outputs/agent_memory_human_audit_labeling_dashboard_zh.md` |
| Human audit labeling dashboard CSV | True | 31843 | `outputs/agent_memory_human_audit_labeling_dashboard.csv` |
| Human audit blind review leakage audit | True | 3326 | `outputs/agent_memory_human_audit_blind_review_leakage_zh.md` |
| Human audit blind review leakage audit CSV | True | 2567 | `outputs/agent_memory_human_audit_blind_review_leakage.csv` |
| Paper experiment status | True | 33868 | `outputs/agent_memory_paper_experiment_status_zh.md` |
| Experiment retro | True | 33114 | `outputs/agent_memory_experiment_retro_zh.md` |
| Environment snapshot | True | 1410 | `outputs/agent_memory_environment_snapshot_zh.md` |
| Environment system snapshot | True | 163 | `outputs/agent_memory_environment_system.csv` |
| Environment package snapshot | True | 188 | `outputs/agent_memory_environment_packages.csv` |
| Environment freshness audit | True | 1337 | `outputs/agent_memory_environment_freshness_audit_zh.md` |
| Environment freshness audit CSV | True | 489 | `outputs/agent_memory_environment_freshness_audit.csv` |

## 核心指标检查

| Metric | Observed | Expected Min | Pass |
|---|---:|---:|---:|
| LoCoMo10 type_aware MRR | 0.6094 | 0.6000 | True |
| LoCoMo10 type_aware Recall@5 | 0.7334 | 0.7300 | True |
| LoCoMo10 fact-slice raw query coverage | 0.9255 | 0.9000 | True |
| LoCoMo10 fact-slice group coverage | 10.0000 | 10.0000 | True |
| LoCoMo10 fact-slice multi-gold query share | 0.4608 | 0.4000 | True |
| Candidate reranker MRR | 0.6606 | 0.6500 | True |
| Candidate reranker Recall@5 | 0.7957 | 0.7900 | True |
| Intrinsic-only candidate reranker MRR | 0.6719 | 0.6700 | True |
| Intrinsic-only candidate reranker Recall@5 | 0.8014 | 0.8000 | True |
| Intrinsic-only LOCO candidate reranker MRR | 0.6638 | 0.6600 | True |
| Intrinsic-only LOCO candidate reranker Recall@5 | 0.7969 | 0.7900 | True |
| Intrinsic-only seed-stability positive-seed rate | 1.0000 | 1.0000 | True |
| Intrinsic-only seed-stability minimum MRR delta | 0.0414 | 0.0400 | True |
| Intrinsic-only train-fraction minimum win rate | 1.0000 | 1.0000 | True |
| Intrinsic-only train-fraction minimum MRR delta | 0.0414 | 0.0400 | True |
| Intrinsic-only paired effect-size MRR Cohen dz | 0.2234 | 0.2000 | True |
| Intrinsic-only paired effect-size positive net rate | 0.0652 | 0.0600 | True |
| Intrinsic-only MRR statistical-power CI precision | -0.0109 | -0.0120 | True |
| Intrinsic-only Recall@5 statistical-power CI precision | -0.0132 | -0.0140 | True |
| Intrinsic-only held-out MRR oracle-gap closure | 0.2154 | 0.2000 | True |
| Type3 Coverage@5 oracle-gap closure is negative | 0.2150 | 0.1000 | True |
| Type3 supervised selector Coverage@5 delta is negative | 0.0572 | 0.0500 | True |

## 复现命令入口

| Stage | Command / Document | Notes |
|---|---|---|
| Main LoCoMo retrieval | `work/agent_memory_experiment/README.md#recommended-locomo-run` | Requires local BGE-M3 cache; no online embedding API. |
| Writer stability | `work/agent_memory_experiment/summarize_writer_stability.py` | Summarizes repeated DeepSeek memory-writer runs from a local manifest. |
| Candidate reranker | `work/agent_memory_experiment/candidate_reranker_experiment.py` | Uses cached rankings.csv; held-out query split. |
| Candidate reranker feature ablation | `work/agent_memory_experiment/candidate_reranker_feature_ablation.py` | Tests feature-group ablations and compares intrinsic-only reranker against full reranker and fixed type-aware. |
| Candidate reranker paired effect size | `work/agent_memory_experiment/generate_paired_effect_size_analysis.py` | Reports improved/worsened/tied paired outcomes, query-type breakdowns, and paired Cohen's dz. |
| Candidate reranker statistical power | `work/agent_memory_experiment/generate_statistical_power_analysis.py` | Estimates paired bootstrap CI precision and sample-size sensitivity for main reranker metric deltas. |
| Paper case study pack | `work/agent_memory_experiment/generate_paper_case_study_pack.py` | Builds compact qualitative examples for success, regression, and stable-correct reranker behavior. |
| Candidate reranker seed stability | `work/agent_memory_experiment/candidate_reranker_seed_stability.py` | Runs an extended 20-seed stability check for intrinsic-only and full candidate rerankers against type-aware. |
| Candidate reranker train-fraction sensitivity | `work/agent_memory_experiment/candidate_reranker_train_fraction_sensitivity.py` | Checks whether intrinsic-only reranker gains hold across 0.5/0.6/0.7/0.8 train fractions. |
| Candidate oracle gap analysis | `work/agent_memory_experiment/generate_oracle_gap_analysis.py` | Quantifies how much oracle headroom is closed by the main reranker and why Type3 remains unresolved. |
| Candidate reranker LOCO | `work/agent_memory_experiment/candidate_reranker_loco_experiment.py` | Uses cached rankings.csv; leave-one-conversation-out split. |
| Intrinsic candidate reranker LOCO | `work/agent_memory_experiment/candidate_reranker_intrinsic_loco_experiment.py` | Reuses leave-one-conversation-out split with intrinsic-only candidate features. |
| Intrinsic reranker method appendix | `work/agent_memory_experiment/generate_intrinsic_reranker_method_appendix.py` | Builds a paper appendix with feature definitions, model hyperparameters, validation protocol, and reproducible commands. |
| Bootstrap metric CI | `work/agent_memory_experiment/bootstrap_metric_ci.py` | Computes query-level bootstrap confidence intervals for main, LOCO, router, and Type3 paired results. |
| Type3 diagnostics | `work/agent_memory_experiment/type3_coverage_significance_analysis.py` | Aggregates Type3 coverage significance tests. |
| Type3 query decomposition fusion4 | `work/agent_memory_experiment/type3_query_decomposition_experiment.py` | Records the stronger keyword-facet decomposition fusion variant and its negative result. |
| Type3 supervised set selector variants | `work/agent_memory_experiment/type3_supervised_set_selector_experiment.py` | Records rw=0 and rw=-0.02 greedy set-selector variants for Type3 negative-result analysis. |
| Embedding baseline status | `work/agent_memory_experiment/generate_embedding_baseline_status.py` | Tracks API embedding baseline readiness without reading or printing keys. |
| Embedding provider profiles | `work/agent_memory_experiment/generate_embedding_provider_profiles.py` | Lists OpenAI and generic OpenAI-compatible provider commands for preflight, estimate, run, and compare. |
| API embedding preflight | `work/agent_memory_experiment/preflight_api_embedding_baseline.py` | Checks inputs, key availability, cache paths, and result summary before paid/API embedding runs. |
| Mock API embedding smoke test | `work/agent_memory_experiment/mock_api_embedding_smoke_test.py` | Runs the API embedding backend against a localhost OpenAI-compatible mock and verifies cache hits. |
| API embedding run estimate | `work/agent_memory_experiment/estimate_api_embedding_run.py` | Estimates API embedding item count, approximate tokens, batches, and cache status without network. |
| API embedding execution runbook | `work/agent_memory_experiment/generate_api_embedding_execution_runbook.py` | Fixes the preflight, estimate, paid run, comparison, postrun, and final-refresh sequence for external embedding baselines. |
| Embedding baseline comparison | `work/agent_memory_experiment/compare_embedding_baselines.py` | Compares API embedding summary against BGE-M3 when the API run exists. |
| API embedding post-run gate | `work/agent_memory_experiment/validate_api_embedding_postrun.py` | Checks summary, result files, metrics, and BGE-M3 comparison before citing an API embedding baseline. |
| Offline embedding sensitivity | `work/agent_memory_experiment/generate_offline_embedding_sensitivity.py` | Compares BGE-M3 against hash-vector and BM25 offline floors without network or paid API calls. |
| External embedding blocker audit | `work/agent_memory_experiment/generate_external_embedding_blocker_audit.py` | Aggregates key, preflight, summary, comparison, and readiness blockers into an actionable audit. |
| Human audit sample | `work/agent_memory_experiment/generate_human_audit_sample.py` | Creates stratified manual-review sample for error-analysis reliability. |
| Human audit summary | `work/agent_memory_experiment/summarize_human_audit.py` | Summarizes manual labels once the audit CSV is filled. |
| LLM-assisted audit | `work/agent_memory_experiment/llm_audit_retrieval_errors.py` | Uses DeepSeek to draft audit labels for human review; does not replace human audit. |
| Human/LLM audit confirmation | `work/agent_memory_experiment/confirm_llm_audit_labels.py` | Creates a human-confirmation sheet and summarizes agreement after manual labels are filled. |
| Human/LLM priority20 audit | `work/agent_memory_experiment/generate_priority_audit_subset.py` | Selects a 20-sample quick-review subset and reuses the agreement workflow. |
| Blinded human audit sheets | `work/agent_memory_experiment/blind_human_audit_labels.py` | Exports blind review sheets that hide LLM-assisted labels and can merge human labels back. |
| Human audit review packet | `work/agent_memory_experiment/generate_human_audit_review_packet.py` | Renders a readable Markdown review packet from the blinded priority20 sheet without exposing LLM-assisted labels. |
| Human audit annotation codebook | `work/agent_memory_experiment/generate_human_audit_annotation_codebook.py` | Defines yes/partial/no label rules, manual reason labels, dual-annotation flow, and paper-claim boundaries. |
| Human audit execution plan | `work/agent_memory_experiment/generate_human_audit_execution_plan.py` | Turns the pending human-audit blocker into ordered labeling, dual-review, adjudication, and paper-refresh steps. |
| Human audit sample QC | `work/agent_memory_experiment/validate_human_audit_sample_qc.py` | Checks sample count, duplicate audit IDs, query/error/rank coverage, and pending human-label progress. |
| Human audit labeling dashboard | `work/agent_memory_experiment/generate_human_audit_labeling_dashboard.py` | Lists per-row missing human_* fields and the next priority/full80 items to label. |
| Human audit annotation interface | `work/agent_memory_experiment/generate_human_audit_annotation_interface.py` | Generates offline HTML annotation forms for priority20/full80 blind-review sheets with CSV export. |
| Human audit annotation interface validation | `work/agent_memory_experiment/validate_human_audit_annotation_interface.py` | Checks that annotation HTML matches blind CSV rows and hides LLM-assisted label fields. |
| Human audit annotation import readiness | `work/agent_memory_experiment/validate_human_audit_annotation_import.py` | Checks exported annotation CSVs before merging human labels into confirmation and agreement reports. |
| Human audit paper-claim upgrade gate | `work/agent_memory_experiment/validate_human_audit_paper_claim_upgrade.py` | Maps current human-audit evidence to protocol-only, quick-review, full-review, and human-verified paper claim tiers. |
| Human audit blind review leakage audit | `work/agent_memory_experiment/validate_human_audit_blind_review.py` | Checks that blinded review sheets hide LLM-assisted labels and keep a stable labeling schema. |
| Dual human audit agreement | `work/agent_memory_experiment/dual_human_audit_agreement.py` | Prepares two-annotator review sheets and reports exact agreement, partial-credit agreement, and Cohen's kappa. |
| Human audit readiness gate | `work/agent_memory_experiment/validate_human_audit_readiness.py` | Checks whether priority20/full80 human confirmations can support paper claims. |
| Evidence matrix | `work/agent_memory_experiment/generate_evidence_matrix.py` | Summarizes paper claims, evidence strength, and remaining gaps. |
| Paper draft outline | `work/agent_memory_experiment/generate_paper_draft_outline.py` | Builds a Chinese paper skeleton from current evidence, formulas, and result tables. |
| Paper manuscript draft | `work/agent_memory_experiment/generate_paper_manuscript.py` | Generates an editable Chinese manuscript draft from cached experiment outputs. |
| Paper manuscript claim check | `work/agent_memory_experiment/validate_manuscript_claims.py` | Checks that the draft does not overclaim pending embedding or human-audit results. |
| Paper manuscript numeric claim check | `work/agent_memory_experiment/validate_manuscript_numeric_claims.py` | Checks that key manuscript numbers match current paper tables and statistical artifacts. |
| Paper scope claim audit | `work/agent_memory_experiment/validate_paper_scope_claims.py` | Audits paper-facing documents for LoCoMo10 scope, external baseline, human-audit, production-scale, and agent-task overclaims. |
| Threats to validity appendix | `work/agent_memory_experiment/generate_threats_to_validity_appendix.py` | Builds a paper appendix of internal/external/construct/statistical validity threats and claim boundaries. |
| Reviewer response preparation matrix | `work/agent_memory_experiment/generate_reviewer_response_prep.py` | Maps likely reviewer questions to current evidence, remaining gaps, and safe paper-writing boundaries. |
| Submission package index | `work/agent_memory_experiment/generate_submission_package_index.py` | Indexes manuscript, tables, appendices, reproducibility artifacts, blockers, and final packaging actions. |
| Submission entrypoint consistency audit | `work/agent_memory_experiment/validate_submission_entrypoint_consistency.py` | Checks that README, package index, and reproducibility entrypoints all point to the current submission readiness artifact. |
| Submission readiness gate | `work/agent_memory_experiment/validate_submission_readiness.py` | Aggregates reproducibility, baseline, human-audit, and reviewer-risk gates before final submission. |
| Public release readiness gate | `work/agent_memory_experiment/validate_public_release_readiness.py` | Scans tracked files for secret-like strings, .env hygiene, release metadata, and artifact links. |
| Untracked artifact audit | `work/agent_memory_experiment/audit_untracked_artifacts.py` | Classifies untracked local outputs and temporary data before public artifact packaging. |
| Large intermediate provenance audit | `work/agent_memory_experiment/validate_large_intermediate_provenance.py` | Explains large untracked ranked/per-query intermediates through README regeneration commands and tracked downstream summaries. |
| Artifact path portability audit | `work/agent_memory_experiment/validate_artifact_path_portability.py` | Checks tracked paper-facing reports for machine-local absolute paths before public artifact sharing. |
| Artifact integrity manifest | `work/agent_memory_experiment/generate_artifact_integrity_manifest.py` | Writes sha256, size, and line-count metadata for all reproducibility artifacts. |
| Submission gap analysis | `work/agent_memory_experiment/generate_submission_gap_analysis.py` | Ranks reviewer-facing risks and minimum actions before submission. |
| Submission blocker closure plan | `work/agent_memory_experiment/generate_submission_blocker_closure_plan.py` | Orders remaining external embedding, human audit, reviewer-risk, and final-refresh gates into a concrete closure path. |
| Paper artifact refresh run | `work/agent_memory_experiment/refresh_paper_artifacts.py` | Runs the offline cached paper-artifact refresh sequence and records step statuses. |
| Paper refresh coverage audit | `work/agent_memory_experiment/validate_paper_refresh_coverage.py` | Checks that the offline paper refresh run contains all required report-refresh steps. |
| Evidence freshness audit | `work/agent_memory_experiment/validate_evidence_freshness.py` | Checks paper-facing reports for stale reproducibility artifact/metric/integrity gate counts after regeneration. |
| Experiment protocol | `work/agent_memory_experiment/generate_experiment_protocol.py` | Builds a paper appendix-style protocol from cached metrics and artifacts. |
| Environment snapshot | `work/agent_memory_experiment/generate_environment_snapshot.py` | Records Python/package/cache/Git environment; does not read .env. |
| Environment freshness audit | `work/agent_memory_experiment/validate_environment_snapshot_freshness.py` | Checks whether the environment snapshot system CSV is present and records generation-time Git freshness. |
| Paper tables | `work/agent_memory_experiment/generate_paper_tables.py` | Generates Markdown and LaTeX tables from cached CSVs. |
| Paper table consistency audit | `work/agent_memory_experiment/validate_paper_table_consistency.py` | Regenerates paper tables in a temporary directory and compares current Markdown/LaTeX artifacts byte-for-byte. |

## 仍需补强

- DeepSeek 抽取重复实验已具备 3 个 completed run；后续可在额外数据集或更大 slice 上复验稳定性。
- 跨智能体/KV cache 仍需要真实或半真实 multi-agent trace。
- Type 3 需要更强 LLM 子问题生成或 listwise/setwise objective；当前浅层方法均为负结果。
- 如果投稿，需要把实验环境写成固定版本，包括 Python、sentence-transformers、FAISS/sklearn 版本和 BGE-M3 缓存来源。
