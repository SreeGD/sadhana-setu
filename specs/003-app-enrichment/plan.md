# Implementation Plan: App Enrichment from the Hari-Nāma Corpus

**Branch**: `003-app-enrichment` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-app-enrichment/spec.md`

## Summary

Generalize `005`'s pre-japa corpus retrieval into a **shared, cached, de-duplicating service**
(`flows/corpus_teaching.py`) and use it to surface reviewed, KG-grounded Hari-Nāma teachings across
three app surfaces — a new **Nama-Tattva** view, the **Saturday check-in**, and a new **study/
browse "Notes"** view. Each surface prefers a corpus teaching (clean text from the note file,
cited) and falls back to its curated library; the day's retrieval is cached once and teachings are
de-duplicated across surfaces. Pre-japa is refactored to delegate to the shared service so it
joins the dedup. All Sattvic-Medium constraints carry over.

## Technical Context

**Language/Version**: Python 3.11+ / Streamlit (the existing app).

**Primary Dependencies**: existing `flows/harinaam_teaching.py` (reused/generalized), the
`corpus/notes/**/*.md` files on disk, `flows/today_value`, `flows/saturday.get_checkin`, the
vidya-karana venv bridge (live ChromaDB). No new third-party deps.

**Storage**: None new. Reads `corpus/notes/` (reviewed notes) + live ChromaDB at runtime; per-day
cache + surfaced-set held in `st.session_state` (UI) / a plain dict (service).

**Testing**: `pytest`. The service (`corpus_teaching.py`) is unit-tested with an injected
`querier` + a plain `state` dict (cache + dedup, no Streamlit). Views get import-safe smoke tests.

**Target Platform**: Streamlit app (macOS) + the static build where applicable.

**Project Type**: UI feature + a thin shared flows service, extending the app.

**Performance Goals**: Live-ChromaDB query runs at most once per theme per day (cached); surfaces
render snappily from cache/curated.

**Constraints**: Sattvic medium (no metrics/scoring/streaks/push); only reviewed (`harinaam-note`)
content; clean cited text; graceful curated fallback; daily/weekly stable; de-duplicated per day.

**Scale/Scope**: Single practitioner; a handful of surfaces; modest corpus.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Only reviewed, KG-grounded notes; clean cited text (FR-002/003). ✅
- **II. Provenance** — Citations (speaker + lecture) preserved on every surfaced teaching. ✅
- **III. Attribution** — Speaker/lecture shown. ✅
- **IV. Sattvic Medium** — No metrics/scoring/streaks/push; teachings deepen, don't quantify. ✅
- **V. Review Gate** — `kind=harinaam-note` + `status: reviewed` only; unreviewed never surfaced. ✅
- **VI. Local-First** — Notes on disk; live ChromaDB local via the existing bridge; graceful
  offline → curated. ✅
- **VII. Monorepo Conventions** — Code under `sadhana_setu/`. ✅
- **VIII. Reuse Vidya-Karana** — Reuses the `005` retrieval/bridge; no new retrieval stack. ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-app-enrichment/
├── plan.md
├── spec.md
├── research.md
├── data-model.md        # CorpusTeaching, RetrievalCache, EnrichedSurface (DONE)
├── quickstart.md        # validation scenarios (DONE)
├── contracts/           # corpus-teaching service API + study-view contract (DONE)
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
sadhana_setu/
├── flows/
│   ├── corpus_teaching.py     # SHARED service: get_for_surface(theme, surface, *, date, state, querier)
│   │                          #   live-ChromaDB candidates (cached per date+theme), dedup via state,
│   │                          #   clean text from note file, cited; None ⇒ curated fallback
│   ├── harinaam_teaching.py   # refactor: delegate to corpus_teaching (pre-japa joins dedup)
│   └── corpus_notes.py        # enumerate/parse reviewed notes from corpus/notes/ (study view)
└── ui/
    ├── nama_tattva_view.py    # NEW nav view: one deeper daily teaching (corpus-preferred)
    ├── notes_view.py          # NEW nav view: browse + read reviewed notes by speaker/seminar
    ├── saturday_view.py       # add optional corpus teaching (themed by week's sankalpa)
    └── app.py                 # add "Nama-Tattva" and "Notes" to VIEWS + dispatch

tests/
├── test_corpus_teaching.py    # cache + dedup + clean text + curated-fallback (injected querier/state)
└── test_corpus_notes.py       # reviewed-only enumeration/parse
```

**Structure Decision**: A single `flows/corpus_teaching.py` owns retrieval + cache + dedup
(Streamlit-free, unit-testable); `harinaam_teaching` delegates to it so pre-japa shares the dedup;
two new thin views plus a Saturday tweak consume it. The study view reads notes from disk
(`flows/corpus_notes.py`), no ChromaDB.

## Key design decisions (finalized in data-model.md / contracts/)

1. **Shared service**: `get_for_surface(theme, surface_id, *, date, state, querier=None)
   -> Teaching | None`. Resolves candidates (cached per date+theme), returns the top not in
   `state["surfaced"]`, marks it; None ⇒ caller uses curated.
2. **Cache + dedup state**: a plain dict per day (`{"theme_cache": {...}, "surfaced": set()}`),
   held in `st.session_state["corpus_<date>"]` by the UI, passed to the service.
3. **Per-surface theme** (FR-014): daily = `pick_today_value(date)`; Saturday = week's
   `tone`/`mood_bhava` from `get_checkin`, falling back to the day's value.
4. **Prefer corpus** (FR-011): each surface tries the service first, then its curated library.
5. **Study view**: list `corpus/notes/**/*.md` with `status: reviewed`, grouped by speaker/seminar,
   rendered clean (no ChromaDB); unreviewed excluded (Constitution V).
6. **Pre-japa refactor**: `harinaam_teaching.fetch_teaching` delegates to `corpus_teaching` (passing
   the same per-day `state`) so its teaching participates in dedup.

## Complexity Tracking

No constitution violations; no entries required.
