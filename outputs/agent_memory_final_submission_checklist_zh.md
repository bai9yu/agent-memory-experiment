# Final Submission Checklist

本文件把最终投稿前的实验、论文、补充材料、匿名化和审稿风险动作整理成可执行 checklist。它不把未完成 blocker 包装成完成状态；只说明当前距离 final-submission candidate 还差什么。

## 总览

- Checklist items: 9
- Passed: 4/9
- Blockers: 5
- Ready for final-submission candidate: False

## Checklist

| Order | Phase | Item | Status | Evidence | Next Action |
| --- | --- | --- | --- | --- | --- |
| 1 | external_embedding | API embedding preflight | blocker | 4/5 required checks pass | 按 `agent_memory_api_embedding_execution_runbook_zh.md` 的 1_configure_key 和 2_preflight 执行；key 只放 `.env` 或 shell。 |
| 2 | external_embedding | External embedding paper-ready baseline | blocker | completed external embedding baselines=0, postrun_pass=0, paper_acceptance_pass=0; embedding_tier=pending | 按 `agent_memory_api_embedding_execution_runbook_zh.md` 执行 4_real_api_run、5_compare_with_bge_m3、6_postrun_gate 和 strict paper acceptance。 |
| 3 | human_audit | Priority20 quick human review | blocker | priority20 confirmed=0/20, invalid=0 | 按 `agent_memory_human_audit_execution_plan_zh.md` 完成 Step 1 的 priority20 blind review、merge、agreement 和 readiness 命令。 |
| 4 | human_audit | Full80 human audit | blocker | full80 confirmed=0/80, invalid=0; human_tier=pending | 按 `agent_memory_human_audit_execution_plan_zh.md` 完成 Step 3/4 的 full80 single/dual/adjudication、agreement 和 readiness。 |
| 5 | paper_claims | Manuscript claim and numeric consistency | pass | 9/9 claim checks pass; 15/15 numeric claim checks pass; scope_failures=0; numeric_failures=0 | 补完 blocker 后重新生成 manuscript、scope audit 和 numeric claim audit。 |
| 6 | reproducibility | Reproducibility, integrity, and freshness | pass | 222/222 artifacts exist; 22/22 metric thresholds pass; integrity manifest covers=222/222, sha256_ok=220, self_skips=2; stale_findings=0 | 任何实验或 artifact 变化后重跑 refresh、reproducibility、integrity 和 freshness。 |
| 7 | supplement | Supplement package manifest | pass | include_now=12, blocked=3, anonymization_findings=0, missing=0 | 关闭外部 embedding 和人审 blocker 后重新生成 supplement manifest。 |
| 8 | release | Public release and anonymization hygiene | pass | public release blockers=0; public_blockers=0; anonymous_blockers=0 | 正式匿名投稿前按会议要求移除作者、仓库 URL、账号身份信息；开源前补 LICENSE。 |
| 9 | reviewer_risk | Reviewer blocker risks closed | blocker | blocker risks=2 | 按 `agent_memory_submission_blocker_closure_plan_zh.md` 补完外部 embedding 和人审后，重跑 gap analysis/reviewer prep。 |

## 当前最短收口路线

- `API embedding preflight`：按 `agent_memory_api_embedding_execution_runbook_zh.md` 的 1_configure_key 和 2_preflight 执行；key 只放 `.env` 或 shell。
- `External embedding paper-ready baseline`：按 `agent_memory_api_embedding_execution_runbook_zh.md` 执行 4_real_api_run、5_compare_with_bge_m3、6_postrun_gate 和 strict paper acceptance。
- `Priority20 quick human review`：按 `agent_memory_human_audit_execution_plan_zh.md` 完成 Step 1 的 priority20 blind review、merge、agreement 和 readiness 命令。
- `Full80 human audit`：按 `agent_memory_human_audit_execution_plan_zh.md` 完成 Step 3/4 的 full80 single/dual/adjudication、agreement 和 readiness。
- `Reviewer blocker risks closed`：按 `agent_memory_submission_blocker_closure_plan_zh.md` 补完外部 embedding 和人审后，重跑 gap analysis/reviewer prep。

## 论文升级规则

- 外部 embedding 与 full80 人审未通过前，不应写最终投稿级强结论。
- 任何 blocker 关闭后，都要重新运行 refresh pipeline、claim checks、freshness、supplement manifest 和 submission readiness。
- checklist 全部通过后，才把 `agent_memory_manuscript_draft_zh.md` 视为 final-submission candidate 的正文基础。
