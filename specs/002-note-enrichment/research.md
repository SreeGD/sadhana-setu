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

**Finding (read-only audit)**: `kg/mcp/tools.py` exposes:
- `get_verse(verse_ref: str) -> {devanagari, iast, word_for_word, translation, purport_summary}`
- `find_verses(source=None, exemplified_by_value=None, edge_kind="any") -> list`
- `search_corpus(query: str, mode="kg_augmented", top_k=10) -> list`
- `cross_author_chunks(value_id: str, authors=None, limit_per_author=5) -> list`
- `kg_status() -> dict`

The app already calls these via `sadhana_setu/mcp_client.py::call_tool_sync(name, args)` over stdio
(e.g. `call_tool_sync("get_verse", {"verse_ref": "BG 18.66"})`).

**Decision**: `grounding.py` reuses `call_tool_sync`. The LLM proposes a `verse_ref` (e.g.
"BG 18.66"); grounding calls `get_verse` and substitutes the returned `iast`/`translation` as the
authoritative text. An empty/missing result ⇒ mark `[UNVERIFIED]` (FR-003); a `kg_status()`
failure or transport error ⇒ fail-safe (FR-010). Cross-references use `search_corpus`
(kg_augmented) and `cross_author_chunks`. Contract captured in `contracts/grounding.md`.

## R3 — vidya-karana ChromaDB back-ingest path (FR-011)

**Question**: What is the supported entry point to add a document to vidya-karana's
corpus/ChromaDB so it becomes KG-queryable, and how is idempotent replace done?

**To investigate** (read-only): vidya-karana `agents/corpus_processor.py` / `pipeline.py` /
ingest scripts; ChromaDB collection + id scheme; whether the KG rebuild is nightly cron or can be
triggered.

**Finding (read-only audit)**: vidya-karana's `agents/corpus_processor.py::CorpusProcessor`
("Agent 0 — ingests source materials into ChromaDB with verified references") exposes
`ingest_text(text, source_id, metadata: dict) -> int` (chunks + adds via
`systems/chromadb_manager.py::ChromaDBManager.add_chunks`, returns new-chunk count) and includes
IAST normalization. The KG itself is a NetworkX snapshot rebuilt nightly by cron with a manual
trigger (per vidya-karana-kg README).

**Decision**: Back-ingest reuses `CorpusProcessor.ingest_text` with `source_id` = the note's
stable id (idempotent replace keyed by that id) and `metadata` carrying speaker/lecture/note
provenance. After ingest, trigger the KG rebuild (manual trigger; fall back to nightly cron if
the trigger is unavailable). Contract captured in `contracts/ingest.md`.

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

**Decision**: The enrichment prompt instructs Claude Code (via `claude -p --output-format json`)
to return a **single JSON object** with: `theme_summary`, `key_teachings[]` (each with `point`,
`timestamp`, optional `candidate_verse_refs[]`), `glossary[]`, `practical_application`, and
`candidate_cross_refs[]` (free-text queries for `search_corpus`/`cross_author_chunks`). The model
supplies **reference identifiers only**, never final verse text — grounding fills that in (R2).
Suspected mishearings are emitted as `sic_flags[]` (FR-014). Contract + JSON schema in
`contracts/enrichment-output.schema.json`, validated by a golden-file test.

## R7 — Review workflow ergonomics

**Question**: How does a devotee actually review and approve — edit front-matter directly, a CLI
`review approve <note>`, or a lightweight UI later?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — a **lightweight Streamlit review UI** is the
review surface; approving flips `draft → reviewed` (reviewer + date) and **auto-triggers
back-ingest + KG rebuild** (FR-011). To investigate at plan time: whether it is a standalone
Streamlit page or folds into the existing app.

## Clarification status

Resolved during `/speckit-plan` (2026-06-24): R2 (kg-mcp tool contracts via `call_tool_sync`),
R3 (back-ingest via `CorpusProcessor.ingest_text`, idempotent by `source_id`), R6 (enrichment
JSON output contract). No open research items remain.

Resolved in the spec's `## Clarifications` (Session 2026-06-24): FR-015 (R1, Claude Code
headless), FR-013 (R4, one note per transcript), FR-014 (R5, annotate-only), review ergonomics
(R7, Streamlit UI), back-ingest trigger (auto on approval). Remaining engineering items for
`/speckit-plan`: R2 (kg-mcp contracts), R3 (ChromaDB ingest path), R6 (prompt contract).

### (historical) open questions feeding `/speckit-clarify`

- FR-013 (R4): note granularity (per-transcript vs aggregated series/seminar).
- FR-014 (R5): transcript-error handling (annotate vs propose upstream correction).
- FR-015 (R1): enrichment LLM choice & locality.
