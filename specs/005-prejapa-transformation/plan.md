# Implementation Plan: Pre-japa Reading for Transformation

**Branch**: `005-prejapa-transformation` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-prejapa-transformation/spec.md`

## Summary

Redesign the pre-japa reading from an informational card layout into a **transformation arc** —
**orient → deepen → apply → enter japa** — within the existing ~60–75s budget. The "deepen" stage
surfaces one **reviewed, KG-grounded Hari-Nāma teaching** via a self-contained `kg-mcp` call
(falling back to curated libraries when offline); the "apply" stage offers one optional
contemplative micro-practice (no input/scoring); the "enter" stage closes with a resolve drawn
from the reading plus an optional gentle echo of the week's sankalpa. Existing content is
restructured into the arc, not stacked beside it. All sattvic-medium constraints carried over.

## Technical Context

**Language/Version**: Python 3.11+ / Streamlit (the existing app stack).

**Primary Dependencies**: Streamlit; existing content modules (`sadhana_setu/content/*`); the
existing MCP client `sadhana_setu/mcp_client.py::call_tool_sync` → `kg-mcp`;
`flows/saturday.py::get_checkin` (sankalpa echo); `flows/today_value.py`.

**Storage**: None new. Reads existing content YAML, the weekly check-in (SQLite, read-only here),
and kg-mcp at runtime. Daily selection is deterministic by date (no persistence).

**Testing**: `pytest`. Arc assembly (`flows/prejapa_reading.py`) is unit-tested with mocked
`call_tool_sync` and a fixture check-in; the Streamlit `render()` is import-safe and exercised by
a light smoke test (no browser).

**Target Platform**: Local Streamlit app (macOS) + the static build path where applicable.

**Project Type**: UI feature + a thin domain/flows layer (single project), extending the app.

**Performance Goals**: The reading renders within the ~60–75s human budget; the kg-mcp call is
best-effort with a fast curated fallback (no blocking/hanging on corpus offline).

**Constraints**: Sattvic medium (no streaks/scoring/push/quantification, no screen-during-japa);
all Sanskrit/teaching content citation-bearing + KG-grounded; daily-stable; graceful fallback.

**Scale/Scope**: Single practitioner; one reading per day; modest content.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Teaching/verses KG-grounded + cited; curated fallback is pre-existing
  reviewed content (FR-003/004). ✅
- **II. Provenance** — Every surfaced teaching carries its citation (speaker+lecture or book+verse). ✅
- **III. Attribution** — Citations name the speaker/source. ✅
- **IV. Sattvic Medium** — No metrics/scoring/streaks/push; micro-practice requires no input;
  screen silent during japa (FR-005/006). ✅
- **V. Review Gate** — Only reviewed `002` notes (`kind=harinaam-note`) are surfaced; unreviewed
  never appear. ✅
- **VI. Local-First** — Runs locally; kg-mcp is the existing local subprocess; graceful offline. ✅
- **VII. Monorepo Conventions** — Code under `sadhana_setu/`; no new content trees beyond a small
  curated contemplations set. ✅
- **VIII. Reuse Vidya-Karana** — Teaching via the existing `kg-mcp` path; no new retrieval stack. ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/005-prejapa-transformation/
├── plan.md
├── spec.md
├── research.md
├── data-model.md        # arc + reading entities (DONE)
├── quickstart.md        # validation scenarios (DONE)
├── contracts/           # reading-assembly + review rubric (DONE)
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
sadhana_setu/
├── flows/
│   ├── prejapa_reading.py     # assemble the arc: orient/deepen/apply/enter (+ fallbacks); date-stable
│   └── harinaam_teaching.py   # self-contained kg-mcp call for one reviewed harinaam-note (+ fallback)
├── content/
│   └── contemplations.py      # small curated micro-practice prompts (prayer / holding-question)
└── ui/
    └── prejapa_view.py        # REWRITTEN render() — renders the arc; CSS retained/extended

data/
└── contemplations.yaml        # curated prompts (reviewed content)

tests/
├── test_prejapa_reading.py    # arc assembly: stages present, grounded teaching, fallback, daily-stable
└── test_harinaam_teaching.py  # mocked call_tool_sync: harinaam-note preferred; offline fallback
```

**Structure Decision**: A thin `flows/prejapa_reading.py` owns the arc assembly + fallback logic
(unit-testable, no Streamlit), and `ui/prejapa_view.py` becomes a thin renderer over it. The
corpus call is isolated in `flows/harinaam_teaching.py`. This keeps transformation logic testable
and the UI declarative.

## Key design decisions (finalized in data-model.md / contracts/)

1. **Arc model**: a `PrejapaReading` with four stages (orient, deepen, apply, enter) + optional
   sankalpa echo; each stage carries text + citation + a `source_kind` (corpus | curated).
2. **Teaching retrieval**: `harinaam_teaching.py` queries `search_corpus` (kg_augmented) by the
   day's value/theme, prefers `kind=harinaam-note`, returns text+citation or `None`.
3. **Fallback chain**: corpus → curated `nama_tattva`; per-stage curated fallbacks so the reading
   always renders (FR-008); a quiet "corpus offline" note when fallback is used.
4. **Daily stability**: deterministic selection by `date.today()` ordinal (existing convention).
5. **Micro-practice**: derived from grounded content where possible; otherwise a curated
   `contemplations` prompt. No input, no tracking (FR-005).
6. **Sankalpa echo**: read-only `get_checkin(most_recent_saturday())`; render `tone`/`mood_bhava`
   as a gentle one-liner; the resolve itself comes from the reading (FR-012).
7. **Evaluation**: a build-time design-review rubric (arc present + sattvic audit) — see
   `contracts/review-rubric.md` (FR-011); no runtime measurement.

## Complexity Tracking

No constitution violations; no entries required.
