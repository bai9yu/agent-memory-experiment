# 智能体记忆开源代码调研与实验分析

本文档按 Experiment Analysis 模板整理：背景、假设、方法、实验设置、结果、解释、限制与下一步。

## 1. 背景

智能体记忆一般解决四类问题：

1. 长期个性化：记住用户偏好、长期目标、历史事实。
2. 长上下文压缩：把原始对话压成可检索事实或摘要，降低 token 成本。
3. 时效性：同一个事实可能多次更新，需要优先使用最新有效记忆。
4. 多智能体复用：不同 agent 之间共享经验、工具知识或任务结果，但必须控制权限边界。

用户项目申请书中提到的“感知-记忆 token 时效性、记忆检索与压缩、跨智能体知识复用/KV cache”与这些方向高度一致。

## 2. 调研假设

| 假设 | 含义 | 本项目验证方式 |
|---|---|---|
| H1：单纯向量检索不足 | 相似但过期的记忆容易被误召回 | 比较 `vector`、`hybrid`、`time_aware` |
| H2：事实级压缩优于粗粒度摘要 | 保持一条事实一个检索单元更适合记忆检索 | 比较 `raw`、`fact`、`summary` |
| H3：跨智能体复用先要权限过滤 | 未授权副本可能在排序中抢占 Top-1 | 比较 `private_only`、`shared_allowed`、`unfiltered_private_first` |
| H4：第一阶段不必先接大模型 API | 先用离线基线确认方向，再替换 embedding/LLM | 当前默认 hash backend + 可选 sentence-transformer |

## 3. 代表性开源项目对照

| 项目 | 背景/目标 | 记忆实现想法 | 使用的大模型/依赖 | 可参考点 |
|---|---|---|---|---|
| mem0 | 面向 AI agents 的通用记忆层，强调 personalized memory | `add/search/get/update`，LLM 抽取记忆，向量库检索，支持 user/agent/run 作用域 | README/文档显示默认 OpenAI LLM，示例包括 `gpt-5-mini`、`gpt-4.1-nano-2025-04-14`，默认 embedding 为 `text-embedding-3-small`；支持 OpenAI、Anthropic、Gemini、DeepSeek、Ollama、vLLM 等 | 适合参考 API 设计、记忆生命周期、provider 抽象、向量库适配 |
| MemoryOS | 个性化 AI agent 的 memory operating system | 借鉴操作系统分层内存：短期、中期、长期 persona/knowledge；包含 Storage、Updating、Retrieval、Generation | 支持 OpenAI、Anthropic、DeepSeek-R1、Qwen/Qwen3、vLLM；配置示例含 `gpt-4o-mini`、`BAAI/bge-m3` | 适合参考分层记忆、热度阈值、记忆晋升/更新机制 |
| MemOS | 面向 LLM 的模块化记忆系统 | 把 textual memory、activation memory/KV cache、parametric memory 统一为 MemCube | 文档称可集成 HuggingFace、Ollama、自定义 LLM；支持图后端如 Neo4j | 与我们“KV cache/activation memory 复用”方向最贴近 |
| Graphiti | 面向 AI agent 的实时 temporal knowledge graph | 将 episode 增量写入时间知识图谱，支持 semantic + keyword + graph reranking | 默认 OpenAI 作为 LLM 和 embedding；支持 Azure OpenAI、Gemini、Anthropic、Groq、Ollama、OpenAI-compatible endpoint；依赖 Neo4j/FalkorDB 等图数据库 | 适合参考时间知识图谱、实体关系、时间有效性和图距离重排 |
| LangGraph / LangMem | LangChain 生态中的长期记忆、memory tools 和 store | 长期记忆存为 JSON document，按 namespace/key 管理；agent 可用工具读写记忆 | memory-agent 示例默认 `anthropic/claude-3-5-sonnet-20240620`，可换 `openai/gpt-4`；LangMem 示例用 `anthropic:claude-3-5-sonnet-latest` 与 `openai:text-embedding-3-small` | 适合参考 namespace、user scope、工具化 memory write/search、评测模板 |
| AutoGen | 多智能体应用框架 | 更偏 agent orchestration，可组合多个 agent 和工具；memory 需要结合外部 store/扩展实现 | 当前 README 示例使用 OpenAI client，示例模型 `gpt-4.1`；AutoGen 项目处于维护模式，新用户建议 Microsoft Agent Framework | 可参考多智能体组织方式，但不建议作为记忆模块主依赖 |
| MemGPT / Letta | 早期“无限上下文/显式内存管理”代表 | working context + archival memory；通过函数/命令在上下文和外部记忆之间迁移信息 | MemGPT 旧版支持 `gpt-4`、`gpt-3.5-turbo` 和本地 LLM；Letta Code 支持 Claude、GPT、Gemini、GLM、Kimi 等 | 适合参考 archival memory、上下文窗口管理、长期 Agent 自我更新 |

## 3.1 它们是不是直接接入大模型

简短结论：多数系统会接入大模型，但不是“只接大模型”。更常见的结构是：

```text
LLM 负责理解/抽取/更新/回答
Embedding 负责语义向量化
Vector DB / Graph DB / SQL 负责存储和检索
规则或时间函数负责权限、时效性、冲突和成本控制
```

| 项目 | 是否直接接 LLM | LLM 主要负责 | Embedding / 存储负责 | 说明 |
|---|---:|---|---|---|
| mem0 | 是 | 从对话中抽取记忆、更新/冲突处理、辅助回答 | OpenAI embedding 或其他 embedding provider；Qdrant/Chroma/FAISS/Neo4j 等 | 典型的 LLM + vector store + optional graph store |
| MemoryOS | 是 | 记忆写入、更新、生成回答 | 分层存储和检索模块 | 强调短期/中期/长期分层记忆 |
| MemOS | 是 | 管理和使用 textual/activation/parametric memory | textual memory、activation memory/KV cache、parametric memory 统一管理 | 与 KV cache/activation memory 方向最相关 |
| Graphiti | 是 | 提取 episode 中的实体/关系/事件 | 图数据库 + embedding + reranking | 不是单纯向量库，而是 temporal knowledge graph |
| LangGraph / LangMem | 是 | Agent 根据工具读写记忆，或后台总结/更新 | namespace store / vector index / checkpointer | 区分 short-term 和 long-term memory |
| AutoGen | 是 | 多 Agent 对话、工具调用和协作 | 记忆通常要接外部 store 或扩展组件 | 更像多智能体框架，不是专门 memory layer |
| MemGPT / Letta | 是 | 决定何时把信息放入上下文或外部记忆 | archival memory / recall memory | 重点是上下文窗口与外部记忆管理 |

因此，不能简单理解成“直接把全部历史塞给大模型”。生产级或研究级 agent memory 通常会先检索、过滤、压缩，再把少量相关记忆交给 LLM。

## 3.2 它们用本地 embedding 还是 API embedding

结论：多数项目两种都支持，默认通常偏向 API embedding，便于开箱即用；本地 embedding 用于隐私、成本和离线部署。

| 项目 | 默认/常见 embedding | 是否支持本地 embedding | 我们能否直接复用 |
|---|---|---:|---|
| mem0 | 默认 OpenAI embedding；Python 支持 OpenAI、Azure OpenAI、Ollama、HuggingFace、Google AI、Vertex AI、Together、LM Studio、LangChain、AWS Bedrock | 支持 | 可复用配置思想和模型选择；不能直接复用其向量缓存 |
| Graphiti | 默认 OpenAI embedding；Gemini 可同时做 LLM、embedding、reranker；Ollama 示例使用 `nomic-embed-text` | 支持 | 可复用 OpenAI/Ollama embedder 接口；图数据库逻辑可后续参考 |
| MemOS | EmbedderFactory 支持 `ollama`、`sentence_transformer`、`universal_api` | 支持 | 非常适合参考“可切换 backend”设计 |
| LangGraph/LangMem | 常见使用 OpenAI embedding，也可接 LangChain 支持的 embedding | 支持 | 可参考 namespace + embedding search |
| MemoryOS | 配置示例可使用 BGE 等 embedding 模型 | 支持 | 可参考分层记忆，不建议直接迁移全部框架 |

这里的“复用”要区分两层：

1. 可以复用它们的 embedding 模型选择思路；当前项目具体采用 BGE、sentence-transformers。
2. 可以复用它们的接口设计：例如 `provider/model/base_url/api_key/embedding_dims`。
3. 通常不能直接复用它们已经算好的 embedding 向量，因为向量和原始文本、模型版本、维度、归一化方式、chunk 切分强绑定。

对我们项目最合适的路线是：

```text
保留当前统一 JSONL 数据格式
-> 新增 embedder backend
-> 支持 local-sentence-transformer / BGE-small / BGE-M3
-> 对 LoCoMo memory/query 生成本地缓存
-> 复用现有 Recall@K / MRR 评估
```

如果你现在使用 DeepSeek 官方 API，需要注意：DeepSeek 更适合 LLM 推理、事实抽取、压缩和回答生成；embedding 层当前先用本地 sentence-transformers/BGE。

## 4. 核心方法与公式

### 4.1 Generative Agents 记忆打分思想

经典 Generative Agents 使用三类信号：相关性、重要性、近因性。可抽象为：

\[
S(m_i, q)=
w_r R(m_i,q)+w_i I(m_i)+w_t T(m_i)
\]

其中：

- \(R(m_i,q)\)：记忆与当前查询的相关性。
- \(I(m_i)\)：记忆的重要性，可由 LLM 打分。
- \(T(m_i)\)：近因性或时间衰减。

我们当前的 `time_aware` 方法借鉴了这个思想，但先去掉 LLM importance，保留 semantic、BM25、entity、time decay 四项。

### 4.2 当前项目公式

语义相似度：

\[
\mathrm{semantic}(q,m_i)=
\frac{\mathbf{h}(q)\cdot \mathbf{h}(m_i)}
{\|\mathbf{h}(q)\|\|\mathbf{h}(m_i)\|}
\]

BM25：

\[
\mathrm{BM25}(q,d)=
\sum_{t \in q}
\mathrm{IDF}(t)
\frac{f(t,d)(k_1+1)}
{f(t,d)+k_1(1-b+b|d|/\mathrm{avgdl})}
\]

时间衰减：

\[
\mathrm{decay}(m_i,q)=0.5^{\Delta t/H}
\]

最终 time-aware 评分：

\[
S_{\mathrm{time}}=
(0.55\cdot \mathrm{semantic}
+0.30\cdot \mathrm{BM25}_{norm}
+0.10\cdot \mathrm{entity})
\cdot
(0.85+0.15\cdot \mathrm{decay})
\]

跨智能体权限过滤：

\[
\mathcal{C}(q,a)=
\{m_i\mid \mathrm{visible}(m_i,a)=1 \land \mathrm{scope}(m_i)\cap \mathrm{scope}(q)\neq \emptyset\}
\]

正确顺序：

\[
\operatorname{TopK}_{m_i\in \mathcal{C}(q,a)}S(q,m_i)
\]

而不是：

\[
\operatorname{filter}(\operatorname{TopK}_{m_i\in M}S(q,m_i))
\]

## 5. 本项目实验设置

| 实验线 | 数据规模 | 方法 | 指标 |
|---|---|---|---|
| 主检索 | 10 / 100 / 300 / 500 memories | `vector`、`hybrid`、`time_aware` | Recall@1/3/5、MRR |
| 压缩 | 100 / 300 / 500 memories | `raw`、`fact`、`summary` | token ratio、Recall@1/3/5、MRR |
| 跨智能体复用 | 100 / 300 / 500 queries | `private_only`、`shared_allowed`、`shared_plus_private_noise`、`unfiltered_private_first` | Recall@1/3/5、MRR |
| LoCoMo-like 转换 | 本地样例 | JSON/JSONL 转 memories + queries | 转换可用性、检索指标 |

当前所有实验默认离线可复现，不需要 API key。

## 5.1 LoCoMo 真实数据集介绍与下载

LoCoMo 是 ACL 2024 论文 "Evaluating Very Long-Term Conversational Memory of LLM Agents" 发布的数据集，目标是评估 LLM agents 的超长期对话记忆能力。它包含 10 个长时段、多 session 的对话样本，并提供 QA、事件摘要、session observation、session summary 等标注或生成字段。

官方仓库：https://github.com/snap-research/locomo

当前阶段最需要下载：

| 文件 | 官方链接 | 本地保存路径 | 用途 |
|---|---|---|---|
| `data/locomo10.json` | https://github.com/snap-research/locomo/blob/main/data/locomo10.json | `work/agent_memory_experiment/data/locomo10.json` | 真实长对话记忆检索实验 |

后续可选下载：

| 文件/目录 | 官方链接 | 何时需要 |
|---|---|---|
| 完整仓库 zip | https://github.com/snap-research/locomo/archive/refs/heads/main.zip | 想复现作者原始脚本、prompt、评测工具时 |
| `data/msc_personas_all.json` | https://github.com/snap-research/locomo/blob/main/data/msc_personas_all.json | 想研究角色 persona 构造或重生成对话时 |
| `data/multimodal_dialog/example/` | https://github.com/snap-research/locomo/tree/main/data/multimodal_dialog/example | 想扩展到图文多模态记忆时 |
| `scripts/` | https://github.com/snap-research/locomo/tree/main/scripts | 想运行作者原始处理/评测脚本时 |
| `requirements.txt` | https://github.com/snap-research/locomo/blob/main/requirements.txt | 想安装作者原始环境时 |

LoCoMo 主要字段和我们的映射关系：

| LoCoMo 字段 | 含义 | 我们当前的映射 |
|---|---|---|
| `sample_id` | 对话样本 id | `session_id` 前缀 / run id |
| `conversation` | 多 session 对话内容 | memory 原始来源 |
| `session_<num>_date_time` | session 时间 | memory `date` |
| `speaker_a`, `speaker_b` | 两个说话人 | `user_id` 或实体字段 |
| `dia_id` | 对话轮次 id | evidence 到 memory id 的映射依据 |
| `text` | 对话文本 | memory `text` |
| `img_url` / `blip_caption` | 图像和图像描述 | 暂时可把 caption 当文本记忆 |
| `observation` | session observation | 可作为观察型记忆 |
| `session_summary` | session 摘要 | 可作为 summary compression baseline |
| `event_summary` | 事件摘要 | 可用于摘要评估 |
| `qa` | 问答标注，含 evidence | query 和 answer_memory_ids |

接入策略：第一步只用 `conversation + qa + evidence` 做文本检索；第二步加入 `observation/session_summary` 对比压缩；第三步再考虑 `img_url/blip_caption` 的多模态记忆。

## 6. 本项目实验结果摘要

### 6.1 主检索

| 数据 | Vector Recall@1 | Time-aware Recall@1 | 解释 |
|---|---:|---:|---|
| 10 条 | 0.800 | 0.800 | 样例可手工检查，主要验证流程 |
| 100 条 | 0.400 | 0.575 | 时效性开始带来收益 |
| 300 条 | 0.175 | 0.338 | 相似记忆增多，纯向量更容易混淆 |
| 500 条 | 0.120 | 0.240 | time-aware 仍保持更好表现 |

500 条 temporal-update 子任务中，time-aware 把 Recall@1 从 `0.030` 提升到 `0.440`。

### 6.2 压缩

| 500 条设置 | Token ratio | Time-aware Recall@1 |
|---|---:|---:|
| raw | 1.000 | 0.240 |
| fact | 0.431 | 0.235 |
| summary | 0.431 | 0.110 |

结论：第一阶段应优先做 fact-level memory extraction，而不是过早把多条记忆合并成粗粒度 summary。

### 6.3 跨智能体

| 500 条设置 | Time-aware Recall@1 |
|---|---:|
| private_only | 0.000 |
| shared_allowed | 0.704 |
| shared_plus_private_noise | 0.704 |
| unfiltered_private_first | 0.000 |

结论：共享记忆能显著提高跨智能体复用能力，但权限过滤必须发生在排序前。

## 7. 我们可以参考哪些设计

| 可参考设计 | 来源 | 如何迁移到本项目 |
|---|---|---|
| `user_id / agent_id / run_id` 多作用域 | mem0 | 扩展当前 JSONL schema，支持 user/project/agent/run 四级过滤 |
| LLM 事实抽取 + memory update prompt | mem0、LangMem | 替换当前规则 `fact_text()`，加入新增/更新/删除判断 |
| 短期-中期-长期分层 | MemoryOS | 增加 hot memory、summary memory、archive memory 三层 |
| textual / activation / parametric memory | MemOS | 第二阶段加入 KV cache metadata 和复用成本 |
| temporal knowledge graph | Graphiti | 对实体、关系、有效时间做结构化存储 |
| namespace/key store | LangGraph | 把 `agent_id/user_id/session_id` 变成可检索 namespace |
| archival memory | MemGPT/Letta | 把长期经验和大段历史放入外部检索库 |

## 8. 限制

1. 当前主实验是合成数据，能验证趋势，但不能替代真实 LoCoMo/LongMemEval。
2. 默认 hash embedding 只用于离线可复现，语义能力弱于真实 embedding。
3. 当前压缩是规则压缩，不是 LLM-based memory extraction。
4. 当前跨智能体实验验证的是权限/排序机制，还没有真实多 Agent 任务执行轨迹。
5. 当前没有评估回答生成质量，只评估“是否检索到正确记忆”。

## 9. 下一步建议

1. 接入真实 LoCoMo 数据，先跑 10 条，再跑 100+ 条。
2. 接入 `sentence-transformers` + BGE-small/BGE-M3，并记录不同模型的 Recall@K / MRR。
3. 增加 LLM 事实抽取模块，输出 add/update/delete/noop。
4. 增加记忆冲突检测：同一实体同一属性保留最新有效事实。
5. 增加 KV cache 复用实验：记录 cache size、reuse hit、latency、privacy risk。
6. 与 mem0 或 Graphiti 做一组对照实验：同样数据、同样指标、不同记忆后端。

## 10. 主要资料来源

- mem0 GitHub / LLM 文档：https://github.com/mem0ai/mem0 和 https://github.com/mem0ai/mem0/blob/main/LLM.md
- MemoryOS GitHub：https://github.com/BAI-LAB/MemoryOS
- MemOS 文档：https://memos-docs.openmem.net/open_source/home/overview/
- Graphiti GitHub / 文档：https://github.com/getzep/graphiti 和 https://help.getzep.com/graphiti/configuration/llm-configuration
- LangGraph long-term memory 文档：https://docs.langchain.com/oss/python/langchain/long-term-memory
- LangGraph memory-agent：https://github.com/langchain-ai/memory-agent
- AutoGen GitHub：https://github.com/microsoft/autogen
- MemGPT GitHub：https://github.com/deductive-ai/MemGPT
- Letta Code GitHub：https://github.com/letta-ai/letta-code
