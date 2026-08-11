# Candidate Oracle Gap 与剩余上界分析

本报告把主方法、固定 baseline 与 candidate oracle 放在同一张表中，量化当前方法关闭了多少候选池上界差距，以及剩余空间更可能来自排序学习、集合选择还是候选召回。candidate oracle 不是可部署方法，只用于诊断候选池内是否存在可利用证据。

## 总览

- Held-out intrinsic MRR oracle-gap closure: 0.215；remaining gap=+0.2375。
- Held-out intrinsic Recall@5 oracle-gap closure: 0.387；remaining gap=+0.1080。
- LOCO intrinsic MRR oracle-gap closure: 0.184；remaining gap=+0.2470。
- Type 3 set selector Coverage@5 closure: -0.215；Type 3 oracle Coverage@5=0.658。
- Type 3 set selector Coverage@20 closure: -0.002；Type 3 oracle Coverage@20=0.658。

## Oracle Gap 表

| Scenario | Metric | Baseline | Candidate | Oracle | Closed Gap | Remaining Gap | Closure Rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| heldout_intrinsic | mrr | 0.607 | 0.672 | 0.909 | +0.0652 | +0.2375 | 0.215 |
| loco_intrinsic | mrr | 0.608 | 0.664 | 0.911 | +0.0556 | +0.2470 | 0.184 |
| type3_set_selector | mrr | 0.434 | 0.389 | 0.778 | -0.0449 | +0.3896 | -0.130 |
| heldout_intrinsic | recall@5 | 0.733 | 0.801 | 0.909 | +0.0681 | +0.1080 | 0.387 |
| loco_intrinsic | recall@5 | 0.732 | 0.797 | 0.911 | +0.0648 | +0.1139 | 0.363 |
| type3_set_selector | recall@5 | 0.546 | 0.481 | 0.778 | -0.0657 | +0.2976 | -0.284 |
| type3_set_coverage | coverage_ratio@5 | 0.377 | 0.317 | 0.658 | -0.0604 | +0.3413 | -0.215 |
| type3_set_coverage | full_coverage@5 | 0.230 | 0.175 | 0.524 | -0.0556 | +0.3492 | -0.189 |
| type3_set_coverage | coverage_ratio@20 | 0.526 | 0.526 | 0.658 | -0.0003 | +0.1327 | -0.002 |
| type3_set_coverage | full_coverage@20 | 0.373 | 0.357 | 0.524 | -0.0159 | +0.1667 | -0.105 |

## 解释

- `heldout_intrinsic` 和 `loco_intrinsic` 的 closure rate 为正，说明 intrinsic reranker 确实关闭了一部分 candidate-oracle 上界差距，但距离 oracle 仍有较大空间。
- Type 3 set selector 的 Coverage@5 closure 为负，说明当前 set-level 修复没有把候选池中的可用证据提前到 Top-5。
- Type 3 oracle Coverage@20 明显高于 fixed method，说明候选池中仍有可利用证据；真正瓶颈更像是多证据集合选择目标，而不是完全没有候选。
- 论文中可以把该结果写成“主方法有效但未穷尽候选池上界；Type 3 需要 listwise/setwise objective 或更强 query decomposition”。
