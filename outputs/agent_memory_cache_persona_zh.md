# Embedding 缓存与 Persona/Entity 过滤实验

## 1. 已完成

本轮完成两个工程与方法改进：

1. BGE-M3 embedding 落盘缓存。
2. Persona/entity soft boost，并支持按 LoCoMo query type 开关。

## 2. Embedding 缓存

缓存位置：

```text
work/agent_memory_experiment/cache/embeddings/sentence_transformer/BAAI_bge-m3/
```

当前缓存大小约 `31MB`，包含 LoCoMo 小样本和全量 LoCoMo 的 memory/query 向量。

缓存键包含：

```text
kind
model_name
item_id
text
```

因此 memory/query 文本变化后会自动生成新缓存，不会误用旧向量。

小样本验证中，同一输入第二次运行从约 `18s` 降到约 `4s`。全量运行仍需要做 BM25、排序和写结果，但不再重复编码 BGE-M3。

## 3. Persona/Entity Soft Boost

公式：

\[
S_{\mathrm{time+persona}}(q,m_i)
=
0.70\cdot \mathrm{semantic}
+0.30\cdot \mathrm{BM25}_{norm}
+0.08\cdot g_{\mathrm{recency}}(q)\cdot \mathrm{decay}
+\gamma(q)\cdot \mathrm{persona}(q,m_i)
\]

其中：

\[
\gamma(q)=
\begin{cases}
0.04, & \mathrm{type}(q)\in\{1,2,3,4\}\\
0, & \mathrm{type}(q)=5
\end{cases}
\]

persona 分数：

```text
query 提到的人名 = memory speaker        -> +1.0
query 提到的人名出现在 memory text 中    -> +0.7
query 提到人名但 memory 不匹配           -> -0.5
query 未提到人名                         -> 0
```

这样不是硬过滤，而是软约束，避免误伤“Melanie 在谈 Caroline”这类证据。

## 4. 全量结果

| Variant | Persona weight | Types | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---|---:|---:|---:|---:|
| Adaptive time-aware | 0.00 | all | 0.310 | 0.473 | 0.537 | 0.418 |
| Persona | 0.01 | all | 0.313 | 0.474 | 0.537 | 0.421 |
| Persona | 0.02 | all | 0.316 | 0.474 | 0.537 | 0.422 |
| Persona | 0.03 | all | 0.318 | 0.471 | 0.538 | 0.423 |
| Persona | 0.04 | all | 0.319 | 0.471 | 0.537 | 0.423 |
| Persona gated | 0.04 | 1,2,3,4 | 0.321 | 0.484 | 0.543 | 0.429 |

最终推荐：`persona_boost_weight=0.04`，`persona_boost_query_types=1,2,3,4`。

## 5. 对 Hybrid 的提升

LoCoMo 全量+BGE-M3：

| Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 |
| time-aware + persona gate | 0.321 | 0.484 | 0.543 | 0.429 |

提升：

```text
Recall@1: +0.038
Recall@3: +0.039
Recall@5: +0.029
MRR:      +0.037
```

## 6. 复现实验命令

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_real_all_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_real_all_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_real_all_bge_m3_persona_004_types_1_4 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 20 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4
```

## 7. 下一步

1. 将 BM25/query ranking 的中间特征也缓存，进一步减少全量排序时间。
2. 加入 importance proxy：长期偏好、身份、目标、关系、计划等记忆权重更高。
3. 用 `session_summary` 和 `observation` 做真实压缩对照。
