# Quickstart: App Enrichment

Validation guide for `003`. Contracts + data model in [`contracts/`](./contracts/) and
[`data-model.md`](./data-model.md).

> Status: **specified + planned, not yet implemented.** Depends on `001`/`002` (reviewed notes)
> and reuses the `005` retrieval bridge.

## Prerequisites

- The app runs (`make run`); the repo has ≥1 reviewed note under `corpus/notes/`.
- For live corpus content: vidya-karana venv reachable (same bridge as `005`); otherwise surfaces
  fall back to curated content.

## Scenario 1 — Nama-Tattva surfaces a corpus teaching (US2)

`make run` → open **Nama-Tattva**.

**Expect**: a reviewed Hari-Nāma teaching (clean text + "speaker — lecture" citation) when the
corpus matches today's value; otherwise the curated nāma-tattva. Stable within the day.

## Scenario 2 — Saturday check-in reflection teaching (US3)

Open **Saturday Check-in** (with a recent check-in present).

**Expect**: an optional corpus teaching themed by the week's sankalpa (`tone`/`mood_bhava`);
clean + cited; absent cleanly when no match. No scoring/tracking.

## Scenario 3 — De-dup across surfaces (FR-013)

Open Pre-japa, then Nama-Tattva, then Saturday on the same day.

**Expect**: each shows a *distinct* reviewed teaching (or curated fallback once the corpus is
exhausted) — never the identical teaching twice in a day.

## Scenario 4 — Caching (FR-012)

Open and re-open the enriched surfaces repeatedly in one day.

**Expect**: the ~2 s live-ChromaDB bridge runs at most once per theme per day; re-opens are
instant (served from `state["theme_cache"]`).

## Scenario 5 — Study / Notes view (US4)

Open **Notes**.

**Expect**: reviewed notes listed by speaker/seminar; selecting one renders its clean Markdown;
`draft` notes never appear; empty-state message when none exist.

## Scenario 6 — Graceful fallback (FR-004, SC-003)

Stop the vidya-karana bridge (corpus offline).

**Expect**: every surface still renders via curated content; the Notes view still lists on-disk
reviewed notes; no errors or empty breaks.

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 reviewed + cited only | 1, 2, 5 |
| SC-002 clean text | 1, 2 |
| SC-003 graceful fallback | 6 |
| SC-004 zero sattvic violations | 1–5 (UX review) |
| SC-005 stable within period | 1, 4 |
