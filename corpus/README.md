# Hari-Nāma Corpus

Verbatim transcripts and enriched class notes of Holy-Name teachings, gathered for the Sadhana
Setu platform. Governed by the [Constitution](../.specify/memory/constitution.md) and built per
the specs in [`specs/`](../specs/). See the [roadmap](../docs/CORPUS_ROADMAP.md).

> **Status:** the pipeline (`specs/001-corpus-pipeline`) and the enrichment stage
> (`specs/002-note-enrichment`) are both **implemented** in `sadhana_setu/corpus/`
> (`seed` → `fetch` → `transcribe` → `enrich` → review UI → `status` / `verify`). The manifest is
> an empty stub until lectures are seeded; no notes exist until transcripts are enriched.

## Usage

```bash
# 1. seed the manifest from a listing page (assisted; verify entries before fetch)
python -m sadhana_setu.corpus seed --set holy-name-seminar --url <listing-url>
# 2. download audio to the git-ignored cache (records SHA-256)
python -m sadhana_setu.corpus fetch --set holy-name-seminar
# 3. transcribe verbatim with whisper.cpp (needs the model downloaded)
python -m sadhana_setu.corpus transcribe --set holy-name-seminar
# 4. enrich transcripts into draft notes (Claude Code + kg-mcp grounding)
python -m sadhana_setu.corpus enrich --set holy-name-seminar
# 5. review + approve drafts (approving auto-ingests into the KG)
streamlit run sadhana_setu/ui/review_view.py
# progress + reproducibility
python -m sadhana_setu.corpus status --json
python -m sadhana_setu.corpus verify --set holy-name-seminar
```

**Enriched notes** land in `corpus/notes/<set-id>/<lecture-id>.md` (one per transcript), with
KG-grounded verse citations, `[UNVERIFIED]`/`[sic?]` review aids, and a `draft`/`reviewed` status.
Enrichment runs **Claude Code headless** (`claude -p`); grounding + back-ingest reuse the
existing `kg-mcp` and vidya-karana ChromaDB. See
[`../specs/002-note-enrichment/`](../specs/002-note-enrichment/).

**Tooling:** `whisper-cli` (whisper.cpp, model `ggml-large-v3-turbo` in `$WHISPER_MODEL_DIR`)
and `ffmpeg`/`ffprobe` on `PATH`; Python deps via `pip install -e ".[dev]"`. See
[`../specs/001-corpus-pipeline/quickstart.md`](../specs/001-corpus-pipeline/quickstart.md).

## What lives here (and what does not)

| Tracked in git | Never in git |
|---|---|
| Source manifest (`sources/manifest.yaml`) | Audio files |
| Verbatim transcripts (`transcripts/`) | The audio cache (`.audio-cache/`) |
| Enriched class notes (`notes/`) | Anything not reproducible from text + manifest |

Audio is fetched to a git-ignored local cache and **never committed or redistributed**
(Constitution Principles III & VI). The committed manifest + checksums make the audio set
reproducible without storing it here.

## Layout

```text
corpus/
├── README.md                 # this file
├── sources/
│   └── manifest.yaml         # source of truth: which lectures belong to the corpus
├── transcripts/              # verbatim, timestamped (spec 001)
│   └── <speaker-or-seminar>/
│       └── <slug>.md         # transcript + provenance front-matter
├── notes/                    # LLM-enriched, KG-grounded, devotee-reviewed (spec 002)
│   └── <speaker-or-seminar>/
│       └── <slug>.md         # class note + provenance front-matter (status: draft|reviewed)
└── .audio-cache/             # GIT-IGNORED downloaded audio, keyed by checksum
```

## Source sets

One set per featured speaker, plus one per Holy Name seminar:

- `bhurijana-prabhu` — Bhūrijana Prabhu
- `sacinandana-maharaja` — HH Sacīnandana Mahārāja
- `mahatma-prabhu` — Mahātmā Prabhu
- `radhanath-swami` — HH Rādhānāth Swami
- `srila-prabhupada` — His Divine Grace A.C. Bhaktivedānta Swami Śrīla Prabhupāda
- `holy-name-seminar-*` — Holy Name seminars (one set per seminar)

## Provenance & review

- Every transcript and note carries front-matter linking to its source URL, audio SHA-256,
  speaker, and date (Principle II).
- Enriched notes are **drafts** until a devotee approves them (Principle V); only `reviewed`
  notes are published or fed to the app.
- All Sanskrit/verse references are **KG-grounded** via `kg-mcp`, never model-invented
  (Principle I / VIII).
