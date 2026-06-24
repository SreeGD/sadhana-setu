# Feature Specification: Pre-japa Reading for Transformation

**Feature Branch**: `005-prejapa-transformation`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Review prejapa reading to bring transformation."

## Context

The current Pre-japa view (`sadhana_setu/ui/prejapa_view.py`, v1.6 "Featured layout") is
**informational**: a daily-rotating featured card plus supporting cards (affirmation, faith
verse, inspiration, nāma-tattva, practical tip, Saturday bhajan) that the devotee glances at,
reads in under ~75 seconds, and closes. It informs well, but the brief asks for a reading that
**brings transformation** — that helps the devotee actually *enter* japa in the right
consciousness (attentive, humble, taking shelter of the Name), not merely learn something.

With the Hari-Nāma corpus now in place (`001`/`002` — reviewed, KG-grounded enriched notes from
senior Vaiṣṇavas, surfaced through `kg-mcp`), the pre-japa moment can draw on far richer,
transformational teaching than the current curated libraries alone. This feature redesigns the
pre-japa reading around **transformation outcomes** while honoring every Sattvic-Medium
constraint (no gamification, no streaks, no push, no quantifying the chanter).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enter japa in the right consciousness (Priority: P1)

Before chanting, the devotee opens the pre-japa reading and, in under a minute, is gently
brought into the mood for attentive chanting — a remembrance of *whose* Name this is, *who* the
chanter is, and the prayerful disposition (e.g. tṛṇād api sunīcena) — rather than only reading
facts about the Name.

**Why this priority**: This is the heart of "bring transformation" — the reading must shape
consciousness at the threshold of japa, the single most important daily act for this audience.

**Independent Test**: Open the reading; confirm it presents a short, contemplative invocation
that orients the devotee toward attentive chanting (not a list of facts), citation-bearing, in
under the time budget.

**Acceptance Scenarios**:

1. **Given** the devotee opens pre-japa, **When** the reading renders, **Then** it leads with a
   brief contemplative orientation toward attentive chanting (the chanter's disposition + the
   glory of the Name), with a citation.
2. **Given** the daily reading, **When** the devotee finishes it, **Then** it closes by pointing
   *into* japa (a resolve / prayer to carry into chanting), not into more reading.

---

### User Story 2 - A transformational teaching from the Hari-Nāma corpus (Priority: P1)

The reading surfaces one short, potent teaching drawn from the **reviewed enriched corpus**
(senior Vaiṣṇavas on the Holy Name) — e.g. on attentive hearing, the ten offenses, taking
shelter, or relishing the Name — grounded and cited, chosen to deepen today's chanting.

**Why this priority**: The corpus is the new material the brief was built to gather; the pre-japa
moment is where it most directly serves transformation. Without this, the redesign is cosmetic.

**Independent Test**: Confirm the reading includes one corpus-sourced teaching with a resolvable
citation (speaker + lecture, or book + verse), and that it varies day to day.

**Acceptance Scenarios**:

1. **Given** reviewed corpus content is available, **When** the reading renders, **Then** it
   surfaces one grounded Hari-Nāma teaching with its citation.
2. **Given** the corpus path is unavailable, **When** the reading renders, **Then** it falls back
   to the existing curated libraries with a clear, quiet indication (no error, no broken reading).

---

### User Story 3 - A contemplative micro-practice, not just a glance (Priority: P2)

Beyond reading, the devotee is offered a brief contemplative action that converts reading into
transformation — e.g. a single line to sit with, a prayer to repeat once, or a question to hold —
that takes seconds and asks nothing to be recorded or scored.

**Why this priority**: Transformation comes from a moment of *application*, not consumption. This
is the mechanism that distinguishes "reading to transform" from "reading to inform" — but it
layers on top of US1/US2.

**Independent Test**: Confirm the reading offers exactly one optional contemplative prompt that
requires no input, tracking, or scoring, and does not delay the start of japa.

**Acceptance Scenarios**:

1. **Given** the reading, **When** it renders, **Then** it offers one optional contemplative
   prompt (sit-with line / single prayer / holding-question).
2. **Given** the prompt, **When** the devotee engages or skips it, **Then** nothing is recorded,
   scored, or required (Constitution Principle IV).

---

### Edge Cases

- The reading must not become longer or heavier than the current ~1-minute budget — transformation
  through depth, not volume. [NEEDS CLARIFICATION: is the time budget still ~60–75s, or is a
  slightly longer contemplative reading acceptable?]
- During japa the screen must stay closed/silent (existing constraint) — the reading is *before*,
  never during.
- The devotee may open pre-japa multiple times a day → the reading is stable within a day (same
  orientation) so it can be returned to, not reshuffled on every open.
- Corpus offline → graceful fallback to curated libraries (US2 scenario 2).
- Content must never quantify or judge the devotee's chanting, add streaks, or push (Constitution
  Principle IV).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pre-japa reading MUST lead with a **contemplative orientation** toward attentive
  chanting (the chanter's disposition + the glory of the Name), not an information list.
- **FR-002**: The reading MUST **close by pointing into japa** — a resolve or prayer to carry into
  chanting — rather than into further reading.
- **FR-003**: The reading MUST surface one **transformational teaching from the reviewed Hari-Nāma
  corpus** (`002` notes via `kg-mcp`), grounded and cited.
- **FR-004**: All Sanskrit/verse/teaching content MUST be **citation-bearing and KG-grounded**
  (Constitution I/VIII) — never fabricated.
- **FR-005**: The reading MUST offer **one optional contemplative micro-practice** that requires
  no input, tracking, or scoring.
- **FR-006**: The reading MUST honor every **Sattvic-Medium** constraint: no streaks, badges,
  gamification, push, screen-during-japa, or quantifying/judging the chanter (Constitution IV).
- **FR-007**: The reading MUST be **stable within a day** (returning to it shows the same
  orientation) and rotate across days.
- **FR-008**: When the corpus/`kg-mcp` path is unavailable, the reading MUST **fall back
  gracefully** to the existing curated libraries with a quiet indicator (no error/broken layout).
- **FR-009**: The reading MUST stay within the established **brief time budget** so it remains a
  daily-sustainable threshold practice. [NEEDS CLARIFICATION: exact budget — keep ~60–75s?]
- **FR-010**: The redesign MUST define what happens to the **existing supporting cards**
  (affirmation, faith verse, inspiration, nāma-tattva, tip, bhajan). [NEEDS CLARIFICATION: are
  they restructured around the transformation arc, trimmed, or kept alongside?]
- **FR-011**: "Transformation" MUST have an observable, **non-quantifying** definition the design
  is evaluated against. [NEEDS CLARIFICATION: how do we know it "brings transformation" without
  measuring/scoring the devotee — e.g. design review against a rubric, the user's own felt sense?]
- **FR-012**: The redesign MUST define its **relationship to the Saturday check-in and Today
  capture** (does the pre-japa resolve connect to the weekly sankalpa?). [NEEDS CLARIFICATION]

### Key Entities *(include if feature involves data)*

- **Pre-japa Reading**: The daily threshold reading. Composed of an orientation, a corpus
  teaching, a contemplative prompt, and a closing resolve — each citation-bearing where applicable.
- **Transformation Arc**: The intended movement of the reading (orient → deepen → apply → enter
  japa); the organizing principle replacing the current "featured + supporting cards" layout.
- **Corpus Teaching**: A short, reviewed, KG-grounded teaching surfaced from `002` notes via
  `kg-mcp`, selected for today.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The reading completes within the agreed time budget (FR-009) — it stays a
  sustainable daily threshold practice, not a study session.
- **SC-002**: 100% of Sanskrit/verse/teaching content in the reading is citation-bearing and
  KG-grounded (zero fabricated content).
- **SC-003**: A design/UX + tattva review confirms **zero** Sattvic-Medium violations (no
  streaks/scoring/push/quantification) — same bar as the v1 audit.
- **SC-004**: The reading reliably renders (with graceful fallback) whether or not the corpus
  path is available — no broken or empty pre-japa state.
- **SC-005**: The reading ends pointing *into* japa (resolve/prayer), verified for every daily
  variation.

## Assumptions

- Builds on the existing `sadhana_setu/ui/prejapa_view.py` and content libraries; this is a
  **redesign of the reading**, not a new app.
- Draws transformational teachings from the **reviewed** `002` corpus via the existing `kg-mcp`
  path (`sadhana_setu/mcp_client.py`); unreviewed notes are never surfaced (Constitution V).
- Likely depends on `003-app-enrichment` for the corpus→app surfacing plumbing; this spec may be
  sequenced after or alongside it. [NEEDS CLARIFICATION: sequence vs 003]
- Honors all v1 sacred constraints; transformation is pursued through depth and disposition, not
  features, metrics, or length.
- Single-practitioner audience (the founder-as-user) for this round; multi-user is out of scope.
