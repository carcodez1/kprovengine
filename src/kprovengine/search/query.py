from __future__ import annotations

import shlex

from .models import SearchQuery

_FIELD_PREFIXES = {
    "sha256": "sha256",
    "run": "run_id",
    "commit": "commit",
    "type": "artifact_type",
    "tag": "tag",
}

_AUDIT_TERMS = {
    "attest",
    "attestation",
    "audit",
    "compliance",
    "evidence",
    "hash",
    "manifest",
    "policy",
    "provenance",
    "sbom",
    "verification",
}


def parse_search_query(raw: str) -> SearchQuery:
    text = raw.strip()
    tokens = _tokenize(text)

    values: dict[str, str | None] = {
        "sha256": None,
        "run_id": None,
        "commit": None,
        "artifact_type": None,
        "tag": None,
    }
    free_terms: list[str] = []

    for token in tokens:
        if ":" not in token:
            free_terms.append(token.casefold())
            continue

        key, value = token.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        field_name = _FIELD_PREFIXES.get(key)
        if field_name is None or not value:
            free_terms.append(token.casefold())
            continue

        normalized_value = value
        if field_name in {"sha256", "commit", "artifact_type", "tag"}:
            normalized_value = value.casefold()
        values[field_name] = normalized_value

    normalized_terms = tuple(sorted(dict.fromkeys(term for term in free_terms if term)))
    phrase = " ".join(normalized_terms) if normalized_terms else None

    audit_vocab = set(normalized_terms)
    if values["tag"]:
        audit_vocab.add(str(values["tag"]).casefold())

    return SearchQuery(
        raw=text,
        terms=normalized_terms,
        sha256=_opt(values["sha256"]),
        run_id=_opt(values["run_id"]),
        commit=_opt(values["commit"]),
        artifact_type=_opt(values["artifact_type"]),
        tag=_opt(values["tag"]),
        phrase=phrase,
        audit_intent=any(term in _AUDIT_TERMS for term in audit_vocab),
    )


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    try:
        return shlex.split(text)
    except ValueError:
        return [token for token in text.split() if token]


def _opt(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
