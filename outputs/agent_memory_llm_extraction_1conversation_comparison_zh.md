# LLM Memory Extraction 对比报告

本报告比较 DeepSeek 抽取的 fact-level memory 与 LoCoMo 官方 observation memory，在同一 conversation/session slice 下的覆盖率、token 成本和 BGE-M3 检索效果。

## 主结果

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| llm_extracted_fact | 187 | 2443 | 175 | 0.474 | 0.669 | 0.726 | 0.590 |
| locomo_observation | 184 | 3002 | 155 | 0.497 | 0.600 | 0.690 | 0.578 |

## API 用量

| Variant | Prompt Tokens | Completion Tokens | Total Tokens |
|---|---:|---:|---:|
| llm_extracted_fact | 26930 | 15084 | 42014 |
| locomo_observation | 0 | 0 | 0 |

## Top-1 错误样例

### LLM Extracted Fact

- `q00003` What fields would Caroline be likely to pursue in her educaton? -> `llm_00034`: Caroline is motivated to pursue counseling because her own journey and support from counseling and support groups improved her life.
- `q00004` What did Caroline research? -> `llm_00049`: Caroline is a transgender woman.
- `q00005` What is Caroline's identity? -> `llm_00122`: Caroline finds painting therapeutic and it helps her explore her identity.
- `q00007` When is Melanie planning on going camping? -> `llm_00093`: Melanie's family has a tradition of going on a camping trip every summer.
- `q00008` What is Caroline's relationship status? -> `llm_00049`: Caroline is a transgender woman.
- `q00014` What career path has Caroline decided to persue? -> `llm_00037`: Caroline is considering counseling and mental health as a career path to help others.
- `q00015` Would Caroline still want to pursue counseling as a career if she hadn't received support growing up? -> `llm_00037`: Caroline is considering counseling and mental health as a career path to help others.
- `q00016` What activities does Melanie partake in? -> `llm_00077`: Melanie and her family went on a camping trip in the forest.

### LoCoMo Observation

- `q00003` What fields would Caroline be likely to pursue in her educaton? -> `obs_00059`: Melanie: Melanie reminds Caroline to pursue her dreams and appreciates the power of books in guiding and motivating her.
- `q00004` What did Caroline research? -> `obs_00157`: Caroline: Caroline recommends doing research, preparing emotionally, and gathering necessary documents when starting the adoption process.
- `q00008` What is Caroline's relationship status? -> `obs_00155`: Caroline: Caroline is looking into adoption and contacted her mentor for advice.
- `q00012` Where did Caroline move from 4 years ago? -> `obs_00015`: Caroline: Caroline started transitioning three years ago.
- `q00014` What career path has Caroline decided to persue? -> `obs_00037`: Caroline: Caroline is considering a career in counseling and mental health to help others.
- `q00016` What activities does Melanie partake in? -> `obs_00010`: Melanie: Melanie carves out me-time each day for activities like running, reading, or playing the violin.
- `q00019` Where has Melanie camped? -> `obs_00087`: Melanie: Melanie's family tradition includes a camping trip where they roast marshmallows and tell stories around the campfire.
- `q00020` What do Melanie's kids like? -> `obs_00144`: Melanie: Melanie enjoys classical music like Bach and Mozart, as well as modern music like Ed Sheeran's "Perfect".

## 解释

- 如果 LLM 的 answerable query 数接近 observation，说明 extraction 的 evidence 覆盖率已经接近官方事实记忆。
- 如果 LLM 的 Recall@1/MRR 低于 observation，说明抽取文本措辞或 memory type 与查询表达仍有差距。
- 如果 LLM 的 Recall@3/5 较高但 Recall@1 较低，下一步优先考虑 reranking 或 memory-type-aware scoring。
