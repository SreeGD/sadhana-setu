"""Nama-Tattva view (spec 003, US2) — one deeper daily teaching on the Holy Name.

Prefers a reviewed corpus teaching (via the shared service, themed by the day's value) and falls
back to the curated `nama_tattva` library. Shares the per-day corpus state with pre-japa, so its
teaching is de-duplicated against the others (FR-013).
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from sadhana_setu.content.nama_tattva import pick_for_today as pick_curated
from sadhana_setu.flows import corpus_teaching
from sadhana_setu.flows.today_value import pick_today_value

_CSS = """
<style>
.nt-card { background:#FFFCF5; border:1px solid #D4A86A; border-left:3px solid #B8860B;
           border-radius:8px; padding:1rem 1.2rem; }
.nt-label { color:#B8860B; font-size:0.72rem; letter-spacing:0.16em; font-weight:600;
            text-transform:uppercase; margin-bottom:0.4rem; }
.nt-body { color:#3D2C1E; line-height:1.6; font-size:1.02rem; }
.nt-cite { color:#8B7355; font-size:0.82rem; margin-top:0.5rem; font-style:italic; }
</style>
"""


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    today = date.today()
    state = st.session_state.setdefault(f"corpus_{today.isoformat()}", corpus_teaching.new_state())

    teaching = corpus_teaching.get_for_surface(
        pick_today_value(today), "nama-tattva", date=today, state=state)

    if teaching is not None:  # prefer corpus (FR-011)
        body, cite = teaching.body, teaching.citation
    else:
        nt = pick_curated(today)
        if nt is None:
            st.info("No Nama-Tattva for today.")
            return
        body, cite = nt.teaching, nt.source

    st.markdown(
        f"<div class='nt-card'><div class='nt-label'>Nāma-Tattva — a teaching on the Name</div>"
        f"<div class='nt-body'>{body}</div>"
        f"<div class='nt-cite'>— {cite}</div></div>",
        unsafe_allow_html=True,
    )
