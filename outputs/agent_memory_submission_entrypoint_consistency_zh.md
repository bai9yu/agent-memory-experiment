# Submission Entrypoint Consistency Audit

本文件检查最终投稿门禁的入口是否唯一且指向当前 artifact，避免旧的 `submission_readiness_gate` 报告与当前 `submission_readiness` 报告并存造成读者误读。

## 总览

- Checks: 9
- Failures: 0
- Entrypoints consistent: True

## 检查明细

| Check | Pass | Severity | Evidence | Action |
| --- | --- | --- | --- | --- |
| current_report_exists | True | blocker | outputs/agent_memory_submission_readiness_zh.md | Regenerate validate_submission_readiness.py with --output-report outputs/agent_memory_submission_readiness_zh.md. |
| current_csv_exists | True | blocker | outputs/agent_memory_submission_readiness.csv | Regenerate validate_submission_readiness.py with --output-csv outputs/agent_memory_submission_readiness.csv. |
| legacy_report_absent | True | major | outputs/agent_memory_submission_readiness_gate_zh.md | Remove stale legacy readiness report from tracked artifacts. |
| legacy_csv_absent | True | major | outputs/agent_memory_submission_readiness_gate.csv | Remove stale legacy readiness CSV from tracked artifacts. |
| readme_links_current_report | True | major | README.md | Update the root README paper artifact list to point to the current readiness report. |
| work_readme_links_current_report | True | major | work/agent_memory_experiment/README.md | Update the experiment README submission command and artifact list. |
| no_legacy_entrypoint_refs | True | major | no legacy references found | Replace legacy submission_readiness_gate references with submission_readiness references. |
| report_csv_blocker_count_consistent | True | blocker | report_blockers=5, csv_blockers=5 | Regenerate submission readiness report and CSV together. |
| report_required_gate_count_present | True | major | required_gates=7/12 | Ensure submission readiness report contains Required gates passed summary. |

## 论文使用边界

- 可以写：最终投稿门禁入口已统一到当前 readiness artifact。
- 不能写：该检查解除外部 embedding 或人工审计 blocker；它只处理入口一致性。
