# Artifact Integrity Manifest

本文件为论文复现清单中的关键 artifact 生成 sha256、大小和行数，便于审稿复现、归档和后续检查结果文件是否被意外改动。

## 总览

- Source artifact list: `outputs/agent_memory_reproducibility_artifacts.csv`
- Artifacts covered: 63/63
- Missing artifacts: 0
- Total bytes: 631262

## 前 20 个 Artifact

| Label | Exists | Bytes | Lines | SHA256 Prefix | Path |
| --- | --- | --- | --- | --- | --- |
| Main baseline CSV | True | 1146 | 11 | c5873d9692fe | outputs/agent_memory_baseline_comparison_locomo10.csv |
| LLM extraction report | True | 3431 | 47 | 098898236878 | outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md |
| Writer stability report | True | 1780 | 36 | 9ab6d5462083 | outputs/agent_memory_writer_stability_zh.md |
| Writer stability aggregate | True | 967 | 11 | a00fb4e1379c | outputs/agent_memory_writer_stability_aggregate.csv |
| Writer stability runs | True | 924 | 4 | 13c91b80d653 | outputs/agent_memory_writer_stability_runs.csv |
| Candidate reranker report | True | 2019 | 53 | 47c06dda556d | outputs/agent_memory_candidate_reranker_locomo10_zh.md |
| Candidate reranker significance | True | 607 | 8 | 3d53a2fea54f | outputs/agent_memory_candidate_reranker_significance_zh.md |
| Candidate reranker LOCO report | True | 3506 | 68 | 79e3f0650f02 | outputs/agent_memory_candidate_reranker_loco_zh.md |
| Candidate reranker LOCO summary | True | 684 | 4 | 282d33bb4303 | outputs/agent_memory_candidate_reranker_loco_summary.csv |
| Candidate reranker LOCO significance | True | 627 | 8 | 2de97cf4cd43 | outputs/agent_memory_candidate_reranker_loco_significance_zh.md |
| Candidate reranker LOCO comparison | True | 316655 | 3677 | aab9dacd7900 | outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv |
| Type3 coverage significance | True | 2545 | 24 | c8fb7374a144 | outputs/agent_memory_type3_coverage_significance_zh.md |
| Paper tables Markdown | True | 2832 | 78 | e4bcb650fa98 | outputs/agent_memory_paper_tables_zh.md |
| Paper tables LaTeX | True | 3994 | 137 | cb2a2e13914d | outputs/agent_memory_paper_tables.tex |
| Paper evidence matrix | True | 6662 | 44 | ec463cba4943 | outputs/agent_memory_paper_evidence_matrix_zh.md |
| Paper draft outline | True | 6827 | 106 | d1377186270a | outputs/agent_memory_paper_draft_outline_zh.md |
| Paper manuscript draft | True | 9893 | 121 | 121f04a66310 | outputs/agent_memory_manuscript_draft_zh.md |
| Paper manuscript claim check | True | 1827 | 23 | 83404a0e0e2b | outputs/agent_memory_manuscript_claim_check_zh.md |
| Paper manuscript claim check CSV | True | 1395 | 9 | b3f776f095fd | outputs/agent_memory_manuscript_claim_check.csv |
| Submission readiness gate | True | 2291 | 38 | 863e2a0471a6 | outputs/agent_memory_submission_readiness_gate_zh.md |

## 使用说明

- 完整 sha256 位于 `outputs/agent_memory_artifact_integrity_manifest.csv`。
- 若重新生成实验结果，预期相关 artifact 的 sha256 会变化；应同时更新复现清单、证据矩阵和论文声明检查。
- 若没有重新运行实验而 sha256 变化，应检查是否存在非预期编辑或文件损坏。
