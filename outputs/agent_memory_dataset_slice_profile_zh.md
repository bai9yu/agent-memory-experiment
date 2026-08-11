# LoCoMo 数据集切片画像

本报告描述当前论文实验使用的 LoCoMo10 数据范围、answerable slice 比例、query type 分布、gold evidence 数量和 memory bank 结构。它用于支撑论文的数据集小节，并明确哪些结论只适用于当前 slice。

## 总览

| Variant | Memories | Queries | Raw Query Count | Answerable Share | Groups | Sessions | Agents | Mean Gold/query | Multi-gold Share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw_turn_full | 5882 | 1986 | 1986 | 100.0% | 10 | 272 | 18 | 1.417 | 21.3% |
| llm_extracted_fact_answerable | 2517 | 1838 | 1986 | 92.5% | 10 | 269 | 65 | 1.943 | 46.1% |
| locomo_observation_answerable | 2507 | 1638 | 1986 | 82.5% | 10 | 269 | 18 | 1.498 | 27.5% |

## 当前主实验切片

- 主实验使用 `llm_extracted_fact_answerable`：2517 条 fact memories，1838 条 answerable queries。
- 相比 raw LoCoMo query 数 1986，answerable 覆盖率为 92.5%。
- 覆盖 group/conversation 数：10；session 数：269；agent 数：65。
- 平均 gold memory 数：1.943；多 gold query 占比：46.1%。
- Memory 时间范围：2022-01-21 到 2024-01-12；Query 时间范围：2022-01-21 到 2024-01-12。

## Observation 对照切片

- `locomo_observation_answerable` 含 2507 条 observation memories 和 1638 条 answerable queries。
- observation memory 数约为 LLM fact memory 的 0.996 倍。
- 两个 answerable slice 的 query 数差异为 200，论文中不应把二者视为完全相同的标注空间。

## llm_extracted_fact_answerable 分布

### query_type

| Value | Count | Share |
| --- | --- | --- |
| 4 | 752 | 40.9% |
| 5 | 412 | 22.4% |
| 2 | 310 | 16.9% |
| 1 | 278 | 15.1% |
| 3 | 86 | 4.7% |

### gold_count

| Value | Count | Share |
| --- | --- | --- |
| 1 | 991 | 53.9% |
| 2 | 476 | 25.9% |
| 3 | 183 | 10.0% |
| 4 | 71 | 3.9% |
| 5 | 50 | 2.7% |
| 7 | 21 | 1.1% |
| 6 | 19 | 1.0% |
| 8 | 10 | 0.5% |
| 9 | 5 | 0.3% |
| 11 | 4 | 0.2% |
| 12 | 3 | 0.2% |
| 17 | 2 | 0.1% |

### memory_type

| Value | Count | Share |
| --- | --- | --- |
| event | 589 | 23.4% |
| preference | 361 | 14.3% |
| hobby | 324 | 12.9% |
| plan | 317 | 12.6% |
| goal | 211 | 8.4% |
| emotion | 151 | 6.0% |
| work | 141 | 5.6% |
| relationship | 133 | 5.3% |
| family | 120 | 4.8% |
| health | 53 | 2.1% |
| other | 44 | 1.7% |
| identity | 42 | 1.7% |

## raw_turn_full 分布

### query_type

| Value | Count | Share |
| --- | --- | --- |
| 4 | 841 | 42.3% |
| 5 | 446 | 22.5% |
| 2 | 321 | 16.2% |
| 1 | 282 | 14.2% |
| 3 | 96 | 4.8% |

### gold_count

| Value | Count | Share |
| --- | --- | --- |
| 1 | 1563 | 78.7% |
| 2 | 241 | 12.1% |
| 3 | 81 | 4.1% |
| 4 | 58 | 2.9% |
| 5 | 20 | 1.0% |
| 6 | 8 | 0.4% |
| 7 | 5 | 0.3% |
| 9 | 2 | 0.1% |
| 8 | 2 | 0.1% |
| 10 | 2 | 0.1% |
| 11 | 2 | 0.1% |
| 19 | 1 | 0.1% |

### memory_type

| Value | Count | Share |
| --- | --- | --- |
| raw_turn | 5882 | 100.0% |

## locomo_observation_answerable 分布

### query_type

| Value | Count | Share |
| --- | --- | --- |
| 4 | 654 | 39.9% |
| 5 | 356 | 21.7% |
| 2 | 280 | 17.1% |
| 1 | 272 | 16.6% |
| 3 | 76 | 4.6% |

### gold_count

| Value | Count | Share |
| --- | --- | --- |
| 1 | 1188 | 72.5% |
| 2 | 282 | 17.2% |
| 3 | 83 | 5.1% |
| 4 | 54 | 3.3% |
| 5 | 9 | 0.5% |
| 7 | 6 | 0.4% |
| 6 | 5 | 0.3% |
| 9 | 3 | 0.2% |
| 11 | 3 | 0.2% |
| 8 | 2 | 0.1% |
| 12 | 1 | 0.1% |
| 17 | 1 | 0.1% |

### memory_type

| Value | Count | Share |
| --- | --- | --- |
| raw_turn | 2507 | 100.0% |

## 论文写法边界

- 可以写：当前主结果覆盖 LoCoMo10 中可映射到 LLM fact memory 的 answerable slice，且保留了多 query type、多个 conversation/group、跨 session 的时间跨度。
- 应谨慎：answerable slice 不是 LoCoMo 所有原始问题；无法映射到 fact memory 的问题会被排除，因此外部有效性仍需更多数据集或更大 slice 验证。
- 不能写：当前结果已经代表所有长对话智能体记忆任务，或已经完成跨数据集泛化。
