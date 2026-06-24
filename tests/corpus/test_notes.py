"""T005 — note front-matter round-trip + state machine."""
import pytest

from sadhana_setu.corpus.notes import (
    Citation,
    KeyTeaching,
    NoteContent,
    NoteError,
    NoteFrontMatter,
    NoteStatus,
    parse,
    render,
)


def _fm(**kw):
    base = dict(lecture_id="l1", set_id="holy-name-seminar", transcript_path="corpus/t/l1.md",
               sha256="0" * 64, speaker="Test", title="T", enrichment_version="v",
               enriched_at="2026-06-24T00:00:00+00:00")
    base.update(kw)
    return NoteFrontMatter(**base)


def _content():
    return NoteContent(
        theme_summary="theme",
        key_teachings=[KeyTeaching(point="chant attentively", timestamp="00:00:01.000")],
        practical_application="apply",
    )


def test_render_and_parse_round_trip():
    text = render(_fm(), _content())
    fm, body = parse(text)
    assert fm["lecture_id"] == "l1"
    assert fm["status"] == "draft"
    assert "Key teachings" in body


def test_reviewed_requires_reviewer():
    fm = _fm(status=NoteStatus.REVIEWED)
    with pytest.raises(NoteError):
        fm.validate()


def test_reviewed_with_reviewer_ok():
    fm = _fm(status=NoteStatus.REVIEWED, reviewer="x", reviewed_at="2026-06-24T00:00:00+00:00")
    fm.validate()


def test_verified_verse_renders_unverified_withheld():
    content = _content()
    content.key_teachings[0].citations = [
        Citation(kind="verse", candidate="BG 18.66", verse_ref="BG 18.66", source="BG 18.66",
                 iast="sarva-dharmān", translation="Abandon all varieties", verified=True),
    ]
    content.unverified = ["verse SB 1.2.3"]
    body = render(_fm(), content)
    assert "sarva-dharmān" in body
    assert "[UNVERIFIED]" in body and "SB 1.2.3" in body
