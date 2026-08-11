# Manuscript Numeric Claim Audit

本文件检查论文正文中的关键数值声明是否能在当前 paper artifacts 中找到一致证据，覆盖主结果、显著性、oracle-gap、稳定性、存储 token 和 Type 3 负结果。

## 总览

- Numeric claim checks: 15
- Failures: 0
- Critical failures: 0
- Ready for citation: True

## 检查明细

| Claim | Group | Severity | Status | Source | Guidance |
| --- | --- | --- | --- | --- | --- |
| fact_type_aware_main | main_result | critical | pass | outputs/agent_memory_paper_tables_zh.md | 更新正文主结果或重新生成 paper tables。 |
| observation_type_aware_main | main_result | critical | pass | outputs/agent_memory_paper_tables_zh.md | 确认 observation memory 口径后更新正文。 |
| candidate_reranker_heldout | reranker | critical | pass | outputs/agent_memory_paper_tables_zh.md | 同步 held-out candidate reranker 主指标。 |
| intrinsic_reranker_heldout | reranker | critical | pass | outputs/agent_memory_paper_tables_zh.md | 同步 intrinsic-only ablation 主指标。 |
| intrinsic_reranker_loco | reranker | critical | pass | outputs/agent_memory_paper_tables_zh.md | 同步 LOCO intrinsic reranker 指标。 |
| type_aware_significance | significance | major | pass | outputs/agent_memory_type_aware_significance_zh.md | 同步 type-aware vs time-aware 显著性表述。 |
| candidate_significance | significance | critical | pass | outputs/agent_memory_paper_tables_zh.md | 同步 full candidate reranker 显著性。 |
| intrinsic_ci_claims | significance | critical | pass | outputs/agent_memory_bootstrap_metric_ci_zh.md | 同步 intrinsic reranker bootstrap CI。 |
| oracle_gap_claims | oracle_gap | major | pass | outputs/agent_memory_candidate_oracle_gap_analysis_zh.md | 同步 oracle-gap closure 口径。 |
| paired_outcome_claims | paired_effect | major | pass | outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md | 同步 paired improved/worsened/tied 数值。 |
| seed_stability_claims | stability | major | pass | outputs/agent_memory_candidate_reranker_seed_stability_zh.md | 同步 20-seed stability 结论。 |
| train_fraction_claims | stability | major | pass | outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md | 同步 train-fraction sensitivity 结论。 |
| loco_delta_ci_claims | significance | major | pass | outputs/agent_memory_bootstrap_metric_ci_zh.md | 同步 LOCO bootstrap CI。 |
| storage_writer_claims | storage | critical | pass | outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md | 同步存储 token 和 writer stability 口径。 |
| type3_boundary_claims | negative_result | critical | pass | outputs/agent_memory_type3_coverage_significance_zh.md | 同步 Type 3 边界和负结果数值。 |

## 使用边界

- 可以写：正文关键数值声明已通过自动一致性核对，并可追溯到当前 paper artifacts。
- 应谨慎：该审计只检查数值一致性，不替代外部 embedding baseline、人工标注或跨数据集验证。
- 不能写：数值一致性通过就代表最终投稿 blocker 已解除。
