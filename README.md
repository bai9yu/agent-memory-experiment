# Agent Memory Experiment

本仓库实现了一套面向长对话与多智能体场景的 agent memory 实验框架，覆盖记忆构建、检索、重排、压缩和跨智能体复用。

## 功能概览

- LoCoMo 真实长对话数据接入
- 本地 BGE-M3 embedding 检索与 embedding cache
- BM25 + semantic hybrid retrieval
- adaptive time-aware reranking
- persona gate，用于减少人物主体混淆
- importance proxy，用于提升身份、关系、长期目标、偏好等高价值记忆
- candidate-level learned reranking，用于从多检索器候选并集中学习排序
- Type 3 多证据覆盖、候选深度和专用重排诊断
- LoCoMo `observation` / `session_summary` 真实压缩对照
- DeepSeek LLM fact-level memory extraction，并与 LoCoMo 官方 observation memory 对比
- 跨智能体共享记忆的权限过滤与风险对照实验
- 中文实验报告、参数搜索记录和复盘文档

主要代码在 `work/agent_memory_experiment/`。

中文文档和实验报告在 `outputs/`，其中 DeepSeek 记忆抽取报告见：

- `outputs/agent_memory_llm_extraction_deepseek_zh.md`
- `outputs/agent_memory_llm_extraction_1conversation_comparison_zh.md`
- `outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md`
- `outputs/agent_memory_error_analysis_locomo10_type_aware_zh.md`

## 当前推荐配置

当前 LoCoMo 全量实验推荐：

```text
BGE-M3 + adaptive time-aware reranking + persona gate + importance proxy
```

关键结果：

| Memory Form | Token Ratio | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| raw turn memory | 1.000 | 0.329 | 0.562 | 0.439 |
| LoCoMo observation memory | 0.281 | 0.400 | 0.585 | 0.484 |
| LoCoMo session summary memory | 0.201 | 0.520 | 0.773 | 0.636 |

结论：事实级 observation memory 能显著降低 token 成本并减少闲聊噪声；session summary 更适合作为二级归档层。

DeepSeek 抽取的 fact-level memory 已完成第 1 个完整 conversation 的真实 API 接入实验：

| Memory Form | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact | 187 | 2443 | 175 | 0.474 | 0.726 | 0.590 |
| LoCoMo observation | 184 | 3002 | 155 | 0.497 | 0.690 | 0.578 |

结论：DeepSeek 可以作为 memory write 模块接入；当前候选召回有效，但 Top-1 排序还需要继续优化。

当前已加入 `type_aware` 重排消融；在 LoCoMo10 全量上，`w_type=0.04` 将 MRR 从 `0.605` 提升到 `0.609`，Recall@5 从 `0.727` 提升到 `0.733`。详细结果见 `outputs/agent_memory_type_aware_reranking_zh.md`。

完整 baseline 对比见 `outputs/agent_memory_baseline_comparison_locomo10_zh.md`。

LoCoMo10 按 query type 的细粒度分析见 `outputs/agent_memory_query_type_locomo10_zh.md`。

Query-type router 离线验证见 `outputs/agent_memory_query_type_router_locomo10_zh.md`。

Text-intent router 可部署规则基线见 `outputs/agent_memory_text_intent_router_locomo10_zh.md`。

监督式 query-text router held-out 实验见 `outputs/agent_memory_supervised_router_locomo10_zh.md`。

验证集调参 text-intent router 实验见 `outputs/agent_memory_validation_tuned_router_locomo10_zh.md`。

候选级学习重排实验见 `outputs/agent_memory_candidate_reranker_locomo10_zh.md`，显著性检验见 `outputs/agent_memory_candidate_reranker_significance_zh.md`。

候选级学习重排的按 query type 分析与失败案例见 `outputs/agent_memory_candidate_reranker_by_type_zh.md`。

多证据覆盖分析见 `outputs/agent_memory_multi_evidence_coverage_zh.md`。

集合级选择基线见 `outputs/agent_memory_set_selection_zh.md`。

Top-20 集合级选择补充基线见 `outputs/agent_memory_set_selection_top20_zh.md`。

候选深度分析见 `outputs/agent_memory_candidate_depth_analysis_zh.md`。

Type 3 专用监督重排诊断见 `outputs/agent_memory_type3_specific_reranker_zh.md`。

Type 3 监督式集合选择诊断见 `outputs/agent_memory_type3_supervised_set_selector_zh.md`。

Type 3 query decomposition 弱基线见 `outputs/agent_memory_type3_query_decomposition_zh.md`。

Type 3 evidence coverage 显著性汇总见 `outputs/agent_memory_type3_coverage_significance_zh.md`。

成本与延迟分析见 `outputs/agent_memory_cost_latency_locomo10_zh.md`。

细粒度延迟分解见 `outputs/agent_memory_latency_breakdown_locomo10_zh.md`。

候选预筛选实验见 `outputs/agent_memory_candidate_prefilter_locomo10_zh.md`。

矩阵化 indexed 候选预筛选实验见 `outputs/agent_memory_indexed_prefilter_locomo10_zh.md`。

sklearn NearestNeighbors 向量索引候选预筛选实验见 `outputs/agent_memory_sklearn_nn_prefilter_locomo10_zh.md`。

FAISS 向量索引对比实验见 `outputs/agent_memory_faiss_index_comparison_locomo10_zh.md`。

FAISS 扩展规模压力测试见 `outputs/agent_memory_faiss_scale_locomo10_zh.md`。

零依赖 LSH 近似索引补充基线见 `outputs/agent_memory_lsh_prefilter_locomo10_zh.md`。

LoCoMo10 全量 DeepSeek 抽取结果：

| Memory Form | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact + type-aware | 2517 | 31148 | 1838 | 0.503 | 0.733 | 0.609 |
| LoCoMo observation | 2507 | 40241 | 1638 | 0.483 | 0.703 | 0.583 |

候选级学习重排在 held-out query split 上进一步提升：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| fixed type-aware | 0.499 | 0.670 | 0.733 | 0.607 |
| candidate reranker | 0.556 | 0.732 | 0.796 | 0.661 |
| candidate oracle | 0.909 | 0.909 | 0.909 | 0.909 |

配对检验显示 candidate reranker 相比 fixed type-aware 的 MRR 提升为 `+0.0539`，95% CI `[0.0462, 0.0619]`，permutation p-value `0.0002`。

Type 3 多证据问题的补充诊断显示，单独训练 Type3 专用候选重排器没有超过固定 `type_aware`：MRR `0.399` vs `0.434`，Coverage@5 `0.331` vs `0.377`。因此 Type 3 后续应转向 query decomposition 或监督式 set-level selection，而不是继续单点优化候选重排器。

进一步的 greedy supervised set selector 仍未超过 `type_aware`：MRR `0.389` vs `0.434`，Coverage@5 `0.320` vs `0.377`。这说明仅靠候选上下文特征做集合贪心选择还不够，下一步应显式拆解 Type 3 query 或使用更强 listwise/setwise 目标。

关键词式 query decomposition 弱基线也未超过 `type_aware`：纯拆解 MRR `0.214`，保守融合 MRR `0.342`，均低于 `type_aware` 的 `0.429`；融合后的 Coverage@20 与 `type_aware` 持平但 Top5/MRR 下降。后续如果继续做 decomposition，需要更强的 LLM/规则子问题生成，而不是简单关键词窗口。

Coverage 显著性汇总进一步表明，Type3 专用重排、监督式集合选择、关键词式拆解融合在 Coverage@5 上均低于 `type_aware`，其中 delta 分别为 `-0.0467`、`-0.0572`、`-0.0325`；Coverage@20 没有可靠提升。这把 Type3 的问题界定为“前排多证据覆盖目标缺失”，而不是单纯候选深度不足。

大文件没有纳入 Git：

- `work/agent_memory_experiment/cache/`：本地 BGE-M3 模型和 embedding 缓存
- `work/agent_memory_experiment/results/`：可复现实验输出
- `work/agent_memory_experiment/.venv/`：本地 Python 虚拟环境

复现步骤见 `work/agent_memory_experiment/README.md`。

## DeepSeek API 配置

复制 `.env.example` 为 `.env`，并填入本地 API key：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

`.env` 已被 `.gitignore` 忽略，不会上传到 GitHub。
