# Phase 0 Research: Note Enrichment

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Unknowns to resolve before Phase 1 design. Items depending on a spec `[NEEDS CLARIFICATION]` are
flagged.

## R1 — Enrichment LLM choice & locality (depends on spec FR-015)

**Question**: Which LLM performs enrichment, and must it run locally?

**Considerations**:
- Constitution Principle VI favors local; but enrichment operates on **text transcripts** (no
  audio), so a cloud text-only model does not violate the "audio never leaves the machine" rule.
- Quality on Gauḍīya Vaiṣṇava tattva and Sanskrit term handling matters; the model must defer
  verse text to the KG (it only proposes *candidate* references).

**Decision**: **RESOLVED (Clarify 2026-06-24)** — enrichment runs via **Claude Code headless**
(`claude -p`) behind a thin provider interface, NOT the Anthropic API (reuses the existing Claude
Code subscription; text-only, VI honored). Implication: a `claude` CLI wrapper that feeds the
prompt contract and parses structured output; a local model is swappable via the same interface.

## R2 — kg-mcp tool contracts for grounding

**Question**: What exactly do `get_verse`, `find_verses`, `search_corpus`, `cross_author_chunks`
accept and return, so `grounding.py` can resolve candidate citations reliably?

**To investigate** (read-only): tool signatures/schemas exposed by `kg-mcp`; how the app's
`sadhana_setu/mcp_client.py` already calls them (`search_corpus`, `get_verse`, `find_verses`,
`cross_author_chunks` per docs); behavior on a miss (empty vs error) — drives the `[UNVERIFIED]`
path and the offline fail-safe.

**Decision**: _TBD_ — document the contract in `contracts/` before implementing grounding.

## R3 — vidya-karana ChromaDB back-ingest path (FR-011)

**Question**: What is the supported entry point to add a document to vidya-karana's
corpus/ChromaDB so it becomes KG-queryable, and how is idempotent replace done?

**To investigate** (read-only): vidya-karana `agents/corpus_processor.py` / `pipeline.py` /
ingest scripts; ChromaDB collection + id scheme; whether the KG rebuild is nightly cron or can be
triggered.

**Decision**: _TBD_ — produce an ingest contract (id scheme, replace semantics, KG-refresh
trigger).

## R4 — Note granularity (depends on spec FR-013)

**Question**: One note per transcript, or aggregate notes per lecture-series / full seminar?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — one note per transcript (1:1 with `001`).
Series/seminar synthesis is out of scope this round.

## R5 — Transcript-error handling (depends on spec FR-014)

**Question**: When enrichment detects a misheard Sanskrit term from whisper, does it annotate
only, or propose a correction upstream to 001's transcript?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — annotate-only: flag suspected mishearings
inline (`[sic?: …]`); never edit the `001` transcript; the reviewer resolves.

## R6 — Prompt contract & section schema

**Question**: What prompt produces reliable, structured, KG-deferring output (candidate
references, not final verse text)?

**To investigate**: a prompt that emits the FR-001 sections + a list of *candidate* citation
identifiers + timestamp anchors, in a parseable structure (e.g. JSON), so `grounding.py` can
resolve and `notes.py` can render. Few-shot examples from a real transcript.

**Decision**: _TBD_ — define in `contracts/` with a golden-file test.

## R7 — Review workflow ergonomics

**Question**: How does a devotee actually review and approve — edit front-matter directly, a CLI
`review approve <note>`, or a lightweight UI later?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — a **lightweight Streamlit review UI** is the
review surface; approving flips `draft → reviewed` (reviewer + date) and **auto-triggers
back-ingest + KG rebuild** (FR-011). To investigate at plan time: whether it is a standalone
Streamlit page or folds into the existing app.

## Clarification status

Resolved in the spec's `## Clarifications` (Session 2026-06-24): FR-015 (R1, Claude Code
headless), FR-013 (R4, one note per transcript), FR-014 (R5, annotate-only), review ergonomics
(R7, Streamlit UI), back-ingest trigger (auto on approval). Remaining engineering items for
`/speckit-plan`: R2 (kg-mcp contracts), R3 (ChromaDB ingest path), R6 (prompt contract).

### (historical) open questions feeding `/speckit-clarify`

- FR-013 (R4): note granularity (per-transcript vs aggregated series/seminar).
- FR-014 (R5): transcript-error handling (annotate vs propose upstream correction).
- FR-015 (R1): enrichment LLM choice & locality.
