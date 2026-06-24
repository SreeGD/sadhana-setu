"""T016/T018 — grounding: verified, [UNVERIFIED], offline fail-safe, cross-refs."""
import pytest

from sadhana_setu.corpus.grounding import KGUnavailable, ground

ENRICH = {
    "theme_summary": "theme",
    "practical_application": "apply",
    "key_teachings": [
        {"point": "p1", "timestamp": "00:00:01.000", "candidate_verse_refs": ["BG 18.66"]},
        {"point": "p2", "timestamp": "00:00:02.000", "candidate_verse_refs": ["SB 9.9.9"]},
    ],
    "candidate_cross_refs": [{"query": "surrender"}],
}


def make_caller(verses=None, search=None, status_ok=True):
    verses = verses or {}

    def caller(name, args):
        if name == "kg_status":
            if not status_ok:
                raise RuntimeError("kg-mcp down")
            return {"ok": True}
        if name == "get_verse":
            return verses.get(args["verse_ref"], {})
        if name in ("search_corpus", "cross_author_chunks"):
            return search or []
        return None

    return caller


def test_verified_verse_substituted_from_kg():
    caller = make_caller(verses={"BG 18.66": {"iast": "sarva-dharmān", "translation": "Abandon"}})
    content = ground(ENRICH, caller=caller)
    cites = content.key_teachings[0].citations
    assert cites[0].verified and cites[0].iast == "sarva-dharmān"


def test_unresolved_verse_marked_unverified():
    caller = make_caller(verses={"BG 18.66": {"iast": "x", "translation": "y"}})  # SB miss
    content = ground(ENRICH, caller=caller)
    assert not content.key_teachings[1].citations  # SB 9.9.9 withheld
    assert any("SB 9.9.9" in u for u in content.unverified)


def test_offline_fail_safe_raises():
    with pytest.raises(KGUnavailable):
        ground(ENRICH, caller=make_caller(status_ok=False))


def test_cross_ref_grounded():
    caller = make_caller(search=[{"text": "Kṛṣṇa reciprocates", "source": "BG 4.11"}])
    content = ground(ENRICH, caller=caller)
    assert content.cross_references and content.cross_references[0].verified


def test_cross_ref_dropped_when_empty():
    content = ground(ENRICH, caller=make_caller(search=[]))
    assert not content.cross_references
    assert any("cross-ref" in u for u in content.unverified)
