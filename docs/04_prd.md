# Phase 4 — PRD: Sadhana Setu

> **Working name** "Sadhana Setu" (सेतु = bridge): the bridge between aspirational sadhana and consistent practice. Name is provisional — open to your choice.
>
> Output of Phase 4 of the seven-phase agentic process. Inputs: `capstone/01_grill.md` (Phase 1 close), `capstone/02_research.md` (Phase 2 close), plus the [[reference-vidya-karana-kg]] system this product composes on top of.

## 1. One-line summary

A typed, local-first sadhana companion that quietly supports the hearing↔chanting loop with **a daily 1-minute pre-japa quote-and-tip drawn from the user's existing Vaishnava corpus, a lightweight rounds-capture, and a 10-minute Saturday check-in** for sankalpa-setting and honest pattern reflection — for one initiated ISKCON practitioner, with family-mode reserved for v2.

## 2. Goals and non-goals

### Goals (v1)

| # | Goal | Measurable as |
|---|---|---|
| G1 | Make the **hearing↔chanting loop** the explicit shape of daily practice | The pre-japa quote+tip is drawn from yesterday's hearing line, when one is captured |
| G2 | Make **Saturday sankalpa-setting** a ritual the user looks forward to | Completion of Saturday check-in for ≥10 of first 13 weeks |
| G3 | Get **count + quality reflection** tracked for 90 consecutive days | Daily rounds field populated; weekly quality reflection captured ≥10/13 weeks |
| G4 | Surface **only honest patterns** — silence is a valid output | Zero pattern-observations fire before N=21; ≥50% of subsequent Saturdays surface no pattern |
| G5 | Honor all **sattvic-medium constraints** from Phase 1 (no streaks/badges/push/screen-during-japa) | Code review + UX review confirms zero violations |

### Non-goals (v1)

- Voice input / STT
- Mobile-native app (iOS / Android)
- Multi-user / family mode
- Push notifications (none, ever)
- Theological Q&A or scripture chatbot
- Health / Ayurveda tracking
- Yoga or fitness coaching
- Document storage / household memory
- Long-distance presence channel with the user's father (Phase 2 of the product)
- Any feature that quantifies, scores, or judges quality on the chanter's behalf

## 3. Primary user

| Trait | Value |
|---|---|
| Name | The user (founder-as-user) |
| Age | 52 |
| Role | ISKCON-initiated householder; works during the day; office meetings 8:30–10:30 PM |
| Sadhana | 3:30 AM wake, japa 4:30–7:10 AM, mangala aarti, SB class, yoga 5–6 PM, temple visit, dinner, 10:45 PM sleep |
| Aspiration vs reality | The schedule is aspirational; not all elements happen on all days |
| Tradition | Gaudiya Vaishnava / ISKCON. Srila Prabhupada's books are the default frame |
| Platform comfort | macOS / Python / Streamlit (already runs vidya-karana-kg locally) |
| Family (v2 audience) | Wife Radhi (43), daughter Anvi (med student), son Advi (just finished 12th), father (80, remote village), three farm workers |

## 4. The product shape

### Daily (background; minimal)

| Moment | What happens | Who initiates |
|---|---|---|
| Pre-japa | Open the app, see 1–2 short sastra quotes + 1 practical tip. Under a minute. Glance, read, close. | User opens |
| During japa | App is closed / silent. No screen, no notifications. | (none) |
| Anytime after | Record rounds completed (tap or number). Record one line from today's hearing (optional). | User initiates, app never asks |

### Saturday (the primary ritual)

A ~10-minute typed check-in. Two halves:

**Half 1 — Observe (the week past):**

1. Show the week's data at a glance (rounds completed per day, hearing notes captured).
2. Present 2–3 rotating questions from a curated library. User types short answers.
3. **Pattern surfacing engine fires** (or stays silent — most weeks, silent is correct).

**Half 2 — Set (the week to come):**

4. **Tone** — short text input ("This week: returning to early rising.")
5. **Mood / bhava** — chosen from sastra-rooted options or typed freely ("trnad api sunicena.")
6. **Practices** — concrete acts list ("Begin japa before 4:45 AM most days.")
7. **Tools needed** — short list of obstacles a tool would remove.
8. **Priorities** — ordered list when not everything fits.

The check-in saves as a single weekly record. Next Saturday compares against it.

## 5. User stories

Numbered for ticket-cutting in Phase 5.

### Daily flow

- **US-001** — As a chanter, I want to see 1–2 short sastra quotes paired with a practical tip before japa, in under a minute, so my chanting begins in the right mood.
- **US-002** — As a chanter, I want every quote to be cited (source + chapter + verse + author of purport) so I can trust the agent never fabricates sastra.
- **US-003** — As a chanter, I want the tip for the day to be paired with the quote (curated, not LLM-generated), so the practical guidance has the same weight as the sloka.
- **US-004** — As a chanter, I want to capture today's rounds with a single tap or number entry, without being asked, so the agent does not interrupt my practice.
- **US-005** — As a chanter, I want to optionally capture one line from today's hearing (SB class, BG, CC), so it can surface in next Saturday's reflection.
- **US-006** — As a chanter, I want the app to be absent during japa itself — no screen interaction expected, no notifications, no presence — because the act of chanting is the work.

### Saturday check-in

- **US-007** — As a chanter, every Saturday I want a 10-minute typed check-in with 2–3 rotating sastra-rooted questions drawn from a curated library, so reflection happens at a sustainable cadence.
- **US-008** — As a chanter, I want to set tone, mood (bhava), practices, and priorities for the coming week, so my sankalpa is explicit.
- **US-009** — As a chanter, I want to identify tools that would remove obstacles to the coming week's practices, so the agent can help track or acquire them.
- **US-010** — As a chanter, I want at most one quiet pattern observation per Saturday — or none, if no pattern qualifies — so I'm not flooded with manufactured insights.
- **US-011** — As a chanter, when no pattern qualifies, I want the agent to say so explicitly ("I checked and didn't find a pattern worth naming") instead of inventing one.

### Sacred constraints

- **US-012** — As a chanter, I never want notifications between 3:30–9:30 AM (sadhana) or 8:30–10:30 PM (office), under any circumstance.
- **US-013** — As a chanter, all my sadhana data stays on my own machine. No cloud sync, no telemetry, no third-party calls without my explicit act.
- **US-014** — As a chanter, I never want streaks, badges, lifetime-count motivators, or any gamification — the practice is its own reward.

### Hearing↔chanting loop

- **US-015** — As a chanter, when I capture a hearing line on Friday, I want it to influence Saturday's pre-japa quote+tip pairing (closing the loop), so today's chanting connects to yesterday's hearing.

## 6. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Sadhana Setu (this project)                  │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │  Streamlit   │    │  Domain      │    │  SQLite              │   │
│  │  UI          │◄──►│  layer       │◄──►│  - rounds            │   │
│  │  (typed)     │    │  (Python)    │    │  - hearing_notes     │   │
│  └──────────────┘    └──────┬───────┘    │  - weekly_checkins   │   │
│                             │            │  - patterns_log      │   │
│                             ▼            └──────────────────────┘   │
│                      ┌──────────────┐                               │
│                      │  Pattern     │                               │
│                      │  engine      │  (Saturday-firing rule)       │
│                      └──────────────┘                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ MCP (stdio or HTTP)
                               ▼
              ┌──────────────────────────────────┐
              │   vidya-karana-kg (existing)     │
              │   ┌────────────┐  ┌──────────┐   │
              │   │ kg-mcp     │  │ ChromaDB │   │
              │   │ 20 tools   │  │ 89,667   │   │
              │   └────────────┘  │ chunks   │   │
              │                   └──────────┘   │
              └──────────────────────────────────┘
```

### Component responsibilities

- **Streamlit UI**: presentation only. Reads from / writes to the domain layer. No business logic.
- **Domain layer (Python)**: orchestrates everything. Reads tips from the curated tip library; calls `kg-mcp` for quotes/verses; reads/writes SQLite; runs the pattern engine.
- **SQLite**: structured user data. Schema in section 7.
- **Pattern engine**: implements the Saturday-firing rule from `02_research.md`. Pure functions; testable in isolation.
- **MCP client**: calls `kg-mcp` tools. Loose coupling. If `kg-mcp` is down, the app still loads (with a clear "corpus offline" indicator); rounds capture still works.

### Why Streamlit

- User has already used Streamlit in vidya-karana (`scripts/chromadb_explorer.py`)
- Zero install pain (runs in browser at `localhost`)
- Forms, rich text, lists are all first-class
- Local-first by default
- Easy to iterate in Phase 6

### Why SQLite

- Single-file, local, zero setup
- Trivial backup (copy the file)
- All v1 data is small enough to never need anything else
- Compatible with the rest of the user's Python ecosystem

## 7. Data model

```sql
-- Daily rounds capture.
CREATE TABLE rounds (
    date TEXT PRIMARY KEY,              -- ISO date 'YYYY-MM-DD'
    count INTEGER NOT NULL,             -- 0..16+
    captured_at TEXT NOT NULL,          -- ISO timestamp
    note TEXT                           -- optional one-liner from chanter
);

-- Optional one-line hearing notes.
CREATE TABLE hearing_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- the day the line came from
    source TEXT,                        -- e.g. 'SB class', 'BG 2.47', 'CC Madhya 17'
    line TEXT NOT NULL,                 -- the user's own words
    captured_at TEXT NOT NULL
);

-- Saturday weekly check-ins.
CREATE TABLE weekly_checkins (
    week_start TEXT PRIMARY KEY,        -- ISO date (the Sunday)
    survey_answers TEXT NOT NULL,       -- JSON: [{question_id, answer}, ...]
    tone TEXT,
    mood_bhava TEXT,
    practices TEXT,                     -- JSON list
    priorities TEXT,                    -- JSON ordered list
    tools_needed TEXT,                  -- JSON list
    surfaced_pattern TEXT,              -- the one observation, or NULL
    submitted_at TEXT NOT NULL
);

-- Curated daily tip library (read-only at runtime; seeded in repo).
CREATE TABLE tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_id TEXT NOT NULL,             -- e.g. 'kirtan', 'bhakti', 'pratijna'
    tip TEXT NOT NULL,
    source TEXT,                        -- e.g. 'NOI verse 1', 'Siksastakam 3'
    ekadasi_aware BOOLEAN DEFAULT 0     -- whether this tip is ekadasi-specific
);

-- Curated weekly question library (read-only at runtime; seeded in repo).
CREATE TABLE weekly_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    routes_through TEXT,                -- e.g. 'Siksastakam 3' if the question references sastra
    last_asked TEXT                     -- ISO date or NULL; for rotation
);

-- Pattern surfacing log (audit trail; never deleted).
CREATE TABLE patterns_log (
    week_start TEXT PRIMARY KEY,
    n_observed_days INTEGER NOT NULL,
    candidates_checked TEXT NOT NULL,   -- JSON: pre-registered predictors
    qualifying_pattern TEXT,            -- NULL if rule fired silent
    statistics TEXT,                    -- JSON: {predictor, rho, bf, fdr_corrected_p}
    fired_at TEXT NOT NULL
);
```

**Multi-user readiness:** every row has a single user implicitly. v2 adds `user_id TEXT NOT NULL DEFAULT 'self'` to every table — migration is trivial. Family mode in v2 builds on this.

## 8. UX flows

### Flow A — Pre-japa (daily)

```
[Open app at ~4:25 AM]
         │
         ▼
┌────────────────────────────────────────────┐
│  Today, before japa                        │
│                                            │
│  [Quote 1, Devanagari + IAST + English]    │
│  — CC Madhya 17.133, Prabhupada's purport  │
│                                            │
│  [Quote 2 — only if hearing line existed]  │
│  — drawn from yesterday's hearing thread   │
│                                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─               │
│                                            │
│  💡 Today's tip:                           │
│  "Sit facing east. Hear each syllable of   │
│   'Krishna' clearly in every round."       │
│                                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─               │
│                                            │
│  [Close]                                   │
└────────────────────────────────────────────┘
         │
         ▼
   [Close app. Begin japa.]
```

### Flow B — Daily capture (anytime after japa)

```
[Open app, "Today" tab]
         │
         ▼
┌────────────────────────────────────────────┐
│  Today — Tuesday, June 2                   │
│                                            │
│  Rounds completed:  [ 16  ▾]    [Save]     │
│                                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─               │
│                                            │
│  Anything from today's hearing?            │
│  (optional, one line, source if you have)  │
│                                            │
│  Source:  [BG 2.47 ▾]                      │
│  Line:    [........................]       │
│                                            │
│  [Save]   [Skip]                           │
└────────────────────────────────────────────┘
```

### Flow C — Saturday check-in

```
[Open app, "Saturday Check-in" tab — only enabled on Saturday]
         │
         ▼
┌────────────────────────────────────────────┐
│  Week of May 25 — May 31                   │
│                                            │
│  Half 1 — Observe                          │
│  ─────────────────                         │
│                                            │
│  Your week at a glance:                    │
│  ▮▮▮▯▮▮▯  rounds completed: 5 of 7         │
│  3 hearing notes captured                  │
│                                            │
│  Q1: Which day this week did the Holy      │
│      Name feel closest?                    │
│  [......................................]  │
│                                            │
│  Q2: Read Siksastakam verse 3. Which line  │
│      spoke to your week?                   │
│  [tṛṇād api sunīcena ... | Click for full] │
│  [......................................]  │
│                                            │
│  Q3: Was there a moment of attentive       │
│      chanting you remember?                │
│  [......................................]  │
│                                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─           │
│                                            │
│  [Continue to Half 2 ▾]                    │
│                                            │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  Half 2 — Set the coming week              │
│  ──────────────────────────                │
│                                            │
│  Tone:        [................]           │
│  Mood (bhava):[..........] [Suggestions ▾] │
│  Practices:                                │
│   • [....................]  [+]           │
│  Tools needed:                             │
│   • [....................]  [+]           │
│  Priorities (drag to reorder):             │
│   1. [....................]                │
│   2. [....................]                │
│                                            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─               │
│                                            │
│  Pattern this week:                        │
│  > I checked for patterns this week and    │
│  > didn't find one worth naming.           │
│  > Here is your raw week: 5/7 days; median │
│  > sleep 10:52 PM.                         │
│                                            │
│  [Save check-in]                           │
└────────────────────────────────────────────┘
```

## 9. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Matches user's existing ecosystem |
| UI | Streamlit | Already used in vidya-karana; zero install pain; forms-first |
| Data store | SQLite (single file) | Local, simple, backup-as-copy |
| Sastra retrieval | MCP client → `kg-mcp` (vidya-karana-kg) | Loose coupling; reuses existing infra |
| LLM (optional) | Local-call only where needed (Claude API allowed with explicit user act) | The MOST text is retrieved, not generated |
| Pattern engine | Pure Python + `scipy.stats` for ρ; Bayes factor via JZS prior implementation (port from R `BayesFactor` or use `pingouin`) | Pure functions; unit-testable |
| Time / calendar | `python-dateutil` + an ekadasi calendar JSON file (one-time seed) | No external calendar service |
| Package manager | `uv` or `pip` + `pyproject.toml` | Match repo norm |
| Tests | `pytest` | Match repo norm |

## 10. Implementation notes (per critical area)

### 10.1 The curated tip library (seed data)

Implementation: a single `data/tips.yaml` or `data/tips.jsonl` file checked into the repo. Format:

```yaml
- value_id: kirtan
  tip: "Sit facing east. Hear each syllable of 'Krishna' clearly in every round."
  source: "NOI verse 1; Siksastakam 1"
  ekadasi_aware: false

- value_id: pratijna
  tip: "Today is Ekadasi. Begin japa earlier than usual; complete before noon if possible."
  source: "Hari-bhakti-vilasa"
  ekadasi_aware: true
```

~10 tips per relevant value × 12 relevant values ≈ **~120 tips total**. Hand-curated. Reviewed by the user before release. **No LLM generation of tips.**

This is one of the few places the project needs the user's deep ISKCON knowledge — drafting and reviewing the tip library is a small but real piece of Phase 6 work.

### 10.2 The curated weekly question library

Same shape — `data/weekly_questions.yaml`. ~30–50 questions. Rotation rule: when picking 2–3 for this Saturday, prefer questions where `last_asked` is null or oldest. Refresh `last_asked` on submit.

A first draft to seed:
1. "Which day this week did the Holy Name feel closest? Which day felt furthest?"
2. "Which verse from this week's SB class stayed with you?"
3. "Read Siksastakam verse 3 (`trnad api sunicena`). Which line spoke to your week?"
4. "Was there a moment of attentive chanting you remember?"
5. "Did any of the ten offenses (nama-aparadha) surface that you want to name?"
6. "What did you hear this week that you don't want to forget?"
7. "Which value from your sankalpa is taking root, and which is still struggling?"
8. "Read NOI verse 3 (`utsahad dhairyat`). Which of the six is your strength right now? Which is your edge?"
9. *(…and ~25 more, drafted by user in Phase 6)*

### 10.3 The pattern surfacing engine

Pure Python module: `sadhana_setu/patterns.py`. One entry point:

```python
def surface_pattern(history: WeeklyHistory) -> PatternResult:
    """
    Returns either:
      - PatternResult(kind="pattern", text=..., statistics={...})  # rule fired
      - PatternResult(kind="silent", text="I checked for patterns this week and didn't find one worth naming.\nHere is your raw week: {raw}")
    """
```

Implements the rule from `02_research.md`:
- N ≥ 21 observed days
- Pre-registered predictors only (configured at install time; v1 default: `prev_night_sleep_time`, `prev_day_rounds_completed`, `ekadasi_today`)
- Spearman |ρ| ≥ 0.35 AND Bayes factor ≥ 3 against null
- BH-FDR at q=.10 across the pre-registered set
- Stable in most recent 14-day window

Audit trail: every Saturday fire writes to `patterns_log` regardless of outcome.

### 10.4 MCP client

Two paths in priority:

1. **Primary** — connect to `kg-mcp` over stdio using the standard MCP SDK. Server is launched by the OS (launchd plist already exists).
2. **Fallback** — direct Python import of `vidya_karana_kg.kg.retrieval` if MCP roundtrip is too slow.

Use the following tools heavily:
- `search_corpus(query, mode="kg_augmented", entity_filters={"value": [...]}, top_k=3)` — pre-japa quotes
- `get_verse(verse_ref)` — full Sanskrit + IAST + translation + purport (for Siksastakam quote inclusion)
- `find_verses(source="Siksastakam", ...)` — verse discovery
- `cross_author_chunks(value_id=this_week_value, authors=["Prabhupada"], limit_per_author=3)` — weekly question grounding
- `value_relationships(value_id, edge_types=["PREREQUISITE"])` — for sankalpa sequencing

### 10.5 Protected hours

Enforce in the UI layer:
- 3:30 AM – 9:30 AM: app launches fine, all read views work, but NO modal popups, NO "did you finish your rounds?" prompts, NO toasts.
- 8:30 PM – 10:30 PM: same.

No push notifications ever (the app has none).

### 10.6 Ekadasi awareness

A one-time seed JSON file with the next 5 years of ekadasi dates (sourced from ISKCON's official Vaishnava calendar — user provides). Lookup is local, no API call.

The ekadasi flag affects:
- Tip selection (prefer `ekadasi_aware: true` tips)
- Pattern surfacing predictor (`ekadasi_today` is one of the three pre-registered)

### 10.7 Citation invariant

**Hard rule:** every quote surfaced to the user has a citation chip. Format:
- "BG 18.66, Prabhupada's purport"
- "Siksastakam 3"
- "SB 1.2.6, Prabhupada's purport"
- "CC Madhya 17.133"

If the corpus returns a chunk without a citable verse_ref, **the chunk is rejected** for pre-japa display. (Other corpus chunks without verse_refs are still usable for question routing — they just don't render as a quote.)

### 10.8 Voice deferred

Explicitly: no microphone permission requested. The `audio_*` columns are not in the schema. If users want voice in v2, the schema migration adds it without breaking anything.

## 11. Acceptance criteria for v1

A v1 ships when ALL of the following pass:

| # | Criterion |
|---|---|
| AC1 | User can complete the **pre-japa flow** (open app, see ≥1 cited quote + 1 tip) in under 60 seconds, end-to-end |
| AC2 | User can **capture today's rounds** with one tap or number entry; no prompt or modal fires unless user opens the app |
| AC3 | User can **complete the Saturday check-in** (both halves) end-to-end; data persists to SQLite |
| AC4 | The **pattern engine fires silent** when N < 21 (verified by automated test) |
| AC5 | The **pattern engine fires silent** when N ≥ 21 but no predictor meets thresholds (verified by automated test) |
| AC6 | The **pattern engine names a pattern** correctly when synthetic data meets all five rule conditions (verified by automated test) |
| AC7 | Every quote surfaced has a **citation** rendered alongside (verified by code review + UX review) |
| AC8 | Zero **streaks, badges, lifetime-count motivators**, or push notifications anywhere in the codebase (verified by code review) |
| AC9 | App functions when `kg-mcp` is **offline**: rounds capture still works, Saturday check-in still works (quotes show a "corpus offline" placeholder) |
| AC10 | All user data lives in **a single SQLite file** on the user's machine; no network calls outside `kg-mcp`; no telemetry |
| AC11 | The **MCP client** can successfully call `search_corpus`, `get_verse`, `find_verses`, `cross_author_chunks` against the user's running `kg-mcp` server |
| AC12 | **Smoke test** suite covers the three flows (Pre-japa, Daily capture, Saturday check-in) end-to-end |

## 12. Out-of-scope appendix (for clarity)

These are real future products and explicitly OUT of v1. Each will deserve its own Grill phase before being built.

- Multi-user / family mode (Phase 2 of the product)
- Voice input
- Mobile-native apps (iOS, Android)
- Scripture chatbot / Q&A
- Health / Ayurveda / fitness coaching
- Document storage / household memory
- Yoga coaching
- Long-distance presence channel with father
- Anything that quantifies, scores, or judges japa quality
- Notifications of any kind

## 13. Open questions for review

Before opening Phase 5 (Issues), confirm or redirect:

1. **Working name "Sadhana Setu"** — acceptable, or your own preferred name? (Other candidates: *Anudina-Saptaha*, *Krishna Smriti*, *Sankalpa*, *Hari Saranam*.)
2. **Streamlit local-web** is the right UX shell for v1 — or do you prefer a Python CLI / TUI instead?
3. **Tip library curation** is a real piece of work in Phase 6 — ~120 hand-crafted tips. Can you draft these (perhaps 5–10 per session), or do you want me to seed first drafts that you only review/edit?
4. **Ekadasi calendar source** — do you have one you trust (e.g., ISKCON BBT calendar)? I'll wire the lookup against whatever format you have.
5. **Three pre-registered predictors for pattern engine** — confirm: `prev_night_sleep_time`, `prev_day_rounds_completed`, `ekadasi_today`. Add or swap any?
6. **Citation format preference** — examples in §10.7. Preferred phrasing?
7. **Repo location** — should the capstone code live in `AgenticCourse/capstone/code/` (under this repo) or as a separate sibling repo `~/Projects/sadhana-setu`? Sibling is cleaner long-term; in-repo is easier for the course demo.

---

**Status:** Phase 4 PRD drafted 2026-06-01. Awaiting your review and answers to the 7 open questions above.
**Next phase:** Phase 5 — Issues (turn this into individual tickets with blocking relationships).
