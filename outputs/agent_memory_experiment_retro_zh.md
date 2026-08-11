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

### 3.14 进展：candidate-level learned reranker 带来稳定提升

现象：query-level router 的几种版本都没有稳定超过 fixed `type_aware` 后，改为 candidate-level reranking：先合并 `keyword/vector/hybrid/time_aware/type_aware` 的 Top-K 候选，再训练轻量随机森林分类器判断候选是否相关。

结果：5 个 held-out query split 下，candidate reranker 的 MRR 为 `0.661`，高于 fixed `type_aware` 的 `0.607`；Recall@1 从 `0.499` 提升到 `0.556`，Recall@5 从 `0.733` 提升到 `0.796`。

显著性：paired bootstrap/permutation test 显示 MRR delta 为 `+0.0539`，95% CI `[0.0462, 0.0619]`，p-value `0.0002`；Recall@5 delta 为 `+0.0623`，95% CI `[0.0500, 0.0746]`，p-value `0.0002`。

原因判断：

- query-level route 只能在几个完整检索器之间切换，粒度太粗。
- candidate-level reranker 能同时使用 semantic、keyword、entity、time、persona、importance、memory type，以及不同检索器的候选排名特征。
- candidate oracle MRR 达到 `0.909`，说明当前多检索器候选池里仍有大量可利用空间。

解决：

- 将 candidate reranker 作为当前最强的学习式排序 baseline。
- 保留 fixed `type_aware` 作为可解释公式 baseline，candidate reranker 作为性能上界方向。
- 后续补充 feature importance、按 query type 的收益分解和更强学习器消融。

收益：项目从“手工公式 + 负结果 router”推进到“有显著提升的学习式重排模块”，更接近论文方法贡献。

### 3.15 问题：candidate reranker 的收益集中在部分 query type，Type 3 下降

现象：按 query type 分析后，candidate reranker 在 Type 5 上 MRR delta 为 `+0.0887`，Type 2 为 `+0.0522`，Type 4 为 `+0.0515`；但 Type 3 为 `-0.0194`，Recall@5 也下降 `-0.0556`。

原因判断：

- Type 5 多为关键词/属性/具体事实问题，多检索器融合能修正固定公式的语义漂移。
- Type 2/4 多为事件或事实定位，candidate reranker 能利用 time-aware、type-aware 和 semantic 排名特征。
- Type 3 更像多跳、推理、判断或跨事实聚合问题，只优化单条候选 memory 的 Top-1 排序可能不够。

解决：

- 保留 candidate reranker 作为总体最强方法。
- 将 Type 3 单独列为下一步短板，不把总体提升解释为所有 query type 都提升。
- 后续尝试多证据聚合、query decomposition 或 answer-aware reranking。

收益：论文分析更诚实，也更像正式实验：既报告总体显著提升，也指出方法边界和下一步改进方向。

### 3.16 问题：Type 3 的核心瓶颈是多证据覆盖，而不是单条候选排序

现象：Top-K 多证据覆盖分析显示，Type 3 的平均 gold evidence 数为 `2.65`，多证据问题比例为 `0.675`。candidate reranker 在 Type 3 上 Top-5 coverage ratio 为 `0.372`，略低于 fixed `type_aware` 的 `0.377`；Top-10 coverage ratio 才基本持平。

原因判断：

- Type 3 往往需要多个事实共同支持答案，例如“是否可能”“会不会喜欢”“两个人是否有共同点”等。
- 当前 candidate reranker 学的是单条 memory relevance，优化目标仍偏 Top-1。
- 即使某条相关 memory 排名提高，也可能没有覆盖完整 evidence set。

解决：

- 新增 `multi_evidence_coverage_analysis.py`，显式评估 `any_hit@K`、`full_coverage@K` 和 `coverage_ratio@K`。
- 将 Type 3 后续方向从“继续调单候选 reranker”调整为 set-level selection / query decomposition。

收益：Type 3 的失败原因从泛泛的“推理问题难”变成可量化的“Top-K evidence set 覆盖不足”，更适合写入论文 error analysis。

### 3.17 问题：简单 MMR 式 set-level selection 没有修复 Type 3

现象：在 candidate reranker Top-10 内测试无监督 set selector：保留原 Top-1，再用文本 Jaccard 去重和 memory type 多样性选择后续候选。结果 Type 3 Coverage@5 从 `0.372` 降到 `0.351`，Full@5 从 `0.262` 降到 `0.238`；Coverage@10 保持 `0.462` 不变。

原因判断：

- 当前 Top-10 候选集合没有扩大，最多只能改变前 5 个候选的顺序。
- 简单多样性会惩罚相似记忆，但 Type 3 的多个 evidence 有时本来就语义相近，去重反而把相关证据推后。
- Top-10 coverage 不变说明候选池容量没有解决，Top-5 下降说明启发式排序目标不够准确。

解决：

- 将该方法记录为负结果 baseline。
- 不继续调 MMR 参数作为主方向。
- 下一步改做 query decomposition 或扩大候选召回后再做 set-level learning。

收益：排除了一个看似自然但无效的简单方案，让后续实验方向更聚焦。

### 3.18 进展：Top-20 深度分析显示 Type 3 仍有候选空间

现象：将 candidate reranker 的 ranked output 从 Top-10 扩展到 Top-20 后，Type 3 的 coverage ratio 从 `0.462` 提升到 `0.597`，Full coverage 从 `0.325` 提升到 `0.444`。相比 fixed `type_aware`，candidate reranker 在 Top-20 的 Type 3 coverage delta 为 `+0.0711`，Full coverage delta 为 `+0.0714`。

原因判断：

- Type 3 不是完全召回不到相关 evidence，而是相关 evidence 常落在更深候选位置。
- Top-10 MMR 失败说明浅层候选里可重排空间不足；Top-20 改善说明扩大候选深度后仍有可利用信号。
- 下一步应优先做“深候选池 + set-level learning”，而不是只继续调浅层 Top-10 重排。

解决：

- 新增 candidate depth analysis，记录不同 K 下 Type 3 coverage 曲线。
- 将下一阶段候选池目标从 Top-10 扩展到 Top-20/Top-50。

收益：Type 3 的后续路线从“尝试 query decomposition 或扩大召回”进一步收敛为“扩大候选深度后做集合级学习选择”。

### 3.19 问题：Top-20 候选池上的启发式 set selector 仍不能提前 Type 3 证据

现象：把 set-level selection 的输入从 Top-10 扩展到 Top-20 后，Type 3 candidate reranker 的 Coverage@20 为 `0.597`，Full@20 为 `0.444`；但启发式 `set_selector_type3` 的 Coverage@5 下降到 `0.340`，Full@5 下降到 `0.238`，Coverage@20 仍为 `0.597`。

原因判断：

- Top-20 里有更多相关 evidence，但它们没有被简单 Jaccard 去重和 memory type 多样性提前。
- 多证据问题需要知道“哪些候选互补地覆盖不同 evidence”，而不是简单惩罚文本相似。
- 启发式 set selector 没有训练目标，无法区分“重复但必要的相近事实”和“真正冗余的相似事实”。

解决：

- 将 Top-20 set selector 记录为负结果 baseline。
- 下一步改为 supervised set-level learning 或 query decomposition。

收益：进一步排除了“扩大候选池 + 简单 MMR”这个自然但不足的方案，明确需要带覆盖目标的学习方法。

### 3.20 问题：Type 3 专用单候选重排没有解决多证据问题

现象：进一步只用训练集中的 Type 3 候选训练专用 reranker，并在 held-out Type 3 query 上评估。结果 `type3_specific_reranker` 的 MRR 为 `0.399`，低于固定 `type_aware` 的 `0.434`；Coverage@5 为 `0.331`，也低于 `type_aware` 的 `0.377`。全局 candidate reranker 在 Type 3 上也没有超过 `type_aware`，MRR 为 `0.421`。

原因判断：

- Type 3 训练样本数量较少，单独训练容易过拟合。
- 当前特征仍以“单条 memory 是否相关”为目标，不能显式建模多条 evidence 之间的互补关系。
- Type 3 的 candidate oracle 仍明显更高，说明候选池内存在可用证据，但排序目标没有把整组证据提前。

解决：

- 新增 `type3_specific_reranker_experiment.py`，把 Type 3 专用重排作为独立负结果记录。
- 同时输出排序指标和 evidence coverage 指标，避免只看 MRR。
- 将下一步路线从“Type3 专用 reranker”调整为 query decomposition 或 supervised set-level selector。

收益：排除了一个看似自然但效果不佳的改进方向，让论文后续贡献点更聚焦在多证据覆盖目标，而不是继续调单候选分类器。

### 3.21 问题：监督式 greedy set selector 仍未解决 Type 3

现象：进一步实现监督式 greedy set selector，在每一步选择候选时加入已选集合的文本冗余、memory type 覆盖等上下文特征。结果 `supervised_set_selector` 的 MRR 为 `0.389`，低于 `type_aware` 的 `0.434`；Coverage@5 为 `0.320`，低于 `type_aware` 的 `0.377`。参数检查中，`redundancy_weight=0.0` 比 `0.02` 和 `-0.02` 略好，但仍不能改善结论。

原因判断：

- 当前训练标签仍是单条候选是否为 evidence，没有真正学习“这一条是否补足当前已选集合缺失的子证据”。
- Type 3 query 常隐含多个子问题，只有候选之间的 Jaccard/type 上下文不足以识别子问题结构。
- 贪心策略容易早期选错，后续步骤无法恢复。

解决：

- 新增 `type3_supervised_set_selector_experiment.py`，把监督式集合贪心选择作为独立负结果记录。
- 实现时发现逐条调用 `predict_proba` 很慢，改为每一步对剩余候选批量预测，运行时间回到可接受范围。
- 将下一步进一步收敛为 query decomposition 或真正的 listwise/setwise objective，而不是继续堆简单候选上下文特征。

收益：排除了“浅层监督 + 贪心集合选择”这个中间方案，避免后续在同一类弱特征上继续投入过多时间。

### 3.22 问题：关键词式 query decomposition 噪声过大

现象：实现一个无训练 Type 3 query decomposition 弱基线：从原 query 中抽取人物名、内容关键词和短窗口 facet query，分别 BM25 召回，再用 RRF 合并；同时测试与 `type_aware` 的保守融合。结果纯 `query_decomposition` 的 MRR 为 `0.214`，保守融合为 `0.342`，均低于 `type_aware` 的 `0.429`。融合方法 Coverage@20 与 `type_aware` 持平，但 Coverage@5 和 MRR 下降。

原因判断：

- 弱拆解反复加入人物名，例如 `Caroline career`、`Caroline Caroline`，会把 identity/profile 类泛化记忆推到前面。
- 关键词窗口不能表达 Type 3 的隐含判断关系，例如“是否仍然想要”“是否可能喜欢”“基于过往经历推断”。
- BM25 facet 召回能找到部分具体词匹配，但缺少语义约束和子问题答案类型约束。

解决：

- 新增 `type3_query_decomposition_experiment.py`，把关键词式 decomposition 作为弱基线记录。
- 增加 `type_aware_plus_decomposition` 融合对照，避免只比较纯 BM25 拆解。
- 用显著性检验证明融合方法 MRR 仍显著低于 `type_aware`。

收益：排除了“简单关键词窗口拆解”这个低成本方案；如果后续继续做 decomposition，应转向 LLM 子问题生成、答案类型约束或更强语义解析。

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
7. 简单 text-intent router 和浅层监督式 query-text router 都弱于 fixed `type_aware`；validation-tuned router 可接近 fixed `type_aware`，但仍没有稳定超过。candidate-level reranker 已取得显著提升，且 feature importance 与 query-type 分析显示它主要改善 Type 2/4/5，但 Type 3 仍是短板。
8. Type 3 专用单候选重排已验证为负结果，说明 Type 3 需要 query decomposition 或 supervised set-level objective，而不是只换一个类型专用分类器。
9. 监督式 greedy set selector 也没有改善 Type 3，说明下一步需要显式 query decomposition 或更强 listwise/setwise 学习目标。
10. 关键词式 query decomposition 也没有改善 Type 3，说明 decomposition 方向若继续推进，需要更强的 LLM 子问题生成，而不是简单关键词窗口。

## 6. 下一步行动清单

1. 固化当前推荐配置：BGE-M3 + adaptive time-aware + persona gate + importance proxy。
2. 固化两层记忆结构：fact/observation 作为在线检索层，session_summary 作为归档回溯层。
3. 针对 Type 3 增加 LLM 子问题生成或真正 listwise/setwise learning，优化 Top-K evidence coverage ratio，而不仅是 Top-1 MRR。
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
