"""Pre-japa view — v2 transformation arc (spec 005).

Replaces the informational card layout with a single contemplative movement:
  orient → deepen (a grounded Hari-Nāma teaching) → apply (a micro-practice) → enter japa.
Reads in ~60–75s; ends pointing into chanting. All sattvic-medium constraints honored:
no streaks, no scoring, no push, no screen interaction expected during japa.
"""
from __future__ import annotations

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

    _stage("Orient", reading.orient.body, reading.orient.citation)
    _stage(reading.deepen.label, reading.deepen.body, reading.deepen.citation)

    if reading.apply is not None:
        _stage("Sit with this — once, before you chant", reading.apply.prompt, reading.apply.source)

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


def _enter(reading: PrejapaReading) -> None:
    echo = (f"<div class='pj-echo'>{reading.sankalpa_echo}</div>"
            if reading.sankalpa_echo else "")
    st.markdown(
        f"<div class='pj-enter'><div class='pj-label'>Enter japa</div>"
        f"<div class='pj-enter-body'>{reading.enter.text}</div>{echo}</div>",
        unsafe_allow_html=True,
    )
