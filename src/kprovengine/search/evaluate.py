from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import RelevanceJudgment, SearchDocument
from .query import parse_search_query
from .ranker import rank_documents


@dataclass(frozen=True)
class EvaluationQuery:
    query_id: str
    query: str


@dataclass(frozen=True)
class QueryEvaluation:
    query_id: str
    precision_at_k: float
    reciprocal_rank: float
    ndcg_at_10: float


@dataclass(frozen=True)
class EvaluationReport:
    query_count: int
    precision_at_k: float
    mrr: float
    ndcg_at_10: float
    per_query: tuple[QueryEvaluation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_count": self.query_count,
            "precision_at_k": self.precision_at_k,
            "mrr": self.mrr,
            "ndcg_at_10": self.ndcg_at_10,
            "per_query": [
                {
                    "query_id": row.query_id,
                    "precision_at_k": row.precision_at_k,
                    "reciprocal_rank": row.reciprocal_rank,
                    "ndcg_at_10": row.ndcg_at_10,
                }
                for row in self.per_query
            ],
        }


def load_golden_fixture(path: Path) -> tuple[list[EvaluationQuery], list[RelevanceJudgment]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Golden fixture must be a JSON object")

    raw_queries = payload.get("queries")
    raw_judgments = payload.get("judgments")
    if not isinstance(raw_queries, list) or not isinstance(raw_judgments, list):
        raise ValueError("Golden fixture requires 'queries' and 'judgments' lists")

    queries = [
        EvaluationQuery(query_id=str(row["query_id"]), query=str(row["query"]))
        for row in raw_queries
    ]
    judgments = [
        RelevanceJudgment(
            query_id=str(row["query_id"]),
            doc_id=str(row["doc_id"]),
            relevance=int(row["relevance"]),
        )
        for row in raw_judgments
    ]

    queries = sorted(queries, key=lambda q: q.query_id)
    judgments = sorted(judgments, key=lambda j: (j.query_id, j.doc_id))
    return queries, judgments


def evaluate_relevance(
    documents: list[SearchDocument],
    queries: list[EvaluationQuery],
    judgments: list[RelevanceJudgment],
    *,
    k: int = 5,
) -> EvaluationReport:
    if k <= 0:
        raise ValueError("k must be positive")

    judgment_index: dict[str, dict[str, int]] = {}
    for judgment in judgments:
        bucket = judgment_index.setdefault(judgment.query_id, {})
        bucket[judgment.doc_id] = judgment.relevance

    per_query: list[QueryEvaluation] = []
    for query in sorted(queries, key=lambda q: q.query_id):
        parsed = parse_search_query(query.query)
        ranked = rank_documents(parsed, documents, limit=max(k, 10))
        ranked_ids = [result.document.doc_id for result in ranked]

        relevance_lookup = judgment_index.get(query.query_id, {})
        precis = _precision_at_k(ranked_ids, relevance_lookup, k)
        rr = _reciprocal_rank(ranked_ids, relevance_lookup)
        ndcg = _ndcg_at_k(ranked_ids, relevance_lookup, 10)

        per_query.append(
            QueryEvaluation(
                query_id=query.query_id,
                precision_at_k=round(precis, 6),
                reciprocal_rank=round(rr, 6),
                ndcg_at_10=round(ndcg, 6),
            )
        )

    count = len(per_query)
    if count == 0:
        return EvaluationReport(
            query_count=0,
            precision_at_k=0.0,
            mrr=0.0,
            ndcg_at_10=0.0,
            per_query=tuple(),
        )

    return EvaluationReport(
        query_count=count,
        precision_at_k=round(sum(row.precision_at_k for row in per_query) / count, 6),
        mrr=round(sum(row.reciprocal_rank for row in per_query) / count, 6),
        ndcg_at_10=round(sum(row.ndcg_at_10 for row in per_query) / count, 6),
        per_query=tuple(per_query),
    )


def _precision_at_k(ranked_doc_ids: list[str], relevance_lookup: dict[str, int], k: int) -> float:
    topk = ranked_doc_ids[:k]
    if not topk:
        return 0.0
    relevant = sum(1 for doc_id in topk if relevance_lookup.get(doc_id, 0) > 0)
    return relevant / float(k)


def _reciprocal_rank(ranked_doc_ids: list[str], relevance_lookup: dict[str, int]) -> float:
    for idx, doc_id in enumerate(ranked_doc_ids, start=1):
        if relevance_lookup.get(doc_id, 0) > 0:
            return 1.0 / float(idx)
    return 0.0


def _ndcg_at_k(ranked_doc_ids: list[str], relevance_lookup: dict[str, int], k: int) -> float:
    gains = [relevance_lookup.get(doc_id, 0) for doc_id in ranked_doc_ids[:k]]
    dcg = _dcg(gains)

    ideal_gains = sorted((value for value in relevance_lookup.values() if value > 0), reverse=True)[:k]
    if not ideal_gains:
        return 0.0

    idcg = _dcg(ideal_gains)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def _dcg(gains: list[int]) -> float:
    total = 0.0
    for idx, gain in enumerate(gains, start=1):
        if gain <= 0:
            continue
        total += (2.0**gain - 1.0) / math.log2(idx + 1.0)
    return total
