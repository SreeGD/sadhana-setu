# Phase 5 — Issues

> Output of Phase 5: the PRD turned into individual tickets with blocking relationships. Each ticket is small enough that a coding agent can execute it in one focused pass. AC numbers reference acceptance criteria in `04_prd.md` §11.

## Milestones (kanban shape)

```
M0 — Foundations
   ├──► M1 — Content seed
   │       ├──► M2 — Pre-japa flow
   │       └──► M4 — Saturday check-in
   ├──► M3 — Daily capture
   ├──► M2 — Pre-japa flow
   └──► M4 — Saturday check-in
                  └──► M5 — Pattern engine
M0/M1/M2/M3/M4/M5 ──► M6 — Sacred constraints + polish
                       └──► M7 — Testing + docs ──► v1 ship
```

## Tickets

### M0 — Foundations (parallel, no blockers)

#### T-001 — Project scaffold
- **Path:** `capstone/code/`
- **Do:** create `pyproject.toml` with deps (streamlit, sqlite via stdlib, mcp-sdk, scipy, pingouin, python-dateutil, pytest); set up `sadhana_setu/` package layout; add `.env.example`, `.gitignore`, `Makefile` targets (`run`, `test`, `lint`).
- **AC:** infrastructure for AC1–AC12; nothing user-visible yet
- **Blocked by:** —

#### T-002 — SQLite schema + migrations
- **Do:** implement the 6 tables from PRD §7 in `sadhana_setu/db/schema.py`; a `migrate()` function idempotently creates them; single-file `data/sadhana_setu.db` location, configurable via env.
- **AC:** AC10
- **Blocked by:** T-001

#### T-003 — MCP client + smoke test
- **Do:** implement `sadhana_setu/mcp_client.py` with a thin wrapper around the MCP SDK. Connect to `kg-mcp` via stdio (default) or HTTP (`KG_MCP_TRANSPORT=streamable-http`). Smoke test: `python -m sadhana_setu.mcp_client smoke` calls `kg_status()` and `get_verse("BG 18.66")` and prints both.
- **AC:** AC11
- **Blocked by:** T-001

#### T-004 — Streamlit app skeleton
- **Do:** `sadhana_setu/ui/app.py` with sidebar navigation: Pre-japa, Today, Saturday Check-in, History. Each tab a placeholder ("not yet implemented"). `streamlit run sadhana_setu/ui/app.py` launches and renders.
- **AC:** infrastructure for AC1–AC3
- **Blocked by:** T-001

#### T-005 — Ekadasi calendar seed
- **Do:** create `data/ekadasi.json` covering 2026-01-01 through 2031-12-31 (sourced from ISKCON's Vaisnava calendar — scrape `vaishnavacalendar.com` once at install or hand-curate). Implement `sadhana_setu/calendar.py::is_ekadasi(date)`.
- **AC:** supports AC2, AC6
- **Blocked by:** T-001

### M1 — Content seed (one user review pass required before ship)

#### T-006 — Tip library: schema + loader
- **Do:** YAML schema in `data/tips.yaml`; loader in `sadhana_setu/content/tips.py`; selection function `pick_tip(value_ids: list, ekadasi: bool) -> Tip` that returns a random tip preferring ekadasi-tagged when on ekadasi.
- **AC:** AC3
- **Blocked by:** T-001

#### T-007 — Tip library: seed ~40 tips (LLM-drafted, user-reviewed)
- **Do:** generate 3–5 tips per relevant value across 12 values (`kirtan`, `bhakti`, `pratijna`, `shraddha`, `svadhyaya`, `shaucha`, `guru_bhakti`, `tulasi_seva`, `dhyana`, `ishvara_pranidhana`, `seva`, `prema`). Each tip cites a real Prabhupada-book source. **Includes a user review checkpoint** — user signs off each tip before it ships in the library.
- **AC:** AC3, AC7
- **Blocked by:** T-006

#### T-008 — Weekly question library: schema + loader
- **Do:** YAML schema in `data/weekly_questions.yaml`; loader in `sadhana_setu/content/questions.py`; rotation selector `pick_questions(n=3) -> list[Question]` that prefers questions where `last_asked` is null or oldest.
- **AC:** AC3
- **Blocked by:** T-001, T-002 (for last_asked tracking)

#### T-009 — Weekly question library: seed ~40 questions
- **Do:** ~40 sastra-rooted questions seeded from PRD §10.2 examples plus 30+ more (mix of direct and Siksastakam/BG/SB-routed). User review checkpoint.
- **AC:** AC3, AC7
- **Blocked by:** T-008

### M2 — Pre-japa flow

#### T-010 — Pre-japa quote selection
- **Do:** `sadhana_setu/flows/prejapa.py::pick_quotes(today_value: str, hearing_thread: HearingThread | None) -> list[Quote]`. Calls `search_corpus(mode="kg_augmented", entity_filters={"value": [today_value, "kirtan", "bhakti"]}, top_k=3)`. If `hearing_thread` exists, attempts a second quote that builds on it. Filters out chunks without `verse_ref`. Returns 1–2 quotes with text + source + author.
- **AC:** AC1, AC7
- **Blocked by:** T-003

#### T-011 — Today-value selector
- **Do:** picks one of the 12 relevant values for "today's value" — drives both quote retrieval and tip selection. Strategy: rotate weekly, with the user's chosen sankalpa value from last Saturday's check-in pinned (if set).
- **AC:** AC1
- **Blocked by:** T-002

#### T-012 — Pre-japa view (Streamlit)
- **Do:** `sadhana_setu/ui/prejapa_view.py` renders 1–2 quotes with citation chips + 1 tip. Layout per PRD §8 Flow A. Glanceable. Includes a `[Close]` button that records the view event (lightweight, no judgment) for "did the user actually use it?" analytics local-only.
- **AC:** AC1, AC7
- **Blocked by:** T-004, T-010, T-011, T-006, T-007

#### T-013 — Citation chip component
- **Do:** reusable component used across Pre-japa, Saturday check-in, History. Renders a citation in the format from PRD §10.7. Hover/expand to show full purport text (lazy-load via `get_verse`).
- **AC:** AC7
- **Blocked by:** T-004, T-003

### M3 — Daily capture

#### T-014 — Today view (rounds + hearing capture)
- **Do:** `sadhana_setu/ui/today_view.py` renders the daily capture form per PRD §8 Flow B. Rounds: numeric input 0–20 with one-click `[16]` shortcut. Hearing: source dropdown (SB / BG / CC + custom) + one-line text. Save to `rounds` and `hearing_notes` tables. Idempotent on re-edit for the same date.
- **AC:** AC2, AC10
- **Blocked by:** T-002, T-004

### M4 — Saturday check-in

#### T-015 — Weekly history aggregator
- **Do:** `sadhana_setu/aggregator.py::week_at_a_glance(week_start: date) -> WeekSummary` returns rounds-completed-per-day, hearing note count, median sleep time (if tracked), median wake time (if tracked). Pure function for unit testing.
- **AC:** AC3
- **Blocked by:** T-002

#### T-016 — Saturday Half 1 — Observe view
- **Do:** `sadhana_setu/ui/saturday_observe_view.py`. Renders week-at-a-glance (T-015 output) + 2–3 rotating questions (T-008/T-009). Each question is a short text input. Submit advances to Half 2.
- **AC:** AC3
- **Blocked by:** T-004, T-008, T-009, T-015

#### T-017 — Saturday Half 2 — Set view
- **Do:** `sadhana_setu/ui/saturday_set_view.py`. Tone (single line), Mood/bhava (single line with optional suggestion list from sastra — *trnad api sunicena*, *dasya*, etc.), Practices (repeatable list), Tools needed (repeatable list), Priorities (orderable list). Renders pattern observation from M5 below it.
- **AC:** AC3
- **Blocked by:** T-004

#### T-018 — Saturday check-in persistence
- **Do:** on submit, persist all of Half 1 + Half 2 + the pattern result as a single row in `weekly_checkins`. Update `last_asked` on each question used. Refuse to submit twice for the same `week_start`.
- **AC:** AC3, AC10
- **Blocked by:** T-002, T-016, T-017

### M5 — Pattern engine

#### T-019 — Pattern engine: data assembly
- **Do:** `sadhana_setu/patterns/assemble.py::build_pairs(history, predictor_id) -> list[(predictor_value, outcome_value)]`. Pure function. Handles missing data honestly (drops days where either side is missing; reports n_used).
- **AC:** AC4
- **Blocked by:** T-002

#### T-020 — Pattern engine: statistics
- **Do:** `sadhana_setu/patterns/stats.py` — Spearman ρ via `scipy.stats.spearmanr`; JZS-prior Bayes factor for correlation via `pingouin.corr` or hand-rolled. Returns `(rho, p_value, bf)`.
- **AC:** AC6
- **Blocked by:** T-019

#### T-021 — Pattern engine: rule orchestrator
- **Do:** `sadhana_setu/patterns/engine.py::surface_pattern(history) -> PatternResult`. Implements the five-condition Saturday-firing rule from PRD §10.3 / `02_research.md`: N≥21, pre-registered ≤3 predictors, |ρ|≥0.35 AND BF≥3, BH-FDR at q=.10, stable in recent 14-day window. Returns either `PatternResult(kind="pattern", ...)` or `PatternResult(kind="silent", ...)` with the honest null phrasing.
- **AC:** AC4, AC5, AC6
- **Blocked by:** T-019, T-020

#### T-022 — Pattern engine: audit log
- **Do:** every Saturday fire writes a row to `patterns_log` regardless of outcome. Captures candidates_checked, statistics, qualifying_pattern.
- **AC:** AC4, AC5, AC6, AC10
- **Blocked by:** T-002, T-021

#### T-023 — Pattern engine: integration into Saturday check-in
- **Do:** Saturday view calls `surface_pattern(history)` and renders the result inline in Half 2 per PRD §8 Flow C. Silent case shows the honest null phrasing.
- **AC:** AC11 (in spirit)
- **Blocked by:** T-017, T-021, T-022

### M6 — Sacred constraints + polish

#### T-024 — Protected-hours guard
- **Do:** `sadhana_setu/guards.py::in_protected_hours(now) -> bool` returns True for 3:30–9:30 AM and 8:30–10:30 PM. UI layer reads this and disables all modals/prompts/toasts during those windows. Pre-japa view still renders (it's the only allowed thing).
- **AC:** AC8 (in spirit — the no-notifications floor)
- **Blocked by:** T-004

#### T-025 — kg-mcp offline graceful degradation
- **Do:** if `kg-mcp` connection fails, all views still render. Pre-japa shows a "corpus offline — only tips available today" placeholder. Saturday check-in still works without the pattern's verse-grounded surfacing.
- **AC:** AC9
- **Blocked by:** T-003, T-012, T-016

#### T-026 — Sattvic-medium audit
- **Do:** code review pass + UX walkthrough confirming zero violations: no streaks counter anywhere, no badges, no lifetime-count motivator, no push API import, no toast notifications, no "X days in a row!" copy. Written report.
- **AC:** AC8
- **Blocked by:** T-012, T-014, T-016, T-017, T-023

### M7 — Testing + docs

#### T-027 — Unit tests: pattern engine
- **Do:** `tests/test_patterns.py`. Cases: silence at N<21; silence at N≥21 with no qualifying predictor; fire on synthetic positive (constructed data that passes all five conditions); FDR correction across the pre-registered set.
- **AC:** AC4, AC5, AC6
- **Blocked by:** T-021

#### T-028 — Smoke tests: three flows
- **Do:** `tests/test_flows.py`. End-to-end: launch Streamlit in headless mode (or via direct domain-layer calls) and walk Pre-japa, Today, Saturday Check-in flows. Asserts persistence to SQLite + citations rendered.
- **AC:** AC12
- **Blocked by:** T-012, T-014, T-018, T-023

#### T-029 — README + setup
- **Do:** `capstone/code/README.md` with install (uv / pip), first-run setup (kg-mcp running, ekadasi calendar seeded), how to launch (`streamlit run …`), how to run tests. Brief architecture diagram. Link to the seven-phase artifacts (`01_grill.md` through `07_qa_plan.md`).
- **AC:** —
- **Blocked by:** T-028 (so README docs what actually works)

## Summary table

| ID | Title | M | AC | Blocked by |
|---|---|---|---|---|
| T-001 | Project scaffold | M0 | infra | — |
| T-002 | SQLite schema + migrations | M0 | AC10 | T-001 |
| T-003 | MCP client + smoke test | M0 | AC11 | T-001 |
| T-004 | Streamlit app skeleton | M0 | infra | T-001 |
| T-005 | Ekadasi calendar seed | M0 | AC2,6 | T-001 |
| T-006 | Tip library schema + loader | M1 | AC3 | T-001 |
| T-007 | Tip library seed ~40 (LLM+review) | M1 | AC3,7 | T-006 |
| T-008 | Weekly questions schema + loader | M1 | AC3 | T-001,T-002 |
| T-009 | Weekly questions seed ~40 | M1 | AC3,7 | T-008 |
| T-010 | Pre-japa quote selection | M2 | AC1,7 | T-003 |
| T-011 | Today-value selector | M2 | AC1 | T-002 |
| T-012 | Pre-japa view | M2 | AC1,7 | T-004,T-010,T-011,T-006,T-007 |
| T-013 | Citation chip component | M2 | AC7 | T-004,T-003 |
| T-014 | Today view (capture) | M3 | AC2,10 | T-002,T-004 |
| T-015 | Weekly history aggregator | M4 | AC3 | T-002 |
| T-016 | Saturday Half 1 — Observe | M4 | AC3 | T-004,T-008,T-009,T-015 |
| T-017 | Saturday Half 2 — Set | M4 | AC3 | T-004 |
| T-018 | Saturday persistence | M4 | AC3,10 | T-002,T-016,T-017 |
| T-019 | Pattern engine: data assembly | M5 | AC4 | T-002 |
| T-020 | Pattern engine: statistics | M5 | AC6 | T-019 |
| T-021 | Pattern engine: rule orchestrator | M5 | AC4,5,6 | T-019,T-020 |
| T-022 | Pattern engine: audit log | M5 | AC4,5,6,10 | T-002,T-021 |
| T-023 | Pattern engine: integration | M5 | — | T-017,T-021,T-022 |
| T-024 | Protected-hours guard | M6 | AC8 | T-004 |
| T-025 | kg-mcp offline degradation | M6 | AC9 | T-003,T-012,T-016 |
| T-026 | Sattvic-medium audit | M6 | AC8 | T-012,T-014,T-016,T-017,T-023 |
| T-027 | Unit tests: pattern engine | M7 | AC4,5,6 | T-021 |
| T-028 | Smoke tests: three flows | M7 | AC12 | T-012,T-014,T-018,T-023 |
| T-029 | README + setup | M7 | — | T-028 |

**Total: 29 tickets across 8 milestones.**

## Critical path

```
T-001 → T-002 → T-019 → T-020 → T-021 → T-023 → T-028 → T-029
T-001 → T-006 → T-007 (depends on user review) ─┐
T-001 → T-008 → T-009 (depends on user review) ─┴─► T-016 → T-018
```

Two user-review checkpoints are on the critical path: **T-007 (tip library review)** and **T-009 (question library review)**. These are the two pieces only the user can sign off.

## Parallelism

M0 can run with up to 5 concurrent agents (T-001 first, then T-002 / T-003 / T-004 / T-005 in parallel). M1, M2, M3, M4 partially parallel. M5 is a sequential chain.

## Status

**Phase 5 closed 2026-06-09.** 29 tickets cut, dependencies mapped, summary table + critical path identified.

**Ready for Phase 6 (Implement)** — the coding-agent loop that executes these tickets in dependency order.
