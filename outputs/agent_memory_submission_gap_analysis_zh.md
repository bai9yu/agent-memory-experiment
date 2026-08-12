# 投稿前差距与审稿风险矩阵

本文件从审稿视角整理当前实验包的主要风险、已有证据、最低补救动作和论文当前可用措辞。它用于决定下一轮实验优先级，不把尚未完成的事项写成已完成结论。

## 总览

- Blocker：2
- Major：3
- Moderate：3

## 最小投稿前动作

- P1 `blocker`：先让 API embedding preflight 的 required checks 全部通过，再运行至少一个主流 API embedding baseline，并自动生成与 BGE-M3 的 delta 表。
- P2 `blocker`：优先填写 priority20 confirmation CSV 的 human_* 字段，先报告 quick-review exact agreement 与 Cohen's kappa；投稿前再扩展到 80 条。

## 风险矩阵

| Priority | Risk | Reviewer Question | Minimum Action | Target Artifact |
| --- | --- | --- | --- | --- |
| 1 | blocker | 是否只在单一 embedding / 单一检索编码器上有效？ | 先让 API embedding preflight 的 required checks 全部通过，再运行至少一个主流 API embedding baseline，并自动生成与 BGE-M3 的 delta 表。 | agent_memory_api_embedding_preflight_zh.md; agent_memory_embedding_baseline_comparison_zh.md |
| 2 | blocker | 错误分析是否经过人工确认？ | 优先填写 priority20 confirmation CSV 的 human_* 字段，先报告 quick-review exact agreement 与 Cohen's kappa；投稿前再扩展到 80 条。 | agent_memory_human_audit_readiness_gate_zh.md; agent_memory_human_llm_audit_priority20_agreement_zh.md; agent_memory_human_llm_audit_agreement_zh.md |
| 3 | major | LoCoMo10 slice 是否足以支撑泛化结论？ | 扩大 LoCoMo slice 或加入第二个长对话/agent memory 数据集；若时间有限，论文标题和结论限制在系统性实证研究。 | agent_memory_paper_draft_outline_zh.md |
| 4 | major | 候选级重排是否真的跨 conversation 泛化？ | 在方法和实验设置中突出 leave-one-conversation-out split，并保留 paired permutation test。 | agent_memory_candidate_reranker_loco_zh.md |
| 5 | major | Type 3 多证据失败是否削弱方法贡献？ | 把 Type 3 写成系统边界和未来工作，避免把浅层修复方法包装为有效贡献。 | agent_memory_type3_coverage_significance_zh.md |
| 6 | moderate | 效率实验是否只反映小规模缓存条件？ | 统一报告硬件、wall-clock 设置、候选数和 synthetic distractor 限制；更高目标再补真实大规模 memory bank。 | agent_memory_sklearn_nn_prefilter_locomo10_zh.md |
| 7 | moderate | memory writer 的随机性是否影响主结论？ | 在实验设置中报告 3-run mean/std，并说明仍是 LoCoMo10 范围内稳定性。 | agent_memory_writer_stability_zh.md |
| 8 | moderate | 复现实验是否足够完整？ | 在 appendix 写清楚数据准备、模型缓存、API key 不入库、重型结果由 CSV 缓存复现。 | agent_memory_reproducibility_checklist_zh.md |

## 论文写作边界

### P1 是否只在单一 embedding / 单一检索编码器上有效？

- 风险等级：`blocker`
- 当前证据：外部 embedding baseline completed=0, ready_or_completed=0；API embedding preflight required=4/5。
- 重要性：没有强外部 embedding 对照时，审稿人可能认为提升来自 BGE-M3 或缓存设置，而不是记忆/重排方法本身。
- 当前可写：只能说 API baseline 接口已经准备好，不能把它写入主结果。
- 最小动作：先让 API embedding preflight 的 required checks 全部通过，再运行至少一个主流 API embedding baseline，并自动生成与 BGE-M3 的 delta 表。
- 目标 artifact：`agent_memory_api_embedding_preflight_zh.md; agent_memory_embedding_baseline_comparison_zh.md`
- 依赖：`needs_api_key`

### P2 错误分析是否经过人工确认？

- 风险等级：`blocker`
- 当前证据：Human/LLM 确认表 80 条，人工确认 0 条，非法标签 0；priority20 快速抽查包 20 条，agreement confirmed=0；readiness gate priority20=0/20, full80=0/80。
- 重要性：自动错误类型如果没有人工或一致性证据，只能作为诊断脚本输出，难以支撑论文中的错误分析结论。
- 当前可写：可以写 LLM-assisted audit draft 和人工确认流程，不能写 human-verified error analysis。
- 最小动作：优先填写 priority20 confirmation CSV 的 human_* 字段，先报告 quick-review exact agreement 与 Cohen's kappa；投稿前再扩展到 80 条。
- 目标 artifact：`agent_memory_human_audit_readiness_gate_zh.md; agent_memory_human_llm_audit_priority20_agreement_zh.md; agent_memory_human_llm_audit_agreement_zh.md`
- 依赖：`needs_human_labels`

### P3 LoCoMo10 slice 是否足以支撑泛化结论？

- 风险等级：`major`
- 当前证据：DeepSeek fact + type-aware: MRR 0.609, R@5 0.733; LoCoMo observation + type-aware: MRR 0.583, R@5 0.703. Dataset slice: 1838/1986 raw queries answerable (92.5%), 10 groups, 269 sessions, multi-gold query share 46.1%.
- 重要性：当前主结果强，但数据范围仍是 LoCoMo10 answerable slice；过度宣称会被质疑外部有效性。
- 当前可写：可以写 LoCoMo10 上有效，不能写一般智能体记忆场景均有效。
- 最小动作：扩大 LoCoMo slice 或加入第二个长对话/agent memory 数据集；若时间有限，论文标题和结论限制在系统性实证研究。
- 目标 artifact：`agent_memory_paper_draft_outline_zh.md`
- 依赖：`experiment_design`

### P4 候选级重排是否真的跨 conversation 泛化？

- 风险等级：`major`
- 当前证据：Held-out type-aware MRR 0.607, R@5 0.733; full candidate reranker MRR 0.661, R@5 0.796; MRR delta +0.0539, p=0.0002; R@5 delta +0.0623, p=0.0002. Intrinsic-only reranker MRR 0.672, R@5 0.801; delta vs type-aware +0.0652, 95% CI [0.0545, 0.0763]; delta vs full +0.0113, 95% CI [0.0029, 0.0199]. 20-seed stability: positive seeds 20/20, mean MRR delta +0.0602, min MRR delta +0.0414. Train-fraction sensitivity: fractions 0.5/0.6/0.7/0.8, min win rate 1.00, min MRR delta +0.0414, mean fraction-level MRR delta +0.0608. Oracle-gap closure: held-out MRR 0.215, held-out R@5 0.387, LOCO MRR 0.184. Statistical power: full-sample MRR CI half-width 0.0109, R@5 CI half-width 0.0132. Paired outcome: MRR improved/worsened/tied 771/591/1398, Cohen dz 0.2234; R@5 improved/worsened/tied 280/92/2388; Type 3 R@5 delta -0.0476; Type 3 Coverage@5 oracle-gap closure -0.2150. LOCO split: type-aware MRR 0.608, candidate reranker MRR 0.657; weighted MRR delta +0.0504, p=0.0002; weighted R@5 delta +0.0522, p=0.0002. Intrinsic LOCO MRR 0.664, R@5 0.797; MRR delta +0.0567, 95% CI [0.0439, 0.0696]; R@5 delta +0.0658, 95% CI [0.0490, 0.0827].
- 重要性：学习式方法容易被质疑过拟合；LOCO 已缓解该风险，但仍应把 split 设置写清楚。
- 当前可写：可以作为核心方法贡献，但需要避免跨数据集泛化措辞。
- 最小动作：在方法和实验设置中突出 leave-one-conversation-out split，并保留 paired permutation test。
- 目标 artifact：`agent_memory_candidate_reranker_loco_zh.md`
- 依赖：`paper_writing`

### P5 Type 3 多证据失败是否削弱方法贡献？

- 风险等级：`major`
- 当前证据：Type 3 best method type_aware with MRR 0.429, R@5 0.547; mean gold evidence 2.651, multi-evidence share 67.5%; Type 5 multi-evidence share is only 35.4%.
- 重要性：如果不主动承认边界，审稿人会把 Type 3 失败视作方法缺陷；主动报告负结果反而能提升可信度。
- 当前可写：可以写负结果、边界分析和后续 setwise/listwise 方向。
- 最小动作：把 Type 3 写成系统边界和未来工作，避免把浅层修复方法包装为有效贡献。
- 目标 artifact：`agent_memory_type3_coverage_significance_zh.md`
- 依赖：`paper_writing`

### P6 效率实验是否只反映小规模缓存条件？

- 风险等级：`moderate`
- 当前证据：Sklearn exact NN top-200 + type-aware MRR 0.613, R@5 0.734; delta vs full type-aware MRR +0.0032.
- 重要性：当前 exact NN 和 synthetic 100k 诊断有价值，但真实大规模 memory bank 证据仍不足。
- 当前可写：可以写效率诊断，不能写真实生产规模结论。
- 最小动作：统一报告硬件、wall-clock 设置、候选数和 synthetic distractor 限制；更高目标再补真实大规模 memory bank。
- 目标 artifact：`agent_memory_sklearn_nn_prefilter_locomo10_zh.md`
- 依赖：`paper_writing`

### P7 memory writer 的随机性是否影响主结论？

- 风险等级：`moderate`
- 当前证据：稳定性 manifest 登记 3 次抽取，目前 completed runs=3；已可报告均值和标准差。
- 重要性：LLM 写记忆天然有随机性；已有 3 次稳定性结果，但需要在论文中说明范围和温度设置。
- 当前可写：可以写 LoCoMo10 重复抽取稳定，不宜写跨模型稳定。
- 最小动作：在实验设置中报告 3-run mean/std，并说明仍是 LoCoMo10 范围内稳定性。
- 目标 artifact：`agent_memory_writer_stability_zh.md`
- 依赖：`paper_writing`

### P8 复现实验是否足够完整？

- 风险等级：`moderate`
- 当前证据：当前复现清单 artifact gate 206/206，metric gate 22/22。
- 重要性：复现清单完整能降低审稿人对工程实验的疑虑，但大模型输出和 embedding cache 不能全部进 Git。
- 当前可写：可以写 artifact-checked reproducibility package。
- 最小动作：在 appendix 写清楚数据准备、模型缓存、API key 不入库、重型结果由 CSV 缓存复现。
- 目标 artifact：`agent_memory_reproducibility_checklist_zh.md`
- 依赖：`paper_writing`

## 优先级建议

- 先补 blocker：外部 embedding baseline 与 Human/LLM 人工确认。这两项直接决定论文能否从“完整实验包”进入“可投稿实验”。
- 再补 major：泛化措辞、LOCO split 说明和 Type 3 负结果写法。这些更多影响审稿观感和论证边界。
- Moderate 项主要靠论文写法和 appendix 补足；不用阻塞下一轮核心实验。
