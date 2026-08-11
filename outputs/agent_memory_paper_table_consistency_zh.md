# Paper Table Consistency Audit

本文件检查论文表格 artifact 是否仍与缓存实验 CSV 一致。它会在临时目录中重新运行 `generate_paper_tables.py`，再把当前 Markdown/LaTeX 表格与重新生成结果做字节级比较。

## 总览

- Checks: 17
- Failures: 0
- Table artifacts match regenerated outputs: True

## 检查明细

| Check | Kind | Pass | Path | Evidence |
| --- | --- | --- | --- | --- |
| source_exists:agent_memory_baseline_comparison_locomo10.csv | source | True | outputs/agent_memory_baseline_comparison_locomo10.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_locomo10_summary.csv | source | True | outputs/agent_memory_candidate_reranker_locomo10_summary.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_significance_results.csv | source | True | outputs/agent_memory_candidate_reranker_significance_results.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_loco_summary.csv | source | True | outputs/agent_memory_candidate_reranker_loco_summary.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_loco_significance_results.csv | source | True | outputs/agent_memory_candidate_reranker_loco_significance_results.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_intrinsic_loco_summary.csv | source | True | outputs/agent_memory_candidate_reranker_intrinsic_loco_summary.csv | source CSV exists |
| source_exists:agent_memory_candidate_reranker_feature_ablation_deltas.csv | source | True | outputs/agent_memory_candidate_reranker_feature_ablation_deltas.csv | source CSV exists |
| source_exists:agent_memory_type3_specific_reranker_summary.csv | source | True | outputs/agent_memory_type3_specific_reranker_summary.csv | source CSV exists |
| source_exists:agent_memory_type3_supervised_set_selector_summary.csv | source | True | outputs/agent_memory_type3_supervised_set_selector_summary.csv | source CSV exists |
| source_exists:agent_memory_type3_query_decomposition_summary.csv | source | True | outputs/agent_memory_type3_query_decomposition_summary.csv | source CSV exists |
| source_exists:agent_memory_type3_coverage_significance_summary.csv | source | True | outputs/agent_memory_type3_coverage_significance_summary.csv | source CSV exists |
| source_exists:agent_memory_sklearn_nn_prefilter_locomo10_summary.csv | source | True | outputs/agent_memory_sklearn_nn_prefilter_locomo10_summary.csv | source CSV exists |
| markdown_matches_regenerated | markdown | True | outputs/agent_memory_paper_tables_zh.md | byte-identical to regenerated table artifact |
| latex_matches_regenerated | latex | True | outputs/agent_memory_paper_tables.tex | byte-identical to regenerated table artifact |
| markdown_table_sections_present | structure | True | outputs/agent_memory_paper_tables_zh.md | markdown sections=11 |
| latex_table_count | structure | True | outputs/agent_memory_paper_tables.tex | latex tables=11 |
| latex_labels_unique | structure | True | outputs/agent_memory_paper_tables.tex | labels=11, unique=11 |

## 论文使用边界

- 可以写：当前论文表格由缓存 CSV 生成，并通过独立一致性审计。
- 应谨慎：该审计只证明表格和 CSV 一致，不证明实验设计本身已解除外部 embedding 或人工审计 blocker。
