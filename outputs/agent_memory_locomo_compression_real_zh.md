# LoCoMo 真实压缩对照实验报告

本实验比较三种记忆形态：原始 turn-level memory、LoCoMo 官方 observation fact、LoCoMo 官方 session summary。评测使用同一套 BGE-M3 embedding、adaptive time-aware、persona gate 和 importance proxy。

## 总体结果

| Variant | Memories | Token Ratio | Evidence Coverage | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw_turn | 5882 | 1.000 | 1.000 | 0.329 | 0.492 | 0.562 | 0.439 |
| observation | 2541 | 0.281 | 0.785 | 0.400 | 0.532 | 0.585 | 0.484 |
| session_summary | 272 | 0.201 | 0.997 | 0.520 | 0.695 | 0.773 | 0.636 |

## 关键解释

- `raw_turn` 是原始对话 turn 级记忆，粒度最细，但 token 成本最高，闲聊噪声也最多。
- `observation` 是 LoCoMo 官方抽取的事实级记忆，只保留约 28% token。它的 Recall@1 高于 raw，说明高质量事实抽取能显著减少检索噪声；但 evidence 覆盖率约 78%，部分 QA 在 observation 中已经没有可召回证据。
- `session_summary` 只保留约 20% token，覆盖率接近完整，检索指标最高。但它把一个 session 压成一个大块，gold target 也变成 session 级，因此指标会比 turn/fact 级更容易；真实 Agent 回答时还需要在摘要内部定位具体事实。

## 当前结论

第一阶段已经可以证明：记忆压缩不是简单越短越好。更合理的结构是两层记忆：

1. 在线检索层：以 observation/fact-level memory 为主，保留较细粒度，适合直接召回事实。
2. 归档回溯层：以 session_summary 为主，保留完整上下文，适合做二次检索或回答补充。

下一步若要继续提升 observation 覆盖率和质量，就需要接入大模型做 memory write：从原始对话中自动抽取事实、重要性、主体、时间、置信度和权限字段。
