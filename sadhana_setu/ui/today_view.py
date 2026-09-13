"""Today view — rounds capture + optional hearing notes (T-014).

User-initiated. The agent never asks; this view exists for when the
chanter chooses to record. Idempotent on re-edit for the same date.
"""
from datetime import date

import streamlit as st

from sadhana_setu import i18n
from sadhana_setu.flows.today_capture import (
    add_hearing_note,
    delete_hearing_note,
    get_today_rounds,
    list_hearing_notes,
    save_rounds,
)

SOURCES = ["SB class", "BG", "CC", "NOI", "NOD", "Other"]


def render() -> None:
    today = date.today()
    st.header(i18n.t("today.heading", date=today.strftime('%A, %B %d')))

    existing = get_today_rounds(today)

    st.markdown(i18n.t("today.rounds_completed"))
    with st.form("rounds_form", clear_on_submit=False):
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            count = st.number_input(
                i18n.t("today.count"),
                min_value=0,
                max_value=64,
                value=existing.count if existing else 16,
                step=1,
                label_visibility="collapsed",
                help=i18n.t("today.count_help"),
            )
        with col_btn:
            saved = st.form_submit_button(i18n.t("today.save"), type="primary", use_container_width=True)

        if saved:
            save_rounds(today, int(count))
            st.success(i18n.t("today.saved_rounds", count=count, date=today.isoformat()))
            st.rerun()

    if existing:
        st.caption(i18n.t("today.last_saved", when=existing.captured_at))

    st.divider()

    st.markdown(i18n.t("today.hearing_prompt"))
    with st.form("hearing_form", clear_on_submit=True):
        source_choice = st.selectbox(i18n.t("today.source"), SOURCES, index=0)
        custom_source = ""
        if source_choice == "Other":
            custom_source = st.text_input(
                i18n.t("today.source_other"),
                placeholder=i18n.t("today.source_other_placeholder"),
            )
        line = st.text_input(
            i18n.t("today.line"),
            placeholder=i18n.t("today.line_placeholder"),
        )
        note_saved = st.form_submit_button(i18n.t("today.save_note"), type="primary")

        if note_saved:
            if not line.strip():
                st.warning(i18n.t("today.note_empty"))
            else:
                final_source = custom_source.strip() if source_choice == "Other" else source_choice
                add_hearing_note(today, final_source or None, line.strip())
                st.success(i18n.t("today.note_saved"))
                st.rerun()

    notes = list_hearing_notes(today)
    if notes:
        st.divider()
        st.markdown(i18n.t("today.notes_heading", n=len(notes)))
        for n in notes:
            col_note, col_del = st.columns([10, 1])
            with col_note:
                src = f"*{n.source}* — " if n.source else ""
                st.markdown(f"- {src}{n.line}")
            with col_del:
                if st.button("✕", key=f"del-{n.id}", help=i18n.t("today.remove_note")):
                    delete_hearing_note(n.id)
                    st.rerun()
