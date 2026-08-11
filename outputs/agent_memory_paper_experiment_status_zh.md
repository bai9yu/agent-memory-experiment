# Agent Memory 论文级实验进展

## 当前已经具备的实验基础

- 真实数据：LoCoMo10 全量。
- 真实 LLM：DeepSeek `deepseek-chat`，用于 memory write / fact extraction。
- 本地 embedding：`BAAI/bge-m3`。
- 主要对照：LoCoMo 官方 `observation` memory。
- 检索方法：`vector`、`hybrid`、`time_aware`、`type_aware`。
- 中文报告：抽取、压缩、跨智能体复用、type-aware 消融均已形成文档。

## LoCoMo10 全量主结果

| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek extracted fact + type-aware | 2517 | 31148 | 1838 | 0.503 | 0.670 | 0.733 | 0.609 |
| LoCoMo observation | 2507 | 40241 | 1638 | 0.483 | 0.639 | 0.703 | 0.583 |

DeepSeek API 用量：

- Prompt tokens：361103
- Completion tokens：198471
- Total tokens：559574

Coverage：

- Query coverage：0.925
- Strict query coverage：0.870
- Evidence coverage：0.896

## Type-Aware 消融

| Type Weight | Method | Recall@1 | Recall@3 | Recall@5 | MRR |
|---:|---|---:|---:|---:|---:|
| 0.00 | time_aware | 0.499 | 0.668 | 0.727 | 0.605 |
| 0.04 | type_aware | 0.503 | 0.670 | 0.733 | 0.609 |
| 0.08 | type_aware | 0.503 | 0.669 | 0.733 | 0.609 |
| 0.12 | type_aware | 0.498 | 0.663 | 0.732 | 0.606 |

当前推荐：`w_type=0.04`。

显著性检验：

| Metric | Delta | 95% Bootstrap CI | Permutation p-value |
|---|---:|---:|---:|
| MRR | 0.004213 | [0.001214, 0.007182] | 0.0072 |
| Recall@1 | 0.003808 | [-0.001088, 0.009249] | 0.2066 |
| Recall@3 | 0.002176 | [-0.002720, 0.007073] | 0.5103 |
| Recall@5 | 0.006529 | [0.002720, 0.010881] | 0.0028 |

结论：MRR 和 Recall@5 的提升较小但通过 paired permutation test；Recall@1 / Recall@3 暂不能证明稳定提升。

## 距离论文发表级仍缺的内容

1. 重复抽取实验：至少对 LoCoMo10 做 3 次不同 seed / temperature 的 DeepSeek 抽取，报告均值和方差。
2. 更强 baseline：加入纯 BM25、OpenAI embedding 或其他主流 embedding API、本地 BGE-small / BGE-M3 对比。
3. 错误分类：系统统计 identity、relationship、activity、temporal、multi-hop 等错误类型。
4. 成本分析：报告 API 成本、memory token ratio、检索 latency、embedding cache 命中影响。
5. 跨智能体/KV cache 方向：需要把当前 synthetic cross-agent 实验替换为真实或半真实 multi-agent trace。

## 下一步建议

优先做错误分类和更强 baseline。它们不需要继续花 DeepSeek 抽取费用，却能把当前结果从“工程实验”推进到“论文实验”。
