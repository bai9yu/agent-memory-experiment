# 智能体记忆项目：Embedding 模型选择与 BGE 本地路线

## 1. 当前结论

当前项目先不接 OpenAI embedding，也不接 Qwen embedding API。推荐路线改为：

```text
hash baseline -> BAAI/bge-small-en-v1.5 -> BAAI/bge-m3
```

原因：

1. `hash` baseline 零依赖，用于确认数据转换、评测指标和检索流程没有问题。
2. `BAAI/bge-small-en-v1.5` 体积小、下载快、适合先做本地真实 embedding smoke test。
3. `BAAI/bge-m3` 是后续主力模型，更适合多语言、长文本和 RAG/记忆检索场景。

## 2. BGE 是否需要下载模型

需要。BGE 是本地开源 embedding 模型，第一次运行会从 Hugging Face 下载模型文件到本地缓存；下载完成后可以离线复用。

当前缓存目录统一放在项目内：

```text
work/agent_memory_experiment/cache/huggingface
work/agent_memory_experiment/cache/sentence_transformers
```

这样之后换机器或清理环境时更容易定位。

## 3. 推荐模型

| 模型 | 类型 | 适合阶段 | 优点 | 注意点 |
|---|---|---|---|---|
| `hash` | 无模型 baseline | 流程验证 | 不需要安装、不需要联网、可快速复现 | 语义能力弱，只能当底线 |
| `BAAI/bge-small-en-v1.5` | 本地开源 embedding | 第一轮真实 embedding 验证 | 小、快、稳定，适合确认代码路径 | 英文为主，能力弱于 BGE-M3 |
| `BAAI/bge-base-en-v1.5` | 本地开源 embedding | 可选中间对照 | 效果通常强于 small | 比 small 慢 |
| `BAAI/bge-m3` | 本地开源 embedding | 正式主线 | 多语言、最长 8192 tokens，贴近记忆检索/RAG | 模型较大，首次下载和加载更慢 |
| Voyage / Gemini / Jina | API embedding | 后续质量对照 | 工业级 API，省本地算力 | 需要 API key 和费用 |

当前优先级：

```text
先完成 BGE-small 和 BGE-M3 的本地复现，再考虑是否加入 API 对照。
```

## 4. 本项目如何接入

代码中的真实 embedding 后端统一使用：

```text
--semantic-backend sentence-transformer
```

模型名通过：

```text
--embedding-model BAAI/bge-small-en-v1.5
--embedding-model BAAI/bge-m3
```

下载后离线复现时加：

```text
--local-files-only
```

## 5. 先跑 BGE-small

```bash
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_1_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_1_bge_small \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-small-en-v1.5 \
  --local-files-only
```

验证重点：

1. 模型是否能从本地缓存加载。
2. `summary.csv`、`rankings.csv`、`report.md` 是否正常生成。
3. `vector / hybrid / time_aware` 三组方法是否都有指标。

## 6. 再跑 BGE-M3

```bash
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_1_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_1_bge_m3 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --local-files-only
```

如果单样本验证没有问题，再跑全量 LoCoMo：

```bash
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_all_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_all_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_all_bge_m3 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --local-files-only
```

## 7. 后续实验记录方式

每次换 embedding 模型，都固定记录：

```text
模型名
数据集规模
Recall@1 / Recall@3 / Recall@5 / MRR
运行时间
是否离线加载成功
遇到的问题和解决方法
```

推荐结果目录命名：

```text
locomo_real_1_bge_small
locomo_real_1_bge_m3
locomo_real_all_bge_m3
locomo_real_all_bge_m3_adaptive_time
locomo_real_all_bge_m3_persona_004_types_1_4
```

## 8. 当前实测结果

### LoCoMo 1 个样本，BGE-small

结果目录：

```text
work/agent_memory_experiment/results/locomo_real_1_bge_small
```

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.271 | 0.447 | 0.558 | 0.392 | 199 |
| time_aware | 0.246 | 0.422 | 0.523 | 0.369 | 199 |
| vector | 0.261 | 0.472 | 0.568 | 0.396 | 199 |

### LoCoMo 1 个样本，BGE-M3

结果目录：

```text
work/agent_memory_experiment/results/locomo_real_1_bge_m3
```

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.276 | 0.412 | 0.528 | 0.381 | 199 |
| time_aware | 0.261 | 0.417 | 0.482 | 0.364 | 199 |
| vector | 0.126 | 0.317 | 0.427 | 0.268 | 199 |

### LoCoMo 全量，BGE-M3，初始 time-aware

结果目录：

```text
work/agent_memory_experiment/results/locomo_real_all_bge_m3
```

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.242 | 0.380 | 0.443 | 0.338 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

### LoCoMo 全量，BGE-M3，adaptive time-aware

结果目录：

```text
work/agent_memory_experiment/results/locomo_real_all_bge_m3_adaptive_time
```

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.310 | 0.473 | 0.537 | 0.418 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

当前判断：BGE-M3 已经能作为本地正式 embedding 主线；adaptive time-aware 已经超过 hybrid。embedding 落盘缓存、persona gate 和 importance proxy 已经完成第一轮验证。

### LoCoMo 全量，BGE-M3，adaptive time-aware + persona gate

结果目录：

```text
work/agent_memory_experiment/results/locomo_real_all_bge_m3_persona_004_types_1_4
```

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.321 | 0.484 | 0.543 | 0.429 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

### LoCoMo 全量，BGE-M3，adaptive time-aware + persona gate + importance proxy

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 |
| time_aware | 0.329 | 0.492 | 0.562 | 0.439 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 |

当前最终推荐：BGE-M3 + embedding cache + adaptive time-aware + persona gate + importance proxy。参数为 `persona_boost_weight=0.04`，`persona_boost_query_types=1,2,3,4`，`importance_weight=0.06`。

## 9. 资料来源

- BGE-M3 Hugging Face: https://huggingface.co/BAAI/bge-m3
- BGE small v1.5 Hugging Face: https://huggingface.co/BAAI/bge-small-en-v1.5
- Sentence Transformers: https://www.sbert.net/
