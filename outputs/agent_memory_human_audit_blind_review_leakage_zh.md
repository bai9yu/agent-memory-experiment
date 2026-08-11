# Human Audit Blind Review Leakage Audit

本文件检查 priority20/full80 盲审标注表是否适合交给人工标注者。它只验证表结构和泄露风险，不自动填写人工标签，也不把未标注样本写成人工结果。

## 总览

- Checks: 17
- Blockers: 0
- Major issues: 0
- Blind-review protocol safe: True

## 检查明细

| Scope | Check | Pass | Severity | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| priority20 | file_exists | True | blocker | outputs/agent_memory_human_audit_priority20_blind_review.csv | Regenerate the blind review CSV from the confirmation sheet. |
| priority20 | expected_row_count | True | blocker | rows=20, expected=20 | Regenerate the blind review sample with the expected scope size. |
| priority20 | no_llm_label_columns | True | blocker | no llm_* columns | Remove llm_* fields from the blind review sheet before labeling. |
| priority20 | expected_columns_present | True | blocker | all expected columns present | Regenerate the blind review sheet with the standard schema. |
| priority20 | no_extra_columns | True | major | no extra columns | Remove non-protocol columns or document why they are needed. |
| priority20 | audit_id_unique_nonempty | True | blocker | duplicates=[], blank_ids=0 | Regenerate the sheet so every row has one unique audit_id. |
| priority20 | review_order_contiguous | True | major | first_orders=[1, 2, 3, 4, 5], expected_len=20 | Regenerate or sort the sheet so review_order is 1..N. |
| priority20 | human_labels_not_prefilled | True | info | filled_required_human_label_cells=0 | If labels are already filled, this is not a leakage issue; run merge/agreement/readiness next. |
| full80 | file_exists | True | blocker | outputs/agent_memory_human_audit_full80_blind_review.csv | Regenerate the blind review CSV from the confirmation sheet. |
| full80 | expected_row_count | True | blocker | rows=80, expected=80 | Regenerate the blind review sample with the expected scope size. |
| full80 | no_llm_label_columns | True | blocker | no llm_* columns | Remove llm_* fields from the blind review sheet before labeling. |
| full80 | expected_columns_present | True | blocker | all expected columns present | Regenerate the blind review sheet with the standard schema. |
| full80 | no_extra_columns | True | major | no extra columns | Remove non-protocol columns or document why they are needed. |
| full80 | audit_id_unique_nonempty | True | blocker | duplicates=[], blank_ids=0 | Regenerate the sheet so every row has one unique audit_id. |
| full80 | review_order_contiguous | True | major | first_orders=[1, 2, 3, 4, 5], expected_len=80 | Regenerate or sort the sheet so review_order is 1..N. |
| full80 | human_labels_not_prefilled | True | info | filled_required_human_label_cells=0 | If labels are already filled, this is not a leakage issue; run merge/agreement/readiness next. |
| cross_scope | priority20_subset_of_full80 | True | major | priority20 ids are included in full80 | Regenerate priority20 from the full80 audit pool or explain the separate sample design. |

## 论文使用边界

- 可以写：人工复核使用不含 LLM 预标注列的盲审表，降低标注者被 LLM 标签锚定的风险。
- 不能写：该检查等同于人工复核完成；最终仍以 agreement/readiness gate 为准。
