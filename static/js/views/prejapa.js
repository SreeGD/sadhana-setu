// Pre-japa view — featured card rotates by weekday; supporting grid + book tip + ekadasi.

import {
  todayAffirmation, todayFaithVerse, todayInspiration, todayTip,
  todayNamaTattva, todayBookTip, weekBhajan, weekStory,
  todayEkadasi, todayValue, todayVerse, todaySankalpa,
} from "../content.js";
import { el, formatDate, todayISO, formatTime, toast } from "../util.js";
import * as store from "../store.js";

function card(cls, label, title, body, cite) {
  const children = [el("div", { class: "card-label" }, label)];
  if (title) children.push(el("div", { class: "card-title" }, title));
  if (body) children.push(el("div", { class: "card-body" }, body));
  if (cite) children.push(el("div", { class: "card-cite" }, "— " + cite));
  return el("div", { class: cls }, ...children);
}

function affirmCard(entry) {
  return card("support-card", "AFFIRMATION", null, `"${entry.text}"`, entry.source);
}
function faithCard(entry) {
  return card("support-card", "FAITH VERSE", entry.verse_ref, entry.summary, entry.source);
}
function inspirationCard(entry) {
  return card("support-card", "INSPIRATION", entry.title, entry.text, entry.source);
}
function tipCard(entry) {
  return card("support-card", "TODAY'S TIP", null, entry.tip, entry.source);
}
function namaTattvaCard(entry) {
  return card("support-card", "NĀMA-TATTVA", entry.title, entry.teaching, entry.source);
}
function bhajanCard(entry) {
  const body = el("div", {},
    entry.verse_iast ? el("div", { class: "iast", html: entry.verse_iast.replace(/\n/g, "<br>") }) : null,
    entry.verse_translation ? el("p", {}, entry.verse_translation) : null,
  );
  return card("support-card", "BHAJAN", entry.title, "", `${entry.author} — ${entry.source}`)
    .appendChild(body), card("support-card", "BHAJAN", entry.title, entry.verse_translation || "", entry.author);
}
function storyCard(entry) {
  return card("support-card", "STORY", entry.title, entry.one_line, entry.scripture);
}

// Featured card big version
function featured(label, title, body, cite, extra) {
  const c = el("div", { class: "featured-card" },
    el("div", { class: "card-label" }, label),
    title ? el("div", { class: "card-title" }, title) : null,
    el("div", { class: "card-body" }, body),
    extra,
    cite ? el("div", { class: "card-cite" }, "— " + cite) : null,
  );
  return c;
}

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
    el("div", { class: "verse-body" },
      iast,
      translation,
      connection,
      el("div", { class: "card-cite" }, "— " + (verse.source || "")),
    ),
  );
}

export async function render(root) {
  const dow = new Date().getDay();   // Sun=0, Sat=6
  const [aff, faith, insp, tip, nt, book, bhajan, story, ekadasi, value, verse, sankalpa] = await Promise.all([
    todayAffirmation(), todayFaithVerse(), todayInspiration(), todayTip(),
    todayNamaTattva(), todayBookTip(), weekBhajan(), weekStory(),
    todayEkadasi(), todayValue(), todayVerse(), todaySankalpa(),
  ]);

  let featuredEl;
  const featuredOrder = ["AFFIRMATION", "FAITH VERSE", "INSPIRATION", "TIP", "NĀMA-TATTVA"];
  if (dow === 6) {
    // Saturday — bhajan. Show the FIRST verse here (full bhajan lives in This Week).
    const firstVerse = (bhajan.verses && bhajan.verses[0]) || null;
    const iastSrc = firstVerse?.iast || bhajan.verse_iast || "";
    const translation = firstVerse?.translation || bhajan.verse_translation || "";
    featuredEl = featured(
      "TODAY'S BHAJAN — verse 1 (full text in This Week)",
      bhajan.title,
      translation,
      `${bhajan.author} — ${bhajan.source}`,
      iastSrc ? el("div", { class: "iast", style: "color:#B8860B; font-style:italic; margin: 0.5rem 0 0.7rem;", html: iastSrc.replace(/\n/g, "<br>") }) : null
    );
  } else if (dow === 0) {
    // Sunday — story
    featuredEl = featured("TODAY'S STORY", story.title, story.text, story.scripture);
  } else {
    const lab = featuredOrder[dow - 1] || "INSPIRATION";
    if (lab === "AFFIRMATION") featuredEl = featured("TODAY'S AFFIRMATION", null, `"${aff.text}"`, aff.source);
    else if (lab === "FAITH VERSE") featuredEl = featured("TODAY'S FAITH VERSE", faith.verse_ref, faith.summary, faith.source);
    else if (lab === "INSPIRATION") featuredEl = featured("TODAY'S INSPIRATION", insp.title, insp.text, insp.source);
    else if (lab === "TIP") featuredEl = featured("TODAY'S TIP", null, tip.tip, tip.source);
    else featuredEl = featured("TODAY'S NĀMA-TATTVA", nt.title, nt.teaching, nt.source);
  }

  // Supporting grid — 4 entries that aren't already in the featured
  const featuredLabel = dow >= 1 && dow <= 5 ? featuredOrder[dow - 1] : null;
  const supportItems = [
    ["AFFIRMATION", affirmCard(aff)],
    ["FAITH VERSE", faithCard(faith)],
    ["INSPIRATION", inspirationCard(insp)],
    ["TIP", tipCard(tip)],
    ["NĀMA-TATTVA", namaTattvaCard(nt)],
  ].filter(([lab]) => lab !== featuredLabel).slice(0, 4).map(([, c]) => c);

  // Book tip + ekadasi at the bottom
  const bookCard = el("div", { class: "book-card" },
    el("div", { class: "card-label" }, "FROM THE BOOK · DAILY PRACTICE"),
    el("div", { class: "card-title" }, book.title),
    el("div", { class: "card-body" }, book.instruction),
    el("div", { class: "card-cite" }, "— " + book.source + (book.addresses ? `  ·  addresses: ${book.addresses}` : "")),
  );

  const ekadasiCard = ekadasi ? el("div", { class: "ekadasi-card" },
    el("div", { class: "card-label" }, "EKĀDAŚĪ TODAY"),
    el("div", { class: "card-title" }, ekadasi.name),
    el("div", { class: "card-body" }, "Fast from grains and beans. Increase chanting and hearing."),
  ) : null;

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" },
    formatDate(new Date()),
    " · value: ", el("strong", {}, value)
  ));
  if (verse) root.appendChild(buildVerseCard(verse));
  root.appendChild(featuredEl);
  root.appendChild(el("div", { class: "support-grid" }, ...supportItems));
  if (ekadasiCard) root.appendChild(ekadasiCard);
  root.appendChild(bookCard);
  root.appendChild(sankalpaCard(sankalpa));
  root.appendChild(el("div", { class: "meta-line" },
    el("em", {}, "Close this window when ready. The Name awaits."),
  ));
}

function sankalpaCard(sankalpa) {
  const date = todayISO();
  const existing = store.getSankalpa(date);

  const card = el("div", { class: "sankalpa-card" + (existing ? " made" : "") });

  function paint() {
    card.innerHTML = "";
    const cur = store.getSankalpa(date);
    const made = !!cur;
    card.classList.toggle("made", made);

    const labelPrefix = sankalpa?.anchor ? "SAṄKALPA · anchor" : "SAṄKALPA · before japa";
    const label = made
      ? `SAṄKALPA · ✓ made at ${formatTime(cur.made_at)}`
      : labelPrefix;
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
      undo.addEventListener("click", () => {
        store.clearSankalpa(date);
        paint();
        toast("Saṅkalpa cleared");
      });
      card.appendChild(el("div", { class: "sankalpa-action" },
        el("div", { class: "sankalpa-confirm" }, "Vow made. Now: just this mantra."),
        undo,
      ));
    } else {
      const btn = el("button", { class: "sankalpa-btn" }, "Make the vow for today");
      btn.addEventListener("click", () => {
        store.setSankalpa(date);
        paint();
        toast("Saṅkalpa made 🪷");
      });
      card.appendChild(btn);
    }
  }

  paint();
  return card;
}
