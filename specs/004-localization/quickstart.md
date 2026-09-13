# Quickstart: Localization (te/kn/ta)

Validation guide for `004`. Contracts + data model in [`contracts/`](./contracts/) and
[`data-model.md`](./data-model.md).

> Status: **implemented (Telugu machinery + drafts); native review pending (T019).** Rollout is
> Telugu first.

## Prerequisites

- `pip install -e ".[dev]"` (adds `indic-transliteration`); the app runs (`make run`).
- Claude Code CLI on PATH for drafting (`scripts/draft_translations.py`).

## Scenario 1 — Switch the UI language (US1)

`make run` → sidebar language selector → **తెలుగు**.

**Expect**: UI labels render in Telugu; any untranslated key shows English (no blanks); the choice
persists across reopen.

## Scenario 2 — Localized daily content (US2)

In Telugu, open Pre-japa / Nama-Tattva.

**Expect**: reviewed Telugu affirmations / faith verses / nāma-tattva / contemplations render with
preserved citations; an unreviewed item shows the English original (never an unreviewed draft).

## Scenario 3 — Sanskrit transliteration (US3, FR-010)

**Expect**: verses + Sanskrit terms appear in **Telugu script** (e.g. `హరే కృష్ణ`), sounds
preserved; a transliteration failure for a rare token falls back to IAST. Run `make test` →
`test_translit` confirms the mahā-mantra + a sample verse transliterate correctly.

## Scenario 4 — Review gate (FR-011, Constitution V)

Drafts and live catalogs are **separate files**. The drafting script writes machine drafts to
`*.draft.yaml`, which the app never reads on the reviewed path; the reviewer *promotes* approved
entries into the live catalog.

```bash
python scripts/draft_translations.py --locale te --kind content --library affirmations
#   → data/i18n/content/te/affirmations.draft.yaml   (every row: reviewed: false)
make run   # in Telugu: affirmations still show ENGLISH (drafts withheld)
# Native devotee reviews the draft, then promotes approved rows into the LIVE catalog:
#   data/i18n/content/te/affirmations.yaml   — copy the row, set reviewed: true
make run   # now the reviewed Telugu affirmations render
```

UI strings work the same way at catalog level: `python scripts/draft_translations.py --locale te
--kind ui` writes `data/i18n/ui/te.draft.yaml`; the reviewer promotes keys into
`data/i18n/ui/te.yaml` and flips its `_meta.reviewed: true` (with `reviewer` + `date`). Until then
the live catalog is withheld and the UI falls back to English.

**Expect**: nothing translated is shown until `reviewed: true`.

**Practitioner opt-in (T021)** — to preview *unreviewed* machine drafts locally (UI + content), set
`show_machine_drafts: true` in `data/i18n/settings.yaml` (git-ignored, default off). The pre-japa
view then shows a "machine-translated — pending devotee review" banner. The static build ignores
this flag: a published site only ever carries reviewed translations.

## Scenario 5 — Static build parity (FR-012)

```bash
python build_static.py
```

**Expect**: `static/i18n/ui/<locale>.json` + `static/i18n/content/<locale>/<library>.json` are
emitted (reviewed-only; an unreviewed UI catalog becomes `{}` ⇒ English fallback); the static app
offers the same language switch (top bar), persists it in `localStorage`, and renders the reviewed
Telugu content. Noto Sans Telugu/Kannada/Tamil are bundled under `static/fonts/` (no network).

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 fully usable in te (English fallback) | 1, 2 |
| SC-002 100% reviewed translations only | 2, 4 |
| SC-003 correct script rendering | 3 |
| SC-004 citations preserved | 2 |
| SC-005 zero sattvic violations | 1–3 (UX review) |
