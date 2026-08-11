# DeepSeek Memory Writer 稳定性报告

本文件汇总 DeepSeek memory writer 多次抽取实验的规模、API 用量和检索指标方差。当前只读取本地 manifest 和结果文件，不调用 API。

## 总览

- Manifest runs: 3
- Completed runs: 3
- 状态：`ready_for_variance`

## Run 明细

| Run | Status | Temp | Seed | Memories | Memory Tokens | API Tokens | MRR | R@5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run1_main | completed | 0.0 | default | 2517 | 31148 | 559574 | 0.6094 | 0.7334 |
| run2_repeat | completed | 0.2 | repeat_1 | 2487 | 31052 | 557657 | 0.6122 | 0.7369 |
| run3_repeat | completed | 0.2 | repeat_2 | 2517 | 31285 | 560030 | 0.6164 | 0.7448 |

## 聚合统计

| Metric | Runs | Mean | Stdev | Min | Max | Status |
| --- | --- | --- | --- | --- | --- | --- |
| num_memories | 3 | 2507.0000 | 17.3205 | 2487.0000 | 2517.0000 | ready_for_variance |
| memory_tokens | 3 | 31161.6667 | 117.0997 | 31052.0000 | 31285.0000 | ready_for_variance |
| prompt_tokens | 3 | 361103.0000 | 0.0000 | 361103.0000 | 361103.0000 | ready_for_variance |
| completion_tokens | 3 | 197984.0000 | 1259.2295 | 196554.0000 | 198927.0000 | ready_for_variance |
| total_tokens | 3 | 559087.0000 | 1259.2295 | 557657.0000 | 560030.0000 | ready_for_variance |
| num_queries | 3 | 1833.3333 | 4.1633 | 1830.0000 | 1838.0000 | ready_for_variance |
| recall@1 | 3 | 0.5055 | 0.0025 | 0.5033 | 0.5082 | ready_for_variance |
| recall@3 | 3 | 0.6762 | 0.0068 | 0.6703 | 0.6836 | ready_for_variance |
| recall@5 | 3 | 0.7384 | 0.0058 | 0.7334 | 0.7448 | ready_for_variance |
| mrr | 3 | 0.6127 | 0.0035 | 0.6094 | 0.6164 | ready_for_variance |

## 论文使用判断

- 可以报告 memory writer 的均值和标准差，作为抽取稳定性证据。
