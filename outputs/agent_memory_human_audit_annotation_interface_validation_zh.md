# Human Audit Annotation Interface Validation

本文件检查离线 HTML 标注界面是否和盲审 CSV 同步，是否保留必要 human_* 字段，以及是否没有泄漏 LLM-assisted 预标注字段。

## 总览

- Checks: 14
- Blockers: 0
- Major issues: 0
- Annotation interface safe: True

## 检查明细

| Scope | Check | Pass | Severity | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| priority20 | html_exists | True | blocker | outputs/agent_memory_human_audit_priority20_annotation.html, size=26223 | Regenerate annotation interface HTML. |
| priority20 | embedded_rows_parseable | True | blocker | embedded_rows=20 | Fix HTML generator so embedded row JSON is parseable. |
| priority20 | row_count_matches_source | True | blocker | source_rows=20, embedded_rows=20 | Regenerate HTML from the current blind review CSV. |
| priority20 | audit_id_order_matches_source | True | major | first_source_ids=['audit_050', 'audit_076', 'audit_020'], first_embedded_ids=['audit_050', 'audit_076', 'audit_020'] | Regenerate HTML without reordering or dropping review rows. |
| priority20 | no_llm_assisted_label_tokens | True | blocker | no forbidden llm label tokens | Remove LLM-assisted label fields from the annotation interface. |
| priority20 | human_fields_present | True | blocker | all human fields present | Regenerate HTML with all required human_* form fields. |
| priority20 | download_button_present | True | major | downloadCsv and export button present | Regenerate HTML with an export/download control. |
| full80 | html_exists | True | blocker | outputs/agent_memory_human_audit_full80_annotation.html, size=71948 | Regenerate annotation interface HTML. |
| full80 | embedded_rows_parseable | True | blocker | embedded_rows=80 | Fix HTML generator so embedded row JSON is parseable. |
| full80 | row_count_matches_source | True | blocker | source_rows=80, embedded_rows=80 | Regenerate HTML from the current blind review CSV. |
| full80 | audit_id_order_matches_source | True | major | first_source_ids=['audit_039', 'audit_009', 'audit_069'], first_embedded_ids=['audit_039', 'audit_009', 'audit_069'] | Regenerate HTML without reordering or dropping review rows. |
| full80 | no_llm_assisted_label_tokens | True | blocker | no forbidden llm label tokens | Remove LLM-assisted label fields from the annotation interface. |
| full80 | human_fields_present | True | blocker | all human fields present | Regenerate HTML with all required human_* form fields. |
| full80 | download_button_present | True | major | downloadCsv and export button present | Regenerate HTML with an export/download control. |

## 使用边界

- 可以写：HTML 标注界面与当前盲审表同步，且未暴露 LLM-assisted 预标注字段。
- 不能写：该校验通过就表示人工标注已完成；它只证明标注入口可用。
