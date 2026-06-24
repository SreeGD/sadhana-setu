"""Assemble the pre-japa transformation arc (spec 005).

orient → deepen → apply → enter japa. Deterministic by date (stable within a day, FR-007);
never raises — every stage has a curated fallback so the reading always renders (FR-008/SC-004).
The "deepen" stage prefers a reviewed corpus teaching; "enter" closes with a resolve drawn from
the reading plus an optional gentle echo of the week's sankalpa (FR-002/012).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sadhana_setu.content import contemplations as contemplations_mod
from sadhana_setu.content import faith_verses as faith_mod
from sadhana_setu.content import nama_tattva as nama_mod
from sadhana_setu.content.affirmations import pick_for_today as pick_affirmation
from sadhana_setu.content.contemplations import Contemplation
from sadhana_setu.flows.today_value import pick_today_value


@dataclass
class ReadingStage:
    label: str
    body: str
    citation: str | None = None
    source_kind: str = "curated"  # "corpus" | "curated"


@dataclass
class Resolve:
    text: str


@dataclass
class PrejapaReading:
    date: date
    orient: ReadingStage
    deepen: ReadingStage
    apply: Contemplation | None
    enter: Resolve
    sankalpa_echo: str | None = None
    corpus_online: bool = False


def build_reading(d: date | None = None, *, caller=None, checkin_loader=None,
                  today_value: str | None = None) -> PrejapaReading:
    """Assemble the day's transformation arc. Deterministic by ``d``; never raises."""
    d = d or date.today()
    theme = today_value or pick_today_value(d)

    orient = _orient(d)
    deepen, corpus_online = _deepen(d, theme, caller)
    apply = contemplations_mod.pick_for_today(d)
    enter = _enter(d, orient)
    echo = _sankalpa_echo(d, checkin_loader)

    return PrejapaReading(date=d, orient=orient, deepen=deepen, apply=apply, enter=enter,
                          sankalpa_echo=echo, corpus_online=corpus_online)


def _orient(d: date) -> ReadingStage:
    aff = pick_affirmation(d)
    faith = faith_mod.pick_for_today(d)
    lines = []
    if aff:
        lines.append(aff.text)
    if faith:
        lines.append(f"The Name promises: {faith.summary}")
    body = "  ".join(lines) or "Take shelter of the Holy Name with attention and humility."
    citation = (aff.source if aff else None) or (faith.verse_ref if faith else None)
    return ReadingStage(label="Orient", body=body, citation=citation, source_kind="curated")


def _deepen(d: date, theme: str, caller) -> tuple[ReadingStage, bool]:
    # Self-contained corpus call; falls back to curated nāma-tattva (FR-003/008).
    from sadhana_setu.flows.harinaam_teaching import fetch_teaching

    stage = fetch_teaching(theme, caller=caller)
    if stage is not None:
        return stage, True
    nt = nama_mod.pick_for_today(d)
    if nt:
        return ReadingStage(label="A teaching on the Holy Name", body=nt.teaching,
                            citation=nt.source, source_kind="curated"), False
    return ReadingStage(label="A teaching on the Holy Name",
                        body="Chant to hear: attention is the soul of japa.",
                        citation=None, source_kind="curated"), False


def _enter(d: date, orient: ReadingStage) -> Resolve:
    # Resolve drawn from the day's reading, pointing into japa (FR-002).
    return Resolve(text=(
        "Now enter your japa — chant to hear each Name, taking shelter, "
        "more humble than a blade of grass. Carry today's orientation in: "
        f"{orient.body}"
    ))


def _sankalpa_echo(d: date, checkin_loader) -> str | None:
    loader = checkin_loader or _default_checkin_loader
    try:
        checkin = loader(d)
    except Exception:  # noqa: BLE001 — optional; never block the reading
        return None
    if not checkin:
        return None
    bits = [b for b in (getattr(checkin, "tone", ""), getattr(checkin, "mood_bhava", "")) if b]
    return "This week's sankalpa: " + " · ".join(bits) if bits else None


def _default_checkin_loader(d: date):
    from sadhana_setu.flows.saturday import get_checkin, most_recent_saturday

    return get_checkin(most_recent_saturday(d))
