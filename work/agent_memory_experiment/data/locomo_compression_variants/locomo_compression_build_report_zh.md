# LoCoMo 真实压缩数据构建报告

本文档记录从 LoCoMo 原始字段构建 `observation` 与 `session_summary` 两种真实压缩记忆的结果。

## 存储规模

| Variant | Memories | Total Tokens | Avg Tokens/Memory | Token Ratio vs Raw |
|---|---:|---:|---:|---:|
| observation | 2541 | 40822 | 16.07 | 0.281 |
| session_summary | 272 | 29252 | 107.54 | 0.201 |

## Evidence 覆盖率

| Variant | Queries | Full Query Coverage | Partial Query Coverage | Unmapped Queries | Evidence Coverage |
|---|---:|---:|---:|---:|---:|
| observation | 1986 | 0.741 | 0.090 | 336 | 0.785 |
| session_summary | 1986 | 0.993 | 0.002 | 9 | 0.997 |

## 评测口径

- `observation` 使用严格 evidence 映射：只有 observation fact 明确引用的 `Dsession:turn` 才会成为 gold memory。
- `session_summary` 把同一 session 的所有 turn 映射到该 session summary，因此覆盖率通常更高，但检索粒度更粗。
- 如果压缩版本没有覆盖某个 QA 的 evidence，该 query 在该版本中会自然记为无法召回；这能反映压缩是否丢失事实。
