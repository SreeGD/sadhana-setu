# Sadhana Setu

A sastra-grounded sadhana companion for one ISKCON practitioner. Built as the capstone for the seven-phase agentic development process demonstrated in the parent course.

**Two runtimes in this repo:** a full Streamlit version (this README) and a no-server static version that deploys to GitHub Pages — see [`docs/STATIC_README.md`](docs/STATIC_README.md). The static version uses browser localStorage for the tracker + a Download/Restore JSON workflow for backup and multi-device transfer.

## Status — v0.1.5 (v1.5 code-complete, draft content awaiting review)

v1 is feature-complete. v1.5 (Option α pre-japa) lands the five-dimension daily view + Saturday Bhajan. **16 tests passing.** Awaiting human review of 5 new content libraries before v1.5 ship.

| Milestone | Tickets | State |
|---|---|---|
| M0 Foundations | T-001 → T-005 | ✓ |
| M1 Content seed (draft library) | T-006 → T-009 | ✓ (user review pending before ship) |
| M2 Pre-japa flow | T-010 → T-013 | ✓ |
| M3 Daily capture | T-014 | ✓ |
| M4 Saturday check-in | T-015 → T-018 | ✓ |
| M5 Pattern engine | T-019 → T-023 | ✓ |
| M6 Sacred constraints + polish | T-024 → T-026 | ✓ |
| M7 Tests + docs | T-027 → T-029 | ✓ |

## Quick start

```bash
cd capstone/code
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env       # paths default to the local kg-mcp install
make migrate               # creates ./data/sadhana_setu.db with 6 tables
make smoke                 # confirms kg-mcp reachable (takes ~4s — snapshot load)
make test                  # runs all 10 tests
make run                   # opens http://localhost:8501
```

Stop Streamlit later with `lsof -ti :8501 | xargs kill`.

## What v1.5 does

A typed local-first companion for an ISKCON-initiated householder. **Weekly-primary, daily-minimal.**

- **Pre-japa** (daily, under 75 seconds reading). Five sections, all citation-bearing, daily-rotating:
  1. **Affirmation** — sankalpa declaration rooted in sastra
  2. **Faith verse** — Name-promise verse (kg-mcp enriches with full Sanskrit + IAST + translation when available; falls back to curated summary)
  3. **Inspiration** — micro-pastime (2–4 sentences from SB / CC / acarya biographies)
  4. **Practical tip** — from the v1.5 expanded library (~62 tips; includes anartha-nivṛtti, yugala-nāma, ten-offenses-aware, body, time-of-day, mode-based)
  5. **Nama-Tattva** — 20-second teaching from Prabhupada's purports, Hari-nama-cintamani, Bhajana-rahasya, Padma Purana, Siksastakam
  6. **Bhajan of the Week** — Saturday only, ISO-week rotation, 52 bhajans target
- **Today** (daily, on demand): one-tap rounds capture + optional one-line hearing note. The agent never asks; the user records when ready.
- **Saturday check-in** (the primary ritual): a 10-minute typed form in two halves.
  - **Observe**: 7-day glance + 2–3 rotating sastra-rooted questions + at most one honest pattern observation.
  - **Set**: tone, mood (bhava), practices, tools needed, priorities for the coming week.
- **Pattern engine**: silent unless N ≥ 21 captured days AND the rule passes (|ρ| ≥ 0.35 AND BF ≥ 3, FDR-corrected, stable in recent 14-day window). When silent, it says so explicitly.

## What v1 does NOT do (by design)

Each of these is a real future product; bundling them now would dilute v1.

- Multi-user / family mode (Phase 2 of the product)
- Voice input (deferred to v2; typed only in v1)
- Theological Q&A chatbot
- Health / Ayurveda tracking
- Document storage / household memory
- Push notifications of any kind
- Streaks, badges, lifetime-count motivators, gamification

See `SATTVIC_AUDIT.md` for the verification.

## Architecture

```
   Streamlit UI ──► domain layer ──► SQLite (state, single file)
   (sidebar nav)         │
                         └────────► MCP client ─stdio─► kg-mcp ──► ChromaDB + NetworkX KG
                                                       (vidya-karana-kg, on this machine)
```

- **Streamlit UI** — `sadhana_setu/ui/` — presentation only, calls into the domain layer.
- **Domain layer** — `sadhana_setu/flows/` (pre-japa, today, saturday) — pure logic + DB calls.
- **Patterns** — `sadhana_setu/patterns/` — predictor registry, assemble, stats (Pearson + BF + BH-FDR), engine (5-condition rule), audit log.
- **Content** — `sadhana_setu/content/` — YAML-backed tip + question libraries.
- **DB** — `sadhana_setu/db/` — SQLite schema + `migrate()` + connection helper.
- **Calendar** — `sadhana_setu/calendar.py` — ekadasi lookup (placeholder JSON; needs Vaisnava calendar replacement before v1 ship).
- **Guards** — `sadhana_setu/guards.py` — protected-hours window check.
- **MCP client** — `sadhana_setu/mcp_client.py` — async wrapper + sync helpers + `parse_response`.

## The seven-phase artifacts

| Phase | Output |
|---|---|
| 1 Grill | `../01_grill.md` |
| 2 Research | `../02_research.md` |
| 3 Prototype | (skipped — Phase 2 closed sharp enough) |
| 4 PRD | `../04_prd.md` |
| 5 Issues | `../05_issues.md` |
| 6 Implement | this directory + `SATTVIC_AUDIT.md` |
| 7 Review | `../07_qa_plan.md` (next) |

## Sacred constraints (load-bearing)

- No screen interaction during japa.
- No notifications between 3:30–9:30 AM (sadhana arc) or 8:30–10:30 PM (office).
- No streaks, badges, lifetime-count motivators, gamification.
- Every sastra quote rendered carries a citation.
- All user data stays on this machine.
- No fabricated slokas; theological content comes from the user-reviewed library or `kg-mcp`.

## Pending before v1.5 ship

User-review checkpoints — read each library, edit/delete freely, change `status: draft` → `status: approved`:

1. `data/tips.yaml` (~62)
2. `data/weekly_questions.yaml` (~39)
3. `data/affirmations.yaml` (25) — v1.5
4. `data/inspirations.yaml` (18) — v1.5
5. `data/faith_verses.yaml` (20) — v1.5
6. `data/nama_tattva.yaml` (22) — v1.5
7. `data/bhajans.yaml` (12) — v1.5 — expand toward 52 for full annual cycle

Other:

- `data/ekadasi.json` — already replaced with Drik Panchang's 2026–2030 ISKCON list (123 entries) ✓
- kg-mcp snapshot is ~42 days old — consider `kg rebuild` in vidya-karana-kg sometime

## License

This is teaching material, not a product. Use freely.
