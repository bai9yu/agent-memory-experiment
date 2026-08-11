# Candidate Depth Analysis

本报告比较不同 Top-K 深度下的 evidence coverage，用于判断 Type 3 是候选池不足还是排序/集合选择不足。

## Type 3 Depth Curve

| K | Base Coverage | Reranker Coverage | Delta Coverage | Base Full | Reranker Full | Delta Full |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.167 | 0.182 | 0.0146 | 0.063 | 0.079 | 0.0159 |
| 3 | 0.332 | 0.316 | -0.0157 | 0.190 | 0.198 | 0.0079 |
| 5 | 0.377 | 0.372 | -0.0050 | 0.230 | 0.262 | 0.0317 |
| 10 | 0.459 | 0.462 | 0.0029 | 0.317 | 0.325 | 0.0079 |
| 20 | 0.526 | 0.597 | 0.0711 | 0.373 | 0.444 | 0.0714 |

## All Query Types @20

| Query Type | Base Coverage@20 | Reranker Coverage@20 | Delta | Base Full@20 | Reranker Full@20 | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Type 1 | 0.539 | 0.625 | 0.0861 | 0.223 | 0.283 | 0.0605 |
| Type 2 | 0.845 | 0.885 | 0.0404 | 0.753 | 0.790 | 0.0365 |
| Type 3 | 0.526 | 0.597 | 0.0711 | 0.373 | 0.444 | 0.0714 |
| Type 4 | 0.843 | 0.874 | 0.0312 | 0.752 | 0.793 | 0.0411 |
| Type 5 | 0.670 | 0.708 | 0.0378 | 0.580 | 0.615 | 0.0349 |

## Interpretation

- Type 3 在 Top-5 上没有改善，但在 Top-20 上 candidate reranker 的 coverage ratio 明显超过 fixed `type_aware`。
- 这说明相关 evidence 并非完全缺失，而是常落在较深候选位置；下一步应扩大候选召回并做 set-level selection。
- 简单 Top-10 MMR 失败并不否定集合选择方向，它说明需要在更深候选池和更明确的覆盖目标上做集合选择。
