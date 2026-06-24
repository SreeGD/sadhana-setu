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
- Timestamp granularity is **resolved: segment-level** (Clarify 2026-06-24); word-level not
  required. Configure whisper.cpp output accordingly.

**Decision**: _Model TBD_ — benchmark and pin one model + flag set (segment-level timestamps)
for reproducibility; record the model in front-matter.

**Rationale**: Larger models transcribe Sanskrit terms far better but are slower; the corpus is
batch, so accuracy is usually worth the time. Pinning makes transcripts reproducible (SC-002).

## R2 — Source-site survey: audio.iskcondesiretree.com

**Question**: How are lectures listed and addressed on the source site, and what are its terms?

**To investigate**:
- URL/listing structure per speaker and per Holy Name seminar; whether stable direct-audio URLs
  exist or pages must be parsed (drives the FR-015 **one-time assisted seed**).
- Existing published transcripts are **not** used — always whisper.cpp (Clarify 2026-06-24);
  no need to survey third-party transcript availability.
- Terms of use / robots / rate-limit expectations (Constitution Principle III).

**Decision**: _Listing structure TBD_ — survey to build the one-time seed for the manifest
(FR-015). Selection scope (FR-014) and non-English policy (FR-013) are already resolved.

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

## R4 — Non-English audio policy (spec FR-013)

**Question**: How to handle Hindi/Bengali/other-language lectures or seminars?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — exclude from Round 1; record in the manifest
as `deferred` with detected language. Round 1 is English-first; nothing is lost. Implication:
the pipeline needs language detection sufficient to set `deferred`.

## R5 — Lecture-selection criteria & scope bound (spec FR-014)

**Question**: What makes a lecture "relevant," and how is "all relevant lectures" bounded?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — Round 1 = all Holy Name seminars in full +
speaker lectures whose title/tag is a Holy-Name topic (japa, nāma, chanting, ten offenses,
bhāva); general back-catalogs deferred. Implication: the seed step must capture title/tag to
apply the topic filter.

## R6 — Rescan & dedup policy (spec FR-015)

**Question**: How are newly added upstream lectures discovered, and how often?

**Decision**: **RESOLVED (Clarify 2026-06-24)** — hybrid: one-time assisted listing seeds the
manifest, then manual additions; no recurring automated crawl. Dedup by audio checksum (FR-009).

## R7 — Chunking long lectures

**Question**: How to transcribe 90+ minute lectures without exhausting memory while keeping
timestamps continuous?

**To investigate**: ffmpeg segmentation + per-chunk transcription with offset-corrected
timestamps, vs. whisper.cpp streaming mode.

**Decision**: _TBD_.

**Rationale**: Many Holy-Name classes and full seminars are long; the pipeline must be robust.

## Clarification status

Resolved in the spec's `## Clarifications` (Session 2026-06-24): FR-013 (R4, non-English),
FR-014 (R5, selection scope), FR-015 (R6, discovery), timestamp granularity (R1, segment-level),
existing-transcripts policy (R2, always whisper.cpp).

Remaining for `/speckit-plan` (engineering, not requirements): R1 model choice, R2 listing
structure for the seed, R3 vidya-karana reuse map, R7 long-audio chunking.
