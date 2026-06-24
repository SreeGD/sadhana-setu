---
description: "Task list for 001-corpus-pipeline"
---

# Tasks: Hari-Nāma Corpus Pipeline

**Input**: Design documents from `specs/001-corpus-pipeline/`

**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Included — this pipeline's correctness (idempotency, provenance) is testable and
worth guarding. Keep them small and fixture-based (no network in CI).

**Organization**: Grouped by user story so each slice is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md

## Phase 0: Research (resolve before building)

- [x] T001 Resolve `[NEEDS CLARIFICATION]` FR-013/FR-014/FR-015 via `/speckit-clarify` — **done (Session 2026-06-24)**; see spec `## Clarifications`
- [ ] T002 [P] Survey `audio.iskcondesiretree.com` listing structure + terms of use (research R2)
- [ ] T003 [P] Read-only reuse audit of vidya-karana `audio_daemon.py` / `agents/pipeline.py` / `corpus_processor.py`; produce reuse map (research R3)
- [ ] T004 [P] Benchmark whisper.cpp models on 2–3 sample lectures; pin model + flags (research R1, R7)

## Phase 1: Setup (Shared Infrastructure)

- [ ] T005 Create `corpus/` content tree: `corpus/README.md`, `corpus/sources/`, `corpus/transcripts/` (per plan.md structure)
- [ ] T006 Add `.gitignore` entry for `corpus/.audio-cache/`; confirm no audio can be staged
- [ ] T007 Create `sadhana_setu/corpus/` sub-package skeleton (`__init__.py`, `cli.py` stub) and `tests/corpus/`
- [ ] T008 [P] Add pipeline deps to `pyproject.toml` (httpx, pyyaml already may be present; ffmpeg/whisper-cli are system tools)

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [ ] T009 Define manifest schema + transcript front-matter contract in `specs/001-corpus-pipeline/contracts/` and `data-model.md`
- [ ] T010 Implement `sadhana_setu/corpus/manifest.py`: load/validate/update YAML manifest; entry status enum
- [ ] T011 [P] Unit test `tests/corpus/test_manifest.py`: schema validation, status transitions, round-trip
- [ ] T012 Seed `corpus/sources/manifest.yaml` with the 5 speaker sets + Holy Name seminar set(s) (entries can start empty/pending)

## Phase 3: User Story 1 — Register source & fetch audio (P1) 🎯 MVP

**Goal**: A manifest entry's audio downloads to the git-ignored cache with a recorded checksum.

- [ ] T013 [US1] Implement `sadhana_setu/corpus/fetch.py`: download to `corpus/.audio-cache/`, compute SHA-256, write to manifest, set status `fetched`
- [ ] T014 [US1] Idempotency: reuse cached file when checksum matches; provenance error on mismatch (FR-007, FR-012)
- [ ] T015 [US1] Mark dead/forbidden sources `unavailable`/`excluded` with reason (FR-011)
- [ ] T016 [US1] Wire `fetch` into `cli.py` (`python -m sadhana_setu.corpus fetch [--set NAME]`)
- [ ] T017 [P] [US1] Test `tests/corpus/test_fetch.py` with a tiny local fixture (no network): checksum, idempotency, mismatch error

**Checkpoint**: One lecture goes URL → cached audio + checksum, nothing committed but the manifest.

## Phase 4: User Story 2 — Transcribe verbatim with whisper.cpp (P1)

**Goal**: Fetched audio → committed, timestamped, provenance-bearing transcript.

- [ ] T018 [US2] Implement `sadhana_setu/corpus/transcribe.py`: invoke `whisper-cli` with pinned model/flags; capture timestamps
- [ ] T019 [US2] Long-audio chunking via ffmpeg with offset-corrected timestamps (research R7)
- [ ] T020 [US2] Write transcript to `corpus/transcripts/<set>/<slug>.md` with front-matter (FR-005); set status `transcribed`
- [ ] T021 [US2] Idempotency: skip if transcript for that checksum + model exists; explicit `--retranscribe` to override (FR-007)
- [ ] T022 [US2] Wire `transcribe` into `cli.py`
- [ ] T023 [P] [US2] Test `tests/corpus/test_transcribe.py` on a short fixture clip: front-matter correctness, timestamps present, idempotency

**Checkpoint**: Lecture → committed verbatim transcript ready for review and for 002 enrichment.

## Phase 5: User Story 3 — Curate by speaker & seminar (P2)

**Goal**: Run scoped to a source set; see per-set progress.

- [ ] T024 [US3] Implement `sadhana_setu/corpus/sets.py`: group entries by set; scoped run filter
- [ ] T025 [US3] `status` command: per-set pending/fetched/transcribed counts (FR-010)
- [ ] T026 [US3] Duplicate-audio detection by checksum across sets; record alternate URLs (FR-009)
- [ ] T027 [P] [US3] Test set scoping + status report + dedup

## Phase 6: User Story 4 — Reproduce on a fresh machine (P3)

**Goal**: Manifest-only reproducibility proven end-to-end.

- [ ] T028 [US4] `verify` command: re-fetch from manifest, assert checksums match recorded values (SC-004)
- [ ] T029 [US4] Document the reproduce flow in `quickstart.md` (clone → fetch → transcribe)
- [ ] T030 [P] [US4] Test that a clean run over a processed corpus yields no transcript diffs (SC-002)

## Phase 7: Polish

- [ ] T031 [P] `quickstart.md` maintainer runbook finalized
- [ ] T032 Update `corpus/README.md` with conventions + per-set directory map
- [ ] T033 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

## Dependencies

- Phase 0 research (esp. T001 clarifications) precedes Phase 2 schema decisions.
- US2 depends on US1 (must fetch before transcribe). US3/US4 depend on US1+US2.
- `[P]` tasks within a phase touch different files and may run in parallel.
