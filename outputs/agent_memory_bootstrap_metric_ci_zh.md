# Bootstrap 置信区间报告

本报告对论文中最容易被审稿人追问的 per-query 检索结果做非参数 bootstrap 置信区间。每次 bootstrap 以 query 为重采样单位，避免只报告单个点估计。

## 设置

- Bootstrap iterations: `5000`
- Random seed: `2026`
- Confidence level: `95%`
- Metrics: `MRR`、`Recall@1`、`Recall@3`、`Recall@5`

## 主要结论

- `candidate_reranker_heldout`：MRR delta=0.0539，95% CI=[0.0459, 0.0618]，CI 不跨 0，提升较稳定。
- `candidate_reranker_loco`：MRR delta=0.0504，95% CI=[0.0409, 0.0600]，CI 不跨 0，提升较稳定。
- `candidate_reranker_intrinsic_ablation_vs_type_aware`：MRR delta=0.0652，95% CI=[0.0543, 0.0759]，CI 不跨 0，提升较稳定。
- `candidate_reranker_intrinsic_ablation_vs_full`：MRR delta=0.0113，95% CI=[0.0032, 0.0199]，CI 不跨 0，提升较稳定。
- `validation_tuned_router`：MRR delta=-0.0012，95% CI=[-0.0021, -0.0004]，CI 不跨 0，但方向为下降，应作为负结果表述。
- `text_intent_router`：MRR delta=-0.0146，95% CI=[-0.0209, -0.0089]，CI 不跨 0，但方向为下降，应作为负结果表述。
- `type3_query_decomposition_fusion4`：MRR delta=-0.0867，95% CI=[-0.1360, -0.0425]，CI 不跨 0，但方向为下降，应作为负结果表述。

## 明细表

| Scenario | Metric | Baseline Mean [95% CI] | Candidate Mean [95% CI] | Delta [95% CI] | Improved/Worse/Tie |
|---|---|---:|---:|---:|---:|
| candidate_reranker_heldout | mrr | 0.6067 [0.5912, 0.6221] | 0.6606 [0.6457, 0.6750] | 0.0539 [0.0459, 0.0618] | 691/498/1571 |
| candidate_reranker_heldout | recall@1 | 0.4989 [0.4797, 0.5178] | 0.5558 [0.5373, 0.5746] | 0.0569 [0.0453, 0.0681] | 214/57/2489 |
| candidate_reranker_heldout | recall@3 | 0.6696 [0.6514, 0.6873] | 0.7322 [0.7156, 0.7486] | 0.0627 [0.0504, 0.0746] | 238/65/2457 |
| candidate_reranker_heldout | recall@5 | 0.7333 [0.7170, 0.7496] | 0.7957 [0.7801, 0.8105] | 0.0623 [0.0500, 0.0750] | 241/69/2450 |
| candidate_reranker_loco | mrr | 0.6094 [0.5907, 0.6289] | 0.6598 [0.6416, 0.6782] | 0.0504 [0.0409, 0.0600] | 447/340/1051 |
| candidate_reranker_loco | recall@1 | 0.5033 [0.4810, 0.5256] | 0.5593 [0.5370, 0.5822] | 0.0560 [0.0424, 0.0696] | 137/34/1667 |
| candidate_reranker_loco | recall@3 | 0.6703 [0.6480, 0.6915] | 0.7236 [0.7029, 0.7437] | 0.0533 [0.0381, 0.0680] | 150/52/1636 |
| candidate_reranker_loco | recall@5 | 0.7334 [0.7138, 0.7535] | 0.7856 [0.7671, 0.8047] | 0.0522 [0.0375, 0.0675] | 149/53/1636 |
| candidate_reranker_intrinsic_ablation_vs_type_aware | mrr | 0.6067 [0.5914, 0.6219] | 0.6719 [0.6570, 0.6868] | 0.0652 [0.0543, 0.0759] | 771/591/1398 |
| candidate_reranker_intrinsic_ablation_vs_type_aware | recall@1 | 0.4989 [0.4804, 0.5174] | 0.5685 [0.5504, 0.5873] | 0.0696 [0.0540, 0.0859] | 342/150/2268 |
| candidate_reranker_intrinsic_ablation_vs_type_aware | recall@3 | 0.6696 [0.6522, 0.6877] | 0.7464 [0.7297, 0.7623] | 0.0768 [0.0627, 0.0909] | 311/99/2350 |
| candidate_reranker_intrinsic_ablation_vs_type_aware | recall@5 | 0.7333 [0.7170, 0.7500] | 0.8014 [0.7866, 0.8163] | 0.0681 [0.0547, 0.0815] | 280/92/2388 |
| candidate_reranker_intrinsic_ablation_vs_full | mrr | 0.6606 [0.6459, 0.6753] | 0.6719 [0.6571, 0.6862] | 0.0113 [0.0032, 0.0199] | 502/409/1849 |
| candidate_reranker_intrinsic_ablation_vs_full | recall@1 | 0.5558 [0.5373, 0.5743] | 0.5685 [0.5500, 0.5866] | 0.0127 [0.0000, 0.0257] | 185/150/2425 |
| candidate_reranker_intrinsic_ablation_vs_full | recall@3 | 0.7322 [0.7159, 0.7486] | 0.7464 [0.7301, 0.7623] | 0.0141 [0.0018, 0.0261] | 157/118/2485 |
| candidate_reranker_intrinsic_ablation_vs_full | recall@5 | 0.7957 [0.7812, 0.8105] | 0.8014 [0.7866, 0.8163] | 0.0058 [-0.0043, 0.0159] | 113/97/2550 |
| validation_tuned_router | mrr | 0.6067 [0.5910, 0.6219] | 0.6056 [0.5898, 0.6209] | -0.0012 [-0.0021, -0.0004] | 11/18/2731 |
| validation_tuned_router | recall@1 | 0.4989 [0.4804, 0.5174] | 0.4975 [0.4790, 0.5163] | -0.0014 [-0.0029, -0.0004] | 0/4/2756 |
| validation_tuned_router | recall@3 | 0.6696 [0.6525, 0.6870] | 0.6688 [0.6514, 0.6862] | -0.0007 [-0.0022, 0.0007] | 1/3/2756 |
| validation_tuned_router | recall@5 | 0.7333 [0.7167, 0.7496] | 0.7326 [0.7159, 0.7489] | -0.0007 [-0.0018, 0.0000] | 0/2/2758 |
| text_intent_router | mrr | 0.6094 [0.5907, 0.6284] | 0.5948 [0.5757, 0.6136] | -0.0146 [-0.0209, -0.0089] | 66/151/1621 |
| text_intent_router | recall@1 | 0.5033 [0.4804, 0.5256] | 0.4886 [0.4652, 0.5114] | -0.0147 [-0.0229, -0.0065] | 15/42/1781 |
| text_intent_router | recall@3 | 0.6703 [0.6485, 0.6926] | 0.6605 [0.6387, 0.6823] | -0.0098 [-0.0185, -0.0016] | 22/40/1776 |
| text_intent_router | recall@5 | 0.7334 [0.7127, 0.7536] | 0.7155 [0.6937, 0.7361] | -0.0180 [-0.0267, -0.0098] | 15/48/1775 |
| type3_query_decomposition_fusion4 | mrr | 0.4291 [0.3407, 0.5180] | 0.3424 [0.2654, 0.4203] | -0.0867 [-0.1360, -0.0425] | 17/40/29 |
| type3_query_decomposition_fusion4 | recall@1 | 0.3256 [0.2326, 0.4302] | 0.1977 [0.1163, 0.2791] | -0.1279 [-0.1977, -0.0581] | 0/11/75 |
| type3_query_decomposition_fusion4 | recall@3 | 0.4884 [0.3837, 0.5930] | 0.4419 [0.3372, 0.5465] | -0.0465 [-0.1163, 0.0116] | 2/6/78 |
| type3_query_decomposition_fusion4 | recall@5 | 0.5465 [0.4419, 0.6512] | 0.5116 [0.4070, 0.6163] | -0.0349 [-0.0930, 0.0116] | 1/4/81 |

## 论文写法建议

- 对 `candidate_reranker_heldout` 和 `candidate_reranker_loco`，若 MRR delta 的 CI 不跨 0，可以作为主方法稳定提升证据。
- 对 CI 跨 0 的 router/decomposition 结果，应写成对照或负结果，避免包装成有效方法。
- 本报告不能替代外部 embedding baseline 或人工复核；它补强的是统计不确定性，而不是外部有效性和人工可靠性。
