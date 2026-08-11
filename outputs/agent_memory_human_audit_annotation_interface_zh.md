# Human Audit Annotation Interface

本文件记录已生成的离线人工标注界面。HTML 文件内嵌盲审样本，只展示人工判断需要的信息，不展示 LLM-assisted 预标注标签；标注者填写后可直接导出 CSV。

## 总览

| Split | Samples | Completed | Pending | HTML | Source CSV |
|---|---:|---:|---:|---|---|
| priority20 | 20 | 0 | 20 | `outputs/agent_memory_human_audit_priority20_annotation.html` | `outputs/agent_memory_human_audit_priority20_blind_review.csv` |
| full80 | 80 | 0 | 80 | `outputs/agent_memory_human_audit_full80_annotation.html` | `outputs/agent_memory_human_audit_full80_blind_review.csv` |

## 使用边界

- 可以写：人工审计已有离线标注界面、盲审 CSV 和 codebook，标注流程可复现。
- 不能写：HTML 生成完成就等于人工审计完成；最终仍以 exported CSV 回填后的 agreement/readiness gate 为准。
