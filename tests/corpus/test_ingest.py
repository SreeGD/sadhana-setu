"""T025 — back-ingest: reviewed-only, verified-body-only, idempotent by source_id."""
import pytest

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus.ingest import IngestError, ingest_note
from sadhana_setu.corpus.notes import Citation, KeyTeaching, NoteContent, NoteFrontMatter, NoteStatus
from sadhana_setu.corpus.review import approve


class FakeProcessor:
    def __init__(self):
        self.calls = []

    def ingest_text(self, text, source_id, metadata):
        self.calls.append({"text": text, "source_id": source_id, "metadata": metadata})
        return 3


def _write_note(cfg, lec_id="l1", reviewed=False):
    fm = NoteFrontMatter(
        lecture_id=lec_id, set_id="holy-name-seminar", transcript_path="corpus/t.md",
        sha256="0" * 64, speaker="Test", title="T", enrichment_version="v",
        enriched_at="2026-06-24T00:00:00+00:00",
    )
    content = NoteContent(
        theme_summary="theme", practical_application="apply",
        key_teachings=[KeyTeaching(point="p", timestamp="00:00:01.000")],
        unverified=["verse SB 1.1.1"],  # must NOT appear in ingested text
    )
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec_id)
    notes_mod.write(path, fm, content)
    if reviewed:
        approve(path, "Reviewer")
    return path


def test_ingest_requires_reviewed(cfg):
    path = _write_note(cfg, reviewed=False)
    with pytest.raises(IngestError):
        ingest_note(path, processor=FakeProcessor())


def test_ingest_reviewed_verified_body_only(cfg):
    path = _write_note(cfg, reviewed=True)
    proc = FakeProcessor()
    rebuilt = []
    added = ingest_note(path, processor=proc, rebuild=lambda: rebuilt.append(True))
    assert added == 3 and rebuilt == [True]
    call = proc.calls[0]
    assert call["source_id"] == "holy-name-seminar/l1"  # idempotency key
    assert "Review notes" not in call["text"]  # [UNVERIFIED] excluded
    assert "SB 1.1.1" not in call["text"]
    assert notes_mod.read_front_matter(path).ingested_at  # stamped


def test_ingest_idempotent_same_source_id(cfg):
    path = _write_note(cfg, reviewed=True)
    proc = FakeProcessor()
    ingest_note(path, processor=proc)
    ingest_note(path, processor=proc)
    assert {c["source_id"] for c in proc.calls} == {"holy-name-seminar/l1"}
