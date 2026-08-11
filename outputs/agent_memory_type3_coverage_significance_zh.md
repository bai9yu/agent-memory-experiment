# Type 3 Evidence Coverage 显著性汇总

本报告只检验 evidence coverage 指标，用于补充 MRR/Recall 的显著性分析。所有检验均为 paired bootstrap CI 和 paired permutation test。

| Experiment | Candidate | Metric | Baseline | Candidate Mean | Delta | 95% Bootstrap CI | p-value | 改善 | 变差 | 持平 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| type3_specific_reranker | type3_specific_reranker | coverage_ratio@5 | 0.3775 | 0.3308 | -0.0467 | [-0.0938, -0.0026] | 0.0474 | 11 | 21 | 94 |
| type3_specific_reranker | type3_specific_reranker | full_coverage@5 | 0.2302 | 0.2063 | -0.0238 | [-0.0794, 0.0317] | 0.5855 | 5 | 8 | 113 |
| type3_specific_reranker | type3_specific_reranker | coverage_ratio@20 | 0.5260 | 0.5452 | 0.0192 | [-0.0309, 0.0700] | 0.4653 | 19 | 18 | 89 |
| type3_specific_reranker | type3_specific_reranker | full_coverage@20 | 0.3730 | 0.4127 | 0.0397 | [-0.0317, 0.1111] | 0.3781 | 13 | 8 | 105 |
| supervised_set_selector | supervised_set_selector | coverage_ratio@5 | 0.3775 | 0.3203 | -0.0572 | [-0.1106, -0.0062] | 0.0286 | 14 | 25 | 87 |
| supervised_set_selector | supervised_set_selector | full_coverage@5 | 0.2302 | 0.1746 | -0.0556 | [-0.1190, 0.0000] | 0.1224 | 4 | 11 | 111 |
| supervised_set_selector | supervised_set_selector | coverage_ratio@20 | 0.5260 | 0.5360 | 0.0101 | [-0.0374, 0.0570] | 0.6823 | 15 | 13 | 98 |
| supervised_set_selector | supervised_set_selector | full_coverage@20 | 0.3730 | 0.3810 | 0.0079 | [-0.0476, 0.0714] | 1.0000 | 8 | 7 | 111 |
| query_decomposition_fusion | type_aware_plus_decomposition | coverage_ratio@5 | 0.3699 | 0.3374 | -0.0325 | [-0.0657, -0.0070] | 0.0198 | 1 | 8 | 77 |
| query_decomposition_fusion | type_aware_plus_decomposition | full_coverage@5 | 0.2326 | 0.2093 | -0.0233 | [-0.0581, 0.0000] | 0.4931 | 0 | 2 | 84 |
| query_decomposition_fusion | type_aware_plus_decomposition | coverage_ratio@20 | 0.5368 | 0.5368 | 0.0000 | [0.0000, 0.0000] | 1.0000 | 0 | 0 | 86 |
| query_decomposition_fusion | type_aware_plus_decomposition | full_coverage@20 | 0.3721 | 0.3721 | 0.0000 | [0.0000, 0.0000] | 1.0000 | 0 | 0 | 86 |

## 结论

- 如果 Coverage@5 显著下降，说明方法不仅排序变差，也没有改善多证据前排覆盖。
- 如果 Coverage@20 持平但 Coverage@5 下降，说明候选空间没有扩大，或者扩大的信号没有被排到前面。
- 当前 Type 3 后续应优先考虑更强 query decomposition 或 listwise/setwise objective，而不是继续堆浅层候选上下文特征。
