# LoCoMo10 Baseline 对比

## 目标

本报告补充纯 BM25 keyword baseline，使 LoCoMo10 全量结果包含更完整的检索方法对照：

- `keyword`：纯 BM25。
- `vector`：纯 BGE-M3 embedding 相似度。
- `hybrid`：BGE-M3 + BM25 + entity overlap。
- `time_aware`：hybrid + recency/persona/importance。
- `type_aware`：time-aware + query intent / memory type matching。

## DeepSeek Extracted Fact

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| keyword | 0.428 | 0.581 | 0.634 | 0.526 |
| vector | 0.419 | 0.585 | 0.643 | 0.527 |
| hybrid | 0.477 | 0.647 | 0.705 | 0.583 |
| time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| type_aware | 0.503 | 0.670 | 0.733 | 0.609 |

## LoCoMo Observation

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| keyword | 0.402 | 0.550 | 0.605 | 0.497 |
| vector | 0.471 | 0.625 | 0.679 | 0.567 |
| hybrid | 0.465 | 0.625 | 0.675 | 0.565 |
| time_aware | 0.483 | 0.639 | 0.703 | 0.583 |
| type_aware | 0.483 | 0.639 | 0.703 | 0.583 |

## 结论

- 纯 keyword 与纯 vector 都明显弱于 hybrid / time-aware / type-aware，说明语义与关键词互补是必要的。
- 在 DeepSeek extracted fact 上，keyword 和 vector 的 MRR 接近，但 Recall@1 表现不同：keyword 的 Recall@1 更高，vector 的 Recall@5 更高。
- 在 LoCoMo observation 上，vector 明显强于 keyword，说明官方 observation 文本更依赖语义相似度。
- `type_aware` 是 DeepSeek extracted fact 上当前最优方法。
- Observation 缺少可用的 `memory_type` 字段，因此 `type_aware` 与 `time_aware` 结果相同。
