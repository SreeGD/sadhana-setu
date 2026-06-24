"""T015 — harinaam_teaching: kind-filtered live query; only harinaam-note; degrade to None."""
from sadhana_setu.flows.harinaam_teaching import fetch_teaching


def _querier(chunks):
    def q(theme):
        return chunks
    return q


def test_accepts_harinaam_note():
    chunks = [
        {"text": "some other corpus chunk", "kind": "book"},
        {"text": "Hear one mantra attentively.", "kind": "harinaam-note",
         "speaker": "Bhūrijana Prabhu", "title": "Holy Name 01"},
    ]
    stage = fetch_teaching("hearing", querier=_querier(chunks))
    assert stage is not None
    assert stage.source_kind == "corpus"
    assert "attentively" in stage.body
    assert "Bhūrijana" in stage.citation


def test_rejects_non_harinaam_note():
    # The review gate: a non-reviewed chunk must never surface (Constitution V).
    stage = fetch_teaching("x", querier=_querier([{"text": "t", "kind": "book"}]))
    assert stage is None


def test_empty_returns_none():
    assert fetch_teaching("x", querier=_querier([])) is None


def test_querier_error_returns_none():
    def boom(theme):
        raise RuntimeError("vidya-karana venv missing")
    assert fetch_teaching("x", querier=boom) is None


def test_nested_metadata_kind_accepted():
    chunks = [{"text": "teaching", "metadata": {"kind": "harinaam-note", "speaker": "X",
                                                "title": "Y"}}]
    assert fetch_teaching("x", querier=_querier(chunks)) is not None
