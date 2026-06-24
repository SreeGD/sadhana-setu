---
description: "Task list for 003-app-enrichment"
---

# Tasks: App Enrichment from the Hari-Nāma Corpus

**Input**: Design documents from `specs/003-app-enrichment/`
**Prerequisites**: plan.md, spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md.
Reuses `005`'s retrieval bridge + `corpus/notes/` files; consumes reviewed `002` output.

**Tests**: INCLUDED — the shared service's cache + dedup + review-gate + clean-text are
trust-critical; views get import-safe smoke tests. ChromaDB bridge is injected (no network/venv).

**Organization**: By user story (US1–US4 from spec.md).

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[USn]**: user-story label (story phases only)

## Clarification note

Spec `## Clarifications` (2026-06-24): all three surfaces in scope (Nama-Tattva + Saturday + study
view); prefer corpus, curated fallback; cache the day's retrieval(s); de-duplicate within a day;
per-surface theme (daily=value, Saturday=sankalpa). No `[NEEDS CLARIFICATION]` open.

---

## Phase 1: Setup

- [ ] T001 Create module skeletons `sadhana_setu/flows/corpus_teaching.py`, `sadhana_setu/flows/corpus_notes.py`, and test files `tests/test_corpus_teaching.py`, `tests/test_corpus_notes.py`
- [ ] T002 [P] Add "Nama-Tattva" and "Notes" placeholders to `VIEWS` + dispatch stubs in `sadhana_setu/ui/app.py` (wired in later phases)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [ ] T003 Extract the reusable candidate query + clean-text-from-note helpers from `sadhana_setu/flows/harinaam_teaching.py` into shared functions (no behavior change yet) so `corpus_teaching.py` can reuse them
- [ ] T004 Implement `new_state()` + the per-`(date, theme)` candidate cache scaffold in `sadhana_setu/flows/corpus_teaching.py` (per contracts/corpus-teaching.md)

**Checkpoint**: shared retrieval primitives + cache scaffold ready.

---

## Phase 3: User Story 1 — Shared corpus-retrieval service (P1) 🎯 MVP

**Goal**: One cached, de-duplicating, review-gated retrieval path that any surface can call.
**Independent test**: with an injected querier + state, repeated calls return distinct reviewed teachings (cached, deduped), and None when exhausted/offline.

- [ ] T005 [US1] Implement `get_for_surface(theme, surface_id, *, date, state, querier)` in `sadhana_setu/flows/corpus_teaching.py`: resolve candidates (cached per date+theme), return top not in `state["surfaced"]`, mark it; clean text + citation; None on no-match/offline (FR-001/002/003/004/012/013)
- [ ] T006 [US1] Refactor `sadhana_setu/flows/harinaam_teaching.py::fetch_teaching` to delegate to `corpus_teaching` with a shared `state`, so pre-japa joins the dedup (plan R1/decision 6)
- [ ] T007 [US1] Wire pre-japa to pass the per-day `state` (`st.session_state["corpus_<date>"]`) in `sadhana_setu/ui/prejapa_view.py`
- [ ] T008 [P] [US1] Test `tests/test_corpus_teaching.py` (injected querier + plain state): review-gate (only harinaam-note), clean text, cache hit (querier called once per theme), **within-day stability** (a second call for the same date/theme/surface returns the same teaching — SC-005), dedup (distinct lecture_ids), None on offline/exhausted (SC-001/002, FR-012/013)

**Checkpoint**: the shared service works; pre-japa uses it.

---

## Phase 4: User Story 2 — Nama-Tattva surface (P1)

**Goal**: A dedicated daily teaching view that prefers a reviewed corpus teaching.
**Independent test**: open Nama-Tattva; shows a reviewed corpus teaching (cited) for today's value, or curated fallback; distinct from pre-japa's (dedup).

- [ ] T009 [US2] Implement `sadhana_setu/ui/nama_tattva_view.py`: theme = `pick_today_value`; call `corpus_teaching.get_for_surface(..., "nama-tattva", state=...)`; render corpus teaching, else curated `nama_tattva` (FR-007/011)
- [ ] T010 [US2] Add "Nama-Tattva" to `VIEWS` + dispatch in `sadhana_setu/ui/app.py`
- [ ] T011 [P] [US2] Import-safe smoke test of `nama_tattva_view.render` wiring in `tests/test_corpus_teaching.py`

**Checkpoint**: Nama-Tattva renders corpus-preferred with curated fallback.

---

## Phase 5: User Story 3 — Saturday check-in enrichment (P2)

**Goal**: An optional corpus teaching in the Saturday reflection, themed by the week's sankalpa.
**Independent test**: open Saturday with a check-in present; an optional corpus teaching themed by tone/mood_bhava appears (cited), absent cleanly otherwise; no scoring.

- [ ] T012 [US3] In `sadhana_setu/ui/saturday_view.py`: theme = `get_checkin(most_recent_saturday()).tone`/`mood_bhava` (fallback to day's value); call `corpus_teaching.get_for_surface(..., "saturday", state=...)`; render optionally; absent cleanly when None (FR-008/014)
- [ ] T013 [P] [US3] Test that the Saturday theme derives from the week's sankalpa + absent-on-None in `tests/test_corpus_teaching.py`

**Checkpoint**: Saturday reflection offers a themed corpus teaching.

---

## Phase 6: User Story 4 — Study / Notes view (P3)

**Goal**: Browse + read the reviewed enriched notes.
**Independent test**: open Notes; reviewed notes listed by speaker/seminar and readable; drafts never shown; empty-state when none.

- [ ] T014 [US4] Implement `sadhana_setu/flows/corpus_notes.py`: `list_reviewed_notes()` (enumerate `corpus/notes/**/*.md`, front-matter `status: reviewed` only) + `read_note(path)` (contracts/study-view.md)
- [ ] T015 [US4] Implement `sadhana_setu/ui/notes_view.py`: list reviewed notes grouped by speaker/seminar; render selected note's Markdown; empty-state message (FR-009)
- [ ] T016 [US4] Add "Notes" to `VIEWS` + dispatch in `sadhana_setu/ui/app.py`
- [ ] T017 [P] [US4] Test `tests/test_corpus_notes.py`: reviewed-only enumeration, draft excluded, front-matter/body parse (SC-001)

**Checkpoint**: reviewed notes are browsable in-app.

---

## Phase 7: Polish & Cross-Cutting

- [ ] T018 [P] Sattvic-medium audit across the new surfaces (no metrics/scoring/streaks/push) + cross-check `quickstart.md` (SC-004)
- [ ] T019 [P] Verify graceful curated fallback + no broken/empty states across the enriched surfaces (`sadhana_setu/ui/nama_tattva_view.py`, `saturday_view.py`, `notes_view.py`) when the corpus is offline (FR-004/SC-003)
- [ ] T020 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

---

## Dependencies

- **Setup (P1)** → **Foundational (P2)** → user stories.
- **US1** (shared service) is the MVP and blocks US2/US3 (they consume it). US4 (study view) is
  independent of the service (reads notes from disk) and can proceed in parallel with US2/US3.
- `[P]` tasks within a phase touch different files and may run in parallel.

## Parallel execution examples

- Phase 3: T008 (tests) alongside finishing T005–T007.
- US4 (T014–T017) can run in parallel with US2/US3 once Foundational is done (disk-based, no service dep).

## Implementation strategy

- **MVP = Phases 1–4 (US1 + US2)**: the shared service + Nama-Tattva surfacing reviewed teachings
  — the core "enhance the app with the corpus" value.
- Then **US3** (Saturday) and **US4** (study view) as incremental slices.
- Stop after each phase for a working, testable increment.
