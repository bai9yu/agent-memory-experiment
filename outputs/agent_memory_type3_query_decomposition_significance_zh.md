# 配对显著性检验

| 指标 | Baseline | Candidate | Delta | 95% Bootstrap CI | Permutation p-value | 改善 | 变差 | 持平 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| mrr | type_aware | type_aware_plus_decomposition | -0.086721 | [-0.137611, -0.044229] | 0.0002 | 17 | 40 | 29 |
| recall@1 | type_aware | type_aware_plus_decomposition | -0.127907 | [-0.197674, -0.058140] | 0.0010 | 0 | 11 | 75 |
| recall@3 | type_aware | type_aware_plus_decomposition | -0.046512 | [-0.116279, 0.011628] | 0.2817 | 2 | 6 | 78 |
| recall@5 | type_aware | type_aware_plus_decomposition | -0.034884 | [-0.093023, 0.011628] | 0.3789 | 1 | 4 | 81 |
