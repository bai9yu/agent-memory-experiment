# Memory Writer 成本边界报告

本报告把 LLM memory write 的一次性 API token 成本，与后续检索阶段可复用的 memory storage token 分开。它用于避免把“存储 token 节省”误写成“没有抽取成本”。

## 总览

- 一次性 memory-write API tokens：`559574`，其中 prompt `361103`，completion `198471`。
- 存储后的 fact memory tokens：`31148`。
- 对照 LoCoMo observation memory tokens：`40241`。
- fact memory 相比 observation memory 的存储节省：`22.6%`。
- 一次性写入 token / fact 存储 token：`17.97x`。
- 仅从 token 数看，若每次检索都需要扫描/携带完整 memory，约 `61.5` 次复用后，累计存储 token 节省可抵消一次性写入 token；该值不是货币成本模型。

## 明细

| Item | Value | Unit | Scope | Paper Boundary |
|---|---:|---|---|---|
| memory_write_api_tokens | 559574 | tokens | 269 DeepSeek memory-write sessions | one_time_generation_cost_not_online_retrieval_storage |
| memory_write_prompt_tokens | 361103 | tokens | DeepSeek memory writer input | report_separately_from_stored_memory_tokens |
| memory_write_completion_tokens | 198471 | tokens | DeepSeek memory writer output | report_separately_from_stored_memory_tokens |
| fact_memory_storage_tokens | 31148 | tokens | 2517 fact memories, avg=12.38 | reused_by_downstream_retrieval_runs |
| observation_memory_storage_tokens | 40241 | tokens | 2507 LoCoMo observation memories, avg=16.05 | comparison_storage_baseline |
| fact_vs_observation_storage_ratio | 0.774036 | ratio | fact tokens / observation tokens | storage_efficiency_claim |
| fact_vs_observation_storage_saving | 0.225964 | ratio | 1 - storage ratio | storage_efficiency_claim |
| write_tokens_per_fact_storage_token | 17.965006 | ratio | one-time API tokens / stored fact-memory tokens | do_not_describe_storage_saving_as_free_extraction |
| storage_break_even_reuses | 61.538986 | retrieval_passes | one-time API tokens / per-pass storage-token saving | token_only_diagnostic_not_monetary_cost_model |
| writer_stability_mrr | 0.6126705729766935 | mean | completed_runs=3, stdev=0.0035468451339777636 | supports_stability_but_not_human_faithfulness |
| writer_stability_recall5 | 0.738371394146766 | mean | completed_runs=3, stdev=0.0058421793607673755 | supports_stability_but_not_human_faithfulness |

## 可写入论文的边界

- 可以写：fact-level memory 在检索阶段的存储 token 低于 LoCoMo observation memory，并在当前 LoCoMo10 slice 上保持更高检索指标。
- 可以写：memory writer 有一次性 API token 成本，后续检索复用的是已写入的短 fact memory。
- 应谨慎：`storage_break_even_reuses` 只是 token 口径诊断，不等同于真实费用、延迟或能耗 break-even。
- 不能写：事实级记忆压缩没有成本；也不能在人工复核前宣称所有抽取事实完全忠实。

## Writer 稳定性引用

- MRR mean=`0.613`，completed_runs=3, stdev=0.0035468451339777636。
- Recall@5 mean=`0.738`，completed_runs=3, stdev=0.0058421793607673755。
