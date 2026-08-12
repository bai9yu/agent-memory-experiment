# Submission Package Consistency Audit

本文件检查 submission package index、supplementary package manifest、reproducibility artifact list 和 integrity manifest 是否互相覆盖。它用于防止投稿打包时漏掉索引文件、把过期文件误放进 supplement，或让索引 artifact 脱离 sha256 manifest。

## 总览

- Checks: 9
- Blockers: 0
- Major issues: 0
- Package artifacts consistent: True

## 明细

| Check | Pass | Status | Evidence | Action |
| --- | --- | --- | --- | --- |
| package_index_exists | True | pass | path=outputs/agent_memory_submission_package_index.csv, rows=30 | Regenerate the submission package index. |
| indexed_artifacts_exist | True | pass | all indexed artifacts exist | Regenerate missing artifacts or remove stale rows from the package index. |
| supplement_manifest_covers_index | True | pass | missing_from_supplement=[] | Regenerate the supplementary package manifest from the current package index. |
| supplement_manifest_has_no_extra_artifacts | True | pass | extra_in_supplement=[] | Regenerate the supplementary package manifest so it mirrors the package index. |
| indexed_artifacts_tracked_in_reproducibility | True | pass | missing_from_reproducibility=[] | Add indexed artifacts to generate_reproducibility_checklist.py or remove stale package-index rows. |
| indexed_artifacts_in_integrity_manifest | True | pass | missing_from_integrity=[] | Regenerate reproducibility checklist and artifact integrity manifest after package-index changes. |
| supplement_manifest_file_flags_match_disk | True | pass | supplement_missing_files=[] | Regenerate missing files or update the package index before packaging. |
| supplement_manifest_repro_flags_match_repro_list | True | pass | supplement_untracked=[] | Ensure package artifacts are tracked in the reproducibility artifact list. |
| supplement_manifest_anonymization_clean | True | pass | anonymization_findings=[] | Resolve anonymization findings before treating current supplement candidates as anonymous-submission ready. |

## 使用边界

- 可以写：当前 package index 中的 artifact 均存在，并由 supplement manifest、reproducibility checklist 和 integrity manifest 覆盖。
- 不能写：package consistency 通过就代表实验 blocker 已解除；它只证明打包索引和复现清单没有互相脱节。
