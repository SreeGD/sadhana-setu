"""Pre-japa view — v3 transformation arc (spec 005 + blend), locale-aware (spec 004).

A single contemplative movement that reads in under two minutes and ends pointing into japa:
  (verse·optional) → orient → tip → deepen → story·optional → apply → saṅkalpa → enter japa.
UI labels come from the i18n catalog; curated content is localized (machine drafts shown for a
non-English locale, by the user's opt-in) and Sanskrit verses are transliterated into the script.
All sattvic-medium constraints honored: no streaks, no scoring, no push.
"""
from __future__ import annotations

import re
from datetime import date

import streamlit as st

from sadhana_setu import i18n
from sadhana_setu.calendar import ekadasi_name, is_ekadasi
from sadhana_setu.content import daily_verses as verses_mod
from sadhana_setu.content import inspirations as inspirations_mod
from sadhana_setu.content import sankalpas as sankalpas_mod
from sadhana_setu.content import tips as tips_mod
from sadhana_setu.flows import corpus_teaching
from sadhana_setu.flows.prejapa_reading import PrejapaReading, build_reading, localize_item
from sadhana_setu.flows.today_value import pick_today_value

_CSS = """
<style>
.pj-meta { text-align:center; color:#8B7355; font-style:italic; font-size:0.9rem; margin-bottom:1rem; }
.pj-sep { color:#B8860B; padding:0 0.3rem; }
.pj-eka { color:#B8860B; font-weight:600; background:#FFF5DA; padding:0.1rem 0.45rem; border-radius:4px; }
.pj-banner { text-align:center; color:#9A6A2E; background:#FFF5E6; border:1px dashed #D4A86A;
             border-radius:6px; padding:0.3rem 0.6rem; font-size:0.78rem; margin-bottom:0.7rem; }
.pj-stage { background:#FFFCF5; border:1px solid #E8D9B5; border-left:3px solid #D4A86A;
            border-radius:8px; padding:0.85rem 1.1rem; margin-bottom:0.8rem; }
.pj-label { color:#B8860B; font-size:0.72rem; letter-spacing:0.16em; font-weight:600;
            text-transform:uppercase; margin-bottom:0.35rem; }
.pj-body { color:#3D2C1E; line-height:1.55; }
.pj-cite { color:#8B7355; font-size:0.8rem; margin-top:0.4rem; font-style:italic; }
.pj-verse-iast { color:#B8860B; font-style:italic; line-height:1.6; margin-bottom:0.5rem; }
.pj-tip { color:#5C4631; font-size:0.9rem; margin:-0.3rem 0 0.8rem; padding:0 0.3rem; }
.pj-tip-label { color:#B8860B; font-size:0.7rem; letter-spacing:0.12em; font-weight:600;
                text-transform:uppercase; margin-right:0.4rem; }
.pj-vow { background:#FFF8E8; border:1px solid #D4A86A; border-radius:8px;
          padding:0.85rem 1.1rem; margin-bottom:0.5rem; text-align:center; }
.pj-vow .pj-label { color:#6B3410; }
.pj-vow-text { color:#5C3a1a; font-style:italic; font-size:1.1rem; line-height:1.5; margin:0.3rem 0; }
.pj-enter { background:#FFF8E8; border:1px solid #D4A86A; border-radius:8px;
            padding:0.9rem 1.1rem; margin-top:0.4rem; }
.pj-enter .pj-label { color:#6B3410; }
.pj-enter-body { color:#4d3520; line-height:1.55; font-size:1.02rem; }
.pj-echo { color:#8B7355; font-size:0.85rem; margin-top:0.5rem; font-style:italic; }
.pj-offline { color:#A07840; font-size:0.78rem; font-style:italic; margin-bottom:0.6rem; }
.pj-footer { text-align:center; color:#A89878; font-style:italic; font-size:0.82rem; margin-top:1rem; }
</style>
"""


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    today = date.today()
    loc = i18n.get_locale()
    # Shared per-day corpus state so pre-japa's teaching joins the cross-surface dedup (spec 003).
    state = st.session_state.setdefault(f"corpus_{today.isoformat()}", corpus_teaching.new_state())
    reading = build_reading(today, state=state, locale=loc)

    _render_meta(today)
    if loc != "en":
        st.markdown(f"<div class='pj-banner'>{i18n.t('prejapa.machine_banner')}</div>",
                    unsafe_allow_html=True)
    elif not reading.corpus_online:
        st.markdown(f"<div class='pj-offline'>{i18n.t('prejapa.corpus_offline')}</div>",
                    unsafe_allow_html=True)

    _mood_verse(reading, loc)                              # optional — collapsible
    _stage(i18n.t("prejapa.orient"), reading.orient.body, reading.orient.citation)
    _tip(reading, loc)                                     # one practical line
    _stage(reading.deepen.label, reading.deepen.body, reading.deepen.citation)
    _inspiration(reading, loc)                             # optional — collapsible

    if reading.apply is not None:
        _stage(i18n.t("prejapa.apply"), reading.apply.prompt, reading.apply.source)

    _sankalpa(reading, today, loc)                         # today's vow + button
    _enter(reading)

    st.markdown(f"<div class='pj-footer'>{i18n.t('prejapa.footer')}</div>", unsafe_allow_html=True)


def _render_meta(today: date) -> None:
    bits = [f"<span>{today.strftime('%A, %B %d')}</span>",
            "<span class='pj-sep'>·</span>",
            f"<span>value: <em>{pick_today_value(today)}</em></span>"]
    if is_ekadasi(today):
        bits.insert(0, f"<span class='pj-eka'>🌿 {ekadasi_name(today) or 'Ekadasi'}</span>")
        bits.insert(1, "<span class='pj-sep'>·</span>")
    st.markdown(f"<div class='pj-meta'>{' '.join(bits)}</div>", unsafe_allow_html=True)


def _stage(label: str, body: str, citation: str | None) -> None:
    cite = f"<div class='pj-cite'>{citation}</div>" if citation else ""
    st.markdown(
        f"<div class='pj-stage'><div class='pj-label'>{label}</div>"
        f"<div class='pj-body'>{body}</div>{cite}</div>",
        unsafe_allow_html=True,
    )


def _mood_verse(reading: PrejapaReading, loc: str) -> None:
    v = reading.mood_verse
    if not v:
        return
    mood = localize_item("daily_verses", verses_mod.all_daily_verses(), v, "mood_brought",
                         v.mood_brought or "", loc)
    head = f"{i18n.t('prejapa.verse_for_mood')} · {v.verse_ref}"
    if mood:
        head += f" · {mood}"
    with st.expander(f"📖 {head} — {i18n.t('prejapa.tap_to_read')}", expanded=False):
        parts = []
        if v.iast:  # Sanskrit is transliterated into the script, never translated (tattva-safe)
            iast = i18n.maybe_transliterate(v.iast.strip(), locale=loc).replace(chr(10), "<br>")
            parts.append(f"<div class='pj-verse-iast'>{iast}</div>")
        translation = localize_item("daily_verses", verses_mod.all_daily_verses(), v,
                                    "translation", v.translation or "", loc)
        if translation:
            parts.append(f"<div class='pj-body'>{translation.strip()}</div>")
        connection = localize_item("daily_verses", verses_mod.all_daily_verses(), v,
                                   "chanting_connection", v.chanting_connection or "", loc)
        if connection:
            parts.append(f"<div class='pj-cite'>{connection}</div>")
        if v.source:
            parts.append(f"<div class='pj-cite'>— {v.source}</div>")
        st.markdown("".join(parts), unsafe_allow_html=True)


def _tip(reading: PrejapaReading, loc: str) -> None:
    t = reading.tip
    if not t:
        return
    text = localize_item("tips", tips_mod.all_tips(), t, "tip", t.tip, loc)
    src = f"<span class='pj-cite'> — {t.source}</span>" if t.source else ""
    st.markdown(
        f"<div class='pj-tip'><span class='pj-tip-label'>{i18n.t('prejapa.tip_label')}</span>{text}{src}</div>",
        unsafe_allow_html=True,
    )


def _inspiration(reading: PrejapaReading, loc: str) -> None:
    i = reading.inspiration
    if not i:
        return
    title = localize_item("inspirations", inspirations_mod.all_inspirations(), i, "title", i.title, loc)
    text = localize_item("inspirations", inspirations_mod.all_inspirations(), i, "text", i.text, loc)
    with st.expander(f"✨ {i18n.t('prejapa.story_to_carry')} · {title} — {i18n.t('prejapa.tap_to_read')}",
                     expanded=False):
        cite = f"<div class='pj-cite'>— {i.source}</div>" if i.source else ""
        st.markdown(f"<div class='pj-body'>{text}</div>{cite}", unsafe_allow_html=True)


def _sankalpa(reading: PrejapaReading, today: date, loc: str) -> None:
    s = reading.sankalpa
    if not s:
        return
    key = f"sankalpa_made_{today.isoformat()}"
    made = st.session_state.get(key, False)
    text = localize_item("sankalpas", sankalpas_mod.all_sankalpas(), s, "text", s.text, loc)
    vow = re.sub(r"\b([A-Z]{2,})\b", r"<strong>\1</strong>", text)  # emphasize a SHOUTED keyword
    label = (i18n.t("prejapa.sankalpa_made") if made
             else i18n.t("prejapa.sankalpa_anchor") if s.anchor else i18n.t("prejapa.sankalpa_before"))
    cite = f"<div class='pj-cite'>— {s.source}</div>" if s.source else ""
    st.markdown(
        f"<div class='pj-vow'><div class='pj-label'>{label}</div>"
        f"<div class='pj-vow-text'>“{vow}”</div>{cite}</div>",
        unsafe_allow_html=True,
    )
    if made:
        st.caption(i18n.t("prejapa.vow_made"))
        if st.button(i18n.t("prejapa.undo"), key="pj_sankalpa_undo"):
            st.session_state[key] = False
            _rerun()
    elif st.button(i18n.t("prejapa.make_vow"), key="pj_sankalpa_make"):
        st.session_state[key] = True
        _rerun()


def _enter(reading: PrejapaReading) -> None:
    echo = (f"<div class='pj-echo'>{reading.sankalpa_echo}</div>"
            if reading.sankalpa_echo else "")
    st.markdown(
        f"<div class='pj-enter'><div class='pj-label'>{i18n.t('prejapa.enter')}</div>"
        f"<div class='pj-enter-body'>{reading.enter.text}</div>{echo}</div>",
        unsafe_allow_html=True,
    )


def _rerun() -> None:
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()
