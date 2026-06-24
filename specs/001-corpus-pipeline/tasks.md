---
description: "Task list for 001-corpus-pipeline"
---

# Tasks: Hari-Nāma Corpus Pipeline

**Input**: Design documents from `specs/001-corpus-pipeline/`
**Prerequisites**: plan.md, spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — plan.md mandates pytest unit + one end-to-end fixture test, and the spec's
acceptance scenarios (idempotency, provenance, reproducibility) are trust-critical. Tests use
small local fixtures; no network in CI.

**Organization**: By user story (US1–US4 from spec.md) so each slice is independently testable.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[USn]**: user-story label (story phases only)

## Clarification note

Spec `## Clarifications` (2026-06-24) bounds Round 1: Holy Name seminars in full + Holy-Name-topic
speaker lectures; non-English ⇒ `deferred`; segment timestamps; always whisper.cpp
(`ggml-large-v3-turbo`); hybrid seed (assisted listing + manual). No `[NEEDS CLARIFICATION]` open.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create `sadhana_setu/corpus/__init__.py`, `sadhana_setu/corpus/cli.py` (stub), and `tests/corpus/__init__.py`
- [X] T002 [P] Add pipeline deps (`httpx`, `pyyaml`, `python-dateutil`) to `pyproject.toml`; document system tools (`whisper-cli`, `ffmpeg`) in `corpus/README.md`
- [X] T003 [P] Implement `sadhana_setu/corpus/config.py`: resolve audio cache dir (`CORPUS_AUDIO_CACHE`), model dir/name (`WHISPER_MODEL_DIR`/`WHISPER_MODEL`, default `ggml-large-v3-turbo`), pinned whisper flags, fetch rate-limit — all from env with defaults
- [X] T004 [P] Add tool-presence preflight (`whisper-cli`, `ffmpeg`, model file) raising exit-code 3 in `sadhana_setu/corpus/config.py`; document one-time model download in `quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [X] T005 Implement `sadhana_setu/corpus/manifest.py`: load/validate/save manifest against `contracts/manifest.schema.json`; typed `Lecture`/`SourceSet` access
- [X] T006 [P] Implement the `Lecture` status state machine (transitions per data-model.md) in `sadhana_setu/corpus/manifest.py`
- [X] T007 [P] Implement transcript front-matter render/parse against `contracts/transcript-frontmatter.schema.json` in `sadhana_setu/corpus/transcript.py`
- [X] T008 [P] Test manifest schema validation + status transitions in `tests/corpus/test_manifest.py`
- [X] T009 Implement ffmpeg helpers (decode to 16 kHz mono WAV; ~10-min silence-boundary segmentation) in `sadhana_setu/corpus/audio.py` (research R7)
- [X] T010 Implement `cli.py` command dispatch for `seed`/`fetch`/`transcribe`/`status`/`verify` + global options per `contracts/cli.md`

**Checkpoint**: manifest + transcript I/O + audio helpers + CLI skeleton ready.

---

## Phase 3: User Story 1 — Register source & fetch audio (P1) 🎯 MVP

**Goal**: A manifest entry's audio downloads to the git-ignored cache with a recorded checksum.
**Independent test**: add one lecture URL, run `fetch`, confirm cached audio + recorded `sha256`, nothing audio staged in git.

- [X] T011 [US1] Implement `sadhana_setu/corpus/seed.py`: parse a speaker/seminar listing into draft `pending` entries, apply FR-014 topic filter, capture `title`/`urls`/`date`/`topic_tags` and a declared `language` (default `en`) (research R2)
- [X] T012 [US1] Implement `sadhana_setu/corpus/fetch.py`: serial rate-limited download to `<cache>/<sha256>.<ext>`, compute SHA-256, record `sha256`/`duration_seconds`, set `status: fetched`
- [X] T013 [US1] Fetch idempotency (reuse cache on hash match) + checksum-mismatch provenance error (exit 1) in `sadhana_setu/corpus/fetch.py` (FR-007, FR-012)
- [X] T014 [US1] In `sadhana_setu/corpus/fetch.py`: dead URL ⇒ `unavailable`, forbidden ⇒ `excluded`; confirm language via a cheap detect on a short audio sample (seed-declared `language` is the default) and set non-English ⇒ `deferred` **before any transcription** (FR-011, FR-013)
- [X] T015 [US1] Wire `seed` and `fetch` into `sadhana_setu/corpus/cli.py`
- [X] T016 [P] [US1] Test fetch with a local fixture (no network): checksum, idempotency, mismatch error in `tests/corpus/test_fetch.py`
- [X] T017 [P] [US1] Test seed parser against a saved listing HTML fixture in `tests/corpus/test_seed.py`

**Checkpoint**: lecture → cached audio + checksum; only the manifest changes in git.

---

## Phase 4: User Story 2 — Transcribe verbatim with whisper.cpp (P1)

**Goal**: Fetched audio → committed, segment-timestamped, provenance-bearing transcript.
**Independent test**: with one lecture fetched, run `transcribe`, confirm a transcript under `corpus/transcripts/` with valid front-matter + timestamps.

- [X] T018 [US2] Implement `sadhana_setu/corpus/transcribe.py`: invoke `whisper-cli` with pinned `ggml-large-v3-turbo` + segment-timestamp flags
- [X] T019 [US2] Long-audio chunking via `audio.py` + offset-corrected timestamp stitching in `sadhana_setu/corpus/transcribe.py` (research R7)
- [X] T020 [US2] Write `corpus/transcripts/<set>/<id>.md` with front-matter via `transcript.py`; set `status: transcribed`, `transcript_path`, `whisper_model` (FR-005)
- [X] T021 [US2] Idempotency (skip existing for `sha256`+model; `--retranscribe` override) + chunk-failure quarantine in `sadhana_setu/corpus/transcribe.py` (FR-007)
- [X] T022 [US2] Wire `transcribe` into `sadhana_setu/corpus/cli.py`
- [X] T023 [P] [US2] Test transcribe on a short fixture clip (front-matter valid, timestamps present, idempotent) in `tests/corpus/test_transcribe.py`

**Checkpoint**: lecture → committed verbatim transcript, ready for 002 enrichment.

---

## Phase 5: User Story 3 — Curate by speaker & seminar (P2)

**Goal**: Run scoped to a source set; see per-set progress; dedup by checksum.
**Independent test**: define two sets, run scoped to one, confirm only it processed and status reports per-set counts.

- [X] T024 [US3] Implement set grouping + `--set` scoped-run filter in `sadhana_setu/corpus/sets.py`
- [X] T025 [US3] Implement `status` report (per-set pending/fetched/transcribed/deferred/unavailable/excluded, `--json`) in `sadhana_setu/corpus/sets.py` + `cli.py` (FR-010)
- [X] T026 [US3] Duplicate-audio detection by `sha256`: fold alternate URLs, mark duplicate `excluded` (`duplicate-of:<id>`) in `sadhana_setu/corpus/manifest.py` (FR-009)
- [X] T027 [P] [US3] Test set scoping + status counts + dedup in `tests/corpus/test_sets.py`

**Checkpoint**: corpus is navigable and runnable per set.

---

## Phase 6: User Story 4 — Reproduce on a fresh machine (P3)

**Goal**: Manifest-only reproducibility proven end-to-end.
**Independent test**: on a clean checkout, `fetch`+`transcribe` from the manifest; checksums match, transcripts byte-stable.

- [X] T028 [US4] Implement `verify` (re-fetch to a temp cache, assert each checksum equals recorded `sha256`) in `sadhana_setu/corpus/verify.py` (SC-004)
- [X] T029 [US4] Wire `verify` into `sadhana_setu/corpus/cli.py`
- [X] T030 [P] [US4] Test that a clean re-run over a processed corpus yields no transcript diffs + verify checksum match in `tests/corpus/test_verify.py` (SC-002)

**Checkpoint**: reproducibility guarantee enforced.

---

## Phase 7: Polish & Cross-Cutting

- [X] T031 [P] Update `corpus/README.md` with the per-set directory map and cross-check against `quickstart.md`
- [X] T032 [P] Add module docstrings and ensure consistent `--json` output across all commands in `sadhana_setu/corpus/`
- [X] T033 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

---

## Dependencies

- **Setup (P1)** → **Foundational (P2)** → user stories.
- **US1** is the MVP and unblocks **US2** (must fetch before transcribe).
- **US3** and **US4** depend on US1+US2 having produced manifest state + transcripts.
- Within a phase, `[P]` tasks touch different files and may run in parallel.

## Parallel execution examples

- Phase 1: T002, T003, T004 in parallel (different files).
- Phase 2: T006, T007, T008 in parallel after T005 lands `manifest.py`.
- Phase 3: T016, T017 (tests) in parallel once T011–T014 exist.

## Implementation strategy

- **MVP = Phases 1–3 (US1)**: registering and fetching audio with provenance is the irreducible
  first deliverable.
- Then **US2** for the core artifact (committed transcripts), then **US3** (curation) and **US4**
  (reproducibility) as incremental hardening.
- Stop after each phase for a working, testable increment.
