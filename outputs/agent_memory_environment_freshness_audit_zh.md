# Environment Snapshot Freshness Audit

本文件检查环境快照是否对应当前实验源状态。由于环境快照被提交后，最终提交号会天然比生成时的 HEAD 晚一个提交，所以 commit/branch 匹配项标为 advisory；真正的 required gate 是环境 system CSV 存在且字段可读。

## 总览

- Required failures: 0
- Advisory mismatches: 0
- System CSV: `outputs/agent_memory_environment_system.csv`

## 检查项

| Check | Pass | Severity | Observed | Expected |
| --- | --- | --- | --- | --- |
| snapshot_system_csv_exists | True | required | outputs/agent_memory_environment_system.csv | existing environment system CSV |
| git_commit_matches_generation_head | True | advisory_after_commit | 9b1903e | 9b1903e |
| git_branch_status_matches_generation_status | True | advisory_after_commit | ## main...origin/main | ## main...origin/main |
| commits_since_snapshot_generation | True | advisory_after_commit | 0 | 0 during generation; 1 is normal after committing the refreshed snapshot |

## 论文使用边界

- 可以写：环境快照记录了生成报告时的 Python/package/cache/Git source state。
- 应谨慎：提交后的 Git commit 可能比快照中的 generation commit 晚一个提交。
- 不能写：环境快照中的 commit 必然等于包含该快照文件的最终 commit。
