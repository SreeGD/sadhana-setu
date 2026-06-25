"""Pickers for the pre-japa blend: daily_verses (mood) + sankalpas (Wed-anchor rotation)."""
from datetime import date

from sadhana_setu.content import daily_verses, sankalpas, tips


def test_daily_verse_picks_and_is_stable():
    d = date(2026, 6, 25)
    v = daily_verses.pick_for_today(d)
    assert v and v.verse_ref
    assert daily_verses.pick_for_today(d) == v  # deterministic by day


def test_sankalpa_wednesday_returns_anchor():
    anchor = sankalpas.pick_for_today(date(2026, 6, 24))  # Wednesday
    assert anchor.anchor is True


def test_sankalpa_other_days_avoid_anchor():
    for day in (date(2026, 6, 25), date(2026, 6, 26), date(2026, 6, 27)):  # Thu/Fri/Sat
        assert sankalpas.pick_for_today(day).anchor is False


def test_tip_pick_for_today_stable():
    d = date(2026, 6, 25)
    assert tips.pick_for_today(d) == tips.pick_for_today(d)
