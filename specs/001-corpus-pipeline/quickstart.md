# Quickstart: Hari-Nāma Corpus Pipeline

Validation/run guide for the corpus pipeline (spec 001). Contracts and the data model are in
[`contracts/`](./contracts/) and [`data-model.md`](./data-model.md). This guide proves the feature
works end-to-end; implementation detail lives in `tasks.md`.

> Status: the pipeline is **specified, not yet implemented**. These are the steps the
> implementation must satisfy.

## Prerequisites

- macOS / Apple Silicon, Python 3.11+, the repo's venv (`pip install -e ".[dev]"`).
- System tools (already present on this machine): `whisper-cli` (whisper.cpp), `ffmpeg`.
- A whisper model downloaded once into the model dir (only a bundled test-tiny exists now):
  ```bash
  # one-time; path recorded via WHISPER_MODEL / WHISPER_MODEL_DIR
  whisper-cli --help    # confirm the binary
  # download ggml-large-v3-turbo into $WHISPER_MODEL_DIR (see research.md R1)
  ```
- Audio cache location is git-ignored (`corpus/.audio-cache/`); confirm `.gitignore` covers it.

## Scenario 1 — Seed the manifest (FR-015)

```bash
python -m sadhana_setu.corpus seed --set holy-name-seminar
```

**Expect**: draft `pending` entries appear under the `holy-name-seminar` set in
`corpus/sources/manifest.yaml`, each with `title` + `urls` + `topic_tags`; no audio downloaded.
Maintainer reviews/edits before fetching.

## Scenario 2 — Fetch one lecture's audio (US1)

```bash
python -m sadhana_setu.corpus fetch --set holy-name-seminar
```

**Expect**:
- Audio lands in `corpus/.audio-cache/<sha256>.<ext>`; `git status` shows **no audio staged**.
- The entry gains `sha256` + `duration_seconds`; `status: fetched`.
- Re-running fetch reuses the cache (no re-download). Corrupting the cache file then re-running ⇒
  **provenance error, exit 1** (FR-012).

## Scenario 3 — Transcribe verbatim (US2)

```bash
python -m sadhana_setu.corpus transcribe --set holy-name-seminar
```

**Expect**:
- `corpus/transcripts/holy-name-seminar/<id>.md` created with front-matter matching
  `contracts/transcript-frontmatter.schema.json` and a segment-timestamped verbatim body.
- `status: transcribed`; `transcript_path` + `whisper_model` recorded.
- Re-running is a no-op (idempotent) unless `--retranscribe`.

## Scenario 4 — Status report (US3)

```bash
python -m sadhana_setu.corpus status --json
```

**Expect**: per-set counts of pending/fetched/transcribed/deferred/unavailable/excluded for all
five speakers + each Holy Name seminar.

## Scenario 5 — Reproducibility (US4, SC-004)

```bash
python -m sadhana_setu.corpus verify --set holy-name-seminar
```

**Expect**: re-fetched audio checksums match the recorded `sha256` for every entry; exit 0.
A clean re-run of the full pipeline over a processed corpus produces **no transcript diffs**
(`git status` clean — SC-002).

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 URL → committed transcript, no audio in git | 2 + 3 |
| SC-002 idempotent (no diffs on re-run) | 3 + 5 |
| SC-003 100% provenance in front-matter | 3 |
| SC-004 manifest-only reproducibility | 5 |
| SC-005 per-set status correct | 4 |
