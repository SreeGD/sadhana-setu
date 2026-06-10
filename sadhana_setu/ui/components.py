"""Reusable Streamlit components."""
import streamlit as st


def citation(verse_ref: str, source: str | None = None, author: str | None = None) -> None:
    """Render a citation line: verse_ref + author's-purport (when present)."""
    parts = [verse_ref]
    if author:
        parts.append(f"{author}'s purport")
    elif source and source != verse_ref:
        parts.append(source)
    st.caption("— " + ", ".join(parts))
