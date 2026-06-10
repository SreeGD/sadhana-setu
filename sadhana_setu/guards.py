"""Protected-hours guard.

Per PRD §10.5, two windows must never see a modal / toast / push:
  - 3:30 AM – 9:30 AM  (sadhana arc)
  - 8:30 PM – 10:30 PM (office meeting block)

v1 has no notifications at all, so the guard is informational today —
it exists so any future code path that adds a notification will have to
consult it. The UI uses it to render a small "protected hours" indicator
in the sidebar.
"""
from datetime import datetime, time

SADHANA_START = time(3, 30)
SADHANA_END = time(9, 30)
OFFICE_START = time(20, 30)
OFFICE_END = time(22, 30)


def in_sadhana_window(now: datetime | None = None) -> bool:
    t = (now or datetime.now()).time()
    return SADHANA_START <= t < SADHANA_END


def in_office_window(now: datetime | None = None) -> bool:
    t = (now or datetime.now()).time()
    return OFFICE_START <= t < OFFICE_END


def in_protected_hours(now: datetime | None = None) -> bool:
    return in_sadhana_window(now) or in_office_window(now)


def protected_label(now: datetime | None = None) -> str | None:
    if in_sadhana_window(now):
        return "Protected hours — sadhana (3:30–9:30 AM)"
    if in_office_window(now):
        return "Protected hours — office (8:30–10:30 PM)"
    return None
