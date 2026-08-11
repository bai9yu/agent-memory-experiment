# Evidence Freshness Audit

本文件检查论文面向读者的关键 artifact 是否还残留旧的复现门禁数字。它用于避免新增实验后，manuscript、evidence matrix、submission gap 等文档出现互相矛盾的 artifact/metric 数。

## 当前权威门禁

- Reproducibility artifact gate: 190/190
- Reproducibility metric gate: 22/22
- Artifact integrity gate: 190/190
- sha256 ok / self skips: 188 / 2

## 结果

- stale count findings: 0
- warnings: 0

## Stale Count Findings

- 无。关键论文文档没有发现旧的 artifact/metric/integrity 门禁数字。

## 使用边界

- 该检查只覆盖复现门禁数字的新旧一致性，不验证实验结论本身是否正确。
- 每次新增 artifact、metric 或重新生成论文文档后，都应重新运行本检查。
