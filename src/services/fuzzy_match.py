"""Fuzzy string matching for reconciling customer-supplied text against BC master data.

More accepting than a plain SequenceMatcher ratio (the approach used by the
so_import_worker's ship-to matcher at threshold 0.5): this normalizes punctuation and
whitespace, then takes the max of (a) a SequenceMatcher ratio and (b) a token-overlap
coefficient, with a containment shortcut when one normalized string fully contains the
other. The overlap coefficient divides by the SHORTER token count, so extra qualifier
words on either side ("GAISANO DAVAO" vs "GAISANO MALL DAVAO CITY") don't tank the
score the way a plain ratio does.
"""
import re
from difflib import SequenceMatcher
from typing import Any

DEFAULT_THRESHOLD = 0.35


def normalize(s: str) -> str:
    """Uppercase, strip punctuation, collapse whitespace."""
    return " ".join(re.sub(r"[^A-Z0-9\s]", " ", (s or "").upper()).split())


def _token_overlap(a_tokens: set, b_tokens: set) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = len(a_tokens & b_tokens)
    return overlap / min(len(a_tokens), len(b_tokens))


def score(query: str, candidate: str) -> float:
    """Similarity score in [0, 1] between query and candidate, case/punctuation-insensitive."""
    norm_q, norm_c = normalize(query), normalize(candidate)
    if not norm_q or not norm_c:
        return 0.0
    if norm_q == norm_c:
        return 1.0
    if norm_q in norm_c or norm_c in norm_q:
        return 0.9
    ratio = SequenceMatcher(None, norm_q, norm_c).ratio()
    overlap = _token_overlap(set(norm_q.split()), set(norm_c.split()))
    return max(ratio, overlap)


def best_matches(
    query: str,
    candidates: list[tuple[str, dict[str, Any]]],
    threshold: float = DEFAULT_THRESHOLD,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Score query against every (candidate_text, payload) pair.

    Returns payload dicts (each augmented with "score" and "matchedText"), filtered to
    threshold and above, sorted by score descending, truncated to top_n.
    """
    scored = []
    for candidate_text, payload in candidates:
        s = score(query, candidate_text)
        if s >= threshold:
            # payload first so "score"/"matchedText" always win, even if BC ever returns
            # a field with one of those names.
            scored.append({**payload, "score": round(s, 4), "matchedText": candidate_text})
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_n]
