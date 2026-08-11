# LLM Memory Extraction 对比报告

本报告比较 DeepSeek 抽取的 fact-level memory 与 LoCoMo 官方 observation memory，在同一 conversation/session slice 下的覆盖率、token 成本和 BGE-M3 检索效果。

## 主结果

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| llm_extracted_fact | 2517 | 31148 | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| locomo_observation | 2507 | 40241 | 1638 | 0.483 | 0.639 | 0.703 | 0.583 |

## API 用量

| Variant | Prompt Tokens | Completion Tokens | Total Tokens |
|---|---:|---:|---:|
| llm_extracted_fact | 361103 | 198471 | 559574 |
| locomo_observation | 0 | 0 | 0 |

## Top-1 错误样例

### LLM Extracted Fact

- `q00004` What did Caroline research? -> `llm_00164`: Caroline gave Melanie tips on starting adoption: research, find an agency or lawyer, gather documents, and prepare emotionally.
- `q00008` What is Caroline's relationship status? -> `llm_00002`: Caroline is transgender.
- `q00014` What career path has Caroline decided to persue? -> `llm_00040`: Caroline is considering counseling and mental health as a career path to help others.
- `q00016` What activities does Melanie partake in? -> `llm_00079`: Melanie and her family enjoy hiking in the mountains and exploring forests.
- `q00019` Where has Melanie camped? -> `llm_00151`: Melanie has kids.
- `q00020` What do Melanie's kids like? -> `llm_00151`: Melanie has kids.
- `q00023` Would Caroline likely have Dr. Seuss books on her bookshelf? -> `llm_00060`: Caroline loves reading and considers books a huge part of her journey.
- `q00024` What books has Melanie read? -> `llm_00151`: Melanie has kids.

### LoCoMo Observation

- `q00004` What did Caroline research? -> `obs_00157`: Caroline: Caroline recommends doing research, preparing emotionally, and gathering necessary documents when starting the adoption process.
- `q00008` What is Caroline's relationship status? -> `obs_00176`: Caroline: Caroline finds empowerment in making a positive difference in someone's life by offering love and support.
- `q00012` Where did Caroline move from 4 years ago? -> `obs_00015`: Caroline: Caroline started transitioning three years ago.
- `q00014` What career path has Caroline decided to persue? -> `obs_00037`: Caroline: Caroline is considering a career in counseling and mental health to help others.
- `q00016` What activities does Melanie partake in? -> `obs_00010`: Melanie: Melanie carves out me-time each day for activities like running, reading, or playing the violin.
- `q00019` Where has Melanie camped? -> `obs_00087`: Melanie: Melanie's family tradition includes a camping trip where they roast marshmallows and tell stories around the campfire.
- `q00020` What do Melanie's kids like? -> `obs_00070`: Melanie: Melanie and her kids enjoy nature-inspired painting projects.
- `q00022` When did Caroline have a picnic? -> `obs_00115`: Caroline: Caroline used to go horseback riding with her dad when she was a kid.

## 解释

- 如果 LLM 的 answerable query 数接近 observation，说明 extraction 的 evidence 覆盖率已经接近官方事实记忆。
- 如果 LLM 的 Recall@1/MRR 低于 observation，说明抽取文本措辞或 memory type 与查询表达仍有差距。
- 如果 LLM 的 Recall@3/5 较高但 Recall@1 较低，下一步优先考虑 reranking 或 memory-type-aware scoring。
