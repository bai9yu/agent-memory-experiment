# DeepSeek LLM Memory Extraction 小样本报告

## 目标

本轮接入 DeepSeek API，用大模型从 LoCoMo 原始 session 中自动抽取 fact-level memory，验证 `memory write / extraction` 链路是否可运行。

## 已实现内容

- 新增 `llm_memory_extractor.py`
- 从本地 `.env` 读取 `DEEPSEEK_API_KEY`
- 调用 DeepSeek Chat Completions API
- 要求模型输出结构化 JSON memory
- 将 `source_turn_ids` 映射到 LoCoMo QA evidence
- 输出可直接用于 `memory_eval.py` 的 `memories.jsonl` 和 `queries.jsonl`
- 新增 `filter_memory_eval_slice.py`，用于按 LoCoMo session / sample 切出小评测集

## Memory Schema

当前 LLM 抽取的 memory 格式为：

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
  "visibility": "shared",
  "source_evidence_ids": ["D1:3"],
  "compression_variant": "llm_extracted_fact"
}
```

## API 小样本结果

设置：

- 模型：`deepseek-chat`
- 数据：LoCoMo 第 1 个 conversation 的第 1 个 session
- 输入 session：`D1`
- 抽取 memory 数：`7`
- API token 用量：prompt `850`，completion `553`，total `1403`

输出目录：

`work/agent_memory_experiment/data/llm_extracted_locomo_1s`

## 与 LoCoMo 官方 Observation 对比

为了公平比较，只评测第一个 conversation 的 `D1`，并只保留可由当前 memory 覆盖的 QA。

| Variant | Memories | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| LLM extracted fact | 7 | 5 | 0.400 | 0.800 | 1.000 | 0.607 |
| LoCoMo observation | 7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 |

解释：

- LLM 已经能抽出与 observation 高度相似的事实，并正确引用 turn id。
- 当前 prompt 抽取得较精简，对 D1 的 5 个可回答 QA 有覆盖，但检索排序不如官方 observation。
- 差距主要来自 memory 文本措辞和证据粒度：官方 observation 更贴近 QA 表达；LLM 输出更概括，hash/hybrid 检索时容易排错。

## 当前判断

DeepSeek API 接入成功，memory write 链路已经打通。

下一步不是继续调检索器，而是优化 extraction prompt：

1. 提高 evidence 覆盖率，避免遗漏 QA 相关事实。
2. 让 memory 文本更接近可检索事实表达，例如保留 `when / what / who / why` 信息。
3. 对一条复杂事实允许生成多个更细粒度 memory。
4. 将 `visibility` 默认改为 `private`，只有明确可共享的事实才标为 `shared`。
5. 增加 automatic judge：比较 LLM memory 与 LoCoMo observation 的 source turn 覆盖率、事实重叠和 token 成本。

## 复现命令

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1s \
  --max-records 1 \
  --max-sessions 1 \
  --temperature 0.1
```

```bash
python3 work/agent_memory_experiment/filter_memory_eval_slice.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s/memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s/queries.jsonl \
  --output-prefix work/agent_memory_experiment/data/llm_extracted_locomo_1s_d1 \
  --sessions D1 \
  --require-answer
```

```bash
python3 work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s_d1_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s_d1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo_1s_d1_hash \
  --rank-output-k 7 \
  --importance-weight 0.06
```
