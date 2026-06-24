"""Streamlit review UI for enriched class notes (US4).

Run with: ``streamlit run sadhana_setu/ui/review_view.py``

Lists draft notes, renders each with its `[UNVERIFIED]` / `[sic?]` review aids, and on Approve
records reviewer + date (`review.approve`) then auto-ingests into the KG (`ingest.ingest_note`).
Importing this module does not start Streamlit; only running it as a script does.
"""
from __future__ import annotations

from pathlib import Path

from sadhana_setu.corpus import ingest as ingest_mod
from sadhana_setu.corpus import review as review_mod
from sadhana_setu.corpus.config import CorpusConfig


def main() -> None:  # pragma: no cover - exercised via `streamlit run`, not unit tests
    import streamlit as st

    cfg = CorpusConfig.from_env()
    st.title("Hari-Nāma Notes — Review")
    st.caption("Approve drafts for tattva accuracy. Approving ingests the note into the KG.")

    reviewer = st.text_input("Reviewer (your initiated name)")
    drafts = review_mod.list_drafts(cfg.notes_dir)
    if not drafts:
        st.success("No drafts awaiting review.")
        return

    choice = st.selectbox("Draft notes", drafts, format_func=lambda p: str(p.relative_to(cfg.repo_root)))
    if choice:
        st.markdown(Path(choice).read_text(encoding="utf-8"))
        if st.button("Approve", disabled=not reviewer):
            review_mod.approve(Path(choice), reviewer)
            try:
                added = ingest_mod.ingest_note(Path(choice))
                st.success(f"Approved + ingested ({added} chunks).")
            except Exception as exc:  # noqa: BLE001 — surface ingest failure, keep approval
                st.warning(f"Approved; ingest pending ({exc}).")
            st.rerun()


if __name__ == "__main__":
    main()
