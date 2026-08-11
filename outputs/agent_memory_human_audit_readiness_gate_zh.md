# Human Audit Readiness 门禁

本文件检查 Human/LLM 确认表是否已经足以支撑论文中的人工复核声明。它不自动填写人工标签，也不把 LLM-assisted 预标注当成人工结果。

## 总览

- blocker 数：2
- priority20 confirmed：0/20
- full80 confirmed：0/80

| Scope | Exists | Samples | Confirmed | Required | Rate | Missing Fields | Invalid Labels | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| priority20 | True | 20 | 0 | 20 | 0.000 | 60 | 0 | pending_human_confirmation |
| full80 | True | 80 | 0 | 80 | 0.000 | 240 | 0 | pending_human_confirmation |

## 论文声明门槛

- `priority20` 达到 20/20 且无非法标签后，可以写为小样本人工抽查或 quick-review agreement。
- `full80` 达到 80/80 且无非法标签后，才可以写为完整 Human/LLM error-audit agreement。
- 在任一门槛未达成前，论文只能写 LLM-assisted audit draft / human confirmation protocol。

## 当前 blocker

- priority20 人工抽查尚未达到最小可报告阈值。
- full80 完整人工确认尚未达到完整 human-verified error analysis 阈值。

## 待填写样例

### priority20
- audit_002(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_006(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_007(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_009(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_010(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_019(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_020(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_025(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_031(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_034(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_040(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_045(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_050(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_051(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_055(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_056(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_069(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_075(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_076(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_077(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)

### full80
- audit_001(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_002(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_003(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_004(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_005(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_006(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_007(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_008(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_009(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_010(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_011(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_012(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_013(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_014(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_015(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_016(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_017(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_018(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_019(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
- audit_020(human_auto_reason_correct,human_top_memory_relevant,human_gold_memory_sufficient)
