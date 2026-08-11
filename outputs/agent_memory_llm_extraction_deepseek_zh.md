# DeepSeek LLM Memory Extraction 实验报告

## 目标

本实验接入 DeepSeek API，从 LoCoMo 原始长对话 session 中自动抽取 fact-level memory，验证真实大模型作为 `memory write / extraction` 模块时，能否生成可检索、可压缩、可复现的长期记忆。

当前链路已经覆盖：

- 从 `.env` 读取 DeepSeek API 配置
- 调用 DeepSeek Chat Completions API
- 从原始 session 抽取结构化 memory
- 将 `source_turn_ids` 映射到 LoCoMo QA evidence
- 输出可直接用于 `memory_eval.py` 的 `memories.jsonl` 和 `queries.jsonl`
- 与 LoCoMo 官方 `observation` memory 做同 slice 对比
- 使用本地 BGE-M3 embedding 进行检索评测

## Memory Schema

LLM 抽取的 memory 格式如下：

```json
{
  "id": "llm_00001",
  "session_id": "1_session_1",
  "turn": 3,
  "date": "2023-05-08",
  "agent_id": "Caroline",
  "user_id": "user_1",
  "text": "Caroline attended a LGBTQ support group and found it powerful.",
  "entities": ["Caroline", "LGBTQ"],
  "memory_type": "event",
  "importance": 0.7,
  "confidence": 0.9,
  "visibility": "private",
  "source_evidence_ids": ["D1:3"],
  "compression_variant": "llm_extracted_fact"
}
```

## 抽取方法

当前方法是“LLM 写记忆 + 本地 embedding 检索”：

1. 对每个 LoCoMo session 构造对话输入。
2. DeepSeek 从对话中抽取 6-12 条长期记忆。
3. 每条记忆保留主体、类型、重要性、置信度、可见性和证据 turn id。
4. 对 goal / plan / work / education 等相邻事实做轻量 evidence 后处理，减少官方 QA evidence 与 LLM 抽取粒度不一致的问题。
5. 用 BGE-M3 将 query 与 memory 编码。
6. 使用 `vector`、`hybrid`、`time_aware` 三类检索策略评测 Recall@K 和 MRR。

## Prompt 优化

早期 prompt 的问题：

- 抽取偏精简，容易漏掉短事实和生活计划。
- 身份类问题没有直接写成可检索事实。
- career / goal 类记忆容易缺少具体领域。
- `visibility` 偏向 `shared`，不适合作为记忆安全默认策略。

当前 prompt 的改动：

- 改为 coverage-first，优先覆盖未来可能被问到的长期事实。
- 身份、关系、计划、偏好、重要事件、情绪和承诺都作为候选长期记忆。
- 多事实拆成多条 memory。
- career / goal 记忆保留具体方向，例如 counseling / mental health。
- event memory 保留 yesterday / last year 等时间表达。
- 默认 `visibility=private`，只有明确共享意图时标记为 `shared`。

## 实验结果

### D1 单 session 小样本

| Variant | Backend | Memories | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| LLM extracted fact v1 | hash | 7 | 5 | 0.400 | 0.800 | 1.000 | 0.607 |
| LLM extracted fact v2 | BGE-M3 | 10 | 7 | 0.714 | 1.000 | 1.000 | 0.833 |
| LLM extracted fact v3 | BGE-M3 | 10 | 7 | 0.857 | 1.000 | 1.000 | 0.929 |
| LoCoMo observation | BGE-M3 | 7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 |

### D1-D3 三 session 对比

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR | API Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LLM extracted fact | 28 | 358 | 29 | 0.586 | 0.759 | 0.793 | 0.679 | 6219 |
| LoCoMo observation | 28 | 464 | 29 | 0.483 | 0.724 | 0.793 | 0.619 | 0 |

### 第 1 个完整 conversation 对比

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR | API Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LLM extracted fact | 187 | 2443 | 175 | 0.474 | 0.669 | 0.726 | 0.590 | 42014 |
| LoCoMo observation | 184 | 3002 | 155 | 0.497 | 0.600 | 0.690 | 0.578 | 0 |

## 当前结论

- DeepSeek 已经可以作为真实 `memory write` 模块接入，生成的 fact-level memory 能直接参与检索实验。
- 在三 session 和完整 conversation 上，LLM 抽取记忆的 token 数少于 LoCoMo observation，同时 answerable query 覆盖不低于 observation。
- 完整 conversation 上，LLM 的 Recall@3、Recall@5、MRR 略高于 observation，但 Recall@1 略低，说明候选召回已经有效，Top-1 排序仍需要优化。
- 主要错误集中在主体混淆、关系/身份查询、活动类查询和时间计划类查询。

## 后续改进方向

1. 扩大到 LoCoMo10 全部 conversation，确认结果是否稳定。
2. 增加 memory-type-aware reranking：身份问题优先 identity，活动问题优先 hobby / event / plan，关系问题优先 relationship。
3. 对 DeepSeek 抽取做重复运行，报告均值和方差，避免单次 prompt 偶然性。
4. 加入消融实验：无 persona gate、无 importance、无 time-aware、仅 vector、仅 hybrid。
5. 增加 API 成本统计：按 session、conversation、memory token ratio 汇总。

## Type-Aware Reranking 初步消融

在第 1 个完整 conversation 上，已加入 `type_aware` 方法：

```text
score_type = score_time + w_type * type_match(query, memory)
```

| Type Weight | Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---|---:|---:|---:|---:|
| 0.00 | time_aware | 0.509 | 0.680 | 0.743 | 0.620 |
| 0.04 | type_aware | 0.514 | 0.680 | 0.737 | 0.624 |
| 0.08 | type_aware | 0.514 | 0.691 | 0.737 | 0.626 |
| 0.12 | type_aware | 0.509 | 0.697 | 0.749 | 0.625 |

初步结论：`w_type=0.08` 的 MRR 最好，能修复部分身份、活动和计划类 Top-1 错误；但该信号仍需在 LoCoMo10 全量上验证稳定性。

## 复现命令

三 session 抽取：

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1c_3s_v3 \
  --max-records 1 \
  --max-sessions 3 \
  --temperature 0.1
```

完整 conversation 抽取：

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3 \
  --max-records 1 \
  --max-sessions 30 \
  --temperature 0.1
```

生成 LLM 与 observation 对比报告：

```bash
python3 work/agent_memory_experiment/summarize_llm_extraction_comparison.py \
  --llm-memories work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3_d1_d30_memories.jsonl \
  --llm-summary work/agent_memory_experiment/results/llm_extracted_locomo_1c_all_v3_d1_d30_bge_m3/summary.csv \
  --llm-rankings work/agent_memory_experiment/results/llm_extracted_locomo_1c_all_v3_d1_d30_bge_m3/rankings.csv \
  --llm-usage work/agent_memory_experiment/data/llm_extracted_locomo_1c_all_v3/usage.csv \
  --observation-memories work/agent_memory_experiment/data/locomo_observation_record1_d1_d30_memories.jsonl \
  --observation-summary work/agent_memory_experiment/results/locomo_observation_record1_d1_d30_bge_m3/summary.csv \
  --observation-rankings work/agent_memory_experiment/results/locomo_observation_record1_d1_d30_bge_m3/rankings.csv \
  --output outputs/agent_memory_llm_extraction_1conversation_comparison_zh.md \
  --csv-output outputs/agent_memory_llm_extraction_1conversation_comparison.csv
```
