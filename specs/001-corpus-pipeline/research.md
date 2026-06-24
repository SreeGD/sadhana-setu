# Phase 0 Research: Hari-Nāma Corpus Pipeline

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document captures the unknowns to resolve before Phase 1 design. Each item lists the
question, the decision (once made), and the rationale. Items that depend on a
`[NEEDS CLARIFICATION]` from the spec are flagged.

## R1 — whisper.cpp model sizing & flags

**Question**: Which whisper.cpp model and flags balance accuracy on Sanskrit-laden English
Vaiṣṇava lectures against transcription time on this Mac?

**To investigate**:
- Available models (`base`, `small`, `medium`, `large-v3`) and their download/runtime cost on
  Apple Silicon with Metal.
- Accuracy on representative samples (devotee names, Sanskrit terms, verse recitation).
- Whether word-level timestamps (`--max-len` / `-ml`, `--output-json`) are needed for the
  enrichment back-links in 002.

**Decision**: _TBD_ — pin one model + flag set for reproducibility; record in front-matter.

**Rationale**: Larger models transcribe Sanskrit terms far better but are slower; the corpus is
batch, so accuracy is usually worth the time. Pinning makes transcripts reproducible (SC-002).

## R2 — Source-site survey: audio.iskcondesiretree.com

**Question**: How are lectures listed and addressed on the source site, and what are its terms?

**To investigate**:
- URL/listing structure per speaker and per Holy Name seminar; whether stable direct-audio URLs
  exist or pages must be parsed.
- Whether existing transcripts are already published anywhere (to prefer over re-STT).
- Terms of use / robots / rate-limit expectations (Constitution Principle III).

**Decision**: _TBD_ — informs FR-014 (selection criteria) and FR-015 (rescan/dedup policy).

**Rationale**: We must honor source terms and avoid hammering the site; a stable addressing
scheme is required for the reproducibility guarantee (US4).

## R3 — Reuse evaluation of vidya-karana audio/ingest infrastructure

**Question**: What of `/Users/sree/Projects/vidya-karana`'s existing code can be reused vs.
wrapped vs. reimplemented thin? (Constitution Principle VIII.)

**To investigate** (read-only):
- `scripts/audio_daemon.py` — does it already fetch/queue/transcribe audio? What engine?
- `agents/pipeline.py`, `agents/corpus_processor.py` — ingest orchestration and chunking we can
  borrow.
- `gdrive_downloads/` and `audio/` conventions — do they imply an existing fetch path?
- ChromaDB ingest entry points (needed by 002 for back-ingest, surveyed early here).

**Decision**: _TBD_ — produce a reuse map: {component → reuse / wrap / reimplement} with reasons.

**Rationale**: Avoid rebuilding working infrastructure; keep the new pipeline thin.

## R4 — Non-English audio policy (depends on spec FR-013)

**Question**: How to handle Hindi/Bengali/other-language lectures or seminars?

**Options**: (a) transcribe in source language and keep as-is; (b) transcribe + machine
translate to English with the original retained; (c) exclude from this round.

**Decision**: _BLOCKED on `[NEEDS CLARIFICATION]` FR-013_ — resolve via `/speckit-clarify`.

## R5 — Lecture-selection criteria & scope bound (depends on spec FR-014)

**Question**: What makes a lecture "relevant," and how is "all relevant lectures" bounded for an
initial round?

**Options**: every Holy-Name-tagged lecture by the five speakers; a curated subset; or
seminars-first then speaker back-catalogs.

**Decision**: _BLOCKED on `[NEEDS CLARIFICATION]` FR-014_ — resolve via `/speckit-clarify`.

## R6 — Rescan & dedup policy (depends on spec FR-015)

**Question**: How are newly added upstream lectures discovered, and how often?

**Options**: manual manifest edits only; periodic automated listing crawl; hybrid.

**Decision**: _BLOCKED on `[NEEDS CLARIFICATION]` FR-015_ — resolve via `/speckit-clarify`.

## R7 — Chunking long lectures

**Question**: How to transcribe 90+ minute lectures without exhausting memory while keeping
timestamps continuous?

**To investigate**: ffmpeg segmentation + per-chunk transcription with offset-corrected
timestamps, vs. whisper.cpp streaming mode.

**Decision**: _TBD_.

**Rationale**: Many Holy-Name classes and full seminars are long; the pipeline must be robust.

## Open questions feeding `/speckit-clarify`

- FR-013 (R4): non-English audio policy.
- FR-014 (R5): lecture-selection criteria / scope bound.
- FR-015 (R6): rescan & dedup cadence and discovery method.
