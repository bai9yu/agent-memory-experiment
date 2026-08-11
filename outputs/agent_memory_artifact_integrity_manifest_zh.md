# Artifact Integrity Manifest

本文件为论文复现清单中的关键 artifact 生成 sha256、大小和行数，便于审稿复现、归档和后续检查结果文件是否被意外改动。

## 总览

- Source artifact list: `outputs/agent_memory_reproducibility_artifacts.csv`
- Artifacts covered: 131/131
- Missing artifacts: 0
- Self-referential checksum skips: 2
- Total bytes: 6188615

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
| Candidate reranker feature ablation report | True | 3225 | 52 | 26995f86ad2b | ok | outputs/agent_memory_candidate_reranker_feature_ablation_zh.md |
| Candidate reranker feature ablation summary | True | 2034 | 11 | b9331061399f | ok | outputs/agent_memory_candidate_reranker_feature_ablation_summary.csv |
| Candidate reranker feature ablation split summary | True | 5458 | 51 | 36853fd8c0fa | ok | outputs/agent_memory_candidate_reranker_feature_ablation_split_summary.csv |
| Candidate reranker feature ablation deltas | True | 1407 | 10 | 51b2e15e43b6 | ok | outputs/agent_memory_candidate_reranker_feature_ablation_deltas.csv |
| Candidate reranker feature ablation comparison | True | 1724236 | 24841 | de37c8ae840f | ok | outputs/agent_memory_candidate_reranker_feature_ablation_comparison_per_query.csv |
| Candidate reranker paired effect-size report | True | 1912 | 35 | 8db941101e8a | ok | outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md |
| Candidate reranker paired effect-size CSV | True | 6383 | 25 | 35a35c2968dc | ok | outputs/agent_memory_candidate_reranker_paired_effect_size.csv |
| Candidate reranker seed stability report | True | 2058 | 38 | b8e8ecc22ba8 | ok | outputs/agent_memory_candidate_reranker_seed_stability_zh.md |
| Candidate reranker seed stability summary | True | 682 | 4 | a5a2589cb075 | ok | outputs/agent_memory_candidate_reranker_seed_stability_summary.csv |
| Candidate reranker seed stability deltas | True | 612 | 3 | db25ff72961b | ok | outputs/agent_memory_candidate_reranker_seed_stability.csv |
| Candidate reranker seed stability split summary | True | 6086 | 61 | 66789519edd1 | ok | outputs/agent_memory_candidate_reranker_seed_stability_split_summary.csv |
| Candidate reranker train-fraction sensitivity report | True | 2558 | 46 | 36acb7a58ab7 | ok | outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md |
| Candidate reranker train-fraction sensitivity summary | True | 2399 | 13 | 1a3f77dc6eb7 | ok | outputs/agent_memory_candidate_reranker_train_fraction_summary.csv |

## 使用说明

- 完整 sha256 位于 `outputs/agent_memory_artifact_integrity_manifest.csv`。
- manifest 自身的 CSV/报告属于自引用文件，`size_bytes`、`line_count` 记为 `0`，`sha256` 标记为 `self_referential`，不作为稳定校验哈希。
- 若重新生成实验结果，预期相关 artifact 的 sha256 会变化；应同时更新复现清单、证据矩阵和论文声明检查。
- 若没有重新运行实验而 sha256 变化，应检查是否存在非预期编辑或文件损坏。
