# Retrieval Error Analysis

- Method: `time_aware`
- Queries: `1838`
- Top-1 errors: `920`
- Top-1 error rate: `0.501`

## Error Reasons

| Reason | Count | Share of Errors | Share of Queries |
|---|---:|---:|---:|
| memory_type_mismatch | 369 | 0.401 | 0.201 |
| gold_below_top20 | 248 | 0.270 | 0.135 |
| other | 76 | 0.083 | 0.041 |
| semantic_neighbor | 62 | 0.067 | 0.034 |
| temporal_neighbor | 55 | 0.060 | 0.030 |
| activity_neighbor | 34 | 0.037 | 0.018 |
| persona_confusion | 34 | 0.037 | 0.018 |
| preference_neighbor | 14 | 0.015 | 0.008 |
| relationship_neighbor | 14 | 0.015 | 0.008 |
| career_education_neighbor | 10 | 0.011 | 0.005 |
| identity_neighbor | 4 | 0.004 | 0.002 |

## Query Intents

| Intent | Count | Share of Errors | Share of Queries |
|---|---:|---:|---:|
| other | 442 | 0.480 | 0.240 |
| temporal | 153 | 0.166 | 0.083 |
| activity | 98 | 0.107 | 0.053 |
| causal_emotion | 57 | 0.062 | 0.031 |
| preference | 52 | 0.057 | 0.028 |
| location | 46 | 0.050 | 0.025 |
| relationship | 38 | 0.041 | 0.021 |
| career_education | 28 | 0.030 | 0.015 |
| identity | 6 | 0.007 | 0.003 |

## Representative Errors

- `q00003` / `career_education` / `memory_type_mismatch`: What fields would Caroline be likely to pursue in her educaton? -> `llm_00037` (emotion)
- `q00004` / `other` / `memory_type_mismatch`: What did Caroline research? -> `llm_00164` (other)
- `q00005` / `identity` / `identity_neighbor`: What is Caroline's identity? -> `llm_00124` (emotion)
- `q00007` / `temporal` / `memory_type_mismatch`: When is Melanie planning on going camping? -> `llm_00094` (family)
- `q00008` / `relationship` / `gold_below_top20`: What is Caroline's relationship status? -> `llm_00002` (identity)
- `q00014` / `career_education` / `career_education_neighbor`: What career path has Caroline decided to persue? -> `llm_00040` (goal)
- `q00016` / `activity` / `memory_type_mismatch`: What activities does Melanie partake in? -> `llm_00151` (family)
- `q00019` / `location` / `other`: Where has Melanie camped? -> `llm_00151` (family)
- `q00020` / `preference` / `preference_neighbor`: What do Melanie's kids like? -> `llm_00151` (family)
- `q00023` / `other` / `memory_type_mismatch`: Would Caroline likely have Dr. Seuss books on her bookshelf? -> `llm_00060` (hobby)
- `q00024` / `other` / `memory_type_mismatch`: What books has Melanie read? -> `llm_00151` (family)
- `q00025` / `other` / `memory_type_mismatch`: What does Melanie do to destress? -> `llm_00151` (family)
