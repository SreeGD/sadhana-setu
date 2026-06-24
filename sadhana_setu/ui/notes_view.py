"""Study / Notes view (spec 003, US4) — browse and read the reviewed enriched notes.

Reads `corpus/notes/` from disk; lists only `status: reviewed` notes grouped by speaker, and
renders the selected note's clean Markdown. Drafts never appear (Constitution V). No metrics.
"""
from __future__ import annotations

from itertools import groupby

import streamlit as st

from sadhana_setu import i18n
from sadhana_setu.flows import corpus_notes


def render() -> None:
    st.markdown(f"### {i18n.t('notes.heading')}")
    st.caption(i18n.t("notes.caption"))

    notes = corpus_notes.list_reviewed_notes()
    if not notes:
        st.info(i18n.t("notes.empty"))
        return

    labels = {f"{n.title}  ·  {n.speaker}": n for n in notes}
    by_speaker = {sp: list(g) for sp, g in groupby(notes, key=lambda n: n.speaker)}
    st.caption(" · ".join(f"{sp} ({len(g)})" for sp, g in by_speaker.items()))

    choice = st.selectbox(i18n.t("notes.open"), list(labels))
    if choice:
        _, body = corpus_notes.read_note(labels[choice].path)
        st.markdown(body)
