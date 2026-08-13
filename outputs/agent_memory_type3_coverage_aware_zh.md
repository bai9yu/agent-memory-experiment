# Type 3 Coverage-Aware Reranking

本实验针对 Type 3 多证据问题，在已缓存的 candidate reranker Top-20 候选上做无监督 coverage-aware 选择。打分只使用候选分数、query token 覆盖、实体覆盖、memory type/session/agent 新颖性和文本冗余惩罚，不使用 gold evidence 调参。

## 参数

| Parameter | Value |
|---|---:|
| score | 1.0 |
| query_coverage | 0.35 |
| entity_coverage | 0.25 |
| type_novelty | 0.08 |
| session_novelty | 0.04 |
| agent_novelty | 0.02 |
| rank_prior | 0.1 |
| redundancy | 0.3 |

## Type 3 结果

| Method | Rows | MRR | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 0.418 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| coverage_aware_free | 126 | 0.414 | 0.444 | 0.333 | 0.222 | 0.597 | 0.444 |
| coverage_aware_keep_top1 | 126 | 0.414 | 0.444 | 0.333 | 0.222 | 0.597 | 0.444 |

## 相比 Candidate Reranker 的变化

| Method | ΔMRR | ΔR@5 | ΔCoverage@5 | ΔFull@5 | ΔCoverage@20 | ΔFull@20 |
|---|---:|---:|---:|---:|---:|---:|
| coverage_aware_free | -0.0044 | -0.0476 | -0.0396 | -0.0397 | 0.0000 | 0.0000 |
| coverage_aware_keep_top1 | -0.0044 | -0.0476 | -0.0396 | -0.0397 | 0.0000 | 0.0000 |

## 解释

- Coverage@5 最好的方法是 `candidate_reranker`，Coverage@5=`0.372`。
- MRR 最好的方法是 `candidate_reranker`，MRR=`0.418`。
- 如果 coverage-aware 方法仍不能提升 Coverage@5，说明仅凭无监督多样性和 query 覆盖信号不足以解决 Type 3，需要真正的 listwise/setwise 学习目标或更强 LLM 子问题分解。
- 如果它提升 Coverage@5 但损害 MRR，则可作为 recall/coverage-oriented reranking 的系统折中，而不是替代主排序器。
