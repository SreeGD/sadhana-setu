# Quickstart: Note Enrichment

Validation/run guide for the enrichment stage (spec 002). Contracts + data model are in
[`contracts/`](./contracts/) and [`data-model.md`](./data-model.md).

> Status: **specified, not yet implemented**. These are the steps the implementation must satisfy.
> Depends on `001-corpus-pipeline` having produced committed transcripts.

## Prerequisites

- The repo venv (`pip install -e ".[dev]"`); `streamlit` (already a dep).
- **Claude Code CLI** on PATH (`claude --version`) — enrichment runs `claude -p --output-format
  json`; no Anthropic API key.
- A running **`kg-mcp`** server (vidya-karana-kg) reachable via `sadhana_setu/mcp_client.py`
  (`make smoke` confirms).
- vidya-karana checkout importable for `CorpusProcessor` back-ingest.

## Scenario 1 — Enrich a transcript (US1, US2)

```bash
python -m sadhana_setu.corpus enrich --set holy-name-seminar
```

**Expect**: for each transcribed lecture, a draft note at `corpus/notes/<set>/<id>.md` with all
FR-001 sections; every `key_teaching` carries a transcript timestamp; every verse in the body is
KG-sourced (resolved via `get_verse`); ungrounded candidates appear under `[UNVERIFIED]`; status
is `draft`. Re-running is idempotent unless `--regenerate`.

## Scenario 2 — KG-offline fail-safe (US2)

```bash
# with kg-mcp stopped
python -m sadhana_setu.corpus enrich --set holy-name-seminar
```

**Expect**: no verses emitted as verified; the note is marked unverifiable and **not** published;
the run reports the fail-safe (non-zero exit).

## Scenario 3 — Cross-references (US3)

**Expect**: each key teaching gains ≥1 grounded cross-reference (via `search_corpus` /
`cross_author_chunks`), each with a citation that resolves in the KG.

## Scenario 4 — Review + auto-ingest (US4, US5)

```bash
streamlit run sadhana_setu/ui/review_view.py     # or the review page in the main app
```

**Expect**: drafts are listed; opening one shows the note + its `[UNVERIFIED]`/`[sic?]` aids;
**Approve** records reviewer + date, flips status to `reviewed`, and **immediately** ingests the
verified body into ChromaDB (`CorpusProcessor.ingest_text`, keyed by note id) and triggers a KG
rebuild. An unreviewed note is never ingested (SC-003).

## Scenario 5 — Retrieval guarantee (US5)

```bash
python -m sadhana_setu.mcp_client smoke   # or a search_corpus call
```

**Expect**: after approval + rebuild, `search_corpus` returns a passage from the reviewed note
(SC-005). Re-approving a re-reviewed note replaces, not duplicates (idempotent by note id).

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 verses 100% KG-grounded | 1 |
| SC-002 every teaching → timestamp | 1 |
| SC-003 no publish without review | 4 |
| SC-004 idempotent enrichment | 1 |
| SC-005 reviewed note retrievable | 5 |
