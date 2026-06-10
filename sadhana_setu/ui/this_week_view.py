"""This Week view — v1.6 Phase β.

Three weekly-rotating sections:
  - Reading: one chapter from the Nama-Tattva book per week
  - Method: one of the four japa methods per week (deep dive)
  - Story: one long-form devotee transformation pastime (the Sunday read)
"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from sadhana_setu.content.japa_methods import pick_for_week as pick_method
from sadhana_setu.content.weekly_readings import pick_for_week as pick_reading
from sadhana_setu.content.weekly_stories import pick_for_week as pick_story


_CSS = """
<style>
.tw-section-title {
    color: #6B3410;
    font-family: 'Garamond', 'Georgia', serif;
    border-bottom: 1px solid #E8D9B5;
    padding-bottom: 0.3rem;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
}
.tw-subtitle {
    color: #8B7355;
    font-style: italic;
    font-size: 0.95rem;
    margin-bottom: 0.2rem;
}
.tw-meta {
    color: #B8860B;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.tw-reading-body {
    line-height: 1.65;
    color: #3D2C1E;
}
.tw-reading-body blockquote {
    border-left: 3px solid #D4A86A !important;
    background-color: #FFFBF3 !important;
    padding: 0.6rem 1rem !important;
    font-style: italic;
}
.tw-method-step {
    background-color: #FFFCF5;
    border: 1px solid #E8D9B5;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.tw-method-step-title {
    font-weight: 600;
    color: #6B3410;
    font-family: 'Garamond', 'Georgia', serif;
    margin-bottom: 0.3rem;
}
.tw-story-text {
    color: #3D2C1E;
    line-height: 1.7;
}
.tw-cite {
    color: #8B7355;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}
.tw-teaching {
    background-color: #FFFBF3;
    border-left: 3px solid #D4A86A;
    padding: 0.8rem 1rem;
    margin-top: 1rem;
    font-style: italic;
    color: #4d3520;
}
</style>
"""


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    today = date.today()
    iso_week = today.isocalendar().week
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    st.markdown(
        f"<h2 style='color:#6B3410; font-family:Garamond,Georgia,serif; "
        f"margin-bottom:0.2rem;'>📖 This Week</h2>"
        f"<div style='color:#8B7355; font-style:italic;'>"
        f"Week {iso_week} · {week_start.strftime('%B %d')} – "
        f"{week_end.strftime('%B %d, %Y')}</div>",
        unsafe_allow_html=True,
    )

    reading = pick_reading(today)
    method = pick_method(today)
    story = pick_story(today)

    # Reading
    st.markdown("<h3 class='tw-section-title'>Reading</h3>", unsafe_allow_html=True)
    if reading is None:
        st.info("Reading library empty.")
    else:
        st.markdown(
            f"<div class='tw-subtitle'>{reading.theme}</div>"
            f"<h4 style='margin-top:0; color:#6B3410;'>{reading.title}</h4>"
            f"<div class='tw-meta'>{reading.subtitle}  ·  ~{reading.reading_minutes} min</div>"
            f"<div class='tw-reading-body'>",
            unsafe_allow_html=True,
        )
        st.markdown(reading.content)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='tw-cite'>— {reading.source}</div>",
            unsafe_allow_html=True,
        )

    # Method
    st.markdown("<h3 class='tw-section-title'>Method of the Week</h3>", unsafe_allow_html=True)
    if method is None:
        st.info("Method library empty.")
    else:
        st.markdown(
            f"<h4 style='margin-top:0; color:#6B3410;'>{method.name}</h4>"
            f"<div class='tw-subtitle'>{method.teacher}  ·  ~{method.duration_minutes} min</div>"
            f"<div style='color:#4d3520; font-style:italic; margin:0.6rem 0;'>"
            f"{method.one_line}</div>"
            f"<div class='tw-reading-body'>{method.overview}</div>",
            unsafe_allow_html=True,
        )
        with st.expander("See the full protocol", expanded=False):
            for step in method.steps:
                st.markdown(
                    f"<div class='tw-method-step'>"
                    f"<div class='tw-method-step-title'>{step.title}</div>"
                    f"<div>{step.practice}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if method.closing:
                st.markdown(
                    f"<div style='margin-top:0.8rem; color:#4d3520; "
                    f"font-style:italic;'>{method.closing}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"<div class='tw-cite'>— {method.source}</div>",
            unsafe_allow_html=True,
        )

    # Story
    is_sunday = today.weekday() == 6
    story_header = "Story of the Week" + ("  ·  ☀️ Sunday read" if is_sunday else "")
    st.markdown(
        f"<h3 class='tw-section-title'>{story_header}</h3>",
        unsafe_allow_html=True,
    )
    if story is None:
        st.info("Story library empty.")
    else:
        st.markdown(
            f"<h4 style='margin-top:0; color:#6B3410;'>{story.title}</h4>"
            f"<div class='tw-subtitle'>{story.devotee}</div>"
            f"<div style='color:#4d3520; font-style:italic; margin:0.6rem 0;'>"
            f"{story.one_line}</div>",
            unsafe_allow_html=True,
        )

        if is_sunday:
            st.markdown(
                f"<div class='tw-story-text'>{_paragraphs(story.text)}</div>",
                unsafe_allow_html=True,
            )
        else:
            with st.expander("Read the full pastime", expanded=False):
                st.markdown(story.text)

        st.markdown(
            f"<div class='tw-teaching'><strong>Teaching:</strong> {story.teaching}</div>"
            f"<div class='tw-cite'>— {story.scripture}  ·  Key verse: {story.key_verse}</div>",
            unsafe_allow_html=True,
        )


def _paragraphs(text: str) -> str:
    """Convert text with double-newline paragraphs into HTML paragraphs."""
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in parts)
