---
description: "Task list for 002-note-enrichment"
---

# Tasks: Note Enrichment

**Input**: Design documents from `specs/002-note-enrichment/`
**Prerequisites**: plan.md, spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md;
**depends on `001-corpus-pipeline`** (committed transcripts).

**Tests**: INCLUDED — grounding correctness and the review gate are trust-critical (Constitution
I/V). Tests mock `claude -p`, `call_tool_sync` (kg-mcp), and `CorpusProcessor`; no network.

**Organization**: By user story (US1–US5 from spec.md).

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[USn]**: user-story label (story phases only)

## Clarification note

Spec `## Clarifications` (2026-06-24): engine = **Claude Code headless** (`claude -p`, not API);
**one note per transcript**; transcript errors **annotate-only** (`[sic?: …]`); review via a
**Streamlit UI**; approval **auto-ingests** into ChromaDB + triggers KG rebuild. No `[NEEDS
CLARIFICATION]` open.

---

## Phase 1: Setup

- [X] T001 Add enrichment config to `sadhana_setu/corpus/config.py`: `enrichment_version`, `claude` CLI flags (`-p --output-format json`), and a `claude`/`kg-mcp` preflight
- [X] T002 [P] Add `corpus/notes/<set-id>/` convention + a notes section to `corpus/README.md`
- [X] T003 [P] Confirm `streamlit`/`pyyaml` deps in `pyproject.toml` (already present); add any enrichment-only dev deps

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [X] T004 Implement `sadhana_setu/corpus/notes.py`: ClassNote read/write, front-matter against `contracts/note-frontmatter.schema.json`, `draft → reviewed` state machine (data-model.md)
- [X] T005 [P] Test `tests/corpus/test_notes.py`: front-matter round-trip + status transitions + reviewed-requires-reviewer
- [X] T006 Implement `sadhana_setu/corpus/llm.py`: `Provider` interface + `ClaudeCodeProvider` (shells `claude -p --output-format json`), parse + validate output against `contracts/enrichment-output.schema.json`
- [X] T007 [P] Test `tests/corpus/test_llm.py`: parse/validate a stubbed `claude -p` JSON payload; schema-violation rejected

**Checkpoint**: note I/O + LLM provider ready.

---

## Phase 3: User Story 1 — Generate enriched class notes (P1) 🎯 MVP

**Goal**: One transcript → structured draft note with all sections + timestamp back-links.
**Independent test**: run `enrich` on a fixture transcript (stubbed provider); a draft note with all FR-001 sections appears, each teaching timestamped, marked `draft`.

- [X] T008 [US1] Implement `sadhana_setu/corpus/enrich.py`: load a `001` transcript, call the provider with the prompt contract, parse `key_teachings`/`glossary`/`practical_application`/`sic_flags`
- [X] T009 [US1] Render + write the draft note to `corpus/notes/<set-id>/<lecture-id>.md` via `notes.py` with provenance front-matter, `status: draft` (FR-001/005); inline `[sic?: …]` flags (FR-014). The maintainer commits notes to git (FR-006; documented in `quickstart.md`)
- [X] T010 [US1] Idempotency: skip existing note for the same transcript + `enrichment_version`; `--regenerate` resets to draft + bumps version (FR-009)
- [X] T011 [US1] Wire `enrich` into `sadhana_setu/corpus/cli.py` (`python -m sadhana_setu.corpus enrich [--set NAME]`)
- [X] T012 [P] [US1] Test `tests/corpus/test_enrich.py` on a fixture transcript with a stubbed provider (golden file): all sections present, timestamps linked, `draft`; and `--regenerate` on a `reviewed` note resets it to `draft` + bumps version (FR-009 — not silently invalidated)

**Checkpoint**: transcript → committed structured draft note.

---

## Phase 4: User Story 2 — Ground verses in the KG (P1)

**Goal**: Every published verse comes from `kg-mcp`, not the LLM.
**Independent test**: a candidate `verse_ref` resolves to the `get_verse` text; an unresolvable one is `[UNVERIFIED]`; kg-mcp offline → fail-safe.

- [X] T013 [US2] Implement `sadhana_setu/corpus/grounding.py`: resolve `candidate_verse_refs` via `call_tool_sync("get_verse", {"verse_ref": …})`; substitute authoritative `iast`/`translation` (contracts/grounding.md)
- [X] T014 [US2] `[UNVERIFIED]` handling (withhold ungrounded from body) + `kg_status` offline fail-safe in `sadhana_setu/corpus/grounding.py` (FR-003/010)
- [X] T015 [US2] Integrate `grounding.py` into `enrich.py` so the note body's `verses_cited` are KG-sourced only (FR-002/012)
- [X] T016 [P] [US2] Test `tests/corpus/test_grounding.py` with mocked `call_tool_sync`: verified / `[UNVERIFIED]` / offline fail-safe

**Checkpoint**: notes contain only KG-grounded verses (SC-001).

---

## Phase 5: User Story 3 — Cross-references (P2)

**Goal**: Grounded cross-references deepen each note.
**Independent test**: each key teaching yields ≥1 grounded cross-reference that resolves in the KG.

- [X] T017 [US3] Cross-reference generation in `sadhana_setu/corpus/grounding.py`: resolve `candidate_cross_refs` via `search_corpus`/`cross_author_chunks`; render with citations (FR-004)
- [X] T018 [P] [US3] Test `tests/corpus/test_grounding.py` (cross-ref cases): grounded vs dropped

**Checkpoint**: notes carry grounded purport/teaching cross-links.

---

## Phase 6: User Story 4 — Review gate via Streamlit UI (P1)

**Goal**: Only devotee-approved notes are publishable; approval happens in a UI.
**Independent test**: approve a draft in the UI → status `reviewed` + reviewer/date; unreviewed notes excluded from publish/ingest.

- [X] T019 [US4] Implement `sadhana_setu/corpus/review.py`: `approve(note, reviewer)` → `draft → reviewed` (+ `reviewed_at`), publish-eligibility check (FR-007/008)
- [X] T020 [US4] Implement `sadhana_setu/ui/review_view.py` (Streamlit): list drafts, render note + `[UNVERIFIED]`/`[sic?]` aids, Approve action
- [X] T021 [US4] Wire the Approve action to call `review.approve` then trigger back-ingest (US5)
- [X] T022 [P] [US4] Test `tests/corpus/test_review.py`: approval flow + exclusion of unreviewed (SC-003)

**Checkpoint**: review gate holds; nothing publishes without approval.

---

## Phase 7: User Story 5 — Auto back-ingest into the KG (P3)

**Goal**: Approving a note ingests it (verified body) into ChromaDB → KG.
**Independent test**: approve → `CorpusProcessor.ingest_text` called with the verified body keyed by note id; re-approve replaces, not duplicates.

- [X] T023 [US5] Implement `sadhana_setu/corpus/ingest.py`: call `CorpusProcessor.ingest_text(text, source_id=note_id, metadata=…)` with the **verified body only**; idempotent replace (contracts/ingest.md, FR-011)
- [X] T024 [US5] Trigger KG rebuild + record `ingested_at`; fail-safe queue if ChromaDB/trigger unavailable
- [X] T025 [P] [US5] Test `tests/corpus/test_ingest.py` with mocked `CorpusProcessor`: verified-body-only, idempotent replace by `source_id` (SC-005)

**Checkpoint**: approved notes reachable via `kg-mcp` for the app (003).

---

## Phase 8: Polish & Cross-Cutting

- [X] T026 [P] Cross-check `specs/002-note-enrichment/quickstart.md` against the implemented commands/UI
- [X] T027 [P] Module docstrings + consistent CLI/UI messaging across `sadhana_setu/corpus/`
- [X] T028 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

---

## Dependencies

- **Setup (P1)** → **Foundational (P2)** → user stories.
- **US1** is the MVP. **US2** grounding underpins US1's *published* validity (a note with ungrounded
  verses is not publishable) — implement US1 structure, then US2 before any note is approved.
- **US3** builds on US2 grounding. **US4** (review) precedes **US5** (ingest); US5 is wired to the
  US4 approval action.
- `[P]` tasks within a phase touch different files and may run in parallel.

## Parallel execution examples

- Phase 2: T005, T007 in parallel after T004/T006 land.
- Phase 3: T012 alongside finishing T008–T011.
- Phase 4–5: grounding tests T016/T018 in parallel with their sibling implementations.

## Implementation strategy

- **MVP = Phases 1–4 (US1 + US2)**: a structured, KG-grounded draft note is the irreducible value
  (an ungrounded note is not trustworthy).
- Then **US3** (cross-refs), **US4** (review UI), **US5** (auto-ingest) as incremental slices.
- Stop after each phase for a working, testable increment.
