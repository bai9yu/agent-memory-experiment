# Agent Memory 论文级实验进展

## 当前已经具备的实验基础

- 真实数据：LoCoMo10 全量。
- 真实 LLM：DeepSeek `deepseek-chat`，用于 memory write / fact extraction。
- 本地 embedding：`BAAI/bge-m3`。
- 主要对照：LoCoMo 官方 `observation` memory。
- 检索方法：`vector`、`hybrid`、`time_aware`、`type_aware`。
- 中文报告：抽取、压缩、跨智能体复用、type-aware 消融、显著性检验和错误分析均已形成文档。

## LoCoMo10 全量主结果

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact + type-aware | 2517 | 31148 | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| LoCoMo observation | 2507 | 40241 | 1638 | 0.483 | 0.639 | 0.703 | 0.583 |

## Baseline 对比

DeepSeek extracted fact：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| keyword | 0.428 | 0.581 | 0.634 | 0.526 |
| vector | 0.419 | 0.585 | 0.643 | 0.527 |
| hybrid | 0.477 | 0.647 | 0.705 | 0.583 |
| time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| type_aware | 0.503 | 0.670 | 0.733 | 0.609 |

结论：纯 keyword 与纯 vector 都明显弱于 hybrid / time-aware / type-aware，说明语义、关键词、时间、人物和类型信号都对最终检索有效。

DeepSeek API 用量：

- Prompt tokens：361103
- Completion tokens：198471
- Total tokens：559574
- 2026-08-11 已完成 `.env` 本地配置后的最小 smoke test：`deepseek-chat` 可正常返回结构化 memory，1 record / 1 session 生成 9 条 fact-level memory。该结果仅用于验证 API 连通性，不作为主实验指标。

成本与延迟：

- DeepSeek extracted fact memory tokens：31148
- LoCoMo observation memory tokens：40241
- Memory storage token ratio：0.774，约节省 22.6%
- LoCoMo10 LLM 评测 runtime：44.6335 秒，约 24.28 ms/query
- LoCoMo10 observation 评测 runtime：40.8617 秒，约 24.95 ms/query
- 细粒度 breakdown：ranking_and_metrics 占 87%-88%，是主要效率瓶颈。
- 候选预筛选：semantic top-200 + type-aware 取得 2.69x speedup，MRR 0.613，略高于 full ranking 的 0.609。
- Indexed prefilter：batched top-200 + type-aware 取得 3.18x speedup，MRR 0.613。
- Sklearn NearestNeighbors：BGE-M3 + exact NN top-200 + type-aware 取得 3.45x speedup，MRR 0.613，Recall@5 0.734；这是当前最适合作为论文效率章节的可复现向量索引基线。
- FAISS：Flat top-200 取得 3.38x speedup，MRR 0.612，Recall@5 0.734；IVF nprobe=32 top-200 取得 3.31x speedup，MRR 0.605，candidate gold recall 0.966；IVF nprobe=8 更快近似但 MRR 降至 0.571。
- FAISS scale stress test：扩展到 100k synthetic distractor memory bank 后，Flat query 0.3602 秒、candidate gold recall 0.952；IVF nprobe=4 query 0.1990 秒但 recall 降至 0.737，nprobe=64 recall 回升到 0.941 但 query 变为 2.0774 秒。
- LSH prefilter：hash embedding + random-hyperplane LSH top-200 + type-aware 取得 2.16x speedup，MRR 0.471；该弱基线说明近似索引本身不够，embedding 表达能力仍是召回质量关键。

Coverage：

- Query coverage：0.925
- Strict query coverage：0.870
- Evidence coverage：0.896

## Type-Aware 消融

| Type Weight | Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---|---:|---:|---:|---:|
| 0.00 | time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| 0.04 | type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| 0.08 | type_aware | 0.503 | 0.669 | 0.733 | 0.609 |
| 0.12 | type_aware | 0.498 | 0.663 | 0.732 | 0.606 |

当前推荐：`w_type=0.04`。

显著性检验：

| Metric | Delta | 95% Bootstrap CI | Permutation p-value |
|---|---:|---:|---:|
| MRR | 0.004213 | [0.001214, 0.007182] | 0.0072 |
| Recall@1 | 0.003808 | [-0.001088, 0.009249] | 0.2066 |
| Recall@3 | 0.002176 | [-0.002720, 0.007073] | 0.5103 |
| Recall@5 | 0.006529 | [0.002720, 0.010881] | 0.0028 |

结论：MRR 和 Recall@5 的提升较小但通过 paired permutation test；Recall@1 / Recall@3 暂不能证明稳定提升。

## Query-Type 细粒度分析

LoCoMo10 answerable slice 按原始 query type 统计后，DeepSeek extracted fact memory 的最佳方法如下：

| Query Type | Queries | Best Method | Recall@1 | Recall@5 | MRR |
|---|---:|---|---:|---:|---:|
| Type 1 | 278 | vector | 0.371 | 0.658 | 0.513 |
| Type 2 | 310 | type_aware | 0.632 | 0.826 | 0.723 |
| Type 3 | 86 | type_aware | 0.326 | 0.547 | 0.429 |
| Type 4 | 752 | type_aware | 0.557 | 0.794 | 0.663 |
| Type 5 | 412 | keyword | 0.442 | 0.633 | 0.537 |

结论：Type 3 是当前明显短板；Type 5 上 keyword 反而最强，说明后续不能只继续增加语义/时间/type 权重，而应做 query-intent 自适应路由。

基于该发现的离线 query-type router：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| fixed type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| query_type_router | 0.505 | 0.674 | 0.731 | 0.611 |

paired significance test 显示 router 的 MRR delta 为 0.001994，但 95% CI 为 [-0.006012, 0.009802]，p=0.6187，尚不能证明稳定提升。因此 router 当前作为下一步方法方向，而不是主结论。

进一步测试可部署的 text-intent rule router，即只根据 query 文本规则选择 route，不使用 LoCoMo type 标注：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| fixed type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| text_intent_router | 0.489 | 0.661 | 0.715 | 0.595 |

该规则 router 显著退化，MRR delta 为 -0.014602，95% CI 为 [-0.020611, -0.008713]，p=0.0002。结论：简单关键词规则不能替代 query type 标注，后续需要 validation-tuned intent classifier 或 LLM few-shot classifier。

进一步测试 held-out 监督式 query-text router：用训练集 per-query 最优方法作为标签，测试集仅根据 query 文本预测 `keyword/vector/hybrid/time_aware/type_aware`。

| Method | Splits | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|
| fixed type_aware | 5 | 0.499 | 0.670 | 0.733 | 0.607 |
| supervised_text_router | 5 | 0.485 | 0.661 | 0.708 | 0.592 |
| oracle_best_method | 5 | 0.600 | 0.756 | 0.799 | 0.693 |

该监督式 router 仍低于 fixed `type_aware`，MRR delta 为 -0.0148，Recall@5 delta 为 -0.0250；同时与 oracle best 存在 0.1013 MRR 差距。结论：query-level 方法选择存在明显潜在上界，但不能直接用浅层 TF-IDF 分类器实现。后续应把 query intent 作为显式中间变量，用验证集调参、LLM few-shot classifier 或 pairwise reranking 学习替代简单分类。

再进一步测试 validation-tuned text-intent router：保留 query 文本规则得到的 intent 分组，但不手写 intent 到方法的映射，而是在训练集上为每个 intent 选择平均 MRR 最好的检索器。

| Method | Splits | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|
| fixed type_aware | 5 | 0.499 | 0.670 | 0.733 | 0.607 |
| validation_tuned_intent_router | 5 | 0.497 | 0.669 | 0.733 | 0.606 |
| oracle_best_method | 5 | 0.600 | 0.756 | 0.799 | 0.693 |

该调参版 router 基本接近 fixed `type_aware`，MRR delta 为 -0.0012，明显好于手写规则和监督式浅层分类器，但仍没有超过固定方法。结论：简单 intent 分组不足以支撑稳定方法选择；后续若要把 router 作为贡献点，需要更细粒度的 intent schema 或直接学习 candidate-level reranking。

基于上述负结果，进一步测试 candidate-level learned reranker：使用 `keyword/vector/hybrid/time_aware/type_aware` 各自 Top-K 候选的并集作为候选池，在训练 query 上学习候选记忆是否相关，并在 held-out query 上重排。

| Method | Splits | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|
| fixed type_aware | 5 | 0.499 | 0.670 | 0.733 | 0.607 |
| candidate_reranker | 5 | 0.556 | 0.732 | 0.796 | 0.661 |
| candidate_oracle | 5 | 0.909 | 0.909 | 0.909 | 0.909 |

配对显著性检验显示 candidate reranker 相比 fixed `type_aware` 稳定提升：MRR delta `+0.0539`，95% CI `[0.0462, 0.0619]`，permutation p-value `0.0002`；Recall@5 delta `+0.0623`，95% CI `[0.0500, 0.0746]`，p-value `0.0002`。这是当前最适合作为论文方法增量的结果：固定公式和 query-level router 不够，而 candidate-level reranking 能从多检索器候选特征中学习更稳的排序。

Feature importance 显示模型主要依赖 `type_aware_score`、`time_aware_rr`、`semantic_score`、`time_aware_score`、`hybrid_score`、`type_aware_rr` 等特征，说明提升来自多检索器排序信号融合，而不是单一字段或 query type 记忆。

## 距离论文发表级仍缺的内容

1. 重复抽取实验：至少对 LoCoMo10 做 3 次不同 seed / temperature 的 DeepSeek 抽取，报告均值和方差。
2. 更强 embedding baseline：加入 OpenAI embedding 或其他主流 embedding API、本地 BGE-small / BGE-M3 对比。
3. 在线检索效率：已有 sklearn exact NN、FAISS Flat、FAISS IVF 和 100k synthetic distractor scale test；仍需在真实更大 memory bank 上验证 ANN 优势，并可补 HNSW/IVF-PQ 对照。
4. 学习式重排：candidate-level reranker 已有显著提升；下一步需要补特征重要性、按 query type 的收益分析、与更强 reranker 模型的消融。
5. 跨智能体/KV cache 方向：需要把当前 synthetic cross-agent 实验替换为真实或半真实 multi-agent trace。
6. 人工复核：对自动错误分类结果抽样检查，估计分类可靠性。

## 错误分析

LoCoMo10 `type_aware` Top-1 错误分析：

| Error Reason | Count | Share of Errors |
|---|---:|---:|
| memory_type_mismatch | 365 | 0.400 |
| gold_below_top20 | 236 | 0.258 |
| semantic_neighbor | 63 | 0.069 |
| temporal_neighbor | 57 | 0.062 |
| persona_confusion | 35 | 0.038 |

与 `time_aware` 相比，`type_aware` 将 Top-1 错误从 920 降到 913，主要减少 `gold_below_top20` 和 `memory_type_mismatch`。这说明 type signal 有效但较弱，后续应优先改进 query intent parser 和候选召回。

## 下一步建议

优先做更强 embedding baseline 和 ANN 向量索引版候选召回。它们不需要继续花 DeepSeek 抽取费用，却能把当前结果从“工程实验”推进到“论文实验”。
