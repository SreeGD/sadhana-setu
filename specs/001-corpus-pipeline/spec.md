# Feature Specification: Hari-Nāma Corpus Pipeline

**Feature Branch**: `001-corpus-pipeline`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Gather all relevant lectures from audio.iskcondesiretree.com,
mainly from Bhurijana Prabhu, HH Sachinandana Maharaj, Mahatma Prabhu, HH Radhanathswami,
HDG Srila Prabhupada, transcribe, make sure transcription is checked into github. Also pull
information from holyname seminars, transcribe, make it part of github. Use whisper.cpp."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a lecture source and fetch its audio (Priority: P1)

A devotee maintaining the corpus adds a Holy-Name lecture (or a whole speaker/seminar
listing) from `audio.iskcondesiretree.com` to a source manifest, then runs the pipeline. The
audio is downloaded to a local, git-ignored cache, its SHA-256 checksum is recorded, and the
manifest entry is marked fetched. Nothing about the audio is committed — only the manifest.

**Why this priority**: Without a reproducible way to register and fetch sources, there is no
corpus. This is the irreducible first slice.

**Independent Test**: Add one known lecture URL to the manifest, run `fetch`, confirm the
audio lands in the cache, the checksum is recorded in the manifest, and `git status` shows
no audio file staged.

**Acceptance Scenarios**:

1. **Given** a manifest entry with a valid lecture URL, **When** the maintainer runs the
   fetch stage, **Then** the audio is downloaded to the git-ignored cache, its SHA-256 is
   written to the manifest, and the entry's status becomes `fetched`.
2. **Given** an entry already fetched with a matching checksum, **When** fetch runs again,
   **Then** the cached file is reused and nothing is re-downloaded (idempotent).
3. **Given** a cached file whose checksum no longer matches the manifest, **When** fetch
   runs, **Then** the pipeline flags a provenance mismatch and refuses to proceed silently.

---

### User Story 2 - Transcribe fetched audio verbatim with whisper.cpp (Priority: P1)

The maintainer runs the transcription stage. For each fetched-but-untranscribed lecture,
whisper.cpp (`whisper-cli`) produces a verbatim transcript with timestamps. The transcript
is written to the corpus as a text/Markdown file with provenance front-matter (source URL,
checksum, speaker, title, date, model used) and committed to GitHub.

**Why this priority**: A verbatim, timestamped, committed transcript is the core deliverable
of this feature and the input every later feature depends on.

**Independent Test**: With one lecture fetched, run `transcribe`, confirm a transcript file
appears under `corpus/` with correct front-matter and timestamps, and that it is a normal
text file ready to commit.

**Acceptance Scenarios**:

1. **Given** a fetched lecture, **When** transcription runs, **Then** a verbatim transcript
   with timestamps and provenance front-matter is written under `corpus/transcripts/...`.
2. **Given** a lecture already transcribed, **When** transcription runs again, **Then** the
   existing transcript is left unchanged (idempotent) unless a re-transcribe is explicitly
   requested.
3. **Given** a transcript file, **When** a reviewer opens it, **Then** every line traces to a
   timestamp and the header identifies speaker, source URL, checksum, and whisper model.

---

### User Story 3 - Curate by speaker and by Holy Name seminar (Priority: P2)

The maintainer can organize the manifest into **source sets**: one per featured speaker
(Bhūrijana Prabhu, HH Sacīnandana Mahārāja, Mahātmā Prabhu, HH Rādhānāth Swami, Śrīla
Prabhupāda) and one per Holy Name seminar. The maintainer can run the pipeline scoped to a
set, and can see at a glance which lectures in a set are pending, fetched, or transcribed.

**Why this priority**: The brief names specific speakers and the Holy Name seminars; the
corpus must be navigable and runnable by those groupings, but this is organization on top of
the core fetch/transcribe slices.

**Independent Test**: Define two source sets, run the pipeline scoped to one, and confirm only
that set's lectures are processed and a status report lists per-set progress.

**Acceptance Scenarios**:

1. **Given** lectures tagged into speaker/seminar sets, **When** the maintainer runs the
   pipeline for one set, **Then** only that set is processed.
2. **Given** a partially processed corpus, **When** the maintainer requests status, **Then**
   a per-set count of pending / fetched / transcribed lectures is shown.

---

### User Story 4 - Reproduce the corpus on a fresh machine (Priority: P3)

A devotee clones the repo on a new machine. Using only the committed manifest (no audio in
the repo), they re-fetch the audio and regenerate identical transcripts, verifying the
corpus is fully reproducible from text + manifest alone.

**Why this priority**: Reproducibility is a constitutional guarantee (Principle II); proving
it end-to-end protects the corpus long-term, but it builds on the first three stories.

**Independent Test**: On a clean checkout, run fetch + transcribe from the manifest and
confirm checksums match and transcripts are byte-stable (modulo declared nondeterminism).

**Acceptance Scenarios**:

1. **Given** only the committed text + manifest, **When** a maintainer runs the pipeline,
   **Then** the same audio is fetched (checksums match) and transcripts regenerate.

---

### Edge Cases

- A source URL is dead or moved → entry is marked `unavailable` with the date; pipeline
  continues with other entries and reports it.
- A lecture is a duplicate of one already in the corpus (same audio, different URL) → detected
  by checksum and not transcribed twice; the alternate URL is recorded on the existing entry.
- Audio is not in English (e.g., Hindi/Bengali portions, or a non-English seminar) →
  `[NEEDS CLARIFICATION]` (see FR-013): transcribe in source language, translate, or skip?
- Very long lectures (90+ min) → transcription must chunk/stream without exhausting memory.
- A source's terms forbid derivative text → the source is excluded, not worked around
  (Constitution Principle III).
- Partial/interrupted run → re-running resumes without corrupting prior outputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a committed, human-editable **source manifest** that is
  the single source of truth for which lectures belong to the corpus.
- **FR-002**: Each manifest entry MUST capture source URL, speaker, lecture title, date (if
  known), source set, processing status, and — once fetched — the audio SHA-256 checksum.
- **FR-003**: The system MUST fetch audio to a **git-ignored local cache**; audio files MUST
  NOT be committed to the repository (Constitution Principle III).
- **FR-004**: The system MUST transcribe audio **verbatim** using whisper.cpp (`whisper-cli`),
  producing timestamped transcripts.
- **FR-005**: Each transcript MUST be stored as a text/Markdown file with provenance
  front-matter: source URL, checksum, speaker, title, date, whisper model, and date
  transcribed.
- **FR-006**: Transcripts and the manifest MUST be committed to GitHub; the commit MUST be
  reviewable as plain text (diff-friendly).
- **FR-007**: All stages (fetch, transcribe) MUST be **idempotent**: re-running over existing
  inputs reproduces existing outputs and never silently overwrites published transcripts.
- **FR-008**: The system MUST support **source sets** (per speaker and per Holy Name seminar)
  and allow runs scoped to a set.
- **FR-009**: The system MUST detect **duplicate audio** by checksum and avoid re-transcribing
  it, recording alternate URLs on the existing entry.
- **FR-010**: The system MUST surface a **status report** of per-set pending / fetched /
  transcribed counts.
- **FR-011**: The system MUST honor **source terms of use** and provide a way to mark a source
  excluded, with reason.
- **FR-012**: On a checksum mismatch between cache and manifest, the system MUST stop and
  report a provenance error rather than proceed silently.
- **FR-013**: The system MUST handle non-English source audio per a defined policy.
  [NEEDS CLARIFICATION: for non-English lectures/seminars — transcribe in source language,
  auto-translate to English, or exclude from this round?]
- **FR-014**: The corpus MUST define **lecture-selection criteria** so "all relevant lectures"
  is bounded. [NEEDS CLARIFICATION: is the scope every Holy-Name-tagged lecture by these
  speakers, a curated subset, or seminar-first? What defines "relevant"?]
- **FR-015**: The system MUST define a **deduplication and re-run policy** for when a source
  listing changes upstream. [NEEDS CLARIFICATION: how often is the source re-scanned, and how
  are newly-added lectures discovered — manual add, or automated listing crawl?]

### Key Entities *(include if feature involves data)*

- **Source Set**: A named grouping of lectures — one per featured speaker, one per Holy Name
  seminar. Has a title, a speaker/seminar identity, and member lectures.
- **Lecture (Manifest Entry)**: A single audio item. Attributes: source URL(s), speaker,
  title, date, source set, status (`pending`/`fetched`/`transcribed`/`unavailable`/`excluded`),
  audio SHA-256, duration, language.
- **Transcript**: The verbatim text output for one lecture. Attributes: provenance
  front-matter (links back to its manifest entry), timestamped body, whisper model.
- **Audio Cache Item**: The downloaded audio in the local git-ignored cache, keyed by
  checksum. Never committed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can take a lecture from URL to committed, timestamped transcript in
  a single scoped pipeline run, with zero audio bytes committed to git.
- **SC-002**: Re-running the full pipeline over an already-processed corpus produces **no
  changes** to committed transcripts (idempotent; verified by a clean `git status`).
- **SC-003**: Every committed transcript traces unambiguously to its source (URL + checksum +
  speaker + date present in front-matter) — 100% of files, no exceptions.
- **SC-004**: A fresh clone can reproduce the audio set from the manifest alone, with 100% of
  fetched checksums matching the recorded checksums.
- **SC-005**: The status report correctly reflects per-set progress for all five named
  speakers and each registered Holy Name seminar.

## Assumptions

- Transcription uses **whisper.cpp** locally (`whisper-cli` is already installed via Homebrew);
  no cloud STT is used for the core path (Constitution Principle VI).
- Only **text + manifest** are committed; audio stays in a git-ignored local cache
  (locked decision).
- The corpus lives **inside the `sadhana-setu` monorepo** under `corpus/` (locked decision).
- Source audio is predominantly English Holy-Name lectures; non-English handling is deferred
  to FR-013 clarification.
- vidya-karana's existing audio/ingest infrastructure (`scripts/audio_daemon.py`,
  `agents/pipeline.py`, `agents/corpus_processor.py`) MAY be reused where it fits, rather than
  building fetch/transcribe orchestration from scratch (Constitution Principle VIII; evaluated
  in `research.md`).
- Enrichment of transcripts into class notes is **out of scope** here — it is `002-note-enrichment`.
