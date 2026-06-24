# Data Model: Note Enrichment

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Entities, fields, and state for the enrichment stage. Machine-readable schemas live in
[`contracts/`](./contracts/). Notes are one-per-transcript Markdown files (FR-013) with YAML
front-matter, diff-friendly and reviewable in PRs.

## Entity: ClassNote

The enriched study note for a single `001` transcript. Stored at
`corpus/notes/<set-id>/<lecture-id>.md`.

### Front-matter (provenance + review)

| Field | Type | Rules |
|---|---|---|
| `lecture_id` | string | The `001` lecture/transcript id (1:1). |
| `set_id` | string | Owning source set. |
| `transcript_path` | string | Path to the source transcript (provenance chain → audio sha256). |
| `sha256` | hex(64) | Inherited audio checksum (ties the note to exact source audio). |
| `speaker` | string | IAST. |
| `title` | string | |
| `status` | enum `draft` \| `reviewed` | Review-gate state. |
| `enrichment_engine` | const `claude-code` | Engine used (FR-015). |
| `enrichment_version` | string | engine + prompt-version pair (reproducibility). |
| `enriched_at` | datetime (ISO) | |
| `reviewer` | string \| null | Set on approval (FR-008). |
| `reviewed_at` | datetime \| null | Set on approval. |
| `ingested_at` | datetime \| null | Set when back-ingested into ChromaDB/KG. |

### Body sections (FR-001)

`theme_summary` · `key_teachings` (ordered, each with a transcript timestamp back-link) ·
`verses_cited` (IAST + citation, **KG-sourced**) · `cross_references` (grounded) ·
`practical_application` (to japa/Hari-Nāma) · `glossary` · an `[UNVERIFIED]` / review section
listing ungrounded candidates and `[sic?: …]` mishearing flags (FR-003, FR-014).

### Status state machine

```text
        enrich                 approve (UI)
   ─────────────►  draft  ───────────────────►  reviewed
                     ▲                              │
                     │   re-enrich (--regenerate;   │
                     └──  bumps enrichment_version) ◄┘
```

- `draft → reviewed`: only via the Streamlit review UI; records `reviewer` + `reviewed_at`
  (FR-007/008); triggers back-ingest (FR-011).
- `reviewed → draft`: only by an explicit `--regenerate`, which re-runs enrichment and bumps
  `enrichment_version` (so a reviewed note is never silently invalidated).
- Only `reviewed` notes are publish/ingest-eligible (SC-003).

### Validation rules

- A `reviewed` note MUST have `reviewer` + `reviewed_at`.
- Every `key_teaching` MUST carry a transcript timestamp (SC-002).
- Every entry in `verses_cited` MUST be KG-sourced (carry a resolved `verse_ref`); otherwise it
  belongs in the `[UNVERIFIED]` section, not the body (FR-002/003, SC-001).

## Entity: Citation / Reference

A grounded link produced by resolving an LLM *candidate* against `kg-mcp`.

| Field | Type | Notes |
|---|---|---|
| `kind` | enum `verse` \| `cross_ref` | |
| `candidate` | string | What the LLM proposed (`verse_ref` or a search query). |
| `verse_ref` | string \| null | e.g. `BG 18.66` (for `get_verse`). |
| `iast` / `translation` | string \| null | **From `kg-mcp`**, never the LLM. |
| `source` | string | Citation label (book + verse, or speaker + lecture). |
| `verified` | bool | False ⇒ rendered as `[UNVERIFIED]`, withheld from the body. |

## Entity: ReviewRecord

Captured by the Streamlit UI on approval; embedded in the note front-matter.

| Field | Type | Notes |
|---|---|---|
| `reviewer` | string | Devotee identity. |
| `reviewed_at` | datetime | |
| `decision` | const `approved` | (Only approval changes state; rejection leaves it `draft`.) |
| `notes` | string | Optional reviewer remarks. |

## Entity: EnrichmentVersion

`enrichment_engine` + prompt-version (e.g. `claude-code/v1`). Pinned in config and recorded on
each note so notes are reproducible and re-review is traceable.

## Relationships

```text
001 Transcript 1───1 ClassNote 1───* Citation/Reference
                          └───0..1 ReviewRecord ──(on approval)──► ChromaDB chunk(s) → KG
```
