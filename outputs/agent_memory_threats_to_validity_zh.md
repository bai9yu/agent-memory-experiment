# Threats to Validity 与论文声明边界

本附录把当前实验的有效性威胁、已有缓解措施和论文可写边界集中列出。它的作用不是美化未完成工作，而是防止论文把 LoCoMo10 范围内的检索结果过度扩展到跨数据集、端到端 agent 或生产规模结论。

## 总览

- Threat items: 8
- Submission blockers reflected here: 2
- 两个仍会阻止最终投稿的方向：外部 embedding baseline 未完成；人工错误复核标签未填写。

| Category | Threat | Current Evidence | Mitigation | Paper Claim Boundary | Status |
| --- | --- | --- | --- | --- | --- |
| internal_validity | LLM memory writer 可能产生抽取偏差或遗漏事实。 | DeepSeek writer 已有三次运行稳定性统计；正文仍限定为 LoCoMo10 范围。 | 报告 writer stability 均值/方差；保留 source evidence；后续扩展第二数据集或人工抽查 writer 输出。 | 可以说 LoCoMo10 中 fact memory 有效，不能泛化到所有长对话记忆写入场景。 | partially_mitigated |
| construct_validity | MRR/Recall@K 只衡量 memory retrieval，不等价于完整 agent task success。 | type-aware MRR=0.6093848002850233, Recall@5=0.7334058759521219; 评估对象是 query-memory retrieval。 | 在任务定义中明确 retrieval-only；后续加入 answer generation 或 downstream agent task success。 | 不能宣称端到端 agent 性能提升，只能宣称记忆检索和重排性能提升。 | bounded_claim |
| external_validity | 主实验只有 LoCoMo10 answerable slice。 | fact memories=2517, queries=1838; claim check: pass | 使用 held-out query split 和 LOCO split 检查跨 conversation 泛化；正文显式禁止跨数据集宣称。 | 可以写跨 LoCoMo conversation 泛化，不可写跨数据集泛化。 | open_until_second_dataset |
| external_validity | 外部 embedding baseline 尚未完成，BGE-M3 结果可能依赖本地 embedding 选择。 | 4/5 required checks pass; completed external embedding baselines=0; OPENAI_API_KEY is not set; summary.csv not found; completed external embedding baselines=0 | 已准备 OpenAI/default 与 generic OpenAI-compatible provider 的 preflight、estimate、run、compare 和 blocker audit。 | 外部 API embedding 对照只能写为 pending/protocol，不能写为完成结果。 | blocker |
| reliability | 错误分析仍缺人工确认，LLM-assisted 标签可能带来判断偏差。 | priority20 confirmed=0/20, invalid=0; full80 confirmed=0/80, invalid=0; priority status=pending_human_confirmation; full status=pending_human_confirmation | 已生成盲审 CSV、阅读包、双人标注表、annotation codebook、agreement/readiness gate。 | 不能宣称 human-verified error analysis；只能写人工复核流程已准备。 | blocker |
| statistical_conclusion_validity | 随机划分或单一指标可能导致偶然提升。 | 已使用 5 seeds held-out split、LOCO split、paired bootstrap CI、permutation test，并报告负结果。 | 继续保留 query-level paired tests；新增数据集后重复所有显著性检验。 | 当前统计结论限定于 LoCoMo10 answerable slice 和现有检索任务。 | mitigated_in_scope |
| scalability_validity | 100k distractor scale test 含 synthetic memory，不能代表真实生产规模。 | claim check: pass | 正文把 FAISS/LSH 大规模实验写成效率诊断；后续加入真实大规模 memory bank。 | 不能写生产规模结论，只能写 synthetic stress-test 诊断。 | bounded_claim |
| reproducibility | 多脚本、多 artifact 可能导致结果漂移或遗漏。 | 113/113 artifacts exist; 9/9 metric thresholds pass; 8/8 claim checks pass | 复现清单、artifact integrity manifest、submission readiness gate 和 claim checker 随每次结果更新重跑。 | 可以写当前 artifact 自洽；不能替代外部独立复现。 | mitigated_in_scope |

## 推荐写入论文的限制段落

本文的结论主要限定在 LoCoMo10 answerable slice 的 memory retrieval setting。虽然 held-out query split 和 leave-one-conversation-out split 均支持 intrinsic feature reranker 相比 fixed type-aware reranking 的稳定提升，但这仍不等价于跨数据集泛化或端到端 agent task success。当前主结果使用本地 BGE-M3 embedding cache，外部 API embedding baseline 尚未完成，因此不能将外部 embedding 对照写入主结果。错误分析部分已经准备 LLM-assisted draft、盲审 CSV、双人标注表和 annotation codebook，但在 priority20/full80 人工确认完成前，不能宣称 human-verified error analysis。大规模检索部分包含 synthetic distractor stress test，只能作为效率诊断，不能直接代表真实生产规模部署。

## 投稿前必须解除的声明风险

- external_validity：外部 embedding baseline 尚未完成，BGE-M3 结果可能依赖本地 embedding 选择。 -> 已准备 OpenAI/default 与 generic OpenAI-compatible provider 的 preflight、estimate、run、compare 和 blocker audit。
- reliability：错误分析仍缺人工确认，LLM-assisted 标签可能带来判断偏差。 -> 已生成盲审 CSV、阅读包、双人标注表、annotation codebook、agreement/readiness gate。

## 审稿问答准备

- 如果审稿人问为什么没有外部 embedding：回答为当前版本中该实验仍是 blocker，代码已具备 provider 接入、preflight、cache、estimate 和 compare，但未配置真实 embedding provider key，因此不写入主结果。
- 如果审稿人问错误分析是否人工验证：回答为当前仅有 LLM-assisted draft 和人工复核流程，priority20/full80 未填写前不声称 human-verified。
- 如果审稿人问是否适用于所有 agent memory：回答为当前证据支持 LoCoMo10 answerable slice 的长期对话 memory retrieval，后续需要第二数据集和端到端任务验证。
