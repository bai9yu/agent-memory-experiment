# Untracked Artifact Audit

本文件审计当前工作树中的未跟踪文件，防止探索性输出、临时数据切片或 API smoke-test 结果误进入公开仓库或论文 artifact 包。它不删除文件，也不把这些文件自动加入 Git。

## 总览

- Untracked entries: 27
- Track as paper artifact: 4
- Review before tracking: 0
- Keep untracked/local: 23

## 明细

| Path | Category | Recommendation | Size Bytes | Reason |
| --- | --- | --- | --- | --- |
| work/agent_memory_experiment/data/llm_extracted_locomo_1s_v2/ | intermediate_llm_extraction_slice | keep_untracked | 43701 | Intermediate one-session extraction slice; not part of current LoCoMo10 paper package. |
| work/agent_memory_experiment/data/llm_extracted_locomo_1s_v2_d1_memories.jsonl | intermediate_llm_extraction_slice | keep_untracked | 4223 | Intermediate one-session extraction slice; not part of current LoCoMo10 paper package. |
| work/agent_memory_experiment/data/llm_extracted_locomo_1s_v2_d1_queries.jsonl | intermediate_llm_extraction_slice | keep_untracked | 1442 | Intermediate one-session extraction slice; not part of current LoCoMo10 paper package. |
| work/agent_memory_experiment/data/locomo_observation_d1_memories.jsonl | intermediate_observation_slice | keep_untracked | 27142 | Intermediate observation conversion slice; not part of tracked paper artifact set. |
| work/agent_memory_experiment/data/locomo_observation_d1_queries.jsonl | intermediate_observation_slice | keep_untracked | 18832 | Intermediate observation conversion slice; not part of tracked paper artifact set. |
| work/agent_memory_experiment/data/locomo_observation_record1_d1_v2_scope_memories.jsonl | intermediate_observation_slice | keep_untracked | 2598 | Intermediate observation conversion slice; not part of tracked paper artifact set. |
| work/agent_memory_experiment/data/locomo_observation_record1_d1_v2_scope_queries.jsonl | intermediate_observation_slice | keep_untracked | 1050 | Intermediate observation conversion slice; not part of tracked paper artifact set. |
| outputs/agent_memory_multi_evidence_coverage_top20_per_query.csv | large_per_query_intermediate | keep_untracked | 857416 | Detailed per-query diagnostic audited by agent_memory_large_intermediate_provenance; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_candidate_reranker_loco_ranked_top20.csv | large_ranked_intermediate | keep_untracked | 4670518 | Large ranked intermediate audited by agent_memory_large_intermediate_provenance; regenerate from README commands and rely on tracked downstream summaries. |
| outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv | large_ranked_intermediate | keep_untracked | 6737780 | Large ranked intermediate audited by agent_memory_large_intermediate_provenance; regenerate from README commands and rely on tracked downstream summaries. |
| outputs/agent_memory_set_selection_ranked.csv | large_ranked_intermediate | keep_untracked | 6289166 | Large ranked intermediate audited by agent_memory_large_intermediate_provenance; regenerate from README commands and rely on tracked downstream summaries. |
| outputs/agent_memory_set_selection_top20_ranked.csv | large_ranked_intermediate | keep_untracked | 12717839 | Large ranked intermediate audited by agent_memory_large_intermediate_provenance; regenerate from README commands and rely on tracked downstream summaries. |
| outputs/agent_memory_type3_coverage_aware_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 65616 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_coverage_aware_ranked_top20.csv | large_type3_coverage_intermediate | keep_untracked | 690164 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_expanded_pool_selector_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 102961 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_expanded_pool_selector_ranked_top20.csv | large_type3_coverage_intermediate | keep_untracked | 6800615 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_intent_fusion_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 159104 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_intent_fusion_ranked_top20.csv | large_type3_coverage_intermediate | keep_untracked | 3176243 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_recall_expansion_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 356356 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_rescue_space_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 18613 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_supervised_window_per_query.csv | large_type3_coverage_intermediate | keep_untracked | 31505 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| outputs/agent_memory_type3_supervised_window_ranked_top20.csv | large_type3_coverage_intermediate | keep_untracked | 814794 | Detailed Type3 coverage-aware intermediate; tracked summary/delta/report carry paper-facing evidence. |
| work/agent_memory_experiment/data/deepseek_smoke_test/ | local_smoke_test_data | keep_untracked | 45402 | DeepSeek smoke-test cache/output should stay local unless explicitly anonymized and documented. |
| outputs/agent_memory_type3_expanded_pool_selector_deltas.csv | release_audit_artifact | track_as_paper_artifact | 996 | New public-release audit support file; track with the paper artifact package. |
| outputs/agent_memory_type3_expanded_pool_selector_summary.csv | release_audit_artifact | track_as_paper_artifact | 1830 | New public-release audit support file; track with the paper artifact package. |
| outputs/agent_memory_type3_expanded_pool_selector_zh.md | release_audit_artifact | track_as_paper_artifact | 2117 | New public-release audit support file; track with the paper artifact package. |
| work/agent_memory_experiment/type3_expanded_pool_selector.py | release_audit_artifact | track_as_paper_artifact | 25748 | New public-release audit support file; track with the paper artifact package. |

## 使用边界

- 可以写：公开发布前已经审计未跟踪文件，避免把本地临时数据误作为论文 artifact。
- 可以写：`track_as_paper_artifact` 文件属于本轮新增的公开发布审计支撑文件，提交后不再计入未跟踪风险。
- 应谨慎：`review_before_tracking` 并不表示文件有问题，只表示需要补 generator/provenance/index 后再纳入论文包。
- 不能写：这些未跟踪输出已经全部通过论文质量门禁或人工验证。
