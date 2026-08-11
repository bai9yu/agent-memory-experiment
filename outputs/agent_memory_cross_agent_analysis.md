# Cross-Agent Memory Reuse Analysis

This report tests whether agent B can answer questions using memories shared by agent A, and how retrieval behaves when private same-topic distractors are present.

## Time-Aware Retrieval

| Run | Strategy | Memories | Tokens | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| cross_agent_100 | private_only | 100 | 2824 | 0.000 | 0.000 | 0.000 | 0.000 |
| cross_agent_100 | shared_allowed | 100 | 2824 | 0.910 | 0.970 | 1.000 | 0.944 |
| cross_agent_100 | shared_plus_private_noise | 200 | 5648 | 0.910 | 0.970 | 1.000 | 0.944 |
| cross_agent_100 | unfiltered_private_first | 200 | 5648 | 0.000 | 0.890 | 0.950 | 0.456 |
| cross_agent_300 | private_only | 300 | 8453 | 0.000 | 0.000 | 0.000 | 0.000 |
| cross_agent_300 | shared_allowed | 300 | 8453 | 0.757 | 0.930 | 0.960 | 0.851 |
| cross_agent_300 | shared_plus_private_noise | 600 | 16906 | 0.757 | 0.930 | 0.960 | 0.851 |
| cross_agent_300 | unfiltered_private_first | 600 | 16906 | 0.000 | 0.733 | 0.857 | 0.398 |
| cross_agent_500 | private_only | 500 | 14092 | 0.000 | 0.000 | 0.000 | 0.000 |
| cross_agent_500 | shared_allowed | 500 | 14092 | 0.704 | 0.864 | 0.912 | 0.800 |
| cross_agent_500 | shared_plus_private_noise | 1000 | 28184 | 0.704 | 0.864 | 0.912 | 0.800 |
| cross_agent_500 | unfiltered_private_first | 1000 | 28184 | 0.000 | 0.656 | 0.810 | 0.367 |

## Shared Memory Gain

| Run | Private Recall@1 | Shared Recall@1 | Mixed Recall@1 | Unfiltered Recall@1 | Shared Gain | Mixed Drop | Permission Drop |
|---|---:|---:|---:|---:|---:|---:|---:|
| cross_agent_100 | 0.000 | 0.910 | 0.910 | 0.000 | 0.910 | 0.000 | 0.910 |
| cross_agent_300 | 0.000 | 0.757 | 0.757 | 0.000 | 0.757 | 0.000 | 0.757 |
| cross_agent_500 | 0.000 | 0.704 | 0.704 | 0.000 | 0.704 | 0.000 | 0.704 |

## Interpretation

- `private_only` should remain near zero because agent B cannot see the answer memories from agent A.
- `shared_allowed` measures the positive value of cross-agent reusable knowledge.
- `shared_plus_private_noise` is the more realistic condition: authorized shared facts compete with private same-topic memories.
- `unfiltered_private_first` is a risk control showing that retrieval should filter by permission scope before ranking, deduplication, or KV-cache reuse.
- A useful next implementation step is adding a permission gate before retrieval and a second score term for source-agent trust/KV-cache reuse cost.
