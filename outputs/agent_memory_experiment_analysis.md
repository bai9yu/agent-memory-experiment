# Agent Memory Experiment Analysis

This report compares the offline first-stage memory retrieval runs.

## Overall Results

| Run | Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---|---:|---:|---:|---:|---:|
| sample_10 | hybrid | 0.800 | 0.900 | 1.000 | 0.875 | 10 |
| sample_10 | time_aware | 0.800 | 0.900 | 1.000 | 0.875 | 10 |
| sample_10 | vector | 0.800 | 0.900 | 1.000 | 0.870 | 10 |
| synthetic_100 | hybrid | 0.400 | 0.825 | 0.988 | 0.637 | 80 |
| synthetic_100 | time_aware | 0.575 | 0.887 | 0.988 | 0.740 | 80 |
| synthetic_100 | vector | 0.400 | 0.825 | 0.988 | 0.637 | 80 |
| synthetic_300 | hybrid | 0.200 | 0.546 | 0.721 | 0.438 | 240 |
| synthetic_300 | time_aware | 0.338 | 0.646 | 0.750 | 0.529 | 240 |
| synthetic_300 | vector | 0.175 | 0.525 | 0.700 | 0.416 | 240 |
| synthetic_500 | hybrid | 0.138 | 0.417 | 0.573 | 0.345 | 400 |
| synthetic_500 | time_aware | 0.240 | 0.522 | 0.642 | 0.424 | 400 |
| synthetic_500 | vector | 0.120 | 0.383 | 0.542 | 0.324 | 400 |

## Best Method Per Run

| Run | Best Method | Recall@1 | MRR |
|---|---|---:|---:|
| sample_10 | hybrid | 0.800 | 0.875 |
| synthetic_100 | time_aware | 0.575 | 0.740 |
| synthetic_300 | time_aware | 0.338 | 0.529 |
| synthetic_500 | time_aware | 0.240 | 0.424 |

## Recall@1 Trend

| Method | sample_10 | synthetic_100 | synthetic_300 | synthetic_500 |
|---|---:|---:|---:|---:|
| hybrid | 0.800 | 0.400 | 0.200 | 0.138 |
| time_aware | 0.800 | 0.575 | 0.338 | 0.240 |
| vector | 0.800 | 0.400 | 0.175 | 0.120 |

## Temporal Update Focus

| Run | Method | Temporal Recall@1 | Temporal Recall@3 | Temporal MRR |
|---|---|---:|---:|---:|
| sample_10 | hybrid | 1.000 | 1.000 | 1.000 |
| sample_10 | time_aware | 1.000 | 1.000 | 1.000 |
| sample_10 | vector | 1.000 | 1.000 | 1.000 |
| synthetic_100 | hybrid | 0.050 | 0.750 | 0.463 |
| synthetic_100 | time_aware | 0.750 | 1.000 | 0.875 |
| synthetic_100 | vector | 0.050 | 0.750 | 0.463 |
| synthetic_300 | hybrid | 0.033 | 0.600 | 0.404 |
| synthetic_300 | time_aware | 0.583 | 1.000 | 0.769 |
| synthetic_300 | vector | 0.033 | 0.583 | 0.394 |
| synthetic_500 | hybrid | 0.030 | 0.460 | 0.345 |
| synthetic_500 | time_aware | 0.440 | 0.880 | 0.659 |
| synthetic_500 | vector | 0.030 | 0.430 | 0.334 |

## Interpretation

- The 10-row sample proves the pipeline works and is easy to inspect by hand.
- At 100 memories, `time_aware` improves Recall@1 over `vector` and `hybrid`, mainly because temporal-update queries need the newest fact rather than the oldest matching fact.
- As memory count grows, the gap becomes clearer: repeated similar memories make plain retrieval confuse old and new facts, while recency-aware reranking recovers many current-state answers.
- Compression and evaluation queries remain harder in synthetic data because many generated memories share the same project and template wording. This is useful: it exposes the need for better entity keys, user/session filters, or stronger embeddings before moving to real LoCoMo data.

## Next Experimental Step

Use this offline baseline as the control group, then replace the hashed-vector scorer with a real memory backend such as `mem0` or a sentence-transformer embedding model. The same JSONL files and metrics can stay unchanged.
