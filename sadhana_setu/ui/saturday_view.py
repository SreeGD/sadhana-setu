"""Saturday check-in view — Observe + Set (T-016, T-017, T-018).

Single-page form with both halves visible. Saturday-aware (shows a notice
on other weekdays but renders anyway, for previewing).
"""
from datetime import date, datetime, timedelta

import streamlit as st

from sadhana_setu.content.questions import (
    all_questions,
    mark_asked,
    pick_questions,
    seed_db,
)
from sadhana_setu.flows.saturday import (
    WeeklyCheckin,
    WeekSummary,
    get_checkin,
    most_recent_saturday,
    save_checkin,
    week_at_a_glance,
)
from sadhana_setu.patterns.audit import log_pattern
from sadhana_setu.patterns.engine import PatternResult, surface_for_saturday

BHAVA_SUGGESTIONS = [
    "tṛṇād api sunīcena — humbler than a blade of grass",
    "dāsya — servitorship",
    "kṛtajñatā — gratitude",
    "śaraṇāgati — surrender",
    "smaranam — constant remembrance",
    "ātma-nivedanam — offering of the self",
]


@st.cache_resource
def _ensure_seeded() -> bool:
    seed_db()
    return True


def _render_corpus_teaching(existing) -> None:
    """Optional, additive: a reviewed corpus teaching themed by the week's sankalpa (FR-008/014).

    Purely additive — absent (not curated-replaced) when there is no match.
    """
    from sadhana_setu.flows import corpus_teaching
    from sadhana_setu.flows.today_value import pick_today_value

    bits = [getattr(existing, "tone", ""), getattr(existing, "mood_bhava", "")] if existing else []
    theme = " ".join(b for b in bits if b).strip() or pick_today_value(date.today())
    state = st.session_state.setdefault(
        f"corpus_{date.today().isoformat()}", corpus_teaching.new_state())
    t = corpus_teaching.get_for_surface(theme, "saturday", date=date.today(), state=state)
    if t is None:
        return
    st.markdown(f"> **A teaching to sit with this week** — {t.body}\n>\n> — *{t.citation}*")


def _render_week(summary: WeekSummary) -> None:
    cols = st.columns(7)
    for i, (d, count) in enumerate(summary.days):
        with cols[i]:
            day_label = d.strftime("%a")
            date_label = d.strftime("%-m/%-d")
            if count is None:
                badge, color = "—", "#888"
            elif count >= 16:
                badge, color = str(count), "#3a3"
            else:
                badge, color = str(count), "#c80"
            st.markdown(
                f"<div style='text-align:center; padding:8px; border:1px solid #555; "
                f"border-radius:4px;'><small>{day_label}<br>{date_label}</small><br>"
                f"<strong style='color:{color}; font-size:1.4em;'>{badge}</strong></div>",
                unsafe_allow_html=True,
            )
    st.caption(
        f"{summary.rounds_completed_days}/7 days at vow (≥16); "
        f"{summary.total_rounds} rounds total; "
        f"{summary.hearing_note_count} hearing notes."
    )


def render() -> None:
    _ensure_seeded()
    today = date.today()
    saturday = most_recent_saturday(today)
    week_start = saturday - timedelta(days=6)

    st.header("Saturday Check-in")
    st.caption(
        f"Week of {week_start.strftime('%B %d')} — {saturday.strftime('%B %d, %Y')}"
    )

    if today.weekday() != 5:
        days_to_sat = (5 - today.weekday()) % 7 or 7
        next_sat = today + timedelta(days=days_to_sat)
        st.info(
            f"Today is {today.strftime('%A')}. The check-in is meant for Saturday "
            f"(next: {next_sat.strftime('%a %b %d')}). You can preview / edit any time."
        )

    summary = week_at_a_glance(saturday)
    existing = get_checkin(saturday)

    st.markdown("### Half 1 — Observe (the week past)")
    _render_week(summary)
    _render_corpus_teaching(existing)

    st.markdown("**Pattern this week**")
    pattern = surface_for_saturday(saturday)
    if pattern.fired:
        st.success(pattern.headline)
        if pattern.detail:
            st.caption(pattern.detail)
    else:
        st.info(pattern.headline)
        if pattern.detail:
            st.caption(pattern.detail)

    qkey = f"sat-questions-{saturday.isoformat()}"
    if qkey not in st.session_state:
        if existing and existing.survey_answers:
            lookup = {q.id: q for q in all_questions()}
            picked = [
                lookup[a["question_id"]]
                for a in existing.survey_answers
                if a.get("question_id") in lookup
            ]
            st.session_state[qkey] = picked or pick_questions(3)
        else:
            st.session_state[qkey] = pick_questions(3)
    questions = st.session_state[qkey]

    prior_answers = {
        a["question_id"]: a.get("answer", "")
        for a in (existing.survey_answers if existing else [])
    }

    with st.expander("Bhava suggestions from sastra (for the Mood field below)"):
        for s in BHAVA_SUGGESTIONS:
            st.markdown(f"- {s}")

    with st.form("saturday_form"):
        st.markdown("**This week's questions**")
        answers: dict[int, tuple[str, str]] = {}
        for q in questions:
            route = (
                f"  •  *routes through {q.routes_through}*"
                if q.routes_through
                else ""
            )
            st.markdown(f"**Q{q.id}.**{route}")
            st.markdown(q.question)
            answers[q.id] = (
                q.question,
                st.text_area(
                    "Answer",
                    value=prior_answers.get(q.id, ""),
                    key=f"qa-{saturday.isoformat()}-{q.id}",
                    height=80,
                    label_visibility="collapsed",
                    placeholder="(short response, or leave empty)",
                ),
            )

        st.divider()
        st.markdown("### Half 2 — Set the coming week")

        tone = st.text_input(
            "**Tone** — the orientation of the coming week",
            value=existing.tone if existing else "",
            placeholder="e.g., Returning to early rising",
        )
        bhava = st.text_input(
            "**Mood (bhava)** — the devotional disposition",
            value=existing.mood_bhava if existing else "",
            placeholder="e.g., trnad api sunicena, or your own",
        )
        practices_text = st.text_area(
            "**Practices** (one per line) — concrete acts for the coming week",
            value="\n".join(existing.practices) if existing else "",
            height=100,
        )
        tools_text = st.text_area(
            "**Tools needed** (one per line) — physical or digital",
            value="\n".join(existing.tools_needed) if existing else "",
            height=80,
        )
        priorities_text = st.text_area(
            "**Priorities** (one per line; top first) — when not everything fits",
            value="\n".join(existing.priorities) if existing else "",
            height=80,
        )

        submitted = st.form_submit_button(
            "Save check-in", type="primary", use_container_width=True
        )

    if submitted:
        survey_answers = []
        for qid, (qtext, ans) in answers.items():
            survey_answers.append(
                {"question_id": qid, "question": qtext, "answer": ans.strip()}
            )
            if ans.strip():
                mark_asked(qid, datetime.now().isoformat(timespec="seconds"))

        practices = [
            line.strip() for line in practices_text.splitlines() if line.strip()
        ]
        tools = [line.strip() for line in tools_text.splitlines() if line.strip()]
        priorities = [
            line.strip() for line in priorities_text.splitlines() if line.strip()
        ]

        checkin = WeeklyCheckin(
            week_start=saturday.isoformat(),
            survey_answers=survey_answers,
            tone=tone.strip(),
            mood_bhava=bhava.strip(),
            practices=practices,
            priorities=priorities,
            tools_needed=tools,
            surfaced_pattern=pattern.headline if pattern.fired else None,
            submitted_at=datetime.now().isoformat(timespec="seconds"),
        )
        save_checkin(checkin)
        log_pattern(saturday, pattern)

        from sadhana_setu import sync as _sync
        from sadhana_setu.ui import sync_sidebar as _sb
        creds = _sb.get_active_credentials()
        if creds is not None:
            try:
                _sync.push(creds)
                st.success(
                    f"Check-in saved for week ending {saturday.isoformat()} · "
                    "synced to Google Drive."
                )
            except Exception as e:  # noqa: BLE001
                st.success(f"Check-in saved for week ending {saturday.isoformat()}.")
                st.warning(f"Sync skipped: {e}")
        else:
            st.success(f"Check-in saved for week ending {saturday.isoformat()}.")
        st.rerun()

    if existing:
        st.caption(f"Last saved: {existing.submitted_at}. Save again to update.")
