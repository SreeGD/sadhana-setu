# Phase 7 — QA Plan

> Output of Phase 7 (Review): a manual QA plan for the human (the user) to validate v1 against the PRD and the Phase 1 sacred constraints. Run each section in order. Tick the boxes. Anything that fails → file as a Phase 6 bugfix and re-run.

## Pre-conditions

- Phase 6 closed: `make test` shows **10/10 passing**
- `vidya-karana-kg` snapshot present (any age — kg-mcp will warn but still serve)
- ~30 minutes for the full pass (~10 if you skip the library review)

---

## Section A — Setup & smoke (≈5 min)

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| A1 | `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"` | No errors; `pip list` shows `sadhana-setu`, `streamlit`, `mcp`, `scipy`, `pingouin` | ☐ |
| A2 | `cp .env.example .env`; open `.env`; confirm `KG_MCP_BIN` points at a real `kg-mcp` binary on disk | `ls -l $KG_MCP_BIN` succeeds | ☐ |
| A3 | `make migrate` | Output: `Migration complete: ./data/sadhana_setu.db` | ☐ |
| A4 | `sqlite3 ./data/sadhana_setu.db ".tables"` | Shows all 6 tables: `rounds, hearing_notes, weekly_checkins, tips, weekly_questions, patterns_log` | ☐ |
| A5 | `make smoke` (takes ~4s) | Last line: `[smoke] OK` | ☐ |
| A6 | `make test` | `10 passed` | ☐ |
| A7 | `make run` | Streamlit opens at http://localhost:8501 without a Python traceback | ☐ |

---

## Section B — Pre-japa flow (AC1, AC7, AC9) (≈5 min)

Navigate to **Pre-japa** in the sidebar.

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| B1 | Page renders within 5s on first load | Header "Before japa", caption "Today's value: *<a value>*" | ☐ |
| B2 | At least one Sanskrit quote appears | Devanagari OR IAST text visible | ☐ |
| B3 | Each quote has a citation line | Format: `— <verse_ref>, <author>'s purport` (e.g., `— BRS 1.2.230, Rupa Goswami's purport`) | ☐ |
| B4 | One tip is shown with a source | "💡 *<tip>*" + `— <source>` | ☐ |
| B5 | Closing caption present | *"Close this window when ready. The agent is silent during japa."* | ☐ |
| B6 | Refresh the page | Loads instantly (session cache hit) | ☐ |
| B7 | **kg-mcp offline test** — edit `.env`: set `KG_MCP_BIN=/nonexistent`; restart Streamlit; reload Pre-japa | Yellow warning: *"Corpus offline — quotes not available today."* Tip still shown. No Python traceback. | ☐ |
| B8 | Restore the correct `KG_MCP_BIN` and restart | Pre-japa works again | ☐ |

---

## Section C — Today (daily capture) flow (AC2, AC10) (≈3 min)

Navigate to **Today**.

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| C1 | Header shows today's day/date | Format: "Today — Tuesday, June 10" | ☐ |
| C2 | Number input defaults to 16 | Slider/spinner present | ☐ |
| C3 | Enter `16`, click Save | Green "Saved: 16 rounds…" | ☐ |
| C4 | Refresh page | Number still 16; caption shows "Last saved: …" | ☐ |
| C5 | Change to `12`, click Save | Green "Saved: 12 rounds…"; caption updates | ☐ |
| C6 | `sqlite3 ./data/sadhana_setu.db "SELECT COUNT(*) FROM rounds WHERE date='YYYY-MM-DD'"` (today's date) | Returns `1` (idempotent — one row, not two) | ☐ |
| C7 | Add a hearing note: source "BG", line "test note 1", click Save note | Green "Note saved"; note appears in "Today's notes" list | ☐ |
| C8 | Add second note: source "Other" → type "HG Radhe Syam class" → line "test note 2" | Both notes visible | ☐ |
| C9 | Click the ✕ next to one note | Note removed from list | ☐ |
| C10 | **Network sniff** — `lsof -i -P | grep streamlit` while the app runs | No outbound connections except the local `kg-mcp` subprocess | ☐ |

---

## Section D — Saturday check-in flow (AC3, AC10) (≈10 min)

Navigate to **Saturday Check-in**.

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| D1 | Header: "Saturday Check-in"; caption: "Week of … — …, 2026" | Format correct | ☐ |
| D2 | If today ≠ Saturday: info banner about previewing | Banner present | ☐ |
| D3 | **Half 1 — Observe**: 7 day cells, one per day of the week past | Each cell shows day-of-week + date + count (or `—` if missing) | ☐ |
| D4 | Caption below cells: "X/7 days at vow (≥16); Y rounds total; Z hearing notes" | All three numbers match what you saved | ☐ |
| D5 | **Pattern this week** section shows "Too early to surface patterns. Observed days so far: N" | Until ≥21 captured days, silent is correct | ☐ |
| D6 | **Bhava suggestions** expander opens and shows sastra-rooted bhavas | Includes "tṛṇād api sunīcena", "dāsya", "kṛtajñatā", etc. | ☐ |
| D7 | "This week's questions" shows 2–3 numbered questions | Mix of sastra-routed (e.g., "Read Siksastakam verse 3…") and direct | ☐ |
| D8 | Fill in answers, Tone, Mood, Practices (one per line), Tools, Priorities | All fields accept text | ☐ |
| D9 | Click "Save check-in" | Green "Check-in saved for week ending …" | ☐ |
| D10 | Refresh page | All your inputs are pre-filled; "Last saved: …" caption present | ☐ |
| D11 | Edit Tone, click Save again | New value persists; only one row per week | ☐ |
| D12 | `sqlite3 ./data/sadhana_setu.db "SELECT COUNT(*) FROM weekly_checkins WHERE week_start=...";` | Returns `1` | ☐ |
| D13 | `sqlite3 ./data/sadhana_setu.db "SELECT * FROM patterns_log;"` | One audit row exists for this Saturday | ☐ |

---

## Section E — Pattern engine (AC4, AC5, AC6) (≈5 min)

These are partly verified by `pytest` and partly need synthetic data.

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| E1 | `make test` shows `tests/test_patterns.py::test_silent_at_low_N PASSED` | AC4 ✓ | ☐ |
| E2 | `make test` shows `tests/test_patterns.py::test_silent_when_no_variance PASSED` | AC5 ✓ | ☐ |
| E3 | `make test` shows `tests/test_patterns.py::test_fires_on_synthetic_positive PASSED` | AC6 ✓ | ☐ |
| E4 | Optional — synthetic data manual test: open a Python REPL, seed 30 days of alternating 16/10, navigate to Saturday view | Pattern section shows the honest weak-association message (ρ, "not proof of cause") | ☐ |

---

## Section F — Sacred constraints (AC8) (≈3 min)

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| F1 | Read `SATTVIC_AUDIT.md` | AC8 PASS at the bottom | ☐ |
| F2 | `grep -rn 'streak\|gamif\|achievement\|push_notification\|st.toast' sadhana_setu/` | Zero hits | ☐ |
| F3 | Sidebar between 3:30–9:30 AM or 8:30–10:30 PM | Shows "🕉 *Protected hours — sadhana/office*" caption | ☐ |
| F4 | Open the app between 3:30–9:30 AM | No popup, modal, or toast fires automatically | ☐ |
| F5 | Source dependency audit: `pip list | grep -iE 'analytics|telemetry|firebase'` | Empty | ☐ |

---

## Section G — User-review checkpoints (the two human approvals) (≈10–20 min)

These can be deferred but must be done before v1 ships to the user himself.

| # | Check | Pass criterion | ☐ |
|---|---|---|---|
| G1 | Open `capstone/code/data/tips.yaml` | All 39 tips read; reviewer name + date filled in | ☐ |
| G2 | Edit / delete tips you disagree with | Free-form edit | ☐ |
| G3 | Change top of `tips.yaml`: `status: draft` → `status: approved` | Status committed | ☐ |
| G4 | Open `capstone/code/data/weekly_questions.yaml` | All 39 questions read; reviewer name + date filled in | ☐ |
| G5 | Edit / delete questions you disagree with | Free-form edit | ☐ |
| G6 | Change top of `weekly_questions.yaml`: `status: draft` → `status: approved` | Status committed | ☐ |
| G7 | Replace `data/ekadasi.json` with real Vaisnava calendar data | Dates verified against `vaishnavacalendar.com` or trusted local ISKCON source | ☐ |

---

## Section H — Final sign-off

| Item | Status | Notes |
|---|---|---|
| All 6 AC sections complete | ☐ | |
| Library review (G1–G6) complete | ☐ | |
| Ekadasi calendar replaced (G7) | ☐ | |
| Any tracked issues from this QA | ☐ | List below |

### Issues found during QA

| # | Section | Description | Severity | Status |
|---|---|---|---|---|
|   |         |             |          |        |

### Sign-off

- Reviewed by: ______________________
- Date: ______________________
- Verdict: ☐ ship  ☐ ship with caveats  ☐ block (issues above)

---

**Status:** Phase 7 QA plan delivered 2026-06-10. v1 awaits user verification.
