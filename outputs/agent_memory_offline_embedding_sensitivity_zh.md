# Offline Embedding Sensitivity

本报告比较主实验使用的 BGE-M3 检索与完全离线的 hash vector / BM25 keyword 下界。它不调用外部 API，因此不能替代最终的 OpenAI/Cohere/Jina 等外部 embedding baseline；它的作用是证明当前结论不是只来自单一排序公式，并给出 lexical 与弱语义编码器的可复现下界。

## 数据与输入

- BGE-M3 summary: `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv`
- Hash summary: `work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_hash_type_004_with_keyword/summary.csv`
- Query 数：1838

## 主表

| Baseline | Role | N | MRR | R@1 | R@3 | R@5 | ΔMRR vs BGE type-aware | ΔR@5 vs BGE type-aware |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BGE-M3 vector | semantic_vector | 1838 | 0.527 | 0.419 | 0.585 | 0.643 | -0.083 | -0.090 |
| BGE-M3 hybrid | semantic_plus_keyword | 1838 | 0.583 | 0.477 | 0.647 | 0.705 | -0.026 | -0.028 |
| BGE-M3 type-aware | main_retrieval_baseline | 1838 | 0.609 | 0.503 | 0.670 | 0.733 | +0.000 | +0.000 |
| Hash vector | offline_semantic_floor | 1838 | 0.354 | 0.268 | 0.385 | 0.442 | -0.256 | -0.292 |
| Hash hybrid | offline_hybrid_floor | 1838 | 0.495 | 0.393 | 0.547 | 0.614 | -0.115 | -0.120 |
| Hash type-aware | offline_type_aware_floor | 1838 | 0.498 | 0.397 | 0.553 | 0.606 | -0.112 | -0.127 |
| BM25 keyword | lexical_baseline | 1838 | 0.526 | 0.428 | 0.581 | 0.634 | -0.084 | -0.099 |

## 关键差值

| Delta | MRR | R@1 | R@3 | R@5 |
| --- | --- | --- | --- | --- |
| bge_type_minus_hash_type | +0.112 | +0.107 | +0.118 | +0.127 |
| bge_type_minus_keyword | +0.084 | +0.075 | +0.090 | +0.099 |
| bge_hybrid_minus_hash_hybrid | +0.089 | +0.083 | +0.100 | +0.091 |

## 论文解释

- BGE-M3 type-aware 的 MRR/R@5 为 0.609/0.733，hash type-aware 为 0.498/0.606，说明真实语义 encoder 带来 +0.112 MRR 和 +0.127 R@5 的增量。
- BM25 keyword 的 MRR/R@5 为 0.526/0.634，高于 hash vector，但低于 BGE-M3 type-aware；这说明 lexical matching 是强下界，语义编码与 type-aware reranking 仍有额外收益。
- 当前仍不能写成外部 embedding 泛化已经完成；最终投稿前仍需至少一个真实 API embedding baseline。

## 写法边界

- 可以写：我们报告了 BGE-M3、BM25 keyword 和 hash-vector 离线下界，验证主方法相对弱语义/词面检索的收益。
- 应谨慎：hash vector 不是主流 embedding model，只能作为工程下界和 pipeline sanity check。
- 不能写：该结果替代了 OpenAI/Cohere/Jina 等外部 embedding baseline。
