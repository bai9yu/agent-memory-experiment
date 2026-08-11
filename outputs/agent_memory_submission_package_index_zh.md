# 论文提交包索引

本文件把当前论文相关 artifact 按正文、表格、方法附录、有效性威胁、外部 embedding、人审和复现门禁组织起来。它用于内部检查和后续投稿打包，不替代真实未完成实验。

## 总览

- Indexed artifacts: 29
- Missing indexed artifacts: 0
- Blocked/not-ready sections: 2

| Section | Artifact | Exists | Status | Role | Next Action |
| --- | --- | --- | --- | --- | --- |
| Manuscript | outputs/agent_memory_manuscript_draft_zh.md | True | ready_for_internal_review | 中文正文初稿，含摘要、方法、实验、结果、Threats to Validity 和投稿前 TODO。 | 外部 embedding 与人工复核完成后重新生成正文并重跑 claim check。 |
| Main Tables | outputs/agent_memory_paper_tables_zh.md | True | ready | 论文主表、消融表、LOCO 验证表和 Type 3 负结果表的 Markdown 版本。 | 投稿前同步最终 embedding baseline 行。 |
| Main Tables | outputs/agent_memory_paper_tables.tex | True | ready | 可复制进论文的 LaTeX booktabs 表格。 | 投稿前根据目标模板微调 caption/label。 |
| Method Appendix | outputs/agent_memory_intrinsic_reranker_method_appendix_zh.md | True | ready | intrinsic feature reranker 的候选池、特征、模型、验证协议和复现命令。 | 将核心公式与特征表压缩进正文方法小节。 |
| Method Appendix | outputs/agent_memory_candidate_reranker_seed_stability_zh.md | True | ready | intrinsic candidate reranker 的 20-seed 随机划分稳定性证据。 | 投稿正文可把该结果写入 robustness/stability 小节。 |
| Method Appendix | outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md | True | ready | intrinsic candidate reranker 的 improved/worsened/tied、query type breakdown 和 paired Cohen's dz。 | 投稿正文可用该结果解释收益分布和 Type 3 边界。 |
| Method Appendix | outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md | True | ready | intrinsic candidate reranker 在 0.5/0.6/0.7/0.8 train fraction 下的敏感性分析。 | 投稿正文可用该结果回应训练比例依赖风险。 |
| Method Appendix | outputs/agent_memory_candidate_oracle_gap_analysis_zh.md | True | ready | candidate oracle 上界、主方法 gap closure 和 Type 3 剩余瓶颈分析。 | 投稿正文可用该结果解释方法上界和未来工作。 |
| Experiment Protocol | outputs/agent_memory_experiment_protocol_zh.md | True | ready | 数据切片、指标公式、显著性检验、主结果、负结果和写法边界。 | 作为 supplementary material 或实验设置附录。 |
| Evidence Matrix | outputs/agent_memory_paper_evidence_matrix_zh.md | True | ready | 论文主张、证据强度、剩余缺口和可写边界矩阵。 | 写作时逐条核对摘要/贡献是否过度宣称。 |
| Paper Tables | outputs/agent_memory_paper_table_consistency_zh.md | True | ready | 重新生成 Markdown/LaTeX 表格并与当前表格 artifact 做字节级一致性审计。 | 任何实验 CSV 或表格生成器更新后重新运行该审计。 |
| Threats to Validity | outputs/agent_memory_threats_to_validity_zh.md | True | ready_with_blockers_declared | 内部/外部/构念/统计/规模/复现有效性威胁与缓解措施。 | 外部 embedding 和人工复核完成后更新 blocker 行。 |
| Reviewer Prep | outputs/agent_memory_reviewer_response_prep_zh.md | True | ready_with_blockers_declared | 审稿人可能追问的问题、当前证据、剩余缺口和安全写作边界。 | 每次补完 blocker 或修改主张后重新生成。 |
| External Embedding | outputs/agent_memory_external_embedding_blocker_audit_zh.md | True | blocked | 外部 embedding baseline 的 key、preflight、summary 和 comparison blocker 审计。 | 配置 OPENAI_API_KEY 或 OpenAI-compatible provider key 后运行 API baseline。 |
| External Embedding | outputs/agent_memory_api_embedding_postrun_gate_zh.md | True | blocked_until_api_run | 外部 API embedding 跑后结果完整性验收，检查 summary、rankings、per-query metrics、summary_by_type 和 comparison。 | API baseline 和 compare 完成后重跑该 gate，再刷新 submission readiness。 |
| External Embedding | outputs/agent_memory_offline_embedding_sensitivity_zh.md | True | ready_diagnostic | BGE-M3、hash vector 和 BM25 keyword 的离线 encoder-sensitivity 下界诊断。 | 保留为下界诊断；投稿前仍需真实外部 API embedding baseline。 |
| Human Audit | outputs/agent_memory_human_audit_annotation_codebook_zh.md | True | ready_for_labeling | 人工复核 yes/partial/no、gold sufficiency、manual reason 和双人标注规则。 | 先填写 priority20 盲审 CSV，再扩展 full80。 |
| Human Audit | outputs/agent_memory_human_audit_execution_plan_zh.md | True | ready_for_labeling | 把 priority20、full80、双人独立标注、仲裁和论文刷新步骤拆成可执行 checklist。 | 按 execution plan 先完成 priority20 single blind labeling。 |
| Human Audit | outputs/agent_memory_human_audit_sample_qc_zh.md | True | ready_qc | 检查 priority20/full80 人工复核样本数、去重、错误类型/query type/rank 区间覆盖和标注进度。 | 人工标注前后都重跑 QC，确保样本结构和 progress 记录一致。 |
| Human Audit | outputs/agent_memory_human_audit_labeling_dashboard_zh.md | True | ready_for_labeling | 逐条列出 priority20/full80 盲审表的缺失 human_* 字段、下一批待标注样本和分布进度。 | 人工填写时按 dashboard 的 review_order 逐步完成 required human_* 字段。 |
| Human Audit | outputs/agent_memory_human_audit_priority20_review_packet_zh.md | True | ready_for_labeling | 20 条优先人工复核阅读包。 | 人工填写 blind review CSV 的 human_* 字段。 |
| Reproducibility | outputs/agent_memory_reproducibility_checklist_zh.md | True | pass | artifact、指标阈值、数据规模、复现命令和环境入口清单。 | 新增任何 artifact 后重新生成。 |
| Reproducibility | outputs/agent_memory_artifact_integrity_manifest_zh.md | True | pass | 复现 artifact sha256、大小和行数 manifest。 | 每次结果更新后重新生成。 |
| Reproducibility | outputs/agent_memory_environment_freshness_audit_zh.md | True | pass | 环境快照的 generation-time Git 状态和 system CSV 新鲜度审计。 | 提交前后若刷新环境快照，应重新运行 freshness audit。 |
| Reproducibility | outputs/agent_memory_untracked_artifact_audit_zh.md | True | ready_for_review | 未跟踪本地输出、临时数据和探索性结果的公开发布审计。 | 公开发布前逐项决定 review_before_tracking 文件是否应转为正式 artifact。 |
| Reproducibility | outputs/agent_memory_paper_artifact_refresh_run_zh.md | True | pass | 离线论文 artifact 刷新流水线的逐步执行日志。 | 补完 API baseline 或人工标签后运行该流水线收口所有报告。 |
| Reproducibility | outputs/agent_memory_paper_refresh_coverage_audit_zh.md | True | pass | 检查离线刷新流水线是否覆盖关键论文报告步骤。 | 新增关键 paper artifact 后同步更新 coverage audit 的 required steps。 |
| Submission Gate | outputs/agent_memory_submission_blocker_closure_plan_zh.md | True | ready_with_external_inputs | 外部 embedding、人审、reviewer risk 和最终一致性刷新的 blocker 关闭路线图。 | 按路线先解除 external embedding 和 human audit blockers。 |
| Submission Gate | outputs/agent_memory_submission_readiness_gate_zh.md | True | not_ready | 最终投稿门禁，聚合复现、claim check、外部 baseline、人工复核和公开发布卫生。 | 解除 external_embedding_completed、priority20/full80_human_audit 和 reviewer_risk_blockers。 |

## 最小投稿前路径

1. 运行至少一个真实外部 embedding baseline，并生成 completed comparison table。
2. 完成 priority20 人工盲审；若目标为最终投稿，继续完成 full80 双人/仲裁复核。
3. 重新生成 manuscript、paper tables、evidence matrix、threats appendix、reproducibility checklist 和 submission readiness gate。
4. 确认 submission gate 从 `ready_for_final_submission=false` 变为 true 后，再把正文和附录作为最终投稿包。
