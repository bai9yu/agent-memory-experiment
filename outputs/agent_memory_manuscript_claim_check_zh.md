# 论文声明一致性检查

本文件检查正文草稿是否把当前仍处于 pending/protocol 的实验写成已完成结论。它是论文写作阶段的安全闸门，不替代实验本身。

## 总览

- 状态：`pass`
- 检查项：8
- 失败项：0
- blocker 失败项：0

## 检查结果

| Rule | Severity | Status | Evidence | Guidance |
| --- | --- | --- | --- | --- |
| external_embedding_not_completed | blocker | pass | completed=0; no forbidden completion claim found | 保持外部 embedding baseline 为待补实验，直到 summary.csv 存在。 |
| human_audit_not_completed | blocker | pass | full_confirmed=0; no forbidden human-verified claim found | 可以写 LLM-assisted audit draft 或人工确认流程；完成后再升级声明。 |
| priority20_not_completed | major | pass | priority_confirmed=0; no forbidden quick-review completion claim found | 可以写 priority20 确认包已准备好，但不能写已完成人工一致性。 |
| cross_dataset_overclaim | major | pass | cross-dataset wording is absent or explicitly framed as a limitation | 跨数据集结论需要第二数据集或更大真实切片支撑。 |
| production_scale_overclaim | major | pass | production-scale wording is absent or explicitly framed as a limitation | 保留 synthetic/diagnostic 限定。 |
| external_embedding_caveat | minor | pass | 外部 embedding baseline completed=0 | 正文应明确包含 `外部 embedding baseline completed=0` 以提醒读者当前范围。 |
| human_audit_caveat | minor | pass | 不能宣称 human-verified error analysis | 正文应明确包含 `不能宣称 human-verified error analysis` 以提醒读者当前范围。 |
| locomo10_scope | minor | pass | LoCoMo10 answerable slice | 正文应明确包含 `LoCoMo10 answerable slice` 以提醒读者当前范围。 |
