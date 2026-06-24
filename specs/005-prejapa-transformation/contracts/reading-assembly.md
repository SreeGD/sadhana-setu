# Contract: Pre-japa Reading Assembly

The internal interface between the arc-assembly flow and the renderer.

## `flows/prejapa_reading.py`

```python
def build_reading(d: date | None = None, *, caller=None, checkin_loader=None) -> PrejapaReading:
    """Assemble the day's transformation arc.

    - Deterministic by date `d` (default today) — stable within a day (FR-007).
    - `caller`     : injectable kg-mcp caller (default the real call_tool_sync) — for tests.
    - `checkin_loader`: injectable weekly-checkin loader (default get_checkin(most_recent_saturday())).
    - NEVER raises on corpus failure — falls back to curated content and sets corpus_online=False.
    """
```

Guarantees:
- `orient`, `deepen`, `apply`, `enter` always populated (SC-004).
- `deepen.citation` present whenever `deepen.source_kind == "corpus"` (FR-003/004).
- No side effects, no persistence, no tracking (FR-005/006).

## `flows/harinaam_teaching.py`

```python
def fetch_teaching(theme: str, *, caller=None) -> ReadingStage | None:
    """Return one reviewed Hari-Nāma teaching, or None (caller falls back).

    Calls caller("search_corpus", {"query": theme, "mode": "kg_augmented", "top_k": 5}),
    prefers a hit whose metadata kind == "harinaam-note" (reviewed 002 content only,
    Constitution V), and returns its text + citation. Returns None on empty result or any
    error (offline / kg-mcp down) — never raises.
    """
```

## `ui/prejapa_view.py::render()`

- Calls `build_reading()` and renders the four stages in order, ending with the resolve and
  (if present) the sankalpa echo, then the existing "screen silent during japa" footer.
- When `reading.corpus_online is False`, shows a quiet inline "corpus offline — curated reading"
  note (no error, no broken layout) — FR-008.
- Renders within the ~60–75s reading budget; no inputs, buttons that score, or trackers.
