"""Smoke tests for the three primary flows — daily capture, Saturday check-in, pre-japa offline.

These tests exercise the domain layer end-to-end. The Streamlit UI is not
tested here (Streamlit's testing harness is heavy and not worth M7 effort
when the views are thin wrappers over the flows).
"""
from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta

import pytest

from sadhana_setu.db.schema import migrate
from sadhana_setu.flows.saturday import (
    WeeklyCheckin,
    get_checkin,
    most_recent_saturday,
    save_checkin,
    week_at_a_glance,
)
from sadhana_setu.flows.today_capture import (
    add_hearing_note,
    delete_hearing_note,
    get_today_rounds,
    list_hearing_notes,
    save_rounds,
)


@pytest.fixture()
def isolated_db(monkeypatch):
    path = tempfile.mktemp(suffix=".db")
    monkeypatch.setenv("SADHANA_SETU_DB", path)
    migrate(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_daily_capture_flow(isolated_db):
    """T-014: rounds save → read → hearing notes add/list/delete."""
    today = date(2026, 6, 10)
    assert get_today_rounds(today) is None

    save_rounds(today, 16)
    r = get_today_rounds(today)
    assert r is not None and r.count == 16

    save_rounds(today, 12)  # re-save
    assert get_today_rounds(today).count == 12

    id1 = add_hearing_note(today, "BG", "Krishna says: do your duty")
    add_hearing_note(today, "SB class", "On detachment")
    add_hearing_note(today, None, "Sourceless line")
    notes = list_hearing_notes(today)
    assert len(notes) == 3

    delete_hearing_note(id1)
    assert len(list_hearing_notes(today)) == 2


def test_saturday_flow(isolated_db):
    """T-015 → T-018: aggregator + persistence."""
    saturday = date(2026, 6, 13)
    for i, count in enumerate([16, 16, 12, 16, 16, 16, 16]):
        save_rounds(saturday - timedelta(days=6 - i), count)
    add_hearing_note(saturday - timedelta(days=2), "BG", "A line")
    add_hearing_note(saturday - timedelta(days=1), "SB class", "Another line")

    summary = week_at_a_glance(saturday)
    assert summary.rounds_completed_days == 6
    assert summary.total_rounds == 108
    assert summary.hearing_note_count == 2

    checkin = WeeklyCheckin(
        week_start=saturday.isoformat(),
        survey_answers=[
            {"question_id": 1, "question": "Which day felt closest?", "answer": "Tuesday"},
        ],
        tone="Return to early rising",
        mood_bhava="trnad api sunicena",
        practices=["Begin japa before 4:45", "One chapter of CC"],
        priorities=["Sleep by 10:45 PM"],
        tools_needed=["Quieter chanting corner"],
        surfaced_pattern=None,
        submitted_at="2026-06-13T07:00:00",
    )
    save_checkin(checkin)
    got = get_checkin(saturday)
    assert got is not None
    assert got.tone == "Return to early rising"
    assert got.practices == ["Begin japa before 4:45", "One chapter of CC"]

    # Upsert
    checkin.tone = "Updated tone"
    save_checkin(checkin)
    assert get_checkin(saturday).tone == "Updated tone"


def test_prejapa_offline_graceful_degradation(isolated_db, monkeypatch):
    """T-025 (AC9): when kg-mcp can't be reached, PreJapaContent reports the failure."""
    monkeypatch.setenv("KG_MCP_BIN", "/nonexistent/kg-mcp-binary")
    from sadhana_setu.flows.prejapa import build_prejapa

    content = build_prejapa("kirtan")
    assert content.mcp_ok is False
    assert content.quotes == []
    assert content.error is not None
    assert content.today_value == "kirtan"


def test_most_recent_saturday_for_various_weekdays():
    """T-015 helper: most_recent_saturday."""
    assert most_recent_saturday(date(2026, 6, 13)) == date(2026, 6, 13)  # Sat
    assert most_recent_saturday(date(2026, 6, 14)) == date(2026, 6, 13)  # Sun
    assert most_recent_saturday(date(2026, 6, 12)) == date(2026, 6, 6)   # Fri
