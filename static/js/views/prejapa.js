// Pre-japa view — v3 transformation arc (blend), parity with the Streamlit prejapa_view.
// (verse·optional) → orient → tip → deepen → story·optional → apply → saṅkalpa → enter japa.
// Reads in under two minutes; the verse and story are collapsible so they cost no budget.

import {
  todayAffirmation, todayFaithVerse, todayInspiration, todayTip,
  todayNamaTattva, todayBookTip, todayEkadasi, todayValue, todayVerse, todaySankalpa,
} from "../content.js";
import { el, formatDate, todayISO, formatTime, toast } from "../util.js";
import * as store from "../store.js";

// A prominent arc-stage card (orient / deepen / apply / enter).
function arcCard(label, bodyHtml, cite, title) {
  return el("div", { class: "featured-card" },
    el("div", { class: "card-label" }, label),
    title ? el("div", { class: "card-title" }, title) : null,
    el("div", { class: "card-body", html: bodyHtml }),
    cite ? el("div", { class: "card-cite" }, "— " + cite) : null,
  );
}

// Optional mood verse — collapsible (tap to read).
function buildVerseCard(verse) {
  const iast = verse.iast ? el("div", { class: "verse-iast", html: verse.iast.replace(/\n/g, "<br>") }) : null;
  const translation = verse.translation ? el("p", { class: "verse-translation" }, verse.translation) : null;
  const connection = verse.chanting_connection ? el("p", { class: "verse-connection" }, verse.chanting_connection) : null;
  return el("details", { class: "verse-card" },
    el("summary", { class: "verse-summary" },
      el("span", { class: "verse-label" }, "VERSE FOR MOOD"),
      el("span", { class: "verse-ref" }, verse.verse_ref || ""),
      verse.mood_brought ? el("span", { class: "verse-mood" }, "· " + verse.mood_brought) : null,
      el("span", { class: "verse-toggle" }, " — tap to read (optional)"),
    ),
    el("div", { class: "verse-body" }, iast, translation, connection,
      el("div", { class: "card-cite" }, "— " + (verse.source || "")),
    ),
  );
}

// Optional inspiration story — collapsible, reuses the verse-card styling.
function buildStoryCard(insp) {
  return el("details", { class: "verse-card" },
    el("summary", { class: "verse-summary" },
      el("span", { class: "verse-label" }, "A STORY TO CARRY IN"),
      el("span", { class: "verse-ref" }, insp.title || ""),
      el("span", { class: "verse-toggle" }, " — tap to read (optional)"),
    ),
    el("div", { class: "verse-body" },
      el("p", { class: "verse-translation" }, insp.text),
      el("div", { class: "card-cite" }, "— " + (insp.source || "")),
    ),
  );
}

export async function render(root) {
  const [aff, faith, insp, tip, nt, book, ekadasi, value, verse, sankalpa] = await Promise.all([
    todayAffirmation(), todayFaithVerse(), todayInspiration(), todayTip(),
    todayNamaTattva(), todayBookTip(), todayEkadasi(), todayValue(), todayVerse(), todaySankalpa(),
  ]);

  root.innerHTML = "";

  // Meta line (date · value · ekadasi badge)
  const meta = el("div", { class: "meta-line" },
    formatDate(new Date()), " · value: ", el("strong", {}, value));
  if (ekadasi) meta.appendChild(el("span", { class: "eka-badge" }, "🌿 " + ekadasi.name));
  root.appendChild(meta);

  // Mood verse — collapsible
  if (verse) root.appendChild(buildVerseCard(verse));

  // ORIENT — affirmation + the Name's promise
  const orientBody = `“${aff.text}”` +
    (faith ? `<span class="orient-faith">The Name promises: ${faith.summary}</span>` : "");
  root.appendChild(arcCard("ORIENT", orientBody, aff.source || (faith && faith.verse_ref)));

  // Today's tip — one practical line
  if (tip) root.appendChild(el("div", { class: "pj-tip" },
    el("span", { class: "pj-tip-label" }, "Today's tip"), tip.tip));

  // DEEPEN — a teaching on the Holy Name
  if (nt) root.appendChild(arcCard("A TEACHING ON THE HOLY NAME", nt.teaching, nt.source, nt.title));

  // Inspiration story — collapsible
  if (insp) root.appendChild(buildStoryCard(insp));

  // APPLY — a micro-practice to sit with, once
  if (book) root.appendChild(
    arcCard("SIT WITH THIS — ONCE, BEFORE YOU CHANT", book.instruction, book.source, book.title));

  // SAṄKALPA — today's vow + button
  root.appendChild(sankalpaCard(sankalpa));

  // ENTER japa
  root.appendChild(arcCard("ENTER JAPA",
    "Now enter your japa — chant to hear each Name, taking shelter, more humble than a blade of " +
    `grass. Carry today's orientation in: “${aff.text}”`, null));

  root.appendChild(el("div", { class: "meta-line" },
    el("em", {}, "Close this window when ready. The Name awaits.")));
}

function sankalpaCard(sankalpa) {
  const date = todayISO();
  const card = el("div", { class: "sankalpa-card" });

  function paint() {
    card.innerHTML = "";
    const cur = store.getSankalpa(date);
    const made = !!cur;
    card.classList.toggle("made", made);

    const labelPrefix = sankalpa?.anchor ? "SAṄKALPA · anchor" : "SAṄKALPA · before japa";
    const label = made ? `SAṄKALPA · ✓ made at ${formatTime(cur.made_at)}` : labelPrefix;
    card.appendChild(el("div", { class: "card-label" }, label));

    const vowText = sankalpa?.text || "I will try to hear THIS mantra.";
    const vowBody = vowText.replace(/\b([A-Z]{2,})\b/g, "<strong>$1</strong>");
    card.appendChild(el("div", {
      class: "sankalpa-vow",
      html: `<span class="quote-mark">“</span>${vowBody}<span class="quote-mark">”</span>`,
    }));
    card.appendChild(el("div", { class: "card-cite" }, "— " + (sankalpa?.source || "HG Bhurijana Prabhu · Melbourne, 2006")));

    if (made) {
      const undo = el("button", { class: "sankalpa-undo" }, "Undo");
      undo.addEventListener("click", () => { store.clearSankalpa(date); paint(); toast("Saṅkalpa cleared"); });
      card.appendChild(el("div", { class: "sankalpa-action" },
        el("div", { class: "sankalpa-confirm" }, "Vow made. Now: just this mantra."), undo));
    } else {
      const btn = el("button", { class: "sankalpa-btn" }, "Make the vow for today");
      btn.addEventListener("click", () => { store.setSankalpa(date); paint(); toast("Saṅkalpa made 🪷"); });
      card.appendChild(btn);
    }
  }

  paint();
  return card;
}
