# Feature Specification: Note Enrichment

**Feature Branch**: `002-note-enrichment`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Enrich class notes from the transcriptions. After transcription,
enhance notes with references using LLM. Make sure enriched notes are checked into github."

## Clarifications

### Session 2026-06-24

- Q: Which LLM performs enrichment, and must it be local? → A: **Claude Code in headless mode** (`claude -p`), behind a thin provider interface — NOT the Anthropic API. Reuses the existing Claude Code subscription (no separate API key/billing); operates on text transcripts only (VI honored). A local model remains swappable via the interface.
- Q: Note granularity — per-transcript or aggregated? → A: **One note per transcript** (1:1 with `001`); clean provenance, incremental processing. Series-level synthesis is out of scope for this round.
- Q: How are whisper transcript errors handled during enrichment? → A: **Annotate-only** — flag suspected mishearings inline (e.g. `[sic?: …]`); the `001` transcript stays verbatim/immutable; the reviewer resolves.
- Q: How does a devotee approve a draft note? → A: A **lightweight Streamlit review UI** (approve flips `draft → reviewed`, stamping reviewer + date).
- Q: When do reviewed notes flow into the KG? → A: **Automatically on approval** — approving in the review UI immediately ingests the note into ChromaDB and triggers a KG rebuild.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate enriched class notes from a transcript (Priority: P1)

A devotee maintaining the corpus runs enrichment over a committed verbatim transcript (output
of `001-corpus-pipeline`). An LLM produces a structured **class note**: a theme summary, the
key teachings in order, the verses cited (with IAST and full citation), practical application
to japa / Hari-Nāma, a glossary of Sanskrit terms, and back-links to the transcript timestamps
where each point appears. The note is written as a Markdown file with provenance front-matter,
marked **draft / unreviewed**, and committed.

**Why this priority**: The enriched class note is the deliverable that makes the corpus usable
for study and for feeding the app. It is the core of this feature.

**Independent Test**: Run enrichment on one transcript; confirm a structured note appears with
every required section, that each cited verse carries IAST + citation, and that every section
links back to transcript timestamps and is marked unreviewed.

**Acceptance Scenarios**:

1. **Given** a committed verbatim transcript, **When** enrichment runs, **Then** a structured
   class note with all required sections is produced and committed as `status: draft`.
2. **Given** the produced note, **When** a reviewer opens it, **Then** each key point links to a
   transcript timestamp and each verse shows IAST + citation.
3. **Given** a transcript already enriched, **When** enrichment runs again, **Then** the existing
   note is not silently overwritten (idempotent unless `--regenerate`).

---

### User Story 2 - Ground every verse and reference in the knowledge graph (Priority: P1)

When the enrichment LLM cites a verse or adds a cross-reference, the system retrieves it through
`kg-mcp` (`get_verse`, `find_verses`, `search_corpus`, `cross_author_chunks`) against
vidya-karana, rather than trusting the model's memory. Verses that cannot be grounded in the KG
are flagged `[UNVERIFIED]` rather than published as fact.

**Why this priority**: This is how Constitution Principle I (no fabricated verses) is enforced.
Without grounding, the enriched notes would be untrustworthy — defeating the purpose.

**Independent Test**: Force the LLM to cite a verse; confirm the published citation text matches
what `kg-mcp` returns for that reference, and that an unresolvable citation is marked
`[UNVERIFIED]` and excluded from the clean note body.

**Acceptance Scenarios**:

1. **Given** the LLM proposes a verse citation, **When** the note is assembled, **Then** the
   verse text/IAST/translation come from `kg-mcp`, not the LLM.
2. **Given** a proposed citation with no KG match, **When** the note is assembled, **Then** it is
   marked `[UNVERIFIED]` and withheld from the verified body.
3. **Given** `kg-mcp` is offline, **When** enrichment runs, **Then** it fails safe: it does not
   emit unverified verses as if verified (it pauses or marks the whole note unverifiable).

---

### User Story 3 - Add cross-references to Prabhupāda's books and related teachings (Priority: P2)

Beyond verses recited in the lecture, the enrichment adds **cross-references**: links to
relevant purports in Śrīla Prabhupāda's books and to related teachings elsewhere in the corpus
(e.g., another speaker on the same point), each grounded via `kg-mcp` /
`cross_author_chunks`. These deepen study without altering the speaker's words.

**Why this priority**: The user explicitly asked to "enhance notes with references using LLM."
This is the enrichment value-add, layered on the core note (US1) once grounding (US2) exists.

**Independent Test**: For a note on a specific teaching, confirm at least one grounded
cross-reference to a Prabhupāda purport or a related corpus passage, each with a resolvable
citation.

**Acceptance Scenarios**:

1. **Given** a key teaching in a note, **When** enrichment runs, **Then** grounded
   cross-references to related purports/teachings are added with citations.
2. **Given** a cross-reference, **When** a reviewer checks it, **Then** the citation resolves via
   `kg-mcp` to real corpus content.

---

### User Story 4 - Review gate before publish (Priority: P1)

A qualified devotee reviews a draft note for tattva accuracy in a **lightweight Streamlit review
UI**. On approval, the note's status flips to `reviewed`, it becomes part of the published
corpus, and it is **immediately ingested into the KG** (US5). Until then it is visibly marked
draft and excluded from anything the app surfaces.

**Why this priority**: Constitution Principle V is non-negotiable — LLM output is a draft until a
devotee approves it. The gate must exist for any of this content to be trustworthy.

**Independent Test**: Take a draft note, record a devotee approval, confirm status becomes
`reviewed` and the note is now eligible for publish/back-ingest; confirm an unreviewed note is
excluded.

**Acceptance Scenarios**:

1. **Given** a draft note, **When** a devotee approves it, **Then** its status becomes
   `reviewed` with reviewer + date recorded.
2. **Given** an unreviewed note, **When** the publish/back-ingest step runs, **Then** the note is
   excluded.

---

### User Story 5 - Ingest reviewed notes back into the knowledge graph (Priority: P3)

**Approving a note in the review UI (US4) automatically** ingests it into vidya-karana's
corpus/ChromaDB and triggers a KG rebuild, so it becomes queryable through the same `kg-mcp` path
the Sadhana Setu app already uses — closing the loop so future app features (003) can surface
these teachings.

**Why this priority**: This makes the enriched corpus reachable by the app. It is wired to the
approval action (US4) but its retrieval guarantee is validated last.

**Independent Test**: Ingest one reviewed note; confirm `kg-mcp` (`search_corpus`) can retrieve a
passage from it afterward.

**Acceptance Scenarios**:

1. **Given** a reviewed note, **When** back-ingest runs, **Then** its content is added to
   vidya-karana's corpus/ChromaDB and retrievable via `kg-mcp`.
2. **Given** an updated/re-reviewed note, **When** back-ingest runs again, **Then** the prior
   ingested version is replaced, not duplicated (idempotent).

---

### Edge Cases

- The LLM hallucinates a verse not present in the KG → flagged `[UNVERIFIED]`, withheld (US2).
- A transcript has misheard Sanskrit (whisper error) → enrichment flags the ambiguity inline
  (`[sic?: …]`) and the reviewer resolves it; the `001` transcript is never edited (FR-014).
- `kg-mcp` offline → fail safe (US2 scenario 3).
- A teaching spans multiple transcripts → each transcript still gets its own note (one note per
  transcript, FR-013); a series-level synthesis is out of scope this round.
- Note must be regenerated after the model or prompt changes → versioning of enrichment so old
  reviewed notes are not silently invalidated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a structured **class note** per transcript with these
  sections: theme summary, key teachings (ordered), verses cited (IAST + citation), practical
  application to japa/Hari-Nāma, glossary, and timestamp back-links.
- **FR-002**: Every verse and reference in a published note MUST be **retrieved through `kg-mcp`**
  (`get_verse`/`find_verses`/`search_corpus`/`cross_author_chunks`), not produced from LLM memory.
- **FR-003**: Any citation that cannot be grounded in the KG MUST be marked `[UNVERIFIED]` and
  excluded from the verified note body.
- **FR-004**: The system MUST add **cross-references** to relevant Prabhupāda purports and related
  corpus teachings, each grounded and cited.
- **FR-005**: Each note MUST carry provenance front-matter linking to its source transcript (and
  thus to the original audio), the enrichment engine (Claude Code) + prompt version, and a
  `status` (`draft`/`reviewed`).
- **FR-006**: Notes MUST be committed to GitHub as Markdown, diff-friendly, and clearly marked
  `draft` until reviewed.
- **FR-007**: The system MUST enforce a **review gate** via a lightweight **Streamlit review UI**:
  only `reviewed` notes are eligible for publish/back-ingest (Constitution Principle V).
- **FR-008**: The review action (approving in the UI) MUST record reviewer identity and date.
- **FR-009**: Enrichment MUST be **idempotent**: re-running does not silently overwrite an
  existing note; regeneration is explicit (`--regenerate`) and bumps the enrichment version.
- **FR-010**: When `kg-mcp` is unavailable, enrichment MUST **fail safe** — it must not emit
  ungrounded verses as verified.
- **FR-011**: Approving a note in the review UI MUST **automatically ingest it back into
  vidya-karana's corpus/ChromaDB and trigger a KG rebuild**, idempotently (replace, not
  duplicate), so the Sadhana Setu app can surface it.
- **FR-012**: The note MUST preserve the speaker's meaning; enrichment annotates and references
  but never paraphrases the speaker as if quoting them (Constitution Principle I).
- **FR-013**: Notes MUST be generated at **one-note-per-transcript** granularity (1:1 with the
  `001` transcript). Series/seminar-level synthesis is out of scope for this round.
- **FR-014**: On a suspected transcript error (misheard Sanskrit), enrichment MUST
  **annotate-only** — flag the ambiguity inline (e.g. `[sic?: …]`) without altering the `001`
  transcript (which stays verbatim per Constitution I); the reviewer resolves it.
- **FR-015**: Enrichment MUST run via **Claude Code in headless mode** (`claude -p`), invoked
  behind a thin provider interface (not the Anthropic API). The prompt contract makes the model
  propose *candidate* references only; KG grounding (FR-002) supplies final verse text. A local
  model may be substituted through the same interface.

### Key Entities *(include if feature involves data)*

- **Class Note**: The enriched study note for a transcript. Attributes: sections (per FR-001),
  provenance front-matter, enrichment version, status, reviewer, review date.
- **Citation / Reference**: A grounded link to a verse or corpus passage, carrying the
  `kg-mcp`-sourced text/IAST/translation and a resolvable identifier. May be `verified` or
  `[UNVERIFIED]`.
- **Review Record**: reviewer identity, date, decision, optional notes — captured via the
  Streamlit review UI and attached to a Class Note.
- **Enrichment Version**: engine (Claude Code) + prompt-version pair, recorded so notes are
  reproducible and re-review is traceable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of verses in published (reviewed) notes resolve via `kg-mcp` to matching
  source text — zero ungrounded verses in verified bodies.
- **SC-002**: Every published note links every key teaching to at least one transcript timestamp.
- **SC-003**: No note reaches published/back-ingested state without a recorded devotee approval
  (review gate holds 100% of the time).
- **SC-004**: Re-running enrichment over an already-enriched corpus produces no changes to
  reviewed notes (idempotent; clean `git status`).
- **SC-005**: A reviewed note, once back-ingested, is retrievable via `kg-mcp` `search_corpus`.

## Assumptions

- Input is the committed verbatim transcripts from `001-corpus-pipeline`; this feature does not
  fetch or transcribe.
- Grounding uses the **existing `kg-mcp`** already wired at `sadhana_setu/mcp_client.py`
  (Constitution Principle VIII).
- Verse/Sanskrit content is **KG-sourced, never LLM-invented** (Principle I).
- Enrichment runs via **Claude Code headless** (`claude -p`) behind a provider interface — not the
  Anthropic API (FR-015); its output is a **draft**; nothing publishes without devotee review
  (Principle V).
- Notes are one-per-transcript Markdown (FR-013) — diff-friendly and reviewable in pull requests.
- Review happens in a **lightweight Streamlit UI**; approving auto-ingests the note into
  vidya-karana's existing ChromaDB path and triggers a KG rebuild (FR-007/008/011).
