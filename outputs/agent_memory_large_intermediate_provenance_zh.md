# Large Intermediate Provenance Audit

本文件审计较大的本地中间文件是否有清晰生成来源、README 命令和已入库的下游小报告。它用于解释为什么部分 ranked/per-query 明细保持未跟踪，而不是误以为复现包遗漏证据。

## 总览

- Audited intermediates: 6
- Major issues: 0
- Review-only items: 1
- Provenance acceptable: True

## 明细

| Path | Policy | Status | Tracked | Size Bytes | Generator | README Command | Downstream Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| outputs/agent_memory_candidate_reranker_loco_ranked_top20.csv | keep_untracked_regenerable | pass | False | 4670518 | work/agent_memory_experiment/candidate_reranker_intrinsic_loco_experiment.py | True | existing=2/2, tracked=2/2 |
| outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv | keep_untracked_regenerable | pass | False | 6737780 | work/agent_memory_experiment/candidate_reranker_experiment.py | True | existing=3/3, tracked=3/3 |
| outputs/agent_memory_set_selection_ranked.csv | keep_untracked_regenerable | pass | False | 6289166 | work/agent_memory_experiment/set_level_selection_experiment.py | True | existing=3/3, tracked=3/3 |
| outputs/agent_memory_set_selection_top20_ranked.csv | keep_untracked_regenerable | pass | False | 12717839 | work/agent_memory_experiment/set_level_selection_experiment.py | True | existing=3/3, tracked=3/3 |
| outputs/agent_memory_multi_evidence_coverage_top20_per_query.csv | optional_track_or_keep_untracked | pass | False | 857416 | work/agent_memory_experiment/multi_evidence_coverage_analysis.py | True | existing=4/4, tracked=4/4 |
| outputs/agent_memory_error_analysis_locomo10_time_aware_zh.md | review_before_tracking | review | False | 2493 | work/agent_memory_experiment/error_analysis.py | False | no tracked downstream artifact declared |

## 论文使用边界

- 可以写：大 ranked/per-query 中间文件有生成命令和下游已跟踪 summary/report 支撑，公开仓库优先保留小型可审阅 artifact。
- 应谨慎：`review_before_tracking` 项不能作为论文主证据，除非补齐正式 summary、claim boundary 和复现索引。
- 不能写：未跟踪的大中间文件已经等同于公开复现包的一部分。
