# Type 3 Top-20 救回空间分析

本分析不作为实际检索方法，而是诊断 Type 3 多证据问题的优化空间：在 candidate reranker 已落盘的 Top-20 候选里，检查有多少问题可以通过更好的集合/列表重排把证据救回 Top-5。

## 总体上限

| 指标 | 当前 Top-5 | Top-20 覆盖 | Oracle Top-5 | 可救回空间 |
|---|---:|---:|---:|---:|
| MRR | 0.392 | - | 0.746 | +0.3537 |
| Coverage | 0.372 | 0.597 | 0.597 | +0.2246 |
| Full Coverage | 0.262 | 0.444 | 0.444 | +0.1825 |

## 问题分型

| 类型 | Rows | Share | Top5 Coverage | Top20 Coverage | Oracle Top5 Coverage | Coverage Gap | Full Gap |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate_missing_all_gold | 32 | 0.254 | 0.000 | 0.000 | 0.000 | +0.0000 | +0.0000 |
| partial_but_not_improvable_within_top20 | 11 | 0.087 | 0.626 | 0.626 | 0.626 | +0.0000 | +0.0000 |
| rerank_rescuable_from_top20 | 50 | 0.397 | 0.141 | 0.707 | 0.707 | +0.5661 | +0.4600 |
| top5_already_full | 33 | 0.262 | 1.000 | 1.000 | 1.000 | +0.0000 | +0.0000 |

## 代表性可救回问题

| Query | Gold 数 | Top5 Coverage | Top20 Coverage | Oracle Top5 Coverage |
|---|---:|---:|---:|---:|
| What kind of job is Joanna beginning to preform the duties of because of her movie scripts? | 2 | 0.000 | 1.000 | 1.000 |
| What kind of job is Joanna beginning to preform the duties of because of her movie scripts? | 2 | 0.000 | 1.000 | 1.000 |
| Which meat does Audrey prefer eating more than others? | 2 | 0.000 | 1.000 | 1.000 |
| What pets wouldn't cause any discomfort to Joanna? | 1 | 0.000 | 1.000 | 1.000 |
| Did James have a girlfriend during April 2022? | 1 | 0.000 | 1.000 | 1.000 |
| Which US state was Sam travelling in during October 2023? | 1 | 0.000 | 1.000 | 1.000 |
| Did James have a girlfriend during April 2022? | 1 | 0.000 | 1.000 | 1.000 |
| Was James feeling lonely before meeting Samantha? | 1 | 0.000 | 1.000 | 1.000 |
| What pets wouldn't cause any discomfort to Joanna? | 1 | 0.000 | 1.000 | 1.000 |
| Does Deborah live close to the beach or the mountains? | 1 | 0.000 | 1.000 | 1.000 |

## 结论

- 如果 `rerank_rescuable_from_top20` 占比较高，下一步应做学习式 listwise/setwise 重排。
- 如果 `candidate_missing_all_gold` 占比较高，下一步应先增强召回，例如 LLM 子问题生成、真实 embedding 或更大的候选池。
- 该分析使用 gold evidence 计算上限，不可作为实际部署方法，只用于确定优化方向。
