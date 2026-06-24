# Hari-Nāma Corpus Roadmap

> Governs the expansion of Sadhana Setu into a Hari-Nāma deep-dive platform for practicing
> ISKCON devotees. Driven by [spec-kit](https://github.com/SreeGD/spec-kit). All work is bound
> by the [Constitution](../.specify/memory/constitution.md). Specs precede code.

## Vision

Gather, transcribe, and enrich the Holy-Name teachings of senior Vaiṣṇavas, check the text
into GitHub with full provenance, fold it into the existing knowledge graph, and surface it
through Sadhana Setu — in English first, then Telugu, Kannada, and Tamil — so devotees can go
deep into Hari-Nāma and find genuine transformation.

## Goal → Spec mapping

| # | Goal (from the brief) | Spec | Round |
|---|---|---|---|
| G1 | Gather lectures from `audio.iskcondesiretree.com` (Bhūrijana Prabhu, HH Sacīnandana Mahārāja, Mahātmā Prabhu, HH Rādhānāth Swami, Śrīla Prabhupāda) **+ Holy Name seminars**, transcribe, commit transcripts + manifest to GitHub | `001-corpus-pipeline` | **1 (now)** |
| G2 | Enrich transcripts into class notes with LLM-added references; commit enriched notes to GitHub | `002-note-enrichment` | **1 (now)** |
| G3 | Enhance Sadhana Setu with the newly gathered information | `003-app-enrichment` | 2 |
| G4 | Make Sadhana Setu available in Telugu, Kannada, and Tamil | `004-localization` | 2 |
| G5 | Review and redesign pre-japa reading to bring transformation | `005-prejapa-transformation` | 2 |

## Round 1 — Corpus Foundation (specced now)

The platform starts upstream of the app: there is nothing to surface, translate, or redesign
around until the corpus exists. Round 1 builds that foundation.

### `001-corpus-pipeline`
Source manifest → fetch audio to a gitignored local cache → whisper.cpp (`whisper-cli`)
transcription → store verbatim transcripts + commit text/manifest. Holy Name seminars are a
**source set** within this pipeline, not a separate spec. Reuses vidya-karana's existing
audio/ingest infrastructure where it fits.

### `002-note-enrichment`
Raw transcripts → LLM-enriched class notes (theme, key teachings, verses cited with IAST,
**added cross-references** to Prabhupāda's books/purports and related teachings, practical
application to japa, glossary, timestamp back-links). Every verse/reference is **KG-grounded
through `kg-mcp`** (never invented). Notes pass the devotee review gate, then are ingested
**back** into vidya-karana's corpus/ChromaDB → KG so the app can surface them.

**Round 1 exit criteria:** a reproducible pipeline, a growing set of committed verbatim
transcripts with provenance, and reviewed enriched notes for an initial batch of lectures —
all queryable through the existing `kg-mcp` path.

## Round 2 — Platform (specced after the corpus exists)

These are named now so the architecture accounts for them, but are specced in a second pass
once Round 1 has produced real content to build against.

### `003-app-enrichment` (G3)
Surface the enriched corpus inside Sadhana Setu: feed Holy-Name teachings, pastimes, and
verse-grounded references into Pre-japa, Nama-Tattva, and the Saturday check-in via the
existing `mcp_client.py` → `kg-mcp` path. Honors all Sattvic-Medium constraints.

### `004-localization` (G4)
Telugu, Kannada, Tamil for the app UI and selected content. Machine-draft + native-devotee
review (Constitution Principle V). Establishes string extraction, locale resources, font/
rendering for Indic scripts, and a review workflow per language.

### `005-prejapa-transformation` (G5)
Review the current pre-japa reading (`sadhana_setu/ui/prejapa_view.py`) against the deepened
corpus and redesign it to bring transformation — not just information. Grounded in the
gathered teachings on attentive chanting, the ten offenses, and bhāva.

## Sequencing

```
001-corpus-pipeline ──► 002-note-enrichment ──► back-ingest to vidya-karana KG
                                                      │
                                                      ▼
                                   003-app-enrichment ──► 005-prejapa-transformation
                                                      │
                                                      ▼
                                              004-localization
```

## Working method

For each spec: `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks`
→ `/speckit-implement`. Open questions stay marked `[NEEDS CLARIFICATION]` until clarified.
