# 实验环境快照

本文件记录复现实验所需的运行环境。它不包含任何 API key，也不读取 `.env`。

## System

| Key | Value |
|---|---|
| git_commit | `12f02e2` |
| git_branch_status | `## main...origin/main [ahead 45]` |
| python_version | `3.9.6` |
| platform | `macOS-26.5.2-arm64-arm-64bit` |
| machine | `arm64` |
| processor | `arm` |

## Python Packages

| Package | Version |
|---|---:|
| numpy | `2.0.2` |
| scikit-learn | `1.6.1` |
| scipy | `1.13.1` |
| sentence-transformers | `5.1.2` |
| transformers | `4.57.6` |
| torch | `2.8.0` |
| faiss-cpu | `1.13.0` |
| huggingface-hub | `0.36.2` |
| tokenizers | `0.22.2` |

## Local Caches

| Cache | Exists | Files | Path |
|---|---:|---:|---|
| sentence_transformers_bge_m3 | True | 31 | `work/agent_memory_experiment/cache/sentence_transformers/models--BAAI--bge-m3` |
| embedding_cache_bge_m3 | True | 27 | `work/agent_memory_experiment/cache/embeddings/sentence_transformer/BAAI_bge-m3` |
| huggingface_cache | True | 2 | `work/agent_memory_experiment/cache/huggingface` |

## Notes

- 主 LoCoMo 实验使用本地 `BAAI/bge-m3` sentence-transformer 缓存。
- 默认检索和重排实验不需要在线 embedding API。
- DeepSeek API 仅用于 memory write / fact extraction；复现已缓存检索结果不需要再次调用 API。
- `.venv`、模型缓存和 embedding 缓存不进入 Git，需要在本地按 README 准备。
