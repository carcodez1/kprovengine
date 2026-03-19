from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from .index import AUDIT_ARTIFACT_TYPES
from .models import ScoreComponent, ScoreExplanation, SearchDocument, SearchQuery, SearchResult

SCORE_SHA256_EXACT = 1000.0
SCORE_RUN_OR_COMMIT_EXACT = 700.0
SCORE_FIELD_EXACT = 300.0
SCORE_PHRASE_MATCH = 120.0
SCORE_TERM_MATCH = 25.0
SCORE_AUDIT_INTENT_BOOST = 35.0
MAX_RECENCY_TIEBREAK = 0.009


def rank_documents(
    query: SearchQuery,
    documents: Iterable[SearchDocument],
    *,
    limit: int = 10,
) -> list[SearchResult]:
    scored: list[tuple[float, str, ScoreExplanation, SearchDocument]] = []
    raw_query = query.raw.strip()

    for document in documents:
        explanation = score_document(query, document)
        if raw_query and explanation.final_score <= 0:
            continue
        scored.append((explanation.final_score, document.doc_id, explanation, document))

    scored.sort(key=lambda item: (-item[0], item[1]))

    results: list[SearchResult] = []
    for rank, (score, _doc_id, explanation, document) in enumerate(scored[:limit], start=1):
        rounded_score = round(score, 6)
        if rounded_score != explanation.final_score:
            explanation = ScoreExplanation(
                final_score=rounded_score,
                components=explanation.components,
            )
        results.append(
            SearchResult(
                rank=rank,
                score=rounded_score,
                explanation=explanation,
                document=document,
            )
        )

    return results


def score_document(query: SearchQuery, document: SearchDocument) -> ScoreExplanation:
    components: list[ScoreComponent] = []
    score = 0.0

    doc_sha = document.artifact_sha256.casefold()
    doc_commit = (document.source_revision or "").casefold()
    doc_type = document.artifact_type.casefold()
    doc_tags = tuple(tag.casefold() for tag in document.policy_tags)
    search_text = document.search_text.casefold()

    if query.sha256 and doc_sha == query.sha256.casefold():
        components.append(ScoreComponent(reason="exact_sha256", points=SCORE_SHA256_EXACT))
        score += SCORE_SHA256_EXACT

    if query.run_id and document.run_id == query.run_id:
        components.append(ScoreComponent(reason="exact_run_id", points=SCORE_RUN_OR_COMMIT_EXACT))
        score += SCORE_RUN_OR_COMMIT_EXACT

    if query.commit and doc_commit and doc_commit == query.commit.casefold():
        components.append(ScoreComponent(reason="exact_commit", points=SCORE_RUN_OR_COMMIT_EXACT))
        score += SCORE_RUN_OR_COMMIT_EXACT

    if query.artifact_type and doc_type == query.artifact_type.casefold():
        components.append(ScoreComponent(reason="exact_artifact_type", points=SCORE_FIELD_EXACT))
        score += SCORE_FIELD_EXACT

    if query.tag and query.tag.casefold() in doc_tags:
        components.append(ScoreComponent(reason="exact_tag", points=SCORE_FIELD_EXACT))
        score += SCORE_FIELD_EXACT

    if query.phrase and query.phrase.casefold() in search_text:
        components.append(ScoreComponent(reason="phrase_match", points=SCORE_PHRASE_MATCH))
        score += SCORE_PHRASE_MATCH

    term_matches = 0
    for term in query.terms:
        if term.casefold() in search_text:
            term_matches += 1
    if term_matches:
        points = SCORE_TERM_MATCH * float(term_matches)
        components.append(ScoreComponent(reason="metadata_term_match", points=points))
        score += points

    if query.audit_intent and _is_audit_artifact(document):
        components.append(ScoreComponent(reason="audit_intent_boost", points=SCORE_AUDIT_INTENT_BOOST))
        score += SCORE_AUDIT_INTENT_BOOST

    # Bounded tie-breaker only: never dominates lexical relevance.
    if score > 0 or not query.raw.strip():
        recency = _recency_tiebreak(document.timestamp)
        if recency > 0:
            components.append(ScoreComponent(reason="recency_tiebreak", points=recency))
            score += recency

    return ScoreExplanation(final_score=round(score, 6), components=tuple(components))


def _is_audit_artifact(document: SearchDocument) -> bool:
    return document.artifact_type in AUDIT_ARTIFACT_TYPES


def _recency_tiebreak(timestamp: str) -> float:
    try:
        normalized = timestamp
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        epoch = datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0

    if epoch <= 0:
        return 0.0

    points = epoch / 1_000_000_000_000
    return min(MAX_RECENCY_TIEBREAK, round(points, 6))
