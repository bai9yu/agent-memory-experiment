# Human/LLM 错误复核一致性报告

本文件用于跟踪人工确认 LLM-assisted 错误复核初稿的进度，并在人工字段填写后统计 Human/LLM 一致性。当前报告不会把 LLM 预标注等同于人工标注。

## 状态

- 状态：`pending_human_confirmation`
- 样本数：80
- 三个人工字段均已确认的样本数：0
- 非法标签数：0

## 一致性指标

| Field | Exact Agree | Total | Exact Rate | Cohen Kappa |
| --- | --- | --- | --- | --- |
| auto_reason_correct | 0 | 0 | 0.000 |  |
| top_memory_relevant | 0 | 0 | 0.000 |  |
| gold_memory_sufficient | 0 | 0 | 0.000 |  |

## 人工标签分布

| Field | Value | Count | Share |
| --- | --- | --- | --- |
| auto_reason_correct | yes | 0 | 0.000 |
| auto_reason_correct | partial | 0 | 0.000 |
| auto_reason_correct | no | 0 | 0.000 |
| top_memory_relevant | yes | 0 | 0.000 |
| top_memory_relevant | partial | 0 | 0.000 |
| top_memory_relevant | no | 0 | 0.000 |
| gold_memory_sufficient | yes | 0 | 0.000 |
| gold_memory_sufficient | no | 0 | 0.000 |
| gold_memory_sufficient | unclear | 0 | 0.000 |

## 人工填写说明

- 在确认表中填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。
- 允许标签：`auto_reason_correct` 和 `top_memory_relevant` 使用 `yes` / `partial` / `no`；`gold_memory_sufficient` 使用 `yes` / `no` / `unclear`。
- 完成人工确认后重新运行本脚本，即可得到可写入论文的 Human/LLM 一致性统计。

## 论文使用判断

- 当前只能说明确认流程已准备好；在人工字段完成前，不能宣称错误分析已经被人工验证。
- 若时间有限，建议至少人工确认 20 条高歧义样本，再单独报告抽样一致性。
