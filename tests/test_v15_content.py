"""Unit tests for v1.5 content libraries and selectors."""
from __future__ import annotations

from datetime import date, timedelta

from sadhana_setu.content.affirmations import (
    all_affirmations,
    pick_for_today as pick_affirmation,
)
from sadhana_setu.content.bhajans import all_bhajans, pick_for_week as pick_bhajan
from sadhana_setu.content.faith_verses import (
    all_faith_verses,
    pick_for_today as pick_faith_verse,
)
from sadhana_setu.content.inspirations import (
    all_inspirations,
    pick_for_today as pick_inspiration,
)
from sadhana_setu.content.nama_tattva import (
    all_teachings,
    pick_for_today as pick_nama_tattva,
)
from sadhana_setu.content.tips import all_tips


def test_all_libraries_have_minimum_seed():
    """Every v1.5 library has at least 12 draft entries."""
    assert len(all_affirmations()) >= 20
    assert len(all_inspirations()) >= 15
    assert len(all_faith_verses()) >= 15
    assert len(all_teachings()) >= 15
    assert len(all_bhajans()) >= 12


def test_every_entry_has_citation():
    """Sacred constraint — no unsourced sastra content ships."""
    for a in all_affirmations():
        assert a.source, f"affirmation missing source: {a.text}"
    for i in all_inspirations():
        assert i.source, f"inspiration missing source: {i.title}"
    for fv in all_faith_verses():
        assert fv.source, f"faith verse missing source: {fv.verse_ref}"
    for nt in all_teachings():
        assert nt.source, f"nama-tattva missing source: {nt.title}"
    for b in all_bhajans():
        assert b.source, f"bhajan missing source: {b.title}"


def test_daily_rotation_is_deterministic():
    """Same day → same pick, every time. Different day → potentially different pick."""
    d = date(2026, 6, 10)
    a1 = pick_affirmation(d)
    a2 = pick_affirmation(d)
    assert a1 == a2

    i1 = pick_inspiration(d)
    i2 = pick_inspiration(d)
    assert i1 == i2

    fv1 = pick_faith_verse(d)
    fv2 = pick_faith_verse(d)
    assert fv1 == fv2

    nt1 = pick_nama_tattva(d)
    nt2 = pick_nama_tattva(d)
    assert nt1 == nt2


def test_rotation_changes_across_days():
    """Over a long enough window, the picker eventually returns different entries."""
    days = [date(2026, 1, 1) + timedelta(days=i) for i in range(60)]
    affs = {pick_affirmation(d) for d in days}
    assert len(affs) >= 5  # not stuck on one
    inspirations = {pick_inspiration(d) for d in days}
    assert len(inspirations) >= 5


def test_bhajan_rotation_is_weekly_not_daily():
    """All days in the same ISO week give the same bhajan."""
    saturday = date(2026, 6, 13)
    sunday = date(2026, 6, 14)  # different ISO week (Sunday starts a new one — verify)
    b_sat = pick_bhajan(saturday)
    b_same_sat = pick_bhajan(saturday)
    assert b_sat == b_same_sat

    # All days within Mon-Sun ISO week share the same bhajan
    days_in_week = [date(2026, 6, 8) + timedelta(days=i) for i in range(7)]  # Mon-Sun
    picks = {pick_bhajan(d) for d in days_in_week}
    assert len(picks) == 1, "all days in one ISO week should share one bhajan"


def test_tips_library_expanded_with_nama_tattva():
    """v1.5 tips expansion added at least 20 new entries with Nama-Tattva sourcing."""
    tips = all_tips()
    assert len(tips) >= 55  # v1 had ~40; v1.5 adds ~20+
    # At least some tips reference Padma Purana (the offenses) or Hari-nama-cintamani
    nama_tattva_sources = sum(
        1
        for t in tips
        if t.source
        and (
            "Padma Purana" in t.source
            or "Hari-nama-cintamani" in t.source
            or "Brhad-Bhagavatamrta" in t.source
        )
    )
    assert nama_tattva_sources >= 5, f"expected >=5 Nama-Tattva-derived tips, got {nama_tattva_sources}"
