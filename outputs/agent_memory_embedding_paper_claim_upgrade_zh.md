# Embedding Baseline Paper-Claim Upgrade Gate

本文件把外部 embedding baseline 从“接入协议已准备”到“可写入论文主结果/稳健性对照”分成多个门槛。它不联网、不调用 API，也不读取或打印 key。

## 总览

- Claim tiers: 6
- Passed tiers: 2/6
- Highest unlocked tier: `cost_cache_reviewed`

## 门槛明细

| Tier | Status | Evidence | Allowed Paper Claim | Next Action |
| --- | --- | --- | --- | --- |
| protocol_ready | pass | preflight_rows=10, status_rows=2, comparison_rows=4, postrun_rows=2 | 可以写：外部 embedding baseline 的接入、费用预估、缓存和跑后验收协议已经准备。 | 配置 OpenAI 或 OpenAI-compatible embedding provider key。 |
| preflight_ready | pending | required_preflight=4/5, ready_or_completed_providers=0 | 可以写：外部 embedding baseline 已通过跑前门禁，可以执行真实 API run。 | 运行真实 API embedding baseline，生成 summary/per-query/ranking 文件。 |
| cost_cache_reviewed | pass | items=4355, approx_tokens=71882, uncached_batches=0 | 可以写：真实 API baseline 的文本规模、近似 token 和缓存批次数已在运行前估算。 | 确认预算后执行真实 API run；若数据变动，先重跑 estimate。 |
| api_result_completed | pending | completed_status_rows=0 | 可以写：至少一个外部 embedding provider 已产生本地 summary 指标。 | 运行 compare_embedding_baselines.py 和 validate_api_embedding_postrun.py。 |
| comparison_completed | pending | pending comparison deltas | 可以写：外部 embedding 与 BGE-M3 的 Recall/MRR delta 已可报告。 | 检查 summary_by_type、per_query_metrics、rankings 并刷新 postrun gate。 |
| paper_claim_ready | pending | postrun_pass=0, paper_acceptance_pass=0, comparison_completed=False | 可以写：外部 embedding baseline 已完成，可作为论文 embedding 稳健性对照。 | 刷新 evidence matrix、manuscript、claim checks、reproducibility、freshness 和 submission readiness。 |

## 使用边界

- 在 `preflight_ready` 之前，只能写外部 embedding baseline 的接入协议准备好。
- 在 `api_result_completed` 之前，不能写任何外部 embedding 指标。
- 在 `paper_claim_ready` 之前，不能把外部 embedding baseline 写入论文主结果或稳健性结论。
- 通过 `paper_claim_ready` 需要 postrun gate、strict paper-acceptance gate 和 comparison 同时通过；若要写跨 provider 稳健性，需要多个 provider 均完成并单独报告。
