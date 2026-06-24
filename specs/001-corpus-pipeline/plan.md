# Implementation Plan: Hari-Nāma Corpus Pipeline

**Branch**: `001-corpus-pipeline` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-corpus-pipeline/spec.md`

## Summary

Build a reproducible, manifest-driven pipeline that fetches Holy-Name lecture audio from
`audio.iskcondesiretree.com` into a git-ignored local cache, transcribes it verbatim with
whisper.cpp, and commits timestamped transcripts plus the source manifest to GitHub. Audio is
never committed. The pipeline is idempotent and organized by source set (per speaker, per Holy
Name seminar). Where it fits, it reuses vidya-karana's existing audio/ingest code rather than
writing fresh orchestration.

## Technical Context

**Language/Version**: Python 3.11+ (matches `pyproject.toml`; whisper.cpp invoked as a
subprocess)

**Primary Dependencies**: `whisper-cli` (whisper.cpp, Homebrew), `ffmpeg` (audio decode/convert),
`httpx` or `requests` (fetch), `pyyaml` (manifest), `python-dateutil`. Reuse candidates from
`/Users/sree/Projects/vidya-karana`: `scripts/audio_daemon.py`, `agents/pipeline.py`,
`agents/corpus_processor.py`.

**Storage**: Plain files. Manifest in YAML under `corpus/sources/`; transcripts in Markdown
under `corpus/transcripts/<speaker-or-seminar>/`; audio in a git-ignored cache (default
`corpus/.audio-cache/`, configurable via env).

**Testing**: `pytest` (repo already uses it). Pipeline stages unit-tested with small fixtures;
one end-to-end test against a single short fixture lecture.

**Target Platform**: macOS / Apple Silicon (local-first); Linux-compatible.

**Project Type**: CLI + library (single project), consistent with the existing `sadhana_setu`
package layout.

**Performance Goals**: Throughput bounded by whisper.cpp; long lectures (90+ min) transcribe
without exhausting memory via chunking/streaming. No hard latency target — this is a batch
maintainer tool.

**Constraints**: Offline core path (no cloud STT); no audio committed; idempotent re-runs;
every output carries provenance.

**Scale/Scope**: Five named speakers + N Holy Name seminars; initial target on the order of
hundreds of lectures, growing. Text-only in git.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Transcripts are verbatim; no paraphrase. ✅ (enrichment is 002)
- **II. Provenance & Reproducibility** — Manifest + checksums + idempotent stages are central
  (FR-002, FR-007, FR-012, US4). ✅
- **III. Attribution & Fair Use** — Audio git-ignored, speaker credited in front-matter, source
  terms honored (FR-003, FR-005, FR-011). ✅
- **IV. Sattvic Medium** — Maintainer batch tool; no user-facing metrics. ✅
- **V. Review Gate** — Transcripts are verbatim machine output committed for review; publish of
  *enriched* content is gated in 002. Verbatim transcripts are reviewable as plain-text diffs. ✅
- **VI. Local-First & Offline** — whisper.cpp local; audio never leaves the machine. ✅
- **VII. Monorepo Conventions** — Fixed `corpus/` layout defined below. ✅
- **VIII. Reuse Vidya-Karana** — Reuse evaluation is a Phase 0 deliverable (`research.md`). ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-corpus-pipeline/
├── plan.md              # This file
├── spec.md              # Feature spec
├── research.md          # Phase 0 — whisper model sizing, source-site survey, reuse eval
├── data-model.md        # Phase 1 — manifest + transcript front-matter schema (TBD in /speckit-plan)
├── quickstart.md        # Phase 1 — maintainer runbook (TBD)
├── contracts/           # Phase 1 — manifest schema, transcript front-matter contract (TBD)
└── tasks.md             # Phase 2 — /speckit-tasks output
```

### Source Code (repository root)

```text
sadhana_setu/
└── corpus/                      # new sub-package: pipeline code
    ├── __init__.py
    ├── manifest.py              # load/validate/update the YAML source manifest
    ├── fetch.py                 # download audio to git-ignored cache; checksum
    ├── transcribe.py            # whisper.cpp (whisper-cli) wrapper; chunking; front-matter
    ├── sets.py                  # source-set grouping + status report
    └── cli.py                   # `python -m sadhana_setu.corpus {fetch,transcribe,status}`

corpus/                          # new content tree (committed text only)
├── README.md                    # conventions
├── sources/
│   └── manifest.yaml            # the source manifest (source of truth)
├── transcripts/
│   └── <speaker-or-seminar>/    # e.g. bhurijana-prabhu/, holy-name-seminar-2019/
│       └── <slug>.md            # verbatim transcript + provenance front-matter
└── .audio-cache/                # git-ignored; downloaded audio keyed by checksum

tests/
└── corpus/
    ├── test_manifest.py
    ├── test_fetch.py            # uses a tiny local fixture, no network
    └── test_transcribe.py       # uses a short fixture clip
```

**Structure Decision**: Pipeline code lives as a `sadhana_setu/corpus/` sub-package (reusing the
existing package + `pytest` setup); committed content lives in a top-level `corpus/` tree so it
is easy to browse, review, and gitignore the audio cache. This keeps app code and content
cleanly separated inside the one monorepo (Constitution Principle VII).

## Key design decisions (to be finalized in data-model.md / contracts/)

1. **Manifest schema** (`corpus/sources/manifest.yaml`): list of source sets, each with member
   lectures carrying url(s), speaker, title, date, status, sha256, duration, language.
2. **Transcript front-matter**: YAML header with the provenance fields from FR-005, plus the
   manifest entry id so transcript ↔ manifest is bidirectional.
3. **Idempotency key**: audio SHA-256. Fetch skips if checksum matches; transcribe skips if a
   transcript for that checksum + model already exists.
4. **whisper.cpp invocation**: model + flags pinned in config so transcripts are reproducible;
   model recorded in front-matter. Long audio chunked via ffmpeg segmentation.
5. **Reuse boundary**: `research.md` decides which of vidya-karana's `audio_daemon.py` /
   `pipeline.py` / `corpus_processor.py` to import/wrap vs. reimplement thin.

## Complexity Tracking

No constitution violations; no entries required.
