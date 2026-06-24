# Implementation Plan: Note Enrichment

**Branch**: `002-note-enrichment` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-note-enrichment/spec.md`

## Summary

Transform the verbatim transcripts produced by `001-corpus-pipeline` into structured, study-ready
**class notes** using an LLM, where every verse and cross-reference is grounded through `kg-mcp`
(never invented), each note links back to transcript timestamps, drafts pass a devotee review
gate before publish, and reviewed notes are ingested back into vidya-karana's corpus/ChromaDB so
the Sadhana Setu app can surface them.

## Technical Context

**Language/Version**: Python 3.11+ (same package + tooling as the app and 001).

**Primary Dependencies**: an LLM client (provider per FR-015 clarification); the existing MCP
client `sadhana_setu/mcp_client.py` → `kg-mcp`; `pyyaml` (front-matter); vidya-karana's ChromaDB
ingest path (reuse) for back-ingest.

**Storage**: Markdown notes under `corpus/notes/<set>/<slug>.md` with YAML front-matter; review
records embedded in front-matter or a sidecar; enrichment-version registry in config.

**Testing**: `pytest`. Grounding logic tested with a mocked `kg-mcp`; review-gate state machine
tested directly; one end-to-end test on a short fixture transcript with a stubbed LLM.

**Target Platform**: macOS / local-first. LLM may be local (Principle VI) or cloud text-only
(no audio leaves the machine) pending FR-015.

**Project Type**: CLI + library (single project), extending `sadhana_setu/corpus/`.

**Performance Goals**: Batch; bounded by LLM + KG round-trips. No latency target.

**Constraints**: KG-grounded verses only; fail-safe when `kg-mcp` offline; idempotent; review
gate before publish; speaker's words never paraphrased as quotes.

**Scale/Scope**: One note per transcript (pending FR-013), hundreds of notes over time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Verses KG-grounded; ungrounded → `[UNVERIFIED]`; speaker not
  paraphrased (FR-002, FR-003, FR-012). ✅
- **II. Provenance & Reproducibility** — Note front-matter links to transcript→audio; enrichment
  version recorded; idempotent (FR-005, FR-009). ✅
- **III. Attribution & Fair Use** — Notes credit speaker via transcript provenance; text-only. ✅
- **IV. Sattvic Medium** — Study notes; no metrics/gamification. ✅
- **V. Review Gate** — Central to this feature (US4, FR-007, FR-008). ✅
- **VI. Local-First & Offline** — LLM locality is the FR-015 decision; audio never involved here
  (works on text transcripts). ✅ (pending FR-015)
- **VII. Monorepo Conventions** — Notes under `corpus/notes/`. ✅
- **VIII. Reuse Vidya-Karana** — Grounding via existing `kg-mcp`; back-ingest via existing
  ChromaDB path (FR-002, FR-011). ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-note-enrichment/
├── plan.md
├── spec.md
├── research.md
├── data-model.md        # Phase 1 — note schema, citation model, review record (TBD)
├── quickstart.md        # Phase 1 — enrich → review → publish runbook (TBD)
├── contracts/           # Phase 1 — LLM prompt contract, note front-matter, kg-mcp usage (TBD)
└── tasks.md
```

### Source Code (repository root)

```text
sadhana_setu/
└── corpus/
    ├── enrich.py            # LLM enrichment: transcript → draft note sections
    ├── grounding.py         # kg-mcp lookups; verify citations; mark [UNVERIFIED]; fail-safe
    ├── notes.py             # note read/write, front-matter, status state machine
    ├── review.py            # review gate: approve/record reviewer + date; publish eligibility
    └── ingest.py            # back-ingest reviewed notes into vidya-karana ChromaDB → KG

corpus/
└── notes/
    └── <speaker-or-seminar>/
        └── <slug>.md        # enriched class note + provenance front-matter (status: draft|reviewed)

tests/
└── corpus/
    ├── test_grounding.py    # mocked kg-mcp: verified vs [UNVERIFIED]; offline fail-safe
    ├── test_review.py       # state machine: draft → reviewed; publish exclusion
    └── test_enrich.py       # stubbed LLM on a short fixture transcript
```

**Structure Decision**: Enrichment extends the `sadhana_setu/corpus/` sub-package from 001 and
adds a `corpus/notes/` content tree parallel to `corpus/transcripts/`. Grounding and back-ingest
go through existing vidya-karana surfaces (`mcp_client.py`, ChromaDB) per Constitution
Principle VIII.

## Key design decisions (finalized in data-model.md / contracts/)

1. **Note front-matter**: source transcript id, audio checksum (inherited), speaker, enrichment
   model + prompt version, status, reviewer, review date.
2. **Grounding contract**: the LLM proposes *candidate* citations (reference identifiers, not
   verse text); `grounding.py` resolves each via `kg-mcp` and substitutes authoritative text;
   unresolved → `[UNVERIFIED]`. The LLM never supplies final verse text.
3. **Review state machine**: `draft → reviewed` (one-way unless re-enriched, which resets to
   draft and bumps version).
4. **Fail-safe**: if `kg-mcp` is unreachable, no note is published; the run reports unverifiable.
5. **Back-ingest**: reuse vidya-karana's ChromaDB ingest entry point; key by note id for
   idempotent replace.

## Complexity Tracking

No constitution violations; no entries required.
