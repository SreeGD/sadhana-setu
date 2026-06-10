// This Week view — week-at-a-glance + verse + reading + bhajan + japa
// method + lecture + story. Weekly rotation by ISO week.

import {
  weekReading, weekJapaMethod, weekStory,
  weekVerse, weekBhajan, weekLecture,
} from "../content.js";
import {
  upcomingSaturday, addDays, el, formatDate, collapse
} from "../util.js";
import { weekDots } from "../week_summary.js";

function verseCard(v) {
  const det = collapse("weekly_verse",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, `WEEKLY VERSE · ${v.source_label}`),
      el("h3", {}, v.verse_ref),
    ),
    v.iast ? el("div", { class: "verse-iast", html: v.iast.replace(/\n/g, "<br>") }) : null,
    v.translation ? el("p", { class: "verse-translation" }, v.translation) : null,
    v.essence ? el("p", { style: "font-style:italic; color:var(--ink-soft);" },
      el("strong", {}, "Essence: "), v.essence) : null,
    v.chanting_application ? el("p", { class: "verse-connection" },
      el("strong", {}, "This week, carry into japa: "),
      v.chanting_application) : null,
    el("p", { class: "card-cite" }, "— " + (v.source || "")),
  );
  det.classList.add("weekly-verse-card");
  return det;
}

function bhajanCard(b) {
  const verseEls = [];
  if (b.refrain) {
    verseEls.push(el("div", { class: "bhajan-refrain" },
      el("div", { class: "bhajan-verse-label" }, "REFRAIN"),
      el("div", { class: "verse-iast", html: b.refrain.replace(/\n/g, "<br>") }),
    ));
  }
  if (Array.isArray(b.verses) && b.verses.length) {
    for (const v of b.verses) {
      verseEls.push(el("div", { class: "bhajan-verse" },
        el("div", { class: "bhajan-verse-label" }, "Verse " + (v.label || "")),
        v.iast ? el("div", { class: "verse-iast", html: v.iast.replace(/\n/g, "<br>") }) : null,
        v.translation ? el("p", { class: "bhajan-translation" }, v.translation) : null,
      ));
    }
  } else if (b.verse_iast) {
    // Backwards-compat for the older single-verse shape.
    verseEls.push(el("div", { class: "verse-iast", html: b.verse_iast.replace(/\n/g, "<br>") }));
    if (b.verse_translation) verseEls.push(el("p", {}, b.verse_translation));
  }

  // Audio block — embed player if audio_url present, else browse link
  const audioEls = [];
  if (b.audio_url) {
    audioEls.push(el("div", { class: "bhajan-audio-label" },
      "🎧 " + (b.audio_speaker || "Recording") + " — audio.iskcondesiretree.com"
    ));
    audioEls.push(el("audio", {
      controls: "",
      preload: "none",
      src: b.audio_url,
      style: "width: 100%;",
    }));
    if (b.audio_note) {
      audioEls.push(el("p", { class: "bhajan-audio-note" }, b.audio_note));
    }
    audioEls.push(el("p", { style: "font-size: 0.8rem; color: var(--muted); margin: 0.2rem 0 0;" },
      "If the player doesn't appear, ",
      el("a", { href: b.audio_url, target: "_blank", rel: "noopener", style: "color: var(--ink-soft);" }, "open the MP3 directly →")
    ));
  } else if (b.audio_folder_url) {
    audioEls.push(el("a", {
      href: b.audio_folder_url,
      target: "_blank",
      rel: "noopener",
      class: "bhajan-browse",
    }, "🎧 Browse recordings on audio.iskcondesiretree.com →"));
    if (b.audio_note) {
      audioEls.push(el("p", { class: "bhajan-audio-note" }, b.audio_note));
    }
  }

  const det = collapse("weekly_bhajan",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, "WEEKLY BHAJAN"),
      el("h3", {}, b.title),
      el("p", { class: "summary-byline", style: "color:var(--muted);" }, "by " + (b.author || "")),
    ),
    b.chanting_mood ? el("p", { style: "font-style:italic; color:var(--ink-soft);" },
      el("strong", {}, "Mood: "), b.chanting_mood) : null,
    b.meditation_for_japa ? el("p", { class: "verse-connection" },
      el("strong", {}, "For today's japa: "), b.meditation_for_japa) : null,
    audioEls.length ? el("div", { class: "bhajan-audio" }, ...audioEls) : null,
    el("div", { class: "bhajan-verses" }, ...verseEls),
    el("p", { class: "card-cite" }, "— " + (b.source || "")),
  );
  det.classList.add("weekly-bhajan-card");
  return det;
}

function lectureCard(l) {
  const audioEl = l.mp3_url ? el("audio", {
    controls: "",
    preload: "none",
    src: l.mp3_url,
    style: "width: 100%; margin: 0.6rem 0;",
  }) : null;

  const browseUrl = l.folder_url || l.search_url || "https://audio.iskcondesiretree.com/";
  const browseBtn = el("a", {
    href: browseUrl,
    target: "_blank",
    rel: "noopener",
    class: "lecture-listen",
  }, l.mp3_url ? "Browse more from this speaker →" : "Browse archive →");

  const det = collapse("weekly_lecture",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, "WEEKLY LECTURE · audio.iskcondesiretree.com"),
      el("h3", {}, l.title),
      el("p", { class: "summary-byline", style: "color:var(--muted);" },
        "by " + (l.speaker || ""),
        l.duration ? "  ·  " + l.duration : "",
      ),
    ),
    l.series ? el("p", { style: "color:var(--muted); font-style:italic; margin: 0 0 0.4rem;" }, l.series) : null,
    l.why_it_helps_chanting ? el("p", { style: "white-space: pre-wrap;" }, l.why_it_helps_chanting) : null,
    audioEl,
    l.mp3_url ? el("p", { style: "color: var(--muted); font-size: 0.8rem; margin: 0.2rem 0 0.5rem;" },
      "If the player doesn't appear, ",
      el("a", { href: l.mp3_url, target: "_blank", rel: "noopener", style: "color: var(--ink-soft);" }, "open the MP3 directly →")
    ) : null,
    el("div", { style: "margin-top: 0.6rem;" }, browseBtn),
    el("p", { class: "card-cite" }, "— " + (l.source || "ISKCON Desire Tree Audio Archive")),
  );
  det.classList.add("weekly-lecture-card");
  return det;
}

export async function render(root) {
  const [reading, method, story, verse, bhajan, lecture] = await Promise.all([
    weekReading(), weekJapaMethod(), weekStory(),
    weekVerse(), weekBhajan(), weekLecture(),
  ]);

  const sat = upcomingSaturday();   // Saturday of the calendar week containing today
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
  root.appendChild(collapse("weekly_reading",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, "WEEKLY READING · " + (reading.reading_minutes || "?") + " min"),
      el("h3", {}, reading.title),
      reading.subtitle ? el("p", { class: "summary-byline", style: "color:var(--muted);" }, reading.subtitle) : null,
    ),
    el("p", { style: "white-space: pre-wrap;" }, reading.content),
    el("p", { class: "card-cite" }, "— " + reading.source),
  ));

  // 4. Weekly bhajan
  if (bhajan) root.appendChild(bhajanCard(bhajan));

  // 5. Japa method
  root.appendChild(collapse("japa_method",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, "JAPA METHOD · " + (method.duration_minutes || "?") + " min"),
      el("h3", {}, method.name),
      el("p", { class: "summary-byline", style: "color:var(--muted);" }, "by " + method.teacher),
    ),
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
  root.appendChild(collapse("weekly_story",
    el("summary", { class: "view-card-summary" },
      el("div", { class: "card-label" }, "WEEKLY STORY"),
      el("h3", {}, story.title),
      el("p", { class: "summary-byline", style: "color:var(--muted);" }, story.devotee + " — " + story.one_line),
    ),
    el("p", { style: "white-space: pre-wrap;" }, story.text),
    story.key_verse ? el("p", { style: "background:#FFF8E8; padding:0.6rem 0.8rem; border-left:3px solid var(--gold);" },
      el("strong", {}, story.key_verse),
      story.scripture ? " — " + story.scripture : ""
    ) : null,
    story.teaching ? el("p", { style: "font-style:italic; color:var(--ink-soft);" }, story.teaching) : null,
  ));
}
