# Type 3 Query Decomposition 检索基线

本实验针对 LoCoMo Type 3 推理/多证据问题，使用无训练的 query decomposition：从原 query 中抽取人物名、内容关键词和短窗口 facet query，分别做 BM25 召回，再用 RRF 与轻量 persona/type/importance 特征合并候选。

参数：max_facets=`12`，facet_top_k=`80`，fusion type_weight=`4.0`，decomp_weight=`1.0`。该方法不使用 gold evidence 调参。

## Type 3 全量结果

| 方法 | Queries | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| type_aware | 86 | 0.429 | 0.326 | 0.488 | 0.547 | 0.370 | 0.233 | 0.537 | 0.372 |
| query_decomposition | 86 | 0.214 | 0.128 | 0.221 | 0.279 | 0.161 | 0.093 | 0.324 | 0.186 |
| type_aware_plus_decomposition | 86 | 0.342 | 0.198 | 0.442 | 0.512 | 0.337 | 0.209 | 0.537 | 0.372 |

## 融合方法相比 Type-Aware 的变化

- MRR delta：`-0.0867`
- Recall@5 delta：`-0.0349`
- Coverage@5 delta：`-0.0325`
- Coverage@20 delta：`0.0000`

## 代表性拆解示例

| Query | Facets | First Relevant Rank | Coverage@5 |
|---|---|---:|---:|
| Who is Anthony? | Who is Anthony? // anthony | 1 | 1.000 |
| What kind of yoga for building core strength might John benefit from? | What kind of yoga for building core strength might John benefit from? // john kind yoga building core strength john benefit // john kind yoga // john yoga building // john building core // john core strength // john strength john // john john benefit // john kind yoga building // john yoga building core // john building core strength // john core strength john | 1 | 1.000 |
| What is a Star Wars book that Tim might enjoy? | What is a Star Wars book that Tim might enjoy? // tim star wars book tim enjoy // tim star wars // tim wars book // tim book tim // tim tim enjoy // tim star wars book // tim wars book tim // tim book tim enjoy // tim star wars book tim // tim wars book tim enjoy // tim star | 1 | 1.000 |
| Which US state do Audrey and Andrew potentially live in? | Which US state do Audrey and Andrew potentially live in? // audrey andrew state audrey andrew potentially live // audrey andrew state audrey // audrey andrew andrew potentially live // audrey andrew audrey andrew // audrey andrew andrew potentially // audrey andrew potentially live // audrey andrew state audrey andrew // audrey andrew audrey andrew potentially // audrey andrew state audrey andrew potentially // audrey andrew audrey andrew potentially live // audrey andrew state | 1 | 1.000 |
| Who is Jill? | Who is Jill? // jill | 1 | 1.000 |
| Is the friend who wrote Deborah the motivational quote no longer alive? | Is the friend who wrote Deborah the motivational quote no longer alive? // deborah friend wrote deborah motivational quote longer alive // deborah friend wrote // deborah wrote deborah // deborah deborah motivational // deborah motivational quote // deborah quote longer // deborah longer alive // deborah friend wrote deborah // deborah wrote deborah motivational // deborah deborah motivational quote // deborah motivational quote longer | 1 | 1.000 |
| In what country did Jolene's mother buy her the pendant? | In what country did Jolene's mother buy her the pendant? // jolene country jolene mother buy pendant // jolene country jolene // jolene jolene mother // jolene mother buy // jolene buy pendant // jolene country jolene mother // jolene jolene mother buy // jolene mother buy pendant // jolene country jolene mother buy // jolene jolene mother buy pendant // jolene country | 3 | 1.000 |
| What card game is Deborah talking about? | What card game is Deborah talking about? // deborah card game deborah talking about // deborah card game // deborah game deborah // deborah deborah talking // deborah talking about // deborah card game deborah // deborah game deborah talking // deborah deborah talking about // deborah card game deborah talking // deborah game deborah talking about // deborah card | 3 | 1.000 |
| Would Caroline still want to pursue counseling as a career if she hadn't received support growing up? | Would Caroline still want to pursue counseling as a career if she hadn't received support growing up? // caroline caroline want pursue counseling career she hadn received support growing // caroline caroline want pursue counseling // caroline career // caroline she hadn received support growing // caroline caroline want // caroline want pursue // caroline pursue counseling // caroline counseling career // caroline career she // caroline she hadn // caroline hadn received | 1 | 0.500 |
| Would Caroline pursue writing as a career option? | Would Caroline pursue writing as a career option? // caroline caroline pursue writing career option // caroline caroline pursue writing // caroline career option // caroline caroline pursue // caroline pursue writing // caroline writing career // caroline pursue writing career // caroline writing career option // caroline caroline pursue writing career // caroline pursue writing career option // caroline caroline | 1 | 0.500 |

## 解释

- 如果纯拆解低于 `type_aware` 但融合方法提升，说明 decomposition 可作为辅助召回信号。
- 如果融合方法也低于 `type_aware`，说明关键词式拆解噪声过大，需要 LLM/规则更准确地生成子问题。
- 该实验是 query decomposition 的弱基线，主要用于判断是否值得继续投入更强的拆解模型。
