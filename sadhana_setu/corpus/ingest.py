"""Back-ingest reviewed notes into vidya-karana's ChromaDB → KG (US5, FR-011).

Reuses ``vidya-karana/agents/corpus_processor.py::CorpusProcessor.ingest_text`` (Constitution
Principle VIII) — idempotent replace keyed by the note id. Only the *verified body* is ingested
(``[UNVERIFIED]`` / ``[sic?]`` aids are review-only, not corpus truth). See ``contracts/ingest.md``.
"""
from __future__ import annotations

from pathlib import Path

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus import review as review_mod
from sadhana_setu.corpus.notes import NoteFrontMatter, parse


class IngestError(RuntimeError):
    pass


def _default_processor():  # pragma: no cover - requires vidya-karana checkout
    from agents.corpus_processor import CorpusProcessor

    return CorpusProcessor()


def ingest_note(path: Path, *, processor=None, rebuild=None) -> int:
    """Ingest a reviewed note's verified body into ChromaDB; return new-chunk count.

    ``processor`` and ``rebuild`` are injectable for tests. Raises ``IngestError`` if the note is
    not reviewed (review gate, SC-003).
    """
    text = path.read_text(encoding="utf-8")
    fm_dict, body = parse(text)
    fm = NoteFrontMatter.from_dict(fm_dict)
    if not review_mod.is_publishable(fm):
        raise IngestError(f"{fm.lecture_id}: only reviewed notes may be ingested")

    proc = processor or _default_processor()
    source_id = f"{fm.set_id}/{fm.lecture_id}"  # idempotency key (replace, not duplicate)
    metadata = {
        "speaker": fm.speaker, "set_id": fm.set_id, "lecture_id": fm.lecture_id,
        "title": fm.title, "sha256": fm.sha256, "kind": "harinaam-note",
    }
    added = proc.ingest_text(_verified_body(body), source_id=source_id, metadata=metadata)

    if rebuild is not None:
        rebuild()  # trigger KG rebuild (else nightly cron picks it up)

    fm.ingested_at = notes_mod.now_iso()
    review_mod._rewrite_front_matter(path, fm, body)
    return added


def _verified_body(body: str) -> str:
    """Drop the '## Review notes (not published)' section before ingest."""
    marker = "## Review notes"
    idx = body.find(marker)
    return body[:idx].rstrip() + "\n" if idx != -1 else body
