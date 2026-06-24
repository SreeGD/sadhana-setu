# Data Model: Pre-japa Reading for Transformation

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

In-memory model only — no persistence. The arc is assembled per day by
`flows/prejapa_reading.py` and rendered by `ui/prejapa_view.py`.

## Entity: PrejapaReading

The full daily threshold reading (the transformation arc).

| Field | Type | Notes |
|---|---|---|
| `date` | date | The day; drives deterministic selection (FR-007). |
| `orient` | ReadingStage | Disposition + glory of the Name. |
| `deepen` | ReadingStage | The Hari-Nāma teaching (corpus or curated). |
| `apply` | Contemplation | One optional micro-practice (FR-005). |
| `enter` | Resolve | Closing resolve that points into japa (FR-002). |
| `sankalpa_echo` | str \| None | Optional gentle echo of the week's tone/bhava (FR-012). |
| `corpus_online` | bool | False ⇒ a quiet "corpus offline" note is shown (FR-008). |

### Validation rules

- `orient`, `deepen`, `enter` MUST be present; `apply` MUST be present but is optional to engage.
- `deepen` MUST carry a citation when `source_kind == "corpus"` (FR-003/004); curated fallback
  carries its existing source.
- The whole reading MUST be assemblable without kg-mcp (every stage has a curated fallback) — SC-004.

## Entity: ReadingStage

| Field | Type | Notes |
|---|---|---|
| `label` | str | e.g. "Orient", "A teaching on the Holy Name". |
| `body` | str | The text (verse/teaching/orientation line). |
| `citation` | str \| None | speaker + lecture, or book + verse. Required for corpus content. |
| `source_kind` | enum `corpus` \| `curated` | Provenance of this stage's content. |

## Entity: Contemplation (the micro-practice)

| Field | Type | Notes |
|---|---|---|
| `kind` | enum `sit_with` \| `prayer` \| `question` | The form of the practice. |
| `prompt` | str | One short line to sit with / repeat once / hold. |
| `citation` | str \| None | If verse-bearing (e.g. tṛṇād api sunīcena). |

- Requires **no input, no tracking, no scoring** (Constitution IV / FR-005).

## Entity: Resolve

| Field | Type | Notes |
|---|---|---|
| `text` | str | A resolve/prayer to carry into chanting, drawn from the day's reading (FR-002/012). |

## Relationships

```text
PrejapaReading
├── orient : ReadingStage (curated: affirmation + Name-glory)
├── deepen : ReadingStage (corpus harinaam-note → curated nama_tattva fallback)
├── apply  : Contemplation (derived/curated)
├── enter  : Resolve (from the reading)
└── sankalpa_echo : str? (read-only from WeeklyCheckin.tone/mood_bhava)
```

## Source mapping (existing content → arc stage)

| Arc stage | Existing source repurposed |
|---|---|
| orient | `content/affirmations` (sankalpa declaration) + `content/faith_verses` (Name glory) |
| deepen | `flows/harinaam_teaching` (kg-mcp) → `content/nama_tattva` fallback; `content/inspirations` as support |
| apply | `content/contemplations` (new, small, curated) |
| enter | resolve composed from the reading; `flows/saturday.get_checkin` for the optional echo |

Saturday: `content/bhajans` (bhajan of the week) folds into orient/deepen; the standalone
story/tip/book-tip peer cards are dropped or folded to keep the arc within budget (FR-010).
