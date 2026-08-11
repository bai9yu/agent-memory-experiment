# 论文提交包索引

本文件把当前论文相关 artifact 按正文、表格、方法附录、有效性威胁、外部 embedding、人审和复现门禁组织起来。它用于内部检查和后续投稿打包，不替代真实未完成实验。

## 总览

- Indexed artifacts: 17
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
| Experiment Protocol | outputs/agent_memory_experiment_protocol_zh.md | True | ready | 数据切片、指标公式、显著性检验、主结果、负结果和写法边界。 | 作为 supplementary material 或实验设置附录。 |
| Evidence Matrix | outputs/agent_memory_paper_evidence_matrix_zh.md | True | ready | 论文主张、证据强度、剩余缺口和可写边界矩阵。 | 写作时逐条核对摘要/贡献是否过度宣称。 |
| Threats to Validity | outputs/agent_memory_threats_to_validity_zh.md | True | ready_with_blockers_declared | 内部/外部/构念/统计/规模/复现有效性威胁与缓解措施。 | 外部 embedding 和人工复核完成后更新 blocker 行。 |
| Reviewer Prep | outputs/agent_memory_reviewer_response_prep_zh.md | True | ready_with_blockers_declared | 审稿人可能追问的问题、当前证据、剩余缺口和安全写作边界。 | 每次补完 blocker 或修改主张后重新生成。 |
| External Embedding | outputs/agent_memory_external_embedding_blocker_audit_zh.md | True | blocked | 外部 embedding baseline 的 key、preflight、summary 和 comparison blocker 审计。 | 配置 OPENAI_API_KEY 或 OpenAI-compatible provider key 后运行 API baseline。 |
| Human Audit | outputs/agent_memory_human_audit_annotation_codebook_zh.md | True | ready_for_labeling | 人工复核 yes/partial/no、gold sufficiency、manual reason 和双人标注规则。 | 先填写 priority20 盲审 CSV，再扩展 full80。 |
| Human Audit | outputs/agent_memory_human_audit_priority20_review_packet_zh.md | True | ready_for_labeling | 20 条优先人工复核阅读包。 | 人工填写 blind review CSV 的 human_* 字段。 |
| Reproducibility | outputs/agent_memory_reproducibility_checklist_zh.md | True | pass | artifact、指标阈值、数据规模、复现命令和环境入口清单。 | 新增任何 artifact 后重新生成。 |
| Reproducibility | outputs/agent_memory_artifact_integrity_manifest_zh.md | True | pass | 复现 artifact sha256、大小和行数 manifest。 | 每次结果更新后重新生成。 |
| Submission Gate | outputs/agent_memory_submission_readiness_gate_zh.md | True | not_ready | 最终投稿门禁，聚合复现、claim check、外部 baseline、人工复核和公开发布卫生。 | 解除 external_embedding_completed、priority20/full80_human_audit 和 reviewer_risk_blockers。 |

## 最小投稿前路径

1. 运行至少一个真实外部 embedding baseline，并生成 completed comparison table。
2. 完成 priority20 人工盲审；若目标为最终投稿，继续完成 full80 双人/仲裁复核。
3. 重新生成 manuscript、paper tables、evidence matrix、threats appendix、reproducibility checklist 和 submission readiness gate。
4. 确认 submission gate 从 `ready_for_final_submission=false` 变为 true 后，再把正文和附录作为最终投稿包。
