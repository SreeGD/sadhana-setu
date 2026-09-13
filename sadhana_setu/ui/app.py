"""Sadhana Setu — Streamlit entry point.

Run with:
    streamlit run sadhana_setu/ui/app.py
"""
import streamlit as st

from sadhana_setu import i18n
from sadhana_setu.db.connection import ensure_initialized
from sadhana_setu.guards import protected_label
from sadhana_setu.ui.fonts import indic_font_faces_css

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
    /* Indic-script fonts (spec 004 / FR-005, T024): Noto Sans Telugu/Kannada/Tamil are BUNDLED
       (static/fonts/*.woff2, embedded below as data URIs) — no network, no system-font reliance.
       The Indic faces sit after the Latin serif stack; the browser falls through to them for the
       Telugu/Kannada/Tamil ranges only, so English keeps its serif look. */
    """ + indic_font_faces_css() + """
    html, body, [class*="css"], [data-testid="stMarkdownContainer"] {
        font-family: Georgia, 'Times New Roman', 'Noto Sans Telugu', 'Noto Sans Kannada',
                     'Noto Sans Tamil', serif;
    }
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
    f"{i18n.t('app.tagline')}</span>"
    "</div>",
    unsafe_allow_html=True,
)

VIEWS = ["Pre-japa", "Nama-Tattva", "Today", "This Week", "Saturday Check-in", "Notes", "History"]

_LANGS = {"English": "en", "తెలుగు": "te", "ಕನ್ನಡ": "kn", "தமிழ்": "ta"}
_VIEW_KEYS = {
    "Pre-japa": "view.pre_japa", "Nama-Tattva": "view.nama_tattva", "Today": "view.today",
    "This Week": "view.this_week", "Saturday Check-in": "view.saturday", "Notes": "view.notes",
    "History": "view.history",
}

with st.sidebar:
    _codes = list(_LANGS.values())
    _lang = st.selectbox(i18n.t("sidebar.language"), list(_LANGS),
                         index=_codes.index(i18n.get_locale()) if i18n.get_locale() in _codes else 0)
    i18n.set_locale(_LANGS[_lang])
    view = st.radio(i18n.t("sidebar.view"), VIEWS,
                    format_func=lambda v: i18n.t(_VIEW_KEYS.get(v, v)))
    label = protected_label()
    if label:
        st.markdown(f"\U0001F549 _{label}_")
    st.caption("v0.1.6")

    from sadhana_setu.ui import sync_sidebar
    sync_sidebar.render()

if view == "Pre-japa":
    from sadhana_setu.ui import prejapa_view
    prejapa_view.render()
elif view == "Nama-Tattva":
    from sadhana_setu.ui import nama_tattva_view
    nama_tattva_view.render()
elif view == "Today":
    from sadhana_setu.ui import today_view
    today_view.render()
elif view == "This Week":
    from sadhana_setu.ui import this_week_view
    this_week_view.render()
elif view == "Saturday Check-in":
    from sadhana_setu.ui import saturday_view
    saturday_view.render()
elif view == "Notes":
    from sadhana_setu.ui import notes_view
    notes_view.render()
elif view == "History":
    from sadhana_setu.ui import history_view
    history_view.render()
