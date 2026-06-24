"""Ground candidate references against kg-mcp (FR-002/003/010).

The enrichment LLM proposes verse refs + cross-ref queries; this module resolves them through
``kg-mcp`` and substitutes authoritative text. Unresolved candidates become ``[UNVERIFIED]`` and
are withheld from the body. If the KG is unreachable, grounding fails safe — no verse is emitted
as verified (Constitution I; see ``contracts/grounding.md``).
"""
from __future__ import annotations

from sadhana_setu.corpus.notes import Citation, KeyTeaching, NoteContent


class KGUnavailable(RuntimeError):
    """kg-mcp could not be reached — caller must withhold the note (FR-010)."""


def default_caller(name: str, args: dict):
    """Call kg-mcp via the app's existing sync MCP client, returning structured content."""
    from sadhana_setu.mcp_client import call_tool_sync

    result = call_tool_sync(name, args)
    # Tolerate either a plain value or an MCP result object.
    for attr in ("structured_content", "structuredContent", "data"):
        if hasattr(result, attr):
            return getattr(result, attr)
    return result


def ground(enrichment: dict, *, caller=None) -> NoteContent:
    """Resolve all candidate references in ``enrichment`` into a grounded NoteContent."""
    call = caller or default_caller

    # Liveness gate (fail-safe).
    try:
        call("kg_status", {})
    except Exception as exc:  # noqa: BLE001 — any failure ⇒ offline
        raise KGUnavailable(str(exc)) from exc

    unverified: list[str] = []

    teachings: list[KeyTeaching] = []
    for kt in enrichment["key_teachings"]:
        cites: list[Citation] = []
        for ref in kt.get("candidate_verse_refs", []) or []:
            c = _resolve_verse(call, ref)
            if c.verified:
                cites.append(c)
            else:
                unverified.append(f"verse {ref} (in: {kt['point'][:60]})")
        teachings.append(KeyTeaching(point=kt["point"], timestamp=kt["timestamp"], citations=cites))

    cross_refs: list[Citation] = []
    for cr in enrichment.get("candidate_cross_refs", []) or []:
        c = _resolve_cross_ref(call, cr)
        if c.verified:
            cross_refs.append(c)
        else:
            unverified.append(f"cross-ref '{cr.get('query', '')[:60]}'")

    return NoteContent(
        theme_summary=enrichment["theme_summary"],
        key_teachings=teachings,
        practical_application=enrichment["practical_application"],
        glossary=[(g["term"], g["gloss"]) for g in enrichment.get("glossary", []) or []],
        cross_references=cross_refs,
        unverified=unverified,
        sic_flags=list(enrichment.get("sic_flags", []) or []),
    )


def _resolve_verse(call, verse_ref: str) -> Citation:
    try:
        res = call("get_verse", {"verse_ref": verse_ref})
    except Exception:  # noqa: BLE001 — a single lookup error ⇒ unverified, not fatal
        res = None
    if isinstance(res, dict) and res.get("iast"):
        return Citation(
            kind="verse", candidate=verse_ref, verse_ref=verse_ref, source=verse_ref,
            iast=res.get("iast"), translation=res.get("translation"), verified=True,
        )
    return Citation(kind="verse", candidate=verse_ref, verse_ref=verse_ref, verified=False)


def _resolve_cross_ref(call, cr: dict) -> Citation:
    query = cr.get("query", "")
    value_id = cr.get("value_id")
    try:
        if value_id:
            hits = call("cross_author_chunks", {"value_id": value_id})
        else:
            hits = call("search_corpus", {"query": query, "mode": "kg_augmented", "top_k": 5})
    except Exception:  # noqa: BLE001
        hits = None
    if hits:
        top = hits[0] if isinstance(hits, list) else hits
        text = top.get("text") if isinstance(top, dict) else str(top)
        source = top.get("source", query) if isinstance(top, dict) else query
        return Citation(kind="cross_ref", candidate=query, source=source,
                        translation=text, verified=True)
    return Citation(kind="cross_ref", candidate=query, verified=False)
