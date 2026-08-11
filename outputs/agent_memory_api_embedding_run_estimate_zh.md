# API Embedding Baseline 运行预估

本文件在不联网、不读取 API key 的情况下，预估外部 embedding baseline 的请求规模、缓存状态和可选费用。

## 总览

- Model: `text-embedding-3-small`
- Base URL: `https://api.openai.com/v1`
- Total items: 4355
- Approx tokens: 71882
- API batches still needed if current cache is unchanged: 35
- Price per 1M tokens: not_set
- Estimated uncached cost: `price_not_set`

## 明细

| Kind | Items | Approx Tokens | Batches | Cache Exists | Estimated Cost |
| --- | --- | --- | --- | --- | --- |
| memories | 2517 | 45429 | 20 | False | price_not_set |
| queries | 1838 | 26453 | 15 | False | price_not_set |

## 使用说明

- 如果 `cache_exists=True`，对应 memories 或 queries embedding 已经缓存，重复运行通常不会再次调用 API。
- `approx_tokens` 是 tokenizer-free 估计值，用于跑前预算，不应作为论文中的精确 token 计数。
- 如果需要费用估算，请通过 `--price-per-million-tokens` 手动传入当前 provider 单价。
