# 多证据覆盖分析

本报告评估 Top-K 候选集合对答案 evidence set 的覆盖情况，特别用于分析 Type 3 多证据/推理类 query。

## 按 Query Type 统计 @ 5

| Query Type | Rows | Mean Gold | Multi-Evidence Share | Base Any | Reranker Any | Base Full | Reranker Full | Base Ratio | Reranker Ratio | Delta Ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Type 1 | 413 | 4.06 | 0.930 | 0.661 | 0.707 | 0.077 | 0.102 | 0.309 | 0.352 | 0.0430 |
| Type 2 | 466 | 1.56 | 0.399 | 0.833 | 0.895 | 0.590 | 0.670 | 0.707 | 0.781 | 0.0740 |
| Type 3 | 126 | 2.65 | 0.675 | 0.548 | 0.492 | 0.230 | 0.262 | 0.377 | 0.372 | -0.0050 |
| Type 4 | 1096 | 1.44 | 0.340 | 0.793 | 0.846 | 0.587 | 0.640 | 0.688 | 0.744 | 0.0565 |
| Type 5 | 659 | 1.50 | 0.354 | 0.645 | 0.756 | 0.470 | 0.555 | 0.552 | 0.652 | 0.1000 |

## Type 3 覆盖变化案例

| Query | Gold | Base Full@5 | Reranker Full@5 | Base Ratio@5 | Reranker Ratio@5 | Delta Ratio@5 |
|---|---:|---:|---:|---:|---:|---:|
| Did John and James study together? | 1 | 0.000 | 1.000 | 0.000 | 1.000 | 1.0000 |
| Would Melanie likely enjoy the song "The Four Seasons" by Vivaldi? | 1 | 0.000 | 1.000 | 0.000 | 1.000 | 1.0000 |
| Which major holiday season conincides with Evan's wedding? | 1 | 0.000 | 1.000 | 0.000 | 1.000 | 1.0000 |
| Would Melanie likely enjoy the song "The Four Seasons" by Vivaldi? | 1 | 0.000 | 1.000 | 0.000 | 1.000 | 1.0000 |
| Which outdoor gear company likely signed up John for an endorsement deal? | 2 | 0.000 | 1.000 | 0.500 | 1.000 | 0.5000 |
| Would Melanie go on another roadtrip soon? | 2 | 0.000 | 1.000 | 0.500 | 1.000 | 0.5000 |
| What underlying condition might Joanna have based on her allergies? | 3 | 0.000 | 1.000 | 0.667 | 1.000 | 0.3333 |
| What might John's degree be in? | 3 | 0.000 | 1.000 | 0.667 | 1.000 | 0.3333 |
| What underlying condition might Joanna have based on her allergies? | 3 | 0.000 | 1.000 | 0.667 | 1.000 | 0.3333 |
| What underlying condition might Joanna have based on her allergies? | 3 | 0.000 | 1.000 | 0.667 | 1.000 | 0.3333 |
| How many hikes has Joanna been on? | 3 | 0.000 | 0.000 | 0.000 | 0.667 | 0.6667 |
| Does James live in Connecticut? | 2 | 0.000 | 0.000 | 0.000 | 0.500 | 0.5000 |

## 解释

- `Any` 表示 Top-K 至少命中一条 evidence；`Full` 表示 Top-K 覆盖该 query 的全部 evidence；`Ratio` 表示覆盖比例。
- 如果 Type 3 的 Full/Ratio 没有提升，即使总体 MRR 上升，也说明单候选重排没有解决多证据聚合。
- 下一步应在 candidate reranker 之后增加 set-level selection 或 query decomposition，而不是只继续优化 Top-1。
