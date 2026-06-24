# Grounding Contract (kg-mcp)

How `grounding.py` turns the LLM's *candidate* references into verified, KG-sourced citations
(FR-002/003/010). All calls go through the existing
`sadhana_setu/mcp_client.py::call_tool_sync(name, args)` (stdio to `kg-mcp`).

## Tools used (audited signatures)

| Tool | Args | Returns |
|---|---|---|
| `kg_status` | `{}` | dict — liveness probe (fail-safe gate) |
| `get_verse` | `{"verse_ref": "BG 18.66"}` | `{devanagari, iast, word_for_word, translation, purport_summary}` |
| `search_corpus` | `{"query": str, "mode": "kg_augmented", "top_k": 10}` | list of chunks |
| `cross_author_chunks` | `{"value_id": str, "authors": [...]?, "limit_per_author": 5}` | list of chunks |
| `find_verses` | `{"source": str?, "exemplified_by_value": str?, "edge_kind": "any"}` | list of verses |

## Resolution rules

1. **Liveness first.** Call `kg_status({})`. If it errors/times out → **fail-safe**: emit no
   verses as verified; mark the whole note unverifiable; do not publish (FR-010).
2. **Verse candidate** (`candidate_verse_refs[i]`): call `get_verse({"verse_ref": ref})`.
   - Non-empty result ⇒ `verified=true`; use the returned `iast` + `translation` as the
     authoritative citation text (the LLM's text is discarded).
   - Empty / not found ⇒ `verified=false` ⇒ render as `[UNVERIFIED]`, withhold from the body
     (FR-003).
3. **Cross-ref candidate** (`candidate_cross_refs[i]`): if `value_id` present, call
   `cross_author_chunks`; else `search_corpus(query, mode="kg_augmented")`. Keep top results with a
   resolvable citation; unresolved ⇒ `[UNVERIFIED]`.
4. The LLM **never** supplies final verse text — only identifiers/queries (Constitution I).

## Failure semantics

| Condition | Behavior |
|---|---|
| `kg_status` unreachable | Whole note unverifiable; not published (exit non-zero in batch) |
| Single `get_verse` miss | That citation `[UNVERIFIED]`; rest of note proceeds |
| Transport error mid-run | Treat as offline → fail-safe |
