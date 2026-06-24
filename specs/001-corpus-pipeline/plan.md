# Implementation Plan: Hari-Nāma Corpus Pipeline

**Branch**: `001-corpus-pipeline` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-corpus-pipeline/spec.md`

## Summary

Build a reproducible, manifest-driven pipeline that fetches Holy-Name lecture audio from
`audio.iskcondesiretree.com` into a git-ignored local cache, transcribes it verbatim with
whisper.cpp, and commits timestamped transcripts plus the source manifest to GitHub. Audio is
never committed. The pipeline is idempotent and organized by source set (per speaker, per Holy
Name seminar). Round 1 is English-first and topic-bounded (per spec Clarifications); non-English
lectures are recorded as `deferred`. A read-only audit (research R3) found vidya-karana's audio
code is text-to-speech, so 001 reuses its proven **operational pattern** (serial queue, checksum
idempotency, quarantine) rather than its code; the ChromaDB/KG reuse lands in 002.

## Technical Context

**Language/Version**: Python 3.11+ (matches `pyproject.toml`; whisper.cpp invoked as a
subprocess)

**Primary Dependencies**: `whisper-cli` (whisper.cpp, Homebrew) with `ggml-large-v3-turbo`,
`ffmpeg` (decode to 16 kHz mono WAV + silence-boundary segmentation), `httpx` (fetch),
`pyyaml` (manifest), `python-dateutil`. No direct vidya-karana code reuse for 001 (its audio is
TTS); the daemon's queue/checksum/quarantine **pattern** is mirrored (research R3).

**Storage**: Plain files. Manifest in YAML under `corpus/sources/`; transcripts in Markdown
under `corpus/transcripts/<speaker-or-seminar>/`; audio in a git-ignored cache (default
`corpus/.audio-cache/`, configurable via env).

**Testing**: `pytest` (repo already uses it). Pipeline stages unit-tested with small fixtures;
one end-to-end test against a single short fixture lecture.

**Target Platform**: macOS / Apple Silicon (local-first); Linux-compatible.

**Project Type**: CLI + library (single project), consistent with the existing `sadhana_setu`
package layout.

**Performance Goals**: Throughput bounded by whisper.cpp; long lectures (90+ min) transcribe
without exhausting memory via ffmpeg ~10-min silence-boundary chunking with offset-corrected
timestamps (research R7). No hard latency target — this is a batch maintainer tool.

**Constraints**: Offline core path (no cloud STT); no audio committed; idempotent re-runs;
every output carries provenance; serial + rate-limited fetch honoring source terms.

**Scale/Scope**: Round 1 (English-first, topic-bounded) — all Holy Name seminars in full + the
five speakers' Holy-Name-topic lectures; order of hundreds of lectures, growing. Text-only in git.

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
- **VIII. Reuse Vidya-Karana** — Audit done (research R3): vidya-karana audio is TTS, so 001
  mirrors its operational pattern, not its code; genuine ChromaDB/KG reuse lands in 002. ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-corpus-pipeline/
├── plan.md              # This file
├── spec.md              # Feature spec
├── research.md          # Phase 0 — model, seed approach, reuse map, chunking (RESOLVED)
├── data-model.md        # Phase 1 — entities, fields, state machine (DONE)
├── quickstart.md        # Phase 1 — maintainer run/validation guide (DONE)
├── contracts/           # Phase 1 — manifest.schema.json, transcript-frontmatter.schema.json, cli.md (DONE)
└── tasks.md             # Phase 2 — /speckit-tasks output (already drafted)
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
4. **whisper.cpp invocation**: `ggml-large-v3-turbo` + flags pinned in config so transcripts are
   reproducible; model recorded in front-matter. Long audio chunked via ffmpeg silence-boundary
   segmentation with offset-corrected timestamps (research R7).
5. **Reuse boundary** (research R3, resolved): 001 imports no vidya-karana code (its audio is
   TTS); it mirrors the `audio_daemon.py` queue/checksum/quarantine pattern. ChromaDB ingest
   (`corpus_processor.py` / `ChromaDBManager`) and `kg-mcp` grounding are reused by 002, not 001.

## Complexity Tracking

No constitution violations; no entries required.
