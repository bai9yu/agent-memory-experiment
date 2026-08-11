# Agent Memory Dataset Plan

This plan maps the first-stage local experiment to real public datasets.

## Recommended Order

| Stage | Dataset | Why It Fits | Suggested Use |
|---|---|---|---|
| 1 | LoCoMo | Long multi-session conversations with QA evidence and temporal categories. Small enough to debug manually. | Download `data/locomo10.json`, convert first 1-2 conversations, then run retrieval/compression. |
| 2 | LongMemEval | Long-term chat memory benchmark with knowledge updates, temporal reasoning, multi-session reasoning, abstention, and 500 questions. | Use after LoCoMo to test larger long-memory QA and temporal update behavior. |
| 3 | LongMemEval-V2 | Agentic memory setting with web/enterprise trajectories, up to 500 trajectories per haystack, and latency-sensitive retrieval. | Use for the later project stage on agent experience memory and reusable operational knowledge. |
| 4 | MTEB LoCoMo | Retrieval-formatted LoCoMo task for embedding evaluation. | Use to compare vector retrievers / embedding models without building full QA generation. |
| 5 | LongBench / LongBench v2 | General long-context benchmark, including long dialogue history and multi-document reasoning. | Use as a secondary stress test, not the primary agent-memory dataset. |

## Dataset Notes

- LoCoMo official repository: https://github.com/snap-research/locomo
- LongMemEval official repository: https://github.com/xiaowu0162/longmemeval
- LongMemEval-V2 official repository: https://github.com/xiaowu0162/LongMemEval-V2/
- MTEB LoCoMo dataset page: https://huggingface.co/datasets/mteb/LoCoMo
- LongBench official repository: https://github.com/THUDM/LongBench

## LoCoMo Manual Download Checklist

For the current project pipeline, the only required LoCoMo file is:

| Priority | File / Folder | Link | Local Target | Needed Now |
|---|---|---|---|---|
| Required | `data/locomo10.json` | https://github.com/snap-research/locomo/blob/main/data/locomo10.json | `work/agent_memory_experiment/data/locomo10.json` | Yes |
| Optional | Full repository zip | https://github.com/snap-research/locomo/archive/refs/heads/main.zip | `work/external/locomo-main.zip` | No |
| Optional | `data/msc_personas_all.json` | https://github.com/snap-research/locomo/blob/main/data/msc_personas_all.json | `work/agent_memory_experiment/data/msc_personas_all.json` | No |
| Optional | `data/multimodal_dialog/example/` | https://github.com/snap-research/locomo/tree/main/data/multimodal_dialog/example | `work/agent_memory_experiment/data/multimodal_dialog/example/` | No |
| Optional | `scripts/` | https://github.com/snap-research/locomo/tree/main/scripts | inside full repo zip | No |
| Optional | `requirements.txt` | https://github.com/snap-research/locomo/blob/main/requirements.txt | inside full repo zip | No |

Recommended action now: download only `locomo10.json`. The optional files are useful only if we want to regenerate LoCoMo conversations, observations, or session summaries with the original authors' scripts.

## LoCoMo Dataset Introduction

LoCoMo is the dataset released with the ACL 2024 work "Evaluating Very Long-Term Conversational Memory of LLM Agents." It contains ten very long-term conversations. Each sample represents one conversation with annotations for question answering and event summarization, and the dialog can also be used for multimodal dialog generation.

Important fields:

| Field | Meaning | How We Use It |
|---|---|---|
| `sample_id` | Conversation id | Run/group id |
| `conversation` | Multi-session dialogs ordered by `session_<num>` | Raw memory records |
| `session_<num>_date_time` | Session timestamp | Memory date / temporal ordering |
| `speaker_a`, `speaker_b` | Two speakers in the conversation | User/session metadata |
| `dia_id` | Dialog turn id | Evidence id mapping |
| `text` | Dialog content | Memory text |
| `img_url`, `blip_caption`, search query | Multimodal metadata when an image is present | Optional; current text-only pipeline can use caption as text |
| `observation` | Generated session observations | Optional RAG database |
| `session_summary` | Generated session-level summaries | Optional compression baseline |
| `event_summary` | Annotated significant events | Future summarization evaluation |
| `qa` | QA annotations with question, answer, category, evidence | Query/evaluation ground truth |

## How To Connect With Current Code

The existing converter is:

```bash
python3 work/agent_memory_experiment/convert_long_conversation.py \
  --input path/to/locomo10.json \
  --output-prefix work/agent_memory_experiment/data/locomo_first_10 \
  --max-records 10
```

Then evaluate:

```bash
python3 work/agent_memory_experiment/memory_eval.py \
  --memories work/agent_memory_experiment/data/locomo_first_10_memories.jsonl \
  --queries work/agent_memory_experiment/data/locomo_first_10_queries.jsonl \
  --output-dir work/agent_memory_experiment/results/locomo_first_10
```

## Practical Recommendation

Start with LoCoMo first. It is the easiest real dataset for debugging memory retrieval because it has long conversations, session structure, QA annotations, and evidence ids. After that, move to LongMemEval for a more demanding long-term memory benchmark. LongMemEval-V2 is best saved for the second stage, when the system has a clearer model of agent trajectories, source-agent trust, permission scope, and KV-cache reuse cost.
