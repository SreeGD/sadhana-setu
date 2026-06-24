# Phase 0 Research: App Enrichment from the Hari-Nāma Corpus

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Requirements-level questions were resolved in the spec's `## Clarifications`. This document
records the engineering decisions from a read-only audit of the app.

## R1 — Generalize `005`'s retrieval into a shared service

**Audit**: `005`'s `sadhana_setu/flows/harinaam_teaching.py::fetch_teaching(theme, *, querier)`
already does: live-ChromaDB `kind=harinaam-note` query (bridged to vidya-karana's venv) → clean
teaching read from the note file → `ReadingStage | None`. It is single-result and has no cache or
dedup.

**Decision**: Introduce `sadhana_setu/flows/corpus_teaching.py` — a shared
`get_for_surface(theme, surface_id, *, date, state, querier)` that returns one **clean, cited,
reviewed** teaching not already surfaced today (or None). `harinaam_teaching.fetch_teaching`
becomes a thin wrapper / is refactored to delegate, so **pre-japa participates in the same cache +
dedup**. Reuses the existing clean-text-from-note-file and bridge logic.

**Rationale**: One retrieval path (FR-001), one review gate, consistent clean+cited output across
all surfaces (pre-japa, Nama-Tattva, Saturday, study view).

**Alternatives**: per-surface ad-hoc queries (rejected — drift + review-gate risk).

## R2 — Per-day caching across surfaces (FR-012)

**Audit**: Streamlit reruns the whole script on every interaction; surfaces open via
`app.py`'s `st.radio` dispatch.

**Decision**: Cache the resolved candidate list per `(date, theme)` so the ~2 s bridge runs at most
once per theme per day. Implementation: a memoized resolver (keyed by date+theme) plus a per-day
**surfaced-set** held in `st.session_state` (`corpus_surfaced_<date>`) that the UI passes in as
`state`; the flows service stays Streamlit-free and takes `state` as a plain mutable dict for
testability.

**Rationale**: Bounds the bridge cost (FR-012); survives reruns; keeps the service unit-testable
without Streamlit.

## R3 — Within-day de-duplication (FR-013)

**Decision**: The per-day `state` records `surfaced` lecture-ids. `get_for_surface` returns the
top candidate whose lecture-id is not in `surfaced`, then adds it. A surface with no remaining
fresh candidate returns None → curated fallback. Pre-japa, Nama-Tattva, Saturday all share the
same `state`, so each gets a distinct teaching when the corpus has enough.

**Rationale**: Distinct teachings per day across surfaces (FR-013); self-correcting with a small
corpus (extra surfaces fall back to curated).

## R4 — Per-surface theme (FR-014)

**Decision**: Daily surfaces (pre-japa, Nama-Tattva) pass the day's value
(`flows/today_value.pick_today_value`). The Saturday check-in passes the week's sankalpa/focus from
`flows/saturday.get_checkin(most_recent_saturday()).tone`/`mood_bhava` (falling back to the day's
value when no check-in exists).

## R5 — The three surfaces in the current app (FR-010)

**Audit**: `app.py` views = Pre-japa, Today, This Week, Saturday Check-in, History. Nama-Tattva is
**not** a standalone view today — it was a card inside the old pre-japa; `005` folded it into the
arc's "deepen" stage. The Saturday view uses curated questions.

**Decision**:
- **Nama-Tattva** → a new lightweight **"Nama-Tattva" nav view**: one deeper daily teaching
  (corpus-preferred), distinct from pre-japa's deepen via the shared dedup. (Keeps pre-japa short;
  gives a dedicated "teaching on the Name" surface.)
- **Saturday check-in** → add an optional corpus teaching to the reflection half, themed by the
  week's sankalpa.
- **Study/browse view** → a new **"Notes" nav view** listing reviewed notes (read from
  `corpus/notes/<set>/<id>.md`, `status: reviewed` only) by speaker/seminar, rendered clean.

**Rationale**: Matches the clarified scope (all three) with minimal disruption to existing views;
reuses the corpus/notes files already on disk.

## R6 — Reading reviewed notes for the study view (FR-009)

**Decision**: The study view enumerates `corpus/notes/**/*.md`, parses front-matter, shows only
`status: reviewed`, groups by `set_id`/speaker, and renders the note Markdown. No ChromaDB needed
(files on disk) — fast and offline-friendly.

## Clarification status

All spec `[NEEDS CLARIFICATION]` resolved (Session 2026-06-24). One structure decision for this
plan — refactor pre-japa to delegate to the shared service so it joins the dedup — is decided in
R1. No open research items.
