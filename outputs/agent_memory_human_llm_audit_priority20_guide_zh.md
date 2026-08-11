# Human/LLM 优先人工抽查包

本文件从 80 条 Human/LLM 确认样本中选出 20 条优先人工抽查样本。目标是先用较小标注成本检查 LLM-assisted 预标注和自动错误分类是否可靠；它不能替代完整 80 条人工确认。

## 抽样原则

- 优先选择 LLM 认为 `auto_reason_correct=no/partial` 的样本。
- 优先选择 `gold_memory_sufficient=no/unclear`、Top memory 不相关、persona/relationship/temporal/other 等高歧义类型。
- 保留部分 `yes` 样本作为 sanity check，避免只看困难样本。
- 抽样结果写入 id 文件后，可以复用 `confirm_llm_audit_labels.py --audit-id-csv` 生成独立一致性报告。

## 分布

| Auto Reason | Count |
| --- | --- |
| activity_neighbor | 1 |
| career_education_neighbor | 3 |
| gold_below_top20 | 3 |
| identity_neighbor | 1 |
| memory_type_mismatch | 4 |
| other | 4 |
| relationship_neighbor | 1 |
| temporal_neighbor | 3 |

| LLM auto_reason_correct | Count |
| --- | --- |
| no | 13 |
| partial | 4 |
| yes | 3 |

## 样本列表

| Audit ID | Query ID | Type | Auto Reason | LLM Label | Score | Selection Reason |
| --- | --- | --- | --- | --- | --- | --- |
| audit_002 | q01430 | 1 | activity_neighbor | partial | 9 | LLM 认为自动错误类型只有部分正确; Top memory 只有部分相关; gold evidence 充分性存疑; gold evidence 未进入 Top-5 |
| audit_006 | q00028 | 3 | career_education_neighbor | partial | 10 | LLM 认为自动错误类型只有部分正确; Top memory 只有部分相关; gold evidence 充分性存疑; 覆盖 Type 3 多证据问题 |
| audit_007 | q00442 | 4 | career_education_neighbor | no | 8 | LLM 认为自动错误类型不正确; Top memory 被判为不相关 |
| audit_009 | q00889 | 4 | career_education_neighbor | no | 9 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 未进入 Top-5 |
| audit_010 | q00183 | 5 | gold_below_top20 | no | 10 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 排名较低 |
| audit_019 | q01169 | 2 | gold_below_top20 | yes | 9 | Top memory 被判为不相关; gold evidence 充分性存疑; gold evidence 排名较低 |
| audit_020 | q01345 | 5 | gold_below_top20 | yes | 9 | Top memory 被判为不相关; gold evidence 充分性存疑; gold evidence 排名较低 |
| audit_025 | q00970 | 5 | identity_neighbor | yes | 8 | Top memory 被判为不相关; gold evidence 充分性存疑; gold evidence 未进入 Top-5 |
| audit_031 | q00459 | 5 | memory_type_mismatch | no | 10 | LLM 认为自动错误类型不正确; Top memory 只有部分相关; gold evidence 充分性存疑 |
| audit_034 | q00645 | 4 | memory_type_mismatch | no | 11 | LLM 认为自动错误类型不正确; Top memory 只有部分相关; gold evidence 充分性存疑; gold evidence 未进入 Top-5 |
| audit_040 | q01164 | 3 | memory_type_mismatch | partial | 11 | LLM 认为自动错误类型只有部分正确; Top memory 只有部分相关; gold evidence 充分性存疑; 覆盖 Type 3 多证据问题; gold evidence 未进入 Top-5 |
| audit_045 | q01756 | 5 | memory_type_mismatch | no | 12 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 充分性存疑 |
| audit_050 | q00715 | 5 | other | no | 9 | LLM 认为自动错误类型不正确; Top memory 只有部分相关; 覆盖高歧义错误类型 other; gold evidence 未进入 Top-5 |
| audit_051 | q01147 | 5 | other | no | 14 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 充分性存疑; 覆盖高歧义错误类型 other |
| audit_055 | q01576 | 5 | other | no | 15 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 充分性存疑; 覆盖高歧义错误类型 other; gold evidence 未进入 Top-5 |
| audit_056 | q01803 | 1 | other | no | 9 | LLM 认为自动错误类型不正确; Top memory 只有部分相关; 覆盖高歧义错误类型 other; gold evidence 未进入 Top-5 |
| audit_069 | q01772 | 5 | relationship_neighbor | no | 10 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; 覆盖高歧义错误类型 relationship_neighbor |
| audit_075 | q00133 | 4 | temporal_neighbor | no | 15 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; gold evidence 充分性存疑; 覆盖高歧义错误类型 temporal_neighbor; gold evidence 未进入 Top-5 |
| audit_076 | q00520 | 2 | temporal_neighbor | partial | 10 | LLM 认为自动错误类型只有部分正确; Top memory 只有部分相关; gold evidence 充分性存疑; 覆盖高歧义错误类型 temporal_neighbor |
| audit_077 | q00555 | 2 | temporal_neighbor | no | 11 | LLM 认为自动错误类型不正确; Top memory 被判为不相关; 覆盖高歧义错误类型 temporal_neighbor; gold evidence 未进入 Top-5 |

## 人工填写指南

- 打开 `outputs/agent_memory_human_llm_audit_priority20_confirmation.csv`。
- 只填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。
- 完成后重新运行 priority20 agreement 命令，得到 quick-review exact agreement 和 Cohen's kappa。
- 论文中可写为抽样人工确认；若要写完整 human audit，仍需填写 80 条确认表。
