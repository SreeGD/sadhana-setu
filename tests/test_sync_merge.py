"""Tests for the pure merge functions in sadhana_setu.sync.gdrive.

These don't touch SQLite or the network — they exercise the dict-in,
dict-out merge logic the sync pipeline depends on.
"""
from sadhana_setu.sync.gdrive import merge_daily, merge_weekly


def _round(date, count, captured_at, note=None):
    return {"date": date, "count": count, "captured_at": captured_at, "note": note}


def _note(date, captured_at, line, source=None):
    return {"date": date, "source": source, "line": line, "captured_at": captured_at}


def _checkin(week_start, submitted_at, **extras):
    base = {
        "week_start": week_start,
        "survey_answers": [],
        "tone": "",
        "mood_bhava": "",
        "practices": [],
        "priorities": [],
        "tools_needed": [],
        "surfaced_pattern": None,
        "submitted_at": submitted_at,
    }
    base.update(extras)
    return base


# ---------- daily / rounds ----------

def test_rounds_remote_wins_when_newer():
    local = {"rounds": [_round("2026-06-10", 12, "2026-06-10T07:00:00")]}
    remote = {"rounds": [_round("2026-06-10", 16, "2026-06-10T08:00:00")]}
    merged = merge_daily(local, remote)
    assert len(merged["rounds"]) == 1
    assert merged["rounds"][0]["count"] == 16


def test_rounds_local_wins_when_newer():
    local = {"rounds": [_round("2026-06-10", 16, "2026-06-10T09:00:00")]}
    remote = {"rounds": [_round("2026-06-10", 12, "2026-06-10T07:00:00")]}
    merged = merge_daily(local, remote)
    assert merged["rounds"][0]["count"] == 16


def test_rounds_union_across_dates():
    local = {"rounds": [_round("2026-06-10", 16, "t1")]}
    remote = {"rounds": [_round("2026-06-11", 14, "t2")]}
    merged = merge_daily(local, remote)
    dates = {r["date"] for r in merged["rounds"]}
    assert dates == {"2026-06-10", "2026-06-11"}


def test_rounds_sorted_by_date():
    local = {"rounds": [_round("2026-06-12", 16, "t1")]}
    remote = {"rounds": [_round("2026-06-10", 14, "t0"), _round("2026-06-11", 15, "t2")]}
    merged = merge_daily(local, remote)
    assert [r["date"] for r in merged["rounds"]] == [
        "2026-06-10", "2026-06-11", "2026-06-12"
    ]


# ---------- daily / hearing_notes ----------

def test_notes_dedup_on_identical_triple():
    n = _note("2026-06-10", "2026-06-10T07:30:00", "SB 1.1.1 — Sūta")
    merged = merge_daily({"hearing_notes": [n]}, {"hearing_notes": [n]})
    assert len(merged["hearing_notes"]) == 1


def test_notes_union_when_different():
    local_n = _note("2026-06-10", "2026-06-10T07:30:00", "morning class")
    remote_n = _note("2026-06-10", "2026-06-10T18:30:00", "evening kirtan")
    merged = merge_daily({"hearing_notes": [local_n]}, {"hearing_notes": [remote_n]})
    assert len(merged["hearing_notes"]) == 2


def test_notes_sorted_by_date_then_time():
    older = _note("2026-06-09", "2026-06-09T18:00:00", "b")
    newer_same_day_early = _note("2026-06-10", "2026-06-10T07:30:00", "a")
    newer_same_day_late = _note("2026-06-10", "2026-06-10T18:30:00", "c")
    merged = merge_daily(
        {"hearing_notes": [newer_same_day_late, older]},
        {"hearing_notes": [newer_same_day_early]},
    )
    assert [n["line"] for n in merged["hearing_notes"]] == ["b", "a", "c"]


# ---------- weekly ----------

def test_checkin_remote_wins_when_newer():
    local = {"checkins": [_checkin("2026-06-08", "2026-06-13T18:00:00", tone="local")]}
    remote = {"checkins": [_checkin("2026-06-08", "2026-06-13T20:00:00", tone="remote")]}
    merged = merge_weekly(local, remote)
    assert len(merged["checkins"]) == 1
    assert merged["checkins"][0]["tone"] == "remote"


def test_checkin_local_wins_when_newer():
    local = {"checkins": [_checkin("2026-06-08", "2026-06-13T20:00:00", tone="local")]}
    remote = {"checkins": [_checkin("2026-06-08", "2026-06-13T18:00:00", tone="remote")]}
    merged = merge_weekly(local, remote)
    assert merged["checkins"][0]["tone"] == "local"


def test_checkin_union_across_weeks():
    local = {"checkins": [_checkin("2026-06-08", "t1")]}
    remote = {"checkins": [_checkin("2026-06-15", "t2")]}
    merged = merge_weekly(local, remote)
    assert {c["week_start"] for c in merged["checkins"]} == {"2026-06-08", "2026-06-15"}


def test_empty_inputs_safe():
    merged = merge_daily({}, {})
    assert merged == {"version": 1, "rounds": [], "hearing_notes": []}
    merged_w = merge_weekly({}, {})
    assert merged_w == {"version": 1, "checkins": []}
