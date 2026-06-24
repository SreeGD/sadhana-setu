---
description: "Task list for 005-prejapa-transformation"
---

# Tasks: Pre-japa Reading for Transformation

**Input**: Design documents from `specs/005-prejapa-transformation/`
**Prerequisites**: plan.md, spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md.
Surfaces reviewed `002` content but is **self-contained** (own `kg-mcp` call; not blocked by `003`).

**Tests**: INCLUDED — arc assembly + graceful fallback are the testable trust paths; the Streamlit
view gets an import-safe smoke test. Grounding/check-in calls are mocked; no browser, no network.

**Organization**: By user story (US1–US3 from spec.md).

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[USn]**: user-story label (story phases only)

## Clarification note

Spec `## Clarifications` (2026-06-24): self-contained kg-mcp call (not blocked by 003); existing
cards **restructured into the arc**; budget **~60–75s**; transformation judged by a **build-time
design-review rubric** (no runtime scoring); closing resolve from the reading with an **optional
sankalpa echo**. No `[NEEDS CLARIFICATION]` open.

---

## Phase 1: Setup

- [ ] T001 Create `data/contemplations.yaml` — a small curated set of micro-practice prompts (sit-with line / single prayer / holding-question), citation-bearing where verse-based
- [ ] T002 [P] Implement `sadhana_setu/content/contemplations.py` (loader + `pick_for_today`), mirroring `sadhana_setu/content/affirmations.py`
- [ ] T003 [P] Create module skeletons `sadhana_setu/flows/prejapa_reading.py`, `sadhana_setu/flows/harinaam_teaching.py`, and test files `tests/test_prejapa_reading.py`, `tests/test_harinaam_teaching.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [ ] T004 Define `PrejapaReading`, `ReadingStage`, `Contemplation`, `Resolve` dataclasses (per data-model.md) in `sadhana_setu/flows/prejapa_reading.py`
- [ ] T005 Implement `build_reading(d, *, caller, checkin_loader)` skeleton in `sadhana_setu/flows/prejapa_reading.py`: date-stable, injectable deps, returns a curated-only arc (no kg yet); never raises (contracts/reading-assembly.md)
- [ ] T006 [P] Test `tests/test_prejapa_reading.py`: `build_reading` returns all four stages and is stable for a fixed date

**Checkpoint**: arc skeleton assembles from curated content, date-stable.

---

## Phase 3: User Story 1 — Enter japa in the right consciousness (P1) 🎯 MVP

**Goal**: A coherent arc that orients toward attentive chanting and ends pointing into japa.
**Independent test**: open Pre-japa; the reading leads with a contemplative orientation and closes with a resolve into japa, within ~60–75s.

- [ ] T007 [US1] Implement the **orient** stage (affirmation sankalpa + Name-glory faith verse) in `sadhana_setu/flows/prejapa_reading.py` (FR-001)
- [ ] T008 [US1] Implement the **enter** stage in `sadhana_setu/flows/prejapa_reading.py`: a resolve drawn from the reading that points into japa (FR-002) + optional sankalpa echo via `sadhana_setu/flows/saturday.py::get_checkin` (FR-012)
- [ ] T009 [US1] Rewrite `sadhana_setu/ui/prejapa_view.py::render()` to render the arc (orient→deepen→apply→enter) + retained "screen silent during japa" footer; restructure/retain CSS (FR-010)
- [ ] T010 [P] [US1] Test `tests/test_prejapa_reading.py`: orient present; enter points into japa; sankalpa echo present-with-checkin / absent-without (FR-012)
- [ ] T011 [P] [US1] Import-safe smoke test of `prejapa_view.render` wiring (no browser) in `tests/test_prejapa_reading.py`

**Checkpoint**: the arc renders end-to-end on curated content.

---

## Phase 4: User Story 2 — A grounded Hari-Nāma teaching (P1)

**Goal**: The "deepen" stage surfaces one reviewed, KG-grounded teaching; graceful fallback offline.
**Independent test**: with kg-mcp + `harinaam-note` content, the deepen stage shows a cited teaching; with kg-mcp off, it falls back to curated with a quiet note.

- [ ] T012 [US2] Implement `sadhana_setu/flows/harinaam_teaching.py::fetch_teaching(theme, *, caller)`: `search_corpus` (kg_augmented), prefer metadata `kind="harinaam-note"`, return `ReadingStage | None`; never raises (contracts/reading-assembly.md, Constitution V)
- [ ] T013 [US2] Integrate the **deepen** stage in `sadhana_setu/flows/prejapa_reading.py`: corpus teaching → curated `nama_tattva` fallback; set `corpus_online` (FR-003/008)
- [ ] T014 [US2] Render a quiet "corpus offline — curated reading" note when `corpus_online` is False in `sadhana_setu/ui/prejapa_view.py` (FR-008)
- [ ] T015 [P] [US2] Test `tests/test_harinaam_teaching.py` with mocked `caller`: `harinaam-note` preferred; empty/offline → None
- [ ] T016 [P] [US2] Test deepen fallback + `corpus_online` flag + citation-present-for-corpus in `tests/test_prejapa_reading.py` (SC-002/004)

**Checkpoint**: deepen stage grounded with reliable fallback.

---

## Phase 5: User Story 3 — Contemplative micro-practice (P2)

**Goal**: One optional micro-practice that asks nothing to be recorded or scored.
**Independent test**: the reading offers exactly one optional prompt; engaging or skipping records nothing.

- [ ] T017 [US3] Implement the **apply** stage in `sadhana_setu/flows/prejapa_reading.py`: select one `Contemplation` (sit-with / prayer / question), no input/tracking (FR-005)
- [ ] T018 [US3] Render the apply stage in `sadhana_setu/ui/prejapa_view.py` — optional, skippable, records nothing (Constitution IV)
- [ ] T019 [P] [US3] Test `tests/test_prejapa_reading.py`: exactly one apply prompt present; no input/score side effects

**Checkpoint**: the full arc (orient→deepen→apply→enter) is complete.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T020 [P] Walk `specs/005-prejapa-transformation/contracts/review-rubric.md` against a rendered reading (and a few days' variations); record pass/fail (FR-011, SC-003)
- [ ] T021 [P] CSS polish in `sadhana_setu/ui/prejapa_view.py` + cross-check `quickstart.md` against the implemented arc
- [ ] T022 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

---

## Dependencies

- **Setup (P1)** → **Foundational (P2)** → user stories.
- **US1** is the MVP (the arc shell on curated content). **US2** fills the deepen stage with
  grounded content; **US3** adds the micro-practice. US2/US3 each slot into the US1 arc.
- `[P]` tasks within a phase touch different files and may run in parallel.

## Parallel execution examples

- Phase 1: T002, T003 in parallel.
- Phase 3: T010, T011 (tests) alongside finishing T007–T009.
- Phase 4: T015, T016 in parallel once T012–T013 exist.

## Implementation strategy

- **MVP = Phases 1–3 (US1)**: a coherent transformation arc that orients and points into japa,
  on curated content — already a real improvement over the card layout.
- Then **US2** (grounded teaching + fallback) and **US3** (micro-practice) as incremental slices.
- Stop after each phase for a working, testable increment.
