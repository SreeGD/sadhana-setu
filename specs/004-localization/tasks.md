---
description: "Task list for 004-localization"
---

# Tasks: Localization (Telugu, Kannada, Tamil)

**Input**: Design documents from `specs/004-localization/`
**Prerequisites**: plan.md, spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md.

**Tests**: INCLUDED — i18n fallback + reviewed-gate and **transliteration fidelity** (the Holy
Name / verses) are trust-critical (Constitution I/V). Catalog/translit logic is unit-testable.

**Organization**: By user story (US1–US3 this round; **US4 corpus-note localization is deferred**
per the clarified scope, FR-009). Rollout is **Telugu first** (FR-013).

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[USn]**: user-story label (story phases only)

## Clarification note

Spec `## Clarifications` (2026-06-24): scope = UI + daily curated content; Sanskrit transliterated
into the vernacular script; per-locale YAML catalogs (English fallback); Claude Code draft + native
file review (`reviewed` flag); Telugu first. No `[NEEDS CLARIFICATION]` open.

---

## Phase 1: Setup

- [X] T001 Add `indic-transliteration` to `pyproject.toml`; create `data/i18n/ui/` and `data/i18n/content/` dirs
- [X] T002 [P] Create `sadhana_setu/i18n.py` + `sadhana_setu/translit.py` skeletons and `tests/test_i18n.py`, `tests/test_translit.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ No user-story work begins until this phase is complete.**

- [X] T003 Implement `sadhana_setu/translit.py::to_script(text, locale, src="iast")` via `indic-transliteration`; `en` passthrough; IAST fallback on any failure (contracts/i18n.md, FR-010)
- [X] T004 [P] Test `tests/test_translit.py`: the mahā-mantra + a sample verse transliterate correctly to te/kn/ta, sounds preserved (Constitution I); failure → IAST fallback
- [X] T005 Implement `sadhana_setu/i18n.py`: `get_locale`/`set_locale` (session_state + persistence in `data/i18n/settings.yaml`), `t(key)` (UI, English fallback), `localize_content(library, id, field, english)` (reviewed-gate; drafts default `reviewed: false`), catalog load + cache (contracts/i18n.md)
- [X] T006 [P] Test `tests/test_i18n.py`: English fallback (missing key/item), reviewed-gate (unreviewed ⇒ English), catalog load (FR-002/004)

**Checkpoint**: i18n core + transliteration ready and tested.

---

## Phase 3: User Story 1 — UI in my language (P1) 🎯 MVP

**Goal**: The interface renders in the selected language with English fallback.
**Independent test**: switch to Telugu; UI labels are Telugu; untranslated keys show English; choice persists.

- [X] T007 [US1] Author `data/i18n/ui/en.yaml` (UI string keys) and replace UI literals with `i18n.t(key)` across `sadhana_setu/ui/` (`app.py`, `prejapa_view.py`, `nama_tattva_view.py`, `notes_view.py`, `saturday_view.py`, `today_view.py`, `this_week_view.py`, `history_view.py`)
- [X] T008 [US1] Add a language selector (English / తెలుగు / ಕನ್ನಡ / தமிழ்) to the sidebar in `sadhana_setu/ui/app.py` → `i18n.set_locale`
- [X] T009 [US1] Draft the Telugu UI catalog `data/i18n/ui/te.yaml` via `scripts/draft_translations.py` (`reviewed` pending native review)
- [X] T010 [P] [US1] Test UI fallback (missing `te` key ⇒ English) in `tests/test_i18n.py` (SC-001)

**Checkpoint**: the app runs in Telugu UI with English fallback.

---

## Phase 4: User Story 2 — Curated content in my language (P1)

**Goal**: The daily libraries render reviewed translations; unreviewed ⇒ English.
**Independent test**: in Telugu, reviewed affirmations/verses/nāma-tattva/contemplations render; an unreviewed item shows English.

- [X] T011 [US2] Implement `scripts/draft_translations.py`: Claude Code headless (`claude -p`) drafts UI + content into `data/i18n/{ui,content}/<locale>/` with `reviewed: false` (FR-011)
- [X] T012 [US2] Wire `i18n.localize_content` into the display of the four daily libraries (`affirmations`, `faith_verses`, `nama_tattva`, `contemplations`) in their views, preserving citations (FR-003/006)
- [X] T013 [US2] Draft Telugu content overlays `data/i18n/content/te/{affirmations,faith_verses,nama_tattva,contemplations}.yaml` (`reviewed: false`; native review pending)
- [X] T014 [P] [US2] Test reviewed-gate in `tests/test_i18n.py`: an unreviewed content item renders the English original (SC-002); a drafted entry defaults `reviewed: false`; a **reviewed item preserves its citation** (SC-004/FR-006)

**Checkpoint**: reviewed Telugu content renders; drafts withheld.

---

## Phase 5: User Story 3 — Correct script rendering (P2)

**Goal**: Sanskrit verses/terms render in the vernacular script (sounds preserved).
**Independent test**: in Telugu, verses/terms appear in Telugu script (`హరే కృష్ణ`); rare-token failure falls back to IAST.

- [X] T015 [US3] Wire `translit.to_script` into verse/Sanskrit-term rendering for vernacular locales (faith-verse IAST, nāma-tattva terms) in the relevant views/`i18n.py` helper
- [X] T016 [P] [US3] Test that verse/term rendering in a vernacular locale is transliterated (and IAST-fallback on miss) in `tests/test_translit.py`

**Checkpoint**: Sanskrit shows in the vernacular script, fidelity-tested.

---

## Phase 6: Polish & Cross-Cutting

- [X] T017 [P] Static-build parity: `build_static.py` emits `data/i18n/` catalogs + a language switch so the static app matches (FR-012)
- [X] T018 [P] Indic-script rendering: **bundle Noto Sans Telugu/Kannada/Tamil** (don't rely on system fonts) in `sadhana_setu/ui/app.py` CSS + `static/css/`; verify no tofu/correct conjuncts in app + static build (US3/FR-005)
- [ ] T019 Native-devotee review of the Telugu drafts — flip `reviewed: true` per item in `data/i18n/**/te*.yaml`, **including a Sattvic-Medium UX pass** (no metrics/scoring/push introduced; SC-005) (human step; documented in `quickstart.md`)
- [X] T020 Run `/speckit-analyze` for cross-artifact consistency before `/speckit-implement`

---

## Dependencies

- **Setup (P1)** → **Foundational (P2)** → user stories.
- **US1** (UI) is the MVP. **US2** (content) and **US3** (transliteration) build on the i18n core +
  translit from Foundational; US2 and US3 are largely independent and can run in parallel.
- **Kannada + Tamil** reuse the same pipeline after Telugu is reviewed (FR-013) — out of this task
  list's critical path; re-run T009/T013 drafting + T019 review per locale.
- `[P]` tasks within a phase touch different files and may run in parallel.

## Parallel execution examples

- Phase 2: T004 (translit test) and T006 (i18n test) in parallel after T003/T005.
- US2 (T011–T014) and US3 (T015–T016) in parallel once Foundational is done.

## Implementation strategy

- **MVP = Phases 1–3 (US1)**: i18n core + transliteration + the language switch + Telugu UI — a
  visibly localized app.
- Then **US2** (content) and **US3** (script rendering), then static parity + Kannada/Tamil.
- Stop after each phase for a working, testable increment.

---

## Phase 7: Convergence

Appended by `/speckit-converge` (2026-09-12). Gaps between the current code and spec/plan/tasks.
Existing tasks above are untouched; T013 is satisfied by the existing `.draft.yaml` files (see T029).

- [X] T021 **CRITICAL** — Restore the review gate on the pre-japa surface: `sadhana_setu/flows/prejapa_reading.py::localize_item` shows unreviewed `.draft.yaml` drafts of all four in-scope libraries via `i18n.localize_content_machine` unconditionally for any non-English locale. Gate the machine path behind an explicit, default-off opt-in (e.g. `show_machine_drafts: true` in `data/i18n/settings.yaml`, read by `i18n`), keep the `prejapa.machine_banner` whenever it is on, default to `localize_content` (reviewed-only ⇒ English) otherwise, update `tests/test_i18n.py::test_localize_content_machine_shows_drafts` to assert the default-off behaviour, and record the justified deviation in `specs/005-prejapa-transformation/plan.md` Complexity Tracking per Constitution V / FR-003 / FR-004 / US2/AC2 (contradicts)
- [X] T022 [P] Static-build parity: extend `build_static.py` to emit `static/i18n/ui/<locale>.json` and reviewed-only `static/i18n/content/<locale>/<library>.json` (same gate as `i18n.localize_content`), add a language selector + persisted choice to `static/index.html`/`static/js/app.js`, a `t(key)` helper with English fallback in `static/js/util.js` or a new `static/js/i18n.js`, and use it in `static/js/views/*.js`; set `<html lang>` from the locale per FR-012 / T017 (missing)
- [X] T023 [P] Externalize the remaining UI literals in `sadhana_setu/ui/today_view.py`, `this_week_view.py`, `saturday_view.py`, `history_view.py` (headers, captions, buttons, inputs, info/success/warning text) into `data/i18n/ui/en.yaml`, replace them with `i18n.t(key)`, and draft the new keys into `data/i18n/ui/te.draft.yaml` via `scripts/draft_translations.py --kind ui` per FR-002 / US1/AC1 / T007 (partial)
- [X] T024 [P] Bundle Indic fonts instead of the Google Fonts `@import`: add Noto Sans Telugu/Kannada/Tamil woff2 under `static/fonts/`, declare `@font-face` in both `sadhana_setu/ui/app.py` CSS and `static/css/style.css`, and fix the `font-family` list in `app.py` (the trailing `inherit` makes the declaration invalid CSS so the Indic stack never applies); verify no tofu / correct conjuncts in both runtimes per FR-005 / SC-003 / T018 / Constitution VI (partial)
- [X] T025 [P] Route the hardcoded English fallbacks in `sadhana_setu/flows/prejapa_reading.py` ("Take shelter of the Holy Name…", "Chant to hear…", "This week's sankalpa: ") and the header tagline in `sadhana_setu/ui/app.py` through `i18n.t` keys in `data/i18n/ui/en.yaml` per FR-002 (partial)
- [X] T026 [P] Preserve citations verbatim in `sadhana_setu/ui/nama_tattva_view.py`: stop passing the full English `nt.source` through `i18n.maybe_transliterate` (it renders "CC Madhya 17.133, Prabhupada's purport" as "చ్చ్ మధ్య ౧౭.౧౩౩, ప్రభుపదఽస్ పుర్పోర్త్"); transliterate only Sanskrit/IAST segments (e.g. the parenthesised verse fragment) or none, and add a test in `tests/test_i18n.py` that a citation survives localization unchanged per FR-006 / SC-004 / FR-010 (partial)
- [X] T027 Record review status for the Telugu UI catalog: `data/i18n/ui/te.yaml` is live and diverges from `te.draft.yaml` while T019 is open and the flat catalog has no `reviewed` field. Add a catalog-level status (e.g. a `_meta: {reviewed: false, reviewer: null, date: null}` key that `i18n.t` honours, falling back to English unless the T021 opt-in is on) and document it in `specs/004-localization/data-model.md` per FR-004 / T009 / T019 (partial)
- [X] T028 [P] Add `data/i18n/settings.yaml` to `.gitignore` (written on every rerun by `i18n.set_locale`; committing it would override the English default for every clone) per FR-001 / plan: storage decision (partial)
- [X] T029 [P] Document the draft → live promotion step in `specs/004-localization/quickstart.md` Scenario 4 and `data-model.md` (drafts are written to `data/i18n/content/<locale>/<library>.draft.yaml` and `ui/<locale>.draft.yaml`; the reviewer promotes approved items into `<library>.yaml` / `<locale>.yaml` with `reviewed: true`), and mark T013 `[X]` — the four in-scope overlays already exist as `.draft.yaml` with aligned ids (25/20/46/7 rows); do NOT re-run drafting, which would overwrite reviewer edits, per T013 / quickstart Scenario 4 (partial)
- [X] T030 [P] Extend `tests/test_translit.py`: Tamil mahā-mantra (`Hare Kṛṣṇa` → `ஹரே க்ருஷ்ண`-style expected output verified against `indic-transliteration`), a sample verse for kn and ta, and a monkeypatched `transliterate` that raises to prove the IAST fallback path per T004 / T016 / Constitution I (partial)
- [X] T031 [P] In `sadhana_setu/ui/nama_tattva_view.py` derive the overlay index from the picked item (`nt_mod.all_teachings().index(nt)`, or reuse `flows.prejapa_reading.localize_item`) instead of re-deriving `tm_yday % len(...)`, so a change to `pick_for_today` cannot pair a translation with the wrong teaching per FR-003 / data-model (partial)
- [X] T032 [P] Justify or remove the out-of-scope overlays `data/i18n/content/te/{daily_verses,inspirations,sankalpas,tips}.draft.yaml` and their `_CONTENT_FIELDS` entries in `scripts/draft_translations.py`: FR-009 scopes this round to affirmations, faith_verses, nama_tattva, contemplations and neither 004 nor 005 artifacts request the extra four; if kept, record the scope extension in `specs/005-prejapa-transformation/spec.md` per FR-009 (unrequested)
