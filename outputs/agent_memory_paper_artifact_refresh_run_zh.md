# Paper Artifact Refresh Run

本文件记录一次论文 artifact 离线刷新流水线的执行结果。该流水线只调用本地已缓存结果和无网络脚本；不会运行真实外部 embedding API，也不会自动填写人工标签。

## 总览

- Dry run: False
- Include environment snapshot: False
- Steps: 47
- Failures: 0

## Step Results

| Step | Status | Return Code | Duration Sec | Notes |
| --- | --- | --- | --- | --- |
| offline_embedding_sensitivity | pass | 0 | 0.040 | Refreshes offline hash/BM25 vs BGE-M3 encoder-sensitivity diagnostics. |
| human_audit_execution_plan | pass | 0 | 0.040 | Refreshes the human-audit labeling execution plan from current gates. |
| human_audit_annotation_codebook | pass | 0 | 0.042 | Refreshes the human-audit annotation codebook, allowed labels, formulas, and recomputation commands. |
| human_audit_sample_qc | pass | 0 | 0.044 | Checks priority20/full80 human-audit sample size, uniqueness, coverage, and labeling progress. |
| human_audit_labeling_dashboard | pass | 0 | 0.044 | Refreshes per-row human-audit labeling progress and next-item dashboard. |
| human_audit_annotation_interface | pass | 0 | 0.047 | Generates offline HTML annotation interfaces for priority20/full80 blind-review sheets. |
| human_audit_annotation_interface_validation | pass | 0 | 0.048 | Validates that generated annotation HTML matches blind CSVs and hides LLM-assisted labels. |
| human_audit_annotation_import_readiness | pass | 0 | 0.049 | Checks whether HTML-exported human labels are ready to merge into confirmation sheets. |
| human_audit_paper_claim_upgrade | pass | 0 | 0.047 | Checks which paper-facing human-audit claim tier is currently unlocked. |
| human_audit_blind_review_leakage | pass | 0 | 0.047 | Checks that blinded human-audit review sheets do not expose LLM-assisted labels and follow the expected schema. |
| human_audit_protocol_compliance | pass | 0 | 0.049 | Checks that human-audit samples, schemas, codebook, interfaces, import checks, and claim gates form a protocol-ready package. |
| embedding_baseline_status | pass | 0 | 0.045 | Refreshes external embedding key/result status without printing keys. |
| embedding_provider_profiles | pass | 0 | 0.048 | Refreshes provider-specific preflight, estimate, run, and compare commands. |
| api_embedding_preflight | pass | 0 | 0.077 | Refreshes paid/API embedding preflight without network calls. |
| api_embedding_run_estimate | pass | 0 | 0.076 | Refreshes API embedding item/token/batch estimate without network calls. |
| api_embedding_execution_runbook | pass | 0 | 0.046 | Generates the external API embedding baseline runbook without starting paid/network calls. |
| embedding_baseline_comparison | pass | 0 | 0.044 | Refreshes BGE-M3 vs API embedding comparison status from local summaries. |
| api_embedding_postrun_gate | pass | 0 | 0.046 | Checks whether any API embedding run has complete paper-ready local outputs. |
| api_embedding_paper_acceptance | pass | 0 | 0.049 | Strictly checks API embedding result scale, metrics, per-query rows, rankings, by-type coverage, and comparison deltas before paper citation. |
| external_embedding_blocker_audit | pass | 0 | 0.046 | Refreshes actionable blocker audit for external embedding baselines. |
| embedding_paper_claim_upgrade | pass | 0 | 0.046 | Checks which paper-facing embedding-baseline claim tier is currently unlocked. |
| submission_blocker_closure_plan | pass | 0 | 0.042 | Refreshes the ordered closure path for final-submission blockers. |
| submission_closure_consistency | pass | 0 | 0.047 | Checks closure plan, final checklist, readiness, reviewer prep, and strict API acceptance for consistent blocker standards. |
| submission_package_index | pass | 0 | 0.046 | Refreshes the index of manuscript, tables, appendices, gates, and packaging actions. |
| supplementary_package_manifest | pass | 0 | 0.062 | Builds a supplement packaging manifest with blocker and anonymization checks. |
| anonymous_submission_readiness | pass | 0 | 0.057 | Checks anonymous-submission readiness for current supplement candidates. |
| paper_table_consistency | pass | 0 | 0.120 | Checks that paper Markdown/LaTeX tables are byte-identical to regenerated CSV-derived outputs. |
| untracked_artifact_audit | pass | 0 | 0.072 | Classifies untracked local outputs before public artifact packaging. |
| large_intermediate_provenance | pass | 0 | 0.299 | Audits large local ranked/per-query intermediates against README commands and tracked downstream summaries. |
| artifact_path_portability | pass | 0 | 0.457 | Checks tracked paper-facing reports for machine-local absolute paths before artifact sharing. |
| public_release_readiness | pass | 0 | 1.031 | Refreshes tracked-file release hygiene checks after untracked artifact audit. |
| reproducibility_checklist | pass | 0 | 0.109 | Refreshes artifact and metric gates. |
| artifact_integrity_manifest | pass | 0 | 0.108 | Refreshes artifact sha256/size/line-count manifest. |
| evidence_matrix | pass | 0 | 0.070 | Refreshes paper claim/evidence/gap matrix. |
| submission_gap_analysis | pass | 0 | 0.057 | Refreshes reviewer-facing risk matrix. |
| submission_readiness | pass | 0 | 0.058 | Refreshes final-submission gates. |
| final_submission_checklist | pass | 0 | 0.058 | Refreshes the action-oriented final-submission checklist. |
| reviewer_response_prep | pass | 0 | 0.067 | Refreshes reviewer question/answer preparation matrix. |
| paper_manuscript | pass | 0 | 0.065 | Refreshes Chinese manuscript draft from current evidence. |
| manuscript_claim_check | pass | 0 | 0.055 | Checks that manuscript does not overclaim pending baselines/audits. |
| manuscript_numeric_claim_check | pass | 0 | 0.073 | Checks that key numeric manuscript claims match current paper artifacts. |
| paper_scope_claim_audit | pass | 0 | 0.062 | Audits paper-facing documents for scope and generalization overclaims. |
| evidence_freshness | pass | 0 | 0.056 | Checks stale artifact/metric/integrity gate counts. |
| submission_entrypoint_consistency | pass | 0 | 0.051 | Checks that README/package/reproducibility entrypoints point to the current submission readiness artifact. |
| paper_refresh_coverage | pass | 0 | 0.044 | Checks that the offline refresh run covers all required paper-facing reports. |
| artifact_integrity_manifest_final | pass | 0 | 0.091 | Final manifest refresh after freshness audit changes. |
| submission_readiness_final | pass | 0 | 0.050 | Final submission gate refresh after manifest changes. |

## 使用边界

- 可以用于补完 API baseline 或人工标签后的最终报告刷新。
- 不能替代真实外部 embedding baseline，也不能替代人工审计填写。
- 如果刷新后 artifact 数变化，应再次运行 freshness audit 并检查 submission readiness。
