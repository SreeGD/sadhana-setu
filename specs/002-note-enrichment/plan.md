# Implementation Plan: Note Enrichment

**Branch**: `002-note-enrichment` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-note-enrichment/spec.md`

## Summary

Transform the verbatim transcripts produced by `001-corpus-pipeline` into structured, study-ready
**class notes**, one per transcript, using **Claude Code headless** (`claude -p`) — every verse
and cross-reference grounded through `kg-mcp` (never invented), each note linking back to
transcript timestamps. Suspected mishearings are flagged inline (annotate-only). A **Streamlit
review UI** is the devotee gate; **approving a note auto-ingests it** into vidya-karana's
ChromaDB (via `CorpusProcessor.ingest_text`) and triggers a KG rebuild so the app can surface it.

## Technical Context

**Language/Version**: Python 3.11+ (same package + tooling as the app and 001).

**Primary Dependencies**: **Claude Code CLI** (`claude -p --output-format json`) behind a thin
provider interface (not the Anthropic API); the existing MCP client
`sadhana_setu/mcp_client.py::call_tool_sync` → `kg-mcp`; vidya-karana's
`agents/corpus_processor.py::CorpusProcessor.ingest_text` for back-ingest; `streamlit` (review
UI, already a dep); `pyyaml`.

**Storage**: Markdown notes under `corpus/notes/<set>/<id>.md` with YAML front-matter (status +
review record inline); enrichment-version pinned in config.

**Testing**: `pytest`. Grounding tested with a mocked `call_tool_sync`; review state machine
tested directly; enrichment tested with a stubbed `claude -p` provider on a fixture transcript;
back-ingest tested with a mocked `CorpusProcessor`.

**Target Platform**: macOS / local-first. Enrichment runs via the local Claude Code CLI on text
transcripts; no audio involved (Principle VI honored).

**Project Type**: CLI + library + a small Streamlit review page, extending `sadhana_setu/corpus/`.

**Performance Goals**: Batch; bounded by `claude -p` + KG round-trips. No latency target.

**Constraints**: KG-grounded verses only; fail-safe when `kg-mcp` offline; idempotent; review
gate before publish (Streamlit UI); speaker's words never paraphrased as quotes.

**Scale/Scope**: One note per transcript (FR-013), hundreds of notes over time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Tattva Fidelity** — Verses KG-grounded; ungrounded → `[UNVERIFIED]`; speaker not
  paraphrased (FR-002, FR-003, FR-012). ✅
- **II. Provenance & Reproducibility** — Note front-matter links to transcript→audio; enrichment
  version recorded; idempotent (FR-005, FR-009). ✅
- **III. Attribution & Fair Use** — Notes credit speaker via transcript provenance; text-only. ✅
- **IV. Sattvic Medium** — Study notes; no metrics/gamification. ✅
- **V. Review Gate** — Central to this feature (US4, FR-007, FR-008). ✅
- **VI. Local-First & Offline** — Enrichment runs via the local Claude Code CLI on text
  transcripts; no audio involved (FR-015). ✅
- **VII. Monorepo Conventions** — Notes under `corpus/notes/`. ✅
- **VIII. Reuse Vidya-Karana** — Grounding via existing `kg-mcp` (`call_tool_sync`); back-ingest
  via existing `CorpusProcessor.ingest_text` (FR-002, FR-011). ✅

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-note-enrichment/
├── plan.md
├── spec.md
├── research.md
├── data-model.md        # Phase 1 — note schema, citation model, review record (DONE)
├── quickstart.md        # Phase 1 — enrich → review → ingest runbook (DONE)
├── contracts/           # Phase 1 — enrichment-output schema, note front-matter, grounding, ingest (DONE)
└── tasks.md             # Phase 2 — /speckit-tasks output (drafted; regenerate)
```

### Source Code (repository root)

```text
sadhana_setu/
└── corpus/
    ├── llm.py              # provider interface; ClaudeCodeProvider wraps `claude -p --output-format json`
    ├── enrich.py           # transcript → draft note (calls provider, parses enrichment JSON)
    ├── grounding.py        # kg-mcp lookups via call_tool_sync; verify citations; [UNVERIFIED]; fail-safe
    ├── notes.py            # note read/write, front-matter, status state machine
    ├── review.py           # approval logic: draft → reviewed (+ reviewer/date); publish eligibility
    └── ingest.py           # back-ingest via CorpusProcessor.ingest_text + KG rebuild trigger

sadhana_setu/ui/
    └── review_view.py      # Streamlit review UI: list drafts, show note, approve → ingest

corpus/
└── notes/
    └── <speaker-or-seminar>/
        └── <id>.md         # enriched class note + provenance front-matter (status: draft|reviewed)

tests/
└── corpus/
    ├── test_grounding.py   # mocked call_tool_sync: verified vs [UNVERIFIED]; offline fail-safe
    ├── test_review.py      # state machine: draft → reviewed; publish exclusion
    ├── test_enrich.py      # stubbed claude -p provider on a fixture transcript (golden file)
    └── test_ingest.py      # mocked CorpusProcessor: idempotent replace by source_id
```

**Structure Decision**: Enrichment extends the `sadhana_setu/corpus/` sub-package from 001 and
adds a `corpus/notes/` content tree parallel to `corpus/transcripts/`. Grounding and back-ingest
go through existing vidya-karana surfaces (`mcp_client.py`, ChromaDB) per Constitution
Principle VIII.

## Key design decisions (finalized in data-model.md / contracts/)

1. **Enrichment engine**: `llm.py` exposes a `Provider` interface; `ClaudeCodeProvider` shells out
   to `claude -p --output-format json` with the prompt contract and parses the result. A local
   model can implement the same interface. No Anthropic API key.
2. **Enrichment output contract**: the model returns one JSON object (theme, key_teachings with
   timestamps + `candidate_verse_refs`, glossary, practical_application, `candidate_cross_refs`,
   `sic_flags`). It supplies *reference identifiers only* — never final verse text
   (`contracts/enrichment-output.schema.json`).
3. **Grounding contract**: `grounding.py` resolves each `candidate_verse_ref` via
   `call_tool_sync("get_verse", {"verse_ref": …})` and substitutes the returned `iast`/
   `translation`; cross-refs via `search_corpus`/`cross_author_chunks`; unresolved → `[UNVERIFIED]`
   (`contracts/grounding.md`).
4. **Review state machine**: `draft → reviewed` (one-way unless re-enriched, which resets to draft
   and bumps the enrichment version). Approval happens in the Streamlit UI.
5. **Fail-safe**: if `kg_status()` fails or the transport errors, no verses are emitted as
   verified; the note is marked unverifiable and withheld (FR-010).
6. **Back-ingest on approval**: `ingest.py` calls `CorpusProcessor.ingest_text(text,
   source_id=note_id, metadata=…)` (idempotent replace by `source_id`) then triggers a KG rebuild
   (`contracts/ingest.md`).

## Complexity Tracking

No constitution violations; no entries required.
