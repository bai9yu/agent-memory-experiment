# DeepSeek Memory Writer 稳定性报告

本文件汇总 DeepSeek memory writer 多次抽取实验的规模、API 用量和检索指标方差。当前只读取本地 manifest 和结果文件，不调用 API。

## 总览

- Manifest runs: 3
- Completed runs: 1
- 状态：`pending_more_runs`

## Run 明细

| Run | Status | Temp | Seed | Memories | Memory Tokens | API Tokens | MRR | R@5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run1_main | completed | 0.0 | default | 2517 | 31148 | 559574 | 0.6094 | 0.7334 |
| run2_repeat | pending | 0.2 | repeat_1 | 0 | 0 | 0 | 0.0000 | 0.0000 |
| run3_repeat | pending | 0.2 | repeat_2 | 0 | 0 | 0 | 0.0000 | 0.0000 |

## 聚合统计

| Metric | Runs | Mean | Stdev | Min | Max | Status |
| --- | --- | --- | --- | --- | --- | --- |
| num_memories | 1 | 2517.0000 | 0.0000 | 2517.0000 | 2517.0000 | pending_more_runs |
| memory_tokens | 1 | 31148.0000 | 0.0000 | 31148.0000 | 31148.0000 | pending_more_runs |
| prompt_tokens | 1 | 361103.0000 | 0.0000 | 361103.0000 | 361103.0000 | pending_more_runs |
| completion_tokens | 1 | 198471.0000 | 0.0000 | 198471.0000 | 198471.0000 | pending_more_runs |
| total_tokens | 1 | 559574.0000 | 0.0000 | 559574.0000 | 559574.0000 | pending_more_runs |
| num_queries | 1 | 1838.0000 | 0.0000 | 1838.0000 | 1838.0000 | pending_more_runs |
| recall@1 | 1 | 0.5033 | 0.0000 | 0.5033 | 0.5033 | pending_more_runs |
| recall@3 | 1 | 0.6703 | 0.0000 | 0.6703 | 0.6703 | pending_more_runs |
| recall@5 | 1 | 0.7334 | 0.0000 | 0.7334 | 0.7334 | pending_more_runs |
| mrr | 1 | 0.6094 | 0.0000 | 0.6094 | 0.6094 | pending_more_runs |

## 论文使用判断

- 当前 completed run 少于 3 个，只能说明稳定性分析框架已准备好，不能宣称 memory writer 方差已验证。
