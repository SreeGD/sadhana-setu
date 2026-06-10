"""Pre-japa view — v1.6 Phase B (Featured layout).

Layout:
  - Compact one-line header (title · date · value · ekadasi)
  - Featured card (full-width, rotates daily; Sat=Bhajan, Sun=Story)
  - Supporting cards in a tight grid
  - Daily practical tip from the Nama-Tattva publication (full-width bottom)
"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from sadhana_setu.calendar import ekadasi_name, is_ekadasi
from sadhana_setu.content.affirmations import pick_for_today as pick_affirmation
from sadhana_setu.content.bhajans import pick_for_week as pick_bhajan
from sadhana_setu.content.book_tips import pick_for_today as pick_book_tip
from sadhana_setu.content.faith_verses import pick_for_today as pick_faith_verse
from sadhana_setu.content.inspirations import pick_for_today as pick_inspiration
from sadhana_setu.content.nama_tattva import pick_for_today as pick_nama_tattva
from sadhana_setu.content.tips import pick_tip
from sadhana_setu.content.weekly_stories import pick_for_week as pick_story
from sadhana_setu.flows.today_value import pick_today_value


_CSS = """
<style>
.prejapa-meta {
    text-align: center;
    color: #8B7355;
    font-style: italic;
    font-size: 0.9rem;
    margin-bottom: 0.9rem;
}
.meta-sep { color: #B8860B; padding: 0 0.3rem; }
.meta-day {}
.meta-val em { color: #6B3410; font-style: italic; }
.meta-eka {
    color: #B8860B;
    font-weight: 600;
    background-color: #FFF5DA;
    padding: 0.1rem 0.45rem;
    border-radius: 4px;
    font-style: normal !important;
}

.featured {
    background-color: #FFFCF5;
    border: 1px solid #D4A86A;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 1px 3px rgba(180, 130, 60, 0.08);
}
.featured-label {
    color: #B8860B;
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.featured-title {
    color: #6B3410;
    font-family: 'Garamond', 'Georgia', serif;
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.featured-devanagari {
    font-family: 'Adobe Devanagari', 'Sanskrit Text', 'Noto Serif Devanagari', serif;
    color: #6B3410;
    font-size: 1.2rem;
    margin: 0.4rem 0;
    text-align: center;
}
.featured-iast {
    color: #8B6F47;
    font-style: italic;
    text-align: center;
    margin-bottom: 0.5rem;
}
.featured-body {
    color: #3D2C1E;
    line-height: 1.55;
    margin: 0.4rem 0;
}
.featured-quote {
    border-left: 3px solid #D4A86A;
    background-color: #FFF8E8;
    padding: 0.55rem 0.9rem;
    margin: 0.5rem 0;
    font-style: italic;
    color: #4d3520;
}
.featured-cite {
    color: #8B7355;
    font-size: 0.82rem;
    margin-top: 0.4rem;
}

.support-card {
    background-color: #FFFCF5;
    border: 1px solid #E8D9B5;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    min-height: 200px;
    display: flex;
    flex-direction: column;
}
.support-label {
    color: #B8860B;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.support-title {
    font-weight: 600;
    color: #6B3410;
    font-family: 'Garamond', 'Georgia', serif;
    font-size: 0.98rem;
    margin-bottom: 0.35rem;
    line-height: 1.3;
}
.support-body {
    color: #3D2C1E;
    font-size: 0.88rem;
    line-height: 1.5;
    flex-grow: 1;
}
.support-cite {
    color: #8B7355;
    font-size: 0.74rem;
    margin-top: 0.5rem;
    padding-top: 0.4rem;
    border-top: 1px solid #F0E5D0;
}

/* Mobile: cards stack, full-width, no min-height constraint */
@media (max-width: 768px) {
    .support-card { min-height: 0; }
    .featured { padding: 0.8rem 1rem; }
    .featured-title { font-size: 1.15rem; }
    .featured-body { font-size: 0.95rem; }
    .book-tip { padding: 0.6rem 0.8rem; }
}

.book-tip {
    background-color: #FFF8E8;
    border-left: 4px solid #B8860B;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-top: 0.6rem;
}
.book-tip-label {
    color: #B8860B;
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.book-tip-title {
    font-weight: 600;
    color: #6B3410;
    font-family: 'Garamond', 'Georgia', serif;
    font-size: 1rem;
    margin-bottom: 0.4rem;
}
.book-tip-body {
    color: #3D2C1E;
    line-height: 1.5;
    font-size: 0.9rem;
}
.book-tip-meta {
    color: #8B7355;
    font-size: 0.78rem;
    margin-top: 0.4rem;
}

.footer-note {
    color: #8B7355;
    font-style: italic;
    text-align: center;
    margin-top: 0.8rem;
    font-size: 0.85rem;
}
</style>
"""


def _truncate(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _render_meta(today: date, today_value: str, is_eka: bool) -> None:
    bits = [
        f"<span class='meta-day'>{today.strftime('%A, %B %d')}</span>",
        "<span class='meta-sep'>·</span>",
        f"<span class='meta-val'>value: <em>{today_value}</em></span>",
    ]
    if is_eka:
        bits.insert(0, f"<span class='meta-eka'>🌿 {ekadasi_name(today) or 'Ekadasi'}</span>")
        bits.insert(1, "<span class='meta-sep'>·</span>")
    st.markdown(
        f"<div class='prejapa-meta'>{' '.join(bits)}</div>",
        unsafe_allow_html=True,
    )


def _render_featured_affirmation(today: date) -> None:
    a = pick_affirmation(today)
    if a is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>❦ TODAY'S AFFIRMATION</div>"
        f"<div class='featured-title' style='text-align:center; font-style:italic;'>"
        f"“{a.text}”"
        f"</div>"
        f"<div class='featured-cite' style='text-align:center;'>— {a.source}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_faith(today: date) -> None:
    fv = pick_faith_verse(today)
    if fv is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>❦ TODAY'S FAITH VERSE</div>"
        f"<div class='featured-title' style='text-align:center;'>{fv.verse_ref}</div>"
        f"<div class='featured-quote'>{fv.summary}</div>"
        f"<div class='featured-cite' style='text-align:center;'>— {fv.source or fv.verse_ref}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_inspiration(today: date) -> None:
    i = pick_inspiration(today)
    if i is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>❦ TODAY'S INSPIRATION</div>"
        f"<div class='featured-title'>{i.title}</div>"
        f"<div class='featured-body'>{i.text}</div>"
        f"<div class='featured-cite'>— {i.source}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_tip(today: date, today_value: str, is_eka: bool) -> None:
    t = pick_tip(value_ids=[today_value, "kirtan", "bhakti"], ekadasi=is_eka)
    if t is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>\U0001F4A1 TODAY'S TIP</div>"
        f"<div class='featured-title' style='font-style:italic;'>“{t.tip}”</div>"
        f"<div class='featured-cite' style='text-align:right;'>— {t.source or ''}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_nama_tattva(today: date) -> None:
    nt = pick_nama_tattva(today)
    if nt is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>❦ NAMA-TATTVA</div>"
        f"<div class='featured-title'>{nt.title}</div>"
        f"<div class='featured-body'>{nt.teaching}</div>"
        f"<div class='featured-cite'>— {nt.source}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_bhajan(today: date) -> None:
    b = pick_bhajan(today)
    if b is None:
        return
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>\U0001F549 BHAJAN OF THE WEEK</div>"
        f"<div class='featured-title' style='text-align:center;'>{b.title}</div>"
        f"<div class='featured-cite' style='text-align:center; font-style:italic; margin-bottom:0.6rem;'>{b.author}</div>"
        f"<div class='featured-iast'>{b.verse_iast}</div>"
        f"<div class='featured-quote'>{b.verse_translation}</div>"
        f"<div class='featured-cite' style='text-align:center;'>— {b.source}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_featured_story(today: date) -> None:
    s = pick_story(today)
    if s is None:
        return
    text_paragraphs = "".join(
        f"<p style='margin:0.5rem 0;'>{p}</p>"
        for p in s.text.split("\n\n")
        if p.strip()
    )
    st.markdown(
        f"<div class='featured'>"
        f"<div class='featured-label'>✨ STORY OF THE WEEK · SUNDAY READ</div>"
        f"<div class='featured-title'>{s.title}</div>"
        f"<div class='featured-cite' style='font-style:italic; margin-bottom:0.6rem;'>{s.one_line}</div>"
        f"<div class='featured-body'>{text_paragraphs}</div>"
        f"<div class='featured-cite'><strong>Teaching:</strong> {s.teaching}</div>"
        f"<div class='featured-cite'>— {s.scripture} · Key verse: {s.key_verse}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _support_card(label: str, title: str, body: str, source: str) -> str:
    title_html = f"<div class='support-title'>{title}</div>" if title else ""
    return (
        f"<div class='support-card'>"
        f"<div class='support-label'>{label}</div>"
        f"{title_html}"
        f"<div class='support-body'>{body}</div>"
        f"<div class='support-cite'>— {source}</div>"
        f"</div>"
    )


def _supporting_affirmation(today: date) -> str:
    a = pick_affirmation(today)
    if a is None:
        return ""
    return _support_card(
        "❦ AFFIRMATION", "", f"<em>“{a.text}”</em>", a.source,
    )


def _supporting_faith(today: date) -> str:
    fv = pick_faith_verse(today)
    if fv is None:
        return ""
    return _support_card(
        "❦ FAITH VERSE", fv.verse_ref, _truncate(fv.summary, 220),
        fv.source or fv.verse_ref,
    )


def _supporting_inspiration(today: date) -> str:
    i = pick_inspiration(today)
    if i is None:
        return ""
    return _support_card(
        "❦ INSPIRATION", i.title, _truncate(i.text, 180), i.source,
    )


def _supporting_tip(today: date, today_value: str, is_eka: bool) -> str:
    t = pick_tip(value_ids=[today_value, "kirtan", "bhakti"], ekadasi=is_eka)
    if t is None:
        return ""
    return _support_card(
        "\U0001F4A1 TODAY'S TIP", "", _truncate(t.tip, 200), t.source or "",
    )


def _supporting_nama_tattva(today: date) -> str:
    nt = pick_nama_tattva(today)
    if nt is None:
        return ""
    return _support_card(
        "❦ NAMA-TATTVA", nt.title, _truncate(nt.teaching, 180), nt.source,
    )


def _render_book_tip(today: date) -> None:
    bt = pick_book_tip(today)
    if bt is None:
        return
    meta = f"— {bt.source}"
    if bt.addresses:
        meta += f"  ·  <em>addresses: {bt.addresses}</em>"
    st.markdown(
        f"<div class='book-tip'>"
        f"<div class='book-tip-label'>\U0001F4D6 FROM THE BOOK · DAILY PRACTICE</div>"
        f"<div class='book-tip-title'>{bt.title}</div>"
        f"<div class='book-tip-body'>{bt.instruction}</div>"
        f"<div class='book-tip-meta'>{meta}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


_FEATURED_DISPATCH = {
    0: ("affirmation", _render_featured_affirmation),
    1: ("faith", _render_featured_faith),
    2: ("inspiration", _render_featured_inspiration),
    3: ("tip", _render_featured_tip),
    4: ("nama_tattva", _render_featured_nama_tattva),
}


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    today = date.today()
    is_eka = is_ekadasi(today)
    today_value = pick_today_value(today)
    weekday = today.weekday()

    _render_meta(today, today_value, is_eka)

    # Featured card — Sat=Bhajan, Sun=Story, Mon-Fri=daily rotation
    if weekday == 5:
        _render_featured_bhajan(today)
        # Mon-Fri rotation slots all appear as supporting cards on Sat
        slots = {"affirmation", "faith", "inspiration", "tip", "nama_tattva"}
    elif weekday == 6:
        _render_featured_story(today)
        slots = {"affirmation", "faith", "inspiration", "tip", "nama_tattva"}
    else:
        featured_slot, featured_fn = _FEATURED_DISPATCH[weekday]
        if featured_slot == "tip":
            featured_fn(today, today_value, is_eka)
        else:
            featured_fn(today)
        slots = {"affirmation", "faith", "inspiration", "tip", "nama_tattva"} - {featured_slot}

    # Render supporting cards in order
    cards: list[str] = []
    if "affirmation" in slots:
        cards.append(_supporting_affirmation(today))
    if "faith" in slots:
        cards.append(_supporting_faith(today))
    if "inspiration" in slots:
        cards.append(_supporting_inspiration(today))
    if "tip" in slots:
        cards.append(_supporting_tip(today, today_value, is_eka))
    if "nama_tattva" in slots:
        cards.append(_supporting_nama_tattva(today))
    cards = [c for c in cards if c]

    # Layout cards in columns
    if len(cards) <= 4:
        cols = st.columns(len(cards), gap="small")
    else:
        cols = st.columns(len(cards), gap="small")
    for col, html in zip(cols, cards):
        with col:
            st.markdown(html, unsafe_allow_html=True)

    # Daily practical tip from the book — always present
    _render_book_tip(today)

    st.markdown(
        "<div class='footer-note'>Close this window when ready. The agent is silent during japa.</div>",
        unsafe_allow_html=True,
    )
