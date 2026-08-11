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
- v1 抽取 memory 数：`7`
- v1 API token 用量：prompt `850`，completion `553`，total `1403`
- v3 抽取 memory 数：`10`
- v3 API token 用量：prompt `1067`，completion `757`，total `1824`

输出目录：

`work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3`

## Prompt 优化

v1 的问题：

- 抽取偏精简，遗漏了 Melanie 正在管理孩子和工作、游泳计划等短事实。
- 对 Caroline 身份只抽到 “transgender stories inspired her”，没有直接写出 “Caroline is a transgender woman”。
- 默认 `visibility` 偏向 `shared`，不符合记忆安全的保守策略。

v3 的改动：

- prompt 改为 coverage-first，优先覆盖可被未来问题询问的事实。
- 要求 identity 问题写直接身份事实。
- 要求 career/goal 记忆保留具体领域，如 counseling / mental health。
- 要求 event memory 保留 yesterday / last year 等时间表达。
- 对同一主体相邻的 plan/goal/work/education 事实增加 source-turn 关联后处理。
- 默认 `visibility=private`，只有明确共享意图才标记为 `shared`。

## 与 LoCoMo 官方 Observation 对比

为了公平比较，只评测第一个 conversation 的 `D1`，并只保留可由当前 memory 覆盖的 QA。

| Variant | Backend | Memories | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| LLM extracted fact v1 | hash | 7 | 5 | 0.400 | 0.800 | 1.000 | 0.607 |
| LLM extracted fact v2 | BGE-M3 | 10 | 7 | 0.714 | 1.000 | 1.000 | 0.833 |
| LLM extracted fact v3 | BGE-M3 | 10 | 7 | 0.857 | 1.000 | 1.000 | 0.929 |
| LoCoMo observation | BGE-M3 | 7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 |

解释：

- LLM 已经能抽出与 observation 高度相似的事实，并正确引用 turn id。
- v3 比 v1 多覆盖 2 个可回答 QA，并在 BGE-M3 下把 Recall@1 提升到 `0.857`。
- 当前剩余 Top-1 错误是 `What activities does Melanie partake in?`：检索器把 `Melanie is managing kids and work` 排在 `Melanie is going swimming with the kids` 前面。
- 这个错误既可以通过 prompt 让 activity/hobby/plan 类记忆更显式，也可以通过检索器增加 query-type / memory-type 重排解决。

## 当前判断

DeepSeek API 接入成功，memory write 链路已经打通；v3 prompt 已经明显优于 v1。

下一步需要人工确认策略后继续：

1. 路线 A：继续优化 extraction prompt，让 activity/hobby/plan 类事实更显式，减少检索歧义。
2. 路线 B：增加 memory-type-aware reranking，例如 activity query 对 `hobby/plan/preference` 加权、对 `work` 降权。
3. 路线 C：先扩大到 3 个 session，观察错误是否稳定，再决定是否引入类型重排。

## 复现命令

```bash
python3 work/agent_memory_experiment/llm_memory_extractor.py \
  --input work/agent_memory_experiment/data/locomo10.json \
  --output-dir work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3 \
  --max-records 1 \
  --max-sessions 1 \
  --temperature 0.1
```

```bash
python3 work/agent_memory_experiment/filter_memory_eval_slice.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3/memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3/queries.jsonl \
  --output-prefix work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1 \
  --sessions D1 \
  --require-answer
```

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HOME=work/agent_memory_experiment/cache/huggingface \
SENTENCE_TRANSFORMERS_HOME=work/agent_memory_experiment/cache/sentence_transformers \
work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1_memories.jsonl \
  --queries work/agent_memory_experiment/data/llm_extracted_locomo_1s_v3_d1_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo_1s_v3_d1_bge_m3 \
  --semantic-backend sentence-transformer \
  --embedding-model BAAI/bge-m3 \
  --embedding-batch-size 16 \
  --local-files-only \
  --rank-output-k 10 \
  --persona-boost-weight 0.04 \
  --persona-boost-query-types 1,2,3,4 \
  --importance-weight 0.06
```
