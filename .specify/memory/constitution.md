# Sadhana Setu — Hari-Nāma Corpus Constitution

This constitution governs the expansion of Sadhana Setu from a single-practitioner
companion into a Hari-Nāma deep-dive platform for practicing ISKCON devotees. It binds
all corpus, enrichment, app-enrichment, localization, and pre-japa work that follows.
The audience is initiated and aspiring devotees who want to go deep into the Holy Name.

## Core Principles

### I. Tattva Fidelity (NON-NEGOTIABLE)

Spiritual accuracy outranks completeness, speed, and polish. Transcripts are stored
**verbatim** — no paraphrase, no "cleanup" that changes meaning. Enrichment never
fabricates verses, translations, or attributions. Sanskrit text and IAST transliteration
are reproduced **only** from authoritative sources (Śrīla Prabhupāda's books, the
vidya-karana knowledge graph, or named published editions), never generated from a model's
memory. Every interpretive claim in an enriched note carries a citation to its source
(speaker + lecture + timestamp, or book + verse). When fidelity cannot be guaranteed, the
content is marked `[UNVERIFIED]` and withheld from publish until a devotee resolves it.

### II. Provenance & Reproducibility

Every artifact is traceable and reproducible. Each transcript and note records its source
URL, SHA-256 checksum of the source audio, speaker, lecture title, and date. The corpus is
**manifest-driven**: a committed manifest is the single source of truth, so any machine can
re-fetch the same audio and regenerate the same outputs. All pipeline stages are
**idempotent** — re-running over existing inputs reproduces existing outputs and never
silently mutates published text.

### III. Attribution & Fair Use

Speakers and ISKCON Desire Tree are credited on every derived artifact. **Audio is never
committed to git and never redistributed** — only text (transcripts, notes) plus a source
manifest of URLs and checksums live in the repository. Source-site terms of use are
honored. Where a source forbids derivative text, that source is excluded, not worked around.

### IV. Sattvic Medium

The existing app's sacred constraints carry forward unchanged: no streaks, no badges, no
gamification, no push notifications, no quantifying or scoring of a devotee's chanting. The
corpus and every feature built on it serve the hearing↔chanting loop and genuine
transformation — not engagement metrics or vanity. Silence is an acceptable output.

### V. Human-Devotee Review Gate

Machine and LLM output is always a **draft**. No enriched note, translation, or
app-surfaced teaching is published until a qualified devotee reviews it for tattva accuracy
and approves it. Review status is explicit and recorded; unreviewed content is visibly
marked as such and excluded from the published corpus.

### VI. Local-First & Offline

Transcription (whisper.cpp) and, wherever feasible, enrichment run **locally**. Source
audio never leaves the practitioner's machine. The pipeline requires no third-party cloud
service for its core path; any optional cloud step must be opt-in and must not transmit
audio. This honors both privacy and the project's offline, self-contained ethos.

### VII. Monorepo Content Conventions

All corpus content lives inside the `sadhana-setu` repository under a fixed `corpus/`
layout with stable naming and file formats defined by the active specs. Structure is
predictable so tooling, review, and the app can rely on it without per-source special cases.

### VIII. Reuse Vidya-Karana

This project composes on the existing sibling systems rather than rebuilding them:

- **vidya-karana** (`/Users/sree/Projects/vidya-karana`) — RAG + content pipeline with
  audio/ingest infrastructure (`scripts/audio_daemon.py`, `agents/pipeline.py`,
  `agents/corpus_processor.py`, `agents/ontologist.py`) and a ChromaDB corpus.
- **vidya-karana-kg** (`/Users/sree/Projects/vidya-karana-kg`) — NetworkX knowledge graph
  served via `kg-mcp` (`search_corpus`, `get_verse`, `find_verses`, `cross_author_chunks`,
  `kg_status`), already wired into the app at `sadhana_setu/mcp_client.py`.

Prefer reusing this infrastructure over new code. **All Sanskrit/verse references are
KG-grounded** — retrieved through `kg-mcp`, never invented (this is how Principle I is
enforced in practice). Approved enriched notes are ingested **back** into vidya-karana's
corpus/ChromaDB → KG so the Sadhana Setu app surfaces them through the same path it
already uses.

## Additional Constraints

- **Languages**: The platform targets English first, then Telugu, Kannada, and Tamil.
  Translations follow a machine-draft + native-devotee-review model (Principle V applies).
- **No audio in git**: Enforced via `.gitignore`; the audio cache is local-only.
- **Diacritics**: IAST is the canonical transliteration scheme for romanized Sanskrit.
- **Formats**: Transcripts and notes are plain text / Markdown with structured front-matter
  so they are diff-friendly, reviewable in pull requests, and parseable by the app.

## Development Workflow

- Work is **spec-driven** (spec-kit): every feature has `spec.md` → `plan.md` → `tasks.md`
  before implementation. Specs precede code.
- Open questions are marked `[NEEDS CLARIFICATION]` in specs and resolved via
  `/speckit-clarify` before planning, not guessed during implementation.
- A change is "done" only when its outputs pass the review gate (Principle V) and its
  provenance is complete (Principle II).
- Pull requests touching corpus content must show: source manifest entry, checksum, and
  review status. Reviewers verify constitution compliance.

## Governance

This constitution supersedes other practices for the Hari-Nāma corpus work. Any deviation
must be justified in a spec's Complexity Tracking section and approved. Principle I (Tattva
Fidelity) and Principle V (Review Gate) are non-negotiable and cannot be waived for
schedule or convenience. Amendments require an explicit edit here, a version bump below, and
a note of what changed and why.

**Version**: 1.0.0 | **Ratified**: 2026-06-24 | **Last Amended**: 2026-06-24
