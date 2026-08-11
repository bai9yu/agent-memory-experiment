# full80 双人 Human Audit Agreement

本文件用于把 retrieval error audit 从单人确认升级为双人独立标注与仲裁流程。它只统计人工字段，不使用 LLM-assisted 预标注作为人工结果。

## 状态

- 状态：`pending_dual_human_labels`
- 样本数：80
- A/B 均完成的样本数：0/80
- 已仲裁样本数：0/80
- 非法标签数：0

## A/B 一致性指标

| Field | Metric | Count | Total | Rate | Cohen Kappa |
| --- | --- | --- | --- | --- | --- |
| auto_reason_correct | exact | 0 | 0 | 0.000 |  |
| auto_reason_correct | partial_credit | 0.0 | 0 | 0.000 |  |
| auto_reason_correct | conflict | 0 | 0 | 0.000 |  |
| top_memory_relevant | exact | 0 | 0 | 0.000 |  |
| top_memory_relevant | partial_credit | 0.0 | 0 | 0.000 |  |
| top_memory_relevant | conflict | 0 | 0 | 0.000 |  |
| gold_memory_sufficient | exact | 0 | 0 | 0.000 |  |
| gold_memory_sufficient | partial_credit | 0.0 | 0 | 0.000 |  |
| gold_memory_sufficient | conflict | 0 | 0 | 0.000 |  |

## 标注规则

- `annotator_a_*` 与 `annotator_b_*` 由两名标注者独立填写，不参考彼此结果。
- `auto_reason_correct` / `top_memory_relevant` 允许：`yes`、`partial`、`no`。
- `gold_memory_sufficient` 允许：`yes`、`no`、`unclear`。
- A/B 冲突样本再填写 `adjudicated_*` 字段；论文主错误类型分布优先使用 adjudicated labels。

## 待填写样例

### Annotator A
- audit_039(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_009(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_069(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_010(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_052(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_047(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_014(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_064(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_080(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_076(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_031(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_071(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_066(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_051(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_034(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_016(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_022(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_046(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_054(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)
- audit_001(annotator_a_auto_reason_correct,annotator_a_top_memory_relevant,annotator_a_gold_memory_sufficient)

### Annotator B
- audit_039(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_009(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_069(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_010(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_052(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_047(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_014(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_064(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_080(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_076(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_031(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_071(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_066(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_051(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_034(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_016(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_022(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_046(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_054(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)
- audit_001(annotator_b_auto_reason_correct,annotator_b_top_memory_relevant,annotator_b_gold_memory_sufficient)

## 论文使用判断

- A/B 均完成后，可以报告 inter-annotator exact agreement 与 Cohen's kappa。
- 仲裁完成后，可以把 adjudicated labels 作为论文错误分析的人工确认结果。
- 在人工字段未完成前，本文件只能证明双人标注流程已准备好，不能宣称人工一致性已完成。
