# Data Model: App Enrichment

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

In-memory only — no new persistence. The shared service resolves teachings at runtime and caches
per day; the study view reads note files from disk.

## Entity: Teaching (retrieved)

One reviewed, themed unit returned by the shared service for display on a surface.

| Field | Type | Notes |
|---|---|---|
| `body` | str | Clean teaching text (read from the note file, not the mangled ChromaDB chunk). |
| `citation` | str | speaker — lecture (e.g. "Bhūrijana Prabhu — Holy Name Seminar 01"). |
| `lecture_id` | str | Identifies the source note; the dedup key. |
| `set_id` | str | Owning source set (speaker/seminar). |
| `source_kind` | const `corpus` | Distinguishes from a curated fallback at the call site. |

- Only notes with `status: reviewed` / `kind=harinaam-note` ever become a Teaching (Constitution V).

## Entity: RetrievalState (per-day cache + dedup)

A plain mutable dict the UI holds in `st.session_state["corpus_<date>"]` and passes to the service.

| Key | Type | Notes |
|---|---|---|
| `theme_cache` | dict[str, list[Candidate]] | `theme → resolved candidates`; bounds the ~2 s bridge to once per theme per day (FR-012). |
| `surfaced` | set[str] | `lecture_id`s already shown today across surfaces — enforces dedup (FR-013). |

State machine: created empty per date; `theme_cache` fills lazily on first query of a theme;
`surfaced` grows as surfaces consume teachings; discarded at day rollover (a new date key).

## Entity: EnrichedSurface

An app view that consumes the service with a curated fallback.

| Surface | Theme (FR-014) | Curated fallback |
|---|---|---|
| Pre-japa "deepen" (`005`, refactored) | day's value | `nama_tattva` |
| Nama-Tattva view (new) | day's value | `nama_tattva` |
| Saturday check-in | week's sankalpa (`tone`/`mood_bhava`) → day's value | (none / question library) |
| Study/Notes view (new) | — (browses all reviewed notes) | — |

## Entity: ReviewedNote (study view, from disk)

| Field | Type | Source |
|---|---|---|
| `set_id` / `lecture_id` | str | front-matter |
| `speaker` / `title` | str | front-matter |
| `status` | enum | only `reviewed` listed |
| `body` | markdown | the note's rendered sections |

## Relationships

```text
EnrichedSurface --uses--> corpus_teaching.get_for_surface(theme, surface, date, state)
                              │  (cached per date+theme; dedup via state.surfaced)
                              └── Teaching | None ── None ⇒ curated fallback
Study view --reads--> corpus/notes/<set_id>/<lecture_id>.md  (status: reviewed only)
```
