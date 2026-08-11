# Submission Readiness Gate

本文件把当前论文实验包的关键门禁统一成一张可复现检查表。它不会把未完成实验包装成已完成结论；只要仍有 blocker，就说明当前不应作为最终投稿版本。

## 总览

- Ready for final submission: False
- Required gates passed: 7/12
- Blockers: 5
- Optional pending: 0

## Gate 明细

| Gate | Category | Required | Pass | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| reproducibility_artifacts | reproducibility | True | True | pass | 200/200 artifacts exist |
| reproducibility_metrics | reproducibility | True | True | pass | 22/22 metric thresholds pass |
| manuscript_claim_check | paper_writing | True | True | pass | 8/8 claim checks pass |
| manuscript_numeric_claim_check | paper_writing | True | True | pass | 15/15 numeric claim checks pass |
| api_embedding_preflight | external_baseline | True | False | blocker | 4/5 required checks pass |
| mock_api_embedding_smoke_test | external_baseline | False | True | pass | second_run_requests=0, summary_exists=True |
| external_embedding_completed | external_baseline | True | False | blocker | completed external embedding baselines=0, postrun_pass=0 |
| human_audit_sample_qc | reliability | True | True | pass | sample QC rows=73, blocking failures=0 |
| priority20_human_audit | reliability | True | False | blocker | priority20 confirmed=0/20, invalid=0 |
| full80_human_audit | reliability | True | False | blocker | full80 confirmed=0/80, invalid=0 |
| reviewer_risk_blockers | submission | True | False | blocker | blocker risks=2 |
| public_release_hygiene | submission | True | True | pass | public release blockers=0 |
| artifact_integrity_manifest | reproducibility | True | True | pass | integrity manifest covers=200/200, sha256_ok=198, self_skips=2 |

## 当前 Blocker

- `api_embedding_preflight`：配置 OPENAI_API_KEY 或等价外部 embedding provider key 后重跑 preflight。
- `external_embedding_completed`：实际运行至少一个外部 embedding baseline，并生成与 BGE-M3 的 delta 表。
- `priority20_human_audit`：填写 priority20 盲审表 human_* 字段，回填 confirmation 后重算 agreement。
- `full80_human_audit`：投稿前完成 80 条人工确认并报告 exact agreement 与 Cohen's kappa。
- `reviewer_risk_blockers`：优先补齐外部 embedding baseline 和人工复核标签。

## 论文使用判断

- 当前仍可用于组会、开题/中期汇报或内部复现实验；在 blocker 解决前，不建议作为最终投稿稿。
