# LoCoMo10 Query-Type Analysis

本报告基于已完成的 LoCoMo10 answerable slice 实验，按原始 LoCoMo query type 统计检索表现。
由于本地数据只保留 type 编号，以下使用 `Type 1` 到 `Type 5` 的数字标签，不强行解释语义类别。

## DeepSeek Extracted Fact Memory

| Query Type | Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|---:|
| Type 1 | hybrid | 278 | 0.335 | 0.547 | 0.601 | 0.469 |
| Type 1 | keyword | 278 | 0.241 | 0.396 | 0.471 | 0.351 |
| Type 1 | time_aware | 278 | 0.356 | 0.558 | 0.633 | 0.491 |
| Type 1 | type_aware | 278 | 0.374 | 0.561 | 0.647 | 0.504 |
| Type 1 | vector | 278 | 0.371 | 0.586 | 0.658 | 0.513 |
| Type 2 | hybrid | 310 | 0.623 | 0.774 | 0.810 | 0.710 |
| Type 2 | keyword | 310 | 0.516 | 0.674 | 0.732 | 0.615 |
| Type 2 | time_aware | 310 | 0.626 | 0.784 | 0.816 | 0.715 |
| Type 2 | type_aware | 310 | 0.632 | 0.787 | 0.826 | 0.723 |
| Type 2 | vector | 310 | 0.629 | 0.768 | 0.819 | 0.717 |
| Type 3 | hybrid | 86 | 0.256 | 0.430 | 0.512 | 0.372 |
| Type 3 | keyword | 86 | 0.174 | 0.291 | 0.326 | 0.265 |
| Type 3 | time_aware | 86 | 0.302 | 0.477 | 0.547 | 0.414 |
| Type 3 | type_aware | 86 | 0.326 | 0.488 | 0.547 | 0.429 |
| Type 3 | vector | 86 | 0.256 | 0.395 | 0.465 | 0.357 |
| Type 4 | hybrid | 752 | 0.556 | 0.714 | 0.774 | 0.657 |
| Type 4 | keyword | 752 | 0.483 | 0.632 | 0.690 | 0.577 |
| Type 4 | time_aware | 752 | 0.559 | 0.723 | 0.790 | 0.663 |
| Type 4 | type_aware | 752 | 0.557 | 0.719 | 0.794 | 0.663 |
| Type 4 | vector | 752 | 0.517 | 0.713 | 0.777 | 0.636 |
| Type 5 | hybrid | 412 | 0.364 | 0.544 | 0.612 | 0.475 |
| Type 5 | keyword | 412 | 0.442 | 0.602 | 0.633 | 0.537 |
| Type 5 | time_aware | 412 | 0.434 | 0.595 | 0.646 | 0.534 |
| Type 5 | type_aware | 412 | 0.432 | 0.604 | 0.650 | 0.534 |
| Type 5 | vector | 412 | 0.150 | 0.252 | 0.294 | 0.228 |

## Type-Aware Gain Over Time-Aware

| Query Type | Queries | Delta Recall@1 | Delta Recall@3 | Delta Recall@5 | Delta MRR |
|---|---:|---:|---:|---:|---:|
| Type 1 | 278 | 0.018 | 0.004 | 0.014 | 0.013 |
| Type 2 | 310 | 0.006 | 0.003 | 0.010 | 0.008 |
| Type 3 | 86 | 0.023 | 0.012 | 0.000 | 0.015 |
| Type 4 | 752 | -0.001 | -0.004 | 0.004 | 0.000 |
| Type 5 | 412 | -0.002 | 0.010 | 0.005 | 0.000 |

## Best Method By Query Type

| Variant | Query Type | Queries | Best Method | Recall@1 | Recall@5 | MRR |
|---|---|---:|---|---:|---:|---:|
| llm_extracted_fact | Type 1 | 278 | vector | 0.371 | 0.658 | 0.513 |
| llm_extracted_fact | Type 2 | 310 | type_aware | 0.632 | 0.826 | 0.723 |
| llm_extracted_fact | Type 3 | 86 | type_aware | 0.326 | 0.547 | 0.429 |
| llm_extracted_fact | Type 4 | 752 | type_aware | 0.557 | 0.794 | 0.663 |
| llm_extracted_fact | Type 5 | 412 | keyword | 0.442 | 0.633 | 0.537 |
| locomo_observation | Type 1 | 272 | vector | 0.408 | 0.721 | 0.546 |
| locomo_observation | Type 2 | 280 | vector | 0.693 | 0.846 | 0.764 |
| locomo_observation | Type 3 | 76 | vector | 0.276 | 0.474 | 0.385 |
| locomo_observation | Type 4 | 654 | vector | 0.589 | 0.804 | 0.683 |
| locomo_observation | Type 5 | 356 | time_aware | 0.393 | 0.570 | 0.482 |

## LoCoMo Observation Memory Reference

| Query Type | Method | Queries | Recall@1 | Recall@5 | MRR |
|---|---|---:|---:|---:|---:|
| Type 1 | hybrid | 272 | 0.309 | 0.559 | 0.438 |
| Type 1 | keyword | 272 | 0.221 | 0.441 | 0.324 |
| Type 1 | time_aware | 272 | 0.327 | 0.618 | 0.452 |
| Type 1 | type_aware | 272 | 0.327 | 0.618 | 0.452 |
| Type 1 | vector | 272 | 0.408 | 0.721 | 0.546 |
| Type 2 | hybrid | 280 | 0.618 | 0.786 | 0.696 |
| Type 2 | keyword | 280 | 0.511 | 0.711 | 0.601 |
| Type 2 | time_aware | 280 | 0.625 | 0.804 | 0.703 |
| Type 2 | type_aware | 280 | 0.625 | 0.804 | 0.703 |
| Type 2 | vector | 280 | 0.693 | 0.846 | 0.764 |
| Type 3 | hybrid | 76 | 0.237 | 0.408 | 0.329 |
| Type 3 | keyword | 76 | 0.184 | 0.316 | 0.248 |
| Type 3 | time_aware | 76 | 0.250 | 0.421 | 0.349 |
| Type 3 | type_aware | 76 | 0.250 | 0.421 | 0.349 |
| Type 3 | vector | 76 | 0.276 | 0.474 | 0.385 |
| Type 4 | hybrid | 654 | 0.547 | 0.786 | 0.655 |
| Type 4 | keyword | 654 | 0.466 | 0.683 | 0.566 |
| Type 4 | time_aware | 654 | 0.563 | 0.801 | 0.668 |
| Type 4 | type_aware | 654 | 0.563 | 0.801 | 0.668 |
| Type 4 | vector | 654 | 0.589 | 0.804 | 0.683 |
| Type 5 | hybrid | 356 | 0.362 | 0.528 | 0.445 |
| Type 5 | keyword | 356 | 0.385 | 0.565 | 0.474 |
| Type 5 | time_aware | 356 | 0.393 | 0.570 | 0.482 |
| Type 5 | type_aware | 356 | 0.393 | 0.570 | 0.482 |
| Type 5 | vector | 356 | 0.171 | 0.329 | 0.251 |

## Interpretation

- DeepSeek extracted fact memory 在 Type 2 和 Type 4 上表现最高，说明当前 fact-level memory write 与 time/type-aware reranking 对这些问题较友好。
- Type 3 是最困难类别，所有方法的 MRR 明显低于其他类型；后续应优先检查该类 query 的证据粒度、意图解析和 memory type 映射。
- `type_aware` 相比 `time_aware` 的增益主要来自 Type 1、Type 2、Type 3 和 Type 5，Type 4 基本持平；这解释了总体显著但幅度较小的原因。
- LoCoMo observation memory 在 Type 5 上弱于 DeepSeek extracted fact，说明 LLM fact extraction 对部分复杂/跨证据问题可能保留了更可检索的细节。
