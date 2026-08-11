# LLM Memory Extraction Report

This report summarizes fact-level memories extracted from LoCoMo sessions with DeepSeek.

## Extraction Summary

- Extracted memories: `187`
- Extracted memory tokens: `2443`
- Prompt tokens: `26930`
- Completion tokens: `15084`
- Query coverage: `0.879`
- Strict query coverage: `0.814`
- Evidence coverage: `0.848`

## Notes

- Query coverage is based on whether extracted memories cite the same LoCoMo evidence turn ids used by QA labels.
- This is a memory-write evaluation: low coverage usually means the extractor omitted a fact or cited the wrong source turn.
- The next comparison should run `memory_eval.py` on these extracted memories and compare against official `observation` memories.
