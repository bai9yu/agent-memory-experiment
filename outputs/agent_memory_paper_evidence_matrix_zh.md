# 论文实验证据矩阵

本文件把当前实验结果整理为“可写入论文的主张-证据-缺口”矩阵。它用于区分主结果、消融结果、负结果、效率结果和仍不能宣称的开放缺口。

## 状态汇总

| Status | Count |
|---|---:|
| ablation_result | 1 |
| baseline_protocol | 1 |
| efficiency_boundary | 1 |
| efficiency_result | 1 |
| main_method | 1 |
| main_result | 2 |
| negative_result | 2 |
| open_gap | 1 |
| reliability_protocol | 1 |
| reproducibility | 1 |
| stability_result | 1 |

## Evidence Matrix

| 状态 | 主张 | 证据 | 证据强度 | 论文写法 | 剩余缺口 |
| --- | --- | --- | --- | --- | --- |
| main_result | DeepSeek 抽取的事实级记忆在 LoCoMo10 上具备竞争力。 | DeepSeek fact + type-aware: MRR 0.609, R@5 0.733; LoCoMo observation + type-aware: MRR 0.583, R@5 0.703. Dataset slice: 1838/1986 raw queries answerable (92.5%), 10 groups, 269 sessions, multi-gold query share 46.1%. | strong_cached | 可以作为记忆形态对比主结果，但需要说明当前仍是 LoCoMo10 切片。 | 仍需在 LoCoMo10 之外补外部数据或更大真实 memory bank，才能宣称广泛泛化。 |
| main_result | 事实级记忆相比 LoCoMo observation memory 能减少存储 token。 | Fact memory tokens 31148 vs observation 40241; ratio 0.774, saving about 22.6%. | strong_cached | 可以支撑 memory compression / storage efficiency 动机。 | 需要把抽取 API 成本和检索阶段存储成本分开报告；方差可引用 writer stability report。 |
| ablation_result | type-aware 重排相比 time-aware 重排有小幅但统计可靠的提升。 | MRR 0.605 -> 0.609, delta +0.0042, p=0.0072; R@5 delta +0.0065, p=0.0028. | statistically_supported_small_effect | 可以写成一个有用但幅度有限的打分组件。 | 不要夸大 Recall@1 / Recall@3，因为它们没有通过显著性检验。 |
| main_method | Intrinsic 候选级学习重排是当前最强的方法贡献。 | Held-out type-aware MRR 0.607, R@5 0.733; full candidate reranker MRR 0.661, R@5 0.796; MRR delta +0.0539, p=0.0002; R@5 delta +0.0623, p=0.0002. Intrinsic-only reranker MRR 0.672, R@5 0.801; delta vs type-aware +0.0652, 95% CI [0.0545, 0.0763]; delta vs full +0.0113, 95% CI [0.0029, 0.0199]. 20-seed stability: positive seeds 20/20, mean MRR delta +0.0602, min MRR delta +0.0414. Train-fraction sensitivity: fractions 0.5/0.6/0.7/0.8, min win rate 1.00, min MRR delta +0.0414, mean fraction-level MRR delta +0.0608. Oracle-gap closure: held-out MRR 0.215, held-out R@5 0.387, LOCO MRR 0.184. Statistical power: full-sample MRR CI half-width 0.0109, R@5 CI half-width 0.0132. Paired outcome: MRR improved/worsened/tied 771/591/1398, Cohen dz 0.2234; R@5 improved/worsened/tied 280/92/2388; Type 3 R@5 delta -0.0476; Type 3 Coverage@5 oracle-gap closure -0.2150. LOCO split: type-aware MRR 0.608, candidate reranker MRR 0.657; weighted MRR delta +0.0504, p=0.0002; weighted R@5 delta +0.0522, p=0.0002. Intrinsic LOCO MRR 0.664, R@5 0.797; MRR delta +0.0567, 95% CI [0.0439, 0.0696]; R@5 delta +0.0658, 95% CI [0.0490, 0.0827]. | strong_heldout_and_loco_statistical | 应作为当前论文方法增量的核心结果；full reranker 保留为消融对照。 | Held-out 和 LOCO 已支持跨 LoCoMo conversation 泛化；若要宣称跨数据集泛化，仍需外部数据集验证。 |
| negative_result | Type 3 多证据问题仍是当前方法边界。 | Type 3 best method type_aware with MRR 0.429, R@5 0.547; mean gold evidence 2.651, multi-evidence share 67.5%; Type 5 multi-evidence share is only 35.4%. | strong_diagnostic | 可以作为 limitations 和下一步研究问题的主要依据。 | 需要更强的 listwise / setwise objective 或 LLM decomposition，不能宣称已解决 Type 3。 |
| negative_result | 浅层 Type 3 修复方法无法解决多证据检索。 | Supervised set selector Coverage@5 delta -0.0572, p=0.0286; Type3-specific reranker and keyword decomposition also reduce Coverage@5. | statistically_supported_negative | 适合作为边界/负结果消融，而不是作为改进方法。 | 下一步应尝试 LLM 子问题生成或真正的 setwise objective。 |
| efficiency_result | 向量候选预筛选可以在不损害质量的情况下提升检索速度。 | Sklearn exact NN top-200 + type-aware MRR 0.613, R@5 0.734; delta vs full type-aware MRR +0.0032. | strong_cached_efficiency | 可以支撑论文效率实验章节。 | 需要统一报告 wall-clock 设置，并在更大的真实 memory bank 上验证。 |
| efficiency_boundary | 100k 记忆规模下 ANN 的速度-质量权衡并非天然占优。 | 100k Flat candidate gold recall 0.952, query 0.360s; IVF nprobe=4 recall 0.737, query 0.199s. | synthetic_scale_diagnostic | 可以作为扩展性诊断，但必须标注为 synthetic distractor stress test。 | 需要真实的大规模 conversation memory bank 才能形成更强系统结论。 |
| reproducibility | 当前仓库已经具备可复现的缓存实验包。 | Reproducibility artifact gate 186/186 and metric gate 22/22. | artifact_checked | 可以用于论文 appendix 和内部复现实验。 | 全新 clone 仍需要按文档准备模型/embedding cache，因为大缓存不进入 Git。 |
| reliability_protocol | 自动错误分析已经具备人工复核入口，并已有 LLM-assisted 预标注。 | 已从 type-aware Top-1 错误中分层抽样 80 条；当前已汇总人工标注 0 条；LLM-assisted 预标注 80 条，auto_reason_correct yes/partial/no=28/29/23；Human/LLM 确认表已生成，人工确认 0 条，非法标签 0；readiness gate: priority20 0/20, full80 0/80。 | llm_assisted_protocol_ready | 可以说明已有 LLM-assisted 预复核流程；在人工确认前，不能把它写成人工验证结论。 | 需要在 confirmation CSV 中填写 human_* 字段，并重新运行一致性脚本，得到 exact agreement 与 Cohen's kappa。 |
| stability_result | DeepSeek memory writer 在 LoCoMo10 重复抽取中具有可报告的稳定性。 | 稳定性 manifest 登记 3 次抽取，目前 completed runs=3；已可报告均值和标准差。 | variance_ready | 可以作为 memory writer stability 小节；需要说明 temperature 设置和 LoCoMo10 slice 范围。 | 若投稿目标更高，需要在额外数据集或更大 LoCoMo slice 上复验。 |
| baseline_protocol | 外部 embedding baseline 已经具备 API 接入与缓存框架，但尚未形成实验结果。 | 已登记 2 个外部 embedding baseline；completed=0, ready_or_completed=0；preflight required=4/5；预计文本 4355 条、约 71882 tokens、未缓存批次 35；对比表完成=False。 | protocol_ready_pending_run | 可以作为复现实验入口；离线 hash/BM25 敏感性可写为下界诊断，但外部 API summary.csv 生成前不能写入外部 embedding 主结果表。 | 需要提供 OpenAI 或其他 OpenAI-compatible provider 的 embedding API key，并实际运行至少一个外部 embedding 对照；hash baseline 不能替代真实外部 embedding。 |
| open_gap | 完整项目距离最终投稿仍需要额外验证。 | 剩余缺口包括实际完成更强 embedding/API baseline、更大真实 memory bank 效率实验，以及人工错误复核标注结果。 | gap_analysis | 作为下一步 checklist，而不是论文主张。 | 投稿前至少补齐一个强 baseline 家族，以及一个稳定性/可靠性检查。 |

## 投稿前最低补强建议

1. 加入至少一个强 embedding/API baseline，避免结果只依赖 BGE-M3。
2. 对错误分析做人工抽样复核，报告自动错误分类的可信度。
3. Type 3 暂按负结果和边界分析书写，不应宣称已经解决多证据检索。
4. 若目标期刊/会议要求更强泛化，应在额外数据集或更大真实 memory bank 上复验 writer stability 和 candidate reranker。
