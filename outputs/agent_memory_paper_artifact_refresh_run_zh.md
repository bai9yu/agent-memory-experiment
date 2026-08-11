# Paper Artifact Refresh Run

本文件记录一次论文 artifact 离线刷新流水线的执行结果。该流水线只调用本地已缓存结果和无网络脚本；不会运行真实外部 embedding API，也不会自动填写人工标签。

## 总览

- Dry run: False
- Include environment snapshot: False
- Steps: 16
- Failures: 0

## Step Results

| Step | Status | Return Code | Duration Sec | Notes |
| --- | --- | --- | --- | --- |
| offline_embedding_sensitivity | pass | 0 | 0.023 | Refreshes offline hash/BM25 vs BGE-M3 encoder-sensitivity diagnostics. |
| human_audit_execution_plan | pass | 0 | 0.021 | Refreshes the human-audit labeling execution plan from current gates. |
| submission_blocker_closure_plan | pass | 0 | 0.021 | Refreshes the ordered closure path for final-submission blockers. |
| submission_package_index | pass | 0 | 0.022 | Refreshes the index of manuscript, tables, appendices, gates, and packaging actions. |
| reproducibility_checklist | pass | 0 | 0.044 | Refreshes artifact and metric gates. |
| artifact_integrity_manifest | pass | 0 | 0.039 | Refreshes artifact sha256/size/line-count manifest. |
| evidence_matrix | pass | 0 | 0.028 | Refreshes paper claim/evidence/gap matrix. |
| submission_gap_analysis | pass | 0 | 0.023 | Refreshes reviewer-facing risk matrix. |
| submission_readiness | pass | 0 | 0.023 | Refreshes final-submission gates. |
| reviewer_response_prep | pass | 0 | 0.027 | Refreshes reviewer question/answer preparation matrix. |
| paper_manuscript | pass | 0 | 0.028 | Refreshes Chinese manuscript draft from current evidence. |
| manuscript_claim_check | pass | 0 | 0.023 | Checks that manuscript does not overclaim pending baselines/audits. |
| evidence_freshness | pass | 0 | 0.024 | Checks stale artifact/metric/integrity gate counts. |
| paper_refresh_coverage | pass | 0 | 0.021 | Checks that the offline refresh run covers all required paper-facing reports. |
| artifact_integrity_manifest_final | pass | 0 | 0.039 | Final manifest refresh after freshness audit changes. |
| submission_readiness_final | pass | 0 | 0.023 | Final submission gate refresh after manifest changes. |

## 使用边界

- 可以用于补完 API baseline 或人工标签后的最终报告刷新。
- 不能替代真实外部 embedding baseline，也不能替代人工审计填写。
- 如果刷新后 artifact 数变化，应再次运行 freshness audit 并检查 submission readiness。
