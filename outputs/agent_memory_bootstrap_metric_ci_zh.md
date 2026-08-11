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
- `validation_tuned_router`：MRR delta=-0.0012，95% CI=[-0.0021, -0.0004]，CI 不跨 0，但方向为下降，应作为负结果表述。
- `text_intent_router`：MRR delta=-0.0146，95% CI=[-0.0207, -0.0089]，CI 不跨 0，但方向为下降，应作为负结果表述。
- `type3_query_decomposition_fusion4`：MRR delta=-0.0867，95% CI=[-0.1336, -0.0428]，CI 不跨 0，但方向为下降，应作为负结果表述。

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
| validation_tuned_router | mrr | 0.6067 [0.5914, 0.6219] | 0.6056 [0.5903, 0.6208] | -0.0012 [-0.0021, -0.0004] | 11/18/2731 |
| validation_tuned_router | recall@1 | 0.4989 [0.4804, 0.5174] | 0.4975 [0.4786, 0.5159] | -0.0014 [-0.0029, -0.0004] | 0/4/2756 |
| validation_tuned_router | recall@3 | 0.6696 [0.6522, 0.6877] | 0.6688 [0.6511, 0.6870] | -0.0007 [-0.0022, 0.0007] | 1/3/2756 |
| validation_tuned_router | recall@5 | 0.7333 [0.7170, 0.7500] | 0.7326 [0.7163, 0.7489] | -0.0007 [-0.0018, 0.0000] | 0/2/2758 |
| text_intent_router | mrr | 0.6094 [0.5902, 0.6288] | 0.5948 [0.5754, 0.6138] | -0.0146 [-0.0207, -0.0089] | 66/151/1621 |
| text_intent_router | recall@1 | 0.5033 [0.4804, 0.5261] | 0.4886 [0.4657, 0.5114] | -0.0147 [-0.0229, -0.0065] | 15/42/1781 |
| text_intent_router | recall@3 | 0.6703 [0.6496, 0.6921] | 0.6605 [0.6393, 0.6823] | -0.0098 [-0.0180, -0.0011] | 22/40/1776 |
| text_intent_router | recall@5 | 0.7334 [0.7133, 0.7535] | 0.7155 [0.6948, 0.7361] | -0.0180 [-0.0267, -0.0098] | 15/48/1775 |
| type3_query_decomposition_fusion4 | mrr | 0.4291 [0.3408, 0.5197] | 0.3424 [0.2687, 0.4208] | -0.0867 [-0.1336, -0.0428] | 17/40/29 |
| type3_query_decomposition_fusion4 | recall@1 | 0.3256 [0.2326, 0.4302] | 0.1977 [0.1163, 0.2791] | -0.1279 [-0.1977, -0.0581] | 0/11/75 |
| type3_query_decomposition_fusion4 | recall@3 | 0.4884 [0.3837, 0.5930] | 0.4419 [0.3372, 0.5465] | -0.0465 [-0.1163, 0.0116] | 2/6/78 |
| type3_query_decomposition_fusion4 | recall@5 | 0.5465 [0.4419, 0.6512] | 0.5116 [0.4070, 0.6163] | -0.0349 [-0.0814, 0.0116] | 1/4/81 |

## 论文写法建议

- 对 `candidate_reranker_heldout` 和 `candidate_reranker_loco`，若 MRR delta 的 CI 不跨 0，可以作为主方法稳定提升证据。
- 对 CI 跨 0 的 router/decomposition 结果，应写成对照或负结果，避免包装成有效方法。
- 本报告不能替代外部 embedding baseline 或人工复核；它补强的是统计不确定性，而不是外部有效性和人工可靠性。
