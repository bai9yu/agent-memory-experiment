# Agent Memory Compression Analysis

This report compares raw memory against two compression variants across dataset sizes.

## Storage Ratios

| Run | Variant | Memories | Total Tokens | Token Ratio vs Raw |
|---|---|---:|---:|---:|
| compression_100 | raw | 100 | 1379 | 1.000 |
| compression_100 | fact | 100 | 599 | 0.434 |
| compression_100 | summary | 20 | 599 | 0.434 |
| compression_300 | raw | 300 | 4117 | 1.000 |
| compression_300 | fact | 300 | 1777 | 0.432 |
| compression_300 | summary | 60 | 1777 | 0.432 |
| compression_500 | raw | 500 | 6856 | 1.000 |
| compression_500 | fact | 500 | 2956 | 0.431 |
| compression_500 | summary | 100 | 2956 | 0.431 |

## Time-Aware Retrieval Under Compression

| Run | Variant | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|
| compression_100 | raw | 0.575 | 0.887 | 0.988 | 0.740 |
| compression_100 | fact | 0.525 | 0.750 | 0.875 | 0.674 |
| compression_100 | summary | 0.400 | 0.662 | 0.750 | 0.567 |
| compression_300 | raw | 0.338 | 0.646 | 0.750 | 0.529 |
| compression_300 | fact | 0.325 | 0.604 | 0.679 | 0.496 |
| compression_300 | summary | 0.183 | 0.367 | 0.463 | 0.327 |
| compression_500 | raw | 0.240 | 0.522 | 0.642 | 0.424 |
| compression_500 | fact | 0.235 | 0.507 | 0.615 | 0.406 |
| compression_500 | summary | 0.110 | 0.285 | 0.352 | 0.241 |

## Best Variant Per Run

| Run | Best Variant | Time-Aware Recall@1 | Time-Aware MRR |
|---|---|---:|---:|
| compression_100 | raw | 0.575 | 0.740 |
| compression_300 | raw | 0.338 | 0.529 |
| compression_500 | raw | 0.240 | 0.424 |

## Interpretation

- `fact` compression keeps one record per source memory and reduces token cost to roughly 43% of raw in these synthetic runs.
- `fact` preserves the time-aware ranking pattern better than grouped `summary` compression, especially at 300 and 500 memories.
- `summary` compression reduces the number of retrievable items by grouping five raw memories into one block, but it loses target precision and hurts Recall@3/MRR.
- For the project proposal direction, the first practical compression baseline should be fact-level memory extraction plus time-aware reranking; grouped summaries are better treated as a second-layer archival store.
