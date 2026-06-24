"""T008/T011/T013 — shared corpus_teaching service: review-gate, cache, stability, dedup."""
from datetime import date

from sadhana_setu.flows import corpus_teaching as ct


def _chunks(*lids):
    return [{"text": f"teaching {l}", "kind": "harinaam-note", "speaker": "Sp",
             "title": "Holy Name 01", "set_id": "s", "lecture_id": l} for l in lids]


def test_review_gate_rejects_non_harinaam():
    q = lambda theme: [{"text": "x", "kind": "book", "lecture_id": "l1"}]
    assert ct.get_for_surface("t", "pre-japa", state=ct.new_state(), querier=q) is None


def test_returns_clean_chunk_text_and_citation():
    t = ct.get_for_surface("t", "nama-tattva", state=ct.new_state(), querier=lambda th: _chunks("l1"))
    assert t and "teaching l1" in t.body and t.source_kind == "corpus"
    assert "Sp" in t.citation and "Holy Name 01" in t.citation


def test_within_day_stability():  # SC-005
    st = ct.new_state()
    q = lambda th: _chunks("l1", "l2")
    a = ct.get_for_surface("t", "nama-tattva", state=st, querier=q)
    b = ct.get_for_surface("t", "nama-tattva", state=st, querier=q)
    assert a is b  # same surface re-asks → same teaching


def test_cache_queries_once_per_theme():  # FR-012
    st = ct.new_state()
    calls = []

    def q(theme):
        calls.append(theme)
        return _chunks("l1", "l2")

    ct.get_for_surface("t", "nama-tattva", state=st, querier=q)
    ct.get_for_surface("t", "saturday", state=st, querier=q)  # same theme, different surface
    assert calls.count("t") == 1


def test_dedup_across_surfaces():  # FR-013
    st = ct.new_state()
    q = lambda th: _chunks("l1", "l2")
    a = ct.get_for_surface("t", "pre-japa", state=st, querier=q)
    b = ct.get_for_surface("t", "nama-tattva", state=st, querier=q)
    assert a.lecture_id != b.lecture_id


def test_none_when_corpus_exhausted():
    st = ct.new_state()
    q = lambda th: _chunks("l1")  # only one note
    ct.get_for_surface("t", "pre-japa", state=st, querier=q)
    assert ct.get_for_surface("t", "nama-tattva", state=st, querier=q) is None  # → curated


def test_offline_querier_error_returns_none():  # FR-004
    def boom(theme):
        raise RuntimeError("vidya-karana offline")
    assert ct.get_for_surface("t", "x", state=ct.new_state(), querier=boom) is None


def test_views_import_safe():  # T011/T013 — importing must not start Streamlit
    import importlib
    for mod in ("sadhana_setu.ui.nama_tattva_view", "sadhana_setu.ui.notes_view",
                "sadhana_setu.ui.saturday_view"):
        assert hasattr(importlib.import_module(mod), "render")
