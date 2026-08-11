# 配对显著性检验

| 指标 | Baseline | Candidate | Delta | 95% Bootstrap CI | Permutation p-value | 改善 | 变差 | 持平 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| mrr | type_aware | candidate_reranker | 0.053877 | [0.046229, 0.061895] | 0.0002 | 691 | 498 | 1571 |
| recall@1 | type_aware | candidate_reranker | 0.056884 | [0.045290, 0.068841] | 0.0002 | 214 | 57 | 2489 |
| recall@3 | type_aware | candidate_reranker | 0.062681 | [0.050362, 0.074638] | 0.0002 | 238 | 65 | 2457 |
| recall@5 | type_aware | candidate_reranker | 0.062319 | [0.050000, 0.074638] | 0.0002 | 241 | 69 | 2450 |
