# Back-Ingest Contract (vidya-karana ChromaDB → KG)

How an approved note flows into the knowledge graph (FR-011), triggered automatically by approval
in the Streamlit review UI.

## Entry point (audited)

`vidya-karana/agents/corpus_processor.py`:

```python
CorpusProcessor(...).ingest_text(
    text: str,                 # the note's verified body (KG-grounded sections only)
    source_id: str,            # = note id (e.g. "holy-name-seminar/<lecture-id>"); idempotency key
    metadata: dict[str, str],  # speaker, set_id, lecture_id, title, sha256, kind="harinaam-note"
) -> int                       # number of new chunks added
```

Backed by `systems/chromadb_manager.py::ChromaDBManager.add_chunks`. IAST normalization is applied
by `CorpusProcessor` (reused, not reimplemented).

## Rules

1. **Eligibility**: only `status: reviewed` notes (SC-003). The review UI calls ingest as part of
   approval.
2. **Content**: ingest the **verified body only** — `[UNVERIFIED]` items and `[sic?: …]` flags are
   excluded from the ingested text (they are review aids, not corpus truth).
3. **Idempotent replace**: keyed by `source_id` = note id. Re-ingesting a re-reviewed note replaces
   its prior chunks, never duplicates.
4. **KG refresh**: after `ingest_text`, trigger the vidya-karana-kg rebuild (manual trigger);
   if unavailable, the nightly cron rebuild picks it up. Record `ingested_at` on the note.
5. **Retrieval guarantee** (SC-005): after ingest + rebuild, `search_corpus` returns a passage
   from the note.

## Failure semantics

| Condition | Behavior |
|---|---|
| `CorpusProcessor`/ChromaDB unavailable | Approval still records `reviewed`; ingest is queued/retried; `ingested_at` stays null and the UI shows "pending ingest" |
| KG rebuild trigger unavailable | Fall back to nightly cron; note remains ingested into ChromaDB |
