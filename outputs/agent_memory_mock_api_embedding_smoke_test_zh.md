# Mock API Embedding Smoke Test

本文件记录 API embedding backend 的离线 smoke test。测试使用 localhost mock server，不访问外网、不使用真实 API key、不产生费用。

## 结论

- Output dir: `work/agent_memory_experiment/results/api_embedding_mock_smoke_test`
- First run API requests: 6
- Second run API requests: 0
- Cache hit verified: True
- Summary has type_aware: True
- Mock type_aware MRR: 0.5650
- Mock type_aware Recall@5: 0.9000

## 运行明细

| Run | Requests | Inputs | Summary Exists | Rankings Exists |
| --- | --- | --- | --- | --- |
| 1 | 6 | 20 | True | True |
| 2 | 0 | 0 | True | True |

## 论文使用判断

- 该 smoke test 只能证明 API embedding backend、缓存和结果写入通路可运行，不能替代真实外部 embedding baseline。
- 投稿主结果仍需要真实 provider summary.csv，并与 BGE-M3 生成 delta 对比。
