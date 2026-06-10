"""Today view — rounds capture + optional hearing notes (T-014).

User-initiated. The agent never asks; this view exists for when the
chanter chooses to record. Idempotent on re-edit for the same date.
"""
from datetime import date

import streamlit as st

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
    st.header(f"Today — {today.strftime('%A, %B %d')}")

    existing = get_today_rounds(today)

    st.markdown("**Rounds completed today**")
    with st.form("rounds_form", clear_on_submit=False):
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            count = st.number_input(
                "Count",
                min_value=0,
                max_value=64,
                value=existing.count if existing else 16,
                step=1,
                label_visibility="collapsed",
                help="Standing vow is 16. Edit and re-save freely.",
            )
        with col_btn:
            saved = st.form_submit_button("Save", type="primary", use_container_width=True)

        if saved:
            save_rounds(today, int(count))
            st.success(f"Saved: {count} rounds for {today.isoformat()}")
            st.rerun()

    if existing:
        st.caption(f"Last saved: {existing.captured_at}  •  Edit above and Save again any time.")

    st.divider()

    st.markdown("**Anything from today's hearing?** (optional)")
    with st.form("hearing_form", clear_on_submit=True):
        source_choice = st.selectbox("Source", SOURCES, index=0)
        custom_source = ""
        if source_choice == "Other":
            custom_source = st.text_input(
                "Source (e.g., HG Radhe Syam class, specific verse, ...)",
                placeholder="HG Radhe Syam class",
            )
        line = st.text_input(
            "One line worth remembering",
            placeholder="What did you hear that you don't want to forget?",
        )
        note_saved = st.form_submit_button("Save note", type="primary")

        if note_saved:
            if not line.strip():
                st.warning("Note is empty — nothing saved.")
            else:
                final_source = custom_source.strip() if source_choice == "Other" else source_choice
                add_hearing_note(today, final_source or None, line.strip())
                st.success("Note saved.")
                st.rerun()

    notes = list_hearing_notes(today)
    if notes:
        st.divider()
        st.markdown(f"**Today's notes ({len(notes)})**")
        for n in notes:
            col_note, col_del = st.columns([10, 1])
            with col_note:
                src = f"*{n.source}* — " if n.source else ""
                st.markdown(f"- {src}{n.line}")
            with col_del:
                if st.button("✕", key=f"del-{n.id}", help="Remove this note"):
                    delete_hearing_note(n.id)
                    st.rerun()
