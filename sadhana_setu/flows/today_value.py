"""Today-value selector. Picks the value-id that frames today's pre-japa.

M2: weekly rotation across the 12 relevant Vaishnava values.
M4 will override from the user's last Saturday sankalpa (when set).
"""
from datetime import date

RELEVANT_VALUES: list[str] = [
    "kirtan",
    "bhakti",
    "pratijna",
    "shraddha",
    "svadhyaya",
    "shaucha",
    "guru_bhakti",
    "tulasi_seva",
    "dhyana",
    "ishvara_pranidhana",
    "seva",
    "prema",
]


def pick_today_value(d: date | None = None) -> str:
    d = d or date.today()
    week_num = d.isocalendar().week
    return RELEVANT_VALUES[week_num % len(RELEVANT_VALUES)]
