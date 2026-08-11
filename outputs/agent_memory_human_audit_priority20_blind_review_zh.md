# Blinded Human Audit Sheet

本文件记录盲审人工复核表的导出/回填状态。盲审表隐藏 LLM-assisted 预标注，只保留 query、top memory、gold memory 和待填写的 human_* 字段，用于降低人工审核被 LLM 标签锚定的风险。

## 状态

- Scope: `priority20`
- Mode: `export`
- Samples: 20
- Fully confirmed: 0
- Validation errors: 0
- blind_csv: `outputs/agent_memory_human_audit_priority20_blind_review.csv`
- source_confirmation: `outputs/agent_memory_human_llm_audit_priority20_confirmation.csv`
- seed: `20260811`
- keep_order: `False`

## 盲审填写说明

- 只填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。
- `human_auto_reason_correct` / `human_top_memory_relevant` 允许：`yes`、`partial`、`no`。
- `human_gold_memory_sufficient` 允许：`yes`、`no`、`unclear`。
- 填完盲审表后用 `merge` 模式回填确认表，再运行 agreement 和 readiness gate。

## 论文使用判断

- 盲审流程可以写入实验协议，说明人工复核不直接暴露 LLM 预标注。
- 在人工字段未完成前，仍不能宣称 human-verified error analysis。
