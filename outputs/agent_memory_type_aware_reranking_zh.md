# Type-Aware Memory Reranking 消融实验

## 实验目标

完整 conversation 实验显示，DeepSeek 抽取的 fact-level memory 已经具备较好的候选召回能力，但 Top-1 排序仍有错误，尤其集中在身份、关系、活动、计划和时间类问题。

本实验加入 `type_aware` 重排方法，验证 query intent 与 memory_type 的匹配是否能改善 Top-1 排序。

## 方法

原 `time_aware` 分数为：

```text
score_time =
  0.70 * semantic
+ 0.30 * keyword
+ 0.08 * recency_gate(query) * time_decay(memory, query)
+ w_persona(query) * persona_score
+ w_importance * importance_score
```

新增 `type_aware` 分数为：

```text
score_type =
  score_time
+ w_type * type_match(query, memory)
```

其中：

- `type_match(query, memory)` 由规则识别 query intent 后，与 `memory.memory_type` 匹配得到。
- 身份类 query 优先 `identity` / `profile`。
- 关系类 query 优先 `relationship` / `family`。
- 职业与教育类 query 优先 `goal` / `plan` / `education` / `work`。
- 活动类 query 优先 `hobby` / `event` / `plan` / `preference`。
- 时间类 query 优先 `event` / `plan`。

## 数据与设置

- 数据：LoCoMo 第 1 个完整 conversation
- Memory：DeepSeek extracted fact v3
- Embedding：本地 `BAAI/bge-m3`
- 基线：`time_aware`
- 固定参数：`persona_boost_weight=0.04`，`importance_weight=0.06`
- 调参范围：`w_type ∈ {0.04, 0.08, 0.12}`

## 主结果

### 第 1 个完整 conversation

| Type Weight | Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---|---:|---:|---:|---:|
| 0.00 | time_aware | 0.509 | 0.680 | 0.743 | 0.620 |
| 0.04 | type_aware | 0.514 | 0.680 | 0.737 | 0.624 |
| 0.08 | type_aware | 0.514 | 0.691 | 0.737 | 0.626 |
| 0.12 | type_aware | 0.509 | 0.697 | 0.749 | 0.625 |

### LoCoMo10 全量

| Type Weight | Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---|---:|---:|---:|---:|
| 0.00 | time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| 0.04 | type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| 0.08 | type_aware | 0.503 | 0.669 | 0.733 | 0.609 |
| 0.12 | type_aware | 0.498 | 0.663 | 0.732 | 0.606 |

全量结果显示 `w_type=0.04` 的 MRR 最好，`w_type=0.08` 接近但略低，`w_type=0.12` 开始退化。因此后续全量主实验推荐采用 `w_type=0.04`。

## 按问题类型观察

第 1 个完整 conversation 上，`w_type=0.08` 时：

- Type 1：MRR 从 `0.405` 提升到 `0.425`，Recall@1 从 `0.233` 提升到 `0.267`。
- Type 3：Recall@3 从 `0.636` 提升到 `0.727`。
- Type 4：MRR 从 `0.677` 提升到 `0.682`，Recall@3 从 `0.702` 提升到 `0.719`。
- Type 5：MRR 轻微提升，但 Recall@5 从 `0.619` 降到 `0.595`。

## 排序变化

第 1 个完整 conversation 上，相对 `time_aware`，`w_type=0.08`：

- 25 个 query 的 MRR 或 Recall@1 改善。
- 9 个 query 的 MRR 或 Recall@1 变差。

典型改善：

- `q00061`：What instruments does Melanie play? 首个正确结果从第 2 位升到第 1 位。
- `q00007`：When is Melanie planning on going camping? 首个正确结果从第 2 位升到第 1 位。
- `q00199`：What does Caroline love most about camping with her family? 首个正确结果从第 4 位升到第 2 位。

典型退化：

- `q00075`：When did Melanie's family go on a roadtrip? 首个正确结果从第 1 位降到第 2 位。
- `q00071`：What transgender-specific events has Caroline attended? 首个正确结果从第 3 位降到第 7 位。
- `q00171`：What does Caroline say running has been great for? 首个正确结果从第 3 位降到第 7 位。

LoCoMo10 全量上，相对 `time_aware`，`w_type=0.04`：

- 174 个 query 的 MRR 或 Recall@1 改善。
- 80 个 query 的 MRR 或 Recall@1 变差。

典型改善：

- `q01629`：How did Evan get into painting? 首个正确结果从第 3 位升到第 1 位。
- `q00005`：What is Caroline's identity? 首个正确结果从第 3 位升到第 1 位。
- `q01944`：What type of cars does Calvin work on at his shop? 首个正确结果从第 2 位升到第 1 位。

典型退化：

- `q01076`：How long does Audrey typically walk her dogs for? 首个正确结果从第 1 位降到第 3 位。
- `q01577`：How did Jolene's mom support her yoga practice when she first started? 首个正确结果从第 1 位降到第 3 位。
- `q00373`：What type of workout class did Maria start doing in December 2023? 首个正确结果从第 1 位降到第 2 位。

## 当前结论

`type_aware` 是一个有效但需要保守使用的重排信号。它能改善身份、活动、计划等 Top-1 排序问题，但过高权重会压过语义相似度，导致部分事件类问题退化。

## 显著性检验

在 LoCoMo10 全量上，对 `time_aware` 与 `type_aware(w_type=0.04)` 做 paired bootstrap 与 paired permutation test：

| Metric | Delta | 95% Bootstrap CI | Permutation p-value |
|---|---:|---:|---:|
| MRR | 0.004213 | [0.001214, 0.007182] | 0.0072 |
| Recall@1 | 0.003808 | [-0.001088, 0.009249] | 0.2066 |
| Recall@3 | 0.002176 | [-0.002720, 0.007073] | 0.5103 |
| Recall@5 | 0.006529 | [0.002720, 0.010881] | 0.0028 |

解释：`type_aware` 对 MRR 和 Recall@5 的提升较小但统计上更可靠；对 Recall@1 和 Recall@3 的提升还不稳定。

当前推荐论文实验设置：

```text
BGE-M3 + time_aware + persona gate + importance proxy + type_aware(w_type=0.04)
```

下一步需要增加多次 LLM 抽取重复实验和显著性检验，判断 `type_aware` 的小幅增益是否稳定。
