// This Week view — week-at-a-glance + verse + reading + bhajan + japa
// method + lecture + story. Weekly rotation by ISO week.

import {
  weekReading, weekJapaMethod, weekStory,
  weekVerse, weekBhajan, weekLecture,
} from "../content.js";
import {
  mostRecentSaturday, addDays, el, formatDate
} from "../util.js";
import * as store from "../store.js";

function weekDots(saturdayDate) {
  const days = [];
  for (let i = 6; i >= 0; i--) days.push(addDays(saturdayDate, -i));
  const grid = el("div", { class: "week-dots" });
  for (const d of days) {
    const iso = d.toISOString().slice(0, 10);
    const r = store.getRounds(iso);
    const count = r?.count || 0;
    const completion = r?.completion;
    let cls = "empty";
    let badge = "—";
    if (completion) {
      cls = "win-" + completion;
      badge = "🪷";
    } else if (count >= 16) {
      cls = "complete";
      badge = String(count);
    } else if (count > 0) {
      cls = "partial";
      badge = String(count);
    }
    grid.appendChild(el("div", { class: `day ${cls}` },
      el("div", { class: "label" }, d.toLocaleDateString(undefined, { weekday: "short" })),
      el("div", { class: "count" }, badge),
    ));
  }
  return grid;
}

function verseCard(v) {
  return el("div", { class: "view-card weekly-verse-card" },
    el("div", { class: "card-label" }, `WEEKLY VERSE · ${v.source_label}`),
    el("h3", {}, v.verse_ref),
    v.iast ? el("div", { class: "verse-iast", html: v.iast.replace(/\n/g, "<br>") }) : null,
    v.translation ? el("p", { class: "verse-translation" }, v.translation) : null,
    v.essence ? el("p", { style: "font-style:italic; color:var(--ink-soft);" },
      el("strong", {}, "Essence: "), v.essence) : null,
    v.chanting_application ? el("p", { class: "verse-connection" },
      el("strong", {}, "This week, carry into japa: "),
      v.chanting_application) : null,
    el("p", { class: "card-cite" }, "— " + (v.source || "")),
  );
}

function bhajanCard(b) {
  return el("div", { class: "view-card weekly-bhajan-card" },
    el("div", { class: "card-label" }, "WEEKLY BHAJAN"),
    el("h3", {}, b.title),
    el("p", { style: "color:var(--muted); margin-top:-0.3rem;" }, "by " + (b.author || "")),
    b.verse_iast ? el("div", { class: "verse-iast", html: b.verse_iast.replace(/\n/g, "<br>") }) : null,
    b.verse_translation ? el("p", {}, b.verse_translation) : null,
    el("p", { class: "card-cite" }, "— " + (b.source || "")),
  );
}

function lectureCard(l) {
  const listenBtn = el("a", {
    href: l.search_url || "https://audio.iskcondesiretree.com/",
    target: "_blank",
    rel: "noopener",
    class: "lecture-listen",
  }, "Listen on audio.iskcondesiretree.com →");

  return el("div", { class: "view-card weekly-lecture-card" },
    el("div", { class: "card-label" }, "WEEKLY LECTURE · audio.iskcondesiretree.com"),
    el("h3", {}, l.title),
    el("p", { style: "color:var(--muted); margin-top:-0.3rem;" },
      "by " + (l.speaker || ""),
      l.series ? "  ·  " + l.series : "",
      l.duration ? "  ·  " + l.duration : "",
    ),
    l.why_it_helps_chanting ? el("p", { style: "white-space: pre-wrap;" }, l.why_it_helps_chanting) : null,
    el("div", { style: "margin-top: 0.6rem;" }, listenBtn),
    el("p", { class: "card-cite" }, "— " + (l.source || "ISKCON Desire Tree Audio Archive")),
  );
}

export async function render(root) {
  const [reading, method, story, verse, bhajan, lecture] = await Promise.all([
    weekReading(), weekJapaMethod(), weekStory(),
    weekVerse(), weekBhajan(), weekLecture(),
  ]);

  const sat = mostRecentSaturday();
  const weekStart = addDays(sat, -6);

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" },
    "Week of ", formatDate(weekStart), " — ", formatDate(sat)
  ));

  // 1. Week at a glance
  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Week at a glance"),
    weekDots(sat),
  ));

  // 2. Weekly verse
  if (verse) root.appendChild(verseCard(verse));

  // 3. Weekly reading (longer essay)
  root.appendChild(el("div", { class: "view-card" },
    el("div", { class: "card-label" }, "WEEKLY READING · " + (reading.reading_minutes || "?") + " min"),
    el("h3", {}, reading.title),
    reading.subtitle ? el("p", { style: "color:var(--muted); margin-top:-0.3rem;" }, reading.subtitle) : null,
    el("p", { style: "white-space: pre-wrap;" }, reading.content),
    el("p", { class: "card-cite" }, "— " + reading.source),
  ));

  // 4. Weekly bhajan
  if (bhajan) root.appendChild(bhajanCard(bhajan));

  // 5. Japa method
  root.appendChild(el("div", { class: "view-card" },
    el("div", { class: "card-label" }, "JAPA METHOD · " + (method.duration_minutes || "?") + " min"),
    el("h3", {}, method.name),
    el("p", { style: "color:var(--muted); margin-top:-0.3rem;" }, "by " + method.teacher),
    el("p", { style: "font-style: italic;" }, method.one_line),
    el("p", {}, method.overview),
    method.steps && method.steps.length
      ? el("ol", {}, ...method.steps.map(s =>
          typeof s === "string"
            ? el("li", {}, s)
            : el("li", {},
                el("strong", {}, s.title || ""),
                s.practice ? el("div", { style: "margin: 0.2rem 0 0.6rem;" }, s.practice) : null,
              )
        ))
      : null,
    method.closing ? el("p", {}, el("strong", {}, "Closing: "), method.closing) : null,
    el("p", { class: "card-cite" }, "— " + method.source),
  ));

  // 6. Weekly lecture
  if (lecture) root.appendChild(lectureCard(lecture));

  // 7. Weekly story
  root.appendChild(el("div", { class: "view-card" },
    el("div", { class: "card-label" }, "WEEKLY STORY"),
    el("h3", {}, story.title),
    el("p", { style: "color:var(--muted); margin-top:-0.3rem;" }, story.devotee + " — " + story.one_line),
    el("p", { style: "white-space: pre-wrap;" }, story.text),
    story.key_verse ? el("p", { style: "background:#FFF8E8; padding:0.6rem 0.8rem; border-left:3px solid var(--gold);" },
      el("strong", {}, story.key_verse),
      story.scripture ? " — " + story.scripture : ""
    ) : null,
    story.teaching ? el("p", { style: "font-style:italic; color:var(--ink-soft);" }, story.teaching) : null,
  ));
}
