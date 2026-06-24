# Phase 0 Research: Pre-japa Reading for Transformation

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

All requirements-level questions were resolved in the spec's `## Clarifications`. This document
records the engineering decisions (Decision / Rationale / Alternatives) from a read-only audit of
the existing app.

## R1 — Surfacing one reviewed Hari-Nāma teaching (FR-003, self-contained)

**Audit**: The app already calls kg-mcp via `sadhana_setu/mcp_client.py::call_tool_sync(name,
args)`. Spec `002` ingests reviewed notes into vidya-karana ChromaDB with metadata
`kind="harinaam-note"` and the note's `source_id`/speaker/lecture.

**Decision**: A small `flows/harinaam_teaching.py` calls
`call_tool_sync("search_corpus", {"query": <today's theme/value>, "mode": "kg_augmented",
"top_k": 5})`, then prefers a chunk whose metadata `kind == "harinaam-note"`, returning its text
+ citation (speaker + lecture). If none qualify (corpus not yet ingested) or kg-mcp is offline,
fall back to the curated `nama_tattva` library (existing `pick_for_today`).

**Rationale**: Self-contained per the clarification (not blocked by `003`); reuses the existing
MCP client; the `harinaam-note` filter guarantees only reviewed `002` content is surfaced
(Constitution V). Querying by the day's value/theme keeps the teaching relevant.

**Alternatives**: a dedicated kg-mcp "random reviewed note" tool (rejected — no such tool, and
theme-relevance is better); waiting on `003` (rejected by clarification).

## R2 — Daily-stable selection (FR-007)

**Audit**: Existing pickers (`pick_for_today`) seed by date (day ordinal) so a day's content is
deterministic.

**Decision**: All arc elements select deterministically from `date.today()` (day ordinal),
matching the existing convention, so reopening pre-japa the same day shows the same reading.

**Rationale**: Matches established behavior; no persistence needed; satisfies FR-007.

## R3 — The contemplative micro-practice source (FR-005, US3)

**Decision**: Derive the micro-practice from the day's already-grounded content rather than
authoring a large new corpus: one of {a "sit with this line" drawn from the day's
affirmation/teaching, a single short prayer to repeat once (e.g. tṛṇād api sunīcena, from the
existing faith/nāma material), a holding-question}. A small curated `contemplations` set provides
the prayer/question prompts; verse-bearing prompts reuse grounded content.

**Rationale**: Minimizes new human-review burden (Constitution V) by reusing reviewed/curated
content; keeps the practice seconds-long (FR-009); no input/tracking (Constitution IV).

**Alternatives**: a large new contemplation library (deferred — needs review); LLM-generated
prompts (rejected — would need grounding/review, overkill for a one-line prompt).

## R4 — The optional weekly-sankalpa echo (FR-012)

**Audit**: `flows/saturday.py::get_checkin(most_recent_saturday())` → `WeeklyCheckin(tone,
mood_bhava, practices, priorities)`.

**Decision**: The "enter japa" stage may render a gentle one-line echo of the current week's
`tone`/`mood_bhava` (if a check-in exists). The closing **resolve itself comes from the day's
reading**, not from this data (clarification Q5 = optional echo).

**Rationale**: Light read of existing data; strengthens weekly↔daily coherence without coupling
the resolve to Saturday; degrades cleanly when no check-in exists.

## R5 — Fallback chain & graceful degradation (FR-008, SC-004)

**Decision**: corpus teaching → (kg-mcp `harinaam-note`) → (curated `nama_tattva`); each arc stage
has a curated fallback so the reading always renders. A quiet inline note indicates "corpus
offline" when the fallback is used (mirrors the existing kg-mcp offline pattern).

**Rationale**: The app already degrades gracefully when kg-mcp is down; reuse that pattern.

## R6 — Mapping existing content onto the arc (FR-010)

**Decision (content → arc stage)**:

| Arc stage | Source (repurposed) |
|---|---|
| **Orient** | affirmation (sankalpa declaration) + a Name-glory line (faith verse) |
| **Deepen** | corpus Hari-Nāma teaching (R1) → fallback nāma-tattva; inspiration pastime as support |
| **Apply** | contemplative micro-practice (R3) |
| **Enter japa** | closing resolve (from the reading) + optional sankalpa echo (R4) |
| Saturday | bhajan-of-the-week folds into Orient/Deepen on Saturdays; book-tip retained, trimmed |

Redundant standalone cards (separate tip + book-tip + story-of-the-week as peers) are dropped or
folded so the reading is one arc, not a card wall.

**Rationale**: Honors FR-010 (restructure, keep valued pieces) and the ~60–75s budget (FR-009).

## Clarification status

All spec `[NEEDS CLARIFICATION]` resolved in Session 2026-06-24. No open research items;
remaining choices (exact CSS, prompt wording) are implementation detail.
