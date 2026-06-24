# Feature Specification: Note Enrichment

**Feature Branch**: `002-note-enrichment`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Enrich class notes from the transcriptions. After transcription,
enhance notes with references using LLM. Make sure enriched notes are checked into github."

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

A qualified devotee reviews a draft note for tattva accuracy. On approval, the note's status
flips to `reviewed` and it becomes part of the published corpus. Until then it is visibly marked
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

Once reviewed, an enriched note is ingested back into vidya-karana's corpus/ChromaDB so it
becomes queryable through the same `kg-mcp` path the Sadhana Setu app already uses — closing the
loop so future app features (003) can surface these teachings.

**Why this priority**: This makes the enriched corpus reachable by the app, but it depends on
everything above and on the app-enrichment work (003), so it is the last slice here.

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
- A transcript has misheard Sanskrit (whisper error) → enrichment notes the ambiguity rather
  than "correcting" the speaker; reviewer resolves. [NEEDS CLARIFICATION: should enrichment
  propose transcript corrections back to 001, or only annotate?]
- `kg-mcp` offline → fail safe (US2 scenario 3).
- A teaching spans multiple transcripts → [NEEDS CLARIFICATION: are notes strictly per-transcript,
  or can a note aggregate a multi-part series / full seminar?]
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
  thus to the original audio), the enrichment model + prompt version, and a `status`
  (`draft`/`reviewed`).
- **FR-006**: Notes MUST be committed to GitHub as Markdown, diff-friendly, and clearly marked
  `draft` until reviewed.
- **FR-007**: The system MUST enforce a **review gate**: only `reviewed` notes are eligible for
  publish/back-ingest (Constitution Principle V).
- **FR-008**: The review action MUST record reviewer identity and date.
- **FR-009**: Enrichment MUST be **idempotent**: re-running does not silently overwrite an
  existing note; regeneration is explicit (`--regenerate`) and bumps the enrichment version.
- **FR-010**: When `kg-mcp` is unavailable, enrichment MUST **fail safe** — it must not emit
  ungrounded verses as verified.
- **FR-011**: Reviewed notes MUST be ingestible **back into vidya-karana's corpus/ChromaDB → KG**,
  idempotently (replace, not duplicate).
- **FR-012**: The note MUST preserve the speaker's meaning; enrichment annotates and references
  but never paraphrases the speaker as if quoting them (Constitution Principle I).
- **FR-013**: The system MUST define note **granularity**. [NEEDS CLARIFICATION: one note per
  transcript, or aggregate notes per lecture-series / full seminar?]
- **FR-014**: The system MUST define handling of **transcript errors** found during enrichment.
  [NEEDS CLARIFICATION: annotate-only, or propose corrections upstream to 001?]
- **FR-015**: The enrichment LLM choice and prompt contract MUST be specified.
  [NEEDS CLARIFICATION: which LLM — local model for Principle VI, or a cloud model (text-only,
  no audio) is acceptable for the enrichment step?]

### Key Entities *(include if feature involves data)*

- **Class Note**: The enriched study note for a transcript. Attributes: sections (per FR-001),
  provenance front-matter, enrichment version, status, reviewer, review date.
- **Citation / Reference**: A grounded link to a verse or corpus passage, carrying the
  `kg-mcp`-sourced text/IAST/translation and a resolvable identifier. May be `verified` or
  `[UNVERIFIED]`.
- **Review Record**: reviewer identity, date, decision, optional notes — attached to a Class Note.
- **Enrichment Version**: model + prompt-version pair, recorded so notes are reproducible and
  re-review is traceable.

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
- LLM output is a **draft**; nothing publishes without devotee review (Principle V).
- Notes are committed as text (Markdown) — diff-friendly and reviewable in pull requests.
- Back-ingest reuses vidya-karana's existing ChromaDB ingest path rather than a new store.
