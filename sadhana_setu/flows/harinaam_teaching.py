"""Surface one reviewed Hari-Nāma teaching from the corpus (spec 005, FR-003).

Self-contained: a single `kg-mcp` `search_corpus` call (not blocked by `003`). Prefers chunks
whose metadata `kind == "harinaam-note"` — i.e. reviewed `002` notes only (Constitution V).
Returns None on an empty result or any error, so the caller can fall back to curated content.
"""
from __future__ import annotations

from sadhana_setu.flows.prejapa_reading import ReadingStage

_HARINAAM_KIND = "harinaam-note"


def _default_caller(name: str, args: dict):
    from sadhana_setu.mcp_client import call_tool_sync

    result = call_tool_sync(name, args)
    for attr in ("structured_content", "structuredContent", "data"):
        if hasattr(result, attr):
            return getattr(result, attr)
    return result


def fetch_teaching(theme: str, *, caller=None) -> ReadingStage | None:
    """Return one reviewed Hari-Nāma teaching for ``theme``, or None (never raises)."""
    call = caller or _default_caller
    try:
        hits = call("search_corpus", {"query": theme, "mode": "kg_augmented", "top_k": 5})
    except Exception:  # noqa: BLE001 — offline / kg-mcp down ⇒ caller falls back
        return None
    if not hits:
        return None
    if not isinstance(hits, list):
        hits = [hits]

    for hit in hits:
        if not isinstance(hit, dict):
            continue
        if _kind(hit) != _HARINAAM_KIND:
            continue
        body = (hit.get("text") or "").strip()
        if not body:
            continue
        return ReadingStage(
            label="A teaching on the Holy Name",
            body=body,
            citation=_citation(hit),
            source_kind="corpus",
        )
    return None


def _kind(hit: dict) -> str | None:
    meta = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
    return meta.get("kind") or hit.get("kind")


def _citation(hit: dict) -> str:
    meta = hit.get("metadata") if isinstance(hit.get("metadata"), dict) else {}
    speaker = meta.get("speaker") or hit.get("speaker")
    title = meta.get("title") or hit.get("title") or meta.get("lecture_id")
    if speaker and title:
        return f"{speaker} — {title}"
    return hit.get("source") or speaker or title or "Hari-Nāma corpus"
