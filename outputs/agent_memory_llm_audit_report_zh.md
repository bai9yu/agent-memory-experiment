# LLM-assisted 错误复核初稿

本文件使用 DeepSeek 对人工复核样本生成第一版标注。它不是人工标注结果，适合作为人工复核前的预标注和一致性检查材料。

## 总览

- 样本数：80
- API 批次：16
- API total tokens：20672

## auto_reason_correct 初稿分布

| Label | Count |
|---|---:|
| yes | 28 |
| partial | 29 |
| no | 23 |

## 论文使用判断

- 可以把该文件作为人工复核加速材料或附录中的 LLM-assisted audit protocol。
- 不能把它直接写成 human audit；最终论文仍应由人工确认或至少抽样复查这些预标注。
