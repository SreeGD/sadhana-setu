"""History view — browse past weekly check-ins and hearing notes. M7."""
import streamlit as st

from sadhana_setu import i18n


def render() -> None:
    st.header(i18n.t("history.heading"))
    st.info(i18n.t("history.placeholder"))
