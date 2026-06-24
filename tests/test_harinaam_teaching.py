"""T015 — harinaam_teaching: prefer reviewed harinaam-note; offline/empty → None."""
from sadhana_setu.flows.harinaam_teaching import fetch_teaching


def _caller(hits):
    def call(name, args):
        assert name == "search_corpus"
        return hits
    return call


def test_prefers_harinaam_note():
    hits = [
        {"text": "some other corpus chunk", "metadata": {"kind": "book"}},
        {"text": "Hear one mantra attentively.", "metadata": {
            "kind": "harinaam-note", "speaker": "Bhūrijana Prabhu", "title": "Holy Name 01"}},
    ]
    stage = fetch_teaching("hearing", caller=_caller(hits))
    assert stage is not None
    assert stage.source_kind == "corpus"
    assert "attentively" in stage.body
    assert "Bhūrijana" in stage.citation


def test_no_harinaam_note_returns_none():
    stage = fetch_teaching("x", caller=_caller([{"text": "t", "metadata": {"kind": "book"}}]))
    assert stage is None


def test_empty_returns_none():
    assert fetch_teaching("x", caller=_caller([])) is None


def test_caller_error_returns_none():
    def boom(name, args):
        raise RuntimeError("kg-mcp down")
    assert fetch_teaching("x", caller=boom) is None


def test_top_level_kind_also_accepted():
    hits = [{"text": "teaching", "kind": "harinaam-note", "speaker": "X", "title": "Y"}]
    assert fetch_teaching("x", caller=_caller(hits)) is not None
