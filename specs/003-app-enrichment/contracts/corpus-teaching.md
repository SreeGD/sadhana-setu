# Contract: Shared Corpus-Teaching Service

`sadhana_setu/flows/corpus_teaching.py` — the single retrieval path for reviewed Hari-Nāma
teachings (FR-001). Streamlit-free and unit-testable (inject `querier` + `state`).

```python
def get_for_surface(theme: str, surface_id: str, *, date, state: dict,
                    querier=None) -> Teaching | None:
    """Return one reviewed, clean, cited teaching for `surface_id`, or None (caller → curated).

    - Resolves candidate reviewed notes for `theme` via the live ChromaDB kind=harinaam-note
      query (reused from harinaam_teaching), CACHED in state["theme_cache"][theme] so the ~2 s
      bridge runs at most once per theme per day (FR-012).
    - Returns the top candidate whose lecture_id is NOT in state["surfaced"], then adds it
      (de-duplication across surfaces within a day — FR-013).
    - body is CLEAN text read from the note file (FR-003); citation = speaker — lecture.
    - Returns None on: no reviewed match, all candidates already surfaced, or corpus unavailable
      (bridge error) — never raises (FR-004).
    """

def new_state() -> dict:
    """Fresh per-day state: {"theme_cache": {}, "surfaced": set()}."""
```

Guarantees:
- Only `kind=harinaam-note` / `status: reviewed` content surfaces (Constitution V; SC-001).
- Text is clean (SC-002); citation always present.
- Idempotent within a day for a given surface (cache); deterministic given the same state.

## UI usage (per surface)

```python
state = st.session_state.setdefault(f"corpus_{today}", corpus_teaching.new_state())
teaching = corpus_teaching.get_for_surface(theme, "nama-tattva", date=today, state=state)
render(teaching) if teaching else render(curated_fallback())   # FR-011
```

`harinaam_teaching.fetch_teaching` (pre-japa) delegates to this service with the same `state`, so
pre-japa participates in the dedup (plan R1/decision 6).
