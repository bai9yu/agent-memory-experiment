# Human Audit Paper-Claim Upgrade Gate

本文件把人工审计从“协议已准备”到“可写入论文的人工可靠性证据”分成多个门槛。它不会自动填写人工标签，也不会把 LLM-assisted 预标注当成人工结果。

## 总览

- Claim tiers: 6
- Passed tiers: 1/6
- Highest unlocked tier: `protocol_only`

## 门槛明细

| Tier | Status | Evidence | Allowed Paper Claim | Next Action |
| --- | --- | --- | --- | --- |
| protocol_only | pass | annotation interface and import readiness artifacts are tracked in the reproducibility package | 可以写：已准备 human-confirmation protocol、blind review sheets 和回填验收脚本。 | 填写 priority20 single-blind human_* 字段。 |
| priority20_quick_review | pending | priority20 confirmed=0/20, invalid=0; agreement confirmed=0/20 | 可以写：priority20 quick-review Human/LLM agreement，并把它作为小样本人工抽查。 | 完成 full80 single-blind labels；若追求更强证据，再完成 priority20 dual A/B。 |
| priority20_dual_review | pending | priority20 A/B both_labeled=0/20, adjudicated=0/20, invalid=0 | 可以写：priority20 inter-annotator agreement，作为错误分析标注可靠性的快速证据。 | 扩展 full80 single-blind 或 full80 dual labels。 |
| full80_single_review | pending | full80 confirmed=0/80, invalid=0; agreement confirmed=0/80 | 可以写：full80 Human/LLM error-audit agreement，支撑完整人工确认的错误分析。 | 完成 full80 dual A/B labels 或在论文中明确 single-review limitation。 |
| full80_dual_review | pending | full80 A/B both_labeled=0/80, adjudicated=0/80, invalid=0 | 可以写：full80 inter-annotator agreement，并报告 exact agreement 与 Cohen's kappa。 | 对 A/B 冲突样本填写 adjudicated_* 字段。 |
| human_verified_ready | pending | full80 adjudicated=0/80, invalid=0 | 可以写：human-verified error analysis，并以 adjudicated labels 作为论文错误类型分布。 | 刷新 gap analysis、reviewer response、manuscript、claim checks 和 submission readiness。 |

## 使用边界

- 可以把本报告作为人工标注后的验收入口，决定论文中能升级到哪一种表述。
- 在 `priority20_quick_review` 之前，只能写 protocol-ready，不能写人工一致性结果。
- 在 `full80_single_review` 之前，不建议把错误分析写成完整 human-confirmed evidence。
- 只有 `human_verified_ready` 通过后，才适合写强版本的 human-verified error analysis。
