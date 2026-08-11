# Agent Memory Experiment

本仓库实现了一套面向长对话与多智能体场景的 agent memory 实验框架，覆盖记忆构建、检索、重排、压缩和跨智能体复用。

## 功能概览

- LoCoMo 真实长对话数据接入
- 本地 BGE-M3 embedding 检索与 embedding cache
- BM25 + semantic hybrid retrieval
- adaptive time-aware reranking
- persona gate，用于减少人物主体混淆
- importance proxy，用于提升身份、关系、长期目标、偏好等高价值记忆
- LoCoMo `observation` / `session_summary` 真实压缩对照
- DeepSeek LLM fact-level memory extraction，并与 LoCoMo 官方 observation memory 对比
- 跨智能体共享记忆的权限过滤与风险对照实验
- 中文实验报告、参数搜索记录和复盘文档

主要代码在 `work/agent_memory_experiment/`。

中文文档和实验报告在 `outputs/`，其中 DeepSeek 记忆抽取报告见：

- `outputs/agent_memory_llm_extraction_deepseek_zh.md`
- `outputs/agent_memory_llm_extraction_1conversation_comparison_zh.md`

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

当前已加入 `type_aware` 重排消融；在第 1 个完整 conversation 上，`w_type=0.08` 将 MRR 从 `0.620` 提升到 `0.626`，Recall@3 从 `0.680` 提升到 `0.691`。详细结果见 `outputs/agent_memory_type_aware_reranking_zh.md`。

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
