# Artifact Integrity Manifest

本文件为论文复现清单中的关键 artifact 生成 sha256、大小和行数，便于审稿复现、归档和后续检查结果文件是否被意外改动。

## 总览

- Source artifact list: `outputs/agent_memory_reproducibility_artifacts.csv`
- Artifacts covered: 84/84
- Missing artifacts: 0
- Self-referential checksum skips: 2
- Total bytes: 3010703

## 前 20 个 Artifact

| Label | Exists | Bytes | Lines | SHA256 Prefix | Checksum Status | Path |
| --- | --- | --- | --- | --- | --- | --- |
| Main baseline CSV | True | 1146 | 11 | c5873d9692fe | ok | outputs/agent_memory_baseline_comparison_locomo10.csv |
| LLM extraction report | True | 3431 | 47 | 098898236878 | ok | outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md |
| Writer stability report | True | 1780 | 36 | 9ab6d5462083 | ok | outputs/agent_memory_writer_stability_zh.md |
| Writer stability aggregate | True | 967 | 11 | a00fb4e1379c | ok | outputs/agent_memory_writer_stability_aggregate.csv |
| Writer stability runs | True | 924 | 4 | 13c91b80d653 | ok | outputs/agent_memory_writer_stability_runs.csv |
| Candidate reranker report | True | 2019 | 53 | 47c06dda556d | ok | outputs/agent_memory_candidate_reranker_locomo10_zh.md |
| Candidate reranker significance | True | 607 | 8 | 3d53a2fea54f | ok | outputs/agent_memory_candidate_reranker_significance_zh.md |
| Candidate reranker LOCO report | True | 3506 | 68 | 79e3f0650f02 | ok | outputs/agent_memory_candidate_reranker_loco_zh.md |
| Candidate reranker LOCO summary | True | 684 | 4 | 282d33bb4303 | ok | outputs/agent_memory_candidate_reranker_loco_summary.csv |
| Candidate reranker LOCO significance | True | 627 | 8 | 2de97cf4cd43 | ok | outputs/agent_memory_candidate_reranker_loco_significance_zh.md |
| Candidate reranker LOCO comparison | True | 316655 | 3677 | aab9dacd7900 | ok | outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv |
| Type3 coverage significance | True | 2545 | 24 | c8fb7374a144 | ok | outputs/agent_memory_type3_coverage_significance_zh.md |
| Type3 query decomposition fusion4 report | True | 5473 | 41 | 1e3b009e3d0d | ok | outputs/agent_memory_type3_query_decomposition_fusion4_zh.md |
| Type3 query decomposition fusion4 summary | True | 1604 | 4 | 4f94bd0a0302 | ok | outputs/agent_memory_type3_query_decomposition_fusion4_summary.csv |
| Type3 query decomposition fusion4 per-query | True | 48687 | 259 | b0f7e329cf1a | ok | outputs/agent_memory_type3_query_decomposition_fusion4_per_query.csv |
| Type3 query decomposition fusion4 facets | True | 43337 | 87 | 6db83e2028a8 | ok | outputs/agent_memory_type3_query_decomposition_fusion4_facets.csv |
| Type3 query decomposition fusion4 ranked top20 | True | 529533 | 3441 | aa104641f5ce | ok | outputs/agent_memory_type3_query_decomposition_fusion4_ranked_top20.csv |
| Type3 supervised selector rw0 report | True | 1936 | 38 | 968e6a1f0a13 | ok | outputs/agent_memory_type3_supervised_set_selector_rw0_zh.md |
| Type3 supervised selector rw0 split summary | True | 2563 | 26 | dfcff8f9f42b | ok | outputs/agent_memory_type3_supervised_set_selector_rw0_split_summary.csv |
| Type3 supervised selector rw0 summary | True | 1074 | 6 | f51e26c630e1 | ok | outputs/agent_memory_type3_supervised_set_selector_rw0_summary.csv |

## 使用说明

- 完整 sha256 位于 `outputs/agent_memory_artifact_integrity_manifest.csv`。
- manifest 自身的 CSV/报告属于自引用文件，`size_bytes`、`line_count` 记为 `0`，`sha256` 标记为 `self_referential`，不作为稳定校验哈希。
- 若重新生成实验结果，预期相关 artifact 的 sha256 会变化；应同时更新复现清单、证据矩阵和论文声明检查。
- 若没有重新运行实验而 sha256 变化，应检查是否存在非预期编辑或文件损坏。
