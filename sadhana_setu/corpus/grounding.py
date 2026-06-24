"""Ground candidate references against kg-mcp (FR-002/003/010).

The enrichment LLM proposes verse candidates ({ref, gloss}) and cross-ref queries; this module
resolves them through ``kg-mcp`` and substitutes authoritative text:

- A verse is grounded by ``get_verse`` (exact, with IAST + translation).
- If the verse is not in the cache, we fall back to ``search_corpus`` on its *gloss* and attach a
  **related corpus passage** — labelled by the passage's real source, never claimed to be that
  exact verse (Constitution I).
- Cross-refs are grounded by ``search_corpus`` (which returns ``{chunks: [...]}``).

kg-mcp returns tool errors as *results* (not exceptions); those are detected and treated as a
miss. Unresolved candidates become ``[UNVERIFIED]``. If the KG is unreachable, grounding fails
safe (FR-010). See ``contracts/grounding.md``.
"""
from __future__ import annotations

from sadhana_setu.corpus.notes import Citation, KeyTeaching, NoteContent


class KGUnavailable(RuntimeError):
    """kg-mcp could not be reached — caller must withhold the note (FR-010)."""


def default_caller(name: str, args: dict):
    """Call kg-mcp via the app's existing sync MCP client, returning structured content."""
    from sadhana_setu.mcp_client import call_tool_sync

    result = call_tool_sync(name, args)
    for attr in ("structured_content", "structuredContent", "data"):
        if hasattr(result, attr):
            return getattr(result, attr)
    return result


def ground(enrichment: dict, *, caller=None) -> NoteContent:
    """Resolve all candidate references in ``enrichment`` into a grounded NoteContent."""
    base = caller or default_caller

    # Memoize identical lookups within this note — the same verse / query recurs across many
    # teachings, so this avoids dozens of redundant kg-mcp round-trips.
    import json

    _cache: dict = {}

    def call(name: str, args: dict):
        key = (name, json.dumps(args, sort_keys=True, default=str))
        if key not in _cache:
            _cache[key] = base(name, args)
        return _cache[key]

    # Liveness gate (fail-safe). kg_status returning an error payload also counts as down.
    try:
        status = call("kg_status", {})
    except Exception as exc:  # noqa: BLE001
        raise KGUnavailable(str(exc)) from exc
    if _is_error(status):
        raise KGUnavailable(str(status))

    unverified: list[str] = []

    teachings: list[KeyTeaching] = []
    for kt in enrichment["key_teachings"]:
        cites: list[Citation] = []
        for cand in _verse_candidates(kt):
            c = _resolve_verse(call, cand)
            if c.verified:
                cites.append(c)
            else:
                unverified.append(f"verse {cand.get('ref', '?')} (in: {kt['point'][:60]})")
        teachings.append(KeyTeaching(point=kt["point"], timestamp=kt["timestamp"], citations=cites))

    cross_refs: list[Citation] = []
    for cr in enrichment.get("candidate_cross_refs", []) or []:
        c = _resolve_cross_ref(call, cr)
        if c.verified:
            cross_refs.append(c)
        else:
            unverified.append(f"cross-ref '{_query_of(cr)[:60]}'")

    return NoteContent(
        theme_summary=enrichment["theme_summary"],
        key_teachings=teachings,
        practical_application=enrichment["practical_application"],
        glossary=[(g["term"], g["gloss"]) for g in enrichment.get("glossary", []) or []],
        cross_references=cross_refs,
        unverified=unverified,
        sic_flags=list(enrichment.get("sic_flags", []) or []),
    )


# -- resolution ----------------------------------------------------------

def _resolve_verse(call, cand: dict) -> Citation:
    ref = cand.get("ref") or cand.get("verse_ref") or ""
    gloss = cand.get("gloss") or ""
    res = _safe(call, "get_verse", {"verse_ref": ref})
    if isinstance(res, dict) and res.get("iast"):
        return Citation(kind="verse", candidate=ref, verse_ref=ref, source=ref,
                        iast=res.get("iast"), translation=res.get("translation"), verified=True)
    # Fallback: a related corpus passage found via the gloss (NOT claimed to be the exact verse).
    chunk = _first_chunk(_safe(call, "search_corpus",
                               {"query": gloss or ref, "mode": "kg_augmented", "top_k": 3}))
    if chunk:
        return Citation(kind="cross_ref", candidate=gloss or ref, verse_ref=ref,
                        source=_chunk_source(chunk), verified=True)
    return Citation(kind="verse", candidate=ref, verse_ref=ref, verified=False)


def _resolve_cross_ref(call, cr: dict) -> Citation:
    query = _query_of(cr)
    chunk = _first_chunk(_safe(call, "search_corpus",
                               {"query": query, "mode": "kg_augmented", "top_k": 5}))
    if chunk:
        return Citation(kind="cross_ref", candidate=query, source=_chunk_source(chunk),
                        verified=True)
    return Citation(kind="cross_ref", candidate=query, verified=False)


# -- helpers -------------------------------------------------------------

def _verse_candidates(kt: dict) -> list[dict]:
    """Accept both the new shape (candidate_verses:[{ref,gloss}]) and the old (candidate_verse_refs:[str])."""
    if kt.get("candidate_verses"):
        return [c for c in kt["candidate_verses"] if isinstance(c, dict)]
    return [{"ref": r, "gloss": ""} for r in (kt.get("candidate_verse_refs") or [])]


def _query_of(cr) -> str:
    return cr.get("query", "") if isinstance(cr, dict) else str(cr)


def _safe(call, name: str, args: dict):
    try:
        res = call(name, args)
    except Exception:  # noqa: BLE001 — a single lookup error ⇒ miss, not fatal
        return None
    return None if _is_error(res) else res


def _is_error(res) -> bool:
    if res is None:
        return True
    if isinstance(res, str):
        low = res.lower()
        return "error executing tool" in low or "unknown value" in low
    if isinstance(res, dict):
        return bool(res.get("isError") or res.get("error"))
    return False


def _first_chunk(res) -> dict | None:
    for c in _chunks(res):
        if _chunk_text(c):
            return c
    return None


def _chunks(res) -> list[dict]:
    if isinstance(res, dict):
        if isinstance(res.get("chunks"), list):
            return [c for c in res["chunks"] if isinstance(c, dict)]
        return [res]
    if isinstance(res, list):
        return [c for c in res if isinstance(c, dict)]
    return []


def _chunk_text(c: dict) -> str:
    return (c.get("text") or c.get("content") or c.get("chunk") or "").strip()


def _chunk_source(c: dict, default: str = "Hari-Nāma corpus") -> str:
    return _clean_source(c.get("source") or c.get("title") or c.get("author") or default)


def _clean_source(s: str) -> str:
    """Tidy a raw corpus source (ebook filename) into a readable citation label."""
    import re

    s = re.sub(r"\.(mobi|azw3|epub|pdf|txt|html?)$", "", s, flags=re.IGNORECASE)
    # strip author suffix ("- His Divine Grace A. C. Bhaktivedanta Swami Prabhupada")
    s = re.sub(r"\s*-\s*(His Divine Grace|H\.?\s*D\.?\s*G\.?|by\b).*$", "", s, flags=re.IGNORECASE)
    return s.strip(" .-_") or "Hari-Nāma corpus"
