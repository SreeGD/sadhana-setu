# Data Model: Hari-Nāma Corpus Pipeline

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Defines the entities, fields, validation rules, and state transitions for the pipeline. The
authoritative machine-readable schemas live in [`contracts/`](./contracts/); this document is the
human-readable model. All entities are plain files (YAML manifest, Markdown transcripts) so they
are diff-friendly and reviewable in pull requests (Constitution VII).

## Entity: SourceSet

A named grouping of lectures — one per featured speaker, one per Holy Name seminar.

| Field | Type | Rules |
|---|---|---|
| `id` | string (kebab-case) | Unique; stable; matches a `corpus/transcripts/<id>/` directory. |
| `speaker` | string | Display name with IAST diacritics. |
| `kind` | enum: `speaker` \| `seminar` | Required. |
| `lectures` | list[Lecture] | May be empty (stub). |

The six seed sets: `bhurijana-prabhu`, `sacinandana-maharaja`, `mahatma-prabhu`,
`radhanath-swami`, `srila-prabhupada`, `holy-name-seminar` (one set per seminar; suffix as needed).

## Entity: Lecture (manifest entry)

A single audio item and the unit the pipeline processes.

| Field | Type | Rules |
|---|---|---|
| `id` | string (kebab-case) | Unique within the corpus; also the transcript filename stem. |
| `title` | string | Required; source-provided. |
| `urls` | list[url] | ≥1; first is canonical. Alternate URLs for the same audio allowed. |
| `date` | date (ISO) \| null | If known. |
| `status` | enum (see below) | Required; drives the state machine. |
| `sha256` | hex(64) \| null | Null until fetched; set from cached audio. |
| `duration_seconds` | int \| null | Set on fetch/transcribe. |
| `language` | BCP-47 (`en`, `hi`, …) | **Declared at `seed`** (default `en`); **confirmed by a cheap language-detect sample at `fetch`**, where non-`en` ⇒ `deferred` (FR-013). Set before transcription so non-English audio is never fully transcribed. |
| `topic_tags` | list[string] | Drives FR-014 topic filter (japa, nama, chanting, offenses, bhava). |
| `notes` | string | Maintainer notes / exclusion or deferral reason. |
| `transcript_path` | path \| null | Set when `transcribed`; relative to repo root. |
| `whisper_model` | string \| null | Model used (e.g. `large-v3-turbo`); set on transcribe. |

### Lecture status state machine

```text
            ┌─────────── excluded (terms forbid / not relevant)
            │
pending ──► fetched ──► transcribed
   │                        
   ├─► deferred  (non-English, or out of Round 1 scope — retained, not processed)
   └─► unavailable (source URL dead/moved)
```

- `pending → fetched`: audio downloaded to cache, `sha256`/`duration` recorded.
- `fetched → transcribed`: transcript written; `transcript_path`/`whisper_model` recorded.
- `pending → deferred`: language ≠ `en` — declared at `seed` or detected from a short sample at
  `fetch` (FR-013) — or out-of-scope per FR-014. Decided before transcription.
- `pending → unavailable`: URL dead/moved (recorded with date in `notes`).
- `* → excluded`: source terms forbid derivative text (FR-011), with reason.
- Transitions are idempotent: re-running a stage on an entry already past it is a no-op unless an
  explicit override (`--refetch` / `--retranscribe`) is given (FR-007).

### Validation rules

- A `transcribed` entry MUST have non-null `sha256`, `transcript_path`, `whisper_model`.
- `sha256`, once set, is immutable; a cache file whose hash differs ⇒ provenance error, stop
  (FR-012).
- Two entries sharing a `sha256` ⇒ duplicate audio: keep one `transcribed`, fold the other's URLs
  into its `urls`, mark the duplicate `excluded` with reason `duplicate-of:<id>` (FR-009).
- `language != "en"` ⇒ status MUST be `deferred` in Round 1.

## Entity: Transcript

The verbatim text output for one lecture: a Markdown file with YAML front-matter, stored at
`corpus/transcripts/<set-id>/<lecture-id>.md`. The body is verbatim (Constitution I).

### Front-matter (provenance — FR-005)

| Field | Type | Notes |
|---|---|---|
| `lecture_id` | string | Back-link to the manifest entry (bidirectional). |
| `set_id` | string | Owning SourceSet. |
| `speaker` | string | IAST. |
| `title` | string | |
| `date` | date \| null | |
| `source_urls` | list[url] | Copied from the manifest entry. |
| `sha256` | hex(64) | Audio checksum — the provenance anchor. |
| `duration_seconds` | int | |
| `language` | BCP-47 | Always `en` for committed Round 1 transcripts. |
| `whisper_model` | string | Pinned model used. |
| `whisper_flags` | string | Exact flags, for reproducibility. |
| `timestamp_granularity` | const `segment` | Per clarification. |
| `transcribed_at` | datetime (ISO) | |
| `pipeline_version` | string | Tool version that produced it. |

### Body

Segment-timestamped verbatim text, e.g.:

```text
[00:00:00.000 → 00:00:07.320] Hare Kṛṣṇa. Today we will discuss attentive chanting...
[00:00:07.320 → 00:00:14.880] ...
```

No paraphrase, no normalization that alters meaning. Misheard Sanskrit is left as transcribed;
correction/annotation is 002's concern, gated by review.

## Entity: AudioCacheItem (never committed)

Downloaded audio in `corpus/.audio-cache/`, keyed by `sha256`. Git-ignored (Constitution III/VI).
Reproducible from the manifest `urls` + `sha256`; not part of the tracked data model beyond the
checksum recorded on its Lecture.

## Relationships

```text
SourceSet 1───* Lecture 1───0..1 Transcript
                   │
                   └───0..1 AudioCacheItem (by sha256, git-ignored)
```
