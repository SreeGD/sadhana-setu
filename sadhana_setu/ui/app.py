"""Sadhana Setu — Streamlit entry point.

Run with:
    streamlit run sadhana_setu/ui/app.py
"""
import streamlit as st

from sadhana_setu.db.connection import ensure_initialized
from sadhana_setu.guards import protected_label

st.set_page_config(
    page_title="Sadhana Setu",
    page_icon="\U0001F549",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ensure_initialized()

st.markdown(
    """
    <style>
    h4 {
        color: #6B3410 !important;
        margin-top: 1rem !important;
        font-family: 'Garamond', 'Georgia', serif !important;
    }
    blockquote {
        border-left: 3px solid #D4A86A !important;
        background-color: #FFFBF3 !important;
        font-style: italic;
    }
    hr {
        border: none !important;
        border-top: 1px solid #E8D9B5 !important;
        margin: 1rem 0 !important;
    }
    .stCaption {
        color: #8B7355 !important;
    }
    [data-testid="stMainBlockContainer"] {
        padding-top: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1280px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Mobile: tighten everything */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.5rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        h4 { font-size: 1rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div style='padding: 0.6rem 0.8rem; margin-bottom: 1rem; "
    "border-bottom: 1px solid #E8D9B5; "
    "font-family: Garamond, Georgia, serif;'>"
    "<span style='color: #B8860B; font-size: 1.15rem;'>❦</span>&nbsp; "
    "<span style='color: #6B3410; font-size: 1.4rem; font-weight: 600; letter-spacing: 0.02em;'>"
    "Sadhana Setu</span>&nbsp;&nbsp;"
    "<span style='color: #B8860B; font-family: \"Adobe Devanagari\", \"Sanskrit Text\", serif; font-size: 1.1rem;'>"
    "साधना सेतुः</span>&nbsp;&nbsp;"
    "<span style='color: #8B7355; font-style: italic; font-size: 0.92rem;'>"
    "· a bridge between aspiration and act</span>"
    "</div>",
    unsafe_allow_html=True,
)

VIEWS = ["Pre-japa", "Today", "This Week", "Saturday Check-in", "History"]

with st.sidebar:
    view = st.radio("View", VIEWS)
    label = protected_label()
    if label:
        st.markdown(f"\U0001F549 _{label}_")
    st.caption("v0.1.5")

if view == "Pre-japa":
    from sadhana_setu.ui import prejapa_view
    prejapa_view.render()
elif view == "Today":
    from sadhana_setu.ui import today_view
    today_view.render()
elif view == "This Week":
    from sadhana_setu.ui import this_week_view
    this_week_view.render()
elif view == "Saturday Check-in":
    from sadhana_setu.ui import saturday_view
    saturday_view.render()
elif view == "History":
    from sadhana_setu.ui import history_view
    history_view.render()
