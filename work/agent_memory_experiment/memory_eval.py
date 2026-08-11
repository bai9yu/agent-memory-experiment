#!/usr/bin/env python3
"""Run a small, reproducible agent-memory retrieval experiment.

The script intentionally uses only Python standard-library modules so the first
phase can run before installing larger frameworks such as mem0 or MemoryOS.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
RECENCY_QUERY_RE = re.compile(
    r"\b(recent|recently|latest|last|yesterday|today|currently|now|since|new|newest)\b",
    re.IGNORECASE,
)
WHEN_QUERY_RE = re.compile(r"\b(when|date|time)\b", re.IGNORECASE)
PERSONA_ALIASES = {
    "mel": "melanie",
}
IMPORTANCE_HIGH_RE = re.compile(
    r"\b(identity|transgender|support group|career|counsel|mental health|relationship|friends|family|mentor|"
    r"adoption|kids|children|goal|dream|plan|planning|decided|decision|realized|learned|important|special|"
    r"prefer|favorite|love|value|birthday|anniversary|conference|class|job|work|study|education|school)\b",
    re.IGNORECASE,
)
IMPORTANCE_EMOTION_RE = re.compile(
    r"\b(happy|sad|proud|thankful|grateful|excited|scared|nervous|inspired|powerful|rewarding|tough|"
    r"accepted|supportive|love|hate|hope|fear|amazing|awesome|meaningful)\b",
    re.IGNORECASE,
)
IMPORTANCE_LOW_RE = re.compile(
    r"\b(hey|hello|hi|thanks|thank you|great chatting|talk to you|see you|wow|cool|awesome|sounds great|"
    r"good to see|how are you|what's up)\b",
    re.IGNORECASE,
)
QUERY_INTENT_TYPE_PATTERNS = (
    (
        re.compile(r"\b(identity|identify|transgender|who is|who was)\b", re.IGNORECASE),
        {"identity": 1.0, "profile": 0.8, "emotion": 0.3},
    ),
    (
        re.compile(r"\b(relationship|status|married|husband|wife|partner|single|dating)\b", re.IGNORECASE),
        {"relationship": 1.0, "family": 0.7, "identity": 0.4},
    ),
    (
        re.compile(r"\b(career|field|fields|pursue|education|educaton|study|school|class|job|work)\b", re.IGNORECASE),
        {"goal": 1.0, "plan": 0.9, "education": 0.9, "work": 0.8, "event": 0.3},
    ),
    (
        re.compile(r"\b(activity|activities|hobby|hobbies|instrument|play|playing|run|running|race|camp|camping|swim|swimming|music|paint|painting)\b", re.IGNORECASE),
        {"hobby": 1.0, "event": 0.8, "plan": 0.7, "preference": 0.7, "emotion": 0.2},
    ),
    (
        re.compile(r"\b(when|date|time|how long|last|yesterday|today|summer)\b", re.IGNORECASE),
        {"event": 0.9, "plan": 0.9, "work": 0.3, "education": 0.3},
    ),
    (
        re.compile(r"\b(where|move|moved|from|place|location)\b", re.IGNORECASE),
        {"event": 0.8, "profile": 0.7, "plan": 0.3},
    ),
    (
        re.compile(r"\b(like|likes|enjoy|favorite|prefer|love|value)\b", re.IGNORECASE),
        {"preference": 1.0, "hobby": 0.8, "emotion": 0.5, "event": 0.2},
    ),
    (
        re.compile(r"\b(kid|kids|child|children|family|parent|adoption|adopt)\b", re.IGNORECASE),
        {"family": 1.0, "relationship": 0.8, "plan": 0.6, "goal": 0.4},
    ),
    (
        re.compile(r"\b(feel|feels|realize|realized|learn|learned|support|supported|negative experience)\b", re.IGNORECASE),
        {"emotion": 1.0, "event": 0.5, "relationship": 0.4},
    ),
)


@dataclass(frozen=True)
class Memory:
    id: str
    session_id: str
    turn: int
    date: datetime
    agent_id: str
    user_id: str
    text: str
    entities: tuple[str, ...]
    memory_type: str = "unknown"


@dataclass(frozen=True)
class Query:
    id: str
    query: str
    answer_memory_ids: tuple[str, ...]
    query_date: datetime
    type: str


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_memories(path: Path) -> list[Memory]:
    memories = []
    for row in load_jsonl(path):
        memories.append(
            Memory(
                id=row["id"],
                session_id=row["session_id"],
                turn=int(row["turn"]),
                date=parse_date(row["date"]),
                agent_id=row["agent_id"],
                user_id=row["user_id"],
                text=row["text"],
                entities=tuple(row.get("entities", [])),
                memory_type=str(row.get("memory_type", "unknown")).lower(),
            )
        )
    return memories


def load_queries(path: Path) -> list[Query]:
    queries = []
    for row in load_jsonl(path):
        queries.append(
            Query(
                id=row["id"],
                query=row["query"],
                answer_memory_ids=tuple(row["answer_memory_ids"]),
                query_date=parse_date(row["query_date"]),
                type=row.get("type", "unknown"),
            )
        )
    return queries


def cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b.get(k, 0.0) for k in a)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def hashed_vector(tokens: Iterable[str], dims: int = 384) -> Counter[str]:
    """Tiny deterministic embedding approximation for offline experiments."""
    vec: Counter[str] = Counter()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = 1 if digest[4] % 2 == 0 else -1
        vec[str(idx)] += sign
    return vec


def safe_cache_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def embedding_cache_key(kind: str, model_name: str, items: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    digest.update(kind.encode("utf-8"))
    digest.update(b"\n")
    digest.update(model_name.encode("utf-8"))
    for item_id, text in items:
        digest.update(b"\n")
        digest.update(item_id.encode("utf-8"))
        digest.update(b"\t")
        digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def dense_cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticScorer(Protocol):
    name: str

    def score(self, query: Query, memories: list[Memory]) -> dict[str, float]:
        ...


class HashSemanticScorer:
    name = "hash"

    def __init__(self, memories: list[Memory]):
        self.memory_vectors = {
            memory.id: hashed_vector(tokenize(memory.text))
            for memory in memories
        }

    def score(self, query: Query, memories: list[Memory]) -> dict[str, float]:
        query_vec = hashed_vector(tokenize(query.query))
        return {
            memory.id: cosine(query_vec, self.memory_vectors[memory.id])
            for memory in memories
        }


class SentenceTransformerSemanticScorer:
    name = "sentence-transformer"

    def __init__(
        self,
        memories: list[Memory],
        model_name: str,
        local_files_only: bool,
        batch_size: int,
        cache_dir: Path | None,
    ):
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install it, then rerun with "
                "`--semantic-backend sentence-transformer`."
            ) from exc

        self.np = np
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, local_files_only=local_files_only)
        self.batch_size = max(batch_size, 1)
        self.cache_dir = cache_dir
        self.memory_ids = [memory.id for memory in memories]
        self.memory_vectors = self.encode_with_cache(
            "memories",
            [(memory.id, memory.text) for memory in memories],
        )
        self.query_vectors: dict[str, object] = {}

    def cache_path(self, kind: str, items: list[tuple[str, str]]) -> Path | None:
        if self.cache_dir is None:
            return None
        key = embedding_cache_key(kind, self.model_name, items)
        return self.cache_dir / "sentence_transformer" / safe_cache_name(self.model_name) / f"{kind}_{key}.npz"

    def encode_with_cache(self, kind: str, items: list[tuple[str, str]]):
        cache_path = self.cache_path(kind, items)
        if cache_path and cache_path.exists():
            try:
                data = self.np.load(cache_path, allow_pickle=False)
                ids = [str(item) for item in data["ids"].tolist()]
                vectors = data["vectors"].astype("float32")
                if ids == [item_id for item_id, _ in items] and vectors.shape[0] == len(items):
                    return vectors
            except (OSError, ValueError, KeyError):
                pass

        vectors = self.model.encode(
            [text for _, text in items],
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
            batch_size=self.batch_size,
        ).astype("float32")
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.np.savez_compressed(
                cache_path,
                ids=self.np.array([item_id for item_id, _ in items]),
                vectors=vectors,
            )
        return vectors

    def prepare_queries(self, queries: list[Query]) -> None:
        vectors = self.encode_with_cache(
            "queries",
            [(query.id, query.query) for query in queries],
        )
        self.query_vectors = {
            query.id: vector
            for query, vector in zip(queries, vectors)
        }

    def score(self, query: Query, memories: list[Memory]) -> dict[str, float]:
        if query.id in self.query_vectors:
            query_vector = self.query_vectors[query.id]
        else:
            query_vector = self.model.encode(
                [query.query],
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
                batch_size=self.batch_size,
            )[0].astype("float32")
        scores = (self.memory_vectors * query_vector).sum(axis=1)
        return {
            memory_id: float(score)
            for memory_id, score in zip(self.memory_ids, scores)
        }


def build_semantic_scorer(args: argparse.Namespace, memories: list[Memory]) -> SemanticScorer:
    if args.semantic_backend == "hash":
        return HashSemanticScorer(memories)
    if args.semantic_backend == "sentence-transformer":
        cache_dir = None if args.no_embedding_cache else args.embedding_cache_dir
        return SentenceTransformerSemanticScorer(
            memories,
            args.embedding_model,
            args.local_files_only,
            args.embedding_batch_size,
            cache_dir,
        )
    raise ValueError(f"Unknown semantic backend: {args.semantic_backend}")


def build_idf(memories: list[Memory]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for memory in memories:
        df.update(set(tokenize(memory.text)))
    n_docs = len(memories)
    return {term: math.log((n_docs - count + 0.5) / (count + 0.5) + 1.0) for term, count in df.items()}


def build_memory_tokens(memories: list[Memory]) -> dict[str, list[str]]:
    return {memory.id: tokenize(memory.text) for memory in memories}


def build_importance_scores(memories: list[Memory]) -> dict[str, float]:
    return {memory.id: importance_score(memory) for memory in memories}


def bm25_score(query_tokens: list[str], memory_tokens: list[str], idf: dict[str, float], avg_len: float) -> float:
    k1 = 1.5
    b = 0.75
    tf = Counter(memory_tokens)
    doc_len = max(len(memory_tokens), 1)
    score = 0.0
    for term in query_tokens:
        freq = tf.get(term, 0)
        if freq == 0:
            continue
        denom = freq + k1 * (1 - b + b * doc_len / max(avg_len, 1e-9))
        score += idf.get(term, 0.0) * (freq * (k1 + 1)) / denom
    return score


def normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    max_value = max(values.values())
    if max_value <= 0:
        return {key: 0.0 for key in values}
    return {key: value / max_value for key, value in values.items()}


def time_decay(memory_date: datetime, query_date: datetime, half_life_days: float) -> float:
    age_days = max((query_date - memory_date).days, 0)
    return 0.5 ** (age_days / half_life_days)


def recency_gate(query: Query) -> float:
    if WHEN_QUERY_RE.search(query.query):
        return 0.0
    return 1.0 if RECENCY_QUERY_RE.search(query.query) else 0.0


def known_personas(memories: list[Memory]) -> set[str]:
    return {memory.agent_id.lower() for memory in memories if memory.agent_id}


def query_personas(query: Query, personas: set[str]) -> set[str]:
    tokens = {token.lower() for token in TOKEN_RE.findall(query.query)}
    expanded = set(tokens)
    for token in tokens:
        if token in PERSONA_ALIASES:
            expanded.add(PERSONA_ALIASES[token])
    return expanded & personas


def parse_query_types(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def persona_weight_for_query(query: Query, weight: float, query_types: set[str]) -> float:
    if weight == 0:
        return 0.0
    if query_types and query.type not in query_types:
        return 0.0
    return weight


def persona_score(memory: Memory, query_persona_names: set[str]) -> float:
    if not query_persona_names:
        return 0.0
    memory_text = memory.text.lower()
    memory_speaker = memory.agent_id.lower()
    if memory_speaker in query_persona_names:
        return 1.0
    if any(persona in memory_text for persona in query_persona_names):
        return 0.7
    return -0.5


def importance_score(memory: Memory) -> float:
    text = memory.text
    tokens = tokenize(text)
    score = 0.0
    if IMPORTANCE_HIGH_RE.search(text):
        score += 0.55
    if IMPORTANCE_EMOTION_RE.search(text):
        score += 0.25
    if len(tokens) >= 18:
        score += 0.15
    if len(memory.entities) >= 2:
        score += 0.10
    if IMPORTANCE_LOW_RE.search(text) and len(tokens) <= 18:
        score -= 0.30
    return max(0.0, min(score, 1.0))


def query_intent_type_weights(query: Query) -> dict[str, float]:
    weights: dict[str, float] = {}
    for pattern, pattern_weights in QUERY_INTENT_TYPE_PATTERNS:
        if pattern.search(query.query):
            for memory_type, weight in pattern_weights.items():
                weights[memory_type] = max(weights.get(memory_type, 0.0), weight)
    return weights


def memory_type_score(memory: Memory, query_type_weights: dict[str, float]) -> float:
    if not query_type_weights:
        return 0.0
    return query_type_weights.get(memory.memory_type, 0.0)


def entity_overlap(query_tokens: set[str], entities: tuple[str, ...]) -> float:
    entity_tokens = set()
    for entity in entities:
        entity_tokens.update(tokenize(entity))
    if not entity_tokens:
        return 0.0
    return len(query_tokens & entity_tokens) / len(entity_tokens)


def rank_memories(
    query: Query,
    memories: list[Memory],
    method: str,
    idf: dict[str, float],
    memory_tokens: dict[str, list[str]],
    avg_len: float,
    half_life_days: float,
    semantic_scorer: SemanticScorer,
    personas: set[str],
    persona_boost_weight: float,
    persona_boost_query_types: set[str],
    importance_weight: float,
    memory_importance: dict[str, float],
    type_awareness_weight: float,
) -> list[dict]:
    query_tokens = tokenize(query.query)
    query_token_set = set(query_tokens)
    query_recency_gate = recency_gate(query)
    query_persona_names = query_personas(query, personas)
    query_persona_weight = persona_weight_for_query(query, persona_boost_weight, persona_boost_query_types)
    query_type_weights = query_intent_type_weights(query)

    semantic_scores = semantic_scorer.score(query, memories)
    bm25_scores = {
        memory.id: bm25_score(query_tokens, memory_tokens[memory.id], idf, avg_len)
        for memory in memories
    }
    bm25_norm = normalize(bm25_scores)

    rows = []
    for memory in memories:
        semantic = semantic_scores[memory.id]
        keyword = bm25_norm[memory.id]
        entity = entity_overlap(query_token_set, memory.entities)
        decay = time_decay(memory.date, query.query_date, half_life_days)
        persona = persona_score(memory, query_persona_names)
        importance = memory_importance[memory.id]
        type_match = memory_type_score(memory, query_type_weights)

        if method == "vector":
            final = semantic
        elif method == "hybrid":
            final = 0.65 * semantic + 0.30 * keyword + 0.05 * entity
        elif method in {"time_aware", "type_aware"}:
            final = (
                0.70 * semantic
                + 0.30 * keyword
                + 0.08 * query_recency_gate * decay
                + query_persona_weight * persona
                + importance_weight * importance
            )
            if method == "type_aware":
                final += type_awareness_weight * type_match
        else:
            raise ValueError(f"Unknown method: {method}")

        rows.append(
            {
                "query_id": query.id,
                "query": query.query,
                "query_type": query.type,
                "method": method,
                "memory_id": memory.id,
                "memory_text": memory.text,
                "memory_type": memory.memory_type,
                "final_score": final,
                "semantic_score": semantic,
                "keyword_score": keyword,
                "entity_score": entity,
                "time_decay": decay,
                "recency_gate": query_recency_gate,
                "persona_score": persona,
                "importance_score": importance,
                "memory_type_score": type_match,
                "semantic_backend": semantic_scorer.name,
                "is_relevant": memory.id in query.answer_memory_ids,
            }
        )
    return sorted(rows, key=lambda row: row["final_score"], reverse=True)


def rank_all_methods(
    query: Query,
    memories: list[Memory],
    methods: tuple[str, ...],
    idf: dict[str, float],
    memory_tokens: dict[str, list[str]],
    avg_len: float,
    half_life_days: float,
    semantic_scorer: SemanticScorer,
    personas: set[str],
    persona_boost_weight: float,
    persona_boost_query_types: set[str],
    importance_weight: float,
    memory_importance: dict[str, float],
    type_awareness_weight: float,
) -> dict[str, list[dict]]:
    query_tokens = tokenize(query.query)
    query_token_set = set(query_tokens)
    relevant_ids = set(query.answer_memory_ids)
    query_recency_gate = recency_gate(query)
    query_persona_names = query_personas(query, personas)
    query_persona_weight = persona_weight_for_query(query, persona_boost_weight, persona_boost_query_types)
    query_type_weights = query_intent_type_weights(query)

    semantic_scores = semantic_scorer.score(query, memories)
    bm25_scores = {
        memory.id: bm25_score(query_tokens, memory_tokens[memory.id], idf, avg_len)
        for memory in memories
    }
    bm25_norm = normalize(bm25_scores)

    base_rows = []
    for memory in memories:
        memory_id = memory.id
        base_rows.append({
            "query_id": query.id,
            "query": query.query,
            "query_type": query.type,
            "memory_id": memory_id,
            "memory_text": memory.text,
            "memory_type": memory.memory_type,
            "semantic_score": semantic_scores[memory_id],
            "keyword_score": bm25_norm[memory_id],
            "entity_score": entity_overlap(query_token_set, memory.entities),
            "time_decay": time_decay(memory.date, query.query_date, half_life_days),
            "recency_gate": query_recency_gate,
            "persona_score": persona_score(memory, query_persona_names),
            "persona_weight": query_persona_weight,
            "importance_score": memory_importance[memory_id],
            "memory_type_score": memory_type_score(memory, query_type_weights),
            "semantic_backend": semantic_scorer.name,
            "is_relevant": memory_id in relevant_ids,
        })

    ranked_by_method = {}
    for method in methods:
        rows = []
        for base_row in base_rows:
            semantic = base_row["semantic_score"]
            keyword = base_row["keyword_score"]
            entity = base_row["entity_score"]
            decay = base_row["time_decay"]

            if method == "vector":
                final = semantic
            elif method == "hybrid":
                final = 0.65 * semantic + 0.30 * keyword + 0.05 * entity
            elif method in {"time_aware", "type_aware"}:
                final = (
                    0.70 * semantic
                    + 0.30 * keyword
                    + 0.08 * base_row["recency_gate"] * decay
                    + base_row["persona_weight"] * base_row["persona_score"]
                    + importance_weight * base_row["importance_score"]
                )
                if method == "type_aware":
                    final += type_awareness_weight * base_row["memory_type_score"]
            else:
                raise ValueError(f"Unknown method: {method}")

            row = dict(base_row)
            row["method"] = method
            row["final_score"] = final
            rows.append(row)
        ranked_by_method[method] = sorted(rows, key=lambda row: row["final_score"], reverse=True)
    return ranked_by_method


def evaluate_rankings(rankings: dict[tuple[str, str], list[dict]], queries: list[Query], k_values: tuple[int, ...]) -> list[dict]:
    return aggregate_metrics(per_query_metrics(rankings, queries, k_values), k_values, group_key=None)


def per_query_metrics(rankings: dict[tuple[str, str], list[dict]], queries: list[Query], k_values: tuple[int, ...]) -> list[dict]:
    methods = sorted({method for _, method in rankings})
    by_query = {query.id: query for query in queries}
    rows = []
    for method in methods:
        for query in queries:
            ranked = rankings[(query.id, method)]
            relevant = set(by_query[query.id].answer_memory_ids)
            top_ids = [row["memory_id"] for row in ranked]
            first_rank = None
            for rank, memory_id in enumerate(top_ids, start=1):
                if memory_id in relevant:
                    first_rank = rank
                    break
            item = {
                "query_id": query.id,
                "query_type": query.type,
                "method": method,
                "mrr": 0.0 if first_rank is None else 1.0 / first_rank,
                "first_rank": first_rank or 0,
            }
            for k in k_values:
                item[f"recall@{k}"] = 1.0 if relevant & set(top_ids[:k]) else 0.0
            rows.append(item)
    return rows


def metrics_for_ranked(query: Query, method: str, ranked: list[dict], k_values: tuple[int, ...]) -> dict:
    relevant = set(query.answer_memory_ids)
    first_rank = None
    top_k_limit = max(k_values)
    top_ids_for_recall = [row["memory_id"] for row in ranked[:top_k_limit]]
    for rank, row in enumerate(ranked, start=1):
        if row["memory_id"] in relevant:
            first_rank = rank
            break
    item = {
        "query_id": query.id,
        "query_type": query.type,
        "method": method,
        "mrr": 0.0 if first_rank is None else 1.0 / first_rank,
        "first_rank": first_rank or 0,
    }
    for k in k_values:
        item[f"recall@{k}"] = 1.0 if relevant & set(top_ids_for_recall[:k]) else 0.0
    return item


def aggregate_metrics(rows: list[dict], k_values: tuple[int, ...], group_key: str | None) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        key = (row["method"], row[group_key]) if group_key else (row["method"],)
        groups[key].append(row)

    summary = []
    for key in sorted(groups):
        method_rows = groups[key]
        aggregate = {
            "method": key[0],
            "num_queries": len(method_rows),
            "mrr": statistics.mean(row["mrr"] for row in method_rows),
        }
        if group_key:
            aggregate[group_key] = key[1]
        for k in k_values:
            aggregate[f"recall@{k}"] = statistics.mean(row[f"recall@{k}"] for row in method_rows)
        summary.append(aggregate)
    return summary


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    summary: list[dict],
    type_summary: list[dict],
    top_rows: list[dict],
    duration_seconds: float,
    num_memories: int,
    num_queries: int,
    max_top_details: int = 90,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Agent Memory Experiment Report",
        "",
        f"Memories: {num_memories}",
        f"Queries: {num_queries}",
        f"Runtime seconds: {duration_seconds:.4f}",
        "",
        "## Metrics",
        "",
        "| Method | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method']} | {row['recall@1']:.3f} | {row['recall@3']:.3f} | {row['recall@5']:.3f} | {row['mrr']:.3f} |"
        )

    lines.extend([
        "",
        "## Metrics By Query Type",
        "",
        "| Type | Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in type_summary:
        lines.append(
            f"| {row['query_type']} | {row['method']} | {row['recall@1']:.3f} | {row['recall@3']:.3f} | "
            f"{row['recall@5']:.3f} | {row['mrr']:.3f} | {row['num_queries']} |"
        )

    lines.extend(["", "## Top-1 Details", ""])
    shown_rows = top_rows[:max_top_details]
    for row in shown_rows:
        mark = "OK" if row["is_relevant"] else "MISS"
        lines.append(
            f"- {mark} `{row['method']}` / `{row['query_id']}` / `{row['query_type']}` -> `{row['memory_id']}` "
            f"(score={row['final_score']:.3f})"
        )
    if len(top_rows) > len(shown_rows):
        lines.append("")
        lines.append(f"Showing first {len(shown_rows)} top-1 rows out of {len(top_rows)}. See `rankings.csv` for full details.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    started = time.perf_counter()
    memories = load_memories(args.memories)
    queries = load_queries(args.queries)
    idf = build_idf(memories)
    memory_tokens = build_memory_tokens(memories)
    memory_importance = build_importance_scores(memories)
    personas = known_personas(memories)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    semantic_scorer = build_semantic_scorer(args, memories)
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    methods = ("vector", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)

    ranked_output_rows = []
    top_rows = []
    query_metric_rows = []
    for query in queries:
        ranked_by_method = rank_all_methods(
            query,
            memories,
            methods,
            idf,
            memory_tokens,
            avg_len,
            args.half_life_days,
            semantic_scorer,
            personas,
            args.persona_boost_weight,
            persona_boost_query_types,
            args.importance_weight,
            memory_importance,
            args.type_awareness_weight,
        )
        for method, ranked in ranked_by_method.items():
            if args.rank_output_k > 0:
                ranked_output_rows.extend(ranked[:args.rank_output_k])
            top_rows.append(ranked[0])
            query_metric_rows.append(metrics_for_ranked(query, method, ranked, k_values=(1, 3, 5)))

    k_values = (1, 3, 5)
    summary = aggregate_metrics(query_metric_rows, k_values=k_values, group_key=None)
    type_summary = aggregate_metrics(query_metric_rows, k_values=k_values, group_key="query_type")
    duration = time.perf_counter() - started

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "rankings.csv", ranked_output_rows)
    write_csv(args.output_dir / "per_query_metrics.csv", query_metric_rows)
    write_csv(args.output_dir / "summary.csv", summary)
    write_csv(args.output_dir / "summary_by_type.csv", type_summary)
    write_report(args.output_dir / "report.md", summary, type_summary, top_rows, duration, len(memories), len(queries))

    print(json.dumps({
        "summary": summary,
        "semantic_backend": semantic_scorer.name,
        "output_dir": str(args.output_dir),
    }, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run agent memory retrieval baselines.")
    base = Path(__file__).resolve().parent
    parser.add_argument("--memories", type=Path, default=base / "data" / "sample_10.jsonl")
    parser.add_argument("--queries", type=Path, default=base / "data" / "queries_10.jsonl")
    parser.add_argument("--output-dir", type=Path, default=base / "results" / "sample_10")
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--rank-output-k", type=int, default=100, help="Write only the top K ranked memories per query/method. Use 0 to skip rankings.csv.")
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=base / "cache" / "embeddings")
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="", help="Comma-separated query types that may receive persona boost. Empty means all types.")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--type-awareness-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true", help="Load sentence-transformer models only from the local Hugging Face cache.")
    return parser


if __name__ == "__main__":
    try:
        run(build_parser().parse_args())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
