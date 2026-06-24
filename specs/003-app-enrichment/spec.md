# Feature Specification: App Enrichment from the Hari-Nāma Corpus

**Feature Branch**: `003-app-enrichment`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description (roadmap G3): "Enhance Sadhana Setu with the newly gathered
information — surface the enriched Hari-Nāma corpus inside the app."

## Context

The corpus pipeline (`001`) and enrichment (`002`) produce reviewed, KG-grounded Hari-Nāma class
notes from senior Vaiṣṇavas. `005` already proved a focused surfacing path: the pre-japa "deepen"
stage retrieves one reviewed teaching from vidya-karana's **live ChromaDB**, filtered to
`kind=harinaam-note`, and displays clean text read from the note file (sidestepping kg-mcp's
static snapshot and vidya-karana's ingest mangling).

This feature **generalizes that pattern** into a shared retrieval capability and surfaces the
reviewed corpus across the app's other reading moments — Nama-Tattva, the Saturday check-in, and
a place to read the notes themselves — while honoring every Sattvic-Medium constraint. It does
**not** change the pipeline or enrichment; it consumes their output.

## Clarifications

### Session 2026-06-24

- Q: Which surfaces are in scope this round? → A: **All three** — Nama-Tattva, the Saturday check-in, AND a study/browse view of the notes.
- Q: Corpus vs. curated when a reviewed match exists? → A: **Prefer the corpus teaching**; the curated library is the fallback (mirrors `005`).
- Q: How to bound the ~2 s live-ChromaDB query cost? → A: **Cache the day's resolved teaching(s)** (keyed by date + theme) and reuse across all surfaces and re-opens.
- Q: Same teaching across surfaces in a day? → A: **De-duplicate within a day** — each surface gets a distinct reviewed teaching; surfaces with no fresh match fall back to curated.
- Q: What theme drives each surface's retrieval? → A: **Per-surface natural theme** — daily surfaces use the day's value; the Saturday check-in uses the week's sankalpa/focus.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A shared corpus-retrieval service (Priority: P1)

Any app surface can ask for one reviewed, themed Hari-Nāma teaching (or verse/pastime) by topic,
and get back clean, cited content — reusing the `005` retrieval pattern (live ChromaDB,
`kind=harinaam-note`, clean text from the note file), with graceful fallback to curated content.

**Why this priority**: Every other story depends on a single, consistent way to fetch reviewed
corpus content. Reimplementing `005`'s ad-hoc query per surface would drift and risk the review
gate. This is the foundation.

**Independent Test**: Call the service with a theme; confirm it returns a reviewed (`harinaam-note`)
teaching with clean text + citation, or a clear "no corpus match" so the caller can fall back.

**Acceptance Scenarios**:

1. **Given** reviewed notes exist, **When** a surface requests a teaching for a theme, **Then**
   the service returns clean, cited corpus content for that theme.
2. **Given** no reviewed match (or corpus offline), **When** a surface requests content, **Then**
   the service returns nothing and the surface falls back to its curated library — no error.
3. **Given** an unreviewed note, **When** any request is made, **Then** it is never surfaced
   (Constitution Principle V).

---

### User Story 2 - Enrich the daily Nama-Tattva (Priority: P1)

The daily Nama-Tattva teaching can draw from the **reviewed corpus** (senior Vaiṣṇavas on the
Holy Name) in addition to the existing curated library — cited to speaker + lecture — deepening
the daily teaching with the gathered material.

**Why this priority**: Nama-Tattva is the app's existing dedicated "teaching on the Name" slot;
it is the most natural and highest-value place for the corpus beyond pre-japa.

**Independent Test**: Open Nama-Tattva; confirm it can show a reviewed corpus teaching with
citation, stable within a day, falling back to the curated library when no match/offline.

**Acceptance Scenarios**:

1. **Given** a reviewed teaching matches today's theme, **When** Nama-Tattva renders, **Then** it
   shows that teaching with its citation.
2. **Given** no match, **When** Nama-Tattva renders, **Then** it shows the curated teaching as today.

---

### User Story 3 - Enrich the Saturday check-in (Priority: P2)

The Saturday check-in's rotating sastra-rooted questions/reflections can surface one reviewed
corpus teaching relevant to the week's theme or the devotee's current sankalpa — supporting honest
weekly reflection without quantifying anything.

**Why this priority**: The Saturday check-in is the primary weekly ritual; a themed corpus teaching
enriches reflection. It builds on US1 and is weekly (lower frequency than daily Nama-Tattva).

**Independent Test**: In the Saturday view, confirm an optional reviewed corpus teaching appears,
themed to the week, with no scoring/tracking, and absent gracefully when there's no match.

**Acceptance Scenarios**:

1. **Given** a reviewed teaching matches the week's theme, **When** the Saturday check-in renders,
   **Then** it offers that teaching as reflection support with citation.
2. **Given** none matches, **When** the check-in renders, **Then** no corpus block appears (clean
   absence, not an error).

---

### User Story 4 - Read the enriched notes in the app (Priority: P3)

The devotee can browse and read the reviewed enriched class notes within the app (a study view) —
by speaker, seminar, or theme — to go deeper than the daily glimpses.

**Why this priority**: The corpus is rich; a study/browse surface lets the devotee read full notes.
Valuable but secondary to weaving teachings into the existing daily/weekly rituals.

**Independent Test**: Open the study view; confirm reviewed notes are listed by speaker/seminar and
readable in clean form; unreviewed notes never appear.

**Acceptance Scenarios**:

1. **Given** reviewed notes exist, **When** the study view opens, **Then** they are browsable and
   readable (clean text + citations).
2. **Given** a note is only `draft`, **When** the study view opens, **Then** it is not shown.

---

### Edge Cases

- Corpus offline / vidya-karana venv unavailable → every surface falls back to curated content;
  no broken or empty states (mirrors `005`).
- The same teaching could surface in pre-japa AND Nama-Tattva on the same day → resolved:
  **de-duplicate within a day** (FR-013); each surface gets a distinct reviewed teaching.
- Latency: the live-ChromaDB query bridges to vidya-karana's venv (~2s) → resolved: **cache the
  day's retrieval(s) once** (FR-012), reused across surfaces and re-opens.
- Retrieval freshness: kg-mcp's snapshot is stale, so reviewed-note retrieval MUST use the live
  ChromaDB path (`005` pattern), not kg-mcp `search_corpus`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a **single shared corpus-retrieval capability** that returns
  one reviewed, themed teaching (clean text + citation) or nothing — generalizing `005`'s
  `harinaam_teaching`.
- **FR-002**: Retrieval MUST use the **live ChromaDB `kind=harinaam-note` path** (only reviewed
  notes; Constitution V), NOT kg-mcp's static snapshot.
- **FR-003**: Displayed corpus text MUST be **clean** (read from the note file, not the mangled
  ChromaDB chunk) and **cited** (speaker + lecture).
- **FR-004**: Every enriched surface MUST **fall back gracefully** to its curated library when
  there is no match or the corpus is unavailable (no error, no empty break).
- **FR-005**: Enriched content MUST be **stable within a day** (daily surfaces) / week (weekly).
- **FR-006**: All enriched surfaces MUST honor the **Sattvic-Medium** constraints (no streaks,
  scoring, push, gamification, screen-during-japa) — Constitution Principle IV.
- **FR-007**: The system MUST enrich the **Nama-Tattva** surface (US2).
- **FR-008**: The system MUST enrich the **Saturday check-in** surface (US3).
- **FR-009**: The system MUST provide a **study/browse view** of reviewed notes (US4) — in scope
  this round.
- **FR-010**: The surfaces in scope for this round are **Nama-Tattva, the Saturday check-in, and
  the study/browse view** (all three).
- **FR-011**: When a reviewed corpus teaching matches, the surface MUST **prefer the corpus
  teaching** and use its curated library as the fallback (one best teaching, not both).
- **FR-012**: Retrieval MUST be **cached per day**: the day's teaching(s) are resolved once (keyed
  by date + theme) and reused across all surfaces and re-opens, bounding the live-ChromaDB cost.
- **FR-013**: Corpus teachings MUST be **de-duplicated within a day** across surfaces — each
  surface gets a distinct reviewed teaching; a surface with no remaining fresh match falls back to
  curated.
- **FR-014**: Each surface MUST retrieve by its **natural theme** — daily surfaces (Nama-Tattva)
  by the day's value; the Saturday check-in by the week's sankalpa/focus.

### Key Entities *(include if feature involves data)*

- **Corpus Teaching (retrieved)**: one reviewed, themed unit (clean text + citation + speaker +
  lecture) returned by the shared retrieval capability.
- **Enriched Surface**: an existing app view (Nama-Tattva, Saturday check-in, study view) that
  consumes the retrieval capability with a curated fallback.
- **Retrieval Cache**: the day's resolved teachings keyed by date + theme, reused across surfaces
  (FR-012) and tracking what has already been surfaced today to enforce de-duplication (FR-013).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of corpus content shown is reviewed (`harinaam-note`) and cited — zero
  unreviewed or uncited corpus content reaches any surface.
- **SC-002**: 100% of displayed corpus text is clean (no ingest-mangled diacritics).
- **SC-003**: Every enriched surface renders with graceful curated fallback whether or not the
  corpus is available — zero broken/empty states.
- **SC-004**: A design/UX + tattva review confirms **zero** Sattvic-Medium violations across all
  enriched surfaces (same bar as the v1 audit).
- **SC-005**: Enriched surfaces are stable within their period (day/week).

## Assumptions

- Consumes the **reviewed** output of `001`/`002`; does not modify the pipeline or enrichment.
- Reuses and generalizes the `005` retrieval pattern (live ChromaDB, `kind=harinaam-note`, clean
  text from note file, graceful fallback) — see `specs/005-prejapa-transformation`.
- kg-mcp's snapshot is stale for freshly-ingested notes (documented in `002`), so reviewed-note
  retrieval uses the live ChromaDB path, not kg-mcp `search_corpus`.
- Single-practitioner audience for this round; multi-user is out of scope.
- Honors all v1 sacred constraints; enrichment adds depth, never metrics or length.
