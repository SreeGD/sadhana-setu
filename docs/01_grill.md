# Phase 1 — Grill

> Output of Phase 1 of the seven-phase agentic project process (Grill → Research → Prototype → PRD → Issues → Implement → Review). The job of this phase was to take a broad family-dharma-agent vision and cut it down to a single seed product worth building first.

## The seed product

A **japa-and-hearing sadhana companion** for one user (and later, the family).

It serves a Gaudiya Vaishnava (ISKCON) practitioner who has an aspirational daily rhythm but inconsistent execution. Version 1 supports the **inner loop of bhakti sadhana**: the mutually reinforcing cycle between hearing (*sravanam* — Srimad Bhagavatam, Bhagavad Gita, Caitanya Caritamrta and their purports) and chanting (*kirtanam* — 16 rounds of the Hare Krishna mahamantra daily).

The product's north star is the user's stated aspiration: *live in harmony, leave the earth in harmony.* Version 1 expresses that operationally as **alignment between vow (sankalpa) and act, deepened through the quality of chanting and hearing.**

## What japa means in this product (load-bearing)

Japa is **not a habit, a task, or a productivity metric.** Every behavior in this product must reflect the following:

- **Direct service to Krishna through His holy names.** The Name and Krishna are non-different (CC Madhya 17.133).
- **The yuga-dharma for Kali-yuga** (SB 12.3.51–52). Both means and end of bhakti; chanting itself develops *bhava* leading to *prema*.
- **Quality matters as much as count.** Sixteen mechanical rounds are not the goal. Sixteen *attentive* rounds — hearing each syllable, free from the ten offenses (*nama-aparadha*), in the mood of *Siksastakam* verse 3 (*trnad api sunicena*) — is.
- **The chanter does the work.** The agent does not chant for the user, does not gamify, does not interrupt. It prepares the ground before, holds silence during, and helps the chanter reflect honestly after.

## The hearing↔chanting loop

These are not two features. They are one loop:

1. **Hearing** (SB / BG / CC class, reading purports) fills the heart with Krishna remembrance.
2. The heart so filled **chants** with more attention; the Name absorbs more deeply.
3. **Chanting** purifies consciousness; the next hearing penetrates further.
4. Return to 1.

The product's primary job in v1 is to help this loop happen daily, then to make the loop visible to the practitioner so it can deepen over time.

## First user

- **The user himself**: 52, ISKCON-initiated householder, working professional, residing where temple attendance is feasible.
- **Family-mode is Phase 2 of the product** (not Phase 2 of this process). Wife Radhi (43), daughter Anvi (3rd-year medical student in India), son Advi (just completed 12th), father (80, remote village), three farm workers — all in his care, none served by v1.

## Cadence: weekly-primary, daily-minimal

The product's primary cadence is **weekly**, not daily. Daily activity is intentionally minimal so reflection never competes with practice. The week — not the day — is the planning unit for a householder, and it matches the existing Vaishnava rhythm (Sunday program, weekly sastra study).

### Daily (minimal)

- **Pre-japa (very small, text-only on screen):** One or two short quotes from sastra (Prabhupada's purports, Siksastakam, BG, SB, CC, NOI, NOD) + a practical tip for today's chanting. Read in under a minute, glanced at — not narrated aloud. Examples of tips: *"Focus on hearing the syllable 'Krishna' clearly in every round." / "If your mind wanders, gently return to the Name without self-criticism." / "Today is Ekadasi — try to complete japa before noon if possible." / "Sit facing east, in the mood of trnad api sunicena."* Quotes are always paired with a tip, not standalone.
- A lightweight rounds capture — a tap, a voice line, a glance. The agent does **not** ask. The chanter logs if and when they want.
- Optional: one line worth remembering from today's hearing (SB / BG / CC).
- No surveys, no reflection prompts during the day.

### Weekly check-in (the primary ritual) — Saturday

A ~10-minute sit-down on **Saturday** (Sunday belongs to the temple's Sunday program; Saturday lets the chanter enter Sunday with the week already framed). Two halves: **Observe** the week past, then **Set** the week to come.

**Half 1 — Observe (the week past):**

- A short rotating survey, 2–3 questions drawn from a curated sastra-rooted library, varied weekly. Mix of direct and indirect. Examples:
  - *"Which day this week did the Holy Name feel closest? Which day felt furthest?"*
  - *"Which verse from this week's SB class stayed with you?"*
  - *"Read Siksastakam verse 3. Which line spoke to your week?"*
  - *"Was there a moment of attentive chanting you remember?"*
  - *"Did any of the ten offenses surface that you want to name?"*
- **One quiet pattern observation from the agent** — a single surfaced pattern, no more. ("Days you completed rounds correlated with sleeping by 10:45 PM the night before." / "On days you finished japa by 7 AM, you noted the SB class felt different.") The agent surfaces *one*; the chanter decides if it matters.

**Half 2 — Set (the week to come):**

- **Tone** — the orientation of the coming week. ("This week is about returning to early rising." / "This week is about deeper hearing.")
- **Mood (bhava)** — the devotional disposition the chanter wants to carry into the week. Not flavoring — substance. ("Approach japa as a servant." / "In the mood of *trnad api sunicena*." / "With gratitude for the Holy Name appearing on the tongue at all.") Sourced or chosen from Vaishnava tradition.
- **Practices** — the concrete acts that express the tone and mood. ("Begin japa before 4:45 AM most days." / "Read one chapter of CC." / "Finish japa before mangala aarti, not at it.") Anchored in the known shape of the coming week (travel, ekadasi, festival, office crunch, family event).
  - **Tools needed for the practices** — what would remove an obstacle this week? (Better japa bag, printed BG for travel, quieter chanting corner, counter ring, CC volume on the shelf.) The agent helps track and acquire; the agent itself can be a tool for some.
- **Priorities** — when not everything fits, what ranks first? The chanter sets the order. The agent remembers it so next Saturday's review knows what to look at.

### Why weekly-primary

- Removes daily friction. Reflection no longer competes with the sadhana arc itself.
- The weekly check-in becomes something to *look forward to*, not a chore.
- Goals and tools land at the right cadence — the householder's natural planning unit.
- Aligned with existing Vaishnava weekly rhythms.

## Ranked focus (user's own ranking)

| Rank | Element | Treatment in v1 |
|---|---|---|
| 1 | 16 rounds of japa (quality first) | **Primary** — quality + count, in the loop with hearing |
| 2 | Daily hearing of SB / BG / CC | **Primary** — the other half of the loop |
| 3 | Mangala aarti at temple | Tertiary thread (light touch) |
| 4 | Yoga 5–6 PM | Observed context |
| 5 | Sleep by 10:45 PM | Observed context |
| 6 | Wake at 3:30 AM | Observed context |

Ranks 4–6 are deliberately *not* features. They are signals that explain why ranks 1–2 happened or didn't.

## What v1 actually does (provisional shape)

**Daily (background, minimal):**
- Pre-japa: 1–2 short sastra quotes + a practical tip for today's chanting. Under a minute.
- One-tap or one-line rounds capture. No prompts.
- One-line "what stayed with me" from today's hearing, if the chanter wants. Optional.
- Silent *during* japa. No screen during the act. No notifications in protected hours.

**Weekly (the primary ritual) — Saturday:**
- **Observe**: rotating sastra-rooted survey (2–3 questions) + one pattern observation from the agent.
- **Set the coming week**: tone, mood (bhava), practices (and tools needed), priorities. Sankalpa-setting, not task management.

**For hearing (across the week):**
- The day's SB class / BG chapter / CC reading is surfaceable on demand.
- One line worth remembering can be captured and surfaces in the weekly check-in.

**Library asset:**
- A curated set of weekly check-in questions, all routed through Prabhupada's books or directly from Siksastakam, BG, SB, CC, NOI, NOD. No generic introspection prompts.

## What is explicitly NOT in v1

Each is a real future product and will deserve its own Grill phase later. Bundling them now would dilute the seed.

- Multi-user / family sharing
- Theological Q&A or scripture chatbot
- Health / Ayurveda tracking
- Document storage, household memory, "where are the keys"
- Yoga or fitness coaching
- Anything that quantifies, scores, or judges the *quality* of japa on the chanter's behalf
- Notifications during sadhana windows (3:30 AM – 9:30 AM) — categorically excluded
- Notifications during office block (8:30 PM – 10:30 PM)
- Cloud-only or surveillance-style design

## Constraints carried forward

- **Tradition:** ISKCON / Gaudiya Vaishnava. Srila Prabhupada's books are the default reference frame, with later acaryas as supporting commentary. Not generic pan-Hindu or comparative-religion sources.
- **Theological correctness:** No LLM-fabricated sloka, no paraphrased "essence of" content. Citations required. When uncertain, the agent says so or asks the chanter rather than inventing.
- **Sattvic medium:** No engagement loops, no streaks-and-badges, no addiction-pattern notifications, no advertising, calm-by-default UX.
- **Privacy:** Personal sadhana data is sacred. Local-first or family-owned hosting strongly preferred.
- **Time:** The product must live inside existing time blocks. It cannot demand new time.
- **Interaction during japa:** Cannot require looking at a screen. The agent is absent during the act itself.
- **Quiet hours:** Protect 3:30 AM – 9:30 AM (sadhana) and 8:30 PM – 10:30 PM (office).
- **Family edge (for Phase 2):** Father (80) in a remote village — family-mode features must not assume smartphone fluency at every node.

## Open questions for Phase 2 (Research)

1. **Source corpus.** Which Prabhupada books are essential for v1? (Likely: SB with purports, BG As It Is with purports, CC, Nectar of Instruction, Nectar of Devotion, Siksastakam.) Licensing / access (BBT, Vedabase API)?
2. **Existing ISKCON japa apps** — Krishna Connect, Murari Counter, Sankirtan Counter, Japa Beads. What do they do, what do they miss, what's worth not duplicating?
3. **Voice-first stack** — what's the simplest private way to capture a one-line daily note and a 10-minute weekly check-in, transcribed locally, stored on the user's own device?
4. **Weekly question library.** How is a library of ~30–50 sastra-rooted weekly check-in questions curated, where do they live, and how is the rotation chosen (random, theme-of-the-week, follow-up to last week)?
4a. **Pre-japa quote-and-tip library.** How is a library of paired sastra quotes + practical tips curated, where do they live, and how is the day's pairing chosen (random, theme, ekadasi-aware, festival-aware, follows from yesterday's hearing)?
5. **Tone / mood / practices / priorities framing.** What's the right format to capture sankalpa-for-the-week without it becoming task-management? Mood (bhava) is the hardest — how is it captured so it remains substance, not a dropdown? How are tools (physical or digital) tracked?
6. **Pattern surfacing.** What signals are honestly worth showing each week? (Sleep-before-rounds-completed, hearing-before-japa, ekadasi effect, weekday pattern.) What's the floor for "we have a pattern" vs. "it's noise"?
7. **Family-mode primitives.** Minimum data shapes that allow Phase 2 family extension without requiring v1 rework.

## Veto checkpoint

If anything above misreads the user's intent, redirect before opening Phase 2.

---

**Status:** Phase 1 **CLOSED** 2026-06-01. Ready to open Phase 2 (Research).
**Date:** 2026-06-01
