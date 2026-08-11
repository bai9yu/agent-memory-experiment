# Paired Outcome 与效应量分析

本报告补充 bootstrap CI 之外的效应解释：同一 query/seed 配对中，候选方法相对 baseline 到底有多少样本变好、变差或不变，并给出 paired Cohen's dz。它用于回答“平均提升是否由少数样本拉动”以及“收益集中在哪些 query type”。

## intrinsic_only_vs_type_aware

### Overall

| Metric | Baseline | Candidate | ΔMean | Cohen dz | Improved/Worse/Tie | Net Positive Rate | Win/Loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| mrr | 0.6067 | 0.6719 | 0.0652 | 0.2234 | 771/591/1398 | 0.0652 | 1.3046 |
| recall@1 | 0.4989 | 0.5685 | 0.0696 | 0.1670 | 342/150/2268 | 0.0696 | 2.2800 |
| recall@3 | 0.6696 | 0.7464 | 0.0768 | 0.2033 | 311/99/2350 | 0.0768 | 3.1414 |
| recall@5 | 0.7333 | 0.8014 | 0.0681 | 0.1888 | 280/92/2388 | 0.0681 | 3.0435 |

### Query Type Breakdown

| Query Type | Metric | Pairs | ΔMean | Cohen dz | Improved/Worse/Tie | Net Positive Rate |
|---|---|---:|---:|---:|---:|---:|
| 1 | mrr | 413 | 0.0039 | 0.0101 | 131/159/123 | -0.0678 |
| 1 | recall@5 | 413 | 0.0315 | 0.0664 | 53/40/320 | 0.0315 |
| 2 | mrr | 466 | 0.0812 | 0.3295 | 110/44/312 | 0.1416 |
| 2 | recall@5 | 466 | 0.0644 | 0.2250 | 35/5/426 | 0.0644 |
| 3 | mrr | 126 | -0.0021 | -0.0083 | 31/54/41 | -0.1825 |
| 3 | recall@5 | 126 | -0.0476 | -0.1199 | 7/13/106 | -0.0476 |
| 4 | mrr | 1096 | 0.0667 | 0.2638 | 285/158/653 | 0.1159 |
| 4 | recall@5 | 1096 | 0.0757 | 0.2175 | 111/28/957 | 0.0757 |
| 5 | mrr | 659 | 0.1026 | 0.3311 | 214/176/269 | 0.0577 |
| 5 | recall@5 | 659 | 0.1032 | 0.3098 | 74/6/579 | 0.1032 |

### Interpretation

- MRR: improved/worse/tie=771/591/1398，net positive rate=0.0652，Cohen dz=0.2234。
- Recall@5: improved/worse/tie=280/92/2388，net positive rate=0.0681，Cohen dz=0.1888。
- 该分析仍基于 LoCoMo10 answerable slice，不能替代外部数据集泛化或人工复核。
