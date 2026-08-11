# Agent Memory Experiment

本仓库用于验证智能体记忆模块的第一阶段方案，包括：

- LoCoMo 真实长对话数据接入
- BGE-M3 本地 embedding 检索
- adaptive time-aware reranking
- persona gate 与 importance proxy
- observation / session_summary 真实压缩对照
- 跨智能体共享记忆的权限过滤实验

主要代码在 `work/agent_memory_experiment/`。

中文阶段文档和实验报告在 `outputs/`。

大文件没有纳入 Git：

- `work/agent_memory_experiment/cache/`：本地 BGE-M3 模型和 embedding 缓存
- `work/agent_memory_experiment/results/`：可复现实验输出
- `work/agent_memory_experiment/.venv/`：本地 Python 虚拟环境

复现步骤见 `work/agent_memory_experiment/README.md`。
