"""Study / Notes view (spec 003, US4) — browse and read the reviewed enriched notes.

Reads `corpus/notes/` from disk; lists only `status: reviewed` notes grouped by speaker, and
renders the selected note's clean Markdown. Drafts never appear (Constitution V). No metrics.
"""
from __future__ import annotations

from itertools import groupby

import streamlit as st

from sadhana_setu.flows import corpus_notes


def render() -> None:
    st.markdown("### Hari-Nāma Notes")
    st.caption("Reviewed class notes from the gathered Holy-Name lectures.")

    notes = corpus_notes.list_reviewed_notes()
    if not notes:
        st.info("No reviewed notes yet. Enriched notes appear here once a devotee approves them.")
        return

    labels = {f"{n.title}  ·  {n.speaker}": n for n in notes}
    by_speaker = {sp: list(g) for sp, g in groupby(notes, key=lambda n: n.speaker)}
    st.caption(" · ".join(f"{sp} ({len(g)})" for sp, g in by_speaker.items()))

    choice = st.selectbox("Open a note", list(labels))
    if choice:
        _, body = corpus_notes.read_note(labels[choice].path)
        st.markdown(body)
