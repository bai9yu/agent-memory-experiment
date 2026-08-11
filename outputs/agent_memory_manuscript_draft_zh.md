# 面向长对话智能体的事实级记忆写入与候选级学习重排

> 当前状态：论文正文初稿。本文稿已经可用于组会、开题/中期汇报或继续扩写，但在外部 embedding baseline 和人工一致性确认完成前，不应作为最终投稿稿。

## 摘要

长对话智能体需要在不断增长的交互历史中检索与当前任务相关的个体事实、事件、偏好和计划。本文围绕 agent memory 的写入、检索、压缩和重排过程构建一套可复现实验框架，并在 LoCoMo10 answerable slice 上比较 LLM-written fact memory、LoCoMo observation memory、BGE-M3 embedding 检索、BM25 混合检索、时间感知重排、type-aware 重排和候选级学习重排。实验显示，DeepSeek fact memory + type-aware reranking 达到 MRR 0.609、Recall@5 0.733，高于 LoCoMo observation memory + type-aware 的 MRR 0.583、Recall@5 0.703。候选级学习重排进一步将 held-out MRR 从 0.607 提升至 0.661，而 feature ablation 显示更简洁的 intrinsic feature reranker 可达到 MRR 0.672、Recall@5 0.801，并在 leave-one-conversation-out split 中达到 MRR 0.664、Recall@5 0.797。同时，事实级记忆将 memory token 降至 observation memory 的 77.4%，DeepSeek memory writer 三次运行的 MRR 标准差为 0.004。负结果表明，Type 3 多证据问题仍是主要边界，浅层单候选重排和简单 query decomposition 不能有效提高覆盖率。本文还给出复现清单、审稿风险矩阵和人工复核流程，用于后续补齐外部 embedding baseline 与人工一致性证据。

## 1 引言

长对话智能体的记忆模块通常同时承担三个目标：保留长期个人事实，控制存储与检索成本，并在新任务中快速找到可用证据。直接保留原始对话虽然信息完整，但会带来上下文窗口、检索噪声和隐私控制问题；过度压缩的 session summary 又可能丢失细粒度事实。因此，一个可投稿的 agent memory 实验需要同时回答：记忆写入是否有效，检索/重排是否带来增益，多证据问题是否被解决，以及这些结论是否可复现。

本文的核心观察是：将长对话写成结构化 fact-level memory 后，固定检索器已经能获得强基线；真正明显的性能增量来自候选级学习重排，而不是简单的时间或类型启发式。与此同时，Type 3 多证据问题对当前方法仍然困难，说明未来需要 listwise/setwise objective 或更强的 LLM 子问题分解。

本文贡献如下：

1. 构建一套覆盖 memory writing、retrieval、reranking、compression、efficiency diagnostics 和 error audit 的 agent memory 实验框架。
2. 在 LoCoMo10 answerable slice 上验证 DeepSeek fact-level memory 相比 observation memory 具有更好的检索表现和更低 token 存储成本。
3. 提出并验证 candidate-level learned reranking，并通过 feature-group ablation 发现更简洁的 intrinsic feature reranker；held-out、bootstrap CI 和 LOCO split 均支持该类方法优于 type-aware reranking。
4. 系统报告 Type 3 multi-evidence retrieval 的负结果，明确当前方法边界。
5. 提供论文级 artifact：复现清单、实验协议、审稿风险矩阵、LLM-assisted audit、盲审人工复核表和 priority20 人工确认包。

## 2 任务定义

给定查询 \(q\) 和记忆库 \(M=\{m_i\}_{i=1}^{N}\)，每个查询对应一个或多个 gold memory \(G_q\subset M\)。系统目标是在 Top-K 返回集合中覆盖至少一个或尽可能多的 gold memory。本文主要使用 Recall@K、MRR 和多证据 Coverage@K：

\[Recall@K=\frac{1}{|Q|}\sum_{q\in Q}\mathbf{1}[\exists g\in G_q, rank_q(g)\le K]\]

\[MRR=\frac{1}{|Q|}\sum_{q\in Q}\frac{1}{\min_{g\in G_q}rank_q(g)}\]

\[Coverage@K=\frac{1}{|Q|}\sum_{q\in Q}\frac{|G_q\cap TopK(q)|}{|G_q|}\]

## 3 方法

### 3.1 Fact-Level Memory Writing

本文使用 DeepSeek API 从 LoCoMo 长对话中抽取事实级记忆。每条记忆包含文本、记忆类型、日期、实体、重要性和 source evidence。形式化地，记忆可表示为：

\[m_i=(text_i,type_i,date_i,entities_i,importance_i,source_i)\]

与 session summary 或 observation memory 相比，fact-level memory 的目标是将检索单元压缩到可直接回答问题的事实粒度，从而降低检索噪声和存储 token。

### 3.2 固定检索与 Type-Aware Reranking

基础检索包括 keyword、vector 和 hybrid。hybrid score 组合语义相似度、BM25 和实体匹配：

\[S_{hybrid}=0.65s_{sem}+0.30s_{bm25}+0.05s_{entity}\]

time-aware 与 type-aware reranking 在 hybrid 的基础上进一步加入时间、人物、重要性和 query-intent 与 memory type 的匹配项：

\[S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\gamma p(q,m_i)+\eta I(m_i)+\lambda T(q,m_i)\]

其中 \(g(q)\) 是 recency gate，\(d(q,m_i)\) 是时间衰减，\(p(q,m_i)\) 是 persona match，\(I(m_i)\) 是重要性 proxy，\(T(q,m_i)\) 表示 query-intent 与 memory type 的匹配。

### 3.3 Intrinsic Candidate-Level Learned Reranking

候选级学习重排从 keyword、vector、hybrid、time-aware 和 type-aware 的 Top-K 并集中构造候选集，并为每个候选抽取语义、关键词、时间、人物、memory type、importance 和交互特征。完整版本也可使用各检索器的 method-level score/rank，但 feature-group ablation 显示，只使用候选自身 intrinsic features 的变体更稳定。模型学习候选是否为 gold memory 的相关性分数：

\[\hat{y}_{q,i}=f_{\theta}(s_{sem},s_{bm25},d(q,m_i),p(q,m_i),T(q,m_i),type_i,I_i,\phi(q,m_i))\]

其中 \(\phi(q,m_i)\) 表示语义-关键词、persona-type、recency-decay 等交互项。最终按照 \(\hat{y}_{q,i}\) 对候选重新排序。该方法不重新生成记忆，而是在已有检索结果上学习更稳健的排序函数。

## 4 实验设置

数据使用 LoCoMo10 answerable slice，包含 2517 条 fact memory 和 1838 条可评估查询。主结果使用本地 BGE-M3 embedding cache。评估指标为 Recall@1/3/5、MRR，以及 Type 3 多证据问题的 Coverage@K。显著性检验采用 paired bootstrap 置信区间和 paired permutation test。

候选级重排使用四类稳定性检查：held-out query split 用于基础泛化检查，20-seed split sweep 用于排除单一随机划分偶然性，train-fraction sensitivity 用于检查训练比例依赖，leave-one-conversation-out split 用于验证模型是否跨 conversation 泛化。intrinsic feature reranker 同时报告 held-out、multi-seed、train-fraction 和 LOCO 结果。所有可复现入口记录在 `outputs/agent_memory_reproducibility_checklist_zh.md`。

## 5 结果

### 5.1 主检索结果

| Method | MRR | Recall@5 |
| --- | --- | --- |
| hybrid | 0.583 | 0.705 |
| time-aware | 0.605 | 0.727 |
| type-aware | 0.609 | 0.733 |
| candidate reranker | 0.661 | 0.796 |
| intrinsic feature reranker | 0.672 | 0.801 |
| intrinsic feature reranker LOCO | 0.664 | 0.797 |
| candidate reranker LOCO | 0.657 | 0.782 |

fact memory + type-aware 的 MRR 为 0.609，Recall@5 为 0.733，高于 observation memory + type-aware 的 MRR 0.583 和 Recall@5 0.703。这说明将长对话写成事实级记忆可以作为有效的 memory representation。

### 5.2 Type-Aware Reranking 的作用

type-aware 相比 time-aware 的 MRR delta 为 +0.0042，p=0.0072；Recall@5 delta 为 +0.0065，p=0.0028。该增益幅度不大，但在 MRR 和 Recall@5 上具有统计支持，因此适合写作一个有用的固定打分组件。

### 5.3 Intrinsic Candidate-Level Reranking 是主要收益来源

在 held-out split 下，full candidate reranker 将 MRR 从 0.607 提升到 0.661，MRR delta 为 +0.0539，p=0.0002；Recall@5 delta 为 +0.0623。进一步的 feature-group ablation 显示，intrinsic feature reranker 达到 MRR 0.672、Recall@5 0.801，相对 type-aware 的 MRR delta 为 +0.0652，95% CI=[0.0545, 0.0763]；相对 full reranker 的 MRR delta 为 +0.0113，95% CI=[0.0029, 0.0199]。oracle-gap 分析显示，intrinsic reranker 在 held-out MRR 上关闭 candidate-oracle gap 的 0.215，Recall@5 closure 为 0.387；LOCO MRR closure 为 0.184，说明当前方法有效但仍未穷尽候选池上界。paired outcome 分析显示，MRR improved/worsened/tied 为 771/591/1398，Cohen dz=0.2234；Recall@5 improved/worsened/tied 为 280/92/2388，但 Type 3 Recall@5 delta 为 -0.0476，Type 3 set Coverage@5 oracle-gap closure 为 -0.2150，说明收益并不覆盖多证据问题。扩展 20-seed stability 检查显示，intrinsic reranker 在 20/20 个随机划分上 MRR 均高于 type-aware，平均 ΔMRR=+0.0602，最小 ΔMRR=+0.0414。训练比例敏感性实验进一步显示，在 train fraction 0.5/0.6/0.7/0.8 下，intrinsic reranker 的最低 MRR win rate=1.00，最小 seed-level ΔMRR=+0.0414，平均 fraction-level ΔMRR=+0.0608。在 LOCO split 下，intrinsic feature reranker 的 MRR 为 0.664、Recall@5 为 0.797，相对 type-aware 的 MRR delta 为 +0.0567，95% CI=[0.0439, 0.0696]，Recall@5 delta 为 +0.0658，95% CI=[0.0490, 0.0827]。这支持将 intrinsic candidate-level learned reranking 作为本文最主要的方法贡献，同时把 method-level rank/score 特征视为可能带来噪声的消融发现。

### 5.4 存储效率与 Writer 稳定性

fact memory 使用 31148 个 memory tokens，而 observation memory 使用 40241 个 tokens，fact/observation token ratio 为 0.774。DeepSeek writer 三次运行的 MRR mean=0.613, stdev=0.004；Recall@5 mean=0.738, stdev=0.006。这些结果说明当前 LoCoMo10 范围内 writer 输出对主指标影响较小，但仍需要在更大切片或第二数据集上复验。

### 5.5 Type 3 多证据负结果

Type 3 supervised set selector 的 Coverage@5 delta 为 -0.0572，p=0.0286，说明浅层 set selector 不但没有解决多证据检索，反而降低了覆盖率。本文因此将 Type 3 写作方法边界，而不是已解决问题。

## 6 错误分析与可靠性

当前已有 80 条 LLM-assisted audit 初稿，并生成 priority20 快速人工确认包和盲审人工复核表。priority20 包包含 20 条样本，当前人工确认 0 条。该流程适合先在不暴露 LLM 预标注的条件下完成 quick-review，再回填 confirmation 表并报告 exact agreement 与 Cohen's kappa；完整投稿前仍应扩展到 80 条。

## 7 Threats to Validity 与限制

本文当前有效性威胁附录覆盖 8 项风险，类别包括 construct_validity, external_validity, internal_validity, reliability, reproducibility, scalability_validity, statistical_conclusion_validity；其中仍有 2 项会阻止最终投稿。第一，外部 embedding baseline completed=0，因此目前不能把外部 API embedding 对照写入主结果。第二，Human/LLM 人工确认尚未完成，不能宣称 human-verified error analysis。第三，主结果仍限定在 LoCoMo10 answerable slice；LOCO split 支持跨 conversation 泛化，但不等同于跨数据集泛化。第四，MRR/Recall@K 只衡量 memory retrieval，不等价于端到端 agent task success。第五，100k 扩展性实验包含 synthetic distractor，只能作为效率诊断，不能直接代表真实生产规模。完整有效性威胁、缓解措施和论文声明边界见 `outputs/agent_memory_threats_to_validity_zh.md`。

## 8 结论

本文给出一套面向长对话智能体记忆的可复现实验框架。结果显示，LLM-written fact memory 是紧凑且有效的记忆表示，intrinsic candidate-level learned reranking 是当前最强的排序改进，而 Type 3 多证据检索仍是关键未解问题。后续最小补强是完成一个外部 embedding baseline，并通过盲审表填写 priority20/80 Human/LLM confirmation 以形成可靠性证据。

## Appendix A 复现状态

- Artifact gate：135/135
- Metric gate：19/19
- 关键文档：`outputs/agent_memory_experiment_protocol_zh.md`、`outputs/agent_memory_submission_gap_analysis_zh.md`、`outputs/agent_memory_reproducibility_checklist_zh.md`、`outputs/agent_memory_manuscript_claim_check_zh.md`、`outputs/agent_memory_threats_to_validity_zh.md`、`outputs/agent_memory_human_audit_readiness_gate_zh.md`。

## Appendix B 投稿前 TODO

- 运行外部 embedding baseline，生成 `agent_memory_embedding_baseline_comparison_zh.md` 的 completed 版本。
- 填写 `agent_memory_human_audit_priority20_blind_review.csv` 的 human_* 字段，回填 confirmation 后生成 quick-review agreement。
- 若目标为更高等级会议/期刊，继续扩展 LoCoMo slice 或加入第二数据集。
