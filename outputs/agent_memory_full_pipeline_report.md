# Agent Memory Full Pipeline Report

This is the consolidated first-stage evidence for the memory module.

## What Was Verified

- Retrieval baselines from 10 hand-checkable records to several hundred synthetic memories.
- Recency-aware reranking for memory token freshness / temporal validity.
- Fact-level and grouped-summary compression tradeoffs.
- Cross-agent shared memory reuse and the risk of skipping permission filtering before ranking.

## Key Numbers

| Check | Result |
|---|---:|
| 10-row sanity check, time-aware Recall@1 | 0.800 |
| 500-memory vector Recall@1 | 0.120 |
| 500-memory time-aware Recall@1 | 0.240 |
| 500-memory raw time-aware Recall@1 | 0.240 |
| 500-memory fact-compressed time-aware Recall@1 | 0.235 |
| 500-memory summary-compressed time-aware Recall@1 | 0.110 |
| 500-memory cross-agent private-only Recall@1 | 0.000 |
| 500-memory cross-agent shared Recall@1 | 0.704 |
| 500-memory unfiltered private-first Recall@1 | 0.000 |

## Interpretation

- The first-stage pipeline is easy to reproduce and inspect, because it starts from 10 records and scales to 100/300/500 records with identical metrics.
- Recency-aware scoring is the strongest simple baseline when repeated memories contain old and new versions of similar facts.
- Fact-level compression is the safer first compression target: it reduces token cost strongly while preserving more retrieval quality than grouped summaries.
- Cross-agent reuse should be implemented as `permission filter -> retrieval/reranking -> optional KV-cache reuse`; the risk control shows that ranking before filtering can put unauthorized copies in the top result.

## Output Index

- Retrieval analysis: `outputs/agent_memory_experiment_analysis.md`
- Trend table: `outputs/agent_memory_experiment_trends.csv`
- Visualization: `outputs/agent_memory_experiment_visualization.html`
- Compression analysis: `outputs/agent_memory_compression_analysis.md`
- Compression table: `outputs/agent_memory_compression_results.csv`
- Cross-agent analysis: `outputs/agent_memory_cross_agent_analysis.md`
- Cross-agent table: `outputs/agent_memory_cross_agent_results.csv`
