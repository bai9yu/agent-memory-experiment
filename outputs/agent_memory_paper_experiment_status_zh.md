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

按 query type 分析显示，candidate reranker 的收益并不均匀：

| Query Type | Base MRR | Reranker MRR | Delta MRR | Base R@5 | Reranker R@5 |
|---|---:|---:|---:|---:|---:|
| Type 1 | 0.508 | 0.537 | +0.0288 | 0.661 | 0.707 |
| Type 2 | 0.714 | 0.766 | +0.0522 | 0.833 | 0.895 |
| Type 3 | 0.439 | 0.419 | -0.0194 | 0.548 | 0.492 |
| Type 4 | 0.667 | 0.718 | +0.0515 | 0.793 | 0.846 |
| Type 5 | 0.524 | 0.613 | +0.0887 | 0.645 | 0.756 |

结论：candidate reranker 对 Type 5、Type 2、Type 4 收益最明显，说明它能纠正固定公式在关键词/事件/偏好类问题上的排序错误；但 Type 3 下降，说明推理型或跨事实问题仍需要单独处理，可能需要多证据聚合或 answer-aware reranking。

进一步做 Top-K 多证据覆盖分析，比较 `type_aware` 与 candidate reranker 的候选集合是否覆盖答案 evidence set：

| Query Type | Mean Gold | Multi-Evidence Share | Base Coverage@5 | Reranker Coverage@5 | Delta |
|---|---:|---:|---:|---:|---:|
| Type 1 | 4.06 | 0.930 | 0.309 | 0.352 | +0.0430 |
| Type 2 | 1.56 | 0.399 | 0.707 | 0.781 | +0.0740 |
| Type 3 | 2.65 | 0.675 | 0.377 | 0.372 | -0.0050 |
| Type 4 | 1.44 | 0.340 | 0.688 | 0.744 | +0.0565 |
| Type 5 | 1.50 | 0.354 | 0.552 | 0.652 | +0.1000 |

该结果支持 Type 3 的错误诊断：Type 3 的平均 gold evidence 数为 `2.65`，多证据问题比例为 `0.675`，明显高于 Type 2/4/5；candidate reranker 虽然提升总体 Top-1，但没有改善 Type 3 的 Top-5 evidence coverage ratio。因此下一步应做 set-level selection，而不是只继续优化单候选排序。

进一步测试无监督 set-level selection baseline：在 candidate reranker 的 Top-10 内保留原 Top-1，再用文本 Jaccard 去重和 memory type 多样性选择后续候选。结果显示该启发式方法没有改善 Type 3：

| Method | Type 3 MRR | Type 3 R@5 | Type 3 Coverage@5 | Type 3 Full@5 | Type 3 Coverage@10 |
|---|---:|---:|---:|---:|---:|
| candidate_reranker | 0.410 | 0.492 | 0.372 | 0.262 | 0.462 |
| set_selector_type3 | 0.407 | 0.468 | 0.351 | 0.238 | 0.462 |

结论：仅在当前 Top-10 里做启发式多样性重排会把部分相关证据推后，无法解决 Type 3。下一步应扩大候选召回、做 query decomposition，或训练真正的 set-level selector。

候选深度分析进一步显示，Type 3 的相关 evidence 在更深候选中仍有明显空间：

| K | Base Coverage | Reranker Coverage | Delta Coverage | Base Full | Reranker Full | Delta Full |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.167 | 0.182 | +0.0146 | 0.063 | 0.079 | +0.0159 |
| 3 | 0.332 | 0.316 | -0.0157 | 0.190 | 0.198 | +0.0079 |
| 5 | 0.377 | 0.372 | -0.0050 | 0.230 | 0.262 | +0.0317 |
| 10 | 0.459 | 0.462 | +0.0029 | 0.317 | 0.325 | +0.0079 |
| 20 | 0.526 | 0.597 | +0.0711 | 0.373 | 0.444 | +0.0714 |

结论：Type 3 并非完全缺少候选证据，而是相关 evidence 往往落在 Top-10 之后。下一步更合理的路线是“扩大候选召回到 Top-20/Top-50 + 学习式集合选择”，而不是只在 Top-10 内做启发式 MMR。

将同一个无监督 set-level selection baseline 改用 Top-20 候选池后，Type 3 仍未改善：

| Method | Type 3 MRR | Type 3 R@5 | Type 3 Coverage@5 | Type 3 Full@5 | Type 3 Coverage@20 | Type 3 Full@20 |
|---|---:|---:|---:|---:|---:|---:|
| candidate_reranker | 0.418 | 0.492 | 0.372 | 0.262 | 0.597 | 0.444 |
| set_selector_type3 | 0.412 | 0.452 | 0.340 | 0.238 | 0.597 | 0.444 |

结论：Top-20 候选池里确实有更多 evidence，但简单去重/类型多样性不会把它们提前到 Top-5；真正需要的是带监督信号的 set-level learning，或先做 query decomposition 再分别召回。

进一步测试 Type 3 专用监督重排：使用同一 query-level held-out 划分，对比固定 `type_aware`、全局 candidate reranker、只用 Type 3 训练样本学习的专用 reranker，以及 candidate oracle。

| Method | Type 3 MRR | Type 3 R@1 | Type 3 R@3 | Type 3 R@5 | Coverage@5 | Full@5 |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 0.434 | 0.344 | 0.507 | 0.546 | 0.377 | 0.230 |
| global_candidate_reranker | 0.421 | 0.351 | 0.432 | 0.496 | 0.372 | 0.262 |
| type3_specific_reranker | 0.399 | 0.312 | 0.417 | 0.475 | 0.331 | 0.206 |
| candidate_oracle | 0.778 | 0.778 | 0.778 | 0.778 | 0.658 | 0.524 |

结论：Type 3 专用单候选重排没有改善，反而低于固定 `type_aware`。这说明当前 Type 3 的瓶颈不是“把所有类型混在一起训练导致分布不匹配”，而是多证据问题本身需要集合级目标或 query decomposition。Candidate oracle 仍明显更高，证明候选池中存在可利用空间，但需要更适合多证据覆盖的模型。

配对显著性检验显示 Type 3 专用重排相对 `type_aware` 的下降并非偶然：MRR delta `-0.0362`，95% CI `[-0.0705, -0.0002]`，p-value `0.0460`；Recall@5 delta `-0.0794`，95% CI `[-0.1429, -0.0238]`，p-value `0.0260`。

继续测试 Type 3 监督式 greedy set selector：模型每一步选择候选时加入已选集合的文本冗余和 memory type 覆盖特征，直接面向多证据集合选择。但该方法仍未超过固定 `type_aware`：

| Method | Type 3 MRR | Type 3 R@1 | Type 3 R@3 | Type 3 R@5 | Coverage@5 | Full@5 |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 0.434 | 0.344 | 0.507 | 0.546 | 0.377 | 0.230 |
| type3_specific_reranker | 0.399 | 0.312 | 0.417 | 0.475 | 0.331 | 0.206 |
| supervised_set_selector | 0.389 | 0.312 | 0.393 | 0.490 | 0.320 | 0.175 |
| candidate_oracle | 0.778 | 0.778 | 0.778 | 0.778 | 0.658 | 0.524 |

显著性检验显示 `supervised_set_selector` 相比 `type_aware` 的 MRR delta 为 `-0.0456`，95% CI `[-0.0893, -0.0017]`，p-value `0.0366`；Recall@5 delta 为 `-0.0635`，p-value `0.1410`。结论：仅靠候选上下文特征和贪心集合选择不足以解决 Type 3；下一步应显式做 query decomposition，或使用真正的 listwise/setwise objective。

进一步测试关键词式 query decomposition 弱基线：从 Type 3 query 中抽取人物名、内容关键词和短窗口 facet query，分别做 BM25 召回，再与 `type_aware` 做保守 RRF 融合。结果仍低于固定 `type_aware`：

| Method | Type 3 MRR | Type 3 R@1 | Type 3 R@3 | Type 3 R@5 | Coverage@5 | Coverage@20 |
|---|---:|---:|---:|---:|---:|---:|
| type_aware | 0.429 | 0.326 | 0.488 | 0.547 | 0.370 | 0.537 |
| query_decomposition | 0.214 | 0.128 | 0.221 | 0.279 | 0.161 | 0.324 |
| type_aware_plus_decomposition | 0.342 | 0.198 | 0.442 | 0.512 | 0.337 | 0.537 |

融合方法的 Coverage@20 与 `type_aware` 持平，但 MRR 和 Top5 指标下降；显著性检验显示 MRR delta 为 `-0.0867`，95% CI `[-0.1376, -0.0442]`，p-value `0.0002`。结论：简单关键词窗口拆解噪声过大，容易把人物身份/泛化事实推到前面；如果继续做 query decomposition，需要使用更准确的 LLM 子问题生成或任务专用规则，而不是弱关键词拆解。

对 Type 3 三条改进尝试进一步做 evidence coverage 显著性汇总：

| Experiment | Candidate | Coverage@5 Delta | Coverage@5 p-value | Coverage@20 Delta | Coverage@20 p-value |
|---|---|---:|---:|---:|---:|
| type3_specific_reranker | type3_specific_reranker | -0.0467 | 0.0474 | +0.0192 | 0.4653 |
| supervised_set_selector | supervised_set_selector | -0.0572 | 0.0286 | +0.0101 | 0.6823 |
| query_decomposition_fusion | type_aware_plus_decomposition | -0.0325 | 0.0198 | +0.0000 | 1.0000 |

结论：三条 Type 3 尝试在 Coverage@5 上均下降，且均有统计证据；Coverage@20 没有可靠提升。因此当前 Type 3 失败并不是“多证据已经在深层候选中被方法稳定召回，只是没排到前面”，而是这些浅层方法没有形成有效的前排 evidence coverage 目标。

## 距离论文发表级仍缺的内容

当前已生成论文表格包：

- `outputs/agent_memory_paper_tables_zh.md`：Markdown 主表、消融表、Type 3 失败分析表。
- `outputs/agent_memory_paper_tables.tex`：可直接复制到论文的 LaTeX `booktabs` 表格。
- `outputs/agent_memory_paper_evidence_matrix_zh.md`：按“论文主张-证据-证据强度-剩余缺口”整理当前实验是否足以支撑投稿表述。
- `outputs/agent_memory_embedding_baseline_status_zh.md`：外部 embedding baseline 接入状态；当前 OpenAI-compatible `text-embedding-3-small` baseline 已有 API/cache 入口，但尚未实际运行出指标。
- `outputs/agent_memory_human_audit_protocol_zh.md`：自动错误分析的人工复核协议；已生成 80 条分层抽样待标注样本，但人工标注尚未完成。
- `outputs/agent_memory_human_audit_summary_zh.md`：人工复核统计报告；当前为 `pending_labels`，用于标注完成后自动汇总可靠性。

当前已生成论文复现清单：

- `outputs/agent_memory_reproducibility_checklist_zh.md`：检查关键 artifact、核心指标阈值、数据规模和复现命令入口；当前 artifact gate 为 `17/17`，metric gate 为 `5/5`。
- `outputs/agent_memory_environment_snapshot_zh.md`：记录 Python、关键依赖包、BGE-M3 本地缓存、Git 状态和系统环境；不读取 `.env`，不包含 API key。

1. 重复抽取实验：至少对 LoCoMo10 做 3 次不同 seed / temperature 的 DeepSeek 抽取，报告均值和方差。
2. 更强 embedding baseline：加入 OpenAI embedding 或其他主流 embedding API、本地 BGE-small / BGE-M3 对比。
3. 在线检索效率：已有 sklearn exact NN、FAISS Flat、FAISS IVF 和 100k synthetic distractor scale test；仍需在真实更大 memory bank 上验证 ANN 优势，并可补 HNSW/IVF-PQ 对照。
4. 学习式重排：candidate-level reranker 已有显著提升；Type 3 专用单候选重排、监督式 greedy set selector 和关键词式 query decomposition 均已验证为负结果，下一步需要更强 LLM 子问题生成或真正 listwise/setwise objective。
5. 跨智能体/KV cache 方向：需要把当前 synthetic cross-agent 实验替换为真实或半真实 multi-agent trace。
6. 人工复核：已生成 80 条分层抽样复核表，下一步需要人工填写并统计自动错误分类可靠性。

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
