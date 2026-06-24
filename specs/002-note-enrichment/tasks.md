---
description: "Task list for 002-note-enrichment"
---

# Tasks: Note Enrichment

**Input**: Design documents from `specs/002-note-enrichment/`

**Prerequisites**: plan.md (required), spec.md (required), research.md;
**depends on `001-corpus-pipeline`** producing committed transcripts.

**Tests**: Included — grounding correctness and the review gate are the trust-critical paths.

**Organization**: Grouped by user story (US1–US5 from spec.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5

## Phase 0: Research (resolve before building)

- [ ] T001 Resolve `[NEEDS CLARIFICATION]` FR-013/FR-014/FR-015 via `/speckit-clarify` (R4/R5/R1)
- [ ] T002 [P] Document `kg-mcp` tool contracts for grounding (research R2) into `contracts/`
- [ ] T003 [P] Read-only audit of vidya-karana ChromaDB back-ingest path (research R3)
- [ ] T004 [P] Draft + golden-test the enrichment prompt contract & section schema (research R6)

## Phase 1: Setup

- [ ] T005 Create `corpus/notes/` content tree mirroring `corpus/transcripts/` set structure
- [ ] T006 Add note-enrichment deps to `pyproject.toml` (LLM client per FR-015; reuse existing MCP client)
- [ ] T007 Define note front-matter + citation + review-record schema in `data-model.md` and `contracts/`

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [ ] T008 Implement `sadhana_setu/corpus/notes.py`: read/write notes, front-matter, status state machine (`draft`/`reviewed`)
- [ ] T009 [P] Test `tests/corpus/test_notes.py`: front-matter round-trip, status transitions
- [ ] T010 Implement `sadhana_setu/corpus/grounding.py`: resolve candidate citations via `kg-mcp`; mark `[UNVERIFIED]`; offline fail-safe (FR-002, FR-003, FR-010)
- [ ] T011 [P] Test `tests/corpus/test_grounding.py` with mocked `kg-mcp`: verified vs unverified vs offline

## Phase 3: User Story 1 — Generate enriched class notes (P1) 🎯 MVP

**Goal**: Transcript → structured draft note with all required sections + timestamp back-links.

- [ ] T012 [US1] Implement `sadhana_setu/corpus/enrich.py`: call LLM with the prompt contract; parse sections + candidate citations + timestamp anchors
- [ ] T013 [US1] Render note via `notes.py` to `corpus/notes/<set>/<slug>.md` with provenance front-matter, `status: draft` (FR-001, FR-005, FR-006)
- [ ] T014 [US1] Idempotency: skip if a note for that transcript+enrichment-version exists; `--regenerate` resets to draft + bumps version (FR-009)
- [ ] T015 [US1] Wire `enrich` into `cli.py` (`python -m sadhana_setu.corpus enrich [--set NAME]`)
- [ ] T016 [P] [US1] Test `tests/corpus/test_enrich.py` on a short fixture transcript with a stubbed LLM: all sections present, timestamps linked, marked draft

**Checkpoint**: One transcript → committed structured draft note.

## Phase 4: User Story 2 — Ground verses/references in the KG (P1)

**Goal**: Every published verse/reference comes from `kg-mcp`, not the LLM.

- [ ] T017 [US2] Integrate `grounding.py` into the enrich flow: LLM proposes candidate references only; grounding substitutes authoritative KG text (FR-002, FR-012)
- [ ] T018 [US2] `[UNVERIFIED]` handling: withhold ungrounded citations from the verified body, list them in a review section (FR-003)
- [ ] T019 [US2] Fail-safe: if `kg-mcp` offline, do not emit verses as verified; mark note unverifiable (FR-010)
- [ ] T020 [P] [US2] Extend grounding tests for substitution + withholding + offline behavior

**Checkpoint**: Notes contain only KG-grounded verses; SC-001 testable.

## Phase 5: User Story 3 — Cross-references to purports & related teachings (P2)

**Goal**: Grounded cross-references deepen each note.

- [ ] T021 [US3] Add cross-reference generation: query `cross_author_chunks`/`search_corpus` for related purports/teachings per key teaching (FR-004)
- [ ] T022 [US3] Render cross-references with resolvable citations; reuse grounding for verification
- [ ] T023 [P] [US3] Test that each key teaching yields ≥1 grounded cross-reference

## Phase 6: User Story 4 — Review gate (P1)

**Goal**: Only devotee-approved notes are publishable.

- [ ] T024 [US4] Implement `sadhana_setu/corpus/review.py`: `review approve <note>` records reviewer + date, flips `draft → reviewed` (FR-007, FR-008)
- [ ] T025 [US4] Publish eligibility: exclude unreviewed notes from any publish/back-ingest step
- [ ] T026 [P] [US4] Test `tests/corpus/test_review.py`: approval flow + exclusion of unreviewed (SC-003)

**Checkpoint**: Review gate holds; nothing publishes without approval.

## Phase 7: User Story 5 — Back-ingest reviewed notes into the KG (P3)

**Goal**: Reviewed notes become queryable via `kg-mcp` for the app (003).

- [ ] T027 [US5] Implement `sadhana_setu/corpus/ingest.py`: add reviewed notes to vidya-karana ChromaDB via its existing path; key by note id (FR-011)
- [ ] T028 [US5] Idempotent replace on re-ingest; trigger/await KG refresh
- [ ] T029 [P] [US5] Test: after back-ingest, `kg-mcp` `search_corpus` retrieves a note passage (SC-005)

## Phase 8: Polish

- [ ] T030 [P] `quickstart.md`: enrich → review → publish → back-ingest runbook
- [ ] T031 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

## Dependencies

- Requires `001-corpus-pipeline` transcripts as input.
- Phase 0 clarifications (T001) precede schema + prompt decisions.
- Grounding (US2) underpins US3; review gate (US4) precedes back-ingest (US5).
- `[P]` tasks within a phase touch different files and may run in parallel.
