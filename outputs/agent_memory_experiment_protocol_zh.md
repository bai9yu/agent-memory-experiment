# 论文实验协议与审稿复核清单

本文件把当前 agent memory 实验整理为论文 appendix 可用的实验协议。它强调数据范围、模型组件、评价指标、显著性检验、复现入口和不能过度宣称的边界。

## 1. 数据与切片

- 数据源：LoCoMo10 answerable slice。
- 事实级记忆数：2517
- 可评估查询数：1838
- 主要实验单位：query-memory retrieval；每个 query 有一个或多个 gold memory ids。
- 论文写法：所有主结论默认限定在 LoCoMo10 answerable slice，除 LOCO split 外不宣称跨数据集泛化。

## 2. 记忆写入与检索组件

- Memory writer：DeepSeek API 抽取 fact-level memory，字段包括 text、type、date、entities、importance、source evidence。
- Memory baseline：LoCoMo 官方 observation memory。
- Embedding：本地主结果使用 BGE-M3 缓存；外部 API embedding baseline 当前仍是投稿 blocker。
- 检索方法：keyword、vector、hybrid、time-aware、type-aware、candidate-level learned reranker。
- 学习式重排：从多个检索器 Top-K 并集构造候选，使用候选级特征预测相关性分数，再重新排序。

## 3. 指标与公式

- Recall@K：\(\frac{1}{|Q|}\sum_{q\in Q}\mathbf{1}[\exists g\in G_q, rank_q(g)\le K]\)。
- MRR：\(\frac{1}{|Q|}\sum_{q\in Q}\frac{1}{\min_{g\in G_q} rank_q(g)}\)。
- 多证据 Coverage@K：\(\frac{1}{|Q|}\sum_{q\in Q}\frac{|G_q\cap TopK(q)|}{|G_q|}\)。
- type-aware score：\(S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\gamma p(q,m_i)+\eta I(m_i)+\lambda T(q,m_i)\)。
- 显著性：paired bootstrap 置信区间 + paired permutation p-value；报告 improved / worsened / tied queries。

## 4. 主结果摘要

| Method | MRR | Recall@5 | Role |
| --- | --- | --- | --- |
| Fact memory + time-aware | 0.605 | 0.727 | fixed reranking baseline |
| Fact memory + type-aware | 0.609 | 0.733 | main fixed reranker |
| Observation + type-aware | 0.583 | 0.703 | memory-form baseline |
| Candidate reranker | 0.661 | 0.796 | held-out learned reranker |
| Candidate reranker LOCO | 0.657 | 0.782 | leave-one-conversation-out |

## 5. 显著性与泛化检查

| Comparison | Metric | Delta | Permutation p | CI Low | CI High |
| --- | --- | --- | --- | --- | --- |
| type-aware vs time-aware | MRR | +0.0042 | 0.0072 | 0.001 | 0.007 |
| type-aware vs time-aware | Recall@5 | +0.0065 | 0.0028 | 0.003 | 0.011 |
| candidate reranker vs type-aware | MRR | +0.0539 | 0.0002 | 0.046 | 0.062 |
| candidate reranker vs type-aware | Recall@5 | +0.0623 | 0.0002 | 0.050 | 0.075 |
| LOCO candidate reranker vs type-aware | MRR | +0.0504 | 0.0002 | 0.041 | 0.060 |
| LOCO candidate reranker vs type-aware | Recall@5 | +0.0522 | 0.0002 | 0.038 | 0.067 |

## 6. 稳定性与负结果

- DeepSeek memory writer 三次运行：MRR mean=0.613, stdev=0.004; Recall@5 mean=0.738, stdev=0.006。
- Type 3 supervised set selector Coverage@5 delta=-0.0572, p=0.0286；该结果应写为负结果和边界分析。
- Human/LLM 错误复核：已有 80 条确认表、priority20 快速抽查包 20 条和盲审人工复核表；当前人工确认 0 条；不能写作 human-verified error analysis。

## 7. 复现与审稿风险

- 复现清单：artifact gate 59/59，metric gate 5/5。
- 投稿风险矩阵：8 个风险，其中 blocker=2。
- 两个 blocker：外部 embedding baseline 未实际完成；Human/LLM 人工确认未完成。

## 8. 论文写法边界

- 可以写：fact-level memory 在 LoCoMo10 上有效且更紧凑；candidate-level reranker 在 held-out 和 LOCO split 下稳定优于 type-aware。
- 可以写：Type 3 multi-evidence retrieval 是当前方法边界，浅层修复方法为负结果。
- 暂不能写：跨数据集泛化、生产规模 ANN 结论、human-verified error analysis、外部 embedding baseline 主结果。

## 9. 最小投稿前检查

- 完成至少一个外部 embedding baseline 并生成 delta。
- 优先填写 priority20 blind review CSV 的 human_* 字段，回填 confirmation 后报告 quick-review exact agreement 和 Cohen's kappa；投稿前再扩展到完整 80 条。
- 在论文实验设置中显式写出 LoCoMo10 slice、BGE-M3 cache、DeepSeek writer、LOCO split、paired significance test。
