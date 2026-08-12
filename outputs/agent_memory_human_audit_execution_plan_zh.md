# Human Audit Execution Plan

本文件把人工复核 blocker 拆成可执行步骤，用于从当前 protocol-ready 状态推进到论文可报告的人类一致性证据。它不自动填写人工标签，也不把 LLM-assisted 预标注当成人工结果。

## 总览

- Pending execution steps: 5/5
- priority20 blind samples: 20
- full80 blind samples: 80
- 当前论文边界：未完成人工标签前，只能写 human confirmation protocol，不能写 human-verified error analysis。

## 执行步骤

| Step | Stage | Status | Artifact To Edit | Current Evidence | Pass Condition |
| --- | --- | --- | --- | --- | --- |
| 1 | priority20 single blind labeling | pending | outputs/agent_memory_human_audit_priority20_blind_review.csv | confirmed=0/20; missing_fields=60; invalid=0 | 20/20 samples have valid human_* labels after merge and agreement recomputation. |
| 2 | priority20 dual independent labeling | pending | outputs/agent_memory_human_audit_priority20_dual_review.csv | both_labeled=0/20; adjudicated=0/20 | Both annotators complete 20 rows; conflicts are adjudicated when needed. |
| 3 | full80 single blind labeling | pending | outputs/agent_memory_human_audit_full80_blind_review.csv | confirmed=0/80; missing_fields=240; invalid=0 | 80/80 samples have valid human_* labels after merge and agreement recomputation. |
| 4 | full80 dual independent labeling | pending | outputs/agent_memory_human_audit_full80_dual_review.csv | both_labeled=0/80; adjudicated=0/80 | Both annotators complete 80 rows and adjudication is complete. |
| 5 | paper refresh after human labels | waiting_on_labels | generated reports | Current paper-facing reports correctly state human audit is pending. | No stale evidence findings; manuscript claim check has 0 failures; submission readiness human gates pass. |

## 标注字段

- `human_auto_reason_correct`: yes / partial / no，用于判断自动错误类型是否合理。
- `human_top_memory_relevant`: yes / partial / no，用于判断 top memory 是否支持 query。
- `human_gold_memory_sufficient`: yes / no / unclear，用于判断 gold memory 是否足够。
- `human_manual_reason`: 推荐短标签，如 gold_below_top20、memory_type_mismatch、temporal_neighbor、entity_confusion、multi_evidence_missing、gold_insufficient、other。
- `human_auditor_notes`: 写出触发判断的关键词、时间线、人物或冲突证据。

## 一致性指标公式

令第 `i` 个样本在某字段上的人工标签为 `h_i`，LLM-assisted 标签为 `l_i`：

- Exact agreement: `A_exact = (1/N) * sum_i 1[h_i = l_i]`。
- Partial-credit agreement: 对 yes/partial/no，可设 `s(yes, partial)=0.5`、`s(no, partial)=0.5`、完全一致为 1、yes/no 冲突为 0，然后 `A_partial = (1/N) * sum_i s(h_i, l_i)`。
- Cohen's kappa: `kappa = (p_o - p_e) / (1 - p_e)`，其中 `p_o` 是观测一致率，`p_e` 是按边际分布计算的随机一致率。

## 推荐执行顺序

1. 先填 `outputs/agent_memory_human_audit_priority20_blind_review.csv`，形成 quick-review 结果。
2. 再填 `outputs/agent_memory_human_audit_priority20_dual_review.csv`，若只有一位标注者，可先跳过双人一致性，但论文措辞要更保守。
3. priority20 通过后扩展到 full80；最终投稿建议至少完成 full80 single blind labeling。
4. 每次人工字段更新后，重新运行 codebook 中的 merge/agreement/readiness 命令，并刷新 submission readiness。

## 命令附录

以下命令来自 execution plan CSV 的 `command` 字段。它们只用于回填、汇总和刷新已经由人工填写好的标签；不会自动生成或伪造人工标签。

### Step 1 priority20 single blind labeling

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

work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_readiness.py \
  --full-confirmation outputs/agent_memory_human_llm_audit_confirmation.csv \
  --priority-confirmation outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --output-csv outputs/agent_memory_human_audit_readiness_gate.csv \
  --output-report outputs/agent_memory_human_audit_readiness_gate_zh.md
```

### Step 2 priority20 dual independent labeling

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_protocol_compliance.py \
  --outputs-dir outputs \
  --output-csv outputs/agent_memory_human_audit_protocol_compliance.csv \
  --output-report outputs/agent_memory_human_audit_protocol_compliance_zh.md
```

### Step 3 full80 single blind labeling

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/blind_human_audit_labels.py merge \
  --scope full80 \
  --confirmation-csv outputs/agent_memory_human_llm_audit_confirmation.csv \
  --blind-csv outputs/agent_memory_human_audit_full80_blind_review.csv \
  --output-confirmation-csv outputs/agent_memory_human_llm_audit_confirmation.csv \
  --output-report outputs/agent_memory_human_audit_full80_blind_review_zh.md

work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/confirm_llm_audit_labels.py \
  --llm-audit-csv outputs/agent_memory_llm_audit_sample_type_aware.csv \
  --confirmation-csv outputs/agent_memory_human_llm_audit_confirmation.csv \
  --output-summary-csv outputs/agent_memory_human_llm_audit_agreement.csv \
  --output-report outputs/agent_memory_human_llm_audit_agreement_zh.md

work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_readiness.py \
  --full-confirmation outputs/agent_memory_human_llm_audit_confirmation.csv \
  --priority-confirmation outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \
  --output-csv outputs/agent_memory_human_audit_readiness_gate.csv \
  --output-report outputs/agent_memory_human_audit_readiness_gate_zh.md
```

### Step 4 full80 dual independent labeling

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_protocol_compliance.py \
  --outputs-dir outputs \
  --output-csv outputs/agent_memory_human_audit_protocol_compliance.csv \
  --output-report outputs/agent_memory_human_audit_protocol_compliance_zh.md
```

### Step 5 paper refresh after human labels

```bash
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/refresh_paper_artifacts.py \
  --project-root . \
  --output-csv outputs/agent_memory_paper_artifact_refresh_run.csv \
  --output-report outputs/agent_memory_paper_artifact_refresh_run_zh.md
```

## 论文写法门槛

- 0/20：只能写“人工复核协议与盲审表已准备”。
- 20/20：可以写“priority20 quick-review agreement”，但不能代表完整错误分析。
- 80/80：可以写“full80 Human/LLM audit agreement”。
- 80/80 + 双人/仲裁完成：可以更稳健地写“human-verified error analysis”。
