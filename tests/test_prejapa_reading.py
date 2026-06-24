"""T006/T010/T016/T019 — pre-japa arc assembly: stages, grounding, fallback, echo, daily-stable."""
from datetime import date

from sadhana_setu.flows.prejapa_reading import build_reading

FIXED = date(2026, 6, 24)


def _no_corpus(theme):
    return []  # no reviewed harinaam-note ⇒ curated fallback


def _corpus_hit(theme):
    return [{"text": "Hear one Hare Kṛṣṇa mantra attentively.", "kind": "harinaam-note",
             "speaker": "Bhūrijana Prabhu", "title": "Holy Name 01"}]


class _Checkin:
    tone = "returning to early rising"
    mood_bhava = "tṛṇād api sunīcena"


def test_all_four_stages_present():
    r = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert r.orient.body and r.deepen.body and r.enter.text
    assert r.apply is not None  # one micro-practice (US3)


def test_enter_points_into_japa():
    r = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert "japa" in r.enter.text.lower()  # SC-005


def test_corpus_teaching_used_when_available():
    r = build_reading(FIXED, querier=_corpus_hit, checkin_loader=lambda d: None)
    assert r.corpus_online is True
    assert r.deepen.source_kind == "corpus"
    assert "attentively" in r.deepen.body
    assert r.deepen.citation  # SC-002 cited


def test_graceful_fallback_when_corpus_empty():
    r = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert r.corpus_online is False         # SC-004
    assert r.deepen.source_kind == "curated"
    assert r.deepen.body                      # still renders


def test_sankalpa_echo_present_and_absent():
    with_echo = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: _Checkin())
    assert with_echo.sankalpa_echo and "early rising" in with_echo.sankalpa_echo
    without = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert without.sankalpa_echo is None


def test_daily_stable():
    a = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    b = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert a.orient.body == b.orient.body and a.apply == b.apply


def test_apply_requires_no_input():
    # The contemplation is plain data — no callbacks, no recording.
    r = build_reading(FIXED, querier=_no_corpus, checkin_loader=lambda d: None)
    assert r.apply.kind in ("sit_with", "prayer", "question")
    assert isinstance(r.apply.prompt, str)


def test_view_import_safe():
    import importlib

    mod = importlib.import_module("sadhana_setu.ui.prejapa_view")
    assert hasattr(mod, "render")  # importing must not start Streamlit
