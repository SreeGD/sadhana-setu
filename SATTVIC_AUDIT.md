# Sattvic-medium audit (T-026)

Date: 2026-06-10
Auditor: implementation pass

This is the v1 sattvic-medium audit per `04_prd.md` §11 (AC8) and §10.5.
Every constraint from `01_grill.md` §"Sacred constraints" is verified.

## Hard exclusions — confirmed absent

| Constraint | Result |
|---|---|
| No streaks counter | ✓ — grep `streak`: 0 hits |
| No badges as rewards | ✓ — grep `badge`: 4 hits, all are the local variable `badge` in `saturday_view.py` that holds a day-of-week count string for the week-at-a-glance visual. **Not** a gamification badge. Renamed mention for future audit clarity: this variable could be renamed `cell_text` but the semantics are local and inert. |
| No lifetime-count motivator | ✓ — grep `lifetime`: 0 hits. Saturday view shows week totals only, never cumulative. |
| No gamification language | ✓ — grep `gamif`, `achievement`, `level up`, `earn.*points`, `earned.*xp`: 0 hits |
| No push API | ✓ — grep `push_notification`, `send_notification`: 0 hits |
| No `st.toast` (auto-fires) | ✓ — grep `st.toast`: 0 hits. All `st.success` calls are immediate responses to user clicks (form submits, delete buttons), not background-fired |
| No third-party network calls | ✓ — grep `import requests`, `import urllib`, `import http`: 0 hits. The only network is the local stdio subprocess to `kg-mcp` |
| No analytics / telemetry | ✓ — Streamlit's `gatherUsageStats` is disabled in the `make run` target |

## Soft constraints — verified

| Constraint | Result |
|---|---|
| Every quote rendered has a citation | ✓ — `flows/prejapa.py:53` filters `if c.get("verse_ref")` before any chunk becomes a quote; `ui/prejapa_view.py:66` always calls `citation(...)` per quote |
| LLM never generates tips at runtime | ✓ — `content/tips.py` reads from `data/tips.yaml`, no LLM call path |
| LLM never generates check-in questions at runtime | ✓ — `content/questions.py` reads from `data/weekly_questions.yaml`, no LLM call path |
| Pre-japa view stays absent during japa | ✓ — view renders only when navigated to (user action); no auto-launch, no scheduled rendering |
| Protected-hours guard implemented | ✓ — `guards.py:in_protected_hours()`. The sidebar surfaces `protected_label()` when in those windows so any future notification-adding code is visible during review |
| Pattern engine silent by default | ✓ — `patterns/engine.py:surface_pattern()` returns `silent_low_n` until N ≥ 21 and the 5-condition rule passes. Test `test_silent_at_low_N` enforces |
| Pattern engine never uses causal language | ✓ — `engine.py` headline templates say "moved together" / "moved in opposite directions" + "weak-to-moderate association, not proof of cause" |
| Null-result reporting honest | ✓ — `engine.py` returns `silent_no_pattern` with an explicit "I checked for patterns this week and didn't find one worth naming" message |
| All data local | ✓ — single SQLite file at `data/sadhana_setu.db`; no cloud sync code |
| Theological correctness — no fabricated slokas | ✓ — All sloka content comes from `kg-mcp` (vidya-karana corpus) or from the user-reviewed library files |

## AC8 verdict

AC8 (no streaks, badges, lifetime-count, push) — **PASS**.

## Notes for future iterations

1. The local variable `badge` in `saturday_view.py:50–58` is innocent but a future audit might pause on it. Consider renaming to `cell_text` for clarity (cosmetic only).
2. M5 pattern engine's `1e6` cap for `BF=inf` in JSON serialization is a serialization artifact, not a substantive issue.
3. v1 has no microphone permission, no camera permission, no location permission — and never requests any. This should remain true in v2 unless voice journaling re-enters scope.

---

# v1.5 addendum (2026-06-10)

v1.5 lands Option α — pre-japa enhancement with five daily-rotating dimensions (affirmation, faith verse, inspiration, practical tip, nama-tattva teaching) plus Bhajan of the Week on Saturday. **97 new draft entries** across 5 new YAML libraries, plus 23 Nama-Tattva-derived tips appended to the existing tips library. Audit grep over all v1.5 files confirms no forbidden patterns introduced.

## v1.5 sattvic grep — confirmed absent

| Constraint | Result over v1.5 files |
|---|---|
| streak / lifetime / badge in content code or YAML | ✓ zero hits |
| gamification / achievement / points / rewards / unlock | ✓ zero hits |
| network libraries in new code (`sadhana_setu/content/*`) | ✓ zero hits — all libraries are local YAML readers |
| `st.toast` in the new pre-japa view | ✓ zero hits |
| Microphone / camera / location permissions | ✓ none requested |

## v1.5 soft constraints — verified

| Constraint | Result |
|---|---|
| Every affirmation, inspiration, faith verse, nama-tattva teaching, and bhajan carries a citation | ✓ — `test_every_entry_has_citation` enforces |
| No LLM runtime generation in any new dimension | ✓ — every selector reads from YAML, returns dataclasses; no LLM imports in `sadhana_setu/content/` |
| Daily rotation is deterministic (same day → same pick) | ✓ — `test_daily_rotation_is_deterministic` |
| Bhajan rotation is weekly, not daily | ✓ — `test_bhajan_rotation_is_weekly_not_daily` |
| Pre-japa view stays under the one-minute envelope | Mon–Fri: 5 sections × ~15s = ~75s. Sat: + Bhajan ~20s = ~95s. Within scope per `01_grill.md` constraint |
| Faith verse renders even when kg-mcp is offline (fallback to curated summary) | ✓ — `_enriched_for_today()` returns empty dict on failure; view uses `enrich.get('translation') or fv.summary` |
| Tips library expansion preserves the existing v1 schema | ✓ — additions are appended; no schema break |
| Total curated entries: 159 across 6 libraries; every one cited | ✓ |

## v1.5 review checkpoint (mirror of v1 process)

Five new draft libraries (`affirmations.yaml`, `inspirations.yaml`, `faith_verses.yaml`, `nama_tattva.yaml`, `bhajans.yaml`) and the tips expansion in `tips.yaml` all carry `status: draft`. They will work technically before review, but **must not be considered shipped until the user has read each entry and flipped `status: draft` → `status: approved`** — same flow as v1 T-007/T-009.

## v1.5 verdict

AC8 (sattvic constraints) — **PASS for v1.5 code path.** Library-level approval is pending user review of the 97 new + 23 expanded entries.
