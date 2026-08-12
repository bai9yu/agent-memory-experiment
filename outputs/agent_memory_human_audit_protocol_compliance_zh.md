# Human Audit Protocol Compliance

本文件检查人工审计流程是否已经具备论文级可执行性：样本、盲审隔离、标注字段、HTML 标注入口、导入检查、协议文档和 claim tier 都必须闭环。它不填写人工标签，也不把 protocol-ready 误写成人工审计完成。

## 总览

- Checks: 32
- Blockers: 0
- Major issues: 0
- Protocol ready for human labeling: True
- Human labels completed: False

## 检查明细

| Group | Item | Pass | Status | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| protocol_documentation | codebook_exists | True | pass | outputs/agent_memory_human_audit_annotation_codebook_zh.md, size=8945 | Regenerate the human-audit annotation codebook. |
| protocol_documentation | codebook_fields_and_labels | True | pass | missing=none | Add required fields, reason labels, and agreement terminology to the codebook. |
| protocol_documentation | codebook_decision_flow | True | pass | flowchart TD present | Add a decision flow so annotators follow a stable order. |
| protocol_documentation | codebook_recompute_commands | True | pass | merge/agreement commands present | Add merge and agreement recomputation commands to the codebook. |
| sample_design | sample_counts | True | pass | priority20=20/20; full80=80/80 | Regenerate priority20/full80 samples with expected row counts. |
| sample_design | sample_unique_ids | True | pass | priority20_duplicates=0; full80_duplicates=0 | Regenerate audit IDs before collecting labels. |
| sample_design | sample_coverage | True | pass | failed_coverage_checks=0 | Check auto-reason, query-type, and rank-bucket coverage before labeling. |
| blind_review_schema | priority20_blind_exists | True | pass | outputs/agent_memory_human_audit_priority20_blind_review.csv, rows=20 | Regenerate the human-audit CSV from the current audit sample. |
| blind_review_schema | priority20_blind_row_count | True | pass | rows=20, expected=20 | Regenerate the scope with the expected sample size. |
| blind_review_schema | priority20_blind_schema | True | pass | missing=none | Regenerate the CSV with the standard human-audit schema. |
| blind_review_schema | priority20_blind_audit_ids_unique | True | pass | duplicates=[], blank_ids=0 | Regenerate the CSV so each row has one stable non-empty audit_id. |
| blind_review_schema | full80_blind_exists | True | pass | outputs/agent_memory_human_audit_full80_blind_review.csv, rows=80 | Regenerate the human-audit CSV from the current audit sample. |
| blind_review_schema | full80_blind_row_count | True | pass | rows=80, expected=80 | Regenerate the scope with the expected sample size. |
| blind_review_schema | full80_blind_schema | True | pass | missing=none | Regenerate the CSV with the standard human-audit schema. |
| blind_review_schema | full80_blind_audit_ids_unique | True | pass | duplicates=[], blank_ids=0 | Regenerate the CSV so each row has one stable non-empty audit_id. |
| dual_review_schema | priority20_dual_exists | True | pass | outputs/agent_memory_human_audit_priority20_dual_review.csv, rows=20 | Regenerate the human-audit CSV from the current audit sample. |
| dual_review_schema | priority20_dual_row_count | True | pass | rows=20, expected=20 | Regenerate the scope with the expected sample size. |
| dual_review_schema | priority20_dual_schema | True | pass | missing=none | Regenerate the CSV with the standard human-audit schema. |
| dual_review_schema | priority20_dual_audit_ids_unique | True | pass | duplicates=[], blank_ids=0 | Regenerate the CSV so each row has one stable non-empty audit_id. |
| dual_review_schema | full80_dual_exists | True | pass | outputs/agent_memory_human_audit_full80_dual_review.csv, rows=80 | Regenerate the human-audit CSV from the current audit sample. |
| dual_review_schema | full80_dual_row_count | True | pass | rows=80, expected=80 | Regenerate the scope with the expected sample size. |
| dual_review_schema | full80_dual_schema | True | pass | missing=none | Regenerate the CSV with the standard human-audit schema. |
| dual_review_schema | full80_dual_audit_ids_unique | True | pass | duplicates=[], blank_ids=0 | Regenerate the CSV so each row has one stable non-empty audit_id. |
| upstream_validation | blind_review_leakage_exists | True | pass | outputs/agent_memory_human_audit_blind_review_leakage.csv, rows=17 | Regenerate the upstream human-audit validation artifact. |
| upstream_validation | blind_review_leakage_no_protocol_blockers | True | pass | blockers=0, major=0, other_problem_statuses=[] | Fix protocol/schema/interface problems before sending the packet to annotators. |
| upstream_validation | annotation_interface_validation_exists | True | pass | outputs/agent_memory_human_audit_annotation_interface_validation.csv, rows=14 | Regenerate the upstream human-audit validation artifact. |
| upstream_validation | annotation_interface_validation_no_protocol_blockers | True | pass | blockers=0, major=0, other_problem_statuses=[] | Fix protocol/schema/interface problems before sending the packet to annotators. |
| upstream_validation | annotation_import_readiness_exists | True | pass | outputs/agent_memory_human_audit_annotation_import_readiness.csv, scopes=['full80', 'priority20'] | Regenerate annotation import readiness for priority20 and full80. |
| upstream_validation | annotation_import_pending_or_ready | True | pass | statuses={'priority20': 'pending_human_labels', 'full80': 'pending_human_labels'} | Fix invalid exported labels, row order, duplicate audit IDs, or schema mismatch before merge. |
| human_label_gate | protocol_only_claim_unlocked | True | pass | annotation interface and import readiness artifacts are tracked in the reproducibility package | Regenerate protocol artifacts before discussing human-audit protocol in the paper. |
| human_label_gate | priority20_labels_pending | True | pass | priority20 confirmed=0/20; claim_tier=pending | Fill priority20 human_* fields to unlock quick-review agreement. |
| human_label_gate | full80_labels_pending | True | pass | full80 confirmed=0/80; claim_tier=pending | Fill full80 human_* fields to unlock full Human/LLM audit agreement. |

## 论文使用边界

- 可以写：人工审计协议、盲审材料、标注界面、回填检查和 claim gate 已形成可复现闭环。
- 可以写：当前人审 blocker 是外部人工标签尚未填写，而不是协议或工程入口缺失。
- 不能写：human-verified error analysis、priority20 agreement 或 full80 agreement 已完成，除非相应 human_* 字段填写并重算 agreement。
