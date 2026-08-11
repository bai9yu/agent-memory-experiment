# Agent Memory 论文草稿骨架

本文件面向论文写作，不是最终论文。它把当前实验结果组织成可投稿论文的章节结构，并明确哪些结论已有证据、哪些只能写为限制或未来工作。

## 题目候选

1. 面向长对话智能体的事实级记忆写入与候选级学习重排
2. Agent Memory Retrieval with LLM-Written Facts and Candidate-Level Reranking
3. From Memory Writing to Retrieval: A Reproducible Study on Long-Conversation Agent Memory

## 摘要草稿

长对话智能体需要在大量历史交互中高效检索与当前任务相关的事实记忆。本文构建了一个基于 LoCoMo 长对话数据的可复现实验框架，比较 DeepSeek 抽取的 fact-level memory、LoCoMo 官方 observation memory、本地 BGE-M3 embedding 检索、BM25 混合检索、时间感知重排、type-aware 重排以及候选级学习重排。在 LoCoMo10 answerable slice 上，DeepSeek fact memory + type-aware reranking 取得 MRR 0.609 和 Recall@5 0.733，高于 LoCoMo observation memory 的 MRR 0.583 和 Recall@5 0.703。进一步地，候选级学习重排在 held-out split 上将 MRR 从 0.607 提升到 0.661，MRR delta 为 +0.0539，permutation p=0.0002。在更严格的 leave-one-conversation-out split 下，candidate reranker 的 MRR 为 0.657，高于 type-aware 的 0.608，加权 MRR delta 为 +0.0504。DeepSeek memory writer 三次运行的 MRR 均值为 0.613，标准差为 0.004，Recall@5 均值为 0.738，标准差为 0.006。错误分析方面，80 条 LLM-assisted audit 初稿中 auto_reason_correct 的 yes/partial/no 为 28/29/23，并已生成 Human/LLM 确认表，可作为人工复核前的预标注材料。同时，Type 3 多证据问题仍是主要边界，浅层 set selector 和关键词式 decomposition 未能改善 Coverage@5。本文给出主结果、负结果、稳定性、效率诊断和复现清单，并指出外部 embedding baseline 和人工错误复核仍需补齐后才能作为完整投稿版本。

## 贡献点写法

- 构建一套面向 agent memory 的可复现实验框架，覆盖 memory write、retrieval、reranking、compression、cross-agent reuse 和 error analysis。
- 证明 fact-level LLM-written memory 在 LoCoMo10 上可以作为紧凑且有效的记忆形态，同时节省存储 token。
- 提出并验证 candidate-level learned reranking，比固定 type-aware scoring 有显著提升。
- 系统报告 Type 3 multi-evidence retrieval 的负结果，说明浅层单候选重排和简单 query decomposition 不足以解决多证据覆盖。
- 提供复现实验包、环境快照、证据矩阵、人工复核协议、writer stability 框架和 API embedding baseline 框架。

## 方法章节结构

### Problem Setup

给定查询 \(q\) 和记忆库 \(M=\{m_i\}_{i=1}^{N}\)，目标是在 Top-K 中召回答案证据记忆 \(G_q\subset M\)。主要指标为 Recall@K 和 MRR。

### Memory Writing

使用 DeepSeek 将长对话 session/turn 抽取为结构化 fact-level memory：

\[m_i=(text_i, type_i, date_i, entities_i, importance_i, source_i)\]

当前稳定性框架已登记 3 次 LoCoMo10 抽取，completed runs=3。

### Retrieval Scoring

语义分数：

\[s_{sem}(q,m_i)=\cos(e(q), e(m_i))\]

混合检索：

\[S_{hybrid}=0.65s_{sem}+0.30s_{bm25}+0.05s_{entity}\]

time-aware / type-aware 重排：

\[S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\gamma p(q,m_i)+\eta I(m_i)+\lambda T(q,m_i)\]

其中 \(g(q)\) 为 recency gate，\(d\) 为时间衰减，\(p\) 为 persona match，\(I\) 为 importance proxy，\(T\) 为 query-intent 与 memory type 的匹配分。

### Candidate-Level Learned Reranking

从 keyword/vector/hybrid/time-aware/type-aware 的 Top-K 并集构造候选集合，用候选级特征学习相关性：

\[\hat{y}_{q,i}=f_{\theta}(s_{sem},s_{bm25},S_{hybrid},S_{time},S_{type},rank_{*},type_i,I_i,...)\]

最终按 \(\hat{y}_{q,i}\) 重新排序候选。当前该方法是最强方法贡献。

## 实验章节结构

### RQ1: LLM-written fact memory 是否有效？

- 主表：fact memory type-aware MRR 0.609, Recall@5 0.733；observation MRR 0.583, Recall@5 0.703。
- 写法：可以作为 memory-form comparison；必须说明 LoCoMo10 slice 限制，并把 writer stability 作为 LoCoMo10 范围内证据。

### RQ2: 固定重排组件是否有用？

- 表格：paper tables 中的 LoCoMo10 主检索结果和 type-aware 显著性。
- 写法：type-aware 是小幅但可靠提升，不要夸大 Recall@1/3。

### RQ3: 学习式候选重排是否带来主要收益？

- 结果：candidate reranker MRR 0.661 vs type-aware 0.607；MRR delta +0.0539，Recall@5 delta +0.0623。
- LOCO 验证：candidate reranker MRR 0.657 vs type-aware 0.608；加权 MRR delta +0.0504，Recall@5 delta +0.0522。
- 写法：这是当前论文最稳的算法贡献；随机 held-out 与 leave-one-conversation-out 均支持该结论。

### RQ4: Type 3 多证据问题是否解决？

- 结果：supervised set selector Coverage@5 delta -0.0572，p=0.0286。
- 写法：作为负结果和 limitation；不能宣称解决 Type 3。

### RQ5: 效率与扩展性如何？

- 写法：sklearn exact NN / FAISS / LSH 作为效率与索引诊断；100k synthetic distractor 必须标注 synthetic。

## 当前不可写为主结果的内容

- `reliability_protocol`：自动错误分析已经具备人工复核入口，并已有 LLM-assisted 预标注。；缺口：需要在 confirmation CSV 中填写 human_* 字段，并重新运行一致性脚本，得到 exact agreement 与 Cohen's kappa。
- `baseline_protocol`：外部 embedding baseline 已经具备 API 接入与缓存框架，但尚未形成实验结果。；缺口：需要提供 API key 并实际运行 text-embedding-3-small 等外部 embedding 对照。
- `open_gap`：完整项目距离最终投稿仍需要额外验证。；缺口：投稿前至少补齐一个强 baseline 家族，以及一个稳定性/可靠性检查。

## 投稿前最小完成条件

投稿风险矩阵当前列出 8 个审稿风险，其中 2 个 blocker。完整清单见 `outputs/agent_memory_submission_gap_analysis_zh.md`。

1. 至少完成一个外部 embedding baseline，并自动生成与 BGE-M3 的 delta 对比。
2. 优先在盲审人工复核表中填写 human_* 字段，回填 Human/LLM 确认表后报告 exact agreement 与 Cohen's kappa。
3. 若不补外部数据集，需要在论文中明确本工作是 LoCoMo10 slice 的系统性实验，而非广泛泛化结论。

## 复现状态

- Artifact gate: 63/63
- Metric gate: 5/5
- 关键入口：`outputs/agent_memory_reproducibility_checklist_zh.md`、`outputs/agent_memory_paper_evidence_matrix_zh.md`、`outputs/agent_memory_paper_tables_zh.md`、`outputs/agent_memory_experiment_protocol_zh.md`、`outputs/agent_memory_manuscript_draft_zh.md`。
