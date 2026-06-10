// This Week view — weekly reading + japa method + story + week-at-a-glance.

import { weekReading, weekJapaMethod, weekStory } from "../content.js";
import {
  mostRecentSaturday, addDays, todayISO, el, formatDate
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

export async function render(root) {
  const [reading, method, story] = await Promise.all([
    weekReading(), weekJapaMethod(), weekStory(),
  ]);

  const sat = mostRecentSaturday();
  const weekStart = addDays(sat, -6);

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" },
    "Week of ", formatDate(weekStart), " — ", formatDate(sat)
  ));

  // Week at a glance
  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Week at a glance"),
    weekDots(sat),
  ));

  // Reading
  root.appendChild(el("div", { class: "view-card" },
    el("div", { class: "card-label" }, "WEEKLY READING · " + (reading.reading_minutes || "?") + " min"),
    el("h3", {}, reading.title),
    reading.subtitle ? el("p", { style: "color:var(--muted); margin-top:-0.3rem;" }, reading.subtitle) : null,
    el("p", { style: "white-space: pre-wrap;" }, reading.content),
    el("p", { class: "card-cite" }, "— " + reading.source),
  ));

  // Japa method
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

  // Story
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
