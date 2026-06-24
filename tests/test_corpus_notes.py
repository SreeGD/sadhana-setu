"""T017 — corpus_notes: reviewed-only enumeration; drafts excluded; parse."""
from sadhana_setu.flows import corpus_notes


def _write(path, status, lid):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nset_id: bhurijana-prabhu\nlecture_id: {lid}\nspeaker: Bhūrijana Prabhu\n"
        f"title: Talk {lid}\nstatus: {status}\n---\n\n## Theme\n\nThe Holy Name.\n",
        encoding="utf-8")


def test_lists_reviewed_only(tmp_path):
    _write(tmp_path / "bhurijana-prabhu" / "a.md", "reviewed", "a")
    _write(tmp_path / "bhurijana-prabhu" / "b.md", "draft", "b")
    notes = corpus_notes.list_reviewed_notes(tmp_path)
    assert [n.lecture_id for n in notes] == ["a"]  # draft excluded (Constitution V)
    assert notes[0].speaker == "Bhūrijana Prabhu"


def test_read_note_returns_front_matter_and_body(tmp_path):
    p = tmp_path / "s" / "x.md"
    _write(p, "reviewed", "x")
    fm, body = corpus_notes.read_note(p)
    assert fm["status"] == "reviewed" and fm["lecture_id"] == "x"
    assert "## Theme" in body and "Holy Name" in body


def test_empty_when_no_notes(tmp_path):
    assert corpus_notes.list_reviewed_notes(tmp_path) == []
