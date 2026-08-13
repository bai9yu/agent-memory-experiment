# Type 3 召回扩展分析

本实验针对 Type 3 中 Top-20 候选缺失 gold evidence 的问题，比较扩大候选池、离线多信号检索和意图 facet 检索能否提升证据召回。该实验只评估候选池覆盖，不作为最终排序方法。

## 主要结果

| 方法 | Pool | Missing-All | Coverage@20 | Full@20 | Coverage@50 | Full@50 | Coverage@100 | Full@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_top20 | 20.0 | 0.254 | 0.597 | 0.444 | 0.597 | 0.444 | 0.597 | 0.444 |
| candidate_top50 | 20.0 | 0.254 | 0.597 | 0.444 | 0.597 | 0.444 | 0.597 | 0.444 |
| candidate_top100 | 20.0 | 0.254 | 0.597 | 0.444 | 0.597 | 0.444 | 0.597 | 0.444 |
| offline_top50 | 50.0 | 0.294 | 0.403 | 0.246 | 0.529 | 0.341 | 0.529 | 0.341 |
| facet_top50 | 50.0 | 0.325 | 0.390 | 0.246 | 0.485 | 0.317 | 0.485 | 0.317 |
| candidate20_plus_offline50 | 57.6 | 0.190 | 0.597 | 0.444 | 0.657 | 0.492 | 0.668 | 0.500 |
| candidate20_plus_facet50 | 57.3 | 0.183 | 0.597 | 0.444 | 0.658 | 0.492 | 0.664 | 0.516 |
| candidate20_plus_offline50_facet50 | 80.2 | 0.151 | 0.597 | 0.444 | 0.657 | 0.492 | 0.704 | 0.556 |

## 相比 Candidate Top-20 的变化

- `candidate20_plus_facet50`：Missing-All `-0.0714`，Coverage@50 `+0.0606`，Full@50 `+0.0476`。
- `candidate20_plus_offline50`：Missing-All `-0.0635`，Coverage@50 `+0.0602`，Full@50 `+0.0476`。
- `candidate20_plus_offline50_facet50`：Missing-All `-0.1032`，Coverage@50 `+0.0602`，Full@50 `+0.0476`。
- `candidate_top100`：Missing-All `+0.0000`，Coverage@50 `+0.0000`，Full@50 `+0.0000`。
- `candidate_top50`：Missing-All `+0.0000`，Coverage@50 `+0.0000`，Full@50 `+0.0000`。
- `facet_top50`：Missing-All `+0.0714`，Coverage@50 `-0.1123`，Full@50 `-0.1270`。
- `offline_top50`：Missing-All `+0.0397`，Coverage@50 `-0.0684`，Full@50 `-0.1032`。

## 解释

- Candidate Top-20 的 Missing-All 为 `0.254`；该值越高，说明重排无法解决的问题越多。
- 如果扩大候选池显著降低 Missing-All，下一步应把候选池扩大后接 listwise/setwise 重排。
- 如果离线检索或 facet 检索优于简单扩大 candidate，则说明 query decomposition / 多路召回值得继续投入。
- 如果所有离线召回仍不足，下一步应接真实 embedding 或 LLM 子问题生成。
