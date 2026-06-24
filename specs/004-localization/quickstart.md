# Quickstart: Localization (te/kn/ta)

Validation guide for `004`. Contracts + data model in [`contracts/`](./contracts/) and
[`data-model.md`](./data-model.md).

> Status: **specified + planned, not yet implemented.** Rollout is Telugu first.

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

```bash
python scripts/draft_translations.py --locale te --library affirmations   # writes reviewed: false
make run   # in Telugu: affirmations still show ENGLISH (drafts withheld)
# native devotee edits data/i18n/content/te/affirmations.yaml, sets reviewed: true
make run   # now the reviewed Telugu affirmations render
```

**Expect**: nothing translated is shown until `reviewed: true`.

## Scenario 5 — Static build parity (FR-012)

```bash
python build_static.py
```

**Expect**: the static build carries the per-locale catalogs; the static app offers the same
language switch and renders the reviewed Telugu content.

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 fully usable in te (English fallback) | 1, 2 |
| SC-002 100% reviewed translations only | 2, 4 |
| SC-003 correct script rendering | 3 |
| SC-004 citations preserved | 2 |
| SC-005 zero sattvic violations | 1–3 (UX review) |
