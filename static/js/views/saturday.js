// Saturday Check-in view — rotating questions + tone/bhava/practices/tools/priorities.

import { weekQuestions } from "../content.js";
import { mostRecentSaturday, addDays, el, formatDate, toast } from "../util.js";
import * as store from "../store.js";

export async function render(root) {
  const sat = mostRecentSaturday();
  const satISO = sat.toISOString().slice(0, 10);
  const weekStart = addDays(sat, -6);
  const today = new Date();
  const isSaturday = today.getDay() === 6;

  const existing = store.getCheckin(satISO);
  const questions = await weekQuestions(3);

  root.innerHTML = "";
  root.appendChild(el("div", { class: "meta-line" },
    "Week of ", formatDate(weekStart), " — ", formatDate(sat)
  ));

  if (!isSaturday) {
    root.appendChild(el("div", { class: "view-card", style: "background:#FFF5E0;" },
      el("p", { style: "margin:0; color:var(--ink-soft);" },
        `Today is ${today.toLocaleDateString(undefined, { weekday: "long" })}. The check-in is meant for Saturday. You can preview / edit any time.`),
    ));
  }

  // Half 1 — questions
  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Half 1 — Observe (the week past)"),
    el("h4", {}, "This week's questions"),
    ...questions.map((q, i) => el("div", { style: "margin-bottom:0.9rem;" },
      el("p", { style: "color:var(--ink-soft); font-weight:600; margin:0.4rem 0 0.2rem;" }, `Q${i + 1}.`),
      el("p", { style: "margin:0 0 0.3rem;" }, q.question),
      q.routes_through ? el("p", { style: "color:var(--muted); font-style:italic; font-size:0.85rem; margin:0 0 0.3rem;" }, `routes through ${q.routes_through}`) : null,
      el("textarea", {
        id: `q${i}`,
        placeholder: "(short response, or leave empty)",
        rows: 2,
      }, (existing?.answers || [])[i] || ""),
    )),
  ));

  // Half 2 — set
  const toneI = el("input", { type: "text", id: "tone", placeholder: "e.g., Returning to early rising" });
  const bhavaI = el("input", { type: "text", id: "bhava", placeholder: "e.g., trnad api sunicena" });
  const practicesT = el("textarea", { id: "practices", placeholder: "One per line — concrete acts for the coming week" });
  const toolsT = el("textarea", { id: "tools", placeholder: "One per line — physical or digital" });
  const prioritiesT = el("textarea", { id: "priorities", placeholder: "One per line; top first" });

  if (existing) {
    toneI.value = existing.tone || "";
    bhavaI.value = existing.mood_bhava || "";
    practicesT.value = (existing.practices || []).join("\n");
    toolsT.value = (existing.tools_needed || []).join("\n");
    prioritiesT.value = (existing.priorities || []).join("\n");
  }

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Half 2 — Set the coming week"),
    el("label", { class: "field" }, "Tone — the orientation"),
    toneI,
    el("label", { class: "field" }, "Mood (bhava)"),
    bhavaI,
    el("label", { class: "field" }, "Practices (one per line)"),
    practicesT,
    el("label", { class: "field" }, "Tools needed (one per line)"),
    toolsT,
    el("label", { class: "field" }, "Priorities (one per line; top first)"),
    prioritiesT,
  ));

  const saveBtn = el("button", { class: "primary" }, existing ? "Update check-in" : "Save check-in");
  saveBtn.addEventListener("click", () => {
    const answers = questions.map((_, i) => document.getElementById(`q${i}`).value.trim());
    const payload = {
      tone: toneI.value.trim(),
      mood_bhava: bhavaI.value.trim(),
      practices: practicesT.value.split("\n").map(s => s.trim()).filter(Boolean),
      tools_needed: toolsT.value.split("\n").map(s => s.trim()).filter(Boolean),
      priorities: prioritiesT.value.split("\n").map(s => s.trim()).filter(Boolean),
      answers,
      questions: questions.map(q => q.question),
    };
    store.saveCheckin(satISO, payload);
    toast(`Check-in saved for week ending ${satISO}`);
  });
  root.appendChild(el("div", { style: "text-align:center; margin: 1rem 0;" }, saveBtn));

  if (existing) {
    root.appendChild(el("p", { class: "meta-line" }, `Last saved: ${new Date(existing.submitted_at).toLocaleString()}`));
  }
}
