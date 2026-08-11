# Supplementary Package Manifest

本文件把当前论文提交包索引转成补充材料打包清单。它区分可进入当前 supplement 的 artifact、只供内部审查的 gate、因 blocker 暂缓的实验报告，并扫描匿名投稿前常见身份/本地路径风险。

## 总览

- Indexed artifacts: 30
- Include in current supplement: 12
- Internal/review gates or protocol-only artifacts: 15
- Exclude until blocker closed: 3
- Missing indexed artifacts: 0
- Anonymization findings: 0
- Submission blockers still open: 5

## 打包明细

| Section | Artifact | Bucket | Include Now | Status | Anonymization Findings |
| --- | --- | --- | --- | --- | --- |
| Manuscript | outputs/agent_memory_manuscript_draft_zh.md | main_paper_candidate | True | ready_for_internal_review | none |
| Main Tables | outputs/agent_memory_paper_tables_zh.md | main_paper_candidate | True | ready | none |
| Main Tables | outputs/agent_memory_paper_tables.tex | main_paper_candidate | True | ready | none |
| Method Appendix | outputs/agent_memory_intrinsic_reranker_method_appendix_zh.md | supplement_candidate | True | ready | none |
| Method Appendix | outputs/agent_memory_candidate_reranker_seed_stability_zh.md | supplement_candidate | True | ready | none |
| Method Appendix | outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md | supplement_candidate | True | ready | none |
| Method Appendix | outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md | supplement_candidate | True | ready | none |
| Method Appendix | outputs/agent_memory_candidate_oracle_gap_analysis_zh.md | supplement_candidate | True | ready | none |
| Experiment Protocol | outputs/agent_memory_experiment_protocol_zh.md | supplement_candidate | True | ready | none |
| Evidence Matrix | outputs/agent_memory_paper_evidence_matrix_zh.md | internal_review_gate | False | ready | none |
| Paper Tables | outputs/agent_memory_paper_table_consistency_zh.md | supplement_candidate | True | ready | none |
| Threats to Validity | outputs/agent_memory_threats_to_validity_zh.md | supplement_candidate | True | ready_with_blockers_declared | none |
| Reviewer Prep | outputs/agent_memory_reviewer_response_prep_zh.md | internal_review_gate | False | ready_with_blockers_declared | none |
| External Embedding | outputs/agent_memory_external_embedding_blocker_audit_zh.md | exclude_until_blocker_closed | False | blocked | none |
| External Embedding | outputs/agent_memory_api_embedding_postrun_gate_zh.md | exclude_until_blocker_closed | False | blocked_until_api_run | none |
| External Embedding | outputs/agent_memory_offline_embedding_sensitivity_zh.md | protocol_or_diagnostic_candidate | True | ready_diagnostic | none |
| Human Audit | outputs/agent_memory_human_audit_annotation_codebook_zh.md | protocol_appendix_candidate | False | ready_for_labeling | none |
| Human Audit | outputs/agent_memory_human_audit_execution_plan_zh.md | protocol_appendix_candidate | False | ready_for_labeling | none |
| Human Audit | outputs/agent_memory_human_audit_sample_qc_zh.md | protocol_appendix_candidate | False | ready_qc | none |
| Human Audit | outputs/agent_memory_human_audit_labeling_dashboard_zh.md | protocol_appendix_candidate | False | ready_for_labeling | none |
| Human Audit | outputs/agent_memory_human_audit_priority20_review_packet_zh.md | protocol_appendix_candidate | False | ready_for_labeling | none |
| Reproducibility | outputs/agent_memory_reproducibility_checklist_zh.md | internal_review_gate | False | pass | none |
| Reproducibility | outputs/agent_memory_artifact_integrity_manifest_zh.md | internal_review_gate | False | pass | none |
| Reproducibility | outputs/agent_memory_environment_freshness_audit_zh.md | internal_review_gate | False | pass | none |
| Reproducibility | outputs/agent_memory_untracked_artifact_audit_zh.md | internal_review_gate | False | classified | none |
| Reproducibility | outputs/agent_memory_paper_artifact_refresh_run_zh.md | internal_review_gate | False | pass | none |
| Reproducibility | outputs/agent_memory_paper_refresh_coverage_audit_zh.md | internal_review_gate | False | pass | none |
| Submission Gate | outputs/agent_memory_submission_blocker_closure_plan_zh.md | internal_review_gate | False | ready_with_external_inputs | none |
| Submission Gate | outputs/agent_memory_submission_entrypoint_consistency_zh.md | internal_review_gate | False | ready | none |
| Submission Gate | outputs/agent_memory_submission_readiness_zh.md | exclude_until_blocker_closed | False | not_ready | none |

## 使用边界

- `include_in_current_supplement=True` 表示当前内部/非匿名补充材料候选；最终匿名投稿仍要按会议模板去除作者信息。
- `internal_review_gate` 适合留在仓库或 rebuttal 准备材料中，不一定适合提交为 supplement。
- `exclude_until_blocker_closed` 在外部 embedding 或人工审计完成前不应作为已完成实验结果进入 supplement。
- 该 manifest 不压缩文件、不复制文件，只提供可复现打包决策。
