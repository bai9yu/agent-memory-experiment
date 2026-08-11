# API Embedding Execution Runbook

本文件把外部 API embedding baseline 的真实运行路径整理成可执行 runbook。它不联网、不读取 API key 内容，也不会自动启动付费调用；目标是在拿到 key 后按同一顺序关闭 external embedding blocker。

## 总览

- Providers: 2
- Paid/network steps listed: 2
- Providers completed for paper: 0
- Offline refresh starts paid run: False

## Step Matrix

| Provider | Step | Phase | Current Pass | Evidence | Acceptance |
| --- | --- | --- | --- | --- | --- |
| OpenAI text-embedding-3-small | 1_configure_key | manual | False | OPENAI_API_KEY available=False | Store the provider key in .env or shell; never commit the key. |
| OpenAI text-embedding-3-small | 2_preflight | offline_check | False | default preflight required=4/5; provider key available=False | All required preflight checks pass before any paid/network API call. |
| OpenAI text-embedding-3-small | 3_cost_and_cache_estimate | offline_check | True | memories: items=2517, tokens=45429, batches=20, cache_exists=False; queries: items=1838, tokens=26453, batches=15, cache_exists=False | Review item count, approximate tokens, uncached batches, and expected cache reuse. |
| OpenAI text-embedding-3-small | 4_real_api_run | network_paid_run | False | intentionally not run by offline refresh | Run only after preflight passes and expected cost/cache behavior is acceptable. |
| OpenAI text-embedding-3-small | 5_compare_with_bge_m3 | offline_after_run | False | requires provider summary.csv from real API run | Generate numeric delta table versus BGE-M3 after summary.csv exists. |
| OpenAI text-embedding-3-small | 6_postrun_gate | offline_after_run | False | completed_for_paper=0 | Post-run gate must report at least one provider completed_for_paper. |
| OpenAI text-embedding-3-small | 7_final_refresh | offline_after_run | False | run after external baseline and comparison are complete | Refresh evidence matrix, manuscript, claim checks, reproducibility, freshness, and submission readiness. |
| Generic OpenAI-compatible embedding | 1_configure_key | manual | False | EXTERNAL_EMBEDDING_API_KEY available=False | Store the provider key in .env or shell; never commit the key. |
| Generic OpenAI-compatible embedding | 2_preflight | offline_check | False | default preflight required=4/5; provider key available=False | All required preflight checks pass before any paid/network API call. |
| Generic OpenAI-compatible embedding | 3_cost_and_cache_estimate | offline_check | True | memories: items=2517, tokens=45429, batches=20, cache_exists=False; queries: items=1838, tokens=26453, batches=15, cache_exists=False | Review item count, approximate tokens, uncached batches, and expected cache reuse. |
| Generic OpenAI-compatible embedding | 4_real_api_run | network_paid_run | False | intentionally not run by offline refresh | Run only after preflight passes and expected cost/cache behavior is acceptable. |
| Generic OpenAI-compatible embedding | 5_compare_with_bge_m3 | offline_after_run | False | requires provider summary.csv from real API run | Generate numeric delta table versus BGE-M3 after summary.csv exists. |
| Generic OpenAI-compatible embedding | 6_postrun_gate | offline_after_run | False | completed_for_paper=0 | Post-run gate must report at least one provider completed_for_paper. |
| Generic OpenAI-compatible embedding | 7_final_refresh | offline_after_run | False | run after external baseline and comparison are complete | Refresh evidence matrix, manuscript, claim checks, reproducibility, freshness, and submission readiness. |

## 使用方式

1. 选择一个 provider。
2. 完成 `1_configure_key`，确保 key 只在 `.env` 或 shell 中，不进入 Git。
3. 运行 `2_preflight` 和 `3_cost_and_cache_estimate`。
4. 只有 preflight 全部通过、费用/缓存可接受时，才运行 `4_real_api_run`。
5. 跑完后依次运行 compare、postrun gate 和 final refresh。

## 论文使用边界

- 可以写：外部 embedding baseline 的真实运行和验收路径已经固定，且离线刷新不会误触发付费 API。
- 不能写：runbook 生成完成就等于外部 embedding baseline 已完成；最终仍以 postrun gate completed_for_paper 为准。
