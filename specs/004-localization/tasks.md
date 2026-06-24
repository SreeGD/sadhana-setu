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
- [ ] T013 [US2] Draft Telugu content overlays `data/i18n/content/te/{affirmations,faith_verses,nama_tattva,contemplations}.yaml` (`reviewed: false`; native review pending)
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

- [ ] T017 [P] Static-build parity: `build_static.py` emits `data/i18n/` catalogs + a language switch so the static app matches (FR-012)
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
