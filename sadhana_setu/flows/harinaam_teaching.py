"""Pre-japa adapter over the shared corpus-teaching service (spec 005 + 003).

Retrieval, cache, dedup, clean-text, and the live-ChromaDB bridge now live in
``flows/corpus_teaching.py`` (the single path for all surfaces, spec 003). This module keeps the
`005` entry point and wraps the result as a pre-japa ``ReadingStage``, passing a shared per-day
``state`` so the pre-japa "deepen" teaching participates in the cross-surface de-duplication.
"""
from __future__ import annotations

from sadhana_setu.flows import corpus_teaching
from sadhana_setu.flows.prejapa_reading import ReadingStage


def fetch_teaching(theme: str, *, querier=None, state: dict | None = None) -> ReadingStage | None:
    """Return one reviewed Hari-Nāma teaching for the pre-japa deepen stage, or None."""
    t = corpus_teaching.get_for_surface(theme, "pre-japa", state=state, querier=querier)
    if t is None:
        return None
    return ReadingStage(label="A teaching on the Holy Name", body=t.body,
                        citation=t.citation, source_kind="corpus")
