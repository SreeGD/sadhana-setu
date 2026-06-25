"""Assemble the pre-japa transformation arc (spec 005).

orient → deepen → apply → enter japa. Deterministic by date (stable within a day, FR-007);
never raises — every stage has a curated fallback so the reading always renders (FR-008/SC-004).
The "deepen" stage prefers a reviewed corpus teaching; "enter" closes with a resolve drawn from
the reading plus an optional gentle echo of the week's sankalpa (FR-002/012).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date

from sadhana_setu import i18n
from sadhana_setu.content import affirmations as affirmations_mod
from sadhana_setu.content import contemplations as contemplations_mod
from sadhana_setu.content import daily_verses as verses_mod
from sadhana_setu.content import faith_verses as faith_mod
from sadhana_setu.content import inspirations as inspirations_mod
from sadhana_setu.content import nama_tattva as nama_mod
from sadhana_setu.content import sankalpas as sankalpas_mod
from sadhana_setu.content import tips as tips_mod
from sadhana_setu.content.affirmations import pick_for_today as pick_affirmation
from sadhana_setu.content.contemplations import Contemplation
from sadhana_setu.content.daily_verses import DailyVerse
from sadhana_setu.content.inspirations import Inspiration
from sadhana_setu.content.sankalpas import Sankalpa
from sadhana_setu.content.tips import Tip
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
    # Blended elements (spec 005 v3) — kept light: verse + story are collapsible (tap-to-read),
    # the tip is a one-liner, the saṅkalpa is the vow taken at the threshold into japa.
    mood_verse: DailyVerse | None = None
    tip: Tip | None = None
    inspiration: Inspiration | None = None
    sankalpa: Sankalpa | None = None
    locale: str = "en"


def localize_item(library: str, all_list: list, item, field: str, english: str, locale: str) -> str:
    """Machine-Telugu (etc.) text for a picked content item, by its position in its library.

    Used by both the reading and the view so the whole pre-japa surface localizes consistently.
    Returns ``english`` for the English locale or when no translation exists.
    """
    if item is None or locale == "en":
        return english
    try:
        idx = all_list.index(item)
    except ValueError:
        return english
    return i18n.localize_content_machine(library, idx, field, english, locale=locale)


def build_reading(d: date | None = None, *, querier=None, checkin_loader=None,
                  today_value: str | None = None, state: dict | None = None,
                  locale: str | None = None) -> PrejapaReading:
    """Assemble the day's transformation arc. Deterministic by ``d``; never raises.

    ``state`` is the shared per-day corpus-retrieval state (spec 003); when the app passes the
    same state to other surfaces, the pre-japa teaching participates in cross-surface dedup.
    ``locale`` localizes the curated content (machine drafts shown for non-English — spec 005/004).
    """
    d = d or date.today()
    loc = locale or i18n.get_locale()
    theme = today_value or pick_today_value(d)

    orient = _orient(d, loc)
    deepen, corpus_online = _deepen(d, theme, querier, state, loc)
    apply = _apply(d, loc)
    enter = _enter(d, orient)
    echo = _sankalpa_echo(d, checkin_loader)

    return PrejapaReading(
        date=d, orient=orient, deepen=deepen, apply=apply, enter=enter,
        sankalpa_echo=echo, corpus_online=corpus_online, locale=loc,
        mood_verse=verses_mod.pick_for_today(d),
        tip=tips_mod.pick_for_today(d),
        inspiration=inspirations_mod.pick_for_today(d),
        sankalpa=sankalpas_mod.pick_for_today(d),
    )


def _orient(d: date, loc: str) -> ReadingStage:
    aff = pick_affirmation(d)
    faith = faith_mod.pick_for_today(d)
    lines = []
    if aff:
        lines.append(localize_item("affirmations", affirmations_mod.all_affirmations(),
                                   aff, "text", aff.text, loc))
    if faith:
        summary = localize_item("faith_verses", faith_mod.all_faith_verses(),
                                faith, "summary", faith.summary, loc)
        lines.append(i18n.t("prejapa.name_promises", summary=summary))
    body = "  ".join(lines) or "Take shelter of the Holy Name with attention and humility."
    citation = (aff.source if aff else None) or (faith.verse_ref if faith else None)
    return ReadingStage(label="Orient", body=body, citation=citation, source_kind="curated")


def _apply(d: date, loc: str):
    c = contemplations_mod.pick_for_today(d)
    if c is None:
        return None
    prompt = localize_item("contemplations", contemplations_mod.all_contemplations(),
                           c, "prompt", c.prompt, loc)
    return replace(c, prompt=prompt) if prompt != c.prompt else c


def _deepen(d: date, theme: str, querier, state, loc: str) -> tuple[ReadingStage, bool]:
    # Shared corpus retrieval; falls back to curated nāma-tattva (FR-003/008).
    from sadhana_setu.flows.harinaam_teaching import fetch_teaching

    stage = fetch_teaching(theme, querier=querier, state=state)
    if stage is not None and loc == "en":
        return stage, True
    # For a non-English locale the corpus note is English (note translation is deferred, 004 US4),
    # so use the localized curated teaching to keep the screen fully in-language.
    nt = nama_mod.pick_for_today(d)
    if nt:
        teaching = localize_item("nama_tattva", nama_mod.all_teachings(), nt, "teaching", nt.teaching, loc)
        return ReadingStage(label=i18n.t("prejapa.deepen_default"), body=teaching,
                            citation=nt.source, source_kind="curated"), False
    return ReadingStage(label=i18n.t("prejapa.deepen_default"),
                        body="Chant to hear: attention is the soul of japa.",
                        citation=None, source_kind="curated"), False


def _enter(d: date, orient: ReadingStage) -> Resolve:
    # Resolve drawn from the day's reading, pointing into japa (FR-002).
    return Resolve(text=i18n.t("prejapa.enter_body", orient=orient.body))


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
