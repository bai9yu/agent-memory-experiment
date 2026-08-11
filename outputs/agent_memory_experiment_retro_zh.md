# 智能体记忆实验复盘：问题、解决思路与后续改进

## 1. 复盘目的

本文档记录第一阶段实验过程中遇到的问题、原因判断、解决方式和后续注意点。后续继续改代码或写项目阶段总结时，可以把这里当作“实验日志”和“踩坑记录”。

## 2. 已完成内容

| 模块 | 已完成内容 |
|---|---|
| 数据 | 10 条手工样例；100/300/500 条合成数据；LoCoMo-like 转换样例 |
| 检索 | `vector`、`hybrid`、`time_aware` 三种 baseline |
| 评估 | Recall@1/3/5、MRR、per-query、by-type、rankings |
| 压缩 | `raw`、`fact`、`summary` 三种记忆形态 |
| 跨智能体 | private/shared/mixed/unfiltered 四种策略 |
| 自动化 | `run_full_pipeline.py` 一键跑完整实验和总报告 |
| 输出 | 中文阶段摘要、总报告、数据集计划、调研文档 |
| 真实数据 | LoCoMo `locomo10.json` 已接入，转换为 5882 条 memory 和 1986 个 query |
| 真实 embedding | 本地 BGE-M3 已接入，embedding 落盘缓存已验证 |
| 记忆特征 | persona gate 与 importance proxy 已加入 time-aware ranking |

## 3. 问题与解决

### 3.1 问题：第一阶段是否需要马上接入大模型 API

现象：最开始目标是验证智能体记忆思路，但如果一上来接 API，会同时引入模型费用、联网、prompt 不稳定、API 兼容问题。

判断：第一阶段核心不是让 Agent 回答得多自然，而是验证记忆检索和组织方法是否有效。

解决：先构建完全离线的 hash embedding baseline，并保留 `sentence-transformer` 可选入口。

收益：

- 不需要 API key。
- 结果可复现。
- 方便从 10 条快速扩展到 500 条。
- 后续替换为真实 embedding/LLM 时，指标和数据格式不用变。

后续改进：接入本地 BGE-small 和 BGE-M3，作为真实语义检索对照。

### 3.1.1 问题：BGE-M3 全量评测明显慢于 hash baseline

现象：`BAAI/bge-m3` 已能本地下载、离线加载并跑通 LoCoMo，但全量 5882 条 memory + 1986 个 query 的首次编码耗时明显。

原因：BGE-M3 模型较大，本地 CPU/Apple Silicon 上首次编码全量文本会慢；同时第一版评测器对真实 embedding 的相似度计算使用 Python 循环，放大全量数据后效率不足。

解决：

- 将真实 embedding 的相似度计算改为向量化求和。
- 增加 `--embedding-batch-size`，允许在速度和内存之间调节。
- 增加 `--local-files-only`，确保下载完成后可离线复现。

后续改进：增加本地 embedding 落盘缓存，避免每次全量实验重新编码 memory/query。

### 3.1.2 问题：初始 time-aware 在 LoCoMo 上低于 hybrid

现象：BGE-M3 接入后，初始 time-aware 的 Recall@1 为 `0.242`，低于 hybrid 的 `0.283`。

原因：旧公式把所有问题都乘上 recency decay，但 LoCoMo 中很多时间问题是 `When did ...`，它们询问历史事件发生时间，并不等价于“越新的记忆越相关”。

解决：

- 参考 Generative Agents 的 relevance + recency 思路，但增加 query gate。
- 只有 query 包含 recent/latest/last/today/currently/now/since/new 等最近性意图，并且不是 when/date/time 问句时，才触发 recency boost。
- 固化参数：`0.70 semantic + 0.30 BM25 + 0.08 * gate(q) * decay`。

最终结果：LoCoMo 全量+BGE-M3 下，adaptive time-aware Recall@1 为 `0.310`，高于 hybrid 的 `0.283`；MRR 为 `0.418`，高于 hybrid 的 `0.392`。

### 3.1.3 问题：BGE-M3 重复编码拖慢调参

现象：每次改权重后重新跑全量 LoCoMo，都会等待 BGE-M3 编码 5882 条 memory 和 1986 个 query。

解决：增加 sentence-transformer embedding 落盘缓存，缓存 key 包含模型名、id 和文本内容。

结果：LoCoMo 小样本第二次运行从约 `18s` 降到约 `4s`；全量运行后缓存目录约 `31MB`。

### 3.1.4 问题：人物主体相似导致误召回

现象：LoCoMo 中 Caroline 和 Melanie 的对话主题相互交织，仅靠语义相似度和 BM25 容易把“主体相似但人物不对”的 memory 排在前面。

解决：增加 persona/entity soft boost：

- query 提到的人名匹配 memory speaker：`+1.0`
- query 提到的人名出现在 memory text：`+0.7`
- query 提到人名但 memory 不匹配：`-0.5`
- query 未提到人名：`0`

同时把 boost 限制在 query type `1,2,3,4`，避免 type `5` 被过度干扰。

最终结果：LoCoMo 全量+BGE-M3 下，time-aware + persona gate Recall@1 为 `0.321`，MRR 为 `0.429`，继续高于 adaptive time-aware 的 `0.310 / 0.418`。

### 3.1.5 问题：哪些记忆应该更值得保留和召回

现象：只看语义、关键词、时间和人物后，部分长期偏好、身份、关系、目标和强情绪记忆仍可能排在普通闲聊之后。

判断：Generative Agents 使用 LLM 给 memory 打 importance，但第一阶段直接接 LLM 会增加费用和不稳定因素。因此先做一个可复现 importance proxy。

解决：在 `memory_eval.py` 中增加规则重要性分数：

- 身份、职业、关系、家庭、长期目标、偏好、重要日期等信号加权。
- proud、grateful、excited、scared、meaningful 等情绪信号加权。
- 较长且实体密度更高的记忆小幅加权。
- hello、thanks、goodbye 等短闲聊小幅降权。

最终结果：LoCoMo 全量+BGE-M3 下，`persona_boost_weight=0.04`、`importance_weight=0.06` 的最终方法 Recall@1 为 `0.329`，Recall@5 为 `0.562`，MRR 为 `0.439`。相比只加 persona gate 的 `0.321 / 0.543 / 0.429` 继续提升。

### 3.1.6 问题：每次调权重都全量跑太慢

现象：BGE-M3 全量评测即使有 embedding 缓存，也还要做 BM25、候选排序和结果写入。

解决：新增 `tune_memory_features_from_rankings.py`，把 `rankings.csv` 当作候选级特征缓存，直接在已保存的 semantic、keyword、time decay、persona、importance 特征上重排。

注意：候选级缓存只能在已落盘 Top-K 候选内调参，不能替代最终全量验证。因此本次先用缓存搜索出 `importance_weight=0.06`，再用 `memory_eval.py` 做全量复验。

### 3.1.7 问题：真实压缩应该用合成摘要，还是 LoCoMo 官方记忆字段

现象：早期压缩实验用规则生成 `fact` 和 grouped `summary`，能验证 token 成本趋势，但不代表真实长对话数据中的高质量 memory write。

解决：新增 `build_locomo_compression_variants.py`，直接使用 LoCoMo 官方 `observation` 和 `session_summary` 字段构建压缩记忆，并把原始 evidence `D1:3` 映射到压缩后的 memory id。

结果：

- `observation`：2541 条 memory，token ratio `0.281`，evidence coverage `0.785`，Recall@1 `0.400`，MRR `0.484`。
- `session_summary`：272 条 memory，token ratio `0.201`，evidence coverage `0.997`，Recall@1 `0.520`，MRR `0.636`。
- `raw_turn`：5882 条 memory，token ratio `1.000`，Recall@1 `0.329`，MRR `0.439`。

判断：官方 observation 的表现说明“事实级 memory write”是有效方向；session summary 适合作为二级归档，但因为 gold target 变粗，不能直接把高指标理解为事实级检索已经解决。

### 3.2 问题：合成数据中 `multi-agent` 分支没有真正出现

现象：检查 100 条合成 query 时，没有找到 `type = multi-agent` 的记录。

原因：生成器中 temporal-update 一次生成两条 memory，导致 memory_id 跳号，原先预期的分支节奏被打乱。

解决：没有强行改主合成数据口径，而是新增 `cross_agent_experiment.py`，专门从现有 memories 构造跨智能体评测数据。

收益：

- 主检索实验结果保持稳定，不被改动。
- 跨智能体实验可以更明确控制 private/shared/unfiltered 条件。

后续改进：如果真实多 Agent 数据到位，可把跨智能体样本从“构造型”替换为真实 trajectory。

### 3.3 问题：跨智能体风险对照一开始没有拉开差距

现象：`unfiltered_private_first` 最初没有让 time-aware Recall@1 下降。

原因：共享副本和私有副本在实体字段上不完全一致，共享副本因为实体项更多，排序时仍然占优。

解决：把私有副本和共享副本的文本、实体设为完全一致，只保留 `visibility` 元数据不同，并让未过滤条件中私有副本排在前面。

收益：风险对照更干净，下降可以归因于“没有先做权限过滤”，而不是文本相似度或实体字段差异。

最终结果：500 条下 `shared_allowed` time-aware Recall@1 为 `0.704`，`unfiltered_private_first` 为 `0.000`。

### 3.4 问题：压缩会降低 token 成本，但可能损失检索粒度

现象：`fact` 和 `summary` 的 token ratio 都约为 43%，但检索效果不同。

原因：

- `fact` 保持一条原始记忆对应一条压缩事实，检索粒度仍然细。
- `summary` 把多条记忆合并为一个 block，多个 query 的答案会映射到同一块，容易降低精确排序。

解决：保留两种压缩策略做对照，而不是只报告 token 节省。

结论：第一阶段推荐 fact-level memory extraction，summary 更适合作为二级归档层。

### 3.5 问题：真实数据集格式不统一

现象：LoCoMo、LongMemEval、不同 GitHub 仓库的数据结构不完全一致，字段名可能是 `messages`、`turns`、`dialogue`、`qa`、`questions` 等。

解决：写了宽松的 `convert_long_conversation.py`，支持多种容器字段和文本字段，并统一输出：

- `*_memories.jsonl`
- `*_queries.jsonl`

后续注意：真实数据接入时要重点核对 evidence id 是否能准确映射到 memory id。

### 3.6 问题：总实验命令分散

现象：主检索、压缩、跨智能体实验分别有脚本，容易忘记某一步，输出报告也容易不同步。

解决：新增 `run_full_pipeline.py`，统一执行：

1. 生成/评估 10、100、300、500 数据。
2. 汇总主检索报告和趋势 CSV。
3. 运行压缩实验并汇总。
4. 运行跨智能体实验并汇总。
5. 生成 `agent_memory_full_pipeline_report.md`。

收益：后续修改代码后，只需要运行一个命令即可刷新主要结果。

### 3.7 问题：LoCoMo 官方 raw 下载在命令行里超时

现象：通过 `raw.githubusercontent.com` 下载 `locomo10.json` 时长时间无响应。

原因：本地命令行网络环境对 GitHub raw 域名不稳定；浏览器可以打开文件，但命令行下载不可靠。

解决：让用户从 GitHub 页面手动下载 `data/locomo10.json`，保存到项目数据目录。

收益：绕开命令行网络问题，保证真实数据文件完整到位。

后续注意：如果还需要下载 LongMemEval 或 LoCoMo 完整仓库，优先给出手动下载链接和本地保存路径。

### 3.8 问题：LoCoMo 全量评测会产生过大的 ranking 明细

现象：全量 LoCoMo 有 5882 条 memory 和 1986 个 query，如果每个 query/方法都保存所有候选排序，会产生约 3500 万行 ranking，速度慢且文件过大。

原因：评估指标需要完整排序来找到相关 evidence 的 rank，但用户分析通常只需要 Top-K 明细。

解决：

- `memory_eval.py` 改为流式计算 per-query metrics，不再把所有完整排序长期保存在内存里。
- `rankings.csv` 默认每个 query/方法只保存 Top 100。
- 指标仍然基于完整排序计算，不受 Top 100 落盘限制影响。

收益：LoCoMo 全量真实数据可以在本地完成评测，输出文件规模也可控。

### 3.9 问题：FAISS 与本地 embedding 环境存在原生库线程冲突

现象：安装 `faiss-cpu` 后，最小 FAISS import、Flat 和 IVF toy example 都正常，但在同一进程中加载 sentence-transformers/BGE-M3 后直接运行 FAISS-IVF，曾出现退出码 139 的段错误。

原因判断：不是 Python 代码逻辑错误，而是 macOS/arm64 环境下 FAISS、BLAS/OpenMP、sentence-transformers 相关原生库的线程运行时冲突。

解决：

- 复现实验命令中固定单线程环境变量：`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`。
- 保留 FAISS Flat 作为 exact index upper-bound，FAISS IVF 作为 ANN 速度-召回折中。
- 在报告中显式记录该环境要求，避免后续复现时误判为算法失败。

收益：FAISS Flat、IVF nprobe=8、IVF nprobe=32 均可稳定完成 LoCoMo10 实验，并形成向量索引效率对照表。

### 3.10 问题：LoCoMo10 memory bank 太小，不足以体现 ANN 优势

现象：LoCoMo10 answerable slice 只有 2517 条 memory，FAISS Flat 已经非常快；IVF 虽然是 ANN，但在该规模下没有稳定快过 Flat。

解决：

- 新增 `faiss_scale_experiment.py`，在真实 BGE-M3 memory/query embedding 基础上加入轻微扰动的 synthetic distractor vectors，扩展到 10k、25k、50k、100k。
- 该实验只评估候选召回层，不执行完整 type-aware reranking，因此在报告中明确标注为 index-only stress test。
- 100k 结果显示 IVF nprobe=4 可以比 Flat 快，但 candidate gold recall 明显下降；nprobe=64 召回接近 Flat，但查询时间慢于 Flat。

收益：形成了 ANN 速度-召回折中曲线，也明确了下一步应在真实更大 memory bank 或 HNSW/IVF-PQ 上继续验证。

### 3.11 问题：简单文本规则无法可靠替代 query type router

现象：oracle-light query-type router 使用 LoCoMo 标注 type 时，MRR 从 fixed `type_aware` 的 0.609 提升到 0.611，但提升不显著。进一步改成只看 query 文本的规则 router 后，MRR 降到 0.595，且显著低于 fixed `type_aware`。

原因判断：query 文本中的关键词不足以稳定判断最佳检索方法。例如 “what kind/type/project/issue” 类问题有时需要 keyword，有时仍需要 type-aware 或语义匹配；简单规则会把大量 query 路由到不合适的方法。

解决：

- 保留 query-type router 作为 oracle-light 上界启发，不作为主结论。
- 新增 text-intent router 作为可部署弱基线，并报告其显著退化结果。
- 下一步应使用 validation-tuned classifier、LLM few-shot classifier，或更细粒度的 intent rules，并在验证集上调参。

收益：避免把未验证的 router 写成贡献点，同时明确了后续方法改进方向。

### 3.12 问题：监督式 query-text router 仍低于固定 type-aware

现象：新增 held-out 监督式路由实验后，TF-IDF + LogisticRegression 根据 query 文本预测最佳检索方法，5 个划分下 MRR 为 `0.592`，低于 fixed `type_aware` 的 `0.607`；Recall@5 也从 `0.733` 降到 `0.708`。

原因判断：

- 训练标签来自 per-query oracle best method，本身噪声较大；很多 query 在多个检索器之间差距很小。
- query 文本较短，仅靠 n-gram 特征难以区分“需要关键词精确匹配”还是“需要人物/时间/type-aware 约束”。
- 类别分布不均衡，`type_aware` 是最大类，但仍有大量 query 被预测到 `keyword` 或 `vector`。

解决：

- 将监督式路由保留为可部署负结果 baseline，不作为当前主方法。
- 报告 oracle best 上界：MRR `0.693`，说明 query-level route 仍有潜在空间。
- 后续改为 validation-tuned router、LLM few-shot intent classifier，或 candidate-level reranking learner，而不是继续堆简单规则。

收益：当前方法边界更清楚，论文中可以把 router 写成“分析驱动的后续方向”，避免夸大未稳定提升的模块。

### 3.13 问题：验证集调参能修复手写路由退化，但仍没有带来增益

现象：新增 validation-tuned text-intent router 后，保留原来的 query 文本 intent 分组，但在训练集上自动选择每个 intent 的最佳方法。5 个 held-out split 下 MRR 为 `0.606`，几乎等于 fixed `type_aware` 的 `0.607`，但仍未超过。

原因判断：

- 手写 route 的主要问题是把 `keyword_heavy` 和 `identity_profile_vector` 过早固定到 `keyword/vector`，而训练集经常会把这些 intent 重新选回 `type_aware`。
- 调参后不再明显退化，说明验证集选择是必要的。
- 但 intent 分组本身太粗，无法捕捉 Type 3、Type 5 内部的细粒度差异，因此距离 oracle best MRR `0.693` 仍有明显差距。

解决：

- 保留 validation-tuned router 作为更公平的可部署 baseline。
- 暂不把 router 写成主贡献，只把它作为“query-level 方法选择仍有上界，但当前 intent schema 不够”的证据。
- 后续优先尝试 LLM few-shot intent classifier 或 candidate-level reranking learner。

收益：形成了更完整的负结果链条：oracle-light 有潜力，手写规则会退化，浅层监督分类也会退化，验证集调参可以回到固定方法水平但不产生显著收益。

## 4. 当前实验结论

### 4.1 时效性

记忆规模越大，相似旧事实越容易干扰检索。time-aware 在 500 条下 Recall@1 为 `0.240`，高于 vector 的 `0.120`。

### 4.2 压缩

合成数据中，fact-level 压缩把 token 成本降到约 `43%`，500 条下 time-aware Recall@1 从 `0.240` 小幅降到 `0.235`；summary 压缩降到 `0.110`。真实 LoCoMo 中，官方 observation 把 token 成本降到 `28%`，Recall@1 提升到 `0.400`；session_summary 把 token 成本降到 `20%`，Recall@1 为 `0.520`，但属于 session 级粗粒度检索。

### 4.3 跨智能体

Agent B 只看私有记忆时 Recall@1 为 `0`；允许读取 Agent A 授权共享记忆后，500 条下 Recall@1 为 `0.704`；如果不先过滤权限，Recall@1 回到 `0`。

### 4.4 真实 LoCoMo

LoCoMo `locomo10.json` 已转换为 5882 条 memory 和 1986 个 query。hash baseline 下，`hybrid` Recall@1 为 `0.186`、MRR 为 `0.263`；本地 BGE-M3 加入 adaptive time-aware、persona gate 和 importance proxy 后，最终 Recall@1 达到 `0.329`、Recall@5 达到 `0.562`、MRR 达到 `0.439`。这说明真实数据管线、真实 embedding 和记忆特征重排已经进入可用验证阶段。

## 5. 后续风险

1. importance proxy 还是规则分数，不等价于真实 LLM reflection 或人工标注。
2. 候选级特征缓存只适合快速调参，最终结论仍要跑完整 `memory_eval.py`。
3. 当前没有 LLM-based memory write/update，无法处理复杂冲突。
4. 当前只评估检索，不评估最终回答生成质量。
5. KV cache 复用还没有真实实现，只在方法文档中给出下一步公式。
6. FAISS IVF 在 LoCoMo10 当前规模下没有明显速度优势，100k synthetic distractor 实验也只能说明趋势，ANN 优势仍需要真实更大 memory bank 才能充分证明。
7. 简单 text-intent router 和浅层监督式 query-text router 都弱于 fixed `type_aware`；validation-tuned router 可接近 fixed `type_aware`，但仍没有稳定超过，说明路由方法需要更细 intent schema 或学习式 reranker。

## 6. 下一步行动清单

1. 固化当前推荐配置：BGE-M3 + adaptive time-aware + persona gate + importance proxy。
2. 固化两层记忆结构：fact/observation 作为在线检索层，session_summary 作为归档回溯层。
3. 增加强 router：在 validation-tuned router 基础上，尝试 LLM few-shot classifier 或 candidate-level reranking learner，并与 fixed `type_aware` 做 paired significance。
4. 增加 LLM memory extraction 重复实验：从原始对话抽取事实、时间、实体、重要性、权限，并报告 seed/temperature 方差。
5. 增加 conflict resolver：同一主体同一属性按时间和置信度更新。
6. 增加真实多 Agent trace：把 Agent A 的工具经验、错误修复、代码片段作为共享记忆。
7. 增加 KV cache metadata：记录 cache key、来源 agent、scope、token cost、latency gain。

## 7. 建议复盘口径

向老师或组内汇报时，可以按下面顺序讲：

1. 第一阶段目标不是做完整 Agent，而是验证记忆模块三件事：检索是否有效、压缩是否保质、跨智能体共享是否有风险。
2. 当前先用离线基线保证可复现，再逐步替换成真实 embedding 和 LLM。
3. 实验已经从 10 条扩展到 500 条，结果显示 time-aware、fact compression、permission-first retrieval 三个方向都值得继续。
4. 下一阶段接 LoCoMo/LongMemEval，并加入真实模型 API 和真实 Agent 轨迹。
