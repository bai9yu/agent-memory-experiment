# LLM Memory Extraction 对比报告

本报告比较 DeepSeek 抽取的 fact-level memory 与 LoCoMo 官方 observation memory，在同一 conversation/session slice 下的覆盖率、token 成本和 BGE-M3 检索效果。

## 主结果

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| llm_extracted_fact | 28 | 358 | 29 | 0.586 | 0.759 | 0.793 | 0.679 |
| locomo_observation | 28 | 464 | 29 | 0.483 | 0.724 | 0.793 | 0.619 |

## API 用量

| Variant | Prompt Tokens | Completion Tokens | Total Tokens |
|---|---:|---:|---:|
| llm_extracted_fact | 4012 | 2207 | 6219 |
| locomo_observation | 0 | 0 | 0 |

## Top-1 错误样例

### LLM Extracted Fact

- `q00004` What did Caroline research? -> `llm_00002`: Caroline is a transgender woman.
- `q00008` What is Caroline's relationship status? -> `llm_00002`: Caroline is a transgender woman.
- `q00016` What activities does Melanie partake in? -> `llm_00007`: Melanie is managing kids and work.
- `q00039` What activities has Melanie done with her family? -> `llm_00027`: Melanie cherishes time with her family and feels alive and happy when spending time with them.
- `q00061` What instruments does Melanie play? -> `llm_00024`: Melanie is married and has kids.
- `q00084` What did Melanie realize after the charity race? -> `llm_00011`: Melanie ran a charity race for mental health last Saturday.
- `q00085` How does Melanie prioritize self-care? -> `llm_00018`: Melanie believes self-care is important and helps her better look after her family.
- `q00086` What are Caroline's plans for the summer? -> `llm_00005`: Caroline plans to continue her education and explore career options.

### LoCoMo Observation

- `q00004` What did Caroline research? -> `obs_00015`: Caroline: Caroline started transitioning three years ago.
- `q00008` What is Caroline's relationship status? -> `obs_00021`: Caroline: Caroline's friends, family, and mentors are her rocks, motivating her and giving her strength to push on.
- `q00012` Where did Caroline move from 4 years ago? -> `obs_00015`: Caroline: Caroline started transitioning three years ago.
- `q00015` Would Caroline still want to pursue counseling as a career if she hadn't received support growing up? -> `obs_00003`: Caroline: Caroline is planning to continue her education and explore career options in counseling or mental health to support those with similar issues.
- `q00016` What activities does Melanie partake in? -> `obs_00010`: Melanie: Melanie carves out me-time each day for activities like running, reading, or playing the violin.
- `q00035` What events has Caroline participated in to help children? -> `obs_00018`: Caroline: Caroline feels sharing experiences is important to help promote understanding and acceptance.
- `q00048` Who supports Caroline when she has a negative experience? -> `obs_00014`: Caroline: Caroline is excited to create a family for kids who need one, even though she anticipates challenges as a single parent.
- `q00061` What instruments does Melanie play? -> `obs_00027`: Melanie: Melanie has been married for 5 years.

## 解释

- 如果 LLM 的 answerable query 数接近 observation，说明 extraction 的 evidence 覆盖率已经接近官方事实记忆。
- 如果 LLM 的 Recall@1/MRR 低于 observation，说明抽取文本措辞或 memory type 与查询表达仍有差距。
- 如果 LLM 的 Recall@3/5 较高但 Recall@1 较低，下一步优先考虑 reranking 或 memory-type-aware scoring。
