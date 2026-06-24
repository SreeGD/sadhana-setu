# Quickstart: Pre-japa Reading for Transformation

Validation guide for the redesigned pre-japa reading (spec 005). Contracts + data model are in
[`contracts/`](./contracts/) and [`data-model.md`](./data-model.md).

> Status: **specified + planned, not yet implemented**.

## Prerequisites

- The repo venv (`pip install -e ".[dev]"`); the existing app runs (`make run`).
- Optional for the live "deepen" stage: a running **`kg-mcp`** with reviewed `002`
  `harinaam-note` content ingested. Without it, the reading falls back to curated content.

## Scenario 1 — The arc renders (US1)

```bash
make run    # open Pre-japa
```

**Expect**: the reading is one arc — **Orient** (disposition + glory of the Name) →
**Deepen** (a Hari-Nāma teaching) → **Apply** (one optional contemplative prompt) → **Enter japa**
(a resolve pointing into chanting). It reads in ~60–75s and ends with the "screen silent during
japa" footer.

## Scenario 2 — Grounded corpus teaching (US2)

With `kg-mcp` running and `harinaam-note` content ingested:

**Expect**: the Deepen stage shows a reviewed teaching with a citation (speaker + lecture). It is
stable within the day and varies across days.

## Scenario 3 — Graceful fallback (US2, SC-004)

```bash
# with kg-mcp stopped
make run
```

**Expect**: the reading still renders fully; the Deepen stage uses a curated nāma-tattva teaching;
a quiet inline "corpus offline — curated reading" note appears. No error, no empty layout.

## Scenario 4 — Contemplative micro-practice (US3)

**Expect**: exactly one optional prompt (a line to sit with / a single prayer / a holding
question). Engaging or skipping it records nothing and is not scored.

## Scenario 5 — Optional sankalpa echo (FR-012)

With a recent Saturday check-in present:

**Expect**: the Enter stage shows a gentle one-line echo of the week's tone/bhava; the resolve
itself is drawn from the day's reading (not generated from the check-in).

## Scenario 6 — Design-review rubric (FR-011)

Walk a rendered reading (and a few days' variations) against
[`contracts/review-rubric.md`](./contracts/review-rubric.md).

**Expect**: every rubric item checks — arc present, within budget, graceful fallback, **zero
sattvic-medium violations**, 100% cited/grounded content. No runtime measurement of the devotee.

## Acceptance ↔ scenario map

| Spec criterion | Scenario |
|---|---|
| SC-001 ~60–75s budget | 1 |
| SC-002 100% cited/grounded | 2, 6 |
| SC-003 zero sattvic violations | 6 |
| SC-004 renders with fallback | 3 |
| SC-005 ends pointing into japa | 1, 5 |
