# CLI Contract: `sadhana_setu.corpus`

The pipeline is invoked as `python -m sadhana_setu.corpus <command> [options]`. All commands are
**idempotent** and operate against the manifest at `corpus/sources/manifest.yaml` (override with
`--manifest`). Text in/out: human-readable to stdout, errors to stderr; `--json` emits
machine-readable status where applicable.

## Global options

| Option | Default | Meaning |
|---|---|---|
| `--manifest PATH` | `corpus/sources/manifest.yaml` | Manifest file. |
| `--set ID` | (all) | Scope the run to one SourceSet (FR-008). |
| `--cache DIR` | `corpus/.audio-cache/` (env `CORPUS_AUDIO_CACHE`) | Git-ignored audio cache. |
| `--json` | off | Machine-readable output. |

## Commands

### `seed` — build/refresh the manifest from source listings (FR-015)

Parses speaker/seminar listing pages, applies the FR-014 topic filter, and writes **draft**
`pending` entries for maintainer verification. Never fetches audio. One-time/assisted; not a
recurring crawl.

- Exit non-zero if a listing page is unreachable or a source's terms forbid use.

### `fetch` — download audio to the cache (US1)

For each `pending` (or `--set`-scoped) entry: download to `<cache>/<sha256>.<ext>`, compute
SHA-256, record `sha256`/`duration_seconds`, set `status: fetched`.

- Serial + rate-limited; descriptive User-Agent.
- Idempotent: cached file with matching hash ⇒ reused, no re-download (FR-007).
- Checksum mismatch vs. recorded `sha256` ⇒ **stop with provenance error** (FR-012).
- Dead URL ⇒ `status: unavailable` (date in `notes`); forbidden ⇒ `excluded`. Run continues.
- Non-English detected ⇒ `status: deferred`, `language` set (FR-013).

### `transcribe` — verbatim transcription (US2)

For each `fetched` entry: decode to 16 kHz mono WAV, ~10-min silence-boundary chunking for long
audio, run `whisper-cli` (pinned model, segment timestamps), stitch with offset-corrected
timestamps, write `corpus/transcripts/<set>/<id>.md` with front-matter (transcript-frontmatter
schema), set `status: transcribed`.

- Idempotent: existing transcript for that `sha256` + model ⇒ skipped unless `--retranscribe`.
- Failure on a chunk ⇒ entry quarantined (retry next run), not corrupted (pattern from research R3).

### `status` — progress report (US3, FR-010)

Per-set counts of `pending` / `fetched` / `transcribed` / `deferred` / `unavailable` /
`excluded`. `--json` for tooling.

### `verify` — reproducibility check (US4, SC-004)

Re-fetch from the manifest (to a temp cache) and assert each computed checksum equals the recorded
`sha256`. Reports any drift; exits non-zero on mismatch.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (including "nothing to do"). |
| 1 | Provenance error (checksum mismatch) — halts (FR-012). |
| 2 | Source/terms error (forbidden source encountered without an `excluded` mark). |
| 3 | Tool missing (`whisper-cli`/`ffmpeg` not found) or model not available. |
