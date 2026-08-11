# LoCoMo 真实数据接入实验报告

## 数据与转换

- Memory 文件：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/data/locomo_real_all_memories.jsonl`
- Query 文件：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/data/locomo_real_all_queries.jsonl`
- 评测结果目录：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/results/locomo_real_all`

LoCoMo 原始数据包含多 session 长对话、时间戳、QA 标注和 evidence。当前转换器把对话 turn 转为 memory，把 QA question 转为 query，并把 `D1:3` 这类 evidence id 映射到本地 `mxxxxx` memory id。

## 总体指标

### Hash baseline

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.186 | 0.299 | 0.342 | 0.263 | 1986 |
| time_aware | 0.161 | 0.267 | 0.318 | 0.237 | 1986 |
| vector | 0.081 | 0.119 | 0.141 | 0.116 | 1986 |

### BGE-M3 本地 embedding：初始 time-aware

结果目录：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/results/locomo_real_all_bge_m3`

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.242 | 0.380 | 0.443 | 0.338 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

对比 hash baseline，BGE-M3 明显提升纯向量与 hybrid 检索质量，说明当前 LoCoMo 真实数据已经适合进入“真实 embedding + 权重/时间项调参”阶段。

### BGE-M3 本地 embedding：adaptive time-aware

结果目录：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/results/locomo_real_all_bge_m3_adaptive_time`

参数来源：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/outputs/agent_memory_time_aware_tuning_zh.md`

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.310 | 0.473 | 0.537 | 0.418 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

这版 time-aware 已经超过 hybrid：Recall@1 提升 `+0.027`，Recall@3 提升 `+0.028`，Recall@5 提升 `+0.023`，MRR 提升 `+0.026`。

### BGE-M3 本地 embedding：adaptive time-aware + persona gate

结果目录：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/results/locomo_real_all_bge_m3_persona_004_types_1_4`

参数：`persona_boost_weight=0.04`，`persona_boost_query_types=1,2,3,4`

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.321 | 0.484 | 0.543 | 0.429 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

相比 hybrid，最终 time-aware + persona gate 的 Recall@1 提升 `+0.038`，MRR 提升 `+0.037`。

### BGE-M3 本地 embedding：adaptive time-aware + persona gate + importance proxy

结果目录：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/work/agent_memory_experiment/results/locomo_real_all_bge_m3_importance_006`

参数：`persona_boost_weight=0.04`，`persona_boost_query_types=1,2,3,4`，`importance_weight=0.06`

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---:|---:|---:|---:|---:|
| hybrid | 0.283 | 0.445 | 0.514 | 0.392 | 1986 |
| time_aware | 0.329 | 0.492 | 0.562 | 0.439 | 1986 |
| vector | 0.202 | 0.366 | 0.452 | 0.322 | 1986 |

相比只加 persona gate 的版本，importance proxy 继续提升 Recall@1 `+0.008`，Recall@3 `+0.009`，Recall@5 `+0.019`，MRR `+0.010`。相比 hybrid，最终推荐方法 Recall@1 提升 `+0.045`，MRR 提升 `+0.047`。

## 真实压缩对照

结果文档：`/Users/byx/Documents/Codex/2026-08-10/referenced-chatgpt-conversation-this-is-an/outputs/agent_memory_locomo_compression_real_zh.md`

| Variant | Memories | Token Ratio | Evidence Coverage | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw_turn | 5882 | 1.000 | 1.000 | 0.329 | 0.492 | 0.562 | 0.439 |
| observation | 2541 | 0.281 | 0.785 | 0.400 | 0.532 | 0.585 | 0.484 |
| session_summary | 272 | 0.201 | 0.997 | 0.520 | 0.695 | 0.773 | 0.636 |

解释：LoCoMo 官方 `observation` 相当于高质量事实抽取，去掉大量闲聊噪声，所以在只保留约 28% token 的情况下 Recall@1 高于 raw；但 evidence 覆盖率约 78%，说明部分事实没有被抽出。`session_summary` 覆盖率接近完整且指标最高，但它是 session 级粗粒度目标，不能直接等价为“事实级检索更准”。

## 按问题类别

| Category | Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |
|---|---|---:|---:|---:|---:|---:|
| 1 | hybrid | 0.142 | 0.298 | 0.358 | 0.250 | 282 |
| 1 | time_aware | 0.170 | 0.326 | 0.404 | 0.284 | 282 |
| 1 | vector | 0.145 | 0.273 | 0.383 | 0.261 | 282 |
| 2 | hybrid | 0.389 | 0.589 | 0.632 | 0.506 | 321 |
| 2 | time_aware | 0.414 | 0.598 | 0.667 | 0.527 | 321 |
| 2 | vector | 0.318 | 0.502 | 0.573 | 0.444 | 321 |
| 3 | hybrid | 0.125 | 0.208 | 0.260 | 0.198 | 96 |
| 3 | time_aware | 0.135 | 0.229 | 0.281 | 0.213 | 96 |
| 3 | vector | 0.094 | 0.219 | 0.292 | 0.184 | 96 |
| 4 | hybrid | 0.334 | 0.501 | 0.576 | 0.447 | 841 |
| 4 | time_aware | 0.371 | 0.530 | 0.592 | 0.478 | 841 |
| 4 | vector | 0.238 | 0.442 | 0.532 | 0.376 | 841 |
| 5 | hybrid | 0.235 | 0.381 | 0.466 | 0.339 | 446 |
| 5 | time_aware | 0.247 | 0.422 | 0.478 | 0.356 | 446 |
| 5 | vector | 0.110 | 0.213 | 0.291 | 0.200 | 446 |

## 初步解释

- 真实 LoCoMo 比合成数据更难：问题存在转述、跨 session、多证据、时间推理和隐含推理。
- hash embedding 只是离线基线，语义能力弱；BGE-M3 接入后 `vector`、`hybrid` 均明显提升。
- 初始 time-aware 把所有问题统一偏向最近记忆，因此在 LoCoMo 上低于 hybrid。
- adaptive time-aware 只在“最近性意图”问题上触发时间项，并排除 `when/date/time` 这类历史时间问句，因此在全量和各类别上都超过 hybrid。
- persona gate 进一步减少“人物相似但主体错误”的干扰；它是 soft boost，不是硬过滤，因此仍允许“别人谈到目标人物”的证据进入排序。
- importance proxy 让身份、关系、长期目标、偏好、重要事件和强情绪记忆更容易被召回；当前先用规则代理保证可复现，后续可替换为 LLM-based memory importance estimator。

## 下一步

1. 继续验证 persona gate + importance proxy 在 LongMemEval 或更多 LoCoMo split 上是否稳定。
2. 增加 LLM-based memory write：把原始对话转为结构化事实、重要性、置信度和过期时间。
3. 在跨智能体设置中加入 shared memory 的去重、冲突更新和 KV cache 复用收益统计。
