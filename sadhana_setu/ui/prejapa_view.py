"""Pre-japa view — v3 transformation arc (spec 005 + blend).

A single contemplative movement that reads in under two minutes and ends pointing into japa:
  (verse·optional) → orient → tip → deepen (a grounded Hari-Nāma teaching) → story·optional →
  apply (a micro-practice) → saṅkalpa (today's vow) → enter japa.
The mood verse and inspiration story are collapsible (tap-to-read), so they add depth without
spending the time budget. All sattvic-medium constraints honored: no streaks, no scoring, no push.
"""
from __future__ import annotations

import re
from datetime import date

import streamlit as st

from sadhana_setu.calendar import ekadasi_name, is_ekadasi
from sadhana_setu.flows import corpus_teaching
from sadhana_setu.flows.prejapa_reading import PrejapaReading, build_reading
from sadhana_setu.flows.today_value import pick_today_value

_CSS = """
<style>
.pj-meta { text-align:center; color:#8B7355; font-style:italic; font-size:0.9rem; margin-bottom:1rem; }
.pj-sep { color:#B8860B; padding:0 0.3rem; }
.pj-eka { color:#B8860B; font-weight:600; background:#FFF5DA; padding:0.1rem 0.45rem; border-radius:4px; }
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
    # Shared per-day corpus state so pre-japa's teaching joins the cross-surface dedup (spec 003).
    state = st.session_state.setdefault(f"corpus_{today.isoformat()}", corpus_teaching.new_state())
    reading = build_reading(today, state=state)

    _render_meta(today)
    if not reading.corpus_online:
        st.markdown(
            "<div class='pj-offline'>Corpus offline — today's teaching is from the curated library.</div>",
            unsafe_allow_html=True,
        )

    _mood_verse(reading)                                  # optional — collapsible
    _stage("Orient", reading.orient.body, reading.orient.citation)
    _tip(reading)                                         # one practical line
    _stage(reading.deepen.label, reading.deepen.body, reading.deepen.citation)
    _inspiration(reading)                                 # optional — collapsible

    if reading.apply is not None:
        _stage("Sit with this — once, before you chant", reading.apply.prompt, reading.apply.source)

    _sankalpa(reading, today)                             # today's vow + button
    _enter(reading)

    st.markdown(
        "<div class='pj-footer'>Close this window when ready. The screen is silent during japa.</div>",
        unsafe_allow_html=True,
    )


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


def _mood_verse(reading: PrejapaReading) -> None:
    v = reading.mood_verse
    if not v:
        return
    head = f"Verse for mood · {v.verse_ref}"
    if v.mood_brought:
        head += f" · {v.mood_brought}"
    with st.expander(f"📖 {head} — tap to read (optional)", expanded=False):
        parts = []
        if v.iast:
            parts.append(f"<div class='pj-verse-iast'>{v.iast.strip().replace(chr(10), '<br>')}</div>")
        if v.translation:
            parts.append(f"<div class='pj-body'>{v.translation.strip()}</div>")
        if v.chanting_connection:
            parts.append(f"<div class='pj-cite'>{v.chanting_connection}</div>")
        if v.source:
            parts.append(f"<div class='pj-cite'>— {v.source}</div>")
        st.markdown("".join(parts), unsafe_allow_html=True)


def _tip(reading: PrejapaReading) -> None:
    t = reading.tip
    if not t:
        return
    src = f"<span class='pj-cite'> — {t.source}</span>" if t.source else ""
    st.markdown(
        f"<div class='pj-tip'><span class='pj-tip-label'>Today's tip</span>{t.tip}{src}</div>",
        unsafe_allow_html=True,
    )


def _inspiration(reading: PrejapaReading) -> None:
    i = reading.inspiration
    if not i:
        return
    with st.expander(f"✨ A story to carry in · {i.title} — tap to read (optional)", expanded=False):
        cite = f"<div class='pj-cite'>— {i.source}</div>" if i.source else ""
        st.markdown(f"<div class='pj-body'>{i.text}</div>{cite}", unsafe_allow_html=True)


def _sankalpa(reading: PrejapaReading, today: date) -> None:
    s = reading.sankalpa
    if not s:
        return
    key = f"sankalpa_made_{today.isoformat()}"
    made = st.session_state.get(key, False)
    # Emphasize a SHOUTED keyword (e.g. THIS) the way the vow is spoken.
    vow = re.sub(r"\b([A-Z]{2,})\b", r"<strong>\1</strong>", s.text)
    label = "Saṅkalpa · ✓ made" if made else ("Saṅkalpa · anchor" if s.anchor else "Saṅkalpa · before japa")
    cite = f"<div class='pj-cite'>— {s.source}</div>" if s.source else ""
    st.markdown(
        f"<div class='pj-vow'><div class='pj-label'>{label}</div>"
        f"<div class='pj-vow-text'>“{vow}”</div>{cite}</div>",
        unsafe_allow_html=True,
    )
    if made:
        st.caption("Vow made. Now: just this mantra.")
        if st.button("Undo", key="pj_sankalpa_undo"):
            st.session_state[key] = False
            _rerun()
    elif st.button("Make the vow for today", key="pj_sankalpa_make"):
        st.session_state[key] = True
        _rerun()


def _enter(reading: PrejapaReading) -> None:
    echo = (f"<div class='pj-echo'>{reading.sankalpa_echo}</div>"
            if reading.sankalpa_echo else "")
    st.markdown(
        f"<div class='pj-enter'><div class='pj-label'>Enter japa</div>"
        f"<div class='pj-enter-body'>{reading.enter.text}</div>{echo}</div>",
        unsafe_allow_html=True,
    )


def _rerun() -> None:
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()
