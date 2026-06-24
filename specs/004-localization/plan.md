# Implementation Plan: Localization (te/kn/ta)

**Branch**: `004-localization` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-localization/spec.md`

## Summary

Localize Sadhana Setu's **UI strings + daily curated content** (affirmations, faith verses,
nāma-tattva, contemplations) into **Telugu, Kannada, Tamil**, English-first with per-key fallback.
Translations live in **per-locale YAML catalogs**, drafted by **Claude Code** and approved per
item by a **native-devotee reviewer** via the files (`reviewed` flag; git-diff trail). Sanskrit
verses/terms are **transliterated phonetically into the vernacular script** (sounds preserved)
via `indic-transliteration`. A new `i18n` core + `translit` module power both the Streamlit app
and the static build. Rollout is **Telugu first**, then Kannada + Tamil.

## Technical Context

**Language/Version**: Python 3.11+ / Streamlit + the static (JS) build.

**Primary Dependencies**: NEW `indic-transliteration` (Sanskrit→te/kn/ta); existing `pyyaml`,
content modules (`sadhana_setu/content/*`, `data/*.yaml`), `build_static.py`. Claude Code CLI for
drafting (reused from `002`).

**Storage**: New `data/i18n/ui/<locale>.yaml` (UI strings) and
`data/i18n/content/<locale>/<library>.yaml` (translated content, per-item `reviewed`). English
source data unchanged. Locale persisted in `st.session_state` + a small settings file.

**Testing**: `pytest`. i18n fallback + reviewed-gate, transliteration fidelity (mahā-mantra +
sample verse per script), catalog loading — all unit-testable without a browser.

**Target Platform**: Streamlit app (macOS) + GitHub Pages static build.

**Project Type**: i18n layer + content overlays + a transliteration module, extending the app.

**Performance Goals**: Catalogs loaded once and cached; no per-render cost beyond a dict lookup.

**Constraints**: English fallback (no blanks); only **reviewed** translations published
(Constitution V); Sanskrit sounds preserved by transliteration (Constitution I); Sattvic medium
(Constitution IV); static parity (FR-012).

**Scale/Scope**: 4 locales (en + te/kn/ta); UI strings + 4 daily content libraries; Telugu first.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Sanskrit transliterated (sounds preserved, verified), never garbled;
  translations are devotee-reviewed (FR-010/011). ✅
- **II. Provenance** — Citations preserved on translated content (FR-006). ✅
- **III. Attribution** — Sources kept across locales. ✅
- **IV. Sattvic Medium** — Localization adds no metrics/scoring/push. ✅
- **V. Review Gate** — Only `reviewed: true` translations are published; unreviewed → English
  (FR-004/011). ✅
- **VI. Local-First** — Catalogs on disk; transliteration is a local library; Claude Code drafting
  is local (text only). ✅
- **VII. Monorepo Conventions** — Catalogs under `data/i18n/`; code under `sadhana_setu/`. ✅
- **VIII. Reuse Vidya-Karana** — N/A for localization (no corpus retrieval); the Claude Code
  drafting reuses the `002` provider pattern. ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-localization/
├── plan.md
├── spec.md
├── research.md
├── data-model.md        # Locale, MessageCatalog, TranslatedContentItem, Transliteration (DONE)
├── quickstart.md        # validation scenarios (DONE)
├── contracts/           # i18n API, translit API, catalog file format (DONE)
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
sadhana_setu/
├── i18n.py                # locale state; t(key) [UI]; localize_content(...) [content]; English fallback + reviewed-gate
├── translit.py            # to_script(text, locale, src="iast") via indic-transliteration; IAST fallback on miss
└── ui/
    └── app.py             # language selector in the sidebar → st.session_state["locale"]

data/i18n/
├── ui/<locale>.yaml                 # UI strings: key → string (en authored; te/kn/ta drafted+reviewed)
└── content/<locale>/<library>.yaml  # affirmations/faith_verses/nama_tattva/contemplations overlays (+ reviewed)

scripts/
└── draft_translations.py  # Claude Code headless drafts → catalogs (reviewed: false)

build_static.py            # emit per-locale catalogs for the static build (FR-012)

tests/
├── test_i18n.py           # fallback, reviewed-gate, catalog load
└── test_translit.py       # mahā-mantra + verse fidelity per te/kn/ta
```

**Structure Decision**: A small runtime-agnostic `i18n` core + `translit` module + YAML catalogs
under `data/i18n/` is the single source of truth for both the Streamlit app and the static build.
Views/content call `i18n.t`/`i18n.localize_content`; Sanskrit goes through `translit.to_script`.

## Key design decisions (finalized in data-model.md / contracts/)

1. **Catalogs**: `data/i18n/ui/<locale>.yaml` (key→string) + `data/i18n/content/<locale>/<library>.yaml`
   (item-id→fields + `reviewed`). English is the source; missing/unreviewed → English fallback.
2. **i18n API**: `set_locale`/`get_locale`; `t(key)`; `localize_content(library, item_id, field,
   english)` — reviewed-gated.
3. **Transliteration**: `translit.to_script(text, locale, src="iast")`; used for verses + Sanskrit
   terms in a vernacular locale; IAST fallback on any failure. Fidelity verified by tests.
4. **Review gate**: a translation is shown only when its catalog entry has `reviewed: true`
   (Constitution V); the draft script writes `reviewed: false`.
5. **Drafting**: `scripts/draft_translations.py` runs Claude Code headless to fill the target
   catalogs; native devotee flips `reviewed: true` per item via the file.
6. **Rollout**: Telugu first (core + 4 libraries + UI, reviewed), then Kannada + Tamil reuse the
   pipeline. Static build (FR-012) consumes the same catalogs.

## Complexity Tracking

No constitution violations; no entries required.
