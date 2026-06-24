# Feature Specification: Localization (Telugu, Kannada, Tamil)

**Feature Branch**: `004-localization`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description (roadmap G4): "Make Sadhana Setu available in Telugu, Kannada and
Tamil languages." Decided earlier: machine draft + native-devotee review.

## Context

Sadhana Setu is currently English-first (UI strings + curated content libraries: affirmations,
faith verses, nāma-tattva, inspirations, tips, contemplations, weekly questions/stories). The
audience is ISKCON devotees, many of whom are native Telugu / Kannada / Tamil speakers. This
feature makes the app usable in those three languages.

Per the locked decision, translation is **machine-draft + native-devotee review** — an LLM/MT
produces a first draft, and a native-speaker devotee reviews it for accuracy and tattva fidelity
before publish (Constitution Principle V applies to translations just as to enriched notes).
Sanskrit verses and IAST are a special case: they are not "translated" away — the question is
whether to add a vernacular gloss alongside.

## Clarifications

### Session 2026-06-24

- Q: Scope for this round? → A: **UI strings + the daily curated content** (affirmations, faith verses, nāma-tattva, contemplations); weekly stories and corpus notes are deferred.
- Q: Sanskrit verses/terms in a vernacular locale? → A: **Transliterate them phonetically into the vernacular script** (Telugu/Kannada/Tamil) — the exact Sanskrit sounds are preserved (tattva-safe), via a transliteration engine.
- Q: i18n mechanism? → A: **Per-locale YAML/JSON message catalogs** (`en`/`te`/`kn`/`ta`): key → string with English fallback, matching the existing `content/*.yaml` convention.
- Q: Drafting + review tooling? → A: **Claude Code drafts translations into the catalog files** (marked unreviewed); a native-devotee reviewer approves per item via the files (git diff is the review trail).
- Q: Rollout across the three languages? → A: **Telugu first**, end-to-end, then replicate the established pipeline for Kannada and Tamil.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the app interface in my language (Priority: P1)

A devotee selects Telugu, Kannada, or Tamil and the app's **interface** (labels, buttons,
section headings, prompts) renders in that language, with a persistent language choice.

**Why this priority**: Interface language is the entry point — without it, the app is inaccessible
to a non-English reader regardless of content. It is the smallest, highest-leverage slice.

**Independent Test**: Switch language; confirm UI strings render in the chosen language and the
choice persists across sessions; English remains available.

**Acceptance Scenarios**:

1. **Given** the language is set to Telugu/Kannada/Tamil, **When** any view renders, **Then** its
   UI strings appear in that language.
2. **Given** a language is selected, **When** the app is reopened, **Then** the choice persists.
3. **Given** a string has no translation yet, **When** a view renders, **Then** it falls back to
   English (no missing/blank label).

---

### User Story 2 - Read the curated content in my language (Priority: P1)

The curated content libraries (affirmations, faith-verse summaries, nāma-tattva teachings,
and contemplations — **the four daily libraries in scope this round**, FR-009) are available in
the chosen language — **machine-drafted then native-devotee-reviewed** before publish.

**Why this priority**: The content *is* the app's spiritual value; localized UI over English
content is half the experience. Content carries tattva, so the review gate is essential here.

**Independent Test**: In a chosen language, confirm reviewed translated content renders; confirm
an unreviewed translation is never shown (English shown instead).

**Acceptance Scenarios**:

1. **Given** reviewed translations exist for a library, **When** content is shown in that
   language, **Then** the reviewed translation renders with the same citation.
2. **Given** a translation is only machine-drafted (unreviewed), **When** content is shown,
   **Then** it is withheld and the English original is shown (Constitution V).

---

### User Story 3 - Correct script rendering (Priority: P2)

Telugu, Kannada, and Tamil text (and Sanskrit Devanāgarī / IAST shown alongside) renders correctly
— right fonts, no tofu/boxes, readable sizing — in both the Streamlit app and the static build.

**Why this priority**: Indic scripts have specific font/shaping needs; broken glyphs make the
localization unusable even when the strings exist. It supports US1/US2.

**Independent Test**: Render representative Telugu/Kannada/Tamil + Devanāgarī + IAST on the app and
the static build; confirm no missing glyphs and correct conjuncts.

**Acceptance Scenarios**:

1. **Given** localized content, **When** rendered, **Then** all script glyphs display correctly
   (no tofu), including conjuncts.
2. **Given** a verse, **When** rendered, **Then** Devanāgarī + IAST + any vernacular gloss all
   display correctly together.

---

### User Story 4 - Localized corpus notes (Priority: P3)

The reviewed Hari-Nāma corpus notes (`002`) can be offered in the chosen language — machine-drafted
+ devotee-reviewed — for devotees who study in their mother tongue.

**Why this priority**: High value but large scope (many long notes) and depends on the corpus
maturing; best deferred until UI + curated content are localized.

**Independent Test**: For one reviewed note, confirm a reviewed translation can be shown in the
chosen language with attribution; unreviewed translations withheld.

**Acceptance Scenarios**:

1. **Given** a reviewed translated note, **When** opened in that language, **Then** it renders with
   attribution.
2. **Given** only a machine draft, **When** opened, **Then** the English note is shown instead.

---

### Edge Cases

- A string/content item is partially translated → fall back to English per-item (never a blank).
- Sanskrit verses/terms → resolved (FR-010): **transliterated phonetically into the vernacular
  script** (sounds preserved); surrounding prose is translated. A transliteration miss for a rare
  term falls back to IAST.
- Right-to-left / complex shaping: N/A for te/kn/ta (all LTR), but conjunct shaping must be correct.
- The static (GitHub Pages) build must carry the same localization, not just the Streamlit app.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST support a **language selection** (English, Telugu, Kannada, Tamil) that
  **persists** across sessions, defaulting to English.
- **FR-002**: All **UI strings** MUST be externalized and render in the selected language, with
  **per-string English fallback** when a translation is missing.
- **FR-003**: The **curated content libraries** MUST be translatable per language, surfaced only
  when a **native-devotee-reviewed** translation exists (Constitution V); otherwise English shows.
- **FR-004**: Translations MUST follow **machine-draft → native-devotee review**; review status is
  recorded per item, and unreviewed translations are never published.
- **FR-005**: Indic scripts (te/kn/ta) and Sanskrit (Devanāgarī/IAST) MUST **render correctly** in
  both the Streamlit app and the static build (fonts bundled/available; no tofu).
- **FR-006**: Citations/provenance MUST be **preserved** on translated content.
- **FR-007**: Localization MUST honor all **Sattvic-Medium** constraints (Constitution IV).
- **FR-008**: Translations MUST be stored as **per-locale YAML/JSON message catalogs**
  (`en`/`te`/`kn`/`ta`): key → string with **English fallback**, matching the existing
  `content/*.yaml` convention, loadable in both the Streamlit app and the static build.
- **FR-009**: This round's scope is **UI strings + the daily curated content** (affirmations,
  faith verses, nāma-tattva, contemplations). Weekly stories and corpus notes are **deferred**.
- **FR-010**: Sanskrit verses and terms MUST be **transliterated phonetically into the vernacular
  script** (Telugu/Kannada/Tamil) via a transliteration engine — preserving the exact Sanskrit
  sounds (tattva-safe). (IAST/Devanāgarī MAY also be retained; the surrounding prose is translated.)
- **FR-011**: Translations MUST be produced as a **Claude Code machine draft written into the
  catalog files** (marked unreviewed), then **approved per item by a native-devotee reviewer via
  the files** (a `reviewed` status per entry; git diff is the review trail). Unreviewed entries
  are never published (Constitution V).
- **FR-012**: The **static build** MUST carry the same localization as the Streamlit app.
- **FR-013**: Rollout MUST proceed **Telugu first, end-to-end**, then replicate the established
  catalog + transliteration + review pipeline for Kannada and Tamil.

### Key Entities *(include if feature involves data)*

- **Locale**: a supported language (`en`, `te`, `kn`, `ta`) and the user's persisted selection.
- **Message Catalog**: UI strings keyed by id, per locale, with English fallback.
- **Translated Content Item**: a curated content row (or corpus note) in a target language, with a
  translation **status** (`draft`/`reviewed`), reviewer, and preserved citation.
- **Translation Review Record**: native-devotee reviewer + date + decision per translated item.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A devotee can run the app fully in Telugu, Kannada, or Tamil for the in-scope
  surfaces, with English fallback for any untranslated item — no blank/missing strings.
- **SC-002**: 100% of published translated content is **native-devotee-reviewed**; zero unreviewed
  translations are shown.
- **SC-003**: All te/kn/ta + Devanāgarī/IAST glyphs render correctly (no tofu) in both runtimes.
- **SC-004**: Citations/provenance are preserved on 100% of translated content.
- **SC-005**: A UX + tattva review confirms zero Sattvic-Medium violations introduced by
  localization.

## Assumptions

- Translation is **machine-draft + native-devotee review** (locked decision); the review gate is
  Constitution Principle V, mirroring `002`.
- Targets **Telugu, Kannada, Tamil** (+ English). Hindi/Bengali/others are out of scope this round.
- Sanskrit verses/terms are **transliterated into the vernacular script** (sounds preserved),
  not discarded (FR-010); a transliteration engine (e.g. indic-transliteration / Aksharamukha) is
  introduced.
- Translations are stored as **per-locale YAML/JSON catalogs** (FR-008), drafted by **Claude
  Code** and **reviewed per item by a native devotee via the files** (FR-011).
- Rollout is **Telugu first**, then Kannada + Tamil (FR-013).
- Reuses existing content structures (`sadhana_setu/content/*` + `data/*.yaml`) and the static
  build path; this is localization of the existing app, not a new app.
- Corpus-note localization (US4) likely depends on `003-app-enrichment` surfacing being in place.
