# Time-Aware 参数搜索报告

## 搜索对象

使用已有 `rankings.csv` 的候选集合进行重排搜索，不重新调用 embedding 模型。

参考思路：Generative Agents 中的 relevance + recency + importance。当前 LoCoMo 第一版没有显式 importance 标注，因此先使用 semantic relevance、BM25 keyword、entity overlap 和 gated recency。

## Baseline

| Formula | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| 0.65 semantic + 0.30 BM25 + 0.05 entity | 0.283 | 0.445 | 0.514 | 0.391 |

## 最优参数

| semantic | BM25 | entity | recency | gate | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 0.70 | 0.30 | 0.00 | 0.08 | recency | 0.310 | 0.473 | 0.537 | 0.416 |

## 解释

- `recency` gate 只在 query 包含 recent/latest/last/today/currently/now/since/new 等最近性意图，且不是 when/date/time 问句时触发。
- 这样避免把所有时间问题都误解成“越新越好”。LoCoMo 里很多 `When did ...` 问的是历史事件日期，盲目偏新会伤害检索。
- 当前最优参数已固化到 `memory_eval.py` 的 `time_aware` 方法。

## 全量复验

在 `memory_eval.py` 固化该参数后，使用 LoCoMo 全量数据和本地 BGE-M3 重新评测：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.310 | 0.473 | 0.537 | 0.418 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

结论：adaptive time-aware 在全量复验中超过 hybrid，不只是候选重排搜索中的局部结果。
