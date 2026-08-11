# Paper Scope Claim Audit

本文件跨 README、正文草稿、实验协议、风险矩阵、有效性威胁和复现文档检查论文声明边界，防止把 LoCoMo10 检索实验过度写成跨数据集、生产规模或端到端 agent 成功结论。

## 总览

- Checks: 47
- Blockers: 0
- Major warnings: 0
- Scope-safe for current draft: True

## 检查明细

| Group | Item | Document | Severity | Pass | Evidence | Guidance |
| --- | --- | --- | --- | --- | --- | --- |
| document_presence | document_exists | README.md | info | True | chars=8126 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | README.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | README.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | README.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | README.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | README.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_manuscript_draft_zh.md | info | True | chars=8296 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_manuscript_draft_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_manuscript_draft_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_manuscript_draft_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_manuscript_draft_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_manuscript_draft_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_experiment_protocol_zh.md | info | True | chars=3177 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_experiment_protocol_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_experiment_protocol_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_experiment_protocol_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_experiment_protocol_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_experiment_protocol_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_submission_gap_analysis_zh.md | info | True | chars=6757 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_submission_gap_analysis_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_submission_gap_analysis_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_submission_gap_analysis_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_submission_gap_analysis_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_submission_gap_analysis_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_threats_to_validity_zh.md | info | True | chars=3904 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_threats_to_validity_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_threats_to_validity_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_threats_to_validity_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_threats_to_validity_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_threats_to_validity_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_reproducibility_checklist_zh.md | info | True | chars=39091 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_reproducibility_checklist_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_reproducibility_checklist_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_reproducibility_checklist_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_reproducibility_checklist_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_reproducibility_checklist_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| document_presence | document_exists | outputs/agent_memory_current_design_zh.md | info | True | chars=15729 | Document is available for scope-claim audit. |
| forbidden_overclaim | cross_dataset_generalization | outputs/agent_memory_current_design_zh.md | major | True | no unqualified overclaim found | 当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。 |
| forbidden_overclaim | external_embedding_completed | outputs/agent_memory_current_design_zh.md | blocker | True | no unqualified overclaim found | 外部 embedding baseline completed=0，不能写成已完成结果。 |
| forbidden_overclaim | human_verified_error_analysis | outputs/agent_memory_current_design_zh.md | blocker | True | no unqualified overclaim found | 人工确认仍为 0，不能写 human-verified error analysis。 |
| forbidden_overclaim | production_scale_validation | outputs/agent_memory_current_design_zh.md | major | True | no unqualified overclaim found | 100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。 |
| forbidden_overclaim | end_to_end_agent_success | outputs/agent_memory_current_design_zh.md | major | True | no unqualified overclaim found | 当前评估是 memory retrieval，不等同端到端 agent task success。 |
| required_boundary | locomo10_scope | outputs/agent_memory_manuscript_draft_zh.md;outputs/agent_memory_experiment_protocol_zh.md;outputs/agent_memory_submission_gap_analysis_zh.md;outputs/agent_memory_threats_to_validity_zh.md | major | True | LoCoMo10 answerable slice | 至少一个核心文档需要明确主结论限定在 LoCoMo10 answerable slice。 |
| required_boundary | external_embedding_pending | outputs/agent_memory_manuscript_draft_zh.md;outputs/agent_memory_submission_gap_analysis_zh.md | major | True | 外部 embedding baseline completed=0 | 至少一个核心文档需要明确外部 embedding baseline 尚未完成。 |
| required_boundary | human_audit_pending | outputs/agent_memory_manuscript_draft_zh.md;outputs/agent_memory_threats_to_validity_zh.md | major | True | 不能宣称 human-verified error analysis | 至少一个核心文档需要明确人工错误分析尚未 human-verified。 |
| required_boundary | synthetic_scaling_limit | outputs/agent_memory_manuscript_draft_zh.md;outputs/agent_memory_submission_gap_analysis_zh.md;outputs/agent_memory_threats_to_validity_zh.md | major | True | synthetic distractor | 至少一个核心文档需要说明大规模效率实验包含 synthetic distractor 限定。 |
| required_boundary | retrieval_not_agent_success | outputs/agent_memory_manuscript_draft_zh.md | major | True | 不等价于端到端 agent task success | 至少一个核心文档需要说明检索指标不等价于端到端 agent 成功。 |

## 论文使用边界

- 可以写：当前 paper-facing 文档的主要结论边界与 LoCoMo10 answerable slice、pending external embedding baseline、pending human audit 一致。
- 不能写：该审计通过就等于外部泛化、人工验证或生产级部署已经完成。
