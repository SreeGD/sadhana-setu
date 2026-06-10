"""Ekadasi calendar lookup.

    from sadhana_setu.calendar import is_ekadasi, ekadasi_name

CLI:
    python -m sadhana_setu ekadasi [YYYY-MM-DD]
"""
import json
import sys
from datetime import date as date_cls, datetime
from pathlib import Path

EKADASI_FILE = Path(__file__).parent.parent / "data" / "ekadasi.json"


def _load() -> dict:
    if not EKADASI_FILE.exists():
        return {"dates": []}
    return json.loads(EKADASI_FILE.read_text())


_DATA = _load()
_DATES: dict[str, str | None] = {
    entry["date"]: entry.get("name") for entry in _DATA.get("dates", [])
}


def is_ekadasi(d: date_cls) -> bool:
    return d.isoformat() in _DATES


def ekadasi_name(d: date_cls) -> str | None:
    return _DATES.get(d.isoformat())


def main(argv: list[str]) -> None:
    if argv:
        d = datetime.strptime(argv[0], "%Y-%m-%d").date()
    else:
        d = date_cls.today()
    if is_ekadasi(d):
        name = ekadasi_name(d)
        print(f"{d.isoformat()}: {name or 'ekadasi (unnamed)'}")
    else:
        print(f"{d.isoformat()}: not ekadasi")


if __name__ == "__main__":
    main(sys.argv[1:])
