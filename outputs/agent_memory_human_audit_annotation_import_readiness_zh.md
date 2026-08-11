# Human Audit Annotation Import Readiness

本文件检查 HTML 标注界面导出的 CSV 是否可以安全回填到 Human/LLM confirmation 表。它不自动生成或伪造人工标签；当前若 human_* 仍为空，会明确显示为 pending。

## 总览

- Scopes: 2
- Ready to merge: 0
- Pending or invalid: 2

## 检查明细

| Scope | Export Exists | Rows | Audit ID Order Match | Complete Labels | Invalid Labels | Status |
| --- | --- | --- | --- | --- | --- | --- |
| priority20 | True | 20/20 | True | 0 | 0 | pending_human_labels |
| full80 | True | 80/80 | True | 0 | 0 | pending_human_labels |

## 回填命令

priority20 完成后：

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/blind_human_audit_labels.py merge \
  --scope priority20 \
  --confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --blind-csv outputs/agent_memory_human_audit_priority20_blind_review.csv \
  --output-confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --output-report outputs/agent_memory_human_audit_priority20_blind_review_zh.md
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/confirm_llm_audit_labels.py \
  --llm-audit-csv outputs/agent_memory_llm_audit_sample_type_aware.csv \
  --audit-id-csv outputs/agent_memory_human_llm_audit_priority20_ids.csv \
  --confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --output-summary-csv outputs/agent_memory_human_llm_audit_priority20_agreement.csv \
  --output-report outputs/agent_memory_human_llm_audit_priority20_agreement_zh.md
```

full80 完成后使用同一流程，替换为 full80 对应 confirmation / blind review / agreement 文件。最后运行：

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_readiness.py \
  --full-confirmation outputs/agent_memory_human_llm_audit_confirmation.csv \
  --priority-confirmation outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --output-csv outputs/agent_memory_human_audit_readiness_gate.csv \
  --output-report outputs/agent_memory_human_audit_readiness_gate_zh.md
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_submission_readiness.py \
  --output-report outputs/agent_memory_submission_readiness_zh.md \
  --output-csv outputs/agent_memory_submission_readiness.csv
```

## 使用边界

- 可以写：人工标注结果回填前有 schema、audit_id 顺序、合法标签和完成度检查。
- 不能写：import readiness 通过前或人工字段为空时，错误分析已经 human-verified。
