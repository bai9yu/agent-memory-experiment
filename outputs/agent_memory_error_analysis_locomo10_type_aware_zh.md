# LoCoMo10 Type-Aware 检索错误分析

## 目标

本报告分析 LoCoMo10 全量实验中 `type_aware(w_type=0.04)` 的 Top-1 检索错误，用于回答两个问题：

1. 当前系统主要错在哪里？
2. `type_aware` 相比 `time_aware` 改善的是哪类错误？

## 设置

- 数据：LoCoMo10 全量 answerable slice
- Memory：DeepSeek extracted fact v3
- Embedding：本地 `BAAI/bge-m3`
- 方法：`type_aware`
- Query 数：1838
- Top-1 错误数：913
- Top-1 错误率：0.497

## 错误原因分布

| Error Reason | Count | Share of Errors | Share of Queries |
|---|---:|---:|---:|
| memory_type_mismatch | 365 | 0.400 | 0.199 |
| gold_below_top20 | 236 | 0.258 | 0.128 |
| other | 78 | 0.085 | 0.042 |
| semantic_neighbor | 63 | 0.069 | 0.034 |
| temporal_neighbor | 57 | 0.062 | 0.031 |
| persona_confusion | 35 | 0.038 | 0.019 |
| activity_neighbor | 33 | 0.036 | 0.018 |
| preference_neighbor | 16 | 0.018 | 0.009 |
| relationship_neighbor | 15 | 0.016 | 0.008 |
| career_education_neighbor | 12 | 0.013 | 0.007 |
| identity_neighbor | 3 | 0.003 | 0.002 |

解释：

- `memory_type_mismatch` 是最大错误来源，说明当前 query intent 到 memory type 的规则仍然粗糙。
- `gold_below_top20` 占 25.8%，说明部分 query 的正确记忆没有进入候选前 20，单纯重排无法修复。
- `persona_confusion` 只占 3.8%，说明 persona gate 对人物主体混淆已有一定控制。
- temporal / activity / preference 等 neighbor 错误说明模型常能找到同一主题附近的记忆，但未能定位到具体事实。

## Query Intent 分布

| Query Intent | Count | Share of Errors | Share of Queries |
|---|---:|---:|---:|
| other | 442 | 0.484 | 0.240 |
| temporal | 153 | 0.168 | 0.083 |
| activity | 97 | 0.106 | 0.053 |
| causal_emotion | 57 | 0.062 | 0.031 |
| preference | 50 | 0.055 | 0.027 |
| location | 47 | 0.051 | 0.026 |
| relationship | 37 | 0.041 | 0.020 |
| career_education | 25 | 0.027 | 0.014 |
| identity | 5 | 0.005 | 0.003 |

`other` 占比过高，说明 query intent 规则还需要继续细化，尤其是 “What did / What kind / What type / Would ...” 这类问题。

## 与 Time-Aware 对比

| Reason | Time-Aware Errors | Type-Aware Errors | Delta |
|---|---:|---:|---:|
| memory_type_mismatch | 369 | 365 | -4 |
| gold_below_top20 | 248 | 236 | -12 |
| activity_neighbor | 34 | 33 | -1 |
| identity_neighbor | 4 | 3 | -1 |
| semantic_neighbor | 62 | 63 | +1 |
| temporal_neighbor | 55 | 57 | +2 |
| persona_confusion | 34 | 35 | +1 |
| preference_neighbor | 14 | 16 | +2 |
| relationship_neighbor | 14 | 15 | +1 |
| career_education_neighbor | 10 | 12 | +2 |

总体上，`type_aware` 把 Top-1 错误从 920 降到 913。主要收益来自：

- 减少正确记忆落到 top-20 之外的情况。
- 略微减少 memory type mismatch。

代价是：

- 部分 temporal / preference / relationship 相邻事实错误略有增加。
- 说明 type signal 不能继续加大权重，否则会压过语义相似度。

## 代表错误

- `q00004` / memory_type_mismatch：What did Caroline research?  
  Top-1 是 adoption tips，gold 是 adoption agency research。

- `q00008` / gold_below_top20：What is Caroline's relationship status?  
  Top-1 是 Caroline is transgender，gold relationship 记忆排在 top-20 之外。

- `q00016` / memory_type_mismatch：What activities does Melanie partake in?  
  Top-1 是 hiking/forest activity，gold 是 pottery/camping/swimming 等活动记忆。

- `q00034` / temporal_neighbor：When did Caroline go to a pride parade during the summer?  
  Top-1 是 missed pride parade last weekend，gold 是 attended pride parade last week。

- `q00049` / gold_below_top20：What types of pottery have Melanie and her kids made?  
  Top-1 是 pottery workshop，gold 是具体 pottery type，正确记忆未进 top-20。

## 后续改进方向

1. 改进 query intent parser，减少 `other` 类。
2. 引入二阶段重排：先保证 gold-like candidates 进入 top-20，再做 type/persona/time reranking。
3. 对 temporal query 引入更强的时间表达解析，区分 last week / last weekend / during summer 等相邻时间。
4. 对 activity / preference query 增加细粒度动作词匹配，避免同主题不同事实互相替代。
5. 抽样人工复核错误分类规则，估计自动错误分类的可靠性。
