# Phase 0 Research: Hari-Nāma Corpus Pipeline

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document captures the unknowns to resolve before Phase 1 design. Each item lists the
question, the decision (once made), and the rationale. Items that depend on a
`[NEEDS CLARIFICATION]` from the spec are flagged.

## R1 — whisper.cpp model sizing & flags

**Question**: Which whisper.cpp model and flags balance accuracy on Sanskrit-laden English
Vaiṣṇava lectures against transcription time on this Mac?

**Decision**: Default model **`ggml-large-v3-turbo`** (whisper.cpp), segment-level timestamps,
pinned flags, recorded in transcript front-matter. A `large-v3` (non-turbo) override is allowed
for hard recitation-heavy lectures. Models are downloaded once into a configured, git-ignored
model dir (env `WHISPER_MODEL`/`WHISPER_MODEL_DIR`); only a bundled test-tiny exists locally now.

**Rationale**: This is a batch tool, so accuracy on Sanskrit terms, devotee names, and verse
recitation matters more than speed; `large-v3-turbo` gets near-large accuracy at a fraction of
the runtime on Apple-Silicon Metal, making the full back-catalog tractable. Pinning the model +
flags makes transcripts reproducible (SC-002).

**Alternatives considered**: `medium.en` — faster but noticeably weaker on Sanskrit/IAST terms
and proper nouns; `large-v3` — marginally better than turbo on dense recitation but several times
slower (kept as an override, not the default); word-level timestamps — rejected by clarification
(segment-level suffices for note back-links and halves output size).

## R2 — Source-site survey: audio.iskcondesiretree.com

**Question**: How are lectures listed and addressed on the source site, and what are its terms?

**Decision**: The one-time seed (FR-015) is built by an **assisted listing parser** that reads
each speaker/seminar listing page on `audio.iskcondesiretree.com`, extracts `{title, page/audio
URL, date}` per lecture, applies the FR-014 topic filter, and writes draft manifest entries that
a maintainer verifies before fetch. The concrete DOM/URL structure is captured by the seed task
(T002/T012) at implementation time and pinned into the parser. Fetch is **rate-limited and
serial** with a descriptive User-Agent; robots/terms are checked first and a forbidding source is
marked `excluded` (FR-011).

**Rationale**: A parser-assisted seed avoids hand-typing hundreds of URLs while keeping a human
verification step; serial + rate-limited fetching honors source terms (Constitution III). Stable
per-lecture URLs recorded in the manifest give the reproducibility guarantee (US4).

**Alternatives considered**: full manual entry (rejected — too slow at corpus scale); recurring
automated crawl (rejected by clarification — terms/“don’t hammer” risk); using third-party
transcripts (rejected by clarification — always whisper.cpp).

## R3 — Reuse evaluation of vidya-karana audio/ingest infrastructure

**Question**: What of `/Users/sree/Projects/vidya-karana`'s existing code can be reused vs.
wrapped vs. reimplemented thin? (Constitution Principle VIII.)

**Finding (read-only audit, 2026-06-24)**: vidya-karana's audio code is **text-to-speech**, not
speech-to-text. `scripts/audio_daemon.py` and `scripts/generate_audio.py` render `edge-tts`
audio *from* text for a multilingual education product; `scripts/verify_audio.py` uses ffmpeg
silence-detect. None of it transcribes. The ChromaDB ingest path, however, is real and relevant:
`agents/corpus_processor.py` ("Agent 0 — ingests source materials into ChromaDB with verified
references") wraps `systems/chromadb_manager.py::ChromaDBManager` and includes IAST normalization.

**Decision (reuse map)**:

| vidya-karana component | For spec 001 | For spec 002 |
|---|---|---|
| `audio_daemon.py` (edge-tts queue/quarantine/sha256/PAUSE) | **Mirror the pattern**, not the code (serial queue, checksum idempotency, quarantine-after-N) | — |
| `generate_audio.py`, `verify_audio.py` (TTS, ffmpeg) | Borrow **ffmpeg invocation patterns** only | — |
| `agents/corpus_processor.py` + `systems/chromadb_manager.py` | — | **Reuse** for back-ingest (FR-011) |
| IAST normalization (`corpus_processor.py`) | — | **Reuse** for note rendering |
| `kg-mcp` via app `mcp_client.py` | — | **Reuse** for verse grounding |

So for **001 there is no direct code reuse** (audio direction is opposite); the new fetch+
transcribe pipeline is thin and standalone, mirroring proven operational patterns. Constitution
Principle VIII is satisfied chiefly at the KG/ChromaDB layer, which **002** consumes.

**Rationale**: Reusing TTS code for STT would be a forced fit; mirroring the daemon's robust
queue/checksum/quarantine pattern captures its value without coupling. The ChromaDB layer is
genuinely shared and must not be re-implemented.

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

**Decision**: Decode to 16 kHz mono WAV with ffmpeg, then segment into ~10-minute chunks at
ffmpeg-detected silence boundaries (avoid splitting mid-word); transcribe each chunk with the
pinned model; stitch transcripts and **offset each chunk's segment timestamps by its start time**
so the final timeline is continuous. Short lectures (< chunk size) skip segmentation.

**Rationale**: Per-chunk transcription bounds peak memory regardless of lecture length and lets a
failed chunk retry/quarantine independently (mirroring the daemon pattern, R3). Silence-boundary
splitting keeps words and timestamps intact; offset-correction preserves a single continuous
timeline for 002's back-links.

**Alternatives considered**: whisper.cpp streaming mode (rejected — tuned for live/low-latency,
not reproducible batch); fixed-time splits ignoring silence (rejected — risks cutting mid-word
and corrupting boundary segments).

## Clarification status

Resolved in the spec's `## Clarifications` (Session 2026-06-24): FR-013 (R4, non-English),
FR-014 (R5, selection scope), FR-015 (R6, discovery), timestamp granularity (R1, segment-level),
existing-transcripts policy (R2, always whisper.cpp).

Resolved during `/speckit-plan` (2026-06-24): R1 model (`large-v3-turbo`, segment timestamps),
R2 seed approach (assisted listing parser + manual verify), R3 reuse map (001 = pattern only;
002 = ChromaDB/KG reuse), R7 chunking (ffmpeg 10-min silence-boundary chunks, offset-corrected).
No open research items remain; the concrete site DOM is captured by the seed task at build time.
