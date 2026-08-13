# Type 3 Intent-Facet Fusion 优化实验

本实验针对 Type 3 多证据问题做保守优化：不替换已有 candidate reranker，而是为每个问题生成少量高置信度检索意图 facet，从全量记忆库补充候选，再用 RRF、候选分数和 facet 命中次数融合排序。

该方法不调用大模型，也不使用 gold evidence 参与打分；gold evidence 只用于最终评估。

## 参数

- max_facets：`6`
- facet_top_k：`40`
- candidate_weight：`4.0`
- facet_weight：`0.35`
- facet_hit_weight：`0.002`

## 结果

| 方法 | Rows | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 126 | 0.418 | 0.349 | 0.429 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| intent_fusion_top5_window_keep_top1 | 126 | 0.420 | 0.349 | 0.413 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| intent_fusion_top5_window_free | 126 | 0.420 | 0.349 | 0.413 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| intent_fusion_candidate_only_keep_top1 | 126 | 0.418 | 0.349 | 0.413 | 0.476 | 0.359 | 0.254 | 0.597 | 0.444 |
| intent_fusion_candidate_only_free | 126 | 0.418 | 0.349 | 0.413 | 0.476 | 0.359 | 0.254 | 0.597 | 0.444 |
| intent_fusion_keep_top1 | 126 | 0.420 | 0.349 | 0.413 | 0.476 | 0.359 | 0.254 | 0.597 | 0.444 |
| intent_fusion_free | 126 | 0.420 | 0.349 | 0.413 | 0.476 | 0.359 | 0.254 | 0.597 | 0.444 |

## 相比 Candidate Reranker 的变化

- `intent_fusion_candidate_only_free`：MRR `-0.0006`，R@5 `-0.0159`，Coverage@5 `-0.0132`，Full@5 `-0.0079`。
- `intent_fusion_candidate_only_keep_top1`：MRR `-0.0006`，R@5 `-0.0159`，Coverage@5 `-0.0132`，Full@5 `-0.0079`。
- `intent_fusion_free`：MRR `+0.0017`，R@5 `-0.0159`，Coverage@5 `-0.0132`，Full@5 `-0.0079`。
- `intent_fusion_keep_top1`：MRR `+0.0017`，R@5 `-0.0159`，Coverage@5 `-0.0132`，Full@5 `-0.0079`。
- `intent_fusion_top5_window_free`：MRR `+0.0013`，R@5 `+0.0000`，Coverage@5 `+0.0000`，Full@5 `+0.0000`。
- `intent_fusion_top5_window_keep_top1`：MRR `+0.0013`，R@5 `+0.0000`，Coverage@5 `+0.0000`，Full@5 `+0.0000`。

## Facet 示例

| Query | Facets |
|---|---|
| What would Caroline's political leaning likely be? | original:What would Caroline's political leaning likely be? // content:caroline caroline political leaning // intent:caroline preference hobby enjoy // intent_content:caroline preference hobby enjoy caroline political leaning |
| Would Caroline be considered religious? | original:Would Caroline be considered religious? // content:caroline caroline considered religious |
| What pets wouldn't cause any discomfort to Joanna? | original:What pets wouldn't cause any discomfort to Joanna? // content:joanna pets wouldn cause any discomfort joanna // intent:joanna reason motive cause decision // intent_content:joanna reason motive cause decision pets wouldn cause any discomfort joanna |
| What alternative career might Nate consider after gaming? | original:What alternative career might Nate consider after gaming? // content:nate alternative career nate consider after gaming // clause:nate alternative career nate consider // intent:nate career education work goal plan // intent_content:nate career education work goal plan alternative career nate consider after gaming |
| Was the first half of September 2022 a good month career-wise for Nate and Joanna? Answer yes or no. | original:Was the first half of September 2022 a good month career-wise for Nate and Joanna? Answer yes or no. // content:joanna nate first half september 2022 good month career wise nate joanna answer yes // clause:joanna nate first half september 2022 good month career wise nate // clause:joanna nate joanna answer yes // intent:joanna nate career education work goal plan // intent_content:joanna nate career education work goal plan first half september 2022 good month career wise nate joanna answer yes |
| What kind of job is Joanna beginning to preform the duties of because of her movie scripts? | original:What kind of job is Joanna beginning to preform the duties of because of her movie scripts? // content:joanna job joanna beginning preform duties because movie scripts // clause:joanna job joanna beginning preform duties // clause:joanna movie scripts // intent:joanna reason motive cause decision // intent_content:joanna reason motive cause decision job joanna beginning preform duties because movie scripts |
| What state did Nate visit? | original:What state did Nate visit? // content:nate state nate visit // intent:nate place location live move // intent_content:nate place location live move state nate visit |
| Would Tim enjoy reading books by C. S. Lewis or John Greene? | original:Would Tim enjoy reading books by C. S. Lewis or John Greene? // content:john tim tim enjoy reading books lewis john greene // clause:john tim tim enjoy reading books lewis // clause:john tim john greene // intent:john tim preference hobby enjoy // intent_content:john tim preference hobby enjoy tim enjoy reading books lewis john greene |
| Which US states might Tim be in during September 2023 based on his plans of visiting Universal Studios? | original:Which US states might Tim be in during September 2023 based on his plans of visiting Universal Studios? // content:tim states tim during september 2023 based plans visiting universal studios // clause:tim states tim during september 2023 // clause:tim plans visiting universal studios // intent:tim place location live move // intent_content:tim place location live move states tim during september 2023 based plans visiting universal studios |
| What other exercises can help John with his basketball performance? | original:What other exercises can help John with his basketball performance? // content:john other exercises can help john basketball performance |

## 解释

- 如果 `intent_fusion_keep_top1` 提升，说明保留强首位证据后，意图补召回有助于增加多证据覆盖。
- 如果 `intent_fusion_free` 提升但 MRR 下降，说明它更偏向集合覆盖，可能适合作为生成回答前的证据包选择器。
- 如果两者仍下降，说明 Type 3 的主要瓶颈不是候选补召回，而是需要学习式 set/listwise 目标或更强的 LLM 子问题生成。
