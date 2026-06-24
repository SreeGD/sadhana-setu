# Phase 0 Research: Localization (te/kn/ta)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Requirements-level questions were resolved in the spec's `## Clarifications`. This records the
engineering decisions (Decision / Rationale / Alternatives).

## R1 — Transliteration engine (FR-010) — the tattva-sensitive piece

**Decision**: Use **`indic-transliteration`** (the `sanscript` module). It transliterates between
IAST / Devanāgarī and Telugu / Kannada / Tamil scripts, pure-Python, pip-installable. A thin
wrapper `sadhana_setu/translit.py::to_script(text, locale, *, src="iast")` exposes
`iast → te/kn/ta`. Pin the version.

**Rationale**: Mature, widely used in Indic-text projects; deterministic phoneme-preserving
transliteration. **Tattva safety (Constitution I)**: transliteration preserves the exact Sanskrit
**sounds** — e.g. `Hare Kṛṣṇa` → `హరే కృష్ణ` (te) / `ಹರೇ ಕೃಷ್ಣ` (kn) / `ஹரே க்ருஷ்ண` (ta) — so the
Holy Name's vibration is unchanged. A plan task MUST verify the mahā-mantra + a sample verse
round-trip correctly per script; on any failure for a rare token, **fall back to IAST**.

**Alternatives**: Aksharamukha (heavier/optional service); hand-mapping (rejected — error-prone).

## R2 — i18n core (FR-002/008)

**Decision**: `sadhana_setu/i18n.py` holds the current locale (default `en`, persisted in
`st.session_state["locale"]`) and:
- `t(key, **kw)` → UI string for the locale from `data/i18n/ui/<locale>.yaml`, **English fallback**
  per key (FR-002).
- `localize_content(library, item_id, field, english)` → the **reviewed** translated value from
  `data/i18n/content/<locale>/<library>.yaml`, else the English original (FR-003).
Catalogs are plain YAML (FR-008), loaded once and cached.

**Rationale**: Matches the existing `content/*.yaml` convention; trivial in Streamlit and the
static build; English fallback guarantees no blank strings.

## R3 — Content-translation overlay structure (FR-003/004)

**Decision**: Per-locale, per-library overlay files
`data/i18n/content/<locale>/<library>.yaml` keyed by the item's id/index, each entry carrying the
translated field(s) **plus** `reviewed: true|false`. `localize_content` returns the translated
value only when `reviewed: true`; unreviewed entries fall through to English (Constitution V).
English source data (`data/*.yaml`) is unchanged.

**Rationale**: Keeps source English data intact; per-item review status; reviewer edits a small
YAML and flips `reviewed: true`; git diff is the trail (FR-011).

## R4 — Language selector + persistence (FR-001)

**Decision**: A selector in the `app.py` sidebar (`English / తెలుగు / ಕನ್ನಡ / தமிழ்`) sets
`st.session_state["locale"]`. For multi-session persistence, also write a small JSON
(`~/.sadhana_setu/locale` or the existing settings store). The static build mirrors via
`localStorage` reading the same catalogs (R6).

## R5 — Machine-draft + review workflow (FR-011)

**Decision**: A maintainer script (`scripts/draft_translations.py`) runs **Claude Code headless**
(`claude -p`, reusing the `002` provider pattern) to draft each English string/content item into
the target-locale catalog with `reviewed: false`. A native-devotee reviewer edits the YAML and
sets `reviewed: true` per item; the change is reviewed via git diff. No new UI this round.

**Rationale**: Reuses the Claude Code headless path; lightweight for short strings; the review
gate is enforced by the `reviewed` flag in `localize_content`/`t`.

## R6 — Static-build parity (FR-012)

**Decision**: `build_static.py` emits the per-locale catalogs alongside the static content so the
JS app reads the **same** `data/i18n/` catalogs (and pre-transliterated Sanskrit). The static
language switch uses `localStorage`. The data layer is shared; only the runtime wiring differs.

**Rationale**: One source of translations for both runtimes; avoids divergence.

## R7 — Telugu-first rollout (FR-013)

**Decision**: Build the i18n core + transliteration + catalog structure + review workflow and
populate **Telugu** end-to-end first (UI + the four daily libraries), validated by a native Telugu
reviewer. Kannada and Tamil then reuse the identical pipeline (new locale dir + drafts + review).

## New dependency

`indic-transliteration` (pinned) added to `pyproject.toml`.

## Clarification status

All spec `[NEEDS CLARIFICATION]` resolved (Session 2026-06-24). No open research items; the one
risk to verify at build time is transliteration fidelity of the Holy Name + verses (R1).
