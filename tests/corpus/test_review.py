"""T022 — review gate: approve flow, list_drafts, publish exclusion."""
import pytest

from sadhana_setu.corpus import notes as notes_mod
from sadhana_setu.corpus.notes import NoteContent, NoteFrontMatter, NoteStatus, KeyTeaching
from sadhana_setu.corpus.review import ReviewError, approve, is_publishable, list_drafts


def _write_draft(cfg, lec_id="l1"):
    fm = NoteFrontMatter(
        lecture_id=lec_id, set_id="holy-name-seminar",
        transcript_path="corpus/t.md", sha256="0" * 64, speaker="Test", title="T",
        enrichment_version="v", enriched_at="2026-06-24T00:00:00+00:00",
    )
    content = NoteContent(theme_summary="t", practical_application="a",
                          key_teachings=[KeyTeaching(point="p", timestamp="00:00:01.000")])
    path = notes_mod.note_path(cfg, "holy-name-seminar", lec_id)
    notes_mod.write(path, fm, content)
    return path


def test_list_drafts(cfg):
    _write_draft(cfg, "l1")
    drafts = list_drafts(cfg.notes_dir)
    assert len(drafts) == 1


def test_approve_sets_reviewed(cfg):
    path = _write_draft(cfg)
    fm = approve(path, "Bhakta Dāsa")
    assert fm.status is NoteStatus.REVIEWED
    assert fm.reviewer == "Bhakta Dāsa" and fm.reviewed_at
    assert notes_mod.read_front_matter(path).status is NoteStatus.REVIEWED


def test_approve_requires_reviewer(cfg):
    path = _write_draft(cfg)
    with pytest.raises(ReviewError):
        approve(path, "")


def test_unreviewed_not_publishable(cfg):
    path = _write_draft(cfg)
    assert not is_publishable(notes_mod.read_front_matter(path))
    approve(path, "x")
    assert is_publishable(notes_mod.read_front_matter(path))


def test_approve_idempotent(cfg):
    path = _write_draft(cfg)
    approve(path, "x")
    fm = approve(path, "y")  # already reviewed → no-op
    assert fm.reviewer == "x"
    assert list_drafts(cfg.notes_dir) == []  # no longer a draft
